"""
URLs do módulo financeiro.
"""
from django.urls import path
from . import views

app_name = 'financeiro'

urlpatterns = [
    path('', views.DashboardFinanceiroView.as_view(), name='dashboard'),
    path('receber/', views.TituloReceberListView.as_view(), name='titulos_receber'),
    path('receber/criar/', views.TituloReceberCreateView.as_view(), name='titulo_receber_criar'),
    path('receber/<int:pk>/', views.TituloReceberDetailView.as_view(), name='titulo_receber_detail'),
    path('receber/<int:pk>/editar/', views.TituloReceberUpdateView.as_view(), name='titulo_receber_editar'),
    path('receber/<int:pk>/baixar/', views.baixar_titulo_receber, name='titulo_receber_baixar'),
    path('pagar/', views.TituloPagarListView.as_view(), name='titulos_pagar'),
    path('pagar/criar/', views.TituloPagarCreateView.as_view(), name='titulo_pagar_criar'),
    path('pagar/<int:pk>/', views.TituloPagarDetailView.as_view(), name='titulo_pagar_detail'),
    path('pagar/<int:pk>/editar/', views.TituloPagarUpdateView.as_view(), name='titulo_pagar_editar'),
    path('pagar/<int:pk>/baixar/', views.baixar_titulo_pagar, name='titulo_pagar_baixar'),
    path('relatorio/fluxo-caixa/', views.RelatorioFluxoCaixaView.as_view(), name='relatorio_fluxo_caixa'),
]

