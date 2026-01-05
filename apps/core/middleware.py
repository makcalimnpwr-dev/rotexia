"""
Multi-Tenancy Middleware
Her request'te tenant bilgisini otomatik olarak ayarlar
"""
from django.utils.deprecation import MiddlewareMixin
from django.db.utils import OperationalError, ProgrammingError
from .models import Tenant


class TenantMiddleware(MiddlewareMixin):
    """
    Subdomain-based Multi-Tenancy Middleware
    
    Production: Subdomain bazlı tenant belirleme (firma1.fieldops.com)
    Development: Session bazlı tenant belirleme (localhost:8000)
    """
    
    def process_request(self, request):
        # Allow Render health checks to bypass
        if request.path.startswith("/healthz"):
            request.tenant = None
            return None

        # If DB is not ready, do not break the app
        try:
            _ = Tenant.objects.all()[:1]
        except (OperationalError, ProgrammingError):
            request.tenant = None
            return None

        # Admin panel kontrolü - Admin panelindeyken tenant yüklenmemeli
        is_admin_panel_path = (
            request.path.startswith('/admin-home') or
            request.path.startswith('/admin/') or
            request.path.startswith('/admin-panel/') or
            request.path.startswith('/admin-login') or
            'admin_mode=1' in request.GET or
            'admin_mode=1' in request.META.get('QUERY_STRING', '')
        )
        
        host = request.get_host()
        host_without_port = host.split(':')[0] if ':' in host else host
        
        # Subdomain kontrolü
        has_subdomain = '.' in host_without_port and host_without_port not in ['127.0.0.1', 'localhost']
        
        if has_subdomain:
            parts = host_without_port.split('.')
            subdomain = parts[0].lower()
            
            # Admin paneli için özel subdomain kontrolü
            if subdomain == 'admin':
                # Admin panelindeyken session'daki tenant bilgilerini temizle
                for key in ['tenant_id', 'connect_tenant_id', 'connect_tenant_slug', 'connect_tenant_color', 'connect_tenant_name', 'admin_from_panel']:
                    request.session.pop(key, None)
                request.tenant = None
                return None
            
            # Diğer subdomain'ler için tenant bul
            if subdomain not in ['www', 'api']:
                try:
                    tenant = Tenant.objects.get(slug=subdomain, is_active=True)
                    request.tenant = tenant
                    return None
                except Tenant.DoesNotExist:
                    request.tenant = None
                    return None
        
        # Admin panel path'indeyse tenant yükleme ve session temizleme
        if is_admin_panel_path:
            # Admin panelindeyken session'daki tenant bilgilerini temizle
            for key in ['tenant_id', 'connect_tenant_id', 'connect_tenant_slug', 'connect_tenant_color', 'connect_tenant_name', 'admin_from_panel']:
                request.session.pop(key, None)
            request.tenant = None
            return None
        
        # Development modu (localhost) - Session'dan tenant yükle
        # Sadece admin panelinde değilsek session'dan tenant yükle
        # Root admin ise ve admin panelindeyse tenant yüklenmemeli
        is_root_admin_user = False
        if request.user.is_authenticated:
            try:
                from apps.users.utils import is_root_admin
                is_root_admin_user = is_root_admin(request.user)
            except:
                pass
        
        # Root admin ise ve admin panelindeyse (veya admin panelinden geliyorsa) tenant yüklenmemeli
        if is_root_admin_user:
            # Admin panel path'lerinde zaten tenant yüklenmiyor (yukarıda kontrol edildi)
            # Ama root admin normal view'lara giderse de tenant yüklenmemeli
            # Sadece admin panelinden bağlanıldıysa (admin_from_panel=True) tenant yüklensin
            admin_from_panel = request.session.get('admin_from_panel', False)
            if not admin_from_panel:
                # Root admin admin panelindeyken normal view'lara giderse tenant yüklenmemeli
                # Session'daki tenant bilgilerini temizle
                for key in ['tenant_id', 'connect_tenant_id', 'connect_tenant_slug', 'connect_tenant_color', 'connect_tenant_name']:
                    request.session.pop(key, None)
                request.tenant = None
                return None
        
        tenant_id = request.session.get('tenant_id') or request.session.get('connect_tenant_id')
        
        if tenant_id:
            try:
                tenant = Tenant.objects.get(id=tenant_id, is_active=True)
                request.tenant = tenant
            except Tenant.DoesNotExist:
                request.session.pop('tenant_id', None)
                request.session.pop('connect_tenant_id', None)
                request.tenant = None
        else:
            request.tenant = None
        
        return None
