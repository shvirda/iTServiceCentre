"""
Главное Flask приложение PromoService
Инициализация API и маршрутов
"""
from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from database.models import db
from database.db_manager import init_db_with_app
from backend.auth import AuthManager
import logging
from pathlib import Path


def create_app(config_class=Config):
    """
    Создать и инициализировать Flask приложение
    
    Args:
        config_class: Класс конфигурации
    
    Returns:
        Flask: Настроенное приложение
    """
    app = Flask(__name__)
    
    # Загружаем конфиг
    app.config.from_object(config_class)
    
    # Инициализируем расширения
    db.init_app(app)
    CORS(app)
    
    # Настраиваем логирование
    setup_logging(app)
    
    # Создаем БД при необходимости
    with app.app_context():
        db.create_all()
    
    # Регистрируем API маршруты
    register_routes(app)
    
    # Регистрируем обработчики ошибок
    register_error_handlers(app)
    
    return app


def setup_logging(app):
    """Настроить логирование"""
    if not app.debug:
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        file_handler = logging.FileHandler('logs/promoservice.log')
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)


def register_routes(app):
    """Регистрировать все API маршруты"""
    # Импортируем и регистрируем blueprints
    from backend.api.clients import clients_bp
    from backend.api.equipment import equipment_bp
    from backend.api.warehouse import warehouse_bp
    from backend.api.employees import employees_bp
    from backend.api.services_logging import services_bp, logging_bp
    from backend.api.users import users_bp
    
    app.register_blueprint(clients_bp)
    app.register_blueprint(equipment_bp)
    app.register_blueprint(warehouse_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(services_bp)
    app.register_blueprint(logging_bp)
    app.register_blueprint(users_bp)
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Проверка здоровья API"""
        return jsonify({
            'status': 'ok',
            'message': 'PromoService API работает'
        }), 200
    
    @app.route('/api/auth/login', methods=['POST'])
    def login():
        """
        Вход пользователя
        
        JSON:
            username: Имя пользователя
            password: Пароль
        """
        from flask import request
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'message': 'Username и password требуются'}), 400
        
        success, result, user = AuthManager.authenticate_user(
            data['username'],
            data['password']
        )
        
        if not success:
            return jsonify({'message': result}), 401
        
        return jsonify({
            'message': 'Вход успешен',
            'token': result,
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role
            }
        }), 200
    
    @app.route('/api/auth/register', methods=['POST'])
    def register():
        """
        Регистрация нового пользователя
        
        JSON:
            username: Имя пользователя
            password: Пароль
            role: Роль (director, manager, employee, warehouse)
        """
        from flask import request
        from backend.auth import token_required, role_required
        
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'message': 'Username и password требуются'}), 400
        
        success, result = AuthManager.create_user(
            data['username'],
            data['password'],
            data.get('role', 'employee')
        )
        
        if not success:
            return jsonify({'message': result}), 409
        
        return jsonify({
            'message': 'Пользователь создан',
            'user': {
                'id': result.id,
                'username': result.username,
                'role': result.role
            }
        }), 201
    
    # Инициализируем API endpoints для остальных модулей
    init_api_routes(app)


def init_api_routes(app):
    """Инициализировать API маршруты для всех модулей"""
    from flask import jsonify
    pass  # API маршруты теперь зарегистрированы через blueprints


def register_error_handlers(app):
    """Регистрировать обработчики ошибок"""
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'message': 'Маршрут не найден'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'message': 'Внутренняя ошибка сервера'}), 500
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'message': 'Доступ запрещен'}), 403


if __name__ == '__main__':
    app = create_app()
    app.run(
        host=Config.API_HOST,
        port=Config.API_PORT,
        debug=Config.DEBUG
    )
