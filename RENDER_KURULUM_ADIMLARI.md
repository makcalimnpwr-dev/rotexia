# 🚀 Render Deployment - Adım Adım Kurulum

## ✅ Render'a Dosyaları Yükledikten Sonra Yapılacaklar

### 1. Web Service (Ana Uygulama)
Zaten mevcut, sadece environment variables'ları kontrol edin:
- `DJANGO_SETTINGS_MODULE=config.settings`
- `DATABASE_URL` (PostgreSQL bağlantısı)
- `SECRET_KEY`
- SMTP ayarları (email host, port, user, password)

### 2. YENİ: Background Worker Oluşturun (Otomatik Mail İçin)

#### Adım 1: Render Dashboard'a Gidin
- https://dashboard.render.com
- Projenizi seçin

#### Adım 2: Yeni Worker Oluşturun
1. **"New +"** butonuna tıklayın
2. **"Background Worker"** seçin

#### Adım 3: Worker Ayarları

**General:**
- **Name:** `fieldops-automated-emails`
- **Environment:** `Python 3`
- **Region:** İstediğiniz bölge (en yakın olanı seçin)
- **Branch:** `main` (veya hangi branch'i kullanıyorsanız)

**Build & Deploy:**
- **Build Command:** `pip install -r requirements.txt && python manage.py migrate`
- **Start Command:** `python manage.py send_automated_emails --loop`

**Environment Variables:**
Web service ile **AYNI** environment variables'ları ekleyin:
- `DJANGO_SETTINGS_MODULE=config.settings`
- `DATABASE_URL` (PostgreSQL - Web service ile AYNI)
- `SECRET_KEY` (Web service ile AYNI)
- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_USE_TLS=True`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `DEFAULT_FROM_EMAIL`
- Diğer tüm environment variables

**Plan:**
- **Free Plan:** Ücretsiz (yeterli olur)
- **Starter Plan:** Daha güvenilir (ücretli)

#### Adım 4: Create Worker
**"Create Background Worker"** butonuna tıklayın

### 3. Kontrol ve Test

#### Worker Loglarına Bakın:
1. Worker'ı seçin
2. **"Logs"** sekmesine gidin
3. Şu mesajı görmelisiniz:
   ```
   [LOOP MODE] Starting continuous email check loop (every 5 minutes)...
   [2026-01-07 ...] Checking automated emails...
   ```

#### Worker'ın Çalıştığını Doğrulayın:
- Loglar sürekli güncelleniyor mu?
- Her 5 dakikada bir log çıktısı var mı?
- Hata mesajı var mı?

### 4. Otomatik Mail Ayarlarını Yapın

Web uygulamanızda:
1. Otomatik Mail sayfasına gidin
2. Mail oluşturun veya düzenleyin
3. **"Aktif"** kutusunu işaretleyin ✅
4. Gönderim saatini ayarlayın (örn: 16:53)
5. Kaydedin

### 5. Test Edin

Mail'in gönderildiğini test etmek için:
1. Gönderim saatini şu anki saatten 1-2 dakika sonrasına ayarlayın
2. Worker loglarını izleyin
3. 5 dakika içinde mail gönderilmeli

## 📋 Önemli Notlar

### Worker Her Zaman Çalışmalı
- Worker durursa otomatik mail gönderilmez
- Render'da worker'ı durdurmak için manuel olarak durdurmanız gerekir
- Worker'ı silmeyin, sadece pause edebilirsiniz

### Free Plan Limitleri
- Free plan'da worker'lar 15 dakika inaktiflikten sonra durur
- Bu yüzden **Starter Plan** önerilir (ücretli ama daha güvenilir)
- VEYA her 10 dakikada bir ping yapan bir health check ekleyebilirsiniz

### Database Connection
- Worker'ın da PostgreSQL database'e erişmesi gerekiyor
- `DATABASE_URL` environment variable'ını eklediğinizden emin olun

### SMTP Ayarları
- Worker'ın SMTP ayarlarına da erişmesi gerekiyor
- Environment variables'ları worker'a da ekleyin

## 🔍 Sorun Giderme

### Worker başlamıyor
- Build Command doğru mu? (`pip install -r requirements.txt`)
- Start Command doğru mu? (`python manage.py send_automated_emails --loop`)
- Environment variables eksik mi?

### Mail gönderilmiyor
- Worker çalışıyor mu? (Logları kontrol edin)
- Mail aktif mi? (Web uygulamasında kontrol edin)
- SMTP ayarları doğru mu? (Environment variables kontrol edin)
- Gönderim saati geçti mi?

### Worker sürekli restart oluyor
- Database bağlantısı başarısız olabilir
- Environment variables eksik olabilir
- Kod hatası olabilir (logları kontrol edin)

## ✅ Kontrol Listesi

- [ ] Web service deploy edildi
- [ ] PostgreSQL database oluşturuldu
- [ ] Background Worker oluşturuldu
- [ ] Worker'a environment variables eklendi
- [ ] Worker çalışıyor (logları kontrol edildi)
- [ ] Otomatik mail oluşturuldu ve aktif
- [ ] Test gönderimi yapıldı

## 💡 Alternatif: Cron Job (Render Pro Plan)

Eğer Render Pro planınız varsa, cron job kullanabilirsiniz:
1. Render Dashboard → **Cron Jobs**
2. **New Cron Job**
3. Schedule: `*/5 * * * *` (her 5 dakikada bir)
4. Command: `python manage.py send_automated_emails`
5. Environment: Python 3

Bu daha az kaynak kullanır ama Pro plan gerekir.




