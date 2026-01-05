# Yeni Firma Ekleme Rehberi

## 📋 Adım Adım Süreç

### 1. Admin Panelinden Firma Ekleme

1. **Admin paneline giriş yapın** (`admin.localhost:8000` veya `admin.fieldops.com`)
2. **"Firma Ekle"** butonuna tıklayın
3. **Formu doldurun:**
   - **Firma Adı** (Zorunlu): Örn: "Yeni Firma"
   - **Subdomain** (Opsiyonel): Boş bırakılırsa otomatik oluşturulur
   - **E-posta**: İletişim e-postası
   - **Tema Rengi**: Firma için özel renk

4. **"Firma Ekle"** butonuna tıklayın

### 2. Otomatik İşlemler

✅ **Slug Oluşturma:**
- Firma adı otomatik olarak subdomain'e dönüştürülür
- Türkçe karakterler çevrilir: `ı→i`, `ş→s`, `ğ→g`, vb.
- Boşluklar tire (`-`) ile değiştirilir
- Özel karakterler temizlenir

✅ **Benzersizlik Kontrolü:**
- Aynı slug varsa otomatik numara eklenir: `yeni-firma`, `yeni-firma-1`, `yeni-firma-2`

✅ **Varsayılan Plan:**
- Yeni firmaya otomatik "Ücretsiz Plan" atanır

### 3. Sonuç

Başarılı ekleme sonrası:
- ✅ Firma oluşturuldu mesajı gösterilir
- ✅ Subdomain bilgisi gösterilir: `firma-adi.fieldops.com`

## 🌐 Subdomain Erişimi

### Development (Localhost)

1. **Hosts dosyasını güncelleyin:**
   ```
   C:\Windows\System32\drivers\etc\hosts
   ```
   
   Yeni satır ekleyin:
   ```
   127.0.0.1    yeni-firma.localhost
   ```

2. **Tarayıcıda açın:**
   ```
   http://yeni-firma.localhost:8000
   ```

### Production

1. **DNS kontrolü:**
   - Wildcard DNS kaydı (`*.fieldops.com`) varsa otomatik çalışır
   - Yoksa manuel DNS kaydı ekleyin:
     ```
     yeni-firma.fieldops.com  A  [SUNUCU_IP]
     ```

2. **Tarayıcıda açın:**
   ```
   https://yeni-firma.fieldops.com
   ```

## 📝 Örnek Senaryolar

### Senaryo 1: Basit Firma Adı
- **Firma Adı:** `Pastel`
- **Otomatik Slug:** `pastel`
- **Subdomain:** `pastel.fieldops.com`

### Senaryo 2: Türkçe Karakter İçeren Ad
- **Firma Adı:** `Şirket Ürünleri`
- **Otomatik Slug:** `sirket-urunleri`
- **Subdomain:** `sirket-urunleri.fieldops.com`

### Senaryo 3: Özel Karakter İçeren Ad
- **Firma Adı:** `ABC & Co. Ltd.`
- **Otomatik Slug:** `abc-co-ltd`
- **Subdomain:** `abc-co-ltd.fieldops.com`

### Senaryo 4: Manuel Slug
- **Firma Adı:** `Çok Uzun Firma Adı A.Ş.`
- **Manuel Slug:** `cufa` (kullanıcı girdi)
- **Subdomain:** `cufa.fieldops.com`

### Senaryo 5: Çakışan Slug
- **Firma 1:** `Pastel` → Slug: `pastel`
- **Firma 2:** `Pastel` → Slug: `pastel-1` (otomatik numara eklendi)

## ⚠️ Önemli Notlar

1. **Slug Kuralları:**
   - Sadece küçük harf, rakam ve tire (`-`)
   - Türkçe karakter yok
   - Boşluk yok
   - Özel karakter yok (`@`, `&`, `.`, vb.)

2. **Slug Değiştirme:**
   - Slug oluşturulduktan sonra değiştirilebilir (Edit Tenant sayfasından)
   - Ancak subdomain değişeceği için kullanıcıların yeniden giriş yapması gerekebilir

3. **DNS Güncellemesi:**
   - Development'ta: Hosts dosyasını manuel güncelleyin
   - Production'da: Wildcard DNS varsa otomatik, yoksa manuel kayıt gerekir

## 🔧 Troubleshooting

### Slug oluşturulamadı hatası
- Firma adında sadece özel karakter varsa slug boş olabilir
- **Çözüm:** Manuel slug girin

### Subdomain çalışmıyor
- **Development:** Hosts dosyasını kontrol edin
- **Production:** DNS kayıtlarını kontrol edin
- Tarayıcı cache'ini temizleyin

### Çift firma oluşturuldu
- Formu iki kez gönderilmiş olabilir
- **Çözüm:** İkinci firmayı silin veya slug'ını değiştirin





