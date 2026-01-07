"""
Varsayılan Şirket tenant'ını silen management command
"""
import sys
from django.core.management.base import BaseCommand
from apps.core.models import Tenant

class Command(BaseCommand):
    help = "Varsayılan Şirket tenant'ını siler"

    def handle(self, *args, **options):
        sys.stdout.reconfigure(encoding='utf-8')
        
        try:
            default_tenant = Tenant.objects.filter(slug='default').first()
            if default_tenant:
                name = default_tenant.name
                default_tenant.delete()
                self.stdout.write(self.style.SUCCESS(f'✅ "{name}" tenant\'ı başarıyla silindi.'))
            else:
                self.stdout.write(self.style.WARNING('⚠️  Varsayılan şirket bulunamadı.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Hata: {str(e)}'))











