# 🚀 FieldOps - Kurulum ve Başlangıç Rehberi

> **Hedef Kitle:** Kodlama bilmeyen tek kişilik ekip için basit kurulum rehberi

---

## 📋 İçindekiler

1. [Gereksinimler](#gereksinimler)
2. [Kurulum Adımları](#kurulum-adımları)
3. [İlk Çalıştırma](#ilk-çalıştırma)
4. [Yapılandırma](#yapılandırma)
5. [Sık Karşılaşılan Sorunlar](#sık-karşılaşılan-sorunlar)

---

## 🔧 Gereksinimler

### Yazılım Gereksinimleri

- **Python 3.10 veya üzeri**
  - Kontrol etmek için: `python --version`
  - İndirmek için: [python.org](https://www.python.org/downloads/)

- **pip** (Python paket yöneticisi - genelde Python ile birlikte gelir)

- **Git** (opsiyonel - kodları indirmek için)
  - İndirmek için: [git-scm.com](https://git-scm.com/downloads)

### Sistem Gereksinimleri

- **RAM:** Minimum 2GB (4GB önerilir)
- **Disk:** Minimum 1GB boş alan
- **İşletim Sistemi:** Windows, macOS veya Linux

---

## 📦 Kurulum Adımları

### 1. Projeyi İndirin

Eğer Git kullanıyorsanız:
```bash
git clone <repository-url>
cd field_ops_project
```

Ya da ZIP olarak indirip açın.

### 2. Python Sanal Ortamı Oluşturun

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

✅ Başarılı olduysa, terminal'inizde `(venv)` yazısı görünecek.

### 3. Gerekli Paketleri Yükleyin

```bash
pip install -r requirements.txt
```

⏳ Bu işlem birkaç dakika sürebilir.

### 4. Environment Variables Ayarlayın

`.env.example` dosyasını `.env` olarak kopyalayın:

**Windows:**
```bash
copy .env.example .env
```

**macOS/Linux:**
```bash
cp .env.example .env
```

Sonra `.env` dosyasını bir metin editörü ile açın ve `SECRET_KEY` değerini değiştirin:

```env
SECRET_KEY=buraya-rastgele-bir-anahtar-yazin
```

🔑 Secret key üretmek için:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 5. Veritabanını Oluşturun

```bash
python manage.py migrate
```

Bu komut, veritabanı tablolarını oluşturur.

### 6. Süper Kullanıcı Oluşturun

Admin paneline giriş yapmak için:

```bash
python manage.py createsuperuser
```

Soruları yanıtlayın:
- Kullanıcı adı: `admin` (veya istediğiniz)
- E-posta: `admin@example.com` (veya istediğiniz)
- Şifre: Güçlü bir şifre girin

---

## 🎯 İlk Çalıştırma

### Development Sunucusunu Başlatın

```bash
python manage.py runserver
```

✅ Başarılı olduysa şu mesajı göreceksiniz:
```
Starting development server at http://127.0.0.1:8000/
```

### Tarayıcıda Açın

1. Tarayıcınızı açın
2. Adres çubuğuna yazın: `http://127.0.0.1:8000/`
3. Ana sayfayı göreceksiniz!

### Admin Paneline Giriş

1. Tarayıcıda: `http://127.0.0.1:8000/admin/`
2. Oluşturduğunuz süper kullanıcı bilgileriyle giriş yapın

---

## ⚙️ Yapılandırma

### 1. Site Ayarları

Admin panelinden:
1. **Core → Site Ayarları** → Site başlığı, logo, renkler
2. **Core → Sistem Ayarları** → Diğer ayarlar

### 2. İlk Tenant (Kiracı) Oluşturma

SaaS yapısı için ilk şirketi oluşturun:

1. Admin panel → **Core → Kiracılar (Tenants)**
2. **Add Tenant** butonuna tıklayın
3. Bilgileri doldurun:
   - **Name:** Şirket adı
   - **Slug:** URL'de görünecek kısaltma (örn: `acme-corp`)
   - **Email:** İletişim e-postası
   - **Plan:** Bir plan seçin (önce plan oluşturmanız gerekebilir)

### 3. İlk Plan Oluşturma

1. Admin panel → **Core → Abonelik Planları**
2. **Add Plan** butonuna tıklayın
3. Örnek plan:
   - **Name:** Ücretsiz Plan
   - **Plan Type:** Temel
   - **Price Monthly:** 0
   - **Max Users:** 3
   - **Max Customers:** 20

### 4. İlk Kullanıcı Oluşturma

1. Admin panel → **Users → Custom Users**
2. Yeni kullanıcı ekleyin
3. **Role** seçin (önce rol oluşturmanız gerekebilir)

---

## 🐛 Sık Karşılaşılan Sorunlar

### Problem: "ModuleNotFoundError: No module named 'dotenv'"

**Çözüm:**
```bash
pip install python-dotenv
```

### Problem: "django.db.utils.OperationalError: no such table"

**Çözüm:**
```bash
python manage.py migrate
```

### Problem: "SECRET_KEY bulunamadı" hatası

**Çözüm:**
1. `.env` dosyasının proje kök dizininde olduğundan emin olun
2. `.env` dosyasında `SECRET_KEY=...` satırının olduğundan emin olun

### Problem: Port 8000 zaten kullanılıyor

**Çözüm:**
Farklı bir port kullanın:
```bash
python manage.py runserver 8001
```

### Problem: "Permission denied" hatası

**Çözüm (Windows):**
- PowerShell'i "Yönetici olarak çalıştır" ile açın

**Çözüm (macOS/Linux):**
- `sudo` kullanmayın, normal kullanıcı olarak çalıştırın

---

## 📚 Sonraki Adımlar

1. ✅ **Mimari Dokümantasyonu Okuyun:** `MIMARI_TASARIM.md`
2. ✅ **İlk Müşteriyi Ekleyin:** Admin panel → Customers
3. ✅ **İlk Rotayı Oluşturun:** Admin panel → Field Operations
4. ✅ **İlk Anketi Oluşturun:** Admin panel → Forms

---

## 🆘 Yardım

Sorun yaşıyorsanız:
1. Hata mesajını tam olarak okuyun
2. Google'da hata mesajını arayın
3. Django dokümantasyonuna bakın: [docs.djangoproject.com](https://docs.djangoproject.com)

---

## 🎉 Başarılar!

Artık FieldOps platformunuz çalışıyor! 🚀

*Son Güncelleme: 2024*




