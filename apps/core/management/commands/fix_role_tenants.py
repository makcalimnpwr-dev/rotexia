"""
Eski rolleri (tenant=None olanları) doğru tenant'a atayan veya silen command
"""
from django.core.management.base import BaseCommand
from apps.users.models import UserRole
from apps.core.models import Tenant


class Command(BaseCommand):
    help = 'Tenant=None olan rolleri düzeltir'

    def add_arguments(self, parser):
        parser.add_argument(
            '--assign-to-tenant',
            type=int,
            help='Tenant ID - Bu tenant\'a atanacak tenant=None olan roller',
        )
        parser.add_argument(
            '--delete-no-tenant',
            action='store_true',
            help='Tenant=None olan rolleri sil',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Sadece göster, değiştirme yapma',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        assign_to_tenant_id = options.get('assign_to_tenant')
        delete_no_tenant = options.get('delete_no_tenant', False)

        # Tenant=None olan rolleri bul
        roles_without_tenant = UserRole.objects.filter(tenant__isnull=True)
        count = roles_without_tenant.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('Tüm rollerin tenant bilgisi var.'))
            return

        self.stdout.write(self.style.WARNING(f'{count} rolün tenant bilgisi yok (Global):'))

        # Rolleri listele
        for role in roles_without_tenant:
            self.stdout.write(f'  - {role.name} (ID: {role.id})')

        if dry_run:
            self.stdout.write(self.style.WARNING('\n[DRY-RUN] Değişiklik yapılmadı.'))
            return

        # Silme işlemi
        if delete_no_tenant:
            if input(f'\n{count} rol silinecek. Emin misiniz? (evet/hayır): ').lower() == 'evet':
                deleted = roles_without_tenant.delete()
                self.stdout.write(self.style.SUCCESS(f'{deleted[0]} rol silindi.'))
            else:
                self.stdout.write(self.style.WARNING('İşlem iptal edildi.'))
            return

        # Tenant atama işlemi
        if assign_to_tenant_id:
            try:
                tenant = Tenant.objects.get(id=assign_to_tenant_id)
                updated = roles_without_tenant.update(tenant=tenant)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'{updated} rol "{tenant.name}" firmasına atandı.'
                    )
                )
            except Tenant.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Tenant ID {assign_to_tenant_id} bulunamadı.'))
        else:
            self.stdout.write(
                self.style.WARNING(
                    '\nRolleri bir tenant\'a atamak için --assign-to-tenant=<ID> kullanın.\n'
                    'Veya silmek için --delete-no-tenant kullanın.\n'
                    'Mevcut tenant\'lar:'
                )
            )
            tenants = Tenant.objects.filter(is_active=True)
            for t in tenants:
                self.stdout.write(f'  - ID: {t.id}, İsim: {t.name}')





