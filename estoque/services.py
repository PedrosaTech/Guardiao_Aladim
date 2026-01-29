"""
Serviços para movimentação de estoque.
"""
from django.db import transaction
from decimal import Decimal
from typing import List
from .models import EstoqueAtual, MovimentoEstoque, LocalEstoque
from produtos.models import Produto
import logging

logger = logging.getLogger(__name__)


@transaction.atomic
def realizar_movimento_estoque(
    produto: Produto,
    tipo_movimento: str,
    quantidade: Decimal,
    local_origem: LocalEstoque = None,
    local_destino: LocalEstoque = None,
    referencia: str = None,
    observacao: str = None,
    usuario=None
) -> MovimentoEstoque:
    """
    Realiza uma movimentação de estoque de forma atômica.
    
    Args:
        produto: Produto a ser movimentado
        tipo_movimento: Tipo de movimento (ENTRADA, SAIDA, TRANSFERENCIA, AJUSTE)
        quantidade: Quantidade a ser movimentada
        local_origem: Local de origem (para SAIDA e TRANSFERENCIA)
        local_destino: Local de destino (para ENTRADA e TRANSFERENCIA)
        referencia: Referência externa (ID de pedido, nota, etc.)
        observacao: Observação sobre o movimento
        usuario: Usuário que realizou o movimento
    
    Returns:
        MovimentoEstoque criado
    
    Raises:
        ValueError: Se os parâmetros forem inválidos
    """
    # Validações
    if tipo_movimento == 'ENTRADA' and not local_destino:
        raise ValueError("ENTRADA requer local_destino")
    if tipo_movimento == 'SAIDA' and not local_origem:
        raise ValueError("SAIDA requer local_origem")
    if tipo_movimento == 'TRANSFERENCIA' and (not local_origem or not local_destino):
        raise ValueError("TRANSFERENCIA requer local_origem e local_destino")
    if tipo_movimento == 'AJUSTE' and not local_destino:
        raise ValueError("AJUSTE requer local_destino")
    
    # Verifica quantidade disponível para saída/transferência
    if tipo_movimento in ['SAIDA', 'TRANSFERENCIA']:
        estoque_origem, _ = EstoqueAtual.objects.get_or_create(
            produto=produto,
            local_estoque=local_origem,
            defaults={'quantidade': Decimal('0.000')}
        )
        if estoque_origem.quantidade < quantidade:
            raise ValueError(
                f"Quantidade insuficiente em {local_origem.nome}. "
                f"Disponível: {estoque_origem.quantidade}, Solicitado: {quantidade}"
            )
    
    # Cria o movimento
    movimento = MovimentoEstoque.objects.create(
        produto=produto,
        local_origem=local_origem,
        local_destino=local_destino,
        tipo_movimento=tipo_movimento,
        quantidade=quantidade,
        referencia=referencia,
        observacao=observacao,
        created_by=usuario,
    )
    
    # Atualiza estoques
    if tipo_movimento == 'ENTRADA':
        estoque_destino, _ = EstoqueAtual.objects.get_or_create(
            produto=produto,
            local_estoque=local_destino,
            defaults={'quantidade': Decimal('0.000')}
        )
        estoque_destino.quantidade += quantidade
        estoque_destino.save(update_fields=['quantidade', 'updated_at'])
    
    elif tipo_movimento == 'SAIDA':
        estoque_origem.quantidade -= quantidade
        estoque_origem.save(update_fields=['quantidade', 'updated_at'])
    
    elif tipo_movimento == 'TRANSFERENCIA':
        estoque_origem.quantidade -= quantidade
        estoque_origem.save(update_fields=['quantidade', 'updated_at'])
        
        estoque_destino, _ = EstoqueAtual.objects.get_or_create(
            produto=produto,
            local_estoque=local_destino,
            defaults={'quantidade': Decimal('0.000')}
        )
        estoque_destino.quantidade += quantidade
        estoque_destino.save(update_fields=['quantidade', 'updated_at'])
    
    elif tipo_movimento == 'AJUSTE':
        estoque_destino, _ = EstoqueAtual.objects.get_or_create(
            produto=produto,
            local_estoque=local_destino,
            defaults={'quantidade': Decimal('0.000')}
        )
        estoque_destino.quantidade = quantidade
        estoque_destino.save(update_fields=['quantidade', 'updated_at'])
    
    # TODO: Log de segurança para produtos com restrição de Exército
    if produto.possui_restricao_exercito:
        logger.warning(
            f"Movimentação de produto com restrição de Exército: "
            f"Produto={produto.codigo_interno}, "
            f"Tipo={tipo_movimento}, "
            f"Quantidade={quantidade}, "
            f"Usuário={usuario}"
        )
    
    return movimento


@transaction.atomic
def registrar_saida_estoque_para_pedido(
    pedido,
    local_estoque: LocalEstoque,
    usuario=None
) -> List[MovimentoEstoque]:
    """
    Registra saída de estoque para todos os itens de um pedido de venda.
    
    Args:
        pedido: PedidoVenda
        local_estoque: LocalEstoque de onde será baixado o estoque
        usuario: Usuário que realizou a operação
    
    Returns:
        Lista de MovimentoEstoque criados
    
    Raises:
        ValueError: Se houver estoque insuficiente ou erro de validação
    """
    from vendas.models import PedidoVenda, ItemPedidoVenda
    
    if not isinstance(pedido, PedidoVenda):
        raise ValueError("pedido deve ser uma instância de PedidoVenda")
    
    movimentos = []
    itens = pedido.itens.filter(is_active=True)
    
    if not itens.exists():
        raise ValueError("Pedido não possui itens ativos")
    
    # TODO: Validar se há estoque suficiente antes de permitir a venda
    # Por enquanto, a validação é feita dentro de realizar_movimento_estoque
    
    for item in itens:
        produto = item.produto
        
        # Valida estoque disponível
        estoque_atual, _ = EstoqueAtual.objects.get_or_create(
            produto=produto,
            local_estoque=local_estoque,
            defaults={'quantidade': Decimal('0.000')}
        )
        
        if estoque_atual.quantidade < item.quantidade:
            raise ValueError(
                f"Estoque insuficiente para produto {produto.codigo_interno} ({produto.descricao}). "
                f"Local: {local_estoque.nome} (Loja: {local_estoque.loja.nome}). "
                f"Disponível: {estoque_atual.quantidade}, Solicitado: {item.quantidade}"
            )
        
        # TODO: Emitir alerta se o produto tem possui_restricao_exercito=True
        if produto.possui_restricao_exercito:
            logger.warning(
                f"Baixando estoque de produto com restrição de Exército: "
                f"Produto={produto.codigo_interno}, "
                f"Pedido={pedido.id}, "
                f"Quantidade={item.quantidade}, "
                f"Usuário={usuario}"
            )
        
        # Cria movimento de saída
        movimento = realizar_movimento_estoque(
            produto=produto,
            tipo_movimento='SAIDA',
            quantidade=item.quantidade,
            local_origem=local_estoque,
            referencia=f"PEDIDO_{pedido.id}",
            observacao=f"Venda balcão - Pedido #{pedido.id}",
            usuario=usuario,
        )
        
        movimentos.append(movimento)
    
    logger.info(
        f"Estoque baixado para pedido {pedido.id}: "
        f"{len(movimentos)} movimentos criados no local {local_estoque.nome}"
    )
    
    return movimentos

