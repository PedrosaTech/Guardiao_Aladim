"""
Admin para modelos de vendas.
"""
from django.contrib import admin
from .models import CondicaoPagamento, PedidoVenda, ItemPedidoVenda


@admin.register(CondicaoPagamento)
class CondicaoPagamentoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'empresa', 'numero_parcelas', 'dias_entre_parcelas', 'is_active']
    list_filter = ['empresa', 'is_active']
    search_fields = ['nome', 'descricao']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


class ItemPedidoVendaInline(admin.TabularInline):
    model = ItemPedidoVenda
    extra = 1
    fields = [
        'produto',
        'quantidade',
        'preco_unitario',
        'desconto',
        'total',
        'codigo_barras_usado',
        'codigo_alternativo_usado',
        'multiplicador_aplicado',
        'is_active',
    ]
    readonly_fields = ['total']


@admin.register(PedidoVenda)
class PedidoVendaAdmin(admin.ModelAdmin):
    list_display = ['id', 'cliente', 'loja', 'tipo_venda', 'status', 'origem', 'valor_total', 'vendedor', 'data_emissao']
    list_filter = ['status', 'tipo_venda', 'origem', 'loja', 'data_emissao']
    search_fields = ['id', 'cliente__nome_razao_social', 'observacoes']
    readonly_fields = ['data_emissao', 'created_at', 'updated_at', 'created_by', 'updated_by']
    date_hierarchy = 'data_emissao'
    inlines = [ItemPedidoVendaInline]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('loja', 'cliente', 'tipo_venda', 'status', 'vendedor')
        }),
        ('PDV Móvel', {
            'fields': ('origem', 'atendente_tablet'),
        }),
        ('Pagamento', {
            'fields': ('condicao_pagamento', 'valor_total')
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
        ('Controle', {
            'fields': ('data_emissao', 'is_active', 'created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )


@admin.register(ItemPedidoVenda)
class ItemPedidoVendaAdmin(admin.ModelAdmin):
    list_display = [
        'pedido',
        'produto',
        'quantidade',
        'multiplicador_aplicado',
        'codigo_barras_usado',
        'codigo_alternativo_usado',
        'preco_unitario',
        'desconto',
        'total',
    ]
    list_filter = ['pedido__status', 'pedido__loja']
    search_fields = ['pedido__id', 'produto__codigo_interno', 'produto__descricao']
    readonly_fields = ['total', 'created_at', 'updated_at', 'created_by', 'updated_by']

