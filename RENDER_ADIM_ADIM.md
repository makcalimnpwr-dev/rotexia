# 🚀 Render.com ile Rotexia Deployment - Adım Adım Rehber

Bu rehber, Rotexia projenizi Render.com'da canlıya almak için tüm adımları içerir.

---

## 📋 ÖN HAZIRLIK

### Adım 1: GitHub Repository Oluşturma

1. **GitHub'a gidin:** [github.com](https://github.com)
2. **Yeni repository oluşturun:**
   - Sağ üstte "+" → "New repository"
   - Repository name: `rotexia` (veya istediğiniz isim)
   - Public veya Private seçin
   - "Create repository" tıklayın

### Adım 2: Projeyi GitHub'a Yükleme

**Terminal/PowerShell'de proje klasörünüzde:**

```bash
# Git başlat (eğer başlatılmadıysa)
git init

# Tüm dosyaları ekle
git add .

# İlk commit
git commit -m "Rotexia - İlk deployment hazırlığı"

# Ana branch'i main yap
git branch -M main

# GitHub repository'nizi ekleyin (URL'yi kendi repo'nuzla değiştirin)
git remote add origin https://github.com/KULLANICI_ADINIZ/rotexia.git

# GitHub'a gönder
git push -u origin main
```

✅ **Kontrol:** GitHub'da dosyalarınızı görebiliyor musunuz?

---

## 🔑 Adım 3: SECRET_KEY Oluşturma

**Python'da SECRET_KEY oluşturun:**

1. Terminal'de proje klasöründe:
```bash
python manage.py shell
```

2. Python shell'de:
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

3. Çıkan key'i kopyalayın (örnek: `django-insecure-abc123xyz...`)
4. `exit()` yazarak shell'den çıkın

✅ **Bu key'i saklayın, bir sonraki adımda kullanacağız!**

---

## 🌐 RENDER.COM KURULUMU

### Adım 4: Render.com Hesabı Oluşturma

1. **Render.com'a gidin:** [render.com](https://render.com)
2. **"Get Started for Free" tıklayın**
3. **GitHub ile giriş yapın** (önerilir) veya email ile kayıt olun
4. **GitHub hesabınızı bağlayın** (eğer GitHub ile giriş yaptıysanız)

✅ **Hesabınız hazır!**

---

## 🗄️ Adım 5: PostgreSQL Veritabanı Oluşturma

1. **Render Dashboard'da:**
   - "New +" butonuna tıklayın (sağ üstte)
   - "PostgreSQL" seçin

2. **Veritabanı Ayarları:**
   - **Name:** `rotexia-db` (veya istediğiniz isim)
   - **Database:** `rotexia` (otomatik doldurulur)
   - **User:** `rotexia_user` (otomatik doldurulur)
   - **Region:** En yakın bölgeyi seçin (Avrupa: `Frankfurt` önerilir)
   - **PostgreSQL Version:** En son sürüm (varsayılan)
   - **Plan:** **Free** seçin (ücretsiz)

3. **"Create Database" tıklayın**

4. **Veritabanı oluştuktan sonra:**
   - Veritabanı sayfasına gidin
   - **"Connections" sekmesine** tıklayın
   - **"Internal Database URL"** kısmındaki URL'yi kopyalayın
   - Bu URL şuna benzer olacak: `postgresql://rotexia_user:xxxxx@dpg-xxxxx-a/rotexia`

✅ **DATABASE_URL'yi kopyaladınız mı? Bir sonraki adımda kullanacağız!**

---

## 🌍 Adım 6: Web Service Oluşturma

1. **Render Dashboard'da:**
   - "New +" butonuna tıklayın
   - **"Web Service"** seçin

2. **GitHub Repository Bağlama:**
   - GitHub hesabınızı seçin (eğer bağlı değilse bağlayın)
   - **Repository'nizi seçin:** `rotexia` (veya oluşturduğunuz isim)
   - **"Connect" tıklayın**

3. **Web Service Ayarları:**

   **Temel Bilgiler:**
   - **Name:** `rotexia` (veya istediğiniz isim)
   - **Region:** En yakın bölge (veritabanıyla aynı olmalı)
   - **Branch:** `main` (varsayılan)
   - **Root Directory:** (boş bırakın)

   **Build & Deploy:**
   - **Environment:** `Python 3` seçin
   - **Build Command:** 
     ```
     pip install -r requirements.txt && python manage.py collectstatic --noinput
     ```
   - **Start Command:**
     ```
     gunicorn config.wsgi:application
     ```

4. **Environment Variables Ekleme:**

   "Advanced" bölümünde "Add Environment Variable" butonuna tıklayarak şunları ekleyin:

   **1. SECRET_KEY:**
   - Key: `SECRET_KEY`
   - Value: Adım 3'te oluşturduğunuz key'i yapıştırın

   **2. DEBUG:**
   - Key: `DEBUG`
   - Value: `False`

   **3. ALLOWED_HOSTS:**
   - Key: `ALLOWED_HOSTS`
   - Value: `rotexia.onrender.com` (veya Render'ın size vereceği domain)

   **4. DATABASE_URL:**
   - Key: `DATABASE_URL`
   - Value: Adım 5'te kopyaladığınız PostgreSQL URL'ini yapıştırın

   **5. PYTHON_VERSION (opsiyonel):**
   - Key: `PYTHON_VERSION`
   - Value: `3.11.9`

5. **"Create Web Service" tıklayın**

✅ **Deployment başladı! 2-5 dakika sürebilir.**

---

## ⏳ Adım 7: Deployment Bekleme

1. **Deployment durumunu izleyin:**
   - Dashboard'da servisinize tıklayın
   - "Events" sekmesinde build loglarını görebilirsiniz
   - "Logs" sekmesinde canlı logları izleyebilirsiniz

2. **Başarılı deployment için bekleyin:**
   - Yeşil "Live" yazısı göründüğünde hazır!
   - Eğer hata varsa, logları kontrol edin

✅ **Deployment tamamlandı!**

---

## 🗄️ Adım 8: İlk Kurulum (Migration ve Superuser)

1. **Render Dashboard'da:**
   - Servisinize tıklayın
   - **"Shell" sekmesine** tıklayın (üst menüde)

2. **Shell'de şu komutları çalıştırın:**

   ```bash
   # Migration'ları çalıştır
   python manage.py migrate
   ```

   Bu komut veritabanı tablolarını oluşturur. Biraz sürebilir.

   ```bash
   # Superuser (admin) oluştur
   python manage.py createsuperuser
   ```

   - Username: `admin` (veya istediğiniz)
   - Email: (opsiyonel)
   - Password: Güçlü bir şifre girin (görünmeyecek, normal)

✅ **Kurulum tamamlandı!**

---

## 🎉 Adım 9: Siteyi Test Etme

1. **Site URL'inizi alın:**
   - Render Dashboard'da servisinize tıklayın
   - Üstte site URL'iniz görünür: `https://rotexia.onrender.com`

2. **Test edin:**
   - Ana sayfa: `https://rotexia.onrender.com`
   - Giriş sayfası: `https://rotexia.onrender.com/accounts/login/`
   - Admin paneli: `https://rotexia.onrender.com/admin/`

3. **Admin paneline giriş yapın:**
   - Adım 8'de oluşturduğunuz kullanıcı adı ve şifre ile

✅ **Site canlıda ve çalışıyor!**

---

## 🔄 Güncelleme Nasıl Yapılır?

### Otomatik Güncelleme (Çok Kolay!):

1. **Yerel bilgisayarınızda kodu değiştirin**

2. **GitHub'a gönderin:**
   ```bash
   git add .
   git commit -m "Yeni özellik eklendi"
   git push origin main
   ```

3. **Render otomatik olarak deploy eder!**
   - Dashboard'da yeni deployment göreceksiniz
   - 2-5 dakika içinde site güncellenir

✅ **Bu kadar! Otomatik güncelleme yapıldı!**

---

## 🆘 Sorun Giderme

### Site Açılmıyor (500 Error)

1. **Logs kontrol edin:**
   - Dashboard → Servisiniz → "Logs" sekmesi
   - Hata mesajını okuyun

2. **Yaygın sorunlar:**
   - Migration çalıştırılmamış → Shell'de `python manage.py migrate`
   - SECRET_KEY yanlış → Environment variables kontrol edin
   - DATABASE_URL yanlış → PostgreSQL URL'ini kontrol edin

### Static Files Görünmüyor

Shell'de çalıştırın:
```bash
python manage.py collectstatic --noinput
```

### Database Bağlantı Hatası

1. **DATABASE_URL doğru mu?**
   - Environment variables'da kontrol edin
   - PostgreSQL servisinin çalıştığından emin olun

2. **PostgreSQL uyku modunda mı?**
   - Free plan'da 90 gün kullanılmazsa uyku moduna geçer
   - İlk istekte otomatik uyanır (30 saniye sürebilir)

### Deployment Başarısız

1. **Build loglarını kontrol edin:**
   - Dashboard → Servisiniz → "Events" sekmesi
   - Hangi adımda hata olduğunu görün

2. **Yaygın hatalar:**
   - `requirements.txt` eksik paket → Ekleyin
   - Python versiyonu uyumsuz → `runtime.txt` kontrol edin
   - Build command hatalı → Build command'i kontrol edin

---

## 📝 Kontrol Listesi

Deployment öncesi:
- [ ] GitHub repository oluşturuldu
- [ ] Kod GitHub'a yüklendi
- [ ] SECRET_KEY oluşturuldu
- [ ] Render.com hesabı oluşturuldu

Deployment sırasında:
- [ ] PostgreSQL veritabanı oluşturuldu
- [ ] DATABASE_URL kopyalandı
- [ ] Web service oluşturuldu
- [ ] Environment variables eklendi (SECRET_KEY, DEBUG, ALLOWED_HOSTS, DATABASE_URL)
- [ ] Build command doğru
- [ ] Start command doğru

Deployment sonrası:
- [ ] Migration çalıştırıldı
- [ ] Superuser oluşturuldu
- [ ] Site açılıyor
- [ ] Giriş yapılabiliyor
- [ ] Admin paneli çalışıyor

---

## 🎊 Tebrikler!

Rotexia projeniz artık canlıda! Müşterilerinize gösterebilirsiniz. 🚀

**Site URL'iniz:** `https://rotexia.onrender.com` (veya Render'ın verdiği URL)

**Güncelleme yapmak için:** Sadece GitHub'a push edin, gerisi otomatik!

---

## 💡 İpuçları

1. **Ücretsiz plan limitleri:**
   - PostgreSQL: 90 gün kullanılmazsa uyku modu
   - Web Service: 750 saat/ay (yeterli)
   - Disk: 512 MB

2. **Performans:**
   - İlk istek yavaş olabilir (uyku modundan uyanma)
   - Sonraki istekler normal hızda

3. **Yedekleme:**
   - Düzenli olarak veritabanı yedeği alın
   - Shell'de: `pg_dump $DATABASE_URL > backup.sql`

**Başarılar!** 🎉

