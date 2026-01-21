"""
Modelos do módulo de vendas.
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings
from decimal import Decimal
from core.models import BaseModel, Loja
from pessoas.models import Cliente
from produtos.models import Produto


class CondicaoPagamento(BaseModel):
    """
    Condição de pagamento (ex: PIX à vista, Cartão 2x, Boleto 30 dias).
    """
    empresa = models.ForeignKey(
        'core.Empresa',
        on_delete=models.CASCADE,
        related_name='condicoes_pagamento',
        verbose_name='Empresa',
    )
    nome = models.CharField('Nome', max_length=100)
    descricao = models.TextField('Descrição', blank=True, null=True)
    numero_parcelas = models.IntegerField('Número de Parcelas', default=1, validators=[MinValueValidator(1)])
    dias_entre_parcelas = models.IntegerField('Dias entre Parcelas', default=0, validators=[MinValueValidator(0)])
    
    class Meta:
        verbose_name = 'Condição de Pagamento'
        verbose_name_plural = 'Condições de Pagamento'
        ordering = ['empresa', 'nome']
    
    def __str__(self):
        return f"{self.empresa.nome_fantasia} - {self.nome}"


class PedidoVenda(BaseModel):
    """
    Pedido de venda.
    
    LGPD:
    - TODO: Venda restrita para menores - validar idade do cliente antes de finalizar
    - TODO: Exigência de dados específicos do comprador para produtos com restrição de Exército
    - TODO: Registrar consentimento do cliente para uso de dados pessoais
    """
    
    TIPO_VENDA_CHOICES = [
        ('BALCAO', 'Balcão'),
        ('EXTERNA', 'Externa'),
        ('EVENTO', 'Evento'),
    ]
    
    STATUS_CHOICES = [
        ('ORCAMENTO', 'Orçamento'),
        ('ABERTO', 'Aberto'),
        ('FATURADO', 'Faturado'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    loja = models.ForeignKey(
        Loja,
        on_delete=models.PROTECT,
        related_name='pedidos_venda',
        verbose_name='Loja',
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='pedidos',
        verbose_name='Cliente',
    )
    tipo_venda = models.CharField('Tipo de Venda', max_length=20, choices=TIPO_VENDA_CHOICES)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='ORCAMENTO')
    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='pedidos_vendidos',
        verbose_name='Vendedor',
    )
    condicao_pagamento = models.ForeignKey(
        CondicaoPagamento,
        on_delete=models.PROTECT,
        related_name='pedidos',
        verbose_name='Condição de Pagamento',
    )
    valor_total = models.DecimalField(
        'Valor Total',
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    data_emissao = models.DateTimeField('Data de Emissão', auto_now_add=True)
    observacoes = models.TextField('Observações', blank=True, null=True)
    
    class Meta:
        verbose_name = 'Pedido de Venda'
        verbose_name_plural = 'Pedidos de Venda'
        ordering = ['-data_emissao', '-id']
        indexes = [
            models.Index(fields=['loja', 'status']),
            models.Index(fields=['cliente', '-data_emissao']),
            models.Index(fields=['vendedor', '-data_emissao']),
        ]
    
    def __str__(self):
        return f"Pedido #{self.id} - {self.cliente.nome_razao_social} - {self.valor_total}"
    
    def recalcular_total(self):
        """
        Recalcula o valor total do pedido somando os totais dos itens ativos.
        """
        total = Decimal('0.00')
        for item in self.itens.filter(is_active=True):
            total += item.total
        self.valor_total = total
        self.save(update_fields=['valor_total', 'updated_at'])
        return total


class ItemPedidoVenda(BaseModel):
    """
    Item de um pedido de venda.
    """
    pedido = models.ForeignKey(
        PedidoVenda,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name='Pedido',
    )
    produto = models.ForeignKey(
        Produto,
        on_delete=models.PROTECT,
        related_name='itens_pedido',
        verbose_name='Produto',
    )
    quantidade = models.DecimalField(
        'Quantidade',
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    preco_unitario = models.DecimalField(
        'Preço Unitário',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    desconto = models.DecimalField(
        'Desconto',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    total = models.DecimalField(
        'Total',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    class Meta:
        verbose_name = 'Item do Pedido de Venda'
        verbose_name_plural = 'Itens dos Pedidos de Venda'
        ordering = ['pedido', 'id']
    
    def __str__(self):
        return f"{self.pedido} - {self.produto.descricao} x {self.quantidade}"
    
    def save(self, *args, **kwargs):
        """
        Calcula o total do item antes de salvar.
        """
        self.total = (self.preco_unitario * self.quantidade) - self.desconto
        super().save(*args, **kwargs)
        # Recalcula o total do pedido
        if self.pedido:
            self.pedido.recalcular_total()

