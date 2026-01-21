"""
URLs do módulo PDV.
"""
from django.urls import path
from . import views

app_name = 'pdv'

urlpatterns = [
    path('', views.pdv_view, name='pdv'),
    path('abrir-caixa/', views.abrir_caixa, name='abrir_caixa'),
    path('fechar-caixa/', views.fechar_caixa, name='fechar_caixa'),
    path('fechar-caixa/<int:caixa_id>/', views.fechar_caixa, name='fechar_caixa_id'),
    path('buscar-produto/', views.buscar_produto, name='buscar_produto'),
    path('finalizar-venda/', views.finalizar_venda, name='finalizar_venda'),
    path('criar-orcamento/', views.criar_orcamento_pdv, name='criar_orcamento_pdv'),
]

