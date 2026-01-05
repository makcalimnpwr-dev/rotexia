"""
Eksik admin kullanıcılarını oluştur
Mevcut firmalar için admin kullanıcısı yoksa oluşturur
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.core.models import Tenant
from apps.users.models import UserRole
from apps.users.utils import get_root_admin_user

User = get_user_model()


class Command(BaseCommand):
    help = 'Eksik admin kullanıcılarını oluştur'

    def handle(self, *args, **options):
        root_admin = get_root_admin_user()
        
        if not root_admin:
            self.stdout.write(self.style.ERROR('Root admin kullanıcısı bulunamadı!'))
            return
        
        admin_password_hash = root_admin.password
        
        tenants = Tenant.objects.all()
        created_count = 0
        existing_count = 0
        
        for tenant in tenants:
            # Bu firma için admin kullanıcısı var mı kontrol et
            admin_user = User.objects.filter(
                tenant=tenant,
                user_code='admin',
                authority='Admin'
            ).first()
            
            if admin_user:
                # Admin kullanıcısı var, şifresini güncelle (root admin ile senkronize)
                if admin_user.password != admin_password_hash:
                    admin_user.password = admin_password_hash
                    admin_user.save(update_fields=['password'])
                    self.stdout.write(self.style.SUCCESS(f'✅ "{tenant.name}" - Admin şifresi güncellendi'))
                else:
                    self.stdout.write(self.style.WARNING(f'⚠️ "{tenant.name}" - Admin kullanıcısı zaten mevcut'))
                existing_count += 1
            else:
                # Admin kullanıcısı yok, oluştur
                admin_username = f"{tenant.slug}_admin"
                
                # Eğer bu username zaten varsa, farklı bir username kullan
                counter = 1
                original_admin_username = admin_username
                while User.objects.filter(username=admin_username).exists():
                    admin_username = f"{original_admin_username}_{counter}"
                    counter += 1
                
                # Admin kullanıcısını oluştur
                admin_user = User.objects.create(
                    username=admin_username,
                    user_code='admin',
                    first_name='Admin',
                    last_name=tenant.name,
                    email=tenant.email or f'admin@{tenant.slug}.fieldops.com',
                    tenant=tenant,
                    authority='Admin',
                    is_staff=True,
                    is_active=True
                )
                
                # Ana admin'in şifre hash'ini direkt atayalım
                admin_user.password = admin_password_hash
                admin_user.save(update_fields=['password'])
                
                # Admin rolü oluştur (eğer yoksa)
                admin_role, _ = UserRole.objects.get_or_create(
                    name='Admin',
                    tenant=tenant,
                    defaults={'description': 'Firma yöneticisi'}
                )
                admin_user.role = admin_role
                admin_user.save(update_fields=['role'])
                
                self.stdout.write(self.style.SUCCESS(f'✅ "{tenant.name}" - Admin kullanıcısı oluşturuldu: {admin_username}'))
                created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'\n📊 Özet: {created_count} yeni admin kullanıcısı oluşturuldu, {existing_count} admin kullanıcısı zaten mevcuttu.'))


