"""
User management API endpoints
Обеспечивает управление пользователями системы
"""

from flask import Blueprint, request, jsonify
from database.models import db, User
from backend.auth import token_required
from datetime import datetime
import logging

# Создаем blueprint
users_bp = Blueprint('users', __name__, url_prefix='/api/users')

logger = logging.getLogger(__name__)


@users_bp.route('', methods=['GET'])
@token_required
def get_users_list(current_user):
    """
    Получить список пользователей
    
    Query parameters:
        - search: поиск по имени пользователя
        - role: фильтр по роли
        - limit: количество записей
        - offset: смещение
    
    Returns:
        JSON с списком пользователей
    """
    try:
        search = request.args.get('search', '').strip()
        role = request.args.get('role', '').strip()
        
        try:
            limit = min(int(request.args.get('limit', 50)), 500)
            offset = int(request.args.get('offset', 0))
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid limit or offset values'
            }), 400
        
        query = User.query
        
        if search:
            query = query.filter(User.username.ilike(f'%{search}%'))
        
        if role:
            query = query.filter(User.role == role)
        
        total = query.count()
        users_list = query.offset(offset).limit(limit).all()
        
        return jsonify({
            'success': True,
            'data': [user.to_dict() for user in users_list],
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset,
                'count': len(users_list)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting users list: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@users_bp.route('/<int:user_id>', methods=['GET'])
@token_required
def get_user(current_user, user_id):
    """
    Получить информацию о пользователе по ID
    """
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@users_bp.route('', methods=['POST'])
@token_required
def create_user(current_user):
    """
    Создать нового пользователя (только для director/manager)
    
    JSON Body:
        - username (required): имя пользователя
        - password (required): пароль
        - role (optional): роль (по умолчанию 'employee')
        - email (optional): email
    """
    try:
        # Проверяем права доступа
        if current_user.role not in ['director', 'manager', 'admin']:
            return jsonify({
                'success': False,
                'message': 'Insufficient permissions'
            }), 403
        
        data = request.get_json()
        
        # Валидация
        if not data.get('username'):
            return jsonify({
                'success': False,
                'message': 'Username is required'
            }), 400
        
        if not data.get('password'):
            return jsonify({
                'success': False,
                'message': 'Password is required'
            }), 400
        
        # Проверяем существующего пользователя
        existing = User.query.filter_by(username=data['username']).first()
        if existing:
            return jsonify({
                'success': False,
                'message': 'Username already exists'
            }), 409
        
        # Хешируем пароль
        from backend.auth import AuthManager
        password_hash = AuthManager.hash_password(data['password'])
        
        # Создаем пользователя
        new_user = User(
            username=data['username'].strip(),
            password_hash=password_hash,
            role=data.get('role', 'employee'),
            created_at=datetime.utcnow()
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'User created successfully',
            'data': new_user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating user: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@users_bp.route('/<int:user_id>', methods=['PUT'])
@token_required
def update_user(current_user, user_id):
    """
    Обновить пользователя (только для director/manager или самого себя)
    
    JSON Body:
        - password (optional): новый пароль
        - role (optional): роль
    """
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Проверяем права доступа - director/manager могут редактировать любого, обычный пользователь только себя
        if current_user.role not in ['director', 'manager', 'admin'] and current_user.id != user_id:
            return jsonify({
                'success': False,
                'message': 'Insufficient permissions'
            }), 403
        
        data = request.get_json()
        
        # Обновляем роль (только director/manager)
        if 'role' in data and current_user.role in ['director', 'manager', 'admin']:
            user.role = data['role']
        
        # Обновляем пароль
        if 'password' in data and data['password']:
            from backend.auth import AuthManager
            user.password_hash = AuthManager.hash_password(data['password'])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'User updated successfully',
            'data': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating user: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@users_bp.route('/<int:user_id>', methods=['DELETE'])
@token_required
def delete_user(current_user, user_id):
    """
    Удалить пользователя (только для director)
    """
    try:
        # Только director может удалять пользователей
        if current_user.role not in ['director', 'admin']:
            return jsonify({
                'success': False,
                'message': 'Insufficient permissions'
            }), 403
        
        # Нельзя удалить самого себя
        if current_user.id == user_id:
            return jsonify({
                'success': False,
                'message': 'Cannot delete yourself'
            }), 400
        
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        username = user.username
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'User {username} deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting user: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500
