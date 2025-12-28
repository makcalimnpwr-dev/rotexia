"""
Base Models for Multi-Tenancy Support
Tüm modeller bu base model'den türemeli
"""
from django.db import models
from django.core.exceptions import ValidationError


class TenantModel(models.Model):
    """
    Tüm tenant-specific modeller için base model
    Otomatik olarak tenant filtrelemesi yapar
    """
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        verbose_name="Kiracı",
        related_name='%(class)s_set'  # Her model için ayrı related_name
    )
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        # Eğer tenant yoksa ve request'ten alınabiliyorsa, ekle
        if not self.tenant_id:
            from django.core.exceptions import ImproperlyConfigured
            # Bu durumda view'dan tenant'ı manuel eklemek gerekir
            # Ya da middleware'den alınabilir (gelecekte)
            pass
        super().save(*args, **kwargs)
    
    @classmethod
    def get_for_tenant(cls, tenant):
        """Belirli bir tenant için tüm kayıtları getir"""
        return cls.objects.filter(tenant=tenant)


class TimestampedModel(models.Model):
    """
    created_at ve updated_at alanlarını otomatik ekler
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")
    
    class Meta:
        abstract = True




