"""
Vínculo User ↔ Empresa para multitenancy (sessão).
"""
from django.conf import settings
from django.db import models

from .base import BaseModel
from .empresa import Empresa


class UsuarioEmpresa(BaseModel):
    """
    Relação entre usuário e empresa com perfil de acesso.
    Um usuário pode ter acesso a uma ou mais empresas.
    """

    PERFIL_CHOICES = [
        ('ADMIN', 'Administrador'),
        ('GERENTE', 'Gerente'),
        ('OPERADOR', 'Operador'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='empresas_acesso',
    )
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='usuarios_acesso',
    )
    perfil = models.CharField(max_length=20, choices=PERFIL_CHOICES, default='OPERADOR')
    empresa_padrao = models.BooleanField(
        'Empresa Padrão',
        default=False,
        help_text='Se verdadeiro, esta empresa é sugerida na sessão quando o usuário ainda não escolheu outra.',
    )

    class Meta:
        verbose_name = 'Acesso de Usuário à Empresa'
        verbose_name_plural = 'Acessos de Usuários às Empresas'
        unique_together = [['user', 'empresa']]

    def __str__(self):
        return f'{self.user.username} → {self.empresa.nome_fantasia} ({self.perfil})'
