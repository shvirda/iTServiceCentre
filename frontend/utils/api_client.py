"""
Клиент для API запросов к backend серверу
"""
import requests
import json
from typing import Dict, Any, Tuple
from config import Config


class APIClient:
    """Клиент для работы с REST API"""
    
    def __init__(self, base_url: str = None, token: str = None):
        """
        Инициализация клиента
        
        Args:
            base_url: Базовый URL API (по умолчанию из Config)
            token: JWT токен (опционально)
        """
        self.base_url = base_url or Config.API_URL
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        
        if self.token:
            self.set_token(self.token)
    
    def set_token(self, token: str):
        """
        Установить JWT токен
        
        Args:
            token: JWT токен
        """
        self.token = token
        self.session.headers.update({
            'Authorization': f'Bearer {token}'
        })
    
    def clear_token(self):
        """Удалить токен"""
        self.token = None
        if 'Authorization' in self.session.headers:
            del self.session.headers['Authorization']
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Dict = None,
        params: Dict = None
    ) -> Tuple[bool, Any, str]:
        """
        Выполнить HTTP запрос
        
        Args:
            method: HTTP метод (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            data: JSON данные для отправки
            params: Query параметры
        
        Returns:
            tuple: (успешность, данные/ответ, сообщение об ошибке)
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == 'GET':
                response = self.session.get(url, params=params, timeout=10)
            elif method == 'POST':
                response = self.session.post(url, json=data, params=params, timeout=10)
            elif method == 'PUT':
                response = self.session.put(url, json=data, params=params, timeout=10)
            elif method == 'DELETE':
                response = self.session.delete(url, params=params, timeout=10)
            else:
                return False, None, f"Неизвестный метод: {method}"
            
            # Проверяем статус кода
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', 'Неизвестная ошибка')
                except:
                    error_msg = f"HTTP {response.status_code}"
                return False, None, error_msg
            
            # Парсим ответ
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            return True, response_data, ""
        
        except requests.exceptions.ConnectionError:
            return False, None, f"Не удается подключиться к {self.base_url}"
        except requests.exceptions.Timeout:
            return False, None, "Истекло время ожидания запроса"
        except Exception as e:
            return False, None, f"Ошибка запроса: {str(e)}"
    
    # ===== AUTH endpoints =====
    
    def login(self, username: str, password: str) -> Tuple[bool, Dict, str]:
        """
        Вход пользователя
        
        Args:
            username: Имя пользователя
            password: Пароль
        
        Returns:
            tuple: (успешность, данные пользователя, сообщение об ошибке)
        """
        success, response, error = self._make_request(
            'POST',
            '/api/auth/login',
            data={'username': username, 'password': password}
        )
        
        if success and 'token' in response:
            self.set_token(response['token'])
        
        return success, response, error
    
    def register(
        self,
        username: str,
        password: str,
        role: str = 'employee'
    ) -> Tuple[bool, Dict, str]:
        """
        Регистрация нового пользователя
        
        Args:
            username: Имя пользователя
            password: Пароль
            role: Роль пользователя
        
        Returns:
            tuple: (успешность, данные, сообщение об ошибке)
        """
        return self._make_request(
            'POST',
            '/api/auth/register',
            data={
                'username': username,
                'password': password,
                'role': role
            }
        )
    
    def health_check(self) -> Tuple[bool, Dict, str]:
        """
        Проверка здоровья API
        
        Returns:
            tuple: (успешность, данные, сообщение об ошибке)
        """
        return self._make_request('GET', '/api/health')
    
    # ===== CLIENTS endpoints =====
    
    def get_clients(self, search: str = None, phone: str = None, limit: int = 50, offset: int = 0) -> Tuple[bool, list, str]:
        """
        Получить список клиентов
        
        Args:
            search: Текст для поиска (опционально)
            phone: Фильтр по номеру телефона (опционально)
            limit: Количество записей на странице
            offset: Смещение
        
        Returns:
            tuple: (успешность, список клиентов, сообщение об ошибке)
        """
        params = {'limit': limit, 'offset': offset}
        if search:
            params['search'] = search
        if phone:
            params['phone'] = phone
        return self._make_request('GET', '/api/clients', params=params)
    
    def create_client(self, data: Dict) -> Tuple[bool, Dict, str]:
        """
        Создать нового клиента
        
        Args:
            data: Данные клиента
        
        Returns:
            tuple: (успешность, данные, сообщение об ошибке)
        """
        return self._make_request('POST', '/api/clients', data=data)
    
    def update_client(self, client_id: int, data: Dict) -> Tuple[bool, Dict, str]:
        """
        Обновить данные клиента
        
        Args:
            client_id: ID клиента
            data: Новые данные
        
        Returns:
            tuple: (успешность, данные, сообщение об ошибке)
        """
        return self._make_request('PUT', f'/api/clients/{client_id}', data=data)
    
    def delete_client(self, client_id: int) -> Tuple[bool, Dict, str]:
        """
        Удалить клиента
        
        Args:
            client_id: ID клиента
        
        Returns:
            tuple: (успешность, данные, сообщение об ошибке)
        """
        return self._make_request('DELETE', f'/api/clients/{client_id}')
    
    # ===== EQUIPMENT endpoints =====
    
    def get_equipment(self, search: str = None) -> Tuple[bool, list, str]:
        """Получить список техники"""
        params = {'search': search} if search else None
        return self._make_request('GET', '/api/equipment', params=params)
    
    def create_equipment(self, data: Dict) -> Tuple[bool, Dict, str]:
        """Создать запись о технике"""
        return self._make_request('POST', '/api/equipment', data=data)
    
    def update_equipment(self, equipment_id: int, data: Dict) -> Tuple[bool, Dict, str]:
        """Обновить данные техники"""
        return self._make_request('PUT', f'/api/equipment/{equipment_id}', data=data)
    
    def delete_equipment(self, equipment_id: int) -> Tuple[bool, Dict, str]:
        """Удалить технику"""
        return self._make_request('DELETE', f'/api/equipment/{equipment_id}')
    
    # ===== WAREHOUSE endpoints =====
    
    def get_warehouse(self, search: str = None) -> Tuple[bool, list, str]:
        """Получить список товара на складе"""
        params = {'search': search} if search else None
        return self._make_request('GET', '/api/warehouse', params=params)
    
    def create_warehouse_item(self, data: Dict) -> Tuple[bool, Dict, str]:
        """Добавить товар на склад"""
        return self._make_request('POST', '/api/warehouse', data=data)
    
    def update_warehouse_item(self, item_id: int, data: Dict) -> Tuple[bool, Dict, str]:
        """Обновить товар"""
        return self._make_request('PUT', f'/api/warehouse/{item_id}', data=data)
    
    def delete_warehouse_item(self, item_id: int) -> Tuple[bool, Dict, str]:
        """Удалить товар"""
        return self._make_request('DELETE', f'/api/warehouse/{item_id}')
    
    # ===== EMPLOYEES endpoints =====
    
    def get_employees(self, search: str = None) -> Tuple[bool, list, str]:
        """Получить список сотрудников"""
        params = {'search': search} if search else None
        return self._make_request('GET', '/api/employees', params=params)
    
    def create_employee(self, data: Dict) -> Tuple[bool, Dict, str]:
        """Создать нового сотрудника"""
        return self._make_request('POST', '/api/employees', data=data)
    
    def update_employee(self, employee_id: int, data: Dict) -> Tuple[bool, Dict, str]:
        """Обновить данные сотрудника"""
        return self._make_request('PUT', f'/api/employees/{employee_id}', data=data)
    
    def delete_employee(self, employee_id: int) -> Tuple[bool, Dict, str]:
        """Удалить сотрудника"""
        return self._make_request('DELETE', f'/api/employees/{employee_id}')
    
    # ===== SERVICES endpoints =====
    
    def get_services(self) -> Tuple[bool, list, str]:
        """Получить список сервисов"""
        return self._make_request('GET', '/api/services')
    
    def update_service(self, service_id: int, config: Dict) -> Tuple[bool, Dict, str]:
        """Обновить конфигурацию сервиса"""
        return self._make_request('PUT', f'/api/services/{service_id}', data={'config': config})
    
    # ===== LOGGING endpoints =====
    
    def get_logs(self, filter_type: str = None, limit: int = 50, offset: int = 0) -> Tuple[bool, list, str]:
        """Получить логи операций"""
        params = {'limit': limit, 'offset': offset}
        if filter_type:
            params['operation_type'] = filter_type
        return self._make_request('GET', '/api/logs', params=params)
    
    # ===== UNIVERSAL API method for SearchTableWidget =====
    
    def get_from_api(self, endpoint: str, **kwargs) -> Tuple[bool, Dict, str]:
        """
        Универсальный метод для получения данных из API
        
        Args:
            endpoint: API endpoint (напр. '/api/equipment')
            **kwargs: Фильтры и параметры 
        
        Returns:
            tuple: (успешность, данные, сообщение об ошибке)
        """
        params = kwargs if kwargs else None
        return self._make_request('GET', endpoint, params=params)
