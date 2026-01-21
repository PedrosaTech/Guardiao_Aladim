"""
Views do módulo PDV.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import json
import logging

from core.models import Loja
from produtos.models import Produto
from pessoas.models import Cliente
from vendas.models import CondicaoPagamento
from vendas.services import criar_pedido_venda_balcao
from .models import CaixaSessao, Pagamento, CompradorPirotecnia, RegistroVendaPirotecnia
from .validators import validar_cpf, formatar_cpf, calcular_idade, validar_idade_minima

logger = logging.getLogger(__name__)


@login_required
def pdv_view(request):
    """
    Tela principal do PDV.
    
    LGPD: Não exibir dados sensíveis do cliente desnecessariamente na tela do PDV.
    """
    # TODO: Obter loja do usuário ou da sessão
    # Por enquanto, pega a primeira loja (ajustar conforme necessidade)
    loja = Loja.objects.filter(is_active=True).first()
    
    if not loja:
        return render(request, 'pdv/erro.html', {
            'mensagem': 'Nenhuma loja cadastrada. Por favor, cadastre uma loja no admin.'
        })
    
    # Verifica se há sessão de caixa aberta
    # TODO: Futura tela de "Abrir Caixa" / "Fechar Caixa"
    caixa_aberto = CaixaSessao.objects.filter(
        loja=loja,
        status='ABERTO',
        usuario_abertura=request.user
    ).order_by('-data_hora_abertura').first()
    
    # Formas de pagamento disponíveis
    formas_pagamento = Pagamento.TIPO_CHOICES
    
    context = {
        'loja': loja,
        'caixa_aberto': caixa_aberto,
        'formas_pagamento': formas_pagamento,
    }
    return render(request, 'pdv/pdv.html', context)


@login_required
def abrir_caixa(request):
    """
    Tela para abrir uma nova sessão de caixa.
    """
    # Busca loja (por enquanto pega a primeira)
    loja = Loja.objects.filter(is_active=True).first()
    
    if not loja:
        messages.error(request, 'Nenhuma loja cadastrada. Por favor, cadastre uma loja no admin.')
        return redirect('pdv:pdv')
    
    # Verifica se já existe caixa aberto para este usuário
    caixa_aberto = CaixaSessao.objects.filter(
        loja=loja,
        status='ABERTO',
        usuario_abertura=request.user
    ).order_by('-data_hora_abertura').first()
    
    if caixa_aberto:
        messages.warning(request, f'Você já possui um caixa aberto desde {caixa_aberto.data_hora_abertura.strftime("%d/%m/%Y %H:%M")}.')
        return redirect('pdv:pdv')
    
    if request.method == 'POST':
        try:
            saldo_inicial = Decimal(request.POST.get('saldo_inicial', '0.00'))
            
            if saldo_inicial < 0:
                messages.error(request, 'O saldo inicial não pode ser negativo.')
                return render(request, 'pdv/abrir_caixa.html', {'loja': loja})
            
            # Cria nova sessão de caixa
            caixa = CaixaSessao.objects.create(
                loja=loja,
                usuario_abertura=request.user,
                saldo_inicial=saldo_inicial,
                status='ABERTO',
                created_by=request.user
            )
            
            messages.success(request, f'Caixa aberto com sucesso! Saldo inicial: R$ {saldo_inicial:.2f}')
            return redirect('pdv:pdv')
            
        except Exception as e:
            logger.error(f"Erro ao abrir caixa: {str(e)}", exc_info=True)
            messages.error(request, f'Erro ao abrir caixa: {str(e)}')
    
    context = {
        'loja': loja,
    }
    return render(request, 'pdv/abrir_caixa.html', context)


@login_required
def fechar_caixa(request, caixa_id=None):
    """
    Tela para fechar uma sessão de caixa.
    """
    # Busca loja
    loja = Loja.objects.filter(is_active=True).first()
    
    if not loja:
        messages.error(request, 'Nenhuma loja cadastrada.')
        return redirect('pdv:pdv')
    
    # Se não informou caixa_id, busca o caixa aberto do usuário
    if caixa_id:
        caixa = get_object_or_404(CaixaSessao, id=caixa_id, loja=loja, usuario_abertura=request.user)
    else:
        caixa = CaixaSessao.objects.filter(
            loja=loja,
            status='ABERTO',
            usuario_abertura=request.user
        ).order_by('-data_hora_abertura').first()
    
    if not caixa:
        messages.error(request, 'Nenhum caixa aberto encontrado.')
        return redirect('pdv:pdv')
    
    if caixa.status != 'ABERTO':
        messages.error(request, 'Este caixa já está fechado.')
        return redirect('pdv:pdv')
    
    # Calcula totais
    pagamentos = Pagamento.objects.filter(caixa_sessao=caixa)
    total_recebido = pagamentos.aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00')
    
    # Saldo esperado = saldo inicial + total recebido
    saldo_esperado = caixa.saldo_inicial + total_recebido
    
    if request.method == 'POST':
        try:
            saldo_final_informado = Decimal(request.POST.get('saldo_final', '0.00'))
            
            if saldo_final_informado < 0:
                messages.error(request, 'O saldo final não pode ser negativo.')
                return render(request, 'pdv/fechar_caixa.html', {
                    'caixa': caixa,
                    'loja': loja,
                    'total_recebido': total_recebido,
                    'saldo_esperado': saldo_esperado,
                })
            
            # Fecha o caixa
            caixa.saldo_final = saldo_final_informado
            caixa.data_hora_fechamento = timezone.now()
            caixa.usuario_fechamento = request.user
            caixa.status = 'FECHADO'
            caixa.updated_by = request.user
            caixa.save()
            
            # Calcula diferença
            diferenca = saldo_final_informado - saldo_esperado
            
            messages.success(request, f'Caixa fechado com sucesso!')
            if diferenca != 0:
                if diferenca > 0:
                    messages.info(request, f'Diferença (sobra): R$ {diferenca:.2f}')
                else:
                    messages.warning(request, f'Diferença (falta): R$ {abs(diferenca):.2f}')
            
            return redirect('pdv:pdv')
            
        except Exception as e:
            logger.error(f"Erro ao fechar caixa: {str(e)}", exc_info=True)
            messages.error(request, f'Erro ao fechar caixa: {str(e)}')
    
    # Calcula diferença (se já tiver saldo final informado)
    diferenca = None
    diferenca_abs = None
    if caixa.saldo_final:
        diferenca = caixa.saldo_final - saldo_esperado
        diferenca_abs = abs(diferenca)
    
    context = {
        'caixa': caixa,
        'loja': loja,
        'total_recebido': total_recebido,
        'saldo_esperado': saldo_esperado,
        'diferenca': diferenca,
        'diferenca_abs': diferenca_abs,
        'pagamentos': pagamentos,
    }
    return render(request, 'pdv/fechar_caixa.html', context)


@login_required
@require_http_methods(["GET"])
def buscar_produto(request):
    """
    Busca produto por código de barras, código interno ou descrição.
    Usado pela API do PDV.
    """
    termo = request.GET.get('q', '').strip()
    
    if not termo:
        return JsonResponse({'erro': 'Termo de busca não informado'}, status=400)
    
    # Busca APENAS por código numérico (código interno ou código de barras)
    # Remove espaços e caracteres não numéricos para busca mais flexível
    termo_limpo = ''.join(filter(str.isdigit, termo))
    
    produtos = Produto.objects.filter(
        is_active=True
    ).filter(
        Q(codigo_interno__icontains=termo_limpo) |
        Q(codigo_barras__icontains=termo_limpo)
    )[:10]
    
    resultados = []
    for produto in produtos:
        resultados.append({
            'id': produto.id,
            'codigo_interno': produto.codigo_interno,
            'codigo_barras': produto.codigo_barras or '',
            'descricao': produto.descricao,
            'preco_venda_sugerido': str(produto.preco_venda_sugerido),
            'unidade_comercial': produto.unidade_comercial,
            'possui_restricao_exercito': produto.possui_restricao_exercito,
        })
    
    return JsonResponse({'produtos': resultados})


@login_required
@require_http_methods(["POST"])
def criar_orcamento_pdv(request):
    """
    Cria um orçamento a partir dos itens do PDV.
    """
    try:
        data = json.loads(request.body)
        
        # Validações básicas
        loja_id = data.get('loja_id')
        itens = data.get('itens', [])
        nome_responsavel = data.get('nome_responsavel', 'Cliente Balcão')
        cliente_id = data.get('cliente_id')
        
        if not loja_id:
            return JsonResponse({'erro': 'Loja não informada'}, status=400)
        
        if not itens:
            return JsonResponse({'erro': 'O orçamento deve ter pelo menos um item'}, status=400)
        
        # Busca loja
        try:
            loja = Loja.objects.get(id=loja_id, is_active=True)
        except Loja.DoesNotExist:
            return JsonResponse({'erro': 'Loja não encontrada'}, status=404)
        
        # Cliente (opcional)
        cliente = None
        if cliente_id:
            try:
                cliente = Cliente.objects.get(id=cliente_id, is_active=True)
            except Cliente.DoesNotExist:
                logger.warning(f"Cliente {cliente_id} não encontrado, continuando sem cliente")
        
        # Valida itens
        itens_validos = []
        for item in itens:
            produto_id = item.get('produto_id')
            quantidade = item.get('quantidade')
            
            if not produto_id or not quantidade:
                return JsonResponse({'erro': 'Item inválido: produto_id e quantidade são obrigatórios'}, status=400)
            
            try:
                produto = Produto.objects.get(id=produto_id, is_active=True)
            except Produto.DoesNotExist:
                return JsonResponse({'erro': f'Produto {produto_id} não encontrado'}, status=404)
            
            preco_unitario = Decimal(str(item.get('preco_unitario', produto.preco_venda_sugerido)))
            desconto = Decimal(str(item.get('desconto', 0)))
            
            itens_validos.append({
                'produto': produto,
                'quantidade': Decimal(str(quantidade)),
                'valor_unitario': preco_unitario,
                'desconto': desconto,
            })
        
        # Cria o orçamento
        from orcamentos.models import OrcamentoVenda, ItemOrcamentoVenda
        
        with transaction.atomic():
            # Data de validade padrão: 30 dias
            data_validade = timezone.now().date() + timedelta(days=30)
            
            orcamento = OrcamentoVenda.objects.create(
                empresa=loja.empresa,
                loja=loja,
                cliente=cliente,
                vendedor=request.user,
                nome_responsavel=nome_responsavel,
                origem=OrcamentoVenda.OrigemChoices.BALCAO,
                tipo_operacao=OrcamentoVenda.TipoOperacaoChoices.VAREJO,
                data_validade=data_validade,
                status=OrcamentoVenda.StatusChoices.RASCUNHO,
                created_by=request.user,
            )
            
            # Cria os itens
            for item_data in itens_validos:
                ItemOrcamentoVenda.objects.create(
                    orcamento=orcamento,
                    produto=item_data['produto'],
                    quantidade=item_data['quantidade'],
                    valor_unitario=item_data['valor_unitario'],
                    desconto=item_data['desconto'],
                    created_by=request.user,
                )
            
            # Recalcula totais
            orcamento.recalcular_totais()
        
        logger.info(f"Orçamento criado com sucesso: Orçamento #{orcamento.id}")
        
        return JsonResponse({
            'sucesso': True,
            'orcamento_id': orcamento.id,
            'total_liquido': str(orcamento.total_liquido),
            'mensagem': f'Orçamento #{orcamento.id} criado com sucesso!'
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'erro': 'Dados inválidos (JSON malformado)'}, status=400)
    except Exception as e:
        logger.error(f"Erro ao criar orçamento: {str(e)}", exc_info=True)
        return JsonResponse({'erro': f'Erro ao criar orçamento: {str(e)}'}, status=500)


@login_required
@require_http_methods(["POST"])
def finalizar_venda(request):
    """
    Finaliza uma venda no PDV.
    
    Valida se há caixa aberto e chama o serviço de criação de pedido.
    """
    try:
        data = json.loads(request.body)
        
        # Validações básicas
        loja_id = data.get('loja_id')
        itens = data.get('itens', [])
        tipo_pagamento = data.get('tipo_pagamento')
        cliente_id = data.get('cliente_id')  # Opcional
        local_estoque_id = data.get('local_estoque_id')  # Opcional
        
        if not loja_id:
            return JsonResponse({'erro': 'Loja não informada'}, status=400)
        
        if not itens:
            return JsonResponse({'erro': 'A venda deve ter pelo menos um item'}, status=400)
        
        if not tipo_pagamento:
            return JsonResponse({'erro': 'Tipo de pagamento não informado'}, status=400)
        
        # Valida tipo de pagamento
        tipos_validos = [choice[0] for choice in Pagamento.TIPO_CHOICES]
        if tipo_pagamento not in tipos_validos:
            return JsonResponse({'erro': 'Tipo de pagamento inválido'}, status=400)
        
        # Busca loja
        try:
            loja = Loja.objects.get(id=loja_id, is_active=True)
        except Loja.DoesNotExist:
            return JsonResponse({'erro': 'Loja não encontrada'}, status=404)
        
        # Verifica se há caixa aberto
        caixa_sessao = CaixaSessao.objects.filter(
            loja=loja,
            status='ABERTO',
            usuario_abertura=request.user
        ).order_by('-data_hora_abertura').first()
        
        if not caixa_sessao:
            return JsonResponse({
                'erro': 'Nenhuma sessão de caixa aberta. Por favor, abra uma sessão de caixa antes de realizar vendas.'
            }, status=400)
        
        # Cliente (opcional para vendas de balcão)
        cliente = None
        if cliente_id:
            try:
                cliente = Cliente.objects.get(id=cliente_id, is_active=True)
            except Cliente.DoesNotExist:
                # Cliente não encontrado, mas não é obrigatório para balcão
                logger.warning(f"Cliente {cliente_id} não encontrado, continuando sem cliente")
        
        # Local de estoque (opcional)
        local_estoque = None
        if local_estoque_id:
            try:
                from estoque.models import LocalEstoque
                local_estoque = LocalEstoque.objects.get(id=local_estoque_id, loja=loja, is_active=True)
            except:
                logger.warning(f"Local de estoque {local_estoque_id} não encontrado, usando padrão")
        
        # Valida itens e verifica produtos com restrição
        itens_validos = []
        produtos_com_restricao = []
        
        for item in itens:
            produto_id = item.get('produto_id')
            quantidade = item.get('quantidade')
            
            if not produto_id or not quantidade:
                return JsonResponse({'erro': 'Item inválido: produto_id e quantidade são obrigatórios'}, status=400)
            
            try:
                produto = Produto.objects.get(id=produto_id, is_active=True)
            except Produto.DoesNotExist:
                return JsonResponse({'erro': f'Produto {produto_id} não encontrado'}, status=404)
            
            # Verifica se produto tem restrição
            if produto.possui_restricao_exercito:
                produtos_com_restricao.append({
                    'produto_id': produto_id,
                    'produto_nome': produto.descricao,
                    'quantidade': quantidade,
                })
            
            itens_validos.append({
                'produto_id': produto_id,
                'quantidade': Decimal(str(quantidade)),
                'preco_unitario': item.get('preco_unitario'),  # Opcional
                'desconto': item.get('desconto', 0),
            })
        
        # Se houver produtos com restrição, exige dados do comprador
        comprador_pirotecnia = None
        if produtos_com_restricao:
            comprador_data = data.get('comprador_pirotecnia')
            if not comprador_data:
                return JsonResponse({
                    'erro': 'Produtos com restrição de Exército exigem dados do comprador',
                    'produtos_restricao': produtos_com_restricao,
                    'requer_validacao': True
                }, status=400)
            
            # Valida dados do comprador
            try:
                # Valida CPF
                cpf_limpo = validar_cpf(comprador_data.get('cpf'))
                cpf_formatado = formatar_cpf(cpf_limpo)
                
                # Valida idade
                from datetime import datetime
                data_nascimento = datetime.strptime(comprador_data.get('data_nascimento'), '%Y-%m-%d').date()
                validar_idade_minima(data_nascimento, idade_minima=18)
                
                # Obtém IP do cliente
                ip_cliente = request.META.get('REMOTE_ADDR', '')
                if not ip_cliente:
                    ip_cliente = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
                
                # Cria ou busca comprador
                comprador_pirotecnia, created = CompradorPirotecnia.objects.get_or_create(
                    cpf=cpf_formatado,
                    defaults={
                        'nome_completo': comprador_data.get('nome_completo'),
                        'data_nascimento': data_nascimento,
                        'telefone': comprador_data.get('telefone', ''),
                        'email': comprador_data.get('email', ''),
                        'tipo_documento': comprador_data.get('tipo_documento', 'RG'),
                        'numero_documento': comprador_data.get('numero_documento', ''),
                        'orgao_emissor': comprador_data.get('orgao_emissor', ''),
                        'uf_emissor': comprador_data.get('uf_emissor', ''),
                        'logradouro': comprador_data.get('logradouro', ''),
                        'numero': comprador_data.get('numero', ''),
                        'complemento': comprador_data.get('complemento', ''),
                        'bairro': comprador_data.get('bairro', ''),
                        'cidade': comprador_data.get('cidade', ''),
                        'uf': comprador_data.get('uf', ''),
                        'cep': comprador_data.get('cep', ''),
                        'aceite_termo': True,
                        'data_aceite': timezone.now(),
                        'ip_aceite': ip_cliente,
                        'created_by': request.user,
                    }
                )
                
                # Se já existe, atualiza dados se necessário
                if not created:
                    comprador_pirotecnia.aceite_termo = True
                    comprador_pirotecnia.data_aceite = timezone.now()
                    comprador_pirotecnia.ip_aceite = ip_cliente
                    comprador_pirotecnia.save()
                
            except ValidationError as e:
                return JsonResponse({'erro': str(e)}, status=400)
            except Exception as e:
                logger.error(f"Erro ao validar comprador: {str(e)}", exc_info=True)
                return JsonResponse({'erro': f'Erro ao validar dados do comprador: {str(e)}'}, status=400)
        
        # Cria o pedido usando o serviço
        try:
            pedido = criar_pedido_venda_balcao(
                loja=loja,
                caixa_sessao=caixa_sessao,
                usuario=request.user,
                itens=itens_validos,
                tipo_pagamento=tipo_pagamento,
                cliente=cliente,
                local_estoque=local_estoque,
            )
            
            # Registra vendas de produtos com restrição
            if comprador_pirotecnia and produtos_com_restricao:
                from vendas.models import ItemPedidoVenda
                for produto_restricao in produtos_com_restricao:
                    try:
                        produto = Produto.objects.get(id=produto_restricao['produto_id'])
                        item_pedido = ItemPedidoVenda.objects.filter(
                            pedido=pedido,
                            produto=produto,
                            is_active=True
                        ).first()
                        
                        if item_pedido:
                            RegistroVendaPirotecnia.objects.create(
                                pedido_venda=pedido,
                                item_pedido=item_pedido,
                                produto=produto,
                                comprador=comprador_pirotecnia,
                                quantidade=Decimal(str(produto_restricao['quantidade'])),
                                valor_unitario=item_pedido.preco_unitario,
                                valor_total=item_pedido.total,
                                numero_certificado_exercito=produto.numero_certificado_exercito,
                                created_by=request.user,
                            )
                            logger.info(
                                f"Registro pirotécnico criado: Pedido #{pedido.id}, "
                                f"Produto: {produto.descricao}, Comprador: {comprador_pirotecnia.nome_completo}"
                            )
                    except Exception as e:
                        logger.error(f"Erro ao criar registro pirotécnico: {str(e)}", exc_info=True)
                        # Não bloqueia a venda, mas registra o erro
            
            logger.info(f"Venda finalizada com sucesso: Pedido #{pedido.id}")
            
            return JsonResponse({
                'sucesso': True,
                'pedido_id': pedido.id,
                'valor_total': str(pedido.valor_total),
                'mensagem': 'Venda finalizada com sucesso!',
                'registro_pirotecnia': comprador_pirotecnia is not None
            })
        
        except ValueError as e:
            # Erro de validação (ex: estoque insuficiente)
            logger.warning(f"Erro ao finalizar venda: {str(e)}")
            return JsonResponse({'erro': str(e)}, status=400)
        
        except Exception as e:
            # Erro inesperado
            logger.error(f"Erro inesperado ao finalizar venda: {str(e)}", exc_info=True)
            return JsonResponse({'erro': 'Erro ao processar venda. Tente novamente.'}, status=500)
    
    except json.JSONDecodeError:
        return JsonResponse({'erro': 'Dados inválidos (JSON malformado)'}, status=400)
    except Exception as e:
        logger.error(f"Erro ao processar requisição: {str(e)}", exc_info=True)
        return JsonResponse({'erro': 'Erro ao processar requisição'}, status=500)
