# 🔄 Rotexia - Güncelleme Rehberi

Bu rehber, canlıya aldığınız Rotexia projesini nasıl güncelleyeceğinizi açıklar.

## 📋 İçindekiler

1. [Hızlı Güncelleme (Otomatik)](#hızlı-güncelleme-otomatik) ⭐ EN KOLAY
2. [Manuel Güncelleme](#manuel-güncelleme)
3. [Migration Güncellemeleri](#migration-güncellemeleri)
4. [Static Files Güncelleme](#static-files-güncelleme)
5. [Veritabanı Yedekleme](#veritabanı-yedekleme)

---

## 🚀 Hızlı Güncelleme (Otomatik) ⭐

### Render.com için:

1. **Kodunuzu değiştirin** (yerel bilgisayarınızda)
2. **GitHub'a gönderin:**
   ```bash
   git add .
   git commit -m "Yeni özellik: [açıklama]"
   git push origin main
   ```
3. **Render otomatik olarak deploy eder!** ✅
   - Render Dashboard'da deployment durumunu görebilirsiniz
   - Genellikle 2-5 dakika sürer

### Railway.app için:

1. **Kodunuzu değiştirin**
2. **GitHub'a gönderin:**
   ```bash
   git add .
   git commit -m "Yeni özellik: [açıklama]"
   git push origin main
   ```
3. **Railway otomatik olarak deploy eder!** ✅

---

## 🔧 Manuel Güncelleme

### Render.com:

1. Render Dashboard'a gidin
2. Servisinize tıklayın
3. "Manual Deploy" → "Deploy latest commit" seçin
4. Deployment tamamlanana kadar bekleyin

### Railway.app:

1. Railway Dashboard'a gidin
2. Projenize tıklayın
3. "Deployments" sekmesine gidin
4. "Redeploy" butonuna tıklayın

---

## 📦 Migration Güncellemeleri

Eğer veritabanı yapısında değişiklik yaptıysanız (yeni model, yeni alan vb.):

### Otomatik (Önerilen):

Migration'lar genellikle otomatik çalışır. Eğer çalışmazsa:

### Manuel:

**Render.com:**
1. Servisinizde "Shell" sekmesine gidin
2. Şu komutu çalıştırın:
   ```bash
   python manage.py migrate
   ```

**Railway.app:**
1. "Deployments" → "View Logs" → "Open Shell"
2. Şu komutu çalıştırın:
   ```bash
   python manage.py migrate
   ```

---

## 🎨 Static Files Güncelleme

CSS, JavaScript veya görsel dosyalarını değiştirdiyseniz:

### Otomatik:

`build.sh` scripti otomatik olarak static files'ı toplar. Eğer sorun olursa:

### Manuel:

**Render.com Shell:**
```bash
python manage.py collectstatic --noinput
```

**Railway.app Shell:**
```bash
python manage.py collectstatic --noinput
```

---

## 💾 Veritabanı Yedekleme

Güncelleme öncesi yedek almanız önerilir:

### Render.com:

1. "Shell" sekmesine gidin
2. Şu komutu çalıştırın:
   ```bash
   pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
   ```
3. Dosyayı indirin (Render'ın file system'inde saklanır)

### Railway.app:

1. PostgreSQL servisinize gidin
2. "Data" sekmesinde "Download" butonuna tıklayın
3. Veya Shell'de:
   ```bash
   pg_dump $DATABASE_URL > backup.sql
   ```

---

## ⚠️ Önemli Notlar

### 1. Environment Variables

Eğer yeni environment variable eklediyseniz:
- Render: "Environment" sekmesinde ekleyin
- Railway: "Variables" sekmesinde ekleyin

### 2. DEBUG Modu

**ASLA production'da DEBUG=True yapmayın!**
- Güvenlik riski oluşturur
- Performans sorunları yaratır

### 3. Test Etme

Güncelleme sonrası mutlaka test edin:
- [ ] Giriş yapabiliyor musunuz?
- [ ] Ana sayfalar çalışıyor mu?
- [ ] Yeni özellikler çalışıyor mu?
- [ ] Admin paneli çalışıyor mu?

### 4. Rollback (Geri Alma)

Eğer bir sorun olursa:

**Render.com:**
1. "Deployments" sekmesine gidin
2. Önceki başarılı deployment'ı bulun
3. "Redeploy" butonuna tıklayın

**Railway.app:**
1. "Deployments" sekmesine gidin
2. Önceki commit'i seçin
3. "Redeploy" butonuna tıklayın

---

## 📝 Güncelleme Kontrol Listesi

Güncelleme yapmadan önce:

- [ ] Kod değişikliklerini test ettiniz mi? (yerel)
- [ ] Migration'lar hazır mı? (`python manage.py makemigrations`)
- [ ] Static files değişti mi? (CSS, JS, görseller)
- [ ] Yeni environment variable var mı?
- [ ] Veritabanı yedeği aldınız mı?

Güncelleme sonrası:

- [ ] Site açılıyor mu?
- [ ] Giriş yapabiliyor musunuz?
- [ ] Yeni özellikler çalışıyor mu?
- [ ] Hata logları temiz mi?

---

## 🆘 Sorun Giderme

### Deployment Başarısız Oldu

1. **Logs'ları kontrol edin:**
   - Render: "Logs" sekmesi
   - Railway: "Deployments" → "View Logs"

2. **Yaygın hatalar:**
   - Migration hatası → Shell'de `python manage.py migrate` çalıştırın
   - Static files hatası → Shell'de `python manage.py collectstatic --noinput` çalıştırın
   - Import hatası → `requirements.txt` güncel mi kontrol edin

### Site Çalışmıyor

1. **Environment variables kontrol edin**
2. **DEBUG=False olduğundan emin olun**
3. **ALLOWED_HOSTS doğru mu?**
4. **Logs'ları kontrol edin**

---

## 🎉 Başarılı Güncelleme!

Güncelleme tamamlandıktan sonra:
1. Siteyi test edin
2. Müşterilere bildirin
3. Yeni özellikleri gösterin

**İyi çalışmalar!** 🚀

