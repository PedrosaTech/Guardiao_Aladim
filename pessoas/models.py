"""
Modelos de Clientes e Fornecedores.
"""
from django.db import models
from core.models import BaseModel, Empresa, Loja
from core.fields import EncryptedCharField


class Cliente(BaseModel):
    """
    Cliente da empresa.
    
    LGPD:
    - TODO: Adicionar campo aceita_marketing (BooleanField) para consentimento de comunicações
    - TODO: Implementar política de retenção/anonimização de dados
    - TODO: Implementar mecanismo de exclusão/anonymização de dados pessoais
    """
    
    TIPO_PESSOA_CHOICES = [
        ('PF', 'Pessoa Física'),
        ('PJ', 'Pessoa Jurídica'),
    ]
    
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='clientes',
        verbose_name='Empresa',
    )
    loja = models.ForeignKey(
        Loja,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clientes',
        verbose_name='Loja',
    )
    tipo_pessoa = models.CharField('Tipo de Pessoa', max_length=2, choices=TIPO_PESSOA_CHOICES)
    nome_razao_social = models.CharField('Nome / Razão Social', max_length=255)
    apelido_nome_fantasia = models.CharField('Apelido / Nome Fantasia', max_length=255, blank=True, null=True)
    cpf_cnpj = EncryptedCharField('CPF / CNPJ', max_length=255)  # 255 para valor criptografado
    rg_inscricao_estadual = models.CharField('RG / Inscrição Estadual', max_length=20, blank=True, null=True)
    data_nascimento = models.DateField('Data de Nascimento', blank=True, null=True)
    telefone = EncryptedCharField('Telefone', max_length=255, blank=True, null=True)
    whatsapp = EncryptedCharField('WhatsApp', max_length=255, blank=True, null=True)
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
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nome_razao_social']
        indexes = [
            models.Index(fields=['empresa', 'is_active']),
            models.Index(fields=['tipo_pessoa', 'is_active']),
        ]
    
    def __str__(self):
        return self.nome_razao_social


class Fornecedor(BaseModel):
    """
    Fornecedor da empresa.
    """
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='fornecedores',
        verbose_name='Empresa',
    )
    razao_social = models.CharField('Razão Social', max_length=255)
    nome_fantasia = models.CharField('Nome Fantasia', max_length=255, blank=True, null=True)
    cnpj = EncryptedCharField('CNPJ', max_length=255)
    inscricao_estadual = models.CharField('Inscrição Estadual', max_length=20, blank=True, null=True)
    telefone = EncryptedCharField('Telefone', max_length=255, blank=True, null=True)
    whatsapp = EncryptedCharField('WhatsApp', max_length=255, blank=True, null=True)
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
        verbose_name = 'Fornecedor'
        verbose_name_plural = 'Fornecedores'
        ordering = ['razao_social']
        indexes = [
            models.Index(fields=['empresa', 'is_active']),
        ]
    
    def __str__(self):
        return self.razao_social

