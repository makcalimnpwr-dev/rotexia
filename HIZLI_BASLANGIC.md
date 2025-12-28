# ⚡ Rotexia - Hızlı Başlangıç (Canlıya Alma)

## 🎯 3 Adımda Canlıya Alın!

### 1️⃣ GitHub'a Yükleyin

```bash
# Proje klasöründe:
git init
git add .
git commit -m "Rotexia - İlk deployment"
git branch -M main
git remote add origin https://github.com/KULLANICI_ADI/rotexia.git
git push -u origin main
```

### 2️⃣ Render.com'da Deploy Edin (Önerilen)

1. [render.com](https://render.com) → GitHub ile giriş
2. **PostgreSQL oluştur:** "New +" → "PostgreSQL" → Free plan
3. **Web Service oluştur:** "New +" → "Web Service" → GitHub repo seç
4. **Ayarlar:**
   - Build Command: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - Start Command: `gunicorn config.wsgi:application`
5. **Environment Variables ekle:**
   ```
   SECRET_KEY=buraya-güvenli-key (Python'da oluşturun)
   DEBUG=False
   ALLOWED_HOSTS=your-app.onrender.com
   DATABASE_URL=postgresql://... (PostgreSQL'den kopyala)
   ```
6. **Deploy!** 🚀

### 3️⃣ İlk Kurulum

Deploy tamamlandıktan sonra Shell'de:

```bash
python manage.py migrate
python manage.py createsuperuser
```

**Tamamlandı!** ✅ Site canlıda: `https://your-app.onrender.com`

---

## 🔄 Güncelleme Nasıl Yapılır?

**Çok basit!** Kod değiştir → GitHub'a push et → Otomatik deploy olur!

```bash
git add .
git commit -m "Yeni özellik"
git push origin main
```

2-5 dakika içinde site güncellenir! 🎉

---

## 📚 Detaylı Rehberler

- **Tam Deployment Rehberi:** `DEPLOYMENT_REHBERI.md`
- **Güncelleme Rehberi:** `GUNCELLEME_REHBERI.md`

---

## 🆘 Hızlı Yardım

**Site çalışmıyor?**
- Logs kontrol edin (Render Dashboard → Logs)
- Environment variables doğru mu?
- Migration çalıştırdınız mı?

**Static files görünmüyor?**
```bash
# Shell'de:
python manage.py collectstatic --noinput
```

---

**Başarılar!** 🚀

