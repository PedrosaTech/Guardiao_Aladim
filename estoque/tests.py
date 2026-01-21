"""
Testes do app estoque.
"""
import pytest
from decimal import Decimal
from core.models import Empresa, Loja
from produtos.models import CategoriaProduto, Produto
from .models import LocalEstoque, EstoqueAtual
from .services import realizar_movimento_estoque


@pytest.mark.django_db
class TestMovimentacaoEstoque:
    """Testes para movimentação de estoque."""
    
    def test_movimentacao_estoque_entrada(self):
        """Testa entrada de estoque."""
        empresa = Empresa.objects.create(
            nome_fantasia='Guardião Aladin',
            razao_social='Guardião Aladin Ltda',
            cnpj='12345678000190',
        )
        loja = Loja.objects.create(
            empresa=empresa,
            nome='Loja Centro',
        )
        categoria = CategoriaProduto.objects.create(
            empresa=empresa,
            nome='Bombas',
        )
        produto = Produto.objects.create(
            empresa=empresa,
            categoria=categoria,
            codigo_interno='BOM001',
            descricao='Bomba de Festa',
            classe_risco='1.4G',
            ncm='36041000',
            cfop_venda_dentro_uf='5102',
            unidade_comercial='UN',
            origem='0',
            csosn_cst='102',
            aliquota_icms=Decimal('18.00'),
            preco_venda_sugerido=Decimal('10.00'),
        )
        local = LocalEstoque.objects.create(
            loja=loja,
            nome='Depósito Principal',
        )
        
        # Realiza entrada
        movimento = realizar_movimento_estoque(
            produto=produto,
            tipo_movimento='ENTRADA',
            quantidade=Decimal('100.000'),
            local_destino=local,
        )
        
        assert movimento.id is not None
        assert movimento.tipo_movimento == 'ENTRADA'
        
        # Verifica estoque atualizado
        estoque = EstoqueAtual.objects.get(produto=produto, local_estoque=local)
        assert estoque.quantidade == Decimal('100.000')

