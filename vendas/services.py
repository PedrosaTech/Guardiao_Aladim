"""
Serviços para vendas.
"""
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from typing import List, Dict, Optional
import random
from .models import PedidoVenda, ItemPedidoVenda, CondicaoPagamento
from produtos.models import Produto
from produtos.models import CodigoBarrasAlternativo
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

        # Rastreio: código usado / alternativo / multiplicador (opcional)
        codigo_barras_usado = (item_data.get('codigo_barras_usado') or '').strip() or None
        codigo_alternativo_id = item_data.get('codigo_alternativo_id') or None
        multiplicador_aplicado = item_data.get('multiplicador_aplicado')
        try:
            multiplicador_aplicado = Decimal(str(multiplicador_aplicado)) if multiplicador_aplicado is not None else Decimal('1.000')
        except Exception:
            multiplicador_aplicado = Decimal('1.000')

        codigo_alt_obj = None
        if codigo_alternativo_id:
            try:
                codigo_alt_obj = CodigoBarrasAlternativo.objects.select_related('produto').get(
                    pk=int(codigo_alternativo_id),
                    is_active=True,
                )
            except (CodigoBarrasAlternativo.DoesNotExist, ValueError, TypeError):
                raise ValueError("Código alternativo inválido ou inativo.")
            if codigo_alt_obj.produto_id != produto.id:
                raise ValueError("Código alternativo informado não pertence ao produto do item.")
        
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
            codigo_barras_usado=codigo_barras_usado,
            codigo_alternativo_usado=codigo_alt_obj,
            multiplicador_aplicado=multiplicador_aplicado,
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


def gerar_cupom_fiscal(pedido):
    """
    Gera cupom fiscal (SAT/NFC-e).
    TODO: Integrar com sistema fiscal real.
    """
    logger.info(f'[FISCAL] Gerando cupom para pedido #{pedido.id}')
    return f'SAT-{pedido.id:06d}-{random.randint(1000, 9999)}'


def efetivar_pedido_tablet(
    pedido_id: int,
    caixa_sessao_id: int,
    usuario,
    tipo_pagamento: str,
    valor_recebido: Optional[Decimal] = None,
    observacoes: Optional[str] = None,
    emitir_cupom_fiscal: bool = False,
    cpf_cnpj_nota: Optional[str] = None,
) -> dict:
    """
    Efetiva pedido do tablet no balcão.

    Fluxo: validações -> Pagamento -> status FATURADO -> baixa estoque -> títulos.
    Usa estoque.services.registrar_saida_estoque_para_pedido e primeiro local da loja.

    Args:
        pedido_id: ID do pedido
        caixa_sessao_id: ID da sessão de caixa aberta
        usuario: Usuário que está efetivando
        tipo_pagamento: DINHEIRO, PIX, CARTAO_CREDITO, CARTAO_DEBITO
        valor_recebido: Valor recebido (obrigatório para DINHEIRO)
        observacoes: Opcional (não persistido em Pagamento hoje)

    Returns:
        dict: success, pedido_id, pagamento_id, valor_pago, valor_troco,
              movimentos_estoque, titulos_gerados

    Raises:
        ValidationError: Em falha de validação
    """
    tipos_validos = ['DINHEIRO', 'PIX', 'CARTAO_CREDITO', 'CARTAO_DEBITO']
    if tipo_pagamento not in tipos_validos:
        raise ValidationError(f'Tipo de pagamento inválido: {tipo_pagamento}')

    try:
        pedido = PedidoVenda.objects.select_related(
            'loja', 'loja__empresa', 'cliente'
        ).prefetch_related('itens__produto').get(
            id=pedido_id,
            origem='TABLET',
            status='AGUARDANDO_PAGAMENTO',
            is_active=True,
        )
    except PedidoVenda.DoesNotExist:
        raise ValidationError(
            'Pedido não encontrado, já foi finalizado ou não é do tablet.'
        )

    try:
        caixa_sessao = CaixaSessao.objects.select_related('loja').get(
            id=caixa_sessao_id,
            status='ABERTO',
            is_active=True,
        )
        # Qualquer operador pode efetivar se caixa está aberto na loja
    except CaixaSessao.DoesNotExist:
        raise ValidationError(
            'Caixa não está aberto. Abra o caixa antes de efetivar vendas.'
        )

    if pedido.loja_id != caixa_sessao.loja_id:
        raise ValidationError(
            f'Pedido é da loja "{pedido.loja.nome}" mas o caixa é da loja '
            f'"{caixa_sessao.loja.nome}". Pedidos só podem ser efetivados no caixa da mesma loja.'
        )

    itens = pedido.itens.filter(is_active=True).select_related('produto')
    if not itens.exists():
        raise ValidationError('Pedido não possui itens ativos.')

    valor_troco = Decimal('0.00')
    if tipo_pagamento == 'DINHEIRO':
        if valor_recebido is None:
            raise ValidationError(
                'Para pagamento em DINHEIRO é necessário informar o valor recebido.'
            )
        valor_recebido = Decimal(str(valor_recebido))
        if valor_recebido < pedido.valor_total:
            raise ValidationError(
                f'Valor recebido (R$ {valor_recebido:.2f}) é menor que o total do pedido '
                f'(R$ {pedido.valor_total:.2f}).'
            )
        valor_troco = valor_recebido - pedido.valor_total

    local_estoque = pedido.loja.locais_estoque.filter(is_active=True).first()
    if not local_estoque:
        raise ValidationError(
            f'Nenhum local de estoque configurado para a loja "{pedido.loja.nome}".'
        )

    movimentos = []

    with transaction.atomic():
        pagamento = Pagamento.objects.create(
            pedido=pedido,
            caixa_sessao=caixa_sessao,
            tipo=tipo_pagamento,
            valor=pedido.valor_total,
            created_by=usuario,
        )

        pedido.status = 'FATURADO'
        pedido.updated_by = usuario
        update_fields = ['status', 'updated_by', 'updated_at']

        if emitir_cupom_fiscal:
            pedido.emitir_cupom_fiscal = True
            pedido.cpf_cnpj_nota = cpf_cnpj_nota or None
            update_fields.extend(['emitir_cupom_fiscal', 'cpf_cnpj_nota'])
            try:
                numero_cupom = gerar_cupom_fiscal(pedido)
                pedido.numero_cupom_fiscal = numero_cupom
                pedido.data_emissao_cupom = timezone.now()
                update_fields.extend(['numero_cupom_fiscal', 'data_emissao_cupom'])
            except Exception as e:
                logger.error(f'Erro ao gerar cupom fiscal pedido #{pedido.id}: {e}')

        pedido.save(update_fields=update_fields)

        try:
            movimentos = registrar_saida_estoque_para_pedido(
                pedido, local_estoque, usuario
            )
        except ValueError as e:
            logger.error(f"Estoque ao efetivar pedido tablet {pedido.id}: {e}")
            raise ValidationError(str(e))

        titulos_gerados = 0
        try:
            from financeiro.services.financial_service import FinancialService
            titulos = FinancialService.gerar_titulos_de_venda(pedido, usuario)
            titulos_gerados = len(titulos) if titulos else 0
            logger.info(f"Títulos financeiros gerados para pedido #{pedido.id}: {titulos_gerados}")
        except ImportError:
            logger.warning(
                "Módulo financeiro não disponível - títulos não gerados"
            )
        except Exception as e:
            logger.error(
                f"Erro ao gerar títulos para pedido #{pedido.id}: {e}",
                exc_info=True,
            )
            # Não bloquear venda se houver erro no financeiro

    return {
        'success': True,
        'pedido_id': pedido.id,
        'pagamento_id': pagamento.id,
        'valor_pago': float(pedido.valor_total),
        'valor_troco': float(valor_troco),
        'movimentos_estoque': len(movimentos),
        'titulos_gerados': titulos_gerados,
        'numero_cupom': pedido.numero_cupom_fiscal,
    }

