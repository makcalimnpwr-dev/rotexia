from django.urls import path
from . import views
from apps.core import views as core_views

urlpatterns = [
    path('', views.home, name='home'),
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
    path('system-settings/', core_views.settings_home, name='settings_home'),
    path('api/start-visit/<int:task_id>/', views.start_visit_check, name='api_start_visit'),
    path('api/check-required-surveys/<int:task_id>/', views.check_required_surveys, name='api_check_required_surveys'),
    path('api/finish-visit/<int:task_id>/', views.finish_visit, name='api_finish_visit'),
    path('api/get-wander-radius/', views.get_wander_radius, name='api_get_wander_radius'),
    path('api/get-distance-rule/', views.get_distance_rule, name='api_get_distance_rule'),
    path('api/check-visit-status/<int:task_id>/', views.check_visit_status, name='api_check_visit_status'),
    path('api/sync-pending-data/', views.mobile_sync_pending_data, name='mobile_sync_pending_data'),
    path('api/get-sync-interval/', views.get_data_sync_interval, name='api_get_data_sync_interval'),
]