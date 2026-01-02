from __future__ import annotations

from .utils import is_root_admin


def user_permissions(request):
    """
    Inject simple permission booleans into all templates.
    """
    return {
        "is_root_admin": is_root_admin(getattr(request, "user", None)),
    }





