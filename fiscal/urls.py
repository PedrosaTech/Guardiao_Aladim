"""
URLs do módulo fiscal.
"""
from django.urls import path
from . import views

app_name = 'fiscal'

urlpatterns = [
    # Notas Fiscais de Saída
    path('notas-saida/', views.lista_notas_saida, name='lista_notas_saida'),
    path('notas-saida/detalhes/<int:nota_id>/', views.detalhes_nota_saida, name='detalhes_nota_saida'),
    
    # Notas Fiscais de Entrada
    path('notas-entrada/', views.lista_notas_entrada, name='lista_notas_entrada'),
    path('notas-entrada/detalhes/<int:nota_id>/', views.detalhes_nota_entrada, name='detalhes_nota_entrada'),
    
    # PDF
    path('nfe/<int:nota_id>/pdf/', views.imprimir_nfe_pdf, name='imprimir_nfe_pdf'),
]

