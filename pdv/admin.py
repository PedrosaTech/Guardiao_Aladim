"""
Admin para modelos do PDV.
"""
from django.contrib import admin
from .models import CaixaSessao, Pagamento, CompradorPirotecnia, RegistroVendaPirotecnia


@admin.register(CaixaSessao)
class CaixaSessaoAdmin(admin.ModelAdmin):
    list_display = ['loja', 'usuario_abertura', 'data_hora_abertura', 'saldo_inicial', 'status', 'saldo_final', 'data_hora_fechamento']
    list_filter = ['status', 'loja', 'data_hora_abertura']
    search_fields = ['loja__nome', 'usuario_abertura__username']
    readonly_fields = ['data_hora_abertura', 'created_at', 'updated_at', 'created_by', 'updated_by']
    date_hierarchy = 'data_hora_abertura'


@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display = ['pedido', 'caixa_sessao', 'tipo', 'valor', 'created_at']
    list_filter = ['tipo', 'caixa_sessao__loja', 'created_at']
    search_fields = ['pedido__id', 'caixa_sessao__loja__nome']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


@admin.register(CompradorPirotecnia)
class CompradorPirotecniaAdmin(admin.ModelAdmin):
    list_display = ['nome_completo', 'cpf', 'data_nascimento', 'calcular_idade', 'tipo_documento', 'numero_documento', 'aceite_termo', 'created_at']
    list_filter = ['tipo_documento', 'aceite_termo', 'created_at', 'uf']
    search_fields = ['nome_completo', 'cpf', 'numero_documento', 'email', 'telefone']
    readonly_fields = ['calcular_idade', 'is_maior_idade', 'data_aceite', 'ip_aceite', 'created_at', 'updated_at', 'created_by', 'updated_by']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Dados Pessoais', {
            'fields': ('nome_completo', 'cpf', 'data_nascimento', 'telefone', 'email')
        }),
        ('Documento de Identidade', {
            'fields': ('tipo_documento', 'numero_documento', 'orgao_emissor', 'uf_emissor')
        }),
        ('Endereço', {
            'fields': ('logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'uf', 'cep'),
            'classes': ('collapse',)
        }),
        ('Termo de Responsabilidade', {
            'fields': ('aceite_termo', 'data_aceite', 'ip_aceite')
        }),
        ('Auditoria', {
            'fields': ('observacoes', 'calcular_idade', 'is_maior_idade', 'created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(RegistroVendaPirotecnia)
class RegistroVendaPirotecniaAdmin(admin.ModelAdmin):
    list_display = ['pedido_venda', 'produto', 'comprador', 'quantidade', 'valor_total', 'created_at']
    list_filter = ['created_at', 'produto']
    search_fields = ['pedido_venda__id', 'comprador__nome_completo', 'comprador__cpf', 'produto__descricao']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Venda', {
            'fields': ('pedido_venda', 'item_pedido', 'produto')
        }),
        ('Comprador', {
            'fields': ('comprador',)
        }),
        ('Detalhes', {
            'fields': ('quantidade', 'valor_unitario', 'valor_total', 'numero_certificado_exercito')
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

