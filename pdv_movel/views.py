"""
Views do PDV Móvel (Tablet).
Servem templates HTML que consomem API REST via JavaScript.
"""
import os

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.utils import timezone

from .models import AtendentePDV


def sw_js(request):
    """
    Serve o Service Worker em /pdv-movel/sw.js.
    Header Service-Worker-Allowed permite scope /pdv-movel/ mesmo com script sob /pdv-movel/.
    """
    base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, "static", "pdv_movel", "sw.js")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    r = HttpResponse(content, content_type="application/javascript")
    r["Service-Worker-Allowed"] = "/pdv-movel/"
    r["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return r


def login_pin(request):
    """
    Tela de login com PIN de 4 dígitos.

    GET: Exibe tela de login
    POST: Valida PIN e faz login
    """
    if request.method == "POST":
        pin = request.POST.get("pin", "").strip()

        if len(pin) != 4 or not pin.isdigit():
            messages.error(request, "PIN deve ter 4 dígitos.")
            return render(request, "pdv_movel/login.html")

        atendente = (
            AtendentePDV.objects.select_related("user", "loja")
            .filter(pin=pin, ativo=True, loja__is_active=True)
            .first()
        )

        if not atendente:
            messages.error(request, "PIN inválido ou atendente inativo.")
            return render(request, "pdv_movel/login.html")

        try:
            config = atendente.loja.config_pdv_movel
            if not config or not config.ativo:
                messages.error(request, "PDV Móvel desativado nesta loja.")
                return render(request, "pdv_movel/login.html")
        except Exception:
            messages.error(request, "PDV Móvel não configurado.")
            return render(request, "pdv_movel/login.html")

        auth_login(
            request, atendente.user, backend="django.contrib.auth.backends.ModelBackend"
        )
        atendente.ultima_sessao = timezone.now()
        atendente.save(update_fields=["ultima_sessao"])

        return redirect("pdv_movel:pedido_novo")

    if request.user.is_authenticated and hasattr(request.user, "atendente_pdv"):
        return redirect("pdv_movel:pedido_novo")

    return render(request, "pdv_movel/login.html")


@login_required(login_url="/pdv-movel/")
def logout_view(request):
    """Logout do atendente."""
    auth_logout(request)
    messages.success(request, "Logout realizado com sucesso.")
    return redirect("pdv_movel:login_pin")


@login_required(login_url="/pdv-movel/")
def pedido_novo(request):
    """
    Tela para criar/editar pedido.
    Usa API REST via JavaScript.
    """
    if not hasattr(request.user, "atendente_pdv"):
        messages.error(request, "Você não é um atendente PDV.")
        return redirect("pdv_movel:login_pin")

    atendente = request.user.atendente_pdv
    if not atendente.ativo:
        messages.error(request, "Seu acesso ao PDV Móvel está inativo.")
        auth_logout(request)
        return redirect("pdv_movel:login_pin")

    return render(
        request,
        "pdv_movel/pedido_novo.html",
        {"atendente": atendente, "loja": atendente.loja},
    )


@login_required(login_url="/pdv-movel/")
def pedido_lista(request):
    """
    Lista pedidos do atendente.
    Dados carregados via API REST.
    """
    if not hasattr(request.user, "atendente_pdv"):
        messages.error(request, "Você não é um atendente PDV.")
        return redirect("pdv_movel:login_pin")

    atendente = request.user.atendente_pdv
    return render(
        request,
        "pdv_movel/pedido_lista.html",
        {"atendente": atendente, "loja": atendente.loja},
    )
