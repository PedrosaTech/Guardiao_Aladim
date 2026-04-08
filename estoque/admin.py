"""
Admin para modelos de estoque.
"""
from django.contrib import admin
from .models import (
    EstoqueAtual,
    EstoqueValorado,
    LocalEstoque,
    MovimentoEstoque,
    TransferenciaInterempresa,
)


@admin.register(LocalEstoque)
class LocalEstoqueAdmin(admin.ModelAdmin):
    list_display = ['nome', 'loja', 'e_area_restrita', 'is_active']
    list_filter = ['loja', 'e_area_restrita', 'is_active']
    search_fields = ['nome', 'descricao']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


@admin.register(EstoqueAtual)
class EstoqueAtualAdmin(admin.ModelAdmin):
    list_display = ['produto', 'local_estoque', 'quantidade', 'is_active']
    list_filter = ['local_estoque', 'produto__categoria', 'is_active']
    search_fields = ['produto__codigo_interno', 'produto__descricao']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


@admin.register(EstoqueValorado)
class EstoqueValoradoAdmin(admin.ModelAdmin):
    list_display = ['produto', 'empresa', 'custo_medio', 'quantidade_total', 'atualizado_em']
    list_filter = ['empresa']
    search_fields = ['produto__codigo_interno', 'produto__descricao']
    readonly_fields = ['atualizado_em', 'created_at', 'updated_at', 'created_by', 'updated_by']


@admin.register(TransferenciaInterempresa)
class TransferenciaInterempresaAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'empresa_origem',
        'empresa_destino',
        'produto',
        'quantidade',
        'custo_unitario',
        'status',
        'created_at',
    ]
    list_filter = ['status', 'empresa_origem', 'empresa_destino']
    search_fields = ['produto__codigo_interno', 'produto__descricao']
    readonly_fields = [
        'movimento_saida',
        'movimento_entrada',
        'status',
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
    ]

    def has_add_permission(self, request):
        return False


@admin.register(MovimentoEstoque)
class MovimentoEstoqueAdmin(admin.ModelAdmin):
    list_display = ['produto', 'tipo_movimento', 'quantidade', 'custo_unitario', 'local_origem', 'local_destino', 'data_movimento']
    list_filter = ['tipo_movimento', 'data_movimento', 'produto__categoria']
    search_fields = ['produto__codigo_interno', 'produto__descricao', 'referencia', 'observacao']
    readonly_fields = ['data_movimento', 'created_at', 'updated_at', 'created_by', 'updated_by']
    date_hierarchy = 'data_movimento'

