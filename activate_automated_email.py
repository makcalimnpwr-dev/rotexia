"""
Otomatik mail'i aktif hale getir
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.core.models import AutomatedEmail

emails = AutomatedEmail.objects.all()
print(f"Toplam {emails.count()} otomatik mail bulundu:\n")

for email in emails:
    print(f"Mail ID: {email.id}")
    print(f"  Konu: {email.subject}")
    print(f"  Aktif: {email.is_active}")
    print(f"  Gönderim Saati: {email.send_time}")
    print(f"  Periyot: {email.period}")
    print(f"  Tenant: {email.tenant.name if email.tenant else 'None'}")
    
    if not email.is_active:
        email.is_active = True
        email.save()
        print(f"  [OK] Aktif hale getirildi!")
    else:
        print(f"  [OK] Zaten aktif")
    print()

