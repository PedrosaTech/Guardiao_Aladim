"""
Testes do app produtos.
"""
import pytest
from decimal import Decimal
from core.models import Empresa, Loja
from .models import CategoriaProduto, Produto


@pytest.mark.django_db
class TestProduto:
    """Testes para o modelo Produto."""
    
    def test_criar_produto_com_classe_risco(self):
        """Testa criação de produto com classe de risco."""
        empresa = Empresa.objects.create(
            nome_fantasia='Guardião Aladin',
            razao_social='Guardião Aladin Ltda',
            cnpj='12345678000190',
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
        assert produto.id is not None
        assert produto.classe_risco == '1.4G'
        assert produto.possui_restricao_exercito is False
        assert produto.preco_venda_sugerido == Decimal('10.00')

