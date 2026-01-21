"""
Admin para modelos de pessoas.
"""
from django.contrib import admin
from .models import Cliente, Fornecedor


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nome_razao_social', 'empresa', 'tipo_pessoa', 'cpf_cnpj', 'telefone', 'whatsapp', 'email', 'is_active']
    list_filter = ['empresa', 'tipo_pessoa', 'is_active', 'created_at']
    search_fields = ['nome_razao_social', 'apelido_nome_fantasia', 'cpf_cnpj', 'email']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('empresa', 'loja', 'tipo_pessoa', 'nome_razao_social', 'apelido_nome_fantasia')
        }),
        ('Documentos', {
            'fields': ('cpf_cnpj', 'rg_inscricao_estadual', 'data_nascimento')
        }),
        ('Contato', {
            'fields': ('telefone', 'whatsapp', 'email')
        }),
        ('Endereço', {
            'fields': ('logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'uf', 'cep')
        }),
        ('Controle', {
            'fields': ('is_active', 'created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ['razao_social', 'empresa', 'cnpj', 'telefone', 'whatsapp', 'email', 'is_active']
    list_filter = ['empresa', 'is_active', 'created_at']
    search_fields = ['razao_social', 'nome_fantasia', 'cnpj', 'email']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('empresa', 'razao_social', 'nome_fantasia')
        }),
        ('Documentos', {
            'fields': ('cnpj', 'inscricao_estadual')
        }),
        ('Contato', {
            'fields': ('telefone', 'whatsapp', 'email')
        }),
        ('Endereço', {
            'fields': ('logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'uf', 'cep')
        }),
        ('Controle', {
            'fields': ('is_active', 'created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )

