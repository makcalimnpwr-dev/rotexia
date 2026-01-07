# Otomatik Mail Gönderimi - Kurulum Adımları

## ⚠️ ÖNEMLİ: Mail'in Aktif Olması Gerekiyor!

**Sorun:** Mail oluşturulmuş ama **"Aktif"** kutusu işaretli değilse, mail gönderilmez!

## ✅ Adım 1: Mail'i Aktif Hale Getirin

1. Tarayıcıda otomatik mail listesine gidin: `/automated-email/`
2. Mail'inizi bulun ve **"Düzenle"** butonuna tıklayın
3. **"Aktif"** kutusunu işaretleyin ✅
4. **"Kaydet"** butonuna tıklayın

VEYA

Python script ile:
```bash
python activate_automated_email.py
```

## ✅ Adım 2: Task Scheduler Görevini Kurun

1. `setup_automated_email_scheduler.bat` dosyasına **sağ tıklayın**
2. **"Run as administrator"** seçin
3. Script otomatik görev oluşturacak

VEYA

Komut satırından (yönetici olarak):
```cmd
cd C:\Users\musta\Desktop\field_ops_project1
schtasks /Create /TN "FieldOps_AutomatedEmails" /TR "python \"%CD%\manage.py\" send_automated_emails" /SC MINUTE /MO 5 /ST 00:00 /F
```

## ✅ Adım 3: Test Edin

Manuel test:
```bash
python manage.py send_automated_emails
```

Task Scheduler'dan manuel çalıştırma:
```cmd
schtasks /Run /TN "FieldOps_AutomatedEmails"
```

## 🔍 Sorun Giderme

### Mail gelmiyor
1. ✅ Mail aktif mi? (`is_active = True`)
2. ✅ Task Scheduler görevi kurulu mu?
3. ✅ Gönderim saati geçti mi?
4. ✅ SMTP ayarları doğru mu?

### Task Scheduler çalışmıyor
- Görevi kontrol edin: Windows Task Scheduler → Task Scheduler Library → FieldOps_AutomatedEmails
- Son çalışma zamanına bakın
- Manuel çalıştırıp hata var mı kontrol edin




