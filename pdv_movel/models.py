"""
Models para PDV Móvel (Tablet).
Sistema de pedidos em tablet para reduzir filas.
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal

from core.models import BaseModel


class ConfiguracaoPDVMovel(BaseModel):
    """
    Configurações do PDV Móvel por loja.

    Define comportamento do sistema de tablet:
    - Timeout de pedidos não pagos
    - Permissões de edição
    - Funcionalidades ativas
    """
    loja = models.OneToOneField(
        'core.Loja',
        on_delete=models.CASCADE,
        related_name='config_pdv_movel',
        verbose_name='Loja',
    )
    ativo = models.BooleanField(
        'PDV Móvel Ativo',
        default=True,
        help_text='Ativa/desativa o PDV Móvel para esta loja',
    )
    timeout_pedido_minutos = models.IntegerField(
        'Timeout Pedido (minutos)',
        default=30,
        validators=[MinValueValidator(5), MaxValueValidator(120)],
        help_text='Pedidos não pagos após este tempo aparecem como abandonados',
    )
    permitir_edicao_pedido = models.BooleanField(
        'Permitir Editar Pedido',
        default=True,
        help_text='Permite atendente editar pedido após salvar',
    )
    exigir_cliente = models.BooleanField(
        'Exigir Cliente',
        default=False,
        help_text='Obriga informar cliente ao criar pedido',
    )
    permitir_desconto = models.BooleanField(
        'Permitir Desconto',
        default=False,
        help_text='Permite atendente dar desconto no tablet',
    )
    desconto_maximo_percentual = models.DecimalField(
        'Desconto Máximo (%)',
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[
            MinValueValidator(Decimal('0.00')),
            MaxValueValidator(Decimal('100.00')),
        ],
        help_text='Desconto máximo que atendente pode dar',
    )

    class Meta:
        verbose_name = 'Configuração PDV Móvel'
        verbose_name_plural = 'Configurações PDV Móvel'

    def __str__(self):
        return f"Config PDV Móvel - {self.loja.nome}"


class AtendentePDV(BaseModel):
    """
    Atendente que usa tablet para tirar pedidos.

    Cada atendente tem:
    - PIN de 4 dígitos para login rápido
    - Vinculação a uma loja específica
    - Controle de ativo/inativo
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='atendente_pdv',
        verbose_name='Usuário',
    )
    loja = models.ForeignKey(
        'core.Loja',
        on_delete=models.CASCADE,
        related_name='atendentes_pdv',
        verbose_name='Loja',
    )
    pin = models.CharField(
        'PIN',
        max_length=4,
        help_text='PIN de 4 dígitos para login no tablet (ex: 1234)',
    )
    ativo = models.BooleanField(
        'Ativo',
        default=True,
        help_text='Atendente pode usar o tablet',
    )
    ultima_sessao = models.DateTimeField(
        'Última Sessão',
        null=True,
        blank=True,
    )
    tablet_id = models.CharField(
        'ID do Tablet',
        max_length=100,
        blank=True,
        help_text='Identificador do tablet usado (preenchido automaticamente)',
    )

    class Meta:
        verbose_name = 'Atendente PDV'
        verbose_name_plural = 'Atendentes PDV'
        unique_together = [['loja', 'pin']]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.loja.nome}"

    def validar_pin(self, pin):
        """
        Valida PIN do atendente.

        Args:
            pin: PIN de 4 dígitos

        Returns:
            bool: True se PIN correto e atendente ativo
        """
        return self.pin == pin and self.ativo

    def clean(self):
        super().clean()
        if not self.pin:
            return
        if not self.pin.isdigit():
            raise ValidationError({'pin': 'PIN deve conter apenas números'})
        if len(self.pin) != 4:
            raise ValidationError({'pin': 'PIN deve ter exatamente 4 dígitos'})
