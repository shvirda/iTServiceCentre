#!/usr/bin/env python
"""
Запуск только Backend API сервера PromoService V0002
Без Frontend GUI - используйте API напрямую или через Postman
"""
import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from backend.app import create_app
from database.db_manager import DatabaseManager


def main():
    """Главная функция запуска"""
    print("\n" + "=" * 70)
    print("PromoService V0002 - Backend API Сервер")
    print("=" * 70)
    print("\nИнициализация БД...\n")
    
    try:
        # Создаем Flask приложение
        app = create_app()
        
        # Инициализируем БД
        print("Инициализация БД...")
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
        
        # Информация о сервере
        print(f"\n{'=' * 70}")
        print(f"API Сервер запущен:")
        print(f"  Host: {Config.API_HOST}")
        print(f"  Port: {Config.API_PORT}")
        print(f"  URL: {Config.API_URL}")
        print(f"{'=' * 70}\n")
        
        print("Учетные данные для авторизации:")
        print("  Username: admin")
        print("  Password: admin123")
        print("\n⚠️  Обязательно измените пароль администратора!")
        print("\nAPI Endpoints:")
        print("  POST /api/auth/login - Вход пользователя")
        print("  GET /api/health - Проверка статуса сервера")
        print("  GET /api/clients - Список клиентов")
        print("  GET /api/equipment - Список техники")
        print("  GET /api/warehouse - Список товара")
        print("\n" + "=" * 70 + "\n")
        
        # Запускаем Flask приложение
        app.run(
            host=Config.API_HOST,
            port=Config.API_PORT,
            debug=Config.DEBUG,
            use_reloader=True,
            threaded=True
        )
    
    except KeyboardInterrupt:
        print("\n\nСервер остановлен пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
