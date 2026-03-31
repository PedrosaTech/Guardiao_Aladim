"""
Serviço de matching de produtos para itens de NF-e de entrada.

Regras:
- cEAN válido: buscar_produto_por_codigo -> VINCULADO se encontrou
- cProd + fornecedor: CodigoBarrasAlternativo -> VINCULADO se encontrou
- NCM + descrição similar (fuzzy): NUNCA auto-vincular; sempre AGUARDANDO_CONFIRMACAO com produto_sugerido
"""
from typing import Optional, Tuple

from produtos.utils import buscar_produto_por_codigo
from produtos.models import CodigoBarrasAlternativo, Produto
from pessoas.models import Fornecedor


def encontrar_ou_sugerir_produto(
    item_nfe: dict,
    fornecedor: Optional[Fornecedor],
    empresa,
) -> Tuple[Optional[Produto], Optional[Produto], str]:
    """
    Encontra ou sugere produto para um item de NF-e.

    Args:
        item_nfe: dict com codigo_barras, codigo_produto_fornecedor, ncm, descricao
        fornecedor: Fornecedor da nota (para buscar CodigoBarrasAlternativo)
        empresa: Empresa para filtrar produtos

    Returns:
        (produto, produto_sugerido, status)
        - produto: Produto vinculado (se encontrou com certeza)
        - produto_sugerido: Sugestão para confirmação (fuzzy match)
        - status: VINCULADO | AGUARDANDO_CONFIRMACAO | NAO_VINCULADO
    """
    codigo_barras = (item_nfe.get('codigo_barras') or '').strip()
    codigo_fornecedor = (item_nfe.get('codigo_produto_fornecedor') or '').strip()
    ncm = (item_nfe.get('ncm') or '').strip()
    descricao = (item_nfe.get('descricao') or '').strip()

    # 1. cEAN válido (8, 12, 13 ou 14 dígitos)
    if codigo_barras and codigo_barras.isdigit() and len(codigo_barras) in [8, 12, 13, 14]:
        produto, _, _ = buscar_produto_por_codigo(codigo_barras, empresa=empresa)
        if produto:
            return produto, None, 'VINCULADO'

    # 2. cProd + fornecedor -> CodigoBarrasAlternativo
    if codigo_fornecedor and fornecedor:
        alt = CodigoBarrasAlternativo.objects.filter(
            codigo_barras=codigo_fornecedor,
            fornecedor=fornecedor,
            produto__is_active=True,
            is_active=True,
        ).select_related('produto').first()
        if alt:
            return alt.produto, None, 'VINCULADO'

        # Também buscar por codigo_fornecedor como cEAN (fornecedor pode usar codigo próprio como EAN)
        if codigo_fornecedor.isdigit() and len(codigo_fornecedor) in [8, 12, 13, 14]:
            alt = CodigoBarrasAlternativo.objects.filter(
                codigo_barras=codigo_fornecedor,
                produto__empresa=empresa,
                produto__is_active=True,
                is_active=True,
            ).select_related('produto').first()
            if alt:
                return alt.produto, None, 'VINCULADO'

    # 3. NCM + descrição similar (fuzzy) -> NUNCA auto-vincular; sempre AGUARDANDO_CONFIRMACAO
    if ncm and descricao:
        produto_sugerido = _buscar_fuzzy_ncm_descricao(ncm, descricao, empresa)
        if produto_sugerido:
            return None, produto_sugerido, 'AGUARDANDO_CONFIRMACAO'

    return None, None, 'NAO_VINCULADO'


def _buscar_fuzzy_ncm_descricao(ncm: str, descricao: str, empresa) -> Optional[Produto]:
    """
    Busca produto por NCM e descrição similar.
    Retorna apenas sugestão; nunca usar como vínculo automático.
    """
    from django.db.models import Q

    # NCM exato (primeiros 4 ou 8 dígitos)
    ncm_limpo = ncm.replace('.', '').replace(' ', '')[:8]
    if not ncm_limpo:
        return None

    qs = Produto.objects.filter(
        empresa=empresa,
        is_active=True,
        ncm__icontains=ncm_limpo[:4],
    )

    # Descrição: primeiras palavras em comum
    palavras = [p for p in descricao[:50].split() if len(p) > 2][:3]
    if palavras:
        for p in palavras:
            qs = qs.filter(descricao__icontains=p)
        if qs.exists():
            return qs.first()

    # NCM + primeira palavra
    if qs.exists() and len(descricao) > 3:
        primeira = descricao.split()[0] if descricao.split() else ''
        if primeira and len(primeira) > 2:
            qs = qs.filter(descricao__icontains=primeira)
            if qs.exists():
                return qs.first()
        return qs.first()

    return None
