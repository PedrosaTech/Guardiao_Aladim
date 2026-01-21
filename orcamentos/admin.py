"""
Admin do módulo de orçamentos.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import OrcamentoVenda, ItemOrcamentoVenda


class ItemOrcamentoVendaInline(admin.TabularInline):
    """
    Inline para itens do orçamento.
    """
    model = ItemOrcamentoVenda
    extra = 1
    fields = (
        'produto', 'descricao_produto', 'classe_risco', 'subclasse_risco',
        'quantidade', 'valor_unitario', 'desconto', 'valor_total'
    )
    readonly_fields = ('classe_risco', 'subclasse_risco', 'valor_total')
    
    def get_readonly_fields(self, request, obj=None):
        """
        Se o orçamento já foi convertido, tornar todos os campos readonly.
        """
        if obj and obj.pedido_gerado:
            return self.fields
        return self.readonly_fields


@admin.register(OrcamentoVenda)
class OrcamentoVendaAdmin(admin.ModelAdmin):
    """
    Admin para OrcamentoVenda.
    """
    list_display = [
        'id', 'empresa', 'loja', 'cliente', 'nome_responsavel', 'origem',
        'tipo_operacao', 'data_emissao', 'data_validade', 'status',
        'total_liquido', 'pedido_link', 'is_active'
    ]
    list_filter = [
        'empresa', 'loja', 'origem', 'tipo_operacao', 'status',
        'data_emissao', 'data_validade', 'is_active'
    ]
    search_fields = [
        'nome_responsavel', 'email_contato', 'telefone_contato', 'whatsapp_contato'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'created_by', 'updated_by',
        'total_bruto', 'total_liquido', 'pedido_gerado'
    ]
    date_hierarchy = 'data_emissao'
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('empresa', 'loja', 'cliente', 'vendedor', 'pedido_gerado')
        }),
        ('Contato', {
            'fields': (
                'nome_responsavel', 'telefone_contato', 'whatsapp_contato', 'email_contato'
            )
        }),
        ('Classificação', {
            'fields': ('origem', 'tipo_operacao', 'status')
        }),
        ('Datas', {
            'fields': ('data_emissao', 'data_validade')
        }),
        ('Valores', {
            'fields': (
                'total_bruto', 'desconto_total', 'acrescimo_total', 'total_liquido'
            )
        }),
        ('Outros', {
            'fields': ('condicao_pagamento_prevista', 'observacoes')
        }),
        ('Controle', {
            'fields': ('is_active', 'created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    
    inlines = [ItemOrcamentoVendaInline]
    
    def pedido_link(self, obj):
        """
        Exibe link para o pedido gerado, se existir.
        """
        if obj.pedido_gerado:
            url = reverse('admin:vendas_pedidovenda_change', args=[obj.pedido_gerado.id])
            return format_html('<a href="{}">Pedido #{}</a>', url, obj.pedido_gerado.id)
        return '-'
    pedido_link.short_description = 'Pedido Gerado'
    
    actions = ['converter_para_pedido_action']
    
    def converter_para_pedido_action(self, request, queryset):
        """
        Action para converter orçamentos selecionados em pedidos.
        """
        count = 0
        ja_convertidos = 0
        
        for orcamento in queryset:
            if orcamento.pedido_gerado:
                ja_convertidos += 1
                continue
            
            try:
                pedido = orcamento.converter_para_pedido()
                count += 1
                self.message_user(
                    request,
                    f'Orçamento #{orcamento.id} convertido em Pedido #{pedido.id}',
                    level='success'
                )
            except Exception as e:
                self.message_user(
                    request,
                    f'Erro ao converter orçamento #{orcamento.id}: {str(e)}',
                    level='error'
                )
        
        if count > 0:
            self.message_user(
                request,
                f'{count} orçamento(s) convertido(s) com sucesso.',
                level='success'
            )
        
        if ja_convertidos > 0:
            self.message_user(
                request,
                f'{ja_convertidos} orçamento(s) já haviam sido convertidos.',
                level='warning'
            )
    
    converter_para_pedido_action.short_description = 'Converter orçamento em pedido'


@admin.register(ItemOrcamentoVenda)
class ItemOrcamentoVendaAdmin(admin.ModelAdmin):
    """
    Admin para ItemOrcamentoVenda (standalone, caso necessário).
    """
    list_display = ['orcamento', 'produto', 'descricao_produto', 'quantidade', 'valor_unitario', 'valor_total']
    list_filter = ['orcamento', 'produto']
    search_fields = ['descricao_produto', 'produto__descricao']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by', 'valor_total']
