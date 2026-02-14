"""
Модуль аутентификации и авторизации
Работа с JWT токенами и паролями
"""
import bcrypt
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from config import Config
from database.models import User, db


class AuthManager:
    """Менеджер аутентификации"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Хешировать пароль
        
        Args:
            password: Пароль в открытом виде
        
        Returns:
            str: Хеш пароля
        """
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        Проверить пароль
        
        Args:
            password: Пароль в открытом виде
            password_hash: Хеш пароля
        
        Returns:
            bool: Корректен ли пароль
        """
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception:
            return False
    
    @staticmethod
    def generate_token(user_id: int, username: str, role: str) -> str:
        """
        Генерировать JWT токен
        
        Args:
            user_id: ID пользователя
            username: Имя пользователя
            role: Роль пользователя
        
        Returns:
            str: JWT токен
        """
        payload = {
            'id': user_id,
            'user_id': user_id,
            'username': username,
            'role': role,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + Config.JWT_EXPIRATION_DELTA
        }
        
        token = jwt.encode(
            payload,
            Config.JWT_SECRET_KEY,
            algorithm=Config.JWT_ALGORITHM
        )
        return token
    
    @staticmethod
    def verify_token(token: str) -> dict:
        """
        Проверить JWT токен
        
        Args:
            token: JWT токен
        
        Returns:
            dict: Данные из токена или None если токен невалиден
        """
        try:
            payload = jwt.decode(
                token,
                Config.JWT_SECRET_KEY,
                algorithms=[Config.JWT_ALGORITHM]
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    @staticmethod
    def authenticate_user(username: str, password: str) -> tuple:
        """
        Аутентифицировать пользователя по логину и паролю
        
        Args:
            username: Имя пользователя
            password: Пароль
        
        Returns:
            tuple: (успешность, токен или сообщение об ошибке, пользователь)
        """
        user = User.query.filter_by(username=username).first()
        
        if not user:
            return False, "Пользователь не найден", None
        
        if not AuthManager.verify_password(password, user.password_hash):
            return False, "Неверный пароль", None
        
        # Генерируем токен
        token = AuthManager.generate_token(user.id, user.username, user.role)
        
        # Сохраняем токен в БД
        user.token = token
        db.session.commit()
        
        return True, token, user
    
    @staticmethod
    def create_user(username: str, password: str, role: str = 'employee') -> tuple:
        """
        Создать нового пользователя
        
        Args:
            username: Имя пользователя
            password: Пароль
            role: Роль (director, manager, employee, warehouse)
        
        Returns:
            tuple: (успешность, пользователь или сообщение об ошибке)
        """
        # Проверяем существует ли уже такой пользователь
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return False, "Пользователь с таким именем уже существует"
        
        # Хешируем пароль
        password_hash = AuthManager.hash_password(password)
        
        # Создаем пользователя
        user = User(
            username=username,
            password_hash=password_hash,
            role=role
        )
        
        db.session.add(user)
        db.session.commit()
        
        return True, user
    
    @staticmethod
    def change_password(user_id: int, old_password: str, new_password: str) -> tuple:
        """
        Изменить пароль пользователя
        
        Args:
            user_id: ID пользователя
            old_password: Старый пароль
            new_password: Новый пароль
        
        Returns:
            tuple: (успешность, сообщение)
        """
        user = User.query.get(user_id)
        
        if not user:
            return False, "Пользователь не найден"
        
        if not AuthManager.verify_password(old_password, user.password_hash):
            return False, "Неверный старый пароль"
        
        # Устанавливаем новый пароль
        user.password_hash = AuthManager.hash_password(new_password)
        db.session.commit()
        
        return True, "Пароль успешно изменен"


def token_required(f):
    """
    Декоратор для проверки токена в API запросах
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Получаем токен из заголовка Authorization
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Неверный формат токена'}), 401
        
        if not token:
            return jsonify({'message': 'Токен отсутствует'}), 401
        
        # Проверяем токен
        payload = AuthManager.verify_token(token)
        
        if not payload:
            return jsonify({'message': 'Невалидный или истекший токен'}), 401
        
        # Создаем объект для совместимости с .id и .role доступом
        class TokenUser:
            def __init__(self, data):
                self.id = data.get('id') or data.get('user_id')
                self.user_id = data.get('user_id') or data.get('id')
                self.username = data.get('username')
                self.role = data.get('role')
                self._data = data
            
            def __getitem__(self, key):
                return self._data.get(key)
        
        current_user = TokenUser(payload)
        
        # Сохраняем в request для совместимости
        request.current_user = current_user
        
        # Проверяем, принимает ли функция current_user как параметр
        import inspect
        sig = inspect.signature(f)
        if 'current_user' in sig.parameters:
            return f(current_user, *args, **kwargs)
        else:
            return f(*args, **kwargs)
    
    return decorated


def role_required(required_role: str):
    """
    Декоратор для проверки роли пользователя
    
    Args:
        required_role: Требуемая роль (director, manager, employee, warehouse)
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Получаем роль из текущего пользователя
            user_role = getattr(request, 'current_user', {}).get('role')
            
            # Проверяем иерархию ролей
            role_levels = {
                'director': 4,
                'manager': 3,
                'employee': 2,
                'warehouse': 1
            }
            
            required_level = role_levels.get(required_role, 0)
            user_level = role_levels.get(user_role, 0)
            
            if user_level < required_level:
                return jsonify({'message': 'Недостаточно прав доступа'}), 403
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator
