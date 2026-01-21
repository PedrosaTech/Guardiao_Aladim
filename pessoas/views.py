"""
Views do app pessoas.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from rest_framework import viewsets
from .models import Cliente, Fornecedor
from .serializers import ClienteSerializer, FornecedorSerializer


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.filter(is_active=True)
    serializer_class = ClienteSerializer


class FornecedorViewSet(viewsets.ModelViewSet):
    queryset = Fornecedor.objects.filter(is_active=True)
    serializer_class = FornecedorSerializer


@login_required
def lista_clientes(request):
    """
    Lista de clientes com filtros.
    """
    clientes = Cliente.objects.filter(is_active=True).select_related('empresa', 'loja')
    
    # Filtros
    tipo_pessoa_filter = request.GET.get('tipo_pessoa')
    empresa_filter = request.GET.get('empresa')
    loja_filter = request.GET.get('loja')
    search = request.GET.get('search')
    
    if tipo_pessoa_filter:
        clientes = clientes.filter(tipo_pessoa=tipo_pessoa_filter)
    if empresa_filter:
        clientes = clientes.filter(empresa_id=empresa_filter)
    if loja_filter:
        clientes = clientes.filter(loja_id=loja_filter)
    if search:
        clientes = clientes.filter(
            Q(nome_razao_social__icontains=search) |
            Q(apelido_nome_fantasia__icontains=search) |
            Q(cpf_cnpj__icontains=search) |
            Q(email__icontains=search)
        )
    
    # Ordenação
    clientes = clientes.order_by('nome_razao_social')
    
    # Buscar dados para filtros
    from core.models import Empresa, Loja
    empresas = Empresa.objects.filter(is_active=True)
    lojas = Loja.objects.filter(is_active=True)
    
    context = {
        'clientes': clientes,
        'empresas': empresas,
        'lojas': lojas,
        'tipo_pessoa_choices': Cliente.TIPO_PESSOA_CHOICES,
        'filtros': {
            'tipo_pessoa': tipo_pessoa_filter,
            'empresa': empresa_filter,
            'loja': loja_filter,
            'search': search,
        }
    }
    
    return render(request, 'pessoas/lista_clientes.html', context)


@login_required
def detalhes_cliente(request, cliente_id):
    """
    Detalhes completos do cliente.
    """
    cliente = get_object_or_404(
        Cliente.objects.select_related('empresa', 'loja'),
        id=cliente_id,
        is_active=True
    )
    
    # Buscar pedidos do cliente
    from vendas.models import PedidoVenda
    pedidos = PedidoVenda.objects.filter(
        cliente=cliente,
        is_active=True
    ).order_by('-data_emissao')[:10]
    
    # Buscar notas fiscais do cliente
    from fiscal.models import NotaFiscalSaida
    notas = NotaFiscalSaida.objects.filter(
        cliente=cliente,
        is_active=True
    ).order_by('-data_emissao')[:10]
    
    context = {
        'cliente': cliente,
        'pedidos': pedidos,
        'notas': notas,
    }
    
    return render(request, 'pessoas/detalhes_cliente.html', context)


@login_required
def criar_cliente(request):
    """
    Cria um novo cliente.
    """
    from core.models import Empresa, Loja
    
    empresas = Empresa.objects.filter(is_active=True)
    lojas = Loja.objects.filter(is_active=True)
    
    if request.method == 'POST':
        try:
            cliente = Cliente.objects.create(
                empresa_id=request.POST.get('empresa'),
                loja_id=request.POST.get('loja') or None,
                tipo_pessoa=request.POST.get('tipo_pessoa'),
                nome_razao_social=request.POST.get('nome_razao_social'),
                apelido_nome_fantasia=request.POST.get('apelido_nome_fantasia') or None,
                cpf_cnpj=request.POST.get('cpf_cnpj'),
                rg_inscricao_estadual=request.POST.get('rg_inscricao_estadual') or None,
                data_nascimento=request.POST.get('data_nascimento') or None,
                telefone=request.POST.get('telefone') or None,
                whatsapp=request.POST.get('whatsapp') or None,
                email=request.POST.get('email') or None,
                logradouro=request.POST.get('logradouro') or None,
                numero=request.POST.get('numero') or None,
                complemento=request.POST.get('complemento') or None,
                bairro=request.POST.get('bairro') or None,
                cidade=request.POST.get('cidade') or None,
                uf=request.POST.get('uf') or None,
                cep=request.POST.get('cep') or None,
                created_by=request.user,
            )
            
            messages.success(request, f'Cliente "{cliente.nome_razao_social}" criado com sucesso!')
            return redirect('pessoas:detalhes_cliente', cliente_id=cliente.id)
        
        except Exception as e:
            context = {
                'empresas': empresas,
                'lojas': lojas,
                'tipo_pessoa_choices': Cliente.TIPO_PESSOA_CHOICES,
                'erro': str(e),
                'form_data': request.POST,
            }
            return render(request, 'pessoas/criar_cliente.html', context)
    
    context = {
        'empresas': empresas,
        'lojas': lojas,
        'tipo_pessoa_choices': Cliente.TIPO_PESSOA_CHOICES,
    }
    
    return render(request, 'pessoas/criar_cliente.html', context)


@login_required
def lista_fornecedores(request):
    """
    Lista de fornecedores com filtros.
    """
    fornecedores = Fornecedor.objects.filter(is_active=True).select_related('empresa')
    
    # Filtros
    empresa_filter = request.GET.get('empresa')
    search = request.GET.get('search')
    
    if empresa_filter:
        fornecedores = fornecedores.filter(empresa_id=empresa_filter)
    if search:
        fornecedores = fornecedores.filter(
            Q(razao_social__icontains=search) |
            Q(nome_fantasia__icontains=search) |
            Q(cnpj__icontains=search) |
            Q(email__icontains=search)
        )
    
    # Ordenação
    fornecedores = fornecedores.order_by('razao_social')
    
    # Buscar dados para filtros
    from core.models import Empresa
    empresas = Empresa.objects.filter(is_active=True)
    
    context = {
        'fornecedores': fornecedores,
        'empresas': empresas,
        'filtros': {
            'empresa': empresa_filter,
            'search': search,
        }
    }
    
    return render(request, 'pessoas/lista_fornecedores.html', context)


@login_required
def detalhes_fornecedor(request, fornecedor_id):
    """
    Detalhes completos do fornecedor.
    """
    fornecedor = get_object_or_404(
        Fornecedor.objects.select_related('empresa'),
        id=fornecedor_id,
        is_active=True
    )
    
    # Buscar notas fiscais de entrada do fornecedor
    from fiscal.models import NotaFiscalEntrada
    notas = NotaFiscalEntrada.objects.filter(
        fornecedor=fornecedor,
        is_active=True
    ).order_by('-data_entrada')[:10]
    
    context = {
        'fornecedor': fornecedor,
        'notas': notas,
    }
    
    return render(request, 'pessoas/detalhes_fornecedor.html', context)


@login_required
def criar_fornecedor(request):
    """
    Cria um novo fornecedor.
    """
    from core.models import Empresa
    
    empresas = Empresa.objects.filter(is_active=True)
    
    if request.method == 'POST':
        try:
            fornecedor = Fornecedor.objects.create(
                empresa_id=request.POST.get('empresa'),
                razao_social=request.POST.get('razao_social'),
                nome_fantasia=request.POST.get('nome_fantasia') or None,
                cnpj=request.POST.get('cnpj'),
                inscricao_estadual=request.POST.get('inscricao_estadual') or None,
                telefone=request.POST.get('telefone') or None,
                whatsapp=request.POST.get('whatsapp') or None,
                email=request.POST.get('email') or None,
                logradouro=request.POST.get('logradouro') or None,
                numero=request.POST.get('numero') or None,
                complemento=request.POST.get('complemento') or None,
                bairro=request.POST.get('bairro') or None,
                cidade=request.POST.get('cidade') or None,
                uf=request.POST.get('uf') or None,
                cep=request.POST.get('cep') or None,
                created_by=request.user,
            )
            
            messages.success(request, f'Fornecedor "{fornecedor.razao_social}" criado com sucesso!')
            return redirect('pessoas:detalhes_fornecedor', fornecedor_id=fornecedor.id)
        
        except Exception as e:
            context = {
                'empresas': empresas,
                'erro': str(e),
                'form_data': request.POST,
            }
            return render(request, 'pessoas/criar_fornecedor.html', context)
    
    context = {
        'empresas': empresas,
    }
    
    return render(request, 'pessoas/criar_fornecedor.html', context)
