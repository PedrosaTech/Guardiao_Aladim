"""
Views da central de guias de uso.
"""
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import GuiaUso


@login_required
def lista_guias(request):
    """Lista guias publicados para usuarios autenticados."""
    busca = request.GET.get("q", "").strip()
    guias = GuiaUso.objects.filter(is_active=True, publicado=True).order_by("ordem", "titulo")
    if busca:
        guias = guias.filter(
            Q(titulo__icontains=busca)
            | Q(categoria__icontains=busca)
            | Q(resumo__icontains=busca)
            | Q(conteudo__icontains=busca)
        )
    return render(request, "core/lista_guias.html", {"guias": guias, "busca": busca})


@login_required
def detalhe_guia(request, slug):
    """Exibe um guia de uso publicado."""
    guia = get_object_or_404(GuiaUso, slug=slug, is_active=True, publicado=True)
    return render(request, "core/detalhe_guia.html", {"guia": guia})
