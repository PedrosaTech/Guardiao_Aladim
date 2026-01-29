"""
Funções auxiliares para PDV Móvel.
"""
from django.utils import timezone
from datetime import timedelta

from vendas.models import PedidoVenda


def marcar_pedidos_abandonados():
    """
    Marca pedidos não pagos como ABANDONADOS após timeout.

    Deve ser executado periodicamente (ex.: Celery task, cron).
    """
    from .models import ConfiguracaoPDVMovel

    configs = ConfiguracaoPDVMovel.objects.filter(ativo=True)
    total_abandonados = 0

    for config in configs:
        timeout = config.timeout_pedido_minutos
        limite = timezone.now() - timedelta(minutes=timeout)
        qs = PedidoVenda.objects.filter(
            origem="TABLET",
            loja=config.loja,
            status="AGUARDANDO_PAGAMENTO",
            created_at__lt=limite,
            is_active=True,
        )
        n = qs.update(status="ABANDONADO")
        total_abandonados += n

    return total_abandonados
