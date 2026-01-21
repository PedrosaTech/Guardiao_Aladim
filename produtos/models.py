"""
Modelos de Produtos - Fogos de Artifício.
"""
import re
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from core.models import BaseModel, Empresa, Loja


class CategoriaProduto(BaseModel):
    """
    Categoria de produtos (ex: Bombas, Rojões, Kits, Vela, Foguete, Fonte).
    """
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='categorias_produto',
        verbose_name='Empresa',
    )
    nome = models.CharField('Nome', max_length=100)
    descricao = models.TextField('Descrição', blank=True, null=True)
    
    class Meta:
        verbose_name = 'Categoria de Produto'
        verbose_name_plural = 'Categorias de Produto'
        ordering = ['empresa', 'nome']
        unique_together = [['empresa', 'nome']]
    
    def __str__(self):
        return f"{self.empresa.nome_fantasia} - {self.nome}"


class Produto(BaseModel):
    """
    Produto - Fogo de Artifício.
    
    Requisitos de Pirotecnia:
    - TODO: Certos produtos podem exigir registro detalhado de comprador (ex.: categoria de risco maior)
    - TODO: Relatórios de estoque por classe de risco devem ser implementados
    - TODO: Validação de idade mínima do comprador para produtos com restrição
    - TODO: Registro de comprador para produtos com possui_restricao_exercito=True
    """
    
    CLASSE_RISCO_CHOICES = [
        ('1.1G', '1.1G – Explosivo com risco de explosão em massa'),
        ('1.2G', '1.2G – Explosivo com risco de projeção'),
        ('1.3G', '1.3G – Explosivo com risco de fogo intenso/projeção'),
        ('1.4G', '1.4G – Explosivo com baixo risco (uso comum / varejo)'),
        ('1.4S', '1.4S – Explosivo com risco muito reduzido'),
        ('OUTRA', 'OUTRA / NÃO APLICÁVEL (para itens não-explosivos, acessórios, suportes, etc.)'),
    ]
    
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='produtos',
        verbose_name='Empresa',
    )
    loja = models.ForeignKey(
        Loja,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='produtos',
        verbose_name='Loja',
    )
    categoria = models.ForeignKey(
        CategoriaProduto,
        on_delete=models.PROTECT,
        related_name='produtos',
        verbose_name='Categoria',
    )
    codigo_interno = models.CharField('Código Interno', max_length=50, blank=True, null=True, editable=False)
    codigo_barras = models.CharField('Código de Barras', max_length=50, blank=True, null=True)
    descricao = models.CharField('Descrição', max_length=255)
    
    # Campos específicos de fogos
    classe_risco = models.CharField(
        'Classe de Risco', 
        max_length=10, 
        choices=CLASSE_RISCO_CHOICES,
        help_text='Classificação de risco do produto conforme normas de transporte e armazenamento'
    )
    subclasse_risco = models.CharField('Subclasse de Risco', max_length=10, blank=True, null=True)
    possui_restricao_exercito = models.BooleanField('Possui Restrição de Exército', default=False)
    numero_certificado_exercito = models.CharField('Número do Certificado do Exército', max_length=50, blank=True, null=True)
    numero_lote = models.CharField('Número do Lote', max_length=50, blank=True, null=True)
    validade = models.DateField('Validade', blank=True, null=True)
    condicoes_armazenamento = models.TextField('Condições de Armazenamento', blank=True, null=True)
    
    # Campos fiscais - NCM e CEST
    ncm = models.CharField('NCM', max_length=10, help_text='Ex: 3604.10.00')
    cest = models.CharField('CEST', max_length=10, blank=True, null=True, help_text='Ex: 09.001.00')
    
    # Campos fiscais - CFOP
    cfop_venda_dentro_uf = models.CharField(
        'CFOP Venda Dentro UF', 
        max_length=4, 
        help_text='Ex: 5.102 (venda dentro do estado)'
    )
    cfop_venda_fora_uf = models.CharField(
        'CFOP Venda Fora UF', 
        max_length=4, 
        blank=True, 
        null=True,
        help_text='Ex: 6.102 (venda fora do estado)'
    )
    
    # Campos fiscais - Unidade e Origem
    unidade_comercial = models.CharField('Unidade Comercial', max_length=10, default='UN', help_text='Ex: CX, PC, UN')
    origem = models.CharField('Origem', max_length=1, default='0', help_text='TODO: Trocar por choices')
    
    # Campos fiscais - ICMS
    csosn_cst = models.CharField(
        'CSOSN / CST ICMS', 
        max_length=3,
        help_text='Ex: 102 (Simples) ou 00 (Regime Normal)'
    )
    aliquota_icms = models.DecimalField(
        'Alíquota ICMS (%)', 
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('18.00'),
        help_text='Ex: 18% (BA)'
    )
    
    # Campos fiscais - ICMS-ST (Substituição Tributária)
    icms_st_cst = models.CharField(
        'CST/CSOSN ICMS-ST', 
        max_length=3, 
        blank=True, 
        null=True,
        help_text='Ex: 10 (CST) ou 201 (CSOSN) - Somente se estado de destino exigir'
    )
    aliquota_icms_st = models.DecimalField(
        'Alíquota ICMS-ST (%)', 
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('0.00'),
        blank=True,
        null=True,
        help_text='Alíquota de ICMS-ST se aplicável'
    )
    
    # Campos fiscais - PIS
    pis_cst = models.CharField(
        'CST PIS', 
        max_length=2, 
        default='01',
        help_text='Ex: 01 (Operação Tributável com Alíquota Básica)'
    )
    aliquota_pis = models.DecimalField(
        'Alíquota PIS (%)', 
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('1.65'),
        help_text='Ex: 1,65%'
    )
    
    # Campos fiscais - COFINS
    cofins_cst = models.CharField(
        'CST COFINS', 
        max_length=2, 
        default='01',
        help_text='Ex: 01 (Operação Tributável com Alíquota Básica)'
    )
    aliquota_cofins = models.DecimalField(
        'Alíquota COFINS (%)', 
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('7.60'),
        help_text='Ex: 7,6%'
    )
    
    # Campos fiscais - IPI (Venda)
    ipi_venda_cst = models.CharField(
        'CST IPI Venda', 
        max_length=2, 
        default='52',
        help_text='Ex: 52 (Saída Tributada com Alíquota Zero)'
    )
    aliquota_ipi_venda = models.DecimalField(
        'Alíquota IPI Venda (%)', 
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text='Ex: 0% (geralmente zero na venda)'
    )
    
    # Campos fiscais - IPI (Compra)
    ipi_compra_cst = models.CharField(
        'CST IPI Compra', 
        max_length=2, 
        default='02',
        help_text='Ex: 02 (Entrada Tributada) - Conforme NF do fornecedor'
    )
    aliquota_ipi_compra = models.DecimalField(
        'Alíquota IPI Compra (%)', 
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('0.00'),
        blank=True,
        null=True,
        help_text='Conforme NF do fornecedor'
    )
    
    # Comercial
    preco_venda_sugerido = models.DecimalField(
        'Preço de Venda Sugerido',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    observacoes = models.TextField('Observações', blank=True, null=True)
    
    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['empresa', 'codigo_interno']
        unique_together = [['empresa', 'codigo_interno']]
        indexes = [
            models.Index(fields=['empresa', 'is_active']),
            models.Index(fields=['categoria', 'is_active']),
            models.Index(fields=['classe_risco', 'is_active']),
            models.Index(fields=['codigo_barras']),
        ]
    
    def save(self, *args, **kwargs):
        """
        Gera código interno automaticamente se não existir.
        Formato: PROD-0001, PROD-0002, etc. (sequencial por empresa)
        """
        if not self.codigo_interno:
            # Busca o último código da empresa
            ultimo_produto = Produto.objects.filter(
                empresa=self.empresa,
                codigo_interno__isnull=False
            ).exclude(
                codigo_interno=''
            ).order_by('-id').first()
            
            if ultimo_produto and ultimo_produto.codigo_interno:
                # Extrai o número do último código
                try:
                    # Tenta extrair número do formato PROD-0001
                    if '-' in ultimo_produto.codigo_interno:
                        prefixo, numero = ultimo_produto.codigo_interno.rsplit('-', 1)
                        proximo_numero = int(numero) + 1
                    else:
                        # Se não tiver formato, tenta extrair número do final
                        numeros = re.findall(r'\d+', ultimo_produto.codigo_interno)
                        if numeros:
                            proximo_numero = int(numeros[-1]) + 1
                        else:
                            proximo_numero = 1
                except (ValueError, AttributeError):
                    proximo_numero = 1
            else:
                proximo_numero = 1
            
            # Gera código no formato PROD-0001
            self.codigo_interno = f"PROD-{proximo_numero:04d}"
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.codigo_interno} - {self.descricao}"

