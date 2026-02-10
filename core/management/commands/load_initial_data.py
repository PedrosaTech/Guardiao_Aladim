from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Carrega o fixture de dados iniciais apenas se o banco estiver vazio'

    def handle(self, *args, **options):
        # Verifica se já existem usuários no banco
        if User.objects.exists():
            self.stdout.write(
                self.style.WARNING('Banco já possui dados. Pulando carga do fixture.')
            )
            return

        self.stdout.write('Carregando dados iniciais...')
        try:
            call_command('loaddata', 'initial_data')
            self.stdout.write(
                self.style.SUCCESS('✓ Dados iniciais carregados com sucesso!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro ao carregar fixture: {e}')
            )
            raise
