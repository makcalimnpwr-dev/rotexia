"""
Django signals for user model
"""
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .utils import get_root_admin_user, is_root_admin

User = get_user_model()


@receiver(pre_save, sender=User)
def sync_admin_passwords_pre_save(sender, instance, **kwargs):
    """
    Root admin şifresi değiştiğinde, tüm firmalardaki admin kullanıcılarının 
    şifresini de güncellemek için pre_save signal'ı.
    
    pre_save'de eski değeri kontrol edip, şifre değişmişse işaretliyoruz.
    """
    # Eğer bu bir yeni kayıt ise (pk yok), işlem yapma
    if not instance.pk:
        return
    
    # Eğer bu kullanıcı root admin değilse, işlem yapma
    root_admin = get_root_admin_user()
    if not root_admin or root_admin.id != instance.id:
        return
    
    # Eski kaydı al
    try:
        old_instance = User.objects.get(pk=instance.pk)
        # Şifre değişmiş mi kontrol et
        if old_instance.password != instance.password:
            # Şifre değişmiş, instance'a işaret koy (post_save'de kullanacağız)
            instance._password_changed = True
            instance._new_password_hash = instance.password
    except User.DoesNotExist:
        # Yeni kayıt, işlem yapma
        pass


@receiver(post_save, sender=User)
def sync_admin_passwords_post_save(sender, instance, created, **kwargs):
    """
    Root admin şifresi değiştiğinde, tüm firmalardaki admin kullanıcılarının 
    şifresini de güncelle.
    """
    # Eğer bu bir yeni kayıt ise ve root admin ise, işlem yapma (henüz firmalar oluşturulmamış olabilir)
    if created:
        return
    
    # Eğer şifre değişmemişse, işlem yapma
    if not hasattr(instance, '_password_changed') or not instance._password_changed:
        return
    
    # Eğer bu kullanıcı root admin değilse, işlem yapma
    root_admin = get_root_admin_user()
    if not root_admin or root_admin.id != instance.id:
        return
    
    # Yeni şifre hash'ini al
    new_password_hash = getattr(instance, '_new_password_hash', instance.password)
    
    # Tüm tenant'lardaki admin kullanıcılarını bul ve şifrelerini güncelle
    # Admin kullanıcıları: user_code='admin' ve authority='Admin' olanlar
    from apps.core.models import Tenant
    from django.db import connection
    
    admin_users = User.objects.filter(
        user_code='admin',
        authority='Admin',
        tenant__isnull=False  # Tenant'a bağlı olanlar (root admin değil)
    )
    
    # Signal döngüsünü önlemek için direkt SQL ile güncelle
    # Veya bulk_update kullan (Django 2.2+)
    updated_count = 0
    for admin_user in admin_users:
        # Signal'ı bypass etmek için direkt DB'ye yaz
        User.objects.filter(id=admin_user.id).update(password=new_password_hash)
        updated_count += 1
    
    # Temizlik: instance'tan işaretleri kaldır
    if hasattr(instance, '_password_changed'):
        delattr(instance, '_password_changed')
    if hasattr(instance, '_new_password_hash'):
        delattr(instance, '_new_password_hash')

