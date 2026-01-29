"""
URLs do módulo PDV.
"""
from django.urls import path
from . import views, views_api

app_name = 'pdv'

urlpatterns = [
    path('', views.pdv_view, name='pdv'),
    path('abrir-caixa/', views.abrir_caixa, name='abrir_caixa'),
    path('fechar-caixa/', views.fechar_caixa, name='fechar_caixa'),
    path('fechar-caixa/<int:caixa_id>/', views.fechar_caixa, name='fechar_caixa_id'),
    path('buscar-produto/', views.buscar_produto, name='buscar_produto'),
    path('finalizar-venda/', views.finalizar_venda, name='finalizar_venda'),
    path('criar-orcamento/', views.criar_orcamento_pdv, name='criar_orcamento_pdv'),
    path('cupom-fiscal/<int:pedido_id>/', views.cupom_fiscal, name='cupom_fiscal'),
    path('cupom-fiscal/<int:pedido_id>/pdf/', views.cupom_fiscal_pdf, name='cupom_fiscal_pdf'),
    path('api/buscar-pedido-tablet/', views_api.buscar_pedido_tablet, name='buscar_pedido_tablet'),
    path('api/efetivar-pedido-tablet/', views_api.efetivar_pedido_tablet_view, name='efetivar_pedido_tablet'),
    path('api/verificar-caixa/', views_api.verificar_caixa_aberto, name='verificar_caixa'),
]

