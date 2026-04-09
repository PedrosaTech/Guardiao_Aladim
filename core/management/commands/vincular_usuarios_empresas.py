"""
Vincula todos os usuários staff a todas as empresas ativas.
Usar para corrigir ambientes onde UsuarioEmpresa não foi criado.

Uso:
  python manage.py vincular_usuarios_empresas
  python manage.py vincular_usuarios_empresas --corrigir-duplicatas
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Vincula usuarios staff a todas as empresas ativas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--corrigir-duplicatas',
            action='store_true',
            help='Garante apenas um empresa_padrao=True por usuario (mantem o mais antigo)',
        )

    def handle(self, *args, **options):
        from django.contrib.auth import get_user_model

        from core.models import UsuarioEmpresa, Empresa

        User = get_user_model()

        if options['corrigir_duplicatas']:
            for user in User.objects.all():
                padrao = (
                    UsuarioEmpresa.objects.filter(
                        user=user,
                        empresa_padrao=True,
                        is_active=True,
                    )
                    .select_related('empresa')
                    .order_by('created_at')
                )
                if padrao.count() > 1:
                    primeiro = padrao.first()
                    padrao.exclude(pk=primeiro.pk).update(empresa_padrao=False)
                    self.stdout.write(
                        f'Corrigido: {user.username} — mantido '
                        f'{primeiro.empresa.nome_fantasia} como padrao'
                    )
        empresas = Empresa.objects.filter(is_active=True)
        users = User.objects.filter(is_staff=True)
        total = 0

        for user in users:
            ja_tem_padrao = UsuarioEmpresa.objects.filter(
                user=user,
                empresa_padrao=True,
                is_active=True,
            ).exists()
            for empresa in empresas:
                use_padrao = not ja_tem_padrao
                _, created = UsuarioEmpresa.objects.get_or_create(
                    user=user,
                    empresa=empresa,
                    defaults={
                        'perfil': 'ADMIN',
                        'empresa_padrao': use_padrao,
                        'created_by': user,
                        'updated_by': user,
                    },
                )
                if created:
                    if use_padrao:
                        ja_tem_padrao = True
                    total += 1
                    self.stdout.write(
                        f'Vinculado: {user.username} → {empresa.nome_fantasia}'
                    )

        self.stdout.write(
            self.style.SUCCESS(f'Concluído: {total} vínculos criados.')
        )
