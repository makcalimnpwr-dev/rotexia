@echo off
REM Task Scheduler görevini düzelt - Python yolunu tam yol olarak ayarla
echo ============================================
echo Task Scheduler Gorevi Duzeltiliyor...
echo ============================================
echo.

set TASK_NAME=FieldOps_AutomatedEmails
set PROJECT_DIR=C:\Users\musta\Desktop\field_ops_project1

REM Python'un tam yolunu bul
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    for /f "delims=" %%i in ('where python') do set PYTHON_FULL_PATH=%%i
    echo Python bulundu: %PYTHON_FULL_PATH%
) else (
    echo HATA: Python bulunamadi!
    pause
    exit /b 1
)

echo.
echo Eski gorev siliniyor...
schtasks /Delete /TN "%TASK_NAME%" /F >nul 2>&1

echo Yeni gorev olusturuluyor...
echo Python yolu: %PYTHON_FULL_PATH%
echo Komut: "%PYTHON_FULL_PATH%" "%PROJECT_DIR%\manage.py" send_automated_emails
echo.

REM Yeni görev oluştur - Python'un tam yolunu kullan
schtasks /Create /TN "%TASK_NAME%" ^
    /TR "\"%PYTHON_FULL_PATH%\" \"%PROJECT_DIR%\manage.py\" send_automated_emails" ^
    /SC MINUTE /MO 5 ^
    /ST 00:00 ^
    /RL HIGHEST ^
    /F ^
    /D "FieldOps - Otomatik Mail Gonderimi (Her 5 dakikada bir)"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================
    echo BASARILI!
    echo ============================================
    echo.
    echo Task Scheduler gorevi basariyla duzeltildi.
    echo.
    echo Test etmek icin:
    echo   schtasks /Run /TN "%TASK_NAME%"
    echo.
) else (
    echo.
    echo ============================================
    echo HATA!
    echo ============================================
    echo.
    echo Gorev olusturulamadi.
    echo Lutfen YONETICI OLARAK calistirin!
    echo.
)

pause

