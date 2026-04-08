"""
Geração do XML da NF-e usando PyNFe.
Monta os dados do pedido/nota para assinatura (envio SEFAZ em etapa futura).

NotaFiscalProduto: o serializador 0.6.5 lê vários atributos sem default útil no objeto —
``ind_total``, ``valor_tributos_aprox``, ``pis_modalidade``, ``cofins_modalidade``,
``icms_csosn``, ``icms_credito``, etc. — e precisam ser definidos explicitamente.
"""
import logging
import re
from decimal import Decimal

from django.utils import timezone
from pynfe.entidades.cliente import Cliente
from pynfe.entidades.emitente import Emitente
from pynfe.entidades.fonte_dados import FonteDados
from pynfe.entidades.notafiscal import NotaFiscal, NotaFiscalProduto
from pynfe.processamento.assinatura import AssinaturaA1
from pynfe.processamento.serializacao import SerializacaoXML
from pynfe.utils import obter_municipio_por_codigo
from pynfe.utils.flags import CODIGO_BRASIL

from fiscal.nfe_status import get_certificado_path, get_senha_certificado

logger = logging.getLogger(__name__)


def _limpar_cnpj_cpf(valor: str) -> str:
    return re.sub(r'\D', '', str(valor or ''))


def _limpar_cep(valor: str) -> str:
    return re.sub(r'\D', '', str(valor or ''))


def _somente_digitos_ibge(valor: str) -> str:
    return re.sub(r'\D', '', str(valor or ''))


def _nome_municipio_ibge(codigo_ibge: str, uf: str) -> str:
    try:
        return obter_municipio_por_codigo(codigo_ibge, uf)
    except (ValueError, KeyError) as exc:
        raise ValueError(
            f"Código IBGE {codigo_ibge} inválido ou incompatível com a UF {uf}."
        ) from exc


def _crt_emitente(regime: str) -> str:
    regime_upper = (regime or '').upper()
    if 'EXCESSO' in regime_upper:
        return '2'
    if 'SIMPLES' in regime_upper:
        return '1'
    return '3'


def _dec(val) -> Decimal:
    """Normaliza float/int/Decimal para acúmulo nos totais da nota (evita Decimal + float)."""
    if val is None:
        return Decimal('0')
    if isinstance(val, Decimal):
        return val
    return Decimal(str(val))


def _acumular_totais_produto_na_nfe(nfe: NotaFiscal, obj: NotaFiscalProduto) -> None:
    """Replica a lógica de totais de ``NotaFiscal.adicionar_produto_servico`` para um item já montado."""
    nfe.produtos_e_servicos.append(obj)
    nfe.totais_icms_base_calculo += _dec(obj.icms_valor_base_calculo)
    nfe.totais_icms_total += _dec(obj.icms_valor)
    nfe.totais_icms_desonerado += _dec(obj.icms_desonerado)
    nfe.totais_icms_st_base_calculo += _dec(obj.icms_st_valor_base_calculo)
    nfe.totais_icms_st_total += _dec(obj.icms_st_valor)
    nfe.totais_icms_total_produtos_e_servicos += _dec(obj.valor_total_bruto)
    nfe.totais_icms_total_frete += _dec(obj.total_frete)
    nfe.totais_icms_total_seguro += _dec(obj.total_seguro)
    nfe.totais_icms_total_desconto += _dec(obj.desconto)
    nfe.totais_icms_total_ii += _dec(obj.imposto_importacao_valor)
    nfe.totais_icms_total_ipi += _dec(obj.ipi_valor_ipi)
    nfe.totais_icms_total_ipi_dev += _dec(obj.ipi_valor_ipi_dev)
    nfe.totais_icms_pis += _dec(obj.pis_valor)
    nfe.totais_icms_cofins += _dec(obj.cofins_valor)
    nfe.totais_icms_outras_despesas_acessorias += _dec(obj.outras_despesas_acessorias)
    nfe.totais_fcp += _dec(obj.fcp_valor)
    nfe.totais_fcp_destino += _dec(obj.fcp_destino_valor)
    nfe.totais_fcp_st += _dec(obj.fcp_st_valor)
    nfe.totais_fcp_st_ret += _dec(obj.fcp_st_ret_valor)
    nfe.totais_icms_inter_destino += _dec(obj.icms_inter_destino_valor)
    nfe.totais_icms_inter_remetente += _dec(obj.icms_inter_remetente_valor)
    nfe.totais_icms_q_bc_mono += _dec(obj.icms_q_bc_mono)
    nfe.totais_icms_v_icms_mono += _dec(obj.icms_v_icms_mono)
    nfe.totais_icms_q_bc_mono_reten += _dec(obj.icms_q_bc_mono_reten)
    nfe.totais_icms_v_icms_mono_reten += _dec(obj.icms_v_icms_mono_reten)
    nfe.totais_icms_q_bc_mono_ret += _dec(obj.icms_q_bc_mono_ret)
    nfe.totais_icms_v_icms_mono_ret += _dec(obj.icms_v_icms_mono_ret)
    nfe.totais_icms_total_nota += (
        _dec(obj.valor_total_bruto)
        + _dec(obj.icms_st_valor)
        + _dec(obj.fcp_st_valor)
        + _dec(obj.total_frete)
        + _dec(obj.total_seguro)
        + _dec(obj.outras_despesas_acessorias)
        + _dec(obj.imposto_importacao_valor)
        + _dec(obj.ipi_valor_ipi)
        + _dec(obj.ipi_valor_ipi_dev)
        - _dec(obj.desconto)
        - _dec(obj.icms_desonerado)
    )


def gerar_xml_nfe(nota) -> str:
    """
    Gera o XML da NF-e assinada (string) a partir de uma NotaFiscalSaida em RASCUNHO.
    """
    from produtos.models import ProdutoParametrosEmpresa

    loja = nota.loja
    pedido = nota.pedido_venda
    cliente = nota.cliente

    if pedido is None:
        raise ValueError(f"Nota #{nota.id} não está vinculada a um pedido de venda.")

    try:
        config = loja.configuracao_fiscal
    except Exception as exc:
        raise ValueError(f"Loja {loja.nome} não possui configuração fiscal.") from exc
    homologacao = config.ambiente == 'HOMOLOGACAO'
    homologacao = config.ambiente == 'HOMOLOGACAO'

    cnpj_emitente = _limpar_cnpj_cpf(config.cnpj)
    if len(cnpj_emitente) != 14:
        raise ValueError(f"CNPJ inválido na configuração fiscal da loja {loja.nome}.")

    codigo_ibge_raw = (loja.codigo_ibge_municipio or loja.empresa.codigo_ibge_municipio or '').strip()
    codigo_ibge = _somente_digitos_ibge(codigo_ibge_raw)
    if len(codigo_ibge) != 7:
        raise ValueError(
            f"Código IBGE do município não configurado para a loja {loja.nome}. "
            "Configure em Cadastros → Lojas (ou Empresa como fallback)."
        )

    uf_loja = (loja.uf or 'BA').upper()
    nome_municipio_emitente = _nome_municipio_ibge(codigo_ibge, uf_loja)

    emitente = Emitente(
        razao_social=(loja.empresa.razao_social or loja.nome or '')[:60],
        nome_fantasia=(loja.empresa.nome_fantasia or loja.nome or '')[:60],
        cnpj=cnpj_emitente,
        inscricao_estadual=re.sub(r'\D', '', config.inscricao_estadual or '') or 'ISENTO',
        codigo_de_regime_tributario=_crt_emitente(config.regime_tributario),
        endereco_logradouro=(loja.logradouro or 'Não informado')[:60],
        endereco_numero=(loja.numero or 'S/N')[:60],
        endereco_complemento=(loja.complemento or '')[:60],
        endereco_bairro=(loja.bairro or 'Não informado')[:60],
        endereco_municipio=nome_municipio_emitente,
        endereco_uf=uf_loja,
        endereco_cep=_limpar_cep(loja.cep or ''),
        endereco_pais=CODIGO_BRASIL,
        endereco_telefone=_limpar_cnpj_cpf(loja.telefone or '')[:12] or '',
    )

    cpf_cnpj_dest = _limpar_cnpj_cpf(cliente.cpf_cnpj or '')
    is_pj = cliente.tipo_pessoa == 'PJ' and len(cpf_cnpj_dest) == 14
    is_pf = cliente.tipo_pessoa == 'PF' and len(cpf_cnpj_dest) == 11

    if is_pj:
        doc_tipo, doc_num = 'CNPJ', cpf_cnpj_dest
    elif is_pf and cpf_cnpj_dest != '00000000000':
        doc_tipo, doc_num = 'CPF', cpf_cnpj_dest
    else:
        raise ValueError(
            "Para NF-e é necessário CPF (pessoa física) ou CNPJ válido do destinatário. "
            f"Cadastre o documento do cliente {cliente.nome_razao_social}."
        )

    codigo_ibge_dest = codigo_ibge
    uf_dest = (cliente.uf or uf_loja).upper()
    nome_municipio_dest = _nome_municipio_ibge(codigo_ibge_dest, uf_dest)

    destinatario = Cliente(
        razao_social='NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL' if homologacao else (cliente.nome_razao_social or 'Consumidor Final')[:60],
        email=(cliente.email or ''),
        tipo_documento=doc_tipo,
        numero_documento=doc_num,
        indicador_ie=9,
        endereco_logradouro=(cliente.logradouro or 'Não informado')[:60],
        endereco_numero=(cliente.numero or 'S/N')[:60],
        endereco_complemento=(cliente.complemento or '')[:60],
        endereco_bairro=(cliente.bairro or 'Não informado')[:60],
        endereco_municipio=nome_municipio_dest,
        endereco_uf=uf_dest,
        endereco_cep=_limpar_cep(cliente.cep or loja.cep or ''),
        endereco_pais='1058',
        endereco_telefone=_limpar_cnpj_cpf(cliente.telefone or '')[:12] or '',
    )


    tz_emissao = nota.data_emissao or timezone.now()
    if timezone.is_naive(tz_emissao):
        tz_emissao = timezone.make_aware(tz_emissao, timezone.get_current_timezone())

    nfe = NotaFiscal(
        emitente=emitente,
        cliente=destinatario,
        modelo=55,
        serie=str(int(nota.serie)),
        numero_nf=str(nota.numero),
        data_emissao=tz_emissao,
        data_saida_entrada=tz_emissao,
        natureza_operacao='VENDA',
        tipo_documento=1,
        tipo_impressao_danfe=1,
        forma_emissao='1',
        finalidade_emissao=1,
        cliente_final=1,
        indicador_presencial=1,
        indicador_destino=1,
        indicador_intermediador=0,
        municipio=codigo_ibge,
        uf=uf_loja,
        transporte_modalidade_frete=9,
    )

    itens = pedido.itens.filter(is_active=True).select_related('produto')
    if not itens.exists():
        raise ValueError(f"Pedido #{pedido.id} não possui itens ativos.")

    is_simples = 'SIMPLES' in (config.regime_tributario or '').upper()

    for seq, item in enumerate(itens, start=1):
        produto = item.produto
        try:
            params = ProdutoParametrosEmpresa.objects.get(
                produto=produto,
                empresa=loja.empresa,
            )
        except ProdutoParametrosEmpresa.DoesNotExist:
            raise ValueError(
                f"Produto {produto.codigo_interno} não possui parâmetros fiscais "
                f"para a empresa {loja.empresa.nome_fantasia}."
            )

        valor_total_item = item.total
        desconto = item.desconto or Decimal('0.00')
        quantidade = item.quantidade
        valor_unitario = item.preco_unitario
        base_icms = valor_total_item - desconto
        valor_icms = (base_icms * params.aliquota_icms / Decimal('100')).quantize(Decimal('0.01'))
        valor_pis = (base_icms * params.aliquota_pis / Decimal('100')).quantize(Decimal('0.01'))
        valor_cofins = (base_icms * params.aliquota_cofins / Decimal('100')).quantize(Decimal('0.01'))

        ncm = re.sub(r'\D', '', produto.ncm or '')
        if len(ncm) != 8:
            raise ValueError(
                f"Produto {produto.codigo_interno}: NCM deve ter 8 dígitos (atual: {produto.ncm!r})."
            )

        cest_digits = re.sub(r'\D', '', produto.cest or '')
        cfop = re.sub(r'\D', '', params.cfop_venda_dentro_uf or '5102')
        if len(cfop) != 4:
            cfop = '5102'

        p = NotaFiscalProduto()

        p.numero_item = str(seq)
        p.codigo = produto.codigo_interno or str(produto.id)
        p.ean = (produto.codigo_barras or '').strip() or 'SEM GTIN'
        p.ean_tributavel = p.ean
        p.descricao = (produto.descricao or 'Produto').strip()[:120]
        p.ncm = ncm
        p.cest = cest_digits or ''
        p.cfop = cfop

        p.unidade_comercial = produto.unidade_comercial or 'UN'
        p.unidade_tributavel = produto.unidade_comercial or 'UN'
        p.quantidade_comercial = float(quantidade)
        p.quantidade_tributavel = float(quantidade)
        p.valor_unitario_comercial = float(valor_unitario)
        p.valor_unitario_tributavel = float(valor_unitario)
        p.valor_total_bruto = float(valor_total_item)
        p.desconto = float(desconto)
        p.total_frete = 0
        p.total_seguro = 0
        p.outras_despesas_acessorias = 0

        p.ind_total = 1
        p.valor_tributos_aprox = 0
        p.informacoes_adicionais = ''
        p.numero_pedido = ''
        p.nfci = ''

        csosn_raw = (params.csosn_cst or '').strip()
        p.icms_origem = int(produto.origem or '0')
        if is_simples:
            csosn3 = csosn_raw.zfill(3)[-3:]
            p.icms_modalidade = csosn3
            p.icms_csosn = csosn3
            p.icms_credito = 0
            p.icms_modalidade_determinacao_bc = 0
            p.icms_valor_base_calculo = 0.0
            p.icms_aliquota = 0.0
            p.icms_valor = 0.0
        else:
            cst2 = csosn_raw.zfill(2)[-2:]
            p.icms_modalidade = cst2
            p.icms_csosn = ''
            p.icms_credito = 0
            p.icms_modalidade_determinacao_bc = 3
            p.icms_valor_base_calculo = float(base_icms)
            p.icms_aliquota = float(params.aliquota_icms)
            p.icms_valor = float(valor_icms)

        pis_cst = (params.pis_cst or '01').strip().zfill(2)[-2:]
        p.pis_situacao_tributaria = pis_cst
        p.pis_modalidade = pis_cst
        p.pis_tipo_calculo = 'percentual'
        p.pis_valor_base_calculo = float(base_icms)
        p.pis_aliquota_percentual = float(params.aliquota_pis)
        p.pis_valor = float(valor_pis)

        cofins_cst = (params.cofins_cst or '01').strip().zfill(2)[-2:]
        p.cofins_situacao_tributaria = cofins_cst
        p.cofins_modalidade = cofins_cst
        p.cofins_tipo_calculo = 'percentual'
        p.cofins_valor_base_calculo = float(base_icms)
        p.cofins_aliquota_percentual = float(params.aliquota_cofins)
        p.cofins_valor = float(valor_cofins)

        ipi_cst = (params.ipi_venda_cst or '53').strip()
        p.ipi_situacao_tributaria = ipi_cst
        p.ipi_codigo_enquadramento = '999'
        p.ipi_valor_base_calculo = 0.0
        p.ipi_aliquota = 0.0
        p.ipi_valor_ipi = 0.0

        _acumular_totais_produto_na_nfe(nfe, p)

    total_nota = nfe.totais_icms_total_nota
    nfe.adicionar_autorizados_baixar_xml(CPFCNPJ='13937073000156')
    nfe.adicionar_pagamento(
        t_pag='01',
        v_pag=Decimal(str(total_nota)),
        ind_pag=0,
    )

    fonte = FonteDados()
    fonte.adicionar_objeto(nfe)

    serializador = SerializacaoXML(fonte, homologacao=homologacao)
    xml_raiz = serializador.exportar(retorna_string=False)

    certificado_path = get_certificado_path(config)
    senha = get_senha_certificado(config)
    assinatura = AssinaturaA1(certificado_path, senha)
    return assinatura.assinar(xml_raiz, retorna_string=True)


def salvar_xml_na_nota(nota, xml_assinado: str) -> None:
    nota.xml_arquivo = xml_assinado
    nota.status = 'EM_PROCESSAMENTO'
    nota.save(update_fields=['xml_arquivo', 'status', 'updated_at'])
    logger.info('XML NF-e salvo para nota %s/%s (id=%s)', nota.numero, nota.serie, nota.pk)
