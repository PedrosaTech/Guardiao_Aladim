"""
Consulta de status do servico NF-e na SEFAZ.
Primeira integracao real - valida certificado e conectividade.
"""
import logging
import os

from lxml import etree

logger = logging.getLogger(__name__)


def get_certificado_path(config_fiscal) -> str:
    """
    Retorna o caminho do arquivo .pfx do certificado.
    Suporta FileField e CharField.
    """
    cert = config_fiscal.certificado_arquivo
    if hasattr(cert, "path"):
        return cert.path
    if isinstance(cert, str) and os.path.exists(cert):
        return cert
    raise ValueError(
        f"Certificado nao encontrado para loja {config_fiscal.loja.nome}. "
        "Verifique se o arquivo .pfx foi carregado na configuracao fiscal."
    )


def get_senha_certificado(config_fiscal) -> str:
    """
    Retorna a senha do certificado descriptografada.
    EncryptedCharField descriptografa automaticamente ao acessar.
    """
    senha = config_fiscal.senha_certificado
    if not senha:
        raise ValueError(
            f"Senha do certificado nao configurada para loja {config_fiscal.loja.nome}."
        )
    return str(senha)


def consultar_status_servico_nfe(config_fiscal) -> dict:
    """
    Consulta o status do servico NF-e na SEFAZ.
    """
    try:
        from pynfe.processamento.comunicacao import ComunicacaoSefaz

        certificado_path = get_certificado_path(config_fiscal)
        senha = get_senha_certificado(config_fiscal)
        homologacao = config_fiscal.ambiente == "HOMOLOGACAO"

        con = ComunicacaoSefaz(
            uf="ba",
            certificado=certificado_path,
            certificado_senha=senha,
            homologacao=homologacao,
        )
        resposta = con.status_servico("nfe")

        if resposta is None:
            return {
                "ok": False,
                "erro": "Sem resposta da SEFAZ",
                "ambiente": config_fiscal.ambiente,
            }

        root = etree.fromstring(resposta.content)
        ns = {"nfe": "http://www.portalfiscal.inf.br/nfe"}
        c_stat = root.findtext(".//nfe:cStat", namespaces=ns) or ""
        x_motivo = root.findtext(".//nfe:xMotivo", namespaces=ns) or ""

        resultado = {
            "ok": c_stat == "107",
            "cStat": c_stat,
            "xMotivo": x_motivo,
            "ambiente": config_fiscal.ambiente,
        }
        logger.info(
            "Status SEFAZ-BA: cStat=%s xMotivo=%s ambiente=%s",
            c_stat,
            x_motivo,
            config_fiscal.ambiente,
        )
        return resultado
    except Exception as e:
        logger.exception("Erro ao consultar status SEFAZ: %s", e)
        return {
            "ok": False,
            "erro": str(e),
            "ambiente": getattr(config_fiscal, "ambiente", ""),
        }
