"""
Admin para modelos fiscais.
"""
from django.contrib import admin
from .models import ConfiguracaoFiscalLoja, NotaFiscalSaida, NotaFiscalEntrada


@admin.register(ConfiguracaoFiscalLoja)
class ConfiguracaoFiscalLojaAdmin(admin.ModelAdmin):
    list_display = ['loja', 'cnpj', 'inscricao_estadual', 'regime_tributario', 'usar_reforma_2026', 'ambiente', 'is_active']
    list_filter = ['ambiente', 'usar_reforma_2026', 'is_active']
    search_fields = ['loja__nome', 'cnpj', 'inscricao_estadual']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    fieldsets = (
        ('Loja', {
            'fields': ('loja',)
        }),
        ('Dados Fiscais', {
            'fields': ('cnpj', 'inscricao_estadual', 'regime_tributario')
        }),
        ('Certificado Digital', {
            'fields': ('certificado_arquivo', 'senha_certificado')
        }),
        ('Configurações de Emissão', {
            'fields': ('ambiente', 'serie_nfe', 'serie_nfce', 'proximo_numero_nfe', 'proximo_numero_nfce')
        }),
        ('Reforma Tributária 2026', {
            'fields': ('usar_reforma_2026', 'aliquota_ibs_padrao_2026', 'aliquota_cbs_padrao_2026'),
            'description': '⚠️ Ative apenas quando estiver pronto para usar CBS/IBS. Sistema funciona normalmente com reforma desligada.'
        }),
        ('Controle', {
            'fields': ('is_active', 'created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )


@admin.register(NotaFiscalSaida)
class NotaFiscalSaidaAdmin(admin.ModelAdmin):
    list_display = ['numero', 'serie', 'tipo_documento', 'loja', 'cliente', 'evento', 'valor_total', 'status', 'data_emissao']
    list_filter = ['tipo_documento', 'status', 'loja', 'evento', 'data_emissao']
    search_fields = ['numero', 'chave_acesso', 'cliente__nome_razao_social']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    date_hierarchy = 'data_emissao'
    
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:nota_id>/imprimir-pdf/',
                self.admin_site.admin_view(self.imprimir_pdf_view),
                name='fiscal_notafiscalsaida_imprimir_pdf',
            ),
        ]
        return custom_urls + urls
    
    def imprimir_pdf_view(self, request, nota_id):
        """View para imprimir PDF da NF-e."""
        from django.shortcuts import redirect
        from django.urls import reverse
        return redirect(reverse('fiscal:imprimir_nfe_pdf', args=[nota_id]))
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_imprimir_button'] = True
        return super().change_view(request, object_id, form_url, extra_context)
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('loja', 'cliente', 'pedido_venda', 'evento', 'tipo_documento')
        }),
        ('Dados da Nota', {
            'fields': ('numero', 'serie', 'chave_acesso', 'valor_total', 'status', 'data_emissao')
        }),
        ('Cancelamento', {
            'fields': ('motivo_cancelamento',)
        }),
        ('XML', {
            'fields': ('xml_arquivo',)
        }),
        ('Controle', {
            'fields': ('is_active', 'created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )


@admin.register(NotaFiscalEntrada)
class NotaFiscalEntradaAdmin(admin.ModelAdmin):
    list_display = ['numero', 'serie', 'loja', 'fornecedor', 'valor_total', 'data_emissao', 'data_entrada']
    list_filter = ['loja', 'data_emissao', 'data_entrada']
    search_fields = ['numero', 'chave_acesso', 'fornecedor__razao_social']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    date_hierarchy = 'data_entrada'

