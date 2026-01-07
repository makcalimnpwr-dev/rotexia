from django.db import models
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class SiteSetting(models.Model):
    """
    Sistem genel ayarlarını tutan Singleton (Tekil) model.
    Sadece 1 kayıt olmasını garanti altına alacağız.
    """
    site_title = models.CharField(max_length=200, default="Rotexia Platform", verbose_name="Site Başlığı")
    logo = models.ImageField(upload_to='site_branding/', blank=True, null=True, verbose_name="Site Logosu")
    
    # Renk Ayarları (CSS Değişkenleri için)
    primary_color = models.CharField(max_length=7, default="#0d6efd", verbose_name="Ana Renk (Primary)")
    secondary_color = models.CharField(max_length=7, default="#6c757d", verbose_name="İkincil Renk (Secondary)")
    
    def save(self, *args, **kwargs):
        # Cache'i temizle ki değişiklik anında yansısın
        cache.delete('site_settings')
        self.__class__.objects.exclude(id=self.id).delete() # Sadece tek kayıt kalsın
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        """
        Ayarları veritabanından çeker, yoksa varsayılan oluşturur.
        Cache kullanarak performansı artırır (Her sayfada DB sorgusu yapmaz).
        """
        objects = cache.get('site_settings')
        if objects is None:
            objects, created = cls.objects.get_or_create(pk=1)
            cache.set('site_settings', objects)
        return objects

    def __str__(self):
        return "Site Konfigürasyonu"

    class Meta:
        verbose_name = "Site Ayarı"
        verbose_name_plural = "Site Ayarları"

# ... Yukarıda mevcut importlar ve diğer modeller (VisitTask vb.) var ...

class SystemSetting(models.Model):
    CATEGORY_CHOICES = [
        ('general', 'Genel Sistem Ayarları'),
        ('visit', 'Ziyaret & Konum Ayarları'),
        ('user', 'Kullanıcı & Personel Ayarları'),
        ('notification', 'Bildirim Ayarları'),
        ('email', 'E-posta Ayarları'),
    ]

    INPUT_TYPES = [
        ('text', 'Yazı'),
        ('number', 'Sayı'),
        ('bool', 'Açık/Kapalı (Checkbox)'),
        ('password', 'Şifre (Gizli)'),
    ]

    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, null=True, blank=True, related_name='settings', verbose_name="Firma", help_text="Boş ise global/şablon ayarı (Rotexia), dolu ise firma-specific ayar")
    key = models.CharField(max_length=100, verbose_name="Ayar Anahtarı (Kod)")
    label = models.CharField(max_length=200, verbose_name="Ekranda Görünen İsim")
    value = models.TextField(verbose_name="Değer")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    input_type = models.CharField(max_length=10, choices=INPUT_TYPES, default='text')
    description = models.CharField(max_length=300, blank=True, null=True, verbose_name="Açıklama")

    def __str__(self):
        return f"{self.label}: {self.value}"

    class Meta:
        verbose_name = "Sistem Ayarı (YENI)"
        verbose_name_plural = "Sistem Ayarları"
        ordering = ['category', 'id']
        unique_together = [['key', 'tenant']]  # Aynı key'den her tenant için bir tane olabilir


# ============================================================================
# SAAS MULTI-TENANCY MODELLERİ
# ============================================================================

class Plan(models.Model):
    """
    Abonelik planları (Basic, Pro, Enterprise)
    """
    PLAN_TYPES = [
        ('basic', 'Temel'),
        ('pro', 'Profesyonel'),
        ('enterprise', 'Kurumsal'),
    ]
    
    name = models.CharField(max_length=50, unique=True, verbose_name="Plan Adı")
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, verbose_name="Plan Tipi")
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Aylık Fiyat")
    price_yearly = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Yıllık Fiyat")
    
    # Limitler
    max_users = models.IntegerField(default=5, verbose_name="Maksimum Kullanıcı Sayısı")
    max_customers = models.IntegerField(default=50, verbose_name="Maksimum Müşteri Sayısı")
    max_tasks_per_month = models.IntegerField(default=500, verbose_name="Aylık Maksimum Görev")
    max_storage_gb = models.IntegerField(default=5, verbose_name="Maksimum Depolama (GB)")
    
    # Özellikler
    has_advanced_reports = models.BooleanField(default=False, verbose_name="Gelişmiş Raporlar")
    has_api_access = models.BooleanField(default=False, verbose_name="API Erişimi")
    has_custom_branding = models.BooleanField(default=False, verbose_name="Özel Markalama")
    has_priority_support = models.BooleanField(default=False, verbose_name="Öncelikli Destek")
    
    is_active = models.BooleanField(default=True, verbose_name="Aktif mi?")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.price_monthly}₺/ay"
    
    class Meta:
        verbose_name = "Abonelik Planı"
        verbose_name_plural = "Abonelik Planları"
        ordering = ['price_monthly']


class Tenant(models.Model):
    """
    SaaS Multi-Tenancy: Her şirket/organizasyon bir Tenant
    """
    name = models.CharField(max_length=200, verbose_name="Şirket Adı")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="URL Slug")
    
    # İletişim Bilgileri
    email = models.EmailField(verbose_name="İletişim E-postası")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefon")
    address = models.TextField(blank=True, null=True, verbose_name="Adres")
    
    # Abonelik Bilgileri
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, verbose_name="Abonelik Planı")
    subscription_start = models.DateTimeField(null=True, blank=True, verbose_name="Abonelik Başlangıcı")
    subscription_end = models.DateTimeField(null=True, blank=True, verbose_name="Abonelik Bitişi")
    is_active = models.BooleanField(default=True, verbose_name="Aktif mi?")
    
    # Özelleştirmeler
    logo = models.ImageField(upload_to='tenant_logos/', blank=True, null=True, verbose_name="Logo")
    primary_color = models.CharField(max_length=7, default="#0d6efd", verbose_name="Ana Renk")
    
    # Menü Görünürlük Ayarları (JSON)
    # Örn: {"hierarchy": true, "users": true, "customers": true, "tasks": true, "route_plan": true, "forms": true, "images": false, "reports": true}
    menu_settings = models.JSONField(default=dict, blank=True, verbose_name="Menü Ayarları", help_text="Hangi menülerin görünür olacağını belirler")
    
    # Firma Superuser Bilgileri (Firma başına bir superuser)
    superuser_username = models.CharField(max_length=150, blank=True, null=True, verbose_name="Superuser Kullanıcı Adı", help_text="Bu firmaya ait superuser'ın kullanıcı adı")
    superuser_plain_password = models.CharField(max_length=128, blank=True, null=True, verbose_name="Superuser Şifresi", help_text="Şifre düz metin olarak saklanır (sadece görüntüleme için)")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def is_subscription_active(self):
        """Abonelik aktif mi kontrol et"""
        if not self.is_active or not self.plan:
            return False
        if self.subscription_end:
            return timezone.now() < self.subscription_end
        return True
    
    def days_until_expiry(self):
        """Abonelik bitişine kalan gün sayısı"""
        if not self.subscription_end:
            return None
        delta = self.subscription_end - timezone.now()
        return delta.days
    
    class Meta:
        verbose_name = "Kiracı (Tenant)"
        verbose_name_plural = "Kiracılar (Tenants)"
        ordering = ['-created_at']


class Subscription(models.Model):
    """
    Abonelik geçmişi ve ödeme kayıtları
    """
    STATUS_CHOICES = [
        ('active', 'Aktif'),
        ('cancelled', 'İptal Edildi'),
        ('expired', 'Süresi Doldu'),
        ('trial', 'Deneme'),
    ]
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='subscriptions', verbose_name="Kiracı")
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, verbose_name="Plan")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trial', verbose_name="Durum")
    start_date = models.DateTimeField(verbose_name="Başlangıç Tarihi")
    end_date = models.DateTimeField(null=True, blank=True, verbose_name="Bitiş Tarihi")
    
    # Ödeme Bilgileri
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Tutar")
    payment_method = models.CharField(max_length=50, blank=True, null=True, verbose_name="Ödeme Yöntemi")
    payment_date = models.DateTimeField(null=True, blank=True, verbose_name="Ödeme Tarihi")
    invoice_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Fatura No")
    
    notes = models.TextField(blank=True, null=True, verbose_name="Notlar")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.tenant.name} - {self.plan.name if self.plan else 'Plan Yok'} ({self.status})"
    
    class Meta:
        verbose_name = "Abonelik"
        verbose_name_plural = "Abonelikler"
        ordering = ['-created_at']


class AutomatedEmail(models.Model):
    """
    Otomatik mail gönderme sistemi
    Raporları periyodik olarak e-posta ile gönderir
    """
    PERIOD_CHOICES = [
        ('daily', 'Her Gün'),
        ('weekly', 'Her Hafta'),
        ('monthly', 'Her Ay'),
    ]
    
    DAY_CHOICES = [
        ('every_day', 'Her Gün'),
        ('monday', 'Her Pazartesi'),
        ('first_of_month', 'Her Ayın İlk Günü'),
    ]
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='automated_emails', verbose_name="Firma")
    
    # Mail Bilgileri
    to_email = models.TextField(verbose_name="Kime", help_text="Virgülle ayırarak birden fazla e-posta adresi ekleyebilirsiniz")
    cc_email = models.TextField(blank=True, null=True, verbose_name="CC", help_text="Virgülle ayırarak birden fazla e-posta adresi ekleyebilirsiniz")
    subject = models.CharField(max_length=500, verbose_name="Konu")
    body = models.TextField(verbose_name="Mail İçeriği")
    
    # Rapor Ayarları
    # Raporlar JSON formatında saklanacak: {"visit_detail": true, "daily_summary": true, "survey_1": true, ...}
    selected_reports = models.JSONField(default=dict, verbose_name="Seçili Raporlar", help_text="Hangi raporların gönderileceği")
    merge_reports = models.BooleanField(default=False, verbose_name="Raporları Birleştir", help_text="İşaretlenirse tüm raporlar tek Excel dosyasında sheet olarak gönderilir")
    
    # Rapor Tarih Aralığı
    report_start_date = models.DateField(verbose_name="Rapor Başlangıç Tarihi")
    report_end_date = models.DateField(verbose_name="Rapor Bitiş Tarihi")
    
    # Gönderim Ayarları
    send_start_date = models.DateField(verbose_name="Gönderim Başlangıç Tarihi", help_text="Hangi tarihte gönderilmeye başlansın")
    send_end_date = models.DateField(null=True, blank=True, verbose_name="Gönderim Bitiş Tarihi", help_text="Mail gönderiminin son tarihi (opsiyonel)")
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES, verbose_name="Periyot")
    day_option = models.CharField(max_length=20, choices=DAY_CHOICES, verbose_name="Hangi Gün")
    send_time = models.TimeField(verbose_name="Gönderim Saati", help_text="Raporun gönderileceği saat (örn: 22:00)")
    
    # Durum
    is_active = models.BooleanField(default=True, verbose_name="Aktif mi?")
    last_sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Son Gönderim Tarihi")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_automated_emails', verbose_name="Oluşturan")
    
    def __str__(self):
        return f"{self.subject} - {self.tenant.name}"
    
    def get_to_emails_list(self):
        """Kime alanını liste olarak döndürür"""
        if not self.to_email:
            return []
        return [email.strip() for email in self.to_email.split(',') if email.strip()]
    
    def get_cc_emails_list(self):
        """CC alanını liste olarak döndürür"""
        if not self.cc_email:
            return []
        return [email.strip() for email in self.cc_email.split(',') if email.strip()]
    
    def should_send_today(self):
        """Bugün gönderilmeli mi kontrol eder"""
        from datetime import date, datetime
        
        today = date.today()
        now = datetime.now().time()
        
        # Aktif değilse gönderme
        if not self.is_active:
            return False
        
        # Gönderim başlangıç tarihi geçmediyse gönderme
        if today < self.send_start_date:
            return False
        
        # Gönderim bitiş tarihi varsa ve geçtiyse gönderme
        if self.send_end_date and today > self.send_end_date:
            return False
        
        # Saat kontrolü - gönderim saatinden önceyse gönderme
        if now < self.send_time:
            return False
        
        # Periyot kontrolü
        if self.period == 'daily':
            return self.day_option == 'every_day'
        elif self.period == 'weekly':
            return today.weekday() == 0 and self.day_option == 'monday'  # 0 = Pazartesi
        elif self.period == 'monthly':
            return today.day == 1 and self.day_option == 'first_of_month'
        
        return False
    
    class Meta:
        verbose_name = "Otomatik Mail"
        verbose_name_plural = "Otomatik Mailler"
        ordering = ['-created_at']