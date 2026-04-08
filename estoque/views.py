"""
Views do app estoque.
"""
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework import viewsets

from core.tenant import get_empresa_ativa, get_empresas_permitidas

from .models import LocalEstoque, EstoqueAtual, MovimentoEstoque
from .serializers import LocalEstoqueSerializer, EstoqueAtualSerializer, MovimentoEstoqueSerializer
from .transferencia import executar_transferencia_interempresa


class LocalEstoqueViewSet(viewsets.ModelViewSet):
    queryset = LocalEstoque.objects.filter(is_active=True)
    serializer_class = LocalEstoqueSerializer


class EstoqueAtualViewSet(viewsets.ModelViewSet):
    queryset = EstoqueAtual.objects.filter(is_active=True)
    serializer_class = EstoqueAtualSerializer


class MovimentoEstoqueViewSet(viewsets.ModelViewSet):
    queryset = MovimentoEstoque.objects.all()
    serializer_class = MovimentoEstoqueSerializer


@login_required
def transferencia_interempresa(request):
    """
    Transferência física entre CNPJs: saída na empresa ativa, entrada na outra
    empresa à qual o usuário também tem acesso.
    """
    from produtos.models import Produto, ProdutoParametrosEmpresa

    empresa_ativa = get_empresa_ativa(request)
    empresas_destino = get_empresas_permitidas(request).exclude(pk=empresa_ativa.pk)

    locais_origem = LocalEstoque.objects.filter(
        loja__empresa=empresa_ativa,
        is_active=True,
    ).select_related('loja')

    locais_destino = LocalEstoque.objects.filter(
        loja__empresa__in=empresas_destino,
        is_active=True,
    ).select_related('loja', 'loja__empresa')

    produtos_destino_ids = ProdutoParametrosEmpresa.objects.filter(
        empresa__in=empresas_destino,
        ativo_nessa_empresa=True,
    ).values_list('produto_id', flat=True)

    produtos = (
        Produto.objects.filter(
            is_active=True,
            parametros_por_empresa__empresa=empresa_ativa,
            parametros_por_empresa__ativo_nessa_empresa=True,
            pk__in=produtos_destino_ids,
        )
        .distinct()
        .order_by('codigo_interno')
    )

    if request.method == 'POST':
        try:
            produto_id = int(request.POST['produto_id'])
            local_origem_id = int(request.POST['local_origem_id'])
            local_destino_id = int(request.POST['local_destino_id'])
            quantidade = Decimal(request.POST['quantidade'].replace(',', '.'))
            custo_unitario = Decimal(request.POST['custo_unitario'].replace(',', '.'))
            observacao = (request.POST.get('observacao') or '').strip() or None

            produto = get_object_or_404(
                Produto,
                pk=produto_id,
                is_active=True,
                parametros_por_empresa__empresa=empresa_ativa,
                parametros_por_empresa__ativo_nessa_empresa=True,
            )
            local_origem = get_object_or_404(
                LocalEstoque,
                pk=local_origem_id,
                loja__empresa=empresa_ativa,
                is_active=True,
            )
            local_destino = get_object_or_404(
                LocalEstoque,
                pk=local_destino_id,
                loja__empresa__in=empresas_destino,
                is_active=True,
            )

            transferencia = executar_transferencia_interempresa(
                produto=produto,
                local_origem=local_origem,
                local_destino=local_destino,
                quantidade=quantidade,
                custo_unitario=custo_unitario,
                usuario=request.user,
                observacao=observacao,
            )
            messages.success(
                request,
                f'Transferência #{transferencia.id} concluída com sucesso.',
            )
            return redirect('estoque:transferencia_interempresa')

        except (ValidationError, ValueError, InvalidOperation) as e:
            if isinstance(e, ValidationError):
                msg = '; '.join(e.messages) if hasattr(e, 'messages') else str(e)
            else:
                msg = str(e)
            messages.error(request, msg)

    return render(
        request,
        'estoque/transferencia_interempresa.html',
        {
            'locais_origem': locais_origem,
            'locais_destino': locais_destino,
            'empresa_ativa': empresa_ativa,
            'empresas_destino': empresas_destino,
            'produtos': produtos,
        },
    )

