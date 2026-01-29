"""
URLs da API do PDV Móvel + Frontend Tablet.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api.viewsets import ProdutosPDVViewSet, PedidosPDVViewSet, CaixaPDVViewSet
from . import views

app_name = "pdv_movel"

router = DefaultRouter()
router.register(r"produtos", ProdutosPDVViewSet, basename="produtos")
router.register(r"pedidos", PedidosPDVViewSet, basename="pedidos")
router.register(r"caixa", CaixaPDVViewSet, basename="caixa")

# Rota explícita para adicionar_item (evita 404 com o router em alguns ambientes)
adicionar_item_view = PedidosPDVViewSet.as_view(actions={"post": "adicionar_item"})

urlpatterns = [
    path("api/pedidos/<int:pk>/adicionar_item/", adicionar_item_view, name="pedidos-adicionar-item"),
    path("api/", include(router.urls)),
    path("sw.js", views.sw_js, name="sw_js"),
    path("", views.login_pin, name="login_pin"),
    path("login/", views.login_pin, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("pedido/novo/", views.pedido_novo, name="pedido_novo"),
    path("pedidos/", views.pedido_lista, name="pedido_lista"),
]
