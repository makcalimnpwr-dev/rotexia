# 🏗️ FieldOps - Saha Yönetimi SaaS Platformu
## Kapsamlı Mimari Tasarım Dokümanı

> **Hedef:** Kodlama bilmeyen tek kişilik ekip için, Fieldpie ve Fieldscope'a rakip olabilecek, ölçeklenebilir bir FSM SaaS platformu.

---

## 📋 İçindekiler

1. [Genel Bakış](#genel-bakış)
2. [Mimari Prensipler](#mimari-prensipler)
3. [Sistem Mimarisi](#sistem-mimarisi)
4. [Veritabanı Tasarımı](#veritabanı-tasarımı)
5. [Modül Yapısı](#modül-yapısı)
6. [SaaS Özellikleri](#saas-özellikleri)
7. [Güvenlik](#güvenlik)
8. [API Tasarımı](#api-tasarımı)
9. [Mobil Uygulama](#mobil-uygulama)
10. [Ölçeklenebilirlik](#ölçeklenebilirlik)
11. [Geliştirme Yol Haritası](#geliştirme-yol-haritasi)

---

## 🎯 Genel Bakış

### Platform Özellikleri

**Temel Modüller:**
- ✅ **Müşteri Yönetimi** (Customer Management)
- ✅ **Rota Planlama** (Route Planning)
- ✅ **Görev Yönetimi** (Task Management)
- ✅ **Form/Anket Sistemi** (Survey Builder)
- ✅ **Kullanıcı & Rol Yönetimi** (User & Role Management)
- ⚠️ **Multi-Tenancy** (Eksik - Eklenecek)
- ⚠️ **Abonelik Yönetimi** (Eksik - Eklenecek)
- ⚠️ **Raporlama & Analytics** (Eksik - Eklenecek)
- ⚠️ **Bildirim Sistemi** (Eksik - Eklenecek)

### Teknoloji Stack

```
Backend:     Django 5.0.1
Database:     SQLite (Geliştirme) → PostgreSQL (Production)
Frontend:     Django Templates + Vanilla JS
Admin Panel:  Django Admin + Jazzmin
Mobile:       Progressive Web App (PWA)
Deployment:   Gunicorn + Nginx
```

---

## 🏛️ Mimari Prensipler

### 1. **Modüler Yapı (App-Based Architecture)**
Her özellik ayrı bir Django app'i olarak tasarlanmış:
- `apps.core` - Temel sistem ayarları
- `apps.users` - Kullanıcı yönetimi
- `apps.customers` - Müşteri yönetimi
- `apps.field_operations` - Saha operasyonları
- `apps.forms` - Form/Anket sistemi

### 2. **Separation of Concerns**
- **Models**: Veri yapısı
- **Views**: İş mantığı
- **Templates**: Görünüm katmanı
- **Forms**: Veri doğrulama

### 3. **DRY (Don't Repeat Yourself)**
- Ortak fonksiyonlar `apps.core.utils` içinde
- Template tag'ler ile tekrar kullanılabilir bileşenler

### 4. **Scalability First**
- Multi-tenancy hazırlığı
- JSONField ile esnek veri yapıları
- Cache kullanımı (SiteSettings)

---

## 🏗️ Sistem Mimarisi

### Katmanlı Mimari

```
┌─────────────────────────────────────┐
│   Presentation Layer (Templates)    │
│   - Desktop Web UI                  │
│   - Mobile PWA                       │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│   Business Logic Layer (Views)      │
│   - Route Planning Logic            │
│   - Task Generation                 │
│   - Survey Processing               │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│   Data Access Layer (Models)        │
│   - Customer Model                  │
│   - VisitTask Model                 │
│   - Survey Model                    │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│   Database Layer                    │
│   - SQLite (Dev) / PostgreSQL (Prod)│
└─────────────────────────────────────┘
```

### Request Flow

```
1. User Request → URL Routing (urls.py)
2. URL → View Function (views.py)
3. View → Model Query (models.py)
4. Model → Database
5. Database → Model → View
6. View → Template Rendering
7. Template → HTML Response
```

---

## 💾 Veritabanı Tasarımı

### Mevcut Modeller

#### 1. **Core App**
- `SiteSetting` - Site genel ayarları (Singleton)
- `SystemSetting` - Dinamik sistem ayarları

#### 2. **Users App**
- `CustomUser` - Özelleştirilmiş kullanıcı modeli
- `UserRole` - Dinamik rol sistemi

#### 3. **Customers App**
- `CustomerCari` - Firma/Şube
- `Customer` - Müşteri bilgileri
- `CustomerFieldDefinition` - Dinamik alan tanımları
- `CustomFieldDefinition` - (Eski model, kaldırılabilir)

#### 4. **Field Operations App**
- `RoutePlan` - Rota planı şablonu
- `VisitType` - Ziyaret tipi
- `VisitTask` - Ziyaret görevleri

#### 5. **Forms App**
- `Survey` - Anket tanımları
- `Question` - Sorular
- `QuestionOption` - Soru seçenekleri
- `SurveyAnswer` - Cevaplar

### İlişkiler

```
Customer ──┐
           ├──> VisitTask ──> SurveyAnswer
User ──────┘

Survey ──> Question ──> QuestionOption
              └──> SurveyAnswer
```

---

## 📦 Modül Yapısı

### apps/core
**Amaç:** Sistem genel ayarları ve yardımcı fonksiyonlar

**Özellikler:**
- Site branding (logo, renkler)
- Sistem ayarları yönetimi
- Context processor (her sayfaya ayarları ekler)

**Dosyalar:**
- `models.py` - SiteSetting, SystemSetting
- `views.py` - Home, Settings
- `utils.py` - Yardımcı fonksiyonlar
- `context_processors.py` - Template context

### apps/users
**Amaç:** Kullanıcı ve rol yönetimi

**Özellikler:**
- CustomUser modeli (user_code, role)
- Dinamik rol sistemi
- Kullanıcı CRUD işlemleri

### apps/customers
**Amaç:** Müşteri ve lokasyon yönetimi

**Özellikler:**
- Müşteri bilgileri (kod, ad, adres, koordinat)
- Dinamik özel alanlar (JSONField)
- Harita görünümü
- Excel import/export

### apps/field_operations
**Amaç:** Saha operasyonları ve görev yönetimi

**Özellikler:**
- Rota planlama (28 günlük döngü)
- Otomatik görev oluşturma
- Görev durumu takibi
- Harita görünümü

### apps/forms
**Amaç:** Dinamik form/anket sistemi

**Özellikler:**
- Drag-drop anket builder
- Koşullu sorular (dependency)
- Fotoğraf yükleme
- Filtreleme (müşteri, rol, tarih)

---

## 🏢 SaaS Özellikleri

### ⚠️ Eksik Olan Kritik Özellikler

#### 1. **Multi-Tenancy (Çoklu Kiracı)**
**Neden Gerekli:** Her müşteri kendi verilerini görmeli, diğerlerinden izole olmalı.

**Çözüm Yaklaşımları:**
- **A) Shared Database, Tenant ID ile Filtreleme**
  - Her tabloya `tenant_id` ekle
  - Her sorguya `tenant_id` filtresi ekle
  - ✅ Basit, hızlı implementasyon
  - ❌ Veri karışma riski (kod hatası durumunda)

- **B) Separate Database per Tenant**
  - Her müşteri için ayrı veritabanı
  - ✅ Maksimum izolasyon
  - ❌ Karmaşık, ölçeklenmesi zor

**Öneri:** **A) Yaklaşımı** - Tenant modeli ekleyip, middleware ile otomatik filtreleme

#### 2. **Subscription & Billing**
**Gerekli Modeller:**
- `Tenant` - Şirket/Organizasyon
- `Subscription` - Abonelik planı
- `Plan` - Plan tanımları (Basic, Pro, Enterprise)
- `Payment` - Ödeme kayıtları

**Özellikler:**
- Plan limitleri (kullanıcı sayısı, görev sayısı)
- Otomatik faturalama
- Ödeme geçmişi

#### 3. **Raporlama & Analytics**
- Dashboard istatistikleri
- Görev tamamlanma oranları
- Ziyaret süreleri analizi
- Excel/PDF export

#### 4. **Bildirim Sistemi**
- Email bildirimleri
- SMS bildirimleri (opsiyonel)
- In-app bildirimler

---

## 🔒 Güvenlik

### Mevcut Durum
- ✅ Django'nun built-in güvenlik özellikleri
- ✅ CSRF koruması
- ✅ Password hashing
- ⚠️ Secret key production'da değiştirilmeli
- ⚠️ DEBUG=True production'da kapatılmalı

### Yapılması Gerekenler

1. **Environment Variables**
   ```python
   # .env dosyası kullan
   SECRET_KEY=...
   DEBUG=False
   DATABASE_URL=...
   ```

2. **HTTPS Zorunluluğu**
   - Production'da SSL sertifikası
   - SECURE_SSL_REDIRECT = True

3. **Rate Limiting**
   - API endpoint'lerine rate limit
   - Brute force koruması

4. **Permission System**
   - Role-based access control (RBAC)
   - View-level permissions

---

## 🌐 API Tasarımı

### Mevcut Durum
- Django template-based views (monolitik)
- API endpoint'leri yok

### Önerilen Yapı

**Seçenek 1: Django REST Framework (DRF)**
- ✅ Hızlı geliştirme
- ✅ Otomatik dokümantasyon
- ✅ Serializer'lar ile veri doğrulama

**Seçenek 2: Django Ninja (FastAPI benzeri)**
- ✅ Modern, type-hint desteği
- ✅ Daha hafif

**Öneri:** DRF - Daha olgun, daha fazla kaynak

### API Endpoint Örnekleri

```
GET    /api/v1/customers/          # Müşteri listesi
POST   /api/v1/customers/          # Yeni müşteri
GET    /api/v1/customers/{id}/     # Müşteri detayı
PUT    /api/v1/customers/{id}/     # Müşteri güncelle
DELETE /api/v1/customers/{id}/     # Müşteri sil

GET    /api/v1/tasks/              # Görev listesi
POST   /api/v1/tasks/{id}/complete/ # Görev tamamla
```

---

## 📱 Mobil Uygulama

### Mevcut Durum
- PWA (Progressive Web App) yapısı var
- Mobil template'ler mevcut (`templates/mobile/`)

### Özellikler
- ✅ Görev listesi
- ✅ Görev detayı
- ✅ Anket doldurma
- ✅ Fotoğraf yükleme
- ⚠️ Offline çalışma (eksik)
- ⚠️ Push notification (eksik)

### İyileştirme Önerileri
1. Service Worker ekle (offline çalışma)
2. App manifest düzenle
3. Native app wrapper (React Native / Flutter) - Gelecek

---

## 📈 Ölçeklenebilirlik

### Mevcut Durum
- SQLite (geliştirme)
- Tek sunucu mimarisi

### Production Hazırlığı

1. **Database**
   - SQLite → PostgreSQL
   - Connection pooling
   - Read replicas (gelecek)

2. **Caching**
   - Redis cache backend
   - Query result caching

3. **Static Files**
   - CDN (CloudFlare, AWS CloudFront)
   - WhiteNoise (basit çözüm)

4. **Background Tasks**
   - Celery + Redis
   - Görev oluşturma, email gönderme

5. **Monitoring**
   - Sentry (hata takibi)
   - Analytics (Google Analytics)

---

## 🗺️ Geliştirme Yol Haritası

### Faz 1: Temel SaaS Altyapısı (Kritik)
- [ ] Multi-tenancy sistemi
- [ ] Tenant modeli ve middleware
- [ ] Subscription modeli
- [ ] Plan yönetimi

### Faz 2: Güvenlik & Production Hazırlığı
- [ ] Environment variables
- [ ] PostgreSQL migration
- [ ] HTTPS yapılandırması
- [ ] Error logging (Sentry)

### Faz 3: API & Mobil İyileştirmeleri
- [ ] Django REST Framework entegrasyonu
- [ ] API authentication (JWT)
- [ ] PWA offline desteği
- [ ] Push notifications

### Faz 4: İleri Özellikler
- [ ] Raporlama modülü
- [ ] Dashboard analytics
- [ ] Email/SMS bildirimleri
- [ ] Excel/PDF export

### Faz 5: Ölçeklenebilirlik
- [ ] Redis cache
- [ ] Celery background tasks
- [ ] CDN entegrasyonu
- [ ] Load balancing hazırlığı

---

## 📚 Kodlama Bilgisi Olmayanlar İçin Notlar

### Django Yapısı

**Model (models.py):**
- Veritabanı tablolarını tanımlar
- Örnek: `Customer` modeli = `customers` tablosu

**View (views.py):**
- Kullanıcı isteklerini işler
- Veritabanından veri çeker
- Template'e gönderir

**Template (templates/):**
- HTML sayfaları
- Django template syntax kullanır

**URL (urls.py):**
- Hangi URL'nin hangi view'a gideceğini belirler
- Örnek: `/customers/list/` → `customer_list` view'ı

### Yeni Özellik Ekleme Adımları

1. **Model Ekle** (`models.py`)
   ```python
   class YeniModel(models.Model):
       name = models.CharField(max_length=100)
   ```

2. **Migration Oluştur**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

3. **View Ekle** (`views.py`)
   ```python
   def yeni_liste(request):
       items = YeniModel.objects.all()
       return render(request, 'template.html', {'items': items})
   ```

4. **URL Ekle** (`urls.py`)
   ```python
   path('yeni/', views.yeni_liste, name='yeni_liste'),
   ```

5. **Template Oluştur** (`templates/yeni.html`)

---

## 🎯 Sonuç

Bu mimari, tek kişilik bir ekip için:
- ✅ **Basit** - Anlaşılır yapı
- ✅ **Ölçeklenebilir** - Büyüyebilir
- ✅ **Bakımı Kolay** - Modüler yapı
- ✅ **Güvenli** - Django'nun güvenlik özellikleri

**Sonraki Adım:** Multi-tenancy sistemini ekleyerek SaaS altyapısını tamamlamak.

---

*Son Güncelleme: 2024*




