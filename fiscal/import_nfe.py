"""
Serviço de importação de NF-e a partir de arquivo XML.

Suporta estrutura nfeProc (com proc) e NFe direto.
Referência: Manual de Orientação do Contribuinte - NF-e 4.0
"""
import re
import xml.etree.ElementTree as ET
from decimal import Decimal
from datetime import datetime
from typing import Optional

# Namespace padrão NF-e 4.0
NS_NFE = 'http://www.portalfiscal.inf.br/nfe'


def _find_text(element, path: str, default: str = '') -> str:
    """Busca texto em elemento XML. Suporta namespace NFe."""
    if element is None:
        return default
    ns = NS_NFE
    parts = path.split('/')
    current = element
    for part in parts:
        child = current.find(f'{{{ns}}}{part}')
        if child is None:
            child = current.find(part)
        if child is None:
            return default
        current = child
    return (current.text or '').strip()


def _get_root(xml_content: str) -> ET.Element:
    """Obtém o elemento infNFe da NF-e (NFe ou nfeProc)."""
    root = ET.fromstring(xml_content)
    ns = NS_NFE
    # nfeProc contém NFe dentro
    if 'nfeProc' in (root.tag or ''):
        for elem in root.iter():
            if 'infNFe' in (elem.tag or ''):
                return elem
            if 'NFe' in (elem.tag or ''):
                inf = elem.find(f'{{{ns}}}infNFe') or elem.find('infNFe')
                if inf is not None:
                    return inf
    # NFe direto ou infNFe na raiz
    inf = root.find(f'{{{ns}}}infNFe') or root.find('infNFe')
    if inf is not None:
        return inf
    if 'infNFe' in (root.tag or ''):
        return root
    return root


def parse_nfe_xml(xml_content: str) -> dict:
    """
    Extrai dados principais de uma NF-e a partir do XML.

    Returns:
        dict com: chave_acesso, numero, serie, valor_total, data_emissao,
                  cnpj_emitente, razao_social_emitente, xml_arquivo
    Raises:
        ValueError: se XML inválido ou não for NF-e
    """
    if not xml_content or not xml_content.strip():
        raise ValueError('Conteúdo XML vazio.')

    # Remove BOM e espaços
    xml_content = xml_content.strip()
    if xml_content.startswith('\ufeff'):
        xml_content = xml_content[1:]

    try:
        root = _get_root(xml_content)
    except ET.ParseError as e:
        raise ValueError(f'XML inválido: {e}') from e

    # Chave de acesso - pode estar em infNFe ou no atributo Id
    chave = ''
    inf = root
    if root.tag.endswith('infNFe'):
        chave = root.get('Id', '')
        if chave.startswith('NFe'):
            chave = chave[3:]
    if not chave or len(chave) != 44:
        chave = _find_text(root, 'ide/chNFe') or _find_text(root, 'chNFe')
    if not chave or len(chave) != 44:
        raise ValueError('Não foi possível extrair a chave de acesso (44 dígitos) do XML.')

    # ide
    ide = root.find('{http://www.portalfiscal.inf.br/nfe}ide') or root.find('ide')
    numero = _find_text(ide, 'nNF') if ide is not None else ''
    serie = _find_text(ide, 'serie') if ide is not None else ''
    dh_emi = _find_text(ide, 'dhEmi') if ide is not None else ''

    if not numero:
        raise ValueError('Número da nota não encontrado no XML.')

    numero_int = int(numero)
    serie = serie or '1'

    # Data emissão
    data_emissao = None
    if dh_emi:
        try:
            # Formato: 2024-01-15T10:30:00-03:00
            dt = datetime.fromisoformat(dh_emi.replace('Z', '+00:00'))
            data_emissao = dt.date()
        except (ValueError, TypeError):
            pass
    if not data_emissao:
        data_emissao = datetime.now().date()

    # Emitente (fornecedor)
    emit = root.find('{http://www.portalfiscal.inf.br/nfe}emit') or root.find('emit')
    cnpj_emitente = ''
    razao_social_emitente = ''
    if emit is not None:
        cnpj_emitente = _find_text(emit, 'CNPJ') or _find_text(emit, 'CPF')
        razao_social_emitente = _find_text(emit, 'xNome')

    # Valor total
    total = root.find('{http://www.portalfiscal.inf.br/nfe}total') or root.find('total')
    valor_total = Decimal('0.00')
    if total is not None:
        icms = total.find('{http://www.portalfiscal.inf.br/nfe}ICMSTot') or total.find('ICMSTot')
        if icms is not None:
            vnf = _find_text(icms, 'vNF')
            if vnf:
                try:
                    valor_total = Decimal(vnf.replace(',', '.'))
                except (ValueError, TypeError):
                    pass

    # Itens (det)
    itens = []
    ns = NS_NFE
    for det in root.findall(f'{{{ns}}}det') or root.findall('det'):
        n_item = det.get('nItem', str(len(itens) + 1))
        try:
            numero_item = int(n_item)
        except (ValueError, TypeError):
            numero_item = len(itens) + 1

        prod = det.find(f'{{{ns}}}prod') or det.find('prod')
        if prod is None:
            continue

        c_prod = _find_text(prod, 'cProd')
        c_ean = _find_text(prod, 'cEAN')
        if c_ean == 'SEM GTIN':
            c_ean = ''
        ncm = _find_text(prod, 'NCM')
        x_prod = _find_text(prod, 'xProd')
        q_com = _find_text(prod, 'qCom')
        v_un_com = _find_text(prod, 'vUnCom')
        v_prod = _find_text(prod, 'vProd')
        u_com = _find_text(prod, 'uCom') or 'UN'

        quantidade = Decimal('0')
        if q_com:
            try:
                quantidade = Decimal(q_com.replace(',', '.'))
            except (ValueError, TypeError):
                pass

        preco_unitario = Decimal('0')
        if v_un_com:
            try:
                preco_unitario = Decimal(v_un_com.replace(',', '.'))
            except (ValueError, TypeError):
                pass

        valor_total_item = Decimal('0')
        if v_prod:
            try:
                valor_total_item = Decimal(v_prod.replace(',', '.'))
            except (ValueError, TypeError):
                valor_total_item = preco_unitario * quantidade if quantidade else Decimal('0')

        itens.append({
            'numero_item': numero_item,
            'codigo_produto_fornecedor': c_prod,
            'codigo_barras': re.sub(r'\D', '', c_ean) if c_ean and c_ean != 'SEM GTIN' else '',
            'ncm': ncm,
            'descricao': x_prod[:255] if x_prod else '',
            'quantidade': quantidade,
            'unidade_comercial': u_com[:10] if u_com else 'UN',
            'preco_unitario': preco_unitario,
            'valor_total': valor_total_item,
        })

    # Validação rígida: vNF deve bater com soma dos itens (XML é gerado por sistema)
    if itens:
        soma_itens = sum(item['valor_total'] for item in itens)
        if abs(soma_itens - valor_total) > Decimal('0.01'):
            raise ValueError(
                f'XML inconsistente: soma dos produtos (R$ {soma_itens:.2f}) '
                f'difere do total da nota vNF (R$ {valor_total:.2f}). '
                'Verifique o arquivo ou contate o fornecedor.'
            )

    return {
        'chave_acesso': chave,
        'numero': numero_int,
        'serie': serie,
        'valor_total': valor_total,
        'data_emissao': data_emissao,
        'cnpj_emitente': re.sub(r'\D', '', cnpj_emitente) if cnpj_emitente else '',
        'razao_social_emitente': razao_social_emitente,
        'xml_arquivo': xml_content,
        'itens': itens,
    }
