# 🚀 Rotexia - Canlıya Alma Rehberi (Ücretsiz)

Bu rehber, Rotexia projesini ücretsiz hosting platformlarında canlıya almak için hazırlanmıştır.

## 📋 İçindekiler

1. [Hazırlık](#hazırlık)
2. [Render.com ile Deployment](#rendercom-ile-deployment) ⭐ ÖNERİLEN
3. [Railway.app ile Deployment](#railwayapp-ile-deployment)
4. [Güncelleme Süreci](#güncelleme-süreci)
5. [Sorun Giderme](#sorun-giderme)

---

## 🔧 Hazırlık

### 1. Git Repository Hazırlığı

Projenizi GitHub'a yükleyin:

```bash
# Git repository oluştur
git init
git add .
git commit -m "Initial commit - Rotexia deployment ready"
git branch -M main
git remote add origin https://github.com/KULLANICI_ADI/rotexia.git
git push -u origin main
```

### 2. Environment Variables Hazırlığı

Aşağıdaki environment variable'ları hazırlayın (her platformda ekleyeceksiniz):

```
SECRET_KEY=buraya-güvenli-bir-secret-key-yazın
DEBUG=False
ALLOWED_HOSTS=your-app-name.onrender.com,your-app-name.railway.app
DATABASE_URL=postgresql://... (Platform otomatik sağlayacak)
```

**SECRET_KEY oluşturma:**
```python
# Python'da çalıştırın:
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

---

## 🌐 Render.com ile Deployment ⭐ ÖNERİLEN

**Render.com neden öneriliyor:**
- ✅ Ücretsiz PostgreSQL veritabanı
- ✅ Ücretsiz SSL sertifikası
- ✅ Kolay deployment
- ✅ Otomatik güncelleme (GitHub bağlantısı ile)

### Adım 1: Render.com Hesabı Oluştur

1. [Render.com](https://render.com) adresine gidin
2. "Get Started for Free" ile kayıt olun (GitHub ile giriş yapabilirsiniz)

### Adım 2: PostgreSQL Veritabanı Oluştur

1. Dashboard'da "New +" → "PostgreSQL" seçin
2. Aşağıdaki ayarları yapın:
   - **Name:** `rotexia-db`
   - **Database:** `rotexia`
   - **User:** `rotexia_user`
   - **Region:** En yakın bölgeyi seçin (Avrupa önerilir)
   - **Plan:** Free (ücretsiz)
3. "Create Database" tıklayın
4. Veritabanı oluştuktan sonra "Connections" sekmesinden **Internal Database URL**'i kopyalayın

### Adım 3: Web Service Oluştur

1. Dashboard'da "New +" → "Web Service" seçin
2. GitHub repository'nizi bağlayın
3. Aşağıdaki ayarları yapın:

   **Build & Deploy:**
   - **Name:** `rotexia` (veya istediğiniz isim)
   - **Region:** En yakın bölge
   - **Branch:** `main`
   - **Root Directory:** (boş bırakın)
   - **Environment:** `Python 3`
   - **Build Command:** `./build.sh` veya `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - **Start Command:** `gunicorn config.wsgi:application`

   **Environment Variables:**
   ```
   SECRET_KEY=buraya-oluşturduğunuz-secret-key
   DEBUG=False
   ALLOWED_HOSTS=rotexia.onrender.com
   DATABASE_URL=postgresql://... (PostgreSQL'den kopyaladığınız URL)
   PYTHON_VERSION=3.11.9
   ```

4. "Create Web Service" tıklayın

### Adım 4: İlk Migration

Deployment tamamlandıktan sonra:

1. Render Dashboard'da servisinize gidin
2. "Shell" sekmesine tıklayın
3. Aşağıdaki komutları çalıştırın:

```bash
python manage.py migrate
python manage.py createsuperuser
```

### Adım 5: Static Files

Static files otomatik olarak `build.sh` scriptinde toplanıyor. Eğer sorun olursa:

```bash
python manage.py collectstatic --noinput
```

---

## 🚂 Railway.app ile Deployment

### Adım 1: Railway Hesabı Oluştur

1. [Railway.app](https://railway.app) adresine gidin
2. GitHub ile giriş yapın

### Adım 2: Yeni Proje Oluştur

1. "New Project" → "Deploy from GitHub repo" seçin
2. Repository'nizi seçin
3. Railway otomatik olarak Django projesini algılayacak

### Adım 3: PostgreSQL Ekle

1. "New" → "Database" → "Add PostgreSQL" seçin
2. Railway otomatik olarak `DATABASE_URL` environment variable'ını ekleyecek

### Adım 4: Environment Variables

"Variables" sekmesinde şunları ekleyin:

```
SECRET_KEY=buraya-oluşturduğunuz-secret-key
DEBUG=False
ALLOWED_HOSTS=your-app-name.railway.app
```

### Adım 5: Build Ayarları

Railway genellikle otomatik algılar, ama manuel ayar gerekirse:

**Build Command:**
```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput
```

**Start Command:**
```bash
python manage.py migrate && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

---

## 🔄 Güncelleme Süreci

### Yöntem 1: Otomatik Güncelleme (Önerilen) ⭐

**Render.com için:**
1. Kodunuzu değiştirin
2. GitHub'a push edin:
   ```bash
   git add .
   git commit -m "Yeni özellik eklendi"
   git push origin main
   ```
3. Render.com otomatik olarak yeni deployment başlatır
4. Dashboard'da deployment durumunu takip edebilirsiniz

**Railway.app için:**
- Aynı şekilde GitHub'a push ettiğinizde otomatik deploy olur

### Yöntem 2: Manuel Güncelleme

**Render.com:**
1. Dashboard'da servisinize gidin
2. "Manual Deploy" → "Deploy latest commit" tıklayın

**Railway.app:**
1. Dashboard'da "Deployments" sekmesine gidin
2. "Redeploy" butonuna tıklayın

### Yöntem 3: Shell Üzerinden Güncelleme

Eğer migration veya özel komut çalıştırmanız gerekirse:

**Render.com:**
1. Servisinizde "Shell" sekmesine gidin
2. Komutları çalıştırın:
   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```

**Railway.app:**
1. "Deployments" → "View Logs" → "Open Shell" tıklayın
2. Komutları çalıştırın

---

## 🐛 Sorun Giderme

### Static Files Görünmüyor

```bash
# Shell'de çalıştırın:
python manage.py collectstatic --noinput
```

### Database Migration Hatası

```bash
# Shell'de çalıştırın:
python manage.py migrate
```

### 500 Internal Server Error

1. **Logs kontrol edin:**
   - Render: "Logs" sekmesi
   - Railway: "Deployments" → "View Logs"

2. **DEBUG=True yaparak test edin (sadece test için):**
   ```
   DEBUG=True
   ```
   ⚠️ **DİKKAT:** Production'da DEBUG=False olmalı!

3. **Environment variables kontrol edin:**
   - SECRET_KEY doğru mu?
   - DATABASE_URL doğru mu?
   - ALLOWED_HOSTS doğru mu?

### Media Files (Yüklenen Dosyalar) Kayboluyor

**Sorun:** Ücretsiz planlarda media files kalıcı değil.

**Çözümler:**
1. **Cloud Storage kullanın:**
   - AWS S3 (ücretsiz tier var)
   - Cloudinary (ücretsiz tier var)
   - Google Cloud Storage

2. **Render Disk kullanın (sınırlı):**
   - Render'da "Disk" ekleyebilirsiniz ama sınırlı

### Performans Sorunları

1. **Database Index'leri kontrol edin**
2. **Static files CDN kullanın** (Cloudflare ücretsiz)
3. **Caching ekleyin** (Redis - ücretsiz tier var)

---

## 📝 Önemli Notlar

### ⚠️ Güvenlik

1. **SECRET_KEY'i asla GitHub'a yüklemeyin!**
2. **DEBUG=False** production'da mutlaka olmalı
3. **ALLOWED_HOSTS** doğru domain'leri içermeli
4. **.env dosyasını .gitignore'a ekleyin**

### 💰 Ücretsiz Limitler

**Render.com:**
- Web Service: 750 saat/ay (ücretsiz)
- PostgreSQL: 90 gün sonra uyku moduna geçer (uyandırmak için istek gerekir)
- Disk: 512 MB

**Railway.app:**
- $5 ücretsiz kredi/ay
- PostgreSQL: Ücretsiz tier mevcut

### 🔄 Backup

1. **Database backup:**
   ```bash
   # Render Shell'de:
   pg_dump $DATABASE_URL > backup.sql
   ```

2. **Media files backup:**
   - Cloud storage kullanıyorsanız otomatik
   - Yoksa düzenli olarak indirin

---

## ✅ Deployment Kontrol Listesi

- [ ] Git repository hazır
- [ ] SECRET_KEY oluşturuldu
- [ ] Environment variables ayarlandı
- [ ] PostgreSQL veritabanı oluşturuldu
- [ ] Web service deploy edildi
- [ ] Migration'lar çalıştırıldı
- [ ] Superuser oluşturuldu
- [ ] Static files toplandı
- [ ] Site test edildi
- [ ] DEBUG=False yapıldı
- [ ] ALLOWED_HOSTS doğru ayarlandı

---

## 🎉 Başarılı Deployment Sonrası

1. **İlk giriş yapın:** `https://your-app.onrender.com/accounts/login/`
2. **Admin paneline girin:** `https://your-app.onrender.com/admin/`
3. **Test verileri ekleyin**
4. **Müşterilere gösterin!** 🚀

---

## 📞 Destek

Sorun yaşarsanız:
1. Logs'ları kontrol edin
2. Environment variables'ı kontrol edin
3. Migration'ları kontrol edin
4. Static files'ı kontrol edin

**İyi şanslar!** 🎊





