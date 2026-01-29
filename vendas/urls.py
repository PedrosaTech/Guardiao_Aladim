"""
URLs do módulo de vendas.
"""
from django.urls import path
from . import views

app_name = 'vendas'

urlpatterns = [
    # Pedidos de Venda
    path('pedidos/', views.lista_pedidos, name='lista_pedidos'),
    path('pedidos/detalhes/<int:pedido_id>/', views.detalhes_pedido, name='detalhes_pedido'),
    path('pedidos/criar/', views.criar_pedido, name='criar_pedido'),
    path('pedidos/editar/<int:pedido_id>/', views.editar_pedido, name='editar_pedido'),
    
    # Itens do Pedido
    path('pedidos/<int:pedido_id>/adicionar-item/', views.adicionar_item_pedido, name='adicionar_item_pedido'),
    path('pedidos/<int:pedido_id>/editar-item/<int:item_id>/', views.editar_item_pedido, name='editar_item_pedido'),
    path('pedidos/<int:pedido_id>/remover-item/<int:item_id>/', views.remover_item_pedido, name='remover_item_pedido'),
    
    # Ações do Pedido
    path('pedidos/<int:pedido_id>/faturar/', views.faturar_pedido, name='faturar_pedido'),
    path('pedidos/<int:pedido_id>/cancelar/', views.cancelar_pedido, name='cancelar_pedido'),
    
    # APIs
    path('api/buscar-produtos/', views.buscar_produtos_rapido, name='buscar_produtos_rapido'),
    path('api/buscar-clientes/', views.buscar_clientes_rapido, name='buscar_clientes_rapido'),

    # Relatórios
    path('relatorios/vendas/', views.relatorio_vendas_consolidado, name='relatorio_vendas_consolidado'),
]




