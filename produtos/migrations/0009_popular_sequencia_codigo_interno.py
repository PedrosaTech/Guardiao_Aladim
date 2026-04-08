# Data migration: alinhar SequenciaCodigoInterno ao maior sufixo PROD-NNNN existente por empresa.

from django.db import migrations


def popular_sequencias(apps, schema_editor):
    Produto = apps.get_model('produtos', 'Produto')
    SequenciaCodigoInterno = apps.get_model('produtos', 'SequenciaCodigoInterno')
    Empresa = apps.get_model('core', 'Empresa')

    for empresa in Empresa.objects.all():
        produtos = Produto.objects.filter(
            empresa=empresa,
            codigo_interno__isnull=False,
        ).exclude(codigo_interno='')

        maior = 0
        for p in produtos.only('codigo_interno').iterator():
            try:
                if '-' in p.codigo_interno:
                    numero = int(p.codigo_interno.rsplit('-', 1)[1])
                    maior = max(maior, numero)
            except (ValueError, IndexError):
                pass

        SequenciaCodigoInterno.objects.update_or_create(
            empresa=empresa,
            defaults={'ultimo_numero': maior},
        )


def esvaziar_sequencias(apps, schema_editor):
    SequenciaCodigoInterno = apps.get_model('produtos', 'SequenciaCodigoInterno')
    SequenciaCodigoInterno.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('produtos', '0008_sequencia_codigo_interno'),
    ]

    operations = [
        migrations.RunPython(popular_sequencias, esvaziar_sequencias),
    ]
