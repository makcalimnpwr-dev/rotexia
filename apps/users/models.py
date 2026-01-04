from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

# 1. DİNAMİK ROL TABLOSU
class UserRole(models.Model):
    name = models.CharField(max_length=50, verbose_name="Rol Adı")
    description = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    
    # Multi-Tenancy: Her rol bir tenant'a ait
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        verbose_name="Firma",
        null=True,
        blank=True,
        related_name='user_roles'
    )
    
    def save(self, *args, **kwargs):
        # DEBUG: Tenant kontrolü
        if not self.tenant_id and not self.pk:
            # Yeni rol oluşturuluyor ama tenant yok - bu bir hata olabilir
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"UserRole.save: Rol '{self.name}' tenant olmadan kaydediliyor! tenant_id={self.tenant_id}")
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Kullanıcı Rolü"
        verbose_name_plural = "Kullanıcı Rolleri"
        unique_together = [('name', 'tenant')]  # Aynı tenant içinde benzersiz

# 2. KULLANICI ÖZEL ALAN TANIMLARI (Müşterilerdeki gibi)
class UserFieldDefinition(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Alan Adı")
    slug = models.SlugField(max_length=50, unique=True, verbose_name="Slug", blank=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            # Türkçe karakterleri düzelt
            turkish_map = {'ı': 'i', 'ğ': 'g', 'ü': 'u', 'ş': 's', 'ö': 'o', 'ç': 'c', 'İ': 'I', 'Ğ': 'G', 'Ü': 'U', 'Ş': 'S', 'Ö': 'O', 'Ç': 'C'}
            name_clean = self.name
            for tr, en in turkish_map.items():
                name_clean = name_clean.replace(tr, en)
            self.slug = slugify(name_clean)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Kullanıcı Özel Alan Tanımı"
        verbose_name_plural = "Kullanıcı Özel Alan Tanımları"

# 3. KULLANICI TABLOSU
class CustomUser(AbstractUser):
    AUTHORITY_CHOICES = [
        ('Admin', 'Admin'),
        ('Proje Müdürü', 'Proje Müdürü'),
        ('Proje Sorumlusu', 'Proje Sorumlusu'),
        ('Bölge Sorumlusu', 'Bölge Sorumlusu'),
        ('Supervisor', 'Supervisor'),
        ('Satış Sorumlusu', 'Satış Sorumlusu'),
        ('Müşteri', 'Müşteri'),
        ('Saha Ekibi', 'Saha Ekibi'),
        ('Uzman', 'Uzman'),
        ('Günlükçü Personel', 'Günlükçü Personel'),
    ]

    # Username'i override et - tenant slug ile birleştirilerek unique olacak
    # Format: {tenant_slug}_{user_code} (örn: pastel_merch1)
    username = models.CharField(
        max_length=150,
        unique=True,  # Django USERNAME_FIELD gereksinimi için unique olmalı
        verbose_name="Kullanıcı Adı",
        help_text="Otomatik oluşturulur: {firma}_{kod}",
        validators=[AbstractUser.username_validator],
        error_messages={
            'unique': "Bu kullanıcı adı zaten kullanılıyor.",
        },
    )

    user_code = models.CharField(max_length=20, verbose_name="Kullanıcı Kodu")
    phone = models.CharField(max_length=15, blank=True, null=True, verbose_name="Telefon")
    email = models.EmailField(blank=True, null=True, verbose_name="E-posta")
    
    # ARTIK CHOICES YOK, FOREIGN KEY VAR
    role = models.ForeignKey(
        UserRole, 
        on_delete=models.SET_NULL, # Rol silinirse kullanıcı silinmesin, boş kalsın
        null=True, 
        blank=True, 
        verbose_name="Kullanıcı Rolü",
        related_name="users"
    )
    
    # Dinamik özel alanlar (müşterilerdeki gibi)
    extra_data = models.JSONField(default=dict, blank=True, verbose_name="Özel Veriler")

    # Yeni: Sabit Yetki Alanı (Hiyerarşi için)
    authority = models.CharField(
        max_length=30,
        choices=AUTHORITY_CHOICES,
        default='Saha Ekibi',
        verbose_name="Yetki"
    )
    
    # Multi-Tenancy: Her kullanıcı bir tenant'a ait (root admin için null olabilir)
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        verbose_name="Firma",
        null=True,
        blank=True,
        related_name='users'
    )

    def __str__(self):
        return f"{self.user_code} - {self.first_name} {self.last_name}"
    
    class Meta:
        # Tenant bazında unique: Aynı tenant içinde aynı user_code olamaz
        # Farklı tenant'larda aynı user_code olabilir
        # Username otomatik olarak {tenant_slug}_{user_code} formatında oluşturulur (global unique)
        constraints = [
            models.UniqueConstraint(
                fields=['user_code', 'tenant'],
                name='unique_user_code_per_tenant',
                condition=models.Q(tenant__isnull=False)  # tenant=None olanlar için çalışmaz
            ),
        ]
        verbose_name = "Kullanıcı"
        verbose_name_plural = "Kullanıcılar"


class AuthorityNode(models.Model):
    """Hiyerarşi ağacı düğümü (tek parent). Aynı yetkiden birden fazla düğüm açılabilir."""
    AUTHORITY_CHOICES = CustomUser.AUTHORITY_CHOICES

    authority = models.CharField(max_length=30, choices=AUTHORITY_CHOICES, verbose_name="Yetki")
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children', verbose_name="Üst Yetki")
    sort_order = models.IntegerField(default=0, verbose_name="Sıra")
    label = models.CharField(max_length=50, blank=True, default='', verbose_name="Etiket (opsiyonel)")
    assigned_user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_hierarchy_node',
        verbose_name="Atanan Kullanıcı"
    )
    
    # Multi-Tenancy: Her hiyerarşi düğümü bir tenant'a ait
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        verbose_name="Firma",
        null=True,
        blank=True,
        related_name='authority_nodes'
    )

    class Meta:
        verbose_name = "Yetki Hiyerarşisi Düğümü"
        verbose_name_plural = "Yetki Hiyerarşisi Düğümleri"
        ordering = ['sort_order', 'id']

    def __str__(self):
        if self.assigned_user_id:
            name = f"{self.assigned_user.first_name} {self.assigned_user.last_name}".strip() or self.assigned_user.user_code
            return f"{name} ({self.authority})"
        if self.label:
            return f"{self.label} ({self.authority})"
        return self.authority


class UserMenuPermission(models.Model):
    """Kullanıcı menü izinleri (görme/düzenleme)"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='menu_permissions',
        verbose_name="Kullanıcı"
    )
    menu_key = models.CharField(max_length=100, verbose_name="Menü Anahtarı")
    menu_label = models.CharField(max_length=200, verbose_name="Menü Etiketi")
    can_view = models.BooleanField(default=False, verbose_name="Görebilir")
    can_edit = models.BooleanField(default=False, verbose_name="Düzenleyebilir")
    
    # Multi-Tenancy: Her menü izni bir tenant'a ait
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        verbose_name="Firma",
        null=True,
        blank=True,
        related_name='menu_permissions'
    )
    
    class Meta:
        verbose_name = "Kullanıcı Menü İzni"
        verbose_name_plural = "Kullanıcı Menü İzinleri"
        unique_together = ['user', 'menu_key', 'tenant']
        ordering = ['menu_key']
    
    def __str__(self):
        return f"{self.user.username} - {self.menu_label}"