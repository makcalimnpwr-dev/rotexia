import os
import django

# Django ayarlarını yükle
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

# Tüm kullanıcıları getir
users = User.objects.all()

if not users.exists():
    print("HATA: Veritabanında HİÇ kullanıcı yok!")
    print("ÇÖZÜM: Terminale 'python manage.py createsuperuser' yazıp yeni bir tane oluşturmalısın.")
else:
    print("--- Mevcut Kullanıcılar ---")
    for u in users:
        print(f"- {u.username} (Kod: {getattr(u, 'user_code', 'Yok')})")
    
    # İlk bulduğu kullanıcıyı al
    target_user = users.first()
    
    # Şifreyi güncelle
    YENI_SIFRE = '123'
    target_user.set_password(YENI_SIFRE)
    target_user.save()
    
    print("-" * 30)
    print(f"BAŞARILI! '{target_user.username}' adlı kullanıcının şifresi '{YENI_SIFRE}' yapıldı.")
    print(f"Giriş yapabilirsin -> Kullanıcı Adı: {target_user.username} | Şifre: {YENI_SIFRE}")