"""
Views de cadastro de Configuracao Fiscal de Loja (somente ADMINISTRADOR).
"""
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from core.decorators import administrador_required
from core.models import Loja
from core.tenant import get_empresa_ativa
from .forms import ConfiguracaoFiscalLojaForm
from .models import ConfiguracaoFiscalLoja


@administrador_required
def lista_config_fiscal(request):
    """Lista configuracoes fiscais das lojas da empresa ativa."""
    empresa = get_empresa_ativa(request)
    configs = (
        ConfiguracaoFiscalLoja.objects
        .filter(loja__empresa=empresa)
        .select_related("loja", "loja__empresa")
        .order_by("loja__empresa__nome_fantasia", "loja__nome")
    )
    return render(request, "fiscal/lista_config_fiscal.html", {"configs": configs})


@administrador_required
def criar_config_fiscal(request):
    """Formulario para criar configuracao fiscal de uma loja nova."""
    empresa = get_empresa_ativa(request)
    if request.method == "POST":
        form = ConfiguracaoFiscalLojaForm(request.POST, empresa=empresa)
        if form.is_valid():
            config = form.save(commit=False)
            config.created_by = request.user
            config.updated_by = request.user
            config.save()
            messages.success(
                request,
                f'Configuracao fiscal da loja "{config.loja}" criada com sucesso! '
                "Recomendamos iniciar em ambiente de Homologacao.",
            )
            return redirect("fiscal:lista_config_fiscal")
    else:
        initial = {}
        loja_id = request.GET.get("loja")
        if loja_id and loja_id.isdigit():
            lojas_livres = Loja.objects.filter(empresa=empresa, is_active=True).exclude(
                configuracao_fiscal__isnull=False
            )
            loja = lojas_livres.filter(pk=int(loja_id)).first()
            if loja:
                initial["loja"] = loja.pk
        form = ConfiguracaoFiscalLojaForm(initial=initial, empresa=empresa)

    return render(
        request,
        "fiscal/form_config_fiscal.html",
        {"form": form, "titulo": "Nova Configuracao Fiscal", "acao": "Criar"},
    )


@administrador_required
def editar_config_fiscal(request, pk):
    """Formulario para editar configuracao fiscal existente."""
    empresa = get_empresa_ativa(request)
    config = get_object_or_404(
        ConfiguracaoFiscalLoja.objects.select_related("loja", "loja__empresa"),
        pk=pk,
        loja__empresa=empresa,
    )

    if request.method == "POST":
        form = ConfiguracaoFiscalLojaForm(request.POST, instance=config, empresa=empresa)
        if form.is_valid():
            config = form.save(commit=False)
            config.updated_by = request.user
            config.save()
            messages.success(request, f'Configuracao fiscal da loja "{config.loja}" atualizada com sucesso!')
            return redirect("fiscal:lista_config_fiscal")
    else:
        form = ConfiguracaoFiscalLojaForm(instance=config, empresa=empresa)

    return render(
        request,
        "fiscal/form_config_fiscal.html",
        {
            "form": form,
            "config": config,
            "titulo": f"Editar Configuracao - {config.loja}",
            "acao": "Salvar alteracoes",
        },
    )
