# 🚀 Deployment Rehberi - Otomatik Mail Gönderimi

## 📋 Özet

Otomatik mail gönderimi için **2 farklı yöntem** var:

1. **Yerel/Windows Server:** Windows Task Scheduler
2. **Cloud (Render/Heroku/vb.):** Background Worker

---

## 🪟 Windows / Yerel Sunucu

### Kurulum

1. `setup_automated_email_scheduler.bat` dosyasına **SAĞ TIKLAYIN**
2. **"Run as administrator"** seçin
3. Kurulum tamamlandı!

### Nasıl Çalışır?

- Windows Task Scheduler **her 5 dakikada bir** `python manage.py send_automated_emails` komutunu çalıştırır
- Komut aktif mailleri kontrol eder ve gönderim saatinden sonra ise gönderir

### Kontrol

```cmd
# Task Scheduler görevini kontrol et
schtasks /query /tn "FieldOps_AutomatedEmails"

# Manuel çalıştır
schtasks /Run /TN "FieldOps_AutomatedEmails"
```

**Daha fazla bilgi:** `OTOMATIK_MAIL_KURULUM.md`

---

## ☁️ Render / Cloud Sunucu

### Otomatik Kurulum (ÖNERİLEN)

**`render.yaml` dosyası zaten worker'ı içeriyor!**

Projenizi Render'a deploy ettiğinizde:
1. Render Dashboard → New → Blueprint
2. GitHub repo'nuzu seçin
3. Render otomatik olarak `render.yaml` dosyasını okuyup hem web hem worker'ı oluşturacak

### Worker Nedir?

Worker, web service'ten bağımsız çalışan arka plan servisidir. Sürekli çalışır ve her 5 dakikada bir mail kontrol eder.

### Önemli Notlar

1. **Environment Variables:** Worker'ın aynı environment variables'lara ihtiyacı var
   - Render Dashboard → Your Worker → Environment
   - Web service'teki tüm environment variables'ları worker'a da ekleyin:
     - `DJANGO_SETTINGS_MODULE`
     - Database connection strings
     - SMTP settings
     - vb.

2. **Start Command:** `python manage.py send_automated_emails --loop`
   - `--loop` parametresi worker'ın sürekli çalışıp her 5 dakikada bir kontrol etmesini sağlar

3. **Logs:** Render Dashboard → Your Worker → Logs
   - Her 5 dakikada bir log çıktısı görmelisiniz
   - Mail gönderildiğinde başarı mesajı görünür

### Manuel Kurulum (Alternatif)

Eğer `render.yaml` kullanmıyorsanız:
- Render Dashboard → New → Worker
- Settings'i yukarıdaki gibi yapılandırın

**Daha fazla bilgi:** `RENDER_DEPLOYMENT.md`

---

## 🔍 Test Etme

### Yerel Test

```cmd
python manage.py send_automated_emails
```

VEYA zorla gönderim:

```cmd
python test_send_email_now.py
```

### Render Test

1. Render Dashboard → Your Worker → Logs
2. Her 5 dakikada bir log çıktısı görmelisiniz:
   ```
   [2026-01-07 17:35:00] Checking automated emails...
   Found 1 active automated email(s)
   [OK] Sent: ...
   ```

---

## ⚠️ Sorun Giderme

### Mail gelmiyor

1. **Aktif mi?** Otomatik mail ayarlarından "Aktif mi?" seçeneğinin açık olduğundan emin olun
2. **Task Scheduler / Worker çalışıyor mu?**
   - Windows: `schtasks /query /tn "FieldOps_AutomatedEmails"`
   - Render: Dashboard → Worker → Logs kontrol edin
3. **Gönderim saati geçti mi?** Gönderim saatinden sonra kontrol edilmesi gerekir
4. **SMTP ayarları doğru mu?** Email ayarlarını kontrol edin

### Worker çalışmıyor (Render)

1. Environment variables eksik olabilir
2. Logs'ta hata mesajı var mı kontrol edin
3. Worker'ın "Running" durumunda olduğundan emin olun

---

## 📝 Özet

| Platform | Yöntem | Dosya |
|----------|--------|-------|
| Windows | Task Scheduler | `setup_automated_email_scheduler.bat` |
| Render | Background Worker | `render.yaml` |
| Heroku | Heroku Scheduler | `Procfile` + Heroku addon |

Her platform için detaylı bilgi ilgili dosyalarda mevcuttur.

