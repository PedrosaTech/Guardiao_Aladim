"""
Marca como ABANDONADO pedidos no tablet que passaram do timeout configurado.
Rodar periodicamente (cron/celery beat).
"""
from datetime import timedelta
import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Marca pedidos do tablet como ABANDONADO após timeout configurado"

    def handle(self, *args, **options):
        from pdv_movel.models import ConfiguracaoPDVMovel
        from vendas.models import PedidoVenda

        total_marcados = 0
        configs = ConfiguracaoPDVMovel.objects.filter(
            is_active=True,
        ).select_related("loja")

        for config in configs:
            timeout_min = config.timeout_pedido_minutos or 30
            limite = timezone.now() - timedelta(minutes=timeout_min)

            pedidos = PedidoVenda.objects.filter(
                loja=config.loja,
                origem="TABLET",
                status="AGUARDANDO_PAGAMENTO",
                created_at__lt=limite,
                is_active=True,
            )

            count = pedidos.count()
            if count:
                pedidos.update(status="ABANDONADO")
                logger.info(
                    "Loja %s: %s pedido(s) marcados como ABANDONADO (timeout=%smin)",
                    config.loja.nome,
                    count,
                    timeout_min,
                )
                total_marcados += count

        self.stdout.write(
            self.style.SUCCESS(
                f"Concluído: {total_marcados} pedido(s) marcados como ABANDONADO."
            )
        )
