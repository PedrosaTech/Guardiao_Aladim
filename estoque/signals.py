"""
Signals do módulo de estoque.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import MovimentoEstoque


@receiver(post_save, sender=MovimentoEstoque)
def atualizar_valoracao_apos_movimento(sender, instance, created, **kwargs):
    """
    Após criar um MovimentoEstoque:
    - ENTRADA com custo_unitario → custo médio ponderado (EstoqueAtual ainda sem o incremento).

    Sincronização de quantidade_total para demais casos fica em realizar_movimento_estoque
    (após atualizar EstoqueAtual), para funcionar em testes e evitar depender de on_commit.
    """
    if not created:
        return

    from estoque.valoracao import atualizar_custo_medio

    movimento = instance
    if (
        movimento.tipo_movimento == 'ENTRADA'
        and movimento.local_destino
        and movimento.custo_unitario
        and movimento.custo_unitario > 0
    ):
        atualizar_custo_medio(
            empresa=movimento.local_destino.loja.empresa,
            produto=movimento.produto,
            qtd_entrada=movimento.quantidade,
            custo_entrada=movimento.custo_unitario,
        )
