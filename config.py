import os
from datetime import timedelta

class Config:
    """Базовая конфигурация приложения"""
    
    # Для локальной БД (первый этап)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///promoservice_db.sqlite3'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT токены
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_DELTA = timedelta(hours=24)
    
    # Flask/FastAPI
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV == 'development'
    
    # API сервер
    API_HOST = os.getenv('API_HOST', '127.0.0.1')
    API_PORT = int(os.getenv('API_PORT', 5000))
    API_URL = f'http://{API_HOST}:{API_PORT}'
    
    # Доступные уровни доступа
    ACCESS_LEVELS = {
        'director': 4,
        'manager': 3,
        'employee': 2,
        'warehouse': 1
    }
    
    # Логирование
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = 'logs/promoservice.log'
    
    # UI параметры
    APP_TITLE = 'PromoService V0001 - Управление сервисным центром'
    WINDOW_WIDTH = 1400
    WINDOW_HEIGHT = 900
