"""
URLs do app core - cadastros administrativos (Empresa e Loja).
"""
from django.urls import path

from . import cadastro_views
from . import guia_views
from . import views

app_name = "core"

urlpatterns = [
    path("trocar-empresa/", views.trocar_empresa, name="trocar_empresa"),
    path("empresas/", cadastro_views.lista_empresas, name="lista_empresas"),
    path("empresas/nova/", cadastro_views.criar_empresa, name="criar_empresa"),
    path("empresas/<int:pk>/editar/", cadastro_views.editar_empresa, name="editar_empresa"),
    path("lojas/", cadastro_views.lista_lojas, name="lista_lojas"),
    path("lojas/nova/", cadastro_views.criar_loja, name="criar_loja"),
    path("lojas/<int:pk>/editar/", cadastro_views.editar_loja, name="editar_loja"),
    path("guias/", guia_views.lista_guias, name="lista_guias"),
    path("guias/<slug:slug>/", guia_views.detalhe_guia, name="detalhe_guia"),
]
