import os

# Bu klasörler ve dosyalar taranmayacak (Gereksiz kalabalık yapmasın)
IGNORE_DIRS = {
    '__pycache__', 'venv', 'env', '.git', '.idea', 'migrations', 
    'static', 'Media', 'assets', 'node_modules'
}
IGNORE_FILES = {
    'db.sqlite3', '.DS_Store', 'poetry.lock', 'package-lock.json', 
    'ozet_cikar.py', 'proje_haritasi.txt', 'manage.py'
}
# Sadece bu uzantılı dosyaları alalım (Kod dosyaları)
ALLOWED_EXTENSIONS = {'.py', '.html', '.css', '.js', '.txt'}

OUTPUT_FILE = "TUM_PROJE_KODLARI.txt"

def get_project_structure(start_path):
    structure = "=== PROJE DOSYA YAPISI ===\n"
    for root, dirs, files in os.walk(start_path):
        # Gereksiz klasörleri atla
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        level = root.replace(start_path, '').count(os.sep)
        indent = ' ' * 4 * (level)
        structure += f"{indent}[{os.path.basename(root)}]\n"
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            if f not in IGNORE_FILES:
                structure += f"{subindent}{f}\n"
    return structure + "\n" + "="*50 + "\n\n"

def merge_files(start_path):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:
        # 1. Önce Ağaç Yapısını Yaz
        outfile.write(get_project_structure(start_path))
        
        # 2. Dosya İçeriklerini Yaz
        for root, dirs, files in os.walk(start_path):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            for file in files:
                if file in IGNORE_FILES: continue
                
                ext = os.path.splitext(file)[1]
                if ext not in ALLOWED_EXTENSIONS: continue

                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, start_path)

                outfile.write(f"\n\n{'='*20}\nDOSYA: {rel_path}\n{'='*20}\n")
                
                try:
                    with open(file_path, "r", encoding="utf-8") as infile:
                        outfile.write(infile.read())
                except Exception as e:
                    outfile.write(f"!!! HATA: Dosya okunamadı ({e})")

if __name__ == "__main__":
    current_dir = os.getcwd()
    print("Proje özeti çıkarılıyor...")
    merge_files(current_dir)
    print(f"Bitti! '{OUTPUT_FILE}' dosyasına tüm kodlar kaydedildi.")