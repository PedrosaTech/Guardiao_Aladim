# Generated migration to encrypt existing data

from django.db import migrations
from django.apps import apps
from django.conf import settings

from core.security.encryption import FieldEncryption
from core.fields import EncryptedCharField


def encrypt_existing_data_forward(apps, schema_editor):
    """
    Criptografa dados existentes em campos EncryptedCharField.
    
    Esta função percorre todos os models que têm campos EncryptedCharField
    e criptografa valores que ainda não estão criptografados.
    
    Compatibilidade:
    - Dados já criptografados são ignorados (não tentamos re-criptografar)
    - Dados None/vazios são mantidos como estão
    - Se um valor não puder ser descriptografado, assumimos que não está criptografado
    """
    # Verifica se ENCRYPTION_KEY está configurada
    if not getattr(settings, 'ENCRYPTION_KEY', None):
        print("⚠️  AVISO: ENCRYPTION_KEY não está configurada. Pulando criptografia de dados existentes.")
        print("   Configure ENCRYPTION_KEY nas settings antes de executar esta migration.")
        return
    
    # Limpa cache do cipher para garantir uso da chave correta
    FieldEncryption.get_cipher.cache_clear()
    
    # Lista de apps e models que têm EncryptedCharField
    # Baseado na estrutura atual do projeto
    models_to_process = [
        ('core', 'Empresa'),
        ('core', 'Loja'),
        ('pessoas', 'Cliente'),
        ('pessoas', 'Fornecedor'),
        ('fiscal', 'ConfiguracaoFiscalLoja'),
        ('eventos', 'EventoVenda'),
        ('orcamentos', 'OrcamentoVenda'),
        ('crm', 'Lead'),
    ]
    
    total_encrypted = 0
    
    for app_name, model_name in models_to_process:
        try:
            model = apps.get_model(app_name, model_name)
        except LookupError:
            # Model não existe (pode estar em desenvolvimento)
            continue
        
        # Encontra campos EncryptedCharField no model
        encrypted_fields = []
        for field in model._meta.get_fields():
            # Verifica pelo tipo do campo (EncryptedCharField)
            field_type = type(field).__name__
            if field_type == 'EncryptedCharField' or 'EncryptedCharField' in str(type(field)):
                encrypted_fields.append(field.name)
        
        if not encrypted_fields:
            continue
        
        # Processa todos os registros do model
        queryset = model.objects.all()
        model_updated_count = 0
        
        for instance in queryset:
            instance_updated = False
            update_fields = []
            
            for field_name in encrypted_fields:
                current_value = getattr(instance, field_name)
                
                if current_value:
                    # Verifica se já está criptografado
                    # Se o valor descriptografado for igual ao original, não está criptografado
                    test_decrypt = FieldEncryption.decrypt(current_value)
                    
                    if test_decrypt == current_value:
                        # Não estava criptografado, precisa criptografar
                        # Força re-criptografia setando o valor novamente
                        # (o get_prep_value vai criptografar)
                        setattr(instance, field_name, current_value)
                        update_fields.append(field_name)
                        instance_updated = True
            
            if instance_updated:
                instance.save(update_fields=update_fields)
                model_updated_count += 1
        
        if model_updated_count > 0:
            print(f"✓ {model_name}: {model_updated_count} registro(s) criptografado(s)")
            total_encrypted += model_updated_count
    
    if total_encrypted > 0:
        print(f"\n✓ Total: {total_encrypted} registro(s) criptografado(s) com sucesso!")
    else:
        print("\n✓ Nenhum dado precisou ser criptografado (todos já estavam criptografados ou vazios).")


def encrypt_existing_data_reverse(apps, schema_editor):
    """
    Função reverse para descriptografar dados (se necessário).
    
    NOTA: Esta função não descriptografa dados automaticamente por questões de segurança.
    Se precisar reverter, use o comando rotate_encryption_key ou descriptografe manualmente.
    """
    print("⚠️  AVISO: Reversão não descriptografa dados automaticamente.")
    print("   Se precisar reverter, use o comando 'python manage.py rotate_encryption_key'.")
    print("   Ou implemente descriptografia manual se necessário.")


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
        ('pessoas', '0001_initial'),
        ('fiscal', '0001_initial'),
        ('eventos', '0001_initial'),
        ('orcamentos', '0001_initial'),
        ('crm', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            encrypt_existing_data_forward,
            reverse_code=encrypt_existing_data_reverse,
            atomic=True,
        ),
    ]

