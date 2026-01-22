"""
Views do módulo financeiro.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import TemplateView, ListView, DetailView
from django.views.generic.edit import FormView, CreateView, UpdateView
from django.db.models import Sum, Q, Count
from django.utils import timezone
from django.http import JsonResponse
from decimal import Decimal
from datetime import date, timedelta
import json

from .models import TituloReceber, TituloPagar, ContaFinanceira, MovimentoFinanceiro
from .forms import (
    TituloReceberForm, TituloPagarForm,
    BaixaTituloReceberForm, BaixaTituloPagarForm,
    FiltroTitulosForm, FiltroTitulosPagarForm, FiltroFluxoCaixaForm
)
from .services.financial_service import FinancialService


from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required


@method_decorator(login_required, name='dispatch')
class DashboardFinanceiroView(TemplateView):
    """Dashboard financeiro com visão geral."""
    template_name = 'financeiro/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        hoje = date.today()
        proximos_30_dias = hoje + timedelta(days=30)
        
        # Títulos a receber
        a_receber_vencido = TituloReceber.objects.filter(
            status='ABERTO',
            data_vencimento__lt=hoje,
            is_active=True
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
        
        a_receber_hoje = TituloReceber.objects.filter(
            status='ABERTO',
            data_vencimento=hoje,
            is_active=True
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
        
        a_receber_30_dias = TituloReceber.objects.filter(
            status='ABERTO',
            data_vencimento__gte=hoje,
            data_vencimento__lte=proximos_30_dias,
            is_active=True
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
        
        # Títulos a pagar
        a_pagar_vencido = TituloPagar.objects.filter(
            status='ABERTO',
            data_vencimento__lt=hoje,
            is_active=True
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
        
        a_pagar_hoje = TituloPagar.objects.filter(
            status='ABERTO',
            data_vencimento=hoje,
            is_active=True
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
        
        # Saldo das contas
        contas = ContaFinanceira.objects.filter(is_active=True)
        saldo_contas = {}
        for conta in contas:
            saldo_contas[conta.nome] = FinancialService.get_saldo_atual(conta)
        
        saldo_total = FinancialService.get_saldo_atual()
        
        # Fluxo de caixa últimos 7 dias (para gráfico)
        data_inicio_grafico = hoje - timedelta(days=7)
        fluxo_7_dias = FinancialService.calcular_fluxo_caixa(data_inicio_grafico, hoje)
        
        # Próximos vencimentos (10 primeiros)
        proximos_vencimentos_receber = TituloReceber.objects.filter(
            status='ABERTO',
            data_vencimento__gte=hoje,
            is_active=True
        ).select_related('cliente').order_by('data_vencimento')[:10]
        
        proximos_vencimentos_pagar = TituloPagar.objects.filter(
            status='ABERTO',
            data_vencimento__gte=hoje,
            is_active=True
        ).select_related('fornecedor').order_by('data_vencimento')[:10]
        
        context.update({
            'a_receber_vencido': a_receber_vencido,
            'a_receber_hoje': a_receber_hoje,
            'a_receber_30_dias': a_receber_30_dias,
            'a_pagar_vencido': a_pagar_vencido,
            'a_pagar_hoje': a_pagar_hoje,
            'saldo_contas': saldo_contas,
            'saldo_total': saldo_total,
            'fluxo_7_dias': json.dumps([
                {
                    'data': item['data'].strftime('%d/%m'),
                    'entradas': float(item['entradas']),
                    'saidas': float(item['saidas']),
                    'saldo': float(item['saldo']),
                }
                for item in fluxo_7_dias
            ]),
            'proximos_vencimentos_receber': proximos_vencimentos_receber,
            'proximos_vencimentos_pagar': proximos_vencimentos_pagar,
        })
        
        return context


@method_decorator(login_required, name='dispatch')
class TituloReceberCreateView(CreateView):
    """Criar título a receber."""
    model = TituloReceber
    form_class = TituloReceberForm
    template_name = 'financeiro/titulo_receber_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f'Título a receber #{form.instance.id} criado com sucesso!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('financeiro:titulo_receber_detail', kwargs={'pk': self.object.pk})


@method_decorator(login_required, name='dispatch')
class TituloReceberUpdateView(UpdateView):
    """Editar título a receber."""
    model = TituloReceber
    form_class = TituloReceberForm
    template_name = 'financeiro/titulo_receber_form.html'
    
    def get_queryset(self):
        return TituloReceber.objects.filter(is_active=True)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        if form.instance.status == 'PAGO':
            messages.error(self.request, 'Não é possível editar título já recebido.')
            return redirect('financeiro:titulo_receber_detail', pk=form.instance.pk)
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Título atualizado com sucesso!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('financeiro:titulo_receber_detail', kwargs={'pk': self.object.pk})


class TituloReceberListView(ListView):
    """Lista de títulos a receber."""
    model = TituloReceber
    template_name = 'financeiro/titulos_receber_list.html'
    context_object_name = 'titulos'
    paginate_by = 50
    ordering = ['-data_vencimento']
    
    def get_queryset(self):
        queryset = TituloReceber.objects.filter(is_active=True).select_related(
            'cliente', 'loja', 'conta_financeira'
        )
        
        # Aplica filtros do form
        form = FiltroTitulosForm(self.request.GET)
        if form.is_valid():
            status = form.cleaned_data.get('status')
            cliente = form.cleaned_data.get('cliente')
            data_inicio = form.cleaned_data.get('data_inicio')
            data_fim = form.cleaned_data.get('data_fim')
            
            if status:
                queryset = queryset.filter(status=status)
            if cliente:
                queryset = queryset.filter(cliente=cliente)
            if data_inicio:
                queryset = queryset.filter(data_vencimento__gte=data_inicio)
            if data_fim:
                queryset = queryset.filter(data_vencimento__lte=data_fim)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_filtro'] = FiltroTitulosForm(self.request.GET)
        
        # Totalizadores
        queryset = self.get_queryset()
        context['total_aberto'] = queryset.filter(status='ABERTO').aggregate(
            total=Sum('valor')
        )['total'] or Decimal('0.00')
        
        context['total_pago'] = queryset.filter(status='PAGO').aggregate(
            total=Sum('valor')
        )['total'] or Decimal('0.00')
        
        return context


@method_decorator(login_required, name='dispatch')
class TituloReceberDetailView(DetailView):
    """Detalhes de um título a receber."""
    model = TituloReceber
    template_name = 'financeiro/titulo_receber_detail.html'
    context_object_name = 'titulo'
    
    def get_queryset(self):
        return TituloReceber.objects.filter(is_active=True).select_related(
            'cliente', 'loja', 'pedido_venda', 'conta_financeira'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        titulo = self.get_object()
        
        # Histórico de movimentos relacionados
        movimentos = MovimentoFinanceiro.objects.filter(
            titulo_receber=titulo
        ).order_by('-data_movimento')
        
        context['movimentos'] = movimentos
        context['form_baixa'] = BaixaTituloReceberForm(titulo=titulo)
        
        return context


@login_required
def baixar_titulo_receber(request, pk):
    """View para baixar título a receber."""
    titulo = get_object_or_404(TituloReceber, pk=pk, is_active=True)
    
    if titulo.status == 'PAGO':
        messages.error(request, 'Este título já foi recebido.')
        return redirect('financeiro:titulo_receber_detail', pk=pk)
    
    if request.method == 'POST':
        form = BaixaTituloReceberForm(request.POST, titulo=titulo)
        
        if form.is_valid():
            try:
                FinancialService.baixar_titulo_receber(
                    titulo_id=pk,
                    data_pagamento=form.cleaned_data['data_pagamento'],
                    valor_pago=form.cleaned_data['valor_pago'],
                    conta_destino=form.cleaned_data['conta_destino'],
                    juros=form.cleaned_data.get('valor_juros', Decimal('0.00')),
                    multa=form.cleaned_data.get('valor_multa', Decimal('0.00')),
                    desconto=form.cleaned_data.get('valor_desconto', Decimal('0.00')),
                    observacoes=form.cleaned_data.get('observacoes', ''),
                    created_by=request.user,
                )
                
                messages.success(request, f'Título #{titulo.id} baixado com sucesso!')
                return redirect('financeiro:titulo_receber_detail', pk=pk)
            
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f'Erro ao baixar título: {str(e)}')
    else:
        form = BaixaTituloReceberForm(titulo=titulo)
    
    return render(request, 'financeiro/titulo_receber_detail.html', {
        'titulo': titulo,
        'form_baixa': form,
        'movimentos': MovimentoFinanceiro.objects.filter(titulo_receber=titulo),
    })


@method_decorator(login_required, name='dispatch')
@method_decorator(login_required, name='dispatch')
class TituloPagarCreateView(CreateView):
    """Criar título a pagar."""
    model = TituloPagar
    form_class = TituloPagarForm
    template_name = 'financeiro/titulo_pagar_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f'Título a pagar #{form.instance.id} criado com sucesso!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('financeiro:titulo_pagar_detail', kwargs={'pk': self.object.pk})


@method_decorator(login_required, name='dispatch')
class TituloPagarUpdateView(UpdateView):
    """Editar título a pagar."""
    model = TituloPagar
    form_class = TituloPagarForm
    template_name = 'financeiro/titulo_pagar_form.html'
    
    def get_queryset(self):
        return TituloPagar.objects.filter(is_active=True)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        if form.instance.status == 'PAGO':
            messages.error(self.request, 'Não é possível editar título já pago.')
            return redirect('financeiro:titulo_pagar_detail', pk=form.instance.pk)
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Título atualizado com sucesso!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('financeiro:titulo_pagar_detail', kwargs={'pk': self.object.pk})


class TituloPagarListView(ListView):
    """Lista de títulos a pagar."""
    model = TituloPagar
    template_name = 'financeiro/titulos_pagar_list.html'
    context_object_name = 'titulos'
    paginate_by = 50
    ordering = ['-data_vencimento']
    
    def get_queryset(self):
        queryset = TituloPagar.objects.filter(is_active=True).select_related(
            'fornecedor', 'loja'
        )
        
        form = FiltroTitulosPagarForm(self.request.GET)
        if form.is_valid():
            status = form.cleaned_data.get('status')
            fornecedor = form.cleaned_data.get('fornecedor')
            data_inicio = form.cleaned_data.get('data_inicio')
            data_fim = form.cleaned_data.get('data_fim')
            
            if status:
                queryset = queryset.filter(status=status)
            if fornecedor:
                queryset = queryset.filter(fornecedor=fornecedor)
            if data_inicio:
                queryset = queryset.filter(data_vencimento__gte=data_inicio)
            if data_fim:
                queryset = queryset.filter(data_vencimento__lte=data_fim)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_filtro'] = FiltroTitulosPagarForm(self.request.GET)
        
        queryset = self.get_queryset()
        context['total_aberto'] = queryset.filter(status='ABERTO').aggregate(
            total=Sum('valor')
        )['total'] or Decimal('0.00')
        
        return context


@method_decorator(login_required, name='dispatch')
class TituloPagarDetailView(DetailView):
    """Detalhes de um título a pagar."""
    model = TituloPagar
    template_name = 'financeiro/titulo_pagar_detail.html'
    context_object_name = 'titulo'
    
    def get_queryset(self):
        return TituloPagar.objects.filter(is_active=True).select_related(
            'fornecedor', 'loja'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        titulo = self.get_object()
        
        movimentos = MovimentoFinanceiro.objects.filter(
            titulo_pagar=titulo
        ).order_by('-data_movimento')
        
        context['movimentos'] = movimentos
        context['form_baixa'] = BaixaTituloPagarForm(titulo=titulo)
        
        return context


@login_required
def baixar_titulo_pagar(request, pk):
    """View para baixar título a pagar."""
    titulo = get_object_or_404(TituloPagar, pk=pk, is_active=True)
    
    if titulo.status == 'PAGO':
        messages.error(request, 'Este título já foi pago.')
        return redirect('financeiro:titulo_pagar_detail', pk=pk)
    
    if request.method == 'POST':
        form = BaixaTituloPagarForm(request.POST, titulo=titulo)
        
        if form.is_valid():
            try:
                valor_pago = form.cleaned_data['valor_pago']
                conta_origem = form.cleaned_data['conta_origem']
                data_pagamento = form.cleaned_data['data_pagamento']
                
                # Atualiza título
                titulo.status = 'PAGO'
                titulo.data_pagamento = data_pagamento
                titulo.save()
                
                # Cria movimento financeiro
                MovimentoFinanceiro.objects.create(
                    conta=conta_origem,
                    tipo='SAIDA',
                    categoria='PAGAMENTO',
                    valor=valor_pago,
                    data_movimento=data_pagamento,
                    titulo_pagar=titulo,
                    referencia=titulo.descricao,
                    observacao=form.cleaned_data.get('observacoes', ''),
                    created_by=request.user,
                )
                
                messages.success(request, f'Título #{titulo.id} baixado com sucesso!')
                return redirect('financeiro:titulo_pagar_detail', pk=pk)
            
            except Exception as e:
                messages.error(request, f'Erro ao baixar título: {str(e)}')
    else:
        form = BaixaTituloPagarForm(titulo=titulo)
    
    return render(request, 'financeiro/titulo_pagar_detail.html', {
        'titulo': titulo,
        'form_baixa': form,
        'movimentos': MovimentoFinanceiro.objects.filter(titulo_pagar=titulo),
    })


@method_decorator(login_required, name='dispatch')
class RelatorioFluxoCaixaView(TemplateView):
    """Relatório de fluxo de caixa."""
    template_name = 'financeiro/relatorio_fluxo_caixa.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Busca primeira empresa (pode melhorar depois)
        from core.models import Empresa
        empresa = Empresa.objects.filter(is_active=True).first()
        
        form = FiltroFluxoCaixaForm(self.request.GET, empresa=empresa)
        context['form'] = form
        
        if form.is_valid():
            data_inicio = form.cleaned_data['data_inicio']
            data_fim = form.cleaned_data['data_fim']
            conta_financeira = form.cleaned_data.get('conta_financeira')
            
            fluxo = FinancialService.calcular_fluxo_caixa(data_inicio, data_fim, conta_financeira)
            
            context['fluxo'] = fluxo
            context['fluxo_json'] = json.dumps([
                {
                    'data': item['data'].strftime('%d/%m/%Y'),
                    'entradas': float(item['entradas']),
                    'saidas': float(item['saidas']),
                    'saldo': float(item['saldo']),
                }
                for item in fluxo
            ])
        else:
            context['fluxo'] = []
            context['fluxo_json'] = '[]'
        
        return context

