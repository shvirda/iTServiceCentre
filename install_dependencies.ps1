# Скрипт установки всех зависимостей PromoService V0003
# Для Windows PowerShell

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "PromoService V0003 - Установка зависимостей" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Проверка Python
Write-Host "Проверка Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Python не установлен!" -ForegroundColor Red
    Write-Host "  Пожалуйста, установите Python 3.8+ с сайта https://www.python.org/" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Найден: $pythonVersion" -ForegroundColor Green
Write-Host ""

# Обновление pip
Write-Host "Обновление pip, setuptools и wheel..." -ForegroundColor Yellow
python -m pip install --upgrade pip setuptools wheel
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Ошибка при обновлении pip" -ForegroundColor Red
    exit 1
}
Write-Host "✓ pip, setuptools и wheel обновлены" -ForegroundColor Green
Write-Host ""

# Установка backend зависимостей
Write-Host "Установка backend зависимостей..." -ForegroundColor Yellow
pip install Flask Flask-SQLAlchemy Flask-CORS SQLAlchemy python-dotenv bcrypt PyJWT requests python-dateutil
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Ошибка при установке backend зависимостей" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Backend зависимости установлены" -ForegroundColor Green
Write-Host ""

# Установка Excel поддержки
Write-Host "Установка openpyxl..." -ForegroundColor Yellow
pip install openpyxl
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Ошибка при установке openpyxl" -ForegroundColor Red
}
else {
    Write-Host "✓ openpyxl установлен" -ForegroundColor Green
}
Write-Host ""

# Проверка PyQt6 (опционально)
Write-Host "Проверка PyQt6..." -ForegroundColor Yellow
python -c "from PyQt6.QtWidgets import QApplication; print('PyQt6 готов к использованию')" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠ PyQt6 не установлен (требуется для Frontend)" -ForegroundColor Yellow
    Write-Host "  Для установки PyQt6 требуются Visual Studio Build Tools" -ForegroundColor Yellow
    Write-Host "  Попробуйте: pip install PyQt6" -ForegroundColor Cyan
}
else {
    Write-Host "✓ PyQt6 успешно установлен" -ForegroundColor Green
}
Write-Host ""

# Проверка Flask
Write-Host "Проверка установки Flask..." -ForegroundColor Yellow
python -c "import flask; print('Flask версия: ' + flask.__version__)"
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Ошибка при импорте Flask" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Flask успешно установлен" -ForegroundColor Green
Write-Host ""

# Проверка SQLAlchemy
Write-Host "Проверка установки SQLAlchemy..." -ForegroundColor Yellow
python -c "import sqlalchemy; print('SQLAlchemy версия: ' + sqlalchemy.__version__)"
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Ошибка при импорте SQLAlchemy" -ForegroundColor Red
    exit 1
}
Write-Host "✓ SQLAlchemy успешно установлен" -ForegroundColor Green
Write-Host ""

Write-Host "======================================================================" -ForegroundColor Green
Write-Host "✓ ВСЕ ЗАВИСИМОСТИ УСПЕШНО УСТАНОВЛЕНЫ!" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Теперь можно запустить приложение:" -ForegroundColor Cyan
Write-Host "  python run.py" -ForegroundColor White
Write-Host "  или" -ForegroundColor White
Write-Host "  start_app.cmd" -ForegroundColor White
Write-Host ""
