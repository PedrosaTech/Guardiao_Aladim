"""
Admin para modelos de estoque.
"""
from django.contrib import admin
from .models import LocalEstoque, EstoqueAtual, MovimentoEstoque


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


@admin.register(MovimentoEstoque)
class MovimentoEstoqueAdmin(admin.ModelAdmin):
    list_display = ['produto', 'tipo_movimento', 'quantidade', 'local_origem', 'local_destino', 'data_movimento']
    list_filter = ['tipo_movimento', 'data_movimento', 'produto__categoria']
    search_fields = ['produto__codigo_interno', 'produto__descricao', 'referencia', 'observacao']
    readonly_fields = ['data_movimento', 'created_at', 'updated_at', 'created_by', 'updated_by']
    date_hierarchy = 'data_movimento'

