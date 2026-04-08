"""
Utilitários para contexto de tenant (empresa ativa na sessão).
"""
from django.core.exceptions import PermissionDenied

from .models import Empresa, UsuarioEmpresa

SESSION_KEY = 'empresa_ativa_id'


def get_empresa_ativa(request):
    """
    Retorna a Empresa ativa na sessão do usuário.
    Lança PermissionDenied se não há empresa na sessão ou se não está entre as permitidas.
    """
    empresa_id = request.session.get(SESSION_KEY)
    if not empresa_id:
        raise PermissionDenied('Nenhuma empresa selecionada na sessão.')

    permitidas = set(
        UsuarioEmpresa.objects.filter(
            user=request.user,
            is_active=True,
        ).values_list('empresa_id', flat=True)
    )

    if empresa_id not in permitidas:
        raise PermissionDenied('Empresa não permitida para este usuário.')

    return Empresa.objects.get(pk=empresa_id)


def set_empresa_ativa(request, empresa_id):
    """
    Define a empresa ativa na sessão após validar permissão.
    """
    permitida = UsuarioEmpresa.objects.filter(
        user=request.user,
        empresa_id=empresa_id,
        is_active=True,
    ).exists()

    if not permitida:
        raise PermissionDenied('Empresa não permitida para este usuário.')

    request.session[SESSION_KEY] = empresa_id


def get_empresas_permitidas(request):
    """
    Retorna queryset de Empresas que o usuário pode acessar.
    """
    return Empresa.objects.filter(
        usuarios_acesso__user=request.user,
        usuarios_acesso__is_active=True,
    ).distinct()
