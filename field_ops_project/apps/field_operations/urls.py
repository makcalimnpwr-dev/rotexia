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
]