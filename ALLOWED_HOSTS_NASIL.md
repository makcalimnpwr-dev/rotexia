# 🌐 ALLOWED_HOSTS - Hostname Nereden Alınır?

ALLOWED_HOSTS için hostname (domain) bilgisini nereden alacağınız:

---

## 🔍 YÖNTEM 1: Web Service Oluşturduktan Sonra (Önerilen)

**Web Service'i oluşturduktan sonra:**

1. Render Dashboard'a gidin
2. Oluşturduğunuz Web Service'e tıklayın
3. Üst kısımda site URL'inizi göreceksiniz
4. URL şu formatta olacak: `https://rotexia.onrender.com`
5. **Sadece domain kısmını kullanın:** `rotexia.onrender.com` (https:// olmadan)

**Örnek:**
- URL: `https://rotexia.onrender.com`
- ALLOWED_HOSTS için: `rotexia.onrender.com`

---

## 🔍 YÖNTEM 2: Şimdilik Genel Format Kullan (Şimdi Yapabilirsiniz)

**Web Service henüz oluşturulmadıysa:**

Render.com otomatik olarak şu formatı kullanır:
- `your-service-name.onrender.com`

**Eğer Web Service isminiz "rotexia" ise:**
- ALLOWED_HOSTS: `rotexia.onrender.com`

**Eğer farklı bir isim verdinizse:**
- ALLOWED_HOSTS: `your-service-name.onrender.com`

---

## 📝 ADIM ADIM:

### Şu Anda Yapabileceğiniz (Önerilen):

**ALLOWED_HOSTS variable eklerken:**

1. **NAME:** `ALLOWED_HOSTS`
2. **VALUE:** `rotexia.onrender.com` (veya Web Service'e verdiğiniz isim)

**Bu şekilde ekleyebilirsiniz!** Web Service oluşturulduktan sonra eğer domain farklıysa, environment variable'ı düzenleyebilirsiniz.

---

### Web Service Oluşturduktan Sonra Kontrol:

1. Render Dashboard → Web Service'inize gidin
2. Üstte site URL'ini görün
3. Eğer farklıysa:
   - Environment variables sekmesine gidin
   - ALLOWED_HOSTS'i düzenleyin
   - Doğru domain'i yazın

---

## ✅ ÖZET:

**Şu an yapabilirsiniz:**
- ALLOWED_HOSTS: `rotexia.onrender.com` yazın
- (Web Service'e verdiğiniz isim ile .onrender.com)

**Eğer farklı bir domain verilirse:**
- Web Service oluşturulduktan sonra düzenleyebilirsiniz

---

## 🎯 ŞU AN YAPMANIZ GEREKEN:

**ALLOWED_HOSTS variable'ı eklerken:**

- **NAME:** `ALLOWED_HOSTS`
- **VALUE:** `rotexia.onrender.com`

**Bu şekilde ekleyin!** Render genellikle bu formatı kullanır.

---

## 🆘 SORUN MU VAR?

**Web Service'i henüz oluşturmadınız:**
→ `rotexia.onrender.com` yazın (veya verdiğiniz isim)

**Web Service oluşturuldu ama domain farklı:**
→ Environment variables'dan ALLOWED_HOSTS'i düzenleyin

**Domain'i bulamıyorum:**
→ Render Dashboard → Web Service → Üstte URL görünür

---

**Başarılar!** 🚀



