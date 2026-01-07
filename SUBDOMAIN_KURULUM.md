# Subdomain Multi-Tenancy Kurulum Rehberi

## ✅ Tamamlanan İşlemler

1. ✅ Settings'de `SUBDOMAIN_DOMAIN` ayarı eklendi
2. ✅ Session cookie domain ayarları yapılandırıldı
3. ✅ Middleware'de subdomain kontrolü iyileştirildi
4. ✅ Admin panel subdomain desteği eklendi (`admin.fieldops.com`)

## 📋 Mevcut Tenant'lar

Şu anki tenant'lar ve slug'ları:
- **Deneme**: `slug=deneme` → `deneme.fieldops.com`
- **Pastel**: `slug=pastel` → `pastel.fieldops.com`

## 🚀 Production Kurulumu

### 1. DNS Yapılandırması

DNS sağlayıcınızda (GoDaddy, Namecheap, vb.) şu kayıtları ekleyin:

```
# Wildcard A kaydı (tüm subdomain'ler için)
*.fieldops.com    A    [SUNUCU_IP_ADRESI]

# Ana domain (isteğe bağlı)
fieldops.com      A    [SUNUCU_IP_ADRESI]

# Admin paneli için özel kayıt (isteğe bağlı, wildcard yeterli)
admin.fieldops.com A   [SUNUCU_IP_ADRESI]
```

### 2. Environment Variables

`.env` dosyasında veya sunucu environment'ında:

```bash
SUBDOMAIN_DOMAIN=fieldops.com
ALLOWED_HOSTS=fieldops.com,*.fieldops.com
```

### 3. Test Etme

Production'da test etmek için:
```
https://admin.fieldops.com → Admin paneli
https://deneme.fieldops.com → Deneme firması
https://pastel.fieldops.com → Pastel firması
```

## 🧪 Development Kurulumu (Localhost)

### Windows için Hosts Dosyası Düzenleme

1. **Notepad'i Yönetici olarak açın**
2. Şu dosyayı açın: `C:\Windows\System32\drivers\etc\hosts`
3. En alta şu satırları ekleyin:

```
127.0.0.1    admin.localhost
127.0.0.1    deneme.localhost
127.0.0.1    pastel.localhost
```

4. Dosyayı kaydedin

### Django Development Server

```bash
# Normal şekilde çalıştırın (localhost:8000)
python manage.py runserver

# Veya özel port:
python manage.py runserver 8000
```

### Test Etme

Tarayıcıda şu adresleri kullanın:
```
http://admin.localhost:8000 → Admin paneli
http://deneme.localhost:8000 → Deneme firması
http://pastel.localhost:8000 → Pastel firması
```

**NOT:** `localhost:8000` ile de çalışmaya devam eder (session bazlı), ama subdomain'ler daha güvenli!

## 📝 Yeni Tenant Ekleme

### 1. Django Admin'den veya Kod ile:

```python
from apps.core.models import Tenant

# Yeni tenant oluştur
tenant = Tenant.objects.create(
    name="Yeni Firma",
    slug="yeni-firma",  # ← Bu subdomain ile eşleşecek: yeni-firma.fieldops.com
    email="info@yenifirma.com",
    is_active=True
)
```

### 2. Slug Kontrolü

Her tenant'ın `slug` değeri subdomain ile eşleşmeli:
- `slug="deneme"` → `deneme.fieldops.com`
- `slug="pastel"` → `pastel.fieldops.com`
- `slug="yeni-firma"` → `yeni-firma.fieldops.com`

**Önemli:** Slug'lar:
- Küçük harf olmalı
- Türkçe karakter olmamalı (ı → i, ş → s, vb.)
- Boşluk yerine tire (-) kullanılmalı

## 🔐 Güvenlik Notları

### Session Cookie Domain

**Development (localhost):**
- `SESSION_COOKIE_DOMAIN = None` → Her subdomain kendi session'ını kullanır (GÜVENLİ)

**Production:**
- `SESSION_COOKIE_DOMAIN = '.fieldops.com'` → Tüm subdomain'ler aynı session'ı kullanır (Daha az güvenli ama pratik)

**Öneri:** Production'da da `None` kullanabilirsiniz, böylece her subdomain tamamen izole olur.

## 🐛 Sorun Giderme

### Subdomain çalışmıyor?

1. **DNS kontrolü:**
   ```bash
   nslookup deneme.fieldops.com
   # veya
   ping deneme.fieldops.com
   ```

2. **Hosts dosyası kontrolü (development):**
   - Windows: `C:\Windows\System32\drivers\etc\hosts`
   - Linux/Mac: `/etc/hosts`

3. **Django logs kontrolü:**
   ```bash
   python manage.py runserver --verbosity 2
   ```

### Tenant bulunamıyor?

```bash
python manage.py shell
```

```python
from apps.core.models import Tenant
tenants = Tenant.objects.all()
for t in tenants:
    print(f"{t.name}: slug={t.slug}")
```

### Session karışıyor?

- Development'ta `SESSION_COOKIE_DOMAIN = None` olduğundan emin olun
- Tarayıcıda cookie'leri temizleyin
- Her subdomain için farklı tarayıcı/private window kullanın

## 📊 Avantajlar

✅ **Güvenlik:** Her firma tamamen izole
✅ **Performans:** Subdomain bazlı cache
✅ **Ölçeklenebilirlik:** Farklı firmalar farklı sunuculara taşınabilir
✅ **Kod:** Tek kod, tek güncelleme, tüm firmalara uygulanır

## 🎯 Sonraki Adımlar

1. DNS yapılandırmasını yapın (production için)
2. Hosts dosyasını düzenleyin (development için)
3. Test edin
4. Yeni tenant eklerken slug'ları subdomain ile eşleştirmeyi unutmayın











