# 📤 GitHub'a Yükleme - Detaylı Açıklama

## ❓ SORU 1: Komutları Nereye Yazacağım?

### PowerShell/Terminal Penceresi Açma:

**Yöntem 1: Windows Explorer'dan (Kolay)**
1. Windows Explorer'ı açın (Dosya Gezgini)
2. Şu klasöre gidin: `C:\Users\musta\Desktop\field_ops_project1`
3. Klasör içinde **boş bir yere sağ tıklayın**
4. **"Open in Terminal"** veya **"Open PowerShell window here"** seçin
5. Siyah/beyaz bir pencere açılacak - İŞTE BURAYA YAZACAKSINIZ!

**Yöntem 2: PowerShell'i Manuel Açma**
1. Windows tuşuna basın
2. "PowerShell" yazın
3. "Windows PowerShell" açın
4. Şu komutu yazın:
   ```powershell
   cd C:\Users\musta\Desktop\field_ops_project1
   ```
5. Enter'a basın

**Komutları yazdıktan sonra her zaman ENTER'a basın!**

---

## ❓ SORU 2: Username ve Email Nereden Alacağım?

### Username ve Email Açıklaması:

**Username (Kullanıcı Adı):**
- Bu sizin **GitHub kullanıcı adınız** değil!
- Bu sadece **Git'in kimlik bilgisi** (commit'lerde görünecek)
- İstediğiniz herhangi bir isim yazabilirsiniz
- Örnek: `"Mustafa"`, `"Mustafa Yılmaz"`, `"makcalimnpwr-dev"` (GitHub kullanıcı adınız)

**Email:**
- Bu sizin **GitHub email'iniz** değil!
- Bu sadece **Git'in kimlik bilgisi** (commit'lerde görünecek)
- İstediğiniz herhangi bir email yazabilirsiniz
- Örnek: `"mustafa@example.com"`, `"your-email@gmail.com"`

**⚠️ ÖNEMLİ:** 
- Bu bilgiler sadece Git commit'lerinde görünür
- GitHub'a giriş yapmak için kullanılmaz
- İstediğiniz herhangi bir isim/email yazabilirsiniz

---

## 📝 ADIM ADIM ÖRNEK:

### 1. PowerShell'i Açın (yukarıdaki yöntemlerden biriyle)

### 2. Proje Klasöründe Olduğunuzdan Emin Olun:

PowerShell'de şunu yazın:
```powershell
cd C:\Users\musta\Desktop\field_ops_project1
```
Enter'a basın.

### 3. Git Komutlarını Yazın:

**Komut 1: Git'i başlat**
```bash
git init
```
Enter'a basın. "Initialized empty Git repository..." mesajı görünmeli.

**Komut 2: İsim ve Email ayarla (SADECE BİR KEZ)**
```bash
git config --global user.name "Mustafa"
```
Enter'a basın. (İstediğiniz ismi yazın)

```bash
git config --global user.email "mustafa@example.com"
```
Enter'a basın. (İstediğiniz email'i yazın)

**Komut 3: Dosyaları ekle**
```bash
git add .
```
Enter'a basın. (Hiçbir mesaj görünmeyebilir, normal)

**Komut 4: İlk kayıt**
```bash
git commit -m "Rotexia - İlk yükleme"
```
Enter'a basın. "X files changed..." mesajı görünmeli.

**Komut 5: GitHub'ı bağla**
```bash
git remote add origin https://github.com/makcalimnpwr-dev/rotexia.git
```
Enter'a basın. (Hiçbir mesaj görünmeyebilir, normal)

**Komut 6: Branch ayarla**
```bash
git branch -M main
```
Enter'a basın. (Hiçbir mesaj görünmeyebilir, normal)

**Komut 7: GitHub'a gönder**
```bash
git push -u origin main
```
Enter'a basın. 

**Bu komutta GitHub kullanıcı adı ve şifre isteyecek:**
- Username: `makcalimnpwr-dev` (GitHub kullanıcı adınız)
- Password: GitHub şifreniz VEYA Personal Access Token

---

## 🖼️ GÖRSEL ÖRNEK:

PowerShell penceresi şöyle görünecek:

```
PS C:\Users\musta\Desktop\field_ops_project1> git init
Initialized empty Git repository in C:/Users/musta/Desktop/field_ops_project1/.git/

PS C:\Users\musta\Desktop\field_ops_project1> git config --global user.name "Mustafa"

PS C:\Users\musta\Desktop\field_ops_project1> git config --global user.email "mustafa@example.com"

PS C:\Users\musta\Desktop\field_ops_project1> git add .

PS C:\Users\musta\Desktop\field_ops_project1> git commit -m "Rotexia - İlk yükleme"
[main (root-commit) abc123] Rotexia - İlk yükleme
 150 files changed, 5000 insertions(+)

PS C:\Users\musta\Desktop\field_ops_project1> git remote add origin https://github.com/makcalimnpwr-dev/rotexia.git

PS C:\Users\musta\Desktop\field_ops_project1> git branch -M main

PS C:\Users\musta\Desktop\field_ops_project1> git push -u origin main
Username for 'https://github.com': makcalimnpwr-dev
Password for 'https://makcalimnpwr-dev@github.com': [şifre yazılacak, görünmeyecek]
Enumerating objects: 150, done.
Counting objects: 100% (150/150), done.
Writing objects: 100% (150/150), done.
To https://github.com/makcalimnpwr-dev/rotexia.git
 * [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.

PS C:\Users\musta\Desktop\field_ops_project1>
```

---

## ✅ BAŞARILI OLDUĞUNDA:

1. GitHub sayfasını yenileyin (F5)
2. Tüm dosyalarınızı görebilmelisiniz!

---

## 🆘 SORUN MU VAR?

**"git: command not found"**
→ Git yüklü değil. Önce Git'i yükleyin: https://git-scm.com/download/win

**"fatal: not a git repository"**
→ Önce `git init` çalıştırın

**"remote origin already exists"**
→ Şunu çalıştırın:
```bash
git remote remove origin
git remote add origin https://github.com/makcalimnpwr-dev/rotexia.git
```

**"Authentication failed"**
→ Personal Access Token kullanın (şifre yerine)

---

**Başarılar!** 🚀














