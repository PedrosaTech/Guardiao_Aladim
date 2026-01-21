"""
Admin para modelos do core.
"""
from django.contrib import admin
from .models import Empresa, Loja, AuditLog


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['nome_fantasia', 'razao_social', 'cnpj', 'telefone', 'email', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['nome_fantasia', 'razao_social', 'cnpj', 'email']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome_fantasia', 'razao_social', 'cnpj', 'inscricao_estadual')
        }),
        ('Contato', {
            'fields': ('telefone', 'email')
        }),
        ('Endereço', {
            'fields': ('logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'uf', 'cep')
        }),
        ('Controle', {
            'fields': ('is_active', 'created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )


@admin.register(Loja)
class LojaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'empresa', 'cnpj', 'telefone', 'email', 'is_active']
    list_filter = ['empresa', 'is_active', 'created_at']
    search_fields = ['nome', 'cnpj', 'email']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('empresa', 'nome', 'cnpj', 'inscricao_estadual')
        }),
        ('Contato', {
            'fields': ('telefone', 'email')
        }),
        ('Endereço', {
            'fields': ('logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'uf', 'cep')
        }),
        ('Controle', {
            'fields': ('is_active', 'created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['data_hora', 'usuario', 'acao', 'modelo', 'objeto_id', 'ip']
    list_filter = ['acao', 'modelo', 'data_hora']
    search_fields = ['usuario__username', 'modelo', 'objeto_id', 'descricao']
    readonly_fields = ['data_hora', 'created_at', 'updated_at']
    date_hierarchy = 'data_hora'
    
    fieldsets = (
        ('Informações da Ação', {
            'fields': ('usuario', 'acao', 'modelo', 'objeto_id', 'descricao')
        }),
        ('Informações de Acesso', {
            'fields': ('ip', 'user_agent', 'data_hora')
        }),
    )

