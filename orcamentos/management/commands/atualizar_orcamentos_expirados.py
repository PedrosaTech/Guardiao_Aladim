"""
Comando para atualizar status de orçamentos expirados.

Uso: python manage.py atualizar_orcamentos_expirados

Pode ser executado via cron job diariamente.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from orcamentos.models import OrcamentoVenda


class Command(BaseCommand):
    help = 'Atualiza o status de orçamentos expirados para EXPIRADO'

    def handle(self, *args, **options):
        hoje = timezone.now().date()
        
        orcamentos_para_expirar = OrcamentoVenda.objects.filter(
            is_active=True,
            data_validade__lt=hoje,
            status__in=[
                OrcamentoVenda.StatusChoices.RASCUNHO,
                OrcamentoVenda.StatusChoices.ENVIADO,
                OrcamentoVenda.StatusChoices.APROVADO
            ]
        )
        
        count = orcamentos_para_expirar.update(status=OrcamentoVenda.StatusChoices.EXPIRADO)
        
        self.stdout.write(
            self.style.SUCCESS(f'{count} orçamento(s) atualizado(s) para EXPIRADO.')
        )

