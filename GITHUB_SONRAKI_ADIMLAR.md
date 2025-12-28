# ✅ Git Init Başarılı! - Sonraki Adımlar

`git init` komutu başarıyla çalıştı! Şimdi sıradaki komutları çalıştırın:

---

## 📝 SIRADAKI KOMUTLAR:

### 1. İsim ve Email Ayarla (Sadece bir kez, ilk kez kullanıyorsanız):

```bash
git config --global user.name "Mustafa"
```
Enter'a basın. (İstediğiniz ismi yazabilirsiniz: "Mustafa", "Mustafa Yılmaz", vb.)

```bash
git config --global user.email "mustafa@example.com"
```
Enter'a basın. (İstediğiniz email'i yazabilirsiniz: "mustafa@gmail.com", vb.)

**Not:** Bu bilgiler sadece Git commit'lerinde görünür, GitHub'a giriş için değil.

---

### 2. Tüm Dosyaları Ekle:

```bash
git add .
```
Enter'a basın. (Hiçbir mesaj görünmeyebilir, normal)

---

### 3. İlk Kayıt (Commit):

```bash
git commit -m "Rotexia - İlk yükleme"
```
Enter'a basın. 

**Beklenen çıktı:**
```
[main (root-commit) abc123] Rotexia - İlk yükleme
 150 files changed, 5000 insertions(+)
```
(Bu sayılar farklı olabilir, normal)

---

### 4. GitHub Repository'yi Bağla:

```bash
git remote add origin https://github.com/makcalimnpwr-dev/rotexia.git
```
Enter'a basın. (Hiçbir mesaj görünmeyebilir, normal)

---

### 5. Ana Branch'i Ayarla:

```bash
git branch -M main
```
Enter'a basın. (Hiçbir mesaj görünmeyebilir, normal)

---

### 6. GitHub'a Gönder (EN ÖNEMLİSİ):

```bash
git push -u origin main
```
Enter'a basın.

**Bu komutta GitHub kullanıcı adı ve şifre isteyecek:**

1. **Username:** `makcalimnpwr-dev` yazın
2. **Password:** GitHub şifrenizi yazın (görünmeyecek, normal)

**⚠️ Eğer şifre çalışmazsa:**
- Personal Access Token kullanmanız gerekir
- GitHub → Settings → Developer settings → Personal access tokens
- "Generate new token (classic)" → `repo` seçin → Token oluşturun
- Bu token'ı şifre yerine kullanın

---

## ✅ BAŞARILI OLDUĞUNDA:

Şöyle bir mesaj göreceksiniz:
```
Enumerating objects: 150, done.
Counting objects: 100% (150/150), done.
Writing objects: 100% (150/150), done.
To https://github.com/makcalimnpwr-dev/rotexia.git
 * [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

**Sonra:**
1. GitHub sayfasını yenileyin (F5)
2. Tüm dosyalarınızı görebilmelisiniz! 🎉

---

## 🆘 SORUN MU VAR?

**"remote origin already exists" hatası:**
→ Şunu çalıştırın:
```bash
git remote remove origin
git remote add origin https://github.com/makcalimnpwr-dev/rotexia.git
```

**"Authentication failed" hatası:**
→ Personal Access Token kullanın (yukarıda anlatıldı)

**"Nothing to commit" mesajı:**
→ Normal, zaten commit edilmiş. Direkt `git push -u origin main` çalıştırın

---

**Devam edin!** 🚀

