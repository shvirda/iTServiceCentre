#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Единый скрипт запуска PromoService V0002
Запускает Backend API сервер и Frontend приложение на tkinter
"""
import sys
import os
import subprocess
import time
import io

# Установка UTF-8 для вывода
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from backend.app import create_app
from database.db_manager import DatabaseManager


def main():
    """Главная функция запуска с отдельными процессами"""
    print("\n" + "=" * 70)
    print("PromoService V0002 - Управление сервисным центром")
    print("=" * 70)
    print("\nИнициализация Backend...\n")
    
    # Инициализируем БД в главном процессе
    try:
        app = create_app()
        print("Инициализация БД...")
        db_manager = DatabaseManager(Config.SQLALCHEMY_DATABASE_URI)
        db_manager.initialize_database(app, create_admin=True)
        
        db_info = db_manager.get_database_info()
        print(f"\nИнформация о БД:")
        print(f"  URL: {db_info['url']}")
        print(f"  Тип: {db_info['type']}")
        if db_info['type'] == 'SQLite':
            print(f"  Путь: {db_info['path']}")
            print(f"  Существует: {'Да' if db_info.get('exists') else 'Нет'}")
            if db_info.get('size'):
                print(f"  Размер: {db_info['size'] / 1024:.2f} KB")
        print()
    except Exception as e:
        print(f"✗ Ошибка инициализации БД: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("Запуск Backend и Frontend в отдельных процессах...")
    print("=" * 70 + "\n")
    
    # Запускаем Backend в отдельном процессе
    backend_process = subprocess.Popen(
        [sys.executable, "run_backend.py"],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    # Даем Backend время на инициализацию
    print("Ожидание инициализации Backend (3 сек)...")
    time.sleep(3)
    
    # Запускаем Frontend в главном процессе (tkinter)
    try:
        from frontend.auth_window_tk import show_auth_dialog
        from frontend.main_window_tk import run_frontend
        
        print("\n" + "=" * 70)
        print("FRONTEND APPLICATION (tkinter)")
        print("=" * 70)
        print(f"\nПопытка подключения к API: {Config.API_URL}\n")
        
        print("Показание окна авторизации...")
        token, user_data = show_auth_dialog(Config.API_URL)
        
        if token is None or user_data is None:
            print("\nПользователь отменил вход в систему")
            backend_process.terminate()
            sys.exit(0)
        
        print(f"\n✓ Успешный вход")
        print(f"  Пользователь: {user_data.get('username')}")
        print(f"  ID: {user_data.get('id')}")
        print(f"  Роль: {user_data.get('role')}")
        print()
        
        print("Запуск главного окна...\n")
        run_frontend(token, user_data, Config.API_URL)
        
        # Завершаем Backend при выходе
        print("\nЗавершение Backend...")
        backend_process.terminate()
        try:
            backend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend_process.kill()
        
        print("✓ Приложение завершено")
        sys.exit(0)
    
    except ImportError as e:
        print(f"Ошибка импорта: {e}")
        print("Убедитесь, что tkinter установлен (входит в стандартную поставку Python)")
        backend_process.terminate()
        sys.exit(1)
    except Exception as e:
        print(f"Ошибка Frontend: {e}")
        import traceback
        traceback.print_exc()
        backend_process.terminate()
        sys.exit(1)


if __name__ == '__main__':
    main()
