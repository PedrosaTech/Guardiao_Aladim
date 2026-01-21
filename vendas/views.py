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
from decimal import Decimal
from rest_framework import viewsets
from .models import CondicaoPagamento, PedidoVenda, ItemPedidoVenda
from .serializers import CondicaoPagamentoSerializer, PedidoVendaSerializer


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
    lojas = Loja.objects.filter(is_active=True)
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
    
    context = {
        'pedido': pedido,
        'itens': itens,
    }
    
    return render(request, 'vendas/detalhes_pedido.html', context)


@login_required
def criar_pedido(request):
    """
    Cria um novo pedido de venda.
    """
    from core.models import Loja
    from pessoas.models import Cliente
    
    lojas = Loja.objects.filter(is_active=True)
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
    
    lojas = Loja.objects.filter(is_active=True)
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
            quantidade = Decimal(str(request.POST.get('quantidade', 1)))
            preco_unitario = Decimal(str(request.POST.get('preco_unitario', 0)))
            desconto = Decimal(str(request.POST.get('desconto', 0)))
            
            if not produto_id:
                messages.error(request, 'Produto é obrigatório.')
                return redirect('vendas:detalhes_pedido', pedido_id=pedido.id)
            
            produto = Produto.objects.get(id=produto_id, is_active=True)
            
            # Se não informou preço, usar preço sugerido do produto
            if preco_unitario <= 0:
                preco_unitario = produto.preco_venda_sugerido
            
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
        
        except Exception as e:
            messages.error(request, f'Erro ao adicionar item: {str(e)}')
            return redirect('vendas:detalhes_pedido', pedido_id=pedido.id)
    
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
            item.quantidade = Decimal(str(request.POST.get('quantidade', item.quantidade)))
            item.preco_unitario = Decimal(str(request.POST.get('preco_unitario', item.preco_unitario)))
            item.desconto = Decimal(str(request.POST.get('desconto', item.desconto)))
            item.updated_by = request.user
            item.save()
            
            messages.success(request, 'Item atualizado com sucesso!')
            return redirect('vendas:detalhes_pedido', pedido_id=pedido.id)
        
        except Exception as e:
            messages.error(request, f'Erro ao atualizar item: {str(e)}')
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
    Fatura um pedido (muda status para FATURADO).
    """
    pedido = get_object_or_404(PedidoVenda, id=pedido_id, is_active=True)
    
    if pedido.status == 'FATURADO':
        messages.info(request, 'Pedido já está faturado.')
        return redirect('vendas:detalhes_pedido', pedido_id=pedido.id)
    
    if not pedido.itens.filter(is_active=True).exists():
        messages.error(request, 'Não é possível faturar um pedido sem itens.')
        return redirect('vendas:detalhes_pedido', pedido_id=pedido.id)
    
    try:
        pedido.status = 'FATURADO'
        pedido.updated_by = request.user
        pedido.save()
        
        messages.success(request, f'Pedido #{pedido.id} faturado com sucesso!')
    except Exception as e:
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
    API para busca de produtos.
    """
    termo = request.GET.get('q', '').strip()
    
    if not termo:
        return JsonResponse({'produtos': []})
    
    from produtos.models import Produto
    from django.db.models import Q
    
    # Busca por código de barras, código interno ou descrição
    produtos = Produto.objects.filter(
        is_active=True
    ).filter(
        Q(codigo_barras=termo) |
        Q(codigo_interno=termo) |
        Q(descricao__icontains=termo)
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

