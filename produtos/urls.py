"""
URLs do módulo produtos.
"""
from django.urls import path
from . import views

app_name = 'produtos'

urlpatterns = [
    # Listagem e CRUD
    path('', views.lista_produtos, name='lista_produtos'),
    path('criar/', views.criar_produto, name='criar_produto'),
    path('detalhes/<int:produto_id>/', views.detalhes_produto, name='detalhes_produto'),
]

