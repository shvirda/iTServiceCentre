"""
Менеджер для управления БД PromoService
Создание, подключение, инициализация таблиц
"""
import os
import sqlite3
from pathlib import Path
from database.models import db, User, Employee, Client, Equipment, Warehouse, Service, OperationLog


class DatabaseManager:
    """Менеджер для работы с БД"""
    
    def __init__(self, db_url: str = None):
        """
        Инициализация менеджера БД
        
        Args:
            db_url: URL подключения к БД (по умолчанию SQLite локально)
        """
        self.db_url = db_url or 'sqlite:///promoservice_db.sqlite3'
        self.db_path = None
        
        if self.db_url.startswith('sqlite:'):
            # Извлекаем путь из SQLite URL
            self.db_path = self.db_url.replace('sqlite:///', '')
    
    def create_database(self, app):
        """
        Создание БД и таблиц
        
        Args:
            app: Flask приложение
        """
        try:
            # Создаем директорию если её нет
            if self.db_path:
                db_dir = Path(self.db_path).parent
                db_dir.mkdir(parents=True, exist_ok=True)
            
            # Создаем таблицы
            with app.app_context():
                db.create_all()
            
            print(f"[OK] База данных создана: {self.db_url}")
            return True
        except Exception as e:
            print(f"[ERROR] Ошибка при создании БД: {e}")
            return False
    
    def initialize_database(self, app, create_admin: bool = True):
        """
        Инициализация БД с начальными данными
        
        Args:
            app: Flask приложение
            create_admin: Создавать ли администратора по умолчанию
        """
        try:
            with app.app_context():
                # Создаем БД если её нет
                self.create_database(app)
                
                # Проверяем есть ли уже пользователи
                existing_users = User.query.count()
                
                if existing_users == 0 and create_admin:
                    # Создаем администратора по умолчанию
                    import bcrypt
                    
                    admin_password = 'admin123'  # Пароль по умолчанию, нужно изменить
                    password_hash = bcrypt.hashpw(
                        admin_password.encode('utf-8'),
                        bcrypt.gensalt()
                    ).decode('utf-8')
                    
                    admin_user = User(
                        username='admin',
                        password_hash=password_hash,
                        role='director'
                    )
                    db.session.add(admin_user)
                    db.session.commit()
                    
                    # Создаем связанного сотрудника
                    admin_employee = Employee(
                        name='Администратор',
                        position='Директор',
                        access_level='director',
                        user_id=admin_user.id
                    )
                    db.session.add(admin_employee)
                    db.session.commit()
                    
                    print("[OK] Администратор создан (username: admin, password: admin123)")
                    print("  [INFO] Обязательно измените пароль после первого входа!")
                
                print("[OK] База данных инициализирована")
                return True
                
        except Exception as e:
            print(f"[ERROR] Ошибка при инициализации БД: {e}")
            return False
    
    def get_database_info(self) -> dict:
        """
        Получить информацию о БД
        
        Returns:
            dict: Информация о БД
        """
        info = {
            'url': self.db_url,
            'type': 'SQLite' if self.db_url.startswith('sqlite:') else 'PostgreSQL',
            'path': self.db_path if self.db_path else 'remote'
        }
        
        if self.db_path:
            if os.path.exists(self.db_path):
                info['size'] = os.path.getsize(self.db_path)
                info['exists'] = True
            else:
                info['exists'] = False
        
        return info
    
    def drop_all_tables(self, app):
        """
        Удалить все таблицы (ОСТОРОЖНО!)
        
        Args:
            app: Flask приложение
        """
        try:
            with app.app_context():
                db.drop_all()
            print("[OK] Все таблицы удалены")
            return True
        except Exception as e:
            print(f"[ERROR] Ошибка при удалении таблиц: {e}")
            return False
    
    def backup_database(self, backup_path: str = None) -> bool:
        """
        Резервная копия БД
        
        Args:
            backup_path: Путь для сохранения резервной копии
        
        Returns:
            bool: Успешность операции
        """
        if not self.db_path or not os.path.exists(self.db_path):
            print("[ERROR] БД не найдена")
            return False
        
        try:
            if not backup_path:
                # Создаем имя файла с датой
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = f"backups/promoservice_backup_{timestamp}.sqlite3"
            
            # Создаем директорию если её нет
            backup_dir = Path(backup_path).parent
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Копируем файл
            import shutil
            shutil.copy2(self.db_path, backup_path)
            
            print(f"[OK] Резервная копия создана: {backup_path}")
            return True
        except Exception as e:
            print(f"[ERROR] Ошибка при создании резервной копии: {e}")
            return False


def init_db_with_app(app):
    """
    Инициализировать БД с Flask приложением
    
    Args:
        app: Flask приложение
    """
    db.init_app(app)
    manager = DatabaseManager(app.config['SQLALCHEMY_DATABASE_URI'])
    manager.initialize_database(app)
    return manager
