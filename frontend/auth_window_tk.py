"""
Окно авторизации PromoService на tkinter
"""
import tkinter as tk
from tkinter import messagebox, ttk
import requests


class LoginWindow:
    def __init__(self, root, api_url):
        self.root = root
        self.api_url = api_url
        self.token = None
        self.user_data = None
        
        self.root.title("PromoService V0002 - Авторизация")
        self.root.geometry("400x350")
        self.root.resizable(False, False)
        
        # Центрируем окно
        self.root.geometry("+%d+%d" % (self.root.winfo_screenwidth()//2 - 250, 
                                        self.root.winfo_screenheight()//2 - 255))
        
        self.create_ui()
        self.check_api_connection()
    
    def create_ui(self):
        """Создать интерфейс авторизации"""
        # Заголовок
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill=tk.X, padx=20, pady=20)
        
        title = ttk.Label(title_frame, text="PromoService V0002", font=("Arial", 16, "bold"))
        title.pack()
        
        subtitle = ttk.Label(title_frame, text="Управление сервисным центром", font=("Arial", 10))
        subtitle.pack()
        
        # Статус подключения
        status_frame = ttk.LabelFrame(self.root, text="Статус подключения")
        status_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.status_label = ttk.Label(status_frame, text="Проверка подключения к API...", foreground="orange")
        self.status_label.pack(padx=10, pady=10)
        
        # Форма входа
        form_frame = ttk.LabelFrame(self.root, text="Вход в систему")
        form_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Username
        ttk.Label(form_frame, text="Имя пользователя:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        self.username_entry = ttk.Entry(form_frame, width=30)
        self.username_entry.pack(padx=10, pady=(0, 10))
        self.username_entry.focus()
        
        # Password
        ttk.Label(form_frame, text="Пароль:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        self.password_entry = ttk.Entry(form_frame, width=30, show="*")
        self.password_entry.pack(padx=10, pady=(0, 10))
        
        # Bind Enter key
        self.password_entry.bind("<Return>", lambda e: self.do_login())
        
        # Кнопки
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.login_btn = ttk.Button(btn_frame, text="Вход", command=self.do_login)
        self.login_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.exit_btn = ttk.Button(btn_frame, text="Выход", command=self.root.quit)
        self.exit_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Footer
        footer_frame = ttk.Frame(self.root)
        footer_frame.pack(fill=tk.X, padx=20, pady=10)
        
        footer = ttk.Label(footer_frame, text="Стандартный пользователь: admin / admin123", font=("Arial", 8))
        footer.pack()
    
    def check_api_connection(self):
        """Проверить подключение к API"""
        try:
            response = requests.get(f"{self.api_url}/api/health", timeout=5)
            if response.status_code == 200:
                self.status_label.config(text="✓ Подключено к API", foreground="green")
                self.login_btn.config(state=tk.NORMAL)
            else:
                self.status_label.config(text="✗ Ошибка подключения", foreground="red")
                self.login_btn.config(state=tk.DISABLED)
        except Exception as e:
            self.status_label.config(text=f"✗ Ошибка: {str(e)}", foreground="red")
            self.login_btn.config(state=tk.DISABLED)
    
    def do_login(self):
        """Выполнить вход"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showwarning("Ошибка", "Пожалуйста, введите имя пользователя и пароль")
            return
        
        self.login_btn.config(state=tk.DISABLED, text="Вход...")
        
        try:
            response = requests.post(
                f"{self.api_url}/api/auth/login",
                json={"username": username, "password": password},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('token')
                self.user_data = data.get('user', {})
                self.root.quit()
            else:
                messagebox.showerror("Ошибка входа", f"Не удалось войти в систему")
                self.login_btn.config(state=tk.NORMAL, text="Вход")
                self.password_entry.delete(0, tk.END)
                self.password_entry.focus()
        
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при попытке входа: {str(e)}")
            self.login_btn.config(state=tk.NORMAL, text="Вход")


def show_auth_dialog(api_url):
    """Показать окно авторизации"""
    root = tk.Tk()
    login_window = LoginWindow(root, api_url)
    root.mainloop()
    
    return login_window.token, login_window.user_data
