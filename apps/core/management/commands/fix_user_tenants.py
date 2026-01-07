"""
Eski kullanıcıların tenant bilgilerini düzelten management command

Kullanım:
    python manage.py fix_user_tenants
    python manage.py fix_user_tenants --assign-to-tenant=1  # Belirli bir tenant'a ata
    python manage.py fix_user_tenants --dry-run  # Sadece göster, değiştirme
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.core.models import Tenant

User = get_user_model()


class Command(BaseCommand):
    help = 'Tenant bilgisi olmayan kullanıcıları düzeltir'

    def add_arguments(self, parser):
        parser.add_argument(
            '--assign-to-tenant',
            type=int,
            help='Tenant ID - Bu tenant\'a atanacak tenant\'sız kullanıcılar',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Sadece göster, değiştirme yapma',
        )
        parser.add_argument(
            '--delete-no-tenant',
            action='store_true',
            help='Tenant\'ı olmayan kullanıcıları sil (DİKKAT: Tehlikeli!)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        assign_to_tenant_id = options.get('assign_to_tenant')
        delete_no_tenant = options.get('delete_no_tenant', False)

        # Tenant'sız kullanıcıları bul
        users_without_tenant = User.objects.filter(tenant__isnull=True)
        count = users_without_tenant.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('Tüm kullanıcıların tenant bilgisi var.'))
            return

        self.stdout.write(self.style.WARNING(f'{count} kullanıcının tenant bilgisi yok:'))

        # Kullanıcıları listele
        for user in users_without_tenant:
            self.stdout.write(f'  - {user.username} ({user.user_code}) - {user.first_name} {user.last_name}')

        if dry_run:
            self.stdout.write(self.style.WARNING('\n[DRY-RUN] Değişiklik yapılmadı.'))
            return

        # Silme işlemi
        if delete_no_tenant:
            if input(f'\n{count} kullanıcı silinecek. Emin misiniz? (evet/hayır): ').lower() == 'evet':
                deleted = users_without_tenant.delete()
                self.stdout.write(self.style.SUCCESS(f'{deleted[0]} kullanıcı silindi.'))
            else:
                self.stdout.write(self.style.WARNING('İşlem iptal edildi.'))
            return

        # Tenant atama işlemi
        if assign_to_tenant_id:
            try:
                tenant = Tenant.objects.get(id=assign_to_tenant_id)
                updated = users_without_tenant.update(tenant=tenant)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'{updated} kullanıcı "{tenant.name}" firmasına atandı.'
                    )
                )
            except Tenant.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Tenant ID {assign_to_tenant_id} bulunamadı.'))
                # Mevcut tenant'ları listele
                tenants = Tenant.objects.filter(is_active=True)
                self.stdout.write('\nMevcut tenant\'lar:')
                for t in tenants:
                    self.stdout.write(f'  - ID: {t.id}, İsim: {t.name}')
        else:
            self.stdout.write(
                self.style.WARNING(
                    '\nKullanıcıları bir tenant\'a atamak için --assign-to-tenant=<ID> kullanın.\n'
                    'Veya silmek için --delete-no-tenant kullanın (DİKKAT: Tehlikeli!).\n'
                    'Mevcut tenant\'lar:'
                )
            )
            tenants = Tenant.objects.filter(is_active=True)
            for t in tenants:
                self.stdout.write(f'  - ID: {t.id}, İsim: {t.name}')











