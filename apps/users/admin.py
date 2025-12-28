from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserFieldDefinition, AuthorityNode
from .utils import ensure_root_admin_configured, is_root_admin

class CustomUserAdmin(UserAdmin):
    # Admin panelindeki kullanıcı listesinde görünecek sütunlar
    list_display = ('user_code', 'username', 'first_name', 'last_name', 'authority', 'phone', 'is_staff')
    
    # Kullanıcı arama kutusunun hangi alanlara bakacağı
    search_fields = ('user_code', 'username', 'first_name', 'last_name')

    # Kullanıcı düzenleme ekranına yeni alanları ekliyoruz
    fieldsets = UserAdmin.fieldsets + (
        ('Ekstra Bilgiler', {'fields': ('user_code', 'authority', 'phone')}),
    )
    
    # Yeni kullanıcı ekleme ekranına da bu alanları ekliyoruz
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('user_code', 'authority', 'phone', 'email')}),
    )

    def has_delete_permission(self, request, obj=None):
        ensure_root_admin_configured(request.user)
        if obj and is_root_admin(obj):
            return False
        return super().has_delete_permission(request, obj=obj)

    def has_change_permission(self, request, obj=None):
        ensure_root_admin_configured(request.user)
        if obj and is_root_admin(obj):
            return False
        return super().has_change_permission(request, obj=obj)

@admin.register(UserFieldDefinition)
class UserFieldDefinitionAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(CustomUser, CustomUserAdmin)


@admin.register(AuthorityNode)
class AuthorityNodeAdmin(admin.ModelAdmin):
    list_display = ('id', 'authority', 'label', 'parent', 'assigned_user', 'sort_order')
    list_filter = ('authority',)
    search_fields = ('label', 'assigned_user__user_code', 'assigned_user__first_name', 'assigned_user__last_name')
    ordering = ('sort_order', 'id')

    def has_delete_permission(self, request, obj=None):
        if obj and obj.authority == "Admin":
            return False
        return super().has_delete_permission(request, obj=obj)

    def has_change_permission(self, request, obj=None):
        if obj and obj.authority == "Admin":
            return False
        return super().has_change_permission(request, obj=obj)