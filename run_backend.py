#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт запуска Backend API сервера PromoService
"""
import sys
import os
import io

# Установка UTF-8 для вывода
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import create_app
from database.db_manager import DatabaseManager
from config import Config


def main():
    """Главная функция запуска"""
    print("=" * 60)
    print("PromoService V0001 - Backend Server")
    print("=" * 60)
    
    # Создаем Flask приложение
    app = create_app()
    
    # Инициализируем БД
    print("\nИнициализация БД...")
    db_manager = DatabaseManager(Config.SQLALCHEMY_DATABASE_URI)
    db_manager.initialize_database(app, create_admin=True)
    
    # Информация о БД
    db_info = db_manager.get_database_info()
    print(f"\nИнформация о БД:")
    print(f"  URL: {db_info['url']}")
    print(f"  Тип: {db_info['type']}")
    if db_info['type'] == 'SQLite':
        print(f"  Путь: {db_info['path']}")
        print(f"  Существует: {'Да' if db_info.get('exists') else 'Нет'}")
        if db_info.get('size'):
            print(f"  Размер: {db_info['size'] / 1024:.2f} KB")
    
    # Стартуем сервер
    print(f"\n{'=' * 60}")
    print(f"API Сервер запущен:")
    print(f"  Host: {Config.API_HOST}")
    print(f"  Port: {Config.API_PORT}")
    print(f"  URL: {Config.API_URL}")
    print(f"{'=' * 60}\n")
    
    # Запускаем Flask приложение
    try:
        app.run(
            host=Config.API_HOST,
            port=Config.API_PORT,
            debug=Config.DEBUG,
            use_reloader=True
        )
    except KeyboardInterrupt:
        print("\n\nСервер остановлен пользователем")
        sys.exit(0)


if __name__ == '__main__':
    main()
