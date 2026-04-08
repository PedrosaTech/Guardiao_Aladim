"""
Views de cadastro de Empresa e Loja (somente ADMINISTRADOR).
Separado de core/views.py para nao misturar com os ViewSets da API REST.
"""
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .decorators import administrador_required
from .forms import EmpresaForm, LojaForm
from .models import Empresa, Loja


@administrador_required
def lista_empresas(request):
    """Lista todas as empresas com busca simples."""
    search = request.GET.get("search", "").strip()
    ativas = request.GET.get("ativas", "")
    qs = Empresa.objects.all().order_by("nome_fantasia")

    if search:
        qs = qs.filter(
            Q(nome_fantasia__icontains=search) | Q(razao_social__icontains=search)
        )
    if ativas == "1":
        qs = qs.filter(is_active=True)
    elif ativas == "0":
        qs = qs.filter(is_active=False)

    return render(
        request,
        "core/lista_empresas.html",
        {
            "empresas": qs,
            "filtros": {"search": search, "ativas": ativas},
        },
    )


@administrador_required
def criar_empresa(request):
    """Formulario para criacao de nova empresa."""
    if request.method == "POST":
        form = EmpresaForm(request.POST)
        if form.is_valid():
            empresa = form.save(commit=False)
            empresa.created_by = request.user
            empresa.updated_by = request.user
            empresa.save()
            messages.success(request, f'Empresa "{empresa.nome_fantasia}" criada com sucesso!')
            return redirect("core:lista_empresas")
    else:
        form = EmpresaForm()

    return render(
        request,
        "core/form_empresa.html",
        {"form": form, "titulo": "Nova Empresa", "acao": "Criar"},
    )


@administrador_required
def editar_empresa(request, pk):
    """Formulario para edicao de empresa existente."""
    empresa = get_object_or_404(Empresa, pk=pk)

    if request.method == "POST":
        form = EmpresaForm(request.POST, instance=empresa)
        if form.is_valid():
            empresa = form.save(commit=False)
            empresa.updated_by = request.user
            empresa.save()
            messages.success(request, f'Empresa "{empresa.nome_fantasia}" atualizada com sucesso!')
            return redirect("core:lista_empresas")
    else:
        form = EmpresaForm(instance=empresa)

    return render(
        request,
        "core/form_empresa.html",
        {
            "form": form,
            "empresa": empresa,
            "titulo": f"Editar Empresa - {empresa.nome_fantasia}",
            "acao": "Salvar alteracoes",
        },
    )


@administrador_required
def lista_lojas(request):
    """Lista todas as lojas com filtro por empresa e busca."""
    search = request.GET.get("search", "").strip()
    empresa_id = request.GET.get("empresa", "")
    ativas = request.GET.get("ativas", "")

    qs = Loja.objects.select_related("empresa").order_by("empresa__nome_fantasia", "nome")

    if search:
        qs = qs.filter(
            Q(nome__icontains=search) | Q(empresa__nome_fantasia__icontains=search)
        )
    if empresa_id:
        qs = qs.filter(empresa_id=empresa_id)
    if ativas == "1":
        qs = qs.filter(is_active=True)
    elif ativas == "0":
        qs = qs.filter(is_active=False)

    empresas = Empresa.objects.filter(is_active=True).order_by("nome_fantasia")

    return render(
        request,
        "core/lista_lojas.html",
        {
            "lojas": qs,
            "empresas": empresas,
            "filtros": {"search": search, "empresa": empresa_id, "ativas": ativas},
        },
    )


@administrador_required
def criar_loja(request):
    """Formulario para criacao de nova loja."""
    if request.method == "POST":
        form = LojaForm(request.POST)
        if form.is_valid():
            loja = form.save(commit=False)
            loja.created_by = request.user
            loja.updated_by = request.user
            loja.save()
            messages.success(request, f'Loja "{loja.nome}" criada com sucesso!')
            return redirect("core:lista_lojas")
    else:
        form = LojaForm()

    return render(
        request,
        "core/form_loja.html",
        {"form": form, "titulo": "Nova Loja", "acao": "Criar"},
    )


@administrador_required
def editar_loja(request, pk):
    """Formulario para edicao de loja existente."""
    loja = get_object_or_404(Loja.objects.select_related("empresa"), pk=pk)

    if request.method == "POST":
        form = LojaForm(request.POST, instance=loja)
        if form.is_valid():
            loja = form.save(commit=False)
            loja.updated_by = request.user
            loja.save()
            messages.success(request, f'Loja "{loja.nome}" atualizada com sucesso!')
            return redirect("core:lista_lojas")
    else:
        form = LojaForm(instance=loja)

    return render(
        request,
        "core/form_loja.html",
        {
            "form": form,
            "loja": loja,
            "titulo": f"Editar Loja - {loja.nome}",
            "acao": "Salvar alteracoes",
        },
    )
