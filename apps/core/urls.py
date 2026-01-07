from django.urls import path
from . import views
from apps.core import views as core_views

urlpatterns = [
    path('', views.index, name='index'),  # Ana sayfa - firma adı girme
    path('connect/', views.company_connect, name='company_connect'),  # Firma bağlanma
    path('mobile/login/', views.CustomMobileLoginView.as_view(), name='mobile_login'),  # Mobil login
    path('login/<str:tenant_slug>/', views.login_with_tenant, name='login_with_tenant'),  # Firma login sayfası
    path('home/', views.home, name='home'),  # Dashboard (giriş yapıldıktan sonra)
    path('admin-home/', views.admin_home, name='admin_home'),
    path('admin-login/', views.AdminLoginView.as_view(), name='admin_login'),
    path('admin/update-settings/', views.admin_update_settings, name='admin_update_settings'),
    path('company/create/', views.create_company, name='create_company'),
    # path('company/select/<int:tenant_id>/', views.select_company, name='select_company'),  # Devre dışı bırakıldı
    path('company/edit/<int:tenant_id>/', views.edit_tenant, name='edit_tenant'),
    path('company/delete/<int:tenant_id>/', views.delete_tenant, name='delete_tenant'),
    path('company/login/<int:tenant_id>/', views.login_as_tenant_superuser, name='login_as_tenant_superuser'),
    path('company/create-missing-admins/', views.create_missing_admin_users, name='create_missing_admin_users'),
    # ... mevcut urller ...
    path('app/', views.mobile_home, name='mobile_home'), # Mobilin anasayfası
    path('app/team/', views.mobile_team_home, name='mobile_team_home'),
    path('app/team/<str:merch_code>/', views.mobile_team_member, name='mobile_team_member'),
    path('app/profile/', views.mobile_profile, name='mobile_profile'),
    # ... diğer mobil url'ler ...
    path('app/task/<int:pk>/', views.mobile_task_detail, name='mobile_task_detail'),
    # ... mevcut url'lerin altına ...
    path('download-template/<str:template_type>/', views.download_excel_template, name='download_template'),
    # ... diğer mobil url'ler ...
    path('app/task/<int:task_id>/fill/<int:survey_id>/', views.mobile_fill_survey, name='mobile_fill_survey'),
    path('app/task/<int:task_id>/survey/<int:survey_id>/', views.mobile_view_survey, name='mobile_view_survey'),
    path('system-settings/', core_views.settings_home, name='settings_home'),  # Router - admin veya tenant'a yönlendirir
    path('admin-panel/settings/', core_views.admin_settings, name='admin_settings'),  # Admin paneli ayarları (Django admin ile çakışmaması için)
    path('tenant/settings/', core_views.tenant_settings, name='tenant_settings'),  # Firma paneli ayarları
    path('api/start-visit/<int:task_id>/', views.start_visit_check, name='api_start_visit'),
    path('api/check-required-surveys/<int:task_id>/', views.check_required_surveys, name='api_check_required_surveys'),
    path('api/finish-visit/<int:task_id>/', views.finish_visit, name='api_finish_visit'),
    path('api/get-wander-radius/', views.get_wander_radius, name='api_get_wander_radius'),
    path('api/get-distance-rule/', views.get_distance_rule, name='api_get_distance_rule'),
    path('api/check-visit-status/<int:task_id>/', views.check_visit_status, name='api_check_visit_status'),
    path('api/sync-pending-data/', views.mobile_sync_pending_data, name='mobile_sync_pending_data'),
    path('api/get-sync-interval/', views.get_data_sync_interval, name='api_get_data_sync_interval'),
    
    # --- OTOMATIK MAIL ---
    path('automated-email/', views.automated_email_list, name='automated_email_list'),
    path('automated-email/create/', views.automated_email_create, name='automated_email_create'),
    path('automated-email/<int:pk>/edit/', views.automated_email_edit, name='automated_email_edit'),
    path('automated-email/<int:pk>/send-now/', views.automated_email_send_now, name='automated_email_send_now'),
    path('automated-email/<int:pk>/delete/', views.automated_email_delete, name='automated_email_delete'),
]