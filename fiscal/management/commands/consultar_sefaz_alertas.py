"""
Comando para consultar SEFAZ-BA e criar alertas de notas fiscais emitidas no CNPJ.

Uso:
    python manage.py consultar_sefaz_alertas

Pode ser agendado via cron ou Celery para execução periódica.
"""
from django.core.management.base import BaseCommand
from fiscal.sefaz_ba import sincronizar_alertas_sefaz


class Command(BaseCommand):
    help = 'Consulta SEFAZ-BA e cria alertas para notas fiscais emitidas no CNPJ da empresa'

    def handle(self, *args, **options):
        self.stdout.write('Consultando SEFAZ-BA...')
        resultado = sincronizar_alertas_sefaz()

        self.stdout.write(
            self.style.SUCCESS(
                f'Processadas {resultado["lojas_processadas"]} loja(s). '
                f'Alertas criados: {resultado["alertas_criados"]}'
            )
        )
        if resultado['erros']:
            for e in resultado['erros']:
                self.stdout.write(self.style.ERROR(f'  Erro: {e}'))
