"""
URLs do módulo pessoas.
"""
from django.urls import path
from . import views

app_name = 'pessoas'

urlpatterns = [
    # Clientes
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/criar/', views.criar_cliente, name='criar_cliente'),
    path('clientes/detalhes/<int:cliente_id>/', views.detalhes_cliente, name='detalhes_cliente'),
    
    # Fornecedores
    path('fornecedores/', views.lista_fornecedores, name='lista_fornecedores'),
    path('fornecedores/criar/', views.criar_fornecedor, name='criar_fornecedor'),
    path('fornecedores/detalhes/<int:fornecedor_id>/', views.detalhes_fornecedor, name='detalhes_fornecedor'),
]

