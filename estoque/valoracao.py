"""
Serviço de atualização de custo médio ponderado.
Chamado após cada MovimentoEstoque (via signals).
"""
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.db.models import Sum


def _quantidade_total_empresa_produto(empresa, produto) -> Decimal:
    from .models import EstoqueAtual

    total = EstoqueAtual.objects.filter(
        produto=produto,
        local_estoque__loja__empresa=empresa,
        is_active=True,
    ).aggregate(t=Sum('quantidade'))['t']
    return total if total is not None else Decimal('0.000')


def atualizar_custo_medio(empresa, produto, qtd_entrada, custo_entrada):
    """
    Atualiza EstoqueValorado com custo médio ponderado.

    Usa a soma física em EstoqueAtual **antes** do incremento desta entrada
    (o signal roda logo após criar o movimento e antes de atualizar o EstoqueAtual).

    Args:
        empresa: instância de Empresa
        produto: instância de Produto
        qtd_entrada: Decimal — quantidade que entrou
        custo_entrada: Decimal — custo unitário da entrada
    """
    from .models import EstoqueValorado

    if custo_entrada is None or custo_entrada <= 0:
        return
    if not qtd_entrada or qtd_entrada <= 0:
        return

    Q_before = _quantidade_total_empresa_produto(empresa, produto)
    nova_qtd = Q_before + qtd_entrada

    with transaction.atomic():
        ev, _ = EstoqueValorado.objects.select_for_update().get_or_create(
            empresa=empresa,
            produto=produto,
            defaults={
                'custo_medio': Decimal('0.0000'),
                'quantidade_total': Decimal('0.000'),
            },
        )

        cm_old = ev.custo_medio or Decimal('0.0000')
        if Q_before <= 0:
            novo_custo = Decimal(custo_entrada)
        else:
            total_valor_atual = Q_before * cm_old
            total_valor_entrada = qtd_entrada * Decimal(custo_entrada)
            novo_custo = (total_valor_atual + total_valor_entrada) / nova_qtd

        ev.custo_medio = novo_custo.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
        ev.quantidade_total = nova_qtd
        ev.save()


def atualizar_quantidade_total(empresa, produto):
    """
    Recalcula quantidade_total no EstoqueValorado somando EstoqueAtual da empresa.
    """
    from .models import EstoqueValorado

    total = _quantidade_total_empresa_produto(empresa, produto)
    EstoqueValorado.objects.filter(
        empresa=empresa,
        produto=produto,
    ).update(quantidade_total=total)
