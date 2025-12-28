from django.urls import path
from . import views

urlpatterns = [
    path('routes/', views.route_plan_list, name='route_plan_list'),
    path('routes/import/', views.import_route_plan, name='import_route_plan'),
    path('routes/sync/', views.sync_merch_routes, name='sync_merch_routes'),
    path('routes/details/', views.get_route_day_details, name='get_route_day_details'),
    path('routes/action/', views.action_route_day, name='action_route_day'),
    path('routes/bulk-add-day/', views.route_bulk_add_day, name='route_bulk_add_day'),
    path('routes/search-customer/', views.search_customer_api, name='search_customer_api'),
    path('routes/import/', views.import_route_plan, name='import_route_plan'),
    path('routes/add-store/', views.add_store_to_route, name='add_store_to_route'),
    # ... diğer url'lerin arasına ekle ...
    path('routes/bulk-delete/', views.route_bulk_delete, name='route_bulk_delete'),
    path('routes/api/remove-day/', views.route_remove_day_api, name='route_remove_day_api'),
    path('routes/api/replace-store/', views.route_replace_store_api, name='route_replace_store_api'),
    
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/edit/<int:pk>/', views.edit_task, name='edit_task'), # YENİ: Düzenleme Sayfası
    path('tasks/bulk-action/', views.bulk_task_action, name='bulk_task_action'), # YENİ: Toplu İşlem
    path('tasks/create/', views.create_manual_task, name='create_manual_task'),
    path('settings/types/', views.settings_visit_types, name='settings_visit_types'),
    path('tasks/map/', views.task_map_view, name='task_map_view'),
    path('tasks/import/', views.import_tasks, name='import_tasks'),
    path('tasks/generate/', views.generate_daily_tasks, name='generate_daily_tasks'),
    path('tasks/export/', views.export_tasks, name='export_tasks'),

    # --- RAPORLAR ---
    path('reports/', views.reports_home, name='reports_home'),
    path('reports/visit-detail/', views.visit_detail_report, name='visit_detail_report'),
    path('reports/visit-detail/export/', views.visit_detail_report_export, name='visit_detail_report_export'),
    path('reports/daily-summary/', views.daily_visit_summary_report, name='daily_visit_summary_report'),
    path('reports/daily-summary/prefs/', views.daily_visit_summary_save_prefs, name='daily_visit_summary_save_prefs'),

    # --- ANKET RAPORLARI ---
    path('reports/surveys/', views.survey_reports_home, name='survey_reports_home'),
    path('reports/surveys/<int:survey_id>/create/', views.survey_report_create, name='survey_report_create'),
    path('reports/surveys/<int:survey_id>/', views.survey_report, name='survey_report'),
    path('reports/surveys/<int:survey_id>/export/', views.survey_report_export, name='survey_report_export'),
    path('reports/surveys/<int:survey_id>/import/', views.survey_report_import, name='survey_report_import'),
    path('reports/surveys/<int:survey_id>/submission/<int:task_id>/edit/', views.survey_submission_edit, name='survey_submission_edit'),
    path('reports/surveys/<int:survey_id>/submission/<int:task_id>/delete/', views.survey_submission_delete, name='survey_submission_delete'),

    # --- ÇÖP KUTUSU (Raporlar) ---
    path('reports/trash/', views.reports_trash, name='reports_trash'),
    path('reports/trash/settings/', views.reports_trash_settings, name='reports_trash_settings'),
    path('reports/trash/<int:report_id>/restore/', views.reports_trash_restore, name='reports_trash_restore'),
    path('reports/trash/<int:report_id>/delete-now/', views.reports_trash_delete_now, name='reports_trash_delete_now'),
    path('reports/<int:report_id>/delete/', views.report_move_to_trash, name='report_move_to_trash'),
]