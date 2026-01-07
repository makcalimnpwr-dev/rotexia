@echo off
REM Manuel Task Scheduler Kurulumu
echo ============================================
echo Task Scheduler Gorevi Kuruluyor...
echo ============================================
echo.

set TASK_NAME=FieldOps_AutomatedEmails
set PROJECT_DIR=C:\Users\musta\Desktop\field_ops_project1

echo Gorev adi: %TASK_NAME%
echo Proje dizini: %PROJECT_DIR%
echo.

REM Mevcut gorevi sil (varsa)
echo Eski gorev siliniyor (varsa)...
schtasks /Delete /TN "%TASK_NAME%" /F >nul 2>&1

REM Yeni gorev olustur
echo Yeni gorev olusturuluyor...
schtasks /Create /TN "%TASK_NAME%" /TR "python \"%PROJECT_DIR%\manage.py\" send_automated_emails" /SC MINUTE /MO 5 /ST 00:00 /F

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================
    echo BASARILI!
    echo ============================================
    echo.
    echo Task Scheduler gorevi basariyla olusturuldu.
    echo.
    echo Kontrol etmek icin:
    echo   schtasks /query /tn "%TASK_NAME%"
    echo.
    echo Manuel calistirmak icin:
    echo   schtasks /Run /TN "%TASK_NAME%"
    echo.
) else (
    echo.
    echo ============================================
    echo HATA!
    echo ============================================
    echo.
    echo Gorev olusturulamadi. Lutfen YONETICI OLARAK calistirin!
    echo.
    echo Sag tiklayip "Run as administrator" secin.
    echo.
)

pause



