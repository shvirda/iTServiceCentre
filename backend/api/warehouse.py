"""
Warehouse CRUD API endpoints
Обеспечивает управление товарами на складе: получение, создание, обновление, удаление
"""

from flask import Blueprint, request, jsonify
from database.models import db, Warehouse, OperationLog
from backend.auth import token_required
from datetime import datetime
import logging

# Создаем blueprint
warehouse_bp = Blueprint('warehouse', __name__, url_prefix='/api/warehouse')

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


@warehouse_bp.route('', methods=['GET'])
@token_required
def get_warehouse_list(current_user):
    """
    Получить список товаров на складе с опциональной фильтрацией и поиском
    
    Query parameters:
        - search: поиск по названию товара или артикулу (case-insensitive)
        - category: фильтр по категории товара
        - min_quantity: минимальное количество на складе
        - limit: количество записей на странице (по умолчанию 50)
        - offset: смещение для пагинации (по умолчанию 0)
    
    Returns:
        JSON с списком товаров и метаданными пагинации
    """
    try:
        # Получаем параметры из query string
        search = request.args.get('search', '').strip()
        category = request.args.get('category', '').strip()
        
        try:
            min_quantity = int(request.args.get('min_quantity', 0))
            limit = min(int(request.args.get('limit', 50)), 500)
            offset = int(request.args.get('offset', 0))
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid parameter values'
            }), 400
        
        # Начинаем с базового query
        query = Warehouse.query
        
        # Применяем фильтры
        if search:
            query = query.filter(
                db.or_(
                    Warehouse.item_name.ilike(f'%{search}%'),
                    Warehouse.article_number.ilike(f'%{search}%')
                )
            )
        
        if category:
            query = query.filter(Warehouse.category.ilike(f'%{category}%'))
        
        if min_quantity > 0:
            query = query.filter(Warehouse.quantity >= min_quantity)
        
        # Получаем общее количество записей
        total = query.count()
        
        # Применяем пагинацию
        warehouse_list = query.offset(offset).limit(limit).all()
        
        # Логируем операцию чтения
        log_operation(
            current_user.id,
            'READ',
            'warehouse',
            None,
            f'Listed {len(warehouse_list)} warehouse items'
        )
        
        return jsonify({
            'success': True,
            'data': [item.to_dict() for item in warehouse_list],
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset,
                'count': len(warehouse_list)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting warehouse list: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@warehouse_bp.route('/<int:item_id>', methods=['GET'])
@token_required
def get_warehouse_item(current_user, item_id):
    """
    Получить информацию об одном товаре по ID
    
    Args:
        item_id: ID товара на складе
    
    Returns:
        JSON с информацией о товаре или ошибка 404
    """
    try:
        warehouse_item = Warehouse.query.get(item_id)
        
        if not warehouse_item:
            return jsonify({
                'success': False,
                'message': 'Warehouse item not found'
            }), 404
        
        # Логируем операцию чтения
        log_operation(current_user.id, 'READ', 'warehouse', item_id)
        
        return jsonify({
            'success': True,
            'data': warehouse_item.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting warehouse item: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@warehouse_bp.route('', methods=['POST'])
@token_required
def create_warehouse_item(current_user):
    """
    Создать новый товар на складе
    
    JSON Body:
        - item_name (required): название товара
        - article_number (required): артикульный номер
        - category (required): категория товара
        - quantity (required): количество на складе
        - unit_price (optional): цена за единицу
        - location (optional): расположение на складе
        - supplier (optional): поставщик
        - notes (optional): заметки
    
    Returns:
        JSON с информацией о созданном товаре или ошибка
    """
    try:
        data = request.get_json()
        
        # Валидация требуемых полей
        if not data.get('item_name'):
            return jsonify({
                'success': False,
                'message': 'Item name is required'
            }), 400
        
        if not data.get('article_number'):
            return jsonify({
                'success': False,
                'message': 'Article number is required'
            }), 400
        
        if not data.get('category'):
            return jsonify({
                'success': False,
                'message': 'Category is required'
            }), 400
        
        if 'quantity' not in data:
            return jsonify({
                'success': False,
                'message': 'Quantity is required'
            }), 400
        
        # Проверяем дубликаты (по артикульному номеру)
        existing = Warehouse.query.filter(
            Warehouse.article_number.ilike(data['article_number'].strip())
        ).first()
        
        if existing:
            return jsonify({
                'success': False,
                'message': 'Item with this article number already exists'
            }), 409
        
        # Создаем новый товар
        new_item = Warehouse(
            item_name=data['item_name'].strip(),
            article_number=data['article_number'].strip(),
            category=data['category'].strip(),
            quantity=int(data['quantity']),
            unit_price=float(data.get('unit_price', 0)),
            location=data.get('location', '').strip() or None,
            supplier=data.get('supplier', '').strip() or None,
            notes=data.get('notes', '').strip() or None,
            created_at=datetime.utcnow()
        )
        
        db.session.add(new_item)
        db.session.commit()
        
        # Логируем операцию создания
        log_operation(
            current_user.id,
            'CREATE',
            'warehouse',
            new_item.id,
            f'Created warehouse item: {new_item.item_name}'
        )
        
        return jsonify({
            'success': True,
            'message': 'Warehouse item created successfully',
            'data': new_item.to_dict()
        }), 201
        
    except ValueError:
        return jsonify({
            'success': False,
            'message': 'Invalid quantity or price value'
        }), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating warehouse item: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@warehouse_bp.route('/<int:item_id>', methods=['PUT'])
@token_required
def update_warehouse_item(current_user, item_id):
    """
    Обновить информацию о товаре (частичное обновление)
    
    Args:
        item_id: ID товара на складе
    
    JSON Body:
        Любые из полей: item_name, article_number, category, quantity,
        unit_price, location, supplier, notes
    
    Returns:
        JSON с обновленной информацией о товаре или ошибка
    """
    try:
        warehouse_item = Warehouse.query.get(item_id)
        
        if not warehouse_item:
            return jsonify({
                'success': False,
                'message': 'Warehouse item not found'
            }), 404
        
        data = request.get_json()
        
        # Если обновляем артикульный номер, проверяем дубликаты
        if 'article_number' in data:
            new_article = data['article_number'].strip()
            
            existing = Warehouse.query.filter(
                db.and_(
                    Warehouse.id != item_id,
                    Warehouse.article_number.ilike(new_article)
                )
            ).first()
            
            if existing:
                return jsonify({
                    'success': False,
                    'message': 'Item with this article number already exists'
                }), 409
        
        # Обновляем поля
        if 'item_name' in data:
            warehouse_item.item_name = data['item_name'].strip()
        if 'article_number' in data:
            warehouse_item.article_number = data['article_number'].strip()
        if 'category' in data:
            warehouse_item.category = data['category'].strip()
        if 'quantity' in data:
            warehouse_item.quantity = int(data['quantity'])
        if 'unit_price' in data:
            warehouse_item.unit_price = float(data['unit_price'])
        if 'location' in data:
            warehouse_item.location = data['location'].strip() or None
        if 'supplier' in data:
            warehouse_item.supplier = data['supplier'].strip() or None
        if 'notes' in data:
            warehouse_item.notes = data['notes'].strip() or None
        
        warehouse_item.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Логируем операцию обновления
        log_operation(
            current_user.id,
            'UPDATE',
            'warehouse',
            item_id,
            f'Updated warehouse item: {warehouse_item.item_name}'
        )
        
        return jsonify({
            'success': True,
            'message': 'Warehouse item updated successfully',
            'data': warehouse_item.to_dict()
        }), 200
        
    except ValueError:
        return jsonify({
            'success': False,
            'message': 'Invalid quantity or price value'
        }), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating warehouse item: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@warehouse_bp.route('/<int:item_id>', methods=['DELETE'])
@token_required
def delete_warehouse_item(current_user, item_id):
    """
    Удалить товар со склада (требует роль 'manager' или 'admin')
    
    Args:
        item_id: ID товара на складе
    
    Returns:
        JSON с подтверждением удаления или ошибка
    """
    try:
        # Проверяем разрешение (только менеджеры и администраторы)
        if current_user.role not in ['manager', 'admin']:
            return jsonify({
                'success': False,
                'message': 'Insufficient permissions to delete warehouse items'
            }), 403
        
        warehouse_item = Warehouse.query.get(item_id)
        
        if not warehouse_item:
            return jsonify({
                'success': False,
                'message': 'Warehouse item not found'
            }), 404
        
        item_name = warehouse_item.item_name
        
        db.session.delete(warehouse_item)
        db.session.commit()
        
        # Логируем операцию удаления
        log_operation(
            current_user.id,
            'DELETE',
            'warehouse',
            item_id,
            f'Deleted warehouse item: {item_name}'
        )
        
        return jsonify({
            'success': True,
            'message': 'Warehouse item deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting warehouse item: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500
