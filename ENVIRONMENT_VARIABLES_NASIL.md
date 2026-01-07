# 🔐 Environment Variables - Key'ler Nerede?

Web Service oluştururken 4 environment variable eklemeniz gerekiyor. İşte her birini nasıl bulacağınız:

---

## 1. SECRET_KEY (Git'in Güvenlik Anahtarı)

### Eğer Daha Önce Oluşturmadıysanız:

**Python'da oluşturun:**

1. **PowerShell'i açın** (proje klasöründe)
2. Şu komutu çalıştırın:
   ```bash
   python manage.py shell
   ```
3. Python shell'de şunu yazın:
   ```python
   from django.core.management.utils import get_random_secret_key
   print(get_random_secret_key())
   ```
4. Enter'a basın
5. **Çıkan key'i kopyalayın** (örnek: `django-insecure-abc123xyz...`)
6. `exit()` yazarak shell'den çıkın

**Bu key'i SECRET_KEY değeri olarak kullanacaksınız!**

---

## 2. DEBUG (Hata Ayıklama Modu)

**Çok Basit:**
- Key: `DEBUG`
- Value: `False` (sadece bu kelimeyi yazın, tırnak işareti yok)

**Açıklama:**
- Production'da mutlaka `False` olmalı
- Güvenlik için önemli

---

## 3. ALLOWED_HOSTS (İzin Verilen Domain'ler)

**Seçenek 1: Render'ın Vereceği Domain**
- Web Service oluşturduktan sonra Render size bir domain verecek
- Örnek: `rotexia.onrender.com`
- Bu domain'i kullanabilirsiniz

**Seçenek 2: Genel Domain (Önerilen)**
- Key: `ALLOWED_HOSTS`
- Value: `rotexia.onrender.com`
- (Eğer farklı bir isim kullandıysanız, o ismi yazın)

**Açıklama:**
- Render otomatik olarak `your-app-name.onrender.com` formatında domain verir
- Bu domain'i kullanabilirsiniz

---

## 4. DATABASE_URL (Veritabanı Bağlantı URL'si)

**ZATEN VAR!** ✅

- Bu, PostgreSQL oluştururken kopyaladığınız URL
- Eğer kaybettinizse:
  1. Render Dashboard'a gidin
  2. PostgreSQL servisinize tıklayın
  3. **"Connections"** sekmesine gidin
  4. **"Internal Database URL"** kısmındaki URL'yi kopyalayın
  5. Bu URL `postgresql://...` ile başlar

**Bu URL'yi DATABASE_URL değeri olarak kullanacaksınız!**

---

## 📝 ÖZET TABLO:

| Key | Value Nereden | Örnek Value |
|-----|--------------|-------------|
| **SECRET_KEY** | Python'da oluşturun (yukarıda anlatıldı) | `django-insecure-abc123...` |
| **DEBUG** | Sadece `False` yazın | `False` |
| **ALLOWED_HOSTS** | Render domain'i veya `rotexia.onrender.com` | `rotexia.onrender.com` |
| **DATABASE_URL** | PostgreSQL Connections'dan kopyalayın | `postgresql://user:pass@host/db` |

---

## 🔧 ADIM ADIM EKLEME:

Render'da Web Service oluştururken:

1. **"Add Environment Variable"** butonuna tıklayın

2. **Her birini ekleyin:**

   **1. SECRET_KEY ekleyin:**
   - Key: `SECRET_KEY`
   - Value: (Python'da oluşturduğunuz key'i yapıştırın)
   - "Save" tıklayın

   **2. DEBUG ekleyin:**
   - Key: `DEBUG`
   - Value: `False`
   - "Save" tıklayın

   **3. ALLOWED_HOSTS ekleyin:**
   - Key: `ALLOWED_HOSTS`
   - Value: `rotexia.onrender.com`
   - "Save" tıklayın

   **4. DATABASE_URL ekleyin:**
   - Key: `DATABASE_URL`
   - Value: (PostgreSQL'den kopyaladığınız URL'yi yapıştırın)
   - "Save" tıklayın

3. Tüm environment variables eklendikten sonra **"Create Web Service"** tıklayın

---

## ⚠️ ÖNEMLİ NOTLAR:

- **SECRET_KEY:** Her zaman gizli tutun, GitHub'a yüklemeyin!
- **DEBUG:** Production'da mutlaka `False` olmalı
- **ALLOWED_HOSTS:** Tırnak işareti YOK, sadece domain adı
- **DATABASE_URL:** PostgreSQL ile aynı region'da olmalı

---

## 🆘 SORUN MU VAR?

**SECRET_KEY oluşturamıyorum:**
- `python manage.py shell` komutunu çalıştırdınız mı?
- Python yüklü mü kontrol edin

**DATABASE_URL kaybettim:**
- Render Dashboard → PostgreSQL servisi → Connections sekmesi

**Environment variable ekleyemiyorum:**
- "Add Environment Variable" butonuna tıklayın
- Key ve Value'yu yazın
- "Save" tıklayın

---

**Başarılar!** 🚀












