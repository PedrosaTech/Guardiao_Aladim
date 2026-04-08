# Generated manually for NF-e (cMun)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_usuario_empresa'),
    ]

    operations = [
        migrations.AddField(
            model_name='empresa',
            name='codigo_ibge_municipio',
            field=models.CharField(
                blank=True,
                help_text='7 dígitos. Ex: 2927408 (Salvador-BA). Obrigatório para emissão de NF-e.',
                max_length=7,
                null=True,
                verbose_name='Código IBGE do Município',
            ),
        ),
        migrations.AddField(
            model_name='loja',
            name='codigo_ibge_municipio',
            field=models.CharField(
                blank=True,
                help_text='7 dígitos. Ex: 2927408 (Salvador-BA). Obrigatório para emissão de NF-e.',
                max_length=7,
                null=True,
                verbose_name='Código IBGE do Município',
            ),
        ),
    ]
