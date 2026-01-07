# 🔧 Task Scheduler Kurulumu - ADIM ADIM

## ⚠️ SORUN
Task Scheduler görevi kurulu DEĞİL! Bu yüzden otomatik mail gönderilmiyor.

## ✅ ÇÖZÜM - ADIM ADIM

### ADIM 1: Yönetici CMD Aç

1. **Windows tuşu** + **R** tuşlarına basın
2. `cmd` yazın ve **Ctrl + Shift + Enter** tuşlarına basın
   - Bu, CMD'yi yönetici olarak açar
   - VEYA: Windows tuşu → "cmd" yazın → Sağ tık → "Run as administrator"

### ADIM 2: Proje Dizinine Git

```cmd
cd "C:\Users\musta\Desktop\field_ops_project1"
```

### ADIM 3: Task Scheduler Görevini Oluştur

Şu komutu **TAM OLARAK** kopyalayıp yapıştırın:

```cmd
schtasks /Create /TN "FieldOps_AutomatedEmails" /TR "python \"C:\Users\musta\Desktop\field_ops_project1\manage.py\" send_automated_emails" /SC MINUTE /MO 5 /ST 00:00 /F
```

**ÖNEMLİ:** 
- Komutu **TAM OLARAK** kopyalayın (tırnak işaretleri dahil)
- Eğer hata alırsanız, Python yolunu kontrol edin

### ADIM 4: Görevin Kurulduğunu Kontrol Et

```cmd
schtasks /query /tn "FieldOps_AutomatedEmails"
```

Eğer görev görünüyorsa, **BAŞARILI!** ✅

### ADIM 5: Görevi Test Et

```cmd
schtasks /Run /TN "FieldOps_AutomatedEmails"
```

VEYA direkt:

```cmd
python manage.py send_automated_emails
```

## 📋 GÖNDERİM SAATİ

**Şu anki durum:**
- Gönderim saati: **21:30**
- Şu an: Yaklaşık **18:41**
- **Bekleme:** ~2.5 saat

Task Scheduler kurulduktan sonra, **21:30-21:35** arası mail gönderilecek.

## 🧪 HEMEN TEST ETMEK İÇİN

Eğer beklemek istemiyorsanız:

### Seçenek 1: Gönderim saatini değiştir
1. Otomatik mail ayarlarına gidin
2. Gönderim saatini **şu anki saatten 1-2 dakika sonrasına** ayarlayın
3. Task Scheduler otomatik olarak gönderecek

### Seçenek 2: Zorla gönder (test için)
```cmd
python test_send_email_now.py
```

Bu komut, zamanlama kontrolü yapmadan hemen gönderir (test amaçlı).

## 🔍 SORUN GİDERME

### "Erişim engellendi" hatası:
- Mutlaka **yönetici CMD** kullanın (Ctrl + Shift + Enter)

### "Python bulunamadı" hatası:
- Python'un PATH'te olduğundan emin olun
- VEYA Python'un tam yolunu kullanın:
  ```cmd
  schtasks /Create /TN "FieldOps_AutomatedEmails" /TR "\"C:\Python313\python.exe\" \"C:\Users\musta\Desktop\field_ops_project1\manage.py\" send_automated_emails" /SC MINUTE /MO 5 /ST 00:00 /F
  ```

### Görev görünmüyor:
- `schtasks /query /tn "FieldOps_AutomatedEmails"` komutuyla kontrol edin
- Eğer hata veriyorsa, görev kurulu değildir

## ✅ BAŞARILI KURULUM KONTROLÜ

Kurulum başarılı ise şu komut görevin detaylarını gösterecek:

```cmd
schtasks /query /tn "FieldOps_AutomatedEmails" /fo LIST /v
```

Çıktıda şunları görmelisiniz:
- Task Name: FieldOps_AutomatedEmails
- Status: Ready
- Next Run Time: (yaklaşık 5 dakika sonra)

## 📝 ÖZET

1. ✅ Yönetici CMD aç (Ctrl + Shift + Enter)
2. ✅ Proje dizinine git
3. ✅ Task Scheduler görevini oluştur (yukarıdaki komut)
4. ✅ Görevin kurulduğunu kontrol et
5. ✅ Test et (manuel çalıştır)

**ÖNEMLİ:** Task Scheduler görevi kurulmadan otomatik mail gönderimi **ASLA çalışmaz!**

