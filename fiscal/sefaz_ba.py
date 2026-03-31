"""
Serviço de consulta à SEFAZ-BA para alertas de notas fiscais emitidas no CNPJ.

WebService: wsCFP (Compra Legal)
URL: https://sistemas.sefaz.ba.gov.br/webservices/CL/wsCFP.asmx
Operação: consultaNotasFiscais_V02

Requer: credenciais SEFAZ-BA (certificado digital ou usuário/senha conforme documentação).
TODO: Implementar autenticação real quando credenciais estiverem disponíveis.
"""
import logging
from typing import List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def consultar_notas_emitidas_cnpj(
    cnpj: str,
    loja_id: int,
    data_inicio: Optional[datetime] = None,
    data_fim: Optional[datetime] = None,
) -> List[dict]:
    """
    Consulta na SEFAZ-BA as NF-e onde o CNPJ é destinatário (notas de entrada).

    Args:
        cnpj: CNPJ da empresa (apenas dígitos)
        loja_id: ID da Loja para associar os alertas
        data_inicio: Período inicial da consulta
        data_fim: Período final da consulta

    Returns:
        Lista de dicts com: chave_acesso, numero, serie, valor_total, data_emissao,
                            cnpj_emitente, razao_social_emitente
    """
    # TODO: Implementar chamada SOAP real ao wsCFP quando credenciais SEFAZ-BA
    # estiverem configuradas. Por enquanto retorna lista vazia.
    #
    # Exemplo de estrutura da requisição SOAP (consultaNotasFiscais_V02):
    # - campo: tipo de campo (ex: CNPJ)
    # - criterio: critério de busca
    # - valor: valor do CNPJ
    # - flg, tipoUsuario, codUsuario: parâmetros de autenticação
    #
    # A resposta XML contém as notas fiscais. Será necessário parsear e
    # extrair chave, número, série, valor, emitente, etc.

    logger.info(
        "Consulta SEFAZ-BA (stub): cnpj=%s loja=%s - "
        "Integração real pendente de credenciais.",
        cnpj[:8] + "***",
        loja_id,
    )
    return []


def sincronizar_alertas_sefaz() -> dict:
    """
    Percorre as lojas com configuração fiscal e consulta a SEFAZ-BA,
    criando alertas para notas que ainda não estão no sistema.

    Returns:
        dict com: alertas_criados, erros, lojas_processadas
    """
    from .models import ConfiguracaoFiscalLoja, AlertaNotaFiscal, NotaFiscalEntrada
    from core.models import Loja
    import re

    resultado = {
        'alertas_criados': 0,
        'erros': [],
        'lojas_processadas': 0,
    }

    configs = ConfiguracaoFiscalLoja.objects.filter(is_active=True).select_related('loja')
    if not configs.exists():
        logger.info("Nenhuma configuração fiscal encontrada.")
        return resultado

    data_fim = datetime.now()
    data_inicio = data_fim - timedelta(days=30)  # últimos 30 dias

    for config in configs:
        try:
            cnpj_limpo = re.sub(r'\D', '', str(config.cnpj))
            if len(cnpj_limpo) != 14:
                resultado['erros'].append(f"CNPJ inválido na loja {config.loja.nome}")
                continue

            notas = consultar_notas_emitidas_cnpj(
                cnpj=cnpj_limpo,
                loja_id=config.loja_id,
                data_inicio=data_inicio,
                data_fim=data_fim,
            )
            resultado['lojas_processadas'] += 1

            for n in notas:
                chave = n.get('chave_acesso')
                if not chave or len(chave) != 44:
                    continue

                if NotaFiscalEntrada.objects.filter(chave_acesso=chave, is_active=True).exists():
                    continue

                if AlertaNotaFiscal.objects.filter(loja=config.loja, chave_acesso=chave).exists():
                    continue

                AlertaNotaFiscal.objects.create(
                    loja=config.loja,
                    tipo='ENTRADA',
                    status='PENDENTE',
                    chave_acesso=chave,
                    numero=n.get('numero', 0),
                    serie=str(n.get('serie', '1'))[:3],
                    valor_total=n.get('valor_total'),
                    data_emissao=n.get('data_emissao'),
                    cnpj_emitente=n.get('cnpj_emitente', ''),
                    razao_social_emitente=n.get('razao_social_emitente', '')[:255],
                )
                resultado['alertas_criados'] += 1

        except Exception as e:
            logger.exception("Erro ao processar loja %s: %s", config.loja.nome, e)
            resultado['erros'].append(f"{config.loja.nome}: {e}")

    return resultado
