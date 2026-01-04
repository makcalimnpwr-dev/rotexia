from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, get_user_model, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import models
from django.core.files.base import ContentFile
from django.conf import settings
from .models import SystemSetting, Tenant
# VisitTask modelini doğru adresten çağırıyoruz:
from apps.field_operations.models import VisitTask
from .utils import calculate_distance
from datetime import date
import json
from django.db.models import Count, Q as DQ
from django.http import HttpResponseForbidden
from django.http import HttpResponse
from apps.users.hierarchy_access import get_hierarchy_scope_for_user
from apps.users.utils import ensure_root_admin_configured, get_assigned_user_ids_under_admin_node, is_root_admin
from apps.users.decorators import root_admin_required
from apps.users.models import UserRole, CustomUser


# Gerekli Modeller
from apps.field_operations.models import VisitTask
from apps.customers.models import Customer
from apps.forms.models import Survey, SurveyAnswer, Question

from .models import SystemSetting

def init_default_settings():
    """Sistemde hiç ayar yoksa varsayılanları oluşturur."""
    defaults = [
        # --- GENEL AYARLAR ---
        {
            'key': 'app_sync_interval',
            'label': 'Mobil Senkronizasyon Süresi (Dakika)',
            'value': '15',
            'category': 'general',
            'input_type': 'number',
            'description': 'Mobil uygulamanın sunucudan yeni verileri çekme sıklığı.'
        },
        {
            'key': 'maintenance_mode',
            'label': 'Bakım Modu',
            'value': 'False',
            'category': 'general',
            'input_type': 'bool',
            'description': 'Açılırsa sadece yöneticiler sisteme girebilir.'
        },
        
        # --- ZİYARET AYARLARI ---
        {
            'key': 'visit_radius',
            'label': 'Mağaza Giriş Mesafesi (Metre)',
            'value': '300', # 300 metre
            'category': 'visit',
            'input_type': 'number',
            'description': 'Personel mağazaya en fazla ne kadar uzaktayken ziyaret başlatabilir?'
        },
        {
            'key': 'distance_rule',
            'label': 'Mesafe Kuralı',
            'value': 'True',
            'category': 'visit',
            'input_type': 'bool',
            'description': 'Açık: Giriş mesafesi ve gezinme mesafesi kontrolü yapılır. Kapalı: Mesafe kontrolü yapılmaz, herhangi bir mesafeden ziyaret başlatılabilir.'
        },
        {
            'key': 'wander_radius',
            'label': 'Gezinme Sınırı (Metre)',
            'value': '500',
            'category': 'visit',
            'input_type': 'number',
            'description': 'Ziyaret sırasında mağaza konumundan maksimum uzaklaşma mesafesi. Bu mesafeyi aşarsa ziyaret otomatik bitirilir.'
        },
    ]

    for setting in defaults:
        # Eğer bu ayar veritabanında yoksa oluştur
        if not SystemSetting.objects.filter(key=setting['key']).exists():
            SystemSetting.objects.create(**setting)

# --- OTOMATİK GİRİŞ ---
def auto_login(request):
    User = get_user_model()
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        user = User.objects.first()
    
    if user:
        if not user.is_active:
            user.is_active = True
            user.save()
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect('home')
    else:
        return render(request, 'base.html', {'content': 'Kullanıcı yok...'})
    

from .models import SystemSetting

@login_required
def settings_home(request):
    """
    Ayarlar sayfası - Admin paneli veya firma paneli
    Subdomain-only mod: request.tenant'a göre yönlendirir
    """
    # Middleware'den gelen tenant bilgisini kontrol et (subdomain-only mod)
    tenant = getattr(request, 'tenant', None)
    
    # Development modunda session'dan tenant al
    if not tenant:
        tenant_id = request.session.get('tenant_id') or request.session.get('connect_tenant_id')
        if tenant_id:
            try:
                tenant = Tenant.objects.get(id=tenant_id, is_active=True)
                request.tenant = tenant
            except Tenant.DoesNotExist:
                pass
    
    host = request.get_host()
    host_without_port = host.split(':')[0] if ':' in host else host
    
    # Subdomain kontrolü
    is_admin_subdomain = False
    if '.' in host_without_port and host_without_port not in ['127.0.0.1', 'localhost']:
        parts = host_without_port.split('.')
        subdomain = parts[0].lower()
        is_admin_subdomain = (subdomain == 'admin')
    
    # Admin subdomain'inde veya tenant yoksa -> admin ayarları
    admin_from_panel = request.session.get('admin_from_panel', False)
    if is_admin_subdomain or (not tenant and not admin_from_panel):
        if is_root_admin(request.user):
            return redirect('admin_settings')
        else:
            messages.error(request, 'Admin paneline erişim yetkiniz yok.')
            return redirect('home')
    
    # Firma subdomain'inde ve tenant var -> firma ayarları
    if tenant:
        return redirect('tenant_settings')
    
    # Fallback
    messages.warning(request, 'Ayarlar sayfasına erişilemedi.')
    return redirect('home')

@login_required
@root_admin_required
def admin_settings(request):
    """
    Admin Paneli Ayarları - Global/Şablon ayarlar
    Burada eklenen içerikler firmalara otomatik aktarılmaz
    Subdomain-only mod: Sadece admin.fieldops.com'dan erişilmeli
    """
    # Admin panelinde tenant olmamalı
    request.tenant = None
    
    # Subdomain kontrolü - admin subdomain'inde miyiz?
    host = request.get_host()
    host_without_port = host.split(':')[0] if ':' in host else host
    is_admin_subdomain = False
    if '.' in host_without_port:
        parts = host_without_port.split('.')
        subdomain = parts[0].lower()
        is_admin_subdomain = (subdomain == 'admin')
    
    # Admin subdomain'inde değilsek ve subdomain varsa, uyarı ver
    if not is_admin_subdomain and '.' in host_without_port:
        # Firma subdomain'indeyiz, admin ayarlarına erişim yok
        messages.warning(request, 'Admin ayarlarına sadece admin subdomain\'inden erişebilirsiniz.')
        # Firma subdomain'ine geri dön
        tenant = getattr(request, 'tenant', None)
        if tenant:
            if settings.DEBUG:
                return redirect(f"http://{tenant.slug}.localhost:8000/tenant/settings/")
            else:
                domain = getattr(settings, 'SUBDOMAIN_DOMAIN', 'fieldops.com')
                protocol = 'https' if not settings.DEBUG else 'http'
                return redirect(f"{protocol}://{tenant.slug}.{domain}/tenant/settings/")
    
    # --- POST İŞLEMLERİ ---
    if request.method == 'POST':
        # Handle role add/delete (tenant=None - admin paneli için global roller)
        if 'add_role' in request.POST:
            role_name = request.POST.get('role_name', '').strip()
            if role_name:
                # Admin panelinde tenant=None ile oluştur
                if not UserRole.objects.filter(name=role_name, tenant__isnull=True).exists():
                    UserRole.objects.create(name=role_name, tenant=None)
                    messages.success(request, f'✅ Rol "{role_name}" eklendi (Global Şablon).')
                else:
                    messages.warning(request, f'⚠️ Rol "{role_name}" zaten mevcut.')
            else:
                messages.error(request, '❌ Rol adı boş olamaz.')
        elif 'delete_role' in request.POST:
            role_id = request.POST.get('role_id')
            if role_id:
                try:
                    # Sadece tenant=None olan rolleri sil (admin paneli rolleri)
                    role = UserRole.objects.get(id=role_id, tenant__isnull=True)
                    role_name = role.name
                    role.delete()
                    messages.success(request, f'✅ Rol "{role_name}" silindi.')
                except UserRole.DoesNotExist:
                    messages.error(request, '❌ Rol bulunamadı veya bu rol silinemez.')
        
        # Handle regular settings update (global ayarlar)
        all_settings = SystemSetting.objects.all()
        for setting in all_settings:
            if setting.input_type == 'bool':
                new_val = 'True' if request.POST.get(setting.key) == 'on' else 'False'
            else:
                new_val = request.POST.get(setting.key)
            
            if new_val is not None:
                setting.value = new_val
                setting.save()
        
        if 'add_role' not in request.POST and 'delete_role' not in request.POST:
            messages.success(request, '✅ Ayarlar kaydedildi.')
        return redirect('admin_settings')
    
    # --- VERİLERİ ÇEK (TENANT=None - GLOBAL) ---
    settings_general = SystemSetting.objects.filter(category='general')
    settings_visit = SystemSetting.objects.filter(category='visit')
    settings_user = SystemSetting.objects.filter(category='user')
    # Admin panelinde sadece tenant=None olan rolleri göster (global şablonlar)
    user_roles = UserRole.objects.filter(tenant__isnull=True).order_by('name')

    context = {
        'is_admin_panel': True,
        'settings_general': settings_general,
        'settings_visit': settings_visit,
        'settings_user': settings_user,
        'user_roles': user_roles,
    }
    return render(request, 'apps/Core/settings.html', context)

@login_required
def tenant_settings(request):
    """
    Firma Paneli Ayarları - Tenant-specific ayarlar
    Sadece seçili firmanın kendi ayarları görünür
    """
    from apps.core.tenant_utils import get_current_tenant, filter_by_tenant
    from apps.core.models import Tenant
    
    # Önce request.tenant'ı kontrol et (middleware'den)
    tenant = getattr(request, 'tenant', None)
    
    # Eğer request.tenant yoksa, session'dan al (development modu için)
    if not tenant:
        tenant_id = request.session.get('tenant_id') or request.session.get('connect_tenant_id')
        if tenant_id:
            try:
                tenant = Tenant.objects.get(id=tenant_id, is_active=True)
                # Request'e de ekle (middleware için)
                request.tenant = tenant
            except Tenant.DoesNotExist:
                request.session.pop('tenant_id', None)
                request.session.pop('connect_tenant_id', None)
                tenant = None
    
    # Hala tenant yoksa, get_current_tenant'ı kullan (fallback)
    if not tenant:
        tenant = get_current_tenant(request)
        if tenant:
            request.tenant = tenant
    
    if not tenant:
        messages.error(request, '❌ Firma seçimi yapılmamış! Lütfen üst menüden bir firma seçin.')
        return redirect('home')
    
    # --- POST İŞLEMLERİ ---
    if request.method == 'POST':
        from apps.core.tenant_utils import set_tenant_on_save
        
        # Handle role add/delete (tenant-specific)
        if 'add_role' in request.POST:
            role_name = request.POST.get('role_name', '').strip()
            if role_name:
                # DEBUG: Tenant bilgisini kontrol et ve logla
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"DEBUG tenant_settings: tenant={tenant}, tenant_id={tenant.id if tenant else None}, tenant_name={tenant.name if tenant else None}")
                logger.error(f"DEBUG session: tenant_id={request.session.get('tenant_id', 'YOK')}")
                logger.error(f"DEBUG request.tenant: {getattr(request, 'tenant', 'YOK')}")
                
                if not tenant:
                    messages.error(request, '❌ Firma seçimi bulunamadı! Rol eklenemedi. Lütfen üst menüden bir firma seçin.')
                    return redirect('tenant_settings')
                
                # Bu firmanın rolleri arasında kontrol et
                existing_role = UserRole.objects.filter(name=role_name, tenant=tenant).first()
                if not existing_role:
                    # Tenant'ı direkt ata - MUTLAKA tenant_id ile
                    role = UserRole(name=role_name, tenant_id=tenant.id)  # tenant_id kullan
                    role.save()
                    
                    # DEBUG: Kayıt kontrolü - refresh from DB
                    role.refresh_from_db()
                    if role.tenant_id != tenant.id:
                        logger.error(f"DEBUG: Rol kaydedildi ama tenant yanlış! role.tenant_id={role.tenant_id}, tenant.id={tenant.id}")
                        messages.error(request, f'❌ Rol kaydedilirken hata oluştu! Tenant: {role.tenant_id} != {tenant.id}')
                    else:
                        logger.error(f"DEBUG: Rol başarıyla kaydedildi! role.tenant_id={role.tenant_id}, tenant.id={tenant.id}")
                        messages.success(request, f'✅ Rol "{role_name}" "{tenant.name}" firmasına eklendi.')
                else:
                    messages.warning(request, f'⚠️ Rol "{role_name}" bu firmada zaten mevcut.')
            else:
                messages.error(request, '❌ Rol adı boş olamaz.')
        elif 'delete_role' in request.POST:
            role_id = request.POST.get('role_id')
            if role_id:
                try:
                    # Sadece bu firmanın rollerini sil
                    role = get_object_or_404(filter_by_tenant(UserRole.objects.all(), request), id=role_id)
                    role_name = role.name
                    role.delete()
                    messages.success(request, f'✅ Rol "{role_name}" silindi.')
                except:
                    messages.error(request, '❌ Rol bulunamadı veya bu rol silinemez.')
        
        # Handle regular settings update (tenant-specific)
        all_settings = filter_by_tenant(SystemSetting.objects.all(), request)
        for setting in all_settings:
            if setting.input_type == 'bool':
                new_val = 'True' if request.POST.get(setting.key) == 'on' else 'False'
            else:
                new_val = request.POST.get(setting.key)
            
            if new_val is not None:
                setting.value = new_val
                setting.save()
        
        if 'add_role' not in request.POST and 'delete_role' not in request.POST:
            messages.success(request, '✅ Ayarlar kaydedildi.')
        return redirect('tenant_settings')
    
    # --- VERİLERİ ÇEK (TENANT-SPECIFIC) ---
    settings_general = filter_by_tenant(SystemSetting.objects.filter(category='general'), request)
    settings_visit = filter_by_tenant(SystemSetting.objects.filter(category='visit'), request)
    settings_user = filter_by_tenant(SystemSetting.objects.filter(category='user'), request)
    # Sadece bu firmanın rolleri
    user_roles = filter_by_tenant(UserRole.objects.all(), request).order_by('name')

    context = {
        'is_admin_panel': False,
        'tenant': tenant,
        'settings_general': settings_general,
        'settings_visit': settings_visit,
        'settings_user': settings_user,
        'user_roles': user_roles,
    }
    return render(request, 'apps/Core/settings.html', context)

# Eğer eski require_gps ayarı varsa, distance_rule olarak güncelle (migration helper)
def migrate_old_settings():
    old_require_gps = SystemSetting.objects.filter(key='require_gps').first()
    if old_require_gps:
        # Yeni ayar zaten var mı kontrol et
        if not SystemSetting.objects.filter(key='distance_rule').exists():
            # Eski ayarı yeni isimle güncelle
            old_require_gps.key = 'distance_rule'
            old_require_gps.label = 'Mesafe Kuralı'
            old_require_gps.description = 'Açık: Giriş mesafesi ve gezinme mesafesi kontrolü yapılır. Kapalı: Mesafe kontrolü yapılmaz, herhangi bir mesafeden ziyaret başlatılabilir.'
            old_require_gps.save()
        else:
            # Yeni ayar zaten varsa, eski ayarı sil
            old_require_gps.delete()
    
    # CASUS KOD BAŞLANGICI
    print("----------------------------------------")
    print("👀 VIEW ÇALIŞIYOR - KONTROL ZAMANI")
    all_count = SystemSetting.objects.count()
    visit_count = SystemSetting.objects.filter(category='visit').count()
    print(f"Toplam Kayıt: {all_count}")
    print(f"Ziyaret Kategorisi Sayısı: {visit_count}")
    
    # Verileri ekrana da basalım
    for s in SystemSetting.objects.all():
        print(f" -> Kayıt: {s.key} | Kategori: '{s.category}'")
    print("----------------------------------------")
    # CASUS KOD BİTİŞİ

    # --- 3. VERİLERİ ÇEK ---
    settings_general = SystemSetting.objects.filter(category='general')
    settings_visit = SystemSetting.objects.filter(category='visit')
    settings_user = SystemSetting.objects.filter(category='user')
    user_roles = UserRole.objects.all().order_by('name')

    context = {
        'settings_general': settings_general,
        'settings_visit': settings_visit,
        'settings_user': settings_user,
        'user_roles': user_roles,
    }
    return render(request, 'apps/Core/settings.html', context)

# --- AKILLI ANASAYFA ---
def index(request):
    """Ana sayfa - Firma adı girme ekranı (PUBLIC - Herkes erişebilir)"""
    # Eğer kullanıcı zaten giriş yapmışsa, root admin ise admin_home'a, değilse logout yap
    if request.user.is_authenticated:
        from apps.users.utils import is_root_admin
        if is_root_admin(request.user):
            return redirect('admin_home')
        else:
            # Normal kullanıcı için subdomain gerekli - logout yapıp ana sayfayı göster
            from django.contrib.auth import logout
            logout(request)
    
    return render(request, 'index.html')

def company_connect(request):
    """Firma adı girildikten sonra, firmanın login sayfasına yönlendir"""
    if request.method == 'POST':
        company_name = request.POST.get('company_name', '').strip()
        
        if not company_name:
            messages.error(request, 'Lütfen firma adı girin.')
            return redirect('index')
        
        # "Rotexia" yazıldıysa admin login'e yönlendir
        if company_name.lower() == 'rotexia':
            return redirect('admin_login')
        
        # Firma adından tenant'ı bul
        from django.utils.text import slugify
        slug = slugify(company_name)
        
        try:
            tenant = Tenant.objects.filter(
                models.Q(slug=slug) | models.Q(name__iexact=company_name),
                is_active=True
            ).first()
            
            if not tenant:
                messages.error(request, f'"{company_name}" adında bir firma bulunamadı.')
                return redirect('index')
            
            # Firma bilgilerini session'a kaydet (login sayfasında kullanılacak)
            request.session['connect_tenant_id'] = tenant.id
            request.session['connect_tenant_slug'] = tenant.slug
            request.session['connect_tenant_color'] = tenant.primary_color
            request.session['connect_tenant_name'] = tenant.name
            
            # Login sayfasına yönlendir (CustomLoginView tenant bilgisini session'dan alacak)
            return redirect('login')
            
        except Exception as e:
            messages.error(request, f'Firma bulunurken hata oluştu: {str(e)}')
            return redirect('index')
    
    return redirect('index')

def login_with_tenant(request, tenant_slug):
    """Firma rengine göre dinamik login sayfası - Legacy support, ana sayfaya yönlendir"""
    # Bu URL artık kullanılmıyor, önce ana sayfaya gitmesi gerekiyor
    try:
        tenant = Tenant.objects.get(slug=tenant_slug, is_active=True)
        # Session'a tenant bilgilerini kaydet
        request.session['connect_tenant_id'] = tenant.id
        request.session['connect_tenant_slug'] = tenant.slug
        request.session['connect_tenant_color'] = tenant.primary_color
        request.session['connect_tenant_name'] = tenant.name
        # Login sayfasına yönlendir
        return redirect('login')
    except Tenant.DoesNotExist:
        messages.error(request, 'Firma bulunamadı.')
        return redirect('index')

def home(request):
    """
    Dashboard sayfası - Development'ta session bazlı, production'da subdomain bazlı
    
    Development: localhost:8000 -> Session'dan tenant bilgisi alınır
    Production: firma1.fieldops.com -> Middleware'den tenant bilgisi gelir
    """
    # MANUEL GİRİŞ KONTROLÜ - Her zaman giriş yapılması gerekiyor
    if not request.user.is_authenticated:
        messages.error(request, 'Lütfen giriş yapın.')
        return redirect('index')
    
    # Önce middleware'den gelen tenant bilgisini kontrol et
    tenant = getattr(request, 'tenant', None)
    host = request.get_host()
    host_without_port = host.split(':')[0] if ':' in host else host
    
    # Subdomain kontrolü (127.0.0.1 veya localhost gibi durumlar için)
    has_subdomain = '.' in host_without_port and host_without_port not in ['127.0.0.1', 'localhost']
    subdomain = None
    if has_subdomain:
        parts = host_without_port.split('.')
        subdomain = parts[0].lower()
    
    # Root admin kontrolü - Admin panelinden bağlanıldıysa tenant paneline git
    admin_from_panel = request.session.get('admin_from_panel', False)
    if is_root_admin(request.user) and not admin_from_panel:
        # Admin panelinden bağlanılmadıysa, root admin'i admin paneline yönlendir
        if subdomain == 'admin':
            return redirect('admin_home')
        if not has_subdomain:
            return redirect('admin_home')
    
    # Tenant'ı middleware'den al (subdomain veya session'dan)
    tenant = getattr(request, 'tenant', None)
    
    # Subdomain yoksa (development - localhost:8000 veya 127.0.0.1:8000)
    if not has_subdomain:
        # Middleware zaten session'dan tenant'ı okumuş olmalı
        # Ama eğer okumadıysa, session'dan tekrar oku
        if not tenant:
            tenant_id = request.session.get('tenant_id') or request.session.get('connect_tenant_id')
            if tenant_id:
                try:
                    tenant = Tenant.objects.get(id=tenant_id, is_active=True)
                    request.tenant = tenant  # Request'e ekle
                except Tenant.DoesNotExist:
                    # Geçersiz tenant_id, session'dan temizle
                    request.session.pop('tenant_id', None)
                    request.session.pop('connect_tenant_id', None)
            
            # Hala tenant yoksa ana sayfaya yönlendir
            if not tenant:
                messages.error(request, 'Firma bilgisi bulunamadı. Lütfen firma adınızı girin.')
                return redirect('index')
    
    # Subdomain var ama tenant bulunamadı
    if has_subdomain and not tenant:
        messages.error(request, f'"{subdomain}" subdomain\'i için firma bulunamadı. Lütfen admin panelinden firma oluşturun.')
        if is_root_admin(request.user):
            return redirect('admin_home')
        else:
            return redirect('index')
    
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    mobile_keywords = ['mobile', 'android', 'iphone', 'ipad', 'webos', 'ipod']
    
    is_mobile = any(keyword in user_agent for keyword in mobile_keywords)
    
    if is_mobile:
        return redirect('mobile_home')
    else:
        # MASAÜSTÜ DASHBOARD - Tenant'a göre filtrele
        from apps.core.tenant_utils import filter_by_tenant
        total_tasks = filter_by_tenant(VisitTask.objects.all(), request).count()
        completed_tasks = filter_by_tenant(VisitTask.objects.all(), request).filter(status='completed').count()
        today_tasks = filter_by_tenant(VisitTask.objects.all(), request).filter(planned_date=date.today())
        today_done = today_tasks.filter(status='completed').count()
        
        daily_performance = 0
        if today_tasks.count() > 0:
            daily_performance = int((today_done / today_tasks.count()) * 100)

        context = {
            'tenant': tenant,
            'kpi': {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'daily_performance': daily_performance,
            }
        }
        return render(request, 'apps/Core/home.html', context)


def healthz(request):
    """
    Render/healthcheck endpoint. Always returns 200.
    """
    return HttpResponse("ok", content_type="text/plain")

# --- ÖZEL GİRİŞ VIEW (Firma Adı ile) ---
from django.contrib.auth.views import LoginView
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.utils.text import slugify

@method_decorator(csrf_protect, name='dispatch')
class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    
    def get(self, request, *args, **kwargs):
        """GET request - Eğer tenant bilgisi yoksa ana sayfaya yönlendir"""
        # Session'da tenant bilgisi var mı kontrol et
        tenant_id = request.session.get('connect_tenant_id')
        tenant_slug = request.session.get('connect_tenant_slug')
        
        # Eğer tenant bilgisi yoksa, ana sayfaya (Bağlan sayfasına) yönlendir
        if not tenant_id or not tenant_slug:
            return redirect('index')
        
        # Tenant bilgisi varsa login_tenant.html template'ini kullan
        try:
            tenant = Tenant.objects.get(id=tenant_id, slug=tenant_slug, is_active=True)
            context = {
                'tenant': tenant,
                'primary_color': request.session.get('connect_tenant_color', tenant.primary_color),
            }
            return render(request, 'registration/login_tenant.html', context)
        except Tenant.DoesNotExist:
            # Tenant bulunamazsa session'ı temizle ve ana sayfaya yönlendir
            request.session.pop('connect_tenant_id', None)
            request.session.pop('connect_tenant_slug', None)
            request.session.pop('connect_tenant_color', None)
            request.session.pop('connect_tenant_name', None)
            return redirect('index')
    
    def post(self, request, *args, **kwargs):
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        # Tenant bilgisini session'dan al
        tenant_id = request.session.get('connect_tenant_id')
        tenant_slug = request.session.get('connect_tenant_slug')
        
        # Eğer session'da tenant bilgisi yoksa ana sayfaya yönlendir
        if not tenant_id or not tenant_slug:
            messages.error(request, 'Lütfen önce firma adını girin.')
            return redirect('index')
        
        # Tenant'ı bul
        try:
            tenant = Tenant.objects.get(id=tenant_id, slug=tenant_slug, is_active=True)
        except Tenant.DoesNotExist:
            messages.error(request, 'Firma bulunamadı. Lütfen tekrar deneyin.')
            request.session.pop('connect_tenant_id', None)
            request.session.pop('connect_tenant_slug', None)
            return redirect('index')
        
        # Kullanıcıyı doğrula
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_active:
            # Root admin kontrolü - root admin her tenant'a giriş yapabilir
            from apps.users.utils import is_root_admin
            
            if not is_root_admin(user):
                # Normal kullanıcı için tenant kontrolü
                # Kullanıcının tenant'ı varsa ve seçilen tenant ile eşleşmiyorsa hata ver
                if hasattr(user, 'tenant') and user.tenant:
                    if user.tenant != tenant:
                        messages.error(request, f'Bu kullanıcı "{user.tenant.name}" firmasına aittir. Lütfen doğru firmayı seçin.')
                        return self.form_invalid(self.get_form())
                else:
                    # Kullanıcının tenant'ı yoksa, seçilen tenant'ı ata (eski kullanıcılar için)
                    user.tenant = tenant
                    user.save()
                    messages.info(request, f'Kullanıcınız "{tenant.name}" firmasına atandı.')
            
            login(request, user)
            # Tenant'ı session'a kaydet
            request.session['tenant_id'] = tenant.id
            # Bağlanma session bilgilerini temizle (artık gerekli değil)
            request.session.pop('connect_tenant_id', None)
            request.session.pop('connect_tenant_slug', None)
            request.session.pop('connect_tenant_color', None)
            request.session.pop('connect_tenant_name', None)
            # Redirect URL'i belirle
            redirect_url = self.get_success_url()
            return redirect(redirect_url)
        else:
            messages.error(request, 'Kullanıcı adı veya şifre hatalı.')
            return self.form_invalid(self.get_form())
    

# --- GELİŞTİRİCİ ADMIN GİRİŞİ ---
@method_decorator(csrf_protect, name='dispatch')
class AdminLoginView(LoginView):
    template_name = 'registration/admin_login.html'
    redirect_authenticated_user = True
    
    def post(self, request, *args, **kwargs):
        """Admin girişi için firma adı gerektirmez, sadece kullanıcı adı ve şifre"""
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        # Kullanıcıyı doğrula (firma kontrolü yok)
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_active:
            login(request, user)
            # Admin girişinde tenant session'ını temizle
            if 'tenant_id' in request.session:
                del request.session['tenant_id']
            # Redirect URL'i belirle
            redirect_url = self.get_success_url()
            return redirect(redirect_url)
        else:
            messages.error(request, 'Kullanıcı adı veya şifre hatalı.')
            return self.form_invalid(self.get_form())
    
    def get_success_url(self):
        # Root admin kontrolü
        if is_root_admin(self.request.user):
            return reverse_lazy('admin_home')
        return reverse_lazy('home')

# --- LOGOUT VIEW ---
from django.contrib.auth import logout as auth_logout

def logout_view(request):
    """Logout ve session temizleme - Tenant varsa o tenant'ın login sayfasına yönlendir"""
    tenant_id = request.session.get('tenant_id')
    tenant_slug = request.session.get('connect_tenant_slug')
    tenant_name = request.session.get('connect_tenant_name')
    
    auth_logout(request)
    
    # Tenant bilgilerini temizle
    for key in ['tenant_id', 'connect_tenant_id', 'connect_tenant_slug', 'connect_tenant_color', 'connect_tenant_name', 'admin_from_panel']:
        request.session.pop(key, None)
    
    # Eğer tenant varsa, o tenant'ın login sayfasına yönlendir
    if tenant_slug:
        # Tenant bilgisini logout sonrası için sakla
        request.session['from_tenant_logout'] = True
        request.session['logout_tenant_slug'] = tenant_slug
        request.session['logout_tenant_name'] = tenant_name or 'Firma'
        
        # Login sayfasına yönlendir (tenant bilgisi session'da)
        return redirect('login')
    else:
        # Tenant yoksa direkt login sayfasına git
        return redirect('login')

# --- ADMIN AYARLARI GÜNCELLEME ---
@login_required
@root_admin_required
def admin_update_settings(request):
    """Admin kullanıcı adı ve şifre güncelleme"""
    if request.method == 'POST':
        new_username = request.POST.get('username', '').strip()
        new_password = request.POST.get('password', '').strip()
        password_confirm = request.POST.get('password_confirm', '').strip()
        
        if not new_username:
            messages.error(request, 'Kullanıcı adı boş olamaz.')
            return redirect(request.META.get('HTTP_REFERER', 'admin_home'))
        
        # Kullanıcı adı değiştir
        if new_username != request.user.username:
            # Kullanıcı adı benzersiz mi kontrol et
            from django.contrib.auth import get_user_model
            User = get_user_model()
            if User.objects.filter(username=new_username).exclude(id=request.user.id).exists():
                messages.error(request, 'Bu kullanıcı adı zaten kullanılıyor.')
                return redirect(request.META.get('HTTP_REFERER', 'admin_home'))
            request.user.username = new_username
        
        # Şifre değiştir
        if new_password:
            if new_password != password_confirm:
                messages.error(request, 'Şifreler eşleşmiyor.')
                return redirect(request.META.get('HTTP_REFERER', 'admin_home'))
            if len(new_password) < 6:
                messages.error(request, 'Şifre en az 6 karakter olmalıdır.')
                return redirect(request.META.get('HTTP_REFERER', 'admin_home'))
            request.user.set_password(new_password)
        
        request.user.save()
        messages.success(request, 'Ayarlar başarıyla güncellendi. Yeniden giriş yapmanız gerekiyor.')
        
        # Çıkış yap ve login sayfasına yönlendir
        from django.contrib.auth import logout
        logout(request)
        return redirect('login')
    
    return redirect('admin_home')

# --- GELİŞTİRİCİ ADMIN ANA SAYFA (Firma Listesi) ---
@login_required
@root_admin_required
def admin_home(request):
    """
    Root admin için firma listesi ve yönetim sayfası
    Subdomain-only mod: Bu view sadece admin.fieldops.com'dan erişilmeli
    """
    # Admin panelinde tenant olmamalı
    request.tenant = None
    
    tenants = Tenant.objects.filter(is_active=True).order_by('-created_at')
    
    context = {
        'tenants': tenants,
        'is_admin_panel': True,
        'tenant': None,
    }
    return render(request, 'apps/Core/admin_home.html', context)

# --- FİRMA DÜZENLEME ---
@login_required
@root_admin_required
def edit_tenant(request, tenant_id):
    """Firma düzenleme sayfası"""
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    # Menü ayarları için varsayılan değerler (ana menüler ve alt menüler)
    default_menus = {
        'hierarchy': True,
        'users': True,
        'customers': True,
        'tasks': True,
        'route_plan': True,
        'forms': True,
        'images': True,
        'reports': True,
        # Alt menüler
        'reports_list': True,  # Raporlar listesi
        'reports_trash': True,  # Çöp Kutusu
    }
    
    # Mevcut menu_settings yoksa varsayılan değerleri kullan
    if not tenant.menu_settings or len(tenant.menu_settings) == 0:
        tenant.menu_settings = default_menus
        tenant.save(update_fields=['menu_settings'])
    
    # Mevcut menu_settings'te eksik olan menüleri ekle (yeni menüler için)
    menu_settings_updated = tenant.menu_settings.copy()
    for key, default_value in default_menus.items():
        if key not in menu_settings_updated:
            menu_settings_updated[key] = default_value
    
    if menu_settings_updated != tenant.menu_settings:
        tenant.menu_settings = menu_settings_updated
        tenant.save(update_fields=['menu_settings'])
    
    if request.method == 'POST':
        # İsim güncelleme
        if 'name' in request.POST:
            tenant.name = request.POST.get('name', '').strip()
        
        # Renk güncelleme
        if 'primary_color' in request.POST:
            tenant.primary_color = request.POST.get('primary_color', '#0d6efd')
        
        # Logo güncelleme
        if 'logo' in request.FILES:
            tenant.logo = request.FILES['logo']
        
        # Menü ayarları güncelleme
        menu_settings = {}
        for menu_key in default_menus.keys():
            menu_settings[menu_key] = request.POST.get(f'menu_{menu_key}', 'off') == 'on'
        
        # Alt menü kontrolü: Ana menü kapalıysa alt menüler de kapalı olmalı
        if not menu_settings.get('reports', True):
            menu_settings['reports_list'] = False
            menu_settings['reports_trash'] = False
        
        tenant.menu_settings = menu_settings
        
        # Tenant'ı refresh etmeden önce kaydet
        tenant.save()
        
        # Tenant'ı veritabanından yeniden yükle (cache temizleme için)
        tenant.refresh_from_db()
        
        messages.success(request, f'✅ "{tenant.name}" firması güncellendi.')
        return redirect('admin_home')
    
    # Admin panelinde sidebar rengi değişmemesi için tenant'ı None yap
    # Ama formda tenant bilgisini gösteriyoruz, o yüzden ayrı değişkende tutalım
    sidebar_tenant = None  # Admin panelinde sidebar için tenant yok
    request.tenant = None  # Context processor için
    
    # Menü yapısı (ana menüler ve alt menüler)
    menu_structure = [
        {
            'key': 'hierarchy',
            'label': 'Hiyerarşi',
            'icon': 'fa-sitemap',
            'children': []
        },
        {
            'key': 'users',
            'label': 'Kullanıcılar',
            'icon': 'fa-users',
            'children': []
        },
        {
            'key': 'customers',
            'label': 'Müşteriler',
            'icon': 'fa-store',
            'children': []
        },
        {
            'key': 'tasks',
            'label': 'Görevler',
            'icon': 'fa-tasks',
            'children': []
        },
        {
            'key': 'route_plan',
            'label': 'Rota Planı',
            'icon': 'fa-route',
            'children': []
        },
        {
            'key': 'forms',
            'label': 'Formlar',
            'icon': 'fa-clipboard-list',
            'children': []
        },
        {
            'key': 'images',
            'label': 'Görseller',
            'icon': 'fa-images',
            'children': []
        },
        {
            'key': 'reports',
            'label': 'Raporlar',
            'icon': 'fa-chart-line',
            'children': [
                {'key': 'reports_list', 'label': 'Raporlar Listesi', 'icon': 'fa-list'},
                {'key': 'reports_trash', 'label': 'Çöp Kutusu', 'icon': 'fa-trash'},
            ]
        },
    ]
    
    context = {
        'tenant': tenant,  # Form için tenant bilgisi
        'sidebar_tenant': sidebar_tenant,  # Sidebar için None
        'is_admin_panel': True,  # Admin panelinde olduğumuzu belirt
        'menu_structure': menu_structure,
    }
    return render(request, 'apps/Core/edit_tenant.html', context)

# --- FİRMA EKLEME ---
@login_required
def create_company(request):
    """Yeni firma oluştur - Subdomain otomatik oluşturulur"""
    if not is_root_admin(request.user):
        return HttpResponseForbidden("Bu işlem için yetkiniz yok.")
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        primary_color = request.POST.get('primary_color', '#0d6efd')
        # Slug manuel girilebilir veya otomatik oluşturulur
        slug_input = request.POST.get('slug', '').strip()
        
        if not name:
            messages.error(request, 'Firma adı gereklidir.')
            return redirect('admin_home')
        
        try:
            # Slug oluştur (manuel girilmişse onu kullan, yoksa otomatik oluştur)
            if slug_input:
                slug = slugify(slug_input)
            else:
                slug = slugify(name)
            
            # Slug'un boş olmaması için kontrol
            if not slug:
                messages.error(request, 'Firma adından geçerli bir subdomain oluşturulamadı. Lütfen manuel olarak girin.')
                return redirect('admin_home')
            
            # Slug benzersiz olmalı - eğer varsa numara ekle
            original_slug = slug
            counter = 1
            while Tenant.objects.filter(slug=slug).exists():
                slug = f"{original_slug}-{counter}"
                counter += 1
                if counter > 100:  # Güvenlik için limit
                    messages.error(request, 'Çok fazla benzer firma adı var. Lütfen farklı bir ad seçin.')
                    return redirect('admin_home')
            
            # Varsayılan plan oluştur veya al
            from .models import Plan
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
            
            tenant = Tenant.objects.create(
                name=name,
                slug=slug,
                email=email or 'info@example.com',
                plan=default_plan,
                primary_color=primary_color,
                is_active=True
            )
            
            # Başarı mesajında subdomain bilgisi de göster
            messages.success(
                request, 
                f'✅ Firma "{name}" başarıyla oluşturuldu! '
                f'Subdomain: <strong>{slug}.fieldops.com</strong>'
            )
        except Exception as e:
            messages.error(request, f'❌ Hata: {str(e)}')
    
    return redirect('admin_home')

# --- FİRMA SEÇME (Subdomain'e Yönlendir) ---
@login_required
def select_company(request, tenant_id):
    """
    Admin panelinden firma seçimi - Session bazlı olarak direkt o firmanın paneline giriş yapar.
    Admin yetkisiyle full yönetim erişimi sağlar.
    """
    try:
        tenant = Tenant.objects.get(id=tenant_id, is_active=True)
        
        # Kullanıcının bu tenant'a erişim hakkı var mı kontrol et
        if not is_root_admin(request.user):
            if hasattr(request.user, 'tenant') and request.user.tenant != tenant:
                messages.error(request, 'Bu firmaya erişim yetkiniz yok.')
                return redirect('admin_home')
        
        # Admin panelinden bağlanıldığında direkt firma paneline geç
        # Session'a tenant bilgisini kaydet (admin panelinden bağlanıldığını işaretle)
        request.session['tenant_id'] = tenant.id
        request.session['connect_tenant_id'] = tenant.id
        request.session['connect_tenant_slug'] = tenant.slug
        request.session['connect_tenant_color'] = tenant.primary_color
        request.session['connect_tenant_name'] = tenant.name
        request.session['admin_from_panel'] = True  # Admin panelinden bağlanıldığını işaretle
        request.session.modified = True  # Session'ın değiştiğini işaretle
        request.session.save()  # Session'ı kaydet
        
        # Admin zaten authenticated, direkt home'a yönlendir
        messages.success(request, f'"{tenant.name}" firmasına bağlandınız.')
        from django.urls import reverse
        # Redirect'i absolute URL ile yap (session'ın korunması için)
        return redirect(reverse('home'))
        
    except Tenant.DoesNotExist:
        messages.error(request, 'Firma bulunamadı.')
        return redirect('admin_home')

# --- ÖZEL GİRİŞ VIEW (Firma Adı ile) ---
from django.contrib.auth.views import LoginView
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy

@method_decorator(csrf_protect, name='dispatch')
class CustomLoginView(LoginView):
    template_name = 'registration/login_tenant.html'
    redirect_authenticated_user = False  # Her zaman giriş yapılmasını iste
    
    def dispatch(self, request, *args, **kwargs):
        # Admin panelinden bağlanıldıysa ve session'da tenant varsa direkt geçir
        # Bu sadece admin panelinden yapılabilir
        admin_from_panel = request.session.get('admin_from_panel', False)
        connect_tenant_id = request.session.get('connect_tenant_id')
        
        if request.user.is_authenticated and admin_from_panel and connect_tenant_id:
            # Root admin kontrolü - sadece admin panelinden bağlanıldıysa geçir
            if is_root_admin(request.user):
                request.session['tenant_id'] = connect_tenant_id
                from django.urls import reverse
                return redirect(reverse('home'))
        
        # Normal kullanıcılar için her zaman login yapılması gerekiyor
        # Admin panelinden değilse, authenticated olsa bile login sayfasını göster
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        # redirect_authenticated_user = False olduğu için authenticated kullanıcılar da login sayfasını görebilir
        # Bu sayede her zaman giriş yapılması zorunlu olur
        
        # Tenant bilgisini session'dan al
        tenant_id = request.session.get('connect_tenant_id')
        tenant_slug = request.session.get('connect_tenant_slug') or self.kwargs.get('tenant_slug')

        # Eğer tenant bilgisi yoksa, ana sayfayı (index.html) göster
        # Redirect yapmıyoruz çünkü bu sonsuz döngüye neden oluyor
        if not tenant_id or not tenant_slug:
            # Session'ı temizle (eski veriler kalmasın)
            for key in ['connect_tenant_id', 'connect_tenant_slug', 'connect_tenant_color', 'connect_tenant_name', 'admin_from_panel']:
                request.session.pop(key, None)
            # Ana sayfa template'ini göster (redirect yerine)
            return render(request, 'index.html')

        try:
            tenant = Tenant.objects.get(id=tenant_id, slug=tenant_slug, is_active=True)
        except Tenant.DoesNotExist:
            for key in ['connect_tenant_id', 'connect_tenant_slug', 'connect_tenant_color', 'connect_tenant_name', 'admin_from_panel']:
                request.session.pop(key, None)
            return redirect('index')

        # Logout sonrası gelindi mi kontrol et
        from_tenant_logout = request.session.get('from_tenant_logout', False)
        logout_tenant_name = request.session.get('logout_tenant_name', tenant.name)

        context = {
            'tenant': tenant,
            'primary_color': request.session.get('connect_tenant_color', tenant.primary_color),
            'from_tenant_logout': from_tenant_logout,
            'logout_tenant_name': logout_tenant_name,
        }
        return render(request, 'registration/login_tenant.html', context)
    
    def post(self, request, *args, **kwargs):
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        tenant_id = request.session.get('connect_tenant_id')
        tenant_slug = request.session.get('connect_tenant_slug') or request.POST.get('tenant_slug', '').strip()

        if not tenant_id or not tenant_slug:
            messages.error(request, 'Lütfen önce firma adını girin.')
            return redirect('index')

        try:
            tenant = Tenant.objects.get(id=tenant_id, slug=tenant_slug, is_active=True)
        except Tenant.DoesNotExist:
            messages.error(request, 'Firma bulunamadı. Lütfen tekrar deneyin.')
            for key in ['connect_tenant_id', 'connect_tenant_slug', 'connect_tenant_color', 'connect_tenant_name']:
                request.session.pop(key, None)
            return redirect('index')
        
        # Username'i tenant slug ile birleştir (örn: Merch1 -> pastel_Merch1)
        # Önce direkt username'i dene, sonra tenant slug ile birleştirilmiş halini dene
        user = None
        username_attempts = [
            f"{tenant.slug}_{username}",  # pastel_Merch1
            username,  # Merch1 (eski kullanıcılar için)
        ]
        
        for username_attempt in username_attempts:
            user = authenticate(request, username=username_attempt, password=password)
            if user is not None:
                break
        
        if user is not None and user.is_active:
            # Root admin kontrolü - root admin her tenant'a giriş yapabilir
            from apps.users.utils import is_root_admin
            
            if not is_root_admin(user):
                # Normal kullanıcı için MUTLAKA tenant kontrolü
                # Kullanıcının tenant'ı yoksa giriş yapamaz
                if not hasattr(user, 'tenant') or not user.tenant:
                    messages.error(request, 'Bu kullanıcı henüz bir firmaya atanmamış. Lütfen yönetici ile iletişime geçin.')
                    tenant_slug = request.POST.get('tenant_slug', '').strip()
                    if tenant_slug:
                        return redirect('login_with_tenant', tenant_slug=tenant_slug)
                    return redirect('index')
                
                # Kullanıcının tenant'ı seçilen tenant ile eşleşmeli
                if user.tenant != tenant:
                    messages.error(request, f'Bu kullanıcı "{user.tenant.name}" firmasına aittir. Lütfen doğru firmayı seçin.')
                    return self.form_invalid(self.get_form())
            
            login(request, user)
            
            # Session'a tenant bilgisini kaydet (development'ta subdomain olmadığı için gerekli)
            request.session['tenant_id'] = tenant.id
            # connect_tenant_id'yi de koru (middleware için)
            request.session['connect_tenant_id'] = tenant.id
            request.session['connect_tenant_slug'] = tenant.slug
            request.session.modified = True
            request.session.save()
            
            # Admin panelinden bağlanıldıysa, admin_from_panel flag'ini kaldır
            if request.session.get('admin_from_panel'):
                request.session.pop('admin_from_panel', None)
            
            # Logout flag'lerini temizle
            for key in ['from_tenant_logout', 'logout_tenant_slug', 'logout_tenant_name']:
                request.session.pop(key, None)
            
            # Bağlanma session bilgilerini temizleme - tenant_id'yi koruyoruz
            # Sadece gereksiz olanları temizle
            request.session.pop('connect_tenant_color', None)
            request.session.pop('connect_tenant_name', None)

            # Development'ta subdomain kullanmıyoruz, direkt home'a yönlendir
            # Production'da subdomain kullanılabilir
            if settings.DEBUG:
                redirect_url = f"/home/"
            else:
                domain = getattr(settings, 'SUBDOMAIN_DOMAIN', None)
                if domain:
                    protocol = 'https' if not settings.DEBUG else 'http'
                    redirect_url = f"{protocol}://{tenant.slug}.{domain}/home/"
                else:
                    redirect_url = '/home/'

            return redirect(redirect_url)

        messages.error(request, 'Kullanıcı adı veya şifre hatalı.')
        return self.form_invalid(self.get_form())

# --- GELİŞTİRİCİ ADMIN GİRİŞİ ---
@method_decorator(csrf_protect, name='dispatch')
class AdminLoginView(LoginView):
    template_name = 'registration/admin_login.html'
    redirect_authenticated_user = False  # Her zaman giriş yapılmasını iste
    
    def get_success_url(self):
        # Root admin kontrolü
        if is_root_admin(self.request.user):
            return reverse_lazy('admin_home')
        return reverse_lazy('home')

# --- MOBİL ANASAYFA ---
@login_required
def mobile_home(request):
    today = date.today()
    user = request.user
    # Supervisor (veya hiyerarşide altı olan herkes) için sekme göster
    scope_no_self = get_hierarchy_scope_for_user(user, include_self=False)
    # Not: HierarchyScope.usernames boş ise (Admin/superuser) "herkesi görür" anlamına gelir.
    has_team = bool(scope_no_self.usernames) or getattr(user, "is_superuser", False) or getattr(user, "authority", None) == "Admin"
    
    # Aktif ziyaret var mı kontrol et (check_in_time var ama check_out_time yok)
    active_visit = VisitTask.objects.filter(
        merch_code=user.username,
        check_in_time__isnull=False,
        check_out_time__isnull=True,
        status__in=['pending', 'missed']  # completed değilse aktif
    ).first()
    
    # Eğer aktif ziyaret varsa uyarı göster
    if active_visit:
        from django.contrib import messages
        messages.warning(request, f'Devam eden bir ziyaret var: {active_visit.customer.name}. Lütfen önce bu ziyareti tamamlayın.')
    
    tasks = VisitTask.objects.filter(
        merch_code=user.username,
        planned_date=today
    ).select_related('customer').order_by('status', 'customer__name')
    
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(status='completed').count()
    
    progress_percentage = 0
    if total_tasks > 0:
        progress_percentage = int((completed_tasks / total_tasks) * 100)
    
    context = {
        'tasks': tasks,
        'today': today,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'progress_percentage': progress_percentage,
        'active_visit': active_visit,
        'has_team': has_team,
    }
    return render(request, 'mobile/home.html', context)


@login_required
def mobile_team_home(request):
    """
    Supervisor tab: shows team progress (today) and subordinate list.
    """
    today = date.today()
    user = request.user
    ensure_root_admin_configured(user)

    # Root admin: "supervisor gibi görüntüle" desteği
    as_user_id = request.GET.get("as_user")
    if is_root_admin(user) and as_user_id:
        try:
            subject = get_user_model().objects.get(id=int(as_user_id))
        except Exception:
            subject = user
    else:
        subject = user

    # Root admin ana görünüm: Admin node altındaki tüm atanmış kullanıcılar
    if is_root_admin(user) and subject == user and not as_user_id:
        user_ids = get_assigned_user_ids_under_admin_node()
        if user_ids:
            sub_users = list(
                get_user_model().objects.filter(id__in=user_ids).order_by("first_name", "last_name", "username")
            )
            sub_codes = [u.username for u in sub_users]
        else:
            # Fallback: Admin her şeyi görebilir (hiyerarşi ataması yoksa bile)
            sub_users = list(
                get_user_model().objects.exclude(id=user.id).order_by("first_name", "last_name", "username")
            )
            sub_codes = [u.username for u in sub_users]
    else:
        scope_no_self = get_hierarchy_scope_for_user(subject, include_self=False)
        # Admin/superuser için boş set => herkesi görür
        if not scope_no_self.usernames and (
            getattr(subject, "is_superuser", False) or getattr(subject, "authority", None) == "Admin"
        ):
            sub_users = list(
                get_user_model().objects.exclude(id=subject.id).order_by("first_name", "last_name", "username")
            )
            sub_codes = [u.username for u in sub_users]
        else:
            sub_codes = sorted(scope_no_self.usernames)
            sub_users = list(
                get_user_model().objects.filter(username__in=sub_codes).order_by("first_name", "last_name", "username")
            )

    stats_qs = (
        VisitTask.objects.filter(planned_date=today, merch_code__in=sub_codes)
        .values("merch_code")
        .annotate(
            total=Count("id"),
            completed=Count("id", filter=DQ(status="completed")),
        )
    )
    stats = {x["merch_code"]: x for x in stats_qs}

    team_total = sum(x["total"] for x in stats.values()) if stats else 0
    team_completed = sum(x["completed"] for x in stats.values()) if stats else 0
    team_progress_percentage = int((team_completed / team_total) * 100) if team_total > 0 else 0

    team = []
    for u in sub_users:
        s = stats.get(u.username, {"total": 0, "completed": 0})
        # Konum için: aktif ziyaret varsa onun mağazası, yoksa bugünkü ilk görev
        active = (
            VisitTask.objects.filter(
                merch_code=u.username,
                check_in_time__isnull=False,
                check_out_time__isnull=True,
                status__in=["pending", "missed"],
            )
            .select_related("customer")
            .order_by("-check_in_time")
            .first()
        )
        candidate = active
        if not candidate:
            candidate = (
                VisitTask.objects.filter(merch_code=u.username, planned_date=today)
                .select_related("customer")
                .order_by("status", "customer__name")
                .first()
            )
        location_url = None
        if candidate and candidate.customer and candidate.customer.latitude and candidate.customer.longitude:
            location_url = f"https://www.google.com/maps/search/?api=1&query={candidate.customer.latitude},{candidate.customer.longitude}"

        name = (f"{u.first_name} {u.last_name}").strip() or u.username
        # Root admin için: bu kişinin ekip ekranına drill-down mümkün mü?
        drill_as_user_id = None
        if is_root_admin(user):
            sc = get_hierarchy_scope_for_user(u, include_self=False)
            if sc.usernames:
                drill_as_user_id = u.id
        team.append(
            {
                "user_id": u.id,
                "name": name,
                "user_code": getattr(u, "user_code", u.username),
                "merch_code": u.username,
                "authority": getattr(u, "authority", ""),
                "completed": s["completed"],
                "total": s["total"],
                "location_url": location_url,
                "drill_as_user_id": drill_as_user_id,
            }
        )

    return render(
        request,
        "mobile/team_home.html",
        {
            "today": today,
            "has_team": True,
            "team": team,
            "team_total_tasks": team_total,
            "team_completed_tasks": team_completed,
            "team_progress_percentage": team_progress_percentage,
            "viewing_as": (None if subject == user else subject),
            "is_root_admin_view": is_root_admin(user),
        },
    )

# --- MOBİL PROFİL (Hata veren eksik parça buydu) ---
@login_required
def mobile_profile(request):
    return render(request, 'mobile/profile.html')

from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from apps.core.excel_utils import xlsx_from_rows

@login_required
def download_excel_template(request, template_type):
    """
    İstenilen türe göre (customer, user, task) boş bir Excel şablonu oluşturur ve indirir.
    HATA DÜZELTME: Tüm sütunların uzunluğu eşitlendi.
    """
    filename = "sablon.xlsx"
    columns = []
    
    # 1. Sütun Başlıklarını Belirle
    if template_type == 'customer':
        columns = [
            'Müşteri Kodu', 'Müşteri Adı', 'Cari / Firma', 'İl', 'İlçe', 
            'Adres', 'Telefon', 'Yetkili Kişi', 'Enlem', 'Boylam'
        ]
        filename = "musteri_yukleme_sablonu.xlsx"

    elif template_type == 'user':
        columns = ['Kullanıcı Kodu', 'Ad', 'Soyad', 'Telefon', 'E-posta', 'Rol', 'Şifre']
        filename = "personel_yukleme_sablonu.xlsx"

    elif template_type == 'task':
        columns = ['Müşteri Kodu', 'Personel', 'Tarih', 'Ziyaret Notu']
        filename = "gorev_yukleme_sablonu.xlsx"
        
    elif template_type == 'route':
        columns = ['Saha Kullanıcısı', 'Müşteri Kodu', 'Gün 1', 'Gün 2', 'Gün 3', 'Gün 4', 'Gün 5', 'Gün 6', 'Gün 7']
        filename = "rota_yukleme_sablonu.xlsx"

    # Tek satırlık örnek şablon
    row = {col: "" for col in columns}

    if template_type == 'customer':
        row['Müşteri Kodu'] = 'M-001'
        row['Müşteri Adı'] = 'Örnek Market'
        row['İl'] = 'İstanbul'
    elif template_type == 'user':
        row['Kullanıcı Kodu'] = 'Merch1'
        row['Ad'] = 'Ahmet'
        row['Rol'] = 'Saha Personeli'
        row['Şifre'] = '123456'
    elif template_type == 'task':
        row['Müşteri Kodu'] = 'M-001'
        row['Personel'] = 'Merch1'
        row['Tarih'] = '25.12.2025'
    elif template_type == 'route':
        row['Saha Kullanıcısı'] = 'Merch1'
        row['Müşteri Kodu'] = 'M-001'
        row['Gün 1'] = '1'

    content = xlsx_from_rows([row], sheet_name="Şablon", header_order=columns)
    response = HttpResponse(content, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename={filename}'
    return response

from django.shortcuts import get_object_or_404
from apps.forms.models import Survey  # Bunu en üste eklemeyi unutma

@login_required
def mobile_task_detail(request, pk):
    """
    Seçilen görevin detay ekranı.
    Mağaza bilgisi + Formlar + Başlat Butonu
    Filtreleme: Tüm filtreler AND mantığıyla çalışır (şartlı)
    """
    task = get_object_or_404(VisitTask, pk=pk)
    user = request.user
    customer = task.customer
    # Görevin sahibi (form filtreleri ve cevap görüntüleme için)
    task_user = get_user_model().objects.filter(username=task.merch_code).first() or user

    # Yetki kontrolü: görevi sadece sahibi veya hiyerarşide üstü görebilir.
    scope = get_hierarchy_scope_for_user(user, include_self=True)
    if scope.usernames and task.merch_code not in scope.usernames:
        return HttpResponseForbidden("Bu görevi görüntüleme yetkiniz yok.")
    # Aksiyon (ziyaret başlat/bitir, form doldur) sadece görevin sahibinde olmalı
    can_act = (task.merch_code == user.username)
    
    # Aktif anketleri başlangıç olarak al
    surveys = Survey.objects.filter(is_active=True)
    
    # Tarih kontrolü
    from datetime import date
    today = date.today()
    surveys = surveys.filter(
        models.Q(start_date__isnull=True) | models.Q(start_date__lte=today)
    ).filter(
        models.Q(end_date__isnull=True) | models.Q(end_date__gte=today)
    )
    
    # FİLTRELEME (AND MANTIĞI - TÜM ŞARTLAR SAĞLANMALI)
    filtered_surveys = []
    
    for survey in surveys:
        should_show = True  # Varsayılan olarak göster
        
        # 1. KULLANICI FİLTRESİ
        if survey.filter_users.exists():
            # Eğer kullanıcı filtresi varsa, kullanıcı listede olmalı
            if task_user not in survey.filter_users.all():
                should_show = False
        
        # 2. ROL FİLTRESİ
        if survey.target_roles.exists():
            # Eğer rol filtresi varsa, kullanıcının rolü listede olmalı
            if not task_user.role or task_user.role not in survey.target_roles.all():
                should_show = False
        
        # 3. KULLANICI ÖZEL ALAN FİLTRELERİ
        if survey.user_custom_filters:
            for field_slug, allowed_values in survey.user_custom_filters.items():
                if allowed_values:  # Eğer değer seçilmişse
                    user_value_str = task_user.extra_data.get(field_slug, '') if task_user.extra_data else ''
                    # Tag sistemi: Değerler virgülle ayrılmış (örn: "Lansman,Stok Takibi")
                    user_tags = [tag.strip() for tag in str(user_value_str).split(',') if tag.strip()]
                    # Kullanıcının tag'lerinden en az biri, izin verilen değerlerden biri olmalı
                    if not any(tag in allowed_values for tag in user_tags):
                        should_show = False
                        break
        
        # 4. MÜŞTERİ FİLTRESİ
        if survey.filter_customers.exists():
            # Eğer müşteri filtresi varsa, müşteri listede olmalı
            if customer not in survey.filter_customers.all():
                should_show = False
        
        # 5. CARİ FİLTRESİ
        if survey.filter_caris.exists():
            # Eğer cari filtresi varsa, müşterinin carisi listede olmalı
            if not customer.cari or customer.cari not in survey.filter_caris.all():
                should_show = False
        
        # 6. MÜŞTERİ ÖZEL ALAN FİLTRELERİ
        if survey.custom_filters:
            for field_slug, allowed_values in survey.custom_filters.items():
                if allowed_values:  # Eğer değer seçilmişse
                    customer_value = customer.extra_data.get(field_slug, '') if customer.extra_data else ''
                    # Müşterinin bu alandaki değeri, izin verilen değerlerden biri olmalı
                    if customer_value not in allowed_values:
                        should_show = False
                        break
        
        # Tüm şartlar sağlandıysa listeye ekle
        if should_show:
            filtered_surveys.append(survey)
    
    # --- Anket durumları (Yapıldı / Yapılmadı) ---
    # Kural:
    # - Anketin zorunlu soruları varsa: tüm zorunlular cevaplandıysa "Yapıldı"
    # - Zorunlu soru yoksa: ankete ait en az 1 soru cevaplandıysa "Yapıldı"
    survey_ids = [s.id for s in filtered_surveys]
    answered_q_ids = set(
        SurveyAnswer.objects.filter(task=task, question__survey_id__in=survey_ids)
        .exclude(answer_text__isnull=True, answer_photo__isnull=True)
        .values_list('question_id', flat=True)
    )

    questions = list(
        Question.objects.filter(survey_id__in=survey_ids).values('id', 'survey_id', 'required')
    )
    req_map = {}
    all_map = {}
    for q in questions:
        sid = q['survey_id']
        all_map.setdefault(sid, []).append(q['id'])
        if q['required']:
            req_map.setdefault(sid, []).append(q['id'])

    for s in filtered_surveys:
        req_ids = req_map.get(s.id, [])
        all_ids = all_map.get(s.id, [])
        if req_ids:
            done_required = sum(1 for qid in req_ids if qid in answered_q_ids)
            s.is_done = done_required == len(req_ids)
            s.required_done = done_required
            s.required_total = len(req_ids)
        else:
            any_done = any(qid in answered_q_ids for qid in all_ids)
            s.is_done = any_done
            s.required_done = 1 if any_done else 0
            s.required_total = 1 if all_ids else 0
        # Üst kullanıcılar için read-only görüntüleme: en az 1 cevap var mı?
        s.has_answers = any(qid in answered_q_ids for qid in all_ids)

    context = {
        'task': task,
        'surveys': filtered_surveys,
        'can_act': can_act,
    }
    return render(request, 'mobile/task_detail.html', context)


@login_required
def mobile_view_survey(request, task_id, survey_id):
    """
    Read-only: Üst kullanıcılar (hiyerarşide) ve görev sahibi, doldurulan anketi görüntüleyebilir.
    Düzenleme yoktur.
    """
    task = get_object_or_404(VisitTask, pk=task_id)
    survey = get_object_or_404(Survey, pk=survey_id)
    user = request.user

    scope = get_hierarchy_scope_for_user(user, include_self=True)
    if scope.usernames and task.merch_code not in scope.usernames:
        return HttpResponseForbidden("Bu görevin formunu görüntüleme yetkiniz yok.")

    questions = list(survey.questions.all().order_by("order"))
    answers = list(
        SurveyAnswer.objects.filter(task=task, question__in=questions).select_related("question")
    )
    ans_by_qid = {a.question_id: a for a in answers}

    items = []
    for q in questions:
        a = ans_by_qid.get(q.id)
        items.append(
            {
                "question": q,
                "answer_text": (a.answer_text if a else None),
                "answer_photo": (a.answer_photo if a else None),
                "has_answer": bool(a and ((a.answer_text and str(a.answer_text).strip()) or a.answer_photo)),
            }
        )

    return render(
        request,
        "mobile/survey_view.html",
        {
            "task": task,
            "survey": survey,
            "items": items,
        },
    )

@login_required
def mobile_fill_survey(request, task_id, survey_id):
    task = get_object_or_404(VisitTask, pk=task_id)
    survey = get_object_or_404(Survey, pk=survey_id)
    # Sadece görevin sahibi form doldurabilir
    if task.merch_code != request.user.username:
        return HttpResponseForbidden("Bu görevin formunu doldurma yetkiniz yok.")
    
    # Ana soruları al (parent_question veya dependency_question olmayanlar)
    main_questions = survey.questions.filter(
        models.Q(parent_question__isnull=True) & models.Q(dependency_question__isnull=True)
    ).order_by('order')
    
    # Tüm soruları al (alt sorular dahil)
    all_questions = survey.questions.all().order_by('order')

    if request.method == 'POST':
        # AJAX isteği mi kontrol et
        immediate = request.POST.get('immediate', 'false') == 'true'
        
        # Eğer immediate değilse, localStorage'a kaydet (JavaScript tarafında yapılacak)
        # Burada sadece normal form gönderimini işle
        try:
            # Her soru için döngüye girip cevabı alalım
            for q in all_questions:
                # HTML formundaki input ismi: "q_1", "q_2" şeklinde ayarlamıştık
                input_name = f"q_{q.id}"
                
                text_val = request.POST.get(input_name)
                photo_val = request.FILES.get(input_name)
                photo_b64 = request.POST.get(f"{input_name}_base64") if q.input_type == 'photo' else None

                # WebView fallback: base64 geldiyse dosyaya çevir
                if not photo_val and photo_b64 and photo_b64.startswith('data:image/'):
                    try:
                        header, b64data = photo_b64.split(',', 1)
                        # data:image/jpeg;base64
                        ext = 'jpg'
                        if 'image/png' in header:
                            ext = 'png'
                        elif 'image/webp' in header:
                            ext = 'webp'
                        elif 'image/jpeg' in header or 'image/jpg' in header:
                            ext = 'jpg'

                        import base64
                        decoded = base64.b64decode(b64data)
                        photo_val = ContentFile(decoded, name=f"survey_{task_id}_{q.id}.{ext}")
                    except Exception:
                        photo_val = None
                
                # Eğer soruya bir cevap verilmişse (Yazı veya Fotoğraf)
                if text_val or photo_val:
                    # Önce eski cevap varsa silelim (Güncelleme mantığı)
                    SurveyAnswer.objects.filter(task=task, question=q).delete()
                    
                    # Yeni cevabı kaydet
                    SurveyAnswer.objects.create(
                        task=task,
                        question=q,
                        answer_text=text_val,
                        answer_photo=photo_val
                    )
            
            # AJAX isteği ise JSON döndür
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.POST.get('ajax') == 'true':
                return JsonResponse({'success': True, 'message': 'Form başarıyla kaydedildi.'})
            
            messages.success(request, '✅ Form başarıyla kaydedildi.')
            return redirect('mobile_task_detail', pk=task_id)
            
        except Exception as e:
            # AJAX isteği ise JSON döndür
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.POST.get('ajax') == 'true':
                return JsonResponse({'success': False, 'message': f'Hata oluştu: {str(e)}'}, status=400)
            messages.error(request, f'Hata oluştu: {str(e)}')

    # Soruları ve alt sorularını hazırla
    questions_data = []
    for q in main_questions:
        # Alt soruları al (parent_question veya dependency_question ile bağlı olanlar)
        child_questions = survey.questions.filter(
            models.Q(parent_question=q) | models.Q(dependency_question=q)
        ).distinct().order_by('order')
        
        # Alt soruları detaylı bilgilerle hazırla
        child_questions_list = []
        for child in child_questions:
            # Hangi alan kullanılmış? (parent_question veya dependency_question)
            trigger_value = ''
            if child.parent_question == q:
                trigger_value = child.trigger_answer or ''
            elif child.dependency_question == q:
                trigger_value = child.dependency_value or ''
            
            child_questions_list.append({
                'id': child.id,
                'label': child.label,
                'input_type': child.input_type,
                'required': child.required,
                'trigger_answer': trigger_value,
                'parent_id': q.id,
                'options': [{'text': opt.text, 'id': opt.id} for opt in child.options.all()],
                'min_photos': child.min_photos,
                'max_photos': child.max_photos,
            })
        
        # Sorunun seçeneklerini al (select tipi sorular için)
        question_options = [{'text': opt.text, 'id': opt.id} for opt in q.options.all()] if q.input_type == 'select' else []
        
        questions_data.append({
            'question': q,
            'child_questions': child_questions_list,
            'options': question_options,
        })
    
    # Zorunlu soruları kontrol et
    required_questions = [q for q in all_questions if q.required]
    answered_questions = SurveyAnswer.objects.filter(task=task, question__in=required_questions).values_list('question_id', flat=True)
    missing_required = [q for q in required_questions if q.id not in answered_questions]

    context = {
        'task': task,
        'survey': survey,
        'questions_data': questions_data,
        'required_questions': required_questions,
        'missing_required': missing_required,
    }
    return render(request, 'mobile/survey_form.html', context)

@csrf_exempt
@login_required
def start_visit_check(request, task_id):
    # Debug için print ekleyelim (production'da kaldırılabilir)
    print(f"[DEBUG] start_visit_check çağrıldı - Method: {request.method}, Task ID: {task_id}")
    print(f"[DEBUG] User: {request.user if hasattr(request, 'user') else 'Anonymous'}")
    print(f"[DEBUG] Body: {request.body}")
    print(f"[DEBUG] Headers: {dict(request.headers)}")
    
    # GET isteği için test endpoint
    if request.method == 'GET':
        return JsonResponse({
            'success': True,
            'message': 'API çalışıyor',
            'task_id': task_id,
            'method': 'GET'
        })
    
    if request.method == 'POST':
        try:
            # 1. Mobilden gelen body
            body_text = request.body.decode('utf-8')
            data = json.loads(body_text)

            # 2. Görevi ve Müşteriyi Bul
            task = VisitTask.objects.get(id=task_id)
            customer = task.customer
            # Sadece görevin sahibi ziyareti başlatabilir (Admin dahil istisna yok)
            if task.merch_code != getattr(request.user, "username", None):
                return JsonResponse({'success': False, 'message': 'Bu ziyareti başlatma yetkiniz yok.'}, status=403)

            # 3. Mesafe kuralı kontrolü (distance_rule) - kapalıysa konum ve mesafe kontrolü yapılmaz
            distance_rule_setting = SystemSetting.objects.filter(key='distance_rule').first()
            # Eski require_gps ayarını migrate et
            if not distance_rule_setting:
                old_setting = SystemSetting.objects.filter(key='require_gps').first()
                if old_setting:
                    old_setting.key = 'distance_rule'
                    old_setting.label = 'Mesafe Kuralı'
                    old_setting.description = 'Açık: Giriş mesafesi ve gezinme mesafesi kontrolü yapılır. Kapalı: Mesafe kontrolü yapılmaz, herhangi bir mesafeden ziyaret başlatılabilir.'
                    old_setting.save()
                    distance_rule_setting = old_setting

            distance_rule_enabled = True
            if distance_rule_setting:
                try:
                    distance_rule_enabled = distance_rule_setting.value.lower() == 'true'
                except:
                    distance_rule_enabled = True

            # Mesafe kuralı kapalıysa: konum zorunlu değil, doğrudan başlat
            if not distance_rule_enabled:
                from datetime import datetime
                task.check_in_time = datetime.now()
                task.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Ziyaret başlatıldı. (Mesafe kuralı kapalı olduğu için konum ve mesafe kontrolü yapılmadı.)'
                })

            # 4. Kullanıcı koordinatları - mesafe kuralı açıkken zorunlu
            user_lat_raw = data.get('latitude')
            user_lon_raw = data.get('longitude')

            if user_lat_raw is None or user_lon_raw is None:
                return JsonResponse({
                    'success': False, 
                    'message': 'Konum bilgisi alınamadı. Lütfen GPS\'in açık olduğundan ve konum izninin verildiğinden emin olun.'
                })

            try:
                user_lat = float(user_lat_raw)
                user_lon = float(user_lon_raw)
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False, 
                    'message': 'Geçersiz konum bilgisi. Lütfen tekrar deneyin.'
                })

            # Koordinatlar geçerli aralıkta mı?
            if not (-90 <= user_lat <= 90) or not (-180 <= user_lon <= 180):
                return JsonResponse({
                    'success': False, 
                    'message': 'Geçersiz konum koordinatları. Lütfen tekrar deneyin.'
                })

            try:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Koordinat alındı - Lat: {user_lat}, Lon: {user_lon}")
            except:
                pass

            try:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Task ve Customer bulundu - Customer: {customer.name}, Lat: {customer.latitude}, Lon: {customer.longitude}")
            except:
                pass
            
            # Müşterinin koordinatı yoksa mesafe kontrolü yapmadan ziyareti başlat
            # latitude ve longitude FloatField, None veya 0.0 olabilir
            cust_lat_val = customer.latitude
            cust_lng_val = customer.longitude
            
            # Koordinat kontrolü - None veya 0.0 ise mesafe kontrolü yapma
            if (cust_lat_val is None or cust_lng_val is None or 
                cust_lat_val == 0.0 or cust_lng_val == 0.0):
                from datetime import datetime
                task.check_in_time = datetime.now()
                task.save()
                return JsonResponse({
                    'success': True, 
                    'message': 'Ziyaret başlatıldı. (Müşteri konumu sistemde olmadığı için mesafe kontrolü yapılmadı.)'
                })

            # 3. Mesafeyi Hesapla - None kontrolü ile
            try:
                # None kontrolü
                if cust_lat_val is None or cust_lng_val is None:
                    raise ValueError("Müşteri koordinatları None")
                
                cust_lat = float(cust_lat_val)
                cust_lon = float(cust_lng_val)
                
                # Koordinatlar geçerli mi kontrol et (enlem: -90 ile 90, boylam: -180 ile 180)
                if not (-90 <= cust_lat <= 90) or not (-180 <= cust_lon <= 180):
                    raise ValueError("Koordinatlar geçersiz aralıkta")
                
                distance = calculate_distance(user_lat, user_lon, cust_lat, cust_lon)
            except (ValueError, TypeError) as e:
                # Koordinat geçersizse mesafe kontrolü yapmadan başlat
                from datetime import datetime
                task.check_in_time = datetime.now()
                task.save()
                return JsonResponse({
                    'success': True, 
                    'message': 'Ziyaret başlatıldı. (Müşteri konumu geçersiz olduğu için mesafe kontrolü yapılmadı.)'
                })
            
            # 4. Mesafe Kuralı kontrolü - Eğer kapalıysa mesafe kontrolü yapma
            distance_rule_setting = SystemSetting.objects.filter(key='distance_rule').first()
            # Eğer yeni ayar yoksa, eski require_gps ayarını kontrol et
            if not distance_rule_setting:
                old_setting = SystemSetting.objects.filter(key='require_gps').first()
                if old_setting:
                    # Eski ayarı yeni isimle güncelle
                    old_setting.key = 'distance_rule'
                    old_setting.label = 'Mesafe Kuralı'
                    old_setting.description = 'Açık: Giriş mesafesi ve gezinme mesafesi kontrolü yapılır. Kapalı: Mesafe kontrolü yapılmaz, herhangi bir mesafeden ziyaret başlatılabilir.'
                    old_setting.save()
                    distance_rule_setting = old_setting
            
            distance_rule_enabled = True  # Varsayılan: açık
            if distance_rule_setting:
                try:
                    distance_rule_enabled = distance_rule_setting.value.lower() == 'true'
                except:
                    distance_rule_enabled = True
            
            # Eğer mesafe kuralı kapalıysa, direkt ziyareti başlat
            if not distance_rule_enabled:
                from datetime import datetime
                task.check_in_time = datetime.now()
                task.save()
                return JsonResponse({
                    'success': True, 
                    'message': 'Ziyaret başlatıldı. (Mesafe kuralı kapalı olduğu için mesafe kontrolü yapılmadı.)'
                })
            
            # 5. Admin Panelindeki Sınırı Çek (Mesafe kuralı açıksa)
            # Eğer ayar yoksa varsayılan 300 metre olsun
            setting = SystemSetting.objects.filter(key='visit_radius').first()
            try:
                limit = float(setting.value) if setting and setting.value else 300.0
            except (ValueError, TypeError):
                limit = 300.0

            # 6. KARAR ANI - Mesafe kontrolü (>= kullanarak sıkı kontrol)
            # Eğer mesafe limit'e eşit veya fazlaysa ziyaret başlatılmamalı
            if distance >= limit:
                # Mesafe UZAK veya EŞİT - Ziyaret başlatılmamalı
                distance_diff = int(distance - limit)
                return JsonResponse({
                    'success': False, 
                    'message': f"Ziyaret mesafesi uyarısı!\nTespit Edilen Mesafe: {int(distance)}m\nİzin Verilen: {int(limit)}m\nFark: {distance_diff}m fazla"
                })
            
            # Mesafe uygun (limit'ten küçük), ziyaret başlatıldı
            from datetime import datetime
            task.check_in_time = datetime.now()
            task.save()
            return JsonResponse({'success': True, 'message': 'Konum doğrulandı. Ziyaret başladı.'})

        except json.JSONDecodeError as e:
            import logging
            logger = logging.getLogger(__name__)
            try:
                logger.error(f"JSON decode hatası: {str(e)}, Body: {request.body}")
            except:
                pass
            return JsonResponse({'success': False, 'message': 'Geçersiz veri formatı. Lütfen tekrar deneyin.'})
        except ValueError as e:
            import logging
            logger = logging.getLogger(__name__)
            try:
                logger.error(f"ValueError: {str(e)}")
            except:
                pass
            return JsonResponse({'success': False, 'message': 'Koordinat bilgisi geçersiz. Lütfen konum iznini kontrol edin.'})
        except VisitTask.DoesNotExist:
            import logging
            logger = logging.getLogger(__name__)
            try:
                logger.error(f"VisitTask bulunamadı - Task ID: {task_id}")
            except:
                pass
            return JsonResponse({'success': False, 'message': 'Ziyaret görevi bulunamadı.'})
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            try:
                logger.error(f"Genel hata: {str(e)}", exc_info=True)
            except:
                pass
            return JsonResponse({'success': False, 'message': f'Bir hata oluştu: {str(e)}'})

    return JsonResponse({'success': False, 'message': 'Hatalı İstek - POST metodu bekleniyor.'})

# Zorunlu anketleri kontrol et
@csrf_exempt
@login_required
def check_required_surveys(request, task_id):
    """Ziyareti bitirmeden önce zorunlu anketlerin tamamlanıp tamamlanmadığını kontrol eder"""
    task = get_object_or_404(VisitTask, pk=task_id)
    if task.merch_code != request.user.username:
        return JsonResponse({'success': False, 'message': 'Yetkisiz.'}, status=403)
    
    # Bu görev için gösterilen tüm anketleri al
    surveys = Survey.objects.filter(is_active=True)
    from datetime import date
    today = date.today()
    surveys = surveys.filter(
        models.Q(start_date__isnull=True) | models.Q(start_date__lte=today)
    ).filter(
        models.Q(end_date__isnull=True) | models.Q(end_date__gte=today)
    )
    
    # Filtreleme (mobile_task_detail ile aynı mantık)
    user = request.user
    customer = task.customer
    filtered_surveys = []
    
    for survey in surveys:
        should_show = True
        
        if survey.filter_users.exists():
            if user not in survey.filter_users.all():
                should_show = False
        
        if survey.target_roles.exists():
            if not user.role or user.role not in survey.target_roles.all():
                should_show = False
        
        if survey.user_custom_filters:
            for field_slug, allowed_values in survey.user_custom_filters.items():
                if allowed_values:
                    user_value_str = user.extra_data.get(field_slug, '') if user.extra_data else ''
                    user_tags = [tag.strip() for tag in str(user_value_str).split(',') if tag.strip()]
                    if not any(tag in allowed_values for tag in user_tags):
                        should_show = False
                        break
        
        if survey.filter_customers.exists():
            if customer not in survey.filter_customers.all():
                should_show = False
        
        if survey.filter_caris.exists():
            if not customer.cari or customer.cari not in survey.filter_caris.all():
                should_show = False
        
        if survey.custom_filters:
            for field_slug, allowed_values in survey.custom_filters.items():
                if allowed_values:
                    customer_value = customer.extra_data.get(field_slug, '') if customer.extra_data else ''
                    if customer_value not in allowed_values:
                        should_show = False
                        break
        
        if should_show:
            filtered_surveys.append(survey)
    
    # Zorunlu soruları kontrol et
    missing_required = []
    for survey in filtered_surveys:
        # Bu anketin tüm zorunlu sorularını al
        all_questions = survey.questions.all()
        required_questions = [q for q in all_questions if q.required]
        
        # Bu görev için bu anketin sorularına verilen cevapları kontrol et
        for req_q in required_questions:
            answer = SurveyAnswer.objects.filter(task=task, question=req_q).first()
            if not answer or (not answer.answer_text and not answer.answer_photo):
                missing_required.append(survey)
                break  # Bu anket eksik, diğer sorularına bakmaya gerek yok
    
    return JsonResponse({
        'missing_required': [{'id': s.id, 'title': s.title} for s in missing_required],
        'all_completed': len(missing_required) == 0
    })

# Ziyareti bitir
@csrf_exempt
@login_required
def finish_visit(request, task_id):
    """Ziyareti tamamla - Sadece buton ile bitirilebilir, zorunlu formlar kontrol edilir"""
    task = get_object_or_404(VisitTask, pk=task_id)
    if task.merch_code != request.user.username:
        return JsonResponse({'success': False, 'message': 'Bu ziyareti bitirme yetkiniz yok.'}, status=403)
    
    # Zorunlu anketleri kontrol et
    surveys = Survey.objects.filter(is_active=True)
    from datetime import date
    today = date.today()
    surveys = surveys.filter(
        models.Q(start_date__isnull=True) | models.Q(start_date__lte=today)
    ).filter(
        models.Q(end_date__isnull=True) | models.Q(end_date__gte=today)
    )
    
    user = request.user
    customer = task.customer
    filtered_surveys = []
    
    for survey in surveys:
        should_show = True
        
        if survey.filter_users.exists():
            if user not in survey.filter_users.all():
                should_show = False
        
        if survey.target_roles.exists():
            if not user.role or user.role not in survey.target_roles.all():
                should_show = False
        
        if survey.user_custom_filters:
            for field_slug, allowed_values in survey.user_custom_filters.items():
                if allowed_values:
                    user_value_str = user.extra_data.get(field_slug, '') if user.extra_data else ''
                    user_tags = [tag.strip() for tag in str(user_value_str).split(',') if tag.strip()]
                    if not any(tag in allowed_values for tag in user_tags):
                        should_show = False
                        break
        
        if survey.filter_customers.exists():
            if customer not in survey.filter_customers.all():
                should_show = False
        
        if survey.filter_caris.exists():
            if not customer.cari or customer.cari not in survey.filter_caris.all():
                should_show = False
        
        if survey.custom_filters:
            for field_slug, allowed_values in survey.custom_filters.items():
                if allowed_values:
                    customer_value = customer.extra_data.get(field_slug, '') if customer.extra_data else ''
                    if customer_value not in allowed_values:
                        should_show = False
                        break
        
        if should_show:
            filtered_surveys.append(survey)
    
    # Zorunlu soruları kontrol et
    missing_required = []
    for survey in filtered_surveys:
        all_questions = survey.questions.all()
        required_questions = [q for q in all_questions if q.required]
        
        for req_q in required_questions:
            answer = SurveyAnswer.objects.filter(task=task, question=req_q).first()
            if not answer or (not answer.answer_text and not answer.answer_photo):
                missing_required.append(survey)
                break
    
    if missing_required:
        return JsonResponse({
            'success': False,
            'message': 'Zorunlu anketler tamamlanmadan ziyaret bitirilemez.',
            'missing_required': [{'id': s.id, 'title': s.title} for s in missing_required]
        })
    
    # Tüm kontroller geçildi, ziyareti bitir
    from datetime import datetime
    task.status = 'completed'
    task.check_out_time = datetime.now()
    task.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Ziyaret başarıyla tamamlandı.'
    })

# Gezinme sınırını getir
@csrf_exempt
def get_wander_radius(request):
    """Gezinme sınırı ayarını döndürür"""
    setting = SystemSetting.objects.filter(key='wander_radius').first()
    wander_radius = float(setting.value) if setting else 500.0  # Varsayılan 500m
    return JsonResponse({'wander_radius': wander_radius})

@csrf_exempt
@login_required
def get_data_sync_interval(request):
    """Veri paylaşma süresini (dakika) döndürür"""
    setting = SystemSetting.objects.filter(key='data_sync_interval_minutes').first()
    interval = int(setting.value) if setting else 15  # Varsayılan 15 dakika
    return JsonResponse({'interval_minutes': interval})

@login_required
def mobile_sync_pending_data(request):
    """Bekleyen form verilerini hemen gönder"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Sadece POST istekleri kabul edilir.'}, status=405)
    
    try:
        # localStorage'dan bekleyen form verilerini al (JavaScript tarafından gönderilecek)
        import json
        data = json.loads(request.body) if request.body else {}
        pending_forms = data.get('pending_forms', [])
        
        success_count = 0
        error_count = 0
        
        for form_data in pending_forms:
            try:
                task_id = form_data.get('task_id')
                survey_id = form_data.get('survey_id')
                answers = form_data.get('answers', {})
                
                task = VisitTask.objects.get(pk=task_id, merch_code=request.user.username)
                survey = Survey.objects.get(pk=survey_id)
                
                # Form verilerini kaydet
                for q_id, answer_data in answers.items():
                    question = Question.objects.get(pk=q_id, survey=survey)
                    text_val = answer_data.get('text')
                    photo_b64 = answer_data.get('photo_base64')
                    
                    # Eski cevabı sil
                    SurveyAnswer.objects.filter(task=task, question=question).delete()
                    
                    # Fotoğraf varsa işle
                    photo_val = None
                    if photo_b64 and photo_b64.startswith('data:image/'):
                        try:
                            header, b64data = photo_b64.split(',', 1)
                            ext = 'jpg'
                            if 'image/png' in header:
                                ext = 'png'
                            elif 'image/webp' in header:
                                ext = 'webp'
                            
                            import base64
                            decoded = base64.b64decode(b64data)
                            photo_val = ContentFile(decoded, name=f"survey_{task_id}_{q_id}.{ext}")
                        except Exception:
                            pass
                    
                    # Yeni cevabı kaydet
                    if text_val or photo_val:
                        SurveyAnswer.objects.create(
                            task=task,
                            question=question,
                            answer_text=text_val,
                            answer_photo=photo_val
                        )
                
                success_count += 1
            except Exception as e:
                error_count += 1
                print(f"Form gönderim hatası: {str(e)}")
        
        return JsonResponse({
            'success': True,
            'message': f'{success_count} form gönderildi.',
            'success_count': success_count,
            'error_count': error_count
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Hata: {str(e)}'}, status=500)

@csrf_exempt
@login_required
def get_distance_rule(request):
    """Mesafe kuralı ayarını döndürür"""
    setting = SystemSetting.objects.filter(key='distance_rule').first()
    # Eğer eski require_gps ayarı varsa, onu distance_rule olarak kullan
    if not setting:
        old_setting = SystemSetting.objects.filter(key='require_gps').first()
        if old_setting:
            # Eski ayarı yeni isimle güncelle
            old_setting.key = 'distance_rule'
            old_setting.label = 'Mesafe Kuralı'
            old_setting.description = 'Açık: Giriş mesafesi ve gezinme mesafesi kontrolü yapılır. Kapalı: Mesafe kontrolü yapılmaz, herhangi bir mesafeden ziyaret başlatılabilir.'
            old_setting.save()
            setting = old_setting
    
    distance_rule = True  # Varsayılan: açık
    if setting:
        try:
            distance_rule = setting.value.lower() == 'true'
        except:
            distance_rule = True
    
    return JsonResponse({'distance_rule': distance_rule})

@csrf_exempt
@login_required
def check_visit_status(request, task_id):
    """Ziyaretin başlatılıp başlatılmadığını kontrol eder"""
    task = get_object_or_404(VisitTask, pk=task_id)
    if task.merch_code != request.user.username:
        return JsonResponse({'success': False, 'message': 'Yetkisiz.'}, status=403)
    
    # Ziyaret başlatılmışsa check_in_time dolu olur, bitirilmişse check_out_time dolu olur
    is_started = task.check_in_time is not None
    is_finished = task.check_out_time is not None and task.status == 'completed'
    
    return JsonResponse({
        'is_started': is_started and not is_finished,
        'is_finished': is_finished,
        'check_in_time': task.check_in_time.isoformat() if task.check_in_time else None,
        'check_out_time': task.check_out_time.isoformat() if task.check_out_time else None
    })
    
    return JsonResponse({'distance_rule': distance_rule})


@login_required
def mobile_team_member(request, merch_code: str):
    """
    Supervisor view: show today's tasks for a subordinate merch_code.
    """
    user = request.user
    scope = get_hierarchy_scope_for_user(user, include_self=True)
    if scope.usernames and merch_code not in scope.usernames:
        return HttpResponseForbidden("Bu personeli görüntüleme yetkiniz yok.")

    today = date.today()
    tasks = (
        VisitTask.objects.filter(merch_code=merch_code, planned_date=today)
        .select_related("customer")
        .order_by("status", "customer__name")
    )
    total = tasks.count()
    completed = tasks.filter(status="completed").count()
    ctx = {
        "today": today,
        "merch_code": merch_code,
        "tasks": tasks,
        "total": total,
        "completed": completed,
    }
    return render(request, "mobile/team_member_tasks.html", ctx)