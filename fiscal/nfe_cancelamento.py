"""
Cancelamento de NF-e via evento SEFAZ (PyNFe 0.6.5).

Fluxo: SerializacaoXML.serializar_evento → AssinaturaA1.assinar → ComunicacaoSefaz.evento
"""
import logging
import re
from datetime import datetime, timedelta

from django.utils import timezone as dj_timezone
from lxml import etree

from fiscal.nfe_autorizacao import NSMAP

logger = logging.getLogger(__name__)


def extrair_protocolo_do_xml(xml_str: str) -> str:
    """
    Extrai o nProt (protocolo de autorização) do XML procNFe / retorno autorização.
    """
    if not xml_str or not str(xml_str).strip():
        return ''
    raw = str(xml_str).strip()
    try:
        root = etree.fromstring(raw.encode('utf-8'))
    except Exception:
        try:
            root = etree.fromstring(raw)
        except Exception as exc:
            logger.warning('Erro ao parsear XML para protocolo: %s', exc)
            return ''

    inf_prot = root.find('.//nfe:infProt', namespaces=NSMAP)
    if inf_prot is None:
        inf_prot = root.find('.//{*}infProt')
    if inf_prot is not None:
        for child in inf_prot:
            if etree.QName(child).localname == 'nProt' and child.text:
                return child.text.strip()

    for el in root.iter():
        if etree.QName(el).localname == 'nProt' and el.text:
            return el.text.strip()
    return ''


def _parse_resposta_evento(raw: bytes) -> tuple[str, str, list[str]]:
    """
    Extrai cStat / xMotivo do SOAP / retEnvEvento.
    Retorna também a lista de todos os cStat (lote pode ser 128 e o evento 135).
    """
    try:
        root = etree.fromstring(raw)
    except Exception as exc:
        logger.exception('Falha ao parsear retorno evento: %s', exc)
        return '999', f'XML inválido: {exc}', []

    stats: list[str] = []
    motivos: list[str] = []
    for el in root.iter():
        tag = etree.QName(el).localname
        if tag == 'cStat' and el.text:
            stats.append(el.text.strip())
        elif tag == 'xMotivo' and el.text:
            motivos.append(el.text.strip())

    c_stat = stats[-1] if stats else ''
    x_motivo = motivos[-1] if motivos else ''
    return c_stat, x_motivo, stats


def cancelar_nfe(nota, justificativa: str, usuario=None) -> dict:
    """
    Envia evento de cancelamento de NF-e para a SEFAZ.

    Returns:
        dict com: cancelada, cStat, xMotivo
    """
    from pynfe.entidades.evento import EventoCancelarNota
    from pynfe.entidades.fonte_dados import _fonte_dados
    from pynfe.processamento.assinatura import AssinaturaA1
    from pynfe.processamento.comunicacao import ComunicacaoSefaz
    from pynfe.processamento.serializacao import SerializacaoXML

    from fiscal.nfe_status import get_certificado_path, get_senha_certificado

    _ = usuario

    if getattr(nota, 'tipo_documento', '') != 'NFE':
        raise ValueError(
            'Cancelamento por evento está implementado apenas para NF-e (modelo 55).'
        )

    if nota.status != 'AUTORIZADA':
        raise ValueError(
            f"Nota #{nota.id} está com status '{nota.status}'. "
            'Só é possível cancelar notas AUTORIZADAS.'
        )

    chave = (nota.chave_acesso or '').strip()
    if len(chave) != 44 or not chave.isdigit():
        raise ValueError(f'Nota #{nota.id} não possui chave de acesso válida.')

    justificativa = justificativa.strip()
    if len(justificativa) < 15:
        raise ValueError('Justificativa deve ter no mínimo 15 caracteres.')
    if len(justificativa) > 255:
        raise ValueError('Justificativa deve ter no máximo 255 caracteres.')

    if not nota.data_emissao:
        raise ValueError(
            f'Nota #{nota.id} sem data de emissão; não é possível validar o prazo de 24h.'
        )

    agora = dj_timezone.now()
    dt_emit = nota.data_emissao
    if dj_timezone.is_naive(dt_emit):
        dt_emit = dj_timezone.make_aware(
            dt_emit, dj_timezone.get_current_timezone()
        )
    if agora - dt_emit > timedelta(hours=24):
        raise ValueError(
            'Prazo de cancelamento expirado: somente até 24 horas após a emissão '
            '(regra aplicada com base em data_emissão da nota).'
        )

    protocolo = extrair_protocolo_do_xml(nota.xml_arquivo or '')
    if not protocolo:
        raise ValueError(
            f'Não foi possível extrair o número do protocolo (nProt) do XML da nota #{nota.id}.'
        )

    try:
        config = nota.loja.configuracao_fiscal
    except Exception as exc:
        raise ValueError(f'Configuração fiscal da loja não encontrada: {exc}') from exc

    homologacao = config.ambiente == 'HOMOLOGACAO'
    cnpj_emitente = re.sub(r'\D', '', str(config.cnpj or ''))
    if len(cnpj_emitente) != 14:
        raise ValueError('CNPJ do emitente na configuração fiscal inválido ou ausente.')

    certificado_path = get_certificado_path(config)
    senha = get_senha_certificado(config)

    evento = EventoCancelarNota(
        orgao='29',
        cnpj=cnpj_emitente,
        chave=chave,
        data_emissao=datetime.now().astimezone() - timedelta(seconds=30),
        uf='ba',
        protocolo=protocolo,
        justificativa=justificativa,
    )
    evento.n_seq_evento = 1
    evento.identificador

    serializador = SerializacaoXML(_fonte_dados, homologacao=homologacao)
    xml_evento = serializador.serializar_evento(evento)
    a1 = AssinaturaA1(certificado_path, senha)
    xml_assinado = a1.assinar(xml_evento)

    con = ComunicacaoSefaz(
        uf='ba',
        certificado=certificado_path,
        certificado_senha=senha,
        homologacao=homologacao,
    )

    logger.info(
        'Enviando cancelamento NF-e %s/%s chave=%s...',
        nota.numero,
        nota.serie,
        chave[:20],
    )

    try:
        resposta = con.evento(
            modelo='nfe',
            evento=xml_assinado,
            id_lote=nota.id,
        )
    except Exception as exc:
        logger.exception('Erro de comunicação ao cancelar NF-e: %s', exc)
        return {
            'cancelada': False,
            'cStat': '999',
            'xMotivo': f'Erro de comunicação: {exc}',
        }

    raw = resposta.content if hasattr(resposta, 'content') else str(resposta).encode('utf-8')
    c_stat, x_motivo, todos_stats = _parse_resposta_evento(raw)

    cancelada = any(s in ('135', '136') for s in todos_stats)

    logger.info(
        'Retorno cancelamento NF-e %s/%s: cStat=%s xMotivo=%s',
        nota.numero,
        nota.serie,
        c_stat,
        x_motivo,
    )

    return {
        'cancelada': cancelada,
        'cStat': c_stat,
        'xMotivo': x_motivo,
    }
