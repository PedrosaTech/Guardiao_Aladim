"""
Permissões customizadas para API do PDV Móvel.
"""
from rest_framework import permissions


class IsAtendentePDVAtivo(permissions.BasePermission):
    """
    Permissão: usuário deve ser atendente PDV ativo.

    Usado em endpoints que requerem autenticação de atendente.
    """

    message = "Você precisa ser um atendente PDV ativo para acessar este recurso."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if not hasattr(request.user, "atendente_pdv"):
            return False
        atendente = request.user.atendente_pdv
        if not atendente.ativo:
            return False
        try:
            config = atendente.loja.config_pdv_movel
        except Exception:
            return False
        if not config or not config.ativo:
            return False
        return True


class IsCaixaOuAtendente(permissions.BasePermission):
    """
    Permissão: usuário autenticado (caixa ou atendente).
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)
