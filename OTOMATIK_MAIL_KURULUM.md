# Otomatik Mail Gönderimi - Kurulum Rehberi

## 📧 Otomatik Mail Sistemi

Otomatik mail gönderimi için `send_automated_emails` management command'i periyodik olarak çalıştırılmalıdır.

## 🪟 Windows Kurulumu

### Yöntem 1: Otomatik Kurulum (Önerilen)

1. **Yönetici olarak çalıştırın:**
   - `setup_automated_email_scheduler.bat` dosyasına sağ tıklayın
   - **"Run as administrator"** seçin

2. **Script otomatik olarak:**
   - Windows Task Scheduler görevi oluşturur
   - Her 5 dakikada bir `send_automated_emails` command'ini çalıştırır

### Yöntem 2: Manuel Kurulum

1. **Windows Task Scheduler'ı açın:**
   - `Win + R` tuşlarına basın
   - `taskschd.msc` yazın ve Enter'a basın

2. **Yeni görev oluşturun:**
   - Sağ tarafta **"Create Basic Task"** veya **"Create Task"** tıklayın
   - **Name:** `FieldOps_AutomatedEmails`
   - **Description:** `FieldOps - Otomatik Mail Gönderimi`

3. **Trigger (Tetikleyici) ayarları:**
   - **Trigger:** `On a schedule`
   - **Settings:** `Daily` veya `Repeat task every: 5 minutes`
   - **Start:** İstediğiniz başlangıç saati

4. **Action (Eylem) ayarları:**
   - **Action:** `Start a program`
   - **Program/script:** `python` (veya tam yol: `C:\Python313\python.exe`)
   - **Add arguments:** `manage.py send_automated_emails`
   - **Start in:** Proje dizininizin tam yolu (örn: `C:\Users\musta\Desktop\field_ops_project1`)

5. **Ayarlar:**
   - **Run whether user is logged on or not** seçin
   - **Run with highest privileges** seçin (eğer gerekirse)

6. **Kaydedin**

### Manuel Test

Görevi manuel olarak test etmek için:

```bash
python manage.py send_automated_emails
```

veya Windows Task Scheduler'dan görevi sağ tıklayıp **"Run"** seçin.

## ⚙️ Zamanlama Ayarları

Otomatik mail ayarlarında:

- **Periyot:** Günlük / Haftalık / Aylık
- **Gönderim Saati:** Mail'in gönderileceği saat (örn: 09:00)
- **Gönderim Başlangıç Tarihi:** Mail gönderiminin başlayacağı tarih
- **Gönderim Bitiş Tarihi:** Mail gönderiminin biteceği tarih (opsiyonel)

**Önemli:** 
- Belirttiğiniz saat ve dakikada mail gönderilir (örn: 09:30 yazarsanız, tam 09:30'da gönderilir)
- Task Scheduler 5 dakikada bir çalıştığı için, 5 dakika tolerans vardır
- Örnek: 09:30 ayarlanırsa, Task Scheduler 09:30-09:35 arası çalıştığında mail gönderilir
- Eğer gönderim saati geçmişse (5 dakika sonra), o gün gönderilmez, yarın tekrar denenecek

## 🔍 Sorun Giderme

### Mail gönderilmiyor

1. **Task Scheduler görevinin çalıştığını kontrol edin:**
   - Task Scheduler'da görevi bulun
   - **"Last Run Result"** sütununa bakın (0 = başarılı)
   - **"Last Run Time"** sütununa bakın (son çalışma zamanı)

2. **Manuel test edin:**
   ```bash
   python manage.py send_automated_emails
   ```
   Hata mesajlarını kontrol edin.

3. **Zamanlama kontrolü:**
   - Otomatik mail ayarlarında **"Gönderim Saati"** doğru mu?
   - **"Gönderim Başlangıç Tarihi"** bugünden önce mi?
   - **"Gönderim Bitiş Tarihi"** (varsa) bugünden sonra mı?
   - **"Periyot"** ayarı doğru mu? (Günlük için "Her Gün", Haftalık için "Her Pazartesi", vb.)

4. **SMTP ayarlarını kontrol edin:**
   - Ayarlar → E-posta Ayarları
   - SMTP sunucu, port, kullanıcı adı, şifre doğru mu?

5. **Log dosyalarını kontrol edin:**
   - Command çıktısında hata mesajları var mı?

### Task Scheduler görevi çalışmıyor

1. **Yönetici yetkisi:**
   - Görevi yönetici olarak oluşturduğunuzdan emin olun

2. **Python yolu:**
   - Python'un PATH'te olduğundan veya tam yolun kullanıldığından emin olun

3. **Çalışma dizini:**
   - "Start in" alanında proje dizininin tam yolunu girin

4. **Görevi manuel çalıştırın:**
   - Task Scheduler'da görevi sağ tıklayıp **"Run"** seçin
   - Hata mesajlarını kontrol edin

## 📝 Notlar

- Task Scheduler görevi **her 5 dakikada bir** çalışır
- Her çalışmada, aktif otomatik mailler kontrol edilir
- Zamanlama uygun olan mailler gönderilir
- Aynı gün içinde bir mail **sadece bir kez** gönderilir

## 🔄 Görevi Güncelleme

Görevi güncellemek için:

1. Task Scheduler'da görevi bulun
2. Sağ tıklayıp **"Properties"** seçin
3. İstediğiniz ayarları değiştirin
4. **"OK"** tıklayın

## 🗑️ Görevi Silme

Görevi silmek için:

1. Task Scheduler'da görevi bulun
2. Sağ tıklayıp **"Delete"** seçin
3. Onaylayın

veya komut satırından:

```bash
schtasks /Delete /TN "FieldOps_AutomatedEmails" /F
```

