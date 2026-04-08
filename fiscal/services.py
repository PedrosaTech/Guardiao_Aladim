"""
Serviços do módulo fiscal.
"""
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import NotaFiscalSaida, ConfiguracaoFiscalLoja
from .numeracao import reservar_numero_nfe
from vendas.models import PedidoVenda
import logging

logger = logging.getLogger(__name__)


def _fallback_numero_serie_nfe(pedido_loja):
    """Numeração local quando não há ConfiguracaoFiscalLoja ativa (desenvolvimento / legado)."""
    serie = '001'
    ultima_nota = (
        NotaFiscalSaida.objects.filter(
            loja=pedido_loja,
            tipo_documento='NFE',
            serie=serie,
            is_active=True,
        )
        .order_by('-numero')
        .first()
    )
    if ultima_nota:
        numero = ultima_nota.numero + 1
    else:
        numero = 1
    return numero, serie


def _reservar_nfe_com_fallback(loja, log_warning_sem_config=False):
    """
    Reserva número com lock; se não houver config fiscal, usa fallback.
    """
    try:
        return reservar_numero_nfe(loja)
    except ConfiguracaoFiscalLoja.DoesNotExist:
        if log_warning_sem_config:
            logger.warning(
                f"Loja {loja.id} não possui configuração fiscal ativa. Usando numeração local (sem contador)."
            )
        return _fallback_numero_serie_nfe(loja)


def criar_nfe_rascunho_para_pedido_evento(pedido: PedidoVenda) -> NotaFiscalSaida:
    """
    Cria uma NF-e RASCUNHO a partir de um PedidoVenda associado a um EventoVenda.

    Validações:
    - O pedido deve ter tipo_venda = EVENTO
    - O pedido deve estar associado a um EventoVenda
    """
    if pedido.tipo_venda != 'EVENTO':
        raise ValidationError(
            f"Pedido #{pedido.id} não é do tipo EVENTO. Tipo atual: {pedido.tipo_venda}"
        )

    try:
        from eventos.models import EventoVenda
        evento = EventoVenda.objects.get(pedido=pedido)
    except EventoVenda.DoesNotExist:
        raise ValidationError(
            f"Pedido #{pedido.id} não está associado a nenhum EventoVenda."
        )
    except EventoVenda.MultipleObjectsReturned:
        evento = EventoVenda.objects.filter(pedido=pedido).first()

    nota_existente = NotaFiscalSaida.objects.filter(
        pedido_venda=pedido,
        tipo_documento='NFE',
        is_active=True,
    ).first()

    if nota_existente:
        return nota_existente

    numero, serie = _reservar_nfe_com_fallback(pedido.loja, log_warning_sem_config=False)

    nota = NotaFiscalSaida.objects.create(
        loja=pedido.loja,
        cliente=pedido.cliente,
        pedido_venda=pedido,
        evento=evento,
        tipo_documento='NFE',
        numero=numero,
        serie=serie,
        chave_acesso='',
        valor_total=pedido.valor_total,
        xml_arquivo='',
        status='RASCUNHO',
        data_emissao=timezone.now(),
        created_by=pedido.created_by,
    )

    return nota


def criar_nfe_rascunho_para_pedido(pedido: PedidoVenda, usuario=None) -> NotaFiscalSaida:
    """
    Cria uma NF-e RASCUNHO a partir de um PedidoVenda qualquer.
    """
    nota_existente = NotaFiscalSaida.objects.filter(
        pedido_venda=pedido,
        tipo_documento='NFE',
        is_active=True,
    ).first()

    if nota_existente:
        logger.info(
            f"Nota fiscal já existe para pedido {pedido.id}: {nota_existente.numero}/{nota_existente.serie}"
        )
        return nota_existente

    if not pedido.itens.filter(is_active=True).exists():
        raise ValidationError(f"Pedido #{pedido.id} não possui itens ativos")

    numero, serie = _reservar_nfe_com_fallback(
        pedido.loja,
        log_warning_sem_config=True,
    )

    tipo_documento = 'NFE'
    if pedido.tipo_venda == 'BALCAO':
        tipo_documento = 'NFE'

    evento = None
    if pedido.tipo_venda == 'EVENTO':
        try:
            from eventos.models import EventoVenda
            evento = EventoVenda.objects.filter(pedido=pedido).first()
        except Exception:
            pass

    nota = NotaFiscalSaida.objects.create(
        loja=pedido.loja,
        cliente=pedido.cliente,
        pedido_venda=pedido,
        evento=evento,
        tipo_documento=tipo_documento,
        numero=numero,
        serie=serie,
        chave_acesso='',
        valor_total=pedido.valor_total,
        xml_arquivo='',
        status='RASCUNHO',
        data_emissao=timezone.now(),
        created_by=usuario or pedido.created_by,
    )

    logger.info(
        f"Nota fiscal criada: {nota.numero}/{nota.serie} para pedido {pedido.id} "
        f"(Tipo: {pedido.tipo_venda})"
    )

    return nota
