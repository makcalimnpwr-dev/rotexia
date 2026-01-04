"""
Mevcut müşterilere tenant'a göre sys_id atayan command
"""
from django.core.management.base import BaseCommand
from apps.customers.models import Customer
from apps.core.models import Tenant


class Command(BaseCommand):
    help = 'Mevcut müşterilere tenant bazında sys_id atar'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Sadece göster, değiştirme yapma',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Tenant bazında işle
        tenants = Tenant.objects.filter(is_active=True)
        
        for tenant in tenants:
            customers = Customer.objects.filter(tenant=tenant).order_by('id')
            self.stdout.write(f'\n=== {tenant.name} (ID: {tenant.id}) ===')
            
            sys_id_counter = 1
            for customer in customers:
                if customer.sys_id is None or customer.sys_id == 0:
                    if not dry_run:
                        customer.sys_id = sys_id_counter
                        customer.save()
                    self.stdout.write(
                        f'  Customer ID {customer.id}: {customer.name} -> sys_id={sys_id_counter}'
                    )
                    sys_id_counter += 1
                else:
                    self.stdout.write(
                        f'  Customer ID {customer.id}: {customer.name} -> sys_id={customer.sys_id} (zaten var)'
                    )
            
            if customers.count() == 0:
                self.stdout.write(f'  Müşteri yok')
        
        # Tenant=None olan müşteriler
        customers_no_tenant = Customer.objects.filter(tenant__isnull=True)
        if customers_no_tenant.exists():
            self.stdout.write(f'\n=== Tenant=None (Global) - {customers_no_tenant.count()} müşteri ===')
            self.stdout.write(self.style.WARNING(
                'UYARI: Tenant=None olan musteriler var! Bunlara sys_id atanmadi.'
            ))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n[DRY-RUN] Değişiklik yapılmadı.'))

