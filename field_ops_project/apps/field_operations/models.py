from django.db import models
from django.conf import settings
from apps.customers.models import Customer

# 1. ROTA PLANI (Şablon)
class RoutePlan(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="Müşteri")
    merch_code = models.CharField(max_length=50, verbose_name="Personel Kodu (Merch)")
    visit_duration = models.IntegerField(default=45, verbose_name="Ziyaret Süresi (Dk)")
    
    # Günler (1'den 28'e kadar, JSON olarak tutmak veritabanını şişirmez)
    # Örnek Veri: [1, 8, 15, 22] (Bu günlerde gidilecek)
    active_days = models.JSONField(default=list, verbose_name="Aktif Günler")
    visit_duration = models.IntegerField(default=0, verbose_name="Ziyaret Süresi (Dk)", null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.merch_code} - {self.customer.name}"

    class Meta:
        verbose_name = "Rota Planı"
        verbose_name_plural = "Rota Planları"

# 1. YENİ MODEL: ZİYARET TİPİ (Ayarlardan yönetilecek)
class VisitType(models.Model):
    name = models.CharField(max_length=100, verbose_name="Ziyaret Tipi Adı") # Örn: Sabit Rut, Lansman
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Ziyaret Tipi"
        verbose_name_plural = "Ziyaret Tipleri"

# 2. GÖREVLER (Oluşan İş)
class VisitTask(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Bekliyor'),
        ('completed', 'Tamamlandı'),
        ('missed', 'Ziyaret Edilmedi'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="Müşteri")
    merch_code = models.CharField(max_length=50, verbose_name="Atanan Personel")
    
    planned_date = models.DateField(null=True, blank=True, verbose_name="Planlanan Tarih")
    cycle_day = models.IntegerField(verbose_name="Döngü Günü (1-28)")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    visit_type = models.ForeignKey(VisitType, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Ziyaret Tipi")
    
    # Tamamlanınca dolacak alanlar
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    visit_note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.planned_date} - {self.customer.name}"

    class Meta:
        ordering = ['-planned_date']
        verbose_name = "Ziyaret Görevi"
        verbose_name_plural = "Ziyaret Görevleri"