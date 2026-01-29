"""
Views do módulo de orçamentos.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import OrcamentoVenda, ItemOrcamentoVenda
from .serializers import OrcamentoVendaSerializer, ItemOrcamentoVendaSerializer


class OrcamentoVendaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para OrcamentoVenda.
    
    Permite listar, criar, editar e visualizar orçamentos.
    """
    queryset = OrcamentoVenda.objects.filter(is_active=True)
    serializer_class = OrcamentoVendaSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        """
        Ao criar um orçamento, define o vendedor como o usuário autenticado.
        
        TODO: Garantir que empresa/loja sejam preenchidos corretamente
        (pode assumir valor padrão ou validar via serializer).
        """
        serializer.save(
            vendedor=self.request.user,
            created_by=self.request.user
        )
    
    def perform_update(self, serializer):
        """
        Ao atualizar, define updated_by.
        """
        serializer.save(updated_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def converter_para_pedido(self, request, pk=None):
        """
        Converte um orçamento em pedido via API.
        """
        orcamento = self.get_object()
        
        if orcamento.pedido_gerado:
            return Response({
                'message': f'Orçamento já foi convertido em Pedido #{orcamento.pedido_gerado.id}',
                'pedido_id': orcamento.pedido_gerado.id
            }, status=200)
        
        try:
            pedido = orcamento.converter_para_pedido()
            return Response({
                'message': f'Orçamento convertido em Pedido #{pedido.id}',
                'pedido_id': pedido.id
            }, status=201)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=400)


class ItemOrcamentoVendaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para ItemOrcamentoVenda.
    """
    queryset = ItemOrcamentoVenda.objects.filter(is_active=True)
    serializer_class = ItemOrcamentoVendaSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        """
        Ao criar um item, define created_by.
        """
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        """
        Ao atualizar, define updated_by.
        """
        serializer.save(updated_by=self.request.user)


@login_required
def lista_orcamentos(request):
    """
    Lista de orçamentos com filtros.
    """
    orcamentos = OrcamentoVenda.objects.filter(is_active=True).select_related(
        'empresa', 'loja', 'cliente', 'vendedor', 'pedido_gerado'
    )
    
    # Filtros
    origem_filter = request.GET.get('origem')
    tipo_operacao_filter = request.GET.get('tipo_operacao')
    status_filter = request.GET.get('status')
    empresa_filter = request.GET.get('empresa')
    loja_filter = request.GET.get('loja')
    vendedor_filter = request.GET.get('vendedor')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    search = request.GET.get('search')
    apenas_expirados = request.GET.get('apenas_expirados') == 'sim'
    
    if origem_filter:
        orcamentos = orcamentos.filter(origem=origem_filter)
    if tipo_operacao_filter:
        orcamentos = orcamentos.filter(tipo_operacao=tipo_operacao_filter)
    if status_filter:
        orcamentos = orcamentos.filter(status=status_filter)
    if empresa_filter:
        orcamentos = orcamentos.filter(empresa_id=empresa_filter)
    if loja_filter:
        orcamentos = orcamentos.filter(loja_id=loja_filter)
    if vendedor_filter:
        orcamentos = orcamentos.filter(vendedor_id=vendedor_filter)
    if data_inicio:
        try:
            data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
            orcamentos = orcamentos.filter(data_emissao__gte=data_inicio_dt)
        except:
            pass
    if data_fim:
        try:
            data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d') + timedelta(days=1)
            orcamentos = orcamentos.filter(data_emissao__lt=data_fim_dt)
        except:
            pass
    if search:
        orcamentos = orcamentos.filter(
            Q(nome_responsavel__icontains=search) |
            Q(email_contato__icontains=search) |
            Q(observacoes__icontains=search)
        )
    if apenas_expirados:
        hoje = timezone.now().date()
        orcamentos = orcamentos.filter(
            data_validade__lt=hoje,
            status__in=[OrcamentoVenda.StatusChoices.RASCUNHO, OrcamentoVenda.StatusChoices.ENVIADO, OrcamentoVenda.StatusChoices.APROVADO]
        )
    
    # Verificar e atualizar status de expirados
    hoje = timezone.now().date()
    orcamentos_para_expirar = orcamentos.filter(
        data_validade__lt=hoje,
        status__in=[OrcamentoVenda.StatusChoices.RASCUNHO, OrcamentoVenda.StatusChoices.ENVIADO, OrcamentoVenda.StatusChoices.APROVADO]
    )
    orcamentos_para_expirar.update(status=OrcamentoVenda.StatusChoices.EXPIRADO)
    
    # Ordenação
    orcamentos = orcamentos.order_by('-data_emissao', '-id')
    
    # Buscar dados para filtros
    from core.models import Empresa, Loja
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    empresas = Empresa.objects.filter(is_active=True)
    lojas = Loja.objects.filter(is_active=True)
    vendedores = User.objects.filter(is_active=True)
    
    # Estatísticas
    total_valor = orcamentos.aggregate(Sum('total_liquido'))['total_liquido__sum'] or 0
    total_orcamentos = orcamentos.count()
    orcamentos_expirados = orcamentos.filter(status=OrcamentoVenda.StatusChoices.EXPIRADO).count()
    orcamentos_convertidos = orcamentos.filter(status=OrcamentoVenda.StatusChoices.CONVERTIDO).count()
    
    context = {
        'orcamentos': orcamentos,
        'empresas': empresas,
        'lojas': lojas,
        'vendedores': vendedores,
        'total_valor': total_valor,
        'total_orcamentos': total_orcamentos,
        'orcamentos_expirados': orcamentos_expirados,
        'orcamentos_convertidos': orcamentos_convertidos,
        'origem_choices': OrcamentoVenda.OrigemChoices.choices,
        'tipo_operacao_choices': OrcamentoVenda.TipoOperacaoChoices.choices,
        'status_choices': OrcamentoVenda.StatusChoices.choices,
        'filtros': {
            'origem': origem_filter,
            'tipo_operacao': tipo_operacao_filter,
            'status': status_filter,
            'empresa': empresa_filter,
            'loja': loja_filter,
            'vendedor': vendedor_filter,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'search': search,
            'apenas_expirados': apenas_expirados,
        }
    }
    
    return render(request, 'orcamentos/lista_orcamentos.html', context)


@login_required
def detalhes_orcamento(request, orcamento_id):
    """
    Detalhes completos do orçamento.
    """
    orcamento = get_object_or_404(
        OrcamentoVenda.objects.select_related(
            'empresa', 'loja', 'cliente', 'vendedor', 'pedido_gerado', 'condicao_pagamento_prevista'
        ),
        id=orcamento_id,
        is_active=True
    )
    
    # Verificar e atualizar status se expirado
    hoje = timezone.now().date()
    if orcamento.data_validade < hoje and orcamento.status in [
        OrcamentoVenda.StatusChoices.RASCUNHO,
        OrcamentoVenda.StatusChoices.ENVIADO,
        OrcamentoVenda.StatusChoices.APROVADO
    ]:
        orcamento.status = OrcamentoVenda.StatusChoices.EXPIRADO
        orcamento.save(update_fields=['status'])
    
    # Buscar itens
    itens = orcamento.itens.filter(is_active=True).select_related('produto')
    
    context = {
        'orcamento': orcamento,
        'itens': itens,
    }
    
    return render(request, 'orcamentos/detalhes_orcamento.html', context)


@login_required
def criar_orcamento(request):
    """
    Cria um novo orçamento.
    """
    from core.models import Empresa, Loja
    from pessoas.models import Cliente
    from vendas.models import CondicaoPagamento
    
    empresas = Empresa.objects.filter(is_active=True)
    lojas = Loja.objects.filter(is_active=True)
    clientes = Cliente.objects.filter(is_active=True)
    condicoes_pagamento = CondicaoPagamento.objects.filter(is_active=True)
    
    if request.method == 'POST':
        try:
            # Calcular data de validade padrão (30 dias)
            data_validade = request.POST.get('data_validade')
            if not data_validade:
                data_validade = (timezone.now().date() + timedelta(days=30)).isoformat()
            
            orcamento = OrcamentoVenda.objects.create(
                empresa_id=request.POST.get('empresa'),
                loja_id=request.POST.get('loja'),
                cliente_id=request.POST.get('cliente') or None,
                vendedor=request.user,
                nome_responsavel=request.POST.get('nome_responsavel'),
                telefone_contato=request.POST.get('telefone_contato') or None,
                whatsapp_contato=request.POST.get('whatsapp_contato') or None,
                email_contato=request.POST.get('email_contato') or None,
                origem=request.POST.get('origem'),
                tipo_operacao=request.POST.get('tipo_operacao'),
                data_validade=data_validade,
                condicao_pagamento_prevista_id=request.POST.get('condicao_pagamento_prevista') or None,
                observacoes=request.POST.get('observacoes') or None,
                created_by=request.user,
            )
            
            messages.success(request, f'Orçamento #{orcamento.id} criado com sucesso!')
            return redirect('orcamentos:detalhes_orcamento', orcamento_id=orcamento.id)
        
        except Exception as e:
            context = {
                'empresas': empresas,
                'lojas': lojas,
                'clientes': clientes,
                'condicoes_pagamento': condicoes_pagamento,
                'origem_choices': OrcamentoVenda.OrigemChoices.choices,
                'tipo_operacao_choices': OrcamentoVenda.TipoOperacaoChoices.choices,
                'erro': str(e),
                'form_data': request.POST,
            }
            return render(request, 'orcamentos/criar_orcamento.html', context)
    
    context = {
        'empresas': empresas,
        'lojas': lojas,
        'clientes': clientes,
        'condicoes_pagamento': condicoes_pagamento,
        'origem_choices': OrcamentoVenda.OrigemChoices.choices,
        'tipo_operacao_choices': OrcamentoVenda.TipoOperacaoChoices.choices,
    }
    
    return render(request, 'orcamentos/criar_orcamento.html', context)


@login_required
@require_http_methods(["GET"])
def buscar_produtos_rapido(request):
    """
    API para busca de produtos no orçamento rápido.
    Suporta código de barras principal/alternativo.
    """
    termo = request.GET.get('q', '').strip()

    if not termo:
        return JsonResponse({'produtos': []})

    from core.models import Empresa
    from produtos.utils import buscar_produto_por_codigo, buscar_produtos_por_termo

    empresa = Empresa.objects.filter(is_active=True).first()

    if termo.isdigit() and len(termo) >= 8:
        produto, codigo_alt, mult = buscar_produto_por_codigo(termo, empresa=empresa)
        if produto:
            return JsonResponse({
                'produtos': [{
                    'id': produto.id,
                    'codigo_interno': produto.codigo_interno,
                    'codigo_barras': termo,
                    'descricao': produto.descricao,
                    'preco_venda_sugerido': str(produto.preco_venda_sugerido),
                    'unidade_comercial': produto.unidade_comercial,
                    'classe_risco': produto.classe_risco,
                    'subclasse_risco': produto.subclasse_risco or '',
                    'multiplicador': float(mult),
                    'info_codigo': codigo_alt.descricao if codigo_alt else None,
                }]
            })

    produtos = buscar_produtos_por_termo(termo, empresa=empresa, limit=10)
    resultados = []
    for p in produtos:
        resultados.append({
            'id': p.id,
            'codigo_interno': p.codigo_interno,
            'codigo_barras': p.codigo_barras or '',
            'descricao': p.descricao,
            'preco_venda_sugerido': str(p.preco_venda_sugerido),
            'unidade_comercial': p.unidade_comercial,
            'classe_risco': p.classe_risco,
            'subclasse_risco': p.subclasse_risco or '',
            'multiplicador': 1.0,
            'info_codigo': None,
        })
    return JsonResponse({'produtos': resultados})


@login_required
@require_http_methods(["GET"])
def buscar_clientes_rapido(request):
    """
    API para busca de clientes no orçamento rápido.
    Retorna JSON com clientes ativos.
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


@login_required
def orcamento_rapido(request):
    """
    Tela de acesso rápido para criação de orçamentos.
    Interface simplificada focada em produtividade.
    """
    from core.models import Empresa, Loja
    from produtos.models import Produto
    from pessoas.models import Cliente
    
    # Obter empresa/loja padrão (primeira disponível)
    empresa = Empresa.objects.filter(is_active=True).first()
    loja = Loja.objects.filter(is_active=True).first()
    
    if not empresa or not loja:
        messages.error(request, 'É necessário cadastrar pelo menos uma empresa e uma loja.')
        return redirect('admin:index')
    
    if request.method == 'POST':
        try:
            from decimal import Decimal
            import json
            
            # Validar que há pelo menos 1 item
            itens_data = request.POST.get('itens', '[]')
            try:
                itens = json.loads(itens_data) if isinstance(itens_data, str) else itens_data
            except:
                itens = []
            
            if not itens or len(itens) == 0:
                messages.error(request, 'É necessário adicionar pelo menos um produto ao orçamento.')
                return render(request, 'orcamentos/orcamento_rapido.html', {
                    'empresa': empresa,
                    'loja': loja,
                })
            
            # Validar cliente ou nome_responsavel
            cliente_id = request.POST.get('cliente_id')
            nome_responsavel = request.POST.get('nome_responsavel', '').strip()
            
            if not cliente_id and not nome_responsavel:
                messages.error(request, 'É necessário informar um cliente ou o nome do responsável.')
                return render(request, 'orcamentos/orcamento_rapido.html', {
                    'empresa': empresa,
                    'loja': loja,
                })
            
            # Se tem cliente, usar nome do cliente como nome_responsavel se não informado
            if cliente_id and not nome_responsavel:
                try:
                    cliente = Cliente.objects.get(id=cliente_id, is_active=True)
                    nome_responsavel = cliente.nome_razao_social
                except Cliente.DoesNotExist:
                    pass
            
            # Criar orçamento
            orcamento = OrcamentoVenda.objects.create(
                empresa=empresa,
                loja=loja,
                cliente_id=cliente_id if cliente_id else None,
                vendedor=request.user,
                nome_responsavel=nome_responsavel,  # Sempre preencher (obrigatório no modelo)
                telefone_contato=request.POST.get('telefone_contato', '').strip() or None,
                email_contato=request.POST.get('email_contato', '').strip() or None,
                origem=OrcamentoVenda.OrigemChoices.BALCAO,
                tipo_operacao=OrcamentoVenda.TipoOperacaoChoices.VAREJO,
                status=OrcamentoVenda.StatusChoices.RASCUNHO,
                data_validade=timezone.now().date() + timedelta(days=30),
                created_by=request.user,
            )
            
            # Adicionar itens
            for item_data in itens:
                produto_id = item_data.get('produto_id')
                quantidade = Decimal(str(item_data.get('quantidade', 1)))
                desconto = Decimal(str(item_data.get('desconto', 0)))
                
                if not produto_id or quantidade <= 0:
                    continue
                
                try:
                    produto = Produto.objects.get(id=produto_id, is_active=True)
                    
                    ItemOrcamentoVenda.objects.create(
                        orcamento=orcamento,
                        produto=produto,
                        quantidade=quantidade,
                        valor_unitario=produto.preco_venda_sugerido,  # Sempre usa preço sugerido
                        desconto=desconto,
                        created_by=request.user,
                    )
                except Produto.DoesNotExist:
                    continue
            
            # Recalcular totais
            orcamento.recalcular_totais()
            
            # Verificar se deve finalizar ou manter como rascunho
            acao = request.POST.get('acao', 'rascunho')
            if acao == 'finalizar':
                orcamento.status = OrcamentoVenda.StatusChoices.ENVIADO
                orcamento.save()
                messages.success(request, f'Orçamento #{orcamento.id} criado e finalizado com sucesso!')
            else:
                messages.success(request, f'Orçamento #{orcamento.id} salvo como rascunho!')
            
            return redirect('orcamentos:detalhes_orcamento', orcamento_id=orcamento.id)
        
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Erro ao criar orçamento rápido: {str(e)}', exc_info=True)
            messages.error(request, f'Erro ao criar orçamento: {str(e)}')
            return render(request, 'orcamentos/orcamento_rapido.html', {
                'empresa': empresa,
                'loja': loja,
            })
    
    # GET - exibir formulário
    context = {
        'empresa': empresa,
        'loja': loja,
    }
    return render(request, 'orcamentos/orcamento_rapido.html', context)


@login_required
def adicionar_item_orcamento(request, orcamento_id):
    """
    Adiciona um item ao orçamento.
    """
    orcamento = get_object_or_404(OrcamentoVenda, id=orcamento_id, is_active=True)
    
    # Verificar se pode editar
    if orcamento.pedido_gerado:
        messages.error(request, 'Não é possível adicionar itens a um orçamento já convertido em pedido.')
        return redirect('orcamentos:detalhes_orcamento', orcamento_id=orcamento.id)
    
    if request.method == 'POST':
        try:
            from produtos.models import Produto
            from decimal import Decimal
            
            produto_id = request.POST.get('produto_id')
            quantidade = Decimal(str(request.POST.get('quantidade', 1)))
            valor_unitario = Decimal(str(request.POST.get('valor_unitario', 0)))
            desconto = Decimal(str(request.POST.get('desconto', 0)))
            
            if not produto_id:
                messages.error(request, 'Produto é obrigatório.')
                return redirect('orcamentos:detalhes_orcamento', orcamento_id=orcamento.id)
            
            produto = Produto.objects.get(id=produto_id, is_active=True)
            
            # Valor unitário sempre será o preço sugerido do produto (não pode ser alterado)
            valor_unitario = produto.preco_venda_sugerido
            
            from .models import ItemOrcamentoVenda
            item = ItemOrcamentoVenda.objects.create(
                orcamento=orcamento,
                produto=produto,
                quantidade=quantidade,
                valor_unitario=valor_unitario,
                desconto=desconto,
                created_by=request.user,
            )
            
            # Recalcula totais
            orcamento.recalcular_totais()
            
            messages.success(request, f'Item "{produto.descricao}" adicionado com sucesso!')
            return redirect('orcamentos:detalhes_orcamento', orcamento_id=orcamento.id)
        
        except Exception as e:
            messages.error(request, f'Erro ao adicionar item: {str(e)}')
            return redirect('orcamentos:detalhes_orcamento', orcamento_id=orcamento.id)
    
    # GET - mostrar formulário
    from produtos.models import Produto
    produtos = Produto.objects.filter(is_active=True).order_by('descricao')
    
    context = {
        'orcamento': orcamento,
        'produtos': produtos,
    }
    
    return render(request, 'orcamentos/adicionar_item.html', context)


@login_required
def editar_item_orcamento(request, orcamento_id, item_id):
    """
    Edita um item do orçamento.
    """
    orcamento = get_object_or_404(OrcamentoVenda, id=orcamento_id, is_active=True)
    item = get_object_or_404(ItemOrcamentoVenda, id=item_id, orcamento=orcamento, is_active=True)
    
    # Verificar se pode editar
    if orcamento.pedido_gerado:
        messages.error(request, 'Não é possível editar itens de um orçamento já convertido em pedido.')
        return redirect('orcamentos:detalhes_orcamento', orcamento_id=orcamento.id)
    
    if request.method == 'POST':
        try:
            from decimal import Decimal
            
            item.quantidade = Decimal(str(request.POST.get('quantidade', item.quantidade)))
            # Valor unitário não pode ser alterado - sempre usa o preço sugerido do produto
            # item.valor_unitario permanece inalterado (já está salvo com o preço sugerido)
            item.desconto = Decimal(str(request.POST.get('desconto', item.desconto)))
            item.updated_by = request.user
            item.save()
            
            # Recalcula totais
            orcamento.recalcular_totais()
            
            messages.success(request, 'Item atualizado com sucesso!')
            return redirect('orcamentos:detalhes_orcamento', orcamento_id=orcamento.id)
        
        except Exception as e:
            messages.error(request, f'Erro ao atualizar item: {str(e)}')
            return redirect('orcamentos:detalhes_orcamento', orcamento_id=orcamento.id)
    
    context = {
        'orcamento': orcamento,
        'item': item,
    }
    
    return render(request, 'orcamentos/editar_item.html', context)


@login_required
def remover_item_orcamento(request, orcamento_id, item_id):
    """
    Remove (desativa) um item do orçamento.
    """
    orcamento = get_object_or_404(OrcamentoVenda, id=orcamento_id, is_active=True)
    item = get_object_or_404(ItemOrcamentoVenda, id=item_id, orcamento=orcamento, is_active=True)
    
    # Verificar se pode editar
    if orcamento.pedido_gerado:
        messages.error(request, 'Não é possível remover itens de um orçamento já convertido em pedido.')
        return redirect('orcamentos:detalhes_orcamento', orcamento_id=orcamento.id)
    
    if request.method == 'POST':
        try:
            item.is_active = False
            item.updated_by = request.user
            item.save()
            
            # Recalcula totais
            orcamento.recalcular_totais()
            
            messages.success(request, 'Item removido com sucesso!')
            return redirect('orcamentos:detalhes_orcamento', orcamento_id=orcamento.id)
        
        except Exception as e:
            messages.error(request, f'Erro ao remover item: {str(e)}')
            return redirect('orcamentos:detalhes_orcamento', orcamento_id=orcamento.id)
    
    context = {
        'orcamento': orcamento,
        'item': item,
    }
    
    return render(request, 'orcamentos/remover_item.html', context)


@login_required
def imprimir_orcamento_pdf(request, orcamento_id):
    """
    Gera PDF do orçamento.
    
    Requer weasyprint instalado: pip install weasyprint
    """
    try:
        from weasyprint import HTML
        WEASYPRINT_AVAILABLE = True
    except ImportError:
        WEASYPRINT_AVAILABLE = False
    
    if not WEASYPRINT_AVAILABLE:
        from django.http import HttpResponse
        return HttpResponse(
            '<h1>Erro: WeasyPrint não instalado</h1>'
            '<p>Para gerar PDFs, instale o weasyprint:</p>'
            '<pre>pip install weasyprint</pre>',
            status=500
        )
    
    orcamento = get_object_or_404(
        OrcamentoVenda.objects.select_related(
            'empresa', 'loja', 'cliente', 'vendedor', 'condicao_pagamento_prevista'
        ),
        id=orcamento_id,
        is_active=True
    )
    
    # Buscar itens
    itens = orcamento.itens.filter(is_active=True).select_related('produto')
    
    # Preparar contexto
    from django.template.loader import render_to_string
    from django.http import HttpResponse
    
    context = {
        'orcamento': orcamento,
        'empresa': orcamento.empresa,
        'loja': orcamento.loja,
        'cliente': orcamento.cliente,
        'itens': itens,
    }
    
    # Renderizar template HTML
    html_string = render_to_string('orcamentos/orcamento_pdf.html', context)
    
    # Gerar PDF
    html = HTML(string=html_string)
    pdf = html.write_pdf()
    
    # Retornar PDF como resposta
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Orcamento_{orcamento.id}.pdf"'
    
    return response


@login_required
def converter_orcamento_pedido(request, orcamento_id):
    """
    Converte um orçamento em pedido.
    """
    orcamento = get_object_or_404(OrcamentoVenda, id=orcamento_id, is_active=True)
    
    # Verificar se tem itens
    if not orcamento.itens.filter(is_active=True).exists():
        messages.error(request, 'Não é possível converter um orçamento sem itens.')
        return redirect('orcamentos:detalhes_orcamento', orcamento_id=orcamento.id)
    
    if orcamento.pedido_gerado:
        messages.info(request, f'Orçamento já foi convertido em Pedido #{orcamento.pedido_gerado.id}')
        return redirect('orcamentos:detalhes_orcamento', orcamento_id=orcamento.id)
    
    try:
        pedido = orcamento.converter_para_pedido()
        messages.success(request, f'Orçamento convertido em Pedido #{pedido.id} com sucesso!')
        return redirect('admin:vendas_pedidovenda_change', pedido.id)
    except Exception as e:
        messages.error(request, f'Erro ao converter orçamento: {str(e)}')
        return redirect('orcamentos:detalhes_orcamento', orcamento_id=orcamento.id)


@login_required
def relatorio_orcamentos(request):
    """
    Relatório de orçamentos por período/origem.
    """
    # Filtros
    origem_filter = request.GET.get('origem')
    tipo_operacao_filter = request.GET.get('tipo_operacao')
    status_filter = request.GET.get('status')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    orcamentos = OrcamentoVenda.objects.filter(is_active=True).select_related(
        'empresa', 'loja', 'cliente', 'vendedor'
    )
    
    if origem_filter:
        orcamentos = orcamentos.filter(origem=origem_filter)
    if tipo_operacao_filter:
        orcamentos = orcamentos.filter(tipo_operacao=tipo_operacao_filter)
    if status_filter:
        orcamentos = orcamentos.filter(status=status_filter)
    if data_inicio:
        try:
            data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
            orcamentos = orcamentos.filter(data_emissao__gte=data_inicio_dt)
        except:
            pass
    if data_fim:
        try:
            data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d') + timedelta(days=1)
            orcamentos = orcamentos.filter(data_emissao__lt=data_fim_dt)
        except:
            pass
    
    # Estatísticas por origem
    stats_origem = orcamentos.values('origem').annotate(
        total=Count('id'),
        valor_total=Sum('total_liquido')
    ).order_by('origem')
    
    # Estatísticas por status
    stats_status = orcamentos.values('status').annotate(
        total=Count('id'),
        valor_total=Sum('total_liquido')
    ).order_by('status')
    
    # Estatísticas por tipo de operação
    stats_tipo = orcamentos.values('tipo_operacao').annotate(
        total=Count('id'),
        valor_total=Sum('total_liquido')
    ).order_by('tipo_operacao')
    
    # Totais gerais
    total_orcamentos = orcamentos.count()
    valor_total_geral = orcamentos.aggregate(Sum('total_liquido'))['total_liquido__sum'] or 0
    taxa_conversao = 0
    if total_orcamentos > 0:
        convertidos = orcamentos.filter(status=OrcamentoVenda.StatusChoices.CONVERTIDO).count()
        taxa_conversao = (convertidos / total_orcamentos) * 100
    
    context = {
        'orcamentos': orcamentos.order_by('-data_emissao')[:100],  # Limitar para performance
        'stats_origem': stats_origem,
        'stats_status': stats_status,
        'stats_tipo': stats_tipo,
        'total_orcamentos': total_orcamentos,
        'valor_total_geral': valor_total_geral,
        'taxa_conversao': taxa_conversao,
        'origem_choices': OrcamentoVenda.OrigemChoices.choices,
        'tipo_operacao_choices': OrcamentoVenda.TipoOperacaoChoices.choices,
        'status_choices': OrcamentoVenda.StatusChoices.choices,
        'filtros': {
            'origem': origem_filter,
            'tipo_operacao': tipo_operacao_filter,
            'status': status_filter,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
        }
    }
    
    return render(request, 'orcamentos/relatorio_orcamentos.html', context)
