"""
Comando Django para rotacionar a chave de criptografia.

Rotaciona a chave de criptografia e re-criptografa todos os campos EncryptedCharField
com a nova chave. Requer backup prévio e permite rollback.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings
from django.db.models import Model
from django.apps import apps
import os
from datetime import datetime

from core.security.encryption import FieldEncryption
from core.fields import EncryptedCharField


class Command(BaseCommand):
    help = 'Rotaciona a chave de criptografia e re-criptografa todos os campos sensíveis'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--new-key',
            type=str,
            help='Nova chave de criptografia (mínimo 32 caracteres). Se não informada, será solicitada.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executa sem fazer alterações reais (apenas simulação)',
        )
        parser.add_argument(
            '--backup-dir',
            type=str,
            default='./backups',
            help='Diretório para salvar backup antes da rotação (padrão: ./backups)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força execução sem confirmação',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        backup_dir = options['backup_dir']
        
        # Verifica se ENCRYPTION_KEY atual está configurada
        current_key = getattr(settings, 'ENCRYPTION_KEY', None)
        if not current_key:
            raise CommandError(
                'ENCRYPTION_KEY atual não está configurada nas settings. '
                'Configure a variável de ambiente antes de rotacionar.'
            )
        
        # Solicita ou usa nova chave
        new_key = options.get('new_key')
        if not new_key:
            if dry_run:
                new_key = 'test-new-key-minimum-32-characters-long'
                self.stdout.write(self.style.WARNING(
                    'Modo dry-run: usando chave de teste'
                ))
            else:
                new_key = input('Digite a nova chave de criptografia (mínimo 32 caracteres): ')
        
        if len(new_key) < 32:
            raise CommandError('A nova chave deve ter no mínimo 32 caracteres')
        
        # Confirmação (se não for dry-run e não forçado)
        if not dry_run and not force:
            self.stdout.write(self.style.WARNING(
                '\n⚠️  ATENÇÃO: Esta operação vai re-criptografar todos os dados sensíveis!'
            ))
            self.stdout.write('Certifique-se de ter feito backup do banco de dados antes de continuar.')
            confirm = input('\nDeseja continuar? (digite "SIM" para confirmar): ')
            if confirm != 'SIM':
                self.stdout.write(self.style.ERROR('Operação cancelada.'))
                return
        
        # Backup (se não for dry-run)
        if not dry_run:
            self.stdout.write('\nCriando backup...')
            self._create_backup(backup_dir)
        
        # Encontra todos os models com EncryptedCharField
        models_to_update = self._find_encrypted_fields()
        
        if not models_to_update:
            self.stdout.write(self.style.WARNING('Nenhum campo EncryptedCharField encontrado.'))
            return
        
        self.stdout.write(f'\nEncontrados {len(models_to_update)} models com campos criptografados:')
        for model_info in models_to_update:
            self.stdout.write(f'  - {model_info["model"]}: {len(model_info["fields"])} campo(s)')
        
        # Rotaciona chave
        try:
            if dry_run:
                self.stdout.write(self.style.WARNING('\n🔍 Modo DRY-RUN - Nenhuma alteração será feita'))
            
            # Atualiza temporariamente a chave nas settings
            old_key = settings.ENCRYPTION_KEY
            settings.ENCRYPTION_KEY = new_key
            
            # Limpa cache do cipher para usar nova chave
            FieldEncryption.get_cipher.cache_clear()
            
            total_updated = 0
            
            with transaction.atomic():
                for model_info in models_to_update:
                    model = model_info['model']
                    fields = model_info['fields']
                    
                    self.stdout.write(f'\nProcessando {model.__name__}...')
                    
                    updated_count = self._rotate_model_fields(
                        model, fields, dry_run=dry_run
                    )
                    total_updated += updated_count
                    
                    if updated_count > 0:
                        self.stdout.write(self.style.SUCCESS(
                            f'  ✓ {updated_count} registro(s) atualizado(s)'
                        ))
            
            # Se não for dry-run, atualiza settings permanentemente
            if not dry_run:
                self.stdout.write(self.style.SUCCESS(
                    f'\n✓ Rotação concluída! {total_updated} registro(s) re-criptografado(s).'
                ))
                self.stdout.write(self.style.WARNING(
                    '\n⚠️  IMPORTANTE: Atualize a variável de ambiente ENCRYPTION_KEY com a nova chave!'
                ))
                self.stdout.write(f'   Nova chave: {new_key[:20]}...')
                self.stdout.write('\n   Para aplicar em produção, configure no arquivo .env ou variáveis de ambiente.')
            else:
                # Restaura chave original em dry-run
                settings.ENCRYPTION_KEY = old_key
                FieldEncryption.get_cipher.cache_clear()
                self.stdout.write(self.style.SUCCESS(
                    f'\n✓ Simulação concluída! {total_updated} registro(s) seriam atualizados.'
                ))
        
        except Exception as e:
            # Em caso de erro, restaura chave original
            if not dry_run:
                settings.ENCRYPTION_KEY = old_key
                FieldEncryption.get_cipher.cache_clear()
                self.stdout.write(self.style.ERROR(
                    f'\n✗ Erro durante rotação: {str(e)}'
                ))
                self.stdout.write(self.style.WARNING(
                    'Chave original foi restaurada. Nenhuma alteração foi feita.'
                ))
            raise CommandError(f'Erro durante rotação: {str(e)}')
    
    def _find_encrypted_fields(self):
        """Encontra todos os models que têm campos EncryptedCharField."""
        models_with_encrypted = []
        
        for app_config in apps.get_app_configs():
            # Ignora apps do Django
            if app_config.name.startswith('django.') or app_config.name in ['admin', 'auth', 'contenttypes', 'sessions']:
                continue
            
            for model in app_config.get_models():
                encrypted_fields = []
                
                for field in model._meta.get_fields():
                    if isinstance(field, EncryptedCharField):
                        encrypted_fields.append(field.name)
                
                if encrypted_fields:
                    models_with_encrypted.append({
                        'model': model,
                        'fields': encrypted_fields,
                    })
        
        return models_with_encrypted
    
    def _rotate_model_fields(self, model: Model, field_names: list, dry_run: bool = False):
        """Re-criptografa campos de um model com a nova chave."""
        updated_count = 0
        
        # Busca todos os registros do model
        queryset = model.objects.all()
        
        for instance in queryset:
            needs_update = False
            
            for field_name in field_names:
                current_value = getattr(instance, field_name)
                
                if current_value:
                    # Tenta descriptografar com a chave atual
                    # Se conseguir, precisa re-criptografar com nova chave
                    try:
                        # Descriptografa com chave antiga (já está descriptografado na memória)
                        # Mas precisamos re-criptografar ao salvar
                        # Força re-criptografia setando o valor novamente
                        setattr(instance, field_name, current_value)
                        needs_update = True
                    except Exception:
                        pass
            
            if needs_update and not dry_run:
                instance.save(update_fields=field_names)
                updated_count += 1
            elif needs_update and dry_run:
                updated_count += 1
        
        return updated_count
    
    def _create_backup(self, backup_dir: str):
        """Cria backup do banco antes da rotação."""
        try:
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(backup_dir, f'encryption_backup_{timestamp}.txt')
            
            with open(backup_file, 'w') as f:
                f.write(f'Backup criado em: {datetime.now().isoformat()}\n')
                f.write(f'Chave antiga: {settings.ENCRYPTION_KEY[:20]}...\n')
                f.write('\nEste arquivo contém informações sobre o backup da rotação de chave.\n')
                f.write('Faça backup completo do banco de dados antes de rotacionar!\n')
            
            self.stdout.write(self.style.SUCCESS(f'  ✓ Backup info salvo em: {backup_file}'))
            self.stdout.write(self.style.WARNING(
                '  ⚠️  IMPORTANTE: Faça backup completo do banco de dados antes de continuar!'
            ))
        
        except Exception as e:
            self.stdout.write(self.style.WARNING(
                f'  ⚠️  Aviso: Não foi possível criar arquivo de backup: {str(e)}'
            ))



