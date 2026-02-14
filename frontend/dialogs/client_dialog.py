"""
Диалог карточки клиента - добавление и редактирование
"""
import tkinter as tk
from tkinter import ttk, messagebox
import requests


class ClientDialog(tk.Toplevel):
    def __init__(self, parent, api_url, token, client_data=None):
        super().__init__(parent)
        self.api_url = api_url
        self.token = token
        self.client_data = client_data
        self.result = None
        
        self.title("Карточка клиента" if not client_data else f"Редактирование клиента #{client_data.get('id')}")
        self.geometry("600x500")
        self.resizable(False, False)
        
        # Центрируем окно
        self.transient(parent)
        self.grab_set()
        
        self.create_ui()
        self.load_data()
    
    def create_ui(self):
        """Создать интерфейс диалога"""
        # Основной фрейм
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="Информация о клиенте", 
                               font=("Arial", 12, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        # ФИО (обязательное)
        ttk.Label(main_frame, text="ФИО:*").grid(row=1, column=0, sticky="w", pady=5)
        self.full_name = ttk.Entry(main_frame, width=40)
        self.full_name.grid(row=1, column=1, sticky="ew", pady=5)
        
        # Телефон (обязательное)
        ttk.Label(main_frame, text="Телефон:*").grid(row=2, column=0, sticky="w", pady=5)
        self.phone = ttk.Entry(main_frame, width=40)
        self.phone.grid(row=2, column=1, sticky="ew", pady=5)
        
        # Email
        ttk.Label(main_frame, text="Email:").grid(row=3, column=0, sticky="w", pady=5)
        self.email = ttk.Entry(main_frame, width=40)
        self.email.grid(row=3, column=1, sticky="ew", pady=5)
        
        # Адрес
        ttk.Label(main_frame, text="Адрес:").grid(row=4, column=0, sticky="w", pady=5)
        self.address = ttk.Entry(main_frame, width=40)
        self.address.grid(row=4, column=1, sticky="ew", pady=5)
        
        # Соцсети
        ttk.Label(main_frame, text="Соцсети:").grid(row=5, column=0, sticky="w", pady=5)
        self.social_media = ttk.Entry(main_frame, width=40)
        self.social_media.grid(row=5, column=1, sticky="ew", pady=5)
        
        # Примечания
        ttk.Label(main_frame, text="Примечания:").grid(row=6, column=0, sticky="nw", pady=5)
        self.notes = tk.Text(main_frame, height=5, width=40)
        self.notes.grid(row=6, column=1, sticky="ew", pady=5)
        
        # Информация
        info_frame = ttk.LabelFrame(main_frame, text="Информация", padding="5")
        info_frame.grid(row=7, column=0, columnspan=2, sticky="ew", pady=10)
        
        self.info_label = ttk.Label(info_frame, text="Новый клиент", foreground="blue")
        self.info_label.pack()
        
        # Кнопки
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=8, column=0, columnspan=2, sticky="ew", pady=10)
        
        ttk.Button(btn_frame, text="Сохранить", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=self.cancel).pack(side=tk.LEFT, padx=5)
        
        main_frame.columnconfigure(1, weight=1)
    
    def load_data(self):
        """Загрузить данные клиента для редактирования"""
        if self.client_data:
            self.full_name.insert(0, self.client_data.get('full_name', ''))
            self.phone.insert(0, self.client_data.get('phone', ''))
            self.email.insert(0, self.client_data.get('email', ''))
            self.address.insert(0, self.client_data.get('address', ''))
            self.social_media.insert(0, self.client_data.get('social_media', ''))
            self.notes.insert('1.0', self.client_data.get('notes', ''))
            self.info_label.config(
                text=f"Клиент создан: {self.client_data.get('created_at', 'N/A')}"
            )
    
    def save(self):
        """Сохранить данные клиента"""
        full_name = self.full_name.get().strip()
        phone = self.phone.get().strip()
        
        if not full_name or not phone:
            messagebox.showwarning("Ошибка", "ФИО и телефон обязательны!")
            return
        
        data = {
            'full_name': full_name,
            'phone': phone,
            'email': self.email.get().strip(),
            'address': self.address.get().strip(),
            'social_media': self.social_media.get().strip(),
            'notes': self.notes.get('1.0', 'end-1c').strip()
        }
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            
            if self.client_data:
                # Обновить существующего клиента
                url = f"{self.api_url}/api/clients/{self.client_data['id']}"
                response = requests.put(url, json=data, headers=headers)
                if response.status_code == 200:
                    messagebox.showinfo("Успех", "Клиент обновлен")
                    self.result = response.json().get('data')
                    self.destroy()
                else:
                    messagebox.showerror("Ошибка", f"Ошибка: {response.status_code}")
            else:
                # Создать нового клиента
                url = f"{self.api_url}/api/clients"
                response = requests.post(url, json=data, headers=headers)
                if response.status_code == 201:
                    messagebox.showinfo("Успех", "Клиент создан")
                    self.result = response.json().get('data')
                    self.destroy()
                else:
                    messagebox.showerror("Ошибка", f"Ошибка: {response.status_code}")
        
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при сохранении: {str(e)}")
    
    def cancel(self):
        """Закрыть диалог без сохранения"""
        self.destroy()
