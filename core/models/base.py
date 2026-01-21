"""
Modelos base com auditoria e timestamps.
"""
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


class TimeStampedModel(models.Model):
    """
    Modelo abstrato com timestamps de criação e atualização.
    """
    created_at = models.DateTimeField('Data de criação', auto_now_add=True)
    updated_at = models.DateTimeField('Data de atualização', auto_now=True)
    
    class Meta:
        abstract = True


class BaseModel(TimeStampedModel):
    """
    Modelo base com timestamps, controle de ativação e auditoria de usuário.
    """
    is_active = models.BooleanField('Ativo', default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created',
        verbose_name='Criado por',
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated',
        verbose_name='Atualizado por',
    )
    
    class Meta:
        abstract = True

