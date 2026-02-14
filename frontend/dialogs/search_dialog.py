"""
Диалог универсального поиска по всем базам
"""
import tkinter as tk
from tkinter import ttk, messagebox
import requests


class SearchDialog(tk.Toplevel):
    def __init__(self, parent, api_url, token):
        super().__init__(parent)
        self.api_url = api_url
        self.token = token
        
        self.title("Поиск по всем базам")
        self.geometry("900x600")
        self.resizable(True, True)
        
        self.transient(parent)
        self.grab_set()
        
        self.create_ui()
    
    def create_ui(self):
        """Создать интерфейс поиска"""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="Поиск по всем базам данных", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Фрейм поиска
        search_frame = ttk.LabelFrame(main_frame, text="Параметры поиска", padding="10")
        search_frame.pack(fill=tk.X, pady=10)
        
        # Поле поиска
        ttk.Label(search_frame, text="Поисковый запрос:").pack(side=tk.LEFT, padx=5)
        self.search_entry = ttk.Entry(search_frame, width=40)
        self.search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.search_entry.bind('<Return>', lambda e: self.search())
        
        # Выбор категории
        ttk.Label(search_frame, text="Категория:").pack(side=tk.LEFT, padx=5)
        self.category = ttk.Combobox(search_frame, width=15, values=[
            "Все", "Клиенты", "Техника", "Склад", "Услуги", "Сотрудники", "Пользователи"
        ], state="readonly")
        self.category.set("Все")
        self.category.pack(side=tk.LEFT, padx=5)
        
        # Кнопка поиска
        ttk.Button(search_frame, text="Найти", command=self.search).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Очистить", command=self.clear_results).pack(side=tk.LEFT, padx=5)
        
        # Фрейм результатов
        results_frame = ttk.LabelFrame(main_frame, text="Результаты поиска", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Таблица результатов
        self.results_tree = ttk.Treeview(results_frame, columns=(
            "Тип", "ID", "Название", "Контакт", "Статус"
        ), height=20)
        
        self.results_tree.heading('#0', text='№')
        self.results_tree.heading('Тип', text='Тип')
        self.results_tree.heading('ID', text='ID')
        self.results_tree.heading('Название', text='Название/ФИО')
        self.results_tree.heading('Контакт', text='Контакт')
        self.results_tree.heading('Статус', text='Статус')
        
        self.results_tree.column('#0', width=30, anchor=tk.CENTER)
        self.results_tree.column('Тип', width=80, anchor=tk.W)
        self.results_tree.column('ID', width=40, anchor=tk.CENTER)
        self.results_tree.column('Название', width=300, anchor=tk.W)
        self.results_tree.column('Контакт', width=250, anchor=tk.W)
        self.results_tree.column('Статус', width=100, anchor=tk.W)
        
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscroll=scrollbar.set)
        
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Информация о результатах
        self.info_label = ttk.Label(main_frame, text="Введите поисковый запрос", 
                                    foreground="blue")
        self.info_label.pack(pady=5)
        
        self.search_entry.focus()
    
    def search(self):
        """Выполнить поиск"""
        query = self.search_entry.get().strip()
        category = self.category.get()
        
        if not query:
            messagebox.showwarning("Ошибка", "Введите поисковый запрос!")
            return
        
        self.results_tree.delete(*self.results_tree.get_children())
        self.info_label.config(text="Поиск...", foreground="blue")
        self.root.update()
        
        all_results = []
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            
            # Поиск в клиентах
            if category in ["Все", "Клиенты"]:
                try:
                    response = requests.get(f"{self.api_url}/api/clients", headers=headers)
                    if response.status_code == 200:
                        clients = response.json()
                        for client in clients:
                            if self._matches_query(query, [
                                str(client.get('full_name', '')),
                                str(client.get('phone', '')),
                                str(client.get('email', '')),
                                str(client.get('id', ''))
                            ]):
                                all_results.append({
                                    'type': 'Клиент',
                                    'id': client.get('id', ''),
                                    'name': client.get('full_name', ''),
                                    'contact': f"☎ {client.get('phone', '')} | {client.get('email', '')}",
                                    'status': 'Активный'
                                })
                except:
                    pass
            
            # Поиск в техники
            if category in ["Все", "Техника"]:
                try:
                    response = requests.get(f"{self.api_url}/api/equipment", headers=headers)
                    if response.status_code == 200:
                        equipment = response.json()
                        if isinstance(equipment, list):
                            for item in equipment:
                                if self._matches_query(query, [
                                    str(item.get('brand', '')),
                                    str(item.get('model', '')),
                                    str(item.get('id', ''))
                                ]):
                                    all_results.append({
                                        'type': 'Техника',
                                        'id': item.get('id', ''),
                                        'name': f"{item.get('brand', '')} {item.get('model', '')}",
                                        'contact': item.get('serial_number', 'N/A'),
                                        'status': item.get('status', 'N/A')
                                    })
                except:
                    pass
            
            # Поиск в складе
            if category in ["Все", "Склад"]:
                try:
                    response = requests.get(f"{self.api_url}/api/warehouse", headers=headers)
                    if response.status_code == 200:
                        warehouse = response.json()
                        if isinstance(warehouse, list):
                            for item in warehouse:
                                if self._matches_query(query, [
                                    str(item.get('item_name', '')),
                                    str(item.get('article_number', '')),
                                    str(item.get('category', '')),
                                    str(item.get('id', ''))
                                ]):
                                    all_results.append({
                                        'type': 'Товар',
                                        'id': item.get('id', ''),
                                        'name': item.get('item_name', ''),
                                        'contact': f"Артикул: {item.get('article_number', '')} | Кол-во: {item.get('quantity', 0)}",
                                        'status': f"₽ {item.get('unit_price', 0)}"
                                    })
                except:
                    pass
            
            # Поиск в услугах
            if category in ["Все", "Услуги"]:
                try:
                    response = requests.get(f"{self.api_url}/api/services", headers=headers)
                    if response.status_code == 200:
                        services = response.json()
                        if isinstance(services, list):
                            for service in services:
                                if self._matches_query(query, [
                                    str(service.get('name', '')),
                                    str(service.get('category', '')),
                                    str(service.get('id', ''))
                                ]):
                                    all_results.append({
                                        'type': 'Услуга',
                                        'id': service.get('id', ''),
                                        'name': service.get('name', ''),
                                        'contact': service.get('category', ''),
                                        'status': f"₽ {service.get('price', 0)}"
                                    })
                except:
                    pass
            
            # Поиск в сотрудниках
            if category in ["Все", "Сотрудники"]:
                try:
                    response = requests.get(f"{self.api_url}/api/employees", headers=headers)
                    if response.status_code == 200:
                        employees = response.json()
                        if isinstance(employees, list):
                            for emp in employees:
                                if self._matches_query(query, [
                                    str(emp.get('full_name', '')),
                                    str(emp.get('phone', '')),
                                    str(emp.get('position', '')),
                                    str(emp.get('id', ''))
                                ]):
                                    all_results.append({
                                        'type': 'Сотрудник',
                                        'id': emp.get('id', ''),
                                        'name': emp.get('full_name', ''),
                                        'contact': f"☎ {emp.get('phone', '')} | {emp.get('position', '')}",
                                        'status': 'Активный'
                                    })
                except:
                    pass
            
            # Поиск в пользователях
            if category in ["Все", "Пользователи"]:
                try:
                    response = requests.get(f"{self.api_url}/api/users", headers=headers)
                    if response.status_code == 200:
                        users = response.json()
                        if isinstance(users, list):
                            for user in users:
                                if self._matches_query(query, [
                                    str(user.get('username', '')),
                                    str(user.get('email', '')),
                                    str(user.get('role', '')),
                                    str(user.get('id', ''))
                                ]):
                                    status_map = {
                                        'active': 'Активный',
                                        'inactive': 'Неактивный',
                                        'on_leave': 'В отпуске'
                                    }
                                    all_results.append({
                                        'type': 'Пользователь',
                                        'id': user.get('id', ''),
                                        'name': user.get('username', ''),
                                        'contact': user.get('email', ''),
                                        'status': status_map.get(user.get('status', 'active'), 'N/A')
                                    })
                except:
                    pass
            
            # Отображение результатов
            if all_results:
                for idx, result in enumerate(all_results, 1):
                    self.results_tree.insert('', tk.END, text=str(idx), values=(
                        result['type'],
                        result['id'],
                        result['name'],
                        result['contact'],
                        result['status']
                    ))
                self.info_label.config(
                    text=f"Найдено {len(all_results)} результатов", 
                    foreground="green"
                )
            else:
                self.info_label.config(text="Результаты не найдены", foreground="red")
        
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при поиске: {str(e)}")
            self.info_label.config(text="Ошибка при поиске", foreground="red")
    
    def _matches_query(self, query, fields):
        """Проверить, совпадает ли запрос с полями"""
        query_lower = query.lower()
        for field in fields:
            if query_lower in str(field).lower():
                return True
        return False
    
    def clear_results(self):
        """Очистить результаты"""
        self.results_tree.delete(*self.results_tree.get_children())
        self.search_entry.delete(0, tk.END)
        self.info_label.config(text="Введите поисковый запрос", foreground="blue")
        self.search_entry.focus()
