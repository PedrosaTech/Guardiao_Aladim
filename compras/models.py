"""
Modelos do módulo de compras.
"""
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from core.models import BaseModel, Loja
from pessoas.models import Fornecedor
from produtos.models import Produto


class PedidoCompra(BaseModel):
    """
    Pedido de compra de fornecedor.
    """
    
    STATUS_CHOICES = [
        ('ORCAMENTO', 'Orçamento'),
        ('ABERTO', 'Aberto'),
        ('RECEBIDO', 'Recebido'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    loja = models.ForeignKey(
        Loja,
        on_delete=models.PROTECT,
        related_name='pedidos_compra',
        verbose_name='Loja',
    )
    fornecedor = models.ForeignKey(
        Fornecedor,
        on_delete=models.PROTECT,
        related_name='pedidos_compra',
        verbose_name='Fornecedor',
    )
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='ORCAMENTO')
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
        verbose_name = 'Pedido de Compra'
        verbose_name_plural = 'Pedidos de Compra'
        ordering = ['-data_emissao', '-id']
    
    def __str__(self):
        return f"Pedido Compra #{self.id} - {self.fornecedor.razao_social}"


class ItemPedidoCompra(BaseModel):
    """
    Item de um pedido de compra.
    """
    pedido = models.ForeignKey(
        PedidoCompra,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name='Pedido',
    )
    produto = models.ForeignKey(
        Produto,
        on_delete=models.PROTECT,
        related_name='itens_pedido_compra',
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
    total = models.DecimalField(
        'Total',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    class Meta:
        verbose_name = 'Item do Pedido de Compra'
        verbose_name_plural = 'Itens dos Pedidos de Compra'
    
    def __str__(self):
        return f"{self.pedido} - {self.produto.descricao} x {self.quantidade}"
    
    def save(self, *args, **kwargs):
        """
        Calcula o total do item antes de salvar.
        """
        self.total = self.preco_unitario * self.quantidade
        super().save(*args, **kwargs)
        # Recalcula o total do pedido
        if self.pedido:
            self.pedido.valor_total = sum(
                item.total for item in self.pedido.itens.filter(is_active=True)
            )
            self.pedido.save(update_fields=['valor_total', 'updated_at'])

