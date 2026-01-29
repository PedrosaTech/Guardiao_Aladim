# -*- coding: utf-8 -*-
"""
Forms para o app produtos.
"""
from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError

from core.models import Empresa, Loja
from .models import CategoriaProduto, CodigoBarrasAlternativo, Produto
from .utils import validar_codigo_barras_formato


class ProdutoForm(forms.ModelForm):
    """Formulário completo para edição de produto. codigo_interno editável via campo extra."""

    codigo_interno = forms.CharField(
        max_length=50,
        required=True,
        label='Código interno',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: BOMB0001 ou PROD-0001'}),
    )

    class Meta:
        model = Produto
        fields = [
            'empresa',
            'loja',
            'categoria',
            'codigo_barras',
            'descricao',
            'classe_risco',
            'subclasse_risco',
            'possui_restricao_exercito',
            'numero_certificado_exercito',
            'numero_lote',
            'validade',
            'condicoes_armazenamento',
            'ncm',
            'cest',
            'cfop_venda_dentro_uf',
            'cfop_venda_fora_uf',
            'unidade_comercial',
            'origem',
            'csosn_cst',
            'aliquota_icms',
            'icms_st_cst',
            'aliquota_icms_st',
            'pis_cst',
            'aliquota_pis',
            'cofins_cst',
            'aliquota_cofins',
            'ipi_venda_cst',
            'aliquota_ipi_venda',
            'ipi_compra_cst',
            'aliquota_ipi_compra',
            'cclass_trib',
            'cst_ibs',
            'cst_cbs',
            'aliquota_ibs',
            'aliquota_cbs',
            'preco_venda_sugerido',
            'observacoes',
        ]
        widgets = {
            'codigo_barras': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'EAN-13 (8, 12, 13 ou 14 dígitos)',
            }),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'validade': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'condicoes_armazenamento': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.codigo_interno:
            self.fields['codigo_interno'].initial = self.instance.codigo_interno
        self.fields['empresa'].queryset = Empresa.objects.filter(is_active=True)
        self.fields['loja'].queryset = Loja.objects.filter(is_active=True)
        self.fields['categoria'].queryset = CategoriaProduto.objects.filter(is_active=True)
        for name, field in self.fields.items():
            if 'class' in field.widget.attrs:
                continue
            if isinstance(field.widget, (forms.TextInput, forms.NumberInput, forms.DateInput)):
                field.widget.attrs['class'] = 'form-control'
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = 'form-control'

    def clean_codigo_interno(self):
        codigo = (self.cleaned_data.get('codigo_interno') or '').strip()
        if not codigo:
            raise ValidationError('Código interno é obrigatório.')

        empresa = self.cleaned_data.get('empresa')
        if not empresa and self.instance and self.instance.pk:
            empresa = self.instance.empresa
        if not empresa:
            return codigo

        qs = Produto.objects.filter(codigo_interno=codigo, is_active=True, empresa=empresa)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('Este código interno já está em uso nesta empresa.')
        return codigo

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.codigo_interno = self.cleaned_data['codigo_interno']
        if commit:
            obj.save()
        return obj

    def clean_codigo_barras(self):
        valor = (self.cleaned_data.get('codigo_barras') or '').strip()
        if not valor:
            return None
        ok, msg = validar_codigo_barras_formato(valor)
        if not ok:
            raise ValidationError(msg)
        return valor


class CodigoBarrasAlternativoForm(forms.ModelForm):
    """Formulário para adicionar/editar código alternativo."""

    class Meta:
        model = CodigoBarrasAlternativo
        fields = ['codigo_barras', 'descricao', 'multiplicador', 'fornecedor']
        widgets = {
            'codigo_barras': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'id_codigo_barras',
                'placeholder': '8, 12, 13 ou 14 dígitos',
            }),
            'descricao': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'id_descricao',
                'placeholder': 'Ex: Caixa 12 un, Código fornecedor',
            }),
            'multiplicador': forms.NumberInput(attrs={
                'class': 'form-control',
                'id': 'id_multiplicador',
                'step': '0.001',
                'min': '0.001',
                'value': '1.000',
            }),
            'fornecedor': forms.Select(attrs={
                'class': 'form-select',
                'style': 'display: none;',
            }),
        }

    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        from pessoas.models import Fornecedor
        if empresa:
            self.fields['fornecedor'].queryset = Fornecedor.objects.filter(
                empresa=empresa, is_active=True
            ).order_by('razao_social')
        else:
            self.fields['fornecedor'].queryset = Fornecedor.objects.none()
        self.fields['fornecedor'].required = False

    def clean_codigo_barras(self):
        valor = (self.cleaned_data.get('codigo_barras') or '').strip()
        if not valor:
            raise ValidationError('Código de barras é obrigatório.')
        ok, msg = validar_codigo_barras_formato(valor)
        if not ok:
            raise ValidationError(msg)
        return valor

    def clean_multiplicador(self):
        v = self.cleaned_data.get('multiplicador')
        if v is not None and v < Decimal('0.001'):
            raise ValidationError('Multiplicador deve ser >= 0,001.')
        return v or Decimal('1.000')
