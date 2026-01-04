from django.db import models

class CustomerCari(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Cari Adı")
    def __str__(self): return self.name
    class Meta: verbose_name = "Cari / Firma"

# YENİ: Hangi özel alanların olduğunu tutan tablo (Örn: "Raf Sayısı", "M2 Büyüklüğü")
class CustomFieldDefinition(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Alan Adı")
    # Slug, veritabanında saklanacak anahtar isimdir (Örn: Raf Sayısı -> raf_sayisi)
    slug = models.SlugField(max_length=50, unique=True)

    def __str__(self): return self.name

class Customer(models.Model):
    # --- Sabit Alanlar ---
    customer_code = models.CharField(max_length=50, unique=True, verbose_name="Müşteri Kodu")
    name = models.CharField(max_length=200, verbose_name="Müşteri Adı")
    cari = models.ForeignKey(CustomerCari, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Cari / Firma")
    
    city = models.CharField(max_length=50, verbose_name="İl")
    district = models.CharField(max_length=50, verbose_name="İlçe")
    address = models.TextField(blank=True, null=True, verbose_name="Açık Adres")
    
    # Koordinatlar (Float olarak tutulacak, daha hassas)
    latitude = models.FloatField(verbose_name="Enlem", blank=True, null=True, help_text="Harita koordinatı (örn: 41.0082)")
    longitude = models.FloatField(verbose_name="Boylam", blank=True, null=True, help_text="Harita koordinatı (örn: 28.9784)")
    
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefon")
    authorized_person = models.CharField(max_length=100, blank=True, null=True, verbose_name="Yetkili Kişi")
    
    # YENİ: Dinamik Veri Çantası (Tüm sonradan eklenen alanlar burada duracak)
    extra_data = models.JSONField(default=dict, blank=True)
    
    # Multi-Tenancy: Her müşteri bir tenant'a ait
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        verbose_name="Firma",
        null=True,  # Geçici olarak null=True (migration için)
        blank=True
    )
    
    # Tenant-specific Sistem ID (Her firma için 1'den başlayan seri)
    sys_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="Sistem ID", help_text="Firma içinde otomatik atanır (1, 2, 3...)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Eğer yeni kayıt ve sys_id yoksa, tenant'a göre sys_id ata
        if not self.pk and not self.sys_id and self.tenant:
            # Bu tenant'ın en yüksek sys_id'sini bul
            max_sys_id = Customer.objects.filter(tenant=self.tenant).aggregate(
                max_id=models.Max('sys_id')
            )['max_id'] or 0
            self.sys_id = max_sys_id + 1
        
        super().save(*args, **kwargs)
    
    def get_sys_id_display(self):
        """Sistem ID'yi M-{sys_id} formatında döndür"""
        if self.sys_id:
            return f"M-{self.sys_id}"
        return f"M-{self.id}"  # Fallback: eski ID kullan

    def __str__(self):
        return f"{self.customer_code} - {self.name}"

    class Meta:
        ordering = ['-created_at']
        # Her tenant için sys_id benzersiz olmalı
        unique_together = [('tenant', 'sys_id')]

class CustomerFieldDefinition(models.Model):
    name = models.CharField(max_length=100, verbose_name="Alan Adı") 
    options = models.TextField(blank=True, null=True, verbose_name="Seçenekler (Virgülle ayırın)")
    
    def __str__(self):
        return self.name