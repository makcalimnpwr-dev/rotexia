from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.customer_list, name='customer_list'),
    path('add/', views.add_customer, name='add_customer'),
    path('edit/<int:pk>/', views.edit_customer, name='edit_customer'),
    path('map-view/', views.customer_map_view, name='customer_map_view'),
    path('delete/<int:pk>/', views.delete_customer, name='delete_customer'),
    path('bulk-action/', views.bulk_customer_action, name='bulk_customer_action'),
    path('add-field/', views.add_custom_field, name='add_custom_field'), # YENİ
    
    # ... diğerleri aynı
    path('settings/cari/', views.cari_settings, name='cari_settings'),
    path('settings/cari/delete/<int:pk>/', views.delete_cari, name='delete_cari'),
    path('export/', views.export_customers, name='export_customers'),
    path('import/', views.import_customers, name='import_customers'),
]