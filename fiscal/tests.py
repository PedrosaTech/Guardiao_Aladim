"""
Testes do módulo fiscal.
"""
import unittest
from concurrent.futures import ThreadPoolExecutor
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from django.test import TestCase

from core.models import Empresa, Loja
from fiscal.models import ConfiguracaoFiscalLoja
from fiscal.numeracao import reservar_numero_nfe, reservar_numero_nfce


class TestReservaNumeracaoNF(TestCase):

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nome_fantasia='Empresa NF',
            razao_social='Empresa NF LTDA',
            cnpj='22334455000162',
        )
        self.loja = Loja.objects.create(empresa=self.empresa, nome='Loja NF')
        self.config = ConfiguracaoFiscalLoja.objects.create(
            loja=self.loja,
            cnpj='22334455000162',
            inscricao_estadual='123456789',
            regime_tributario='SIMPLES_NACIONAL',
            serie_nfe='001',
            serie_nfce='002',
            proximo_numero_nfe=10,
            proximo_numero_nfce=20,
        )
        self.loja_sem_config = Loja.objects.create(
            empresa=self.empresa,
            nome='Loja Sem Fiscal',
        )

    def test_reserva_incrementa_numero_nfe(self):
        numero1, serie1 = reservar_numero_nfe(self.loja)
        numero2, serie2 = reservar_numero_nfe(self.loja)
        self.assertEqual(numero1, 10)
        self.assertEqual(numero2, 11)
        self.assertEqual(serie1, serie2)
        self.config.refresh_from_db()
        self.assertEqual(self.config.proximo_numero_nfe, 12)

    def test_reserva_incrementa_numero_nfce(self):
        numero1, serie1 = reservar_numero_nfce(self.loja)
        numero2, serie2 = reservar_numero_nfce(self.loja)
        self.assertEqual(numero1, 20)
        self.assertEqual(numero2, 21)
        self.assertEqual(serie1, '002')
        self.config.refresh_from_db()
        self.assertEqual(self.config.proximo_numero_nfce, 22)

    def test_loja_sem_config_fiscal_lanca_excecao(self):
        with self.assertRaises(ObjectDoesNotExist):
            reservar_numero_nfe(self.loja_sem_config)

    @unittest.skipUnless(
        connection.vendor == 'postgresql',
        'select_for_update em conflito real requer PostgreSQL',
    )
    def test_numeracao_concorrente_sem_duplicata(self):
        def reservar(_):
            numero, _ = reservar_numero_nfe(self.loja)
            return numero

        with ThreadPoolExecutor(max_workers=5) as ex:
            resultados = list(ex.map(reservar, range(10)))

        self.assertEqual(
            len(resultados),
            len(set(resultados)),
            'Números duplicados detectados!',
        )
