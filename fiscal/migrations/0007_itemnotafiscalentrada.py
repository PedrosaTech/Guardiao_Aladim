# Generated for ItemNotaFiscalEntrada

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('produtos', '0001_initial'),
        ('estoque', '0001_initial'),
        ('fiscal', '0006_notafiscalentrada_status_entrada_estoque'),
    ]

    operations = [
        migrations.CreateModel(
            name='ItemNotaFiscalEntrada',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Data de criação')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Data de atualização')),
                ('is_active', models.BooleanField(default=True, verbose_name='Ativo')),
                ('numero_item', models.IntegerField(verbose_name='Número do Item')),
                ('codigo_produto_fornecedor', models.CharField(blank=True, max_length=60, verbose_name='Código Produto Fornecedor')),
                ('codigo_barras', models.CharField(blank=True, max_length=50, verbose_name='Código de Barras (EAN)')),
                ('ncm', models.CharField(blank=True, max_length=10, verbose_name='NCM')),
                ('descricao', models.CharField(max_length=255, verbose_name='Descrição')),
                ('quantidade', models.DecimalField(
                    decimal_places=3,
                    max_digits=10,
                    validators=[django.core.validators.MinValueValidator(Decimal('0.001'))],
                    verbose_name='Quantidade',
                )),
                ('unidade_comercial', models.CharField(default='UN', max_length=10, verbose_name='Unidade Comercial')),
                ('preco_unitario', models.DecimalField(
                    decimal_places=4,
                    max_digits=12,
                    validators=[django.core.validators.MinValueValidator(Decimal('0.0001'))],
                    verbose_name='Preço Unitário',
                )),
                ('valor_total', models.DecimalField(
                    decimal_places=2,
                    max_digits=12,
                    validators=[django.core.validators.MinValueValidator(Decimal('0.01'))],
                    verbose_name='Valor Total',
                )),
                ('status', models.CharField(
                    choices=[
                        ('NAO_VINCULADO', 'Não vinculado'),
                        ('AGUARDANDO_CONFIRMACAO', 'Aguardando confirmação'),
                        ('VINCULADO', 'Vinculado'),
                        ('ESTOQUE_ENTRADO', 'Estoque entrado'),
                    ],
                    default='NAO_VINCULADO',
                    max_length=25,
                    verbose_name='Status',
                )),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Criado por')),
                ('local_estoque', models.ForeignKey(blank=True, help_text='Se preenchido, sobrescreve o local padrão da nota', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='itens_nota_entrada', to='estoque.localestoque', verbose_name='Local de Estoque (override)')),
                ('nota_fiscal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='itens', to='fiscal.notafiscalentrada', verbose_name='Nota Fiscal')),
                ('produto', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='itens_nota_entrada', to='produtos.produto', verbose_name='Produto')),
                ('produto_sugerido', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='itens_nota_entrada_sugestao', to='produtos.produto', verbose_name='Produto Sugerido (fuzzy match)')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Atualizado por')),
            ],
            options={
                'verbose_name': 'Item da Nota Fiscal de Entrada',
                'verbose_name_plural': 'Itens da Nota Fiscal de Entrada',
                'ordering': ['nota_fiscal', 'numero_item'],
                'unique_together': {('nota_fiscal', 'numero_item')},
            },
        ),
    ]
