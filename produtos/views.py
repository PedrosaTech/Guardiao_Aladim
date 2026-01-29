"""
Views do app produtos.
"""
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from rest_framework import viewsets

from pessoas.models import Fornecedor

from .forms import CodigoBarrasAlternativoForm, ProdutoForm
from .models import CategoriaProduto, CodigoBarrasAlternativo, Produto
from .serializers import CategoriaProdutoSerializer, ProdutoSerializer


class CategoriaProdutoViewSet(viewsets.ModelViewSet):
    queryset = CategoriaProduto.objects.filter(is_active=True)
    serializer_class = CategoriaProdutoSerializer


class ProdutoViewSet(viewsets.ModelViewSet):
    queryset = Produto.objects.filter(is_active=True)
    serializer_class = ProdutoSerializer


@login_required
def lista_produtos(request):
    """
    Lista de produtos com filtros.
    """
    produtos = Produto.objects.filter(is_active=True).select_related(
        'empresa', 'loja', 'categoria'
    )
    
    # Filtros
    categoria_filter = request.GET.get('categoria')
    classe_risco_filter = request.GET.get('classe_risco')
    empresa_filter = request.GET.get('empresa')
    loja_filter = request.GET.get('loja')
    restricao_exercito = request.GET.get('restricao_exercito')
    search = request.GET.get('search')
    
    if categoria_filter:
        produtos = produtos.filter(categoria_id=categoria_filter)
    if classe_risco_filter:
        produtos = produtos.filter(classe_risco=classe_risco_filter)
    if empresa_filter:
        produtos = produtos.filter(empresa_id=empresa_filter)
    if loja_filter:
        produtos = produtos.filter(loja_id=loja_filter)
    if restricao_exercito == 'sim':
        produtos = produtos.filter(possui_restricao_exercito=True)
    elif restricao_exercito == 'nao':
        produtos = produtos.filter(possui_restricao_exercito=False)
    if search:
        # Inclui códigos alternativos na busca da listagem
        ids_alt = CodigoBarrasAlternativo.objects.filter(
            codigo_barras__icontains=search,
            produto__in=produtos,
            produto__is_active=True,
            is_active=True,
        ).values_list('produto_id', flat=True)
        produtos = produtos.filter(
            Q(codigo_interno__icontains=search)
            | Q(codigo_barras__icontains=search)
            | Q(descricao__icontains=search)
            | Q(ncm__icontains=search)
            | Q(id__in=ids_alt)
        )
    
    # Ordenação
    produtos = produtos.order_by('codigo_interno', 'descricao')
    
    # Buscar dados para filtros
    from core.models import Empresa, Loja
    empresas = Empresa.objects.filter(is_active=True)
    lojas = Loja.objects.filter(is_active=True)
    categorias = CategoriaProduto.objects.filter(is_active=True)
    
    context = {
        'produtos': produtos,
        'empresas': empresas,
        'lojas': lojas,
        'categorias': categorias,
        'classe_risco_choices': Produto.CLASSE_RISCO_CHOICES,
        'filtros': {
            'categoria': categoria_filter,
            'classe_risco': classe_risco_filter,
            'empresa': empresa_filter,
            'loja': loja_filter,
            'restricao_exercito': restricao_exercito,
            'search': search,
        }
    }
    
    return render(request, 'produtos/lista_produtos.html', context)


@login_required
def detalhes_produto(request, produto_id):
    """
    Detalhes completos do produto.
    """
    produto = get_object_or_404(
        Produto.objects.select_related(
            'empresa', 'loja', 'categoria'
        ),
        id=produto_id,
        is_active=True
    )
    
    # Buscar estoque atual
    from estoque.models import EstoqueAtual
    estoques = EstoqueAtual.objects.filter(
        produto=produto,
        is_active=True
    ).select_related('local_estoque', 'local_estoque__loja')
    
    context = {
        'produto': produto,
        'estoques': estoques,
    }
    
    return render(request, 'produtos/detalhes_produto.html', context)


@login_required
def criar_produto(request):
    """
    Cria um novo produto.
    """
    from core.models import Empresa, Loja
    
    empresas = Empresa.objects.filter(is_active=True)
    lojas = Loja.objects.filter(is_active=True)
    categorias = CategoriaProduto.objects.filter(is_active=True)
    
    if request.method == 'POST':
        try:
            # Processar formulário
            produto = Produto.objects.create(
                empresa_id=request.POST.get('empresa'),
                loja_id=request.POST.get('loja') or None,
                categoria_id=request.POST.get('categoria'),
                codigo_barras=request.POST.get('codigo_barras') or None,
                descricao=request.POST.get('descricao'),
                classe_risco=request.POST.get('classe_risco'),
                subclasse_risco=request.POST.get('subclasse_risco') or None,
                possui_restricao_exercito=request.POST.get('possui_restricao_exercito') == 'on',
                numero_certificado_exercito=request.POST.get('numero_certificado_exercito') or None,
                numero_lote=request.POST.get('numero_lote') or None,
                validade=request.POST.get('validade') or None,
                condicoes_armazenamento=request.POST.get('condicoes_armazenamento') or None,
                # Campos fiscais
                ncm=request.POST.get('ncm'),
                cest=request.POST.get('cest') or None,
                cfop_venda_dentro_uf=request.POST.get('cfop_venda_dentro_uf'),
                cfop_venda_fora_uf=request.POST.get('cfop_venda_fora_uf') or None,
                unidade_comercial=request.POST.get('unidade_comercial', 'UN'),
                origem=request.POST.get('origem', '0'),
                csosn_cst=request.POST.get('csosn_cst'),
                aliquota_icms=request.POST.get('aliquota_icms') or 0,
                icms_st_cst=request.POST.get('icms_st_cst') or None,
                aliquota_icms_st=request.POST.get('aliquota_icms_st') or 0,
                pis_cst=request.POST.get('pis_cst', '01'),
                aliquota_pis=request.POST.get('aliquota_pis') or 1.65,
                cofins_cst=request.POST.get('cofins_cst', '01'),
                aliquota_cofins=request.POST.get('aliquota_cofins') or 7.60,
                ipi_venda_cst=request.POST.get('ipi_venda_cst', '52'),
                aliquota_ipi_venda=request.POST.get('aliquota_ipi_venda') or 0,
                ipi_compra_cst=request.POST.get('ipi_compra_cst', '02'),
                aliquota_ipi_compra=request.POST.get('aliquota_ipi_compra') or 0,
                # Comercial
                preco_venda_sugerido=request.POST.get('preco_venda_sugerido'),
                observacoes=request.POST.get('observacoes') or None,
                created_by=request.user,
            )
            
            messages.success(request, f'Produto "{produto.descricao}" criado com sucesso!')
            return redirect('produtos:detalhes_produto', produto_id=produto.id)
        
        except Exception as e:
            context = {
                'empresas': empresas,
                'lojas': lojas,
                'categorias': categorias,
                'classe_risco_choices': Produto.CLASSE_RISCO_CHOICES,
                'erro': str(e),
                'form_data': request.POST,
            }
            return render(request, 'produtos/criar_produto.html', context)
    
    context = {
        'empresas': empresas,
        'lojas': lojas,
        'categorias': categorias,
        'classe_risco_choices': Produto.CLASSE_RISCO_CHOICES,
    }
    
    return render(request, 'produtos/criar_produto.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def produto_editar(request, produto_id):
    """Edição de produto."""
    produto = get_object_or_404(
        Produto.objects.select_related('empresa', 'loja', 'categoria'),
        pk=produto_id,
        is_active=True,
    )
    if request.method == 'POST':
        form = ProdutoForm(request.POST, instance=produto)
        if form.is_valid():
            p = form.save(commit=False)
            p.updated_by = request.user
            p.save()
            messages.success(request, f'Produto "{p.descricao}" atualizado com sucesso.')
            return redirect('produtos:detalhes_produto', produto_id=p.id)
    else:
        form = ProdutoForm(instance=produto)
    return render(request, 'produtos/produto_editar.html', {'form': form, 'produto': produto})


@login_required
@require_http_methods(['GET'])
def produto_codigos_alternativos(request, produto_id):
    """Página de códigos alternativos do produto."""
    produto = get_object_or_404(
        Produto.objects.select_related('empresa', 'categoria'),
        pk=produto_id,
        is_active=True,
    )
    codigos = produto.codigos_alternativos.filter(is_active=True).select_related('fornecedor').order_by('codigo_barras')
    fornecedores = Fornecedor.objects.filter(
        empresa=produto.empresa, is_active=True
    ).order_by('razao_social')
    form_add = CodigoBarrasAlternativoForm(empresa=produto.empresa)
    return render(request, 'produtos/produto_codigos_alternativos.html', {
        'produto': produto,
        'codigos': codigos,
        'fornecedores': fornecedores,
        'form_add': form_add,
    })


@login_required
@require_http_methods(['POST'])
def codigo_alternativo_criar(request, produto_id):
    """Criar código alternativo via AJAX. Sempre retorna JSON."""
    produto = get_object_or_404(Produto, pk=produto_id, is_active=True)
    fornecedor_id = request.POST.get('fornecedor_id')
    fornecedor = None
    if fornecedor_id:
        try:
            fornecedor = Fornecedor.objects.get(
                pk=int(fornecedor_id),
                empresa=produto.empresa,
                is_active=True,
            )
        except (Fornecedor.DoesNotExist, ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'message': 'Fornecedor inválido ou não pertence a esta empresa.',
            }, status=400)
    form = CodigoBarrasAlternativoForm(request.POST, empresa=produto.empresa)
    form.instance.produto = produto
    if form.is_valid():
        try:
            codigo = form.save(commit=False)
            codigo.fornecedor = fornecedor
            codigo.created_by = request.user
            codigo.full_clean()
            codigo.save()
            return JsonResponse({
                'success': True,
                'message': 'Código alternativo adicionado com sucesso!',
                'codigo': {
                    'id': codigo.id,
                    'codigo_barras': codigo.codigo_barras,
                    'descricao': codigo.descricao or '',
                    'multiplicador': f'{codigo.multiplicador:.3f}',
                    'fornecedor_id': codigo.fornecedor_id,
                    'fornecedor_nome': codigo.fornecedor.razao_social if codigo.fornecedor else None,
                },
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Erro ao salvar: {str(e)}'}, status=400)
    errors = []
    for _f, errs in form.errors.items():
        for e in errs:
            errors.append(str(e))
    return JsonResponse({'success': False, 'message': ' | '.join(errors)}, status=400)


@login_required
@require_http_methods(['POST'])
def codigo_alternativo_editar(request, codigo_id):
    """Editar código alternativo via AJAX. Sempre retorna JSON."""
    codigo = get_object_or_404(CodigoBarrasAlternativo, pk=codigo_id, is_active=True)
    fornecedor_id = request.POST.get('fornecedor_id')
    fornecedor = None
    if fornecedor_id:
        try:
            fornecedor = Fornecedor.objects.get(
                pk=int(fornecedor_id),
                empresa=codigo.produto.empresa,
                is_active=True,
            )
        except (Fornecedor.DoesNotExist, ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'message': 'Fornecedor inválido ou não pertence a esta empresa.',
            }, status=400)
    form = CodigoBarrasAlternativoForm(
        request.POST, instance=codigo, empresa=codigo.produto.empresa
    )
    if form.is_valid():
        try:
            c = form.save(commit=False)
            c.fornecedor = fornecedor
            c.updated_by = request.user
            c.full_clean()
            c.save()
            return JsonResponse({
                'success': True,
                'message': 'Código alternativo atualizado com sucesso!',
                'codigo': {
                    'id': c.id,
                    'codigo_barras': c.codigo_barras,
                    'descricao': c.descricao or '',
                    'multiplicador': f'{c.multiplicador:.3f}',
                    'fornecedor_id': c.fornecedor_id,
                    'fornecedor_nome': c.fornecedor.razao_social if c.fornecedor else None,
                },
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Erro ao salvar: {str(e)}'}, status=400)
    errors = []
    for _f, errs in form.errors.items():
        for e in errs:
            errors.append(str(e))
    return JsonResponse({'success': False, 'message': ' | '.join(errors)}, status=400)


@login_required
@require_http_methods(['POST'])
def codigo_alternativo_inativar(request, codigo_id):
    """Inativar código alternativo via AJAX. Sempre retorna JSON."""
    codigo = get_object_or_404(CodigoBarrasAlternativo, pk=codigo_id, is_active=True)
    codigo.is_active = False
    codigo.updated_by = request.user
    codigo.save()
    return JsonResponse({
        'success': True,
        'message': 'Código alternativo removido com sucesso.',
    })


@login_required
@require_http_methods(['GET', 'POST'])
def produto_inativar(request, produto_id):
    """Confirmação e inativação de produto (soft delete)."""
    produto = get_object_or_404(
        Produto.objects.select_related('empresa', 'categoria'),
        pk=produto_id,
        is_active=True,
    )
    if request.method == 'POST':
        produto.is_active = False
        produto.updated_by = request.user
        produto.save()
        produto.codigos_alternativos.filter(is_active=True).update(is_active=False)
        messages.success(request, f'Produto "{produto.descricao}" foi inativado.')
        return redirect('produtos:lista_produtos')
    codigos_ativos = produto.codigos_alternativos.filter(is_active=True)
    return render(request, 'produtos/produto_inativar_confirm.html', {
        'produto': produto,
        'codigos_ativos': codigos_ativos,
    })
