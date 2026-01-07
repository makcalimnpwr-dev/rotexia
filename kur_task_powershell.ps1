# Task Scheduler Görevi Kurulumu (PowerShell)
$TaskName = "FieldOps_AutomatedEmails"
$ProjectDir = "C:\Users\musta\Desktop\field_ops_project1"
$PythonCommand = "python"
$TaskCommand = "$PythonCommand `"$ProjectDir\manage.py`" send_automated_emails"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Task Scheduler Gorevi Kuruluyor..." -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Gorev adi: $TaskName" -ForegroundColor Yellow
Write-Host "Proje dizini: $ProjectDir" -ForegroundColor Yellow
Write-Host "Komut: $TaskCommand" -ForegroundColor Yellow
Write-Host ""

# Mevcut görevi sil (varsa)
Write-Host "Eski gorev siliniyor (varsa)..." -ForegroundColor Gray
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "Eski gorev silindi." -ForegroundColor Gray
}

# Yeni görev oluştur
Write-Host "Yeni gorev olusturuluyor..." -ForegroundColor Gray

$Action = New-ScheduledTaskAction -Execute $PythonCommand -Argument "`"$ProjectDir\manage.py`" send_automated_emails" -WorkingDirectory $ProjectDir
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 365)
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Highest

try {
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description "FieldOps - Otomatik Mail Gonderimi (Her 5 dakikada bir)" -Force
    
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "BASARILI!" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Task Scheduler gorevi basariyla olusturuldu." -ForegroundColor Green
    Write-Host ""
    Write-Host "Kontrol etmek icin:" -ForegroundColor Yellow
    Write-Host "  schtasks /query /tn `"$TaskName`"" -ForegroundColor White
    Write-Host ""
    Write-Host "Manuel calistirmak icin:" -ForegroundColor Yellow
    Write-Host "  schtasks /Run /TN `"$TaskName`"" -ForegroundColor White
    Write-Host ""
} catch {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Red
    Write-Host "HATA!" -ForegroundColor Red
    Write-Host "============================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Gorev olusturulamadi: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Lutfen YONETICI OLARAK calistirin!" -ForegroundColor Yellow
    Write-Host ""
}

Read-Host "Devam etmek icin Enter'a basin"



