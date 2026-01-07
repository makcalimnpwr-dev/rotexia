@echo off
REM ============================================
REM Otomatik Mail Gönderimi - Task Scheduler DURDURMA
REM ============================================
REM Bu script, send_automated_emails Task Scheduler görevini durdurur ve siler.

echo ============================================
echo Otomatik Mail Gönderimi - Task Scheduler DURDURMA
echo ============================================
echo.

REM Task Scheduler görev adı
set TASK_NAME=FieldOps_AutomatedEmails

echo Görev adı: %TASK_NAME%
echo.

REM Görevi durdur
echo Görev durduruluyor...
schtasks /End /TN "%TASK_NAME%" >nul 2>&1

REM Görevi sil
echo Görev siliniyor...
schtasks /Delete /TN "%TASK_NAME%" /F >nul 2>&1

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================
    echo BASARILI!
    echo ============================================
    echo.
    echo Task Scheduler görevi başarıyla durduruldu ve silindi.
    echo Artık otomatik mail gönderimi çalışmayacak.
    echo.
    echo Tekrar başlatmak için:
    echo   setup_automated_email_scheduler.bat dosyasını çalıştırın
    echo.
) else (
    echo.
    echo ============================================
    echo UYARI!
    echo ============================================
    echo.
    echo Görev bulunamadı veya zaten durdurulmuş olabilir.
    echo.
)

pause


