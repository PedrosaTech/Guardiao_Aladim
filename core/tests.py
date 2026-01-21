"""
Testes do app core.
"""
import pytest
from django.contrib.auth import get_user_model
from .models import Empresa, Loja

User = get_user_model()


@pytest.mark.django_db
class TestEmpresa:
    """Testes para o modelo Empresa."""
    
    def test_criar_empresa(self):
        """Testa criação de empresa."""
        empresa = Empresa.objects.create(
            nome_fantasia='Guardião Aladin',
            razao_social='Guardião Aladin Ltda',
            cnpj='12345678000190',
        )
        assert empresa.id is not None
        assert empresa.nome_fantasia == 'Guardião Aladin'
        assert empresa.is_active is True
    
    def test_criar_loja(self):
        """Testa criação de loja."""
        empresa = Empresa.objects.create(
            nome_fantasia='Guardião Aladin',
            razao_social='Guardião Aladin Ltda',
            cnpj='12345678000190',
        )
        loja = Loja.objects.create(
            empresa=empresa,
            nome='Loja Centro',
            cnpj='12345678000190',
        )
        assert loja.id is not None
        assert loja.empresa == empresa
        assert loja.nome == 'Loja Centro'
        assert loja.is_active is True

