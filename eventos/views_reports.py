"""
Views de relatórios e dashboard de eventos.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import datetime, timedelta
from .models import EventoVenda
from .reports import (
    relatorio_eventos_por_periodo,
    relatorio_eventos_por_tipo,
    dashboard_eventos_em_execucao
)


@login_required
def dashboard_eventos(request):
    """
    Dashboard de eventos em execução.
    """
    # TODO: Obter empresa/loja do usuário ou da sessão
    empresa = None
    loja = None
    
    dados = dashboard_eventos_em_execucao(empresa=empresa, loja=loja)
    
    context = {
        'dados': dados,
    }
    
    return render(request, 'eventos/dashboard.html', context)


@login_required
@require_http_methods(["GET"])
def relatorio_eventos_periodo(request):
    """
    API para relatório de eventos por período.
    
    GET /eventos/relatorio/periodo/?data_inicio=2024-01-01&data_fim=2024-12-31
    """
    try:
        data_inicio_str = request.GET.get('data_inicio')
        data_fim_str = request.GET.get('data_fim')
        empresa_id = request.GET.get('empresa_id')
        loja_id = request.GET.get('loja_id')
        
        if not data_inicio_str or not data_fim_str:
            return JsonResponse({'erro': 'data_inicio e data_fim são obrigatórios'}, status=400)
        
        data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
        data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
        
        empresa = None
        if empresa_id:
            from core.models import Empresa
            empresa = Empresa.objects.get(id=empresa_id)
        
        loja = None
        if loja_id:
            from core.models import Loja
            loja = Loja.objects.get(id=loja_id)
        
        relatorio = relatorio_eventos_por_periodo(
            data_inicio=data_inicio,
            data_fim=data_fim,
            empresa=empresa,
            loja=loja
        )
        
        return JsonResponse(relatorio)
    
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def relatorio_eventos_tipo(request):
    """
    API para relatório de eventos por tipo.
    
    GET /eventos/relatorio/tipo/?tipo_evento=SAO_JOAO
    """
    try:
        tipo_evento = request.GET.get('tipo_evento')
        empresa_id = request.GET.get('empresa_id')
        loja_id = request.GET.get('loja_id')
        
        if not tipo_evento:
            return JsonResponse({'erro': 'tipo_evento é obrigatório'}, status=400)
        
        empresa = None
        if empresa_id:
            from core.models import Empresa
            empresa = Empresa.objects.get(id=empresa_id)
        
        loja = None
        if loja_id:
            from core.models import Loja
            loja = Loja.objects.get(id=loja_id)
        
        relatorio = relatorio_eventos_por_tipo(
            tipo_evento=tipo_evento,
            empresa=empresa,
            loja=loja
        )
        
        return JsonResponse(relatorio)
    
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)

