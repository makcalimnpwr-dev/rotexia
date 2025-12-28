from __future__ import annotations

from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from .utils import ensure_root_admin_configured, is_root_admin


def root_admin_required(view_func):
    """
    Only the root Admin user can access.
    """

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")

        # Bootstrap: Root admin henüz set edilmediyse ilk Admin girişini root admin yap.
        ensure_root_admin_configured(request.user)

        if not is_root_admin(request.user):
            messages.error(request, "Bu sayfaya erişim yetkiniz yok.")
            return redirect("home")
        return view_func(request, *args, **kwargs)

    return _wrapped


