"""
Variáveis de template para tenant (empresa na sessão).
"""
from .models import UsuarioEmpresa
from .tenant import SESSION_KEY


def tenant_context(request):
    if not getattr(request.user, 'is_authenticated', False):
        return {}
    return {
        'empresa_ativa_session_id': request.session.get(SESSION_KEY),
        'usuario_empresas_ativas': UsuarioEmpresa.objects.filter(
            user=request.user,
            is_active=True,
        ).select_related('empresa'),
    }
