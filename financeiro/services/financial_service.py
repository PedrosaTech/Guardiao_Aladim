"""
Serviços financeiros para geração de títulos, baixa e relatórios.
"""
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum, Q
from datetime import timedelta, date
from typing import List, Dict, Optional
import logging

from ..models import TituloReceber, TituloPagar, MovimentoFinanceiro, ContaFinanceira
from vendas.models import PedidoVenda, CondicaoPagamento
from pdv.models import Pagamento

logger = logging.getLogger(__name__)


class FinancialService:
    """Serviços financeiros para gestão de títulos e fluxo de caixa."""
    
    @staticmethod
    @transaction.atomic
    def gerar_titulos_de_venda(pedido: PedidoVenda, created_by) -> List[TituloReceber]:
        """
        Gera títulos a receber baseado nos pagamentos do pedido.
        
        Regras:
        - DINHEIRO/PIX: baixa imediata + MovimentoFinanceiro
        - CARTAO_CREDITO: aguarda compensação (30 dias)
        - CARTAO_DEBITO: aguarda compensação (1 dia)
        - PRAZO: gera parcelas conforme CondicaoPagamento
        
        Args:
            pedido: PedidoVenda faturado
            created_by: Usuário que gerou os títulos
            
        Returns:
            Lista de TituloReceber criados
        """
        titulos = []
        
        # Busca pagamentos do pedido
        pagamentos = pedido.pagamentos.all()
        
        if not pagamentos.exists():
            # Se não tem pagamento, gera título baseado na condição de pagamento
            condicao = pedido.condicao_pagamento
            valor_parcela = pedido.valor_total / condicao.numero_parcelas
            
            for i in range(condicao.numero_parcelas):
                dias_vencimento = i * condicao.dias_entre_parcelas
                data_vencimento = pedido.data_emissao.date() + timedelta(days=dias_vencimento)
                
                titulo = TituloReceber.objects.create(
                    empresa=pedido.loja.empresa,
                    loja=pedido.loja,
                    cliente=pedido.cliente,
                    pedido_venda=pedido,
                    numero_documento=f"{pedido.id}-{i+1}",
                    descricao=f"Pedido #{pedido.id} - Parcela {i+1}/{condicao.numero_parcelas}",
                    valor=valor_parcela,
                    data_emissao=pedido.data_emissao.date(),
                    data_vencimento=data_vencimento,
                    status='ABERTO',
                    created_by=created_by,
                )
                titulos.append(titulo)
            
            return titulos
        
        # Processa cada pagamento
        for idx, pagamento in enumerate(pagamentos):
            tipo_pagamento = pagamento.tipo
            
            # Busca conta financeira da loja (primeira disponível)
            conta_financeira = ContaFinanceira.objects.filter(
                empresa=pedido.loja.empresa,
                is_active=True
            ).first()
            
            numero_doc = f"{pedido.id}-P{idx+1}"
            
            if tipo_pagamento in ['DINHEIRO', 'PIX']:
                # À vista - baixa imediata
                data_pagamento = pedido.data_emissao.date()
                
                titulo = TituloReceber.objects.create(
                    empresa=pedido.loja.empresa,
                    loja=pedido.loja,
                    cliente=pedido.cliente,
                    pedido_venda=pedido,
                    conta_financeira=conta_financeira,
                    numero_documento=numero_doc,
                    descricao=f"Pedido #{pedido.id} - {tipo_pagamento}",
                    valor=pagamento.valor,
                    valor_recebido=pagamento.valor,
                    data_emissao=pedido.data_emissao.date(),
                    data_vencimento=data_pagamento,
                    data_pagamento=data_pagamento,
                    status='PAGO',
                    created_by=created_by,
                )
                
                # Cria movimento financeiro
                if conta_financeira:
                    MovimentoFinanceiro.objects.create(
                        conta=conta_financeira,
                        tipo='ENTRADA',
                        categoria='VENDA',
                        valor=pagamento.valor,
                        data_movimento=data_pagamento,
                        titulo_receber=titulo,
                        referencia=str(pedido.id),
                        observacao=f"Venda Pedido #{pedido.id} - {tipo_pagamento}",
                        created_by=created_by,
                    )
                
                titulos.append(titulo)
                
            elif tipo_pagamento == 'CARTAO_CREDITO':
                # Cartão crédito - vencimento em 30 dias
                data_vencimento = pedido.data_emissao.date() + timedelta(days=30)
                
                titulo = TituloReceber.objects.create(
                    empresa=pedido.loja.empresa,
                    loja=pedido.loja,
                    cliente=pedido.cliente,
                    pedido_venda=pedido,
                    conta_financeira=conta_financeira,
                    numero_documento=numero_doc,
                    descricao=f"Pedido #{pedido.id} - Cartão de Crédito",
                    valor=pagamento.valor,
                    data_emissao=pedido.data_emissao.date(),
                    data_vencimento=data_vencimento,
                    status='ABERTO',
                    created_by=created_by,
                )
                titulos.append(titulo)
                
            elif tipo_pagamento == 'CARTAO_DEBITO':
                # Cartão débito - vencimento em 1 dia
                data_vencimento = pedido.data_emissao.date() + timedelta(days=1)
                
                titulo = TituloReceber.objects.create(
                    empresa=pedido.loja.empresa,
                    loja=pedido.loja,
                    cliente=pedido.cliente,
                    pedido_venda=pedido,
                    conta_financeira=conta_financeira,
                    numero_documento=numero_doc,
                    descricao=f"Pedido #{pedido.id} - Cartão de Débito",
                    valor=pagamento.valor,
                    data_emissao=pedido.data_emissao.date(),
                    data_vencimento=data_vencimento,
                    status='ABERTO',
                    created_by=created_by,
                )
                titulos.append(titulo)
        
        logger.info(f"Gerados {len(titulos)} título(s) para pedido #{pedido.id}")
        return titulos
    
    @staticmethod
    @transaction.atomic
    def baixar_titulo_receber(
        titulo_id: int,
        data_pagamento: date,
        valor_pago: Decimal,
        conta_destino: ContaFinanceira,
        juros: Decimal = Decimal('0.00'),
        multa: Decimal = Decimal('0.00'),
        desconto: Decimal = Decimal('0.00'),
        observacoes: str = '',
        created_by=None
    ) -> TituloReceber:
        """
        Baixa um título a receber.
        
        Valida se título está ABERTO, calcula valor total com juros/multa/desconto,
        atualiza status e cria MovimentoFinanceiro.
        
        Args:
            titulo_id: ID do título a receber
            data_pagamento: Data do pagamento
            valor_pago: Valor pago (sem juros/multa/desconto)
            conta_destino: Conta financeira de destino
            juros: Valor de juros (opcional)
            multa: Valor de multa (opcional)
            desconto: Valor de desconto (opcional)
            observacoes: Observações da baixa
            created_by: Usuário que está baixando
            
        Returns:
            TituloReceber atualizado
            
        Raises:
            ValueError: Se título não estiver ABERTO ou outros erros de validação
        """
        # Usa select_for_update para evitar concorrência
        titulo = TituloReceber.objects.select_for_update().get(id=titulo_id)
        
        if titulo.status == 'PAGO':
            raise ValueError('Título já foi recebido/pago')
        
        if titulo.status == 'CANCELADO':
            raise ValueError('Não é possível baixar título cancelado')
        
        # Calcula valor total
        valor_total = valor_pago + juros + multa - desconto
        
        if valor_total <= 0:
            raise ValueError('Valor total deve ser maior que zero')
        
        # Atualiza título
        titulo.data_pagamento = data_pagamento
        titulo.valor_recebido = valor_total
        titulo.valor_juros = juros
        titulo.valor_multa = multa
        titulo.valor_desconto = desconto
        titulo.status = 'PAGO'
        # Nota: TituloReceber não tem campo observacoes no model atual
        # Observações são salvas apenas no MovimentoFinanceiro
        titulo.updated_by = created_by
        titulo.save()
        
        # Cria movimento financeiro
        MovimentoFinanceiro.objects.create(
            conta=conta_destino,
            tipo='ENTRADA',
            categoria='RECEBIMENTO',
            valor=valor_total,
            data_movimento=data_pagamento,
            titulo_receber=titulo,
            referencia=titulo.numero_documento or str(titulo.id),
            observacao=f"Recebimento {titulo.descricao}" + (f" - {observacoes}" if observacoes else ""),
            created_by=created_by,
        )
        
        logger.info(f"Título #{titulo.id} baixado com valor total de R$ {valor_total}")
        return titulo
    
    @staticmethod
    def calcular_fluxo_caixa(
        data_inicio: date,
        data_fim: date,
        conta_financeira: Optional[ContaFinanceira] = None
    ) -> List[Dict]:
        """
        Calcula fluxo de caixa para um período.
        
        Retorna lista de dicionários com data, entradas, saídas e saldo acumulado.
        
        Args:
            data_inicio: Data inicial
            data_fim: Data final
            conta_financeira: Conta específica (None para todas)
            
        Returns:
            Lista de dicts: [{'data': date, 'entradas': Decimal, 'saidas': Decimal, 'saldo': Decimal}, ...]
        """
        # Filtra movimentos por conta e período
        movimentos_qs = MovimentoFinanceiro.objects.filter(
            data_movimento__gte=data_inicio,
            data_movimento__lte=data_fim,
            is_active=True
        )
        
        if conta_financeira:
            movimentos_qs = movimentos_qs.filter(conta=conta_financeira)
        
        # Agrupa por data
        movimentos_por_data = {}
        
        for movimento in movimentos_qs.select_related('conta'):
            data_mov = movimento.data_movimento
            
            if data_mov not in movimentos_por_data:
                movimentos_por_data[data_mov] = {
                    'data': data_mov,
                    'entradas': Decimal('0.00'),
                    'saidas': Decimal('0.00'),
                    'saldo': Decimal('0.00'),
                }
            
            if movimento.tipo == 'ENTRADA':
                movimentos_por_data[data_mov]['entradas'] += movimento.valor
            else:
                movimentos_por_data[data_mov]['saidas'] += movimento.valor
        
        # Ordena por data e calcula saldo acumulado
        resultado = []
        saldo_acumulado = Decimal('0.00')
        
        for data_mov in sorted(movimentos_por_data.keys()):
            item = movimentos_por_data[data_mov]
            saldo_dia = item['entradas'] - item['saidas']
            saldo_acumulado += saldo_dia
            item['saldo'] = saldo_acumulado
            resultado.append(item)
        
        return resultado
    
    @staticmethod
    def get_saldo_atual(conta_financeira: Optional[ContaFinanceira] = None) -> Decimal:
        """
        Retorna saldo atual de uma conta ou todas as contas.
        
        Args:
            conta_financeira: Conta específica (None para todas)
            
        Returns:
            Saldo total (entradas - saídas)
        """
        movimentos_qs = MovimentoFinanceiro.objects.filter(is_active=True)
        
        if conta_financeira:
            movimentos_qs = movimentos_qs.filter(conta=conta_financeira)
        
        entradas = movimentos_qs.filter(tipo='ENTRADA').aggregate(
            total=Sum('valor')
        )['total'] or Decimal('0.00')
        
        saidas = movimentos_qs.filter(tipo='SAIDA').aggregate(
            total=Sum('valor')
        )['total'] or Decimal('0.00')
        
        return entradas - saidas

