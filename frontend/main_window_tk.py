"""
Главное окно приложения PromoService на tkinter
Полностью функциональный интерфейс без внешних зависимостей
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
import json
from datetime import datetime
from frontend.dialogs.search_dialog import SearchDialog
from frontend.dialogs.client_dialog import ClientDialog
from frontend.dialogs.warehouse_dialog import WarehouseDialog


class PromoServiceApp:
    def __init__(self, root, token, user_data, api_url):
        self.root = root
        self.token = token
        self.user_data = user_data
        self.api_url = api_url
        self.headers = {"Authorization": f"Bearer {token}"}
        
        # Настройка окна
        self.root.title("PromoService V0003 - Управление сервисным центром")
        self.root.geometry("1200x700")
        self.root.minsize(800, 600)
        
        # Стиль
        style = ttk.Style()
        style.theme_use('clam')
        
        # Создаем интерфейс
        self.create_menu()
        self.create_ui()
        
        print(f"✓ Frontend запущен для пользователя: {user_data.get('username')}")
    
    def create_menu(self):
        """Создать меню"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Меню Файл
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Выход", command=self.root.quit)
        
        # Меню Данные
        data_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Данные", menu=data_menu)
        data_menu.add_command(label="Клиенты", command=lambda: self.show_tab("clients"))
        data_menu.add_command(label="Техника", command=lambda: self.show_tab("equipment"))
        data_menu.add_command(label="Склад", command=lambda: self.show_tab("warehouse"))
        data_menu.add_command(label="Сотрудники", command=lambda: self.show_tab("employees"))
        data_menu.add_command(label="Логи", command=lambda: self.show_tab("logging"))
        data_menu.add_separator()
        data_menu.add_command(label="Поиск по всем базам", command=self.open_search)
        
        # Меню Помощь
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Помощь", menu=help_menu)
        help_menu.add_command(label="О программе", command=self.show_about)
    
    def create_ui(self):
        """Создать пользовательский интерфейс"""
        # Верхняя панель с информацией
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(top_frame, text=f"Пользователь: {self.user_data.get('username')}").pack(side=tk.LEFT)
        ttk.Label(top_frame, text=f"Роль: {self.user_data.get('role')}").pack(side=tk.LEFT, padx=20)
        ttk.Label(top_frame, text=f"API: {self.api_url}").pack(side=tk.RIGHT)
        
        # Notebook (вкладки)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Вкладка 1: Клиенты
        self.clients_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.clients_frame, text="Клиенты")
        self.create_clients_tab()
        
        # Вкладка 2: Техника
        self.equipment_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.equipment_frame, text="Техника")
        self.create_equipment_tab()
        
        # Вкладка 3: Склад
        self.warehouse_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.warehouse_frame, text="Склад")
        self.create_warehouse_tab()
        
        # Вкладка 4: Сотрудники
        self.employees_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.employees_frame, text="Сотрудники")
        self.create_employees_tab()
        
        # Вкладка 5: Логи
        self.logging_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.logging_frame, text="Логи")
        self.create_logging_tab()
        
        # Вкладка 6: Статус
        self.status_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.status_frame, text="Статус")
        self.create_status_tab()
        
        # Нижняя панель со статусом
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.status_label = ttk.Label(bottom_frame, text="✓ Готово", relief=tk.SUNKEN)
        self.status_label.pack(fill=tk.X)
    
    # ==================== КЛИЕНТЫ ====================
    def create_clients_tab(self):
        """Вкладка Клиенты"""
        # Кнопки управления
        btn_frame = ttk.Frame(self.clients_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Загрузить", command=self.load_clients).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Добавить", command=self.add_client).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Редактировать", command=self.edit_client).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Удалить", command=self.delete_client).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Обновить", command=self.load_clients).pack(side=tk.LEFT, padx=5)
        
        # Поиск
        search_frame = ttk.Frame(self.clients_frame)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT, padx=5)
        self.clients_search = ttk.Entry(search_frame, width=30)
        self.clients_search.pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Найти", command=self.search_clients).pack(side=tk.LEFT, padx=5)
        
        # Таблица (Treeview)
        tree_frame = ttk.Frame(self.clients_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.clients_tree = ttk.Treeview(tree_frame, columns=("ID", "ФИО", "Телефон", "Email", "Адрес"), height=20)
        self.clients_tree.heading('#0', text='ID')
        self.clients_tree.heading('ID', text='ID')
        self.clients_tree.heading('ФИО', text='ФИО')
        self.clients_tree.heading('Телефон', text='Телефон')
        self.clients_tree.heading('Email', text='Email')
        self.clients_tree.heading('Адрес', text='Адрес')
        
        self.clients_tree.column('#0', width=0, stretch=tk.NO)
        self.clients_tree.column('ID', anchor=tk.W, width=50)
        self.clients_tree.column('ФИО', anchor=tk.W, width=200)
        self.clients_tree.column('Телефон', anchor=tk.W, width=150)
        self.clients_tree.column('Email', anchor=tk.W, width=200)
        self.clients_tree.column('Адрес', anchor=tk.W, width=200)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.clients_tree.yview)
        self.clients_tree.configure(yscroll=scrollbar.set)
        
        self.clients_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Двойной клик для редактирования
        self.clients_tree.bind("<Double-1>", lambda e: self.edit_client())
    
    def load_clients(self):
        """Загрузить список клиентов"""
        try:
            response = requests.get(f"{self.api_url}/api/clients", headers=self.headers)
            if response.status_code == 200:
                response_data = response.json()
                clients = response_data.get('data', [])  # API returns {"success": True, "data": [...]}
                self.clients_tree.delete(*self.clients_tree.get_children())
                if isinstance(clients, dict) and 'message' in clients:
                    messagebox.showinfo("Инфо", clients.get('message'))
                else:
                    for client in clients:
                        self.clients_tree.insert('', tk.END, values=(
                            client.get('id', ''),
                            client.get('full_name', ''),
                            client.get('phone', ''),
                            client.get('email', ''),
                            client.get('address', '')
                        ))
                self.status_label.config(text="✓ Клиенты загружены")
            else:
                messagebox.showerror("Ошибка", f"Ошибка: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить: {e}")
    
    def search_clients(self):
        """Поиск клиентов"""
        query = self.clients_search.get().strip()
        if not query:
            self.load_clients()
            return
        
        try:
            response = requests.get(f"{self.api_url}/api/clients?search={query}", headers=self.headers)
            if response.status_code == 200:
                response_data = response.json()
                clients = response_data.get('data', [])  # API returns {"success": True, "data": [...]}
                self.clients_tree.delete(*self.clients_tree.get_children())
                for client in clients:
                    self.clients_tree.insert('', tk.END, values=(
                        client.get('id', ''),
                        client.get('full_name', ''),
                        client.get('phone', ''),
                        client.get('email', ''),
                        client.get('address', '')
                    ))
                self.status_label.config(text=f"✓ Найдено: {len(clients)} клиентов")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка поиска: {e}")
    
    def get_selected_client(self):
        """Получить выбранного клиента"""
        selection = self.clients_tree.selection()
        if not selection:
            messagebox.showwarning("Выберите клиента", "Пожалуйста, выберите клиента из списка")
            return None
        
        item = self.clients_tree.item(selection[0])
        client_id = item['values'][0]
        
        # Находим данные клиента
        for client in self.clients_tree.get_children():
            if self.clients_tree.item(client)['values'][0] == client_id:
                return {'id': client_id, 'full_name': item['values'][1]}
        
        return {'id': client_id}
    
    def add_client(self):
        """Добавить клиента"""
        dialog = ClientDialog(self.root, self.api_url, self.token)
        self.root.wait_window(dialog)
        if dialog.result:
            self.load_clients()
            self.status_label.config(text="✓ Клиент добавлен")
    
    def edit_client(self):
        """Редактировать клиента"""
        selection = self.clients_tree.selection()
        if not selection:
            messagebox.showwarning("Выберите клиента", "Пожалуйста, выберите клиента для редактирования")
            return
        
        item = self.clients_tree.item(selection[0])
        client_id = item['values'][0]
        
        # Загружаем полные данные клиента
        try:
            response = requests.get(f"{self.api_url}/api/clients/{client_id}", headers=self.headers)
            if response.status_code == 200:
                client_data = response.json()
                dialog = ClientDialog(self.root, self.api_url, self.token, client_data)
                self.root.wait_window(dialog)
                if dialog.result:
                    self.load_clients()
                    self.status_label.config(text="✓ Клиент обновлен")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные: {e}")
    
    def delete_client(self):
        """Удалить клиента"""
        selection = self.clients_tree.selection()
        if not selection:
            messagebox.showwarning("Выберите клиента", "Пожалуйста, выберите клиента для удаления")
            return
        
        item = self.clients_tree.item(selection[0])
        client_id = item['values'][0]
        client_name = item['values'][1]
        
        if not messagebox.askyesno("Подтверждение", f"Удалить клиента '{client_name}'?"):
            return
        
        try:
            response = requests.delete(f"{self.api_url}/api/clients/{client_id}", headers=self.headers)
            if response.status_code == 200:
                messagebox.showinfo("Успех", "Клиент удален")
                self.load_clients()
                self.status_label.config(text="✓ Клиент удален")
            else:
                messagebox.showerror("Ошибка", f"Ошибка: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить: {e}")
    
    # ==================== ТЕХНИКА ====================
    def create_equipment_tab(self):
        """Вкладка Техника"""
        # Кнопки управления
        btn_frame = ttk.Frame(self.equipment_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Загрузить", command=self.load_equipment).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Добавить", command=self.add_equipment).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Редактировать", command=self.edit_equipment).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Удалить", command=self.delete_equipment).pack(side=tk.LEFT, padx=5)
        
        # Поиск
        search_frame = ttk.Frame(self.equipment_frame)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT, padx=5)
        self.equipment_search = ttk.Entry(search_frame, width=30)
        self.equipment_search.pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Найти", command=self.search_equipment).pack(side=tk.LEFT, padx=5)
        
        # Таблица
        tree_frame = ttk.Frame(self.equipment_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.equipment_tree = ttk.Treeview(tree_frame, columns=("ID", "Клиент", "Описание", "Серийный №", "IMEI", "Неисправности", "Статус"), height=20)
        self.equipment_tree.heading('#0', text='ID')
        self.equipment_tree.heading('ID', text='ID')
        self.equipment_tree.heading('Клиент', text='Клиент')
        self.equipment_tree.heading('Описание', text='Описание')
        self.equipment_tree.heading('Серийный №', text='Серийный №')
        self.equipment_tree.heading('IMEI', text='IMEI')
        self.equipment_tree.heading('Неисправности', text='Неисправности')
        self.equipment_tree.heading('Статус', text='Статус')
        
        self.equipment_tree.column('#0', width=0, stretch=tk.NO)
        self.equipment_tree.column('ID', anchor=tk.W, width=50)
        self.equipment_tree.column('Клиент', anchor=tk.W, width=150)
        self.equipment_tree.column('Описание', anchor=tk.W, width=150)
        self.equipment_tree.column('Серийный №', anchor=tk.W, width=120)
        self.equipment_tree.column('IMEI', anchor=tk.W, width=120)
        self.equipment_tree.column('Неисправности', anchor=tk.W, width=200)
        self.equipment_tree.column('Статус', anchor=tk.W, width=100)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.equipment_tree.yview)
        self.equipment_tree.configure(yscroll=scrollbar.set)
        
        self.equipment_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def load_equipment(self):
        """Загрузить список техники"""
        try:
            response = requests.get(f"{self.api_url}/api/equipment", headers=self.headers)
            if response.status_code == 200:
                response_data = response.json()
                equipment_list = response_data.get('data', [])  # API returns {"success": True, "data": [...]}
                self.equipment_tree.delete(*self.equipment_tree.get_children())
                
                if isinstance(equipment_list, dict) and 'message' in equipment_list:
                    messagebox.showinfo("Инфо", equipment_list.get('message'))
                else:
                    for item in equipment_list:
                        self.equipment_tree.insert('', tk.END, values=(
                            item.get('id', ''),
                            item.get('name', ''),
                            item.get('equipment_type', ''),
                            item.get('model', ''),
                            item.get('serial_number', ''),
                            item.get('location', ''),
                            item.get('status', '')
                        ))
                self.status_label.config(text="✓ Техника загружена")
            else:
                messagebox.showerror("Ошибка", f"Ошибка: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить: {e}")
    
    def search_equipment(self):
        """Поиск техники"""
        query = self.equipment_search.get().strip()
        if not query:
            self.load_equipment()
            return
        
        try:
            response = requests.get(f"{self.api_url}/api/equipment?search={query}", headers=self.headers)
            if response.status_code == 200:
                response_data = response.json()
                equipment_list = response_data.get('data', [])  # API returns {"success": True, "data": [...]}
                self.equipment_tree.delete(*self.equipment_tree.get_children())
                for item in equipment_list:
                    self.equipment_tree.insert('', tk.END, values=(
                        item.get('id', ''),
                        item.get('name', ''),
                        item.get('equipment_type', ''),
                        item.get('model', ''),
                        item.get('serial_number', ''),
                        item.get('location', ''),
                        item.get('status', '')
                    ))
                self.status_label.config(text=f"✓ Найдено: {len(equipment_list)} единиц техники")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка поиска: {e}")
    
    def add_equipment(self):
        """Добавить технику"""
        # Создаем диалог
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить технику")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Форма
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Выбор клиента
        ttk.Label(main_frame, text="Клиент:*").grid(row=0, column=0, sticky="w", pady=5)
        self.equip_client_combo = ttk.Combobox(main_frame, width=40)
        self.equip_client_combo.grid(row=0, column=1, sticky="ew", pady=5)
        
        # Загружаем клиентов
        try:
            response = requests.get(f"{self.api_url}/api/clients", headers=self.headers)
            if response.status_code == 200:
                response_data = response.json()
                clients = response_data.get('data', [])  # API returns {"success": True, "data": [...]}
                self.clients_list = [(c['id'], c['full_name']) for c in clients]
                self.equip_client_combo['values'] = [f"{c[0]} - {c[1]}" for c in self.clients_list]
        except:
            pass
        
        # Описание
        ttk.Label(main_frame, text="Описание:*").grid(row=1, column=0, sticky="w", pady=5)
        desc_frame = ttk.Frame(main_frame)
        desc_frame.grid(row=1, column=1, sticky="ew", pady=5)
        self.equip_description = tk.Text(desc_frame, height=3, width=40)
        self.equip_description.pack(fill=tk.BOTH, expand=True)
        
        # Серийный номер
        ttk.Label(main_frame, text="Серийный номер:").grid(row=2, column=0, sticky="w", pady=5)
        self.equip_serial = ttk.Entry(main_frame, width=40)
        self.equip_serial.grid(row=2, column=1, sticky="ew", pady=5)
        
        # IMEI
        ttk.Label(main_frame, text="IMEI:").grid(row=3, column=0, sticky="w", pady=5)
        self.equip_imei = ttk.Entry(main_frame, width=40)
        self.equip_imei.grid(row=3, column=1, sticky="ew", pady=5)
        
        # Комплектация
        ttk.Label(main_frame, text="Комплектация:").grid(row=4, column=0, sticky="w", pady=5)
        self.equip_components = tk.Text(main_frame, height=2, width=40)
        self.equip_components.grid(row=4, column=1, sticky="ew", pady=5)
        
        # Неисправности
        ttk.Label(main_frame, text="Неисправности:*").grid(row=5, column=0, sticky="w", pady=5)
        self.equip_defects = tk.Text(main_frame, height=3, width=40)
        self.equip_defects.grid(row=5, column=1, sticky="ew", pady=5)
        
        # Статус
        ttk.Label(main_frame, text="Статус:").grid(row=6, column=0, sticky="w", pady=5)
        self.equip_status = ttk.Combobox(main_frame, width=38, values=["received", "in_repair", "ready", "delivered"])
        self.equip_status.current(0)
        self.equip_status.grid(row=6, column=1, sticky="ew", pady=5)
        
        # Кнопки
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="Сохранить", command=lambda: self.save_equipment(dialog)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        main_frame.columnconfigure(1, weight=1)
    
    def save_equipment(self, dialog):
        """Сохранить технику"""
        # Получаем ID клиента
        client_str = self.equip_client_combo.get()
        if not client_str:
            messagebox.showwarning("Ошибка", "Выберите клиента!")
            return
        
        try:
            client_id = int(client_str.split(" - ")[0])
        except:
            messagebox.showwarning("Ошибка", "Некорректный клиент!")
            return
        
        description = self.equip_description.get('1.0', 'end-1c').strip()
        defects = self.equip_defects.get('1.0', 'end-1c').strip()
        
        if not description or not defects:
            messagebox.showwarning("Ошибка", "Описание и неисправности обязательны!")
            return
        
        data = {
            'client_id': client_id,
            'description': description,
            'serial_number': self.equip_serial.get().strip(),
            'imei': self.equip_imei.get().strip(),
            'components': self.equip_components.get('1.0', 'end-1c').strip(),
            'defects': defects,
            'status': self.equip_status.get()
        }
        
        try:
            response = requests.post(f"{self.api_url}/api/equipment", json=data, headers=self.headers)
            if response.status_code in [200, 201]:
                messagebox.showinfo("Успех", "Техника добавлена")
                dialog.destroy()
                self.load_equipment()
                self.status_label.config(text="✓ Техника добавлена")
            else:
                messagebox.showerror("Ошибка", f"Ошибка: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось добавить: {e}")
    
    def edit_equipment(self):
        """Редактировать технику"""
        selection = self.equipment_tree.selection()
        if not selection:
            messagebox.showwarning("Выберите технику", "Выберите технику для редактирования")
            return
        
        item = self.equipment_tree.item(selection[0])
        equipment_id = item['values'][0]
        
        try:
            response = requests.get(f"{self.api_url}/api/equipment/{equipment_id}", headers=self.headers)
            if response.status_code == 200:
                equip_data = response.json()
                
                dialog = tk.Toplevel(self.root)
                dialog.title(f"Редактировать технику #{equipment_id}")
                dialog.geometry("600x500")
                dialog.transient(self.root)
                dialog.grab_set()
                
                main_frame = ttk.Frame(dialog, padding="10")
                main_frame.pack(fill=tk.BOTH, expand=True)
                
                # Описание
                ttk.Label(main_frame, text="Описание:*").grid(row=0, column=0, sticky="w", pady=5)
                desc_frame = ttk.Frame(main_frame)
                desc_frame.grid(row=0, column=1, sticky="ew", pady=5)
                edit_desc = tk.Text(desc_frame, height=3, width=40)
                edit_desc.pack(fill=tk.BOTH, expand=True)
                edit_desc.insert('1.0', equip_data.get('description', ''))
                
                # Серийный номер
                ttk.Label(main_frame, text="Серийный номер:").grid(row=1, column=0, sticky="w", pady=5)
                edit_serial = ttk.Entry(main_frame, width=40)
                edit_serial.grid(row=1, column=1, sticky="ew", pady=5)
                edit_serial.insert(0, equip_data.get('serial_number', ''))
                
                # IMEI
                ttk.Label(main_frame, text="IMEI:").grid(row=2, column=0, sticky="w", pady=5)
                edit_imei = ttk.Entry(main_frame, width=40)
                edit_imei.grid(row=2, column=1, sticky="ew", pady=5)
                edit_imei.insert(0, equip_data.get('imei', ''))
                
                # Комплектация
                ttk.Label(main_frame, text="Комплектация:").grid(row=3, column=0, sticky="w", pady=5)
                edit_components = tk.Text(main_frame, height=2, width=40)
                edit_components.grid(row=3, column=1, sticky="ew", pady=5)
                edit_components.insert('1.0', equip_data.get('components', ''))
                
                # Неисправности
                ttk.Label(main_frame, text="Неисправности:*").grid(row=4, column=0, sticky="w", pady=5)
                edit_defects = tk.Text(main_frame, height=3, width=40)
                edit_defects.grid(row=4, column=1, sticky="ew", pady=5)
                edit_defects.insert('1.0', equip_data.get('defects', ''))
                
                # Статус
                ttk.Label(main_frame, text="Статус:").grid(row=5, column=0, sticky="w", pady=5)
                edit_status = ttk.Combobox(main_frame, width=38, values=["received", "in_repair", "ready", "delivered"])
                edit_status.current(["received", "in_repair", "ready", "delivered"].index(equip_data.get('status', 'received')))
                edit_status.grid(row=5, column=1, sticky="ew", pady=5)
                
                def save():
                    data = {
                        'description': edit_desc.get('1.0', 'end-1c').strip(),
                        'serial_number': edit_serial.get().strip(),
                        'imei': edit_imei.get().strip(),
                        'components': edit_components.get('1.0', 'end-1c').strip(),
                        'defects': edit_defects.get('1.0', 'end-1c').strip(),
                        'status': edit_status.get()
                    }
                    try:
                        response = requests.put(f"{self.api_url}/api/equipment/{equipment_id}", json=data, headers=self.headers)
                        if response.status_code == 200:
                            messagebox.showinfo("Успех", "Техника обновлена")
                            dialog.destroy()
                            self.load_equipment()
                            self.status_label.config(text="✓ Техника обновлена")
                    except Exception as e:
                        messagebox.showerror("Ошибка", f"Не удалось обновить: {e}")
                
                btn_frame = ttk.Frame(main_frame)
                btn_frame.grid(row=6, column=0, columnspan=2, pady=10)
                ttk.Button(btn_frame, text="Сохранить", command=save).pack(side=tk.LEFT, padx=5)
                ttk.Button(btn_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
                
                main_frame.columnconfigure(1, weight=1)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить: {e}")
    
    def delete_equipment(self):
        """Удалить технику"""
        selection = self.equipment_tree.selection()
        if not selection:
            messagebox.showwarning("Выберите технику", "Выберите технику для удаления")
            return
        
        item = self.equipment_tree.item(selection[0])
        equipment_id = item['values'][0]
        
        if not messagebox.askyesno("Подтверждение", f"Удалить технику #{equipment_id}?"):
            return
        
        try:
            response = requests.delete(f"{self.api_url}/api/equipment/{equipment_id}", headers=self.headers)
            if response.status_code == 200:
                messagebox.showinfo("Успех", "Техника удалена")
                self.load_equipment()
                self.status_label.config(text="✓ Техника удалена")
            else:
                messagebox.showerror("Ошибка", f"Ошибка: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить: {e}")
    
    # ==================== СКЛАД ====================
    def create_warehouse_tab(self):
        """Вкладка Склад"""
        # Кнопки управления
        btn_frame = ttk.Frame(self.warehouse_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Загрузить", command=self.load_warehouse).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Добавить", command=self.add_warehouse).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Редактировать", command=self.edit_warehouse).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Удалить", command=self.delete_warehouse).pack(side=tk.LEFT, padx=5)
        
        # Поиск
        search_frame = ttk.Frame(self.warehouse_frame)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT, padx=5)
        self.warehouse_search = ttk.Entry(search_frame, width=30)
        self.warehouse_search.pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Найти", command=self.search_warehouse).pack(side=tk.LEFT, padx=5)
        
        # Таблица
        tree_frame = ttk.Frame(self.warehouse_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.warehouse_tree = ttk.Treeview(tree_frame, columns=("ID", "Название", "Артикул", "Категория", "Кол-во", "Цена", "Расположение"), height=20)
        self.warehouse_tree.heading('#0', text='ID')
        self.warehouse_tree.heading('ID', text='ID')
        self.warehouse_tree.heading('Название', text='Название')
        self.warehouse_tree.heading('Артикул', text='Артикул')
        self.warehouse_tree.heading('Категория', text='Категория')
        self.warehouse_tree.heading('Кол-во', text='Кол-во')
        self.warehouse_tree.heading('Цена', text='Цена')
        self.warehouse_tree.heading('Расположение', text='Расположение')
        
        self.warehouse_tree.column('#0', width=0, stretch=tk.NO)
        self.warehouse_tree.column('ID', anchor=tk.W, width=50)
        self.warehouse_tree.column('Название', anchor=tk.W, width=180)
        self.warehouse_tree.column('Артикул', anchor=tk.W, width=120)
        self.warehouse_tree.column('Категория', anchor=tk.W, width=100)
        self.warehouse_tree.column('Кол-во', anchor=tk.W, width=80)
        self.warehouse_tree.column('Цена', anchor=tk.W, width=100)
        self.warehouse_tree.column('Расположение', anchor=tk.W, width=120)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.warehouse_tree.yview)
        self.warehouse_tree.configure(yscroll=scrollbar.set)
        
        self.warehouse_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def load_warehouse(self):
        """Загрузить список товара"""
        try:
            response = requests.get(f"{self.api_url}/api/warehouse", headers=self.headers)
            if response.status_code == 200:
                response_data = response.json()
                items = response_data.get('data', [])  # API returns {"success": True, "data": [...]}
                self.warehouse_tree.delete(*self.warehouse_tree.get_children())
                
                if isinstance(items, dict) and 'message' in items:
                    messagebox.showinfo("Инфо", items.get('message'))
                else:
                    for item in items:
                        self.warehouse_tree.insert('', tk.END, values=(
                            item.get('id', ''),
                            item.get('item_name', ''),
                            item.get('article_number', ''),
                            item.get('category', ''),
                            item.get('quantity', ''),
                            item.get('unit_price', ''),
                            item.get('location', '')
                        ))
                self.status_label.config(text="✓ Склад загружен")
            else:
                messagebox.showerror("Ошибка", f"Ошибка: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить: {e}")
    
    def search_warehouse(self):
        """Поиск по складу"""
        query = self.warehouse_search.get().strip()
        if not query:
            self.load_warehouse()
            return
        
        try:
            response = requests.get(f"{self.api_url}/api/warehouse?search={query}", headers=self.headers)
            if response.status_code == 200:
                response_data = response.json()
                items = response_data.get('data', [])  # API returns {"success": True, "data": [...]}
                self.warehouse_tree.delete(*self.warehouse_tree.get_children())
                for item in items:
                    self.warehouse_tree.insert('', tk.END, values=(
                        item.get('id', ''),
                        item.get('item_name', ''),
                        item.get('article_number', ''),
                        item.get('category', ''),
                        item.get('quantity', ''),
                        item.get('unit_price', ''),
                        item.get('location', '')
                    ))
                self.status_label.config(text=f"✓ Найдено: {len(items)} товаров")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка поиска: {e}")
    
    def add_warehouse(self):
        """Добавить товар на склад"""
        dialog = WarehouseDialog(self.root, self.api_url, self.token)
        self.root.wait_window(dialog)
        if dialog.result:
            self.load_warehouse()
            self.status_label.config(text="✓ Товар добавлен")
    
    def edit_warehouse(self):
        """Редактировать товар"""
        selection = self.warehouse_tree.selection()
        if not selection:
            messagebox.showwarning("Выберите товар", "Выберите товар для редактирования")
            return
        
        item = self.warehouse_tree.item(selection[0])
        item_id = item['values'][0]
        
        try:
            response = requests.get(f"{self.api_url}/api/warehouse/{item_id}", headers=self.headers)
            if response.status_code == 200:
                item_data = response.json()
                dialog = WarehouseDialog(self.root, self.api_url, self.token, item_data)
                self.root.wait_window(dialog)
                if dialog.result:
                    self.load_warehouse()
                    self.status_label.config(text="✓ Товар обновлен")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить: {e}")
    
    def delete_warehouse(self):
        """Удалить товар"""
        selection = self.warehouse_tree.selection()
        if not selection:
            messagebox.showwarning("Выберите товар", "Выберите товар для удаления")
            return
        
        item = self.warehouse_tree.item(selection[0])
        item_id = item['values'][0]
        item_name = item['values'][1]
        
        if not messagebox.askyesno("Подтверждение", f"Удалить товар '{item_name}'?"):
            return
        
        try:
            response = requests.delete(f"{self.api_url}/api/warehouse/{item_id}", headers=self.headers)
            if response.status_code == 200:
                messagebox.showinfo("Успех", "Товар удален")
                self.load_warehouse()
                self.status_label.config(text="✓ Товар удален")
            else:
                messagebox.showerror("Ошибка", f"Ошибка: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить: {e}")
    
    # ==================== СОТРУДНИКИ ====================
    def create_employees_tab(self):
        """Вкладка Сотрудники"""
        # Кнопки управления
        btn_frame = ttk.Frame(self.employees_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Загрузить", command=self.load_employees).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Добавить", command=self.add_employee).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Редактировать", command=self.edit_employee).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Удалить", command=self.delete_employee).pack(side=tk.LEFT, padx=5)
        
        # Поиск
        search_frame = ttk.Frame(self.employees_frame)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT, padx=5)
        self.employees_search = ttk.Entry(search_frame, width=30)
        self.employees_search.pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Найти", command=self.search_employees).pack(side=tk.LEFT, padx=5)
        
        # Таблица
        tree_frame = ttk.Frame(self.employees_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.employees_tree = ttk.Treeview(tree_frame, columns=("ID", "Имя", "Фамилия", "Должность", "Отдел", "Телефон", "Email", "Статус"), height=20)
        self.employees_tree.heading('#0', text='ID')
        self.employees_tree.heading('ID', text='ID')
        self.employees_tree.heading('Имя', text='Имя')
        self.employees_tree.heading('Фамилия', text='Фамилия')
        self.employees_tree.heading('Должность', text='Должность')
        self.employees_tree.heading('Отдел', text='Отдел')
        self.employees_tree.heading('Телефон', text='Телефон')
        self.employees_tree.heading('Email', text='Email')
        self.employees_tree.heading('Статус', text='Статус')
        
        self.employees_tree.column('#0', width=0, stretch=tk.NO)
        self.employees_tree.column('ID', anchor=tk.W, width=50)
        self.employees_tree.column('Имя', anchor=tk.W, width=120)
        self.employees_tree.column('Фамилия', anchor=tk.W, width=120)
        self.employees_tree.column('Должность', anchor=tk.W, width=120)
        self.employees_tree.column('Отдел', anchor=tk.W, width=100)
        self.employees_tree.column('Телефон', anchor=tk.W, width=120)
        self.employees_tree.column('Email', anchor=tk.W, width=150)
        self.employees_tree.column('Статус', anchor=tk.W, width=100)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.employees_tree.yview)
        self.employees_tree.configure(yscroll=scrollbar.set)
        
        self.employees_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def load_employees(self):
        """Загрузить сотрудников"""
        try:
            response = requests.get(f"{self.api_url}/api/employees", headers=self.headers)
            if response.status_code == 200:
                response_data = response.json()
                employees = response_data.get('data', [])  # API returns {"success": True, "data": [...]}
                self.employees_tree.delete(*self.employees_tree.get_children())
                
                if isinstance(employees, dict) and 'message' in employees:
                    messagebox.showinfo("Инфо", employees.get('message'))
                else:
                    for emp in employees:
                        self.employees_tree.insert('', tk.END, values=(
                            emp.get('id', ''),
                            emp.get('first_name', ''),
                            emp.get('last_name', ''),
                            emp.get('position', ''),
                            emp.get('department', ''),
                            emp.get('phone', ''),
                            emp.get('email', ''),
                            emp.get('status', '')
                        ))
                self.status_label.config(text="✓ Сотрудники загружены")
            else:
                messagebox.showerror("Ошибка", f"Ошибка: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить: {e}")
    
    def search_employees(self):
        """Поиск сотрудников"""
        query = self.employees_search.get().strip()
        if not query:
            self.load_employees()
            return
        
        try:
            response = requests.get(f"{self.api_url}/api/employees?search={query}", headers=self.headers)
            if response.status_code == 200:
                response_data = response.json()
                employees = response_data.get('data', [])  # API returns {"success": True, "data": [...]}
                self.employees_tree.delete(*self.employees_tree.get_children())
                for emp in employees:
                    self.employees_tree.insert('', tk.END, values=(
                        emp.get('id', ''),
                        emp.get('first_name', ''),
                        emp.get('last_name', ''),
                        emp.get('position', ''),
                        emp.get('department', ''),
                        emp.get('phone', ''),
                        emp.get('email', ''),
                        emp.get('status', '')
                    ))
                self.status_label.config(text=f"✓ Найдено: {len(employees)} сотрудников")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка поиска: {e}")
    
    def add_employee(self):
        """Добавить сотрудника"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить сотрудника")
        dialog.geometry("500x450")
        dialog.transient(self.root)
        dialog.grab_set()
        
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        fields = [
            ("Имя:*", "first_name"),
            ("Фамилия:*", "last_name"),
            ("Должность:*", "position"),
            ("Отдел:", "department"),
            ("Телефон:", "phone"),
            ("Email:", "email"),
        ]
        
        self.emp_entries = {}
        for i, (label, key) in enumerate(fields):
            ttk.Label(main_frame, text=label).grid(row=i, column=0, sticky="w", pady=5)
            entry = ttk.Entry(main_frame, width=35)
            entry.grid(row=i, column=1, sticky="ew", pady=5)
            self.emp_entries[key] = entry
        
        ttk.Label(main_frame, text="Статус:").grid(row=len(fields), column=0, sticky="w", pady=5)
        self.emp_status = ttk.Combobox(main_frame, width=33, values=["active", "inactive", "on_leave"])
        self.emp_status.current(0)
        self.emp_status.grid(row=len(fields), column=1, sticky="ew", pady=5)
        
        def save():
            data = {key: entry.get().strip() for key, entry in self.emp_entries.items()}
            data['status'] = self.emp_status.get()
            
            if not data.get('first_name') or not data.get('last_name') or not data.get('position'):
                messagebox.showwarning("Ошибка", "Имя, фамилия и должность обязательны!")
                return
            
            try:
                response = requests.post(f"{self.api_url}/api/employees", json=data, headers=self.headers)
                if response.status_code in [200, 201]:
                    messagebox.showinfo("Успех", "Сотрудник добавлен")
                    dialog.destroy()
                    self.load_employees()
                    self.status_label.config(text="✓ Сотрудник добавлен")
                else:
                    messagebox.showerror("Ошибка", f"Ошибка: {response.status_code}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось добавить: {e}")
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=len(fields)+1, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Сохранить", command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        main_frame.columnconfigure(1, weight=1)
    
    def edit_employee(self):
        """Редактировать сотрудника"""
        selection = self.employees_tree.selection()
        if not selection:
            messagebox.showwarning("Выберите сотрудника", "Выберите сотрудника для редактирования")
            return
        
        item = self.employees_tree.item(selection[0])
        emp_id = item['values'][0]
        
        try:
            response = requests.get(f"{self.api_url}/api/employees/{emp_id}", headers=self.headers)
            if response.status_code == 200:
                response_data = response.json()
                emp_data = response_data.get('data', {})  # API returns {"success": True, "data": {...}}
                
                dialog = tk.Toplevel(self.root)
                dialog.title(f"Редактировать сотрудника #{emp_id}")
                dialog.geometry("500x450")
                dialog.transient(self.root)
                dialog.grab_set()
                
                main_frame = ttk.Frame(dialog, padding="10")
                main_frame.pack(fill=tk.BOTH, expand=True)
                
                fields = [
                    ("Имя:*", "first_name"),
                    ("Фамилия:*", "last_name"),
                    ("Должность:*", "position"),
                    ("Отдел:", "department"),
                    ("Телефон:", "phone"),
                    ("Email:", "email"),
                ]
                
                emp_entries = {}
                for i, (label, key) in enumerate(fields):
                    ttk.Label(main_frame, text=label).grid(row=i, column=0, sticky="w", pady=5)
                    entry = ttk.Entry(main_frame, width=35)
                    entry.grid(row=i, column=1, sticky="ew", pady=5)
                    entry.insert(0, emp_data.get(key, ''))
                    emp_entries[key] = entry
                
                ttk.Label(main_frame, text="Статус:").grid(row=len(fields), column=0, sticky="w", pady=5)
                emp_status = ttk.Combobox(main_frame, width=33, values=["active", "inactive", "on_leave"])
                status_val = emp_data.get('status', 'active')
                emp_status.current(["active", "inactive", "on_leave"].index(status_val) if status_val in ["active", "inactive", "on_leave"] else 0)
                emp_status.grid(row=len(fields), column=1, sticky="ew", pady=5)
                
                def save():
                    data = {key: entry.get().strip() for key, entry in emp_entries.items()}
                    data['status'] = emp_status.get()
                    
                    try:
                        response = requests.put(f"{self.api_url}/api/employees/{emp_id}", json=data, headers=self.headers)
                        if response.status_code == 200:
                            messagebox.showinfo("Успех", "Сотрудник обновлен")
                            dialog.destroy()
                            self.load_employees()
                            self.status_label.config(text="✓ Сотрудник обновлен")
                    except Exception as e:
                        messagebox.showerror("Ошибка", f"Не удалось обновить: {e}")
                
                btn_frame = ttk.Frame(main_frame)
                btn_frame.grid(row=len(fields)+1, column=0, columnspan=2, pady=10)
                ttk.Button(btn_frame, text="Сохранить", command=save).pack(side=tk.LEFT, padx=5)
                ttk.Button(btn_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
                
                main_frame.columnconfigure(1, weight=1)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить: {e}")
    
    def delete_employee(self):
        """Удалить сотрудника"""
        selection = self.employees_tree.selection()
        if not selection:
            messagebox.showwarning("Выберите сотрудника", "Выберите сотрудника для удаления")
            return
        
        item = self.employees_tree.item(selection[0])
        emp_id = item['values'][0]
        emp_name = f"{item['values'][1]} {item['values'][2]}"
        
        if not messagebox.askyesno("Подтверждение", f"Удалить сотрудника '{emp_name}'?"):
            return
        
        try:
            response = requests.delete(f"{self.api_url}/api/employees/{emp_id}", headers=self.headers)
            if response.status_code == 200:
                messagebox.showinfo("Успех", "Сотрудник удален")
                self.load_employees()
                self.status_label.config(text="✓ Сотрудник удален")
            else:
                messagebox.showerror("Ошибка", f"Ошибка: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить: {e}")
    
    # ==================== ЛОГИ ====================
    def create_logging_tab(self):
        """Вкладка Логи"""
        # Кнопки управления
        btn_frame = ttk.Frame(self.logging_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Загрузить логи", command=self.load_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Очистить", command=self.clear_logs).pack(side=tk.LEFT, padx=5)
        
        # Фильтры
        filter_frame = ttk.Frame(self.logging_frame)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(filter_frame, text="Тип:").pack(side=tk.LEFT, padx=5)
        self.log_type = ttk.Combobox(filter_frame, width=15, values=["all", "client", "equipment", "warehouse", "employee"])
        self.log_type.current(0)
        self.log_type.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(filter_frame, text="Действие:").pack(side=tk.LEFT, padx=5)
        self.log_action = ttk.Combobox(filter_frame, width=15, values=["all", "create", "update", "delete"])
        self.log_action.current(0)
        self.log_action.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(filter_frame, text="Применить фильтр", command=self.filter_logs).pack(side=tk.LEFT, padx=5)
        
        # Таблица
        tree_frame = ttk.Frame(self.logging_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.logs_tree = ttk.Treeview(tree_frame, columns=("ID", "Время", "Пользователь", "Тип", "Действие", "Объект", "Детали"), height=20)
        self.logs_tree.heading('#0', text='ID')
        self.logs_tree.heading('ID', text='ID')
        self.logs_tree.heading('Время', text='Время')
        self.logs_tree.heading('Пользователь', text='Пользователь')
        self.logs_tree.heading('Тип', text='Тип')
        self.logs_tree.heading('Действие', text='Действие')
        self.logs_tree.heading('Объект', text='Объект')
        self.logs_tree.heading('Детали', text='Детали')
        
        self.logs_tree.column('#0', width=0, stretch=tk.NO)
        self.logs_tree.column('ID', anchor=tk.W, width=50)
        self.logs_tree.column('Время', anchor=tk.W, width=150)
        self.logs_tree.column('Пользователь', anchor=tk.W, width=120)
        self.logs_tree.column('Тип', anchor=tk.W, width=100)
        self.logs_tree.column('Действие', anchor=tk.W, width=100)
        self.logs_tree.column('Объект', anchor=tk.W, width=150)
        self.logs_tree.column('Детали', anchor=tk.W, width=250)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.logs_tree.yview)
        self.logs_tree.configure(yscroll=scrollbar.set)
        
        self.logs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def load_logs(self):
        """Загрузить логи"""
        try:
            response = requests.get(f"{self.api_url}/api/logs", headers=self.headers)
            if response.status_code == 200:
                response_data = response.json()
                logs = response_data.get('data', [])  # API returns {"success": True, "data": [...]}
                self.logs_tree.delete(*self.logs_tree.get_children())
                
                if isinstance(logs, dict) and 'message' in logs:
                    messagebox.showinfo("Инфо", logs.get('message'))
                else:
                    for log in logs:
                        self.logs_tree.insert('', tk.END, values=(
                            log.get('id', ''),
                            log.get('timestamp', ''),
                            log.get('user_id', ''),
                            log.get('table_name', ''),
                            log.get('operation_type', ''),
                            str(log.get('record_id', '')),
                            log.get('details', '')[:100]
                        ))
                self.status_label.config(text="✓ Логи загружены")
            else:
                messagebox.showerror("Ошибка", f"Ошибка: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить: {e}")
    
    def filter_logs(self):
        """Фильтровать логи"""
        log_type = self.log_type.get()
        action = self.log_action.get()
        
        try:
            url = f"{self.api_url}/api/logs?type={log_type}&action={action}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                response_data = response.json()
                logs = response_data.get('data', [])  # API returns {"success": True, "data": [...]}
                self.logs_tree.delete(*self.logs_tree.get_children())
                for log in logs:
                    self.logs_tree.insert('', tk.END, values=(
                        log.get('id', ''),
                        log.get('timestamp', ''),
                        log.get('user_id', ''),
                        log.get('table_name', ''),
                        log.get('operation_type', ''),
                        str(log.get('record_id', '')),
                        log.get('details', '')[:100]
                    ))
                self.status_label.config(text=f"✓ Найдено: {len(logs)} записей")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка фильтрации: {e}")
    
    def clear_logs(self):
        """Очистить локальный вид логов"""
        self.logs_tree.delete(*self.logs_tree.get_children())
        self.status_label.config(text="✓ Логи очищены")
    
    # ==================== СТАТУС ====================
    def create_status_tab(self):
        """Вкладка Статус и информация"""
        # Информация о пользователе
        info_frame = ttk.LabelFrame(self.status_frame, text="Информация о пользователе")
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(info_frame, text=f"Username: {self.user_data.get('username')}").pack(anchor=tk.W, padx=10, pady=5)
        ttk.Label(info_frame, text=f"ID: {self.user_data.get('id')}").pack(anchor=tk.W, padx=10, pady=5)
        ttk.Label(info_frame, text=f"Роль: {self.user_data.get('role')}").pack(anchor=tk.W, padx=10, pady=5)
        
        # Информация о сервере
        info_frame2 = ttk.LabelFrame(self.status_frame, text="Информация о сервере")
        info_frame2.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(info_frame2, text="Проверить статус API", command=self.check_api_status).pack(padx=10, pady=10)
        
        self.status_text = scrolledtext.ScrolledText(self.status_frame, height=10, width=50)
        self.status_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def check_api_status(self):
        """Проверить статус API"""
        try:
            response = requests.get(f"{self.api_url}/api/health")
            if response.status_code == 200:
                status = response.json()
                self.status_text.delete(1.0, tk.END)
                self.status_text.insert(tk.END, f"✓ API Status: {status.get('status')}\n")
                self.status_text.insert(tk.END, f"✓ Message: {status.get('message')}\n")
                self.status_text.insert(tk.END, f"✓ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                self.status_label.config(text="✓ API статус: OK")
            else:
                self.status_text.insert(tk.END, f"✗ Ошибка: {response.status_code}\n")
        except Exception as e:
            self.status_text.delete(1.0, tk.END)
            self.status_text.insert(tk.END, f"✗ Ошибка подключения: {e}\n")
            self.status_label.config(text="✗ Ошибка подключения к API")
    
    def show_tab(self, tab_name):
        """Показать определенную вкладку"""
        tabs = {
            "clients": 0,
            "equipment": 1,
            "warehouse": 2,
            "employees": 3,
            "logging": 4,
            "status": 5
        }
        if tab_name in tabs:
            self.notebook.select(tabs[tab_name])
    
    def open_search(self):
        """Открыть диалог поиска"""
        SearchDialog(self.root, self.api_url, self.token)
    
    def show_about(self):
        """Показать информацию о программе"""
        messagebox.showinfo(
            "О программе",
            "PromoService V0003\n"
            "Управление сервисным центром\n\n"
            "Версия: 0.0.3 (Alpha)\n"
            "Frontend: tkinter\n"
            "Backend: Flask\n"
            "БД: SQLite\n\n"
            "© 2025-2026"
        )


def run_frontend(token, user_data, api_url):
    """Запустить frontend"""
    root = tk.Tk()
    app = PromoServiceApp(root, token, user_data, api_url)
    root.mainloop()
