from .models import SiteSetting, Tenant

def site_settings(request):
    """
    Tüm template'lere 'settings' değişkenini gönderir.
    Böylece base.html içinde {{ settings.primary_color }} diyebiliriz.
    """
    return {'settings': SiteSetting.load()}

def tenant_context(request):
    """
    Tüm template'lere 'tenant' ve ilgili değişkenleri gönderir.
    Middleware'den gelen request.tenant'ı kullanır.
    Development'ta session'dan tenant alır.
    """
    tenant = getattr(request, 'tenant', None)
    
    # Development modunda subdomain yoksa session'dan tenant al
    if not tenant and request.user.is_authenticated:
        host = request.get_host()
        host_without_port = host.split(':')[0] if ':' in host else host
        
        # 127.0.0.1 veya localhost ise session'dan tenant al
        if host_without_port in ['127.0.0.1', 'localhost']:
            tenant_id = request.session.get('tenant_id')
            if tenant_id:
                try:
                    tenant = Tenant.objects.get(id=tenant_id, is_active=True)
                    # Request'e de ekle (diğer view'lar için)
                    request.tenant = tenant
                except Tenant.DoesNotExist:
                    request.session.pop('tenant_id', None)
    
    # Subdomain kontrolü - admin panelinde miyiz?
    is_admin_panel = False
    host = request.get_host()
    host_without_port = host.split(':')[0] if ':' in host else host
    
    # 127.0.0.1 veya localhost'u subdomain olarak sayma
    has_subdomain = '.' in host_without_port and host_without_port not in ['127.0.0.1', 'localhost']
    
    if has_subdomain:
        parts = host_without_port.split('.')
        subdomain = parts[0].lower()
        is_admin_panel = (subdomain == 'admin')
    else:
        # Subdomain yok ve tenant yoksa admin panelinde olabiliriz
        is_admin_panel = (tenant is None)
    
    # Root admin kontrolü
    is_root_admin = False
    all_tenants = []
    
    if request.user.is_authenticated:
        try:
            from apps.users.utils import is_root_admin as check_root_admin
            is_root_admin = check_root_admin(request.user)
        except:
            pass
        
        # Root admin ise tüm tenant'ları göster
        if is_root_admin:
            all_tenants = Tenant.objects.filter(is_active=True).order_by('name')
        # Normal kullanıcı ise sadece kendi tenant'ını göster
        elif hasattr(request.user, 'tenant') and request.user.tenant:
            all_tenants = [request.user.tenant]
    
    return {
        'tenant': tenant,
        'is_root_admin': is_root_admin,
        'all_tenants': all_tenants,
        'is_admin_panel': is_admin_panel
    }