"""
Admin para modelos de CRM.
"""
from django.contrib import admin
from .models import Lead, InteracaoCRM


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ['nome', 'empresa', 'loja', 'origem', 'status', 'aceita_comunicacoes', 'created_at']
    list_filter = ['status', 'origem', 'empresa', 'loja', 'aceita_comunicacoes', 'created_at']
    search_fields = ['nome', 'telefone', 'whatsapp', 'email']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    date_hierarchy = 'created_at'


@admin.register(InteracaoCRM)
class InteracaoCRMAdmin(admin.ModelAdmin):
    list_display = ['canal', 'descricao_resumida', 'lead', 'cliente', 'data_hora']
    list_filter = ['canal', 'data_hora']
    search_fields = ['descricao_resumida', 'lead__nome', 'cliente__nome_razao_social']
    readonly_fields = ['data_hora', 'created_at', 'updated_at', 'created_by', 'updated_by']
    date_hierarchy = 'data_hora'

