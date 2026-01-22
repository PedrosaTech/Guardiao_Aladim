"""
Modelos do módulo financeiro.
"""
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from core.models import BaseModel, Empresa, Loja
from pessoas.models import Cliente, Fornecedor
from vendas.models import PedidoVenda


class ContaFinanceira(BaseModel):
    """
    Conta financeira (caixa ou conta bancária).
    """
    
    TIPO_CHOICES = [
        ('CAIXA', 'Caixa'),
        ('CONTA_BANCARIA', 'Conta Bancária'),
    ]
    
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='contas_financeiras',
        verbose_name='Empresa',
    )
    nome = models.CharField('Nome', max_length=255)
    tipo = models.CharField('Tipo', max_length=20, choices=TIPO_CHOICES)
    banco = models.CharField('Banco', max_length=100, blank=True, null=True)
    agencia = models.CharField('Agência', max_length=20, blank=True, null=True)
    conta = models.CharField('Conta', max_length=20, blank=True, null=True)
    
    class Meta:
        verbose_name = 'Conta Financeira'
        verbose_name_plural = 'Contas Financeiras'
        ordering = ['empresa', 'nome']
    
    def __str__(self):
        return f"{self.empresa.nome_fantasia} - {self.nome}"


class TituloReceber(BaseModel):
    """
    Título a receber (conta a receber).
    """
    
    STATUS_CHOICES = [
        ('ABERTO', 'Aberto'),
        ('PAGO', 'Pago'),
        ('ATRASADO', 'Atrasado'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='titulos_receber',
        verbose_name='Empresa',
    )
    loja = models.ForeignKey(
        Loja,
        on_delete=models.PROTECT,
        related_name='titulos_receber',
        verbose_name='Loja',
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='titulos_receber',
        verbose_name='Cliente',
    )
    pedido_venda = models.ForeignKey(
        PedidoVenda,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='titulos_receber',
        verbose_name='Pedido de Venda',
    )
    conta_financeira = models.ForeignKey(
        'ContaFinanceira',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='titulos_receber',
        verbose_name='Conta Financeira',
    )
    descricao = models.CharField('Descrição', max_length=255)
    numero_documento = models.CharField('Número do Documento', max_length=100, blank=True, null=True)
    valor = models.DecimalField(
        'Valor',
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    valor_juros = models.DecimalField(
        'Valor Juros',
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    valor_multa = models.DecimalField(
        'Valor Multa',
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    valor_desconto = models.DecimalField(
        'Valor Desconto',
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    valor_recebido = models.DecimalField(
        'Valor Recebido',
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    data_emissao = models.DateField('Data de Emissão')
    data_vencimento = models.DateField('Data de Vencimento')
    data_pagamento = models.DateField('Data de Pagamento', null=True, blank=True)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='ABERTO')
    
    class Meta:
        verbose_name = 'Título a Receber'
        verbose_name_plural = 'Títulos a Receber'
        ordering = ['-data_vencimento']
        indexes = [
            models.Index(fields=['empresa', 'status']),
            models.Index(fields=['cliente', '-data_vencimento']),
            models.Index(fields=['data_vencimento', 'status']),
        ]
    
    def __str__(self):
        return f"{self.descricao} - {self.cliente.nome_razao_social} - R$ {self.valor}"


class TituloPagar(BaseModel):
    """
    Título a pagar (conta a pagar).
    """
    
    STATUS_CHOICES = [
        ('ABERTO', 'Aberto'),
        ('PAGO', 'Pago'),
        ('ATRASADO', 'Atrasado'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='titulos_pagar',
        verbose_name='Empresa',
    )
    loja = models.ForeignKey(
        Loja,
        on_delete=models.PROTECT,
        related_name='titulos_pagar',
        verbose_name='Loja',
    )
    fornecedor = models.ForeignKey(
        Fornecedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='titulos_pagar',
        verbose_name='Fornecedor',
    )
    descricao = models.CharField('Descrição', max_length=255)
    valor = models.DecimalField(
        'Valor',
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    data_emissao = models.DateField('Data de Emissão')
    data_vencimento = models.DateField('Data de Vencimento')
    data_pagamento = models.DateField('Data de Pagamento', null=True, blank=True)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='ABERTO')
    
    class Meta:
        verbose_name = 'Título a Pagar'
        verbose_name_plural = 'Títulos a Pagar'
        ordering = ['-data_vencimento']
        indexes = [
            models.Index(fields=['empresa', 'status']),
            models.Index(fields=['fornecedor', '-data_vencimento']),
            models.Index(fields=['data_vencimento', 'status']),
        ]
    
    def __str__(self):
        return f"{self.descricao} - R$ {self.valor}"


class MovimentoFinanceiro(BaseModel):
    """
    Movimento financeiro (entrada ou saída de dinheiro).
    """
    
    TIPO_CHOICES = [
        ('ENTRADA', 'Entrada'),
        ('SAIDA', 'Saída'),
    ]
    
    conta = models.ForeignKey(
        ContaFinanceira,
        on_delete=models.PROTECT,
        related_name='movimentos',
        verbose_name='Conta',
    )
    tipo = models.CharField('Tipo', max_length=10, choices=TIPO_CHOICES)
    valor = models.DecimalField(
        'Valor',
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    data_movimento = models.DateField('Data do Movimento')
    titulo_receber = models.ForeignKey(
        'TituloReceber',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentos',
        verbose_name='Título a Receber',
    )
    titulo_pagar = models.ForeignKey(
        'TituloPagar',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentos',
        verbose_name='Título a Pagar',
    )
    categoria = models.CharField(
        'Categoria',
        max_length=50,
        default='OUTROS',
        help_text='Categoria do movimento (VENDA, RECEBIMENTO, PAGAMENTO, etc.)'
    )
    referencia = models.CharField(
        'Referência',
        max_length=100,
        blank=True,
        null=True,
        help_text='ID de título, pedido, etc.'
    )
    observacao = models.TextField('Observação', blank=True, null=True)
    
    class Meta:
        verbose_name = 'Movimento Financeiro'
        verbose_name_plural = 'Movimentos Financeiros'
        ordering = ['-data_movimento']
        indexes = [
            models.Index(fields=['-data_movimento']),
            models.Index(fields=['conta', '-data_movimento']),
            models.Index(fields=['tipo', '-data_movimento']),
        ]
    
    def __str__(self):
        return f"{self.tipo} - {self.conta.nome} - R$ {self.valor}"

