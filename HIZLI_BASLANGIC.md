# Subdomain Kurulumu - Hızlı Başlangıç

## ✅ Kod Hazır!

Subdomain multi-tenancy sistemi kuruldu ve çalışır durumda.

## 🚀 Hemen Test Etmek İçin (Development)

### Windows Kullanıcıları:

1. **Hosts dosyasını düzenle:**
   - `Win + R` tuşlarına basın
   - `notepad C:\Windows\System32\drivers\etc\hosts` yazın
   - Enter'a basın
   - UAC (Kullanıcı Hesabı Denetimi) penceresi açılırsa "Evet" deyin
   - Dosyanın en altına şu satırları ekleyin:

```
127.0.0.1    admin.localhost
127.0.0.1    deneme.localhost
127.0.0.1    pastel.localhost
```

   - Dosyayı kaydedin (Ctrl+S)

2. **Django sunucusunu başlatın:**
   ```bash
   python manage.py runserver
   ```

3. **Tarayıcıda test edin:**
   ```
   http://admin.localhost:8000 → Admin paneli
   http://deneme.localhost:8000 → Deneme firması
   http://pastel.localhost:8000 → Pastel firması
   ```

## 📝 Production'a Geçiş

1. **DNS kayıtlarını ekleyin:**
   ```
   *.fieldops.com → A kaydı → [SUNUCU_IP]
   ```

2. **Environment variable ekleyin:**
   ```bash
   SUBDOMAIN_DOMAIN=fieldops.com
   ```

3. **Test edin:**
   ```
   https://admin.fieldops.com
   https://deneme.fieldops.com
   https://pastel.fieldops.com
   ```

## 🎯 Önemli Noktalar

- ✅ Kod **TEK** kalır - güncelleme **TEK SEFERDE** yapılır
- ✅ Her firma kendi subdomain'inde tamamen izole
- ✅ Session'lar karışmaz (her subdomain kendi session'ını kullanır)
- ✅ Mevcut sistemle uyumlu (localhost:8000 hala çalışır)

Detaylı bilgi için: `SUBDOMAIN_KURULUM.md` dosyasına bakın.
