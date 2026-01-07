# Subdomain Yaklaşımı: Tek Kod, Çoklu Subdomain

## Yanlış Anlama ❌
**YANLIŞ:** Her firma için ayrı Django uygulaması kurulacak, 10 firma = 10 ayrı sistem

## Doğru Yaklaşım ✅
**DOĞRU:** Tek Django uygulaması, farklı subdomain'lerden gelen istekleri farklı tenant'lara yönlendirir

---

## Nasıl Çalışır?

### 1. Tek Django Uygulaması (Kod)
```
field_ops_project1/
├── apps/
├── config/
├── templates/
└── manage.py  ← Tek dosya, tek kod
```

### 2. DNS Yapılandırması (Wildcard)
```
*.fieldops.com  → Aynı sunucuya yönlenir (wildcard DNS)
```

### 3. Middleware Tenant Belirleme (Zaten Var!)
```python
# apps/core/middleware.py (Zaten kodunuzda var)
host = request.get_host()  # firma1.fieldops.com
subdomain = host.split('.')[0]  # firma1
tenant = Tenant.objects.get(slug=subdomain)  # Otomatik tenant bulunur
```

### 4. Gelen İstekler
```
admin.fieldops.com     → request.tenant = None (Admin panel)
firma1.fieldops.com    → request.tenant = Tenant(slug='firma1')
firma2.fieldops.com    → request.tenant = Tenant(slug='firma2')
```

---

## Avantajlar

### ✅ Kod Tek Kalır
- **1 güncelleme = Tüm firmalara uygulanır**
- Kod tek yerde, bakım kolay
- Hata düzeltmeleri tüm firmalara yansır

### ✅ Session İzolasyonu
- Her subdomain kendi session cookie'sini kullanır
- `firma1.fieldops.com` cookie'si `firma2.fieldops.com`'da çalışmaz
- Tam güvenlik

### ✅ Performans
- Her subdomain için ayrı cache
- Database query'ler optimize edilebilir
- CDN yapılandırması kolay

### ✅ Ölçeklenebilirlik
- İhtiyaç halinde farklı firmalar farklı sunuculara taşınabilir
- Load balancing kolay

---

## Güncelleme Süreci

### Mevcut Sistem (Session Bazlı)
```
1. Kod güncelle
2. Deploy et
3. ✅ Tüm firmalar otomatik güncellenir
```

### Subdomain Sistemi
```
1. Kod güncelle (TEK SEFER)
2. Deploy et (TEK SEFER)
3. ✅ Tüm subdomain'ler otomatik güncellenir
```

**SONUÇ:** Güncelleme süreci AYNI! Tek fark: Subdomain'ler session yerine URL bazlı çalışır.

---

## Yapılması Gerekenler

### 1. DNS Yapılandırması (Bir Kere)
```
*.fieldops.com  → A kaydı → Sunucu IP adresi
```

### 2. Django Settings (Küçük Değişiklik)
```python
# config/settings.py
ALLOWED_HOSTS = [
    'fieldops.com',
    '*.fieldops.com',  # Wildcard subdomain
    'admin.fieldops.com',
    'firma1.fieldops.com',
    # ... diğer subdomain'ler
]

# Session cookie domain (isteğe bağlı)
SESSION_COOKIE_DOMAIN = '.fieldops.com'  # Tüm subdomain'lerde çalışır
# VEYA
SESSION_COOKIE_DOMAIN = None  # Her subdomain kendi session'ını kullanır (DAHA GÜVENLİ)
```

### 3. Middleware (Zaten Hazır!)
```python
# apps/core/middleware.py
# Kod zaten subdomain kontrolü yapıyor, sadece test edilmeli
```

### 4. Tenant Slug Kontrolü
```python
# Her tenant'ın slug'ı subdomain ile eşleşmeli
Tenant.objects.create(
    name="Firma 1",
    slug="firma1",  # ← Bu subdomain ile eşleşmeli
    ...
)
```

---

## Örnek Senaryo

### Senaryo: 10 Firma Var, Güncelleme Yapıyorsunuz

#### Mevcut Sistem (Session Bazlı)
```
1. Kod güncelle
2. python manage.py migrate
3. python manage.py collectstatic
4. System restart
5. ✅ Tüm firmalar güncellenir
```

#### Subdomain Sistemi
```
1. Kod güncelle (AYNI)
2. python manage.py migrate (AYNI)
3. python manage.py collectstatic (AYNI)
4. System restart (AYNI)
5. ✅ Tüm subdomain'ler güncellenir
```

**FARK YOK!** Her iki yaklaşımda da güncelleme tek seferde yapılır.

---

## Ne Zaman Geçiş Yapılmalı?

### Şimdi Kalın (Session Bazlı) Eğer:
- ✅ Firma sayısı az (< 10 firma)
- ✅ Güvenlik riski düşük
- ✅ Performans sorunu yok
- ✅ Hızlı geliştirme öncelikli

### Subdomain'e Geçin Eğer:
- ⚠️ Firma sayısı artıyor (> 10 firma)
- ⚠️ Güvenlik önemli (finans, sağlık, vb.)
- ⚠️ Performans sorunları başladı
- ⚠️ Farklı firmalar farklı özelleştirmeler istiyor

---

## Sonuç

**Subdomain yaklaşımı = Tek kod, çoklu URL routing**

- Kod tek kalır ✅
- Güncelleme tek seferde yapılır ✅
- Session izolasyonu artar ✅
- Güvenlik artar ✅
- Performans artar ✅

**Tek yapmanız gereken:** DNS wildcard kaydı ve küçük settings güncellemesi. Kod aynı kalır!









