"""
Relatórios de eventos.
"""
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from .models import EventoVenda


def relatorio_eventos_por_periodo(data_inicio, data_fim, empresa=None, loja=None):
    """
    Relatório de eventos por período.
    
    Args:
        data_inicio: Data de início (datetime ou date)
        data_fim: Data de fim (datetime ou date)
        empresa: Empresa (opcional)
        loja: Loja (opcional)
    
    Returns:
        dict com estatísticas dos eventos
    """
    eventos = EventoVenda.objects.filter(
        is_active=True,
        data_evento__gte=data_inicio,
        data_evento__lte=data_fim
    )
    
    if empresa:
        eventos = eventos.filter(empresa=empresa)
    if loja:
        eventos = eventos.filter(loja=loja)
    
    total_eventos = eventos.count()
    eventos_por_tipo = eventos.values('tipo_evento').annotate(
        total=Count('id')
    )
    eventos_por_status = eventos.values('status').annotate(
        total=Count('id')
    )
    
    # Eventos com pedidos
    eventos_com_pedido = eventos.filter(pedido__isnull=False)
    total_faturado = eventos_com_pedido.aggregate(
        total=Sum('pedido__valor_total')
    )['total'] or Decimal('0.00')
    
    # Eventos concluídos
    eventos_concluidos = eventos.filter(status='CONCLUIDO')
    
    return {
        'periodo': {
            'inicio': data_inicio,
            'fim': data_fim
        },
        'total_eventos': total_eventos,
        'eventos_por_tipo': list(eventos_por_tipo),
        'eventos_por_status': list(eventos_por_status),
        'total_faturado': total_faturado,
        'eventos_concluidos': eventos_concluidos.count(),
        'eventos_com_pedido': eventos_com_pedido.count(),
    }


def relatorio_eventos_por_tipo(tipo_evento, empresa=None, loja=None):
    """
    Relatório de eventos por tipo.
    
    Args:
        tipo_evento: Tipo de evento
        empresa: Empresa (opcional)
        loja: Loja (opcional)
    
    Returns:
        dict com estatísticas
    """
    eventos = EventoVenda.objects.filter(
        is_active=True,
        tipo_evento=tipo_evento
    )
    
    if empresa:
        eventos = eventos.filter(empresa=empresa)
    if loja:
        eventos = eventos.filter(loja=loja)
    
    total = eventos.count()
    eventos_por_status = eventos.values('status').annotate(
        total=Count('id')
    )
    
    eventos_com_pedido = eventos.filter(pedido__isnull=False)
    total_faturado = eventos_com_pedido.aggregate(
        total=Sum('pedido__valor_total')
    )['total'] or Decimal('0.00')
    
    return {
        'tipo_evento': tipo_evento,
        'total_eventos': total,
        'eventos_por_status': list(eventos_por_status),
        'total_faturado': total_faturado,
        'eventos_com_pedido': eventos_com_pedido.count(),
    }


def dashboard_eventos_em_execucao(empresa=None, loja=None):
    """
    Dashboard de eventos em execução.
    
    Args:
        empresa: Empresa (opcional)
        loja: Loja (opcional)
    
    Returns:
        dict com dados do dashboard
    """
    hoje = timezone.now().date()
    
    # Eventos em execução (status EM_EXECUCAO ou data do evento >= hoje)
    eventos_execucao = EventoVenda.objects.filter(
        is_active=True
    ).filter(
        Q(status='EM_EXECUCAO') | Q(data_evento__gte=hoje)
    )
    
    if empresa:
        eventos_execucao = eventos_execucao.filter(empresa=empresa)
    if loja:
        eventos_execucao = eventos_execucao.filter(loja=loja)
    
    # Próximos eventos (próximos 30 dias)
    proximos_30_dias = hoje + timedelta(days=30)
    proximos_eventos = eventos_execucao.filter(
        data_evento__gte=hoje,
        data_evento__lte=proximos_30_dias
    ).order_by('data_evento')[:10]
    
    # Eventos hoje
    eventos_hoje = eventos_execucao.filter(data_evento=hoje)
    
    # Eventos esta semana
    fim_semana = hoje + timedelta(days=7)
    eventos_semana = eventos_execucao.filter(
        data_evento__gte=hoje,
        data_evento__lte=fim_semana
    )
    
    # Estatísticas
    total_em_execucao = eventos_execucao.count()
    eventos_por_tipo = eventos_execucao.values('tipo_evento').annotate(
        total=Count('id')
    )
    
    return {
        'total_em_execucao': total_em_execucao,
        'eventos_hoje': eventos_hoje.count(),
        'eventos_semana': eventos_semana.count(),
        'proximos_eventos': list(proximos_eventos.values(
            'id', 'nome_evento', 'tipo_evento', 'data_evento', 'status'
        )),
        'eventos_por_tipo': list(eventos_por_tipo),
        'eventos_hoje_lista': list(eventos_hoje.values(
            'id', 'nome_evento', 'tipo_evento', 'hora_evento', 'status'
        )),
    }

