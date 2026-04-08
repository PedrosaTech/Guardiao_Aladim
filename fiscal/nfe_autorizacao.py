"""
Envio da NF-e para autorização na SEFAZ (NFeAutorizacao4) e tratamento do retorno.

PyNFe 0.6.5: ``ComunicacaoSefaz.autorizacao`` espera o XML já assinado como elemento
lxml (é anexado dentro de ``enviNFe``). Retorno síncrono ``ind_sinc=1``:
``(0, nfeProc_element)`` se cStat 100 ou 150; caso contrário ``(1, response, nfe_element)``.
"""
import logging
from typing import Union

from lxml import etree

logger = logging.getLogger(__name__)

NS = 'http://www.portalfiscal.inf.br/nfe'
NSMAP = {'nfe': NS}


def _find_ret_envi(proc_or_soap: etree._Element):
    r = proc_or_soap.find('.//nfe:retEnviNFe', namespaces=NSMAP)
    if r is not None:
        return r
    if etree.QName(proc_or_soap).localname == 'retEnviNFe':
        return proc_or_soap
    return None


def _find_inf_prot(tree: etree._Element):
    el = tree.find('.//nfe:infProt', namespaces=NSMAP)
    if el is not None:
        return el
    el = tree.find('.//{*}infProt')
    return el


def _text_inf_prot(inf_prot: etree._Element) -> dict:
    def gt(tag: str) -> str:
        c = inf_prot.find(f'nfe:{tag}', namespaces=NSMAP)
        if c is not None and c.text:
            return c.text.strip()
        for child in inf_prot:
            if etree.QName(child).localname == tag:
                return (child.text or '').strip()
        return ''

    return {
        'cStat': gt('cStat'),
        'xMotivo': gt('xMotivo'),
        'chNFe': gt('chNFe'),
        'nProt': gt('nProt'),
        'dhRecbto': gt('dhRecbto'),
    }


def _parse_resposta_bruta(raw: Union[bytes, str]) -> dict:
    """Extrai cStat/xMotivo/chave de qualquer XML de retorno (SOAP ou retEnviNFe)."""
    out = {
        'cStat': '',
        'xMotivo': '',
        'chNFe': '',
        'nProt': '',
        'dhRecbto': '',
    }
    try:
        if isinstance(raw, str):
            raw = raw.encode('utf-8')
        root = etree.fromstring(raw)
    except Exception as exc:
        logger.exception('Falha ao parsear XML SEFAZ: %s', exc)
        out['cStat'] = '999'
        out['xMotivo'] = f'XML inválido: {exc}'
        return out

    inf_prot = _find_inf_prot(root)
    if inf_prot is not None:
        out.update(_text_inf_prot(inf_prot))
        return out

    ret = _find_ret_envi(root) or root
    for tag in ('cStat', 'xMotivo'):
        el = ret.find(f'.//nfe:{tag}', namespaces=NSMAP)
        if el is not None and el.text:
            out[tag] = el.text.strip()
    if not out['cStat']:
        for elem in ret.iter():
            if etree.QName(elem).localname == 'cStat' and elem.text:
                out['cStat'] = elem.text.strip()
                break
        for elem in ret.iter():
            if etree.QName(elem).localname == 'xMotivo' and elem.text:
                out['xMotivo'] = elem.text.strip()
                break

    return out


def enviar_nfe_para_autorizacao(nota) -> dict:
    """
    Envia NF-e para autorização (``ind_sinc=1``).

    Returns:
        dict: autorizada, cStat, xMotivo, chNFe, nProt, xml_proc
    """
    from pynfe.processamento.comunicacao import ComunicacaoSefaz

    from fiscal.nfe_status import get_certificado_path, get_senha_certificado

    if not getattr(nota, 'status', None) == 'EM_PROCESSAMENTO':
        raise ValueError(
            f"Nota #{nota.id} está com status '{getattr(nota, 'status', '')}'. "
            'Só é possível enviar notas com status EM_PROCESSAMENTO.'
        )

    if not nota.xml_arquivo:
        raise ValueError(f'Nota #{nota.id} não possui XML gerado.')

    try:
        config = nota.loja.configuracao_fiscal
    except Exception as exc:
        raise ValueError(f'Configuração fiscal da loja não encontrada: {exc}') from exc

    homologacao = config.ambiente == 'HOMOLOGACAO'
    certificado_path = get_certificado_path(config)
    senha = get_senha_certificado(config)

    con = ComunicacaoSefaz(
        uf='ba',
        certificado=certificado_path,
        certificado_senha=senha,
        homologacao=homologacao,
    )

    xml_text = nota.xml_arquivo
    if isinstance(xml_text, bytes):
        xml_text = xml_text.decode('utf-8', errors='replace')

    try:
        nfe_element = etree.fromstring(xml_text.encode('utf-8'))
    except Exception as exc:
        raise ValueError(f'XML da nota inválido (não é XML bem formado): {exc}') from exc

    logger.info(
        'Enviando NF-e %s/%s para SEFAZ-BA (ambiente=%s, id_lote=%s)',
        nota.numero,
        nota.serie,
        config.ambiente,
        nota.id,
    )

    try:
        retorno_py = con.autorizacao(
            modelo='nfe',
            nota_fiscal=nfe_element,
            id_lote=nota.id,
            ind_sinc=1,
        )
    except Exception as exc:
        logger.exception('Erro de comunicação com SEFAZ: %s', exc)
        return {
            'autorizada': False,
            'cStat': '999',
            'xMotivo': f'Erro de comunicação: {exc}',
            'chNFe': '',
            'nProt': '',
            'xml_proc': '',
        }

    if not isinstance(retorno_py, tuple) or len(retorno_py) < 2:
        return {
            'autorizada': False,
            'cStat': '999',
            'xMotivo': 'Resposta inesperada do PyNFe (tupla inválida).',
            'chNFe': '',
            'nProt': '',
            'xml_proc': '',
        }

    code = retorno_py[0]

    if code == 0 and len(retorno_py) >= 2:
        proc_el = retorno_py[1]
        if isinstance(proc_el, etree._Element):
            xml_proc_str = etree.tostring(
                proc_el,
                encoding='unicode',
                pretty_print=False,
            )
            inf_prot = _find_inf_prot(proc_el)
            if inf_prot is not None:
                parsed = _text_inf_prot(inf_prot)
            else:
                parsed = {'cStat': '', 'xMotivo': '', 'chNFe': '', 'nProt': '', 'dhRecbto': ''}

            cstat = parsed['cStat']
            autorizada = cstat in ('100', '150')
            if cstat == '110':
                autorizada = False

            logger.info(
                'Retorno SEFAZ NF-e %s/%s: cStat=%s xMotivo=%s',
                nota.numero,
                nota.serie,
                cstat,
                parsed['xMotivo'],
            )

            return {
                'autorizada': autorizada,
                'cStat': cstat or ('100' if autorizada else ''),
                'xMotivo': parsed['xMotivo'] or ('Autorizado o uso da NF-e' if autorizada else ''),
                'chNFe': parsed['chNFe'],
                'nProt': parsed['nProt'],
                'xml_proc': xml_proc_str,
            }

    # Falha: (1, response | xml, ...?)
    resp = retorno_py[1]
    raw: bytes
    if hasattr(resp, 'content'):
        raw = resp.content
    elif isinstance(resp, str):
        raw = resp.encode('utf-8', errors='replace')
    elif isinstance(resp, bytes):
        raw = resp
    else:
        raw = str(resp).encode('utf-8', errors='replace')

    resultado = _parse_resposta_bruta(raw)
    cstat = resultado['cStat'] or '999'
    autorizada = cstat in ('100', '150')

    logger.warning(
        'Retorno SEFAZ (análise bruta) NF-e %s/%s: cStat=%s xMotivo=%s',
        nota.numero,
        nota.serie,
        cstat,
        resultado['xMotivo'],
    )

    return {
        'autorizada': autorizada,
        'cStat': cstat,
        'xMotivo': resultado['xMotivo'] or 'Rejeição ou erro no processamento',
        'chNFe': resultado['chNFe'],
        'nProt': resultado['nProt'],
        'xml_proc': '',
    }
