# ⚠️ OTOMATIK MAIL GÖNDERİMİ ÇALIŞMIYOR - ÇÖZÜM

## 🔍 SORUN
Otomatik mail gönderilmiyor çünkü **Windows Task Scheduler görevi kurulu değil!**

## ✅ ÇÖZÜM

### ADIM 1: Task Scheduler Görevini Kurun

1. `setup_automated_email_scheduler.bat` dosyasına **SAĞ TIKLAYIN**
2. **"Run as administrator"** (Yönetici olarak çalıştır) seçin
3. Kurulum tamamlanana kadar bekleyin

VEYA Manuel olarak:

```cmd
schtasks /Create /TN "FieldOps_AutomatedEmails" /TR "python \"C:\Users\musta\Desktop\field_ops_project1\manage.py\" send_automated_emails" /SC MINUTE /MO 5 /ST 00:00 /F
```

### ADIM 2: Görevin Çalıştığını Kontrol Edin

1. Windows tuşuna basın → **"Task Scheduler"** yazın → Enter
2. **Task Scheduler Library** bölümünde **"FieldOps_AutomatedEmails"** görevini bulun
3. Görevin **"Ready"** (Hazır) durumunda olduğunu kontrol edin

### ADIM 3: Manuel Test

Görevi manuel olarak çalıştırarak test edin:

```cmd
schtasks /Run /TN "FieldOps_AutomatedEmails"
```

VEYA

```cmd
python manage.py send_automated_emails
```

## 📋 NASIL ÇALIŞIR?

- Task Scheduler **her 5 dakikada bir** `send_automated_emails` komutunu çalıştırır
- Sistem, aktif otomatik mailleri kontrol eder
- Gönderim saatinden sonra ise mail gönderir

## ⏰ GÖNDERİM SAATİ

- Gönderim saati: **17:33**
- Task Scheduler her 5 dakikada bir çalıştığı için:
  - 17:33-17:38 arası ilk çalıştırmada mail gönderilir
  - Örnek: Eğer saat 17:35'te çalışırsa, mail 17:35'te gönderilir

## 🔧 SORUN GİDERME

### Task Scheduler görevi çalışmıyor:

1. Görevi kontrol edin: Windows Task Scheduler → Task Scheduler Library → FieldOps_AutomatedEmails
2. Görevi sağ tıklayıp **"Run"** (Çalıştır) seçin
3. "Last Run Result" (Son Çalıştırma Sonucu) bölümünde hata var mı kontrol edin

### Mail hala gelmiyor:

1. **Aktif mi?** kontrolü: Otomatik mail ayarlarından "Aktif mi?" seçeneğinin açık olduğundan emin olun
2. Gönderim saatini kontrol edin: Saat geçti mi?
3. Email ayarlarını kontrol edin: SMTP ayarları doğru mu?

## 📝 NOTLAR

- Task Scheduler görevi kurulmadan otomatik mail gönderimi **ASLA çalışmaz**
- Görev her 5 dakikada bir çalışır, bu yüzden en fazla 5 dakika gecikme olabilir
- Gönderim saatinden önce ayarlanırsa, saat geldiğinde otomatik gönderilir

