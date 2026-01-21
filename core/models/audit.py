"""
Modelo de auditoria de acesso e ações.
"""
from django.db import models
from django.conf import settings
from .base import TimeStampedModel


class AuditLog(TimeStampedModel):
    """
    Registro de auditoria para ações no sistema.
    
    TODO: Implementar middleware para registrar automaticamente:
    - Acessos a dados sensíveis (CPF, CNPJ, telefone)
    - Alterações em clientes
    - Alterações em notas fiscais
    - Alterações em produtos com restrição de Exército
    - Movimentações de estoque de produtos restritos
    """
    
    ACAO_CHOICES = [
        ('VIEW', 'Visualização'),
        ('CREATE', 'Criação'),
        ('UPDATE', 'Atualização'),
        ('DELETE', 'Exclusão'),
        ('EXPORT', 'Exportação'),
        ('PRINT', 'Impressão'),
    ]
    
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name='Usuário',
    )
    acao = models.CharField('Ação', max_length=20, choices=ACAO_CHOICES)
    modelo = models.CharField('Modelo', max_length=100)
    objeto_id = models.CharField('ID do Objeto', max_length=255)
    descricao = models.TextField('Descrição', blank=True, null=True)
    ip = models.CharField('IP', max_length=45, blank=True, null=True)
    user_agent = models.TextField('User Agent', blank=True, null=True)
    data_hora = models.DateTimeField('Data/Hora', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
        ordering = ['-data_hora']
        indexes = [
            models.Index(fields=['-data_hora']),
            models.Index(fields=['usuario', '-data_hora']),
            models.Index(fields=['modelo', '-data_hora']),
        ]
    
    def __str__(self):
        return f"{self.acao} - {self.modelo} #{self.objeto_id} - {self.data_hora}"

