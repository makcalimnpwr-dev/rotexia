"""
Multi-Tenancy Middleware
Her request'te tenant bilgisini otomatik olarak ayarlar
"""
from django.utils.deprecation import MiddlewareMixin
from django.db.utils import OperationalError, ProgrammingError
from .models import Tenant


class TenantMiddleware(MiddlewareMixin):
    """
    Subdomain-only Multi-Tenancy Middleware
    Sadece subdomain bazlı tenant belirleme yapar.
    
    Tenant belirleme yöntemi:
    1. Subdomain: tenant1.fieldops.com -> tenant slug: "tenant1"
       - admin.fieldops.com -> Admin paneli (tenant=None)
       - firma1.fieldops.com -> Tenant bulunur (slug="firma1")
    
    Development'ta localhost için:
    - admin.localhost:8000 -> Admin paneli
    - firma1.localhost:8000 -> Tenant bulunur
    - localhost:8000 (subdomain yok) -> Admin paneline yönlendirilir (root admin için)
    """
    
    def process_request(self, request):
        # Allow Render health checks (and other infra checks) to bypass tenancy/DB calls.
        # This prevents startup loops before migrations are applied.
        if request.path.startswith("/healthz"):
            request.tenant = None
            return None

        # If DB is not ready (migrations not applied yet), do not break the whole app.
        # Render will still be able to serve pages and we can run migrations from Shell.
        try:
            _ = Tenant.objects.all()[:1]
        except (OperationalError, ProgrammingError):
            request.tenant = None
            return None

        tenant = None
        host = request.get_host()
        
        # Subdomain çıkarma (localhost:8000 veya firma1.fieldops.com)
        host_without_port = host.split(':')[0] if ':' in host else host
        
        # Subdomain kontrolü (nokta varsa subdomain var demektir)
        if '.' in host_without_port:
            parts = host_without_port.split('.')
            subdomain = parts[0].lower()  # Küçük harfe çevir
            
            # Admin paneli için özel subdomain kontrolü
            if subdomain == 'admin':
                request.tenant = None
                # Session temizle (subdomain-only mod)
                if 'tenant_id' in request.session:
                    del request.session['tenant_id']
                if 'admin_panel_mode' in request.session:
                    del request.session['admin_panel_mode']
                return None
            
            # Diğer subdomain'ler için tenant bul
            if subdomain not in ['www', 'api']:
                try:
                    tenant = Tenant.objects.get(slug=subdomain, is_active=True)
                    # Session temizle (subdomain-only mod, session kullanmıyoruz)
                    if 'tenant_id' in request.session:
                        del request.session['tenant_id']
                    if 'admin_panel_mode' in request.session:
                        del request.session['admin_panel_mode']
                except Tenant.DoesNotExist:
                    # Subdomain var ama tenant bulunamadı - 404 benzeri durum
                    # View'da handle edilecek
                    tenant = None
        else:
            # Subdomain yok (localhost veya IP adresi - development)
            # Development modunda session'dan tenant_id'yi oku (admin panelinden bağlanıldıysa)
            tenant_id = request.session.get('tenant_id')
            admin_from_panel = request.session.get('admin_from_panel', False)
            
            if tenant_id and admin_from_panel:
                # Admin panelinden bağlanıldıysa, session'dan tenant'ı al
                try:
                    tenant = Tenant.objects.get(id=tenant_id, is_active=True)
                except Tenant.DoesNotExist:
                    # Geçersiz tenant_id, session'dan temizle
                    for key in ['tenant_id', 'admin_from_panel', 'connect_tenant_id', 'connect_tenant_slug', 'connect_tenant_color', 'connect_tenant_name']:
                        request.session.pop(key, None)
                    tenant = None
            else:
                # Normal durumda (subdomain-only mod)
                tenant = None
                # Session temizle (subdomain-only mod) - sadece admin_from_panel yoksa
                if not admin_from_panel and 'tenant_id' in request.session:
                    del request.session['tenant_id']
        
        # Request'e ekle
        request.tenant = tenant
        
        return None

