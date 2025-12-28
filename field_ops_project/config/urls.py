from django.contrib import admin
from django.urls import path, include
from apps.core import views as core_views
from django.views.generic import TemplateView

urlpatterns = [
    # 1. Admin Paneli
    path('admin/', admin.site.urls),

    # Health check (Render)
    path('healthz/', core_views.healthz, name='healthz'),

    # PWA
    path('manifest.webmanifest', TemplateView.as_view(
        template_name='pwa/manifest.webmanifest',
        content_type='application/manifest+json'
    ), name='pwa_manifest'),
    path('sw.js', TemplateView.as_view(
        template_name='pwa/sw.js',
        content_type='application/javascript'
    ), name='pwa_sw'),
    
    # 2. Giriş / Çıkış İşlemleri (Otomatik Giriş KALDIRILDI)
    # Artık standart giriş sistemini kullanıyoruz
    path('accounts/', include('django.contrib.auth.urls')),
    
    # 3. Modüllerin Adresleri
    path('users/', include('apps.users.urls')),
    path('customers/', include('apps.customers.urls')),
    path('ops/', include('apps.field_operations.urls')),
    
    # --- İŞTE EKSİK OLAN SATIR BU ---
    path('forms/', include('apps.forms.urls')), 
    
    # 4. Mobil Uygulama Kısayolu
    path('app/', core_views.mobile_home, name='mobile_home'),
    
    # 5. Masaüstü Anasayfa (En sonda olmalı)
    path('', include('apps.core.urls')),
]