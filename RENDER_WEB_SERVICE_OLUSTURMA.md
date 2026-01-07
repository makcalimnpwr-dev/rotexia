# 🌐 Render.com - Web Service Oluşturma

Database URL'yi kopyaladınız! Şimdi Web Service oluşturalım:

---

## 📝 ADIM 1: Web Service Başlatma

1. **Render Dashboard'a gidin**
2. **"New +" butonuna tıklayın** (sağ üstte)
3. **"Web Service" seçin**

---

## 🔗 ADIM 2: GitHub Repository Bağlama

1. **"Connect account"** veya **"Connect GitHub"** butonuna tıklayın (eğer bağlı değilse)
2. GitHub hesabınızı bağlayın
3. **Repository'nizi seçin:** `makcalimnpwr-dev/rotexia`
4. **"Connect"** tıklayın

---

## ⚙️ ADIM 3: Web Service Ayarları

### Temel Bilgiler:

1. **Name (İsim):**
   - Yazın: `rotexia` (veya istediğiniz isim)

2. **Region (Bölge):**
   - PostgreSQL ile aynı bölgeyi seçin (Frankfurt veya Ireland)
   - **Önemli:** PostgreSQL ile aynı region olmalı!

3. **Branch:**
   - `main` (varsayılan, değiştirmeyin)

4. **Root Directory:**
   - **BOŞ BIRAKIN** (varsayılan)

---

## 🔨 ADIM 4: Build & Deploy Ayarları

### Environment (Ortam):
- **Seçin:** `Python 3`

### Build Command (Önemli!):
Şunu yazın:
```
pip install -r requirements.txt && python manage.py collectstatic --noinput
```

### Start Command (Önemli!):
Şunu yazın:
```
gunicorn config.wsgi:application
```

---

## 🔐 ADIM 5: Environment Variables (ÇOK ÖNEMLİ!)

**"Add Environment Variable"** butonuna tıklayarak şunları ekleyin:

### 1. SECRET_KEY:
- **Key:** `SECRET_KEY`
- **Value:** Daha önce oluşturduğunuz SECRET_KEY'i yapıştırın
- (Eğer oluşturmadıysanız, şu komutu Python'da çalıştırın:)
  ```python
  from django.core.management.utils import get_random_secret_key
  print(get_random_secret_key())
  ```

### 2. DEBUG:
- **Key:** `DEBUG`
- **Value:** `False`

### 3. ALLOWED_HOSTS:
- **Key:** `ALLOWED_HOSTS`
- **Value:** `rotexia.onrender.com` (veya Render'ın size vereceği domain)

### 4. DATABASE_URL:
- **Key:** `DATABASE_URL`
- **Value:** Kopyaladığınız PostgreSQL Internal Database URL'yi yapıştırın
- (postgresql://... ile başlayan URL)

### 5. PYTHON_VERSION (Opsiyonel):
- **Key:** `PYTHON_VERSION`
- **Value:** `3.11.9`

---

## ✅ ADIM 6: Plan Seçimi

- Scroll aşağı yapın
- **"Free"** planını seçin

---

## 🚀 ADIM 7: Deploy!

**"Create Web Service"** butonuna tıklayın!

---

## ⏳ ADIM 8: Deployment Bekleme

1. Deployment başlayacak (2-5 dakika sürebilir)
2. "Events" sekmesinde build loglarını görebilirsiniz
3. "Logs" sekmesinde canlı logları izleyebilirsiniz
4. Yeşil **"Live"** yazısı göründüğünde hazır!

---

## 🗄️ ADIM 9: İlk Kurulum (Migration)

Deployment tamamlandıktan sonra:

1. **Shell sekmesine tıklayın** (üst menüde)
2. Şu komutu çalıştırın:
   ```bash
   python manage.py migrate
   ```
3. Enter'a basın
4. Biraz sürebilir (veritabanı tabloları oluşturulur)

---

## 👤 ADIM 10: Superuser (Admin) Oluşturma

Shell'de:
```bash
python manage.py createsuperuser
```
Enter'a basın.

**Sorular:**
- Username: `admin` (veya istediğiniz)
- Email: (opsiyonel, Enter'a basabilirsiniz)
- Password: Güçlü bir şifre yazın (görünmeyecek, normal)

---

## 🎉 ADIM 11: Siteyi Test Edin!

1. **Site URL'inizi alın:**
   - Render Dashboard'da servisinize tıklayın
   - Üstte site URL'iniz görünür: `https://rotexia.onrender.com`

2. **Test edin:**
   - Ana sayfa: `https://rotexia.onrender.com`
   - Giriş sayfası: `https://rotexia.onrender.com/accounts/login/`
   - Admin paneli: `https://rotexia.onrender.com/admin/`

3. **Admin paneline giriş yapın:**
   - Adım 10'da oluşturduğunuz kullanıcı adı ve şifre ile

---

## ✅ TAMAMLANDI!

Rotexia projeniz artık canlıda! 🎊

---

## 🆘 SORUN MU VAR?

**Deployment başarısız oldu:**
- "Events" sekmesinde logları kontrol edin
- Environment variables doğru mu kontrol edin
- Build command doğru mu kontrol edin

**Site çalışmıyor:**
- Migration çalıştırdınız mı? (Adım 9)
- DATABASE_URL doğru mu?
- SECRET_KEY doğru mu?

**Static files görünmüyor:**
- Shell'de: `python manage.py collectstatic --noinput`

---

**Başarılar!** 🚀












