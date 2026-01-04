"""
Core utility functions for tenant management
"""
from django.core.exceptions import PermissionDenied
from .models import Tenant
import math


def get_current_tenant(request):
    """
    Request'ten mevcut tenant'ı alır.
    Root admin ise None döner (tüm firmaları görebilir).
    """
    # Root admin kontrolü
    from apps.users.utils import is_root_admin
    if is_root_admin(request.user):
        return None
    
    # Session'dan tenant al
    tenant = None
    if 'tenant_id' in request.session:
        try:
            tenant = Tenant.objects.get(id=request.session['tenant_id'], is_active=True)
        except Tenant.DoesNotExist:
            del request.session['tenant_id']
    
    # Eğer tenant yoksa, ilk aktif tenant'ı al
    if not tenant:
        tenant = Tenant.objects.filter(is_active=True).first()
        if tenant:
            request.session['tenant_id'] = tenant.id
    
    return tenant


def require_tenant(view_func):
    """
    Decorator: View'ın çalışması için tenant gerekli.
    Root admin ise tenant gerekmez.
    """
    def wrapper(request, *args, **kwargs):
        from apps.users.utils import is_root_admin
        tenant = get_current_tenant(request)
        
        # Root admin değilse ve tenant yoksa hata ver
        if not tenant and not is_root_admin(request.user):
            from django.contrib import messages
            from django.shortcuts import redirect
            messages.error(request, 'Firma seçilmedi. Lütfen geliştirici admin paneline giriş yapın.')
            return redirect('admin_login')
        
        # Request'e tenant ekle
        request.tenant = tenant
        return view_func(request, *args, **kwargs)
    
    return wrapper


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    İki koordinat arasındaki mesafeyi kilometre cinsinden hesaplar (Haversine formülü)
    """
    try:
        # Dereceyi radyana çevir
        lat1_rad = math.radians(float(lat1))
        lon1_rad = math.radians(float(lon1))
        lat2_rad = math.radians(float(lat2))
        lon2_rad = math.radians(float(lon2))
        
        # Haversine formülü
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Dünya yarıçapı (km)
        R = 6371
        
        distance = R * c
        return round(distance, 2)
    except (ValueError, TypeError):
        return None
