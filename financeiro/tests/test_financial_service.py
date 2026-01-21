"""
Testes para FinancialService.
"""
import pytest
from decimal import Decimal
from django.utils import timezone
from datetime import date, timedelta

from financeiro.services.financial_service import FinancialService
from financeiro.models import TituloReceber, MovimentoFinanceiro, ContaFinanceira
from vendas.models import PedidoVenda, CondicaoPagamento
from core.models import Empresa, Loja
from pessoas.models import Cliente
from pdv.models import Pagamento


@pytest.mark.django_db
class TestFinancialService:
    """Testes para FinancialService."""
    
    def test_gerar_titulos_de_venda_dinheiro(self):
        """Testa geração de título para pagamento em dinheiro."""
        empresa = Empresa.objects.create(
            nome_fantasia='Teste',
            razao_social='Teste LTDA',
            cnpj='12345678000190',
        )
        loja = Loja.objects.create(empresa=empresa, nome='Loja Teste')
        cliente = Cliente.objects.create(
            empresa=empresa,
            tipo_pessoa='PF',
            nome_razao_social='Cliente Teste',
            cpf_cnpj='12345678900',
        )
        conta = ContaFinanceira.objects.create(
            empresa=empresa,
            nome='Caixa Principal',
            tipo='CAIXA',
        )
        condicao = CondicaoPagamento.objects.create(
            empresa=empresa,
            nome='À Vista',
            numero_parcelas=1,
            dias_entre_parcelas=0,
        )
        
        pedido = PedidoVenda.objects.create(
            loja=loja,
            cliente=cliente,
            tipo_venda='BALCAO',
            status='FATURADO',
            vendedor_id=1,
            condicao_pagamento=condicao,
            valor_total=Decimal('100.00'),
        )
        
        Pagamento.objects.create(
            pedido=pedido,
            caixa_sessao_id=1,
            tipo='DINHEIRO',
            valor=Decimal('100.00'),
        )
        
        titulos = FinancialService.gerar_titulos_de_venda(pedido, pedido.vendedor)
        
        assert len(titulos) == 1
        assert titulos[0].status == 'PAGO'
        assert titulos[0].valor == Decimal('100.00')
        assert MovimentoFinanceiro.objects.filter(titulo_receber=titulos[0]).exists()
    
    def test_calcular_fluxo_caixa(self):
        """Testa cálculo de fluxo de caixa."""
        empresa = Empresa.objects.create(
            nome_fantasia='Teste',
            razao_social='Teste LTDA',
            cnpj='12345678000190',
        )
        conta = ContaFinanceira.objects.create(
            empresa=empresa,
            nome='Caixa',
            tipo='CAIXA',
        )
        
        hoje = date.today()
        
        MovimentoFinanceiro.objects.create(
            conta=conta,
            tipo='ENTRADA',
            categoria='VENDA',
            valor=Decimal('100.00'),
            data_movimento=hoje,
        )
        
        MovimentoFinanceiro.objects.create(
            conta=conta,
            tipo='SAIDA',
            categoria='PAGAMENTO',
            valor=Decimal('30.00'),
            data_movimento=hoje,
        )
        
        fluxo = FinancialService.calcular_fluxo_caixa(hoje, hoje, conta)
        
        assert len(fluxo) == 1
        assert fluxo[0]['entradas'] == Decimal('100.00')
        assert fluxo[0]['saidas'] == Decimal('30.00')
        assert fluxo[0]['saldo'] == Decimal('70.00')
    
    def test_get_saldo_atual(self):
        """Testa cálculo de saldo atual."""
        empresa = Empresa.objects.create(
            nome_fantasia='Teste',
            razao_social='Teste LTDA',
            cnpj='12345678000190',
        )
        conta = ContaFinanceira.objects.create(
            empresa=empresa,
            nome='Caixa',
            tipo='CAIXA',
        )
        
        MovimentoFinanceiro.objects.create(
            conta=conta,
            tipo='ENTRADA',
            categoria='VENDA',
            valor=Decimal('200.00'),
            data_movimento=date.today(),
        )
        
        MovimentoFinanceiro.objects.create(
            conta=conta,
            tipo='SAIDA',
            categoria='PAGAMENTO',
            valor=Decimal('50.00'),
            data_movimento=date.today(),
        )
        
        saldo = FinancialService.get_saldo_atual(conta)
        assert saldo == Decimal('150.00')

