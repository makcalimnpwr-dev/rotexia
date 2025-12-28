import os

# Django'nun dosyayı aradığı yer
hedef_klasor = os.path.join(os.getcwd(), 'templates', 'apps', 'users')

print("-" * 50)
print(f"Kontrol edilen klasör:\n{hedef_klasor}")
print("-" * 50)

if os.path.exists(hedef_klasor):
    print("✅ Klasör bulundu! İçindeki dosyalar şunlar:")
    dosyalar = os.listdir(hedef_klasor)
    if not dosyalar:
        print("❌ KLASÖR BOŞ! Hiç dosya yok.")
    else:
        for dosya in dosyalar:
            print(f" 📄 {dosya}")
            
    print("-" * 50)
    if "role_list.html" in dosyalar:
        print("✅ role_list.html dosyası GÖRÜNÜYOR. Sorun başka yerde olabilir.")
    elif "role_list.html.txt" in dosyalar:
        print("⚠️ HATA BULUNDU: Dosya adı 'role_list.html.txt' olmuş!")
        print("   ÇÖZÜM: Dosyanın adındaki '.txt' kısmını silmelisin.")
    else:
        print("❌ HATA: 'role_list.html' dosyası bu klasörde yok.")
else:
    print("❌ HATA: 'templates/apps/users' klasörü hiç YOK!")
    print("   Lütfen klasör yollarını kontrol et.")
print("-" * 50)