"""
Admin para modelos de mensagens.
"""
from django.contrib import admin
from .models import TemplateMensagem, MensagemWhatsApp


@admin.register(TemplateMensagem)
class TemplateMensagemAdmin(admin.ModelAdmin):
    list_display = ['nome', 'empresa', 'codigo_interno', 'ativo', 'is_active']
    list_filter = ['empresa', 'ativo', 'is_active']
    search_fields = ['nome', 'codigo_interno', 'conteudo_texto']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


@admin.register(MensagemWhatsApp)
class MensagemWhatsAppAdmin(admin.ModelAdmin):
    list_display = ['empresa', 'lead', 'cliente', 'direcao', 'status', 'data_envio', 'created_at']
    list_filter = ['direcao', 'status', 'empresa', 'created_at']
    search_fields = ['conteudo', 'lead__nome', 'cliente__nome_razao_social', 'id_externo']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    date_hierarchy = 'created_at'

