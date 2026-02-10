"""
Modelos de Empresa e Loja.
"""
from django.db import models
from .base import BaseModel
from ..fields import EncryptedCharField


class Empresa(BaseModel):
    """
    Empresa principal do sistema.
    """
    nome_fantasia = models.CharField('Nome Fantasia', max_length=255)
    razao_social = models.CharField('Razão Social', max_length=255)
    cnpj = EncryptedCharField('CNPJ', max_length=255)  # 255 para valor criptografado no DB
    inscricao_estadual = models.CharField('Inscrição Estadual', max_length=20, blank=True, null=True)
    telefone = EncryptedCharField('Telefone', max_length=255, blank=True, null=True)  # 255 para valor criptografado
    email = models.EmailField('E-mail', blank=True, null=True)
    
    # Endereço
    logradouro = models.CharField('Logradouro', max_length=255, blank=True, null=True)
    numero = models.CharField('Número', max_length=20, blank=True, null=True)
    complemento = models.CharField('Complemento', max_length=100, blank=True, null=True)
    bairro = models.CharField('Bairro', max_length=100, blank=True, null=True)
    cidade = models.CharField('Cidade', max_length=100, blank=True, null=True)
    uf = models.CharField('UF', max_length=2, blank=True, null=True)
    cep = models.CharField('CEP', max_length=10, blank=True, null=True)
    
    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['nome_fantasia']
    
    def __str__(self):
        return self.nome_fantasia


class Loja(BaseModel):
    """
    Loja/Filial da empresa.
    """
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='lojas',
        verbose_name='Empresa',
    )
    nome = models.CharField('Nome', max_length=255)
    cnpj = EncryptedCharField('CNPJ', max_length=255, blank=True, null=True)  # 255 para valor criptografado
    inscricao_estadual = models.CharField('Inscrição Estadual', max_length=20, blank=True, null=True)
    telefone = EncryptedCharField('Telefone', max_length=255, blank=True, null=True)  # 255 para valor criptografado
    email = models.EmailField('E-mail', blank=True, null=True)
    
    # Endereço
    logradouro = models.CharField('Logradouro', max_length=255, blank=True, null=True)
    numero = models.CharField('Número', max_length=20, blank=True, null=True)
    complemento = models.CharField('Complemento', max_length=100, blank=True, null=True)
    bairro = models.CharField('Bairro', max_length=100, blank=True, null=True)
    cidade = models.CharField('Cidade', max_length=100, blank=True, null=True)
    uf = models.CharField('UF', max_length=2, blank=True, null=True)
    cep = models.CharField('CEP', max_length=10, blank=True, null=True)
    
    class Meta:
        verbose_name = 'Loja'
        verbose_name_plural = 'Lojas'
        ordering = ['empresa', 'nome']
    
    def __str__(self):
        return f"{self.empresa.nome_fantasia} - {self.nome}"

