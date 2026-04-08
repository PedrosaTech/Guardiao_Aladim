"""
Template tags para controle de acesso administrativo.
"""
from django import template

register = template.Library()


@register.filter(name="is_administrador")
def is_administrador(user):
    """Filtro de template para superuser ou grupo ADMINISTRADOR."""
    if user is None or not getattr(user, "is_authenticated", False):
        return False
    return user.is_active and (
        user.is_superuser or user.groups.filter(name="ADMINISTRADOR").exists()
    )
