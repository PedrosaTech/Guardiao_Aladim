# Generated for NotaFiscalEntrada status and audit fields

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def set_existing_notes_confirmed(apps, schema_editor):
    """Notas existentes são tratadas como CONFIRMADA (já foram persistidas)."""
    NotaFiscalEntrada = apps.get_model('fiscal', 'NotaFiscalEntrada')
    NotaFiscalEntrada.objects.all().update(status='CONFIRMADA')


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('fiscal', '0005_alerta_nota_fiscal'),
    ]

    operations = [
        migrations.AddField(
            model_name='notafiscalentrada',
            name='status',
            field=models.CharField(
                choices=[
                    ('RASCUNHO', 'Rascunho'),
                    ('CONFIRMADA', 'Confirmada'),
                    ('ESTOQUE_PARCIAL', 'Estoque Parcial'),
                    ('ESTOQUE_TOTAL', 'Estoque Total'),
                ],
                default='RASCUNHO',
                max_length=20,
                verbose_name='Status',
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='notafiscalentrada',
            name='data_entrada_estoque',
            field=models.DateTimeField(
                blank=True,
                help_text='Quando foi dada entrada em estoque (última execução)',
                null=True,
                verbose_name='Data da Entrada em Estoque',
            ),
        ),
        migrations.AddField(
            model_name='notafiscalentrada',
            name='usuario_entrada_estoque',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='notas_entrada_estoque_processadas',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Usuário que deu entrada em estoque',
            ),
        ),
        migrations.RunPython(set_existing_notes_confirmed, migrations.RunPython.noop),
    ]
