from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserFieldDefinition

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

@admin.register(UserFieldDefinition)
class UserFieldDefinitionAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(CustomUser, CustomUserAdmin)