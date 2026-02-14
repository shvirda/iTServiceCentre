"""
Диалог карточки пользователя - добавление и редактирование
"""
import tkinter as tk
from tkinter import ttk, messagebox
import requests


class UserDialog(tk.Toplevel):
    def __init__(self, parent, api_url, token, user_data=None):
        super().__init__(parent)
        self.api_url = api_url
        self.token = token
        self.user_data = user_data
        self.result = None
        
        self.title("Новый пользователь" if not user_data else f"Редактирование пользователя #{user_data.get('id')}")
        self.geometry("700x450")
        self.resizable(False, False)
        
        self.transient(parent)
        self.grab_set()
        
        self.create_ui()
        self.load_data()
    
    def create_ui(self):
        """Создать интерфейс диалога"""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="Информация пользователя", 
                               font=("Arial", 12, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        # Имя пользователя (обязательное)
        ttk.Label(main_frame, text="Имя пользователя:*").grid(row=1, column=0, sticky="w", pady=5)
        self.username = ttk.Entry(main_frame, width=45)
        self.username.grid(row=1, column=1, sticky="ew", pady=5)
        
        # Пароль (обязательный при создании)
        ttk.Label(main_frame, text="Пароль:*").grid(row=2, column=0, sticky="w", pady=5)
        self.password = ttk.Entry(main_frame, width=45, show="*")
        self.password.grid(row=2, column=1, sticky="ew", pady=5)
        
        # Email (обязательный)
        ttk.Label(main_frame, text="Email:*").grid(row=3, column=0, sticky="w", pady=5)
        self.email = ttk.Entry(main_frame, width=45)
        self.email.grid(row=3, column=1, sticky="ew", pady=5)
        
        # Роль (обязательная)
        ttk.Label(main_frame, text="Роль:*").grid(row=4, column=0, sticky="w", pady=5)
        self.role = ttk.Combobox(main_frame, width=42, values=[
            "Директор", "Менеджер", "Сотрудник", "Складской"
        ])
        self.role.grid(row=4, column=1, sticky="ew", pady=5)
        
        # Статус
        ttk.Label(main_frame, text="Статус:").grid(row=5, column=0, sticky="w", pady=5)
        self.status = ttk.Combobox(main_frame, width=42, values=[
            "Активный", "Неактивный", "В отпуске"
        ])
        self.status.grid(row=5, column=1, sticky="ew", pady=5)
        self.status.set("Активный")
        
        # Информация
        info_frame = ttk.LabelFrame(main_frame, text="Информация", padding="5")
        info_frame.grid(row=6, column=0, columnspan=2, sticky="ew", pady=10)
        
        self.info_label = ttk.Label(info_frame, text="Новый пользователь", foreground="blue")
        self.info_label.pack()
        
        # Кнопки
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=7, column=0, columnspan=2, sticky="ew", pady=10)
        
        ttk.Button(btn_frame, text="Сохранить", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=self.cancel).pack(side=tk.LEFT, padx=5)
        
        main_frame.columnconfigure(1, weight=1)
    
    def load_data(self):
        """Загрузить данные пользователя"""
        if self.user_data:
            self.username.insert(0, self.user_data.get('username', ''))
            self.username.config(state='disabled')  # Нельзя менять имя пользователя
            
            self.password.config(state='disabled')  # При редактировании пароль не показывается
            
            self.email.insert(0, self.user_data.get('email', ''))
            
            # Преобразование роли для комбобокса
            role_mapping = {
                'director': 'Директор',
                'manager': 'Менеджер',
                'employee': 'Сотрудник',
                'warehouse': 'Складской'
            }
            role = role_mapping.get(self.user_data.get('role', 'employee'), 'Сотрудник')
            self.role.set(role)
            
            status_mapping = {
                'active': 'Активный',
                'inactive': 'Неактивный',
                'on_leave': 'В отпуске'
            }
            status = status_mapping.get(self.user_data.get('status', 'active'), 'Активный')
            self.status.set(status)
            
            self.info_label.config(
                text=f"Пользователь создан: {self.user_data.get('created_at', 'N/A')}"
            )
    
    def save(self):
        """Сохранить данные пользователя"""
        username = self.username.get().strip()
        password = self.password.get().strip()
        email = self.email.get().strip()
        role = self.role.get()
        status = self.status.get()
        
        if not username or not email or not role:
            messagebox.showwarning("Ошибка", "Имя пользователя, email и роль обязательны!")
            return
        
        if not self.user_data and not password:
            messagebox.showwarning("Ошибка", "Пароль обязателен для новых пользователей!")
            return
        
        if '@' not in email:
            messagebox.showwarning("Ошибка", "Некорректный email!")
            return
        
        # Преобразование роли для API
        role_mapping = {
            'Директор': 'director',
            'Менеджер': 'manager',
            'Сотрудник': 'employee',
            'Складской': 'warehouse'
        }
        
        # Преобразование статуса для API
        status_mapping = {
            'Активный': 'active',
            'Неактивный': 'inactive',
            'В отпуске': 'on_leave'
        }
        
        data = {
            'username': username,
            'email': email,
            'role': role_mapping.get(role, 'employee'),
            'status': status_mapping.get(status, 'active')
        }
        
        if password:
            data['password'] = password
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            
            if self.user_data:
                url = f"{self.api_url}/api/users/{self.user_data['id']}"
                response = requests.put(url, json=data, headers=headers)
                if response.status_code == 200:
                    messagebox.showinfo("Успех", "Пользователь обновлен")
                    self.result = response.json().get('data')
                    self.destroy()
                else:
                    try:
                        error_msg = response.json().get('message', f"Ошибка: {response.status_code}")
                    except:
                        error_msg = f"Ошибка: {response.status_code}"
                    messagebox.showerror("Ошибка", error_msg)
            else:
                url = f"{self.api_url}/api/users"
                response = requests.post(url, json=data, headers=headers)
                if response.status_code == 201:
                    messagebox.showinfo("Успех", "Пользователь добавлен")
                    self.result = response.json().get('data')
                    self.destroy()
                else:
                    try:
                        error_msg = response.json().get('message', f"Ошибка: {response.status_code}")
                    except:
                        error_msg = f"Ошибка: {response.status_code}"
                    messagebox.showerror("Ошибка", error_msg)
        
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при сохранении: {str(e)}")
    
    def cancel(self):
        """Закрыть диалог"""
        self.destroy()
