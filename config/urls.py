from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
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
    
    # 2. Giriş / Çıkış İşlemleri
    path('accounts/login/', core_views.CustomLoginView.as_view(), name='login'),  # Legacy support
    path('accounts/logout/', core_views.logout_view, name='logout'),
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

# Media files (sadece development için, production'da web server halledecek)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)