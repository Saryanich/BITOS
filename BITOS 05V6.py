import time
import sys
import os
import subprocess
import shutil
import platform
import math
import random
import json
import hashlib
import string
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    print("⚠️ Для блокировки клавиш установите: pip install keyboard")

def shutdown_windows():
    """Реальное выключение Windows"""
    if platform.system() == "Windows":
        try:
            subprocess.run(["shutdown", "/s", "/t", "1", "/f"], shell=True)
        except:
            try:
                os.system("shutdown /s /t 1 /f")
            except:
                messagebox.showerror("Ошибка", "Не удалось выключить компьютер")

def restart_windows():
    """Реальная перезагрузка Windows"""
    if platform.system() == "Windows":
        try:
            subprocess.run(["shutdown", "/r", "/t", "1", "/f"], shell=True)
        except:
            try:
                os.system("shutdown /r /t 1 /f")
            except:
                messagebox.showerror("Ошибка", "Не удалось перезагрузить компьютер")

# Для работы с изображениями
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️ Для галереи установите Pillow: pip install Pillow")

# Для определения флешек (Windows)
try:
    import win32api
    import win32file
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("⚠️ Для определения флешек установите pywin32")

# Попытка импорта requests (для интернета)
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


# ==================== КЛАСС 1: SplashScreen ====================
class SplashScreen:
    """Экран загрузки с анимацией"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.state('zoomed')
        self.root.configure(bg='#2C3E50')
        
        self.width = self.root.winfo_screenwidth()
        self.height = self.root.winfo_screenheight()
        
        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height,
                                highlightthickness=0, bg='#2C3E50')
        self.canvas.pack()
        
        self.create_gradient()
        
        self.canvas.create_text(self.width//2, self.height//2 - 100,
                               text="BITOS",
                               font=('Segoe UI', 80, 'bold'),
                               fill='white')
        
        self.canvas.create_text(self.width//2, self.height//2 - 20,
                               text="Version 05V6",
                               font=('Segoe UI', 24),
                               fill='#ECF0F1')
        
        bar_width = 600
        self.progress_bg = self.canvas.create_rectangle(
            self.width//2 - bar_width//2, self.height//2 + 50,
            self.width//2 + bar_width//2, self.height//2 + 80,
            fill='#34495E', outline=''
        )
        
        self.progress_bar = self.canvas.create_rectangle(
            self.width//2 - bar_width//2, self.height//2 + 50,
            self.width//2 - bar_width//2, self.height//2 + 80,
            fill='#3498DB', outline=''
        )
        
        self.status_text = self.canvas.create_text(
            self.width//2, self.height//2 + 100,
            text="Загрузка системы...",
            font=('Segoe UI', 14),
            fill='#ECF0F1'
        )
        
        self.details_text = self.canvas.create_text(
            self.width//2, self.height//2 + 130,
            text="",
            font=('Segoe UI', 11),
            fill='#BDC3C7'
        )
        
        self.particles = []
        for _ in range(50):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            speed = random.uniform(0.5, 3)
            size = random.randint(1, 4)
            self.particles.append([x, y, speed, size])
        
        self.animate_particles()
        self.root.update()
    
    def create_gradient(self):
        for i in range(self.height):
            r = int(41 + i/self.height * 30)
            g = int(128 + i/self.height * 30)
            b = int(185 + i/self.height * 30)
            color = f'#{r:02x}{g:02x}{b:02x}'
            self.canvas.create_line(0, i, self.width, i, fill=color, tags='gradient')
    
    def animate_particles(self):
        self.canvas.delete('particle')
        for particle in self.particles:
            particle[1] += particle[2]
            if particle[1] > self.height:
                particle[1] = 0
                particle[0] = random.randint(0, self.width)
            x, y, _, size = particle
            self.canvas.create_oval(x-size, y-size, x+size, y+size,
                                   fill='white', outline='', tags='particle')
        self.root.after(50, self.animate_particles)
    
    def update_progress(self, value, status="", details=""):
        bar_width = 600
        x = self.width//2 - bar_width//2 + (bar_width * value // 100)
        self.canvas.coords(self.progress_bar, 
                          self.width//2 - bar_width//2, self.height//2 + 50,
                          x, self.height//2 + 80)
        self.canvas.itemconfig(self.status_text, text=status)
        self.canvas.itemconfig(self.details_text, text=details)
        self.root.update()
    
    def close(self):
        for i in range(10, 0, -1):
            self.root.attributes('-alpha', i/10)
            self.root.update()
            time.sleep(0.03)
        self.root.destroy()

# ==================== КЛАСС 2: LoginScreen (ПОЛНОСТЬЮ) ====================
class LoginScreen:
    """Экран входа в систему с защитой от брутфорса"""
    
    def __init__(self, on_login, bitos_instance=None):
        self.on_login = on_login
        self.bitos = bitos_instance
        self.root = tk.Tk()
        self.root.title("BITOS - Вход")
        self.root.overrideredirect(True)
        self.root.state('zoomed')
        self.width = self.root.winfo_screenwidth()
        self.height = self.root.winfo_screenheight()
        self.root.configure(bg='#2C3E50')
        
        # Защита от брутфорса
        self.failed_attempts = 0
        self.max_attempts = 5
        self.lock_time = 0
        self.lock_duration = 60
        
        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height,
                               highlightthickness=0, bg='#2C3E50')
        self.canvas.place(x=0, y=0, width=self.width, height=self.height)
        
        for i in range(self.height):
            color = f'#{int(44 + i/self.height * 30):02x}{int(62 + i/self.height * 30):02x}{int(80 + i/self.height * 30):02x}'
            self.canvas.create_line(0, i, self.width, i, fill=color, tags='gradient')
        
        self.stars = []
        for _ in range(100):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            size = random.randint(1, 3)
            speed = random.uniform(0.1, 0.5)
            brightness = random.randint(50, 255)
            self.stars.append([x, y, size, speed, brightness])
        
        self.animate_stars()
        self.create_ui()
        self.create_power_buttons()
    
    def create_ui(self):
        panel_width, panel_height = 500, 480
        panel_x = (self.width - panel_width) // 2
        panel_y = (self.height - panel_height) // 2
        
        self.canvas.create_rectangle(panel_x, panel_y, panel_x + panel_width, panel_y + panel_height,
                                     fill='#FFFFFF', outline='#3498DB', width=2, tags='ui')
        
        self.canvas.create_text(panel_x + panel_width//2, panel_y + 80,
                               text="BITOS", font=('Segoe UI', 48, 'bold'), fill='#2C3E50', tags='ui')
        self.canvas.create_text(panel_x + panel_width//2, panel_y + 130,
                               text="Вход в систему", font=('Segoe UI', 14), fill='#7F8C8D', tags='ui')
        
        self.canvas.create_text(panel_x + 80, panel_y + 180,
                               text="👤 Пользователь:", font=('Segoe UI', 12), fill='#34495E', anchor='w', tags='ui')
        self.canvas.create_text(panel_x + 80, panel_y + 260,
                               text="🔒 PIN-код:", font=('Segoe UI', 12), fill='#34495E', anchor='w', tags='ui')
        
        self.username_entry = tk.Entry(self.root, bg='#ECF0F1', fg='#2C3E50',
                                       font=('Segoe UI', 12), bd=0, highlightthickness=2,
                                       highlightcolor='#3498DB', highlightbackground='#BDC3C7')
        self.username_entry.place(x=panel_x + 80, y=panel_y + 210, width=340, height=40)
        self.username_entry.insert(0, "User")
        
        self.pin_entry = tk.Entry(self.root, bg='#ECF0F1', fg='#2C3E50',
                                 font=('Segoe UI', 12), bd=0, highlightthickness=2,
                                 highlightcolor='#3498DB', highlightbackground='#BDC3C7', show='•')
        self.pin_entry.place(x=panel_x + 80, y=panel_y + 290, width=340, height=40)
        self.pin_entry.bind('<Return>', lambda e: self.do_login())
        
        self.login_btn = tk.Button(self.root, text="Войти в систему", bg='#3498DB', fg='white',
                                  font=('Segoe UI', 12, 'bold'), bd=0, cursor='hand2', command=self.do_login)
        self.login_btn.place(x=panel_x + 80, y=panel_y + 350, width=340, height=45)
        self.login_btn.bind('<Enter>', lambda e: self.login_btn.config(bg='#2980B9'))
        self.login_btn.bind('<Leave>', lambda e: self.login_btn.config(bg='#3498DB'))
        
        self.status_label = tk.Label(self.root, text='', bg='white', fg='#E74C3C', font=('Segoe UI', 11))
        self.status_label.place(x=panel_x + 80, y=panel_y + 400, width=340)
        
        self.change_pin_btn = tk.Button(self.root, text="Изменить PIN-код", bg='#95A5A6', fg='white',
                                        font=('Segoe UI', 10), bd=0, cursor='hand2', command=self.change_pin_dialog)
        self.change_pin_btn.place(x=panel_x + 80, y=panel_y + 435, width=340, height=30)
        self.change_pin_btn.bind('<Enter>', lambda e: self.change_pin_btn.config(bg='#7F8C8D'))
        self.change_pin_btn.bind('<Leave>', lambda e: self.change_pin_btn.config(bg='#95A5A6'))
        
        for widget in [self.username_entry, self.pin_entry, self.login_btn, self.status_label, self.change_pin_btn]:
            widget.lift()
    
    def create_power_buttons(self):
        """Создает кнопки выключения и перезагрузки в нижнем правом углу"""
        # Кнопка выключения
        shutdown_btn = tk.Button(self.root, text='⏻ Выключить', bg='#E74C3C', fg='white',
                                 font=('Segoe UI', 11, 'bold'), bd=0, padx=20, pady=10,
                                 command=self.shutdown_system)
        shutdown_btn.place(x=self.width - 200, y=self.height - 80)
        shutdown_btn.lift()
        shutdown_btn.bind('<Enter>', lambda e: shutdown_btn.config(bg='#C0392B'))
        shutdown_btn.bind('<Leave>', lambda e: shutdown_btn.config(bg='#E74C3C'))
        
        # Кнопка перезагрузки
        restart_btn = tk.Button(self.root, text='🔄 Перезагрузить', bg='#E67E22', fg='white',
                                font=('Segoe UI', 11, 'bold'), bd=0, padx=20, pady=10,
                                command=self.restart_system)
        restart_btn.place(x=self.width - 400, y=self.height - 80)
        restart_btn.lift()
        restart_btn.bind('<Enter>', lambda e: restart_btn.config(bg='#D35400'))
        restart_btn.bind('<Leave>', lambda e: restart_btn.config(bg='#E67E22'))
    
    def animate_stars(self):
        self.canvas.delete('star')
        for star in self.stars:
            star[4] += random.randint(-5, 5)
            star[4] = max(50, min(255, star[4]))
            star[1] += star[3]
            if star[1] > self.height:
                star[1] = 0
                star[0] = random.randint(0, self.width)
            x, y, size, _, brightness = star
            color = f'#{brightness:02x}{brightness:02x}{brightness:02x}'
            self.canvas.create_oval(x-size, y-size, x+size, y+size, fill=color, outline='', tags='star')
        self.root.after(50, self.animate_stars)
    
    def get_pin_hash(self, pin):
        return hashlib.sha256(pin.encode()).hexdigest()
    
    def load_pin(self):
        pin_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "System", "Security", "pin.hash")
        default_pin = "1234"
        if os.path.exists(pin_file):
            try:
                with open(pin_file, 'r') as f:
                    saved_hash = f.read().strip()
                    if saved_hash:
                        return saved_hash
            except:
                pass
        self.save_pin(default_pin)
        return self.get_pin_hash(default_pin)
    
    def save_pin(self, new_pin):
        pin_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "System", "Security", "pin.hash")
        os.makedirs(os.path.dirname(pin_file), exist_ok=True)
        try:
            with open(pin_file, 'w') as f:
                f.write(self.get_pin_hash(new_pin))
            return True
        except:
            return False
    
    def change_pin_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Изменить PIN-код")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg='#F5F7FA')
        dialog.resizable(False, False)
        
        x = (dialog.winfo_screenwidth() - 400) // 2
        y = (dialog.winfo_screenheight() - 300) // 2
        dialog.geometry(f'+{x}+{y}')
        
        tk.Label(dialog, text="Изменение PIN-кода", font=('Segoe UI', 16, 'bold'),
                bg='#F5F7FA', fg='#2C3E50').pack(pady=15)
        
        tk.Label(dialog, text="Текущий PIN-код:", bg='#F5F7FA', fg='#2C3E50', font=('Segoe UI', 11)).pack(pady=5)
        old_pin_entry = tk.Entry(dialog, font=('Segoe UI', 12), show='•', width=20)
        old_pin_entry.pack(pady=5)
        
        tk.Label(dialog, text="Новый PIN-код (4-8 цифр):", bg='#F5F7FA', fg='#2C3E50', font=('Segoe UI', 11)).pack(pady=5)
        new_pin_entry = tk.Entry(dialog, font=('Segoe UI', 12), show='•', width=20)
        new_pin_entry.pack(pady=5)
        
        tk.Label(dialog, text="Подтвердите новый PIN-код:", bg='#F5F7FA', fg='#2C3E50', font=('Segoe UI', 11)).pack(pady=5)
        confirm_pin_entry = tk.Entry(dialog, font=('Segoe UI', 12), show='•', width=20)
        confirm_pin_entry.pack(pady=5)
        
        status_label = tk.Label(dialog, text="", bg='#F5F7FA', fg='#E74C3C', font=('Segoe UI', 10))
        status_label.pack(pady=5)
        
        def do_change():
            old_pin = old_pin_entry.get().strip()
            new_pin = new_pin_entry.get().strip()
            confirm_pin = confirm_pin_entry.get().strip()
            saved_hash = self.load_pin()
            
            if self.get_pin_hash(old_pin) != saved_hash:
                status_label.config(text="❌ Неверный текущий PIN-код")
                return
            if not new_pin.isdigit():
                status_label.config(text="❌ PIN-код должен состоять только из цифр")
                return
            if len(new_pin) < 4 or len(new_pin) > 8:
                status_label.config(text="❌ PIN-код должен быть от 4 до 8 цифр")
                return
            if new_pin != confirm_pin:
                status_label.config(text="❌ PIN-коды не совпадают")
                return
            if self.save_pin(new_pin):
                status_label.config(text="✅ PIN-код успешно изменён!", fg='#27AE60')
                if self.bitos and hasattr(self.bitos, 'security'):
                    self.bitos.security.log_pin_change("User")
                dialog.after(1500, dialog.destroy)
            else:
                status_label.config(text="❌ Ошибка сохранения PIN-кода")
        
        tk.Button(dialog, text="Изменить PIN", bg='#3498DB', fg='white',
                 font=('Segoe UI', 11), bd=0, padx=20, pady=8, command=do_change).pack(pady=10)
        tk.Button(dialog, text="Отмена", bg='#95A5A6', fg='white',
                 font=('Segoe UI', 10), bd=0, padx=20, pady=5, command=dialog.destroy).pack()
    
    def shutdown_system(self):
        """Выключение компьютера"""
        if messagebox.askyesno("Выключение", "Вы действительно хотите выключить компьютер?"):
            if self.bitos and hasattr(self.bitos, 'security'):
                self.bitos.security.log_access("System", "SHUTDOWN", "SUCCESS")
            self.root.destroy()
            shutdown_windows()
    
    def restart_system(self):
        """Перезагрузка компьютера"""
        if messagebox.askyesno("Перезагрузка", "Вы действительно хотите перезагрузить компьютер?"):
            if self.bitos and hasattr(self.bitos, 'security'):
                self.bitos.security.log_access("System", "RESTART", "SUCCESS")
            self.root.destroy()
            restart_windows()
    
    def do_login(self):
        # Проверка блокировки
        if self.lock_time > time.time():
            remaining = int(self.lock_time - time.time())
            self.status_label.config(text=f'⏰ Система заблокирована на {remaining} секунд')
            return
        
        username = self.username_entry.get().strip()
        pin = self.pin_entry.get().strip()
        
        if not username:
            self.status_label.config(text='❌ Введите имя пользователя')
            return
        
        saved_hash = self.load_pin()
        if self.get_pin_hash(pin) != saved_hash:
            self.failed_attempts += 1
            remaining = self.max_attempts - self.failed_attempts
            
            if self.bitos and hasattr(self.bitos, 'security'):
                self.bitos.security.log_login_attempt(username, False)
            
            if self.failed_attempts >= self.max_attempts:
                self.lock_time = time.time() + self.lock_duration
                self.status_label.config(text=f'❌ Превышено количество попыток! Блокировка на {self.lock_duration} сек')
                if self.bitos and hasattr(self.bitos, 'security'):
                    self.bitos.security.log_security_event("BRUTE_FORCE_ATTEMPT", f"User: {username}")
                self.pin_entry.delete(0, tk.END)
                self.failed_attempts = 0
            else:
                self.status_label.config(text=f'❌ Неверный PIN-код! Осталось попыток: {remaining}')
                self.pin_entry.delete(0, tk.END)
            return
        
        # Успешный вход
        self.failed_attempts = 0
        self.status_label.config(text='✅ Вход выполнен...', fg='#27AE60')
        self.root.update()
        
        if self.bitos and hasattr(self.bitos, 'security'):
            self.bitos.security.log_login_attempt(username, True)
            self.bitos.security.log_access(username, "LOGIN", "SUCCESS")
        
        time.sleep(0.5)
        self.root.destroy()
        self.on_login(username)
    
    def run(self):
        self.root.mainloop()

# ==================== КЛАСС 3: SecurityManager ====================
class SecurityManager:
    """Менеджер безопасности и логирования BITOS"""
    
    def __init__(self, bitos):
        self.bitos = bitos
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Пути к логам
        self.logs_path = bitos.system_paths["logs"]
        
        # Лог-файлы
        self.log_files = {
            "access": os.path.join(self.logs_path, "access.log"),
            "error": os.path.join(self.logs_path, "error.log"),
            "audit": os.path.join(self.logs_path, "audit.log"),
            "apps": os.path.join(self.logs_path, "applications.log"),
            "files": os.path.join(self.logs_path, "files.log"),
            "security": os.path.join(self.logs_path, "security.log"),
        }
        
        # Статистика сессии
        self.session_stats = {
            'start_time': datetime.now(),
            'apps_launched': [],
            'files_accessed': [],
            'files_deleted': [],
            'files_moved': [],
            'folders_created': [],
            'shortcuts_created': [],
            'shortcuts_deleted': [],
            'errors': [],
            'security_events': []
        }
        
        self.log_audit(f"SESSION_START: User {bitos.current_user} started session {self.session_id}")
    
    def _write_log(self, log_name, message):
        """Запись в лог-файл"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.log_files[log_name], 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] {message}\n")
        except Exception as e:
            print(f"Ошибка записи в лог {log_name}: {e}")
    
    def log_access(self, username, action, result, details=""):
        """Лог доступа (входы/выходы)"""
        self._write_log("access", f"USER:{username} ACTION:{action} RESULT:{result} {details}")
    
    def log_error(self, module, error, details=""):
        """Лог ошибок"""
        self.session_stats['errors'].append({'time': datetime.now(), 'module': module, 'error': error})
        self._write_log("error", f"MODULE:{module} ERROR:{error} {details}")
    
    def log_audit(self, message):
        """Аудит - важные системные события"""
        self._write_log("audit", message)
    
    def log_app_launch(self, app_name, username):
        """Логирование запуска приложений"""
        self.session_stats['apps_launched'].append({'time': datetime.now(), 'app': app_name})
        self._write_log("apps", f"USER:{username} LAUNCHED:{app_name}")
    
    def log_file_access(self, username, path, action):
        """Логирование доступа к файлам"""
        self.session_stats['files_accessed'].append({'time': datetime.now(), 'path': path, 'action': action})
        self._write_log("files", f"USER:{username} ACTION:{action} PATH:{path}")
    
    def log_file_delete(self, username, path, permanent=False):
        """Логирование удаления файлов"""
        action = "PERMANENT_DELETE" if permanent else "MOVE_TO_TRASH"
        self.session_stats['files_deleted'].append({'time': datetime.now(), 'path': path, 'permanent': permanent})
        self._write_log("files", f"USER:{username} {action}:{path}")
    
    def log_file_move(self, username, src, dst):
        """Логирование перемещения файлов"""
        self.session_stats['files_moved'].append({'time': datetime.now(), 'src': src, 'dst': dst})
        self._write_log("files", f"USER:{username} MOVE:{src} -> {dst}")
    
    def log_folder_create(self, username, path):
        """Логирование создания папок"""
        self.session_stats['folders_created'].append({'time': datetime.now(), 'path': path})
        self._write_log("files", f"USER:{username} CREATE_FOLDER:{path}")
    
    def log_security_event(self, event_type, details):
        """Логирование событий безопасности"""
        self.session_stats['security_events'].append({'time': datetime.now(), 'type': event_type, 'details': details})
        self._write_log("security", f"SECURITY:{event_type} {details}")
    
    def log_shortcut_create(self, username, app_name, grid_pos):
        """Логирование создания ярлыков"""
        self.session_stats['shortcuts_created'].append({'time': datetime.now(), 'app': app_name, 'pos': grid_pos})
        self._write_log("apps", f"USER:{username} CREATE_SHORTCUT:{app_name} POS:({grid_pos[0]},{grid_pos[1]})")
    
    def log_shortcut_delete(self, username, app_name):
        """Логирование удаления ярлыков"""
        self.session_stats['shortcuts_deleted'].append({'time': datetime.now(), 'app': app_name})
        self._write_log("apps", f"USER:{username} DELETE_SHORTCUT:{app_name}")
    
    def log_theme_change(self, username, old_theme, new_theme):
        """Логирование смены темы"""
        self._write_log("audit", f"USER:{username} THEME_CHANGE:{old_theme} -> {new_theme}")
    
    def log_pin_change(self, username):
        """Логирование смены PIN-кода"""
        self._write_log("security", f"USER:{username} PIN_CHANGED")
    
    def log_login_attempt(self, username, success, ip="localhost"):
        """Логирование попытки входа"""
        status = "SUCCESS" if success else "FAILED"
        self._write_log("access", f"LOGIN_ATTEMPT USER:{username} STATUS:{status} IP:{ip}")
        if not success:
            self.log_security_event("FAILED_LOGIN", f"User:{username} IP:{ip}")
    
    def log_logout(self, username):
        """Логирование выхода"""
        self._write_log("access", f"USER:{username} LOGOUT")
    
    def log_shutdown(self, username):
        """Логирование завершения работы"""
        self._write_log("access", f"USER:{username} SHUTDOWN")
    
    def log_reboot(self, username):
        """Логирование перезагрузки"""
        self._write_log("access", f"USER:{username} REBOOT")
    
    def get_session_summary(self):
        """Получение сводки по сессии"""
        return {
            'duration': str(datetime.now() - self.session_stats['start_time']),
            'apps_launched': len(self.session_stats['apps_launched']),
            'files_accessed': len(self.session_stats['files_accessed']),
            'files_deleted': len(self.session_stats['files_deleted']),
            'errors': len(self.session_stats['errors']),
            'security_events': len(self.session_stats['security_events'])
        }


# ==================== КЛАСС 4: TrashManager ====================
class TrashManager:
    """Менеджер корзины"""
    
    def __init__(self, bitos):
        self.bitos = bitos
        self.trash_path = os.path.join(bitos.base_path, "System", "Temp", "Trash")
        self.trash_info_path = os.path.join(self.trash_path, "trash_info.json")
        os.makedirs(self.trash_path, exist_ok=True)
        self.trash_items = self.load_trash_info()
    
    def load_trash_info(self):
        if os.path.exists(self.trash_info_path):
            try:
                with open(self.trash_info_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_trash_info(self):
        try:
            with open(self.trash_info_path, 'w', encoding='utf-8') as f:
                json.dump(self.trash_items, f, indent=4, ensure_ascii=False)
        except:
            pass
    
    def move_to_trash(self, paths):
        moved_items = []
        for path in paths:
            if not os.path.exists(path):
                continue
            base_name = os.path.basename(path)
            trash_name = base_name
            counter = 1
            while os.path.exists(os.path.join(self.trash_path, trash_name)):
                name, ext = os.path.splitext(base_name)
                trash_name = f"{name}_{counter}{ext}"
                counter += 1
            trash_dest = os.path.join(self.trash_path, trash_name)
            try:
                shutil.move(path, trash_dest)
                item_info = {
                    'original_path': path,
                    'trash_name': trash_name,
                    'deleted_time': datetime.now().isoformat(),
                    'is_dir': os.path.isdir(trash_dest),
                    'size': self.get_size(trash_dest)
                }
                self.trash_items[trash_name] = item_info
                moved_items.append(item_info)
                if self.bitos and hasattr(self.bitos, 'security'):
                    self.bitos.security.log_file_delete(self.bitos.current_user, path, permanent=False)
            except:
                pass
        self.save_trash_info()
        return moved_items
    
    def get_size(self, path):
        if os.path.isfile(path):
            return os.path.getsize(path)
        elif os.path.isdir(path):
            total = 0
            for root, dirs, files in os.walk(path):
                for f in files:
                    total += os.path.getsize(os.path.join(root, f))
            return total
        return 0
    
    def restore_item(self, trash_name):
        if trash_name not in self.trash_items:
            return False, "Файл не найден в корзине"
        item = self.trash_items[trash_name]
        original_path = item['original_path']
        trash_path = os.path.join(self.trash_path, trash_name)
        if not os.path.exists(trash_path):
            del self.trash_items[trash_name]
            self.save_trash_info()
            return False, "Файл отсутствует в корзине"
        if os.path.exists(original_path):
            base, ext = os.path.splitext(original_path)
            counter = 1
            while os.path.exists(f"{base}_restored_{counter}{ext}"):
                counter += 1
            original_path = f"{base}_restored_{counter}{ext}"
        try:
            os.makedirs(os.path.dirname(original_path), exist_ok=True)
            shutil.move(trash_path, original_path)
            del self.trash_items[trash_name]
            self.save_trash_info()
            return True, original_path
        except Exception as e:
            return False, str(e)
    
    def delete_permanently(self, trash_name):
        if trash_name not in self.trash_items:
            return False, "Файл не найден в корзине"
        trash_path = os.path.join(self.trash_path, trash_name)
        try:
            if os.path.exists(trash_path):
                if os.path.isdir(trash_path):
                    shutil.rmtree(trash_path)
                else:
                    os.remove(trash_path)
            del self.trash_items[trash_name]
            self.save_trash_info()
            return True, "Файл удалён навсегда"
        except Exception as e:
            return False, str(e)
    
    def empty_trash(self):
        try:
            for trash_name in list(self.trash_items.keys()):
                trash_path = os.path.join(self.trash_path, trash_name)
                if os.path.exists(trash_path):
                    if os.path.isdir(trash_path):
                        shutil.rmtree(trash_path)
                    else:
                        os.remove(trash_path)
            self.trash_items = {}
            self.save_trash_info()
            return True, "Корзина очищена"
        except Exception as e:
            return False, str(e)
    
    def get_trash_items(self):
        items = []
        for trash_name, info in self.trash_items.items():
            info['trash_name'] = trash_name
            items.append(info)
        items.sort(key=lambda x: x.get('deleted_time', ''), reverse=True)
        return items


# ==================== КЛАСС 5: TrashWindow ====================
class TrashWindow:
    """Окно корзины"""
    
    def __init__(self, parent, bitos):
        self.parent = parent
        self.bitos = bitos
        self.trash_manager = TrashManager(bitos)
        self.create_window()
        self.load_trash_items()
    
    def create_window(self):
        self.window = tk.Toplevel(self.parent)
        self.window.title("🗑 Корзина BITOS")
        self.window.geometry("900x600")
        self.window.transient(self.parent)
        self.window.configure(bg='#F5F7FA')
        
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 900) // 2
        y = (self.window.winfo_screenheight() - 600) // 2
        self.window.geometry(f'+{x}+{y}')
        
        self.create_toolbar()
        self.create_content_area()
        self.create_status_bar()
        self.create_context_menu()
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def create_toolbar(self):
        toolbar = tk.Frame(self.window, bg='#E0E0E0', height=50)
        toolbar.pack(fill=tk.X, padx=1, pady=1)
        
        tk.Button(toolbar, text="↻ Обновить", bg='#E0E0E0', fg='#2C3E50',
                 font=('Segoe UI', 10), bd=0, padx=15, pady=5,
                 command=self.load_trash_items).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="♻ Восстановить", bg='#27AE60', fg='white',
                 font=('Segoe UI', 10), bd=0, padx=15, pady=5,
                 command=self.restore_selected).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="🗑 Удалить навсегда", bg='#E74C3C', fg='white',
                 font=('Segoe UI', 10), bd=0, padx=15, pady=5,
                 command=self.delete_selected).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="🧹 Очистить корзину", bg='#E67E22', fg='white',
                 font=('Segoe UI', 10), bd=0, padx=15, pady=5,
                 command=self.empty_trash).pack(side=tk.LEFT, padx=5)
        
        self.info_label = tk.Label(toolbar, text="", bg='#E0E0E0', fg='#2C3E50', font=('Segoe UI', 10))
        self.info_label.pack(side=tk.RIGHT, padx=15)
    
    def create_content_area(self):
        columns = ('Имя', 'Оригинальный путь', 'Дата удаления', 'Размер', 'Тип')
        self.tree = ttk.Treeview(self.window, columns=columns, show='headings', height=20)
        
        self.tree.heading('Имя', text='Имя файла')
        self.tree.heading('Оригинальный путь', text='Оригинальный путь')
        self.tree.heading('Дата удаления', text='Дата удаления')
        self.tree.heading('Размер', text='Размер')
        self.tree.heading('Тип', text='Тип')
        
        self.tree.column('Имя', width=200)
        self.tree.column('Оригинальный путь', width=300)
        self.tree.column('Дата удаления', width=150)
        self.tree.column('Размер', width=100)
        self.tree.column('Тип', width=100)
        
        scrollbar = ttk.Scrollbar(self.window, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10, padx=(0, 10))
        
        self.tree.bind('<Button-3>', self.show_context_menu)
        self.tree.bind('<Double-1>', lambda e: self.restore_selected())
    
    def create_status_bar(self):
        self.status_bar = tk.Frame(self.window, bg='#E0E0E0', height=25)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_label = tk.Label(self.status_bar, bg='#E0E0E0', fg='#2C3E50', font=('Segoe UI', 9), anchor='w')
        self.status_label.pack(side=tk.LEFT, padx=10)
        self.size_label = tk.Label(self.status_bar, bg='#E0E0E0', fg='#2C3E50', font=('Segoe UI', 9))
        self.size_label.pack(side=tk.RIGHT, padx=10)
    
    def create_context_menu(self):
        self.context_menu = tk.Menu(self.window, tearoff=0, bg='#2C3E50', fg='white', activebackground='#3498DB')
        self.context_menu.add_command(label="♻ Восстановить", command=self.restore_selected)
        self.context_menu.add_command(label="🗑 Удалить навсегда", command=self.delete_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Свойства", command=self.show_properties)
    
    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def load_trash_items(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        items = self.trash_manager.get_trash_items()
        if not items:
            self.tree.insert('', tk.END, values=('Корзина пуста', '', '', '', ''))
            self.status_label.config(text="Корзина пуста")
            self.size_label.config(text="")
            return
        total_size = 0
        for item in items:
            size = item.get('size', 0)
            total_size += size
            size_str = self.format_size(size)
            date_str = item.get('deleted_time', '')[:19].replace('T', ' ')
            file_type = "Папка" if item.get('is_dir') else "Файл"
            self.tree.insert('', tk.END, values=(
                os.path.basename(item.get('trash_name', '')),
                item.get('original_path', ''),
                date_str,
                size_str,
                file_type
            ), tags=(item.get('trash_name'),))
        self.status_label.config(text=f"Элементов в корзине: {len(items)}")
        self.size_label.config(text=f"Общий размер: {self.format_size(total_size)}")
    
    def format_size(self, size):
        for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} ТБ"
    
    def get_selected_trash_names(self):
        selected = []
        for item in self.tree.selection():
            values = self.tree.item(item)['values']
            if values and values[0] != 'Корзина пуста':
                selected.append(self.tree.item(item)['tags'][0])
        return selected
    
    def restore_selected(self):
        selected = self.get_selected_trash_names()
        if not selected:
            messagebox.showinfo("Информация", "Выберите элементы для восстановления")
            return
        restored = 0
        errors = []
        for trash_name in selected:
            success, result = self.trash_manager.restore_item(trash_name)
            if success:
                restored += 1
            else:
                errors.append(f"{trash_name}: {result}")
        if restored > 0:
            messagebox.showinfo("Успех", f"Восстановлено элементов: {restored}")
        if errors:
            messagebox.showerror("Ошибки", "\n".join(errors[:5]))
        self.load_trash_items()
    
    def delete_selected(self):
        selected = self.get_selected_trash_names()
        if not selected:
            messagebox.showinfo("Информация", "Выберите элементы для удаления")
            return
        msg = f"Удалить {len(selected)} элементов навсегда?" if len(selected) > 1 else "Удалить выбранный элемент навсегда?"
        if not messagebox.askyesno("Подтверждение", msg):
            return
        deleted = 0
        errors = []
        for trash_name in selected:
            success, result = self.trash_manager.delete_permanently(trash_name)
            if success:
                deleted += 1
            else:
                errors.append(f"{trash_name}: {result}")
        if deleted > 0:
            messagebox.showinfo("Успех", f"Удалено навсегда: {deleted}")
        if errors:
            messagebox.showerror("Ошибки", "\n".join(errors[:5]))
        self.load_trash_items()
    
    def empty_trash(self):
        items = self.trash_manager.get_trash_items()
        if not items:
            messagebox.showinfo("Информация", "Корзина уже пуста")
            return
        if not messagebox.askyesno("Очистка корзины", f"Очистить корзину? Будет удалено {len(items)} элементов."):
            return
        success, result = self.trash_manager.empty_trash()
        if success:
            messagebox.showinfo("Успех", result)
        else:
            messagebox.showerror("Ошибка", result)
        self.load_trash_items()
    
    def show_properties(self):
        selected = self.get_selected_trash_names()
        if not selected:
            return
        items = self.trash_manager.get_trash_items()
        for item in items:
            if item.get('trash_name') == selected[0]:
                info = [
                    f"Имя в корзине: {item.get('trash_name')}",
                    f"Оригинальный путь: {item.get('original_path')}",
                    f"Дата удаления: {item.get('deleted_time')}",
                    f"Тип: {'Папка' if item.get('is_dir') else 'Файл'}",
                    f"Размер: {self.format_size(item.get('size', 0))}"
                ]
                messagebox.showinfo("Свойства", "\n".join(info))
                break
    
    def on_close(self):
        self.window.destroy()

class ModernFileExplorer:
    """Современный файловый проводник с поиском файлов и уведомлениями о флешках"""
    
    FORBIDDEN_PATHS = ["C:\\"]
    
    def __init__(self, parent, bitos, start_path=None):
        self.parent = parent
        self.bitos = bitos
        self.current_path = start_path or bitos.user_paths["home"]
        self.history = []
        self.history_index = -1
        self.clipboard = None
        self.clipboard_action = None
        self.view_mode = 'list'
        self.selected_items = []
        self.trash_manager = TrashManager(bitos)
        
        # Поиск
        self.search_active = False
        self.search_results = []
        self.search_timer = None
        
        # Отслеживание флешек
        self.known_drives = set()
        
        # Центр уведомлений
        self.notification_center = None
        
        self.create_window()
        self.load_directory()
        self.check_removable_drives()
    
    def _get_notification_center(self):
        """Получение центра уведомлений"""
        if self.notification_center:
            return self.notification_center
        
        # Пробуем получить через bitos
        if hasattr(self.bitos, 'desktop_instance'):
            if hasattr(self.bitos.desktop_instance, 'notification_center'):
                self.notification_center = self.bitos.desktop_instance.notification_center
                return self.notification_center
        
        # Пробуем получить через parent
        if hasattr(self.parent, 'notification_center'):
            self.notification_center = self.parent.notification_center
            return self.notification_center
        
        # Ищем в цепочке parent
        try:
            current = self.parent
            while current:
                if hasattr(current, 'notification_center'):
                    self.notification_center = current.notification_center
                    return self.notification_center
                if hasattr(current, 'master'):
                    current = current.master
                elif hasattr(current, 'parent'):
                    current = current.parent
                else:
                    break
        except:
            pass
        
        return None
    
    def _send_notification(self, title, message, icon="🔔", duration=5000):
        """Отправка уведомления в центр уведомлений"""
        nc = self._get_notification_center()
        if nc:
            try:
                nc.add_notification(title, message, icon=icon, duration=duration)
                return True
            except:
                pass
        return False
    
    def create_window(self):
        self.window = tk.Toplevel(self.parent)
        self.window.title("📁 Проводник BITOS")
        self.window.geometry("1000x700")
        self.window.transient(self.parent)
        self.window.configure(bg='#F5F7FA')
        
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 1000) // 2
        y = (self.window.winfo_screenheight() - 700) // 2
        self.window.geometry(f'+{x}+{y}')
        
        self.create_toolbar()
        self.create_search_bar()
        self.create_address_bar()
        self.create_content_area()
        self.create_status_bar()
        self.create_context_menu()
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        self.check_drives_timer()
    
    def create_toolbar(self):
        toolbar = tk.Frame(self.window, bg='#E0E0E0', height=50)
        toolbar.pack(fill=tk.X, padx=1, pady=1)
        
        nav_frame = tk.Frame(toolbar, bg='#E0E0E0')
        nav_frame.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.back_btn = tk.Button(nav_frame, text='←', font=('Segoe UI', 14), 
                                 bg='#E0E0E0', fg='#2C3E50', bd=0,
                                 command=self.go_back, state='disabled')
        self.back_btn.pack(side=tk.LEFT, padx=2)
        
        self.forward_btn = tk.Button(nav_frame, text='→', font=('Segoe UI', 14), 
                                    bg='#E0E0E0', fg='#2C3E50', bd=0,
                                    command=self.go_forward, state='disabled')
        self.forward_btn.pack(side=tk.LEFT, padx=2)
        
        up_btn = tk.Button(nav_frame, text='↑', font=('Segoe UI', 14), 
                          bg='#E0E0E0', fg='#2C3E50', bd=0, command=self.go_up)
        up_btn.pack(side=tk.LEFT, padx=2)
        
        refresh_btn = tk.Button(nav_frame, text='↻', font=('Segoe UI', 14), 
                               bg='#E0E0E0', fg='#2C3E50', bd=0, command=self.refresh)
        refresh_btn.pack(side=tk.LEFT, padx=2)
        
        home_btn = tk.Button(nav_frame, text='🏠', font=('Segoe UI', 14), 
                            bg='#E0E0E0', fg='#2C3E50', bd=0, command=self.go_home)
        home_btn.pack(side=tk.LEFT, padx=2)
        
        tk.Frame(toolbar, width=2, bg='#BDC3C7').pack(side=tk.LEFT, padx=10, fill=tk.Y)
        
        actions_frame = tk.Frame(toolbar, bg='#E0E0E0')
        actions_frame.pack(side=tk.LEFT, padx=5)
        
        tk.Button(actions_frame, text='📁 Новая папка', font=('Segoe UI', 10), 
                 bg='#E0E0E0', fg='#2C3E50', bd=0,
                 command=self.new_folder).pack(side=tk.LEFT, padx=2)
        tk.Button(actions_frame, text='📋 Копировать', font=('Segoe UI', 10), 
                 bg='#E0E0E0', fg='#2C3E50', bd=0,
                 command=self.copy_items).pack(side=tk.LEFT, padx=2)
        tk.Button(actions_frame, text='✂ Вырезать', font=('Segoe UI', 10), 
                 bg='#E0E0E0', fg='#2C3E50', bd=0,
                 command=self.cut_items).pack(side=tk.LEFT, padx=2)
        
        self.paste_btn = tk.Button(actions_frame, text='📌 Вставить', font=('Segoe UI', 10), 
                                   bg='#E0E0E0', fg='#2C3E50', bd=0,
                                   command=self.paste_items, state='disabled')
        self.paste_btn.pack(side=tk.LEFT, padx=2)
        
        tk.Button(actions_frame, text='🗑 Удалить', font=('Segoe UI', 10), 
                 bg='#E74C3C', fg='white', bd=0,
                 command=self.delete_items).pack(side=tk.LEFT, padx=2)
        
        tk.Frame(toolbar, width=2, bg='#BDC3C7').pack(side=tk.LEFT, padx=10, fill=tk.Y)
        
        view_frame = tk.Frame(toolbar, bg='#E0E0E0')
        view_frame.pack(side=tk.LEFT, padx=5)
        
        tk.Button(view_frame, text='📋 Список', font=('Segoe UI', 10), 
                 bg='#E0E0E0', fg='#2C3E50', bd=0,
                 command=lambda: self.set_view_mode('list')).pack(side=tk.LEFT, padx=2)
        tk.Button(view_frame, text='🖼 Иконки', font=('Segoe UI', 10), 
                 bg='#E0E0E0', fg='#2C3E50', bd=0,
                 command=lambda: self.set_view_mode('icons')).pack(side=tk.LEFT, padx=2)
        
        tk.Frame(toolbar, width=2, bg='#BDC3C7').pack(side=tk.LEFT, padx=10, fill=tk.Y)
        
        self.drives_frame = tk.Frame(toolbar, bg='#E0E0E0')
        self.drives_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Label(self.drives_frame, text="💾 Съёмные диски:", bg='#E0E0E0', 
                fg='#2C3E50', font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=5)
        self.drives_container = tk.Frame(self.drives_frame, bg='#E0E0E0')
        self.drives_container.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def create_search_bar(self):
        search_frame = tk.Frame(self.window, bg='white', height=35)
        search_frame.pack(fill=tk.X, padx=10, pady=(5, 0))
        
        tk.Label(search_frame, text="🔍", font=('Segoe UI', 12), 
                bg='white', fg='#7F8C8D').pack(side=tk.LEFT, padx=5)
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.on_search_change())
        
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, 
                                     font=('Segoe UI', 10), bg='#F5F7FA', fg='#2C3E50', 
                                     bd=0, highlightthickness=1, 
                                     highlightcolor='#3498DB', highlightbackground='#BDC3C7')
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5, ipady=3)
        
        self.clear_search_btn = tk.Label(search_frame, text="✕", font=('Segoe UI', 12), 
                                         bg='white', fg='#95A5A6', cursor='hand2')
        self.clear_search_btn.pack(side=tk.RIGHT, padx=5)
        self.clear_search_btn.bind('<Button-1>', lambda e: self.clear_search())
        
        options_frame = tk.Frame(search_frame, bg='white')
        options_frame.pack(side=tk.RIGHT, padx=5)
        
        self.search_in_subfolders = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="В подпапках", variable=self.search_in_subfolders,
                      bg='white', fg='#7F8C8D', font=('Segoe UI', 9),
                      selectcolor='white', command=self.on_search_change).pack(side=tk.LEFT, padx=5)
        
        self.search_by_content = tk.BooleanVar(value=False)
        tk.Checkbutton(options_frame, text="По содержимому", variable=self.search_by_content,
                      bg='white', fg='#7F8C8D', font=('Segoe UI', 9),
                      selectcolor='white', command=self.on_search_change).pack(side=tk.LEFT, padx=5)
        
        self.search_status = tk.Label(search_frame, text="", bg='white', fg='#3498DB', 
                                      font=('Segoe UI', 9))
        self.search_status.pack(side=tk.RIGHT, padx=5)
    
    def on_search_change(self):
        query = self.search_var.get().strip()
        
        if self.search_timer:
            self.window.after_cancel(self.search_timer)
        
        if not query:
            self.clear_search()
            return
        
        self.search_timer = self.window.after(300, self.perform_search, query)
    
    def perform_search(self, query):
        self.search_active = True
        self.search_status.config(text="🔍 Поиск...")
        self.search_results = []
        
        thread = threading.Thread(target=self._search_thread, args=(query,))
        thread.daemon = True
        thread.start()
    
    def _search_thread(self, query):
        results = []
        query_lower = query.lower()
        
        try:
            if self.search_in_subfolders.get():
                for root, dirs, files in os.walk(self.current_path):
                    for file in files:
                        if self._match_file(file, query_lower, os.path.join(root, file)):
                            results.append({
                                'name': file,
                                'path': os.path.join(root, file),
                                'is_dir': False,
                                'size': os.path.getsize(os.path.join(root, file))
                            })
                    
                    for dir in dirs:
                        if query_lower in dir.lower():
                            results.append({
                                'name': dir,
                                'path': os.path.join(root, dir),
                                'is_dir': True,
                                'size': 0
                            })
            else:
                for item in os.listdir(self.current_path):
                    item_path = os.path.join(self.current_path, item)
                    if self._match_file(item, query_lower, item_path):
                        is_dir = os.path.isdir(item_path)
                        results.append({
                            'name': item,
                            'path': item_path,
                            'is_dir': is_dir,
                            'size': os.path.getsize(item_path) if not is_dir else 0
                        })
        except Exception as e:
            pass
        
        self.search_results = results
        self.window.after(0, self._display_search_results)
    
    def _match_file(self, filename, query, filepath):
        if query in filename.lower():
            return True
        
        if self.search_by_content.get():
            try:
                if any(filename.lower().endswith(ext) for ext in 
                      ['.txt', '.py', '.js', '.html', '.css', '.json', '.xml', '.log', '.md']):
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(10000)
                        if query in content.lower():
                            return True
            except:
                pass
        
        return False
    
    def _display_search_results(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self.search_status.config(text=f"Найдено: {len(self.search_results)}")
        
        if not self.search_results:
            no_result = tk.Label(self.scrollable_frame, text="🔍 Ничего не найдено", 
                                bg='white', fg='#7F8C8D', font=('Segoe UI', 14))
            no_result.pack(expand=True)
            return
        
        header = tk.Frame(self.scrollable_frame, bg='#3498DB', height=30)
        header.pack(fill=tk.X, pady=(0, 5))
        tk.Label(header, text=f"🔍 Результаты поиска ({len(self.search_results)})", 
                bg='#3498DB', fg='white', font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=10)
        
        tk.Button(header, text="✕ Закрыть поиск", bg='#E74C3C', fg='white',
                 font=('Segoe UI', 9), bd=0, padx=10, pady=3,
                 command=self.clear_search).pack(side=tk.RIGHT, padx=10)
        
        folders = [r for r in self.search_results if r['is_dir']]
        files = [r for r in self.search_results if not r['is_dir']]
        
        if folders:
            tk.Label(self.scrollable_frame, text="📁 Папки:", bg='white', fg='#7F8C8D',
                    font=('Segoe UI', 9, 'bold')).pack(anchor='w', padx=10, pady=(10, 5))
            for result in folders:
                self._create_search_item(result)
        
        if files:
            tk.Label(self.scrollable_frame, text="📄 Файлы:", bg='white', fg='#7F8C8D',
                    font=('Segoe UI', 9, 'bold')).pack(anchor='w', padx=10, pady=(10, 5))
            for result in files:
                self._create_search_item(result)
    
    def _create_search_item(self, result):
        item_frame = tk.Frame(self.scrollable_frame, bg='white', height=30)
        item_frame.pack(fill=tk.X, pady=1)
        item_frame.item_data = result
        
        icon = "📁" if result['is_dir'] else self.get_file_icon(result['name'])
        
        name_label = tk.Label(item_frame, text=f"{icon} {result['name']}", 
                             bg='white', fg='#2C3E50', font=('Segoe UI', 10), anchor='w')
        name_label.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        path_label = tk.Label(item_frame, text=result['path'], bg='white', 
                             fg='#7F8C8D', font=('Segoe UI', 8), anchor='w')
        path_label.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        if not result['is_dir']:
            size_str = self.format_size(result['size'])
            tk.Label(item_frame, text=size_str, bg='white', fg='#7F8C8D', 
                    font=('Segoe UI', 9)).pack(side=tk.RIGHT, padx=10)
        
        for widget in [item_frame, name_label, path_label]:
            widget.bind('<Button-1>', lambda e, f=item_frame: self.select_item(f))
            widget.bind('<Double-1>', lambda e, r=result: self._open_search_result(r))
            widget.bind('<Enter>', lambda e, f=item_frame: f.config(bg='#EBF5FB'))
            widget.bind('<Leave>', lambda e, f=item_frame: f.config(bg='white'))
    
    def _open_search_result(self, result):
        if result['is_dir']:
            self.clear_search()
            self.navigate_to(result['path'])
        else:
            parent_dir = os.path.dirname(result['path'])
            self.clear_search()
            self.navigate_to(parent_dir)
    
    def clear_search(self):
        self.search_var.set('')
        self.search_active = False
        self.search_results = []
        self.search_status.config(text='')
        self.load_directory()
    
    def create_address_bar(self):
        addr_frame = tk.Frame(self.window, bg='white', height=35)
        addr_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(addr_frame, text="📍", font=('Segoe UI', 12), bg='white', fg='#7F8C8D').pack(side=tk.LEFT, padx=5)
        self.address_var = tk.StringVar()
        self.address_entry = tk.Entry(addr_frame, textvariable=self.address_var, font=('Segoe UI', 10),
                                     bg='#F5F7FA', fg='#2C3E50', bd=0, highlightthickness=1,
                                     highlightcolor='#3498DB', highlightbackground='#BDC3C7')
        self.address_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5, ipady=3)
        self.address_entry.bind('<Return>', lambda e: self.navigate_to(self.address_var.get()))
        go_btn = tk.Button(addr_frame, text="Перейти", bg='#3498DB', fg='white', font=('Segoe UI', 10), 
                          bd=0, padx=15, pady=2, command=lambda: self.navigate_to(self.address_var.get()))
        go_btn.pack(side=tk.RIGHT, padx=5)
    
    def create_content_area(self):
        main_frame = tk.Frame(self.window, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.create_sidebar(main_frame)
        self.content_frame = tk.Frame(main_frame, bg='white')
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        self.canvas = tk.Canvas(self.content_frame, bg='white', highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.content_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg='white')
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
    
    def create_sidebar(self, parent):
        sidebar = tk.Frame(parent, bg='#F0F3F4', width=200)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        sidebar.pack_propagate(False)
        tk.Label(sidebar, text="📌 Быстрый доступ", bg='#F0F3F4', fg='#2C3E50', 
                font=('Segoe UI', 10, 'bold')).pack(anchor='w', padx=10, pady=5)
        quick_items = [
            ("🏠 Домой", self.bitos.user_paths["home"]),
            ("📁 Документы", self.bitos.documents_path),
            ("📸 Изображения", os.path.join(self.bitos.user_paths["home"], "Pictures")),
            ("🔐 Безопасные", self.bitos.secure_path),
            ("📥 Загрузки", self.bitos.downloads_path),
        ]
        for name, path in quick_items:
            btn = tk.Button(sidebar, text=name, bg='#F0F3F4', fg='#2C3E50', font=('Segoe UI', 10), 
                           bd=0, anchor='w', command=lambda p=path: self.navigate_to(p))
            btn.pack(fill=tk.X, padx=5, pady=2)
        tk.Frame(sidebar, height=2, bg='#BDC3C7').pack(fill=tk.X, padx=10, pady=10)
        tk.Label(sidebar, text="💾 Съёмные диски", bg='#F0F3F4', fg='#2C3E50', 
                font=('Segoe UI', 10, 'bold')).pack(anchor='w', padx=10, pady=5)
        self.sidebar_drives = tk.Frame(sidebar, bg='#F0F3F4')
        self.sidebar_drives.pack(fill=tk.X, padx=5)
        tk.Frame(sidebar, height=2, bg='#BDC3C7').pack(fill=tk.X, padx=10, pady=10)
        trash_btn = tk.Button(sidebar, text="🗑 Корзина", bg='#F0F3F4', fg='#E74C3C', font=('Segoe UI', 10), 
                             bd=0, anchor='w', command=self.open_trash)
        trash_btn.pack(fill=tk.X, padx=5, pady=2)
    
    def create_status_bar(self):
        self.status_bar = tk.Frame(self.window, bg='#E0E0E0', height=25)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_label = tk.Label(self.status_bar, bg='#E0E0E0', fg='#2C3E50', 
                                     font=('Segoe UI', 9), anchor='w')
        self.status_label.pack(side=tk.LEFT, padx=10)
        self.items_count_label = tk.Label(self.status_bar, bg='#E0E0E0', fg='#2C3E50', 
                                          font=('Segoe UI', 9))
        self.items_count_label.pack(side=tk.RIGHT, padx=10)
    
    def create_context_menu(self):
        self.context_menu = tk.Menu(self.window, tearoff=0, bg='#2C3E50', fg='white', 
                                   activebackground='#3498DB')
        self.context_menu.add_command(label="Открыть", command=self.open_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Копировать", command=self.copy_items)
        self.context_menu.add_command(label="Вырезать", command=self.cut_items)
        self.context_menu.add_command(label="Вставить", command=self.paste_items)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="♻ В корзину", command=self.delete_to_trash)
        self.context_menu.add_command(label="🗑 Удалить навсегда", command=self.delete_items_permanent)
        self.context_menu.add_command(label="Переименовать", command=self.rename_item)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Свойства", command=self.show_properties)
        self.scrollable_frame.bind("<Button-3>", self.show_context_menu)
    
    def show_context_menu(self, event):
        widget = event.widget.winfo_containing(event.x_root, event.y_root)
        if widget and widget.winfo_parent():
            parent = widget.nametowidget(widget.winfo_parent())
            if hasattr(parent, 'item_data'):
                self.selected_items = [parent.item_data]
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def check_removable_drives(self):
        """Проверка съёмных дисков с уведомлениями о подключении/отключении"""
        current_drives = set()
        
        if platform.system() == "Windows" and WIN32_AVAILABLE:
            try:
                drives = win32api.GetLogicalDriveStrings().split('\000')[:-1]
                for drive in drives:
                    try:
                        if win32file.GetDriveType(drive) == win32file.DRIVE_REMOVABLE:
                            if drive not in self.FORBIDDEN_PATHS:
                                current_drives.add(drive)
                                self.add_drive_button(drive)
                    except:
                        continue
            except:
                pass
        else:
            if platform.system() == "Linux":
                media_paths = ["/media", "/mnt", "/run/media"]
                for media in media_paths:
                    if os.path.exists(media):
                        try:
                            for item in os.listdir(media):
                                path = os.path.join(media, item)
                                if os.path.ismount(path):
                                    current_drives.add(path)
                                    self.add_drive_button(path)
                        except:
                            pass
        
        # Проверяем новые устройства
        new_drives = current_drives - self.known_drives
        removed_drives = self.known_drives - current_drives
        
        # Уведомления о новых флешках
        for drive in new_drives:
            drive_name = drive
            try:
                if platform.system() == "Windows" and WIN32_AVAILABLE:
                    try:
                        volume_name = win32file.GetVolumeInformation(drive)[0]
                        if volume_name:
                            drive_name = f"{volume_name} ({drive})"
                    except:
                        pass
                else:
                    drive_name = os.path.basename(drive)
            except:
                pass
            
            self._send_notification(
                "💾 Флешка подключена",
                f"Обнаружено новое устройство: {drive_name}",
                icon="💾",
                duration=5000
            )
        
        # Уведомления об отключении флешек
        for drive in removed_drives:
            drive_name = drive
            try:
                if platform.system() == "Windows" and WIN32_AVAILABLE:
                    try:
                        volume_name = win32file.GetVolumeInformation(drive)[0]
                        if volume_name:
                            drive_name = volume_name
                    except:
                        pass
                else:
                    drive_name = os.path.basename(drive)
            except:
                pass
            
            self._send_notification(
                "💾 Флешка отключена",
                f"Устройство {drive_name} было отключено",
                icon="💾",
                duration=3000
            )
        
        self.known_drives = current_drives
        
        if not current_drives:
            self.show_no_drives_message()
    
    def show_no_drives_message(self):
        for widget in self.drives_container.winfo_children():
            widget.destroy()
        for widget in self.sidebar_drives.winfo_children():
            widget.destroy()
        
        label = tk.Label(self.drives_container, text="нет подключённых устройств", 
                        font=('Segoe UI', 9), bg='#E0E0E0', fg='#7F8C8D')
        label.pack(side=tk.LEFT, padx=5)
        label2 = tk.Label(self.sidebar_drives, text="нет подключённых устройств", 
                         font=('Segoe UI', 9), bg='#F0F3F4', fg='#7F8C8D')
        label2.pack(padx=5, pady=2)
    
    def add_drive_button(self, drive_path):
        for widget in self.drives_container.winfo_children():
            if hasattr(widget, 'drive_path') and widget.drive_path == drive_path:
                return
        
        drive_label = drive_path
        if platform.system() == "Windows" and WIN32_AVAILABLE:
            try:
                volume_name = win32file.GetVolumeInformation(drive_path)[0]
                if volume_name:
                    drive_label = f"{drive_path} ({volume_name})"
            except:
                pass
        
        short_name = drive_path[:2] if platform.system() == "Windows" else os.path.basename(drive_path)
        
        btn = tk.Button(self.drives_container, text=f'💾 {short_name}', font=('Segoe UI', 10), 
                       bg='#E0E0E0', fg='#2C3E50', bd=0,
                       command=lambda p=drive_path: self.navigate_to(p))
        btn.drive_path = drive_path
        btn.pack(side=tk.LEFT, padx=2)
        
        sidebar_btn = tk.Button(self.sidebar_drives, text=f'💾 {drive_label}', bg='#F0F3F4', 
                               fg='#2C3E50', font=('Segoe UI', 10), bd=0, anchor='w', 
                               command=lambda p=drive_path: self.navigate_to(p))
        sidebar_btn.drive_path = drive_path
        sidebar_btn.pack(fill=tk.X, padx=5, pady=2)
    
    def update_drive_buttons(self):
        for widget in self.drives_container.winfo_children():
            widget.destroy()
        for widget in self.sidebar_drives.winfo_children():
            widget.destroy()
        self.check_removable_drives()
    
    def check_drives_timer(self):
        self.update_drive_buttons()
        self.window.after(5000, self.check_drives_timer)
    
    def is_path_allowed(self, path):
        path = os.path.abspath(path)
        for forbidden in self.FORBIDDEN_PATHS:
            if path.startswith(forbidden):
                return False
        if path.startswith(self.bitos.base_path):
            if (path.startswith(self.bitos.user_paths["home"]) or path.startswith(self.bitos.downloads_path)):
                return True
            return False
        if platform.system() == "Windows":
            try:
                if WIN32_AVAILABLE:
                    drive = os.path.splitdrive(path)[0] + '\\'
                    if win32file.GetDriveType(drive) == win32file.DRIVE_REMOVABLE:
                        return True
            except:
                pass
        else:
            if path.startswith(("/media", "/mnt", "/run/media")):
                return True
        return False
    
    def navigate_to(self, path):
        if not os.path.exists(path):
            messagebox.showerror("Ошибка", "Путь не существует")
            return
        if not self.is_path_allowed(path):
            messagebox.showerror("Доступ запрещён", "Нет доступа к системным дискам")
            return
        if self.current_path and self.current_path != path:
            if self.history_index == -1 or self.history[self.history_index] != self.current_path:
                self.history = self.history[:self.history_index+1]
                self.history.append(self.current_path)
                self.history_index = len(self.history) - 1
        self.current_path = path
        self.address_var.set(path)
        self.load_directory()
        self.update_nav_buttons()
    
    def load_directory(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        try:
            items = os.listdir(self.current_path)
            folders = []
            files = []
            for item in items:
                item_path = os.path.join(self.current_path, item)
                if os.path.isdir(item_path):
                    folders.append(item)
                else:
                    files.append(item)
            folders.sort(key=str.lower)
            files.sort(key=str.lower)
            all_items = folders + files
            if self.view_mode == 'list':
                self.display_list_view(all_items)
            else:
                self.display_icon_view(all_items)
            total = len(all_items)
            self.items_count_label.config(text=f"Всего: {total} (папок: {len(folders)}, файлов: {len(files)})")
            self.status_label.config(text=f"📍 {self.current_path}")
        except PermissionError:
            messagebox.showerror("Ошибка", "Нет прав доступа к папке")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def display_list_view(self, items):
        header = tk.Frame(self.scrollable_frame, bg='#F0F3F4', height=25)
        header.pack(fill=tk.X, pady=(0, 2))
        tk.Label(header, text="Имя", bg='#F0F3F4', fg='#2C3E50', 
                font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=10)
        tk.Label(header, text="Размер", bg='#F0F3F4', fg='#2C3E50', 
                font=('Segoe UI', 10, 'bold'), width=10).pack(side=tk.RIGHT, padx=10)
        tk.Label(header, text="Изменён", bg='#F0F3F4', fg='#2C3E50', 
                font=('Segoe UI', 10, 'bold'), width=15).pack(side=tk.RIGHT, padx=10)
        for item in items:
            self.create_list_item(item)
    
    def create_list_item(self, item):
        item_path = os.path.join(self.current_path, item)
        is_dir = os.path.isdir(item_path)
        item_frame = tk.Frame(self.scrollable_frame, bg='white', height=25)
        item_frame.pack(fill=tk.X, pady=1)
        item_frame.item_data = {'name': item, 'path': item_path, 'is_dir': is_dir}
        icon = "📁" if is_dir else self.get_file_icon(item)
        name_label = tk.Label(item_frame, text=f"{icon} {item}", bg='white', fg='#2C3E50', 
                             font=('Segoe UI', 10), anchor='w')
        name_label.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        if not is_dir:
            size = os.path.getsize(item_path)
            size_str = self.format_size(size)
            tk.Label(item_frame, text=size_str, bg='white', fg='#7F8C8D', 
                    font=('Segoe UI', 10), width=10).pack(side=tk.RIGHT, padx=10)
        mtime = datetime.fromtimestamp(os.path.getmtime(item_path))
        tk.Label(item_frame, text=mtime.strftime('%Y-%m-%d %H:%M'), bg='white', fg='#7F8C8D', 
                font=('Segoe UI', 10), width=15).pack(side=tk.RIGHT, padx=10)
        for widget in [item_frame, name_label]:
            widget.bind('<Button-1>', lambda e, f=item_frame: self.select_item(f))
            widget.bind('<Double-1>', lambda e, p=item_path, d=is_dir: self.open_item(p, d))
    
    def display_icon_view(self, items):
        row, col = 0, 0
        max_cols = 6
        for item in items:
            self.create_icon_item(item, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
    
    def create_icon_item(self, item, row, col):
        item_path = os.path.join(self.current_path, item)
        is_dir = os.path.isdir(item_path)
        icon_frame = tk.Frame(self.scrollable_frame, bg='white', width=120, height=120)
        icon_frame.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
        icon_frame.grid_propagate(False)
        icon_frame.item_data = {'name': item, 'path': item_path, 'is_dir': is_dir}
        icon = "📁" if is_dir else self.get_file_icon(item)
        icon_label = tk.Label(icon_frame, text=icon, bg='white', fg='#2C3E50', font=('Segoe UI', 36))
        icon_label.pack(expand=True)
        display_name = item if len(item) <= 15 else item[:12] + '...'
        name_label = tk.Label(icon_frame, text=display_name, bg='white', fg='#2C3E50', 
                             font=('Segoe UI', 9), wraplength=100)
        name_label.pack()
        for widget in [icon_frame, icon_label, name_label]:
            widget.bind('<Button-1>', lambda e, f=icon_frame: self.select_item(f))
            widget.bind('<Double-1>', lambda e, p=item_path, d=is_dir: self.open_item(p, d))
    
    def get_file_icon(self, filename):
        ext = os.path.splitext(filename)[1].lower()
        icons = {
            '.txt': '📄', '.doc': '📝', '.docx': '📝', '.jpg': '🖼', '.jpeg': '🖼', 
            '.png': '🖼', '.gif': '🖼', '.bmp': '🖼', '.mp3': '🎵', '.wav': '🎵', 
            '.flac': '🎵', '.mp4': '🎬', '.avi': '🎬', '.mkv': '🎬', '.pdf': '📕', 
            '.exe': '⚙', '.zip': '📦', '.rar': '📦', '.7z': '📦', '.py': '🐍', 
            '.js': '📜', '.html': '🌐', '.css': '🎨', '.xls': '📊', '.xlsx': '📊', 
            '.ppt': '📽', '.pptx': '📽'
        }
        return icons.get(ext, '📄')
    
    def select_item(self, item_frame):
        for widget in self.scrollable_frame.winfo_children():
            if isinstance(widget, tk.Frame):
                widget.config(bg='white')
                for child in widget.winfo_children():
                    if isinstance(child, tk.Label):
                        child.config(bg='white')
        item_frame.config(bg='#3498DB')
        for child in item_frame.winfo_children():
            if isinstance(child, tk.Label):
                child.config(bg='#3498DB', fg='white')
        self.selected_items = [item_frame.item_data]
    
    def open_item(self, path, is_dir):
        if is_dir:
            self.navigate_to(path)
        else:
            self.open_file(path)
    
    def open_file(self, path):
        ext = os.path.splitext(path)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp'] and PIL_AVAILABLE:
            self.open_in_gallery(path)
        else:
            self.open_in_editor(path)
    
    def open_in_editor(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            dialog = tk.Toplevel(self.window)
            dialog.title(f"📄 {os.path.basename(path)}")
            dialog.geometry("700x600")
            dialog.transient(self.window)
            dialog.configure(bg='#F5F7FA')
            text_area = scrolledtext.ScrolledText(dialog, font=('Consolas', 11))
            text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text_area.insert('1.0', content)
            btn_frame = tk.Frame(dialog, bg='#F5F7FA')
            btn_frame.pack(fill=tk.X, padx=10, pady=5)
            def save():
                new_content = text_area.get('1.0', tk.END)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                messagebox.showinfo("Успех", "Файл сохранён")
            tk.Button(btn_frame, text="Сохранить", bg='#3498DB', fg='white', 
                     font=('Segoe UI', 10), bd=0, padx=20, pady=5, command=save).pack(side=tk.LEFT, padx=5)
            tk.Button(btn_frame, text="Закрыть", bg='#E74C3C', fg='white', 
                     font=('Segoe UI', 10), bd=0, padx=20, pady=5, command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def open_in_gallery(self, path):
        if not PIL_AVAILABLE:
            messagebox.showerror("Ошибка", "Для просмотра изображений установите Pillow")
            return
        dialog = tk.Toplevel(self.window)
        dialog.title(f"🖼 {os.path.basename(path)}")
        dialog.geometry("800x600")
        dialog.transient(self.window)
        try:
            img = Image.open(path)
            max_size = (700, 500)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            label = tk.Label(dialog, image=photo)
            label.image = photo
            label.pack(expand=True, padx=10, pady=10)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def format_size(self, size):
        for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} ТБ"
    
    def new_folder(self):
        dialog = tk.Toplevel(self.window)
        dialog.title("Новая папка")
        dialog.geometry("400x150")
        dialog.transient(self.window)
        dialog.configure(bg='#F5F7FA')
        tk.Label(dialog, text="Имя папки:", bg='#F5F7FA', fg='#2C3E50', 
                font=('Segoe UI', 10)).pack(padx=10, pady=10)
        name_entry = tk.Entry(dialog, font=('Segoe UI', 11), width=30)
        name_entry.pack(padx=10, pady=5)
        name_entry.focus_set()
        def create():
            name = name_entry.get().strip()
            if name:
                path = os.path.join(self.current_path, name)
                try:
                    os.makedirs(path, exist_ok=True)
                    if self.bitos and hasattr(self.bitos, 'security'):
                        self.bitos.security.log_folder_create(self.bitos.current_user, path)
                    dialog.destroy()
                    self.refresh()
                except Exception as e:
                    messagebox.showerror("Ошибка", str(e))
        tk.Button(dialog, text="Создать", bg='#3498DB', fg='white', 
                 font=('Segoe UI', 10), bd=0, padx=20, pady=5, command=create).pack(pady=10)
        name_entry.bind('<Return>', lambda e: create())
    
    def delete_items(self):
        if not self.selected_items:
            messagebox.showinfo("Информация", "Ничего не выбрано")
            return
        dialog = tk.Toplevel(self.window)
        dialog.title("Удаление")
        dialog.geometry("400x200")
        dialog.transient(self.window)
        dialog.grab_set()
        dialog.configure(bg='#F5F7FA')
        x = (dialog.winfo_screenwidth() - 400) // 2
        y = (dialog.winfo_screenheight() - 200) // 2
        dialog.geometry(f'+{x}+{y}')
        items_count = len(self.selected_items)
        tk.Label(dialog, text="🗑 Удаление", font=('Segoe UI', 16, 'bold'), 
                bg='#F5F7FA', fg='#2C3E50').pack(pady=10)
        tk.Label(dialog, text=f"Выбрано элементов: {items_count}", 
                font=('Segoe UI', 11), bg='#F5F7FA', fg='#7F8C8D').pack()
        def trash():
            dialog.destroy()
            self.delete_to_trash()
        def permanent():
            if messagebox.askyesno("Подтверждение", f"Удалить {items_count} элементов навсегда?\nЭто действие нельзя отменить."):
                dialog.destroy()
                for item in self.selected_items:
                    try:
                        path = item['path']
                        if item['is_dir']:
                            shutil.rmtree(path)
                        else:
                            os.remove(path)
                        if self.bitos and hasattr(self.bitos, 'security'):
                            self.bitos.security.log_file_delete(self.bitos.current_user, path, permanent=True)
                    except Exception as e:
                        messagebox.showerror("Ошибка", str(e))
                self.selected_items = []
                self.refresh()
        btn_frame = tk.Frame(dialog, bg='#F5F7FA')
        btn_frame.pack(expand=True)
        tk.Button(btn_frame, text="♻ В корзину", bg='#3498DB', fg='white', 
                 font=('Segoe UI', 11), bd=0, padx=30, pady=10, command=trash).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="🗑 Навсегда", bg='#E74C3C', fg='white', 
                 font=('Segoe UI', 11), bd=0, padx=30, pady=10, command=permanent).pack(side=tk.LEFT, padx=10)
        tk.Button(dialog, text="Отмена", bg='#95A5A6', fg='white', 
                 font=('Segoe UI', 10), bd=0, padx=20, pady=5, command=dialog.destroy).pack(pady=10)
    
    def delete_to_trash(self):
        if not self.selected_items:
            messagebox.showinfo("Информация", "Ничего не выбрано")
            return
        items = self.selected_items
        msg = f"Переместить '{items[0]['name']}' в корзину?" if len(items) == 1 else f"Переместить {len(items)} элементов в корзину?"
        if messagebox.askyesno("Подтверждение", msg):
            paths = [item['path'] for item in items]
            moved = TrashManager(self.bitos).move_to_trash(paths)
            if moved:
                self.selected_items = []
                self.refresh()
                messagebox.showinfo("Успех", f"Перемещено в корзину: {len(moved)}")
    
    def delete_items_permanent(self):
        if not self.selected_items:
            messagebox.showinfo("Информация", "Ничего не выбрано")
            return
        items = self.selected_items
        msg = f"Удалить '{items[0]['name']}' навсегда?\nЭто действие нельзя отменить." if len(items) == 1 else f"Удалить {len(items)} элементов навсегда?\nЭто действие нельзя отменить."
        if messagebox.askyesno("Подтверждение", msg):
            for item in items:
                try:
                    path = item['path']
                    if item['is_dir']:
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                    if self.bitos and hasattr(self.bitos, 'security'):
                        self.bitos.security.log_file_delete(self.bitos.current_user, path, permanent=True)
                except Exception as e:
                    messagebox.showerror("Ошибка", str(e))
            self.selected_items = []
            self.refresh()
    
    def copy_items(self):
        if not self.selected_items:
            return
        self.clipboard = self.selected_items.copy()
        self.clipboard_action = 'copy'
        self.paste_btn.config(state='normal')
    
    def cut_items(self):
        if not self.selected_items:
            return
        self.clipboard = self.selected_items.copy()
        self.clipboard_action = 'cut'
        self.paste_btn.config(state='normal')
    
    def paste_items(self):
        if not self.clipboard:
            return
        for item in self.clipboard:
            src = item['path']
            dst = os.path.join(self.current_path, item['name'])
            if src == dst:
                continue
            try:
                if self.clipboard_action == 'copy':
                    if item['is_dir']:
                        shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)
                else:
                    shutil.move(src, dst)
                    if self.bitos and hasattr(self.bitos, 'security'):
                        self.bitos.security.log_file_move(self.bitos.current_user, src, dst)
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))
        if self.clipboard_action == 'cut':
            self.clipboard = None
            self.paste_btn.config(state='disabled')
        self.refresh()
    
    def rename_item(self):
        if not self.selected_items:
            return
        item = self.selected_items[0]
        dialog = tk.Toplevel(self.window)
        dialog.title("Переименовать")
        dialog.geometry("400x150")
        dialog.transient(self.window)
        dialog.configure(bg='#F5F7FA')
        tk.Label(dialog, text="Новое имя:", bg='#F5F7FA', fg='#2C3E50', 
                font=('Segoe UI', 10)).pack(padx=10, pady=10)
        name_entry = tk.Entry(dialog, font=('Segoe UI', 11), width=30)
        name_entry.pack(padx=10, pady=5)
        name_entry.insert(0, item['name'])
        name_entry.focus_set()
        def rename():
            new_name = name_entry.get().strip()
            if new_name and new_name != item['name']:
                src = item['path']
                dst = os.path.join(self.current_path, new_name)
                try:
                    os.rename(src, dst)
                    dialog.destroy()
                    self.refresh()
                except Exception as e:
                    messagebox.showerror("Ошибка", str(e))
        tk.Button(dialog, text="Переименовать", bg='#3498DB', fg='white', 
                 font=('Segoe UI', 10), bd=0, padx=20, pady=5, command=rename).pack(pady=10)
        name_entry.bind('<Return>', lambda e: rename())
    
    def show_properties(self):
        if not self.selected_items:
            return
        item = self.selected_items[0]
        path = item['path']
        info = [f"Имя: {item['name']}", f"Тип: {'Папка' if item['is_dir'] else 'Файл'}", f"Путь: {path}"]
        if os.path.exists(path):
            stat = os.stat(path)
            info.append(f"Размер: {self.format_size(stat.st_size)}")
            info.append(f"Создан: {datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')}")
            info.append(f"Изменён: {datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
        messagebox.showinfo("Свойства", "\n".join(info))
    
    def open_selected(self):
        if self.selected_items:
            item = self.selected_items[0]
            self.open_item(item['path'], item['is_dir'])
    
    def open_trash(self):
        TrashWindow(self.window, self.bitos)
    
    def set_view_mode(self, mode):
        self.view_mode = mode
        self.load_directory()
    
    def go_back(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.current_path = self.history[self.history_index]
            self.address_var.set(self.current_path)
            self.load_directory()
            self.update_nav_buttons()
    
    def go_forward(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.current_path = self.history[self.history_index]
            self.address_var.set(self.current_path)
            self.load_directory()
            self.update_nav_buttons()
    
    def go_up(self):
        parent = os.path.dirname(self.current_path)
        if parent and parent != self.current_path:
            self.navigate_to(parent)
    
    def go_home(self):
        self.navigate_to(self.bitos.user_paths["home"])
    
    def refresh(self):
        self.load_directory()
    
    def update_nav_buttons(self):
        self.back_btn.config(state='normal' if self.history_index > 0 else 'disabled')
        self.forward_btn.config(state='normal' if self.history_index < len(self.history) - 1 else 'disabled')
    
    def on_close(self):
        self.canvas.unbind_all("<MouseWheel>")
        self.window.destroy()

# ==================== КЛАСС 7: Gallery ====================
class Gallery:
    """Галерея изображений"""
    
    def __init__(self, parent, bitos):
        self.parent = parent
        self.bitos = bitos
        self.pictures_path = os.path.join(bitos.user_paths["home"], "Pictures")
        os.makedirs(self.pictures_path, exist_ok=True)
        self.create_window()
    
    def create_window(self):
        self.window = tk.Toplevel(self.parent)
        self.window.title("🖼 Галерея BITOS")
        self.window.geometry("1000x700")
        self.window.transient(self.parent)
        self.window.configure(bg='#F5F7FA')
        x = (self.window.winfo_screenwidth() - 1000) // 2
        y = (self.window.winfo_screenheight() - 700) // 2
        self.window.geometry(f'+{x}+{y}')
        
        toolbar = tk.Frame(self.window, bg='#E0E0E0', height=40)
        toolbar.pack(fill=tk.X)
        tk.Label(toolbar, text="🖼 Галерея изображений", bg='#E0E0E0', fg='#2C3E50', font=('Segoe UI', 12, 'bold')).pack(side=tk.LEFT, padx=10)
        refresh_btn = tk.Button(toolbar, text="↻ Обновить", bg='#E0E0E0', fg='#2C3E50', bd=0, font=('Segoe UI', 10),
                               command=self.load_images)
        refresh_btn.pack(side=tk.RIGHT, padx=10)
        
        self.canvas = tk.Canvas(self.window, bg='white', highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.window, orient=tk.VERTICAL, command=self.canvas.yview)
        self.images_frame = tk.Frame(self.canvas, bg='white')
        self.images_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.images_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.status_bar = tk.Label(self.window, text="", bg='#E0E0E0', fg='#2C3E50', font=('Segoe UI', 9), anchor='w')
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.load_images()
    
    def load_images(self):
        for widget in self.images_frame.winfo_children():
            widget.destroy()
        if not PIL_AVAILABLE:
            tk.Label(self.images_frame, text="⚠️ Для просмотра изображений установите Pillow",
                    font=('Segoe UI', 14), fg='#E74C3C', bg='white').pack(pady=50)
            return
        images = [f for f in os.listdir(self.pictures_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
        if not images:
            tk.Label(self.images_frame, text="📸 Нет изображений в папке Pictures",
                    font=('Segoe UI', 14), fg='#7F8C8D', bg='white').pack(pady=50)
            self.status_bar.config(text="Нет изображений")
            return
        row, col = 0, 0
        max_cols = 4
        for img_file in sorted(images):
            self.create_thumbnail(img_file, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        self.status_bar.config(text=f"Найдено изображений: {len(images)}")
    
    def create_thumbnail(self, img_file, row, col):
        try:
            img_path = os.path.join(self.pictures_path, img_file)
            img = Image.open(img_path)
            img.thumbnail((200, 200), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            frame = tk.Frame(self.images_frame, bg='white', relief=tk.RAISED, bd=1)
            frame.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
            label = tk.Label(frame, image=photo, bg='white')
            label.image = photo
            label.pack(padx=5, pady=5)
            name = img_file if len(img_file) <= 20 else img_file[:17] + '...'
            tk.Label(frame, text=name, bg='white', fg='#2C3E50', font=('Segoe UI', 9)).pack()
            btn_frame = tk.Frame(frame, bg='white')
            btn_frame.pack(pady=5)
            tk.Button(btn_frame, text="👁 Открыть", bg='#3498DB', fg='white', font=('Segoe UI', 8), bd=0, padx=5,
                     command=lambda p=img_path: self.open_image(p)).pack(side=tk.LEFT, padx=2)
            tk.Button(btn_frame, text="🗑 Удалить", bg='#E74C3C', fg='white', font=('Segoe UI', 8), bd=0, padx=5,
                     command=lambda f=img_file: self.delete_image(f)).pack(side=tk.LEFT, padx=2)
        except Exception as e:
            print(f"Ошибка загрузки {img_file}: {e}")
    
    def open_image(self, path):
        dialog = tk.Toplevel(self.window)
        dialog.title(os.path.basename(path))
        dialog.geometry("800x600")
        dialog.transient(self.window)
        try:
            img = Image.open(path)
            max_size = (750, 500)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            label = tk.Label(dialog, image=photo)
            label.image = photo
            label.pack(expand=True, padx=10, pady=10)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def delete_image(self, filename):
        if messagebox.askyesno("Удаление", f"Удалить {filename}?"):
            path = os.path.join(self.pictures_path, filename)
            try:
                os.remove(path)
                self.load_images()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))


# ==================== КЛАСС 8: Paint ====================
class Paint:
    """Графический редактор Paint"""
    
    def __init__(self, parent):
        self.parent = parent
        self.create_window()
    
    def create_window(self):
        self.window = tk.Toplevel(self.parent)
        self.window.title("🎨 Paint")
        self.window.geometry("800x600")
        self.window.transient(self.parent)
        self.window.configure(bg='#F5F7FA')
        
        self.color = "black"
        self.brush_size = 5
        self.eraser_mode = False
        self.last_x = None
        self.last_y = None
        
        toolbar = tk.Frame(self.window, bg='#E0E0E0', height=40)
        toolbar.pack(fill=tk.X)
        
        colors = ['black', 'red', 'green', 'blue', 'yellow', 'orange', 'purple', 'white']
        for c in colors:
            btn = tk.Button(toolbar, bg=c, width=3, height=1, command=lambda col=c: self.set_color(col))
            btn.pack(side=tk.LEFT, padx=2, pady=5)
        
        tk.Button(toolbar, text="Ластик", bg='#E0E0E0', command=self.toggle_eraser).pack(side=tk.LEFT, padx=5)
        tk.Scale(toolbar, from_=1, to=20, orient=tk.HORIZONTAL, label="Размер",
                command=lambda v: self.set_brush_size(int(v))).pack(side=tk.LEFT, padx=10)
        tk.Button(toolbar, text="Очистить", bg='#E74C3C', fg='white', command=self.clear_canvas).pack(side=tk.RIGHT, padx=5)
        
        self.canvas = tk.Canvas(self.window, bg='white', cursor='cross')
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.canvas.bind('<B1-Motion>', self.paint)
        self.canvas.bind('<ButtonRelease-1>', self.reset)
    
    def set_color(self, color):
        self.color = color
        self.eraser_mode = False
    
    def set_brush_size(self, size):
        self.brush_size = size
    
    def toggle_eraser(self):
        self.eraser_mode = not self.eraser_mode
    
    def clear_canvas(self):
        self.canvas.delete("all")
    
    def paint(self, event):
        x, y = event.x, event.y
        if self.last_x and self.last_y:
            color = "white" if self.eraser_mode else self.color
            self.canvas.create_line(self.last_x, self.last_y, x, y, width=self.brush_size, fill=color,
                                   capstyle=tk.ROUND, smooth=True)
        self.last_x = x
        self.last_y = y
    
    def reset(self, event):
        self.last_x = None
        self.last_y = None

class DesktopIcon:
    """Иконка на рабочем столе с поддержкой сетки и контекстного меню"""
    GRID_SIZE = 100
    START_X = 50
    START_Y = 50
    COLS = 10
    
    def __init__(self, canvas, grid_x, grid_y, icon, text, command, icon_id=None):
        self.canvas = canvas
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.icon = icon
        self.text = text
        self.command = command
        self.icon_id = icon_id if icon_id else self.generate_id()
        self.selected = False
        self.hover = False
        self.is_trash = (text == "Корзина")
        
        self.update_position()
        self.create()
    
    def generate_id(self):
        return f"{self.text}_{int(time.time()*1000)}_{random.randint(1000,9999)}"
    
    def update_position(self):
        self.x = self.START_X + self.grid_x * self.GRID_SIZE
        self.y = self.START_Y + self.grid_y * self.GRID_SIZE
    
    def create(self):
        # Создаем невидимый хитбокс (прямоугольник вокруг иконки)
        hitbox_width = 90
        hitbox_height = 90
        x1 = self.x - hitbox_width // 2
        y1 = self.y - 30
        x2 = self.x + hitbox_width // 2
        y2 = self.y + 45
        
        # Прозрачный хитбокс
        self.hitbox_id = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill='', outline='',  # Полностью прозрачный
            tags=('icon', f'hitbox_{self.icon_id}')
        )
        
        # Текст иконки
        self.icon_id_obj = self.canvas.create_text(
            self.x, self.y-15, 
            text=self.icon,
            font=('Segoe UI', 36), 
            fill='white',
            tags=('icon', f'icon_{self.icon_id}')
        )
        
        # Текст названия
        self.text_id = self.canvas.create_text(
            self.x, self.y+25, 
            text=self.text,
            font=('Segoe UI', 10), 
            fill='white',
            tags=('icon', f'text_{self.icon_id}')
        )
        
        # Привязка событий к хитбоксу
        self.canvas.tag_bind(f'hitbox_{self.icon_id}', '<Button-1>', self.on_click)
        self.canvas.tag_bind(f'hitbox_{self.icon_id}', '<Double-1>', self.on_double_click)
        self.canvas.tag_bind(f'hitbox_{self.icon_id}', '<Button-3>', self.on_right_click)
        self.canvas.tag_bind(f'hitbox_{self.icon_id}', '<Enter>', self.on_enter)
        self.canvas.tag_bind(f'hitbox_{self.icon_id}', '<Leave>', self.on_leave)
        
        # Привязка событий к тексту иконки
        self.canvas.tag_bind(f'icon_{self.icon_id}', '<Button-1>', self.on_click)
        self.canvas.tag_bind(f'icon_{self.icon_id}', '<Double-1>', self.on_double_click)
        self.canvas.tag_bind(f'icon_{self.icon_id}', '<Button-3>', self.on_right_click)
        self.canvas.tag_bind(f'icon_{self.icon_id}', '<Enter>', self.on_enter)
        self.canvas.tag_bind(f'icon_{self.icon_id}', '<Leave>', self.on_leave)
        
        # Привязка событий к тексту названия
        self.canvas.tag_bind(f'text_{self.icon_id}', '<Button-1>', self.on_click)
        self.canvas.tag_bind(f'text_{self.icon_id}', '<Double-1>', self.on_double_click)
        self.canvas.tag_bind(f'text_{self.icon_id}', '<Button-3>', self.on_right_click)
        self.canvas.tag_bind(f'text_{self.icon_id}', '<Enter>', self.on_enter)
        self.canvas.tag_bind(f'text_{self.icon_id}', '<Leave>', self.on_leave)
    
    def on_enter(self, event):
        self.hover = True
        self.canvas.itemconfig(self.icon_id_obj, fill='#3498DB')
        self.canvas.itemconfig(self.text_id, fill='#3498DB')
    
    def on_leave(self, event):
        self.hover = False
        if not self.selected:
            self.canvas.itemconfig(self.icon_id_obj, fill='white')
            self.canvas.itemconfig(self.text_id, fill='white')
    
    def on_click(self, event):
        # Снимаем выделение со всех иконок
        for icon in self.canvas.desktop_icons:
            icon.selected = False
            if not icon.hover:
                icon.canvas.itemconfig(icon.icon_id_obj, fill='white')
                icon.canvas.itemconfig(icon.text_id, fill='white')
        
        self.selected = True
        self.canvas.itemconfig(self.icon_id_obj, fill='#3498DB')
        self.canvas.itemconfig(self.text_id, fill='#3498DB')
    
    def on_double_click(self, event):
        if self.command:
            self.command()
    
    def on_right_click(self, event):
        self.on_click(event)
        menu = tk.Menu(self.canvas, tearoff=0, bg='#2C3E50', fg='white', activebackground='#3498DB')
        menu.add_command(label="Открыть", command=self.command if self.command else lambda: None)
        menu.add_separator()
        
        if not self.is_trash:
            menu.add_command(label="Удалить ярлык", command=self.delete_icon)
        
        menu.add_separator()
        menu.add_command(label="Свойства", command=self.show_properties)
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def delete_icon(self):
        if self.is_trash:
            messagebox.showwarning("Предупреждение", "Корзину нельзя удалить!")
            return
        
        if messagebox.askyesno("Удаление", f"Удалить ярлык '{self.text}' с рабочего стола?"):
            # Удаляем все элементы с канваса
            self.canvas.delete(f'hitbox_{self.icon_id}')
            self.canvas.delete(f'icon_{self.icon_id}')
            self.canvas.delete(f'text_{self.icon_id}')
            
            if self in self.canvas.desktop_icons:
                self.canvas.desktop_icons.remove(self)
            
            if hasattr(self.canvas, 'rearrange_icons'):
                self.canvas.rearrange_icons()
            if hasattr(self.canvas, 'save_shortcuts'):
                self.canvas.save_shortcuts()
    
    def show_properties(self):
        info = [
            f"Название: {self.text}",
            f"Иконка: {self.icon}",
            f"Позиция в сетке: ({self.grid_x}, {self.grid_y})",
            f"Координаты: ({self.x}, {self.y})"
        ]
        messagebox.showinfo("Свойства ярлыка", "\n".join(info))
    
    def move_to_grid(self, new_grid_x, new_grid_y):
        self.grid_x = new_grid_x
        self.grid_y = new_grid_y
        self.update_position()
        
        # Обновляем позицию хитбокса
        hitbox_width = 90
        hitbox_height = 90
        x1 = self.x - hitbox_width // 2
        y1 = self.y - 30
        x2 = self.x + hitbox_width // 2
        y2 = self.y + 45
        self.canvas.coords(self.hitbox_id, x1, y1, x2, y2)
        
        # Обновляем позицию иконки и текста
        self.canvas.coords(self.icon_id_obj, self.x, self.y-15)
        self.canvas.coords(self.text_id, self.x, self.y+25)
    
    def update_theme(self, fg_color):
        if not self.selected and not self.hover:
            self.canvas.itemconfig(self.icon_id_obj, fill=fg_color)
            self.canvas.itemconfig(self.text_id, fill=fg_color)
    
    def to_dict(self):
        command_name = None
        if self.command:
            command_map = {
                'open_explorer': 'explorer',
                'open_network': 'network',
                'open_gallery': 'gallery',
                'open_trash': 'trash',
                'open_notes': 'notes',
                'open_calc': 'calc',
                'open_settings': 'settings',
                'open_paint': 'paint',
                'open_terminal': 'terminal',
                'open_bip_installer': 'bip_installer',
                'open_it_global_catalog': 'it_global_catalog',
            }
            for key, value in command_map.items():
                if key in str(self.command) or value in str(self.command):
                    command_name = value
                    break
        
        # Проверяем BIP приложения
        if not command_name and 'bip:' in str(self.command):
            command_name = str(self.command).split('bip:')[1].split(')')[0] if ')' in str(self.command) else str(self.command).split('bip:')[1]
            command_name = f"bip:{command_name}"
        
        return {
            'icon': self.icon,
            'text': self.text,
            'grid_x': self.grid_x,
            'grid_y': self.grid_y,
            'icon_id': self.icon_id,
            'command': command_name
        }

class Taskbar:
    """Панель задач с микшером звука, батареей, языком и центром уведомлений"""
    
    def __init__(self, parent, username, commands, theme_colors, 
                 desktop_canvas=None, desktop_icons_list=None, desktop=None):
        self.parent = parent
        self.username = username
        self.commands = commands
        self.theme_colors = theme_colors
        self.desktop_canvas = desktop_canvas
        self.desktop_icons_list = desktop_icons_list
        self.desktop = desktop
        
        # Инициализация атрибутов
        self.start_menu = None
        self.notification_panel = None
        self.mixer_window = None
        self.tooltip = None
        
        self.current_lang = "RU"
        
        # Громкость
        self.volume_config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            "System", "Config", "volume.cfg"
        )
        self.current_volume = self._load_volume()
        self.is_muted = self.current_volume == 0
        
        # Уведомления
        self.notification_center = None
        if desktop and hasattr(desktop, 'notification_center'):
            self.notification_center = desktop.notification_center
        self.unread_count = 0
        
        # Создание панели
        self.taskbar = tk.Frame(parent, bg=theme_colors['taskbar_bg'], height=40)
        self.taskbar.pack(fill=tk.X, side=tk.BOTTOM)
        self.taskbar.pack_propagate(False)
        
        # Кнопка ПУСК
        self.start_btn = tk.Button(self.taskbar, text="ПУСК", bg='#2C3E50', fg='white',
                                   font=('Segoe UI', 10, 'bold'), bd=0, padx=15, pady=5,
                                   cursor='hand2', command=self.show_start_menu)
        self.start_btn.pack(side=tk.LEFT, padx=5, pady=5)
        self.start_btn.bind('<Enter>', lambda e: self.start_btn.config(bg='#3498DB'))
        self.start_btn.bind('<Leave>', lambda e: self.start_btn.config(bg='#2C3E50'))
        
        # Разделитель
        tk.Frame(self.taskbar, width=2, bg='#34495E').pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Быстрые иконки
        self.quick_icons = [
            ('📁', 'Проводник', 'explorer'),
            ('🌐', 'Интернет', 'network'),
            ('🖼', 'Галерея', 'gallery'),
            ('🗑', 'Корзина', 'trash'),
            ('📦', 'Установщик BIP', 'bip_installer'),
            ('🌐', 'Каталог IT Global', 'it_global_catalog'),
            ('📝', 'Заметки', 'notes'),
            ('🧮', 'Калькулятор', 'calc'),
        ]
        
        self.quick_buttons = []
        for icon, text, cmd in self.quick_icons:
            btn = tk.Button(self.taskbar, text=icon, bg=theme_colors['taskbar_bg'], 
                           fg=theme_colors['taskbar_fg'], font=('Segoe UI', 16), 
                           bd=0, padx=8, pady=2, cursor='hand2',
                           activebackground='#3498DB', activeforeground='white',
                           command=lambda c=cmd: self.on_quick_click(c))
            btn.pack(side=tk.LEFT, padx=2)
            self.quick_buttons.append(btn)
            self.create_tooltip(btn, text)
        
        # Растягивающийся разделитель
        tk.Frame(self.taskbar, bg=theme_colors['taskbar_bg']).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )
        
        # Системный трей (правая часть)
        self.tray_frame = tk.Frame(self.taskbar, bg=theme_colors['taskbar_bg'])
        self.tray_frame.pack(side=tk.RIGHT, padx=10)
        
        # Кнопка уведомлений
        self.notify_btn = tk.Label(self.tray_frame, text="🔔", 
                                   bg=theme_colors['taskbar_bg'],
                                   fg=theme_colors['taskbar_fg'], 
                                   font=('Segoe UI', 14), cursor='hand2')
        self.notify_btn.pack(side=tk.LEFT, padx=5)
        self.notify_btn.bind('<Button-1>', self.toggle_notification_panel)
        self.notify_btn.bind('<Enter>', lambda e: self.notify_btn.config(bg='#34495E'))
        self.notify_btn.bind('<Leave>', lambda e: self.notify_btn.config(
            bg=theme_colors['taskbar_bg']))
        self.create_tooltip(self.notify_btn, "Центр уведомлений\nНажмите для просмотра")
        
        # Счетчик уведомлений (скрыт изначально)
        self.notify_badge = tk.Label(self.tray_frame, text="", bg='#E74C3C', fg='white',
                                     font=('Segoe UI', 8, 'bold'))
        
        # Кнопка громкости
        self.volume_btn = tk.Label(self.tray_frame, text=self._get_volume_icon(), 
                                    bg=theme_colors['taskbar_bg'],
                                    fg=theme_colors['taskbar_fg'], 
                                    font=('Segoe UI', 14), cursor='hand2')
        self.volume_btn.pack(side=tk.LEFT, padx=5)
        self.volume_btn.bind('<Button-1>', self.toggle_mixer)
        self.volume_btn.bind('<Enter>', lambda e: self.volume_btn.config(bg='#34495E'))
        self.volume_btn.bind('<Leave>', lambda e: self.volume_btn.config(
            bg=theme_colors['taskbar_bg']))
        self.create_tooltip(self.volume_btn, 
                           f"Громкость BITOS: {self.current_volume}%\nНажмите для настройки")
        
        # Кнопка языка
        self.lang_label = tk.Label(self.tray_frame, text=self.current_lang, 
                                    bg=theme_colors['taskbar_bg'],
                                    fg=theme_colors['taskbar_fg'], 
                                    font=('Segoe UI', 10, 'bold'), cursor='hand2')
        self.lang_label.pack(side=tk.LEFT, padx=5)
        self.lang_label.bind('<Button-1>', self.toggle_language)
        self.lang_label.bind('<Enter>', lambda e: self.lang_label.config(bg='#34495E'))
        self.lang_label.bind('<Leave>', lambda e: self.lang_label.config(
            bg=theme_colors['taskbar_bg']))
        self.create_tooltip(self.lang_label, 
                           "Сменить раскладку клавиатуры\nТекущий: Русский (RU)\nНажмите для переключения")
        
        # Индикатор батареи
        self.battery_label = tk.Label(self.tray_frame, text="🔋 ---%", 
                                       bg=theme_colors['taskbar_bg'],
                                       fg=theme_colors['taskbar_fg'], 
                                       font=('Segoe UI', 10))
        self.battery_label.pack(side=tk.LEFT, padx=5)
        self.create_tooltip(self.battery_label, "Состояние батареи")
        
        # Имя пользователя
        self.user_label = tk.Label(self.tray_frame, text=f"👤 {self.username}", 
                                    bg=theme_colors['taskbar_bg'],
                                    fg=theme_colors['taskbar_fg'], 
                                    font=('Segoe UI', 10))
        self.user_label.pack(side=tk.LEFT, padx=5)
        
        # Время и дата
        self.time_label = tk.Label(self.tray_frame, text="", bg=theme_colors['taskbar_bg'],
                                    fg=theme_colors['taskbar_fg'], font=('Segoe UI', 10))
        self.time_label.pack(side=tk.LEFT, padx=5)
        
        self.date_label = tk.Label(self.tray_frame, text="", bg=theme_colors['taskbar_bg'],
                                    fg=theme_colors['taskbar_fg'], font=('Segoe UI', 10))
        self.date_label.pack(side=tk.LEFT, padx=5)
        
        # Кнопка питания
        self.power_btn = tk.Button(self.tray_frame, text="⏻", bg=theme_colors['taskbar_bg'], 
                                    fg='#E74C3C', font=('Segoe UI', 12), bd=0, padx=5, 
                                    cursor='hand2', command=self.show_power_menu)
        self.power_btn.pack(side=tk.LEFT, padx=5)
        self.power_btn.bind('<Enter>', lambda e: self.power_btn.config(bg='#34495E'))
        self.power_btn.bind('<Leave>', lambda e: self.power_btn.config(
            bg=theme_colors['taskbar_bg']))
        self.create_tooltip(self.power_btn, "Меню питания\nВыключение/Перезагрузка/Выход")
        
        # Запуск обновления времени и батареи
        self.update_time()
        self.update_battery()
        self.check_notifications()

    # ===== УВЕДОМЛЕНИЯ =====
    
    def toggle_notification_panel(self, event=None):
        """Открыть/закрыть панель уведомлений"""
        if self.notification_panel and self.notification_panel.winfo_exists():
            self.notification_panel.destroy()
            self.notification_panel = None
            return
        
        self.notification_panel = tk.Toplevel(self.parent)
        self.notification_panel.title("🔔 Центр уведомлений")
        self.notification_panel.configure(bg='#2C3E50')
        self.notification_panel.overrideredirect(True)
        self.notification_panel.attributes('-topmost', True)
        
        panel_w, panel_h = 380, 500
        x = self.notify_btn.winfo_rootx() - panel_w + 30
        y = self.notify_btn.winfo_rooty() - panel_h - 5
        if y < 0:
            y = self.notify_btn.winfo_rooty() + 40
        
        self.notification_panel.geometry(f"{panel_w}x{panel_h}+{x}+{y}")
        
        header = tk.Frame(self.notification_panel, bg='#3498DB', height=50)
        header.pack(fill=tk.X)
        tk.Label(header, text="🔔 Центр уведомлений", bg='#3498DB', fg='white',
                font=('Segoe UI', 12, 'bold')).pack(side=tk.LEFT, padx=15, pady=12)
        
        clear_btn = tk.Label(header, text="Очистить всё", bg='#3498DB', fg='white',
                            font=('Segoe UI', 9), cursor='hand2')
        clear_btn.pack(side=tk.RIGHT, padx=15)
        clear_btn.bind('<Button-1>', lambda e: self.clear_all_notifications())
        
        self.notify_canvas = tk.Canvas(self.notification_panel, bg='#2C3E50', 
                                       highlightthickness=0)
        scrollbar = tk.Scrollbar(self.notification_panel, orient=tk.VERTICAL, 
                                command=self.notify_canvas.yview)
        self.notify_frame = tk.Frame(self.notify_canvas, bg='#2C3E50')
        
        self.notify_frame.bind("<Configure>", 
            lambda e: self.notify_canvas.configure(
                scrollregion=self.notify_canvas.bbox("all"))
        )
        
        self.notify_canvas.create_window((0, 0), window=self.notify_frame, anchor="nw")
        self.notify_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.notify_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.load_notifications()
        
        self.notification_panel.bind('<FocusOut>', lambda e: self.close_notification_panel())
        self.notification_panel.focus_set()
    
    def close_notification_panel(self):
        """Закрыть панель уведомлений"""
        if self.notification_panel and self.notification_panel.winfo_exists():
            self.notification_panel.destroy()
        self.notification_panel = None
    
    def load_notifications(self):
        """Загрузка уведомлений в панель"""
        for widget in self.notify_frame.winfo_children():
            widget.destroy()
        
        notifications = []
        if self.notification_center:
            notifications = self.notification_center.notifications
        
        if not notifications:
            tk.Label(self.notify_frame, text="📭 Нет уведомлений", bg='#2C3E50', fg='#95A5A6',
                    font=('Segoe UI', 12)).pack(pady=50)
            return
        
        for notif in reversed(notifications[-20:]):
            self.create_notification_item(notif)
    
    def create_notification_item(self, notification):
        """Создание элемента уведомления"""
        bg_color = '#34495E' if not notification.get('read', False) else '#2C3E50'
        
        item_frame = tk.Frame(self.notify_frame, bg=bg_color, relief=tk.RAISED, bd=1)
        item_frame.pack(fill=tk.X, padx=5, pady=2)
        
        icon_label = tk.Label(item_frame, text=notification.get('icon', '🔔'), 
                             bg=bg_color, fg='white', font=('Segoe UI', 16))
        icon_label.pack(side=tk.LEFT, padx=10, pady=8)
        
        text_frame = tk.Frame(item_frame, bg=bg_color)
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=5)
        
        tk.Label(text_frame, text=notification.get('title', ''), bg=bg_color, 
                fg='#3498DB', font=('Segoe UI', 10, 'bold'), anchor='w').pack(fill=tk.X)
        
        tk.Label(text_frame, text=notification.get('message', ''), bg=bg_color, 
                fg='#BDC3C7', font=('Segoe UI', 9), anchor='w', 
                wraplength=250, justify='left').pack(fill=tk.X)
        
        timestamp = notification.get('timestamp', '')
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime('%H:%M')
                tk.Label(text_frame, text=time_str, bg=bg_color, fg='#7F8C8D',
                        font=('Segoe UI', 8)).pack(anchor='e')
            except:
                pass
        
        del_btn = tk.Label(item_frame, text="✕", bg=bg_color, fg='#E74C3C',
                          font=('Segoe UI', 10), cursor='hand2')
        del_btn.pack(side=tk.RIGHT, padx=5)
        del_btn.bind('<Button-1>', lambda e, n=notification: self.delete_notification(n))
    
    def delete_notification(self, notification):
        """Удаление уведомления"""
        if self.notification_center and notification in self.notification_center.notifications:
            self.notification_center.notifications.remove(notification)
            self.notification_center.save_history()
        self.load_notifications()
    
    def clear_all_notifications(self):
        """Очистка всех уведомлений"""
        if self.notification_center:
            self.notification_center.notifications.clear()
            self.notification_center.save_history()
        self.load_notifications()
        self.close_notification_panel()
    
    def update_notification_badge(self, count):
        """Обновление счетчика уведомлений"""
        self.unread_count = count
        if count > 0:
            self.notify_btn.config(text="🔴")
            self.notify_badge.config(text=str(count))
            # Размещаем рядом с кнопкой уведомлений в трее
            self.notify_badge.place(x=self.notify_btn.winfo_x() + 15, y=0)
        else:
            self.notify_btn.config(text="🔔")
            self.notify_badge.place_forget()
    
    def check_notifications(self):
        """Периодическая проверка уведомлений"""
        if self.notification_center:
            unread = sum(1 for n in self.notification_center.notifications if not n.get('read', False))
            self.update_notification_badge(unread)
        self.parent.after(5000, self.check_notifications)

    # ===== ГРОМКОСТЬ =====
    
    def _load_volume(self):
        """Загрузка громкости"""
        try:
            if os.path.exists(self.volume_config_path):
                with open(self.volume_config_path, 'r') as f:
                    data = json.load(f)
                    vol = int(data.get('volume', 70))
                    return max(0, min(100, vol))
        except:
            pass
        return 70

    def _save_volume(self):
        """Сохранение громкости"""
        try:
            os.makedirs(os.path.dirname(self.volume_config_path), exist_ok=True)
            with open(self.volume_config_path, 'w') as f:
                json.dump({'volume': self.current_volume}, f)
        except:
            pass

    def _get_volume_icon(self):
        """Иконка громкости"""
        if self.is_muted or self.current_volume == 0:
            return "🔇"
        elif self.current_volume < 30:
            return "🔈"
        elif self.current_volume < 70:
            return "🔉"
        else:
            return "🔊"

    def _update_volume_icon(self):
        """Обновление иконки громкости"""
        self.volume_btn.config(text=self._get_volume_icon())
        state = "ВЫКЛЮЧЕН" if self.is_muted else f"{self.current_volume}%"
        self.create_tooltip(self.volume_btn, 
                           f"Громкость BITOS: {state}\nНажмите для настройки")

    def toggle_mixer(self, event=None):
        """Открыть/закрыть микшер громкости"""
        if self.mixer_window and self.mixer_window.winfo_exists():
            self.mixer_window.destroy()
            self.mixer_window = None
            return
        
        self.mixer_window = tk.Toplevel(self.parent)
        self.mixer_window.title("🔊 Микшер BITOS")
        self.mixer_window.configure(bg='#2C3E50')
        self.mixer_window.overrideredirect(True)
        self.mixer_window.attributes('-topmost', True)
        
        mixer_w, mixer_h = 280, 180
        x = self.volume_btn.winfo_rootx() - mixer_w + 30
        y = self.volume_btn.winfo_rooty() - mixer_h - 5
        if y < 0:
            y = self.volume_btn.winfo_rooty() + 40
        
        self.mixer_window.geometry(f"{mixer_w}x{mixer_h}+{x}+{y}")
        
        tk.Label(self.mixer_window, text="🔊 Громкость BITOS", bg='#2C3E50', fg='white',
                 font=('Segoe UI', 12, 'bold')).pack(pady=(15, 5))
        
        self.mixer_percent_label = tk.Label(self.mixer_window, 
                                              text=f"{self.current_volume}%" if not self.is_muted else "ВЫКЛЮЧЕНО",
                                             bg='#2C3E50', fg='#3498DB',
                                             font=('Segoe UI', 20, 'bold'))
        self.mixer_percent_label.pack(pady=5)
        
        self.volume_slider = tk.Scale(self.mixer_window, from_=0, to=100, orient=tk.HORIZONTAL,
                                       bg='#2C3E50', fg='white', highlightthickness=0,
                                       troughcolor='#34495E', sliderrelief=tk.FLAT,
                                       activebackground='#3498DB', length=240,
                                       showvalue=False, command=self._on_volume_change)
        self.volume_slider.set(self.current_volume)
        self.volume_slider.pack(pady=5)
        
        mute_text = "🔊 Включить звук" if self.is_muted else "🔇 Выключить звук"
        self.mute_btn = tk.Button(self.mixer_window, text=mute_text, bg='#34495E', fg='white',
                                   font=('Segoe UI', 10), bd=0, padx=15, pady=5,
                                   cursor='hand2', command=self._toggle_mute)
        self.mute_btn.pack(pady=10)
        self.mute_btn.bind('<Enter>', lambda e: self.mute_btn.config(bg='#3498DB'))
        self.mute_btn.bind('<Leave>', lambda e: self.mute_btn.config(bg='#34495E'))
        
        self.mixer_window.bind('<FocusOut>', lambda e: self._close_mixer())
        self.mixer_window.focus_set()

    def _on_volume_change(self, value):
        """Изменение громкости"""
        vol = int(float(value))
        self.current_volume = vol
        self.is_muted = vol == 0
        self._save_volume()
        self._update_volume_icon()
        
        if hasattr(self, 'mixer_percent_label') and self.mixer_percent_label.winfo_exists():
            self.mixer_percent_label.config(text=f"{vol}%")
        
        if hasattr(self, 'mute_btn') and self.mute_btn.winfo_exists():
            self.mute_btn.config(text="🔇 Выключить звук" if vol > 0 else "🔊 Включить звук")

    def _toggle_mute(self):
        """Включить/выключить звук"""
        if self.is_muted:
            self.current_volume = 50 if self.current_volume == 0 else self.current_volume
            self.is_muted = False
        else:
            self.is_muted = True
        
        self._save_volume()
        self._update_volume_icon()
        
        if hasattr(self, 'volume_slider') and self.volume_slider.winfo_exists():
            self.volume_slider.set(self.current_volume if not self.is_muted else 0)
        if hasattr(self, 'mixer_percent_label') and self.mixer_percent_label.winfo_exists():
            self.mixer_percent_label.config(
                text=f"{self.current_volume}%" if not self.is_muted else "ВЫКЛЮЧЕНО")
        if hasattr(self, 'mute_btn') and self.mute_btn.winfo_exists():
            self.mute_btn.config(
                text="🔊 Включить звук" if self.is_muted else "🔇 Выключить звук")

    def _close_mixer(self):
        """Закрыть микшер"""
        if self.mixer_window and self.mixer_window.winfo_exists():
            self.mixer_window.destroy()
        self.mixer_window = None

    def get_volume(self):
        """Получить текущую громкость"""
        if self.is_muted:
            return 0
        return self.current_volume

    # ===== ЯЗЫК =====
    
    def toggle_language(self, event=None):
        """Переключение языка"""
        if self.current_lang == "RU":
            self.current_lang = "EN"
            self.lang_label.config(text="EN", fg='#3498DB')
            self.switch_keyboard_layout("EN")
        else:
            self.current_lang = "RU"
            self.lang_label.config(text="RU", fg=self.theme_colors['taskbar_fg'])
            self.switch_keyboard_layout("RU")
        
        lang_name = "Английский (EN)" if self.current_lang == "EN" else "Русский (RU)"
        self.create_tooltip(self.lang_label, 
                           f"Сменить раскладку клавиатуры\nТекущий: {lang_name}\nНажмите для переключения")

    def switch_keyboard_layout(self, lang):
        """Переключение раскладки клавиатуры"""
        try:
            if platform.system() == "Windows":
                import ctypes
                if lang == "EN":
                    ctypes.windll.user32.LoadKeyboardLayoutW("00000409", 1)
                else:
                    ctypes.windll.user32.LoadKeyboardLayoutW("00000419", 1)
        except Exception as e:
            print(f"Не удалось переключить раскладку: {e}")

    # ===== БАТАРЕЯ =====
    
    def get_battery_info(self):
        """Получение информации о батарее"""
        try:
            if platform.system() == "Windows":
                try:
                    import psutil
                    battery = psutil.sensors_battery()
                    if battery:
                        return battery.percent, battery.power_plugged
                except ImportError:
                    pass
                try:
                    result = subprocess.run(
                        ['wmic', 'path', 'Win32_Battery', 'get', 
                         'EstimatedChargeRemaining,BatteryStatus'], 
                        capture_output=True, text=True, timeout=5
                    )
                    lines = result.stdout.strip().split('\n')
                    if len(lines) >= 2:
                        values = lines[1].strip().split()
                        if len(values) >= 2:
                            return int(values[0]), int(values[1]) == 2
                except:
                    pass
            elif platform.system() == "Linux":
                for bat in ["/sys/class/power_supply/BAT0", "/sys/class/power_supply/BAT1"]:
                    if os.path.exists(bat):
                        with open(os.path.join(bat, "capacity")) as f:
                            percent = int(f.read().strip())
                        with open(os.path.join(bat, "status")) as f:
                            status = f.read().strip()
                        return percent, status in ("Charging", "Full")
        except:
            pass
        return None, None

    def update_battery(self):
        """Обновление индикатора батареи"""
        try:
            percent, plugged = self.get_battery_info()
            if percent is not None:
                if plugged:
                    icon = "⚡"
                elif percent >= 20:
                    icon = "🔋"
                else:
                    icon = "🪫"
                
                self.battery_label.config(text=f"{icon} {percent}%")
                if percent <= 20 and not plugged:
                    self.battery_label.config(fg='#E74C3C')
                else:
                    self.battery_label.config(fg=self.theme_colors['taskbar_fg'])
                
                self.create_tooltip(self.battery_label, 
                    f"Батарея: {percent}%\n{'Заряжается' if plugged else 'От батареи'}")
            else:
                self.battery_label.config(text="🔌 ПК", fg=self.theme_colors['taskbar_fg'])
                self.create_tooltip(self.battery_label, "Питание от сети")
        except:
            self.battery_label.config(text="🔋 ---%", fg=self.theme_colors['taskbar_fg'])
        
        self.parent.after(10000, self.update_battery)

    # ===== ВРЕМЯ =====
    
    def update_time(self):
        """Обновление времени и даты"""
        now = datetime.now()
        self.time_label.config(text=now.strftime("%H:%M"))
        self.date_label.config(text=now.strftime("%d.%m.%Y"))
        self.parent.after(1000, self.update_time)

    # ===== МЕНЮ ПУСК =====
    
    def on_quick_click(self, command):
        """Обработчик клика по быстрой иконке"""
        if command in self.commands:
            self.commands[command]()

    def load_installed_apps_for_menu(self):
        """Загрузка установленных приложений для меню Пуск"""
        apps = []
        start_menu_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            "System", "Config", "start_menu_apps.json"
        )
        if os.path.exists(start_menu_file):
            try:
                with open(start_menu_file, 'r', encoding='utf-8') as f:
                    apps = json.load(f)
            except:
                pass
        return apps

    def show_start_menu(self):
        """Показать меню Пуск"""
        if self.start_menu and self.start_menu.winfo_exists():
            self.start_menu.destroy()
            self.start_menu = None
            return
        
        self.start_menu = tk.Toplevel(self.parent)
        self.start_menu.title("Меню Пуск")
        self.start_menu.configure(bg='#2C3E50')
        self.start_menu.overrideredirect(True)
        
        menu_width = 800
        menu_height = 600
        
        x = self.start_btn.winfo_rootx()
        y = self.start_btn.winfo_rooty() - menu_height
        if y < 0:
            y = self.start_btn.winfo_rooty() + 50
        self.start_menu.geometry(f"{menu_width}x{menu_height}+{x}+{y}")
        
        header = tk.Frame(self.start_menu, bg='#3498DB', height=80)
        header.pack(fill=tk.X)
        tk.Label(header, text=f"👤 {self.username}", bg='#3498DB', fg='white',
                font=('Segoe UI', 18, 'bold')).pack(pady=20)
        
        main_frame = tk.Frame(self.start_menu, bg='#2C3E50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        canvas = tk.Canvas(main_frame, bg='#2C3E50', highlightthickness=0)
        scrollbar = tk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#2C3E50')
        
        scrollable_frame.bind("<Configure>", 
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        all_apps = [
            ('📁', 'Проводник', 'explorer', 'Системные'),
            ('⚙', 'Настройки', 'settings', 'Системные'),
            ('🗑', 'Корзина', 'trash', 'Системные'),
            ('📡', 'Терминал', 'terminal', 'Системные'),
            ('📦', 'Установщик BIP', 'bip_installer', 'Системные'),
            ('🌐', 'Интернет', 'network', 'Сеть'),
            ('🖼', 'Галерея', 'gallery', 'Графика'),
            ('🎨', 'Paint', 'paint', 'Графика'),
            ('📝', 'Заметки', 'notes', 'Офис'),
            ('🧮', 'Калькулятор', 'calc', 'Офис'),
            ('🌐', 'Каталог IT Global', 'it_global_catalog', 'Прочее'),
        ]
        
        installed_bip_apps = self.load_installed_apps_for_menu()
        if installed_bip_apps:
            for app in installed_bip_apps:
                all_apps.append((
                    app.get('icon', '📦'), 
                    app.get('name', 'App'), 
                    f"bip:{app.get('id')}", 
                    'Установленные приложения'
                ))
        
        categories = {}
        for icon, name, cmd, category in all_apps:
            if category not in categories:
                categories[category] = []
            categories[category].append((icon, name, cmd))
        
        for category, apps in categories.items():
            cat_frame = tk.Frame(scrollable_frame, bg='#2C3E50')
            cat_frame.pack(fill=tk.X, pady=(10, 5))
            tk.Label(cat_frame, text=f"── {category} ──", bg='#2C3E50', fg='#3498DB',
                    font=('Segoe UI', 12, 'bold')).pack(anchor='w')
            
            apps_frame = tk.Frame(scrollable_frame, bg='#2C3E50')
            apps_frame.pack(fill=tk.X, pady=5)
            
            for i, (icon, name, cmd) in enumerate(apps):
                row = i // 4
                col = i % 4
                
                app_frame = tk.Frame(apps_frame, bg='#34495E', relief=tk.RAISED, bd=1)
                app_frame.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
                app_frame.configure(width=180, height=70)
                app_frame.grid_propagate(False)
                
                icon_label = tk.Label(app_frame, text=icon, bg='#34495E', fg='white',
                                     font=('Segoe UI', 24))
                icon_label.pack(pady=(5, 0))
                
                name_label = tk.Label(app_frame, text=name, bg='#34495E', fg='white',
                                     font=('Segoe UI', 9))
                name_label.pack()
                
                app_frame.app_data = {'icon': icon, 'name': name, 'command': cmd}
                
                def on_enter(e, f=app_frame):
                    f.config(bg='#3498DB')
                    for child in f.winfo_children():
                        child.config(bg='#3498DB')
                
                def on_leave(e, f=app_frame):
                    f.config(bg='#34495E')
                    for child in f.winfo_children():
                        child.config(bg='#34495E')
                
                app_frame.bind('<Enter>', on_enter)
                app_frame.bind('<Leave>', on_leave)
                app_frame.bind('<Button-1>', self.start_drag)
                app_frame.bind('<B1-Motion>', self.drag)
                app_frame.bind('<ButtonRelease-1>', 
                              lambda e, f=app_frame: self.drop_on_desktop(e, f))
                app_frame.bind('<Double-Button-1>', 
                              lambda e, c=cmd: self.launch_app(c, self.start_menu))
                
                icon_label.bind('<Button-1>', self.start_drag)
                icon_label.bind('<B1-Motion>', self.drag)
                icon_label.bind('<ButtonRelease-1>', 
                               lambda e, f=app_frame: self.drop_on_desktop(e, f))
                
                name_label.bind('<Button-1>', self.start_drag)
                name_label.bind('<B1-Motion>', self.drag)
                name_label.bind('<ButtonRelease-1>', 
                               lambda e, f=app_frame: self.drop_on_desktop(e, f))
            
            for col in range(4):
                apps_frame.grid_columnconfigure(col, weight=1)
        
        exit_frame = tk.Frame(scrollable_frame, bg='#2C3E50')
        exit_frame.pack(fill=tk.X, pady=(20, 10))
        exit_btn = tk.Button(exit_frame, text="🚪 Выйти из системы", bg='#E74C3C', fg='white',
                            font=('Segoe UI', 12, 'bold'), bd=0, padx=20, pady=10, 
                            cursor='hand2',
                            command=lambda: self.launch_app('logout', self.start_menu))
        exit_btn.pack(fill=tk.X, padx=50)
        exit_btn.bind('<Enter>', lambda e: exit_btn.config(bg='#C0392B'))
        exit_btn.bind('<Leave>', lambda e: exit_btn.config(bg='#E74C3C'))
        
        def on_focus_out(event):
            if event.widget != self.start_menu and event.widget not in self.start_menu.winfo_children():
                self.start_menu.destroy()
                self.start_menu = None
        
        self.start_menu.bind('<FocusOut>', on_focus_out)
        self.start_menu.focus_set()

    # ===== ПЕРЕТАСКИВАНИЕ =====
    
    drag_data = {"x": 0, "y": 0, "item": None, "icon": None, "name": None, "command": None}

    def start_drag(self, event):
        widget = event.widget
        while widget and not hasattr(widget, 'app_data'):
            widget = widget.master
        if widget and hasattr(widget, 'app_data'):
            self.drag_data["item"] = widget
            self.drag_data["icon"] = widget.app_data['icon']
            self.drag_data["name"] = widget.app_data['name']
            self.drag_data["command"] = widget.app_data['command']
            self.drag_data["x"] = event.x_root
            self.drag_data["y"] = event.y_root

    def drag(self, event):
        pass

    def find_next_grid_position(self, icons_list):
        used_positions = set()
        for icon in icons_list:
            if icon.text != "Корзина":
                used_positions.add((icon.grid_x, icon.grid_y))
        for row in range(20):
            for col in range(DesktopIcon.COLS):
                if (col, row) not in used_positions:
                    return col, row
        return 0, 0

    def drop_on_desktop(self, event, app_frame):
        if not self.desktop_canvas or not self.desktop_icons_list:
            if event.widget and event.widget.winfo_toplevel() == self.start_menu:
                self.launch_app(self.drag_data["command"], self.start_menu)
            self.drag_data = {"x": 0, "y": 0, "item": None, "icon": None, 
                            "name": None, "command": None}
            return
        
        x_root = event.x_root
        y_root = event.y_root
        
        desktop_x = self.desktop_canvas.winfo_rootx()
        desktop_y = self.desktop_canvas.winfo_rooty()
        desktop_width = self.desktop_canvas.winfo_width()
        desktop_height = self.desktop_canvas.winfo_height()
        
        if (desktop_x <= x_root <= desktop_x + desktop_width and 
            desktop_y <= y_root <= desktop_y + desktop_height):
            
            icon_text = self.drag_data["name"]
            icon_symbol = self.drag_data["icon"]
            command_name = self.drag_data["command"]
            
            existing = False
            for existing_icon in self.desktop_icons_list:
                if existing_icon.text == icon_text:
                    existing = True
                    break
            
            if not existing and command_name:
                new_grid_x, new_grid_y = self.find_next_grid_position(
                    self.desktop_icons_list)
                
                command = None
                if self.desktop:
                    command = self.desktop.get_command_by_name(command_name)
                
                if command:
                    new_icon = DesktopIcon(self.desktop_canvas, new_grid_x, new_grid_y,
                                          icon_symbol, icon_text, command)
                    new_icon.update_theme(self.theme_colors['icon_fg'])
                    self.desktop_icons_list.append(new_icon)
                    
                    if self.desktop:
                        self.desktop.save_desktop_shortcuts()
                        if hasattr(self.desktop.bitos, 'security'):
                            self.desktop.bitos.security.log_shortcut_create(
                                self.username, icon_text, (new_grid_x, new_grid_y))
                    
                    self.show_notification(f"Ярлык '{icon_text}' добавлен на рабочий стол")
        
        self.drag_data = {"x": 0, "y": 0, "item": None, "icon": None, 
                        "name": None, "command": None}

    def show_notification(self, message):
        if self.notification_center:
            self.notification_center.add_notification(
                "Рабочий стол",
                message,
                icon="📌",
                duration=3000
            )

    def launch_app(self, app_name, menu_window):
        if menu_window:
            menu_window.destroy()
            self.start_menu = None
        
        if app_name.startswith("bip:"):
            app_id = app_name.split(":", 1)[1]
            installer = BipInstaller(self.parent, 
                                    self.desktop.bitos if self.desktop else None)
            success, msg = installer.launch_app(app_id)
            if not success:
                messagebox.showerror("Ошибка", msg)
        elif app_name in self.commands:
            if hasattr(self, 'desktop') and self.desktop and hasattr(self.desktop.bitos, 'security'):
                self.desktop.bitos.security.log_app_launch(app_name, self.username)
            self.commands[app_name]()

    # ===== МЕНЮ ПИТАНИЯ =====
    
    def show_power_menu(self):
        power_menu = tk.Menu(self.parent, tearoff=0, bg='#2C3E50', fg='white', 
                            activebackground='#3498DB')
        power_menu.add_command(label="🔄 Перезагрузка", command=self.restart_system)
        power_menu.add_separator()
        power_menu.add_command(label="🚪 Выход", 
                              command=lambda: self.commands.get('logout', lambda: None)())
        power_menu.add_separator()
        power_menu.add_command(label="⏻ Выключение", command=self.shutdown_system)
        power_menu.post(self.power_btn.winfo_rootx(), 
                       self.power_btn.winfo_rooty() - 100)

    def shutdown_system(self):
        if messagebox.askyesno("Выключение", "Вы действительно хотите выключить компьютер?"):
            if hasattr(self, 'desktop') and self.desktop:
                if hasattr(self.desktop.bitos, 'security'):
                    self.desktop.bitos.security.log_shutdown(self.username)
                self.desktop.save_desktop_shortcuts()
                self.desktop.save_widgets()
            self.parent.destroy()
            shutdown_windows()

    def restart_system(self):
        if messagebox.askyesno("Перезагрузка", "Вы действительно хотите перезагрузить компьютер?"):
            if hasattr(self, 'desktop') and self.desktop:
                if hasattr(self.desktop.bitos, 'security'):
                    self.desktop.bitos.security.log_reboot(self.username)
                self.desktop.save_desktop_shortcuts()
                self.desktop.save_widgets()
            self.parent.destroy()
            restart_windows()

    # ===== ТУЛТИПЫ =====
    
    def create_tooltip(self, widget, text):
        def enter(event):
            x = widget.winfo_rootx() + 25
            y = widget.winfo_rooty() - 30
            self.tooltip = tk.Toplevel(widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")
            label = tk.Label(self.tooltip, text=text, background="#FFFFE0", 
                           relief=tk.SOLID, borderwidth=1, font=('Segoe UI', 9))
            label.pack()
        
        def leave(event):
            if self.tooltip:
                self.tooltip.destroy()
                self.tooltip = None
        
        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)

    def update_theme(self, theme_colors):
        self.theme_colors = theme_colors
        self.taskbar.config(bg=theme_colors['taskbar_bg'])
        
        for btn in self.quick_buttons:
            btn.config(bg=theme_colors['taskbar_bg'], fg=theme_colors['taskbar_fg'])
        
        self.user_label.config(bg=theme_colors['taskbar_bg'], fg=theme_colors['taskbar_fg'])
        self.time_label.config(bg=theme_colors['taskbar_bg'], fg=theme_colors['taskbar_fg'])
        self.date_label.config(bg=theme_colors['taskbar_bg'], fg=theme_colors['taskbar_fg'])
        self.battery_label.config(bg=theme_colors['taskbar_bg'], fg=theme_colors['taskbar_fg'])
        self.lang_label.config(bg=theme_colors['taskbar_bg'], fg=theme_colors['taskbar_fg'])
        self.volume_btn.config(bg=theme_colors['taskbar_bg'], fg=theme_colors['taskbar_fg'])
        self.notify_btn.config(bg=theme_colors['taskbar_bg'], fg=theme_colors['taskbar_fg'])
        self.power_btn.config(bg=theme_colors['taskbar_bg'])

        # ==================== КЛАСС 17: DevModeDialog ====================
class DevModeDialog:
    """Диалог входа в режим разработчика"""
    
    def __init__(self, parent, bitos_instance):
        self.parent = parent
        self.bitos = bitos_instance
        self.result = False
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("🔧 Режим разработчика")
        self.dialog.geometry("400x280")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        self.dialog.configure(bg='#F5F7FA')
        
        x = (self.dialog.winfo_screenwidth() - 400) // 2
        y = (self.dialog.winfo_screenheight() - 280) // 2
        self.dialog.geometry(f'+{x}+{y}')
        
        title_frame = tk.Frame(self.dialog, bg='#F5F7FA')
        title_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        tk.Label(title_frame, text="🔧", font=('Segoe UI', 48), bg='#F5F7FA', fg='#2C3E50').pack()
        tk.Label(title_frame, text="Вход в режим разработчика", font=('Segoe UI', 14, 'bold'), bg='#F5F7FA', fg='#2C3E50').pack(pady=(5, 0))
        tk.Label(title_frame, text="Введите пароль для доступа к расширенным функциям", font=('Segoe UI', 10), bg='#F5F7FA', fg='#7F8C8D').pack(pady=(5, 0))
        
        password_frame = tk.Frame(self.dialog, bg='#F5F7FA')
        password_frame.pack(fill=tk.X, padx=20, pady=20)
        tk.Label(password_frame, text="Пароль:", font=('Segoe UI', 11), bg='#F5F7FA', fg='#2C3E50').pack(anchor='w')
        self.password_entry = tk.Entry(password_frame, font=('Segoe UI', 11), show='•', bd=0, bg='white',
                                      highlightthickness=2, highlightcolor='#3498DB', highlightbackground='#BDC3C7')
        self.password_entry.pack(fill=tk.X, ipady=8, pady=(5, 0))
        self.password_entry.bind('<Return>', lambda e: self.check_password())
        self.password_entry.focus_set()
        
        info_label = tk.Label(self.dialog, text="Подсказка: стандартный пароль BIT642Os", font=('Segoe UI', 9), bg='#F5F7FA', fg='#3498DB', cursor='hand2')
        info_label.pack(pady=5)
        info_label.bind('<Button-1>', lambda e: self.show_hint())
        
        button_frame = tk.Frame(self.dialog, bg='#F5F7FA')
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        tk.Button(button_frame, text="Войти", bg='#3498DB', fg='white', font=('Segoe UI', 10, 'bold'), bd=0, padx=30, pady=8, cursor='hand2',
                 command=self.check_password).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Отмена", bg='#E74C3C', fg='white', font=('Segoe UI', 10, 'bold'), bd=0, padx=30, pady=8, cursor='hand2',
                 command=self.cancel).pack(side=tk.LEFT, padx=5)
        
        self.message_label = tk.Label(self.dialog, text='', bg='#F5F7FA', fg='#E74C3C', font=('Segoe UI', 10))
        self.message_label.pack(pady=5)
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel)
    
    def show_hint(self):
        messagebox.showinfo("Подсказка", "Пароль режима разработчика: BIT642Os\n\nПосле входа используйте терминал для команд:\nhedev - полная справка\nsystem - команды системы\nuser - команды пользователей\nnetwork - сетевые команды\ndiag - диагностика\nutil - утилиты")
    
    def check_password(self):
        password = self.password_entry.get().strip()
        if password == self.bitos.dev_password:
            self.bitos.dev_mode = True
            self.bitos.dev_log("DEV MODE ACTIVATED")
            self.result = True
            self.dialog.destroy()
            messagebox.showinfo("Режим разработчика", "✅ Режим разработчика активирован!\n\nДоступные команды можно ввести в терминале:\nhedev - полная справка\nsystem - команды системы\nuser - команды пользователей\nnetwork - сетевые команды\ndiag - диагностика\nutil - утилиты")
        else:
            self.message_label.config(text='❌ Неверный пароль')
            self.password_entry.delete(0, tk.END)
            self.password_entry.focus_set()
    
    def cancel(self):
        self.result = False
        self.dialog.destroy()

# ==================== КЛАСС: BipInstaller ====================
class BipInstaller:
    """Установщик .bip пакетов для BITOS"""
    
    def __init__(self, parent, bitos):
        self.parent = parent
        self.bitos = bitos
        self.apps_path = os.path.join(bitos.base_path, "System", "Apps")
        self.installed_db = os.path.join(bitos.base_path, "System", "Apps", "installed.json")
        self.start_menu_db = os.path.join(bitos.system_paths["config"], "start_menu_apps.json")
        
        os.makedirs(self.apps_path, exist_ok=True)
        
        self.installed_apps = self.load_installed()
        self.start_menu_apps = self.load_start_menu_apps()
    
    def load_installed(self):
        if os.path.exists(self.installed_db):
            try:
                with open(self.installed_db, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_installed(self):
        with open(self.installed_db, 'w', encoding='utf-8') as f:
            json.dump(self.installed_apps, f, indent=4, ensure_ascii=False)
    
    def load_start_menu_apps(self):
        if os.path.exists(self.start_menu_db):
            try:
                with open(self.start_menu_db, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_start_menu_apps(self):
        with open(self.start_menu_db, 'w', encoding='utf-8') as f:
            json.dump(self.start_menu_apps, f, indent=4, ensure_ascii=False)
    
    def install_bip(self, bip_path):
        """Установка .bip пакета"""
        try:
            if not os.path.exists(bip_path):
                return False, "Файл не найден"
            
            if not bip_path.endswith('.bip'):
                return False, "Неверный формат файла. Ожидается .bip"
            
            # Читаем файл .bip (это текстовый файл с разметкой)
            with open(bip_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Парсим .bip файл
            metadata = {}
            app_code = ""
            
            lines = content.split('\n')
            in_metadata = False
            in_code = False
            
            for line in lines:
                if line.strip() == '---METADATA---':
                    in_metadata = True
                    in_code = False
                    continue
                elif line.strip() == '---CODE---':
                    in_metadata = False
                    in_code = True
                    continue
                
                if in_metadata and ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()
                elif in_code:
                    app_code += line + '\n'
            
            if not metadata:
                return False, "Неверный формат файла: отсутствуют метаданные"
            
            app_id = metadata.get('id')
            app_name = metadata.get('name', 'Unknown')
            app_version = metadata.get('version', '1.0')
            app_icon = metadata.get('icon', '📦')
            app_main = metadata.get('main', 'main.pyw')
            
            if not app_id:
                return False, "Отсутствует ID приложения в метаданных"
            
            if app_id in self.installed_apps:
                return False, f"Приложение '{app_name}' уже установлено"
            
            if not app_code.strip():
                return False, "Отсутствует код приложения"
            
            # Создаем папку приложения
            app_folder = os.path.join(self.apps_path, app_id)
            os.makedirs(app_folder, exist_ok=True)
            
            # Сохраняем метаданные
            with open(os.path.join(app_folder, 'package.json'), 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=4, ensure_ascii=False)
            
            # Сохраняем код приложения
            with open(os.path.join(app_folder, app_main), 'w', encoding='utf-8') as f:
                f.write(app_code)
            
            # Регистрируем приложение
            self.installed_apps[app_id] = {
                'name': app_name,
                'version': app_version,
                'icon': app_icon,
                'main': app_main,
                'install_date': datetime.now().isoformat(),
                'path': app_folder
            }
            self.save_installed()
            
            # Добавляем в меню Пуск
            self.add_to_start_menu(app_id, app_name, app_icon)
            
            if hasattr(self.bitos, 'security'):
                self.bitos.security.log_audit(f"APP_INSTALLED: {app_name} v{app_version}")
            
            return True, metadata
            
        except Exception as e:
            return False, f"Ошибка установки: {str(e)}"
    
    def add_to_start_menu(self, app_id, app_name, app_icon):
        """Добавление приложения в меню Пуск"""
        # Проверяем, нет ли уже такого приложения
        for app in self.start_menu_apps:
            if app.get('id') == app_id:
                return
        
        self.start_menu_apps.append({
            'id': app_id,
            'name': app_name,
            'icon': app_icon
        })
        self.save_start_menu_apps()
    
    def add_to_desktop(self, app_id, app_name, app_icon):
        """Добавление иконки на рабочий стол"""
        desktop_shortcuts_file = os.path.join(self.bitos.user_paths["home"], "desktop_shortcuts.json")
        
        shortcuts = []
        if os.path.exists(desktop_shortcuts_file):
            try:
                with open(desktop_shortcuts_file, 'r', encoding='utf-8') as f:
                    shortcuts = json.load(f)
            except:
                pass
        
        # Ищем свободную позицию
        used_positions = [(s.get('grid_x', 0), s.get('grid_y', 0)) for s in shortcuts]
        
        grid_x, grid_y = 0, 0
        for row in range(20):
            found = False
            for col in range(10):
                if (col, row) not in used_positions:
                    grid_x, grid_y = col, row
                    found = True
                    break
            if found:
                break
        
        shortcuts.append({
            'icon': app_icon,
            'text': app_name,
            'grid_x': grid_x,
            'grid_y': grid_y,
            'icon_id': f"{app_id}_{int(time.time())}",
            'command': f"bip:{app_id}"
        })
        
        with open(desktop_shortcuts_file, 'w', encoding='utf-8') as f:
            json.dump(shortcuts, f, indent=4, ensure_ascii=False)
    
    def launch_app(self, app_id):
        """Запуск установленного приложения"""
        if app_id not in self.installed_apps:
            return False, "Приложение не установлено"
        
        app_info = self.installed_apps[app_id]
        main_file = os.path.join(app_info['path'], app_info['main'])
        
        if not os.path.exists(main_file):
            return False, "Исполняемый файл не найден"
        
        try:
            if platform.system() == "Windows":
                subprocess.Popen(["pythonw", main_file], creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.Popen(["python3", main_file])
            return True, f"Запущено: {app_info['name']}"
        except Exception as e:
            return False, f"Ошибка запуска: {str(e)}"
    
    def get_installed_apps(self):
        return self.installed_apps
    
    def get_start_menu_apps(self):
        return self.start_menu_apps

# ==================== КЛАСС: BipInstallWindow (ИСПОЛЬЗУЕТ ВСТРОЕННЫЙ ПРОВОДНИК) ====================
class BipInstallWindow:
    """Окно установки .bip пакета"""
    
    def __init__(self, parent, bitos, desktop=None, bip_path=None):
        self.parent = parent
        self.bitos = bitos
        self.desktop = desktop
        self.installer = BipInstaller(parent, bitos)
        self.bip_path = bip_path
        self.metadata = None
        
        self.window = tk.Toplevel(parent)
        self.window.title("📦 Установщик BIP")
        self.window.geometry("500x650")
        self.window.transient(parent)
        self.window.configure(bg='#F5F7FA')
        self.window.resizable(False, False)
        
        x = (self.window.winfo_screenwidth() - 500) // 2
        y = (self.window.winfo_screenheight() - 650) // 2
        self.window.geometry(f'+{x}+{y}')
        
        self.create_ui()
        
        if bip_path:
            self.select_file(bip_path)
        else:
            # Автоматически открываем встроенный проводник
            self.window.after(300, self.open_builtin_explorer)
    
    def open_builtin_explorer(self):
        """Открывает встроенный проводник BITOS для выбора .bip файла"""
        downloads_path = self.bitos.downloads_path if hasattr(self.bitos, 'downloads_path') else os.path.expanduser("~")
        
        # Используем существующий ModernFileExplorer
        explorer = ModernFileExplorer(self.window, self.bitos, downloads_path)
        
        # Переопределяем метод открытия файла чтобы он работал с .bip
        original_open = explorer.open_file
        def custom_open_file(path):
            if path.lower().endswith('.bip'):
                self.select_file(path)
                explorer.on_close()
            else:
                original_open(path)
        
        explorer.open_file = custom_open_file
        self.file_label.config(text="Выберите файл .bip в проводнике...")
    
    def create_ui(self):
        header = tk.Frame(self.window, bg='#3498DB', height=60)
        header.pack(fill=tk.X)
        tk.Label(header, text="📦 Установщик пакетов BIP", bg='#3498DB', fg='white',
                font=('Segoe UI', 14, 'bold')).pack(pady=15)
        
        self.content = tk.Frame(self.window, bg='#F5F7FA')
        self.content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Выбор файла
        select_frame = tk.Frame(self.content, bg='#F5F7FA')
        select_frame.pack(fill=tk.X, pady=10)
        
        self.file_label = tk.Label(select_frame, text="Проводник открыт...", bg='white', fg='#7F8C8D',
                                   font=('Segoe UI', 10), anchor='w', relief=tk.SUNKEN, bd=1)
        self.file_label.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5, padx=(0, 5))
        
        tk.Button(select_frame, text="📂 Проводник", bg='#3498DB', fg='white',
                 font=('Segoe UI', 10), bd=0, padx=15, pady=5, cursor='hand2',
                 command=self.open_builtin_explorer).pack(side=tk.RIGHT)
        
        # Информация о пакете
        self.info_frame = tk.Frame(self.content, bg='white', relief=tk.RIDGE, bd=1)
        self.info_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(self.info_frame, text="Информация о пакете", bg='white', fg='#2C3E50',
                font=('Segoe UI', 11, 'bold')).pack(anchor='w', padx=10, pady=5)
        
        self.info_text = tk.Label(self.info_frame, text="Выберите файл .bip в проводнике",
                                  bg='white', fg='#7F8C8D', font=('Segoe UI', 10),
                                  justify='left', wraplength=420)
        self.info_text.pack(anchor='w', padx=10, pady=5)
        
        # Прогресс
        self.progress_frame = tk.Frame(self.content, bg='#F5F7FA')
        self.progress_frame.pack(fill=tk.X, pady=10)
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='determinate', length=460)
        self.progress_bar.pack()
        
        self.progress_label = tk.Label(self.progress_frame, text="", bg='#F5F7FA',
                                       fg='#2C3E50', font=('Segoe UI', 9))
        self.progress_label.pack(pady=5)
        
        # Опции
        self.options_frame = tk.Frame(self.content, bg='#F5F7FA')
        self.options_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(self.options_frame, text="Параметры установки:", bg='#F5F7FA',
                fg='#2C3E50', font=('Segoe UI', 11, 'bold')).pack(anchor='w')
        
        self.add_to_desktop_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self.options_frame, text="Добавить ярлык на рабочий стол",
                      variable=self.add_to_desktop_var, bg='#F5F7FA', fg='#2C3E50',
                      font=('Segoe UI', 10)).pack(anchor='w', padx=20, pady=5)
        
        # Кнопка установки
        self.install_btn = tk.Button(self.content, text="📥 Установить", bg='#27AE60', fg='white',
                                     font=('Segoe UI', 12, 'bold'), bd=0, padx=30, pady=10,
                                     cursor='hand2', command=self.start_install, state='disabled')
        self.install_btn.pack(pady=10)
        self.install_btn.bind('<Enter>', lambda e: self.install_btn.config(bg='#219A52'))
        self.install_btn.bind('<Leave>', lambda e: self.install_btn.config(bg='#27AE60'))
        
        self.status_label = tk.Label(self.content, text="", bg='#F5F7FA',
                                     fg='#2C3E50', font=('Segoe UI', 10))
        self.status_label.pack(pady=5)
    
    def select_file(self, file_path):
        """Обработка выбранного файла"""
        self.bip_path = file_path
        self.file_label.config(text=os.path.basename(file_path))
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            metadata = {}
            lines = content.split('\n')
            in_metadata = False
            
            for line in lines:
                if line.strip() == '---METADATA---':
                    in_metadata = True
                    continue
                elif line.strip() == '---CODE---':
                    break
                
                if in_metadata and ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()
            
            if metadata:
                self.metadata = metadata
                info = f"""
📦 Название: {metadata.get('name', 'Неизвестно')}
🔢 Версия: {metadata.get('version', '1.0')}
👤 Автор: {metadata.get('author', 'Неизвестен')}
📝 Описание: {metadata.get('description', 'Нет описания')}
📂 Категория: {metadata.get('category', 'Без категории')}
📄 Файл: {metadata.get('main', 'main.pyw')}
"""
                self.info_text.config(text=info, fg='#2C3E50')
                self.install_btn.config(state='normal')
            else:
                self.info_text.config(text="❌ Неверный формат файла (нет метаданных)", fg='#E74C3C')
                self.metadata = None
                self.install_btn.config(state='disabled')
        except:
            self.info_text.config(text="❌ Ошибка чтения файла", fg='#E74C3C')
            self.metadata = None
            self.install_btn.config(state='disabled')
    
    def start_install(self):
        if not self.bip_path or not self.metadata:
            return
        
        self.install_btn.config(state='disabled')
        self.status_label.config(text="⏳ Установка...")
        
        thread = threading.Thread(target=self.install_process)
        thread.daemon = True
        thread.start()
    
    def install_process(self):
        for i in range(101):
            time.sleep(0.05)
            self.window.after(0, self.update_progress, i, "Распаковка и установка...")
        
        success, result = self.installer.install_bip(self.bip_path)
        
        if success:
            if self.add_to_desktop_var.get():
                app_id = result.get('id')
                app_name = result.get('name')
                app_icon = result.get('icon', '📦')
                self.installer.add_to_desktop(app_id, app_name, app_icon)
            
            self.window.after(0, self.install_complete, result)
        else:
            self.window.after(0, self.install_failed, result)
    
    def update_progress(self, value, text):
        self.progress_bar['value'] = value
        self.progress_label.config(text=f"{text} {value}%")
    
    def install_complete(self, metadata):
        self.progress_bar['value'] = 100
        self.progress_label.config(text="✅ Установка завершена!")
        self.status_label.config(text=f"✅ {metadata.get('name')} успешно установлен!", fg='#27AE60')
        self.install_btn.config(text="✅ Готово", state='disabled', bg='#95A5A6')
        
        desktop_msg = "и на рабочий стол" if self.add_to_desktop_var.get() else ""
        messagebox.showinfo("Успех", 
            f"Приложение '{metadata.get('name')}' установлено!\n"
            f"Доступно в меню Пуск → Установленные приложения {desktop_msg}")
    
    def install_failed(self, error):
        self.progress_bar['value'] = 0
        self.progress_label.config(text="❌ Ошибка установки")
        self.status_label.config(text=f"❌ {error}", fg='#E74C3C')
        self.install_btn.config(state='normal')
        messagebox.showerror("Ошибка", error)

class Desktop:
    """Рабочий стол с обоями, виджетами и поддержкой BIP"""
    
    THEMES = {
        "Темная": {'name': 'Темная', 'bg': '#1E1E1E', 'fg': 'white', 
                   'taskbar_bg': '#2C3E50', 'taskbar_fg': 'white', 
                   'canvas_bg': '#1E1E1E', 'icon_fg': 'white',
                   'widget_bg': '#2C3E50', 'widget_fg': 'white'},
        "Светлая": {'name': 'Светлая', 'bg': '#F5F7FA', 'fg': '#2C3E50', 
                    'taskbar_bg': '#D0D0D0', 'taskbar_fg': '#2C3E50', 
                    'canvas_bg': '#F5F7FA', 'icon_fg': '#2C3E50',
                    'widget_bg': '#FFFFFF', 'widget_fg': '#2C3E50'},
        "Синяя": {'name': 'Синяя', 'bg': '#3498DB', 'fg': 'white', 
                  'taskbar_bg': '#1F618D', 'taskbar_fg': 'white', 
                  'canvas_bg': '#3498DB', 'icon_fg': 'white',
                  'widget_bg': '#2980B9', 'widget_fg': 'white'},
        "Зеленая": {'name': 'Зеленая', 'bg': '#27AE60', 'fg': 'white', 
                    'taskbar_bg': '#1E8449', 'taskbar_fg': 'white', 
                    'canvas_bg': '#27AE60', 'icon_fg': 'white',
                    'widget_bg': '#229954', 'widget_fg': 'white'},
        "Фиолетовая": {'name': 'Фиолетовая', 'bg': '#9B59B6', 'fg': 'white', 
                       'taskbar_bg': '#6C3483', 'taskbar_fg': 'white', 
                       'canvas_bg': '#9B59B6', 'icon_fg': 'white',
                       'widget_bg': '#8E44AD', 'widget_fg': 'white'}
    }

    def __init__(self, root, username, bitos_instance):
        self.root = root
        self.username = username
        self.bitos = bitos_instance
        
        # Сохраняем ссылку на desktop в bitos для доступа из проводника
        self.bitos.desktop_instance = self
        
        self.current_theme = self.load_theme()
        self.theme_colors = self.THEMES[self.current_theme]
        
        # Менеджеры
        self.wallpaper_manager = WallpaperManager(bitos_instance)
        self.notification_center = NotificationCenter(root, bitos_instance)
        
        self.root.overrideredirect(True)
        self.root.state('zoomed')
        self.root.configure(bg=self.theme_colors['bg'])
        
        # Таймер для отложенного ресайза
        self._resize_timer = None
        
        # Основной canvas
        self.canvas = tk.Canvas(self.root, highlightthickness=0, 
                               bg=self.theme_colors['canvas_bg'], bd=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1, height=-40)
        
        self.canvas.desktop_icons = []
        self.canvas.rearrange_icons = self.rearrange_icons
        self.canvas.save_shortcuts = self.save_desktop_shortcuts
        
        # Виджеты
        self.widgets = []
        self.widget_visible = True
        
        # Словарь команд
        self.icon_commands = {
            'explorer': self.open_explorer,
            'network': self.open_network,
            'gallery': self.open_gallery,
            'trash': self.open_trash,
            'it_global_catalog': self.open_it_global_catalog,
            'notes': self.open_notes,
            'calc': self.open_calc,
            'settings': self.open_settings,
            'paint': self.open_paint,
            'terminal': self.open_terminal,
            'bip_installer': self.open_bip_installer,
        }
        
        # Сначала рисуем обои
        self.update_wallpaper()
        
        # Создаем иконки
        self.create_desktop_icons()
        self.load_desktop_shortcuts()
        self.load_desktop_files()  # Загружаем реальные файлы с рабочего стола
        
        # Загружаем виджеты
        self.load_widgets()
        
        # Контекстное меню
        self.create_context_menu()
        
        # Привязка событий
        self.canvas.bind('<Button-3>', self.show_context_menu)
        self.canvas.bind('<Button-1>', self.clear_selection)
        self.root.bind('<Escape>', self.toggle_fullscreen)
        self.root.bind('<Configure>', self.on_window_resize)
        
        # Команды для панели задач
        taskbar_commands = {
            'explorer': self.open_explorer,
            'network': self.open_network,
            'gallery': self.open_gallery,
            'trash': self.open_trash,
            'it_global_catalog': self.open_it_global_catalog,
            'notes': self.open_notes,
            'calc': self.open_calc,
            'settings': self.open_settings,
            'paint': self.open_paint,
            'terminal': self.open_terminal,
            'bip_installer': self.open_bip_installer,
            'logout': self.logout,
            'shutdown': self.shutdown,
            'reboot': self.reboot,
        }
        
        self.taskbar = Taskbar(self.root, username, taskbar_commands, 
                              self.theme_colors, self.canvas, 
                              self.canvas.desktop_icons, self)
        self.taskbar.desktop = self
        
        # Поднимаем иконки над обоями
        self.canvas.tag_raise('icon')
        
        # Приветственное уведомление
        self.root.after(1000, self.show_welcome_notification)
    
    def show_welcome_notification(self):
        """Приветственное уведомление"""
        self.notification_center.add_notification(
            "Добро пожаловать!",
            f"Пользователь {self.username} вошёл в систему BITOS",
            icon="👋",
            category="system"
        )
    
    def update_wallpaper(self):
        """Обновление обоев рабочего стола"""
        try:
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()
            
            if width > 1 and height > 1:
                self.canvas.delete('wallpaper')
                
                if not self.wallpaper_manager.draw_on_canvas(self.canvas, width, height):
                    self.draw_gradient_background(width, height)
                
                self.canvas.tag_raise('icon')
            else:
                self.root.after(100, self.update_wallpaper)
        except:
            pass
    
    def draw_gradient_background(self, width, height):
        """Рисует градиентный фон"""
        try:
            for i in range(0, height, 2):
                factor = i / height
                color = self._interpolate_color(
                    self.theme_colors['canvas_bg'],
                    self._adjust_brightness(self.theme_colors['canvas_bg'], 0.85),
                    factor
                )
                self.canvas.create_line(0, i, width, i, fill=color, tags='wallpaper')
        except:
            pass
    
    def _interpolate_color(self, color1, color2, factor):
        c1 = self._hex_to_rgb(color1)
        c2 = self._hex_to_rgb(color2)
        r = int(c1[0] + (c2[0] - c1[0]) * factor)
        g = int(c1[1] + (c2[1] - c1[1]) * factor)
        b = int(c1[2] + (c2[2] - c1[2]) * factor)
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def _hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _adjust_brightness(self, hex_color, factor):
        r, g, b = self._hex_to_rgb(hex_color)
        r = min(255, int(r * factor))
        g = min(255, int(g * factor))
        b = min(255, int(b * factor))
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def on_window_resize(self, event):
        """Обработчик изменения размера окна с задержкой"""
        if event.widget == self.root:
            if self._resize_timer:
                self.root.after_cancel(self._resize_timer)
            self._resize_timer = self.root.after(500, self._delayed_resize)
    
    def _delayed_resize(self):
        """Отложенное обновление после изменения размера"""
        try:
            self.update_wallpaper()
            self.canvas.tag_raise('icon')
        except:
            pass
        try:
            self.update_widgets_position()
        except:
            pass
    
    # ===== ЗАГРУЗКА ФАЙЛОВ С РАБОЧЕГО СТОЛА =====
    
    def load_desktop_files(self):
        """Загрузка реальных файлов и папок с рабочего стола как иконок"""
        desktop_path = self.bitos.user_paths.get("desktop", "")
        if not desktop_path or not os.path.exists(desktop_path):
            return
        
        try:
            items = os.listdir(desktop_path)
            
            # Сначала папки, потом файлы
            folders = []
            files = []
            for item in items:
                item_path = os.path.join(desktop_path, item)
                if os.path.isdir(item_path):
                    folders.append(item)
                else:
                    files.append(item)
            
            folders.sort(key=str.lower)
            files.sort(key=str.lower)
            
            # Добавляем папки
            for folder in folders:
                folder_path = os.path.join(desktop_path, folder)
                self._add_file_icon_to_desktop(folder_path, folder, is_dir=True)
            
            # Добавляем файлы
            for file in files:
                file_path = os.path.join(desktop_path, file)
                self._add_file_icon_to_desktop(file_path, file, is_dir=False)
            
            self.rearrange_icons()
        except Exception as e:
            print(f"Ошибка загрузки файлов рабочего стола: {e}")
    
    def _add_file_icon_to_desktop(self, path, name, is_dir=False):
        """Добавление иконки файла/папки на рабочий стол"""
        # Проверяем, нет ли уже такой иконки
        for icon in self.canvas.desktop_icons:
            if hasattr(icon, 'file_path') and icon.file_path == path:
                return
        
        if is_dir:
            icon_symbol = "📁"
            command = lambda p=path: self.open_explorer(p)
        else:
            icon_symbol = self._get_file_icon_symbol(name)
            command = lambda p=path: self._open_file_in_editor(p)
        
        # Находим свободную позицию
        grid_x, grid_y = self._find_free_grid_position()
        
        desktop_icon = DesktopIcon(self.canvas, grid_x, grid_y, icon_symbol, name, command)
        desktop_icon.file_path = path  # Сохраняем путь к файлу
        desktop_icon.is_file_item = True  # Помечаем как реальный файл
        desktop_icon.update_theme(self.theme_colors['icon_fg'])
        self.canvas.desktop_icons.append(desktop_icon)
        self.canvas.tag_raise('icon')
    
    def _find_free_grid_position(self):
        """Поиск свободной позиции в сетке"""
        used_positions = set()
        used_positions.add((0, 0))  # Корзина всегда в (0,0)
        
        for icon in self.canvas.desktop_icons:
            used_positions.add((icon.grid_x, icon.grid_y))
        
        for row in range(20):
            start_col = 0 if row > 0 else 1
            for col in range(start_col, DesktopIcon.COLS):
                if (col, row) not in used_positions:
                    return col, row
        return 1, 0
    
    def _get_file_icon_symbol(self, filename):
        """Получение иконки для файла"""
        ext = os.path.splitext(filename)[1].lower()
        icons = {
            '.txt': '📄', '.doc': '📝', '.docx': '📝',
            '.jpg': '🖼', '.jpeg': '🖼', '.png': '🖼', '.gif': '🖼', '.bmp': '🖼',
            '.mp3': '🎵', '.wav': '🎵', '.flac': '🎵',
            '.mp4': '🎬', '.avi': '🎬', '.mkv': '🎬',
            '.pdf': '📕', '.exe': '⚙',
            '.zip': '📦', '.rar': '📦', '.7z': '📦',
            '.py': '🐍', '.js': '📜', '.html': '🌐', '.css': '🎨',
            '.xls': '📊', '.xlsx': '📊', '.ppt': '📽', '.pptx': '📽',
            '.json': '📊', '.xml': '📝',
        }
        return icons.get(ext, '📄')
    
    def refresh_desktop_files(self):
        """Обновление отображения файлов на рабочем столе"""
        # Удаляем старые иконки файлов (не ярлыки и не корзину)
        icons_to_remove = []
        for icon in self.canvas.desktop_icons:
            if hasattr(icon, 'is_file_item') and icon.is_file_item and not icon.is_trash:
                icons_to_remove.append(icon)
        
        for icon in icons_to_remove:
            try:
                self.canvas.delete(f'hitbox_{icon.icon_id}')
                self.canvas.delete(f'icon_{icon.icon_id}')
                self.canvas.delete(f'text_{icon.icon_id}')
                self.canvas.desktop_icons.remove(icon)
            except:
                pass
        
        # Загружаем файлы заново
        self.load_desktop_files()
        self.canvas.tag_raise('icon')
    
    # ===== ВИДЖЕТЫ =====
    
    def load_widgets(self):
        """Загрузка сохранённых виджетов"""
        widgets_file = os.path.join(self.bitos.system_paths["config"], "widgets.json")
        if os.path.exists(widgets_file):
            try:
                with open(widgets_file, 'r', encoding='utf-8') as f:
                    widgets_config = json.load(f)
                
                for widget in self.widgets[:]:
                    try:
                        widget.destroy()
                    except:
                        pass
                self.widgets.clear()
                
                for config in widgets_config:
                    self.add_widget_from_config(config)
            except:
                pass
        
        if not self.widgets:
            self.add_default_widgets()
    
    def save_widgets(self):
        """Сохранение виджетов"""
        widgets_file = os.path.join(self.bitos.system_paths["config"], "widgets.json")
        configs = []
        for widget in self.widgets:
            try:
                if hasattr(widget, 'frame') and widget.frame and widget.frame.winfo_exists():
                    configs.append(widget.get_config())
            except:
                pass
        try:
            with open(widgets_file, 'w', encoding='utf-8') as f:
                json.dump(configs, f, indent=4, ensure_ascii=False)
        except:
            pass
    
    def add_default_widgets(self):
        """Добавление виджетов по умолчанию"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        clock_widget = ClockWidget(self.canvas, self.theme_colors, 
                                  screen_width - 220, 50)
        self.widgets.append(clock_widget)
        
        calendar_widget = CalendarWidget(self.canvas, self.theme_colors,
                                        screen_width - 220, 200)
        self.widgets.append(calendar_widget)
        
        sticker_widget = StickerWidget(self.canvas, self.theme_colors,
                                      50, screen_height - 250,
                                      "✨ Добро пожаловать в BITOS!\n\n"
                                      "• Правый клик — меню\n"
                                      "• Двойной клик — запуск\n"
                                      "• Перетаскивайте ярлыки\n\n"
                                      "🕐 Виджеты можно двигать\n"
                                      "🎨 Темы в настройках")
        self.widgets.append(sticker_widget)
        
        self.save_widgets()
    
    def add_widget_from_config(self, config):
        """Добавление виджета из конфигурации"""
        widget_type = config.get('type')
        x = config.get('x', 50)
        y = config.get('y', 50)
        
        try:
            if widget_type == 'clock':
                widget = ClockWidget(self.canvas, self.theme_colors, x, y)
            elif widget_type == 'calendar':
                widget = CalendarWidget(self.canvas, self.theme_colors, x, y)
            elif widget_type == 'sticker':
                widget = StickerWidget(self.canvas, self.theme_colors, x, y, 
                                      config.get('text', ''))
            else:
                return
            
            self.widgets.append(widget)
        except:
            pass
    
    def update_widgets_position(self):
        """Обновление позиций всех виджетов"""
        for widget in self.widgets[:]:
            try:
                if hasattr(widget, 'frame') and widget.frame and widget.frame.winfo_exists():
                    if hasattr(widget, 'update_position'):
                        widget.update_position()
                else:
                    self.widgets.remove(widget)
            except:
                if widget in self.widgets:
                    self.widgets.remove(widget)
    
    def toggle_widgets(self):
        """Показать/скрыть виджеты"""
        self.widget_visible = not self.widget_visible
        for widget in self.widgets[:]:
            try:
                if hasattr(widget, 'frame') and widget.frame and widget.frame.winfo_exists():
                    if self.widget_visible:
                        widget.show()
                    else:
                        widget.hide()
                else:
                    self.widgets.remove(widget)
            except:
                if widget in self.widgets:
                    self.widgets.remove(widget)
        
        status = "показаны" if self.widget_visible else "скрыты"
        self.notification_center.add_notification(
            "Виджеты",
            f"Виджеты {status}",
            icon="📌",
            duration=2000
        )
    
    def add_widget(self, widget_type):
        """Добавление нового виджета"""
        x = random.randint(50, 300)
        y = random.randint(50, 300)
        
        try:
            if widget_type == 'clock':
                widget = ClockWidget(self.canvas, self.theme_colors, x, y)
            elif widget_type == 'calendar':
                widget = CalendarWidget(self.canvas, self.theme_colors, x, y)
            elif widget_type == 'sticker':
                widget = StickerWidget(self.canvas, self.theme_colors, x, y, 
                                      "📝 Новая заметка\n\nПравый клик — изменить\nЛевый клик — перетащить")
            else:
                return
            
            self.widgets.append(widget)
            self.save_widgets()
            
            self.notification_center.add_notification(
                "Виджет добавлен",
                f"Виджет '{widget_type}' добавлен на рабочий стол",
                icon="📌"
            )
        except:
            pass
    
    def remove_all_widgets(self):
        """Удаление всех виджетов"""
        if messagebox.askyesno("Удаление виджетов", "Удалить все виджеты с рабочего стола?"):
            for widget in self.widgets[:]:
                try:
                    widget.destroy()
                except:
                    pass
            self.widgets.clear()
            self.save_widgets()
            
            self.notification_center.add_notification(
                "Виджеты удалены",
                "Все виджеты удалены с рабочего стола",
                icon="🗑"
            )
    
    def open_wallpaper_settings(self):
        """Открыть настройки обоев"""
        self.wallpaper_manager.open_wallpaper_selector(
            self.root, 
            callback=self.update_wallpaper
        )
    
    def load_theme(self):
        """Загрузка темы"""
        theme_file = os.path.join(self.bitos.system_paths["config"], "theme.cfg")
        if os.path.exists(theme_file):
            try:
                with open(theme_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    theme = data.get('theme', 'Темная')
                    if theme in self.THEMES:
                        return theme
            except:
                pass
        return "Темная"
    
    def save_theme(self, theme_name):
        """Сохранение темы"""
        theme_file = os.path.join(self.bitos.system_paths["config"], "theme.cfg")
        try:
            with open(theme_file, 'w', encoding='utf-8') as f:
                json.dump({'theme': theme_name}, f, indent=4)
        except:
            pass
    
    def create_desktop_icons(self):
        """Создание иконок рабочего стола (только корзина)"""
        trash_icon = DesktopIcon(self.canvas, 0, 0, '🗑', 'Корзина', self.open_trash)
        trash_icon.update_theme(self.theme_colors['icon_fg'])
        self.canvas.desktop_icons.append(trash_icon)
        self.canvas.tag_raise('icon')
    
    def rearrange_icons(self):
        """Упорядочивание иконок по сетке (корзина всегда в 0,0)"""
        trash_icon = None
        other_icons = []
        
        for icon in self.canvas.desktop_icons:
            if icon.is_trash:
                trash_icon = icon
            else:
                other_icons.append(icon)
        
        if trash_icon:
            trash_icon.move_to_grid(0, 0)
        
        for i, icon in enumerate(other_icons):
            col = (i % (DesktopIcon.COLS - 1)) + 1
            row = i // (DesktopIcon.COLS - 1)
            icon.move_to_grid(col, row)
        
        self.save_desktop_shortcuts()
        self.canvas.tag_raise('icon')
    
    def save_desktop_shortcuts(self):
        """Сохранение ярлыков рабочего стола"""
        shortcuts_file = os.path.join(self.bitos.user_paths["home"], "desktop_shortcuts.json")
        shortcuts = []
        for icon in self.canvas.desktop_icons:
            if icon.is_trash:
                continue
            # Сохраняем только ярлыки, не реальные файлы
            if hasattr(icon, 'is_file_item') and icon.is_file_item:
                continue
            icon_dict = icon.to_dict()
            if icon_dict.get('command'):
                shortcuts.append(icon_dict)
        try:
            with open(shortcuts_file, 'w', encoding='utf-8') as f:
                json.dump(shortcuts, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка сохранения ярлыков: {e}")
    
    def load_desktop_shortcuts(self):
        """Загрузка ярлыков рабочего стола"""
        shortcuts_file = os.path.join(self.bitos.user_paths["home"], "desktop_shortcuts.json")
        if os.path.exists(shortcuts_file):
            try:
                with open(shortcuts_file, 'r', encoding='utf-8') as f:
                    shortcuts = json.load(f)
                
                for shortcut in shortcuts:
                    cmd_name = shortcut.get('command', '')
                    if not cmd_name:
                        continue
                    
                    exists = False
                    for icon in self.canvas.desktop_icons:
                        if icon.text == shortcut.get('text') and not icon.is_trash:
                            exists = True
                            break
                    
                    if exists:
                        continue
                    
                    if cmd_name.startswith("bip:"):
                        app_id = cmd_name.split(":", 1)[1]
                        command = lambda aid=app_id: self.launch_bip_app(aid)
                    else:
                        command = self.icon_commands.get(cmd_name)
                    
                    if command:
                        desktop_icon = DesktopIcon(
                            self.canvas, 
                            shortcut.get('grid_x', 0), 
                            shortcut.get('grid_y', 0), 
                            shortcut.get('icon', '📄'), 
                            shortcut.get('text', 'Приложение'), 
                            command, 
                            shortcut.get('icon_id')
                        )
                        desktop_icon.update_theme(self.theme_colors['icon_fg'])
                        self.canvas.desktop_icons.append(desktop_icon)
                
                self.canvas.tag_raise('icon')
                self.rearrange_icons()
            except Exception as e:
                print(f"Ошибка загрузки ярлыков: {e}")
    
    def create_context_menu(self):
        """Создание контекстного меню рабочего стола с созданием файлов и папок"""
        self.context_menu = tk.Menu(self.root, tearoff=0, bg='#2C3E50', fg='white', 
                                   activebackground='#3498DB', activeforeground='white')
        
        # Подменю "Создать"
        create_menu = tk.Menu(self.context_menu, tearoff=0, bg='#2C3E50', fg='white',
                             activebackground='#3498DB')
        create_menu.add_command(label='📁 Новую папку', command=self.create_new_folder)
        create_menu.add_separator()
        create_menu.add_command(label='📄 Текстовый документ (.txt)', 
                               command=lambda: self.create_new_file('txt'))
        create_menu.add_command(label='🌐 HTML документ (.html)', 
                               command=lambda: self.create_new_file('html'))
        create_menu.add_command(label='🐍 Python скрипт (.py)', 
                               command=lambda: self.create_new_file('py'))
        create_menu.add_command(label='📜 JavaScript (.js)', 
                               command=lambda: self.create_new_file('js'))
        create_menu.add_command(label='🎨 Таблица стилей (.css)', 
                               command=lambda: self.create_new_file('css'))
        create_menu.add_command(label='📊 JSON файл (.json)', 
                               command=lambda: self.create_new_file('json'))
        create_menu.add_command(label='📝 XML файл (.xml)', 
                               command=lambda: self.create_new_file('xml'))
        create_menu.add_separator()
        create_menu.add_command(label='📋 Другой файл...', command=self.create_custom_file)
        
        self.context_menu.add_cascade(label='➕ Создать', menu=create_menu)
        self.context_menu.add_separator()
        
        self.context_menu.add_command(label='🔄 Обновить', command=self.refresh_desktop)
        self.context_menu.add_command(label='📁 Открыть проводник', command=self.open_explorer)
        self.context_menu.add_separator()
        self.context_menu.add_command(label='🖼 Сменить обои', command=self.open_wallpaper_settings)
        self.context_menu.add_command(label='📦 Установщик BIP', command=self.open_bip_installer)
        self.context_menu.add_separator()
        
        widget_menu = tk.Menu(self.context_menu, tearoff=0, bg='#2C3E50', fg='white',
                             activebackground='#3498DB')
        widget_menu.add_command(label='⏰ Добавить часы', 
                               command=lambda: self.add_widget('clock'))
        widget_menu.add_command(label='📅 Добавить календарь', 
                               command=lambda: self.add_widget('calendar'))
        widget_menu.add_command(label='📝 Добавить стикер', 
                               command=lambda: self.add_widget('sticker'))
        widget_menu.add_separator()
        widget_menu.add_command(label='👁 Показать/скрыть виджеты', 
                               command=self.toggle_widgets)
        widget_menu.add_command(label='🗑 Удалить все виджеты', 
                               command=self.remove_all_widgets)
        
        self.context_menu.add_cascade(label='📌 Виджеты', menu=widget_menu)
        self.context_menu.add_separator()
        
        self.context_menu.add_command(label='📋 Упорядочить иконки', 
                                     command=self.rearrange_icons)
        self.context_menu.add_separator()
        self.context_menu.add_command(label='🚪 Выйти', command=self.logout)
    
    # ===== СОЗДАНИЕ ФАЙЛОВ И ПАПОК =====
    
    def create_new_folder(self):
        """Создание новой папки на рабочем столе"""
        dialog = tk.Toplevel(self.root)
        dialog.title("📁 Новая папка")
        dialog.geometry("450x200")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg='#F5F7FA')
        dialog.resizable(False, False)
        
        x = (dialog.winfo_screenwidth() - 450) // 2
        y = (dialog.winfo_screenheight() - 200) // 2
        dialog.geometry(f'+{x}+{y}')
        
        header = tk.Frame(dialog, bg='#3498DB', height=50)
        header.pack(fill=tk.X)
        tk.Label(header, text="📁 Создание новой папки", bg='#3498DB', fg='white',
                font=('Segoe UI', 12, 'bold')).pack(pady=12)
        
        main_frame = tk.Frame(dialog, bg='#F5F7FA')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(main_frame, text="Имя папки:", bg='#F5F7FA', fg='#2C3E50',
                font=('Segoe UI', 11)).pack(anchor='w')
        
        name_entry = tk.Entry(main_frame, font=('Segoe UI', 12), bg='white', fg='#2C3E50',
                             relief=tk.SOLID, bd=1)
        name_entry.pack(fill=tk.X, ipady=5, pady=(5, 15))
        name_entry.insert(0, "Новая папка")
        name_entry.focus_set()
        name_entry.select_range(0, tk.END)
        
        btn_frame = tk.Frame(main_frame, bg='#F5F7FA')
        btn_frame.pack(fill=tk.X)
        
        def create():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning("Предупреждение", "Введите имя папки", parent=dialog)
                return
            
            desktop_path = self.bitos.user_paths["desktop"]
            folder_path = os.path.join(desktop_path, name)
            
            if os.path.exists(folder_path):
                messagebox.showwarning("Предупреждение", f"Папка '{name}' уже существует", parent=dialog)
                return
            
            try:
                os.makedirs(folder_path, exist_ok=True)
                
                if hasattr(self.bitos, 'security'):
                    self.bitos.security.log_folder_create(self.username, folder_path)
                
                # Добавляем иконку на рабочий стол
                self._add_file_icon_to_desktop(folder_path, name, is_dir=True)
                self.rearrange_icons()
                
                self.notification_center.add_notification(
                    "Папка создана",
                    f"Папка '{name}' создана на рабочем столе",
                    icon="📁",
                    duration=3000
                )
                
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось создать папку:\n{str(e)}", parent=dialog)
        
        tk.Button(btn_frame, text="Создать", bg='#27AE60', fg='white',
                 font=('Segoe UI', 10, 'bold'), bd=0, padx=20, pady=8,
                 command=create).pack(side=tk.RIGHT, padx=5)
        tk.Button(btn_frame, text="Отмена", bg='#95A5A6', fg='white',
                 font=('Segoe UI', 10), bd=0, padx=20, pady=8,
                 command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
        name_entry.bind('<Return>', lambda e: create())
    
    def create_new_file(self, extension):
        """Создание нового файла с указанным расширением"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"📄 Новый файл .{extension}")
        dialog.geometry("500x450")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg='#F5F7FA')
        dialog.resizable(False, False)
        
        x = (dialog.winfo_screenwidth() - 500) // 2
        y = (dialog.winfo_screenheight() - 450) // 2
        dialog.geometry(f'+{x}+{y}')
        
        header = tk.Frame(dialog, bg='#3498DB', height=50)
        header.pack(fill=tk.X)
        tk.Label(header, text=f"📄 Создание .{extension} файла", bg='#3498DB', fg='white',
                font=('Segoe UI', 12, 'bold')).pack(pady=12)
        
        main_frame = tk.Frame(dialog, bg='#F5F7FA')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(main_frame, text="Имя файла:", bg='#F5F7FA', fg='#2C3E50',
                font=('Segoe UI', 11)).pack(anchor='w')
        
        name_frame = tk.Frame(main_frame, bg='#F5F7FA')
        name_frame.pack(fill=tk.X, pady=(5, 10))
        
        name_entry = tk.Entry(name_frame, font=('Segoe UI', 12), bg='white', fg='#2C3E50',
                             relief=tk.SOLID, bd=1)
        name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        name_entry.insert(0, "новый_файл")
        
        tk.Label(name_frame, text=f".{extension}", bg='#F5F7FA', fg='#7F8C8D',
                font=('Segoe UI', 12)).pack(side=tk.LEFT, padx=5)
        
        initial_content = self._get_initial_content(extension)
        
        tk.Label(main_frame, text="Содержимое:", bg='#F5F7FA', fg='#2C3E50',
                font=('Segoe UI', 11)).pack(anchor='w', pady=(10, 5))
        
        text_area = scrolledtext.ScrolledText(main_frame, font=('Consolas', 11),
                                              bg='white', fg='#2C3E50', height=10)
        text_area.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        text_area.insert('1.0', initial_content)
        
        btn_frame = tk.Frame(main_frame, bg='#F5F7FA')
        btn_frame.pack(fill=tk.X)
        
        def create():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning("Предупреждение", "Введите имя файла", parent=dialog)
                return
            
            if not name.endswith(f'.{extension}'):
                name = f"{name}.{extension}"
            
            desktop_path = self.bitos.user_paths["desktop"]
            file_path = os.path.join(desktop_path, name)
            
            if os.path.exists(file_path):
                if not messagebox.askyesno("Файл существует", 
                                          f"Файл '{name}' уже существует. Перезаписать?",
                                          parent=dialog):
                    return
            
            try:
                content = text_area.get('1.0', tk.END)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                if hasattr(self.bitos, 'security'):
                    self.bitos.security.log_file_access(self.username, file_path, "CREATE")
                
                # Добавляем иконку на рабочий стол
                self._add_file_icon_to_desktop(file_path, name, is_dir=False)
                self.rearrange_icons()
                
                self.notification_center.add_notification(
                    "Файл создан",
                    f"Файл '{name}' создан на рабочем столе",
                    icon="📄",
                    duration=3000
                )
                
                dialog.destroy()
                
                # Открываем файл в редакторе
                self._open_file_in_editor(file_path)
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось создать файл:\n{str(e)}", parent=dialog)
        
        tk.Button(btn_frame, text="Создать и открыть", bg='#27AE60', fg='white',
                 font=('Segoe UI', 10, 'bold'), bd=0, padx=20, pady=8,
                 command=create).pack(side=tk.RIGHT, padx=5)
        tk.Button(btn_frame, text="Отмена", bg='#95A5A6', fg='white',
                 font=('Segoe UI', 10), bd=0, padx=20, pady=8,
                 command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
        name_entry.bind('<Return>', lambda e: create())
        name_entry.focus_set()
    
    def create_custom_file(self):
        """Создание файла с произвольным расширением"""
        dialog = tk.Toplevel(self.root)
        dialog.title("📋 Создать файл")
        dialog.geometry("500x450")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg='#F5F7FA')
        dialog.resizable(False, False)
        
        x = (dialog.winfo_screenwidth() - 500) // 2
        y = (dialog.winfo_screenheight() - 450) // 2
        dialog.geometry(f'+{x}+{y}')
        
        header = tk.Frame(dialog, bg='#3498DB', height=50)
        header.pack(fill=tk.X)
        tk.Label(header, text="📋 Создание файла", bg='#3498DB', fg='white',
                font=('Segoe UI', 12, 'bold')).pack(pady=12)
        
        main_frame = tk.Frame(dialog, bg='#F5F7FA')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(main_frame, text="Имя файла (с расширением):", bg='#F5F7FA', fg='#2C3E50',
                font=('Segoe UI', 11)).pack(anchor='w')
        
        name_entry = tk.Entry(main_frame, font=('Segoe UI', 12), bg='white', fg='#2C3E50',
                             relief=tk.SOLID, bd=1)
        name_entry.pack(fill=tk.X, ipady=5, pady=(5, 10))
        name_entry.insert(0, "новый_файл.txt")
        name_entry.focus_set()
        name_entry.select_range(0, tk.END)
        
        tk.Label(main_frame, text="Содержимое:", bg='#F5F7FA', fg='#2C3E50',
                font=('Segoe UI', 11)).pack(anchor='w', pady=(10, 5))
        
        text_area = scrolledtext.ScrolledText(main_frame, font=('Consolas', 11),
                                              bg='white', fg='#2C3E50', height=10)
        text_area.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        btn_frame = tk.Frame(main_frame, bg='#F5F7FA')
        btn_frame.pack(fill=tk.X)
        
        def create():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning("Предупреждение", "Введите имя файла", parent=dialog)
                return
            
            if '.' not in name:
                messagebox.showwarning("Предупреждение", 
                                      "Укажите расширение файла (например: .txt, .py)", 
                                      parent=dialog)
                return
            
            desktop_path = self.bitos.user_paths["desktop"]
            file_path = os.path.join(desktop_path, name)
            
            if os.path.exists(file_path):
                if not messagebox.askyesno("Файл существует", 
                                          f"Файл '{name}' уже существует. Перезаписать?",
                                          parent=dialog):
                    return
            
            try:
                content = text_area.get('1.0', tk.END)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                if hasattr(self.bitos, 'security'):
                    self.bitos.security.log_file_access(self.username, file_path, "CREATE")
                
                # Добавляем иконку на рабочий стол
                self._add_file_icon_to_desktop(file_path, name, is_dir=False)
                self.rearrange_icons()
                
                self.notification_center.add_notification(
                    "Файл создан",
                    f"Файл '{name}' создан на рабочем столе",
                    icon="📄",
                    duration=3000
                )
                
                dialog.destroy()
                self._open_file_in_editor(file_path)
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось создать файл:\n{str(e)}", parent=dialog)
        
        tk.Button(btn_frame, text="Создать и открыть", bg='#27AE60', fg='white',
                 font=('Segoe UI', 10, 'bold'), bd=0, padx=20, pady=8,
                 command=create).pack(side=tk.RIGHT, padx=5)
        tk.Button(btn_frame, text="Отмена", bg='#95A5A6', fg='white',
                 font=('Segoe UI', 10), bd=0, padx=20, pady=8,
                 command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
        name_entry.bind('<Return>', lambda e: create())
    
    def _get_initial_content(self, extension):
        """Получение начального содержимого для разных типов файлов"""
        templates = {
            'txt': '',
            'html': '<!DOCTYPE html>\n<html lang="ru">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>Новый документ</title>\n</head>\n<body>\n    <h1>Привет, BITOS!</h1>\n    <p>Это новый HTML документ.</p>\n</body>\n</html>\n',
            'py': '#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n\ndef main():\n    print("Привет, BITOS!")\n\nif __name__ == "__main__":\n    main()\n',
            'js': '// JavaScript файл\n\nfunction main() {\n    console.log("Привет, BITOS!");\n}\n\nmain();\n',
            'css': '/* CSS файл */\n\nbody {\n    font-family: Arial, sans-serif;\n    margin: 0;\n    padding: 20px;\n    background-color: #f0f0f0;\n}\n\nh1 {\n    color: #2C3E50;\n}\n',
            'json': '{\n    "name": "Новый проект",\n    "version": "1.0.0",\n    "description": "Создано в BITOS",\n    "author": "' + self.username + '"\n}\n',
            'xml': '<?xml version="1.0" encoding="UTF-8"?>\n<root>\n    <name>Новый документ</name>\n    <description>Создано в BITOS</description>\n</root>\n',
        }
        return templates.get(extension, '')
    
    def _open_file_in_editor(self, file_path):
        """Открытие файла во встроенном редакторе"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            dialog = tk.Toplevel(self.root)
            dialog.title(f"📄 {os.path.basename(file_path)}")
            dialog.geometry("800x600")
            dialog.transient(self.root)
            dialog.configure(bg='#F5F7FA')
            
            toolbar = tk.Frame(dialog, bg='#E0E0E0', height=40)
            toolbar.pack(fill=tk.X)
            
            file_label = tk.Label(toolbar, text=f"📄 {file_path}", bg='#E0E0E0', 
                                 fg='#2C3E50', font=('Segoe UI', 10))
            file_label.pack(side=tk.LEFT, padx=10)
            
            text_area = scrolledtext.ScrolledText(dialog, font=('Consolas', 12),
                                                  bg='white', fg='#2C3E50')
            text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text_area.insert('1.0', content)
            
            btn_frame = tk.Frame(dialog, bg='#F5F7FA')
            btn_frame.pack(fill=tk.X, padx=10, pady=5)
            
            def save():
                try:
                    new_content = text_area.get('1.0', tk.END)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    if hasattr(self.bitos, 'security'):
                        self.bitos.security.log_file_access(self.username, file_path, "EDIT")
                    
                    self.notification_center.add_notification(
                        "Файл сохранён",
                        f"Файл '{os.path.basename(file_path)}' успешно сохранён",
                        icon="💾",
                        duration=2000
                    )
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{str(e)}", parent=dialog)
            
            tk.Button(btn_frame, text="💾 Сохранить", bg='#3498DB', fg='white',
                     font=('Segoe UI', 10, 'bold'), bd=0, padx=20, pady=8,
                     command=save).pack(side=tk.LEFT, padx=5)
            
            tk.Button(btn_frame, text="❌ Закрыть", bg='#E74C3C', fg='white',
                     font=('Segoe UI', 10), bd=0, padx=20, pady=8,
                     command=dialog.destroy).pack(side=tk.LEFT, padx=5)
            
            dialog.bind('<Control-s>', lambda e: save())
            dialog.bind('<Control-S>', lambda e: save())
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n{str(e)}")
    
    def show_context_menu(self, event):
        """Показать контекстное меню"""
        overlapping = self.canvas.find_overlapping(event.x, event.y, event.x+1, event.y+1)
        for item in overlapping:
            tags = self.canvas.gettags(item)
            for tag in tags:
                if tag.startswith('icon_') or tag.startswith('text_') or tag.startswith('hitbox_'):
                    return
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def clear_selection(self, event=None):
        """Снять выделение со всех иконок"""
        if event is not None:
            try:
                overlapping = self.canvas.find_overlapping(event.x, event.y, event.x+1, event.y+1)
                for item in overlapping:
                    tags = self.canvas.gettags(item)
                    for tag in tags:
                        if tag.startswith('icon_') or tag.startswith('text_') or tag.startswith('hitbox_'):
                            return
            except AttributeError:
                pass
        
        for icon in self.canvas.desktop_icons:
            icon.selected = False
            if not icon.hover:
                try:
                    self.canvas.itemconfig(icon.icon_id_obj, fill=self.theme_colors['icon_fg'])
                    self.canvas.itemconfig(icon.text_id, fill=self.theme_colors['icon_fg'])
                except tk.TclError:
                    pass
    
    def toggle_fullscreen(self, event=None):
        """Переключение полноэкранного режима"""
        if not hasattr(self, 'fullscreen'):
            self.fullscreen = False
        self.fullscreen = not self.fullscreen
        self.root.attributes('-fullscreen', self.fullscreen)
    
    def change_theme(self, theme_name):
        """Смена темы оформления"""
        if theme_name in self.THEMES:
            old_theme = self.current_theme
            self.current_theme = theme_name
            self.theme_colors = self.THEMES[theme_name]
            self.save_theme(theme_name)
            
            self.root.configure(bg=self.theme_colors['bg'])
            self.canvas.config(bg=self.theme_colors['canvas_bg'])
            
            self.update_wallpaper()
            self.taskbar.update_theme(self.theme_colors)
            
            for icon in self.canvas.desktop_icons:
                try:
                    icon.update_theme(self.theme_colors['icon_fg'])
                except tk.TclError:
                    pass
            
            for widget in self.widgets[:]:
                try:
                    widget.update_theme(self.theme_colors)
                except:
                    if widget in self.widgets:
                        self.widgets.remove(widget)
            
            self.canvas.tag_raise('icon')
            
            for icon in self.canvas.desktop_icons:
                icon.selected = False
                if not icon.hover:
                    try:
                        self.canvas.itemconfig(icon.icon_id_obj, fill=self.theme_colors['icon_fg'])
                        self.canvas.itemconfig(icon.text_id, fill=self.theme_colors['icon_fg'])
                    except tk.TclError:
                        pass
            
            if hasattr(self.bitos, 'security'):
                self.bitos.security.log_theme_change(self.username, old_theme, theme_name)
            
            self.notification_center.add_notification(
                "Тема изменена",
                f"Применена тема: {theme_name}",
                icon="🎨",
                duration=3000
            )
    
    def get_command_by_name(self, name):
        """Получение команды по имени"""
        if name and name.startswith("bip:"):
            app_id = name.split(":", 1)[1]
            return lambda aid=app_id: self.launch_bip_app(aid)
        return self.icon_commands.get(name)
    
    def launch_bip_app(self, app_id):
        """Запуск BIP приложения"""
        installer = BipInstaller(self.root, self.bitos)
        success, msg = installer.launch_app(app_id)
        if not success:
            messagebox.showerror("Ошибка", msg)
    
    def open_it_global_catalog(self):
        """Открыть каталог IT Global"""
        if hasattr(self.bitos, 'security'):
            self.bitos.security.log_app_launch("IT Global Catalog", self.username)
        import webbrowser
        webbrowser.open("https://saryanich.github.io/services/")
    
    def open_bip_installer(self):
        """Открыть установщик BIP"""
        if hasattr(self.bitos, 'security'):
            self.bitos.security.log_app_launch("BIP Installer", self.username)
        BipInstallWindow(self.root, self.bitos, self)
    
    def open_explorer(self, path=None):
        """Открыть проводник"""
        if path is None:
            path = self.bitos.user_paths["home"]
        if hasattr(self.bitos, 'security'):
            self.bitos.security.log_app_launch("Explorer", self.username)
        ModernFileExplorer(self.root, self.bitos, path)
    
    def open_gallery(self):
        """Открыть галерею"""
        if hasattr(self.bitos, 'security'):
            self.bitos.security.log_app_launch("Gallery", self.username)
        Gallery(self.root, self.bitos)
    
    def open_network(self):
        """Открыть браузер"""
        if hasattr(self.bitos, 'security'):
            self.bitos.security.log_app_launch("Network", self.username)
        glonet_path = os.path.join(self.bitos.base_path, "System", "Glonet.exe")
        if os.path.exists(glonet_path):
            try:
                if platform.system() == "Windows":
                    subprocess.Popen([glonet_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                else:
                    subprocess.Popen([glonet_path])
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось запустить браузер Glonet: {e}")
        else:
            messagebox.showerror("Ошибка", f"Браузер Glonet.exe не найден по пути:\n{glonet_path}")
    
    def open_settings(self):
        """Открыть настройки"""
        if hasattr(self.bitos, 'security'):
            self.bitos.security.log_app_launch("Settings", self.username)
        dialog = tk.Toplevel(self.root)
        dialog.title("⚙ Настройки")
        dialog.geometry("800x600")
        dialog.transient(self.root)
        dialog.configure(bg='#F5F7FA')
        
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        theme_frame = ttk.Frame(notebook)
        notebook.add(theme_frame, text="Темы")
        
        theme_canvas = tk.Canvas(theme_frame, bg='white', highlightthickness=0)
        theme_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(theme_canvas, text="Выберите тему оформления:", font=('Segoe UI', 12, 'bold'), 
                bg='white', fg='#2C3E50').place(x=30, y=30)
        
        themes = [
            ("Темная", "#1E1E1E", "#FFFFFF"),
            ("Светлая", "#F5F7FA", "#2C3E50"),
            ("Синяя", "#3498DB", "#FFFFFF"),
            ("Зеленая", "#27AE60", "#FFFFFF"),
            ("Фиолетовая", "#9B59B6", "#FFFFFF")
        ]
        
        self.theme_var = tk.StringVar(value=self.current_theme)
        
        for i, (theme_name, bg_color, fg_color) in enumerate(themes):
            y_pos = 80 + i * 80
            
            preview = tk.Frame(theme_canvas, bg=bg_color, width=100, height=60, 
                             relief=tk.RIDGE, bd=1)
            preview.place(x=50, y=y_pos)
            tk.Label(preview, text="Aa", bg=bg_color, fg=fg_color, 
                    font=('Segoe UI', 16)).place(relx=0.5, rely=0.5, anchor='center')
            
            rb = tk.Radiobutton(theme_canvas, text=theme_name, variable=self.theme_var, 
                               value=theme_name, bg='white', fg='#2C3E50', 
                               font=('Segoe UI', 10), activebackground='white',
                               command=lambda t=theme_name: self.change_theme(t))
            rb.place(x=180, y=y_pos + 15)
        
        apply_btn = tk.Button(theme_canvas, text="Применить тему", bg='#3498DB', fg='white',
                             font=('Segoe UI', 10, 'bold'), bd=0, padx=30, pady=8,
                             cursor='hand2', 
                             command=lambda: self.change_theme(self.theme_var.get()))
        apply_btn.place(x=50, y=520)
        
        security_frame = ttk.Frame(notebook)
        notebook.add(security_frame, text="Безопасность")
        
        sec_canvas = tk.Canvas(security_frame, bg='white', highlightthickness=0)
        sec_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(sec_canvas, text="Изменение PIN-кода входа", font=('Segoe UI', 14, 'bold'),
                bg='white', fg='#2C3E50').place(x=30, y=30)
        
        tk.Label(sec_canvas, text="Текущий PIN-код:", bg='white', fg='#2C3E50',
                font=('Segoe UI', 11)).place(x=30, y=100)
        old_pin_entry = tk.Entry(sec_canvas, font=('Segoe UI', 12), show='•', width=20)
        old_pin_entry.place(x=30, y=130, width=250, height=35)
        
        tk.Label(sec_canvas, text="Новый PIN-код (4-8 цифр):", bg='white', fg='#2C3E50',
                font=('Segoe UI', 11)).place(x=30, y=180)
        new_pin_entry = tk.Entry(sec_canvas, font=('Segoe UI', 12), show='•', width=20)
        new_pin_entry.place(x=30, y=210, width=250, height=35)
        
        tk.Label(sec_canvas, text="Подтвердите новый PIN-код:", bg='white', fg='#2C3E50',
                font=('Segoe UI', 11)).place(x=30, y=260)
        confirm_pin_entry = tk.Entry(sec_canvas, font=('Segoe UI', 12), show='•', width=20)
        confirm_pin_entry.place(x=30, y=290, width=250, height=35)
        
        pin_status = tk.Label(sec_canvas, text="", bg='white', fg='#E74C3C', font=('Segoe UI', 10))
        pin_status.place(x=30, y=340)
        
        def change_pin():
            old_pin = old_pin_entry.get().strip()
            new_pin = new_pin_entry.get().strip()
            confirm_pin = confirm_pin_entry.get().strip()
            
            pin_file = os.path.join(self.bitos.base_path, "System", "Security", "pin.hash")
            saved_hash = ""
            if os.path.exists(pin_file):
                with open(pin_file, 'r') as f:
                    saved_hash = f.read().strip()
            
            if hashlib.sha256(old_pin.encode()).hexdigest() != saved_hash:
                pin_status.config(text="❌ Неверный текущий PIN-код", fg='#E74C3C')
                return
            if not new_pin.isdigit():
                pin_status.config(text="❌ PIN-код должен состоять только из цифр", fg='#E74C3C')
                return
            if len(new_pin) < 4 or len(new_pin) > 8:
                pin_status.config(text="❌ PIN-код должен быть от 4 до 8 цифр", fg='#E74C3C')
                return
            if new_pin != confirm_pin:
                pin_status.config(text="❌ PIN-коды не совпадают", fg='#E74C3C')
                return
            
            os.makedirs(os.path.dirname(pin_file), exist_ok=True)
            with open(pin_file, 'w') as f:
                f.write(hashlib.sha256(new_pin.encode()).hexdigest())
            
            pin_status.config(text="✅ PIN-код успешно изменён!", fg='#27AE60')
            old_pin_entry.delete(0, tk.END)
            new_pin_entry.delete(0, tk.END)
            confirm_pin_entry.delete(0, tk.END)
            
            if hasattr(self.bitos, 'security'):
                self.bitos.security.log_pin_change(self.username)
            
            self.notification_center.add_notification(
                "🔐 Пароль изменён",
                f"PIN-код входа успешно изменён пользователем {self.username}\n"
                f"В целях безопасности, старый пароль деактивирован\n"
                f"Дата изменения: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
                icon="🔒",
                category="security",
                duration=7000
            )
        
        tk.Button(sec_canvas, text="Изменить PIN-код", bg='#3498DB', fg='white',
                 font=('Segoe UI', 11, 'bold'), bd=0, padx=20, pady=8,
                 cursor='hand2', command=change_pin).place(x=30, y=380)
    
    def open_trash(self):
        """Открыть корзину"""
        if hasattr(self.bitos, 'security'):
            self.bitos.security.log_app_launch("Trash", self.username)
        TrashWindow(self.root, self.bitos)
    
    def open_calc(self):
        """Открыть калькулятор"""
        if hasattr(self.bitos, 'security'):
            self.bitos.security.log_app_launch("Calculator", self.username)
        dialog = tk.Toplevel(self.root)
        dialog.title("🧮 Калькулятор")
        dialog.geometry("300x400")
        dialog.transient(self.root)
        dialog.configure(bg='#F5F7FA')
        dialog.resizable(False, False)
        
        display = tk.Entry(dialog, font=('Arial', 18), justify='right', bd=0, 
                          bg='white', fg='#2C3E50')
        display.pack(fill=tk.X, padx=10, pady=10, ipady=10)
        
        buttons = [
            ['7', '8', '9', '/'],
            ['4', '5', '6', '*'],
            ['1', '2', '3', '-'],
            ['0', '.', '=', '+'],
            ['C', '√', 'π', 'e']
        ]
        
        def click(btn):
            current = display.get()
            if btn == 'C':
                display.delete(0, tk.END)
            elif btn == '=':
                try:
                    result = eval(current)
                    display.delete(0, tk.END)
                    display.insert(0, str(result))
                except:
                    display.delete(0, tk.END)
                    display.insert(0, "Ошибка")
            elif btn == '√':
                try:
                    result = math.sqrt(float(current))
                    display.delete(0, tk.END)
                    display.insert(0, str(result))
                except:
                    display.delete(0, tk.END)
                    display.insert(0, "Ошибка")
            elif btn == 'π':
                display.insert(tk.END, str(math.pi))
            elif btn == 'e':
                display.insert(tk.END, str(math.e))
            else:
                display.insert(tk.END, btn)
        
        btn_frame = tk.Frame(dialog, bg='#F5F7FA')
        btn_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        for i, row in enumerate(buttons):
            for j, btn in enumerate(row):
                b = tk.Button(btn_frame, text=btn, command=lambda x=btn: click(x),
                             bg='white', fg='#2C3E50', font=('Arial', 12, 'bold'),
                             bd=1, relief=tk.RAISED, cursor='hand2')
                b.grid(row=i, column=j, padx=2, pady=2, sticky='nsew')
                btn_frame.grid_columnconfigure(j, weight=1)
            btn_frame.grid_rowconfigure(i, weight=1)
    
    def open_notes(self):
        """Открыть заметки"""
        if hasattr(self.bitos, 'security'):
            self.bitos.security.log_app_launch("Notes", self.username)
        dialog = tk.Toplevel(self.root)
        dialog.title("📝 Заметки")
        dialog.geometry("700x500")
        dialog.transient(self.root)
        dialog.configure(bg='#F5F7FA')
        text_area = scrolledtext.ScrolledText(dialog, font=('Arial', 12))
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def open_terminal(self):
        """Открыть терминал"""
        if hasattr(self.bitos, 'security'):
            self.bitos.security.log_app_launch("Terminal", self.username)
        try:
            terminal_path = os.path.join(self.bitos.base_path, "System", "BITOSterm.pyw")
            if not os.path.exists(terminal_path):
                messagebox.showerror("Ошибка", "Терминал не найден")
                return
            if platform.system() == "Windows":
                subprocess.Popen(["python", terminal_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen(["python3", terminal_path])
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def open_paint(self):
        """Открыть Paint"""
        if hasattr(self.bitos, 'security'):
            self.bitos.security.log_app_launch("Paint", self.username)
        Paint(self.root)
    
    def refresh_desktop(self):
        """Обновить рабочий стол"""
        self.update_wallpaper()
        self.refresh_desktop_files()
        self.canvas.tag_raise('icon')
        self.notification_center.add_notification(
            "Рабочий стол обновлён",
            "Обои и файлы перезагружены",
            icon="🔄",
            duration=2000
        )
    
    def reboot(self):
        """Перезагрузка"""
        if messagebox.askyesno("Перезагрузка", "Перезагрузить компьютер?"):
            if hasattr(self.bitos, 'security'):
                self.bitos.security.log_reboot(self.username)
            self.save_desktop_shortcuts()
            self.save_widgets()
            self.root.destroy()
            restart_windows()
    
    def logout(self):
        """Выход из системы"""
        if messagebox.askyesno("Выход", "Выйти из системы?"):
            if hasattr(self.bitos, 'security'):
                self.bitos.security.log_logout(self.username)
            self.save_desktop_shortcuts()
            self.save_widgets()
            self.root.destroy()
            login = LoginScreen(self.bitos.after_login, self.bitos)
            login.run()
    
    def shutdown(self):
        """Выключение"""
        if messagebox.askyesno("Выключение", "Выключить компьютер?"):
            if hasattr(self.bitos, 'security'):
                self.bitos.security.log_shutdown(self.username)
            self.save_desktop_shortcuts()
            self.save_widgets()
            self.root.destroy()
            shutdown_windows()

class BITOS:
    """Ядро операционной системы BITOS"""
    def __init__(self):
        self.version = "05V6"
        self.build = "2026.03"
        self.running = True
        self.start_time = time.time()
        self.current_user = "User"
        self.last_logged_minute = None
        self.check_results = []
        self.security_violations = []
        
        self.input_blocker = InputBlocker()
         
        self.dev_mode = False
        self.dev_password = "BIT642Os"
        self.dev_commands_history = []
        self.protected_files = []
        
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        
        self.system_paths = {
             "config": os.path.join(self.base_path, "System", "Config"),
             "security": os.path.join(self.base_path, "System", "Security"),
             "logs": os.path.join(self.base_path, "System", "Logs"),
             "temp": os.path.join(self.base_path, "System", "Temp"),
             "system": os.path.join(self.base_path, "System"),
             "users": os.path.join(self.base_path, "User"),
        }
        
        self.user_paths = {
             "home": os.path.join(self.base_path, "User", self.current_user),
             "documents": os.path.join(self.base_path, "User", self.current_user, "Documents"),
             "secure": os.path.join(self.base_path, "User", self.current_user, "Secure"),
             "pictures": os.path.join(self.base_path, "User", self.current_user, "Pictures"),
             "downloads": os.path.join(self.base_path, "User", self.current_user, "Downloads"),
             "desktop": os.path.join(self.base_path, "User", self.current_user, "Desktop"),
        }
        
        self.documents_path = self.user_paths["documents"]
        self.secure_path = self.user_paths["secure"]
        self.pictures_path = self.user_paths["pictures"]
        self.downloads_path = self.user_paths["downloads"]
        self.temp_path = self.system_paths["temp"]
        
        self.system_files = {
             "serial": os.path.join(self.system_paths["security"], "serial.bin"),
             "license": os.path.join(self.system_paths["security"], "license.key"),
             "checksums": os.path.join(self.system_paths["security"], "checksums.db"),
             "dev_log": os.path.join(self.system_paths["logs"], "dev.log"),
             "system_config": os.path.join(self.system_paths["config"], "system.cfg"),
             "users_db": os.path.join(self.system_paths["config"], "users.db"),
             "pin_db": os.path.join(self.system_paths["security"], "pin.hash"),
        }
        
        self.log_files = {
             "boot": os.path.join(self.system_paths["logs"], "boot.log"),
             "access": os.path.join(self.system_paths["logs"], "access.log"),
             "error": os.path.join(self.system_paths["logs"], "error.log"),
             "audit": os.path.join(self.system_paths["logs"], "audit.log"),
             "apps": os.path.join(self.system_paths["logs"], "applications.log"),
             "files": os.path.join(self.system_paths["logs"], "files.log"),
             "security": os.path.join(self.system_paths["logs"], "security.log"),
        }
        
        self.protected_files = [
            self.system_files["serial"],
            self.system_files["license"],
            self.system_files["pin_db"],
        ]
        
        # === СЛОВАРИ ШИФРОВАНИЯ УДАЛЕНЫ ===
        # === self.init_encryption_dictionaries() УДАЛЕН ===
        
        self.initialize_filesystem()
        self.security = SecurityManager(self)
        self.run()

    # === МЕТОД init_encryption_dictionaries ПОЛНОСТЬЮ УДАЛЕН ===

    def initialize_filesystem(self):
        print("=" * 60)
        print("🔧 ИНИЦИАЛИЗАЦИЯ ФАЙЛОВОЙ СИСТЕМЫ BITOS")
        print("=" * 60)
        
        for name, path in self.system_paths.items():
            os.makedirs(path, exist_ok=True)
            print(f"  ✅ Создана папка: {name} -> {path}")
        
        for name, path in self.user_paths.items():
            os.makedirs(path, exist_ok=True)
            print(f"  ✅ Создана папка: {name} -> {path}")
        
        print("\n📄 СОЗДАНИЕ СИСТЕМНЫХ ФАЙЛОВ")
        print("-" * 40)
        self.create_system_files()
        
        print("\n🔐 ПРОВЕРКА БЕЗОПАСНОСТИ")
        print("-" * 40)
        modified = self.verify_and_restore_files()
        if modified > 0:
            print(f"  ⚠️ Восстановлено {modified} защищённых файлов")
        else:
            print(f"  ✅ Все защищённые файлы в порядке")
        
        self.init_log_files()
        self.write_boot_info()
        
        print("\n" + "=" * 60)
        print("✅ ФАЙЛОВАЯ СИСТЕМА BITOS ГОТОВА К РАБОТЕ!")
        print(f"📁 Базовая директория: {self.base_path}")
        print(f"👤 Пользователь: {self.current_user}")
        print(f"📅 Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60 + "\n")

    def create_system_files(self):
        if not os.path.exists(self.system_files["system_config"]):
            config_data = {"version": self.version, "build": self.build, "first_boot": datetime.now().isoformat(), "last_boot": datetime.now().isoformat(), "boot_count": 1, "default_user": self.current_user, "os_name": "BITOS", "architecture": platform.machine(), "python_version": platform.python_version()}
            with open(self.system_files["system_config"], "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            print(f"  ✅ Создан system.cfg")
        
        if not os.path.exists(self.system_files["serial"]):
            serial = self.generate_serial()
            with open(self.system_files["serial"], "w", encoding="utf-8") as f:
                f.write(f"BITOS-SERIAL-{serial}\n")
                f.write(f"Created: {datetime.now().isoformat()}\n")
                f.write(f"Version: {self.version}\n")
            print(f"  ✅ Создан serial.bin: {serial}")
        
        if not os.path.exists(self.system_files["license"]):
            license_data = {"product": "BITOS", "version": self.version, "license_type": "Evaluation", "valid_until": "2026-12-31", "issued_to": self.current_user, "issued_date": datetime.now().isoformat(), "features": ["full_access", "updates", "support"]}
            with open(self.system_files["license"], "w", encoding="utf-8") as f:
                json.dump(license_data, f, indent=4, ensure_ascii=False)
            print(f"  ✅ Создан license.key")
        
        if not os.path.exists(self.system_files["pin_db"]):
            default_pin_hash = hashlib.sha256("1234".encode()).hexdigest()
            with open(self.system_files["pin_db"], "w") as f:
                f.write(default_pin_hash)
            print(f"  ✅ Создан pin.hash (PIN по умолчанию: 1234)")
        
        if not os.path.exists(self.system_files["users_db"]):
            users_data = {self.current_user: {"created": datetime.now().isoformat(), "last_login": None, "is_admin": True, "home": self.user_paths["home"]}}
            with open(self.system_files["users_db"], "w", encoding="utf-8") as f:
                json.dump(users_data, f, indent=4, ensure_ascii=False)
            print(f"  ✅ Создан users.db")

    def init_log_files(self):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_headers = {
            "boot": f"╔══════════════════════════════════════════════════════════════════╗\n║                      BITOS BOOT LOG                               ║\n╠══════════════════════════════════════════════════════════════════╣\n║ Version: {self.version} ({self.build})\n║ Date: {datetime.now().strftime('%Y-%m-%d')}\n║ Time: {datetime.now().strftime('%H:%M:%S')}\n║ User: {self.current_user}\n╠══════════════════════════════════════════════════════════════════╣\n",
            "access": f"╔══════════════════════════════════════════════════════════════════╗\n║                     BITOS ACCESS LOG                              ║\n╚══════════════════════════════════════════════════════════════════╝\n",
            "error": f"╔══════════════════════════════════════════════════════════════════╗\n║                      BITOS ERROR LOG                              ║\n╚══════════════════════════════════════════════════════════════════╝\n",
            "audit": f"╔══════════════════════════════════════════════════════════════════╗\n║                      BITOS AUDIT LOG                              ║\n╠══════════════════════════════════════════════════════════════════╣\n║ Session started at: {timestamp}\n║ User: {self.current_user}\n╠══════════════════════════════════════════════════════════════════╣\n",
            "apps": f"╔══════════════════════════════════════════════════════════════════╗\n║                   BITOS APPLICATIONS LOG                          ║\n╚══════════════════════════════════════════════════════════════════╝\n",
            "files": f"╔══════════════════════════════════════════════════════════════════╗\n║                     BITOS FILES LOG                               ║\n╚══════════════════════════════════════════════════════════════════╝\n",
            "security": f"╔══════════════════════════════════════════════════════════════════╗\n║                    BITOS SECURITY LOG                             ║\n╚══════════════════════════════════════════════════════════════════╝\n",
        }
        for log_name, header in log_headers.items():
            log_path = self.log_files[log_name]
            if not os.path.exists(log_path) or os.path.getsize(log_path) == 0:
                with open(log_path, 'w', encoding='utf-8') as f:
                    f.write(header)
                print(f"  ✅ Создан {log_name}.log")

    def write_boot_info(self):
        boot_info = f"\n{'='*66}\nBITOS BOOT SEQUENCE COMPLETED\n{'='*66}\nVersion:     {self.version} ({self.build})\nBoot time:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nUser:        {self.current_user}\nPython:      {platform.python_version()}\nPlatform:    {platform.system()} {platform.release()}\nMachine:     {platform.machine()}\n{'='*66}\n"
        with open(self.log_files["boot"], 'a', encoding='utf-8') as f:
            f.write(boot_info)

    def generate_serial(self):
        import uuid
        try:
            mac = uuid.getnode()
            unique_string = f"{mac}{time.time()}{random.randint(1000, 9999)}"
        except:
            unique_string = f"{time.time()}{random.randint(1000, 9999)}{random.randint(1000, 9999)}"
        serial_hash = hashlib.md5(unique_string.encode()).hexdigest().upper()
        formatted = '-'.join([serial_hash[i:i+4] for i in range(0, 16, 4)])
        return formatted

    def calculate_checksum(self, filepath):
        if not os.path.exists(filepath):
            return None
        try:
            with open(filepath, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except:
            return None

    def save_checksums(self):
        checksums = {}
        for filepath in self.protected_files:
            if os.path.exists(filepath):
                checksums[filepath] = self.calculate_checksum(filepath)
        os.makedirs(os.path.dirname(self.system_files["checksums"]), exist_ok=True)
        with open(self.system_files["checksums"], 'w', encoding='utf-8') as f:
            json.dump(checksums, f, indent=4)
        if hasattr(self, 'security') and self.security:
            self.security.log_audit(f"Checksums saved for {len(checksums)} files")

    def load_checksums(self):
        if os.path.exists(self.system_files["checksums"]):
            try:
                with open(self.system_files["checksums"], 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def verify_and_restore_files(self):
        saved = self.load_checksums()
        modified = []
        for filepath in self.protected_files:
            if os.path.exists(filepath):
                current = self.calculate_checksum(filepath)
                if filepath in saved and current != saved[filepath]:
                    modified.append(filepath)
                    self.restore_file(filepath)
                    if hasattr(self, 'security') and self.security:
                        self.security.log_security_event("FILE_TAMPERED", f"File {os.path.basename(filepath)} was modified and restored")
        self.save_checksums()
        return len(modified)

    def restore_file(self, filepath):
        filename = os.path.basename(filepath)
        backup_dir = os.path.join(self.temp_path, "security_backups")
        os.makedirs(backup_dir, exist_ok=True)
        backup_name = f"{filename}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.backup"
        backup_path = os.path.join(backup_dir, backup_name)
        try:
            if os.path.exists(filepath):
                shutil.copy2(filepath, backup_path)
                print(f"  📁 Создана резервная копия: {backup_name}")
            if filename == "serial.bin":
                serial = self.generate_serial()
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"BITOS-SERIAL-{serial}\n")
                    f.write(f"Restored: {datetime.now().isoformat()}\n")
                print(f"  🔄 Восстановлен serial.bin с новым номером: {serial}")
            elif filename == "license.key":
                license_data = {"product": "BITOS", "version": self.version, "license_type": "Evaluation", "valid_until": "2026-12-31", "restored": True, "restored_date": datetime.now().isoformat()}
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(license_data, f, indent=4)
                print(f"  🔄 Восстановлен license.key")
            elif filename == "pin.hash":
                default_pin_hash = hashlib.sha256("1234".encode()).hexdigest()
                with open(filepath, 'w') as f:
                    f.write(default_pin_hash)
                print(f"  🔄 Восстановлен pin.hash (сброшен до 1234)")
            self.security_violations.append({"time": datetime.now().isoformat(), "file": filename, "backup": backup_name, "restored": True})
        except Exception as e:
            print(f"  ❌ Ошибка восстановления {filename}: {e}")
            if hasattr(self, 'security') and self.security:
                self.security.log_error("Restore", str(e), f"File: {filename}")

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        with open(self.log_files["boot"], 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
        print(message)

    def dev_log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.system_files["dev_log"], "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {message}\n")
        except:
            pass

    # === ВСЕ МЕТОДЫ ШИФРОВАНИЯ (ercc_encrypt, ercc_decrypt, ascii_encrypt, ascii_decrypt, unicode_encrypt, unicode_decrypt) ПОЛНОСТЬЮ УДАЛЕНЫ ===

    def boot_sequence(self):
        splash = SplashScreen()
        stages = [
            (10, "Проверка компонентов...", "Сканирование системных модулей"),
            (25, "Инициализация ядра...", "Загрузка драйверов устройств"),
            (40, "Проверка файловой системы...", "Сканирование директорий"),
            (55, "Загрузка конфигурации...", "Чтение системных настроек"),
            (70, "Проверка безопасности...", "Анализ защищенных файлов"),
            (85, "Запуск служб...", "Инициализация сервисов"),
            (95, "Подготовка интерфейса...", "Загрузка графических компонентов"),
            (100, "Готов к работе!", "Добро пожаловать в BITOS 05V6")
        ]
        for progress, status, details in stages:
            splash.update_progress(progress, status, details)
            time.sleep(0.3)
        splash.close()
        self.input_blocker.start_blocking()
        login = LoginScreen(self.after_login, self)
        login.run()

    def after_login(self, username):
        self.current_user = username
        self.user_paths["home"] = os.path.join(self.base_path, "User", username)
        self.user_paths["documents"] = os.path.join(self.base_path, "User", username, "Documents")
        self.user_paths["secure"] = os.path.join(self.base_path, "User", username, "Secure")
        self.user_paths["pictures"] = os.path.join(self.base_path, "User", username, "Pictures")
        self.user_paths["downloads"] = os.path.join(self.base_path, "User", username, "Downloads")
        self.user_paths["desktop"] = os.path.join(self.base_path, "User", username, "Desktop")
        
        self.documents_path = self.user_paths["documents"]
        self.secure_path = self.user_paths["secure"]
        self.pictures_path = self.user_paths["pictures"]
        self.downloads_path = self.user_paths["downloads"]
        
        for path in self.user_paths.values():
            os.makedirs(path, exist_ok=True)
        
        self.security = SecurityManager(self)
        self.security.log_access(username, "LOGIN", "SUCCESS", f"Session: {self.security.session_id}")
        self.log(f"Пользователь {username} вошел в систему")
        
        try:
            with open(self.system_files["users_db"], 'r', encoding='utf-8') as f:
                users = json.load(f)
            if username not in users:
                users[username] = {"created": datetime.now().isoformat(), "last_login": datetime.now().isoformat(), "is_admin": False, "home": self.user_paths["home"]}
            else:
                users[username]["last_login"] = datetime.now().isoformat()
            with open(self.system_files["users_db"], 'w', encoding='utf-8') as f:
                json.dump(users, f, indent=4, ensure_ascii=False)
        except:
            pass
        
        desktop_root = tk.Tk()
        desktop = Desktop(desktop_root, username, self)
        
        def on_desktop_close():
            self.input_blocker.stop_blocking()
            desktop_root.destroy()
        
        desktop_root.protocol("WM_DELETE_WINDOW", on_desktop_close)
        desktop_root.mainloop()

    def run(self):
        self.boot_sequence()

# ==================== КЛАСС 0: InputBlocker (С ЧИТ-КОДОМ) ====================
class InputBlocker:
    """Блокировщик с разблокировкой по комбинации: 5x CapsLock + 2x Tab"""
    
    def __init__(self):
        self.blocking = False
        self.available = KEYBOARD_AVAILABLE
        
        # Счетчики для чит-кода
        self.caps_count = 0
        self.tab_count = 0
        
        # Требуемое количество нажатий
        self.TARGET_CAPS = 5
        self.TARGET_TAB = 2
        
        if not self.available:
            print("⚠️ InputBlocker: библиотека keyboard не найдена")

    def start_blocking(self):
        if not self.available:
            return
        
        try:
            # Блокируем системные клавиши
            system_keys = [
                'win', 'left windows', 'right windows',
                'alt+tab', 'alt+f4', 'ctrl+esc',
                'win+d', 'win+r', 'win+l', 'win+e',
                'ctrl+shift+esc', 'ctrl+alt+del'
            ]
            for key in system_keys:
                keyboard.add_hotkey(key, lambda: None, suppress=True)
            
            # Вешаем обработчик на CapsLock и Tab для подсчета
            keyboard.on_press_key('caps lock', self._on_caps_press, suppress=False) # suppress=False чтобы видеть нажатие
            keyboard.on_press_key('tab', self._on_tab_press, suppress=False)
            
            self.blocking = True
            print("🔒 InputBlocker: Активирован. Чит-код: 5xCaps + 2xTab")
        except Exception as e:
            print(f"⚠️ Ошибка InputBlocker: {e}")

    def _on_caps_press(self, event):
        if not self.blocking:
            return
        self.caps_count += 1
        self.tab_count = 0 # Сброс табов, если последовательность прервана (опционально, можно убрать эту строку если порядок не важен)
        print(f"🔓 CapsLock: {self.caps_count}/{self.TARGET_CAPS}")
        self._check_unlock()

    def _on_tab_press(self, event):
        if not self.blocking:
            return
        # Табы считаем только если капсы уже нажаты (или просто накапливаем)
        # Для простоты: просто считаем табы. Если нужно строго после капсов - добавь условие if self.caps_count > 0:
        self.tab_count += 1
        print(f"🔓 Tab: {self.tab_count}/{self.TARGET_TAB}")
        self._check_unlock()

    def _check_unlock(self):
        if self.caps_count >= self.TARGET_CAPS and self.tab_count >= self.TARGET_TAB:
            print("✅ ЧИТ-КОД АКТИВИРОВАН! Клавиатура разблокирована.")
            self.stop_blocking()
            # Сброс счетчиков, чтобы можно было снова заблокировать (если нужно)
            self.caps_count = 0
            self.tab_count = 0

    def stop_blocking(self):
        if not self.available:
            return
        try:
            keyboard.unhook_all()
            self.blocking = False
            print("🔓 InputBlocker: Разблокировано")
        except:
            pass

    def is_active(self):
        return self.blocking

class WallpaperManager:
    """Менеджер обоев рабочего стола с выбором через встроенный проводник BITOS"""
    
    def __init__(self, bitos):
        self.bitos = bitos
        self.wallpaper_path = None
        self.wallpaper_style = "fill"
        self.wallpaper_dir = os.path.join(bitos.system_paths["config"], "wallpapers")
        os.makedirs(self.wallpaper_dir, exist_ok=True)
        self.load_config()
    
    def load_config(self):
        config_file = os.path.join(self.bitos.system_paths["config"], "wallpaper.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.wallpaper_path = config.get('path')
                    self.wallpaper_style = config.get('style', 'fill')
            except:
                pass
    
    def save_config(self):
        config_file = os.path.join(self.bitos.system_paths["config"], "wallpaper.json")
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'path': self.wallpaper_path,
                    'style': self.wallpaper_style
                }, f, indent=4)
        except:
            pass
    
    def set_wallpaper(self, image_path):
        if not os.path.exists(image_path):
            return False, "Файл не найден"
        
        if not image_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            return False, "Неподдерживаемый формат изображения"
        
        try:
            wallpaper_name = f"wallpaper_{datetime.now().strftime('%Y%m%d_%H%M%S')}{os.path.splitext(image_path)[1]}"
            dest_path = os.path.join(self.wallpaper_dir, wallpaper_name)
            shutil.copy2(image_path, dest_path)
            
            self.wallpaper_path = dest_path
            self.save_config()
            
            if hasattr(self.bitos, 'security'):
                self.bitos.security.log_audit(f"WALLPAPER_CHANGED: {wallpaper_name}")
            
            return True, dest_path
        except Exception as e:
            return False, str(e)
    
    def remove_wallpaper(self):
        self.wallpaper_path = None
        self.save_config()
    
    def get_wallpaper(self):
        return self.wallpaper_path
    
    def open_wallpaper_selector(self, parent, callback=None):
        """Открывает окно выбора обоев через встроенный проводник"""
        dialog = tk.Toplevel(parent)
        dialog.title("🖼 Выбор обоев рабочего стола")
        dialog.geometry("800x600")
        dialog.transient(parent)
        dialog.configure(bg='#F5F7FA')
        
        x = (dialog.winfo_screenwidth() - 800) // 2
        y = (dialog.winfo_screenheight() - 600) // 2
        dialog.geometry(f'+{x}+{y}')
        
        # Заголовок
        header = tk.Frame(dialog, bg='#3498DB', height=60)
        header.pack(fill=tk.X)
        tk.Label(header, text="🖼 Выбор обоев рабочего стола", bg='#3498DB', fg='white',
                font=('Segoe UI', 14, 'bold')).pack(pady=15)
        
        # Панель выбора файла
        select_frame = tk.Frame(dialog, bg='#F5F7FA')
        select_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.wp_file_label = tk.Label(select_frame, text="Файл не выбран", bg='white', fg='#7F8C8D',
                                      font=('Segoe UI', 10), anchor='w', relief=tk.SUNKEN, bd=1)
        self.wp_file_label.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5, padx=(0, 5))
        
        tk.Button(select_frame, text="📂 Открыть проводник", bg='#3498DB', fg='white',
                 font=('Segoe UI', 10), bd=0, padx=15, pady=5, cursor='hand2',
                 command=lambda: self._open_bitos_explorer(dialog)).pack(side=tk.RIGHT)
        
        # Выбор стиля
        style_frame = tk.Frame(dialog, bg='#F5F7FA')
        style_frame.pack(fill=tk.X, padx=20, pady=5)
        
        tk.Label(style_frame, text="Стиль отображения:", bg='#F5F7FA', fg='#2C3E50',
                font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=5)
        
        self.wp_style_var = tk.StringVar(value=self.wallpaper_style)
        style_menu = ttk.Combobox(style_frame, textvariable=self.wp_style_var, width=12,
                                  values=['fill', 'fit', 'stretch', 'tile', 'center'],
                                  state='readonly')
        style_menu.pack(side=tk.LEFT, padx=5)
        
        # Область предпросмотра
        preview_frame = tk.Frame(dialog, bg='white', relief=tk.SUNKEN, bd=2)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.wp_preview_label = tk.Label(preview_frame, bg='#2C3E50', fg='white',
                                         text="Предпросмотр обоев\n\nНажмите 'Открыть проводник'\nдля выбора изображения",
                                         font=('Segoe UI', 12))
        self.wp_preview_label.pack(expand=True, fill=tk.BOTH)
        
        # Показываем текущие обои если есть
        if self.wallpaper_path and os.path.exists(self.wallpaper_path):
            self.wp_file_label.config(text=os.path.basename(self.wallpaper_path))
            self._show_preview_in_label(self.wallpaper_path)
        
        # Кнопки
        btn_frame = tk.Frame(dialog, bg='#F5F7FA')
        btn_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Button(btn_frame, text="🗑 Удалить обои", bg='#E74C3C', fg='white',
                 font=('Segoe UI', 10), bd=0, padx=15, pady=8, cursor='hand2',
                 command=lambda: self._clear_wp(dialog, callback)).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="✅ Применить", bg='#27AE60', fg='white',
                 font=('Segoe UI', 11, 'bold'), bd=0, padx=30, pady=8, cursor='hand2',
                 command=lambda: self._apply_wp(dialog, callback)).pack(side=tk.RIGHT, padx=5)
        
        tk.Button(btn_frame, text="Отмена", bg='#95A5A6', fg='white',
                 font=('Segoe UI', 11), bd=0, padx=30, pady=8,
                 command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
        self.wp_selected_file = self.wallpaper_path
    
    def _open_bitos_explorer(self, dialog):
        """Открывает встроенный проводник BITOS для выбора обоев"""
        start_path = self.bitos.user_paths.get("home", os.path.expanduser("~"))
        
        # Создаем проводник
        explorer = ModernFileExplorer(dialog, self.bitos, start_path)
        
        # Переопределяем метод открытия файла
        original_open = explorer.open_file
        def custom_open_file(path):
            if path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                self.wp_selected_file = path
                self.wp_file_label.config(text=os.path.basename(path))
                self._show_preview_in_label(path)
                # Закрываем проводник
                explorer.on_close()
            else:
                original_open(path)
        
        explorer.open_file = custom_open_file
        
        # Переопределяем метод для папок
        original_open_item = explorer.open_item
        def custom_open_item(path, is_dir):
            if is_dir:
                original_open_item(path, is_dir)
            else:
                custom_open_file(path)
        
        explorer.open_item = custom_open_item
        
        self.wp_file_label.config(text="Выберите изображение в проводнике...")
    
    def _show_preview_in_label(self, image_path):
        """Показывает превью в label"""
        if not PIL_AVAILABLE:
            self.wp_preview_label.config(text="Pillow не установлен\npip install Pillow",
                                         bg='#2C3E50', fg='#E74C3C')
            return
        
        try:
            img = Image.open(image_path)
            
            self.wp_preview_label.update_idletasks()
            max_w = self.wp_preview_label.winfo_width() or 600
            max_h = self.wp_preview_label.winfo_height() or 400
            
            if max_w < 50:
                max_w = 600
            if max_h < 50:
                max_h = 400
            
            style = self.wp_style_var.get()
            if style == 'fill':
                img = self._resize_fill(img, (max_w, max_h))
            elif style == 'fit':
                img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
            elif style == 'stretch':
                img = img.resize((max_w, max_h), Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(img)
            self.wp_preview_label.config(image=photo, text='', bg='white')
            self.wp_preview_label.image = photo
        except Exception as e:
            self.wp_preview_label.config(text=f"Ошибка: {e}", bg='#2C3E50', fg='#E74C3C')
    
    def _clear_wp(self, dialog, callback):
        """Очистка обоев"""
        if messagebox.askyesno("Удаление обоев", "Удалить обои рабочего стола?", parent=dialog):
            self.remove_wallpaper()
            self.wp_selected_file = None
            self.wp_file_label.config(text="Файл не выбран")
            self.wp_preview_label.config(image='', text="Обои удалены", bg='#2C3E50', fg='white')
            self.wp_preview_label.image = None
            if callback:
                callback()
    
    def _apply_wp(self, dialog, callback):
        """Применение обоев"""
        self.wallpaper_style = self.wp_style_var.get()
        self.save_config()
        
        if self.wp_selected_file and os.path.exists(self.wp_selected_file):
            success, result = self.set_wallpaper(self.wp_selected_file)
            if not success:
                messagebox.showerror("Ошибка", result, parent=dialog)
                return
        
        if callback:
            callback()
        
        dialog.destroy()
    
    def _resize_fill(self, img, target_size):
        """Масштабирование с заполнением"""
        img_ratio = img.width / img.height
        target_ratio = target_size[0] / target_size[1]
        
        if img_ratio > target_ratio:
            new_height = target_size[1]
            new_width = int(new_height * img_ratio)
        else:
            new_width = target_size[0]
            new_height = int(new_width / img_ratio)
        
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        left = (new_width - target_size[0]) // 2
        top = (new_height - target_size[1]) // 2
        right = left + target_size[0]
        bottom = top + target_size[1]
        
        return img.crop((left, top, right, bottom))
    
    def draw_on_canvas(self, canvas, width, height):
        """Рисует обои на канвасе"""
        if not self.wallpaper_path or not os.path.exists(self.wallpaper_path):
            return False
        
        if not PIL_AVAILABLE:
            return False
        
        try:
            img = Image.open(self.wallpaper_path)
            
            if self.wallpaper_style == 'fill':
                img = self._resize_fill(img, (width, height))
            elif self.wallpaper_style == 'fit':
                img.thumbnail((width, height), Image.Resampling.LANCZOS)
                new_img = Image.new('RGB', (width, height), (30, 30, 30))
                x = (width - img.width) // 2
                y = (height - img.height) // 2
                new_img.paste(img, (x, y))
                img = new_img
            elif self.wallpaper_style == 'stretch':
                img = img.resize((width, height), Image.Resampling.LANCZOS)
            elif self.wallpaper_style == 'tile':
                new_img = Image.new('RGB', (width, height))
                for x in range(0, width, img.width):
                    for y in range(0, height, img.height):
                        new_img.paste(img, (x, y))
                img = new_img
            elif self.wallpaper_style == 'center':
                new_img = Image.new('RGB', (width, height), (30, 30, 30))
                x = (width - img.width) // 2
                y = (height - img.height) // 2
                new_img.paste(img, (x, y))
                img = new_img
            
            photo = ImageTk.PhotoImage(img)
            canvas.create_image(0, 0, image=photo, anchor='nw', tags='wallpaper')
            canvas.wallpaper_image = photo
            canvas.tag_lower('wallpaper')
            return True
        except:
            return False

class NotificationCenter:
    """Центр уведомлений с историей и всплывающими сообщениями"""
    
    def __init__(self, parent, bitos):
        self.parent = parent
        self.bitos = bitos
        self.notifications = []
        self.max_notifications = 50
        self.active_popups = []
        self.popup_spacing = 110
        
        self.history_file = os.path.join(bitos.system_paths["config"], "notifications.json")
        self.load_history()
    
    def load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.notifications = json.load(f)
            except:
                self.notifications = []
    
    def save_history(self):
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.notifications[-self.max_notifications:], f, indent=4, ensure_ascii=False)
        except:
            pass
    
    def add_notification(self, title, message, icon="🔔", category="system", duration=5000):
        notification = {
            'id': len(self.notifications) + 1,
            'title': title,
            'message': message,
            'icon': icon,
            'category': category,
            'timestamp': datetime.now().isoformat(),
            'read': False
        }
        
        self.notifications.append(notification)
        self.save_history()
        self.show_popup(notification, duration)
    
    def show_popup(self, notification, duration=5000):
        popup = tk.Toplevel(self.parent)
        popup.overrideredirect(True)
        popup.attributes('-topmost', True)
        popup.configure(bg='#2C3E50')
        
        popup_width = 350
        popup_height = 100
        
        screen_width = popup.winfo_screenwidth()
        screen_height = popup.winfo_screenheight()
        
        y_offset = len(self.active_popups) * self.popup_spacing
        x = screen_width - popup_width - 20
        y = screen_height - popup_height - 20 - y_offset
        
        popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")
        
        frame = tk.Frame(popup, bg='#34495E', relief=tk.RAISED, bd=2)
        frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        header_frame = tk.Frame(frame, bg='#34495E')
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        tk.Label(header_frame, text=notification['icon'], font=('Segoe UI', 20),
                bg='#34495E', fg='white').pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Label(header_frame, text=notification['title'], font=('Segoe UI', 11, 'bold'),
                bg='#34495E', fg='#3498DB').pack(side=tk.LEFT)
        
        close_label = tk.Label(header_frame, text="✕", font=('Segoe UI', 12),
                              bg='#34495E', fg='#95A5A6', cursor='hand2')
        close_label.pack(side=tk.RIGHT)
        close_label.bind('<Button-1>', lambda e: self.close_popup(popup))
        
        msg_frame = tk.Frame(frame, bg='#34495E')
        msg_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        tk.Label(msg_frame, text=notification['message'][:100], font=('Segoe UI', 9),
                bg='#34495E', fg='#BDC3C7', wraplength=300, justify='left').pack(anchor='w')
        
        progress = ttk.Progressbar(frame, mode='determinate', length=popup_width-20)
        progress.pack(padx=10, pady=(0, 10))
        
        steps = 20
        step_time = duration // steps
        
        def update_progress(step=0):
            if step <= steps and popup.winfo_exists():
                progress['value'] = (step / steps) * 100
                popup.after(step_time, update_progress, step + 1)
        
        update_progress()
        
        self.active_popups.append(popup)
        popup.after(duration, lambda: self.close_popup(popup))
    
    def close_popup(self, popup):
        if popup in self.active_popups:
            self.active_popups.remove(popup)
        try:
            if popup.winfo_exists():
                popup.destroy()
        except:
            pass
        self.reposition_popups()
    
    def reposition_popups(self):
        for i, popup in enumerate(self.active_popups):
            try:
                if popup.winfo_exists():
                    screen_width = popup.winfo_screenwidth()
                    screen_height = popup.winfo_screenheight()
                    popup_width = popup.winfo_width()
                    popup_height = popup.winfo_height()
                    
                    x = screen_width - popup_width - 20
                    y = screen_height - popup_height - 20 - (i * self.popup_spacing)
                    popup.geometry(f"+{x}+{y}")
            except:
                pass

class ClockWidget:
    """Виджет часов"""
    
    def __init__(self, canvas, theme_colors, x, y):
        self.canvas = canvas
        self.theme_colors = theme_colors
        self.x = x
        self.y = y
        self.visible = True
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.frame = None
        
        self.create_widget()
        self.update_time()
    
    def create_widget(self):
        self.frame = tk.Frame(self.canvas, bg=self.theme_colors['widget_bg'],
                              relief=tk.RAISED, bd=2)
        self.frame.place(x=self.x, y=self.y, width=180, height=120)
        
        title_bar = tk.Frame(self.frame, bg=self.theme_colors['taskbar_bg'], height=25)
        title_bar.pack(fill=tk.X)
        
        self.title_label = tk.Label(title_bar, text="⏰ Часы", bg=self.theme_colors['taskbar_bg'],
                                     fg=self.theme_colors['widget_fg'], font=('Segoe UI', 9, 'bold'))
        self.title_label.pack(side=tk.LEFT, padx=5)
        
        close_btn = tk.Label(title_bar, text="✕", bg=self.theme_colors['taskbar_bg'],
                            fg=self.theme_colors['widget_fg'], cursor='hand2')
        close_btn.pack(side=tk.RIGHT, padx=5)
        close_btn.bind('<Button-1>', lambda e: self.destroy())
        
        title_bar.bind('<Button-1>', self.start_drag)
        title_bar.bind('<B1-Motion>', self.drag)
        title_bar.bind('<ButtonRelease-1>', self.stop_drag)
        
        self.time_label = tk.Label(self.frame, text="", bg=self.theme_colors['widget_bg'],
                                    fg=self.theme_colors['widget_fg'], font=('Segoe UI', 36, 'bold'))
        self.time_label.pack(expand=True)
        
        self.date_label = tk.Label(self.frame, text="", bg=self.theme_colors['widget_bg'],
                                    fg=self.theme_colors['widget_fg'], font=('Segoe UI', 10))
        self.date_label.pack()
    
    def update_time(self):
        if self.visible and self.frame and self.frame.winfo_exists():
            now = datetime.now()
            try:
                self.time_label.config(text=now.strftime("%H:%M:%S"))
                self.date_label.config(text=now.strftime("%d %B %Y"))
                self.frame.after(1000, self.update_time)
            except tk.TclError:
                pass
    
    def start_drag(self, event):
        self.drag_start_x = event.x
        self.drag_start_y = event.y
    
    def drag(self, event):
        try:
            if self.frame and self.frame.winfo_exists():
                x = self.frame.winfo_x() + event.x - self.drag_start_x
                y = self.frame.winfo_y() + event.y - self.drag_start_y
                self.frame.place(x=x, y=y)
                self.x = x
                self.y = y
        except tk.TclError:
            pass
    
    def stop_drag(self, event):
        pass
    
    def update_theme(self, theme_colors):
        self.theme_colors = theme_colors
        try:
            if self.frame and self.frame.winfo_exists():
                self.frame.config(bg=theme_colors['widget_bg'])
                self.title_label.config(bg=theme_colors['taskbar_bg'], fg=theme_colors['widget_fg'])
                self.time_label.config(bg=theme_colors['widget_bg'], fg=theme_colors['widget_fg'])
                self.date_label.config(bg=theme_colors['widget_bg'], fg=theme_colors['widget_fg'])
        except tk.TclError:
            pass
    
    def show(self):
        self.visible = True
        try:
            if self.frame and self.frame.winfo_exists():
                self.frame.place(x=self.x, y=self.y, width=180, height=120)
        except tk.TclError:
            pass
    
    def hide(self):
        self.visible = False
        try:
            if self.frame and self.frame.winfo_exists():
                self.frame.place_forget()
        except tk.TclError:
            pass
    
    def destroy(self):
        try:
            if self.frame and self.frame.winfo_exists():
                self.frame.destroy()
        except tk.TclError:
            pass
        
        try:
            if hasattr(self.canvas, 'master') and hasattr(self.canvas.master, 'widgets'):
                if self in self.canvas.master.widgets:
                    self.canvas.master.widgets.remove(self)
        except:
            pass
    
    def update_position(self):
        if self.visible:
            try:
                if self.frame and self.frame.winfo_exists():
                    self.frame.place(x=self.x, y=self.y)
            except tk.TclError:
                pass
    
    def get_config(self):
        return {'type': 'clock', 'x': self.x, 'y': self.y}
    
class CalendarWidget:
    """Виджет календаря"""
    
    def __init__(self, canvas, theme_colors, x, y):
        self.canvas = canvas
        self.theme_colors = theme_colors
        self.x = x
        self.y = y
        self.visible = True
        self.current_date = datetime.now()
        self.frame = None
        
        self.create_widget()
    
    def create_widget(self):
        self.frame = tk.Frame(self.canvas, bg=self.theme_colors['widget_bg'],
                              relief=tk.RAISED, bd=2)
        self.frame.place(x=self.x, y=self.y, width=200, height=220)
        
        title_bar = tk.Frame(self.frame, bg=self.theme_colors['taskbar_bg'], height=25)
        title_bar.pack(fill=tk.X)
        
        self.title_label = tk.Label(title_bar, text="📅 Календарь", bg=self.theme_colors['taskbar_bg'],
                                     fg=self.theme_colors['widget_fg'], font=('Segoe UI', 9, 'bold'))
        self.title_label.pack(side=tk.LEFT, padx=5)
        
        close_btn = tk.Label(title_bar, text="✕", bg=self.theme_colors['taskbar_bg'],
                            fg=self.theme_colors['widget_fg'], cursor='hand2')
        close_btn.pack(side=tk.RIGHT, padx=5)
        close_btn.bind('<Button-1>', lambda e: self.destroy())
        
        title_bar.bind('<Button-1>', self.start_drag)
        title_bar.bind('<B1-Motion>', self.drag)
        title_bar.bind('<ButtonRelease-1>', self.stop_drag)
        
        self.month_label = tk.Label(self.frame, text="", bg=self.theme_colors['widget_bg'],
                                     fg=self.theme_colors['widget_fg'],
                                     font=('Segoe UI', 11, 'bold'))
        self.month_label.pack(pady=5)
        
        days_frame = tk.Frame(self.frame, bg=self.theme_colors['widget_bg'])
        days_frame.pack(padx=5, pady=5)
        
        days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        for i, day in enumerate(days):
            tk.Label(days_frame, text=day, bg=self.theme_colors['widget_bg'],
                    fg=self.theme_colors['widget_fg'], font=('Segoe UI', 8),
                    width=3).grid(row=0, column=i)
        
        self.calendar_grid = tk.Frame(self.frame, bg=self.theme_colors['widget_bg'])
        self.calendar_grid.pack(padx=5, pady=5)
        
        self.update_calendar()
    
    def update_calendar(self):
        try:
            if not self.frame or not self.frame.winfo_exists():
                return
            
            for widget in self.calendar_grid.winfo_children():
                widget.destroy()
            
            self.month_label.config(text=self.current_date.strftime("%B %Y"))
            
            year = self.current_date.year
            month = self.current_date.month
            
            first_day = datetime(year, month, 1)
            first_weekday = first_day.weekday()
            
            if month == 12:
                next_month = datetime(year + 1, 1, 1)
            else:
                next_month = datetime(year, month + 1, 1)
            
            days_in_month = (next_month - first_day).days
            
            today = datetime.now().date()
            
            for i in range(first_weekday):
                tk.Label(self.calendar_grid, text="", bg=self.theme_colors['widget_bg'],
                        width=3).grid(row=(i // 7) + 1, column=i % 7)
            
            for day in range(1, days_in_month + 1):
                row = (first_weekday + day - 1) // 7 + 1
                col = (first_weekday + day - 1) % 7
                
                date = datetime(year, month, day).date()
                bg_color = self.theme_colors['widget_bg']
                fg_color = self.theme_colors['widget_fg']
                
                if date == today:
                    bg_color = '#3498DB'
                    fg_color = 'white'
                
                tk.Label(self.calendar_grid, text=str(day), bg=bg_color, fg=fg_color,
                        font=('Segoe UI', 8), width=3).grid(row=row, column=col, padx=1, pady=1)
        except tk.TclError:
            pass
    
    def start_drag(self, event):
        self.drag_start_x = event.x
        self.drag_start_y = event.y
    
    def drag(self, event):
        try:
            if self.frame and self.frame.winfo_exists():
                x = self.frame.winfo_x() + event.x - self.drag_start_x
                y = self.frame.winfo_y() + event.y - self.drag_start_y
                self.frame.place(x=x, y=y)
                self.x = x
                self.y = y
        except tk.TclError:
            pass
    
    def stop_drag(self, event):
        pass
    
    def update_theme(self, theme_colors):
        self.theme_colors = theme_colors
        try:
            if self.frame and self.frame.winfo_exists():
                self.frame.config(bg=theme_colors['widget_bg'])
                self.title_label.config(bg=theme_colors['taskbar_bg'], fg=theme_colors['widget_fg'])
                self.month_label.config(bg=theme_colors['widget_bg'], fg=theme_colors['widget_fg'])
                self.update_calendar()
        except tk.TclError:
            pass
    
    def show(self):
        self.visible = True
        try:
            if self.frame and self.frame.winfo_exists():
                self.frame.place(x=self.x, y=self.y, width=200, height=220)
        except tk.TclError:
            pass
    
    def hide(self):
        self.visible = False
        try:
            if self.frame and self.frame.winfo_exists():
                self.frame.place_forget()
        except tk.TclError:
            pass
    
    def destroy(self):
        try:
            if self.frame and self.frame.winfo_exists():
                self.frame.destroy()
        except tk.TclError:
            pass
        
        try:
            if hasattr(self.canvas, 'master') and hasattr(self.canvas.master, 'widgets'):
                if self in self.canvas.master.widgets:
                    self.canvas.master.widgets.remove(self)
        except:
            pass
    
    def update_position(self):
        if self.visible:
            try:
                if self.frame and self.frame.winfo_exists():
                    self.frame.place(x=self.x, y=self.y)
            except tk.TclError:
                pass
    
    def get_config(self):
        return {'type': 'calendar', 'x': self.x, 'y': self.y}
    
class StickerWidget:
    """Виджет стикера для заметок с сохранением текста"""
    
    def __init__(self, canvas, theme_colors, x, y, text=""):
        self.canvas = canvas
        self.theme_colors = theme_colors
        self.x = x
        self.y = y
        self.text = text
        self.visible = True
        self.frame = None
        self.drag_start_x = 0
        self.drag_start_y = 0
        
        self.create_widget()
    
    def create_widget(self):
        self.frame = tk.Frame(self.canvas, bg='#FFF9C4', relief=tk.RAISED, bd=2)
        self.frame.place(x=self.x, y=self.y, width=200, height=180)
        
        title_bar = tk.Frame(self.frame, bg='#F9A825', height=25)
        title_bar.pack(fill=tk.X)
        
        tk.Label(title_bar, text="📝 Заметка", bg='#F9A825', fg='white',
                font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT, padx=5)
        
        close_btn = tk.Label(title_bar, text="✕", bg='#F9A825', fg='white', cursor='hand2')
        close_btn.pack(side=tk.RIGHT, padx=5)
        close_btn.bind('<Button-1>', lambda e: self.destroy())
        
        title_bar.bind('<Button-1>', self.start_drag)
        title_bar.bind('<B1-Motion>', self.drag)
        title_bar.bind('<ButtonRelease-1>', self.stop_drag)
        
        # Текстовое поле с сохранением
        self.text_widget = tk.Text(self.frame, bg='#FFF9C4', fg='#333333',
                                    font=('Segoe UI', 10), wrap=tk.WORD,
                                    relief=tk.FLAT, bd=0)
        self.text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        if self.text:
            self.text_widget.insert('1.0', self.text)
        
        # Сохраняем текст при каждом изменении
        self.text_widget.bind('<KeyRelease>', self.save_text)
        self.text_widget.bind('<FocusOut>', self.save_text)
    
    def save_text(self, event=None):
        """Сохранение текста заметки"""
        try:
            if self.text_widget and self.text_widget.winfo_exists():
                self.text = self.text_widget.get('1.0', 'end-1c')
                # Сохраняем в конфигурацию виджетов
                if hasattr(self.canvas, 'master') and hasattr(self.canvas.master, 'save_widgets'):
                    self.canvas.master.save_widgets()
        except tk.TclError:
            pass
    
    def start_drag(self, event):
        self.drag_start_x = event.x
        self.drag_start_y = event.y
    
    def drag(self, event):
        try:
            if self.frame and self.frame.winfo_exists():
                x = self.frame.winfo_x() + event.x - self.drag_start_x
                y = self.frame.winfo_y() + event.y - self.drag_start_y
                self.frame.place(x=x, y=y)
                self.x = x
                self.y = y
        except tk.TclError:
            pass
    
    def stop_drag(self, event):
        # Сохраняем позицию после перетаскивания
        if hasattr(self.canvas, 'master') and hasattr(self.canvas.master, 'save_widgets'):
            self.canvas.master.save_widgets()
    
    def update_theme(self, theme_colors):
        self.theme_colors = theme_colors
    
    def show(self):
        self.visible = True
        try:
            if self.frame and self.frame.winfo_exists():
                self.frame.place(x=self.x, y=self.y, width=200, height=180)
        except tk.TclError:
            pass
    
    def hide(self):
        self.visible = False
        try:
            if self.frame and self.frame.winfo_exists():
                self.frame.place_forget()
        except tk.TclError:
            pass
    
    def destroy(self):
        # Сохраняем текст перед удалением
        try:
            self.save_text()
        except:
            pass
        
        try:
            if self.frame and self.frame.winfo_exists():
                self.frame.destroy()
        except tk.TclError:
            pass
        
        try:
            if hasattr(self.canvas, 'master') and hasattr(self.canvas.master, 'widgets'):
                if self in self.canvas.master.widgets:
                    self.canvas.master.widgets.remove(self)
                    self.canvas.master.save_widgets()
        except:
            pass
    
    def update_position(self):
        if self.visible:
            try:
                if self.frame and self.frame.winfo_exists():
                    self.frame.place(x=self.x, y=self.y)
            except tk.TclError:
                pass
    
    def get_config(self):
        # Сохраняем текст перед получением конфигурации
        try:
            self.save_text()
        except:
            pass
        return {'type': 'sticker', 'x': self.x, 'y': self.y, 'text': self.text}
    
# ==================== ЗАПУСК ====================
if __name__ == "__main__":
    if not PIL_AVAILABLE:
        print("⚠️ Рекомендуется установить Pillow для работы галереи:")
        print("   pip install Pillow")
        time.sleep(2)
    if platform.system() == "Windows" and not WIN32_AVAILABLE:
        print("⚠️ Для определения флешек рекомендуется установить pywin32:")
        print("   pip install pywin32")
        time.sleep(2)
    bitos = BITOS()
