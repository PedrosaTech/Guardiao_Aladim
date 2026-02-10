"""
Carrega o fixture de dados iniciais apenas se o banco estiver vazio (primeira vez).
Usado no Release Command do Render para popular o PostgreSQL no primeiro deploy.
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Carrega data/fixtures/initial_data.json apenas se não existir nenhum usuário (idempotente).'

    def handle(self, *args, **options):
        if User.objects.exists():
            self.stdout.write(self.style.NOTICE('Banco já possui dados; load_initial_data ignorado.'))
            return

        self.stdout.write('Carregando dados iniciais...')
        try:
            call_command('loaddata', 'initial_data', verbosity=options.get('verbosity', 1))
            self.stdout.write(self.style.SUCCESS('Dados iniciais carregados.'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Erro ao carregar fixture: {e}'))
            raise
