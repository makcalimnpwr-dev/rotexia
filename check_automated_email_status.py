"""
Automated email durumunu kontrol eden script
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.core.models import AutomatedEmail, Tenant
from django.utils import timezone
from datetime import datetime, date

print("=" * 60)
print("OTOMATIK MAIL DURUM KONTROLÜ")
print("=" * 60)

# Tüm otomatik mailleri kontrol et
automated_emails = AutomatedEmail.objects.all()

if not automated_emails.exists():
    print("\n[UYARI] Hiç otomatik mail ayarı bulunamadı!")
    exit()

print(f"\nToplam {automated_emails.count()} otomatik mail ayarı bulundu.\n")

now = timezone.now()
today = now.date()
current_time = now.time()

for email in automated_emails:
    print("-" * 60)
    print(f"ID: {email.id}")
    print(f"Firma: {email.tenant.name}")
    print(f"Konu: {email.subject}")
    print(f"Kime: {email.to_email}")
    print(f"Periyot: {email.get_period_display()}")
    print(f"Hangi Gün: {email.get_day_option_display()}")
    print(f"Gönderim Saati: {email.send_time.strftime('%H:%M') if email.send_time else 'Belirtilmemiş'}")
    print(f"Başlangıç Tarihi: {email.send_start_date}")
    print(f"Bitiş Tarihi: {email.send_end_date if email.send_end_date else 'Sınırsız'}")
    print(f"Son Gönderim: {email.last_sent_at if email.last_sent_at else 'Henüz gönderilmedi'}")
    print(f"Aktif mi? {email.is_active}")
    
    # Durum kontrolü
    issues = []
    
    if not email.is_active:
        issues.append("[HATA] AKTIF DEGIL - 'Aktif mi?' secenegini acmaniz gerekiyor!")
    
    if email.send_start_date > today:
        issues.append(f"[BEKLE] Baslangic tarihi henuz gelmedi ({email.send_start_date})")
    
    if email.send_end_date and email.send_end_date < today:
        issues.append(f"[DURDU] Bitis tarihi gecti ({email.send_end_date})")
    
    if email.send_time:
        send_datetime = datetime.combine(today, email.send_time)
        now_datetime = datetime.combine(today, current_time)
        
        if now_datetime < send_datetime:
            diff_minutes = int((send_datetime - now_datetime).total_seconds() / 60)
            issues.append(f"[BEKLE] Gonderim saati henuz gelmedi ({diff_minutes} dakika sonra)")
        else:
            diff_minutes = int((now_datetime - send_datetime).total_seconds() / 60)
            if email.period == 'daily':
                if email.last_sent_at:
                    last_sent_date = email.last_sent_at.date()
                    if last_sent_date == today:
                        issues.append(f"[GONDERILDI] Bugun zaten gonderildi ({email.last_sent_at.strftime('%H:%M')})")
                    else:
                        issues.append(f"[HAZIR] Gonderim zamani gecti ({diff_minutes} dakika once) - Gonderebilir!")
                else:
                    issues.append(f"[HAZIR] Gonderim zamani gecti ({diff_minutes} dakika once) - Gonderebilir!")
    
    if not email.selected_reports:
        issues.append("[HATA] Hic rapor secilmemis!")
    
    if issues:
        print("\nDurum:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("\n[OK] Tum kontroller gecti - Mail gondermeye hazir!")
    
    print()

print("=" * 60)
print("ÖNERİLER:")
print("=" * 60)
print("1. Eğer mail 'Aktif değil' ise, ayarlardan 'Aktif mi?' seçeneğini açın")
print("2. Windows Task Scheduler'ın çalıştığından emin olun")
print("   - 'schtasks /query /tn FieldOpsAutomatedEmail' komutuyla kontrol edin")
print("3. Task Scheduler her 5 dakikada bir çalışmalı")
print("   - Komut: python manage.py send_automated_emails")
print("4. Manuel test için: python manage.py send_automated_emails")
print("=" * 60)

