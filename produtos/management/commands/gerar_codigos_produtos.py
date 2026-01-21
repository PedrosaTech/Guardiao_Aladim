"""
Comando para gerar códigos internos para produtos que não possuem código.
"""
from django.core.management.base import BaseCommand
from produtos.models import Produto
from django.db.models import Q


class Command(BaseCommand):
    help = 'Gera códigos internos automaticamente para produtos que não possuem código'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--empresa',
            type=int,
            help='ID da empresa (opcional, se não informado, processa todas)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas simula, não salva alterações',
        )
    
    def handle(self, *args, **options):
        empresa_id = options.get('empresa')
        dry_run = options.get('dry_run', False)
        
        # Busca produtos sem código
        produtos_sem_codigo = Produto.objects.filter(
            Q(codigo_interno__isnull=True) | Q(codigo_interno='')
        )
        
        if empresa_id:
            produtos_sem_codigo = produtos_sem_codigo.filter(empresa_id=empresa_id)
        
        total = produtos_sem_codigo.count()
        
        if total == 0:
            self.stdout.write(self.style.SUCCESS('Nenhum produto sem código encontrado.'))
            return
        
        self.stdout.write(f'Encontrados {total} produto(s) sem código.')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Modo DRY-RUN: nenhuma alteração será salva.'))
        
        # Agrupa por empresa para gerar sequenciais corretos
        empresas = produtos_sem_codigo.values_list('empresa', flat=True).distinct()
        
        for empresa_id_loop in empresas:
            produtos_empresa = produtos_sem_codigo.filter(empresa_id=empresa_id_loop).order_by('id')
            
            # Busca o último código da empresa
            ultimo_produto = Produto.objects.filter(
                empresa_id=empresa_id_loop,
                codigo_interno__isnull=False
            ).exclude(
                codigo_interno=''
            ).order_by('-id').first()
            
            if ultimo_produto and ultimo_produto.codigo_interno:
                # Extrai o número do último código
                try:
                    if '-' in ultimo_produto.codigo_interno:
                        prefixo, numero = ultimo_produto.codigo_interno.rsplit('-', 1)
                        proximo_numero = int(numero) + 1
                    else:
                        import re
                        numeros = re.findall(r'\d+', ultimo_produto.codigo_interno)
                        if numeros:
                            proximo_numero = int(numeros[-1]) + 1
                        else:
                            proximo_numero = 1
                except (ValueError, AttributeError):
                    proximo_numero = 1
            else:
                proximo_numero = 1
            
            # Gera códigos para produtos sem código
            for produto in produtos_empresa:
                codigo = f"PROD-{proximo_numero:04d}"
                
                if dry_run:
                    self.stdout.write(
                        f'  [{produto.empresa.nome_fantasia}] {produto.descricao} -> {codigo} (simulação)'
                    )
                else:
                    produto.codigo_interno = codigo
                    produto.save(update_fields=['codigo_interno'])
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  [{produto.empresa.nome_fantasia}] {produto.descricao} -> {codigo}'
                        )
                    )
                
                proximo_numero += 1
        
        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f'\n✅ {total} produto(s) atualizado(s) com sucesso!'))
        else:
            self.stdout.write(self.style.WARNING(f'\n⚠️ Modo DRY-RUN: execute sem --dry-run para aplicar as alterações.'))

