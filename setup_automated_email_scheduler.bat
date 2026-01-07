@echo off
REM ============================================
REM Otomatik Mail Gönderimi - Windows Task Scheduler Kurulumu
REM ============================================
REM Bu script, send_automated_emails management command'ini
REM her 5 dakikada bir çalıştırmak için Windows Task Scheduler görevi oluşturur.

echo ============================================
echo Otomatik Mail Gönderimi - Task Scheduler Kurulumu
echo ============================================
echo.

REM Proje dizinini bul (bu script'in bulunduğu dizin)
set PROJECT_DIR=%~dp0
set PROJECT_DIR=%PROJECT_DIR:~0,-1%

echo Proje dizini: %PROJECT_DIR%
echo.

REM Python yolunu bul
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo HATA: Python bulunamadı! Lütfen Python'u PATH'e ekleyin.
    pause
    exit /b 1
)

set PYTHON_CMD=python
echo Python komutu: %PYTHON_CMD%
echo.

REM Task Scheduler görev adı
set TASK_NAME=FieldOps_AutomatedEmails
set TASK_DESC=FieldOps - Otomatik Mail Gönderimi (Her 5 dakikada bir)

echo Görev adı: %TASK_NAME%
echo.

REM Mevcut görevi sil (varsa)
schtasks /Delete /TN "%TASK_NAME%" /F >nul 2>&1

REM Yeni görev oluştur
echo Görev oluşturuluyor...
schtasks /Create /TN "%TASK_NAME%" ^
    /TR "\"%PYTHON_CMD%\" \"%PROJECT_DIR%\manage.py\" send_automated_emails" ^
    /SC MINUTE /MO 5 ^
    /ST 00:00 ^
    /RU SYSTEM ^
    /RL HIGHEST ^
    /F ^
    /D "%TASK_DESC%"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================
    echo BASARILI!
    echo ============================================
    echo.
    echo Task Scheduler görevi başarıyla oluşturuldu.
    echo Görev adı: %TASK_NAME%
    echo Çalışma sıklığı: Her 5 dakikada bir
    echo.
    echo Görevi kontrol etmek için:
    echo   1. Windows Task Scheduler'ı açın
    echo   2. "Task Scheduler Library" bölümünde "%TASK_NAME%" görevini bulun
    echo.
    echo Görevi manuel çalıştırmak için:
    echo   schtasks /Run /TN "%TASK_NAME%"
    echo.
    echo Görevi silmek için:
    echo   schtasks /Delete /TN "%TASK_NAME%" /F
    echo.
) else (
    echo.
    echo ============================================
    echo HATA!
    echo ============================================
    echo.
    echo Task Scheduler görevi oluşturulamadı.
    echo Lütfen yönetici olarak çalıştırın (Run as Administrator).
    echo.
)

pause


