"""
Views do app core.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncDate, ExtractMonth
from django.utils import timezone
from datetime import datetime, timedelta
import json
from rest_framework import viewsets
from .models import Empresa, Loja
from .serializers import EmpresaSerializer, LojaSerializer


class EmpresaViewSet(viewsets.ModelViewSet):
    queryset = Empresa.objects.filter(is_active=True)
    serializer_class = EmpresaSerializer


class LojaViewSet(viewsets.ModelViewSet):
    queryset = Loja.objects.filter(is_active=True)
    serializer_class = LojaSerializer


@login_required
def dashboard(request):
    """
    Dashboard principal do sistema.
    """
    # Estatísticas de Produtos
    from produtos.models import Produto
    total_produtos = Produto.objects.filter(is_active=True).count()
    produtos_restricao = Produto.objects.filter(is_active=True, possui_restricao_exercito=True).count()
    
    # Estatísticas de Estoque
    from estoque.models import EstoqueAtual
    total_locais = EstoqueAtual.objects.filter(is_active=True).values('local_estoque').distinct().count()
    produtos_com_estoque = EstoqueAtual.objects.filter(is_active=True, quantidade__gt=0).values('produto').distinct().count()
    
    # Estatísticas de Vendas
    from vendas.models import PedidoVenda
    hoje = timezone.now().date()
    mes_atual = datetime.now().replace(day=1).date()
    
    pedidos_hoje = PedidoVenda.objects.filter(
        is_active=True,
        data_emissao__date=hoje
    ).count()
    
    pedidos_mes = PedidoVenda.objects.filter(
        is_active=True,
        data_emissao__date__gte=mes_atual
    ).count()
    
    valor_mes = PedidoVenda.objects.filter(
        is_active=True,
        data_emissao__date__gte=mes_atual,
        status__in=['ABERTO', 'FATURADO']
    ).aggregate(Sum('valor_total'))['valor_total__sum'] or 0
    
    # Estatísticas de Eventos
    from eventos.models import EventoVenda
    eventos_abertos = EventoVenda.objects.filter(
        is_active=True,
        status__in=['RASCUNHO', 'PROPOSTA_ENVIADA', 'APROVADO', 'EM_EXECUCAO']
    ).count()
    
    eventos_mes = EventoVenda.objects.filter(
        is_active=True,
        data_evento__gte=mes_atual
    ).count()
    
    # Estatísticas Fiscais
    from fiscal.models import NotaFiscalSaida
    notas_autorizadas_mes = NotaFiscalSaida.objects.filter(
        is_active=True,
        status='AUTORIZADA',
        data_emissao__date__gte=mes_atual if timezone.now().date() >= mes_atual else None
    ).count()
    
    valor_nfe_mes = NotaFiscalSaida.objects.filter(
        is_active=True,
        status='AUTORIZADA',
        data_emissao__date__gte=mes_atual if timezone.now().date() >= mes_atual else None
    ).aggregate(Sum('valor_total'))['valor_total__sum'] or 0
    
    # Pedidos pendentes
    pedidos_pendentes = PedidoVenda.objects.filter(
        is_active=True,
        status__in=['ORCAMENTO', 'ABERTO']
    ).count()
    
    # Notas em rascunho
    notas_rascunho = NotaFiscalSaida.objects.filter(
        is_active=True,
        status='RASCUNHO'
    ).count()
    
    # ========== DADOS PARA GRÁFICOS ==========
    
    # 1. VENDAS DOS ÚLTIMOS 7 DIAS (incluindo hoje)
    sete_dias_atras = hoje - timedelta(days=6)  # 7 dias incluindo hoje
    
    try:
        vendas_7_dias = PedidoVenda.objects.filter(
            is_active=True,
            data_emissao__date__gte=sete_dias_atras,
            data_emissao__date__lte=hoje,
            status__in=['ABERTO', 'FATURADO']
        ).annotate(
            dia=TruncDate('data_emissao')
        ).values('dia').annotate(
            total=Sum('valor_total')
        ).order_by('dia')
        
        # Criar dicionário para facilitar busca
        vendas_dict = {v['dia']: float(v['total'] or 0) for v in vendas_7_dias}
        
        # Preencher todos os 7 dias (mesmo os sem vendas)
        labels_vendas = []
        dados_vendas = []
        dias_semana = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']
        
        for i in range(7):
            dia = sete_dias_atras + timedelta(days=i)
            dia_semana = dias_semana[dia.weekday()]
            labels_vendas.append(f"{dia_semana} {dia.day:02d}")
            dados_vendas.append(vendas_dict.get(dia, 0))
    except Exception as e:
        # Em caso de erro, retorna arrays vazios
        labels_vendas = []
        dados_vendas = []
    
    # 2. FATURAMENTO MENSAL DO ANO
    ano_atual = datetime.now().year
    primeiro_dia_ano = datetime(ano_atual, 1, 1).date()
    
    try:
        faturamento_mensal = PedidoVenda.objects.filter(
            is_active=True,
            data_emissao__date__gte=primeiro_dia_ano,
            status__in=['ABERTO', 'FATURADO']
        ).annotate(
            mes=ExtractMonth('data_emissao')
        ).values('mes').annotate(
            total=Sum('valor_total')
        ).order_by('mes')
        
        # Criar dicionário de faturamento
        faturamento_dict = {f['mes']: float(f['total'] or 0) for f in faturamento_mensal}
        
        # Preencher todos os 12 meses
        meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 
                 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        dados_faturamento = [faturamento_dict.get(i+1, 0) for i in range(12)]
    except Exception as e:
        meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 
                 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        dados_faturamento = [0] * 12
    
    # 3. TOP 5 PRODUTOS MAIS VENDIDOS (ÚLTIMOS 30 DIAS)
    trinta_dias_atras = hoje - timedelta(days=30)
    
    try:
        from vendas.models import ItemPedidoVenda
        
        produtos_top = ItemPedidoVenda.objects.filter(
            is_active=True,
            pedido__is_active=True,
            pedido__data_emissao__date__gte=trinta_dias_atras,
            pedido__status__in=['ABERTO', 'FATURADO']
        ).values(
            'produto__descricao'
        ).annotate(
            total_vendido=Sum('quantidade')
        ).order_by('-total_vendido')[:5]
        
        labels_produtos = [
            (p['produto__descricao'][:30] + '...' if len(p['produto__descricao']) > 30 
             else p['produto__descricao']) 
            for p in produtos_top
        ]
        dados_produtos = [float(p['total_vendido'] or 0) for p in produtos_top]
    except Exception as e:
        # Se não houver ItemPedidoVenda ou der erro, retorna vazio
        labels_produtos = []
        dados_produtos = []
    
    # 4. ESTOQUE POR LOCAL (TOP 5 LOCAIS)
    try:
        from estoque.models import LocalEstoque
        
        estoque_por_local = EstoqueAtual.objects.filter(
            is_active=True,
            quantidade__gt=0
        ).values(
            'local_estoque__nome'
        ).annotate(
            quantidade_total=Sum('quantidade')
        ).order_by('-quantidade_total')[:5]
        
        labels_locais = [e['local_estoque__nome'] or 'Sem nome' for e in estoque_por_local]
        dados_locais = [float(e['quantidade_total'] or 0) for e in estoque_por_local]
    except Exception as e:
        labels_locais = []
        dados_locais = []
    
    context = {
        'total_produtos': total_produtos,
        'produtos_restricao': produtos_restricao,
        'total_locais': total_locais,
        'produtos_com_estoque': produtos_com_estoque,
        'pedidos_hoje': pedidos_hoje,
        'pedidos_mes': pedidos_mes,
        'valor_mes': valor_mes,
        'eventos_abertos': eventos_abertos,
        'eventos_mes': eventos_mes,
        'notas_autorizadas_mes': notas_autorizadas_mes,
        'valor_nfe_mes': valor_nfe_mes,
        'pedidos_pendentes': pedidos_pendentes,
        'notas_rascunho': notas_rascunho,
        # Dados para gráficos (converter para JSON)
        'vendas_labels': json.dumps(labels_vendas),
        'vendas_dados': json.dumps(dados_vendas),
        'faturamento_labels': json.dumps(meses),
        'faturamento_dados': json.dumps(dados_faturamento),
        'produtos_labels': json.dumps(labels_produtos),
        'produtos_dados': json.dumps(dados_produtos),
        'locais_labels': json.dumps(labels_locais),
        'locais_dados': json.dumps(dados_locais),
    }
    
    return render(request, 'core/dashboard.html', context)
