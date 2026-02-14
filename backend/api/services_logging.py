"""
Services and Operation Logging API endpoints
Обеспечивает управление услугами и просмотр логов операций
"""

from flask import Blueprint, request, jsonify
from database.models import db, Service, OperationLog
from backend.auth import token_required
from datetime import datetime
import logging

# Создаем blueprints
services_bp = Blueprint('services', __name__, url_prefix='/api/services')
logging_bp = Blueprint('logs', __name__, url_prefix='/api/logs')

logger = logging.getLogger(__name__)


def log_operation(user_id, operation_type, table_name, record_id, details=None):
    """
    Логирует операцию в таблицу операций
    
    Args:
        user_id: ID пользователя, выполнившего операцию
        operation_type: Тип операции (CREATE, READ, UPDATE, DELETE)
        table_name: Название таблицы
        record_id: ID записи
        details: Дополнительные детали операции
    """
    try:
        log_entry = OperationLog(
            user_id=user_id,
            operation_type=operation_type,
            table_name=table_name,
            record_id=record_id,
            details=details,
            timestamp=datetime.utcnow()
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        logger.error(f"Error logging operation: {str(e)}")


# ==================== SERVICES ENDPOINTS ====================

@services_bp.route('', methods=['GET'])
@token_required
def get_services_list(current_user):
    """
    Получить список услуг с опциональной фильтрацией и поиском
    
    Query parameters:
        - search: поиск по названию услуги (case-insensitive)
        - category: фильтр по категории
        - limit: количество записей на странице (по умолчанию 50)
        - offset: смещение для пагинации (по умолчанию 0)
    
    Returns:
        JSON с списком услуг и метаданными пагинации
    """
    try:
        search = request.args.get('search', '').strip()
        category = request.args.get('category', '').strip()
        
        try:
            limit = min(int(request.args.get('limit', 50)), 500)
            offset = int(request.args.get('offset', 0))
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid limit or offset values'
            }), 400
        
        query = Service.query
        
        if search:
            query = query.filter(Service.name.ilike(f'%{search}%'))
        
        if category:
            query = query.filter(Service.category.ilike(f'%{category}%'))
        
        total = query.count()
        services_list = query.offset(offset).limit(limit).all()
        
        log_operation(
            current_user.id,
            'READ',
            'service',
            None,
            f'Listed {len(services_list)} services'
        )
        
        return jsonify({
            'success': True,
            'data': [svc.to_dict() for svc in services_list],
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset,
                'count': len(services_list)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting services list: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@services_bp.route('/<int:service_id>', methods=['GET'])
@token_required
def get_service(current_user, service_id):
    """
    Получить информацию об одной услуге по ID
    """
    try:
        service = Service.query.get(service_id)
        
        if not service:
            return jsonify({
                'success': False,
                'message': 'Service not found'
            }), 404
        
        log_operation(current_user.id, 'READ', 'service', service_id)
        
        return jsonify({
            'success': True,
            'data': service.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting service: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@services_bp.route('', methods=['POST'])
@token_required
def create_service(current_user):
    """
    Создать новую услугу
    
    JSON Body:
        - name (required): название услуги
        - category (required): категория услуги
        - price (optional): цена услуги
        - description (optional): описание
        - duration_minutes (optional): длительность в минутах
        - notes (optional): заметки
    
    Returns:
        JSON с информацией о созданной услуге или ошибка
    """
    try:
        data = request.get_json()
        
        if not data.get('name'):
            return jsonify({
                'success': False,
                'message': 'Service name is required'
            }), 400
        
        if not data.get('category'):
            return jsonify({
                'success': False,
                'message': 'Service category is required'
            }), 400
        
        # Проверяем дубликаты
        existing = Service.query.filter(
            db.and_(
                Service.name.ilike(data['name'].strip()),
                Service.category.ilike(data['category'].strip())
            )
        ).first()
        
        if existing:
            return jsonify({
                'success': False,
                'message': 'Service with this name and category already exists'
            }), 409
        
        new_service = Service(
            name=data['name'].strip(),
            category=data['category'].strip(),
            price=float(data.get('price', 0)),
            description=data.get('description', '').strip() or None,
            duration_minutes=int(data.get('duration_minutes', 0)) if data.get('duration_minutes') else None,
            notes=data.get('notes', '').strip() or None,
            created_at=datetime.utcnow()
        )
        
        db.session.add(new_service)
        db.session.commit()
        
        log_operation(
            current_user.id,
            'CREATE',
            'service',
            new_service.id,
            f'Created service: {new_service.name}'
        )
        
        return jsonify({
            'success': True,
            'message': 'Service created successfully',
            'data': new_service.to_dict()
        }), 201
        
    except ValueError:
        return jsonify({
            'success': False,
            'message': 'Invalid price or duration value'
        }), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating service: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@services_bp.route('/<int:service_id>', methods=['PUT'])
@token_required
def update_service(current_user, service_id):
    """
    Обновить информацию об услуге
    """
    try:
        service = Service.query.get(service_id)
        
        if not service:
            return jsonify({
                'success': False,
                'message': 'Service not found'
            }), 404
        
        data = request.get_json()
        
        if any(field in data for field in ['name', 'category']):
            new_name = data.get('name', service.name).strip()
            new_cat = data.get('category', service.category).strip()
            
            existing = Service.query.filter(
                db.and_(
                    Service.id != service_id,
                    Service.name.ilike(new_name),
                    Service.category.ilike(new_cat)
                )
            ).first()
            
            if existing:
                return jsonify({
                    'success': False,
                    'message': 'Service with this name and category already exists'
                }), 409
        
        if 'name' in data:
            service.name = data['name'].strip()
        if 'category' in data:
            service.category = data['category'].strip()
        if 'price' in data:
            service.price = float(data['price'])
        if 'description' in data:
            service.description = data['description'].strip() or None
        if 'duration_minutes' in data:
            service.duration_minutes = int(data['duration_minutes']) if data['duration_minutes'] else None
        if 'notes' in data:
            service.notes = data['notes'].strip() or None
        
        service.updated_at = datetime.utcnow()
        db.session.commit()
        
        log_operation(
            current_user.id,
            'UPDATE',
            'service',
            service_id,
            f'Updated service: {service.name}'
        )
        
        return jsonify({
            'success': True,
            'message': 'Service updated successfully',
            'data': service.to_dict()
        }), 200
        
    except ValueError:
        return jsonify({
            'success': False,
            'message': 'Invalid price or duration value'
        }), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating service: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@services_bp.route('/<int:service_id>', methods=['DELETE'])
@token_required
def delete_service(current_user, service_id):
    """
    Удалить услугу (требует роль 'manager' или 'admin')
    """
    try:
        if current_user.role not in ['manager', 'admin']:
            return jsonify({
                'success': False,
                'message': 'Insufficient permissions to delete services'
            }), 403
        
        service = Service.query.get(service_id)
        
        if not service:
            return jsonify({
                'success': False,
                'message': 'Service not found'
            }), 404
        
        service_name = service.name
        db.session.delete(service)
        db.session.commit()
        
        log_operation(
            current_user.id,
            'DELETE',
            'service',
            service_id,
            f'Deleted service: {service_name}'
        )
        
        return jsonify({
            'success': True,
            'message': 'Service deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting service: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


# ==================== OPERATION LOGGING ENDPOINTS ====================

@logging_bp.route('', methods=['GET'])
@token_required
def get_operation_logs(current_user):
    """
    Получить логи операций с опциональной фильтрацией
    
    Query parameters:
        - operation_type: фильтр по типу операции (CREATE, READ, UPDATE, DELETE)
        - table_name: фильтр по названию таблицы
        - user_id: фильтр по ID пользователя
        - start_date: фильтр по начальной дате (YYYY-MM-DD HH:MM:SS)
        - end_date: фильтр по конечной дате (YYYY-MM-DD HH:MM:SS)
        - limit: количество записей на странице (по умолчанию 50)
        - offset: смещение для пагинации (по умолчанию 0)
    
    Returns:
        JSON со списком логов и метаданными пагинации
    """
    try:
        operation_type = request.args.get('operation_type', '').strip()
        table_name = request.args.get('table_name', '').strip()
        user_id = request.args.get('user_id', '').strip()
        start_date = request.args.get('start_date', '').strip()
        end_date = request.args.get('end_date', '').strip()
        
        try:
            limit = min(int(request.args.get('limit', 50)), 500)
            offset = int(request.args.get('offset', 0))
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid limit or offset values'
            }), 400
        
        query = OperationLog.query
        
        if operation_type:
            query = query.filter(OperationLog.operation_type == operation_type)
        
        if table_name:
            query = query.filter(OperationLog.table_name == table_name)
        
        if user_id:
            try:
                query = query.filter(OperationLog.user_id == int(user_id))
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Invalid user_id'
                }), 400
        
        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
                query = query.filter(OperationLog.timestamp >= start)
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Invalid start_date format (use YYYY-MM-DD HH:MM:SS)'
                }), 400
        
        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
                query = query.filter(OperationLog.timestamp <= end)
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Invalid end_date format (use YYYY-MM-DD HH:MM:SS)'
                }), 400
        
        # Сортируем по времени (новые первыми)
        query = query.order_by(OperationLog.timestamp.desc())
        
        total = query.count()
        logs = query.offset(offset).limit(limit).all()
        
        return jsonify({
            'success': True,
            'data': [log.to_dict() for log in logs],
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset,
                'count': len(logs)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting operation logs: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@logging_bp.route('/user/<int:user_id>', methods=['GET'])
@token_required
def get_user_operations(current_user, user_id):
    """
    Получить все операции конкретного пользователя
    
    Query parameters:
        - limit: количество записей на странице (по умолчанию 50)
        - offset: смещение для пагинации (по умолчанию 0)
    
    Returns:
        JSON со списком операций пользователя
    """
    try:
        try:
            limit = min(int(request.args.get('limit', 50)), 500)
            offset = int(request.args.get('offset', 0))
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid limit or offset values'
            }), 400
        
        query = OperationLog.query.filter(OperationLog.user_id == user_id)
        query = query.order_by(OperationLog.timestamp.desc())
        
        total = query.count()
        logs = query.offset(offset).limit(limit).all()
        
        return jsonify({
            'success': True,
            'data': [log.to_dict() for log in logs],
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset,
                'count': len(logs)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user operations: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@logging_bp.route('/table/<string:table_name>', methods=['GET'])
@token_required
def get_table_operations(current_user, table_name):
    """
    Получить все операции для конкретной таблицы
    
    Query parameters:
        - limit: количество записей на странице (по умолчанию 50)
        - offset: смещение для пагинации (по умолчанию 0)
    
    Returns:
        JSON со списком операций для таблицы
    """
    try:
        try:
            limit = min(int(request.args.get('limit', 50)), 500)
            offset = int(request.args.get('offset', 0))
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid limit or offset values'
            }), 400
        
        query = OperationLog.query.filter(OperationLog.table_name == table_name)
        query = query.order_by(OperationLog.timestamp.desc())
        
        total = query.count()
        logs = query.offset(offset).limit(limit).all()
        
        return jsonify({
            'success': True,
            'data': [log.to_dict() for log in logs],
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset,
                'count': len(logs)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting table operations: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@logging_bp.route('/stats', methods=['GET'])
@token_required
def get_operation_stats(current_user):
    """
    Получить статистику по операциям
    
    Returns:
        JSON со статистикой по типам операций и таблицам
    """
    try:
        # Статистика по типам операций
        stats_by_type = db.session.query(
            OperationLog.operation_type,
            db.func.count(OperationLog.id).label('count')
        ).group_by(OperationLog.operation_type).all()
        
        # Статистика по таблицам
        stats_by_table = db.session.query(
            OperationLog.table_name,
            db.func.count(OperationLog.id).label('count')
        ).group_by(OperationLog.table_name).all()
        
        return jsonify({
            'success': True,
            'data': {
                'by_operation_type': {
                    op_type: count for op_type, count in stats_by_type
                },
                'by_table': {
                    table: count for table, count in stats_by_table
                },
                'total_operations': db.session.query(db.func.count(OperationLog.id)).scalar()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting operation stats: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500
