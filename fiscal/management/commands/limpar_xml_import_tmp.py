"""
Comando para limpar arquivos XML temporários de importação com mais de 24h.

Uso:
    python manage.py limpar_xml_import_tmp

Pode ser agendado via cron para execução diária.
"""
from django.core.management.base import BaseCommand
from fiscal.storage_nfe import limpar_xml_temporarios_antigos


class Command(BaseCommand):
    help = 'Remove arquivos XML temporários de importação com mais de 24 horas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--horas',
            type=int,
            default=24,
            help='Idade mínima em horas para remoção (default: 24)',
        )

    def handle(self, *args, **options):
        horas = options['horas']
        removidos = limpar_xml_temporarios_antigos(horas=horas)
        self.stdout.write(
            self.style.SUCCESS(f'Removidos {removidos} arquivo(s) temporário(s) com mais de {horas}h')
        )
