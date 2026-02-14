"""
Диалог карточки товара на складе - добавление и редактирование
"""
import tkinter as tk
from tkinter import ttk, messagebox
import requests


class WarehouseDialog(tk.Toplevel):
    def __init__(self, parent, api_url, token, item_data=None):
        super().__init__(parent)
        self.api_url = api_url
        self.token = token
        self.item_data = item_data
        self.result = None
        
        self.title("Карточка товара" if not item_data else f"Редактирование товара #{item_data.get('id')}")
        self.geometry("700x550")
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
        title_label = ttk.Label(main_frame, text="Информация о товаре на складе", 
                               font=("Arial", 12, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        # Название (обязательное)
        ttk.Label(main_frame, text="Название:*").grid(row=1, column=0, sticky="w", pady=5)
        self.item_name = ttk.Entry(main_frame, width=45)
        self.item_name.grid(row=1, column=1, sticky="ew", pady=5)
        
        # Артикул (обязательный)
        ttk.Label(main_frame, text="Артикул:*").grid(row=2, column=0, sticky="w", pady=5)
        self.article_number = ttk.Entry(main_frame, width=45)
        self.article_number.grid(row=2, column=1, sticky="ew", pady=5)
        
        # Категория
        ttk.Label(main_frame, text="Категория:").grid(row=3, column=0, sticky="w", pady=5)
        self.category = ttk.Combobox(main_frame, width=42, values=[
            "Детали ПК", "Кабели", "Охлаждение", "Разъемы", "Расходники",
            "ПО", "Периферия", "Прочее"
        ])
        self.category.grid(row=3, column=1, sticky="ew", pady=5)
        
        # Количество
        ttk.Label(main_frame, text="Количество:*").grid(row=4, column=0, sticky="w", pady=5)
        self.quantity = ttk.Entry(main_frame, width=45)
        self.quantity.grid(row=4, column=1, sticky="ew", pady=5)
        
        # Цена за единицу
        ttk.Label(main_frame, text="Цена (₽):*").grid(row=5, column=0, sticky="w", pady=5)
        self.unit_price = ttk.Entry(main_frame, width=45)
        self.unit_price.grid(row=5, column=1, sticky="ew", pady=5)
        
        # Местоположение
        ttk.Label(main_frame, text="Расположение:").grid(row=6, column=0, sticky="w", pady=5)
        self.location = ttk.Entry(main_frame, width=45)
        self.location.grid(row=6, column=1, sticky="ew", pady=5)
        
        # Поставщик
        ttk.Label(main_frame, text="Поставщик:").grid(row=7, column=0, sticky="w", pady=5)
        self.supplier = ttk.Entry(main_frame, width=45)
        self.supplier.grid(row=7, column=1, sticky="ew", pady=5)
        
        # Примечания
        ttk.Label(main_frame, text="Примечания:").grid(row=8, column=0, sticky="nw", pady=5)
        self.notes = tk.Text(main_frame, height=4, width=45)
        self.notes.grid(row=8, column=1, sticky="ew", pady=5)
        
        # Информация
        info_frame = ttk.LabelFrame(main_frame, text="Информация", padding="5")
        info_frame.grid(row=9, column=0, columnspan=2, sticky="ew", pady=10)
        
        self.info_label = ttk.Label(info_frame, text="Новый товар", foreground="blue")
        self.info_label.pack()
        
        # Кнопки
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=10, column=0, columnspan=2, sticky="ew", pady=10)
        
        ttk.Button(btn_frame, text="Сохранить", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=self.cancel).pack(side=tk.LEFT, padx=5)
        
        main_frame.columnconfigure(1, weight=1)
    
    def load_data(self):
        """Загрузить данные товара"""
        if self.item_data:
            self.item_name.insert(0, self.item_data.get('item_name', ''))
            self.article_number.insert(0, self.item_data.get('article_number', ''))
            self.category.set(self.item_data.get('category', ''))
            self.quantity.insert(0, str(self.item_data.get('quantity', '')))
            self.unit_price.insert(0, str(self.item_data.get('unit_price', '')))
            self.location.insert(0, self.item_data.get('location', ''))
            self.supplier.insert(0, self.item_data.get('supplier', ''))
            self.notes.insert('1.0', self.item_data.get('notes', ''))
            self.info_label.config(
                text=f"Товар создан: {self.item_data.get('created_at', 'N/A')}"
            )
    
    def save(self):
        """Сохранить данные товара"""
        item_name = self.item_name.get().strip()
        article_number = self.article_number.get().strip()
        
        if not item_name or not article_number:
            messagebox.showwarning("Ошибка", "Название и артикул обязательны!")
            return
        
        try:
            quantity = int(self.quantity.get() or 0)
        except:
            messagebox.showwarning("Ошибка", "Некорректное количество!")
            return
        
        try:
            price = float(self.unit_price.get() or 0)
        except:
            messagebox.showwarning("Ошибка", "Некорректная цена!")
            return
        
        data = {
            'item_name': item_name,
            'article_number': article_number,
            'category': self.category.get(),
            'quantity': quantity,
            'unit_price': price,
            'location': self.location.get().strip(),
            'supplier': self.supplier.get().strip(),
            'notes': self.notes.get('1.0', 'end-1c').strip()
        }
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            
            if self.item_data:
                url = f"{self.api_url}/api/warehouse/{self.item_data['id']}"
                response = requests.put(url, json=data, headers=headers)
                if response.status_code == 200:
                    messagebox.showinfo("Успех", "Товар обновлен")
                    self.result = response.json().get('data')
                    self.destroy()
                else:
                    messagebox.showerror("Ошибка", f"Ошибка: {response.status_code}")
            else:
                url = f"{self.api_url}/api/warehouse"
                response = requests.post(url, json=data, headers=headers)
                if response.status_code == 201:
                    messagebox.showinfo("Успех", "Товар добавлен")
                    self.result = response.json().get('data')
                    self.destroy()
                else:
                    messagebox.showerror("Ошибка", f"Ошибка: {response.status_code}")
        
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при сохранении: {str(e)}")
    
    def cancel(self):
        """Закрыть диалог"""
        self.destroy()
