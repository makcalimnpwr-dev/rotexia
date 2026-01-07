"""
Otomatik maili hemen göndermek için test scripti
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.core.models import AutomatedEmail
from apps.core.views import _send_automated_email

print("=" * 60)
print("OTOMATIK MAIL TEST - HEMMEN GONDER")
print("=" * 60)

# Aktif otomatik mailleri al
automated_emails = AutomatedEmail.objects.filter(is_active=True)

if not automated_emails.exists():
    print("\n[UYARI] Aktif otomatik mail bulunamadi!")
    exit()

for email in automated_emails:
    print(f"\nMail ID: {email.id}")
    print(f"Firma: {email.tenant.name}")
    print(f"Konu: {email.subject}")
    print(f"Kime: {email.to_email}")
    print(f"Gonderim Saati: {email.send_time}")
    print("\nGonderiliyor...")
    
    # force=True ile zorla gönder (zamanlama kontrolü yapma)
    success, message = _send_automated_email(email, force=True)
    
    if success:
        print(f"[BASARILI] Mail gonderildi: {message}")
    else:
        print(f"[HATA] Mail gonderilemedi: {message}")

print("\n" + "=" * 60)

