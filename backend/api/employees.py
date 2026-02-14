"""
Employee CRUD API endpoints
Обеспечивает управление сотрудниками: получение, создание, обновление, удаление
"""

from flask import Blueprint, request, jsonify
from database.models import db, Employee, OperationLog
from backend.auth import token_required
from datetime import datetime
import logging

# Создаем blueprint
employees_bp = Blueprint('employees', __name__, url_prefix='/api/employees')

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


@employees_bp.route('', methods=['GET'])
@token_required
def get_employees_list(current_user):
    """
    Получить список сотрудников с опциональной фильтрацией и поиском
    
    Query parameters:
        - search: поиск по имени, фамилии или должности (case-insensitive)
        - position: фильтр по должности
        - department: фильтр по отделу
        - status: фильтр по статусу (active, inactive, on_leave)
        - limit: количество записей на странице (по умолчанию 50)
        - offset: смещение для пагинации (по умолчанию 0)
    
    Returns:
        JSON с списком сотрудников и метаданными пагинации
    """
    try:
        # Получаем параметры из query string
        search = request.args.get('search', '').strip()
        position = request.args.get('position', '').strip()
        department = request.args.get('department', '').strip()
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
        query = Employee.query
        
        # Применяем фильтры
        if search:
            query = query.filter(
                db.or_(
                    Employee.first_name.ilike(f'%{search}%'),
                    Employee.last_name.ilike(f'%{search}%'),
                    Employee.position.ilike(f'%{search}%')
                )
            )
        
        if position:
            query = query.filter(Employee.position.ilike(f'%{position}%'))
        
        if department:
            query = query.filter(Employee.department.ilike(f'%{department}%'))
        
        if status:
            query = query.filter(Employee.status == status)
        
        # Получаем общее количество записей
        total = query.count()
        
        # Применяем пагинацию
        employees_list = query.offset(offset).limit(limit).all()
        
        # Логируем операцию чтения
        log_operation(
            current_user.id,
            'READ',
            'employee',
            None,
            f'Listed {len(employees_list)} employees'
        )
        
        return jsonify({
            'success': True,
            'data': [emp.to_dict() for emp in employees_list],
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset,
                'count': len(employees_list)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting employees list: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@employees_bp.route('/<int:employee_id>', methods=['GET'])
@token_required
def get_employee(current_user, employee_id):
    """
    Получить информацию об одном сотруднике по ID
    
    Args:
        employee_id: ID сотрудника
    
    Returns:
        JSON с информацией о сотруднике или ошибка 404
    """
    try:
        employee = Employee.query.get(employee_id)
        
        if not employee:
            return jsonify({
                'success': False,
                'message': 'Employee not found'
            }), 404
        
        # Логируем операцию чтения
        log_operation(current_user.id, 'READ', 'employee', employee_id)
        
        return jsonify({
            'success': True,
            'data': employee.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting employee: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@employees_bp.route('', methods=['POST'])
@token_required
def create_employee(current_user):
    """
    Создать нового сотрудника
    
    JSON Body:
        - first_name (required): имя
        - last_name (required): фамилия
        - position (required): должность
        - department (optional): отдел
        - phone (optional): номер телефона
        - email (optional): email
        - hire_date (optional): дата приема на работу (YYYY-MM-DD)
        - status (optional): статус (defaults to 'active')
        - notes (optional): заметки
    
    Returns:
        JSON с информацией о созданном сотруднике или ошибка
    """
    try:
        data = request.get_json()
        
        # Валидация требуемых полей
        if not data.get('first_name'):
            return jsonify({
                'success': False,
                'message': 'First name is required'
            }), 400
        
        if not data.get('last_name'):
            return jsonify({
                'success': False,
                'message': 'Last name is required'
            }), 400
        
        if not data.get('position'):
            return jsonify({
                'success': False,
                'message': 'Position is required'
            }), 400
        
        # Проверяем дубликаты (по имени, фамилии и должности)
        existing = Employee.query.filter(
            db.and_(
                Employee.first_name.ilike(data['first_name'].strip()),
                Employee.last_name.ilike(data['last_name'].strip()),
                Employee.position.ilike(data['position'].strip())
            )
        ).first()
        
        if existing:
            return jsonify({
                'success': False,
                'message': 'Employee with this name and position already exists'
            }), 409
        
        # Создаем нового сотрудника
        new_employee = Employee(
            first_name=data['first_name'].strip(),
            last_name=data['last_name'].strip(),
            position=data['position'].strip(),
            department=data.get('department', '').strip() or None,
            phone=data.get('phone', '').strip() or None,
            email=data.get('email', '').strip() or None,
            hire_date=data.get('hire_date'),
            status=data.get('status', 'active').strip(),
            notes=data.get('notes', '').strip() or None,
            created_at=datetime.utcnow()
        )
        
        db.session.add(new_employee)
        db.session.commit()
        
        # Логируем операцию создания
        log_operation(
            current_user.id,
            'CREATE',
            'employee',
            new_employee.id,
            f'Created employee: {new_employee.first_name} {new_employee.last_name}'
        )
        
        return jsonify({
            'success': True,
            'message': 'Employee created successfully',
            'data': new_employee.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating employee: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@employees_bp.route('/<int:employee_id>', methods=['PUT'])
@token_required
def update_employee(current_user, employee_id):
    """
    Обновить информацию о сотруднике (частичное обновление)
    
    Args:
        employee_id: ID сотрудника
    
    JSON Body:
        Любые из полей: first_name, last_name, position, department, phone,
        email, hire_date, status, notes
    
    Returns:
        JSON с обновленной информацией о сотруднике или ошибка
    """
    try:
        employee = Employee.query.get(employee_id)
        
        if not employee:
            return jsonify({
                'success': False,
                'message': 'Employee not found'
            }), 404
        
        data = request.get_json()
        
        # Если обновляем основные данные, проверяем дубликаты
        if any(field in data for field in ['first_name', 'last_name', 'position']):
            new_first = data.get('first_name', employee.first_name).strip()
            new_last = data.get('last_name', employee.last_name).strip()
            new_pos = data.get('position', employee.position).strip()
            
            existing = Employee.query.filter(
                db.and_(
                    Employee.id != employee_id,
                    Employee.first_name.ilike(new_first),
                    Employee.last_name.ilike(new_last),
                    Employee.position.ilike(new_pos)
                )
            ).first()
            
            if existing:
                return jsonify({
                    'success': False,
                    'message': 'Employee with this name and position already exists'
                }), 409
        
        # Обновляем поля
        if 'first_name' in data:
            employee.first_name = data['first_name'].strip()
        if 'last_name' in data:
            employee.last_name = data['last_name'].strip()
        if 'position' in data:
            employee.position = data['position'].strip()
        if 'department' in data:
            employee.department = data['department'].strip() or None
        if 'phone' in data:
            employee.phone = data['phone'].strip() or None
        if 'email' in data:
            employee.email = data['email'].strip() or None
        if 'hire_date' in data:
            employee.hire_date = data['hire_date']
        if 'status' in data:
            employee.status = data['status'].strip()
        if 'notes' in data:
            employee.notes = data['notes'].strip() or None
        
        employee.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Логируем операцию обновления
        log_operation(
            current_user.id,
            'UPDATE',
            'employee',
            employee_id,
            f'Updated employee: {employee.first_name} {employee.last_name}'
        )
        
        return jsonify({
            'success': True,
            'message': 'Employee updated successfully',
            'data': employee.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating employee: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@employees_bp.route('/<int:employee_id>', methods=['DELETE'])
@token_required
def delete_employee(current_user, employee_id):
    """
    Удалить сотрудника (требует роль 'manager' или 'admin')
    
    Args:
        employee_id: ID сотрудника
    
    Returns:
        JSON с подтверждением удаления или ошибка
    """
    try:
        # Проверяем разрешение (только менеджеры и администраторы)
        if current_user.role not in ['manager', 'admin']:
            return jsonify({
                'success': False,
                'message': 'Insufficient permissions to delete employees'
            }), 403
        
        employee = Employee.query.get(employee_id)
        
        if not employee:
            return jsonify({
                'success': False,
                'message': 'Employee not found'
            }), 404
        
        employee_name = f"{employee.first_name} {employee.last_name}"
        
        db.session.delete(employee)
        db.session.commit()
        
        # Логируем операцию удаления
        log_operation(
            current_user.id,
            'DELETE',
            'employee',
            employee_id,
            f'Deleted employee: {employee_name}'
        )
        
        return jsonify({
            'success': True,
            'message': 'Employee deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting employee: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500
