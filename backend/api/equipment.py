"""
Equipment CRUD API endpoints
Обеспечивает управление оборудованием: получение, создание, обновление, удаление
"""

from flask import Blueprint, request, jsonify
from database.models import db, Equipment, OperationLog
from backend.auth import token_required
from datetime import datetime
import logging

# Создаем blueprint
equipment_bp = Blueprint('equipment', __name__, url_prefix='/api/equipment')

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
        # Не прерываем основную операцию, даже если логирование не удалось


@equipment_bp.route('', methods=['GET'])
@token_required
def get_equipment_list(current_user):
    """
    Получить список оборудования с опциональной фильтрацией и поиском
    
    Query parameters:
        - search: поиск по названию или типу (case-insensitive)
        - type: фильтр по типу оборудования
        - status: фильтр по статусу
        - limit: количество записей на странице (по умолчанию 50)
        - offset: смещение для пагинации (по умолчанию 0)
    
    Returns:
        JSON с списком оборудования и метаданными пагинации
    """
    try:
        # Получаем параметры из query string
        search = request.args.get('search', '').strip()
        equipment_type = request.args.get('type', '').strip()
        status = request.args.get('status', '').strip()
        
        try:
            limit = min(int(request.args.get('limit', 50)), 500)
            offset = int(request.args.get('offset', 0))
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid limit or offset values'
            }), 400
        
        # Начинаем с базового query
        query = Equipment.query
        
        # Применяем фильтры
        if search:
            query = query.filter(
                db.or_(
                    Equipment.name.ilike(f'%{search}%'),
                    Equipment.equipment_type.ilike(f'%{search}%')
                )
            )
        
        if equipment_type:
            query = query.filter(Equipment.equipment_type.ilike(f'%{equipment_type}%'))
        
        if status:
            query = query.filter(Equipment.status == status)
        
        # Получаем общее количество записей
        total = query.count()
        
        # Применяем пагинацию
        equipment_list = query.offset(offset).limit(limit).all()
        
        # Логируем операцию чтения
        log_operation(
            current_user.id,
            'READ',
            'equipment',
            None,
            f'Listed {len(equipment_list)} equipment records'
        )
        
        return jsonify({
            'success': True,
            'data': [item.to_dict() for item in equipment_list],
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset,
                'count': len(equipment_list)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting equipment list: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@equipment_bp.route('/<int:equipment_id>', methods=['GET'])
@token_required
def get_equipment(current_user, equipment_id):
    """
    Получить информацию об одном оборудовании по ID
    
    Args:
        equipment_id: ID оборудования
    
    Returns:
        JSON с информацией об оборудовании или ошибка 404
    """
    try:
        equipment = Equipment.query.get(equipment_id)
        
        if not equipment:
            return jsonify({
                'success': False,
                'message': 'Equipment not found'
            }), 404
        
        # Логируем операцию чтения
        log_operation(current_user.id, 'READ', 'equipment', equipment_id)
        
        return jsonify({
            'success': True,
            'data': equipment.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting equipment: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@equipment_bp.route('', methods=['POST'])
@token_required
def create_equipment(current_user):
    """
    Создать новое оборудование
    
    JSON Body:
        - name (required): название оборудования
        - equipment_type (required): тип оборудования
        - model (optional): модель
        - serial_number (optional): серийный номер
        - purchase_date (optional): дата покупки (YYYY-MM-DD)
        - status (optional): статус (defaults to 'active')
        - location (optional): расположение
        - notes (optional): заметки
    
    Returns:
        JSON с информацией о созданном оборудовании или ошибка
    """
    try:
        data = request.get_json()
        
        # Валидация требуемых полей
        if not data.get('name'):
            return jsonify({
                'success': False,
                'message': 'Equipment name is required'
            }), 400
        
        if not data.get('equipment_type'):
            return jsonify({
                'success': False,
                'message': 'Equipment type is required'
            }), 400
        
        # Проверяем дубликаты (по названию и типу)
        existing = Equipment.query.filter(
            db.and_(
                Equipment.name.ilike(data['name'].strip()),
                Equipment.equipment_type.ilike(data['equipment_type'].strip())
            )
        ).first()
        
        if existing:
            return jsonify({
                'success': False,
                'message': 'Equipment with this name and type already exists'
            }), 409
        
        # Создаем новое оборудование
        new_equipment = Equipment(
            name=data['name'].strip(),
            equipment_type=data['equipment_type'].strip(),
            model=data.get('model', '').strip() or None,
            serial_number=data.get('serial_number', '').strip() or None,
            purchase_date=data.get('purchase_date'),
            status=data.get('status', 'active').strip(),
            location=data.get('location', '').strip() or None,
            notes=data.get('notes', '').strip() or None,
            created_at=datetime.utcnow()
        )
        
        db.session.add(new_equipment)
        db.session.commit()
        
        # Логируем операцию создания
        log_operation(
            current_user.id,
            'CREATE',
            'equipment',
            new_equipment.id,
            f'Created equipment: {new_equipment.name}'
        )
        
        return jsonify({
            'success': True,
            'message': 'Equipment created successfully',
            'data': new_equipment.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating equipment: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@equipment_bp.route('/<int:equipment_id>', methods=['PUT'])
@token_required
def update_equipment(current_user, equipment_id):
    """
    Обновить информацию об оборудовании (частичное обновление)
    
    Args:
        equipment_id: ID оборудования
    
    JSON Body:
        Любые из полей: name, equipment_type, model, serial_number, 
        purchase_date, status, location, notes
    
    Returns:
        JSON с обновленной информацией об оборудовании или ошибка
    """
    try:
        equipment = Equipment.query.get(equipment_id)
        
        if not equipment:
            return jsonify({
                'success': False,
                'message': 'Equipment not found'
            }), 404
        
        data = request.get_json()
        
        # Если обновляем name и equipment_type, проверяем дубликаты
        if 'name' in data or 'equipment_type' in data:
            new_name = data.get('name', equipment.name).strip()
            new_type = data.get('equipment_type', equipment.equipment_type).strip()
            
            existing = Equipment.query.filter(
                db.and_(
                    Equipment.id != equipment_id,
                    Equipment.name.ilike(new_name),
                    Equipment.equipment_type.ilike(new_type)
                )
            ).first()
            
            if existing:
                return jsonify({
                    'success': False,
                    'message': 'Equipment with this name and type already exists'
                }), 409
        
        # Обновляем поля
        if 'name' in data:
            equipment.name = data['name'].strip()
        if 'equipment_type' in data:
            equipment.equipment_type = data['equipment_type'].strip()
        if 'model' in data:
            equipment.model = data['model'].strip() or None
        if 'serial_number' in data:
            equipment.serial_number = data['serial_number'].strip() or None
        if 'purchase_date' in data:
            equipment.purchase_date = data['purchase_date']
        if 'status' in data:
            equipment.status = data['status'].strip()
        if 'location' in data:
            equipment.location = data['location'].strip() or None
        if 'notes' in data:
            equipment.notes = data['notes'].strip() or None
        
        equipment.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Логируем операцию обновления
        log_operation(
            current_user.id,
            'UPDATE',
            'equipment',
            equipment_id,
            f'Updated equipment: {equipment.name}'
        )
        
        return jsonify({
            'success': True,
            'message': 'Equipment updated successfully',
            'data': equipment.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating equipment: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@equipment_bp.route('/<int:equipment_id>', methods=['DELETE'])
@token_required
def delete_equipment(current_user, equipment_id):
    """
    Удалить оборудование (требует роль 'manager' или 'admin')
    
    Args:
        equipment_id: ID оборудования
    
    Returns:
        JSON с подтверждением удаления или ошибка
    """
    try:
        # Проверяем разрешение (только менеджеры и администраторы)
        if current_user.role not in ['manager', 'admin']:
            return jsonify({
                'success': False,
                'message': 'Insufficient permissions to delete equipment'
            }), 403
        
        equipment = Equipment.query.get(equipment_id)
        
        if not equipment:
            return jsonify({
                'success': False,
                'message': 'Equipment not found'
            }), 404
        
        equipment_name = equipment.name
        
        db.session.delete(equipment)
        db.session.commit()
        
        # Логируем операцию удаления
        log_operation(
            current_user.id,
            'DELETE',
            'equipment',
            equipment_id,
            f'Deleted equipment: {equipment_name}'
        )
        
        return jsonify({
            'success': True,
            'message': 'Equipment deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting equipment: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500
