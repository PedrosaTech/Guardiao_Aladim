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
    cnpj = EncryptedCharField('CNPJ', max_length=255)  # 255 para valor criptografado no DB
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
    
    # ═══════════════════════════════════════════════════════════
    # REFORMA TRIBUTÁRIA 2026
    # ═══════════════════════════════════════════════════════════
    
    usar_reforma_2026 = models.BooleanField(
        'Ativar Reforma 2026',
        default=False,  # CRÍTICO: começa desligado
        help_text=(
            'Ativa o cálculo de CBS e IBS conforme Reforma Tributária. '
            'Desligado = sistema funciona como antes. '
            'Ligado = inclui CBS/IBS nos cálculos e notas.'
        )
    )
    
    aliquota_ibs_padrao_2026 = models.DecimalField(
        'Alíquota IBS Padrão 2026',
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.10'),
        help_text='Alíquota padrão do IBS quando produto não especificar (fase teste: 0,10%)'
    )
    
    aliquota_cbs_padrao_2026 = models.DecimalField(
        'Alíquota CBS Padrão 2026',
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.90'),
        help_text='Alíquota padrão da CBS quando produto não especificar (fase teste: 0,90%)'
    )
    
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
    
    # ═══════════════════════════════════════════════════════════
    # REFORMA TRIBUTÁRIA 2026 - Cache de Impostos
    # Valores CONGELADOS no momento da autorização
    # ═══════════════════════════════════════════════════════════
    
    base_ibs_total = models.DecimalField(
        'Base IBS Total (Cache)',
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Valor CONGELADO no momento da autorização - não recalcular'
    )
    
    valor_ibs_total = models.DecimalField(
        'Valor IBS Total (Cache)',
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    base_cbs_total = models.DecimalField(
        'Base CBS Total (Cache)',
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    valor_cbs_total = models.DecimalField(
        'Valor CBS Total (Cache)',
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Snapshot completo dos impostos por item (JSON)
    # Armazena estado imutável dos impostos no momento da autorização
    impostos_snapshot = models.JSONField(
        'Snapshot Impostos',
        null=True,
        blank=True,
        help_text='JSON com impostos por item no momento da autorização (imutável)'
    )
    
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
    
    def gravar_snapshot_impostos(self, config_fiscal=None):
        """
        Grava snapshot dos impostos no momento da autorização.
        
        IMPORTANTE: Após autorização, valores não devem ser recalculados.
        Este método deve ser chamado APENAS quando a nota for autorizada pela SEFAZ.
        
        Args:
            config_fiscal: ConfiguracaoFiscalLoja (opcional, busca automaticamente se None)
        """
        from fiscal.calculos import calcular_impostos_nota, calcular_impostos_item
        
        if not self.pedido_venda:
            raise ValueError("Nota deve ter pedido_venda para gravar snapshot")
        
        # Buscar config se não fornecida
        if not config_fiscal:
            try:
                config_fiscal = self.loja.configuracao_fiscal
            except:
                config_fiscal = None
        
        itens = self.pedido_venda.itens.filter(is_active=True)
        regime = config_fiscal.regime_tributario if config_fiscal else None
        
        # Calcular totais
        totais = calcular_impostos_nota(itens, regime, config_fiscal)
        
        # Gravar cache de totais
        self.base_ibs_total = totais.get('base_ibs', Decimal('0.00'))
        self.valor_ibs_total = totais.get('valor_ibs', Decimal('0.00'))
        self.base_cbs_total = totais.get('base_cbs', Decimal('0.00'))
        self.valor_cbs_total = totais.get('valor_cbs', Decimal('0.00'))
        
        # Gravar snapshot por item
        snapshot = []
        for item in itens:
            impostos_item = calcular_impostos_item(item, regime, config_fiscal)
            
            snapshot.append({
                'item_id': item.id,
                'produto_id': item.produto_id if hasattr(item, 'produto_id') else None,
                'servico_id': item.servico_id if hasattr(item, 'servico_id') else None,
                'descricao': item.get_descricao() if hasattr(item, 'get_descricao') else (
                    item.produto.descricao if item.produto else item.servico.nome if hasattr(item, 'servico') and item.servico else 'Item'
                ),
                'quantidade': float(item.quantidade),
                'valor_unitario': float(item.preco_unitario),
                'valor_total': float(item.total),
                'impostos': {
                    k: float(v) if isinstance(v, Decimal) else v 
                    for k, v in impostos_item.items()
                }
            })
        
        self.impostos_snapshot = snapshot
        self.save(update_fields=[
            'base_ibs_total', 'valor_ibs_total', 
            'base_cbs_total', 'valor_cbs_total',
            'impostos_snapshot', 'updated_at'
        ])
    
    def get_impostos(self, recalcular=False):
        """
        Retorna impostos da nota.
        
        Lógica:
        - Se nota AUTORIZADA e tem snapshot: usa snapshot (valores imutáveis)
        - Se nota RASCUNHO ou recalcular=True: calcula em tempo real
        
        Args:
            recalcular: Se True, força recálculo mesmo se autorizada
        
        Returns:
            dict com impostos (formato igual calcular_impostos_nota)
        """
        # CORREÇÃO 3: Validar se snapshot não está vazio
        # CT-013: Recuperação graciosa de snapshot corrompido
        if (self.status == 'AUTORIZADA' and 
            self.impostos_snapshot and 
            len(self.impostos_snapshot) > 0 and 
            not recalcular):
            try:
                # Reconstruir dict de totais a partir do snapshot
                totais = {
                    'base_icms': Decimal('0.00'),
                    'valor_icms': Decimal('0.00'),
                    'base_icms_st': Decimal('0.00'),
                    'valor_icms_st': Decimal('0.00'),
                    'base_pis': Decimal('0.00'),
                    'valor_pis': Decimal('0.00'),
                    'base_cofins': Decimal('0.00'),
                    'valor_cofins': Decimal('0.00'),
                    'base_ipi': Decimal('0.00'),
                    'valor_ipi': Decimal('0.00'),
                    'base_ibs': self.base_ibs_total or Decimal('0.00'),
                    'valor_ibs': self.valor_ibs_total or Decimal('0.00'),
                    'base_cbs': self.base_cbs_total or Decimal('0.00'),
                    'valor_cbs': self.valor_cbs_total or Decimal('0.00'),
                    'valor_produtos': Decimal('0.00'),
                    'valor_frete': Decimal('0.00'),
                    'valor_seguro': Decimal('0.00'),
                    'valor_desconto': Decimal('0.00'),
                    'valor_outras_despesas': Decimal('0.00'),
                }
                
                # Somar totais do snapshot
                for item_snapshot in self.impostos_snapshot:
                    impostos = item_snapshot.get('impostos')
                    if not isinstance(impostos, dict):
                        raise ValueError("Snapshot item sem 'impostos' válido")
                    totais['base_icms'] += Decimal(str(impostos.get('base_icms', 0)))
                    totais['valor_icms'] += Decimal(str(impostos.get('valor_icms', 0)))
                    totais['base_icms_st'] += Decimal(str(impostos.get('base_icms_st', 0)))
                    totais['valor_icms_st'] += Decimal(str(impostos.get('valor_icms_st', 0)))
                    totais['base_pis'] += Decimal(str(impostos.get('base_pis', 0)))
                    totais['valor_pis'] += Decimal(str(impostos.get('valor_pis', 0)))
                    totais['base_cofins'] += Decimal(str(impostos.get('base_cofins', 0)))
                    totais['valor_cofins'] += Decimal(str(impostos.get('valor_cofins', 0)))
                    totais['base_ipi'] += Decimal(str(impostos.get('base_ipi', 0)))
                    totais['valor_ipi'] += Decimal(str(impostos.get('valor_ipi', 0)))
                    totais['valor_produtos'] += Decimal(str(item_snapshot.get('valor_total', 0)))
                
                # Adicionar flags
                config_fiscal = getattr(self.loja, 'configuracao_fiscal', None)
                regime = config_fiscal.regime_tributario if config_fiscal else None
                totais['regime_tributario'] = regime or ''
                totais['is_simples_nacional'] = regime and 'SIMPLES' in regime.upper()
                
                return totais
            except (KeyError, ValueError, TypeError, Exception) as e:
                import logging
                logging.getLogger(__name__).warning(
                    "Snapshot de impostos inválido (nota %s): %s. Recalculando.",
                    self.id, e
                )
                # Fallback: recalcular em tempo real (CT-013)
        
        # Calcular em tempo real (rascunho, forçado ou snapshot falhou)
        from fiscal.calculos import calcular_impostos_nota
        
        if not self.pedido_venda:
            return {
                'base_icms': Decimal('0.00'),
                'valor_icms': Decimal('0.00'),
                'base_icms_st': Decimal('0.00'),
                'valor_icms_st': Decimal('0.00'),
                'base_pis': Decimal('0.00'),
                'valor_pis': Decimal('0.00'),
                'base_cofins': Decimal('0.00'),
                'valor_cofins': Decimal('0.00'),
                'base_ipi': Decimal('0.00'),
                'valor_ipi': Decimal('0.00'),
                'base_ibs': Decimal('0.00'),
                'valor_ibs': Decimal('0.00'),
                'base_cbs': Decimal('0.00'),
                'valor_cbs': Decimal('0.00'),
                'valor_produtos': Decimal('0.00'),
                'valor_frete': Decimal('0.00'),
                'valor_seguro': Decimal('0.00'),
                'valor_desconto': Decimal('0.00'),
                'valor_outras_despesas': Decimal('0.00'),
                'regime_tributario': '',
                'is_simples_nacional': False,
            }
        
        config_fiscal = getattr(self.loja, 'configuracao_fiscal', None)
        itens = self.pedido_venda.itens.filter(is_active=True)
        regime = config_fiscal.regime_tributario if config_fiscal else None
        return calcular_impostos_nota(itens, regime, config_fiscal)
    
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

