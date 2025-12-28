"""
Multi-Tenancy Middleware
Her request'te tenant bilgisini otomatik olarak ayarlar
"""
from django.utils.deprecation import MiddlewareMixin
from .models import Tenant


class TenantMiddleware(MiddlewareMixin):
    """
    Request'ten tenant bilgisini çıkarır ve request.tenant'a ekler
    
    Tenant belirleme yöntemleri (öncelik sırasına göre):
    1. Subdomain: tenant1.fieldops.com -> tenant slug: "tenant1"
    2. URL parametresi: ?tenant=tenant1
    3. Session: Daha önce seçilmiş tenant
    4. User'ın varsayılan tenant'ı (ilk oluşturduğu)
    """
    
    def process_request(self, request):
        # Allow Render health checks (and other infra checks) to bypass tenancy/DB calls.
        # This prevents startup loops before migrations are applied.
        if request.path.startswith("/healthz"):
            request.tenant = None
            return None

        tenant = None
        
        # 1. Subdomain kontrolü (production'da)
        host = request.get_host()
        if '.' in host:
            subdomain = host.split('.')[0]
            if subdomain not in ['www', 'admin', 'api']:
                try:
                    tenant = Tenant.objects.get(slug=subdomain, is_active=True)
                except Tenant.DoesNotExist:
                    pass
        
        # 2. URL parametresi (?tenant=slug)
        if not tenant and 'tenant' in request.GET:
            tenant_slug = request.GET.get('tenant')
            try:
                tenant = Tenant.objects.get(slug=tenant_slug, is_active=True)
                # Session'a kaydet
                request.session['tenant_id'] = tenant.id
            except Tenant.DoesNotExist:
                pass
        
        # 3. Session'dan al
        if not tenant and 'tenant_id' in request.session:
            try:
                tenant = Tenant.objects.get(
                    id=request.session['tenant_id'],
                    is_active=True
                )
            except Tenant.DoesNotExist:
                # Geçersiz tenant_id, session'dan temizle
                del request.session['tenant_id']
        
        # 4. User'ın varsayılan tenant'ı (eğer giriş yapmışsa)
        if not tenant and request.user.is_authenticated:
            # User modeline tenant ilişkisi eklenmeli (gelecekte)
            # Şimdilik ilk aktif tenant'ı al (geliştirme için)
            tenant = Tenant.objects.filter(is_active=True).first()
        
        # Request'e ekle
        request.tenant = tenant
        
        # Eğer tenant yoksa ve admin sayfası değilse, hata ver
        # (Admin sayfasında tenant zorunlu değil - superuser için)
        if not tenant and not request.path.startswith('/admin/'):
            # İlk çalıştırmada tenant yoksa, varsayılan oluştur
            if Tenant.objects.count() == 0:
                from .models import Plan
                # Varsayılan plan oluştur
                default_plan, _ = Plan.objects.get_or_create(
                    name="Ücretsiz Plan",
                    defaults={
                        'plan_type': 'basic',
                        'price_monthly': 0,
                        'max_users': 3,
                        'max_customers': 20,
                        'max_tasks_per_month': 100,
                    }
                )
                # Varsayılan tenant oluştur
                tenant = Tenant.objects.create(
                    name="Varsayılan Şirket",
                    slug="default",
                    email="admin@example.com",
                    plan=default_plan,
                    is_active=True
                )
                request.tenant = tenant
        
        return None

