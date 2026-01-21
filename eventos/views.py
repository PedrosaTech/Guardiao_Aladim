"""
Views do app eventos.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.core.exceptions import ValidationError
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from decimal import Decimal
import json

from .models import EventoVenda
from .serializers import EventoVendaSerializer
from .services import faturar_evento_com_nfe
from vendas.models import PedidoVenda, ItemPedidoVenda, CondicaoPagamento
from produtos.models import Produto


class EventoVendaViewSet(viewsets.ModelViewSet):
    queryset = EventoVenda.objects.filter(is_active=True)
    serializer_class = EventoVendaSerializer
    
    @action(detail=True, methods=['post'])
    def gerar_pedido(self, request, pk=None):
        """Gera pedido de venda para o evento."""
        evento = self.get_object()
        condicao_pagamento_id = request.data.get('condicao_pagamento_id')
        cliente_id = request.data.get('cliente_id')
        
        condicao_pagamento = None
        if condicao_pagamento_id:
            condicao_pagamento = CondicaoPagamento.objects.get(id=condicao_pagamento_id)
        
        cliente = None
        if cliente_id:
            from pessoas.models import Cliente
            cliente = Cliente.objects.get(id=cliente_id)
        
        pedido = evento.gerar_pedido_evento(condicao_pagamento=condicao_pagamento, cliente=cliente)
        
        return Response({
            'pedido_id': pedido.id,
            'mensagem': 'Pedido gerado com sucesso'
        })


@login_required
def proposta_evento(request, evento_id):
    """
    Tela de proposta de evento para montar itens do pedido.
    """
    evento = get_object_or_404(EventoVenda, id=evento_id, is_active=True)
    
    # Gera ou busca o pedido do evento
    pedido = evento.pedido
    if not pedido:
        pedido = evento.gerar_pedido_evento()
    
    # Busca itens do pedido
    itens = pedido.itens.filter(is_active=True)
    
    context = {
        'evento': evento,
        'pedido': pedido,
        'itens': itens,
    }
    
    return render(request, 'eventos/proposta_evento.html', context)


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def adicionar_item_proposta(request, evento_id):
    """
    Adiciona item à proposta do evento.
    """
    try:
        evento = get_object_or_404(EventoVenda, id=evento_id, is_active=True)
        
        # Garante que existe pedido
        if not evento.pedido:
            evento.gerar_pedido_evento()
        
        data = json.loads(request.body)
        produto_id = data.get('produto_id')
        quantidade = Decimal(str(data.get('quantidade', 1)))
        preco_unitario = Decimal(str(data.get('preco_unitario', 0)))
        desconto = Decimal(str(data.get('desconto', 0)))
        
        if not produto_id:
            return JsonResponse({'erro': 'Produto não informado'}, status=400)
        
        produto = Produto.objects.get(id=produto_id, is_active=True)
        
        # Se preço não informado, usa o preço sugerido
        if preco_unitario == 0:
            preco_unitario = produto.preco_venda_sugerido
        
        # Cria ou atualiza item
        item, created = ItemPedidoVenda.objects.get_or_create(
            pedido=evento.pedido,
            produto=produto,
            defaults={
                'quantidade': quantidade,
                'preco_unitario': preco_unitario,
                'desconto': desconto,
                'created_by': request.user,
            }
        )
        
        if not created:
            item.quantidade += quantidade
            item.save()
        
        # Recalcula total do pedido
        evento.pedido.recalcular_total()
        
        return JsonResponse({
            'sucesso': True,
            'item_id': item.id,
            'mensagem': 'Item adicionado com sucesso'
        })
    
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def remover_item_proposta(request, evento_id, item_id):
    """
    Remove item da proposta do evento.
    """
    try:
        evento = get_object_or_404(EventoVenda, id=evento_id, is_active=True)
        item = get_object_or_404(ItemPedidoVenda, id=item_id, pedido=evento.pedido, is_active=True)
        
        item.is_active = False
        item.save()
        
        # Recalcula total do pedido
        evento.pedido.recalcular_total()
        
        return JsonResponse({
            'sucesso': True,
            'mensagem': 'Item removido com sucesso'
        })
    
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def faturar_evento(request, evento_id):
    """
    Fatura o evento, criando NF-e se necessário.
    
    TODO: Integrar com SEFAZ-BA para emissão real de NF-e
    """
    try:
        evento = get_object_or_404(EventoVenda, id=evento_id, is_active=True)
        
        # Usa o serviço para faturar
        nota_fiscal = faturar_evento_com_nfe(evento, usuario=request.user)
        
        return JsonResponse({
            'sucesso': True,
            'mensagem': f'Evento faturado com sucesso! NF-e {nota_fiscal.numero}/{nota_fiscal.serie} criada.',
            'pedido_id': evento.pedido.id,
            'nota_fiscal_id': nota_fiscal.id,
            'nota_fiscal_numero': nota_fiscal.numero
        })
    
    except ValueError as e:
        return JsonResponse({'erro': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)


@login_required
def lista_eventos(request):
    """
    Lista de eventos com filtros.
    """
    eventos = EventoVenda.objects.filter(is_active=True).select_related(
        'empresa', 'loja', 'cliente', 'pedido'
    ).prefetch_related('equipe_responsavel')
    
    # Filtros
    status_filter = request.GET.get('status')
    tipo_filter = request.GET.get('tipo_evento')
    loja_filter = request.GET.get('loja')
    search = request.GET.get('search')
    
    if status_filter:
        eventos = eventos.filter(status=status_filter)
    if tipo_filter:
        eventos = eventos.filter(tipo_evento=tipo_filter)
    if loja_filter:
        eventos = eventos.filter(loja_id=loja_filter)
    if search:
        eventos = eventos.filter(
            nome_evento__icontains=search
        ) | eventos.filter(
            responsavel_evento__icontains=search
        )
    
    # Ordenação
    eventos = eventos.order_by('-data_evento', '-created_at')
    
    # Buscar lojas para filtro
    from core.models import Loja
    lojas = Loja.objects.filter(is_active=True)
    
    context = {
        'eventos': eventos,
        'lojas': lojas,
        'status_choices': EventoVenda.STATUS_CHOICES,
        'tipo_choices': EventoVenda.TIPO_EVENTO_CHOICES,
        'filtros': {
            'status': status_filter,
            'tipo_evento': tipo_filter,
            'loja': loja_filter,
            'search': search,
        }
    }
    
    return render(request, 'eventos/lista_eventos.html', context)


@login_required
def detalhes_evento(request, evento_id):
    """
    Detalhes completos do evento.
    """
    evento = get_object_or_404(
        EventoVenda.objects.select_related(
            'empresa', 'loja', 'cliente', 'lead', 'pedido'
        ).prefetch_related('equipe_responsavel'),
        id=evento_id,
        is_active=True
    )
    
    # Buscar pedido e itens se existir
    pedido = evento.pedido
    itens_pedido = []
    if pedido:
        itens_pedido = pedido.itens.filter(is_active=True).select_related('produto')
    
    # Buscar notas fiscais relacionadas
    notas_fiscais = []
    if pedido:
        from fiscal.models import NotaFiscalSaida
        notas_fiscais = NotaFiscalSaida.objects.filter(
            pedido_venda=pedido,
            is_active=True
        ).order_by('-data_emissao')
    
    context = {
        'evento': evento,
        'pedido': pedido,
        'itens_pedido': itens_pedido,
        'notas_fiscais': notas_fiscais,
    }
    
    return render(request, 'eventos/detalhes_evento.html', context)


@login_required
def criar_evento(request):
    """
    Cria um novo evento.
    """
    from core.models import Empresa, Loja
    from pessoas.models import Cliente
    from crm.models import Lead
    from vendas.models import CondicaoPagamento
    
    empresas = Empresa.objects.filter(is_active=True)
    lojas = Loja.objects.filter(is_active=True)
    clientes = Cliente.objects.filter(is_active=True)
    leads = Lead.objects.filter(is_active=True, status__in=['NOVO', 'EM_ANDAMENTO'])
    
    if request.method == 'POST':
        try:
            # Processar formulário
            evento = EventoVenda.objects.create(
                empresa_id=request.POST.get('empresa'),
                loja_id=request.POST.get('loja'),
                lead_id=request.POST.get('lead') or None,
                cliente_id=request.POST.get('cliente') or None,
                nome_evento=request.POST.get('nome_evento'),
                tipo_evento=request.POST.get('tipo_evento'),
                data_evento=request.POST.get('data_evento'),
                hora_evento=request.POST.get('hora_evento') or None,
                endereco_logradouro=request.POST.get('endereco_logradouro'),
                endereco_numero=request.POST.get('endereco_numero'),
                endereco_complemento=request.POST.get('endereco_complemento') or None,
                endereco_bairro=request.POST.get('endereco_bairro'),
                endereco_cidade=request.POST.get('endereco_cidade'),
                endereco_uf=request.POST.get('endereco_uf'),
                endereco_cep=request.POST.get('endereco_cep'),
                estimativa_publico=request.POST.get('estimativa_publico') or None,
                responsavel_evento=request.POST.get('responsavel_evento'),
                telefone_responsavel=request.POST.get('telefone_responsavel'),
                status=request.POST.get('status', 'RASCUNHO'),
                observacoes=request.POST.get('observacoes') or None,
                created_by=request.user,
            )
            
            # Adicionar equipe responsável
            equipe_ids = request.POST.getlist('equipe_responsavel')
            if equipe_ids:
                evento.equipe_responsavel.set(equipe_ids)
            
            return redirect('eventos:detalhes_evento', evento_id=evento.id)
        
        except Exception as e:
            context = {
                'empresas': empresas,
                'lojas': lojas,
                'clientes': clientes,
                'leads': leads,
                'erro': str(e),
                'form_data': request.POST,
            }
            return render(request, 'eventos/criar_evento.html', context)
    
    context = {
        'empresas': empresas,
        'lojas': lojas,
        'clientes': clientes,
        'leads': leads,
        'status_choices': EventoVenda.STATUS_CHOICES,
        'tipo_choices': EventoVenda.TIPO_EVENTO_CHOICES,
    }
    
    return render(request, 'eventos/criar_evento.html', context)


@login_required
@require_http_methods(["POST"])
def gerar_pedido_evento_view(request, pk):
    """
    View para gerar/abrir pedido de venda do evento.
    
    Se o evento já tiver pedido, redireciona para o admin do pedido.
    Se não tiver, cria o pedido e redireciona para o admin.
    
    TODO: No futuro, substituir redirecionamento ao admin por tela própria do Guardião.
    TODO: Adicionar restrição por grupo: ADMIN, GERENTE, FISCAL.
    """
    try:
        evento = get_object_or_404(EventoVenda, pk=pk, is_active=True)
        
        # Se já tem pedido, redireciona para o admin do pedido
        if evento.pedido:
            messages.info(request, f'Evento já possui pedido #{evento.pedido.id} associado.')
            admin_url = reverse('admin:vendas_pedidovenda_change', args=[evento.pedido.id])
            return redirect(admin_url)
        
        # Cria o pedido
        pedido = evento.gerar_pedido_evento()
        messages.success(request, f'Pedido de venda #{pedido.id} criado com sucesso para o evento "{evento.nome_evento}".')
        
        # Redireciona para o admin do pedido
        admin_url = reverse('admin:vendas_pedidovenda_change', args=[pedido.id])
        return redirect(admin_url)
    
    except Exception as e:
        messages.error(request, f'Erro ao gerar pedido: {str(e)}')
        return redirect('eventos:detalhes_evento', evento_id=pk)


@login_required
@require_http_methods(["POST"])
def gerar_nfe_evento_view(request, pk):
    """
    View para gerar NF-e rascunho do evento.
    
    Verifica se o evento tem pedido. Se tiver, cria NF-e rascunho e redireciona para o admin.
    
    TODO: No futuro, substituir redirecionamento ao admin por tela própria do Guardião.
    TODO: Integrar com SEFAZ para emissão real da NF-e.
    TODO: Adicionar restrição por grupo: ADMIN, GERENTE, FISCAL.
    """
    from fiscal.services import criar_nfe_rascunho_para_pedido_evento
    
    try:
        evento = get_object_or_404(EventoVenda, pk=pk, is_active=True)
        
        # Verifica se tem pedido
        if not evento.pedido:
            messages.error(
                request,
                'Evento não possui pedido associado. Crie o pedido primeiro usando a ação "Gerar Pedido".'
            )
            return redirect('eventos:detalhes_evento', evento_id=pk)
        
        # Verifica se já existe NF-e para este pedido
        from fiscal.models import NotaFiscalSaida
        nota_existente = NotaFiscalSaida.objects.filter(
            pedido_venda=evento.pedido,
            tipo_documento='NFE',
            is_active=True
        ).first()
        
        if nota_existente:
            # Se já existe, redireciona para a existente
            messages.info(
                request,
                f'Já existe uma NF-e {nota_existente.numero}/{nota_existente.serie} para este pedido.'
            )
            admin_url = reverse('admin:fiscal_notafiscalsaida_change', args=[nota_existente.id])
            return redirect(admin_url)
        
        # Cria a NF-e rascunho
        nota = criar_nfe_rascunho_para_pedido_evento(evento.pedido)
        messages.success(
            request,
            f'NF-e RASCUNHO {nota.numero}/{nota.serie} criada com sucesso para o evento "{evento.nome_evento}".'
        )
        
        # Redireciona para o admin da nota fiscal
        admin_url = reverse('admin:fiscal_notafiscalsaida_change', args=[nota.id])
        return redirect(admin_url)
    
    except ValidationError as e:
        messages.error(request, f'Erro de validação: {str(e)}')
        return redirect('eventos:detalhes_evento', evento_id=pk)
    except Exception as e:
        messages.error(request, f'Erro ao gerar NF-e: {str(e)}')
        return redirect('eventos:detalhes_evento', evento_id=pk)
