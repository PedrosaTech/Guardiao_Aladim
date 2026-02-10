"""
Modelos do módulo de orçamentos.
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from core.models import BaseModel
from core.fields import EncryptedCharField


class OrcamentoVenda(BaseModel):
    """
    Orçamento de venda.
    
    Pode ser convertido em PedidoVenda através do método converter_para_pedido().
    
    TODO: Ao converter orçamento em pedido, futura reserva de estoque (sem baixar estoque ainda).
    TODO: Orçamentos de origem EXTERNO vindo de app móvel.
    TODO: Integração com eventos (EventoVenda) para orçamentos de EVENTO (link futuro).
    """
    
    class OrigemChoices(models.TextChoices):
        BALCAO = 'BALCAO', 'Balcão'
        EXTERNO = 'EXTERNO', 'Externo'
        EVENTO = 'EVENTO', 'Evento'
        REVENDA = 'REVENDA', 'Revenda'
    
    class TipoOperacaoChoices(models.TextChoices):
        VAREJO = 'VAREJO', 'Varejo'
        ATACADO = 'ATACADO', 'Atacado'
        EVENTO_SHOW = 'EVENTO_SHOW', 'Evento/Show'
        REVENDER = 'REVENDER', 'Revender'
    
    class StatusChoices(models.TextChoices):
        RASCUNHO = 'RASCUNHO', 'Rascunho'
        ENVIADO = 'ENVIADO', 'Enviado'
        APROVADO = 'APROVADO', 'Aprovado'
        EXPIRADO = 'EXPIRADO', 'Expirado'
        CONVERTIDO = 'CONVERTIDO', 'Convertido'
        CANCELADO = 'CANCELADO', 'Cancelado'
    
    # Relacionamentos
    empresa = models.ForeignKey(
        'core.Empresa',
        on_delete=models.CASCADE,
        related_name='orcamentos',
        verbose_name='Empresa',
    )
    loja = models.ForeignKey(
        'core.Loja',
        on_delete=models.PROTECT,
        related_name='orcamentos',
        verbose_name='Loja',
    )
    cliente = models.ForeignKey(
        'pessoas.Cliente',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orcamentos',
        verbose_name='Cliente',
    )
    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='orcamentos_vendedor',
        verbose_name='Vendedor',
    )
    pedido_gerado = models.ForeignKey(
        'vendas.PedidoVenda',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orcamentos_origem',
        verbose_name='Pedido Gerado',
    )
    
    # Contato
    nome_responsavel = models.CharField('Nome do Responsável', max_length=255)
    telefone_contato = EncryptedCharField('Telefone de Contato', max_length=255, blank=True, null=True)
    whatsapp_contato = EncryptedCharField('WhatsApp de Contato', max_length=255, blank=True, null=True)
    email_contato = models.EmailField('E-mail de Contato', blank=True, null=True)
    
    # Classificação
    origem = models.CharField('Origem', max_length=20, choices=OrigemChoices.choices)
    tipo_operacao = models.CharField('Tipo de Operação', max_length=20, choices=TipoOperacaoChoices.choices)
    
    # Datas
    data_emissao = models.DateTimeField('Data de Emissão', default=timezone.now)
    data_validade = models.DateField('Data de Validade')
    
    # Status
    status = models.CharField(
        'Status',
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.RASCUNHO
    )
    
    # Valores
    total_bruto = models.DecimalField(
        'Total Bruto',
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    desconto_total = models.DecimalField(
        'Desconto Total',
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    acrescimo_total = models.DecimalField(
        'Acréscimo Total',
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    total_liquido = models.DecimalField(
        'Total Líquido',
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Outros
    condicao_pagamento_prevista = models.ForeignKey(
        'vendas.CondicaoPagamento',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orcamentos',
        verbose_name='Condição de Pagamento Prevista',
    )
    observacoes = models.TextField('Observações', blank=True)
    
    class Meta:
        verbose_name = 'Orçamento de Venda'
        verbose_name_plural = 'Orçamentos de Venda'
        ordering = ['-data_emissao', '-id']
        indexes = [
            models.Index(fields=['empresa', 'status']),
            models.Index(fields=['loja', 'status']),
            models.Index(fields=['cliente', '-data_emissao']),
            models.Index(fields=['vendedor', '-data_emissao']),
            models.Index(fields=['origem', 'status']),
        ]
    
    def __str__(self):
        return f"Orçamento #{self.id} - {self.nome_responsavel} - R$ {self.total_liquido}"
    
    def recalcular_totais(self):
        """
        Recalcula os totais do orçamento somando os valores dos itens ativos.
        """
        total_bruto = Decimal('0.00')
        
        for item in self.itens.filter(is_active=True):
            total_bruto += item.valor_total
        
        self.total_bruto = total_bruto
        self.total_liquido = total_bruto - self.desconto_total + self.acrescimo_total
        
        self.save(update_fields=['total_bruto', 'total_liquido', 'updated_at'])
        
        # Verificar e atualizar status se expirado
        hoje = timezone.now().date()
        if self.data_validade < hoje and self.status in [
            self.StatusChoices.RASCUNHO,
            self.StatusChoices.ENVIADO,
            self.StatusChoices.APROVADO
        ]:
            self.status = self.StatusChoices.EXPIRADO
            self.save(update_fields=['status'])
        
        return {
            'total_bruto': self.total_bruto,
            'desconto_total': self.desconto_total,
            'acrescimo_total': self.acrescimo_total,
            'total_liquido': self.total_liquido,
        }
    
    def converter_para_pedido(self) -> 'vendas.models.PedidoVenda':
        """
        Converte o orçamento em um PedidoVenda.
        
        Se já existir um pedido gerado, retorna esse pedido.
        Caso contrário, cria um novo pedido com os itens do orçamento.
        
        TODO: No futuro, podemos implementar reserva de estoque quando converter em pedido
        (sem baixar estoque ainda).
        
        Returns:
            PedidoVenda: O pedido gerado a partir do orçamento.
        """
        from vendas.models import PedidoVenda, ItemPedidoVenda, CondicaoPagamento
        
        # Se já existe pedido gerado, retornar
        if self.pedido_gerado:
            return self.pedido_gerado
        
        # Determinar condição de pagamento
        # Se o orçamento tem uma condição prevista, usar ela
        # Caso contrário, buscar uma condição padrão da empresa ou criar uma
        condicao_pagamento = self.condicao_pagamento_prevista
        
        if not condicao_pagamento:
            # Buscar uma condição de pagamento padrão da empresa (à vista, 1 parcela)
            condicao_pagamento = CondicaoPagamento.objects.filter(
                empresa=self.empresa,
                is_active=True,
                numero_parcelas=1,
                dias_entre_parcelas=0
            ).first()
            
            # Se não encontrar, criar uma condição padrão
            if not condicao_pagamento:
                condicao_pagamento = CondicaoPagamento.objects.create(
                    empresa=self.empresa,
                    nome='À Vista',
                    descricao='Pagamento à vista',
                    numero_parcelas=1,
                    dias_entre_parcelas=0,
                    created_by=self.created_by,
                )
        
        # Mapear origem para tipo_venda
        origem_tipo_venda_map = {
            self.OrigemChoices.BALCAO: 'BALCAO',
            self.OrigemChoices.EXTERNO: 'EXTERNA',
            self.OrigemChoices.EVENTO: 'EVENTO',
            self.OrigemChoices.REVENDA: 'EXTERNA',  # TODO: Adicionar REVENDA em PedidoVenda.TIPO_VENDA_CHOICES se necessário
        }
        
        tipo_venda = origem_tipo_venda_map.get(self.origem, 'EXTERNA')
        
        # Criar PedidoVenda
        pedido = PedidoVenda.objects.create(
            loja=self.loja,
            cliente=self.cliente,
            tipo_venda=tipo_venda,
            status='ORCAMENTO',  # Pedido começa como orçamento
            vendedor=self.vendedor,
            condicao_pagamento=condicao_pagamento,  # Agora sempre terá um valor
            valor_total=Decimal('0.00'),
            observacoes=f'Orçamento convertido do orçamento #{self.id}',
            created_by=self.created_by,
        )
        
        # Criar itens do pedido a partir dos itens do orçamento
        for item_orcamento in self.itens.filter(is_active=True):
            ItemPedidoVenda.objects.create(
                pedido=pedido,
                produto=item_orcamento.produto,
                quantidade=item_orcamento.quantidade,
                preco_unitario=item_orcamento.valor_unitario,
                desconto=item_orcamento.desconto,
                total=item_orcamento.valor_total,
                created_by=self.created_by,
            )
        
        # Recalcular total do pedido
        pedido.recalcular_total()
        
        # Associar pedido ao orçamento e atualizar status
        self.pedido_gerado = pedido
        self.status = self.StatusChoices.CONVERTIDO
        self.save(update_fields=['pedido_gerado', 'status', 'updated_at'])
        
        return pedido


class ItemOrcamentoVenda(BaseModel):
    """
    Item de um orçamento de venda.
    """
    orcamento = models.ForeignKey(
        OrcamentoVenda,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name='Orçamento',
    )
    produto = models.ForeignKey(
        'produtos.Produto',
        on_delete=models.PROTECT,
        related_name='itens_orcamento',
        verbose_name='Produto',
    )
    
    # Campos copiados do produto (snapshot no momento da criação)
    descricao_produto = models.CharField('Descrição do Produto', max_length=255)
    classe_risco = models.CharField('Classe de Risco', max_length=10)
    subclasse_risco = models.CharField('Subclasse de Risco', max_length=10, blank=True, null=True)
    
    # Valores
    quantidade = models.DecimalField(
        'Quantidade',
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    valor_unitario = models.DecimalField(
        'Valor Unitário',
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
    valor_total = models.DecimalField(
        'Valor Total',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    class Meta:
        verbose_name = 'Item do Orçamento de Venda'
        verbose_name_plural = 'Itens dos Orçamentos de Venda'
        ordering = ['orcamento', 'id']
    
    def __str__(self):
        return f"{self.orcamento} - {self.descricao_produto} x {self.quantidade}"
    
    def save(self, *args, **kwargs):
        """
        Calcula o valor total e copia dados do produto se necessário.
        """
        # Copiar dados do produto se estiverem vazios
        if not self.descricao_produto and self.produto:
            self.descricao_produto = self.produto.descricao
        
        if not self.classe_risco and self.produto:
            self.classe_risco = self.produto.classe_risco
        
        if not self.subclasse_risco and self.produto:
            self.subclasse_risco = self.produto.subclasse_risco or ''
        
        # Calcular valor total
        self.valor_total = (self.valor_unitario * self.quantidade) - self.desconto
        
        super().save(*args, **kwargs)
        
        # Recalcular totais do orçamento
        if self.orcamento:
            self.orcamento.recalcular_totais()
