"""
Serviços para entrada de estoque a partir de Nota Fiscal de Entrada.
"""
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
from typing import Tuple, List, Iterable, Union

from .models import NotaFiscalEntrada, ItemNotaFiscalEntrada, HistoricoEntradaEstoque
from estoque.services import realizar_movimento_estoque
from estoque.models import LocalEstoque

TOLERANCIA_MANUAL = Decimal('0.10')


def validar_totais(
    nota_valor_total: Decimal,
    itens_valores: Iterable[Union[Decimal, float]],
    tolerancia: Decimal = TOLERANCIA_MANUAL,
) -> None:
    """
    Valida se a soma dos itens bate com o total da nota.

    Args:
        nota_valor_total: valor total da nota (vNF)
        itens_valores: iterável com valor_total de cada item
        tolerancia: diferença aceitável (ex: R$ 0,10 para arredondamento).
                    Use Decimal('0') para XML (validação rígida).

    Raises:
        ValidationError: se a diferença exceder a tolerância
    """
    total_itens = sum(Decimal(str(v)) for v in itens_valores)
    diferenca = abs(total_itens - Decimal(str(nota_valor_total)))
    if diferenca > tolerancia:
        raise ValidationError(
            f"Soma dos itens (R$ {total_itens:.2f}) difere do total da nota "
            f"(R$ {nota_valor_total:.2f}) em R$ {diferenca:.2f}. "
            "Corrija os valores antes de salvar."
        )


def dar_entrada_estoque_nota(
    nota: NotaFiscalEntrada,
    local_estoque_padrao: LocalEstoque,
    usuario,
) -> Tuple[int, List[str], str]:
    """
    Dá entrada em estoque para os itens vinculados da nota.

    Fonte de verdade: ItemNotaFiscalEntrada.status != ESTOQUE_ENTRADO
    Usa savepoint por item para modo "melhor esforço".

    Returns:
        (itens_processados, lista_erros, motivo_parcial)
        motivo_parcial: None | 'PARCIAL_SEM_VINCULO' | 'PARCIAL_COM_ERRO'
    """
    itens_processados = 0
    lista_erros = []
    motivo_parcial = None

    itens_todos = list(nota.itens.filter(is_active=True))
    if itens_todos:
        validar_totais(
            nota.valor_total,
            (i.valor_total for i in itens_todos),
            tolerancia=TOLERANCIA_MANUAL,
        )
    itens = nota.itens.filter(
        is_active=True,
        produto__isnull=False,
    ).exclude(status='ESTOQUE_ENTRADO').select_related('produto', 'local_estoque')

    total_vinculados = nota.itens.filter(is_active=True, produto__isnull=False).count()
    total_estoque_entrado_antes = nota.itens.filter(
        is_active=True, status='ESTOQUE_ENTRADO'
    ).count()

    for item in itens:
        local = item.local_estoque or local_estoque_padrao
        if not local:
            lista_erros.append(f"Item {item.numero_item}: Nenhum local de estoque definido.")
            motivo_parcial = 'PARCIAL_COM_ERRO'
            continue

        sid = transaction.savepoint()
        try:
            realizar_movimento_estoque(
                produto=item.produto,
                tipo_movimento='ENTRADA',
                quantidade=item.quantidade,
                local_destino=local,
                referencia=f"NFE_{nota.id}",
                observacao=f"NF-e Entrada {nota.numero}/{nota.serie} - Item {item.numero_item}",
                usuario=usuario,
                custo_unitario=item.preco_unitario,
            )
            item.status = 'ESTOQUE_ENTRADO'
            item.save(update_fields=['status', 'updated_at'])
            itens_processados += 1
            transaction.savepoint_commit(sid)
        except Exception as e:
            transaction.savepoint_rollback(sid)
            lista_erros.append(f"Item {item.numero_item} ({item.descricao[:30]}...): {e}")
            motivo_parcial = 'PARCIAL_COM_ERRO'

    total_estoque_entrado_depois = nota.itens.filter(
        is_active=True, status='ESTOQUE_ENTRADO'
    ).count()

    if itens_processados > 0:
        nota.data_entrada_estoque = timezone.now()
        nota.usuario_entrada_estoque = usuario
        if total_estoque_entrado_depois >= total_vinculados:
            nota.status = 'ESTOQUE_TOTAL'
        else:
            nota.status = 'ESTOQUE_PARCIAL'
            if not motivo_parcial:
                motivo_parcial = 'PARCIAL_SEM_VINCULO'
        nota.save(update_fields=['data_entrada_estoque', 'usuario_entrada_estoque', 'status', 'updated_at'])

        HistoricoEntradaEstoque.objects.create(
            nota_fiscal=nota,
            usuario=usuario,
            itens_processados=itens_processados,
            motivo_parcial=motivo_parcial,
            erros=lista_erros,
        )

    return itens_processados, lista_erros, motivo_parcial
