import os

# Hedef dosya yolu
dosya_yolu = os.path.join(os.getcwd(), 'apps', 'customers', 'models.py')

print("-" * 50)
print(f"Kontrol edilen dosya:\n{dosya_yolu}")
print("-" * 50)

if os.path.exists(dosya_yolu):
    print("✅ Dosya bulundu!")
    
    # İçini oku
    with open(dosya_yolu, 'r', encoding='utf-8') as f:
        icerik = f.read()
        
    if not icerik.strip():
        print("❌ HATA: Dosyanın içi BOMBOŞ!")
        print("   ÇÖZÜM: Kodları bu dosyaya yapıştırıp kaydetmelisin.")
    elif "class Customer(models.Model):" in icerik:
        print("✅ Kodlar görünüyor. Sorun başka yerde olabilir.")
    else:
        print("⚠️ HATA: Dosya dolu ama 'class Customer' kodu yok.")
        print("   Muhtemelen yanlış kod yapıştırıldı veya kaydedilmedi.")
        print(f"   Dosya İçeriği Özeti: {icerik[:50]}...")
else:
    print("❌ HATA: 'apps/customers/models.py' dosyası YOK!")
    print("   Lütfen klasör yapısını kontrol et (apps -> customers -> models.py).")

print("-" * 50)