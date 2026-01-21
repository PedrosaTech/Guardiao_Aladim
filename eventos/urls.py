"""
URLs do módulo eventos.
"""
from django.urls import path
from . import views

app_name = 'eventos'

from . import views_reports

urlpatterns = [
    # Listagem e CRUD
    path('', views.lista_eventos, name='lista_eventos'),
    path('criar/', views.criar_evento, name='criar_evento'),
    path('detalhes/<int:evento_id>/', views.detalhes_evento, name='detalhes_evento'),
    
    # Ações
    path('guardiao/eventos/<int:pk>/gerar-pedido/', views.gerar_pedido_evento_view, name='gerar_pedido_evento'),
    path('guardiao/eventos/<int:pk>/gerar-nfe/', views.gerar_nfe_evento_view, name='gerar_nfe_evento'),
    
    # Proposta
    path('proposta/<int:evento_id>/', views.proposta_evento, name='proposta_evento'),
    path('proposta/<int:evento_id>/adicionar-item/', views.adicionar_item_proposta, name='adicionar_item_proposta'),
    path('proposta/<int:evento_id>/remover-item/<int:item_id>/', views.remover_item_proposta, name='remover_item_proposta'),
    path('faturar/<int:evento_id>/', views.faturar_evento, name='faturar_evento'),
    
    # Relatórios
    path('dashboard/', views_reports.dashboard_eventos, name='dashboard_eventos'),
    path('relatorio/periodo/', views_reports.relatorio_eventos_periodo, name='relatorio_eventos_periodo'),
    path('relatorio/tipo/', views_reports.relatorio_eventos_tipo, name='relatorio_eventos_tipo'),
]

