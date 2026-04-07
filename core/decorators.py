"""
Decorators reutilizaveis do app core.
"""
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test


def _is_administrador(user):
    """Retorna True se o usuario e superuser ou do grupo ADMINISTRADOR."""
    if user is None or not getattr(user, "is_authenticated", False):
        return False
    return user.is_active and (
        user.is_superuser or user.groups.filter(name="ADMINISTRADOR").exists()
    )


def administrador_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Exige usuario superuser ou membro de ADMINISTRADOR.
    """
    actual_decorator = user_passes_test(
        _is_administrador,
        login_url=login_url or "/admin/login/",
        redirect_field_name=redirect_field_name,
    )
    if function:
        return actual_decorator(function)
    return actual_decorator
