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
    path('notas-entrada/criar/', views.criar_nota_entrada, name='criar_nota_entrada'),
    path('notas-entrada/importar-xml/', views.importar_nota_entrada_xml, name='importar_nota_entrada_xml'),
    path('notas-entrada/importar-xml/confirmar/', views.importar_nota_entrada_confirmar, name='importar_nota_entrada_confirmar'),
    path('notas-entrada/detalhes/<int:nota_id>/', views.detalhes_nota_entrada, name='detalhes_nota_entrada'),
    path('notas-entrada/detalhes/<int:nota_id>/dar-entrada-estoque/', views.dar_entrada_estoque_nota_view, name='dar_entrada_estoque_nota'),
    
    # Alertas SEFAZ-BA
    path('alertas-sefaz/', views.lista_alertas_sefaz, name='lista_alertas_sefaz'),
    
    # PDF
    path('nfe/<int:nota_id>/pdf/', views.imprimir_nfe_pdf, name='imprimir_nfe_pdf'),
]

