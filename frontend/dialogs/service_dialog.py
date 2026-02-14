"""
Диалог карточки услуги/сервиса - добавление и редактирование
"""
import tkinter as tk
from tkinter import ttk, messagebox
import requests


class ServiceDialog(tk.Toplevel):
    def __init__(self, parent, api_url, token, service_data=None):
        super().__init__(parent)
        self.api_url = api_url
        self.token = token
        self.service_data = service_data
        self.result = None
        
        self.title("Карточка услуги" if not service_data else f"Редактирование услуги #{service_data.get('id')}")
        self.geometry("600x500")
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
        title_label = ttk.Label(main_frame, text="Информация об услуге", 
                               font=("Arial", 12, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        # Название услуги (обязательное)
        ttk.Label(main_frame, text="Название:*").grid(row=1, column=0, sticky="w", pady=5)
        self.name = ttk.Entry(main_frame, width=40)
        self.name.grid(row=1, column=1, sticky="ew", pady=5)
        
        # Категория
        ttk.Label(main_frame, text="Категория:").grid(row=2, column=0, sticky="w", pady=5)
        self.category = ttk.Combobox(main_frame, width=37, values=[
            "Диагностика", "Ремонт", "Обслуживание", "Чистка", "Установка",
            "Консультация", "Тестирование", "Прочее"
        ])
        self.category.grid(row=2, column=1, sticky="ew", pady=5)
        
        # Цена
        ttk.Label(main_frame, text="Цена (₽):").grid(row=3, column=0, sticky="w", pady=5)
        self.price = ttk.Entry(main_frame, width=40)
        self.price.grid(row=3, column=1, sticky="ew", pady=5)
        
        # Время выполнения
        ttk.Label(main_frame, text="Время (мин):").grid(row=4, column=0, sticky="w", pady=5)
        self.duration = ttk.Entry(main_frame, width=40)
        self.duration.grid(row=4, column=1, sticky="ew", pady=5)
        
        # Описание
        ttk.Label(main_frame, text="Описание:").grid(row=5, column=0, sticky="nw", pady=5)
        self.description = tk.Text(main_frame, height=6, width=40)
        self.description.grid(row=5, column=1, sticky="ew", pady=5)
        
        # Информация
        info_frame = ttk.LabelFrame(main_frame, text="Информация", padding="5")
        info_frame.grid(row=6, column=0, columnspan=2, sticky="ew", pady=10)
        
        self.info_label = ttk.Label(info_frame, text="Новая услуга", foreground="blue")
        self.info_label.pack()
        
        # Кнопки
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=7, column=0, columnspan=2, sticky="ew", pady=10)
        
        ttk.Button(btn_frame, text="Сохранить", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=self.cancel).pack(side=tk.LEFT, padx=5)
        
        main_frame.columnconfigure(1, weight=1)
    
    def load_data(self):
        """Загрузить данные услуги"""
        if self.service_data:
            self.name.insert(0, self.service_data.get('name', ''))
            self.category.set(self.service_data.get('category', ''))
            self.price.insert(0, str(self.service_data.get('price', '')))
            self.duration.insert(0, str(self.service_data.get('duration_minutes', '')))
            self.description.insert('1.0', self.service_data.get('description', ''))
            self.info_label.config(
                text=f"Услуга создана: {self.service_data.get('created_at', 'N/A')}"
            )
    
    def save(self):
        """Сохранить данные услуги"""
        name = self.name.get().strip()
        
        if not name:
            messagebox.showwarning("Ошибка", "Название услуги обязательно!")
            return
        
        try:
            price = float(self.price.get() or 0)
        except:
            messagebox.showwarning("Ошибка", "Некорректная цена!")
            return
        
        try:
            duration = int(self.duration.get() or 0)
        except:
            messagebox.showwarning("Ошибка", "Некорректное время!")
            return
        
        data = {
            'name': name,
            'category': self.category.get(),
            'price': price,
            'duration_minutes': duration,
            'description': self.description.get('1.0', 'end-1c').strip()
        }
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            
            if self.service_data:
                url = f"{self.api_url}/api/services/{self.service_data['id']}"
                response = requests.put(url, json=data, headers=headers)
                if response.status_code == 200:
                    messagebox.showinfo("Успех", "Услуга обновлена")
                    self.result = response.json().get('data')
                    self.destroy()
                else:
                    messagebox.showerror("Ошибка", f"Ошибка: {response.status_code}")
            else:
                url = f"{self.api_url}/api/services"
                response = requests.post(url, json=data, headers=headers)
                if response.status_code == 201:
                    messagebox.showinfo("Успех", "Услуга создана")
                    self.result = response.json().get('data')
                    self.destroy()
                else:
                    messagebox.showerror("Ошибка", f"Ошибка: {response.status_code}")
        
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при сохранении: {str(e)}")
    
    def cancel(self):
        """Закрыть диалог"""
        self.destroy()
