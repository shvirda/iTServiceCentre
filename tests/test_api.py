"""
Тесты для API PromoService
"""
import unittest
import json
import sys
import os

# Добавляем родительскую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app
from database.models import db, User
from config import Config


class APITestCase(unittest.TestCase):
    """Тестовые случаи для API"""
    
    def setUp(self):
        """Подготовка к тестам"""
        # Создаем тестовое приложение
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        self.client = self.app.test_client()
        
        # Создаем таблицы
        with self.app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Очистка после тестов"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_health_check(self):
        """Тест проверки здоровья API"""
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'ok')
    
    def test_login_missing_credentials(self):
        """Тест входа без учетных данных"""
        response = self.client.post('/api/auth/login', json={})
        self.assertEqual(response.status_code, 400)
    
    def test_login_invalid_user(self):
        """Тест входа с неправильным пользователем"""
        response = self.client.post(
            '/api/auth/login',
            json={'username': 'nonexistent', 'password': 'password'}
        )
        self.assertEqual(response.status_code, 401)
    
    def test_register_user(self):
        """Тест регистрации пользователя"""
        response = self.client.post(
            '/api/auth/register',
            json={
                'username': 'testuser',
                'password': 'password123',
                'role': 'employee'
            }
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['user']['username'], 'testuser')
    
    def test_register_duplicate_user(self):
        """Тест регистрации дублирующегося пользователя"""
        # Первая регистрация
        self.client.post(
            '/api/auth/register',
            json={
                'username': 'testuser',
                'password': 'password123'
            }
        )
        
        # Вторая регистрация с тем же пользователем
        response = self.client.post(
            '/api/auth/register',
            json={
                'username': 'testuser',
                'password': 'password456'
            }
        )
        self.assertEqual(response.status_code, 409)
    
    def test_login_success(self):
        """Тест успешного входа"""
        # Создаем пользователя
        self.client.post(
            '/api/auth/register',
            json={
                'username': 'testuser',
                'password': 'password123'
            }
        )
        
        # Входим
        response = self.client.post(
            '/api/auth/login',
            json={
                'username': 'testuser',
                'password': 'password123'
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('token', data)
        self.assertEqual(data['user']['username'], 'testuser')
    
    def test_clients_endpoint(self):
        """Тест endpoint для клиентов"""
        response = self.client.get('/api/clients')
        self.assertEqual(response.status_code, 200)
    
    def test_equipment_endpoint(self):
        """Тест endpoint для техники"""
        response = self.client.get('/api/equipment')
        self.assertEqual(response.status_code, 200)
    
    def test_warehouse_endpoint(self):
        """Тест endpoint для склада"""
        response = self.client.get('/api/warehouse')
        self.assertEqual(response.status_code, 200)
    
    def test_employees_endpoint(self):
        """Тест endpoint для сотрудников"""
        response = self.client.get('/api/employees')
        self.assertEqual(response.status_code, 200)
    
    def test_services_endpoint(self):
        """Тест endpoint для сервисов"""
        response = self.client.get('/api/services')
        self.assertEqual(response.status_code, 200)
    
    def test_logs_endpoint(self):
        """Тест endpoint для логирования"""
        response = self.client.get('/api/logs')
        self.assertEqual(response.status_code, 200)
    
    def test_404_error(self):
        """Тест ошибки 404"""
        response = self.client.get('/api/nonexistent')
        self.assertEqual(response.status_code, 404)


if __name__ == '__main__':
    unittest.main()
