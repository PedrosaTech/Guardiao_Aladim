"""
Forms do módulo fiscal.
"""
from django import forms
from django.forms import formset_factory, BaseFormSet
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date

from .models import NotaFiscalEntrada, ItemNotaFiscalEntrada
from pessoas.models import Fornecedor
from core.models import Loja
from produtos.models import Produto


class NotaFiscalEntradaForm(forms.ModelForm):
    """Formulário para digitação manual de Nota Fiscal de Entrada."""

    class Meta:
        model = NotaFiscalEntrada
        fields = [
            'loja', 'fornecedor', 'numero', 'serie', 'chave_acesso',
            'valor_total', 'data_emissao', 'data_entrada'
        ]
        widgets = {
            'loja': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'fornecedor': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'numero': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'required': True,
                'placeholder': 'Ex: 12345',
            }),
            'serie': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': 3,
                'required': True,
                'placeholder': 'Ex: 001',
            }),
            'chave_acesso': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': 44,
                'required': True,
                'placeholder': '44 dígitos da chave de acesso',
            }),
            'valor_total': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'required': True,
            }),
            'data_emissao': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'required': True,
            }),
            'data_entrada': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'required': True,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['loja'].queryset = Loja.objects.filter(is_active=True)
        self.fields['fornecedor'].queryset = Fornecedor.objects.filter(is_active=True)

        if not self.instance.pk:
            self.fields['data_entrada'].initial = date.today()
            self.fields['data_emissao'].initial = date.today()

    def clean_chave_acesso(self):
        chave = self.cleaned_data.get('chave_acesso', '').strip()
        if chave and len(chave) != 44:
            raise ValidationError('A chave de acesso deve ter exatamente 44 dígitos.')
        if chave and not chave.isdigit():
            raise ValidationError('A chave de acesso deve conter apenas números.')
        return chave

    def clean_valor_total(self):
        valor = self.cleaned_data.get('valor_total')
        if valor is not None and valor <= 0:
            raise ValidationError('O valor total deve ser maior que zero.')
        return valor

    def clean_data_entrada(self):
        data_emissao = self.cleaned_data.get('data_emissao')
        data_entrada = self.cleaned_data.get('data_entrada')
        if data_emissao and data_entrada and data_entrada < data_emissao:
            raise ValidationError('A data de entrada não pode ser anterior à data de emissão.')
        return data_entrada


class ItemNotaFiscalEntradaForm(forms.Form):
    """
    Formulário para item de NF-e na digitação manual.
    Campos: produto, quantidade, preco_unitario, local_estoque (opcional).
    Formulários vazios são ignorados (formset permite linhas em branco).
    """
    produto = forms.ModelChoiceField(
        queryset=Produto.objects.none(),
        required=False,
        label='Produto',
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
    )
    quantidade = forms.DecimalField(
        min_value=Decimal('0.001'),
        max_digits=10,
        decimal_places=3,
        required=False,
        label='Quantidade',
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-sm',
            'step': '0.001',
            'placeholder': 'Ex: 10',
        })
    )
    preco_unitario = forms.DecimalField(
        min_value=Decimal('0.0001'),
        max_digits=12,
        decimal_places=4,
        required=False,
        label='Preço Unit.',
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-sm',
            'step': '0.0001',
            'placeholder': 'Ex: 1,50',
        })
    )
    local_estoque = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label='Local Estoque',
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'}),
        empty_label='(Padrão)'
    )

    def clean(self):
        data = super().clean()
        produto = data.get('produto')
        quantidade = data.get('quantidade')
        preco = data.get('preco_unitario')
        if produto or quantidade is not None or preco is not None:
            if not produto:
                raise ValidationError('Produto é obrigatório quando há quantidade ou preço.')
            if quantidade is None or quantidade <= 0:
                raise ValidationError('Quantidade inválida.')
            if preco is None or preco <= 0:
                raise ValidationError('Preço unitário inválido.')
        return data

    def __init__(self, *args, loja=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['produto'].queryset = Produto.objects.filter(is_active=True).order_by('descricao')
        if loja:
            from estoque.models import LocalEstoque
            self.fields['local_estoque'].queryset = LocalEstoque.objects.filter(
                loja=loja, is_active=True
            ).order_by('nome')
        else:
            from estoque.models import LocalEstoque
            self.fields['local_estoque'].queryset = LocalEstoque.objects.none()


class BaseItemNotaFiscalEntradaFormSet(BaseFormSet):
    """Formset que passa loja para cada form e valida totais."""

    def __init__(self, *args, loja=None, **kwargs):
        self.loja = loja
        super().__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        kwargs['loja'] = self.loja
        return super()._construct_form(i, **kwargs)

    def clean(self):
        from .services_entrada import validar_totais, TOLERANCIA_MANUAL

        itens_com_dados = [f for f in self.forms if f.cleaned_data and f.cleaned_data.get('produto')]
        if not itens_com_dados:
            return

        itens_valores = [
            cd['quantidade'] * cd['preco_unitario']
            for cd in (f.cleaned_data for f in itens_com_dados)
            if cd.get('produto')
        ]
        if not itens_valores:
            return

        valor_total_str = self.data.get('valor_total', '')
        if not valor_total_str:
            return
        try:
            nota_valor_total = Decimal(str(valor_total_str).replace(',', '.'))
        except (ValueError, TypeError):
            return

        validar_totais(nota_valor_total, itens_valores, tolerancia=TOLERANCIA_MANUAL)


ItemNotaFiscalEntradaFormSet = formset_factory(
    ItemNotaFiscalEntradaForm,
    formset=BaseItemNotaFiscalEntradaFormSet,
    extra=3,
    min_num=0,
    validate_min=True,
    max_num=50,
    validate_max=True,
)
