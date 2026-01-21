"""
Modelos do módulo de mensagens (WhatsApp).
"""
from django.db import models
from core.models import BaseModel, Empresa
from crm.models import Lead
from pessoas.models import Cliente


class TemplateMensagem(BaseModel):
    """
    Template de mensagem para WhatsApp.
    """
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='templates_mensagem',
        verbose_name='Empresa',
    )
    nome = models.CharField('Nome', max_length=255)
    codigo_interno = models.CharField('Código Interno', max_length=50)
    conteudo_texto = models.TextField('Conteúdo do Texto')
    ativo = models.BooleanField('Ativo', default=True)
    
    class Meta:
        verbose_name = 'Template de Mensagem'
        verbose_name_plural = 'Templates de Mensagem'
        ordering = ['empresa', 'nome']
        unique_together = [['empresa', 'codigo_interno']]
    
    def __str__(self):
        return f"{self.empresa.nome_fantasia} - {self.nome}"


class MensagemWhatsApp(BaseModel):
    """
    Mensagem WhatsApp enviada ou recebida.
    
    TODO: Integrar com API oficial WhatsApp Business via outro serviço
    TODO: Garantir LGPD: uso de consentimento antes de campanhas de marketing
    """
    
    DIRECAO_CHOICES = [
        ('ENTRADA', 'Entrada'),
        ('SAIDA', 'Saída'),
    ]
    
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('ENVIADA', 'Enviada'),
        ('ERRO', 'Erro'),
    ]
    
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='mensagens_whatsapp',
        verbose_name='Empresa',
    )
    lead = models.ForeignKey(
        Lead,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mensagens_whatsapp',
        verbose_name='Lead',
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mensagens_whatsapp',
        verbose_name='Cliente',
    )
    conteudo = models.TextField('Conteúdo')
    direcao = models.CharField('Direção', max_length=10, choices=DIRECAO_CHOICES)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='PENDENTE')
    id_externo = models.CharField(
        'ID Externo',
        max_length=100,
        blank=True,
        null=True,
        help_text='ID da mensagem no sistema externo (WhatsApp Business API)'
    )
    data_envio = models.DateTimeField('Data de Envio', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Mensagem WhatsApp'
        verbose_name_plural = 'Mensagens WhatsApp'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['empresa', 'status']),
            models.Index(fields=['lead', '-created_at']),
            models.Index(fields=['cliente', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_direcao_display()} - {self.get_status_display()} - {self.created_at}"

