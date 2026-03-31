# Generated manually for AlertaNotaFiscal

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
        ('fiscal', '0004_increase_document_fields_max_length'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AlertaNotaFiscal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Data de criação')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Data de atualização')),
                ('is_active', models.BooleanField(default=True, verbose_name='Ativo')),
                ('tipo', models.CharField(choices=[('ENTRADA', 'Nota de Entrada (destinatário)'), ('SAIDA', 'Nota de Saída (emitente)')], default='ENTRADA', max_length=10, verbose_name='Tipo')),
                ('status', models.CharField(choices=[('PENDENTE', 'Pendente'), ('IMPORTADA', 'Importada no sistema'), ('IGNORADA', 'Ignorada')], default='PENDENTE', max_length=20, verbose_name='Status')),
                ('chave_acesso', models.CharField(db_index=True, max_length=44, verbose_name='Chave de Acesso')),
                ('numero', models.IntegerField(verbose_name='Número')),
                ('serie', models.CharField(max_length=3, verbose_name='Série')),
                ('valor_total', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Valor Total')),
                ('data_emissao', models.DateField(blank=True, null=True, verbose_name='Data de Emissão')),
                ('cnpj_emitente', models.CharField(blank=True, max_length=20, verbose_name='CNPJ Emitente')),
                ('razao_social_emitente', models.CharField(blank=True, max_length=255, verbose_name='Razão Social Emitente')),
                ('data_consulta_sefaz', models.DateTimeField(auto_now_add=True, verbose_name='Data da Consulta SEFAZ')),
                ('mensagem', models.TextField(blank=True, verbose_name='Mensagem')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Criado por')),
                ('loja', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alertas_nota_fiscal', to='core.loja', verbose_name='Loja')),
                ('nota_fiscal_entrada', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='alertas', to='fiscal.notafiscalentrada', verbose_name='Nota Fiscal Importada')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Atualizado por')),
            ],
            options={
                'verbose_name': 'Alerta de Nota Fiscal',
                'verbose_name_plural': 'Alertas de Notas Fiscais',
                'ordering': ['-data_consulta_sefaz'],
                'unique_together': {('loja', 'chave_acesso')},
                'indexes': [
                    models.Index(fields=['loja', 'status'], name='fiscal_alert_loja_id_7a8f3a_idx'),
                    models.Index(fields=['chave_acesso'], name='fiscal_alert_chave_a_9b2c4d_idx'),
                ],
            },
        ),
    ]
