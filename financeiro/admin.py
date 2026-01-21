"""
Admin para modelos financeiros.
"""
from django.contrib import admin
from .models import ContaFinanceira, TituloReceber, TituloPagar, MovimentoFinanceiro


@admin.register(ContaFinanceira)
class ContaFinanceiraAdmin(admin.ModelAdmin):
    list_display = ['nome', 'empresa', 'tipo', 'banco', 'is_active']
    list_filter = ['empresa', 'tipo', 'is_active']
    search_fields = ['nome', 'banco', 'conta']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


@admin.register(TituloReceber)
class TituloReceberAdmin(admin.ModelAdmin):
    list_display = ['descricao', 'empresa', 'loja', 'cliente', 'valor', 'data_vencimento', 'status']
    list_filter = ['status', 'empresa', 'loja', 'data_vencimento']
    search_fields = ['descricao', 'cliente__nome_razao_social']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    date_hierarchy = 'data_vencimento'


@admin.register(TituloPagar)
class TituloPagarAdmin(admin.ModelAdmin):
    list_display = ['descricao', 'empresa', 'loja', 'fornecedor', 'valor', 'data_vencimento', 'status']
    list_filter = ['status', 'empresa', 'loja', 'data_vencimento']
    search_fields = ['descricao', 'fornecedor__razao_social']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    date_hierarchy = 'data_vencimento'


@admin.register(MovimentoFinanceiro)
class MovimentoFinanceiroAdmin(admin.ModelAdmin):
    list_display = ['conta', 'tipo', 'valor', 'data_movimento', 'referencia']
    list_filter = ['tipo', 'conta', 'data_movimento']
    search_fields = ['referencia', 'observacao']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    date_hierarchy = 'data_movimento'

