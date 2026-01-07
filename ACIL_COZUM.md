# 🚨 ACİL ÇÖZÜM: Otomatik Mail Gönderimi

## SORUN
Mail gelmiyor çünkü **Task Scheduler görevi kurulu değil!**

## ✅ HEMEN YAPIN

### ADIM 1: Task Scheduler Görevini Kurun

**Seçenek A - Otomatik (1 dakika):**
1. `setup_automated_email_scheduler.bat` dosyasına **SAĞ TIKLAYIN**
2. **"Run as administrator"** seçin
3. Script otomatik görevi oluşturacak
4. **TAMAM!** Artık her 5 dakikada bir otomatik kontrol edecek

**Seçenek B - Manuel (3 dakika):**
1. Windows tuşuna basın → "Task Scheduler" yazın → Enter
2. Sağ tarafta **"Create Basic Task"** tıklayın
3. Name: `FieldOps_AutomatedEmails`
4. Description: `Otomatik Mail Gönderimi`
5. **Next**
6. Trigger: **Daily** seçin → **Next**
7. Start: Bugünün tarihi, saat: 00:00 → **Next**
8. Action: **Start a program** → **Next**
9. Program/script: `python`
10. Add arguments: `manage.py send_automated_emails`
11. Start in: `C:\Users\musta\Desktop\field_ops_project1`
12. **Next** → **Next** → **Finish**
13. Oluşturulan göreve **SAĞ TIKLAYIN** → **Properties**
14. **Triggers** tab → **Edit**
15. **Repeat task every:** 5 minutes
16. **Duration:** Indefinitely
17. **OK** → **OK**

### ADIM 2: Test Edin

Görevi manuel çalıştırın:
```cmd
schtasks /Run /TN "FieldOps_AutomatedEmails"
```

VEYA komut satırından:
```bash
python manage.py send_automated_emails
```

## 📋 KONTROL LİSTESİ

- [ ] Mail aktif mi? (Otomatik Mail sayfasında "Aktif" kutusu işaretli olmalı)
- [ ] Task Scheduler görevi kurulu mu? (Windows Task Scheduler'da kontrol edin)
- [ ] Gönderim saati geçti mi? (16:53)
- [ ] Bugün gönderilmiş mi? (Eğer bugün gönderilmişse, yarın gönderilecek)

## ⚠️ ÖNEMLİ NOT

**Task Scheduler görevi kurulmadan otomatik mail gönderimi ASLA çalışmaz!**

Bu görev her 5 dakikada bir `python manage.py send_automated_emails` komutunu çalıştırır.

## 🔍 SORUN GİDERME

**"Bugün zaten gönderildi" hatası alıyorsanız:**
- Bu normal! Günde bir kere gönderilir
- Yarın otomatik gönderilecek
- Veya "Şimdi Gönder" butonunu kullanın

**Task Scheduler çalışmıyor:**
- Görevi manuel çalıştırıp hata var mı kontrol edin
- Python PATH'te mi? (`where python` komutu ile kontrol edin)
- Görev "Run whether user is logged on or not" olarak ayarlanmış mı?


