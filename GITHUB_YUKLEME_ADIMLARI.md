# 📤 GitHub'a Yükleme - Adım Adım

GitHub repository sayfasındasınız. Şimdi projenizi yüklemek için şu adımları izleyin:

---

## 🔧 ADIM 1: Git Yükleme (Eğer yüklü değilse)

1. **Git'i indirin:**
   - [git-scm.com/download/win](https://git-scm.com/download/win) adresine gidin
   - "Download for Windows" tıklayın
   - İndirilen .exe dosyasını çalıştırın
   - Kurulum sırasında varsayılan ayarları kabul edin (Next, Next, Install)

2. **Kurulum sonrası:**
   - PowerShell/Terminal'i kapatıp yeniden açın
   - Veya bilgisayarı yeniden başlatın

3. **Git'in yüklü olduğunu kontrol edin:**
   ```bash
   git --version
   ```
   Versiyon numarası görünmeli (örn: `git version 2.42.0`)

---

## 📤 ADIM 2: Projeyi GitHub'a Yükleme

GitHub sayfasında gördüğünüz komutları kullanacağız. **PowerShell'i proje klasörünüzde açın:**

### Proje Klasörüne Gitme:

1. **Windows Explorer'da:**
   - `C:\Users\musta\Desktop\field_ops_project1` klasörüne gidin
   - Klasör içinde sağ tık → "Open in Terminal" veya "Open PowerShell window here"

2. **Veya PowerShell'de:**
   ```powershell
   cd C:\Users\musta\Desktop\field_ops_project1
   ```

### Komutları Çalıştırma:

GitHub sayfasında gördüğünüz komutları sırayla çalıştırın:

**1. Git başlat (eğer başlatılmadıysa):**
```bash
git init
```

**2. Remote repository ekle:**
```bash
git remote add origin https://github.com/makcalimnpwr-dev/rotexia.git
```

**3. Tüm dosyaları ekle:**
```bash
git add .
```

**4. İlk commit:**
```bash
git commit -m "Rotexia - İlk deployment"
```

**5. Branch'i main yap:**
```bash
git branch -M main
```

**6. GitHub'a gönder:**
```bash
git push -u origin main
```

---

## ⚠️ İLK KEZ KULLANIMDA:

Eğer ilk kez Git kullanıyorsanız, şu komutları da çalıştırmanız gerekebilir:

```bash
git config --global user.name "Adınız Soyadınız"
git config --global user.email "email@example.com"
```

---

## 🔐 GitHub Kimlik Doğrulama:

`git push` komutunu çalıştırdığınızda GitHub kullanıcı adı ve şifre isteyebilir:

1. **Kullanıcı adı:** GitHub kullanıcı adınız (`makcalimnpwr-dev`)
2. **Şifre:** GitHub şifreniz (veya Personal Access Token)

**Eğer şifre çalışmazsa:**
- GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
- "Generate new token" → "repo" seçin → Token oluşturun
- Bu token'ı şifre yerine kullanın

---

## ✅ BAŞARILI OLDUĞUNDA:

GitHub sayfasını yenileyin (F5). Artık tüm dosyalarınızı görebilmelisiniz!

- ✅ Dosyalar görünüyor mu?
- ✅ README.md var mı?
- ✅ Tüm klasörler yüklendi mi?

---

## 🚀 SONRAKI ADIM:

GitHub'a yükleme tamamlandıktan sonra:

1. **Render.com'a gidin** (bir sonraki adım)
2. **Repository'nizi bağlayın**
3. **Deploy edin!**

Detaylı rehber: `RENDER_ADIM_ADIM.md` dosyasına bakın.

---

## 🆘 SORUN MU VAR?

**"git: command not found" hatası:**
→ Git yüklü değil, Adım 1'i yapın

**"remote origin already exists" hatası:**
→ Şu komutu çalıştırın:
```bash
git remote remove origin
git remote add origin https://github.com/makcalimnpwr-dev/rotexia.git
```

**"Authentication failed" hatası:**
→ Personal Access Token kullanın (yukarıda anlatıldı)

**"Nothing to commit" mesajı:**
→ Normal, zaten commit edilmiş. Direkt `git push -u origin main` çalıştırın

---

**Başarılar!** 🎉



