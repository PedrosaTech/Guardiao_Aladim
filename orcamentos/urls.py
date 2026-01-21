"""
URLs do módulo de orçamentos.
"""
from django.urls import path
from . import views

app_name = 'orcamentos'

urlpatterns = [
    # Listagem e CRUD
    path('', views.lista_orcamentos, name='lista_orcamentos'),
    path('criar/', views.criar_orcamento, name='criar_orcamento'),
    path('rapido/', views.orcamento_rapido, name='orcamento_rapido'),
    path('detalhes/<int:orcamento_id>/', views.detalhes_orcamento, name='detalhes_orcamento'),
    
    # API para orçamento rápido
    path('api/produtos/', views.buscar_produtos_rapido, name='api_produtos_rapido'),
    path('api/clientes/', views.buscar_clientes_rapido, name='api_clientes_rapido'),
    
    # Gerenciamento de Itens
    path('detalhes/<int:orcamento_id>/adicionar-item/', views.adicionar_item_orcamento, name='adicionar_item_orcamento'),
    path('detalhes/<int:orcamento_id>/editar-item/<int:item_id>/', views.editar_item_orcamento, name='editar_item_orcamento'),
    path('detalhes/<int:orcamento_id>/remover-item/<int:item_id>/', views.remover_item_orcamento, name='remover_item_orcamento'),
    
    # Ações
    path('detalhes/<int:orcamento_id>/pdf/', views.imprimir_orcamento_pdf, name='imprimir_orcamento_pdf'),
    path('detalhes/<int:orcamento_id>/converter/', views.converter_orcamento_pedido, name='converter_orcamento_pedido'),
    
    # Relatórios
    path('relatorio/', views.relatorio_orcamentos, name='relatorio_orcamentos'),
]

