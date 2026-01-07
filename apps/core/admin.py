from django.contrib import admin
from .models import SiteSetting, SystemSetting, Tenant, Plan, Subscription, AutomatedEmail


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    # Kullanıcının yanlışlıkla silmesini engelleyelim
    def has_delete_permission(self, request, obj=None):
        return False
    
    # Yeni eklemeyi engelleyelim (zaten 1 tane var)
    def has_add_permission(self, request):
        return not SiteSetting.objects.exists()


@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ['key', 'label', 'category', 'value', 'input_type']
    list_filter = ['category', 'input_type']
    search_fields = ['key', 'label']


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'plan_type', 'price_monthly', 'max_users', 'max_customers', 'is_active']
    list_filter = ['plan_type', 'is_active']
    search_fields = ['name']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('name', 'plan_type', 'is_active')
        }),
        ('Fiyatlandırma', {
            'fields': ('price_monthly', 'price_yearly')
        }),
        ('Limitler', {
            'fields': ('max_users', 'max_customers', 'max_tasks_per_month', 'max_storage_gb')
        }),
        ('Özellikler', {
            'fields': ('has_advanced_reports', 'has_api_access', 'has_custom_branding', 'has_priority_support')
        }),
    )


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'plan', 'is_active', 'is_subscription_active', 'created_at']
    list_filter = ['is_active', 'plan', 'created_at']
    search_fields = ['name', 'slug', 'email']
    readonly_fields = ['created_at', 'updated_at', 'days_until_expiry_display']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('name', 'slug', 'is_active')
        }),
        ('İletişim', {
            'fields': ('email', 'phone', 'address')
        }),
        ('Abonelik', {
            'fields': ('plan', 'subscription_start', 'subscription_end', 'days_until_expiry_display')
        }),
        ('Özelleştirmeler', {
            'fields': ('logo', 'primary_color')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def days_until_expiry_display(self, obj):
        """Abonelik bitişine kalan gün sayısını göster"""
        days = obj.days_until_expiry()
        if days is None:
            return "Sınırsız"
        if days < 0:
            return f"❌ {abs(days)} gün önce doldu"
        if days < 7:
            return f"⚠️ {days} gün kaldı"
        return f"✅ {days} gün kaldı"
    days_until_expiry_display.short_description = "Abonelik Durumu"
    
    def is_subscription_active(self, obj):
        """Abonelik aktif mi?"""
        return "✅" if obj.is_subscription_active() else "❌"
    is_subscription_active.short_description = "Aktif Abonelik"
    is_subscription_active.boolean = True


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'plan', 'status', 'start_date', 'end_date', 'amount', 'payment_date']
    list_filter = ['status', 'plan', 'payment_date', 'start_date']
    search_fields = ['tenant__name', 'invoice_number']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Abonelik Bilgileri', {
            'fields': ('tenant', 'plan', 'status')
        }),
        ('Tarihler', {
            'fields': ('start_date', 'end_date')
        }),
        ('Ödeme', {
            'fields': ('amount', 'payment_method', 'payment_date', 'invoice_number')
        }),
        ('Notlar', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(AutomatedEmail)
class AutomatedEmailAdmin(admin.ModelAdmin):
    list_display = ['subject', 'tenant', 'is_active', 'period', 'send_time', 'last_sent_at', 'created_at']
    list_filter = ['is_active', 'period', 'tenant', 'created_at']
    search_fields = ['subject', 'to_email', 'tenant__name']
    readonly_fields = ['created_at', 'updated_at', 'last_sent_at']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('tenant', 'is_active', 'created_by')
        }),
        ('Mail Bilgileri', {
            'fields': ('to_email', 'cc_email', 'subject', 'body')
        }),
        ('Rapor Ayarları', {
            'fields': ('selected_reports', 'merge_reports', 'report_start_date', 'report_end_date')
        }),
        ('Gönderim Ayarları', {
            'fields': ('send_start_date', 'send_end_date', 'period', 'day_option', 'send_time')
        }),
        ('Metadata', {
            'fields': ('last_sent_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )