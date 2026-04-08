# Catálogo global: ProdutoParametrosEmpresa, Categoria sem empresa, sequência global.

import re
from decimal import Decimal

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.db.models import Min


def _forwards_migrar_dados(apps, schema_editor):
    Produto = apps.get_model('produtos', 'Produto')
    ProdutoParametrosEmpresa = apps.get_model('produtos', 'ProdutoParametrosEmpresa')
    CategoriaProduto = apps.get_model('produtos', 'CategoriaProduto')
    SequenciaCodigoInterno = apps.get_model('produtos', 'SequenciaCodigoInterno')

    # 1) Overlay comercial/fiscal por empresa
    for produto in Produto.objects.iterator():
        ProdutoParametrosEmpresa.objects.get_or_create(
            empresa_id=produto.empresa_id,
            produto_id=produto.id,
            defaults={
                'preco_venda': produto.preco_venda_sugerido,
                'cfop_venda_dentro_uf': produto.cfop_venda_dentro_uf,
                'cfop_venda_fora_uf': produto.cfop_venda_fora_uf or None,
                'csosn_cst': produto.csosn_cst,
                'aliquota_icms': produto.aliquota_icms,
                'icms_st_cst': produto.icms_st_cst,
                'aliquota_icms_st': produto.aliquota_icms_st,
                'pis_cst': produto.pis_cst,
                'aliquota_pis': produto.aliquota_pis,
                'cofins_cst': produto.cofins_cst,
                'aliquota_cofins': produto.aliquota_cofins,
                'ipi_venda_cst': produto.ipi_venda_cst,
                'aliquota_ipi_venda': produto.aliquota_ipi_venda,
                'ipi_compra_cst': produto.ipi_compra_cst,
                'aliquota_ipi_compra': produto.aliquota_ipi_compra,
                'cclass_trib': produto.cclass_trib,
                'cst_ibs': produto.cst_ibs,
                'cst_cbs': produto.cst_cbs,
                'aliquota_ibs': produto.aliquota_ibs,
                'aliquota_cbs': produto.aliquota_cbs,
                'ativo_nessa_empresa': True,
                'is_active': True,
            },
        )

    # 2) Mesclar categorias com o mesmo nome (raiz) e realocar produtos
    for row in CategoriaProduto.objects.values('nome').annotate(mid=Min('id')):
        canonical_id = row['mid']
        nome = row['nome']
        dupes = list(
            CategoriaProduto.objects.filter(nome=nome).exclude(pk=canonical_id).values_list('id', flat=True)
        )
        for dup_id in dupes:
            Produto.objects.filter(categoria_id=dup_id).update(categoria_id=canonical_id)
            CategoriaProduto.objects.filter(pk=dup_id).delete()

    # 3) Resolver codigo_interno duplicado (unicidade global)
    from collections import defaultdict

    by_code = defaultdict(list)
    for pid, code in Produto.objects.values_list('id', 'codigo_interno'):
        if code:
            by_code[code].append(pid)

    def _next_num():
        seq = SequenciaCodigoInterno.objects.filter(empresa__isnull=True).first()
        if not seq:
            seq = SequenciaCodigoInterno.objects.create(empresa=None, ultimo_numero=0)
        seq.ultimo_numero += 1
        seq.save(update_fields=['ultimo_numero'])
        return seq.ultimo_numero

    for code, ids in by_code.items():
        if len(ids) <= 1:
            continue
        keep_id = min(ids)
        for pid in sorted(ids):
            if pid == keep_id:
                continue
            n = _next_num()
            Produto.objects.filter(pk=pid).update(codigo_interno=f'PROD-{n:04d}')

    # 4) Sequência global: maior sufixo PROD-NNNN entre todos os produtos
    max_n = 0
    for code in Produto.objects.exclude(codigo_interno__isnull=True).exclude(codigo_interno='').values_list(
        'codigo_interno', flat=True
    ):
        m = re.match(r'(?i)PROD-(\d+)', code)
        if m:
            max_n = max(max_n, int(m.group(1)))

    SequenciaCodigoInterno.objects.update_or_create(
        empresa=None,
        defaults={'ultimo_numero': max_n},
    )


def _backwards_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0001_initial'),
        ('produtos', '0009_popular_sequencia_codigo_interno'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProdutoParametrosEmpresa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Data de criação')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Data de atualização')),
                ('is_active', models.BooleanField(default=True, verbose_name='Ativo')),
                (
                    'ativo_nessa_empresa',
                    models.BooleanField(
                        default=True,
                        help_text='Se False, produto não aparece nas operações desta empresa',
                        verbose_name='Ativo nessa Empresa',
                    ),
                ),
                (
                    'preco_venda',
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(Decimal('0.01'))],
                        verbose_name='Preço de Venda',
                    ),
                ),
                (
                    'cfop_venda_dentro_uf',
                    models.CharField(help_text='Ex: 5102', max_length=4, verbose_name='CFOP Venda Dentro UF'),
                ),
                (
                    'cfop_venda_fora_uf',
                    models.CharField(
                        blank=True,
                        help_text='Ex: 6102',
                        max_length=4,
                        null=True,
                        verbose_name='CFOP Venda Fora UF',
                    ),
                ),
                ('csosn_cst', models.CharField(max_length=3, verbose_name='CSOSN / CST ICMS')),
                (
                    'aliquota_icms',
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal('18.00'),
                        max_digits=5,
                        verbose_name='Alíquota ICMS (%)',
                    ),
                ),
                (
                    'icms_st_cst',
                    models.CharField(blank=True, max_length=3, null=True, verbose_name='CST/CSOSN ICMS-ST'),
                ),
                (
                    'aliquota_icms_st',
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=Decimal('0.00'),
                        max_digits=5,
                        null=True,
                        verbose_name='Alíquota ICMS-ST (%)',
                    ),
                ),
                ('pis_cst', models.CharField(default='01', max_length=2, verbose_name='CST PIS')),
                (
                    'aliquota_pis',
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal('1.65'),
                        max_digits=5,
                        verbose_name='Alíquota PIS (%)',
                    ),
                ),
                ('cofins_cst', models.CharField(default='01', max_length=2, verbose_name='CST COFINS')),
                (
                    'aliquota_cofins',
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal('7.60'),
                        max_digits=5,
                        verbose_name='Alíquota COFINS (%)',
                    ),
                ),
                ('ipi_venda_cst', models.CharField(default='52', max_length=2, verbose_name='CST IPI Venda')),
                (
                    'aliquota_ipi_venda',
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal('0.00'),
                        max_digits=5,
                        verbose_name='Alíquota IPI Venda (%)',
                    ),
                ),
                ('ipi_compra_cst', models.CharField(default='02', max_length=2, verbose_name='CST IPI Compra')),
                (
                    'aliquota_ipi_compra',
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=Decimal('0.00'),
                        max_digits=5,
                        null=True,
                        verbose_name='Alíquota IPI Compra (%)',
                    ),
                ),
                (
                    'cclass_trib',
                    models.CharField(blank=True, max_length=10, null=True, verbose_name='Classificação Tributária'),
                ),
                ('cst_ibs', models.CharField(blank=True, max_length=3, null=True, verbose_name='CST-IBS')),
                ('cst_cbs', models.CharField(blank=True, max_length=3, null=True, verbose_name='CST-CBS')),
                (
                    'aliquota_ibs',
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal('0.10'),
                        max_digits=5,
                        verbose_name='Alíquota IBS (%)',
                    ),
                ),
                (
                    'aliquota_cbs',
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal('0.90'),
                        max_digits=5,
                        verbose_name='Alíquota CBS (%)',
                    ),
                ),
                (
                    'created_by',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='%(class)s_created',
                        to=settings.AUTH_USER_MODEL,
                        verbose_name='Criado por',
                    ),
                ),
                (
                    'empresa',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='parametros_produtos',
                        to='core.empresa',
                        verbose_name='Empresa',
                    ),
                ),
                (
                    'produto',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='parametros_por_empresa',
                        to='produtos.produto',
                        verbose_name='Produto',
                    ),
                ),
                (
                    'updated_by',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='%(class)s_updated',
                        to=settings.AUTH_USER_MODEL,
                        verbose_name='Atualizado por',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Parâmetros do Produto por Empresa',
                'verbose_name_plural': 'Parâmetros de Produtos por Empresa',
                'unique_together': {('empresa', 'produto')},
            },
        ),
        migrations.AddIndex(
            model_name='produtoparametrosempresa',
            index=models.Index(fields=['empresa', 'ativo_nessa_empresa'], name='produtos_pr_empresa_2a8b9c_idx'),
        ),
        migrations.AddIndex(
            model_name='produtoparametrosempresa',
            index=models.Index(fields=['produto', 'empresa'], name='produtos_pr_produto__3d4e5f_idx'),
        ),
        migrations.AlterField(
            model_name='sequenciacodigointerno',
            name='empresa',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='sequencia_codigo_interno',
                to='core.empresa',
            ),
        ),
        migrations.AddField(
            model_name='categoriaproduto',
            name='categoria_pai',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='subcategorias',
                to='produtos.categoriaproduto',
                verbose_name='Categoria Pai',
            ),
        ),
        migrations.RunPython(_forwards_migrar_dados, _backwards_noop),
        migrations.AlterUniqueTogether(
            name='produto',
            unique_together=set(),
        ),
        migrations.RemoveIndex(
            model_name='produto',
            name='produtos_pr_empresa_bb3338_idx',
        ),
        migrations.RemoveField(
            model_name='produto',
            name='empresa',
        ),
        migrations.RemoveField(
            model_name='produto',
            name='loja',
        ),
        migrations.RemoveField(
            model_name='produto',
            name='preco_venda_sugerido',
        ),
        migrations.RemoveField(
            model_name='produto',
            name='cfop_venda_dentro_uf',
        ),
        migrations.RemoveField(
            model_name='produto',
            name='cfop_venda_fora_uf',
        ),
        migrations.RemoveField(
            model_name='produto',
            name='csosn_cst',
        ),
        migrations.RemoveField(
            model_name='produto',
            name='aliquota_icms',
        ),
        migrations.RemoveField(
            model_name='produto',
            name='icms_st_cst',
        ),
        migrations.RemoveField(
            model_name='produto',
            name='aliquota_icms_st',
        ),
        migrations.RemoveField(
            model_name='produto',
            name='pis_cst',
        ),
        migrations.RemoveField(
            model_name='produto',
            name='aliquota_pis',
        ),
        migrations.RemoveField(
            model_name='produto',
            name='cofins_cst',
        ),
        migrations.RemoveField(
            model_name='produto',
            name='aliquota_cofins',
        ),
        migrations.RemoveField(
            model_name='produto',
            name='ipi_venda_cst',
        ),
        migrations.RemoveField(
            model_name='produto',
            name='aliquota_ipi_venda',
        ),
        migrations.RemoveField(
            model_name='produto',
            name='ipi_compra_cst',
        ),
        migrations.RemoveField(
            model_name='produto',
            name='aliquota_ipi_compra',
        ),
        migrations.RemoveField(
            model_name='produto',
            name='cclass_trib',
        ),
        migrations.RemoveField(
            model_name='produto',
            name='cst_ibs',
        ),
        migrations.RemoveField(
            model_name='produto',
            name='cst_cbs',
        ),
        migrations.RemoveField(
            model_name='produto',
            name='aliquota_ibs',
        ),
        migrations.RemoveField(
            model_name='produto',
            name='aliquota_cbs',
        ),
        migrations.AlterUniqueTogether(
            name='categoriaproduto',
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name='categoriaproduto',
            name='empresa',
        ),
        migrations.AddIndex(
            model_name='produto',
            index=models.Index(fields=['is_active'], name='produtos_pr_is_active_b7c8d9_idx'),
        ),
        migrations.AlterField(
            model_name='produto',
            name='codigo_interno',
            field=models.CharField(
                blank=True,
                editable=False,
                max_length=50,
                null=True,
                unique=True,
                verbose_name='Código Interno',
            ),
        ),
        migrations.AlterModelOptions(
            name='categoriaproduto',
            options={
                'ordering': ['nome'],
                'verbose_name': 'Categoria de Produto',
                'verbose_name_plural': 'Categorias de Produto',
            },
        ),
        migrations.AlterUniqueTogether(
            name='categoriaproduto',
            unique_together={('categoria_pai', 'nome')},
        ),
        migrations.AlterModelOptions(
            name='produto',
            options={
                'ordering': ['codigo_interno'],
                'verbose_name': 'Produto',
                'verbose_name_plural': 'Produtos',
            },
        ),
    ]
