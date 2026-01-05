"""
Tenant filtering utilities for multi-tenancy support
"""
from django.db.models import QuerySet
from .models import Tenant


def get_current_tenant(request):
    """
    Request'ten mevcut tenant'ı alır.
    Root admin bile olsa, session'daki tenant'ı döner.
    Tenant yoksa None döner (güvenlik için).
    
    Admin panel modunda ise None döner (tüm veriler görülebilir).
    Root admin ve admin panelindeyse tenant yüklenmez.
    """
    # Admin panel modunda ise tenant yok
    if request.session.get('admin_panel_mode', False):
        return None
    
    # Admin panel path kontrolü
    is_admin_panel_path = (
        request.path.startswith('/admin-home') or
        request.path.startswith('/admin/') or
        request.path.startswith('/admin-panel/') or
        request.path.startswith('/admin-login') or
        'admin_mode=1' in request.GET or
        'admin_mode=1' in request.META.get('QUERY_STRING', '')
    )
    
    # Root admin kontrolü - Admin panelindeyse tenant yüklenmemeli
    if request.user.is_authenticated:
        try:
            from apps.users.utils import is_root_admin
            if is_root_admin(request.user) and is_admin_panel_path:
                return None
            # Root admin ise ve admin panelinden bağlanılmadıysa tenant yüklenmemeli
            if is_root_admin(request.user):
                admin_from_panel = request.session.get('admin_from_panel', False)
                if not admin_from_panel and not request.path.startswith('/admin-home'):
                    # Root admin admin panelindeyken normal view'lara giderse tenant yüklenmemeli
                    return None
        except:
            pass
    
    # Önce request.tenant'ı kontrol et (middleware'den gelmiş olabilir)
    if hasattr(request, 'tenant') and request.tenant:
        # Session'a da kaydet (tutarlılık için)
        request.session['tenant_id'] = request.tenant.id
        return request.tenant
    
    # Session'dan tenant al
    tenant = None
    if 'tenant_id' in request.session:
        try:
            tenant = Tenant.objects.get(id=request.session['tenant_id'], is_active=True)
        except Tenant.DoesNotExist:
            del request.session['tenant_id']
    
    # Eğer tenant yoksa ve kullanıcı giriş yapmışsa, kullanıcının tenant'ını al
    if not tenant and request.user.is_authenticated:
        # Kullanıcının tenant'ına bak
        if hasattr(request.user, 'tenant') and request.user.tenant:
            tenant = request.user.tenant
            request.session['tenant_id'] = tenant.id
    
    # Root admin için otomatik tenant seçimi YAPILMAMALI
    # Sadece normal kullanıcılar için ilk aktif tenant'ı al
    if not tenant and request.user.is_authenticated:
        try:
            from apps.users.utils import is_root_admin
            if not is_root_admin(request.user):
                # Normal kullanıcı için ilk aktif tenant'ı al (sadece geliştirme için)
                tenant = Tenant.objects.filter(is_active=True).first()
                if tenant:
                    request.session['tenant_id'] = tenant.id
        except:
            pass
    
    return tenant


def filter_by_tenant(queryset: QuerySet, request):
    """
    QuerySet'i mevcut tenant'a göre filtreler.
    Root admin bile olsa, session'daki tenant'a göre filtreleme yapar.
    Bu sayede firmalar arası veri karışması engellenir.
    
    Admin panel modunda ise, tenant filtresi uygulanmaz (tüm veriler görülebilir).
    """
    # Admin panel modunda ise filtreleme yapma (tüm veriler görülebilir)
    if request.session.get('admin_panel_mode', False):
        # Admin panelinde tüm tenant'ların verilerini göster
        return queryset
    
    tenant = get_current_tenant(request)
    
    # Tenant yoksa boş queryset döndür (güvenlik - veri karışmasını önler)
    if tenant is None:
        return queryset.none()
    
    # Tenant alanı varsa filtrele
    if hasattr(queryset.model, 'tenant'):
        return queryset.filter(tenant=tenant)
    
    return queryset


def set_tenant_on_save(instance, request):
    """
    Model instance'a tenant'ı otomatik ekler.
    Root admin bile olsa, session'daki tenant'a göre ayarlar.
    Bu sayede veriler doğru tenant'a kaydedilir.
    """
    tenant = get_current_tenant(request)
    
    # Tenant alanı varsa mutlaka ekle (null olamaz, veri karışmasını önler)
    if tenant and hasattr(instance, 'tenant'):
        instance.tenant = tenant
    elif hasattr(instance, 'tenant') and not instance.tenant:
        # Eğer tenant yoksa ve alan varsa, hata ver (güvenlik)
        if not tenant:
            from django.core.exceptions import ValidationError
            raise ValidationError("Tenant bilgisi bulunamadı. Lütfen bir firma seçin.")
    
    return instance


def require_tenant_for_action(request, instance=None):
    """
    Bir işlem yapmadan önce tenant kontrolü yapar.
    Root admin bile olsa, session'daki tenant ile işlem yapmalı.
    """
    tenant = get_current_tenant(request)
    if not tenant:
        return False
    
    # Instance varsa tenant kontrolü yap (root admin bile başka tenant'ın verisini değiştirmemeli)
    if instance and hasattr(instance, 'tenant'):
        if instance.tenant != tenant:
            return False
    
    return True
