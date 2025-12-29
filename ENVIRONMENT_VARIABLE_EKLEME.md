# 🔐 Environment Variable Ekleme - Adım Adım

Environment Variables ekranındasınız! Şimdi 4 variable ekleyeceğiz:

---

## 📝 ADIM ADIM EKLEME:

### 1. İLK VARIABLE: SECRET_KEY

**Kırmızı "NAME_OF_VARIABLE" alanına:**
- Yazın: `SECRET_KEY` (büyük harfle)

**Sağdaki alana (value):**
- Eğer Python'da oluşturduysanız: O key'i yapıştırın
- Eğer oluşturmadıysanız: Şimdi oluşturalım!

**SECRET_KEY oluşturma:**
1. PowerShell'i açın (proje klasöründe)
2. Şunu çalıştırın:
   ```bash
   python manage.py shell
   ```
3. Python shell'de:
   ```python
   from django.core.management.utils import get_random_secret_key
   print(get_random_secret_key())
   ```
4. Çıkan key'i kopyalayın (örnek: `django-insecure-abc123xyz...`)
5. `exit()` yazarak çıkın
6. Bu key'i sağdaki value alanına yapıştırın

**Kaydet:** "Save" veya "Add" butonuna tıklayın

---

### 2. İKİNCİ VARIABLE: DEBUG

**"Add Environment Variable" butonuna tıklayın** (yeni bir satır oluşacak)

**Sol alana (NAME):**
- Yazın: `DEBUG` (büyük harfle)

**Sağ alana (value):**
- Yazın: `False` (büyük F ile, tırnak işareti yok)

**Kaydet:** "Save" veya "Add" butonuna tıklayın

---

### 3. ÜÇÜNCÜ VARIABLE: ALLOWED_HOSTS

**"Add Environment Variable" butonuna tıklayın** (yeni bir satır oluşacak)

**Sol alana (NAME):**
- Yazın: `ALLOWED_HOSTS` (büyük harfle, alt çizgi ile)

**Sağ alana (value):**
- Yazın: `rotexia.onrender.com` (küçük harfle, tırnak işareti yok)
- Veya Web Service'e verdiğiniz isim varsa onu yazın

**Kaydet:** "Save" veya "Add" butonuna tıklayın

---

### 4. DÖRDÜNCÜ VARIABLE: DATABASE_URL

**"Add Environment Variable" butonuna tıklayın** (yeni bir satır oluşacak)

**Sol alana (NAME):**
- Yazın: `DATABASE_URL` (büyük harfle, alt çizgi ile)

**Sağ alana (value):**
- PostgreSQL'den kopyaladığınız URL'yi yapıştırın
- `postgresql://...` ile başlayan URL
- Eğer kaybettinizse:
  1. Render Dashboard → PostgreSQL servisi → "Connections" sekmesi
  2. "Internal Database URL" kısmından kopyalayın

**Kaydet:** "Save" veya "Add" butonuna tıklayın

---

## ✅ SONUÇ:

4 environment variable eklendikten sonra şunları görmelisiniz:

1. ✅ SECRET_KEY → (uzun bir key)
2. ✅ DEBUG → False
3. ✅ ALLOWED_HOSTS → rotexia.onrender.com
4. ✅ DATABASE_URL → postgresql://...

---

## 🎯 SONRA:

Tüm environment variables eklendikten sonra:
- **"Create Web Service"** veya **"Save"** butonuna tıklayın
- Deployment başlayacak!

---

## 📋 ÖZET TABLO:

| Sol Alan (NAME) | Sağ Alan (VALUE) |
|----------------|------------------|
| `SECRET_KEY` | Python'da oluşturduğunuz key |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `rotexia.onrender.com` |
| `DATABASE_URL` | PostgreSQL'den kopyaladığınız URL |

---

## ⚠️ ÖNEMLİ NOTLAR:

- **Büyük/küçük harf önemli!** NAME'ler tam olarak yazıldığı gibi olmalı
- **Tırnak işareti YOK!** Value'larda tırnak kullanmayın
- **Her variable'dan sonra Save/Add butonuna tıklayın**
- **SECRET_KEY:** GitHub'a yüklemeyin, gizli tutun!

---

**Başarılar!** 🚀


