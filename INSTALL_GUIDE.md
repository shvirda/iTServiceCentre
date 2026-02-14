# Руководство по установке и запуску PromoService V0002

## Быстрый старт

### Вариант 1: Автоматическая установка (Рекомендуется)

```powershell
# Запустить скрипт установки зависимостей
.\install_dependencies.ps1
```

Если возникнет ошибка с правами доступа PowerShell:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Затем снова запустите скрипт установки.

### Вариант 2: Безопасный запуск (Автоматическая проверка зависимостей)

```powershell
python run_safe.py
```

Этот скрипт:
- Проверит все зависимости
- Установит недостающие модули автоматически
- Предложит запустить только Backend, если PyQt6 не установлен

### Вариант 3: Ручная установка

```powershell
# Обновить pip
python -m pip install --upgrade pip setuptools wheel

# Установить все зависимости
pip install -r requirements.txt
```

## Решение проблем

### Ошибка: "DLL load failed while importing QtCore"

Это означает, что PyQt6 установлен неправильно.

**Решение:**

```powershell
# Очистить кэш pip
pip cache purge

# Переустановить PyQt6
pip install --no-cache-dir --force-reinstall PyQt6==6.6.0

# Проверить установку
python -c "from PyQt6.QtWidgets import QApplication; print('OK')"
```

### Ошибка: "No module named 'PyQt6'"

PyQt6 не установлен.

**Решение:**

```powershell
# Установить PyQt6 с зависимостями
pip install PyQt6==6.6.0 PyQt6-sip PyQt6-Qt6
```

### Ошибка: "No module named 'flask'"

Backend зависимости не установлены.

**Решение:**

```powershell
# Установить все зависимости
pip install -r requirements.txt
```

## Запуск приложения

### Запуск с автоматической проверкой зависимостей

```powershell
python run_safe.py
```

### Запуск Backend и Frontend одновременно

```powershell
python run.py
```

### Запуск только Backend (если проблема с PyQt6)

```powershell
python run_backend.py
```

API будет доступен на: `http://127.0.0.1:5000`

### Запуск только Frontend (нужен уже запущенный Backend)

Окно 1:
```powershell
python run_backend.py
```

Окно 2:
```powershell
python run_frontend.py
```

## Проверка установки

```powershell
# Проверить Python
python --version

# Проверить pip
pip --version

# Проверить Flask
python -c "import flask; print(f'Flask {flask.__version__}')"

# Проверить SQLAlchemy
python -c "import sqlalchemy; print(f'SQLAlchemy {sqlalchemy.__version__}')"

# Проверить PyQt6
python -c "from PyQt6.QtWidgets import QApplication; print('PyQt6 OK')"
```

## Первый запуск

При первом запуске приложение автоматически:
1. Создает БД (SQLite)
2. Создает таблицы
3. Создает администратора по умолчанию

**Учетные данные администратора:**
- Username: `admin`
- Password: `admin123`

⚠️ **Обязательно измените пароль после первого входа!**

## Требования

- Python 3.8 или выше
- Windows 7+ (для GUI)
- 200 MB свободного места для установки зависимостей

## Системные требования

### Windows
- Python 3.8+
- pip
- Права администратора для установки (может потребоваться)

### Проверка Python

```powershell
python --version
```

Должна быть версия 3.8.0 или выше.

## Частые вопросы

**Q: Почему не работает PyQt6?**
A: Это проблема совместимости с DLL файлами. Пересоздайте виртуальное окружение или переустановите PyQt6.

**Q: Можно ли запустить только Backend?**
A: Да, используйте `python run_backend.py`. Backend доступен на `http://127.0.0.1:5000`.

**Q: Как изменить порт API?**
A: Отредактируйте `config.py`, строка 25:
```python
API_PORT = int(os.getenv('API_PORT', 5001))  # Измените 5001 на нужный порт
```

**Q: Где находится БД?**
A: По умолчанию в `instance/promoservice_db.sqlite3`

## Контакт и поддержка

Для вопросов и проблем обратитесь к разработчику.

---

**Версия**: 0.0.2  
**Последнее обновление**: 2025-12-29
