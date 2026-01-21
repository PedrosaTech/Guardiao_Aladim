"""
Serviços para vendas.
"""
from django.db import transaction
from decimal import Decimal
from typing import List, Dict, Optional
from .models import PedidoVenda, ItemPedidoVenda, CondicaoPagamento
from produtos.models import Produto
from pessoas.models import Cliente
from core.models import Loja
from pdv.models import CaixaSessao, Pagamento
from estoque.services import registrar_saida_estoque_para_pedido
from estoque.models import LocalEstoque
import logging

logger = logging.getLogger(__name__)


@transaction.atomic
def criar_pedido_venda_balcao(
    loja: Loja,
    caixa_sessao: CaixaSessao,
    usuario,
    itens: List[Dict],
    tipo_pagamento: str,
    cliente: Optional[Cliente] = None,
    local_estoque: Optional[LocalEstoque] = None,
) -> PedidoVenda:
    """
    Cria um pedido de venda de balcão completo.
    
    Args:
        loja: Loja onde a venda está sendo realizada
        caixa_sessao: Sessão de caixa aberta
        usuario: Usuário que está realizando a venda
        itens: Lista de itens com formato:
            [
                {
                    'produto_id': int,
                    'quantidade': Decimal ou str,
                    'preco_unitario': Decimal ou str (opcional, usa preco_venda_sugerido se não informado),
                    'desconto': Decimal ou str (opcional, default 0)
                },
                ...
            ]
        tipo_pagamento: Tipo de pagamento (DINHEIRO, PIX, CARTAO_CREDITO, CARTAO_DEBITO)
        cliente: Cliente (opcional, pode ser None para venda avulsa)
        local_estoque: Local de estoque para baixar (se None, usa o primeiro local da loja)
    
    Returns:
        PedidoVenda criado
    
    Raises:
        ValueError: Se houver erro de validação
        Exception: Se houver erro na criação
    """
    # Validações
    if not itens:
        raise ValueError("A venda deve ter pelo menos um item")
    
    if caixa_sessao.status != 'ABERTO':
        raise ValueError("A sessão de caixa deve estar aberta")
    
    if caixa_sessao.loja != loja:
        raise ValueError("A sessão de caixa não pertence à loja informada")
    
    # Busca ou cria condição de pagamento padrão (à vista)
    condicao_pagamento = CondicaoPagamento.objects.filter(
        empresa=loja.empresa,
        nome__icontains='vista',
        is_active=True
    ).first()
    
    if not condicao_pagamento:
        condicao_pagamento = CondicaoPagamento.objects.create(
            empresa=loja.empresa,
            nome='À Vista',
            numero_parcelas=1,
            dias_entre_parcelas=0,
            created_by=usuario,
        )
        logger.info(f"Condição de pagamento padrão criada para empresa {loja.empresa.id}")
    
    # Se não houver cliente, cria ou busca cliente genérico "Consumidor Final"
    if not cliente:
        cliente, _ = Cliente.objects.get_or_create(
            empresa=loja.empresa,
            tipo_pessoa='PF',
            nome_razao_social='Consumidor Final',
            cpf_cnpj='00000000000',
            defaults={
                'created_by': usuario,
            }
        )
        logger.info(f"Usando cliente genérico 'Consumidor Final' para venda balcão")
    
    # Cria o pedido
    pedido = PedidoVenda.objects.create(
        loja=loja,
        cliente=cliente,
        tipo_venda='BALCAO',
        status='FATURADO',  # Por enquanto, vendas de balcão são faturadas imediatamente
        vendedor=usuario,
        condicao_pagamento=condicao_pagamento,
        valor_total=Decimal('0.00'),  # Será recalculado
        created_by=usuario,
    )
    
    # Cria os itens
    valor_total_pedido = Decimal('0.00')
    produtos_com_restricao = []
    
    for item_data in itens:
        produto_id = item_data.get('produto_id')
        if not produto_id:
            raise ValueError("Item deve ter produto_id")
        
        produto = Produto.objects.get(id=produto_id, is_active=True)
        quantidade = Decimal(str(item_data.get('quantidade', 1)))
        preco_unitario = Decimal(str(item_data.get('preco_unitario', produto.preco_venda_sugerido)))
        desconto = Decimal(str(item_data.get('desconto', 0)))
        
        # Verifica se produto tem restrição de Exército
        if produto.possui_restricao_exercito:
            produtos_com_restricao.append(produto.codigo_interno)
            # TODO: No futuro, exigir dados específicos do comprador para produtos com restrição
            # TODO: Registrar em auditoria para possível verificação futura
        
        item = ItemPedidoVenda.objects.create(
            pedido=pedido,
            produto=produto,
            quantidade=quantidade,
            preco_unitario=preco_unitario,
            desconto=desconto,
            created_by=usuario,
        )
        
        valor_total_pedido += item.total
    
    # Atualiza valor total do pedido
    pedido.valor_total = valor_total_pedido
    pedido.save(update_fields=['valor_total', 'updated_at'])
    
    # Baixa estoque
    if local_estoque:
        try:
            registrar_saida_estoque_para_pedido(pedido, local_estoque, usuario)
        except Exception as e:
            logger.error(f"Erro ao baixar estoque para pedido {pedido.id}: {str(e)}")
            raise ValueError(f"Erro ao baixar estoque: {str(e)}")
    else:
        # Se não informado, usa o primeiro local de estoque da loja
        local_estoque = loja.locais_estoque.filter(is_active=True).first()
        if local_estoque:
            try:
                registrar_saida_estoque_para_pedido(pedido, local_estoque, usuario)
            except Exception as e:
                logger.error(f"Erro ao baixar estoque para pedido {pedido.id}: {str(e)}")
                raise ValueError(f"Erro ao baixar estoque: {str(e)}")
        else:
            logger.warning(f"Nenhum local de estoque encontrado para loja {loja.id}")
            # TODO: Criar local de estoque padrão ou exigir que seja criado
    
    # Cria o pagamento
    Pagamento.objects.create(
        pedido=pedido,
        caixa_sessao=caixa_sessao,
        tipo=tipo_pagamento,
        valor=valor_total_pedido,
        created_by=usuario,
    )
    
    # Gera títulos financeiros automaticamente
    try:
        from financeiro.services.financial_service import FinancialService
        FinancialService.gerar_titulos_de_venda(pedido, usuario)
        logger.info(f"Títulos financeiros gerados para pedido #{pedido.id}")
    except Exception as e:
        logger.error(f"Erro ao gerar títulos financeiros para pedido #{pedido.id}: {str(e)}")
        # Não bloqueia a venda se houver erro ao gerar títulos
    
    # Log de sucesso
    logger.info(
        f"Pedido de venda balcão criado: ID={pedido.id}, "
        f"Loja={loja.id}, Valor={valor_total_pedido}, "
        f"Itens={len(itens)}, Usuário={usuario.username}"
    )
    
    if produtos_com_restricao:
        logger.warning(
            f"Pedido {pedido.id} contém produtos com restrição de Exército: {produtos_com_restricao}"
        )
    
    # TODO: Disparar emissão de NFC-e aqui (futuro)
    
    return pedido

