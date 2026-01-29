"""
Views do app vendas.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
import re
import logging
import json
from django.core.serializers.json import DjangoJSONEncoder
from rest_framework import viewsets
from .models import CondicaoPagamento, PedidoVenda, ItemPedidoVenda
from .serializers import CondicaoPagamentoSerializer, PedidoVendaSerializer
from .forms import RelatorioVendasForm
from . import reports

logger = logging.getLogger(__name__)


def safe_decimal(value, default=Decimal('0.00')):
    """
    Converte valor do formulário para Decimal de forma segura.
    Trata valores vazios, None e formatação brasileira (vírgula).
    
    Args:
        value: Valor a converter (pode ser string, int, float, Decimal, None ou vazio)
        default: Valor padrão se conversão falhar
    
    Returns:
        Decimal: Valor convertido ou default
    """
    if value is None:
        return default
    
    # Converter para string e limpar
    value_str = str(value).strip()
    
    # Se vazio após strip, retornar default
    if not value_str or value_str == '':
        return default
    
    # Se já for Decimal, retornar direto
    if isinstance(value, Decimal):
        return value
    
    # Substituir vírgula por ponto (formatação brasileira)
    value_str = value_str.replace(',', '.')
    
    # Remover caracteres não numéricos exceto ponto e sinal negativo
    value_str = re.sub(r'[^\d.-]', '', value_str)
    
    # Se ficou vazio ou só tem símbolos, retornar default
    if not value_str or value_str == '.' or value_str == '-' or value_str == '+':
        return default
    
    try:
        return Decimal(value_str)
    except (ValueError, InvalidOperation, Exception):
        return default


class CondicaoPagamentoViewSet(viewsets.ModelViewSet):
    queryset = CondicaoPagamento.objects.filter(is_active=True)
    serializer_class = CondicaoPagamentoSerializer


class PedidoVendaViewSet(viewsets.ModelViewSet):
    queryset = PedidoVenda.objects.all()
    serializer_class = PedidoVendaSerializer


@login_required
def lista_pedidos(request):
    """
    Lista de pedidos de venda com filtros.
    """
    pedidos = PedidoVenda.objects.filter(is_active=True).select_related(
        'loja', 'cliente', 'vendedor', 'condicao_pagamento'
    )
    
    # Filtros
    tipo_venda_filter = request.GET.get('tipo_venda')
    status_filter = request.GET.get('status')
    loja_filter = request.GET.get('loja')
    cliente_filter = request.GET.get('cliente')
    vendedor_filter = request.GET.get('vendedor')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    search = request.GET.get('search')
    
    if tipo_venda_filter:
        pedidos = pedidos.filter(tipo_venda=tipo_venda_filter)
    if status_filter:
        pedidos = pedidos.filter(status=status_filter)
    if loja_filter:
        pedidos = pedidos.filter(loja_id=loja_filter)
    if cliente_filter:
        pedidos = pedidos.filter(cliente_id=cliente_filter)
    if vendedor_filter:
        pedidos = pedidos.filter(vendedor_id=vendedor_filter)
    if data_inicio:
        try:
            data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
            pedidos = pedidos.filter(data_emissao__gte=data_inicio_dt)
        except:
            pass
    if data_fim:
        try:
            data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d') + timedelta(days=1)
            pedidos = pedidos.filter(data_emissao__lt=data_fim_dt)
        except:
            pass
    if search:
        pedidos = pedidos.filter(
            Q(id__icontains=search) |
            Q(cliente__nome_razao_social__icontains=search) |
            Q(observacoes__icontains=search)
        )
    
    # Ordenação
    pedidos = pedidos.order_by('-data_emissao', '-id')
    
    # Buscar dados para filtros
    from core.models import Loja
    from pessoas.models import Cliente
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    lojas = Loja.objects.filter(is_active=True).select_related('empresa')
    clientes = Cliente.objects.filter(is_active=True)
    vendedores = User.objects.filter(is_active=True)
    
    # Estatísticas
    total_valor = pedidos.aggregate(Sum('valor_total'))['valor_total__sum'] or 0
    total_pedidos = pedidos.count()
    pedidos_abertos = pedidos.filter(status='ABERTO').count()
    pedidos_faturados = pedidos.filter(status='FATURADO').count()
    
    context = {
        'pedidos': pedidos,
        'lojas': lojas,
        'clientes': clientes,
        'vendedores': vendedores,
        'total_valor': total_valor,
        'total_pedidos': total_pedidos,
        'pedidos_abertos': pedidos_abertos,
        'pedidos_faturados': pedidos_faturados,
        'tipo_venda_choices': PedidoVenda.TIPO_VENDA_CHOICES,
        'status_choices': PedidoVenda.STATUS_CHOICES,
        'filtros': {
            'tipo_venda': tipo_venda_filter,
            'status': status_filter,
            'loja': loja_filter,
            'cliente': cliente_filter,
            'vendedor': vendedor_filter,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'search': search,
        }
    }
    
    return render(request, 'vendas/lista_pedidos.html', context)


@login_required
def detalhes_pedido(request, pedido_id):
    """
    Detalhes completos do pedido de venda.
    """
    pedido = get_object_or_404(
        PedidoVenda.objects.select_related(
            'loja', 'cliente', 'vendedor', 'condicao_pagamento'
        ),
        id=pedido_id,
        is_active=True
    )
    
    # Buscar itens
    itens = pedido.itens.filter(is_active=True).select_related('produto')
    
    # Buscar nota fiscal associada (se existir)
    nota_fiscal = None
    try:
        from fiscal.models import NotaFiscalSaida
        nota_fiscal = NotaFiscalSaida.objects.filter(
            pedido_venda=pedido,
            is_active=True
        ).first()
    except:
        pass
    
    context = {
        'pedido': pedido,
        'itens': itens,
        'nota_fiscal': nota_fiscal,
    }
    
    return render(request, 'vendas/detalhes_pedido.html', context)


@login_required
def relatorio_vendas_consolidado(request):
    """
    Relatório de vendas consolidado (somente pedidos FATURADO).
    Inclui filtros e permite segmentar por fornecedor do código alternativo usado.
    """
    # Melhor esforço para filtrar por empresa (se existir contexto)
    empresa = None
    if hasattr(request.user, "empresa"):
        empresa = getattr(request.user, "empresa", None)
    if not empresa:
        try:
            from core.models import Empresa

            empresa = Empresa.objects.filter(is_active=True).first()
        except Exception:
            empresa = None

    form = RelatorioVendasForm(request.GET or None, empresa=empresa)
    qs = reports.aplicar_filtros(reports.queryset_base_vendas(), form)

    agrupar_por = "produto"
    ordenar_por = "-valor_total"
    if form.is_valid():
        agrupar_por = form.cleaned_data.get("agrupar_por") or "produto"
        ordenar_por = form.cleaned_data.get("ordenar_por") or "-valor_total"

    dados_qs = reports.agregar(qs, agrupar_por=agrupar_por, ordenar_por=ordenar_por)
    dados = list(dados_qs) if hasattr(dados_qs, "__iter__") else []

    totais = reports.calcular_totais(qs)
    produtos_top = reports.top_produtos(qs, limit=10)

    codigos_alt_info = []
    if form.is_valid() and form.cleaned_data.get("produto"):
        codigos_alt_info = reports.codigos_alternativos_info(form.cleaned_data["produto"].id)

    # exportações
    export = request.GET.get("export")
    filtros_desc = request.GET.urlencode()
    if export == "excel":
        return reports.exportar_excel(dados, totais, filtros_desc=filtros_desc)
    if export == "pdf":
        return reports.exportar_pdf(
            request,
            dados,
            totais,
            context_extra={
                "filtros_desc": filtros_desc,
            },
        )

    # json para charts (se necessário)
    if request.GET.get("format") == "json":
        return JsonResponse(
            {
                "dados": dados,
                "totais": totais.__dict__,
                "produtos_top": produtos_top,
            },
            encoder=DjangoJSONEncoder,
            safe=True,
        )

    # querystring para manter filtros nos botões de export
    querystring = request.GET.urlencode()
    if querystring:
        # removemos export se estiver presente para não acumular
        q = request.GET.copy()
        q.pop("export", None)
        querystring = q.urlencode()

    context = {
        "form": form,
        "dados": dados,
        "totais": totais,
        "produtos_top": produtos_top,
        "codigos_alternativos_info": codigos_alt_info,
        "dados_json": json.dumps(dados, cls=DjangoJSONEncoder),
        "querystring": querystring,
    }
    return render(request, "vendas/relatorio_vendas.html", context)


@login_required
def criar_pedido(request):
    """
    Cria um novo pedido de venda.
    """
    from core.models import Loja
    from pessoas.models import Cliente
    
    lojas = Loja.objects.filter(is_active=True).select_related('empresa')
    clientes = Cliente.objects.filter(is_active=True)
    condicoes_pagamento = CondicaoPagamento.objects.filter(is_active=True)
    
    if request.method == 'POST':
        try:
            # Buscar condição de pagamento ou criar padrão
            condicao_pagamento_id = request.POST.get('condicao_pagamento')
            if not condicao_pagamento_id:
                # Buscar condição padrão da loja
                loja = Loja.objects.get(id=request.POST.get('loja'))
                condicao_pagamento = CondicaoPagamento.objects.filter(
                    empresa=loja.empresa,
                    is_active=True,
                    numero_parcelas=1,
                    dias_entre_parcelas=0
                ).first()
                
                if not condicao_pagamento:
                    condicao_pagamento = CondicaoPagamento.objects.create(
                        empresa=loja.empresa,
                        nome='À Vista',
                        descricao='Pagamento à vista',
                        numero_parcelas=1,
                        dias_entre_parcelas=0,
                        created_by=request.user,
                    )
            else:
                condicao_pagamento = CondicaoPagamento.objects.get(id=condicao_pagamento_id, is_active=True)
            
            pedido = PedidoVenda.objects.create(
                loja_id=request.POST.get('loja'),
                cliente_id=request.POST.get('cliente'),
                tipo_venda=request.POST.get('tipo_venda'),
                status=request.POST.get('status', 'ORCAMENTO'),
                vendedor=request.user,
                condicao_pagamento=condicao_pagamento,
                valor_total=Decimal('0.00'),
                observacoes=request.POST.get('observacoes') or None,
                created_by=request.user,
            )
            
            messages.success(request, f'Pedido #{pedido.id} criado com sucesso!')
            return redirect('vendas:detalhes_pedido', pedido_id=pedido.id)
        
        except Exception as e:
            context = {
                'lojas': lojas,
                'clientes': clientes,
                'condicoes_pagamento': condicoes_pagamento,
                'tipo_venda_choices': PedidoVenda.TIPO_VENDA_CHOICES,
                'status_choices': PedidoVenda.STATUS_CHOICES,
                'erro': str(e),
                'form_data': request.POST,
            }
            return render(request, 'vendas/criar_pedido.html', context)
    
    context = {
        'lojas': lojas,
        'clientes': clientes,
        'condicoes_pagamento': condicoes_pagamento,
        'tipo_venda_choices': PedidoVenda.TIPO_VENDA_CHOICES,
        'status_choices': PedidoVenda.STATUS_CHOICES,
    }
    
    return render(request, 'vendas/criar_pedido.html', context)


@login_required
def editar_pedido(request, pedido_id):
    """
    Edita um pedido de venda.
    """
    pedido = get_object_or_404(PedidoVenda, id=pedido_id, is_active=True)
    
    # Verificar se pode editar
    if pedido.status == 'FATURADO':
        messages.error(request, 'Não é possível editar um pedido faturado.')
        return redirect('vendas:detalhes_pedido', pedido_id=pedido.id)
    
    from core.models import Loja
    from pessoas.models import Cliente
    
    lojas = Loja.objects.filter(is_active=True).select_related('empresa')
    clientes = Cliente.objects.filter(is_active=True)
    condicoes_pagamento = CondicaoPagamento.objects.filter(is_active=True)
    
    if request.method == 'POST':
        try:
            pedido.loja_id = request.POST.get('loja')
            pedido.cliente_id = request.POST.get('cliente')
            pedido.tipo_venda = request.POST.get('tipo_venda')
            pedido.status = request.POST.get('status')
            pedido.condicao_pagamento_id = request.POST.get('condicao_pagamento')
            pedido.observacoes = request.POST.get('observacoes') or None
            pedido.updated_by = request.user
            pedido.save()
            
            messages.success(request, 'Pedido atualizado com sucesso!')
            return redirect('vendas:detalhes_pedido', pedido_id=pedido.id)
        
        except Exception as e:
            messages.error(request, f'Erro ao atualizar pedido: {str(e)}')
    
    context = {
        'pedido': pedido,
        'lojas': lojas,
        'clientes': clientes,
        'condicoes_pagamento': condicoes_pagamento,
        'tipo_venda_choices': PedidoVenda.TIPO_VENDA_CHOICES,
        'status_choices': PedidoVenda.STATUS_CHOICES,
    }
    
    return render(request, 'vendas/editar_pedido.html', context)


@login_required
def adicionar_item_pedido(request, pedido_id):
    """
    Adiciona um item ao pedido.
    """
    pedido = get_object_or_404(PedidoVenda, id=pedido_id, is_active=True)
    
    # Verificar se pode editar
    if pedido.status == 'FATURADO':
        messages.error(request, 'Não é possível adicionar itens a um pedido faturado.')
        return redirect('vendas:detalhes_pedido', pedido_id=pedido.id)
    
    if request.method == 'POST':
        try:
            from produtos.models import Produto
            
            produto_id = request.POST.get('produto_id')
            
            # Converter valores com tratamento seguro
            quantidade_str = request.POST.get('quantidade', '1')
            quantidade = safe_decimal(quantidade_str, Decimal('1.00'))
            
            preco_unitario_str = request.POST.get('preco_unitario', '')
            preco_unitario = safe_decimal(preco_unitario_str, Decimal('0.00'))
            
            desconto_str = request.POST.get('desconto', '0')
            desconto = safe_decimal(desconto_str, Decimal('0.00'))
            
            if not produto_id:
                messages.error(request, 'Produto é obrigatório.')
                return redirect('vendas:detalhes_pedido', pedido_id=pedido.id)
            
            # Validar quantidade
            if quantidade <= 0:
                messages.error(request, 'Quantidade deve ser maior que zero.')
                return redirect('vendas:adicionar_item_pedido', pedido_id=pedido.id)
            
            produto = Produto.objects.get(id=produto_id, is_active=True)
            
            # Se não informou preço, usar preço sugerido do produto
            if preco_unitario <= 0:
                preco_unitario = produto.preco_venda_sugerido
            
            # Validar preço unitário
            if preco_unitario <= 0:
                messages.error(request, 'Preço unitário deve ser maior que zero.')
                return redirect('vendas:adicionar_item_pedido', pedido_id=pedido.id)
            
            # Validar desconto não pode ser negativo
            if desconto < 0:
                desconto = Decimal('0.00')
            
            item = ItemPedidoVenda.objects.create(
                pedido=pedido,
                produto=produto,
                quantidade=quantidade,
                preco_unitario=preco_unitario,
                desconto=desconto,
                created_by=request.user,
            )
            
            messages.success(request, f'Item "{produto.descricao}" adicionado com sucesso!')
            return redirect('vendas:detalhes_pedido', pedido_id=pedido.id)
        
        except Produto.DoesNotExist:
            messages.error(request, 'Produto não encontrado.')
            return redirect('vendas:adicionar_item_pedido', pedido_id=pedido.id)
        except Exception as e:
            import traceback
            messages.error(request, f'Erro ao adicionar item: {str(e)}')
            # Log do erro completo para debug
            print(f"Erro completo: {traceback.format_exc()}")
            return redirect('vendas:adicionar_item_pedido', pedido_id=pedido.id)
    
    # GET - mostrar formulário
    from produtos.models import Produto
    produtos = Produto.objects.filter(is_active=True).order_by('descricao')
    
    context = {
        'pedido': pedido,
        'produtos': produtos,
    }
    
    return render(request, 'vendas/adicionar_item.html', context)


@login_required
def editar_item_pedido(request, pedido_id, item_id):
    """
    Edita um item do pedido.
    """
    pedido = get_object_or_404(PedidoVenda, id=pedido_id, is_active=True)
    item = get_object_or_404(ItemPedidoVenda, id=item_id, pedido=pedido, is_active=True)
    
    # Verificar se pode editar
    if pedido.status == 'FATURADO':
        messages.error(request, 'Não é possível editar itens de um pedido faturado.')
        return redirect('vendas:detalhes_pedido', pedido_id=pedido.id)
    
    if request.method == 'POST':
        try:
            # Converter valores com tratamento seguro
            quantidade_str = request.POST.get('quantidade', str(item.quantidade))
            quantidade = safe_decimal(quantidade_str, item.quantidade)
            
            preco_unitario_str = request.POST.get('preco_unitario', str(item.preco_unitario))
            preco_unitario = safe_decimal(preco_unitario_str, item.preco_unitario)
            
            desconto_str = request.POST.get('desconto', str(item.desconto))
            desconto = safe_decimal(desconto_str, item.desconto)
            
            # Validações
            if quantidade <= 0:
                messages.error(request, 'Quantidade deve ser maior que zero.')
                return redirect('vendas:editar_item_pedido', pedido_id=pedido.id, item_id=item.id)
            
            if preco_unitario <= 0:
                messages.error(request, 'Preço unitário deve ser maior que zero.')
                return redirect('vendas:editar_item_pedido', pedido_id=pedido.id, item_id=item.id)
            
            if desconto < 0:
                desconto = Decimal('0.00')
            
            item.quantidade = quantidade
            item.preco_unitario = preco_unitario
            item.desconto = desconto
            item.updated_by = request.user
            item.save()
            
            messages.success(request, 'Item atualizado com sucesso!')
            return redirect('vendas:detalhes_pedido', pedido_id=pedido.id)
        
        except Exception as e:
            import traceback
            messages.error(request, f'Erro ao atualizar item: {str(e)}')
            # Log do erro completo para debug
            print(f"Erro completo: {traceback.format_exc()}")
            return redirect('vendas:detalhes_pedido', pedido_id=pedido.id)
    
    context = {
        'pedido': pedido,
        'item': item,
    }
    
    return render(request, 'vendas/editar_item.html', context)


@login_required
def remover_item_pedido(request, pedido_id, item_id):
    """
    Remove (desativa) um item do pedido.
    """
    pedido = get_object_or_404(PedidoVenda, id=pedido_id, is_active=True)
    item = get_object_or_404(ItemPedidoVenda, id=item_id, pedido=pedido, is_active=True)
    
    # Verificar se pode editar
    if pedido.status == 'FATURADO':
        messages.error(request, 'Não é possível remover itens de um pedido faturado.')
        return redirect('vendas:detalhes_pedido', pedido_id=pedido.id)
    
    if request.method == 'POST':
        try:
            item.is_active = False
            item.updated_by = request.user
            item.save()
            
            messages.success(request, 'Item removido com sucesso!')
            return redirect('vendas:detalhes_pedido', pedido_id=pedido.id)
        
        except Exception as e:
            messages.error(request, f'Erro ao remover item: {str(e)}')
            return redirect('vendas:detalhes_pedido', pedido_id=pedido.id)
    
    context = {
        'pedido': pedido,
        'item': item,
    }
    
    return render(request, 'vendas/remover_item.html', context)


@login_required
@require_http_methods(["POST"])
def faturar_pedido(request, pedido_id):
    """
    Fatura um pedido (muda status para FATURADO) e cria nota fiscal automaticamente.
    """
    from django.db import transaction
    from fiscal.services import criar_nfe_rascunho_para_pedido
    
    pedido = get_object_or_404(PedidoVenda, id=pedido_id, is_active=True)
    
    if pedido.status == 'FATURADO':
        messages.info(request, 'Pedido já está faturado.')
        return redirect('vendas:detalhes_pedido', pedido_id=pedido.id)
    
    if not pedido.itens.filter(is_active=True).exists():
        messages.error(request, 'Não é possível faturar um pedido sem itens.')
        return redirect('vendas:detalhes_pedido', pedido_id=pedido.id)
    
    try:
        with transaction.atomic():
            # Criar nota fiscal antes de faturar
            try:
                nota_fiscal = criar_nfe_rascunho_para_pedido(pedido, usuario=request.user)
                mensagem_nota = f' Nota Fiscal {nota_fiscal.numero}/{nota_fiscal.serie} criada.'
            except Exception as e_nota:
                # Se falhar ao criar nota, ainda fatura o pedido mas avisa
                logger.warning(f"Erro ao criar nota fiscal para pedido {pedido.id}: {str(e_nota)}")
                mensagem_nota = f' Atenção: Não foi possível criar a nota fiscal automaticamente: {str(e_nota)}'
            
            # Faturar pedido
            pedido.status = 'FATURADO'
            pedido.updated_by = request.user
            pedido.save()
            
            messages.success(
                request, 
                f'Pedido #{pedido.id} faturado com sucesso!{mensagem_nota}'
            )
            
            # Se criou nota, gerar títulos financeiros
            try:
                from financeiro.services.financial_service import FinancialService
                FinancialService.gerar_titulos_de_venda(pedido, request.user)
            except Exception as e_fin:
                logger.warning(f"Erro ao gerar títulos financeiros para pedido {pedido.id}: {str(e_fin)}")
                # Não bloqueia o faturamento se falhar ao gerar títulos
                
    except Exception as e:
        import traceback
        logger.error(f"Erro ao faturar pedido {pedido.id}: {str(e)}\n{traceback.format_exc()}")
        messages.error(request, f'Erro ao faturar pedido: {str(e)}')
    
    return redirect('vendas:detalhes_pedido', pedido_id=pedido.id)


@login_required
@require_http_methods(["POST"])
def cancelar_pedido(request, pedido_id):
    """
    Cancela um pedido (muda status para CANCELADO).
    """
    pedido = get_object_or_404(PedidoVenda, id=pedido_id, is_active=True)
    
    if pedido.status == 'CANCELADO':
        messages.info(request, 'Pedido já está cancelado.')
        return redirect('vendas:detalhes_pedido', pedido_id=pedido.id)
    
    if pedido.status == 'FATURADO':
        messages.error(request, 'Não é possível cancelar um pedido faturado.')
        return redirect('vendas:detalhes_pedido', pedido_id=pedido.id)
    
    try:
        pedido.status = 'CANCELADO'
        pedido.updated_by = request.user
        pedido.save()
        
        messages.success(request, f'Pedido #{pedido.id} cancelado com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro ao cancelar pedido: {str(e)}')
    
    return redirect('vendas:detalhes_pedido', pedido_id=pedido.id)


@login_required
@require_http_methods(["GET"])
def buscar_produtos_rapido(request):
    """
    API para busca de produtos. Suporta código de barras principal/alternativo.
    """
    termo = request.GET.get('q', '').strip()

    if not termo:
        return JsonResponse({'produtos': []})

    from produtos.utils import buscar_produto_por_codigo, buscar_produtos_por_termo

    if termo.isdigit() and len(termo) >= 8:
        produto, codigo_alt, mult = buscar_produto_por_codigo(termo, empresa=None)
        if produto:
            return JsonResponse({
                'produtos': [{
                    'id': produto.id,
                    'codigo_interno': produto.codigo_interno,
                    'codigo_barras': termo,
                    'descricao': produto.descricao,
                    'preco_venda_sugerido': str(produto.preco_venda_sugerido),
                    'unidade_comercial': produto.unidade_comercial,
                    'multiplicador': float(mult),
                    'info_codigo': codigo_alt.descricao if codigo_alt else None,
                }]
            })

    produtos = buscar_produtos_por_termo(termo, empresa=None, limit=10)
    resultados = []
    for p in produtos:
        resultados.append({
            'id': p.id,
            'codigo_interno': p.codigo_interno,
            'codigo_barras': p.codigo_barras or '',
            'descricao': p.descricao,
            'preco_venda_sugerido': str(p.preco_venda_sugerido),
            'unidade_comercial': p.unidade_comercial,
            'multiplicador': 1.0,
            'info_codigo': None,
        })
    return JsonResponse({'produtos': resultados})


@login_required
@require_http_methods(["GET"])
def buscar_clientes_rapido(request):
    """
    API para busca de clientes.
    """
    termo = request.GET.get('q', '').strip()
    
    if not termo:
        return JsonResponse({'clientes': []})
    
    from pessoas.models import Cliente
    from django.db.models import Q
    
    # Busca por nome, CPF/CNPJ, email ou telefone
    clientes = Cliente.objects.filter(
        is_active=True
    ).filter(
        Q(nome_razao_social__icontains=termo) |
        Q(apelido_nome_fantasia__icontains=termo) |
        Q(cpf_cnpj__icontains=termo) |
        Q(email__icontains=termo) |
        Q(telefone__icontains=termo)
    )[:10]
    
    resultados = []
    for cliente in clientes:
        resultados.append({
            'id': cliente.id,
            'nome_razao_social': cliente.nome_razao_social,
            'apelido_nome_fantasia': cliente.apelido_nome_fantasia or '',
            'cpf_cnpj': cliente.cpf_cnpj or '',
            'telefone': cliente.telefone or '',
            'email': cliente.email or '',
        })
    
    return JsonResponse({'clientes': resultados})

