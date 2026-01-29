"""
Funções auxiliares para produtos.
"""
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, Tuple

from django.db.models import Q

if TYPE_CHECKING:
    from produtos.models import CodigoBarrasAlternativo, Empresa, Produto


def buscar_produto_por_codigo(
    codigo_barras: str,
    empresa: Optional['Empresa'] = None,
) -> Tuple[Optional['Produto'], Optional['CodigoBarrasAlternativo'], Decimal]:
    """
    Busca produto pelo código de barras principal OU alternativo.

    Args:
        codigo_barras: Código de barras a buscar
        empresa: Filtrar por empresa (None = todos)

    Returns:
        (Produto ou None, CodigoBarrasAlternativo ou None, multiplicador)
    """
    from produtos.models import CodigoBarrasAlternativo, Produto

    if not codigo_barras:
        return None, None, Decimal('1.0')

    codigo_barras = codigo_barras.strip()

    qs = Produto.objects.filter(is_active=True)
    if empresa:
        qs = qs.filter(empresa=empresa)

    produto = qs.filter(codigo_barras=codigo_barras).first()
    if produto:
        return produto, None, Decimal('1.0')

    alt_qs = CodigoBarrasAlternativo.objects.filter(
        codigo_barras=codigo_barras,
        produto__is_active=True,
        is_active=True,
    ).select_related('produto')
    if empresa:
        alt_qs = alt_qs.filter(produto__empresa=empresa)
    alt = alt_qs.first()

    if alt:
        return alt.produto, alt, alt.multiplicador

    return None, None, Decimal('1.0')


def buscar_produtos_por_termo(
    termo: str,
    empresa: Optional['Empresa'] = None,
    limit: int = 100,
    order_by: tuple = ('descricao',),
    select_related: tuple = (),
):
    """
    Busca produtos por nome, código interno ou código de barras (principal/alternativo).

    Args:
        termo: Termo de busca
        empresa: Filtrar por empresa (None = todos)
        limit: Limite de resultados
        order_by: Campos para order_by (antes do slice)
        select_related: Campos para select_related (antes do slice)

    Returns:
        QuerySet de Produto (distinct, limitado, ordenado)
    """
    from produtos.models import CodigoBarrasAlternativo, Produto

    if not termo:
        return Produto.objects.none()

    termo = termo.strip()

    qs = Produto.objects.filter(is_active=True)
    if empresa:
        qs = qs.filter(empresa=empresa)

    produtos = qs.filter(
        Q(descricao__icontains=termo)
        | Q(codigo_interno__icontains=termo)
        | Q(codigo_barras__icontains=termo)
    )

    ids_alt = CodigoBarrasAlternativo.objects.filter(
        codigo_barras__icontains=termo,
        produto__is_active=True,
        is_active=True,
    )
    if empresa:
        ids_alt = ids_alt.filter(produto__empresa=empresa)
    ids_alt = ids_alt.values_list('produto_id', flat=True)

    produtos = produtos | qs.filter(id__in=ids_alt)
    qs = produtos.distinct()
    if select_related:
        qs = qs.select_related(*select_related)
    if order_by:
        qs = qs.order_by(*order_by)
    return qs[:limit]


def validar_codigo_barras_formato(codigo: str) -> Tuple[bool, str]:
    """
    Valida formato do código de barras.

    Args:
        codigo: Código a validar

    Returns:
        (is_valid, message)
    """
    if not codigo:
        return False, 'Código de barras não pode ser vazio'

    codigo = codigo.strip()

    if not codigo.isdigit():
        return False, 'Código de barras deve conter apenas números'

    if len(codigo) not in [8, 12, 13, 14]:
        return False, 'Código de barras deve ter 8, 12, 13 ou 14 dígitos (EAN/GTIN/UPC)'

    return True, 'OK'
