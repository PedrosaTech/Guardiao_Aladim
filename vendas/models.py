"""
Modelos do módulo de vendas.
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.conf import settings
from decimal import Decimal, ROUND_HALF_UP
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
        ('AGUARDANDO_PAGAMENTO', 'Aguardando Pagamento'),
        ('ABANDONADO', 'Abandonado'),
    ]

    ORIGEM_CHOICES = [
        ('CAIXA', 'Caixa (PDV)'),
        ('TABLET', 'PDV Móvel (Tablet)'),
        ('ECOMMERCE', 'E-commerce'),
        ('WHATSAPP', 'WhatsApp'),
    ]

    FORMA_PAGAMENTO_PRETENDIDA_CHOICES = [
        ('NAO_INFORMADO', 'Não Informado'),
        ('DINHEIRO', 'Dinheiro'),
        ('CARTAO_DEBITO', 'Cartão Débito'),
        ('CARTAO_CREDITO', 'Cartão Crédito'),
        ('PIX', 'PIX'),
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

    # PDV Móvel - origem e atendente tablet
    origem = models.CharField(
        'Origem do Pedido',
        max_length=20,
        choices=ORIGEM_CHOICES,
        default='CAIXA',
        help_text='Canal de origem do pedido',
    )
    atendente_tablet = models.ForeignKey(
        'pdv_movel.AtendentePDV',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pedidos_tablet',
        verbose_name='Atendente (Tablet)',
        help_text='Atendente que criou o pedido no tablet',
    )
    forma_pagamento_pretendida = models.CharField(
        'Forma de Pagamento Pretendida',
        max_length=20,
        choices=FORMA_PAGAMENTO_PRETENDIDA_CHOICES,
        default='NAO_INFORMADO',
        blank=True,
        help_text='Forma que o cliente pretende usar (informativa; pode ser alterada no caixa)',
    )

    # Cupom fiscal (tablet -> balcão)
    emitir_cupom_fiscal = models.BooleanField(
        'Emitir Cupom Fiscal',
        default=False,
        help_text='Se deve emitir documento fiscal (SAT/NFC-e)',
    )
    cpf_cnpj_nota = models.CharField(
        'CPF/CNPJ na Nota',
        max_length=20,
        blank=True,
        null=True,
        help_text='CPF ou CNPJ para incluir no documento fiscal',
    )
    numero_cupom_fiscal = models.CharField(
        'Número do Cupom Fiscal',
        max_length=100,
        blank=True,
        null=True,
        help_text='Número do cupom SAT ou chave NFC-e gerada',
    )
    data_emissao_cupom = models.DateTimeField(
        'Data Emissão Cupom',
        null=True,
        blank=True,
        help_text='Data/hora de emissão do documento fiscal',
    )

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

    # Rastreio do código usado (principal ou alternativo)
    # Obs: manter max_length=50 para compatibilidade com Produto.codigo_barras
    # e evitar problemas em dados antigos.
    codigo_barras_usado = models.CharField(
        'Código de Barras Usado',
        max_length=50,
        blank=True,
        null=True,
        help_text='Código escaneado/digitado na venda (principal ou alternativo).',
    )
    codigo_alternativo_usado = models.ForeignKey(
        'produtos.CodigoBarrasAlternativo',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vendas_registradas',
        verbose_name='Código Alternativo Usado',
        help_text='Se foi usado um código alternativo, referência do cadastro.',
    )
    multiplicador_aplicado = models.DecimalField(
        'Multiplicador Aplicado',
        max_digits=10,
        decimal_places=3,
        default=Decimal('1.000'),
        validators=[MinValueValidator(Decimal('0.001'))],
        help_text='Snapshot do multiplicador no momento da venda (informativo/histórico).',
    )
    
    class Meta:
        verbose_name = 'Item do Pedido de Venda'
        verbose_name_plural = 'Itens dos Pedidos de Venda'
        ordering = ['pedido', 'id']
        indexes = [
            models.Index(fields=['codigo_barras_usado'], name='item_codigo_usado_idx'),
            models.Index(fields=['codigo_alternativo_usado'], name='item_codigo_alt_idx'),
            models.Index(fields=['codigo_alternativo_usado', 'created_at'], name='item_alt_created_idx'),
        ]
    
    def __str__(self):
        return f"{self.pedido} - {self.produto.descricao} x {self.quantidade}"

    def clean(self):
        super().clean()
        # Integridade: se apontar para um código alternativo, ele deve ser do mesmo produto.
        if self.codigo_alternativo_usado_id and self.produto_id:
            if self.codigo_alternativo_usado.produto_id != self.produto_id:
                raise ValidationError(
                    f'Código alternativo "{self.codigo_alternativo_usado.codigo_barras}" '
                    f'não pertence ao produto "{self.produto.descricao}".'
                )
    
    def save(self, *args, **kwargs):
        """
        Calcula o total do item antes de salvar.
        """
        self.total = (self.preco_unitario * self.quantidade) - self.desconto
        # total é armazenado com 2 casas decimais
        try:
            self.total = Decimal(self.total).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        except Exception:
            # deixa o Django validar/lançar erro se for inválido
            pass
        # Garante validações (inclui clean() acima) antes de persistir.
        self.full_clean()
        super().save(*args, **kwargs)
        # Recalcula o total do pedido
        if self.pedido:
            self.pedido.recalcular_total()

