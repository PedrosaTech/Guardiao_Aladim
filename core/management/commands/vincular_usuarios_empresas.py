"""
Vincula todos os usuários staff a todas as empresas ativas.
Usar para corrigir ambientes onde UsuarioEmpresa não foi criado.

Uso: python manage.py vincular_usuarios_empresas
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Vincula usuarios staff a todas as empresas ativas'

    def handle(self, *args, **options):
        from django.contrib.auth import get_user_model

        from core.models import UsuarioEmpresa, Empresa

        User = get_user_model()
        empresas = Empresa.objects.filter(is_active=True)
        users = User.objects.filter(is_staff=True)
        total = 0

        for user in users:
            for empresa in empresas:
                _, created = UsuarioEmpresa.objects.get_or_create(
                    user=user,
                    empresa=empresa,
                    defaults={
                        'perfil': 'ADMIN',
                        'empresa_padrao': True,
                        'created_by': user,
                        'updated_by': user,
                    },
                )
                if created:
                    total += 1
                    self.stdout.write(
                        f'Vinculado: {user.username} → {empresa.nome_fantasia}'
                    )

        self.stdout.write(
            self.style.SUCCESS(f'Concluído: {total} vínculos criados.')
        )
