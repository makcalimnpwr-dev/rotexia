# 📤 GitHub'a Proje Yükleme - Kolay Rehber

## 🔧 ADIM 1: Git Yükleme (İLK KEZ İSE)

Git yüklü değil. Önce Git'i yükleyin:

1. **Git'i İndirin:**
   - Bu linke gidin: https://git-scm.com/download/win
   - "Download for Windows" butonuna tıklayın
   - İndirilen dosyayı çalıştırın (Git-2.xx.x-64-bit.exe)

2. **Kurulum:**
   - Kurulum sırasında **tüm adımlarda "Next" veya "Install"** tıklayın
   - Varsayılan ayarları kabul edin
   - Kurulum bitince "Finish" tıklayın

3. **PowerShell'i Yeniden Açın:**
   - Mevcut PowerShell penceresini kapatın
   - Yeni bir PowerShell penceresi açın
   - Proje klasörüne gidin:
     ```powershell
     cd C:\Users\musta\Desktop\field_ops_project1
     ```

4. **Git Yüklü mü Kontrol:**
   ```bash
   git --version
   ```
   Versiyon numarası görünmeli (örn: `git version 2.42.0`)

---

## 📤 ADIM 2: GitHub'a Yükleme

Git yüklendikten sonra, şu komutları **sırayla** çalıştırın:

### 1. Git'i Başlat:
```bash
git init
```

### 2. İlk Kez Git Kullanıyorsanız (Sadece bir kez):
```bash
git config --global user.name "Adınız"
git config --global user.email "email@example.com"
```
*(Adınız ve email'inizi yazın)*

### 3. Tüm Dosyaları Ekle:
```bash
git add .
```

### 4. İlk Kayıt (Commit):
```bash
git commit -m "Rotexia - İlk yükleme"
```

### 5. GitHub Repository'yi Bağla:
```bash
git remote add origin https://github.com/makcalimnpwr-dev/rotexia.git
```

### 6. Ana Branch'i Ayarla:
```bash
git branch -M main
```

### 7. GitHub'a Gönder:
```bash
git push -u origin main
```

---

## 🔐 ADIM 3: GitHub Girişi

`git push` komutunu çalıştırdığınızda GitHub kullanıcı adı ve şifre isteyecek:

1. **Username:** `makcalimnpwr-dev` (GitHub kullanıcı adınız)
2. **Password:** GitHub şifreniz

**⚠️ ÖNEMLİ:** Eğer şifre çalışmazsa, **Personal Access Token** kullanmanız gerekir:

### Personal Access Token Oluşturma:

1. GitHub'a gidin ve giriş yapın
2. Sağ üstte profil resminize tıklayın → **Settings**
3. Sol menüden **Developer settings**
4. **Personal access tokens** → **Tokens (classic)**
5. **Generate new token** → **Generate new token (classic)**
6. **Note:** `Rotexia Deployment` yazın
7. **Expiration:** 90 days (veya istediğiniz süre)
8. **Scopes:** Sadece **`repo`** seçin (tüm alt seçenekler otomatik seçilir)
9. En alta scroll yapın → **Generate token**
10. **Token'ı kopyalayın** (bir daha gösterilmeyecek!)
11. Bu token'ı şifre yerine kullanın

---

## ✅ BAŞARILI OLDUĞUNDA:

1. GitHub sayfasını yenileyin (F5)
2. Artık tüm dosyalarınızı görebilmelisiniz:
   - ✅ `apps/` klasörü
   - ✅ `config/` klasörü
   - ✅ `templates/` klasörü
   - ✅ `static/` klasörü
   - ✅ `requirements.txt`
   - ✅ `manage.py`
   - Ve diğer tüm dosyalar

---

## 🆘 SORUN GİDERME

### "git: command not found"
→ Git yüklü değil, Adım 1'i yapın

### "remote origin already exists"
→ Şu komutu çalıştırın:
```bash
git remote remove origin
git remote add origin https://github.com/makcalimnpwr-dev/rotexia.git
```

### "Authentication failed"
→ Personal Access Token kullanın (yukarıda anlatıldı)

### "Nothing to commit, working tree clean"
→ Normal, zaten commit edilmiş. Direkt `git push -u origin main` çalıştırın

### "fatal: not a git repository"
→ Önce `git init` çalıştırın

---

## 🎉 TAMAMLANDI!

GitHub'a yükleme başarılı olduğunda:
- ✅ Tüm dosyalar GitHub'da
- ✅ Sonraki adım: Render.com'a deploy etmek
- ✅ Detaylı rehber: `RENDER_ADIM_ADIM.md`

**Başarılar!** 🚀














