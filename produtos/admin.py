"""
Admin para modelos de produtos.
"""
from django.contrib import admin

from .models import CategoriaProduto, CodigoBarrasAlternativo, Produto


class CodigoBarrasAlternativoInline(admin.TabularInline):
    """Inline para gerenciar códigos alternativos no produto."""
    model = CodigoBarrasAlternativo
    extra = 1
    fields = ['codigo_barras', 'descricao', 'multiplicador', 'is_active']
    verbose_name = 'Código Alternativo'
    verbose_name_plural = 'Códigos Alternativos'


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
    inlines = [CodigoBarrasAlternativoInline]

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
        ('Reforma Tributária 2026', {
            'fields': (
                'cclass_trib', 'cst_ibs', 'cst_cbs', 'aliquota_ibs', 'aliquota_cbs'
            ),
            'description': 'Campos da Reforma Tributária 2026. Se não preenchidos, usarão valores padrão da configuração fiscal da loja.'
        }),
        ('Comercial', {
            'fields': ('preco_venda_sugerido', 'observacoes')
        }),
        ('Controle', {
            'fields': ('is_active', 'created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )


@admin.register(CodigoBarrasAlternativo)
class CodigoBarrasAlternativoAdmin(admin.ModelAdmin):
    """Admin separado para códigos alternativos."""
    list_display = [
        'codigo_barras',
        'produto_codigo',
        'produto_descricao',
        'descricao',
        'multiplicador',
        'is_active',
    ]
    list_filter = ['is_active', 'produto__empresa']
    search_fields = [
        'codigo_barras',
        'produto__codigo_interno',
        'produto__descricao',
        'descricao',
    ]
    autocomplete_fields = ['produto']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

    def produto_codigo(self, obj):
        return obj.produto.codigo_interno

    produto_codigo.short_description = 'Código Produto'
    produto_codigo.admin_order_field = 'produto__codigo_interno'

    def produto_descricao(self, obj):
        return obj.produto.descricao

    produto_descricao.short_description = 'Descrição Produto'
    produto_descricao.admin_order_field = 'produto__descricao'
