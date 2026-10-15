"""
Outil réutilisable pour protéger une page par rôle.

Utilisation, au-dessus d'une vue :
    @role_requis(roles.SERVICE_STAGES)
    def ma_vue(request): ...

- visiteur non connecté  -> renvoyé vers la page de connexion
- connecté sans ce rôle  -> refus (erreur 403, page « Accès refusé »)
"""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_requis(*roles_acceptes):
    """Autorise la page si la personne a AU MOINS UN des rôles donnés."""

    def decorateur(vue):
        @login_required
        @wraps(vue)
        def vue_protegee(request, *args, **kwargs):
            if not any(request.user.a_le_role(role) for role in roles_acceptes):
                raise PermissionDenied("Page réservée aux rôles : " + ", ".join(roles_acceptes))
            return vue(request, *args, **kwargs)

        return vue_protegee

    return decorateur
