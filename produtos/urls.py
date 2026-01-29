"""
URLs do módulo produtos.
"""
from django.urls import path
from . import views

app_name = 'produtos'

urlpatterns = [
    path('', views.lista_produtos, name='lista_produtos'),
    path('criar/', views.criar_produto, name='criar_produto'),
    path('detalhes/<int:produto_id>/', views.detalhes_produto, name='detalhes_produto'),
    # API (mais específicas primeiro)
    path(
        'api/codigo-alternativo/criar/<int:produto_id>/',
        views.codigo_alternativo_criar,
        name='codigo_alternativo_criar',
    ),
    path(
        'api/codigo-alternativo/editar/<int:codigo_id>/',
        views.codigo_alternativo_editar,
        name='codigo_alternativo_editar',
    ),
    path(
        'api/codigo-alternativo/inativar/<int:codigo_id>/',
        views.codigo_alternativo_inativar,
        name='codigo_alternativo_inativar',
    ),
    # Páginas
    path('editar/<int:produto_id>/', views.produto_editar, name='produto_editar'),
    path('inativar/<int:produto_id>/', views.produto_inativar, name='produto_inativar'),
    path(
        '<int:produto_id>/codigos-alternativos/',
        views.produto_codigos_alternativos,
        name='produto_codigos_alternativos',
    ),
]
