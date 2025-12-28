from django.contrib import admin
from .models import Customer, CustomerCari

@admin.register(CustomerCari)
class CustomerCariAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    # BURADA DEĞİŞİKLİK YAPTIK: custom_id -> customer_code
    list_display = ('customer_code', 'name', 'cari', 'city', 'phone')
    search_fields = ('name', 'customer_code', 'phone')
    list_filter = ('cari', 'city')