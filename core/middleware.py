"""
Middleware: sugere empresa padrão na sessão após login quando ainda vazia.
"""
from .models import UsuarioEmpresa
from .tenant import SESSION_KEY


class EmpresaAtivaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.session.get(SESSION_KEY):
            padrao = (
                UsuarioEmpresa.objects.filter(
                    user=request.user,
                    empresa_padrao=True,
                    is_active=True,
                )
                .select_related('empresa')
                .first()
            )
            if padrao:
                request.session[SESSION_KEY] = padrao.empresa_id

        return self.get_response(request)
