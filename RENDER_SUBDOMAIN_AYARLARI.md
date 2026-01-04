# 🚀 Render'da Subdomain Yapılandırması

## ✅ Mevcut Durum
- Render'da zaten bir web service var
- Sistem subdomain desteği için hazır

## 📋 Render Dashboard'da Yapılacaklar

### 1. Environment Variables Ekleme

Render Dashboard → Web Service → Environment sekmesine gidin ve şu değişkenleri ekleyin:

#### SUBDOMAIN_DOMAIN
- **Key:** `SUBDOMAIN_DOMAIN`
- **Value:** Render'ın size verdiği domain (örn: `yourapp.onrender.com`)
- **Örnek:** Eğer siteniz `rotexia.onrender.com` ise → `rotexia.onrender.com`

#### ALLOWED_HOSTS (Güncelle)
- **Key:** `ALLOWED_HOSTS`
- **Value:** `yourapp.onrender.com,*.yourapp.onrender.com`
- **Örnek:** `rotexia.onrender.com,*.rotexia.onrender.com`

#### DEBUG (Production için)
- **Key:** `DEBUG`
- **Value:** `False` (Production'da mutlaka False olmalı)

### 2. Render'da Wildcard Subdomain

**ÖNEMLİ:** Render'ın kendi domain'i (`*.onrender.com`) için wildcard subdomain otomatik çalışır!

Yani:
- `dene2.yourapp.onrender.com` → Otomatik çalışır ✅
- `pastel.yourapp.onrender.com` → Otomatik çalışır ✅
- `admin.yourapp.onrender.com` → Otomatik çalışır ✅

**Ekstra bir şey yapmanıza gerek yok!** Render otomatik olarak tüm subdomain'leri kabul eder.

### 3. Test Etme

Environment variables'ı ekledikten sonra:

1. **Render Dashboard → Web Service → Manual Deploy** (veya otomatik deploy bekleyin)
2. Deployment tamamlandıktan sonra test edin:
   ```
   https://dene2.yourapp.onrender.com
   https://pastel.yourapp.onrender.com
   https://admin.yourapp.onrender.com
   ```

### 4. SSL Sertifikası

✅ **Otomatik!** Render tüm subdomain'ler için otomatik SSL sağlar (Let's Encrypt).

## 🔧 Özel Domain Kullanıyorsanız

Eğer `fieldops.com` gibi özel bir domain kullanıyorsanız:

### DNS Ayarları (Domain sağlayıcınızda)

```
# Wildcard A kaydı
*.fieldops.com    A    [RENDER_IP_ADRESI]

# veya CNAME (Render önerir)
*.fieldops.com    CNAME    yourapp.onrender.com
```

### Render Dashboard'da

1. **Web Service → Settings → Custom Domains**
2. **Add Custom Domain** → `*.fieldops.com` ekleyin
3. Render size DNS kayıtlarını verecek, bunları domain sağlayıcınıza ekleyin

### Environment Variables

```bash
SUBDOMAIN_DOMAIN=fieldops.com
ALLOWED_HOSTS=fieldops.com,*.fieldops.com
```

## ✅ Kontrol Listesi

- [ ] `SUBDOMAIN_DOMAIN` environment variable eklendi
- [ ] `ALLOWED_HOSTS` wildcard ile güncellendi
- [ ] `DEBUG=False` (production için)
- [ ] Deployment tamamlandı
- [ ] Subdomain'ler test edildi

## 🎯 Sonuç

Render'da wildcard subdomain otomatik çalışır! Sadece environment variables'ı eklemeniz yeterli.

