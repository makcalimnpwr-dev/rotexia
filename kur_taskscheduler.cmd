@echo off
REM Task Scheduler görevi oluştur (Basit versiyon)
echo Task Scheduler gorevi olusturuluyor...

cd /d "%~dp0"

schtasks /Create /TN "FieldOps_AutomatedEmails" /TR "python \"%CD%\manage.py\" send_automated_emails" /SC MINUTE /MO 5 /ST 00:00 /F /RU SYSTEM

if %ERRORLEVEL% EQU 0 (
    echo [OK] Gorev basariyla olusturuldu!
    echo.
    echo Gorevi manuel calistirmak icin:
    echo   schtasks /Run /TN "FieldOps_AutomatedEmails"
    echo.
) else (
    echo [HATA] Gorev olusturulamadi. Lutfen yonetici olarak calistirin.
)

pause


