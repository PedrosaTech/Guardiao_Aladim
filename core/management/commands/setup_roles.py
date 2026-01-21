"""
Comando para criar grupos de permissões padrão (RBAC).
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Cria grupos de permissões padrão para o sistema'
    
    GRUPOS = {
        'ADMINISTRADOR': {
            'description': 'Acesso total ao sistema',
            'permissions': 'all',  # Todas as permissões
        },
        'GERENTE': {
            'description': 'Gerente com acesso amplo, exceto configurações críticas',
            'permissions': ['view', 'change'],  # Pode ver e alterar, mas não criar/excluir em alguns casos
        },
        'CAIXA': {
            'description': 'Operador de caixa - PDV e vendas',
            'permissions': ['view', 'add', 'change'],  # Pode criar e alterar vendas
        },
        'ESTOQUISTA': {
            'description': 'Responsável pelo estoque',
            'permissions': ['view', 'add', 'change'],  # Pode gerenciar estoque
        },
        'VENDEDOR_EXTERNO': {
            'description': 'Vendedor externo - vendas e CRM',
            'permissions': ['view', 'add'],  # Pode criar vendas e leads
        },
        'FINANCEIRO': {
            'description': 'Acesso ao módulo financeiro',
            'permissions': ['view', 'add', 'change'],  # Pode gerenciar títulos e movimentos
        },
        'FISCAL': {
            'description': 'Acesso ao módulo fiscal',
            'permissions': ['view', 'add', 'change'],  # Pode gerenciar notas fiscais
        },
    }
    
    def handle(self, *args, **options):
        self.stdout.write('Criando grupos de permissões...')
        
        # Obtém todas as permissões
        all_permissions = Permission.objects.all()
        
        for nome_grupo, config in self.GRUPOS.items():
            grupo, created = Group.objects.get_or_create(name=nome_grupo)
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Grupo "{nome_grupo}" criado'))
            else:
                self.stdout.write(self.style.WARNING(f'Grupo "{nome_grupo}" já existe'))
            
            # Limpa permissões existentes
            grupo.permissions.clear()
            
            # Adiciona permissões
            if config['permissions'] == 'all':
                grupo.permissions.set(all_permissions)
                self.stdout.write(f'  - Todas as permissões adicionadas')
            else:
                # TODO: Refinar permissões por modelo específico
                # Por enquanto, adiciona permissões genéricas baseadas nos apps
                apps_permitidos = [
                    'core', 'pessoas', 'produtos', 'fiscal', 'estoque',
                    'compras', 'vendas', 'pdv', 'financeiro', 'crm', 'mensagens'
                ]
                
                perms_adicionadas = 0
                for perm in all_permissions:
                    app_label = perm.content_type.app_label
                    codename = perm.codename
                    
                    # Verifica se é de um app permitido
                    if app_label in apps_permitidos:
                        # Verifica se o tipo de permissão está na lista
                        if any(codename.startswith(prefix) for prefix in config['permissions']):
                            grupo.permissions.add(perm)
                            perms_adicionadas += 1
                
                self.stdout.write(f'  - {perms_adicionadas} permissões adicionadas')
            
            # Atualiza descrição se houver
            if 'description' in config:
                # Django não tem campo description nativo em Group, mas podemos usar um comentário
                pass
        
        self.stdout.write(self.style.SUCCESS('\nGrupos criados com sucesso!'))
        self.stdout.write('\nTODO: Refinar permissões por modelo específico conforme necessidade de negócio.')

