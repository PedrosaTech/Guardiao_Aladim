"""
Django Admin para PDV Móvel.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone

from .models import ConfiguracaoPDVMovel, AtendentePDV


@admin.register(ConfiguracaoPDVMovel)
class ConfiguracaoPDVMovelAdmin(admin.ModelAdmin):
    list_display = [
        'loja',
        'ativo_badge',
        'timeout_pedido_minutos',
        'permitir_edicao_pedido',
        'permitir_desconto',
    ]
    list_filter = ['ativo', 'permitir_edicao_pedido', 'permitir_desconto']
    search_fields = ['loja__nome']
    fieldsets = (
        ('Loja', {
            'fields': ('loja', 'ativo'),
        }),
        ('Configurações de Pedido', {
            'fields': (
                'timeout_pedido_minutos',
                'permitir_edicao_pedido',
                'exigir_cliente',
            ),
        }),
        ('Descontos', {
            'fields': (
                'permitir_desconto',
                'desconto_maximo_percentual',
            ),
        }),
    )

    def ativo_badge(self, obj):
        if obj.ativo:
            return format_html('<span style="color: green;">✓ Ativo</span>')
        return format_html('<span style="color: red;">✗ Inativo</span>')

    ativo_badge.short_description = 'Status'


@admin.register(AtendentePDV)
class AtendentePDVAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'loja',
        'ativo_badge',
        'pin_display',
        'ultima_sessao',
        'total_pedidos_hoje',
    ]
    list_filter = ['ativo', 'loja']
    search_fields = [
        'user__username',
        'user__first_name',
        'user__last_name',
        'loja__nome',
    ]
    fieldsets = (
        ('Usuário', {
            'fields': ('user', 'loja'),
        }),
        ('Acesso', {
            'fields': ('pin', 'ativo'),
        }),
        ('Informações de Sessão', {
            'fields': ('ultima_sessao', 'tablet_id'),
            'classes': ('collapse',),
        }),
    )

    def ativo_badge(self, obj):
        if obj.ativo:
            return format_html('<span style="color: green;">✓ Ativo</span>')
        return format_html('<span style="color: red;">✗ Inativo</span>')

    ativo_badge.short_description = 'Status'

    def pin_display(self, obj):
        if obj.pin and len(obj.pin) >= 1:
            return f"****{obj.pin[-1]}"
        return "••••"

    pin_display.short_description = 'PIN'

    def total_pedidos_hoje(self, obj):
        from vendas.models import PedidoVenda

        hoje = timezone.now().date()
        total = PedidoVenda.objects.filter(
            atendente_tablet=obj,
            created_at__date=hoje,
            is_active=True,
        ).count()
        return format_html('<span style="font-weight: bold;">{}</span> pedidos', total)

    total_pedidos_hoje.short_description = 'Pedidos Hoje'
