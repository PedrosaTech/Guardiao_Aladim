"""
Comando para gerar códigos internos para produtos que não possuem código (sequência global).
"""
from django.core.management.base import BaseCommand
from django.db.models import Q

from produtos.models import Produto


class Command(BaseCommand):
    help = 'Gera códigos internos automaticamente para produtos que não possuem código'

    def add_arguments(self, parser):
        parser.add_argument(
            '--empresa',
            type=int,
            help='(Ignorado) Mantido por compatibilidade; a sequência é global.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas simula, não salva alterações',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        if options.get('empresa'):
            self.stdout.write(
                self.style.WARNING(
                    'Aviso: --empresa é ignorado; códigos internos são únicos no catálogo global.'
                )
            )

        produtos_sem_codigo = Produto.objects.filter(
            Q(codigo_interno__isnull=True) | Q(codigo_interno='')
        ).order_by('id')

        total = produtos_sem_codigo.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS('Nenhum produto sem código encontrado.'))
            return

        self.stdout.write(f'Encontrados {total} produto(s) sem código.')

        if dry_run:
            self.stdout.write(self.style.WARNING('Modo DRY-RUN: nenhuma alteração será salva.'))

        for produto in produtos_sem_codigo:
            if dry_run:
                self.stdout.write(f'  {produto.descricao} -> (será gerado ao salvar)')
            else:
                produto.save()
                self.stdout.write(
                    self.style.SUCCESS(f'  {produto.descricao} -> {produto.codigo_interno}')
                )

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f'\n✅ {total} produto(s) atualizado(s) com sucesso!'))
        else:
            self.stdout.write(self.style.WARNING('\n⚠️ Modo DRY-RUN: execute sem --dry-run para aplicar.'))
