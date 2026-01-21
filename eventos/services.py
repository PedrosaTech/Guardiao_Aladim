"""
Serviços para eventos.
"""
from django.db import transaction
from decimal import Decimal
from typing import Optional
import logging

from .models import EventoVenda
from vendas.models import PedidoVenda
from fiscal.models import NotaFiscalSaida

logger = logging.getLogger(__name__)


@transaction.atomic
def faturar_evento_com_nfe(evento: EventoVenda, usuario=None) -> NotaFiscalSaida:
    """
    Fatura um evento criando a NF-e associada.
    
    TODO: Integrar com SEFAZ-BA para emissão real de NF-e
    TODO: Validar dados fiscais antes de criar a nota
    TODO: Gerar XML da nota fiscal
    
    Args:
        evento: EventoVenda a ser faturado
        usuario: Usuário que está realizando a operação
    
    Returns:
        NotaFiscalSaida criada
    
    Raises:
        ValueError: Se houver erro de validação
    """
    if not evento.pedido:
        raise ValueError("Evento não possui pedido associado")
    
    pedido = evento.pedido
    
    if pedido.itens.filter(is_active=True).count() == 0:
        raise ValueError("Pedido não possui itens")
    
    if pedido.status == 'FATURADO':
        raise ValueError("Pedido já está faturado")
    
    # Verifica se já existe nota fiscal para este evento
    nota_existente = NotaFiscalSaida.objects.filter(evento=evento).first()
    if nota_existente:
        logger.warning(f"Nota fiscal já existe para evento {evento.id}: {nota_existente.numero}")
        return nota_existente
    
    # Busca configuração fiscal da loja
    from fiscal.models import ConfiguracaoFiscalLoja
    config_fiscal = getattr(evento.loja, 'configuracao_fiscal', None)
    
    if not config_fiscal:
        raise ValueError(f"Loja {evento.loja.nome} não possui configuração fiscal")
    
    # Gera número da nota
    numero_nfe = config_fiscal.proximo_numero_nfe
    config_fiscal.proximo_numero_nfe += 1
    config_fiscal.save(update_fields=['proximo_numero_nfe', 'updated_at'])
    
    # Cria a nota fiscal
    nota_fiscal = NotaFiscalSaida.objects.create(
        loja=evento.loja,
        cliente=pedido.cliente,
        pedido_venda=pedido,
        evento=evento,
        tipo_documento='NFE',
        numero=numero_nfe,
        serie=config_fiscal.serie_nfe,
        valor_total=pedido.valor_total,
        status='RASCUNHO',  # TODO: Mudar para EM_PROCESSAMENTO quando integrar com SEFAZ
        created_by=usuario,
    )
    
    # Atualiza status do pedido
    pedido.status = 'FATURADO'
    pedido.save(update_fields=['status', 'updated_at'])
    
    # Atualiza status do evento
    evento.status = 'CONCLUIDO'
    evento.save(update_fields=['status', 'updated_at'])
    
    logger.info(
        f"Evento {evento.id} faturado: Nota Fiscal {nota_fiscal.numero}/{nota_fiscal.serie} criada"
    )
    
    # TODO: Disparar emissão real da NF-e na SEFAZ-BA
    # TODO: Atualizar status da nota após autorização
    
    return nota_fiscal

