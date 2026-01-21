"""
Admin para modelos de produtos.
"""
from django.contrib import admin
from .models import CategoriaProduto, Produto


@admin.register(CategoriaProduto)
class CategoriaProdutoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'empresa', 'is_active']
    list_filter = ['empresa', 'is_active', 'created_at']
    search_fields = ['nome', 'descricao']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ['codigo_interno', 'descricao', 'empresa', 'categoria', 'classe_risco', 'ncm', 'preco_venda_sugerido', 'is_active']
    list_filter = ['empresa', 'categoria', 'classe_risco', 'possui_restricao_exercito', 'is_active', 'created_at']
    search_fields = ['codigo_interno', 'codigo_barras', 'descricao', 'ncm']
    readonly_fields = ['codigo_interno', 'created_at', 'updated_at', 'created_by', 'updated_by']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('empresa', 'loja', 'categoria', 'codigo_interno', 'codigo_barras', 'descricao'),
            'description': '⚠️ O código interno é gerado automaticamente pelo sistema ao salvar (formato: PROD-0001, PROD-0002, etc.).'
        }),
        ('Características de Pirotecnia', {
            'fields': (
                'classe_risco', 'subclasse_risco', 'possui_restricao_exercito',
                'numero_certificado_exercito', 'numero_lote', 'validade', 'condicoes_armazenamento'
            )
        }),
        ('Dados Fiscais - NCM, CEST e CFOP', {
            'fields': (
                'ncm', 'cest', 'cfop_venda_dentro_uf', 'cfop_venda_fora_uf',
                'unidade_comercial', 'origem'
            )
        }),
        ('Dados Fiscais - ICMS', {
            'fields': (
                'csosn_cst', 'aliquota_icms', 'icms_st_cst', 'aliquota_icms_st'
            )
        }),
        ('Dados Fiscais - PIS e COFINS', {
            'fields': (
                'pis_cst', 'aliquota_pis', 'cofins_cst', 'aliquota_cofins'
            )
        }),
        ('Dados Fiscais - IPI', {
            'fields': (
                'ipi_venda_cst', 'aliquota_ipi_venda', 'ipi_compra_cst', 'aliquota_ipi_compra'
            )
        }),
        ('Comercial', {
            'fields': ('preco_venda_sugerido', 'observacoes')
        }),
        ('Controle', {
            'fields': ('is_active', 'created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )

