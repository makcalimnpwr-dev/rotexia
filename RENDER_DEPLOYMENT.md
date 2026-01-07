# Render Deployment - Otomatik Mail Gönderimi

## 🚀 Render'da Otomatik Mail Gönderimi

Windows Task Scheduler Render'da çalışmaz. Bunun yerine **Render Worker** kullanılır.

## ✅ Otomatik Kurulum (ÖNERİLEN)

**`render.yaml` dosyası zaten worker'ı içeriyor!**

Projenizi Render'a deploy ettiğinizde, `render.yaml` dosyasındaki worker otomatik olarak oluşturulacak.

### 1. Render Dashboard'a Gidin
- https://dashboard.render.com
- Projenizi açın veya yeni bir Blueprint (render.yaml) service oluşturun

### 2. Blueprint Deploy
- Render Dashboard → New → Blueprint
- GitHub repo'nuzu seçin
- Render otomatik olarak `render.yaml` dosyasını okuyup hem web hem worker'ı oluşturacak

### 3. Environment Variables
Worker'ın aynı environment variables'lara ihtiyacı var (database, SMTP settings, vb.)
- Render Dashboard → Your Worker → Environment
- Web service'teki tüm environment variables'ları worker'a da ekleyin

## 📋 Manuel Kurulum (Alternatif)

Eğer `render.yaml` kullanmıyorsanız:

### 1. Render Dashboard'a Gidin
- https://dashboard.render.com
- Projenizi açın

### 2. Yeni Worker Oluşturun

**Settings:**
- **Type:** Worker (Background Worker)
- **Name:** `fieldops-automated-emails`
- **Environment:** Python 3
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python manage.py send_automated_emails --loop`

### 3. Environment Variables
Aynı environment variables'ları worker'a da ekleyin (database, SMTP settings, vb.)

### 4. Deploy
Worker'ı deploy edin. Artık sürekli çalışacak ve her 5 dakikada bir mail kontrol edecek.

## 📋 Alternatif: Cron Job (Daha Az Kaynak Kullanır)

Eğer worker sürekli çalışmasın istiyorsanız, `render.yaml` dosyasında cron job tanımlayabilirsiniz:

```yaml
services:
  - type: web
    name: fieldops-web
    # ... web ayarları ...
  
  - type: worker
    name: fieldops-automated-emails
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python manage.py send_automated_emails --loop
```

VEYA Render Cron Job kullanın (Render Pro planında mevcut):
- Render Dashboard → Cron Jobs
- Schedule: `*/5 * * * *` (her 5 dakikada bir)
- Command: `python manage.py send_automated_emails`

## 🔍 Test Etme

Render worker loglarına bakarak test edin:
1. Render Dashboard → Your Worker → Logs
2. Her 5 dakikada bir log çıktısı görmelisiniz

## ⚙️ Notlar

- **Worker modu:** Sürekli çalışır, daha fazla kaynak kullanır ama garantili
- **Cron job:** Sadece zamanında çalışır, daha az kaynak kullanır (Render Pro gerekir)

Her iki yöntem de çalışır. Worker modunu öneriyoruz çünkü daha güvenilir.


