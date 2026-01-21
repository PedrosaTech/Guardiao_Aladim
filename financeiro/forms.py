"""
Forms do módulo financeiro.
"""
from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date

from .models import TituloReceber, TituloPagar, ContaFinanceira
from pessoas.models import Cliente, Fornecedor
from core.models import Empresa, Loja


class TituloReceberForm(forms.ModelForm):
    """Form para criar/editar título a receber."""
    
    class Meta:
        model = TituloReceber
        fields = ['empresa', 'loja', 'cliente', 'conta_financeira', 'descricao', 
                  'numero_documento', 'valor', 'data_emissao', 'data_vencimento', 'status']
        widgets = {
            'empresa': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'loja': forms.Select(attrs={'class': 'form-control'}),
            'cliente': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'conta_financeira': forms.Select(attrs={'class': 'form-control'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'numero_documento': forms.TextInput(attrs={'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={
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
            'data_vencimento': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'required': True,
            }),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtra empresas ativas
        self.fields['empresa'].queryset = Empresa.objects.filter(is_active=True)
        
        # Se empresa selecionada, filtra lojas dessa empresa
        if self.instance and self.instance.pk and self.instance.empresa:
            self.fields['loja'].queryset = Loja.objects.filter(
                empresa=self.instance.empresa,
                is_active=True
            )
            self.fields['cliente'].queryset = Cliente.objects.filter(
                empresa=self.instance.empresa,
                is_active=True
            )
            self.fields['conta_financeira'].queryset = ContaFinanceira.objects.filter(
                empresa=self.instance.empresa,
                is_active=True
            )
        else:
            self.fields['loja'].queryset = Loja.objects.none()
            self.fields['cliente'].queryset = Cliente.objects.none()
            self.fields['conta_financeira'].queryset = ContaFinanceira.objects.none()
        
        # Valores padrão
        if not self.instance.pk:
            self.fields['data_emissao'].initial = date.today()
            self.fields['status'].initial = 'ABERTO'
    
    def clean_valor(self):
        valor = self.cleaned_data.get('valor')
        if valor and valor <= 0:
            raise ValidationError('Valor deve ser maior que zero.')
        return valor
    
    def clean_data_vencimento(self):
        data_emissao = self.cleaned_data.get('data_emissao')
        data_vencimento = self.cleaned_data.get('data_vencimento')
        
        if data_emissao and data_vencimento and data_vencimento < data_emissao:
            raise ValidationError('Data de vencimento não pode ser anterior à data de emissão.')
        
        return data_vencimento


class TituloPagarForm(forms.ModelForm):
    """Form para criar/editar título a pagar."""
    
    class Meta:
        model = TituloPagar
        fields = ['empresa', 'loja', 'fornecedor', 'descricao', 'valor', 
                  'data_emissao', 'data_vencimento', 'status']
        widgets = {
            'empresa': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'loja': forms.Select(attrs={'class': 'form-control'}),
            'fornecedor': forms.Select(attrs={'class': 'form-control'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'valor': forms.NumberInput(attrs={
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
            'data_vencimento': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'required': True,
            }),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        self.fields['empresa'].queryset = Empresa.objects.filter(is_active=True)
        
        if self.instance and self.instance.pk and self.instance.empresa:
            self.fields['loja'].queryset = Loja.objects.filter(
                empresa=self.instance.empresa,
                is_active=True
            )
            self.fields['fornecedor'].queryset = Fornecedor.objects.filter(
                empresa=self.instance.empresa,
                is_active=True
            )
        else:
            self.fields['loja'].queryset = Loja.objects.none()
            self.fields['fornecedor'].queryset = Fornecedor.objects.none()
        
        if not self.instance.pk:
            self.fields['data_emissao'].initial = date.today()
            self.fields['status'].initial = 'ABERTO'
    
    def clean_valor(self):
        valor = self.cleaned_data.get('valor')
        if valor and valor <= 0:
            raise ValidationError('Valor deve ser maior que zero.')
        return valor
    
    def clean_data_vencimento(self):
        data_emissao = self.cleaned_data.get('data_emissao')
        data_vencimento = self.cleaned_data.get('data_vencimento')
        
        if data_emissao and data_vencimento and data_vencimento < data_emissao:
            raise ValidationError('Data de vencimento não pode ser anterior à data de emissão.')
        
        return data_vencimento


class BaixaTituloReceberForm(forms.Form):
    """Form para baixa de título a receber."""
    
    data_pagamento = forms.DateField(
        label='Data de Pagamento',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'required': True,
        }),
        initial=lambda: date.today(),
    )
    
    valor_pago = forms.DecimalField(
        label='Valor Pago',
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0.01',
            'required': True,
        }),
    )
    
    conta_destino = forms.ModelChoiceField(
        label='Conta de Destino',
        queryset=ContaFinanceira.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': True,
        }),
    )
    
    valor_juros = forms.DecimalField(
        label='Juros',
        max_digits=12,
        decimal_places=2,
        required=False,
        initial=Decimal('0.00'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
        }),
    )
    
    valor_multa = forms.DecimalField(
        label='Multa',
        max_digits=12,
        decimal_places=2,
        required=False,
        initial=Decimal('0.00'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
        }),
    )
    
    valor_desconto = forms.DecimalField(
        label='Desconto',
        max_digits=12,
        decimal_places=2,
        required=False,
        initial=Decimal('0.00'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
        }),
    )
    
    observacoes = forms.CharField(
        label='Observações',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
        }),
    )
    
    def __init__(self, *args, **kwargs):
        titulo = kwargs.pop('titulo', None)
        super().__init__(*args, **kwargs)
        
        # Filtra contas pela empresa do título
        if titulo:
            self.fields['conta_destino'].queryset = ContaFinanceira.objects.filter(
                empresa=titulo.empresa,
                is_active=True
            )
            # Valor pago inicial é o valor do título
            self.fields['valor_pago'].initial = titulo.valor
        
        # Define data máxima como hoje
        self.fields['data_pagamento'].widget.attrs['max'] = date.today().isoformat()
    
    def clean_data_pagamento(self):
        """Valida que data de pagamento não é futura."""
        data_pagamento = self.cleaned_data.get('data_pagamento')
        if data_pagamento and data_pagamento > date.today():
            raise ValidationError('Data de pagamento não pode ser futura.')
        return data_pagamento
    
    def clean_valor_pago(self):
        """Valida que valor pago é positivo."""
        valor_pago = self.cleaned_data.get('valor_pago')
        if valor_pago and valor_pago <= 0:
            raise ValidationError('Valor pago deve ser maior que zero.')
        return valor_pago
    
    def clean(self):
        """Calcula valor total automaticamente."""
        cleaned_data = super().clean()
        valor_pago = cleaned_data.get('valor_pago', Decimal('0.00'))
        juros = cleaned_data.get('valor_juros', Decimal('0.00'))
        multa = cleaned_data.get('valor_multa', Decimal('0.00'))
        desconto = cleaned_data.get('valor_desconto', Decimal('0.00'))
        
        valor_total = valor_pago + juros + multa - desconto
        
        if valor_total <= 0:
            raise ValidationError('Valor total (valor pago + juros + multa - desconto) deve ser maior que zero.')
        
        cleaned_data['valor_total'] = valor_total
        return cleaned_data


class BaixaTituloPagarForm(forms.Form):
    """Form para baixa de título a pagar."""
    
    data_pagamento = forms.DateField(
        label='Data de Pagamento',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'required': True,
        }),
        initial=lambda: date.today(),
    )
    
    valor_pago = forms.DecimalField(
        label='Valor Pago',
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0.01',
            'required': True,
        }),
    )
    
    conta_origem = forms.ModelChoiceField(
        label='Conta de Origem',
        queryset=ContaFinanceira.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': True,
        }),
    )
    
    observacoes = forms.CharField(
        label='Observações',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
        }),
    )
    
    def __init__(self, *args, **kwargs):
        titulo = kwargs.pop('titulo', None)
        super().__init__(*args, **kwargs)
        
        if titulo:
            self.fields['conta_origem'].queryset = ContaFinanceira.objects.filter(
                empresa=titulo.empresa,
                is_active=True
            )
            self.fields['valor_pago'].initial = titulo.valor
        
        self.fields['data_pagamento'].widget.attrs['max'] = date.today().isoformat()
    
    def clean_data_pagamento(self):
        data_pagamento = self.cleaned_data.get('data_pagamento')
        if data_pagamento and data_pagamento > date.today():
            raise ValidationError('Data de pagamento não pode ser futura.')
        return data_pagamento
    
    def clean_valor_pago(self):
        valor_pago = self.cleaned_data.get('valor_pago')
        if valor_pago and valor_pago <= 0:
            raise ValidationError('Valor pago deve ser maior que zero.')
        return valor_pago


class FiltroTitulosForm(forms.Form):
    """Form para filtros de títulos."""
    
    status = forms.ChoiceField(
        label='Status',
        required=False,
        choices=[('', 'Todos')] + list(TituloReceber.STATUS_CHOICES),
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
    )
    
    cliente = forms.ModelChoiceField(
        label='Cliente',
        required=False,
        queryset=Cliente.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
    )
    
    data_inicio = forms.DateField(
        label='Data Início',
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        }),
    )
    
    data_fim = forms.DateField(
        label='Data Fim',
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        }),
    )
    
    def clean(self):
        """Valida que data início é menor que data fim."""
        cleaned_data = super().clean()
        data_inicio = cleaned_data.get('data_inicio')
        data_fim = cleaned_data.get('data_fim')
        
        if data_inicio and data_fim and data_inicio > data_fim:
            raise ValidationError('Data início deve ser menor que data fim.')
        
        return cleaned_data


class FiltroTitulosPagarForm(forms.Form):
    """Form para filtros de títulos a pagar."""
    
    status = forms.ChoiceField(
        label='Status',
        required=False,
        choices=[('', 'Todos')] + list(TituloPagar.STATUS_CHOICES),
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
    )
    
    fornecedor = forms.ModelChoiceField(
        label='Fornecedor',
        required=False,
        queryset=Fornecedor.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
    )
    
    data_inicio = forms.DateField(
        label='Data Início',
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        }),
    )
    
    data_fim = forms.DateField(
        label='Data Fim',
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        }),
    )
    
    def clean(self):
        cleaned_data = super().clean()
        data_inicio = cleaned_data.get('data_inicio')
        data_fim = cleaned_data.get('data_fim')
        
        if data_inicio and data_fim and data_inicio > data_fim:
            raise ValidationError('Data início deve ser menor que data fim.')
        
        return cleaned_data


class FiltroFluxoCaixaForm(forms.Form):
    """Form para filtros de fluxo de caixa."""
    
    data_inicio = forms.DateField(
        label='Data Início',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'required': True,
        }),
    )
    
    data_fim = forms.DateField(
        label='Data Fim',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'required': True,
        }),
    )
    
    conta_financeira = forms.ModelChoiceField(
        label='Conta Financeira',
        required=False,
        queryset=ContaFinanceira.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        empty_label='Todas as contas',
    )
    
    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        
        if empresa:
            self.fields['conta_financeira'].queryset = ContaFinanceira.objects.filter(
                empresa=empresa,
                is_active=True
            )
        
        # Valores padrão: últimos 30 dias
        from datetime import timedelta
        hoje = date.today()
        self.fields['data_inicio'].initial = hoje - timedelta(days=30)
        self.fields['data_fim'].initial = hoje
    
    def clean(self):
        cleaned_data = super().clean()
        data_inicio = cleaned_data.get('data_inicio')
        data_fim = cleaned_data.get('data_fim')
        
        if data_inicio and data_fim and data_inicio > data_fim:
            raise ValidationError('Data início deve ser menor que data fim.')
        
        return cleaned_data

