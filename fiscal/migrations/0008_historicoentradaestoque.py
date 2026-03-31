# Generated for HistoricoEntradaEstoque

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('fiscal', '0007_itemnotafiscalentrada'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricoEntradaEstoque',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_processamento', models.DateTimeField(auto_now_add=True, verbose_name='Data do Processamento')),
                ('itens_processados', models.PositiveIntegerField(default=0, verbose_name='Itens Processados')),
                ('motivo_parcial', models.CharField(
                    blank=True,
                    choices=[
                        ('PARCIAL_SEM_VINCULO', 'Parcial - itens sem vínculo'),
                        ('PARCIAL_COM_ERRO', 'Parcial - erro técnico em algum item'),
                    ],
                    max_length=25,
                    null=True,
                    verbose_name='Motivo Parcial',
                )),
                ('erros', models.JSONField(
                    blank=True,
                    default=list,
                    help_text='Lista de mensagens de erro por item',
                    verbose_name='Erros',
                )),
                ('nota_fiscal', models.ForeignKey(
                    db_index=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='historico_entrada_estoque',
                    to='fiscal.notafiscalentrada',
                    verbose_name='Nota Fiscal',
                )),
                ('usuario', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='historicos_entrada_estoque',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Usuário',
                )),
            ],
            options={
                'verbose_name': 'Histórico de Entrada em Estoque',
                'verbose_name_plural': 'Históricos de Entrada em Estoque',
                'ordering': ['-data_processamento'],
                'indexes': [
                    models.Index(fields=['nota_fiscal', '-data_processamento'], name='fiscal_hist_nota_fi_idx'),
                ],
            },
        ),
    ]
