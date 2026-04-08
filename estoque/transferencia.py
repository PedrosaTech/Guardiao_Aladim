"""
Serviço de transferência de estoque entre empresas (CNPJs distintos).
"""
from decimal import Decimal
import logging

from django.core.exceptions import ValidationError
from django.db import transaction

logger = logging.getLogger(__name__)


@transaction.atomic
def executar_transferencia_interempresa(
    produto,
    local_origem,
    local_destino,
    quantidade: Decimal,
    custo_unitario: Decimal,
    usuario=None,
    observacao=None,
):
    """
    Executa transferência de estoque entre duas empresas distintas.

    Cria:
    - MovimentoEstoque SAIDA na empresa origem
    - MovimentoEstoque ENTRADA na empresa destino
    - TransferenciaInterempresa com status CONCLUIDA

    Raises:
        ValidationError: empresas iguais, produto inativo em alguma empresa
        ValueError: estoque insuficiente (propagado de realizar_movimento_estoque)
    """
    from produtos.models import ProdutoParametrosEmpresa

    from .models import TransferenciaInterempresa
    from .services import realizar_movimento_estoque

    empresa_origem = local_origem.loja.empresa
    empresa_destino = local_destino.loja.empresa

    if empresa_origem == empresa_destino:
        raise ValidationError(
            'Use transferência normal (tipo TRANSFERENCIA) para locais da mesma empresa.'
        )

    if custo_unitario is None or custo_unitario <= 0:
        raise ValidationError('custo_unitario é obrigatório e deve ser maior que zero.')

    for empresa in (empresa_origem, empresa_destino):
        if not ProdutoParametrosEmpresa.objects.filter(
            empresa=empresa,
            produto=produto,
            ativo_nessa_empresa=True,
        ).exists():
            raise ValidationError(
                f'Produto {produto.codigo_interno} não está ativo '
                f'na empresa {empresa.nome_fantasia}.'
            )

    transferencia = TransferenciaInterempresa.objects.create(
        empresa_origem=empresa_origem,
        empresa_destino=empresa_destino,
        local_origem=local_origem,
        local_destino=local_destino,
        produto=produto,
        quantidade=quantidade,
        custo_unitario=custo_unitario,
        status='PENDENTE',
        observacao=observacao,
        created_by=usuario,
        updated_by=usuario,
    )

    referencia = f'TRANSF_IE_{transferencia.id}'

    mov_saida = realizar_movimento_estoque(
        produto=produto,
        tipo_movimento='SAIDA',
        quantidade=quantidade,
        local_origem=local_origem,
        referencia=referencia,
        observacao=(
            f'Transferência interempresa #{transferencia.id} → {empresa_destino.nome_fantasia}'
        ),
        usuario=usuario,
    )

    mov_entrada = realizar_movimento_estoque(
        produto=produto,
        tipo_movimento='ENTRADA',
        quantidade=quantidade,
        local_destino=local_destino,
        custo_unitario=custo_unitario,
        referencia=referencia,
        observacao=(
            f'Transferência interempresa #{transferencia.id} ← {empresa_origem.nome_fantasia}'
        ),
        usuario=usuario,
    )

    transferencia.movimento_saida = mov_saida
    transferencia.movimento_entrada = mov_entrada
    transferencia.status = 'CONCLUIDA'
    transferencia.updated_by = usuario
    transferencia.save(
        update_fields=[
            'movimento_saida',
            'movimento_entrada',
            'status',
            'updated_by',
            'updated_at',
        ]
    )

    logger.info(
        'Transferência interempresa #%s concluída: %s → %s | %s x %s | custo=%s',
        transferencia.id,
        empresa_origem.nome_fantasia,
        empresa_destino.nome_fantasia,
        produto.codigo_interno,
        quantidade,
        custo_unitario,
    )

    return transferencia
