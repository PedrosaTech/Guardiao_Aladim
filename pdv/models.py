"""
Modelos do módulo PDV (Ponto de Venda).
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings
from django.core.exceptions import ValidationError
from decimal import Decimal
from core.models import BaseModel, Loja
from vendas.models import PedidoVenda
from .validators import validar_cpf, formatar_cpf


class CaixaSessao(BaseModel):
    """
    Sessão de caixa (abertura e fechamento).
    """
    
    STATUS_CHOICES = [
        ('ABERTO', 'Aberto'),
        ('FECHADO', 'Fechado'),
    ]
    
    loja = models.ForeignKey(
        Loja,
        on_delete=models.PROTECT,
        related_name='sessoes_caixa',
        verbose_name='Loja',
    )
    usuario_abertura = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='sessoes_caixa_abertas',
        verbose_name='Usuário de Abertura',
    )
    data_hora_abertura = models.DateTimeField('Data/Hora de Abertura', auto_now_add=True)
    saldo_inicial = models.DecimalField(
        'Saldo Inicial',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    usuario_fechamento = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sessoes_caixa_fechadas',
        verbose_name='Usuário de Fechamento',
    )
    data_hora_fechamento = models.DateTimeField('Data/Hora de Fechamento', null=True, blank=True)
    saldo_final = models.DecimalField(
        'Saldo Final',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    status = models.CharField('Status', max_length=10, choices=STATUS_CHOICES, default='ABERTO')
    
    class Meta:
        verbose_name = 'Sessão de Caixa'
        verbose_name_plural = 'Sessões de Caixa'
        ordering = ['-data_hora_abertura']
        indexes = [
            models.Index(fields=['loja', 'status']),
            models.Index(fields=['usuario_abertura', '-data_hora_abertura']),
        ]
    
    def __str__(self):
        return f"Caixa {self.loja.nome} - {self.data_hora_abertura} - {self.status}"


class Pagamento(BaseModel):
    """
    Pagamento de um pedido de venda.
    """
    
    TIPO_CHOICES = [
        ('DINHEIRO', 'Dinheiro'),
        ('PIX', 'PIX'),
        ('CARTAO_CREDITO', 'Cartão de Crédito'),
        ('CARTAO_DEBITO', 'Cartão de Débito'),
    ]
    
    pedido = models.ForeignKey(
        PedidoVenda,
        on_delete=models.CASCADE,
        related_name='pagamentos',
        verbose_name='Pedido',
    )
    caixa_sessao = models.ForeignKey(
        CaixaSessao,
        on_delete=models.PROTECT,
        related_name='pagamentos',
        verbose_name='Sessão de Caixa',
    )
    tipo = models.CharField('Tipo de Pagamento', max_length=20, choices=TIPO_CHOICES)
    valor = models.DecimalField(
        'Valor',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    class Meta:
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['pedido']),
            models.Index(fields=['caixa_sessao', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.pedido} - {self.tipo} - {self.valor}"


class CompradorPirotecnia(BaseModel):
    """
    Dados do comprador de produtos pirotécnicos com restrição.
    
    Conforme R-105 do Exército Brasileiro, é obrigatório registrar:
    - CPF válido
    - Idade mínima 18 anos
    - Documento de identidade
    - Termo de responsabilidade
    - IP e timestamp do registro
    """
    
    TIPO_DOCUMENTO_CHOICES = [
        ('RG', 'RG - Registro Geral'),
        ('CNH', 'CNH - Carteira Nacional de Habilitação'),
        ('RNE', 'RNE - Registro Nacional de Estrangeiro'),
        ('PASSAPORTE', 'Passaporte'),
        ('OUTRO', 'Outro'),
    ]
    
    # Dados pessoais
    cpf = models.CharField('CPF', max_length=16, help_text='CPF formatado: 000.000.000-00')
    nome_completo = models.CharField('Nome Completo', max_length=255)
    data_nascimento = models.DateField('Data de Nascimento')
    
    def clean(self):
        """Valida CPF e idade antes de salvar."""
        from .validators import validar_cpf, validar_idade_minima
        super().clean()
        
        # Valida CPF
        try:
            cpf_limpo = validar_cpf(self.cpf)
            self.cpf = formatar_cpf(cpf_limpo)  # Formata para exibição
        except ValidationError as e:
            raise ValidationError({'cpf': str(e)})
        
        # Valida idade mínima
        try:
            validar_idade_minima(self.data_nascimento, idade_minima=18)
        except ValidationError as e:
            raise ValidationError({'data_nascimento': str(e)})
    
    def save(self, *args, **kwargs):
        """Salva o modelo após validação."""
        self.full_clean()
        super().save(*args, **kwargs)
    telefone = models.CharField('Telefone', max_length=20, blank=True, null=True)
    email = models.EmailField('E-mail', blank=True, null=True)
    
    # Documento de identidade
    tipo_documento = models.CharField(
        'Tipo de Documento',
        max_length=20,
        choices=TIPO_DOCUMENTO_CHOICES,
        default='RG'
    )
    numero_documento = models.CharField('Número do Documento', max_length=50)
    orgao_emissor = models.CharField('Órgão Emissor', max_length=20, blank=True, null=True)
    uf_emissor = models.CharField('UF Emissor', max_length=2, blank=True, null=True)
    
    # Endereço (opcional, mas recomendado)
    logradouro = models.CharField('Logradouro', max_length=255, blank=True, null=True)
    numero = models.CharField('Número', max_length=20, blank=True, null=True)
    complemento = models.CharField('Complemento', max_length=100, blank=True, null=True)
    bairro = models.CharField('Bairro', max_length=100, blank=True, null=True)
    cidade = models.CharField('Cidade', max_length=100, blank=True, null=True)
    uf = models.CharField('UF', max_length=2, blank=True, null=True)
    cep = models.CharField('CEP', max_length=10, blank=True, null=True)
    
    # Termo de responsabilidade
    aceite_termo = models.BooleanField('Aceite do Termo de Responsabilidade', default=False)
    data_aceite = models.DateTimeField('Data/Hora do Aceite', null=True, blank=True)
    ip_aceite = models.GenericIPAddressField('IP do Aceite', null=True, blank=True)
    
    # Auditoria adicional
    observacoes = models.TextField('Observações', blank=True, null=True)
    
    class Meta:
        verbose_name = 'Comprador de Produto Pirotécnico'
        verbose_name_plural = 'Compradores de Produtos Pirotécnicos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['cpf']),
            models.Index(fields=['data_nascimento']),
            models.Index(fields=['-created_at']),
        ]
    
    def calcular_idade(self):
        """Calcula a idade do comprador."""
        from datetime import date
        hoje = date.today()
        idade = hoje.year - self.data_nascimento.year
        if (hoje.month, hoje.day) < (self.data_nascimento.month, self.data_nascimento.day):
            idade -= 1
        return idade
    
    def is_maior_idade(self):
        """Verifica se o comprador é maior de 18 anos."""
        return self.calcular_idade() >= 18
    
    def __str__(self):
        return f"{self.nome_completo} - CPF: {self.cpf}"


class RegistroVendaPirotecnia(BaseModel):
    """
    Registro de venda de produto pirotécnico com restrição.
    
    Relaciona pedido, item, produto e comprador para auditoria completa.
    """
    
    pedido_venda = models.ForeignKey(
        PedidoVenda,
        on_delete=models.CASCADE,
        related_name='registros_pirotecnia',
        verbose_name='Pedido de Venda',
    )
    item_pedido = models.ForeignKey(
        'vendas.ItemPedidoVenda',
        on_delete=models.CASCADE,
        related_name='registros_pirotecnia',
        verbose_name='Item do Pedido',
        null=True,
        blank=True,
    )
    produto = models.ForeignKey(
        'produtos.Produto',
        on_delete=models.PROTECT,
        related_name='registros_venda_pirotecnia',
        verbose_name='Produto',
    )
    comprador = models.ForeignKey(
        CompradorPirotecnia,
        on_delete=models.PROTECT,
        related_name='registros_venda',
        verbose_name='Comprador',
    )
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
    valor_total = models.DecimalField(
        'Valor Total',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Informações adicionais
    numero_certificado_exercito = models.CharField(
        'Número do Certificado do Exército',
        max_length=50,
        blank=True,
        null=True,
        help_text='Número do certificado do produto vendido'
    )
    
    class Meta:
        verbose_name = 'Registro de Venda Pirotécnica'
        verbose_name_plural = 'Registros de Vendas Pirotécnicas'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['pedido_venda']),
            models.Index(fields=['comprador', '-created_at']),
            models.Index(fields=['produto', '-created_at']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.pedido_venda} - {self.produto.descricao} - {self.comprador.nome_completo}"
