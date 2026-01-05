from __future__ import annotations
from .utils import is_root_admin
from .models import UserMenuPermission
from apps.core.tenant_utils import get_current_tenant

def user_permissions(request):
    """
    Inject simple permission booleans into all templates.
    """
    user = getattr(request, "user", None)
    is_root = is_root_admin(user)
    
    perms = {}
    
    # Root admin için tüm izinler açık (zaten base.html'de root admin için menüler gösteriliyor)
    if is_root:
        # Root admin için tüm menüleri açık yap (base.html'de zaten gösteriliyor ama yine de set edelim)
        perms = {
            'hierarchy': True,
            'users': True,
            'customers': True,
            'tasks': True,
            'route_plan': True,
            'forms': True,
            'images': True,
            'reports': True,
        }
    # Firma admin kullanıcıları için tüm izinler açık
    elif user and user.is_authenticated:
        # Firma admin kontrolü: user_code='admin' ve authority='Admin' olan kullanıcılar
        is_tenant_admin = (
            hasattr(user, 'user_code') and user.user_code == 'admin' and
            hasattr(user, 'authority') and user.authority == 'Admin' and
            hasattr(user, 'tenant') and user.tenant is not None
        )
        
        if is_tenant_admin:
            # Firma admin için tüm menüleri açık yap
            perms = {
                'hierarchy': True,
                'users': True,
                'customers': True,
                'tasks': True,
                'route_plan': True,
                'forms': True,
                'images': True,
                'reports': True,
            }
        else:
            # Normal kullanıcılar için izinleri çek
            tenant = get_current_tenant(request)
            
            if tenant:
                # Bu tenant için kullanıcının izinlerini al
                user_perms = UserMenuPermission.objects.filter(user=user, tenant=tenant)
                for p in user_perms:
                    if p.can_view:
                        perms[p.menu_key] = True

    # Firma admin kontrolü
    is_tenant_admin = False
    if user and user.is_authenticated and not is_root:
        is_tenant_admin = (
            hasattr(user, 'user_code') and user.user_code == 'admin' and
            hasattr(user, 'authority') and user.authority == 'Admin' and
            hasattr(user, 'tenant') and user.tenant is not None
        )
    
    return {
        "is_root_admin": is_root,
        "is_tenant_admin": is_tenant_admin,
        "user_menu_perms": perms, # {'hierarchy': True, 'users': True, ...}
    }
