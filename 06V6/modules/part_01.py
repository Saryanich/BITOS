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
import hmac
import re
import string
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
from bitos_update_manager import UpdateManager, safe_version_token

try:
    import ctypes
    from ctypes import wintypes
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    print("⚠️ Для блокировки клавиш установите: pip install keyboard")




def hash_pin(pin):
    """Создаёт PBKDF2-хеш PIN с уникальной криптографической солью."""
    import secrets
    salt = secrets.token_bytes(16)
    iterations = 310000
    digest = hashlib.pbkdf2_hmac("sha256", str(pin).encode("utf-8"), salt, iterations)
    return "pbkdf2_sha256$%s$%s$%s" % (iterations, salt.hex(), digest.hex())


def verify_pin_hash(pin, saved_hash):
    """Проверяет PBKDF2 и поддерживает старые SHA-256-хеши."""
    if not saved_hash:
        return False
    if saved_hash.startswith("pbkdf2_sha256$"):
        try:
            _, iterations, salt_hex, digest_hex = saved_hash.split("$", 3)
            iterations = int(iterations)
            if iterations < 100000 or iterations > 2000000:
                return False
            actual = hashlib.pbkdf2_hmac(
                "sha256", str(pin).encode("utf-8"), bytes.fromhex(salt_hex), iterations
            )
            return hmac.compare_digest(actual, bytes.fromhex(digest_hex))
        except (ValueError, TypeError):
            return False
    legacy_digest = hashlib.sha256(str(pin).encode("utf-8")).hexdigest()
    return hmac.compare_digest(legacy_digest, saved_hash)


def shutdown_windows():
    """Реальное выключение Windows"""
    if platform.system() == "Windows":
        try:
            subprocess.run(["shutdown", "/s", "/t", "1", "/f"])
        except:
            try:
                os.system("shutdown /s /t 1 /f")
            except:
                messagebox.showerror("Ошибка", "Не удалось выключить компьютер")

def restart_windows():
    """Реальная перезагрузка Windows"""
    if platform.system() == "Windows":
        try:
            subprocess.run(["shutdown", "/r", "/t", "1", "/f"])
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

# ==================== КЛАСС 1: SplashScreen (ИСПРАВЛЕННЫЙ) ====================
class SplashScreen:
    """Экран загрузки с современным дизайном и синхронизацией цветов"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.state('zoomed')
        
        self.width = self.root.winfo_screenwidth()
        self.height = self.root.winfo_screenheight()
        self.version = "06V6"
        
        # ТЕКУЩАЯ ТЕМА ДЛЯ СИНХРОНИЗАЦИИ
        self.current_theme = self._load_theme()
        self.theme_colors = self._get_theme_colors(self.current_theme)
        
        # Создаем canvas
        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height,
                                highlightthickness=0, bg=self.theme_colors['canvas_bg'])
        self.canvas.pack()
        
        # Рисуем градиентный фон с цветами темы
        self._draw_gradient_background()
        
        # Звезды
        self.stars = []
        for _ in range(200):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            size = random.randint(1, 3)
            brightness = random.randint(80, 255)
            self.stars.append([x, y, size, brightness])
        
        self.animate_stars()
        
        # Основной цвет для текста (из темы)
        main_color = self.theme_colors.get('fg', '#00D4FF')
        accent_color = self.theme_colors.get('fg', '#00D4FF')
        sub_color = self.theme_colors.get('widget_fg', '#A8D8EA')
        
        # Главный заголовок
        self.canvas.create_text(self.width//2, self.height//2 - 120,
                               text="BITOS",
                               font=('Segoe UI', 100, 'bold'),
                               fill=accent_color,
                               tags='text')
        
        # Тень заголовка
        self.canvas.create_text(self.width//2 + 3, self.height//2 - 117,
                               text="BITOS",
                               font=('Segoe UI', 100, 'bold'),
                               fill='#0a0a2a',
                               tags='text')
        
        # Подзаголовок
        self.canvas.create_text(self.width//2, self.height//2 - 30,
                               text="Операционная система будущего",
                               font=('Segoe UI', 20, 'italic'),
                               fill=sub_color,
                               tags='text')
        
        # Декоративная линия
        self.canvas.create_line(self.width//2 - 200, self.height//2 + 10,
                               self.width//2 + 200, self.height//2 + 10,
                               fill=accent_color, width=2, tags='text')
        
        # Версия
        self.canvas.create_text(self.width//2, self.height//2 + 35,
                               text=f"Версия {self.version}",
                               font=('Segoe UI', 12, 'bold'),
                               fill=accent_color,
                               tags='text')
        
        # Полоса загрузки
        self.bar_width = 500
        self.bar_height = 6
        self.bar_x = self.width//2 - self.bar_width//2
        self.bar_y = self.height//2 + 80
        
        # Фон полосы (цвет из темы с прозрачностью)
        self.canvas.create_rectangle(self.bar_x, self.bar_y, 
                                     self.bar_x + self.bar_width, 
                                     self.bar_y + self.bar_height,
                                     fill='#1a1a4e', outline='', tags='progress')
        
        # Полоса прогресса
        self.progress_rect = self.canvas.create_rectangle(self.bar_x, self.bar_y,
                                                         self.bar_x, 
                                                         self.bar_y + self.bar_height,
                                                         fill=accent_color, outline='', 
                                                         tags='progress')
        
        # Текст статуса
        self.status_text = self.canvas.create_text(
            self.width//2, self.height//2 + 115,
            text="Загрузка системы...",
            font=('Segoe UI', 13, 'bold'),
            fill=sub_color,
            tags='text'
        )
        
        # Детали загрузки
        self.details_text = self.canvas.create_text(
            self.width//2, self.height//2 + 145,
            text="",
            font=('Segoe UI', 10),
            fill=sub_color,
            tags='text'
        )
        
        # Процент
        self.percent_label = self.canvas.create_text(
            self.width//2 + 260, self.height//2 + 80,
            text="0%",
            font=('Segoe UI', 11, 'bold'),
            fill=accent_color,
            tags='text'
        )
        
        self.root.update()
    
    def _load_theme(self):
        """Загрузка сохранённой темы"""
        base_path = os.path.dirname(os.path.abspath(__file__))
        theme_file = os.path.join(base_path, "System", "Config", "theme.cfg")
        
        if os.path.exists(theme_file):
            try:
                with open(theme_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('theme', 'Базовая')
            except:
                pass
        return "Базовая"
    
    def _get_theme_colors(self, theme_name):
        """Получение цветов темы"""
        # Стандартные темы
        themes = {
            "Базовая": {
                'name': 'Базовая', 
                'bg': '#2980B9', 
                'fg': '#00D4FF', 
                'taskbar_bg': '#1A5276', 
                'taskbar_fg': 'white', 
                'canvas_bg': '#0a0a2a', 
                'icon_fg': 'white',
                'widget_bg': '#1F618D', 
                'widget_fg': '#A8D8EA',
                'wallpaper': 'System\\Config\\Wallpaper\\buinw1'
            },
            "Техно": {
                'name': 'Техно', 
                'bg': '#1B5E20', 
                'fg': '#00FF00', 
                'taskbar_bg': '#0D3B0D', 
                'taskbar_fg': '#00FF00', 
                'canvas_bg': '#0a0a1a', 
                'icon_fg': '#00FF00',
                'widget_bg': '#0D3B0D', 
                'widget_fg': '#00FF00',
                'wallpaper': 'System\\Config\\Wallpaper\\buinw2'
            },
            "Эко": {
                'name': 'Эко', 
                'bg': '#27AE60', 
                'fg': '#2ECC71', 
                'taskbar_bg': '#1E8449', 
                'taskbar_fg': '#FFFFFF', 
                'canvas_bg': '#0a2a1a', 
                'icon_fg': '#FFFFFF',
                'widget_bg': '#1E8449', 
                'widget_fg': '#FFFFFF',
                'wallpaper': 'System\\Config\\Wallpaper\\buinw3'
            },
            "Космо": {
                'name': 'Космо', 
                'bg': '#0B1B3D', 
                'fg': '#87CEEB', 
                'taskbar_bg': '#060D1A', 
                'taskbar_fg': '#87CEEB', 
                'canvas_bg': '#050a1a', 
                'icon_fg': '#87CEEB',
                'widget_bg': '#060D1A', 
                'widget_fg': '#87CEEB',
                'wallpaper': 'System\\Config\\Wallpaper\\buinw4'
            },
        }
        
        # Пытаемся загрузить пользовательские темы
        user_themes = {}
        base_path = os.path.dirname(os.path.abspath(__file__))
        themes_file = os.path.join(base_path, "System", "Config", "user_themes.json")
        
        if os.path.exists(themes_file):
            try:
                with open(themes_file, 'r', encoding='utf-8') as f:
                    user_themes = json.load(f)
            except:
                pass
        
        all_themes = {**themes, **user_themes}
        return all_themes.get(theme_name, themes["Базовая"])
    
    def _draw_gradient_background(self):
        """Рисует градиентный фон с цветами темы"""
        # Получаем цвета из темы
        canvas_bg = self.theme_colors.get('canvas_bg', '#0a0a2a')
        
        # Преобразуем в RGB
        try:
            r, g, b = self._hex_to_rgb(canvas_bg)
        except:
            r, g, b = 10, 10, 42
        
        for i in range(self.height):
            t = i / self.height
            # Создаём градиент от темного к светлому
            new_r = min(255, int(r + (255 - r) * t * 0.15))
            new_g = min(255, int(g + (255 - g) * t * 0.15))
            new_b = min(255, int(b + (255 - b) * t * 0.15))
            color = f'#{new_r:02x}{new_g:02x}{new_b:02x}'
            self.canvas.create_line(0, i, self.width, i, fill=color, tags='bg')
    
    def _hex_to_rgb(self, hex_color):
        """Преобразование HEX в RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def animate_stars(self):
        """Анимация звезд"""
        self.canvas.delete('star')
        for star in self.stars:
            star[3] += random.randint(-15, 15)
            star[3] = max(50, min(255, star[3]))
            
            star[1] += random.uniform(-0.1, 0.1)
            if star[1] > self.height:
                star[1] = 0
                star[0] = random.randint(0, self.width)
            if star[1] < 0:
                star[1] = self.height
            if star[0] > self.width:
                star[0] = 0
            if star[0] < 0:
                star[0] = self.width
                
            x, y, size, brightness = star
            brightness = min(255, max(0, brightness))
            color = f'#{brightness:02x}{brightness:02x}{brightness:02x}'
            self.canvas.create_oval(x-size, y-size, x+size, y+size,
                                   fill=color, outline='', tags='star')
        self.root.after(80, self.animate_stars)
    
    def update_progress(self, value, status="", details=""):
        """Обновление прогресса загрузки"""
        try:
            # Вычисляем ширину полосы
            progress_width = (value / 100) * self.bar_width
            
            # Обновляем полосу
            self.canvas.coords(self.progress_rect,
                              self.bar_x, self.bar_y,
                              self.bar_x + progress_width, 
                              self.bar_y + self.bar_height)
            
            # Обновляем процент
            self.canvas.itemconfig(self.percent_label, text=f"{int(value)}%")
            
            # Обновляем статус
            if status:
                self.canvas.itemconfig(self.status_text, text=status)
            if details:
                self.canvas.itemconfig(self.details_text, text=details)
            
            # Меняем цвет полосы для эффекта
            if value < 100:
                main_color = self.theme_colors.get('fg', '#00D4FF')
                self.canvas.itemconfig(self.progress_rect, fill=main_color)
            
            self.root.update()
        except Exception as e:
            pass
    
    def close(self):
        """Закрытие экрана загрузки"""
        for i in range(10, 0, -1):
            try:
                self.root.attributes('-alpha', i/10)
                self.root.update()
                time.sleep(0.02)
            except:
                pass
        self.root.destroy()


# ==================== КЛАСС 2: LoginScreen (ИСПРАВЛЕННЫЙ) ====================
class LoginScreen:
    """Экран входа в систему с синхронизацией цветов темы"""
    
    def __init__(self, on_login, bitos_instance=None):
        self.on_login = on_login
        self.bitos = bitos_instance
        self.root = tk.Tk()
        self.root.title("BITOS - Вход")
        self.root.overrideredirect(True)
        self.root.state('zoomed')
        self.width = self.root.winfo_screenwidth()
        self.height = self.root.winfo_screenheight()
        
        # ТЕКУЩАЯ ТЕМА ДЛЯ СИНХРОНИЗАЦИИ
        self.current_theme = self._load_theme()
        self.theme_colors = self._get_theme_colors(self.current_theme)
        
        # Защита от брутфорса
        self.failed_attempts = 0
        self.max_attempts = 5
        self.lock_time = 0
        self.lock_duration = 60
        
        # Фон
        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height,
                               highlightthickness=0, bg=self.theme_colors['canvas_bg'])
        self.canvas.place(x=0, y=0, width=self.width, height=self.height)
        
        # Градиентный фон с цветами темы
        self._draw_gradient_background()
        
        # Звезды
        self.stars = []
        for _ in range(150):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            size = random.randint(1, 3)
            speed = random.uniform(0.1, 0.5)
            brightness = random.randint(50, 255)
            self.stars.append([x, y, size, speed, brightness])
        
        self.animate_stars()
        
        # Панель входа
        self._create_login_panel()
        
        # Кнопки питания
        self._create_power_buttons()
    
    def _load_theme(self):
        """Загрузка сохранённой темы"""
        if self.bitos and hasattr(self.bitos, 'system_paths'):
            theme_file = os.path.join(self.bitos.system_paths["config"], "theme.cfg")
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            theme_file = os.path.join(base_path, "System", "Config", "theme.cfg")
        
        if os.path.exists(theme_file):
            try:
                with open(theme_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('theme', 'Базовая')
            except:
                pass
        return "Базовая"
    
    def _get_theme_colors(self, theme_name):
        """Получение цветов темы"""
        themes = {
            "Базовая": {
                'name': 'Базовая', 
                'bg': '#2980B9', 
                'fg': '#00D4FF', 
                'taskbar_bg': '#1A5276', 
                'taskbar_fg': 'white', 
                'canvas_bg': '#0a0a2a', 
                'icon_fg': 'white',
                'widget_bg': '#1F618D', 
                'widget_fg': '#A8D8EA',
                'panel_bg': '#0a0a2a',
                'panel_outline': '#2a2a5e',
                'input_bg': '#1a1a3e',
                'input_fg': '#A8D8EA',
                'button_bg': '#00D4FF',
                'button_fg': '#0a0a2a',
            },
            "Техно": {
                'name': 'Техно', 
                'bg': '#1B5E20', 
                'fg': '#00FF00', 
                'taskbar_bg': '#0D3B0D', 
                'taskbar_fg': '#00FF00', 
                'canvas_bg': '#0a0a1a', 
                'icon_fg': '#00FF00',
                'widget_bg': '#0D3B0D', 
                'widget_fg': '#00FF00',
                'panel_bg': '#0a0a1a',
                'panel_outline': '#1a5a1a',
                'input_bg': '#0D2B0D',
                'input_fg': '#00FF00',
                'button_bg': '#00FF00',
                'button_fg': '#0a0a1a',
            },
            "Эко": {
                'name': 'Эко', 
                'bg': '#27AE60', 
                'fg': '#2ECC71', 
                'taskbar_bg': '#1E8449', 
                'taskbar_fg': '#FFFFFF', 
                'canvas_bg': '#0a2a1a', 
                'icon_fg': '#FFFFFF',
                'widget_bg': '#1E8449', 
                'widget_fg': '#FFFFFF',
                'panel_bg': '#0a2a1a',
                'panel_outline': '#1a5a3a',
                'input_bg': '#0D3B1D',
                'input_fg': '#FFFFFF',
                'button_bg': '#2ECC71',
                'button_fg': '#0a2a1a',
            },
            "Космо": {
                'name': 'Космо', 
                'bg': '#0B1B3D', 
                'fg': '#87CEEB', 
                'taskbar_bg': '#060D1A', 
                'taskbar_fg': '#87CEEB', 
                'canvas_bg': '#050a1a', 
                'icon_fg': '#87CEEB',
                'widget_bg': '#060D1A', 
                'widget_fg': '#87CEEB',
                'panel_bg': '#050a1a',
                'panel_outline': '#1a2a5a',
                'input_bg': '#0a1a3a',
                'input_fg': '#87CEEB',
                'button_bg': '#87CEEB',
                'button_fg': '#050a1a',
            },
        }
        
        # Пытаемся загрузить пользовательские темы
        user_themes = {}
        if self.bitos and hasattr(self.bitos, 'system_paths'):
            themes_file = os.path.join(self.bitos.system_paths["config"], "user_themes.json")
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            themes_file = os.path.join(base_path, "System", "Config", "user_themes.json")
        
        if os.path.exists(themes_file):
            try:
                with open(themes_file, 'r', encoding='utf-8') as f:
                    user_themes = json.load(f)
            except:
                pass
        
        all_themes = {**themes, **user_themes}
        return all_themes.get(theme_name, themes["Базовая"])
    
    def _draw_gradient_background(self):
        """Рисует градиентный фон с цветами темы"""
        canvas_bg = self.theme_colors.get('canvas_bg', '#0a0a2a')
        
        try:
            r, g, b = self._hex_to_rgb(canvas_bg)
        except:
            r, g, b = 10, 10, 42
        
        for i in range(self.height):
            t = i / self.height
            new_r = min(255, int(r + (255 - r) * t * 0.15))
            new_g = min(255, int(g + (255 - g) * t * 0.15))
            new_b = min(255, int(b + (255 - b) * t * 0.15))
            color = f'#{new_r:02x}{new_g:02x}{new_b:02x}'
            self.canvas.create_line(0, i, self.width, i, fill=color, tags='bg')
    
    def _hex_to_rgb(self, hex_color):
        """Преобразование HEX в RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def animate_stars(self):
        """Анимация звезд"""
        self.canvas.delete('star')
        for star in self.stars:
            star[4] += random.randint(-10, 10)
            star[4] = max(50, min(255, star[4]))
            
            star[1] += star[3]
            if star[1] > self.height:
                star[1] = 0
                star[0] = random.randint(0, self.width)
            
            x, y, size, _, brightness = star
            brightness = min(255, max(0, brightness))
            color = f'#{brightness:02x}{brightness:02x}{brightness:02x}'
            self.canvas.create_oval(x-size, y-size, x+size, y+size,
                                   fill=color, outline='', tags='star')
        self.root.after(100, self.animate_stars)
    
    def _create_login_panel(self):
        """Создает панель входа с цветами темы"""
        panel_width, panel_height = 480, 480
        panel_x = (self.width - panel_width) // 2
        panel_y = (self.height - panel_height) // 2 - 30
        
        # Получаем цвета темы
        panel_bg = self.theme_colors.get('panel_bg', '#0a0a2a')
        panel_outline = self.theme_colors.get('panel_outline', '#2a2a5e')
        main_color = self.theme_colors.get('fg', '#00D4FF')
        sub_color = self.theme_colors.get('widget_fg', '#A8D8EA')
        input_bg = self.theme_colors.get('input_bg', '#1a1a3e')
        input_fg = self.theme_colors.get('input_fg', '#A8D8EA')
        button_bg = self.theme_colors.get('button_bg', '#00D4FF')
        button_fg = self.theme_colors.get('button_fg', '#0a0a2a')
        
        # Фон панели
        self.canvas.create_rectangle(panel_x, panel_y, 
                                     panel_x + panel_width, panel_y + panel_height,
                                     fill=panel_bg, outline=panel_outline, width=2,
                                     tags='panel')
        
        # Внутренний градиент панели
        for i in range(panel_height):
            alpha = int(20 * (panel_height - i) / panel_height)
            alpha = min(20, max(0, alpha))
            color = f'#{alpha:02x}{alpha:02x}{min(255, alpha+25):02x}'
            self.canvas.create_line(panel_x, panel_y + i, 
                                   panel_x + panel_width, panel_y + i,
                                   fill=color, tags='panel')
        
        # Внешняя подсветка
        self.canvas.create_rectangle(panel_x - 1, panel_y - 1, 
                                     panel_x + panel_width + 1, 
                                     panel_y + panel_height + 1,
                                     outline=main_color, width=1, tags='panel')
        
        # Заголовок
        self.canvas.create_text(panel_x + panel_width//2, panel_y + 60,
                               text="BITOS",
                               font=('Segoe UI', 52, 'bold'),
                               fill=main_color, tags='panel')
        
        # Подзаголовок
        self.canvas.create_text(panel_x + panel_width//2, panel_y + 110,
                               text="Вход в систему",
                               font=('Segoe UI', 14, 'bold'),
                               fill=sub_color, tags='panel')
        
        self.canvas.create_text(panel_x + panel_width//2, panel_y + 135,
                               text="Введите свои учетные данные",
                               font=('Segoe UI', 10),
                               fill=sub_color, tags='panel')
        
        # Разделитель
        self.canvas.create_line(panel_x + 50, panel_y + 160,
                               panel_x + panel_width - 50, panel_y + 160,
                               fill=panel_outline, width=1, tags='panel')
        
        # Поля ввода
        fields_y = panel_y + 185
        
        # Поле пользователя
        self._create_input_field(panel_x + 50, fields_y, 380, 42, "👤 Имя пользователя")
        
        # Используем Entry с цветами темы
        self.username_entry = tk.Entry(self.root, bg=input_bg, fg=input_fg,
                                       font=('Segoe UI', 12),
                                       bd=0, highlightthickness=2,
                                       highlightcolor=main_color,
                                       highlightbackground=panel_outline,
                                       insertbackground=main_color)
        self.username_entry.place(x=panel_x + 65, y=fields_y + 10, width=350, height=26)
        self.username_entry.insert(0, "User")
        self.username_entry.bind('<FocusIn>', lambda e: self._on_entry_focus(self.username_entry, 'User'))
        
        # Поле PIN
        pin_y = fields_y + 72
        self._create_input_field(panel_x + 50, pin_y, 380, 42, "🔒 PIN-код")
        
        self.pin_entry = tk.Entry(self.root, bg=input_bg, fg=input_fg,
                                 font=('Segoe UI', 12),
                                 bd=0, highlightthickness=2,
                                 highlightcolor=main_color,
                                 highlightbackground=panel_outline,
                                 show='●',
                                 insertbackground=main_color)
        self.pin_entry.place(x=panel_x + 65, y=pin_y + 10, width=350, height=26)
        self.pin_entry.bind('<Return>', lambda e: self.do_login())
        
        # Кнопка входа
        login_btn_x = panel_x + 50
        login_btn_y = pin_y + 90
        
        self.login_btn = tk.Button(self.root, text="➜ Войти в систему",
                                  bg=button_bg, fg=button_fg,
                                  font=('Segoe UI', 12, 'bold'),
                                  bd=0, cursor='hand2',
                                  activebackground=main_color,
                                  activeforeground=button_fg,
                                  command=self.do_login)
        self.login_btn.place(x=login_btn_x, y=login_btn_y, width=380, height=45)
        
        # Статус
        self.status_label = tk.Label(self.root, text='',
                                    bg=panel_bg, fg='#FF6B6B',
                                    font=('Segoe UI', 10, 'bold'))
        self.status_label.place(x=login_btn_x, y=login_btn_y + 53, width=380, height=22)
        
        # Кнопка смены PIN
        self.change_pin_btn = tk.Button(self.root, text="🔑 Изменить PIN-код",
                                       bg=panel_outline, fg=sub_color,
                                       font=('Segoe UI', 9),
                                       bd=0, cursor='hand2',
                                       activebackground=main_color,
                                       activeforeground='#FFFFFF',
                                       command=self.change_pin_dialog)
        self.change_pin_btn.place(x=login_btn_x, y=login_btn_y + 85, width=380, height=32)
    
    def _create_input_field(self, x, y, width, height, label):
        """Создает поле ввода с цветами темы"""
        panel_bg = self.theme_colors.get('panel_bg', '#0a0a2a')
        panel_outline = self.theme_colors.get('panel_outline', '#2a2a5e')
        sub_color = self.theme_colors.get('widget_fg', '#A8D8EA')
        
        self.canvas.create_rectangle(x, y, x + width, y + height,
                                    fill=panel_bg, outline=panel_outline, width=2,
                                    tags='panel')
        
        self.canvas.create_rectangle(x + 2, y + 2, x + width - 2, y + height - 2,
                                    fill=panel_bg, outline='', tags='panel')
        
        self.canvas.create_text(x + 12, y + height//2,
                               text=label,
                               font=('Segoe UI', 10),
                               fill=sub_color, anchor='w',
                               tags='panel')
    
    def _on_entry_focus(self, entry, default_text):
        if entry.get() == default_text:
            entry.delete(0, tk.END)
            entry.config(fg=self.theme_colors.get('input_fg', '#A8D8EA'))
    
    def _create_power_buttons(self):
        """Создает кнопки питания"""
        panel_bg = self.theme_colors.get('panel_bg', '#0a0a2a')
        
        btn_frame = tk.Frame(self.root, bg=panel_bg, bd=0)
        btn_frame.place(x=self.width - 250, y=self.height - 65, width=230, height=45)
        
        shutdown_btn = tk.Button(btn_frame, text='⏻ Выключить',
                                bg='#E74C3C', fg='white',
                                font=('Segoe UI', 10, 'bold'),
                                bd=0, cursor='hand2', padx=12, pady=6,
                                activebackground='#C0392B',
                                activeforeground='white',
                                command=self.shutdown_system)
        shutdown_btn.pack(side=tk.RIGHT, padx=4)
        
        restart_btn = tk.Button(btn_frame, text='🔄 Перезагрузить',
                               bg='#E67E22', fg='white',
                               font=('Segoe UI', 10, 'bold'),
                               bd=0, cursor='hand2', padx=12, pady=6,
                               activebackground='#D35400',
                               activeforeground='white',
                               command=self.restart_system)
        restart_btn.pack(side=tk.RIGHT, padx=4)
    
    def get_pin_hash(self, pin):
        return hash_pin(pin)

    def verify_pin(self, pin, saved_hash):
        """Проверяет PIN и мигрирует устаревший хеш после успешного входа."""
        if not verify_pin_hash(pin, saved_hash):
            return False
        if not saved_hash.startswith("pbkdf2_sha256$"):
            self.save_pin(pin)
        return True
    
    def load_pin(self):
        if self.bitos and hasattr(self.bitos, 'system_paths'):
            pin_file = os.path.join(self.bitos.system_paths["security"], "pin.hash")
        else:
            pin_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "System", "Security", "pin.hash")
        
        if os.path.exists(pin_file):
            try:
                with open(pin_file, 'r', encoding='utf-8') as f:
                    saved_hash = f.read().strip()
                # Известный стандартный PIN 1234 больше не принимается:
                # просим владельца задать свой PIN при следующем входе.
                legacy_default = hashlib.sha256(b"1234").hexdigest()
                if saved_hash == legacy_default:
                    try:
                        os.remove(pin_file)
                    except OSError:
                        pass
                    return None
                if saved_hash:
                    return saved_hash
            except (OSError, UnicodeError):
                return None
        return None
    
    def save_pin(self, new_pin):
        if self.bitos and hasattr(self.bitos, 'system_paths'):
            pin_file = os.path.join(self.bitos.system_paths["security"], "pin.hash")
        else:
            pin_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "System", "Security", "pin.hash")
        
        os.makedirs(os.path.dirname(pin_file), exist_ok=True)
        try:
            with open(pin_file, 'w') as f:
                f.write(self.get_pin_hash(new_pin))
            return True
        except:
            return False
    
    def setup_pin_dialog(self):
        """Первичная настройка собственного PIN вместо общего значения 1234."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Настройка PIN-кода BITOS")
        dialog.geometry("400x290")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        bg = self.theme_colors.get("panel_bg", "#0a0a2a")
        fg = self.theme_colors.get("fg", "#00D4FF")
        entry_bg = self.theme_colors.get("input_bg", "#1a1a3e")
        entry_fg = self.theme_colors.get("input_fg", "#A8D8EA")
        tk.Label(dialog, text="🔐 Создайте личный PIN-код", font=("Segoe UI", 15, "bold"),
                 bg=bg, fg=fg).pack(pady=(20, 10))
        tk.Label(dialog, text="Используйте 4–8 цифр. Общий PIN 1234 больше не используется.",
                 font=("Segoe UI", 9), bg=bg, fg=entry_fg, wraplength=350).pack(pady=5)
        first = tk.Entry(dialog, show="●", font=("Segoe UI", 12), bg=entry_bg, fg=entry_fg)
        first.pack(fill=tk.X, padx=35, pady=(12, 6), ipady=6)
        first.insert(0, "")
        first.focus_set()
        second = tk.Entry(dialog, show="●", font=("Segoe UI", 12), bg=entry_bg, fg=entry_fg)
        second.pack(fill=tk.X, padx=35, pady=6, ipady=6)
        status = tk.Label(dialog, text="", bg=bg, fg="#E74C3C", font=("Segoe UI", 9))
        status.pack(pady=5)

        def save_new_pin():
            pin = first.get().strip()
            confirmation = second.get().strip()
            if not pin.isdigit() or not 4 <= len(pin) <= 8:
                status.config(text="PIN должен состоять из 4–8 цифр")
                return
            if pin == "1234":
                status.config(text="Выберите PIN, отличный от 1234")
                return
            if pin != confirmation:
                status.config(text="PIN-коды не совпадают")
                return
            if not self.save_pin(pin):
                status.config(text="Не удалось сохранить PIN-код")
                return
            self.status_label.config(text="✅ PIN создан. Теперь войдите с новым PIN-кодом")
            self.pin_entry.delete(0, tk.END)
            dialog.destroy()

        tk.Button(dialog, text="Сохранить PIN", command=save_new_pin,
                  bg=fg, fg=bg, bd=0, padx=25, pady=8).pack(pady=8)

    def change_pin_dialog(self):
        """Диалог смены PIN-кода с цветами темы"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Изменить PIN-код")
        dialog.geometry("400x320")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=self.theme_colors.get('panel_bg', '#0a0a2a'))
        dialog.resizable(False, False)
        
        x = (dialog.winfo_screenwidth() - 400) // 2
        y = (dialog.winfo_screenheight() - 320) // 2
        dialog.geometry(f'+{x}+{y}')
        
        main_color = self.theme_colors.get('fg', '#00D4FF')
        sub_color = self.theme_colors.get('widget_fg', '#A8D8EA')
        panel_bg = self.theme_colors.get('panel_bg', '#0a0a2a')
        panel_outline = self.theme_colors.get('panel_outline', '#2a2a5e')
        input_bg = self.theme_colors.get('input_bg', '#1a1a3e')
        input_fg = self.theme_colors.get('input_fg', '#A8D8EA')
        
        tk.Label(dialog, text="🔑 Изменение PIN-кода",
                font=('Segoe UI', 16, 'bold'),
                bg=panel_bg, fg=main_color).pack(pady=15)
        
        fields = [
            ("Текущий PIN-код:", 'old'),
            ("Новый PIN-код (4-8 цифр):", 'new'),
            ("Подтвердите новый PIN-код:", 'confirm')
        ]
        
        entries = {}
        for label, key in fields:
            tk.Label(dialog, text=label, bg=panel_bg, fg=sub_color,
                    font=('Segoe UI', 10)).pack(pady=(8, 3))
            entry = tk.Entry(dialog, font=('Segoe UI', 12),
                            bg=input_bg, fg=input_fg,
                            bd=0, highlightthickness=2,
                            highlightcolor=main_color,
                            highlightbackground=panel_outline,
                            show='●', width=25)
            entry.pack(pady=(0, 5))
            entries[key] = entry
        
        status_label = tk.Label(dialog, text="", bg=panel_bg, fg='#E74C3C',
                               font=('Segoe UI', 10))
        status_label.pack(pady=5)
        
        def do_change():
            old_pin = entries['old'].get().strip()
            new_pin = entries['new'].get().strip()
            confirm_pin = entries['confirm'].get().strip()
            saved_hash = self.load_pin()
            
            if not self.verify_pin(old_pin, saved_hash):
                status_label.config(text="❌ Неверный текущий PIN-код", fg='#E74C3C')
                return
            if not new_pin.isdigit():
                status_label.config(text="❌ Только цифры", fg='#E74C3C')
                return
            if len(new_pin) < 4 or len(new_pin) > 8:
                status_label.config(text="❌ 4-8 цифр", fg='#E74C3C')
                return
            if new_pin != confirm_pin:
                status_label.config(text="❌ PIN-коды не совпадают", fg='#E74C3C')
                return
            if self.save_pin(new_pin):
                status_label.config(text="✅ PIN-код изменён!", fg='#27AE60')
                if self.bitos and hasattr(self.bitos, 'security'):
                    self.bitos.security.log_pin_change("User")
                dialog.after(1500, dialog.destroy)
            else:
                status_label.config(text="❌ Ошибка сохранения", fg='#E74C3C')
        
        btn_frame = tk.Frame(dialog, bg=panel_bg)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Изменить PIN",
                 bg=main_color, fg=panel_bg,
                 font=('Segoe UI', 11, 'bold'),
                 bd=0, padx=30, pady=8,
                 cursor='hand2', command=do_change).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Отмена",
                 bg=panel_outline, fg=sub_color,
                 font=('Segoe UI', 10), bd=0,
                 padx=30, pady=8, command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def shutdown_system(self):
        if messagebox.askyesno("Выключение", "Вы действительно хотите выключить компьютер?"):
            if self.bitos and hasattr(self.bitos, 'security'):
                self.bitos.security.log_access("System", "SHUTDOWN", "SUCCESS")
            self.root.destroy()
            shutdown_windows()
    
    def restart_system(self):
        if messagebox.askyesno("Перезагрузка", "Вы действительно хотите перезагрузить компьютер?"):
            if self.bitos and hasattr(self.bitos, 'security'):
                self.bitos.security.log_access("System", "RESTART", "SUCCESS")
            self.root.destroy()
            restart_windows()
    
    def do_login(self):
        if self.lock_time > time.time():
            remaining = int(self.lock_time - time.time())
            self.status_label.config(text=f'⏰ Блокировка на {remaining} сек')
            return
        
        username = self.username_entry.get().strip()
        pin = self.pin_entry.get().strip()
        
        if not username:
            self.status_label.config(text='❌ Введите имя пользователя')
            return
        
        saved_hash = self.load_pin()
        if not saved_hash:
            self.setup_pin_dialog()
            return
        if not self.verify_pin(pin, saved_hash):
            self.failed_attempts += 1
            remaining = self.max_attempts - self.failed_attempts
            
            if self.bitos and hasattr(self.bitos, 'security'):
                self.bitos.security.log_login_attempt(username, False)
            
            if self.failed_attempts >= self.max_attempts:
                self.lock_time = time.time() + self.lock_duration
                self.status_label.config(text=f'❌ Блокировка на {self.lock_duration} сек')
                if self.bitos and hasattr(self.bitos, 'security'):
                    self.bitos.security.log_security_event("BRUTE_FORCE_ATTEMPT", f"User: {username}")
                self.pin_entry.delete(0, tk.END)
                self.failed_attempts = 0
            else:
                self.status_label.config(text=f'❌ Неверный PIN! Осталось: {remaining}')
                self.pin_entry.delete(0, tk.END)
            return
        
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

