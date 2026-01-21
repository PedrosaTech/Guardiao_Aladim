"""
Modelos do módulo fiscal - NF-e / NFC-e.
"""
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from core.models import BaseModel, Loja
from core.fields import EncryptedCharField
from pessoas.models import Cliente, Fornecedor


class ConfiguracaoFiscalLoja(BaseModel):
    """
    Configuração fiscal de uma loja para emissão de NF-e / NFC-e.
    
    TODO: Integração com SEFAZ-BA (NF-e/NFC-e)
    TODO: Armazenamento seguro do certificado digital (usar FileField com criptografia)
    TODO: Validação de certificado antes de salvar
    TODO: Implementar renovação automática de certificado
    """
    
    AMBIENTE_CHOICES = [
        ('HOMOLOGACAO', 'Homologação'),
        ('PRODUCAO', 'Produção'),
    ]
    
    loja = models.OneToOneField(
        Loja,
        on_delete=models.CASCADE,
        related_name='configuracao_fiscal',
        verbose_name='Loja',
    )
    cnpj = EncryptedCharField('CNPJ', max_length=18)
    inscricao_estadual = models.CharField('Inscrição Estadual', max_length=20)
    regime_tributario = models.CharField(
        'Regime Tributário',
        max_length=50,
        help_text='Ex: SIMPLES_NACIONAL, LUCRO_PRESUMIDO, LUCRO_REAL'
    )
    
    # Certificado Digital
    # TODO: Em produção, usar FileField com armazenamento seguro (ex: S3 com criptografia)
    certificado_arquivo = models.CharField('Caminho do Certificado', max_length=500, blank=True, null=True)
    senha_certificado = EncryptedCharField('Senha do Certificado', max_length=255, blank=True, null=True)
    
    ambiente = models.CharField('Ambiente', max_length=20, choices=AMBIENTE_CHOICES, default='HOMOLOGACAO')
    serie_nfe = models.CharField('Série NF-e', max_length=3, default='001')
    serie_nfce = models.CharField('Série NFC-e', max_length=3, default='001')
    proximo_numero_nfe = models.IntegerField('Próximo Número NF-e', default=1)
    proximo_numero_nfce = models.IntegerField('Próximo Número NFC-e', default=1)
    
    class Meta:
        verbose_name = 'Configuração Fiscal da Loja'
        verbose_name_plural = 'Configurações Fiscais das Lojas'
    
    def __str__(self):
        return f"Configuração Fiscal - {self.loja.nome}"


class NotaFiscalSaida(BaseModel):
    """
    Nota Fiscal de Saída (NF-e ou NFC-e).
    
    TODO: Integração com SEFAZ-BA para emissão/autorização
    TODO: Validação de schema XML antes de salvar
    TODO: Armazenamento seguro dos XMLs (criptografia)
    TODO: Possibilidade de exportação para fiscalização
    TODO: Implementar cancelamento e carta de correção
    """
    
    TIPO_DOCUMENTO_CHOICES = [
        ('NFE', 'NF-e'),
        ('NFCE', 'NFC-e'),
    ]
    
    STATUS_CHOICES = [
        ('RASCUNHO', 'Rascunho'),
        ('EM_PROCESSAMENTO', 'Em Processamento'),
        ('AUTORIZADA', 'Autorizada'),
        ('REJEITADA', 'Rejeitada'),
        ('CANCELADA', 'Cancelada'),
    ]
    
    loja = models.ForeignKey(
        Loja,
        on_delete=models.PROTECT,
        related_name='notas_fiscais_saida',
        verbose_name='Loja',
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='notas_fiscais',
        verbose_name='Cliente',
    )
    pedido_venda = models.ForeignKey(
        'vendas.PedidoVenda',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notas_fiscais',
        verbose_name='Pedido de Venda',
    )
    evento = models.ForeignKey(
        'eventos.EventoVenda',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notas_fiscais',
        verbose_name='Evento',
    )
    
    tipo_documento = models.CharField('Tipo de Documento', max_length=4, choices=TIPO_DOCUMENTO_CHOICES)
    numero = models.IntegerField('Número')
    serie = models.CharField('Série', max_length=3)
    chave_acesso = models.CharField('Chave de Acesso', max_length=44, blank=True, null=True)
    valor_total = models.DecimalField(
        'Valor Total',
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    xml_arquivo = models.TextField('XML da Nota', blank=True, null=True)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='RASCUNHO')
    data_emissao = models.DateTimeField('Data de Emissão', null=True, blank=True)
    motivo_cancelamento = models.TextField('Motivo do Cancelamento', blank=True, null=True)
    
    class Meta:
        verbose_name = 'Nota Fiscal de Saída'
        verbose_name_plural = 'Notas Fiscais de Saída'
        ordering = ['-data_emissao', '-numero']
        unique_together = [['loja', 'tipo_documento', 'serie', 'numero']]
        indexes = [
            models.Index(fields=['loja', 'status']),
            models.Index(fields=['cliente', '-data_emissao']),
            models.Index(fields=['chave_acesso']),
        ]
    
    def __str__(self):
        return f"{self.tipo_documento} {self.numero}/{self.serie} - {self.cliente.nome_razao_social}"


class NotaFiscalEntrada(BaseModel):
    """
    Nota Fiscal de Entrada (compra de fornecedor).
    
    TODO: Importação de XML de NF-e de fornecedor
    TODO: Validação de schema XML
    TODO: Armazenamento seguro dos XMLs
    """
    loja = models.ForeignKey(
        Loja,
        on_delete=models.PROTECT,
        related_name='notas_fiscais_entrada',
        verbose_name='Loja',
    )
    fornecedor = models.ForeignKey(
        Fornecedor,
        on_delete=models.PROTECT,
        related_name='notas_fiscais',
        verbose_name='Fornecedor',
    )
    numero = models.IntegerField('Número')
    serie = models.CharField('Série', max_length=3)
    chave_acesso = models.CharField('Chave de Acesso', max_length=44)
    valor_total = models.DecimalField(
        'Valor Total',
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    xml_arquivo = models.TextField('XML da Nota', blank=True, null=True)
    data_emissao = models.DateField('Data de Emissão')
    data_entrada = models.DateField('Data de Entrada')
    
    class Meta:
        verbose_name = 'Nota Fiscal de Entrada'
        verbose_name_plural = 'Notas Fiscais de Entrada'
        ordering = ['-data_entrada', '-numero']
        unique_together = [['loja', 'chave_acesso']]
        indexes = [
            models.Index(fields=['loja', '-data_entrada']),
            models.Index(fields=['fornecedor', '-data_entrada']),
            models.Index(fields=['chave_acesso']),
        ]
    
    def __str__(self):
        return f"NF-e Entrada {self.numero}/{self.serie} - {self.fornecedor.razao_social}"

