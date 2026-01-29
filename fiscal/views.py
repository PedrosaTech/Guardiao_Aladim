"""
Views do módulo fiscal.
"""
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.template.loader import render_to_string
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
from .models import NotaFiscalSaida, NotaFiscalEntrada, ConfiguracaoFiscalLoja

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False


@login_required
def lista_notas_saida(request):
    """
    Lista de notas fiscais de saída (NF-e e NFC-e).
    """
    notas = NotaFiscalSaida.objects.filter(is_active=True).select_related(
        'loja', 'cliente', 'pedido_venda', 'evento'
    )
    
    # Filtros
    tipo_documento_filter = request.GET.get('tipo_documento')
    status_filter = request.GET.get('status')
    loja_filter = request.GET.get('loja')
    cliente_filter = request.GET.get('cliente')
    evento_filter = request.GET.get('evento')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    search = request.GET.get('search')
    
    if tipo_documento_filter:
        notas = notas.filter(tipo_documento=tipo_documento_filter)
    if status_filter:
        notas = notas.filter(status=status_filter)
    if loja_filter:
        notas = notas.filter(loja_id=loja_filter)
    if cliente_filter:
        notas = notas.filter(cliente_id=cliente_filter)
    if evento_filter:
        notas = notas.filter(evento_id=evento_filter)
    if data_inicio:
        try:
            data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
            notas = notas.filter(data_emissao__gte=data_inicio_dt)
        except:
            pass
    if data_fim:
        try:
            data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d') + timedelta(days=1)
            notas = notas.filter(data_emissao__lt=data_fim_dt)
        except:
            pass
    if search:
        notas = notas.filter(
            Q(numero__icontains=search) |
            Q(chave_acesso__icontains=search) |
            Q(cliente__nome_razao_social__icontains=search)
        )
    
    # Ordenação
    notas = notas.order_by('-data_emissao', '-numero')
    
    # Buscar dados para filtros
    from core.models import Loja
    from pessoas.models import Cliente
    from eventos.models import EventoVenda
    
    lojas = Loja.objects.filter(is_active=True)
    clientes = Cliente.objects.filter(is_active=True)
    eventos = EventoVenda.objects.filter(is_active=True)
    
    # Estatísticas
    total_valor = notas.aggregate(Sum('valor_total'))['valor_total__sum'] or 0
    total_notas = notas.count()
    
    context = {
        'notas': notas,
        'lojas': lojas,
        'clientes': clientes,
        'eventos': eventos,
        'total_valor': total_valor,
        'total_notas': total_notas,
        'filtros': {
            'tipo_documento': tipo_documento_filter,
            'status': status_filter,
            'loja': loja_filter,
            'cliente': cliente_filter,
            'evento': evento_filter,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'search': search,
        }
    }
    
    return render(request, 'fiscal/lista_notas_saida.html', context)


@login_required
def detalhes_nota_saida(request, nota_id):
    """
    Detalhes completos da nota fiscal de saída.
    """
    nota = get_object_or_404(
        NotaFiscalSaida.objects.select_related(
            'loja', 'cliente', 'pedido_venda', 'evento'
        ),
        id=nota_id,
        is_active=True
    )
    
    # Buscar configuração fiscal
    config_fiscal = None
    try:
        config_fiscal = nota.loja.configuracao_fiscal
    except:
        pass
    
    # Obter impostos (usa snapshot se autorizada, senão calcula)
    impostos = nota.get_impostos()
    
    # Calcular impostos por item para exibição
    itens_com_impostos = []
    
    if nota.pedido_venda:
        itens = nota.pedido_venda.itens.filter(is_active=True).select_related('produto')
        
        for item in itens:
            # Se autorizada, buscar do snapshot
            if nota.status == 'AUTORIZADA' and nota.impostos_snapshot:
                item_snapshot = next(
                    (s for s in nota.impostos_snapshot if s['item_id'] == item.id),
                    None
                )
                if item_snapshot:
                    impostos_item = item_snapshot['impostos']
                    # Converter valores de volta para Decimal
                    from decimal import Decimal
                    impostos_item = {
                        k: Decimal(str(v)) if isinstance(v, (int, float)) else v
                        for k, v in impostos_item.items()
                    }
                else:
                    # Fallback: calcular
                    from fiscal.calculos import calcular_impostos_item
                    regime = config_fiscal.regime_tributario if config_fiscal else None
                    impostos_item = calcular_impostos_item(item, regime, config_fiscal)
            else:
                # Calcular em tempo real
                from fiscal.calculos import calcular_impostos_item
                regime = config_fiscal.regime_tributario if config_fiscal else None
                impostos_item = calcular_impostos_item(item, regime, config_fiscal)
            
            # Helper para descrição
            if hasattr(item, 'get_descricao'):
                descricao = item.get_descricao()
            elif item.produto:
                descricao = item.produto.descricao
            elif hasattr(item, 'servico') and item.servico:
                descricao = item.servico.nome
            else:
                descricao = 'Item'
            
            itens_com_impostos.append({
                'item': item,
                'descricao': descricao,
                'quantidade': item.quantidade,
                'valor_unitario': item.preco_unitario,
                'total': item.total,
                'impostos': impostos_item,
                'eh_produto': item.produto is not None,
                'eh_servico': hasattr(item, 'servico') and item.servico is not None,
            })
    
    context = {
        'nota': nota,
        'itens': itens_com_impostos,  # ← Agora com impostos por item
        'config_fiscal': config_fiscal,
        'impostos': impostos,  # ← Totais
    }
    
    return render(request, 'fiscal/detalhes_nota_saida.html', context)


@login_required
def lista_notas_entrada(request):
    """
    Lista de notas fiscais de entrada.
    """
    notas = NotaFiscalEntrada.objects.filter(is_active=True).select_related(
        'loja', 'fornecedor'
    )
    
    # Filtros
    loja_filter = request.GET.get('loja')
    fornecedor_filter = request.GET.get('fornecedor')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    search = request.GET.get('search')
    
    if loja_filter:
        notas = notas.filter(loja_id=loja_filter)
    if fornecedor_filter:
        notas = notas.filter(fornecedor_id=fornecedor_filter)
    if data_inicio:
        try:
            data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
            notas = notas.filter(data_entrada__gte=data_inicio_dt)
        except:
            pass
    if data_fim:
        try:
            data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d') + timedelta(days=1)
            notas = notas.filter(data_entrada__lt=data_fim_dt)
        except:
            pass
    if search:
        notas = notas.filter(
            Q(numero__icontains=search) |
            Q(chave_acesso__icontains=search) |
            Q(fornecedor__razao_social__icontains=search)
        )
    
    # Ordenação
    notas = notas.order_by('-data_entrada', '-numero')
    
    # Buscar dados para filtros
    from core.models import Loja
    from pessoas.models import Fornecedor
    
    lojas = Loja.objects.filter(is_active=True)
    fornecedores = Fornecedor.objects.filter(is_active=True)
    
    # Estatísticas
    total_valor = notas.aggregate(Sum('valor_total'))['valor_total__sum'] or 0
    total_notas = notas.count()
    
    context = {
        'notas': notas,
        'lojas': lojas,
        'fornecedores': fornecedores,
        'total_valor': total_valor,
        'total_notas': total_notas,
        'filtros': {
            'loja': loja_filter,
            'fornecedor': fornecedor_filter,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'search': search,
        }
    }
    
    return render(request, 'fiscal/lista_notas_entrada.html', context)


@login_required
def detalhes_nota_entrada(request, nota_id):
    """
    Detalhes completos da nota fiscal de entrada.
    """
    nota = get_object_or_404(
        NotaFiscalEntrada.objects.select_related(
            'loja', 'fornecedor'
        ),
        id=nota_id,
        is_active=True
    )
    
    context = {
        'nota': nota,
    }
    
    return render(request, 'fiscal/detalhes_nota_entrada.html', context)


@login_required
def imprimir_nfe_pdf(request, nota_id):
    """
    Gera PDF da NF-e no layout SEFAZ-BA.
    
    Requer weasyprint instalado: pip install weasyprint
    """
    if not WEASYPRINT_AVAILABLE:
        return HttpResponse(
            '<h1>Erro: WeasyPrint não instalado</h1>'
            '<p>Para gerar PDFs, instale o weasyprint:</p>'
            '<pre>pip install weasyprint</pre>',
            status=500
        )
    
    nota = get_object_or_404(NotaFiscalSaida, id=nota_id, is_active=True)
    
    # Buscar dados relacionados
    pedido = nota.pedido_venda
    itens = []
    if pedido:
        itens = pedido.itens.filter(is_active=True).select_related('produto')
    
    # Buscar configuração fiscal da loja
    config_fiscal = None
    regime_tributario = None
    try:
        config_fiscal = nota.loja.configuracao_fiscal
        if config_fiscal:
            regime_tributario = config_fiscal.regime_tributario
    except:
        pass
    
    # Calcular impostos conforme normas SEFAZ-BA
    # IMPORTANTE: Para Simples Nacional, os impostos não são calculados separadamente
    # Usar get_impostos() que já considera snapshot se autorizada
    impostos = nota.get_impostos()
    
    # Preparar contexto
    context = {
        'nota': nota,
        'loja': nota.loja,
        'empresa': nota.loja.empresa,
        'cliente': nota.cliente,
        'pedido': pedido,
        'itens': itens,
        'config_fiscal': config_fiscal,
        'impostos': impostos,
    }
    
    # Renderizar template HTML
    html_string = render_to_string('fiscal/nfe_pdf.html', context)
    
    # Gerar PDF
    html = HTML(string=html_string)
    pdf = html.write_pdf()
    
    # Retornar PDF como resposta
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="NF-e_{nota.numero}_{nota.serie}.pdf"'
    
    return response

