"""
Rolleri ve tenant atamalarını kontrol eden command
"""
from django.core.management.base import BaseCommand
from apps.users.models import UserRole
from apps.core.models import Tenant


class Command(BaseCommand):
    help = 'Rolleri ve tenant atamalarını listeler'

    def handle(self, *args, **options):
        self.stdout.write('\n=== TÜM ROLLER ===\n')
        for role in UserRole.objects.all().select_related('tenant'):
            tenant_name = role.tenant.name if role.tenant else "None (Global)"
            self.stdout.write(f'  - {role.name} (ID: {role.id}, Tenant: {tenant_name})')
        
        self.stdout.write('\n=== TÜM TENANT\'LAR ===\n')
        for tenant in Tenant.objects.filter(is_active=True):
            roles_count = UserRole.objects.filter(tenant=tenant).count()
            self.stdout.write(f'  - {tenant.name} (ID: {tenant.id}) - {roles_count} rol')
            roles = UserRole.objects.filter(tenant=tenant)
            for role in roles:
                self.stdout.write(f'      - {role.name}')


