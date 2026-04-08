"""
Modelos do módulo de estoque.
"""
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from core.models import BaseModel, Empresa, Loja
from produtos.models import Produto


class LocalEstoque(BaseModel):
    """
    Local de armazenamento de estoque.
    Ex: Depósito Principal, Loja, Vitrine, Caminhão Equipe Externa
    """
    loja = models.ForeignKey(
        Loja,
        on_delete=models.CASCADE,
        related_name='locais_estoque',
        verbose_name='Loja',
    )
    nome = models.CharField('Nome', max_length=255)
    descricao = models.TextField('Descrição', blank=True, null=True)
    e_area_restrita = models.BooleanField(
        'É Área Restrita',
        default=False,
        help_text='Indica se o local armazena produtos de alto risco'
    )
    
    class Meta:
        verbose_name = 'Local de Estoque'
        verbose_name_plural = 'Locais de Estoque'
        ordering = ['loja', 'nome']
        unique_together = [['loja', 'nome']]
    
    def __str__(self):
        return f"{self.loja.nome} - {self.nome}"


class EstoqueAtual(BaseModel):
    """
    Estoque atual de um produto em um local específico.
    """
    produto = models.ForeignKey(
        Produto,
        on_delete=models.CASCADE,
        related_name='estoques',
        verbose_name='Produto',
    )
    local_estoque = models.ForeignKey(
        LocalEstoque,
        on_delete=models.CASCADE,
        related_name='estoques',
        verbose_name='Local de Estoque',
    )
    quantidade = models.DecimalField(
        'Quantidade',
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.00'))],
        default=Decimal('0.000')
    )
    
    class Meta:
        verbose_name = 'Estoque Atual'
        verbose_name_plural = 'Estoques Atuais'
        unique_together = [['produto', 'local_estoque']]
        indexes = [
            models.Index(fields=['produto', 'local_estoque']),
            models.Index(fields=['local_estoque', 'produto']),
        ]
    
    def __str__(self):
        return f"{self.produto.codigo_interno} - {self.local_estoque.nome}: {self.quantidade}"


class MovimentoEstoque(BaseModel):
    """
    Movimentação de estoque (entrada, saída, transferência, ajuste).
    
    TODO: Implementar logs de segurança quando movimentar produtos com possui_restricao_exercito=True
    TODO: Validar quantidade disponível antes de saída/transferência
    TODO: Implementar controle de lote para produtos com número_lote
    """
    
    TIPO_MOVIMENTO_CHOICES = [
        ('ENTRADA', 'Entrada'),
        ('SAIDA', 'Saída'),
        ('TRANSFERENCIA', 'Transferência'),
        ('AJUSTE', 'Ajuste'),
    ]
    
    produto = models.ForeignKey(
        Produto,
        on_delete=models.PROTECT,
        related_name='movimentos',
        verbose_name='Produto',
    )
    local_origem = models.ForeignKey(
        LocalEstoque,
        on_delete=models.PROTECT,
        related_name='movimentos_origem',
        verbose_name='Local de Origem',
        null=True,
        blank=True,
    )
    local_destino = models.ForeignKey(
        LocalEstoque,
        on_delete=models.PROTECT,
        related_name='movimentos_destino',
        verbose_name='Local de Destino',
        null=True,
        blank=True,
    )
    tipo_movimento = models.CharField('Tipo de Movimento', max_length=20, choices=TIPO_MOVIMENTO_CHOICES)
    quantidade = models.DecimalField(
        'Quantidade',
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    custo_unitario = models.DecimalField(
        'Custo Unitário',
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        help_text='Custo unitário no momento da movimentação (obrigatório em entradas com valoração)',
    )
    data_movimento = models.DateTimeField('Data do Movimento', auto_now_add=True)
    referencia = models.CharField(
        'Referência',
        max_length=100,
        blank=True,
        null=True,
        help_text='ID de pedido, nota, etc.'
    )
    observacao = models.TextField('Observação', blank=True, null=True)
    
    class Meta:
        verbose_name = 'Movimento de Estoque'
        verbose_name_plural = 'Movimentos de Estoque'
        ordering = ['-data_movimento']
        indexes = [
            models.Index(fields=['-data_movimento']),
            models.Index(fields=['produto', '-data_movimento']),
            models.Index(fields=['tipo_movimento', '-data_movimento']),
        ]
    
    def __str__(self):
        return f"{self.tipo_movimento} - {self.produto.codigo_interno} - {self.quantidade}"


class TransferenciaInterempresa(BaseModel):
    """
    Registro de transferência de estoque entre duas empresas (CNPJs distintos).

    Fluxo simplificado (sem NF-e):
    - Gera MovimentoEstoque SAIDA na empresa origem
    - Gera MovimentoEstoque ENTRADA na empresa destino
    - Registra custo_unitario para atualizar custo médio do destino

    Futura integração fiscal: adicionar campos nota_saida/nota_entrada FKs.
    """

    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('CONCLUIDA', 'Concluída'),
        ('CANCELADA', 'Cancelada'),
    ]

    empresa_origem = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name='transferencias_enviadas',
        verbose_name='Empresa Origem',
    )
    empresa_destino = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name='transferencias_recebidas',
        verbose_name='Empresa Destino',
    )
    local_origem = models.ForeignKey(
        LocalEstoque,
        on_delete=models.PROTECT,
        related_name='transferencias_saida',
        verbose_name='Local de Origem',
    )
    local_destino = models.ForeignKey(
        LocalEstoque,
        on_delete=models.PROTECT,
        related_name='transferencias_entrada',
        verbose_name='Local de Destino',
    )
    produto = models.ForeignKey(
        Produto,
        on_delete=models.PROTECT,
        related_name='transferencias_interempresa',
        verbose_name='Produto',
    )
    quantidade = models.DecimalField(
        'Quantidade',
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))],
    )
    custo_unitario = models.DecimalField(
        'Custo Unitário',
        max_digits=10,
        decimal_places=4,
        help_text='Custo usado para atualizar custo médio na empresa destino',
    )
    status = models.CharField(
        'Status',
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDENTE',
    )
    movimento_saida = models.OneToOneField(
        MovimentoEstoque,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='transferencia_saida',
        verbose_name='Movimento de Saída',
    )
    movimento_entrada = models.OneToOneField(
        MovimentoEstoque,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='transferencia_entrada',
        verbose_name='Movimento de Entrada',
    )
    observacao = models.TextField('Observação', blank=True, null=True)

    class Meta:
        verbose_name = 'Transferência Interempresa'
        verbose_name_plural = 'Transferências Interempresa'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['empresa_origem', 'status']),
            models.Index(fields=['empresa_destino', 'status']),
            models.Index(fields=['produto', '-created_at']),
        ]

    def __str__(self):
        oid = self.pk or '—'
        return (
            f"Transferência #{oid} "
            f"{self.empresa_origem.nome_fantasia} → {self.empresa_destino.nome_fantasia} "
            f"| {self.produto.codigo_interno} x {self.quantidade} [{self.status}]"
        )


class EstoqueValorado(BaseModel):
    """
    Custo médio ponderado de um produto por empresa.
    Atualizado a cada MovimentoEstoque de entrada (com custo) e sincronizado em saídas/ajustes.
    """

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='estoques_valorados',
        verbose_name='Empresa',
    )
    produto = models.ForeignKey(
        Produto,
        on_delete=models.CASCADE,
        related_name='estoques_valorados',
        verbose_name='Produto',
    )
    custo_medio = models.DecimalField(
        'Custo Médio',
        max_digits=10,
        decimal_places=4,
        default=Decimal('0.0000'),
    )
    quantidade_total = models.DecimalField(
        'Quantidade Total em Estoque',
        max_digits=10,
        decimal_places=3,
        default=Decimal('0.000'),
        help_text='Soma das quantidades em todos os locais desta empresa',
    )
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Estoque Valorado'
        verbose_name_plural = 'Estoques Valorados'
        unique_together = [['empresa', 'produto']]
        indexes = [
            models.Index(fields=['empresa', 'produto']),
        ]

    def __str__(self):
        return (
            f"{self.produto.codigo_interno} @ {self.empresa.nome_fantasia}: "
            f"CM={self.custo_medio} Qtd={self.quantidade_total}"
        )
