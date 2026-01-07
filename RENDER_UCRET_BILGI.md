# 💰 Render ve GitHub Ücret Bilgisi

## 🆓 GitHub - ÜCRETSİZ!

GitHub **tamamen ücretsiz**:
- ✅ Public repo'lar: Sınırsız ücretsiz
- ✅ Private repo'lar: Ücretsiz plan mevcut (sınırsız)
- ✅ Kolaborasyon: Ücretsiz
- ✅ Issue tracking: Ücretsiz

**GitHub'a kayıt olmak ve repo oluşturmak tamamen ücretsizdir!**

---

## 💰 Render - Worker İçin Ücret Gerekebilir

### ⚠️ ÖNEMLİ BİLGİ

Render'da **Background Worker** genellikle **ücretli plan** gerektirir:

| Plan | Worker Desteği |
|------|----------------|
| **Free Plan** | ❌ Worker yok (sadece Web service) |
| **Starter Plan** ($7/ay) | ✅ Worker var (512 MB RAM) |
| **Standard Plan** ($25/ay) | ✅ Worker var (1 GB RAM) |

### 🆓 ÜCRETSİZ ALTERNATİFLER

Eğer ücretsiz bir çözüm istiyorsanız:

#### 1. **Render Cron Job (Free Plan'da Mevcut)**
- Render Free planında **Cron Job** özelliği var
- Ancak **Render Pro** gerektirebilir (kontrol edin)

#### 2. **Alternatif Ücretsiz Servisler:**
- **Heroku Scheduler** (Ücretsiz tier kaldırıldı, ama alternatifler var)
- **Cron-job.org** (Ücretsiz web cron service)
- **EasyCron** (Ücretsiz plan)
- **GitHub Actions** (Ücretsiz, otomatik çalıştırma)

---

## 🎯 ÖNERİLER

### Seçenek 1: Render Starter Plan ($7/ay) - ÖNERİLEN
- ✅ Background Worker destekler
- ✅ Sürekli çalışır
- ✅ Güvenilir
- ✅ 512 MB RAM yeterli (otomatik mail için)

### Seçenek 2: Ücretsiz Alternatif - GitHub Actions
GitHub Actions ile ücretsiz otomatik mail gönderme:

1. GitHub repo'nuzda `.github/workflows/automated-email.yml` dosyası oluşturun
2. Her 5 dakikada bir GitHub Actions çalıştırır
3. Render worker'a gerek kalmaz

**GitHub Actions workflow örneği:**
```yaml
name: Send Automated Emails

on:
  schedule:
    - cron: '*/5 * * * *'  # Her 5 dakikada bir
  workflow_dispatch:  # Manuel çalıştırma

jobs:
  send-emails:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Send emails
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          SECRET_KEY: ${{ secrets.SECRET_KEY }}
          # Diğer environment variables...
        run: python manage.py send_automated_emails
```

### Seçenek 3: Yerel Windows Server
- ✅ Tamamen ücretsiz
- ✅ Task Scheduler kullanır
- ❌ Bilgisayar sürekli açık olmalı
- ❌ İnternet bağlantısı gerekli

---

## 📊 KARŞILAŞTIRMA

| Özellik | Render Worker | GitHub Actions | Yerel Windows |
|---------|---------------|----------------|---------------|
| **Ücret** | $7/ay (Starter) | Ücretsiz | Ücretsiz |
| **Süreklilik** | ✅ 7/24 | ✅ 7/24 | ❌ PC açık olmalı |
| **Güvenilirlik** | ✅ Çok iyi | ✅ İyi | ⚠️ Orta |
| **Kurulum** | Kolay | Orta | Kolay |
| **RAM** | 512 MB | Sınırlı | Sınırsız |

---

## ✅ SONUÇ

1. **GitHub:** Tamamen ücretsiz ✅
2. **Render Worker:** Ücretli plan gerekiyor ($7/ay)
3. **Ücretsiz Alternatif:** GitHub Actions kullanabilirsiniz

### ÖNERİM:
- **Küçük proje:** GitHub Actions (ücretsiz) veya yerel Windows Task Scheduler
- **Profesyonel proje:** Render Starter Plan ($7/ay)

---

## 📝 GitHub Actions Kurulumu İsterseniz

Eğer GitHub Actions ile ücretsiz çözüm isterseniz, size workflow dosyası hazırlayabilirim. Sadece söyleyin!



