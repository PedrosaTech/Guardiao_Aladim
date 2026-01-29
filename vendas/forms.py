"""
Forms para relatórios de vendas.
"""
from datetime import timedelta

from django import forms
from django.utils import timezone

from core.models import Loja
from pessoas.models import Cliente, Fornecedor
from produtos.models import CategoriaProduto, Produto


class RelatorioVendasForm(forms.Form):
    """Filtros do relatório de vendas consolidado (somente FATURADO)."""

    data_inicio = forms.DateField(
        label='Data Início',
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    data_fim = forms.DateField(
        label='Data Fim',
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )

    produto = forms.ModelChoiceField(
        label='Produto',
        queryset=Produto.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    categoria = forms.ModelChoiceField(
        label='Categoria',
        queryset=CategoriaProduto.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    loja = forms.ModelChoiceField(
        label='Loja',
        queryset=Loja.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    cliente = forms.ModelChoiceField(
        label='Cliente',
        queryset=Cliente.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    fornecedor = forms.ModelChoiceField(
        label='Fornecedor (Código Alternativo)',
        queryset=Fornecedor.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Filtra itens vendidos usando código alternativo vinculado ao fornecedor.',
    )
    classe_risco = forms.ChoiceField(
        label='Classe de Risco',
        required=False,
        choices=[('', 'Todas')] + list(Produto.CLASSE_RISCO_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    agrupar_por = forms.ChoiceField(
        label='Agrupar Por',
        choices=[
            ('produto', 'Produto'),
            ('categoria', 'Categoria'),
            ('fornecedor', 'Fornecedor (código alternativo usado)'),
            ('cliente', 'Cliente'),
            ('dia', 'Dia'),
            ('mes', 'Mês'),
        ],
        initial='produto',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    ordenar_por = forms.ChoiceField(
        label='Ordenar Por',
        choices=[
            ('-quantidade', 'Quantidade (Maior → Menor)'),
            ('quantidade', 'Quantidade (Menor → Maior)'),
            ('-valor_total', 'Valor (Maior → Menor)'),
            ('valor_total', 'Valor (Menor → Maior)'),
            ('nome', 'Nome (A → Z)'),
            ('-nome', 'Nome (Z → A)'),
        ],
        initial='-valor_total',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)

        # Padrão: últimos 30 dias
        if not (self.data.get('data_inicio') or self.initial.get('data_inicio')):
            self.fields['data_inicio'].initial = timezone.now().date() - timedelta(days=30)
        if not (self.data.get('data_fim') or self.initial.get('data_fim')):
            self.fields['data_fim'].initial = timezone.now().date()

        produtos = Produto.objects.filter(is_active=True)
        categorias = CategoriaProduto.objects.filter(is_active=True)
        lojas = Loja.objects.filter(is_active=True)
        clientes = Cliente.objects.filter(is_active=True)
        fornecedores = Fornecedor.objects.filter(is_active=True)

        if empresa:
            produtos = produtos.filter(empresa=empresa)
            categorias = categorias.filter(empresa=empresa)
            lojas = lojas.filter(empresa=empresa)
            clientes = clientes.filter(empresa=empresa)
            fornecedores = fornecedores.filter(empresa=empresa)

        self.fields['produto'].queryset = produtos.order_by('descricao')
        self.fields['categoria'].queryset = categorias.order_by('nome')
        self.fields['loja'].queryset = lojas.order_by('nome')
        self.fields['cliente'].queryset = clientes.order_by('nome_razao_social')
        self.fields['fornecedor'].queryset = fornecedores.order_by('razao_social')

