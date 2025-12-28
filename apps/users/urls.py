from django.urls import path
from . import views
from apps.core import views as core_views

urlpatterns = [
    # Ayarlar Ana Sayfası
    path('settings/', views.settings_home, name='settings_home'),
    
    # Rol Yönetimi
    path('settings/roles/', views.role_list, name='role_list'),
    path('settings/roles/delete/<int:pk>/', views.role_delete, name='role_delete'),

    # Kullanıcı İşlemleri
    path('list/', views.user_list, name='user_list'),
    path('add/', views.add_user, name='add_user'),
    path('edit/<int:pk>/', views.edit_user, name='edit_user'),
    path('delete/<int:pk>/', views.delete_user, name='delete_user'),
    path('toggle-status/<int:pk>/', views.toggle_user_status, name='toggle_user_status'),
    path('export/', views.export_users, name='export_users'),
    path('import/', views.import_users, name='import_users'),
    path('add-field/', views.add_user_field, name='add_user_field'),

    # Hiyerarşi
    path('hierarchy/', views.hierarchy, name='hierarchy'),
    path('hierarchy/create-node/', views.hierarchy_create_node, name='hierarchy_create_node'),
    path('hierarchy/set-parent/', views.hierarchy_set_parent, name='hierarchy_set_parent'),
    path('hierarchy/assign-user/', views.hierarchy_assign_user, name='hierarchy_assign_user'),
    path('hierarchy/unassign-user/', views.hierarchy_unassign_user, name='hierarchy_unassign_user'),
    path('hierarchy/delete-node/', views.hierarchy_delete_node, name='hierarchy_delete_node'),
    # Eski endpoint (geriye dönük): artık kullanılmıyor
    path('hierarchy/users/', views.hierarchy_users_for_authority, name='hierarchy_users_for_authority'),
]