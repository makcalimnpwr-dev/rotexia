# ⚠️ Task Scheduler Kurulumu - YÖNETİCİ GEREKLİ

## 🔴 SORUN
Task Scheduler görevi oluşturmak için **YÖNETİCİ YETKİSİ** gerekiyor!

## ✅ ÇÖZÜM - 3 YÖNTEM

### YÖNTEM 1: Batch Dosyasını Yönetici Olarak Çalıştır (ÖNERİLEN)

1. `setup_automated_email_scheduler.bat` dosyasına **SAĞ TIKLAYIN**
2. **"Run as administrator"** (Yönetici olarak çalıştır) seçin
3. Kurulum tamamlanana kadar bekleyin
4. Başarı mesajını görmelisiniz

### YÖNTEM 2: PowerShell'i Yönetici Olarak Aç ve Çalıştır

1. Windows tuşuna basın → **"PowerShell"** yazın
2. **"Windows PowerShell"**'e **SAĞ TIKLAYIN**
3. **"Run as administrator"** seçin
4. Şu komutu çalıştırın:

```powershell
cd "C:\Users\musta\Desktop\field_ops_project1"
.\setup_automated_email_scheduler.bat
```

VEYA direkt komut:

```powershell
cd "C:\Users\musta\Desktop\field_ops_project1"
schtasks /Create /TN "FieldOps_AutomatedEmails" /TR "python \"C:\Users\musta\Desktop\field_ops_project1\manage.py\" send_automated_emails" /SC MINUTE /MO 5 /ST 00:00 /F
```

### YÖNTEM 3: CMD'yi Yönetici Olarak Aç ve Çalıştır

1. Windows tuşuna basın → **"cmd"** yazın
2. **"Command Prompt"**'a **SAĞ TIKLAYIN**
3. **"Run as administrator"** seçin
4. Şu komutu çalıştırın:

```cmd
cd "C:\Users\musta\Desktop\field_ops_project1"
schtasks /Create /TN "FieldOps_AutomatedEmails" /TR "python \"C:\Users\musta\Desktop\field_ops_project1\manage.py\" send_automated_emails" /SC MINUTE /MO 5 /ST 00:00 /F
```

## ✅ KURULUMU KONTROL ET

Kurulumdan sonra şu komutu çalıştırın:

```cmd
schtasks /query /tn "FieldOps_AutomatedEmails"
```

Eğer görev görünüyorsa, başarılı!

## 🧪 TEST ET

Görevi manuel olarak çalıştırın:

```cmd
schtasks /Run /TN "FieldOps_AutomatedEmails"
```

VEYA direkt:

```cmd
python manage.py send_automated_emails
```

## ⚠️ ÖNEMLİ NOTLAR

1. **Yönetici yetkisi mutlaka gerekli** - Aksi halde "Erişim engellendi" hatası alırsınız
2. Kurulumdan sonra görevin **"Ready"** (Hazır) durumunda olduğunu kontrol edin
3. Görev her 5 dakikada bir otomatik çalışacak
4. Gönderim saati geçtiğinde mail gönderilecek

## 📋 GÖNDERİM SAATİ

Şu anki durum:
- **Gönderim saati:** 21:06
- **Şu anki saat:** Yaklaşık 18:23
- **Bekleme süresi:** ~162 dakika (2.5 saat)

Görev kurulduktan sonra, 21:06-21:11 arası (5 dakika tolerans) mail gönderilecek.

## 🔧 SORUN GİDERME

### "Erişim engellendi" hatası:
- Mutlaka yönetici olarak çalıştırın

### Görev görünmüyor:
- `schtasks /query /tn "FieldOps_AutomatedEmails"` komutuyla kontrol edin
- Görev yoksa, yönetici olarak tekrar kurun

### Mail hala gelmiyor:
1. Gönderim saatini kontrol edin (21:06)
2. Görevin çalıştığını kontrol edin (Task Scheduler'da "Last Run Result")
3. Manuel test edin: `python manage.py send_automated_emails`

