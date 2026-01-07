# ✅ Render Deployment Checklist - Otomatik Mail Gönderimi

## 🎉 EVET, RENDER'DA ÇALIŞACAK!

Yerel CMD'de çalışıyorsa, Render'da da **kesinlikle çalışacak**. Tek fark:
- **Yerel:** Windows Task Scheduler kullanır
- **Render:** Background Worker kullanır

## ✅ HAZIRLIK KONTROLÜ

### 1. `render.yaml` Dosyası ✅
- Worker tanımlı: `fieldops-automated-emails`
- Start Command: `python manage.py send_automated_emails --loop`
- Environment variables ayarlanabilir

### 2. `requirements.txt` ✅
- `pytz` eklendi (Türkiye saati için gerekli)

### 3. Kod Düzeltmeleri ✅
- Türkiye saatine göre kontrol ediyor (UTC+3)
- `--loop` parametresi ile sürekli çalışır

## 🚀 RENDER'A DEPLOY ADIMLARI

### ADIM 1: GitHub'a Push
```bash
git add .
git commit -m "Add automated email worker for Render"
git push
```

### ADIM 2: Render Dashboard'a Git
- https://dashboard.render.com
- Projenizi açın veya yeni Blueprint oluşturun

### ADIM 3: Blueprint Deploy (ÖNERİLEN)
1. Render Dashboard → **New → Blueprint**
2. GitHub repo'nuzu seçin
3. Render **otomatik olarak** `render.yaml` dosyasını okuyacak
4. Hem **Web** hem **Worker** otomatik oluşturulacak

### ADIM 4: Environment Variables Ekle

**Worker'ın aynı environment variables'lara ihtiyacı var:**

1. Render Dashboard → **Your Worker** → **Environment**
2. Web service'teki **TÜM** environment variables'ları worker'a da ekleyin:
   - Database connection string
   - Django SECRET_KEY
   - SMTP settings (EMAIL_HOST, EMAIL_PORT, vb.)
   - Diğer gerekli ayarlar

**ÖNEMLİ:** Web service ile worker'ın aynı database'i kullanması gerekiyor!

### ADIM 5: Deploy

Render otomatik olarak deploy edecek. Worker başladığında:
- Sürekli çalışır
- Her 5 dakikada bir mail kontrol eder
- Türkiye saatine göre gönderir

## 🔍 TEST ETME

### 1. Worker Loglarını Kontrol Et

Render Dashboard → **Your Worker** → **Logs**

Her 5 dakikada bir şu log'u görmelisiniz:
```
[LOOP MODE] Starting continuous email check loop (every 5 minutes)...
[2026-01-07 ...] Checking automated emails...
Found 1 active automated email(s)
...
```

### 2. Mail Gönderimini Test Et

1. Otomatik mail ayarlarından gönderim saatini **şu anki saatten 2-3 dakika sonrasına** ayarlayın
2. Worker loglarını izleyin
3. Belirlenen saatte mail gönderildiğini görmelisiniz:
   ```
   [OK] Sent: ... to ...
   ```

## ⚙️ NASIL ÇALIŞIR?

### Yerel (Windows):
- Task Scheduler her 5 dakikada bir `send_automated_emails` komutunu çalıştırır
- Tek seferlik çalışır, biter

### Render (Worker):
- Worker **sürekli çalışır**
- `--loop` parametresi ile **her 5 dakikada bir** otomatik kontrol eder
- Daha güvenilir (kesintisiz çalışır)

## 📋 ÖNEMLİ NOTLAR

1. **Türkiye Saati:** Sistem artık Türkiye saatine (TSİ) göre çalışıyor
   - Gönderim saatini TSİ olarak yazın (örn: 21:50)
   - Sistem otomatik olarak kontrol eder

2. **Environment Variables:** Worker'a **mutlaka** environment variables ekleyin
   - Özellikle database ve SMTP ayarları!

3. **Worker Sürekli Çalışır:** Worker çalışırken kaynak kullanır
   - Render'da ücretsiz plan sınırlarına dikkat edin
   - Worker'ı durdurmak isterseniz: Render Dashboard → Worker → Manual Suspend

4. **Log Kontrolü:** Sorun olursa loglara bakın
   - Render Dashboard → Worker → Logs

## ✅ ÖZET

- ✅ `render.yaml` hazır
- ✅ `requirements.txt` güncel (pytz eklendi)
- ✅ Kod Türkiye saatine göre çalışıyor
- ✅ Worker `--loop` ile sürekli çalışacak
- ✅ Her 5 dakikada bir kontrol edip mail gönderecek

**Yerel CMD'de çalışıyorsa, Render'da da kesinlikle çalışacak!** 🎉



