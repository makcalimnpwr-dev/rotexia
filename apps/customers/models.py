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
        verbose_name="Kiracı",
        null=True,  # Geçici olarak null=True (migration için)
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.customer_code} - {self.name}"

    class Meta:
        ordering = ['-created_at']

class CustomerFieldDefinition(models.Model):
    name = models.CharField(max_length=100, verbose_name="Alan Adı") 
    options = models.TextField(blank=True, null=True, verbose_name="Seçenekler (Virgülle ayırın)")
    
    def __str__(self):
        return self.name