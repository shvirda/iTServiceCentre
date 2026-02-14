# Скрипт для исправления ошибки DLL в PyQt6
# Установка Microsoft Visual C++ Runtime

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Исправление ошибки PyQt6 DLL" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Проверка Windows Edition
$osInfo = Get-WmiObject -Class Win32_OperatingSystem
Write-Host "Операционная система: $($osInfo.Caption)" -ForegroundColor Yellow
Write-Host "Разрядность: $([System.Environment]::Is64BitOperatingSystem ? '64-bit' : '32-bit')" -ForegroundColor Yellow
Write-Host ""

# Вариант 1: Переустановка PyQt6
Write-Host "Попытка 1: Переустановка PyQt6..." -ForegroundColor Yellow
Write-Host "Очистка кэша pip..." -ForegroundColor Gray
pip cache purge
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Кэш очищен" -ForegroundColor Green
}

Write-Host "Переустановка PyQt6..." -ForegroundColor Gray
pip install --no-cache-dir --force-reinstall PyQt6==6.6.0 PyQt6-sip PyQt6-Qt6
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ PyQt6 переустановлена" -ForegroundColor Green
    
    # Проверяем импорт
    python -c "from PyQt6.QtWidgets import QApplication; print('PyQt6 работает!')"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ PyQt6 успешно работает!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Теперь вы можете запустить: python run.py" -ForegroundColor Cyan
        exit 0
    }
}

Write-Host ""
Write-Host "Попытка 2: Установка Visual C++ Runtime..." -ForegroundColor Yellow
Write-Host ""

# Определяем разрядность Python
$pythonBitness = python -c "import struct; print(64 if struct.calcsize('P') * 8 == 64 else 32)"

if ($pythonBitness -eq 64) {
    Write-Host "Обнаружена 64-разрядная версия Python" -ForegroundColor Yellow
    $url = "https://aka.ms/vs/17/release/vc_redist.x64.exe"
    $filename = "vc_redist.x64.exe"
} else {
    Write-Host "Обнаружена 32-разрядная версия Python" -ForegroundColor Yellow
    $url = "https://aka.ms/vs/17/release/vc_redist.x86.exe"
    $filename = "vc_redist.x86.exe"
}

# Проверяем интернет соединение
Write-Host ""
Write-Host "Проверка интернет соединения..." -ForegroundColor Gray
$ping = Test-Connection -ComputerName 8.8.8.8 -Count 1 -Quiet
if (-not $ping) {
    Write-Host "✗ Нет интернета. Невозможно скачать Visual C++ Runtime" -ForegroundColor Red
    Write-Host ""
    Write-Host "Решение: Установите вручную с сайта Microsoft:" -ForegroundColor Yellow
    Write-Host "https://support.microsoft.com/en-us/help/2977003/the-latest-supported-visual-c-downloads" -ForegroundColor Cyan
    exit 1
}

Write-Host "✓ Интернет соединение OK" -ForegroundColor Green
Write-Host ""

# Скачиваем Visual C++ Runtime
Write-Host "Скачивание Visual C++ Runtime..." -ForegroundColor Gray
$downloadPath = Join-Path $env:TEMP $filename

try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $url -OutFile $downloadPath -UseBasicParsing -TimeoutSec 60
    
    if (Test-Path $downloadPath) {
        Write-Host "✓ Файл скачан: $downloadPath" -ForegroundColor Green
        
        # Запускаем установщик
        Write-Host ""
        Write-Host "Запуск установщика Visual C++ Runtime..." -ForegroundColor Yellow
        Write-Host "⚠️  Возможно, потребуется подтверждение администратора" -ForegroundColor Yellow
        
        & $downloadPath /install /quiet /norestart
        Start-Sleep -Seconds 3
        
        # Удаляем временный файл
        Remove-Item $downloadPath -Force -ErrorAction SilentlyContinue
        
        Write-Host "✓ Visual C++ Runtime установлен" -ForegroundColor Green
        Write-Host ""
        
        # Проверяем работу PyQt6
        Write-Host "Проверка PyQt6..." -ForegroundColor Gray
        python -c "from PyQt6.QtWidgets import QApplication; print('✓ PyQt6 работает!')"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Все готово! Теперь вы можете запустить: python run.py" -ForegroundColor Green
        } else {
            Write-Host "✗ PyQt6 все еще не работает" -ForegroundColor Red
            Write-Host ""
            Write-Host "Дополнительные варианты:" -ForegroundColor Yellow
            Write-Host "1. Перезагрузите компьютер и попробуйте снова" -ForegroundColor White
            Write-Host "2. Используйте python start_backend_only.py для запуска без GUI" -ForegroundColor White
            Write-Host "3. Переустановите Python полностью" -ForegroundColor White
        }
    } else {
        Write-Host "✗ Не удалось скачать файл" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Ошибка при скачивании: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Если проблема не решена, используйте:" -ForegroundColor Yellow
Write-Host "  python start_backend_only.py" -ForegroundColor White
Write-Host "======================================================================" -ForegroundColor Cyan
