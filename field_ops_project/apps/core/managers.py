"""
Custom Managers for Multi-Tenancy
Otomatik tenant filtrelemesi yapar
"""
from django.db import models


class TenantManager(models.Manager):
    """
    Tenant'a göre otomatik filtreleme yapan manager
    """
    def get_queryset(self):
        """
        Bu manager kullanıldığında otomatik olarak tenant filtresi uygulanır
        Ancak şimdilik tüm kayıtları döndürüyoruz (request.tenant yoksa)
        """
        return super().get_queryset()
    
    def for_tenant(self, tenant):
        """Belirli bir tenant için filtrele"""
        return self.get_queryset().filter(tenant=tenant)
    
    def current(self, request):
        """Request'ten tenant'ı al ve filtrele"""
        tenant = getattr(request, 'tenant', None)
        if tenant:
            return self.for_tenant(tenant)
        return self.get_queryset()




