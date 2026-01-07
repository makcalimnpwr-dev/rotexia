"""
Task Scheduler görevini test et ve debug bilgisi ver
"""
import os
import subprocess
import sys

print("=" * 60)
print("TASK SCHEDULER TEST VE DEBUG")
print("=" * 60)
print()

# 1. Görev adlarını kontrol et
print("1. Tüm Task Scheduler görevlerini kontrol ediyorum...")
print("-" * 60)
try:
    result = subprocess.run(['schtasks', '/query', '/fo', 'LIST'], 
                          capture_output=True, text=True, encoding='utf-8', errors='ignore')
    tasks = result.stdout
    if 'FieldOps' in tasks or 'fieldops' in tasks.lower():
        print("[OK] FieldOps gorevi bulundu!")
        for line in tasks.split('\n'):
            if 'FieldOps' in line or 'fieldops' in line.lower():
                print(f"  {line}")
    else:
        print("[HATA] FieldOps gorevi BULUNAMADI!")
        print("\nTüm görevler:")
        print(tasks[:500])  # İlk 500 karakter
except Exception as e:
    print(f"[HATA] Hata: {e}")

print()
print("2. Manuel olarak komutu test ediyorum...")
print("-" * 60)

# 2. Manuel komutu test et
project_dir = r"C:\Users\musta\Desktop\field_ops_project1"
python_cmd = "python"
manage_py = os.path.join(project_dir, "manage.py")

if os.path.exists(manage_py):
    print(f"[OK] manage.py bulundu: {manage_py}")
    print(f"[OK] Python komutu: {python_cmd}")
    print(f"[OK] Proje dizini: {project_dir}")
    print()
    print("Komut:")
    print(f'  {python_cmd} "{manage_py}" send_automated_emails')
    print()
    print("Bu komutu manuel olarak çalıştırmayı deneyin:")
    print(f'  cd "{project_dir}"')
    print(f'  {python_cmd} manage.py send_automated_emails')
else:
    print(f"[HATA] manage.py bulunamadi: {manage_py}")

print()
print("3. Task Scheduler görevini oluşturma komutu:")
print("-" * 60)
task_name = "FieldOps_AutomatedEmails"
task_command = f'{python_cmd} "{manage_py}" send_automated_emails'
print(f"Görev adı: {task_name}")
print(f"Komut: {task_command}")
print()
print("Yönetici CMD'de şu komutu çalıştırın:")
print(f'  schtasks /Create /TN "{task_name}" /TR "{python_cmd} \\"{manage_py}\\" send_automated_emails" /SC MINUTE /MO 5 /ST 00:00 /F')

print()
print("=" * 60)

