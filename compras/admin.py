"""
Admin para modelos de compras.
"""
from django.contrib import admin
from .models import PedidoCompra, ItemPedidoCompra


class ItemPedidoCompraInline(admin.TabularInline):
    model = ItemPedidoCompra
    extra = 1
    fields = ['produto', 'quantidade', 'preco_unitario', 'total', 'is_active']
    readonly_fields = ['total']


@admin.register(PedidoCompra)
class PedidoCompraAdmin(admin.ModelAdmin):
    list_display = ['id', 'fornecedor', 'loja', 'status', 'valor_total', 'data_emissao']
    list_filter = ['status', 'loja', 'data_emissao']
    search_fields = ['id', 'fornecedor__razao_social', 'observacoes']
    readonly_fields = ['data_emissao', 'created_at', 'updated_at', 'created_by', 'updated_by']
    date_hierarchy = 'data_emissao'
    inlines = [ItemPedidoCompraInline]


@admin.register(ItemPedidoCompra)
class ItemPedidoCompraAdmin(admin.ModelAdmin):
    list_display = ['pedido', 'produto', 'quantidade', 'preco_unitario', 'total']
    list_filter = ['pedido__status', 'pedido__loja']
    search_fields = ['pedido__id', 'produto__codigo_interno', 'produto__descricao']
    readonly_fields = ['total', 'created_at', 'updated_at', 'created_by', 'updated_by']

