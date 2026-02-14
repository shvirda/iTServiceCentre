"""
API endpoints для управления клиентами
"""
from flask import Blueprint, request, jsonify
from database.models import db, Client, OperationLog
from backend.auth import token_required, role_required
from datetime import datetime

clients_bp = Blueprint('clients', __name__, url_prefix='/api/clients')


@clients_bp.route('', methods=['GET'])
@token_required
def get_clients():
    """
    Получить список клиентов с опциональной фильтрацией
    
    Query params:
        search: Строка поиска
        phone: Фильтр по телефону
        limit: Ограничение на количество результатов (по умолчанию 100)
        offset: Смещение (по умолчанию 0)
    """
    try:
        # Параметры запроса
        search = request.args.get('search', '').lower()
        phone = request.args.get('phone', '')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # Начальный запрос
        query = Client.query
        
        # Фильтр по поиску
        if search:
            query = query.filter(
                db.or_(
                    Client.full_name.ilike(f'%{search}%'),
                    Client.phone.ilike(f'%{search}%'),
                    Client.address.ilike(f'%{search}%'),
                    Client.social_media.ilike(f'%{search}%')
                )
            )
        
        # Фильтр по телефону
        if phone:
            query = query.filter(Client.phone.ilike(f'%{phone}%'))
        
        # Подсчет всего
        total = query.count()
        
        # Получаем данные с лимитом и смещением
        clients = query.order_by(Client.id.desc()).limit(limit).offset(offset).all()
        
        # Формируем ответ
        data = [{
            'id': client.id,
            'full_name': client.full_name,
            'phone': client.phone,
            'address': client.address,
            'social_media': client.social_media,
            'email': client.email,
            'notes': client.notes,
            'created_at': client.created_at.isoformat() if client.created_at else None
        } for client in clients]
        
        return jsonify({
            'success': True,
            'data': data,
            'total': total,
            'limit': limit,
            'offset': offset
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении клиентов: {str(e)}'
        }), 500


@clients_bp.route('/<int:client_id>', methods=['GET'])
@token_required
def get_client(client_id):
    """Получить клиента по ID"""
    try:
        client = Client.query.get(client_id)
        
        if not client:
            return jsonify({
                'success': False,
                'message': 'Клиент не найден'
            }), 404
        
        return jsonify({
            'success': True,
            'data': {
                'id': client.id,
                'full_name': client.full_name,
                'phone': client.phone,
                'address': client.address,
                'social_media': client.social_media,
                'email': client.email,
                'notes': client.notes,
                'created_at': client.created_at.isoformat() if client.created_at else None
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении клиента: {str(e)}'
        }), 500


@clients_bp.route('', methods=['POST'])
@token_required
def create_client():
    """
    Создать нового клиента
    
    JSON:
        full_name: ФИО клиента (обязательно)
        phone: Номер телефона (обязательно)
        address: Адрес (опционально)
        social_media: Соцсети (опционально)
    """
    try:
        data = request.get_json()
        
        # Валидация
        if not data.get('full_name') or not data.get('phone'):
            return jsonify({
                'success': False,
                'message': 'ФИО и телефон обязательны'
            }), 400
        
        # Проверка на дублирование
        existing = Client.query.filter_by(phone=data['phone']).first()
        if existing:
            return jsonify({
                'success': False,
                'message': 'Клиент с этим номером уже существует'
            }), 409
        
        # Создаем клиента
        client = Client(
            full_name=data['full_name'],
            phone=data['phone'],
            address=data.get('address', ''),
            social_media=data.get('social_media', ''),
            notes=data.get('notes', ''),
            email=data.get('email', '')
        )
        
        db.session.add(client)
        db.session.commit()
        
        # Логирование
        log_operation(request, 'create', 'clients', client.id)
        
        return jsonify({
            'success': True,
            'message': 'Клиент успешно создан',
            'data': {
                'id': client.id,
                'full_name': client.full_name,
                'phone': client.phone,
                'address': client.address,
                'social_media': client.social_media,
                'email': client.email,
                'notes': client.notes
            }
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Ошибка при создании клиента: {str(e)}'
        }), 500


@clients_bp.route('/<int:client_id>', methods=['PUT'])
@token_required
def update_client(client_id):
    """
    Обновить данные клиента
    
    JSON:
        full_name: ФИО (опционально)
        phone: Телефон (опционально)
        address: Адрес (опционально)
        social_media: Соцсети (опционально)
    """
    try:
        client = Client.query.get(client_id)
        
        if not client:
            return jsonify({
                'success': False,
                'message': 'Клиент не найден'
            }), 404
        
        data = request.get_json()
        
        # Обновляем данные
        if 'full_name' in data:
            client.full_name = data['full_name']
        if 'phone' in data:
            # Проверка на дублирование
            existing = Client.query.filter(
                Client.phone == data['phone'],
                Client.id != client_id
            ).first()
            if existing:
                return jsonify({
                    'success': False,
                    'message': 'Клиент с этим номером уже существует'
                }), 409
            client.phone = data['phone']
        if 'address' in data:
            client.address = data['address']
        if 'social_media' in data:
            client.social_media = data['social_media']
        if 'email' in data:
            client.email = data['email']
        if 'notes' in data:
            client.notes = data['notes']
        
        db.session.commit()
        
        # Логирование
        log_operation(request, 'update', 'clients', client_id)
        
        return jsonify({
            'success': True,
            'message': 'Клиент успешно обновлен',
            'data': {
                'id': client.id,
                'full_name': client.full_name,
                'phone': client.phone,
                'address': client.address,
                'social_media': client.social_media,
                'email': client.email,
                'notes': client.notes
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Ошибка при обновлении клиента: {str(e)}'
        }), 500


@clients_bp.route('/<int:client_id>', methods=['DELETE'])
@token_required
@role_required('manager')
def delete_client(client_id):
    """Удалить клиента"""
    try:
        client = Client.query.get(client_id)
        
        if not client:
            return jsonify({
                'success': False,
                'message': 'Клиент не найден'
            }), 404
        
        # Логирование перед удалением
        log_operation(request, 'delete', 'clients', client_id)
        
        db.session.delete(client)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Клиент успешно удален'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Ошибка при удалении клиента: {str(e)}'
        }), 500


def log_operation(request, operation_type, table_name, record_id):
    """Вспомогательная функция для логирования операций"""
    try:
        user_id = getattr(request, 'current_user', {}).id
        
        if user_id:
            log = OperationLog(
                user_id=user_id,
                operation_type=operation_type,
                table_name=table_name,
                record_id=record_id,
                details=f'{operation_type} record in {table_name}'
            )
            
            db.session.add(log)
            db.session.commit()
    except Exception as e:
        # Silently fail logging to not disrupt main operation
        pass
