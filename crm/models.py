"""
Modelos do módulo CRM.
"""
from django.db import models
from core.models import BaseModel, Empresa, Loja
from core.fields import EncryptedCharField
from pessoas.models import Cliente


class Lead(BaseModel):
    """
    Lead (prospecto/cliente potencial).
    
    LGPD:
    - Campo aceita_comunicacoes para consentimento de marketing
    """
    
    ORIGEM_CHOICES = [
        ('WHATSAPP', 'WhatsApp'),
        ('INDICACAO', 'Indicação'),
        ('EVENTO', 'Evento'),
        ('OUTROS', 'Outros'),
    ]
    
    STATUS_CHOICES = [
        ('NOVO', 'Novo'),
        ('EM_ANDAMENTO', 'Em Andamento'),
        ('CONVERTIDO', 'Convertido'),
        ('PERDIDO', 'Perdido'),
    ]
    
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='leads',
        verbose_name='Empresa',
    )
    loja = models.ForeignKey(
        Loja,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leads',
        verbose_name='Loja',
    )
    nome = models.CharField('Nome', max_length=255)
    telefone = EncryptedCharField('Telefone', max_length=255, blank=True, null=True)
    whatsapp = EncryptedCharField('WhatsApp', max_length=255, blank=True, null=True)
    email = models.EmailField('E-mail', blank=True, null=True)
    origem = models.CharField('Origem', max_length=20, choices=ORIGEM_CHOICES, default='OUTROS')
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='NOVO')
    observacoes = models.TextField('Observações', blank=True, null=True)
    aceita_comunicacoes = models.BooleanField(
        'Aceita Comunicações',
        default=False,
        help_text='LGPD: Consentimento para receber comunicações de marketing'
    )
    
    class Meta:
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['empresa', 'status']),
            models.Index(fields=['origem', 'status']),
        ]
    
    def __str__(self):
        return f"{self.nome} - {self.get_status_display()}"


class InteracaoCRM(BaseModel):
    """
    Interação com lead ou cliente (via WhatsApp, ligação, presencial, email).
    
    TODO: Interação via WhatsApp será alimentada por um microserviço (Guardião) via API
    """
    
    CANAL_CHOICES = [
        ('WHATSAPP', 'WhatsApp'),
        ('LIGACAO', 'Ligação'),
        ('PRESENCIAL', 'Presencial'),
        ('EMAIL', 'E-mail'),
    ]
    
    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='interacoes',
        verbose_name='Lead',
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='interacoes_crm',
        verbose_name='Cliente',
    )
    canal = models.CharField('Canal', max_length=20, choices=CANAL_CHOICES)
    descricao_resumida = models.CharField('Descrição Resumida', max_length=255)
    data_hora = models.DateTimeField('Data/Hora', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Interação CRM'
        verbose_name_plural = 'Interações CRM'
        ordering = ['-data_hora']
        indexes = [
            models.Index(fields=['-data_hora']),
            models.Index(fields=['lead', '-data_hora']),
            models.Index(fields=['cliente', '-data_hora']),
        ]
    
    def __str__(self):
        return f"{self.get_canal_display()} - {self.descricao_resumida} - {self.data_hora}"

