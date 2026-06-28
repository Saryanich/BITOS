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
        return hashlib.sha256(pin.encode()).hexdigest()
    
    def load_pin(self):
        if self.bitos and hasattr(self.bitos, 'system_paths'):
            pin_file = os.path.join(self.bitos.system_paths["security"], "pin.hash")
        else:
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
            
            if self.get_pin_hash(old_pin) != saved_hash:
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
        if self.get_pin_hash(pin) != saved_hash:
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

class ModernFileExplorer:
    """Современный файловый проводник с поиском и уведомлениями о флешках"""
    
    # ЗАПРЕЩЁННЫЕ ПУТИ - НОВАЯ СИСТЕМА
    # 1. ВСЕ ПУТИ НА ДИСКЕ C:\ КРОМЕ C:\Users
    # 2. СИСТЕМНАЯ ПАПКА BITOS (...\System)
    
    def __init__(self, parent, bitos, start_path=None):
        self.parent = parent
        self.bitos = bitos
        
        # Сохраняем базовый путь BITOS
        self.base_path = os.path.abspath(bitos.base_path)
        self.system_folder_path = os.path.join(self.base_path, "System")
        
        # Определяем разрешённые корневые пути
        self.allowed_root_paths = self._get_allowed_root_paths()
        
        # Определяем, какой путь показывать
        if start_path and self._is_path_allowed(start_path):
            self.current_path = start_path
        else:
            # Начинаем с домашней папки пользователя
            self.current_path = bitos.user_paths["home"]
        
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
    
    def _get_allowed_root_paths(self):
        """Получение списка разрешённых корневых путей"""
        allowed = []
        
        if platform.system() == "Windows":
            # На Windows: только C:\Users разрешён
            users_path = "C:\\Users"
            if os.path.exists(users_path):
                allowed.append(users_path)
            
            # Также добавляем съёмные диски (флешки)
            try:
                import win32api
                import win32file
                drives = win32api.GetLogicalDriveStrings().split('\000')[:-1]
                for drive in drives:
                    try:
                        if win32file.GetDriveType(drive) == win32file.DRIVE_REMOVABLE:
                            allowed.append(drive)
                    except:
                        pass
            except:
                pass
        else:
            # На Linux: домашняя папка и /media, /mnt
            allowed.append(os.path.expanduser("~"))
            for path in ["/media", "/mnt", "/run/media"]:
                if os.path.exists(path):
                    allowed.append(path)
        
        # Добавляем домашнюю папку BITOS
        if hasattr(self.bitos, 'user_paths'):
            allowed.append(self.bitos.user_paths["home"])
        
        return allowed
    
    def _is_path_allowed(self, path):
        """Проверка доступа к пути"""
        if not path:
            return False
        
        abs_path = os.path.abspath(path)
        
        # 1. БЛОКИРУЕМ ВСЕ ПУТИ НА C:\ КРОМЕ C:\Users
        if platform.system() == "Windows":
            # Проверяем, находится ли путь на диске C:
            if abs_path[0:2].upper() == "C:" or abs_path.startswith("C:\\"):
                # Разрешаем только C:\Users и его подпапки
                if not abs_path.startswith("C:\\Users"):
                    return False
                
                # Блокируем системные папки Windows внутри Users (на всякий случай)
                blocked_system = ["System32", "System", "Windows", "Program Files", "Program Files (x86)"]
                for blocked in blocked_system:
                    if f"C:\\Users\\{blocked}" in abs_path or f"C:\\Users\\{blocked}\\".replace("/", "\\") in abs_path:
                        return False
        
        # 2. БЛОКИРУЕМ СИСТЕМНУЮ ПАПКУ BITOS
        if abs_path == self.system_folder_path:
            return False
        
        if abs_path.startswith(self.system_folder_path + os.sep):
            return False
        
        # Блокируем любую папку с именем "System" в корне BITOS
        if os.path.basename(abs_path) == "System" and os.path.dirname(abs_path) == self.base_path:
            return False
        
        # 3. БЛОКИРУЕМ СИСТЕМНЫЕ ПАПКИ WINDOWS (для безопасности)
        blocked_system_folders = ["System32", "Windows", "Program Files", "Program Files (x86)"]
        for blocked in blocked_system_folders:
            if abs_path.startswith(f"C:\\{blocked}") or abs_path.startswith(f"C:\\{blocked}\\".replace("/", "\\")):
                return False
        
        # 4. ПРОВЕРЯЕМ, ЧТО ПУТЬ В РАЗРЕШЁННЫХ КОРНЯХ
        # Исключение: если путь уже разрешён (пользовательский или флешка)
        for root in self.allowed_root_paths:
            if abs_path == root or abs_path.startswith(root + os.sep):
                return True
        
        # Если путь не в разрешённых корнях - блокируем
        return False
    
    def _get_notification_center(self):
        """Получение центра уведомлений"""
        if self.notification_center:
            return self.notification_center
        
        if hasattr(self.bitos, 'desktop_instance'):
            if hasattr(self.bitos.desktop_instance, 'notification_center'):
                self.notification_center = self.bitos.desktop_instance.notification_center
                return self.notification_center
        
        if hasattr(self.parent, 'notification_center'):
            self.notification_center = self.parent.notification_center
            return self.notification_center
        
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
        
        if not self._is_path_allowed(self.current_path):
            self.search_results = []
            self.window.after(0, self._display_search_results)
            return
        
        try:
            if self.search_in_subfolders.get():
                for root, dirs, files in os.walk(self.current_path):
                    # Проверяем доступ к каждому пути
                    if not self._is_path_allowed(root):
                        continue
                    
                    for file in files:
                        file_path = os.path.join(root, file)
                        if self._match_file(file, query_lower, file_path):
                            try:
                                results.append({
                                    'name': file,
                                    'path': file_path,
                                    'is_dir': False,
                                    'size': os.path.getsize(file_path)
                                })
                            except:
                                pass
                    
                    for dir in dirs:
                        if query_lower in dir.lower():
                            dir_path = os.path.join(root, dir)
                            if self._is_path_allowed(dir_path):
                                results.append({
                                    'name': dir,
                                    'path': dir_path,
                                    'is_dir': True,
                                    'size': 0
                                })
            else:
                for item in os.listdir(self.current_path):
                    item_path = os.path.join(self.current_path, item)
                    if not self._is_path_allowed(item_path):
                        continue
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
                import win32api
                import win32file
                drives = win32api.GetLogicalDriveStrings().split('\000')[:-1]
                for drive in drives:
                    try:
                        if win32file.GetDriveType(drive) == win32file.DRIVE_REMOVABLE:
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
        
        new_drives = current_drives - self.known_drives
        removed_drives = self.known_drives - current_drives
        
        for drive in new_drives:
            drive_name = drive
            try:
                if platform.system() == "Windows" and WIN32_AVAILABLE:
                    try:
                        import win32file
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
        
        for drive in removed_drives:
            drive_name = drive
            try:
                if platform.system() == "Windows" and WIN32_AVAILABLE:
                    try:
                        import win32file
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
                import win32file
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
    
    def navigate_to(self, path):
        if not os.path.exists(path):
            messagebox.showerror("Ошибка", "Путь не существует")
            return
        if not self._is_path_allowed(path):
            messagebox.showerror("Доступ запрещён", 
                "Доступ к этому пути запрещён.\n\n"
                "Разрешены только:\n"
                "• C:\\Users и его подпапки\n"
                "• Папка пользователя BITOS\n"
                "• Подключённые флешки")
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
            all_items = os.listdir(self.current_path)
            
            # Фильтруем запрещённые элементы
            filtered_items = []
            for item in all_items:
                item_path = os.path.join(self.current_path, item)
                if self._is_path_allowed(item_path):
                    filtered_items.append(item)
            
            folders = []
            files = []
            for item in filtered_items:
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
                if name == "System" and self.current_path == self.base_path:
                    messagebox.showerror("Ошибка", "Невозможно создать папку с именем 'System'")
                    dialog.destroy()
                    return
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
                if new_name == "System" and self.current_path == self.base_path:
                    messagebox.showerror("Ошибка", "Невозможно переименовать в 'System'")
                    dialog.destroy()
                    return
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
        if parent and parent != self.current_path and self._is_path_allowed(parent):
            self.navigate_to(parent)
        else:
            messagebox.showinfo("Информация", "Нет доступа к родительской папке")
    
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
        
        # Оптимальные размеры для отображения
        self.icon_size = 36
        self.text_font_size = 9
        self.max_text_width = 80
        
        self.update_position()
        self.create()
    
    def generate_id(self):
        return f"{self.text}_{int(time.time()*1000)}_{random.randint(1000,9999)}"
    
    def update_position(self):
        self.x = self.START_X + self.grid_x * self.GRID_SIZE
        self.y = self.START_Y + self.grid_y * self.GRID_SIZE
    
    def _truncate_text(self, text, max_width=80):
        """Обрезает текст, если он не помещается в заданную ширину"""
        max_chars = 12
        if len(text) > max_chars:
            return text[:max_chars - 3] + "..."
        return text
    
    def create(self):
        # Хитбокс - область клика
        hitbox_width = 88
        hitbox_height = 90
        x1 = self.x - hitbox_width // 2
        y1 = self.y - 30
        x2 = self.x + hitbox_width // 2
        y2 = self.y + 40
        
        # Прозрачный хитбокс для кликов
        self.hitbox_id = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill='', outline='',
            tags=('icon', f'hitbox_{self.icon_id}')
        )
        
        # Иконка (эмодзи)
        self.icon_id_obj = self.canvas.create_text(
            self.x, self.y - 12,
            text=self.icon,
            font=('Segoe UI', self.icon_size),
            fill='white',
            tags=('icon', f'icon_{self.icon_id}')
        )
        
        # Текст названия с обрезкой
        display_text = self._truncate_text(self.text, self.max_text_width)
        self.text_id = self.canvas.create_text(
            self.x, self.y + 28,
            text=display_text,
            font=('Segoe UI', self.text_font_size),
            fill='white',
            width=self.max_text_width,
            justify='center',
            tags=('icon', f'text_{self.icon_id}')
        )
        
        # Привязка событий к хитбоксу
        self.canvas.tag_bind(f'hitbox_{self.icon_id}', '<Button-1>', self.on_click)
        self.canvas.tag_bind(f'hitbox_{self.icon_id}', '<Double-1>', self.on_double_click)
        self.canvas.tag_bind(f'hitbox_{self.icon_id}', '<Button-3>', self.on_right_click)
        self.canvas.tag_bind(f'hitbox_{self.icon_id}', '<Enter>', self.on_enter)
        self.canvas.tag_bind(f'hitbox_{self.icon_id}', '<Leave>', self.on_leave)
        
        # Привязка событий к иконке
        self.canvas.tag_bind(f'icon_{self.icon_id}', '<Button-1>', self.on_click)
        self.canvas.tag_bind(f'icon_{self.icon_id}', '<Double-1>', self.on_double_click)
        self.canvas.tag_bind(f'icon_{self.icon_id}', '<Button-3>', self.on_right_click)
        self.canvas.tag_bind(f'icon_{self.icon_id}', '<Enter>', self.on_enter)
        self.canvas.tag_bind(f'icon_{self.icon_id}', '<Leave>', self.on_leave)
        
        # Привязка событий к тексту
        self.canvas.tag_bind(f'text_{self.icon_id}', '<Button-1>', self.on_click)
        self.canvas.tag_bind(f'text_{self.icon_id}', '<Double-1>', self.on_double_click)
        self.canvas.tag_bind(f'text_{self.icon_id}', '<Button-3>', self.on_right_click)
        self.canvas.tag_bind(f'text_{self.icon_id}', '<Enter>', self.on_enter)
        self.canvas.tag_bind(f'text_{self.icon_id}', '<Leave>', self.on_leave)
    
    def on_enter(self, event):
        self.hover = True
        try:
            self.canvas.itemconfig(self.icon_id_obj, fill='#3498DB')
            self.canvas.itemconfig(self.text_id, fill='#3498DB')
        except tk.TclError:
            pass
    
    def on_leave(self, event):
        self.hover = False
        if not self.selected:
            try:
                self.canvas.itemconfig(self.icon_id_obj, fill='white')
                self.canvas.itemconfig(self.text_id, fill='white')
            except tk.TclError:
                pass
    
    def on_click(self, event):
        # Снимаем выделение со всех иконок
        if hasattr(self.canvas, 'desktop_icons'):
            for icon in self.canvas.desktop_icons:
                if icon is not self:
                    icon.selected = False
                    if not icon.hover:
                        try:
                            icon.canvas.itemconfig(icon.icon_id_obj, fill='white')
                            icon.canvas.itemconfig(icon.text_id, fill='white')
                        except tk.TclError:
                            pass
        
        self.selected = True
        try:
            self.canvas.itemconfig(self.icon_id_obj, fill='#3498DB')
            self.canvas.itemconfig(self.text_id, fill='#3498DB')
        except tk.TclError:
            pass
    
    def on_double_click(self, event):
        if self.command:
            try:
                self.command()
            except Exception:
                pass
    
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
            try:
                self.canvas.delete(f'hitbox_{self.icon_id}')
                self.canvas.delete(f'icon_{self.icon_id}')
                self.canvas.delete(f'text_{self.icon_id}')
            except tk.TclError:
                pass
            
            if hasattr(self.canvas, 'desktop_icons') and self in self.canvas.desktop_icons:
                self.canvas.desktop_icons.remove(self)
            
            if hasattr(self.canvas, 'rearrange_icons'):
                self.canvas.rearrange_icons()
            if hasattr(self.canvas, 'save_shortcuts'):
                self.canvas.save_shortcuts()
    
    def show_properties(self):
        info = [
            f"Название: {self.text}",
            f"Иконка: {self.icon}",
            f"Позиция в сетке: ({self.grid_x}, {self.grid_y})"
        ]
        messagebox.showinfo("Свойства ярлыка", "\n".join(info))
    
    def move_to_grid(self, new_grid_x, new_grid_y):
        self.grid_x = new_grid_x
        self.grid_y = new_grid_y
        self.update_position()
        
        # Обновляем позицию хитбокса
        hitbox_width = 88
        hitbox_height = 90
        x1 = self.x - hitbox_width // 2
        y1 = self.y - 30
        x2 = self.x + hitbox_width // 2
        y2 = self.y + 40
        
        try:
            self.canvas.coords(self.hitbox_id, x1, y1, x2, y2)
            self.canvas.coords(self.icon_id_obj, self.x, self.y - 12)
            self.canvas.coords(self.text_id, self.x, self.y + 28)
        except tk.TclError:
            pass
    
    def update_theme(self, fg_color):
        if not self.selected and not self.hover:
            try:
                self.canvas.itemconfig(self.icon_id_obj, fill=fg_color)
                self.canvas.itemconfig(self.text_id, fill=fg_color)
            except tk.TclError:
                pass
    
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
                'open_app_store': 'app_store',
            }
            for key, value in command_map.items():
                if key in str(self.command) or value in str(self.command):
                    command_name = value
                    break
        
        if not command_name and 'bip:' in str(self.command):
            cmd_str = str(self.command)
            if ')' in cmd_str:
                command_name = cmd_str.split('bip:')[1].split(')')[0]
            else:
                command_name = cmd_str.split('bip:')[1]
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
    """Панель задач с микшером звука, батареей, языком, центром уведомлений и отслеживанием окон"""
    
    def __init__(self, parent, username, commands, theme_colors, 
                 desktop_canvas=None, desktop_icons_list=None, desktop=None):
        self.parent = parent
        self.username = username
        self.commands = commands
        self.theme_colors = theme_colors
        self.desktop_canvas = desktop_canvas
        self.desktop_icons_list = desktop_icons_list
        self.desktop = desktop
        
        # Список открытых окон
        self.open_windows = []
        self.window_buttons = {}
        self.window_counter = 0
        
        # Старые атрибуты
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
        
        # Контейнер для кнопок открытых окон
        self.windows_container = tk.Frame(self.taskbar, bg=theme_colors['taskbar_bg'])
        self.windows_container.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
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
        
        # Счетчик уведомлений
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
        
        # Система отслеживания окон
        self._setup_window_tracking()

    # ==================== МЕТОДЫ ДЛЯ ОТСЛЕЖИВАНИЯ ОКОН ====================
    
    def _setup_window_tracking(self):
        """Настройка отслеживания открытых окон"""
        # Сохраняем оригинальные конструкторы
        self._original_tk_toplevel = tk.Toplevel
        self._original_tk_tk = tk.Tk
        
        # Переопределяем для перехвата
        def patched_toplevel(master=None, **kwargs):
            window = self._original_tk_toplevel(master, **kwargs)
            self._track_window(window)
            return window
        
        def patched_tk(**kwargs):
            window = self._original_tk_tk(**kwargs)
            self._track_window(window)
            return window
        
        try:
            tk.Toplevel = patched_toplevel
            tk.Tk = patched_tk
        except:
            pass

    def _track_window(self, window):
        """Отслеживание окна"""
        try:
            try:
                title = window.title() or "Окно"
            except:
                title = "Окно"
            
            window_id = f"win_{self.window_counter}"
            self.window_counter += 1
            
            window_info = {
                'id': window_id,
                'window': window,
                'title': title,
                'icon': self._get_window_icon(title),
                'is_active': False
            }
            
            self.open_windows.append(window_info)
            self._create_window_button(window_info)
            
            original_destroy = window.destroy
            
            def patched_destroy():
                self._remove_window(window_id)
                try:
                    original_destroy()
                except:
                    pass
            
            window.destroy = patched_destroy
            
            def on_focus_in(event):
                self._set_active_window(window_id)
            
            try:
                window.bind('<FocusIn>', on_focus_in)
            except:
                pass
            
            self._update_windows_container()
            
        except Exception as e:
            pass

    def _get_window_icon(self, title):
        """Получить иконку для окна по заголовку"""
        title_lower = title.lower()
        
        icon_map = {
            'проводник': '📁',
            'explorer': '📁',
            'настройки': '⚙',
            'settings': '⚙',
            'корзина': '🗑',
            'trash': '🗑',
            'терминал': '📡',
            'terminal': '📡',
            'установщик': '📦',
            'bip': '📦',
            'галерея': '🖼',
            'gallery': '🖼',
            'paint': '🎨',
            'заметки': '📝',
            'notes': '📝',
            'калькулятор': '🧮',
            'calc': '🧮',
            'магазин': '🛒',
            'app store': '🛒',
            'браузер': '🌐',
            'browser': '🌐',
            'windows': '🪟',
            'chrome': '🌐',
            'firefox': '🦊',
            'notepad': '📄',
            'блокнот': '📄',
        }
        
        for key, icon in icon_map.items():
            if key in title_lower:
                return icon
        
        return '📄'

    def _create_window_button(self, window_info):
        """Создание кнопки окна в панели задач"""
        window_id = window_info['id']
        
        # Ограничиваем длину текста
        title = window_info['title'][:25]
        if len(window_info['title']) > 25:
            title += "..."
        
        button = tk.Button(
            self.windows_container,
            text=f"{window_info['icon']} {title}",
            bg=self.theme_colors['taskbar_bg'],
            fg=self.theme_colors['taskbar_fg'],
            font=('Segoe UI', 9),
            bd=0,
            padx=8,
            pady=3,
            cursor='hand2',
            relief=tk.FLAT,
            anchor='w'
        )
        
        self.window_buttons[window_id] = button
        
        button.bind('<Button-1>', lambda e, wid=window_id: self._activate_window(wid))
        button.bind('<Button-3>', lambda e, wid=window_id: self._show_window_context_menu(e, wid))
        button.bind('<Enter>', lambda e, btn=button: btn.config(bg='#34495E'))
        button.bind('<Leave>', lambda e, btn=button: btn.config(
            bg=self.theme_colors['taskbar_bg'] if not window_info.get('is_active', False) else '#3498DB'
        ))
        
        self.create_tooltip(button, f"{window_info['title']}\nНажмите для активации")
        
        button.pack(side=tk.LEFT, padx=2, pady=2)
        
        if window_info.get('is_active', False):
            button.config(bg='#3498DB', fg='white')

    def _remove_window(self, window_id):
        """Удаление окна из панели задач"""
        if window_id in self.window_buttons:
            try:
                self.window_buttons[window_id].destroy()
            except:
                pass
            del self.window_buttons[window_id]
        
        self.open_windows = [w for w in self.open_windows if w['id'] != window_id]
        self._update_windows_container()

    def _update_window_title(self, window_id, new_title):
        """Обновление заголовка окна"""
        for window_info in self.open_windows:
            if window_info['id'] == window_id:
                window_info['title'] = new_title
                window_info['icon'] = self._get_window_icon(new_title)
                break
        
        self._update_windows_container()

    def _set_active_window(self, window_id):
        """Установка активного окна"""
        for window_info in self.open_windows:
            window_info['is_active'] = (window_info['id'] == window_id)
        
        self._update_windows_container()

    def _activate_window(self, window_id):
        """Активация окна при клике на кнопку"""
        for window_info in self.open_windows:
            if window_info['id'] == window_id:
                try:
                    window = window_info['window']
                    if window.winfo_exists():
                        window.deiconify()
                        window.lift()
                        window.focus_force()
                        self._set_active_window(window_id)
                except:
                    pass
                break

    def _show_window_context_menu(self, event, window_id):
        """Контекстное меню для кнопки окна"""
        menu = tk.Menu(self.parent, tearoff=0, bg='#2C3E50', fg='white', 
                       activebackground='#3498DB')
        
        menu.add_command(label="🔄 Активировать", 
                        command=lambda: self._activate_window(window_id))
        menu.add_separator()
        menu.add_command(label="❌ Закрыть окно", 
                        command=lambda: self._close_window(window_id))
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _close_window(self, window_id):
        """Закрытие окна"""
        for window_info in self.open_windows:
            if window_info['id'] == window_id:
                try:
                    window = window_info['window']
                    if window.winfo_exists():
                        window.destroy()
                except:
                    pass
                self._remove_window(window_id)
                break

    def _update_windows_container(self):
        """Обновление контейнера с кнопками окон"""
        for window_id, button in self.window_buttons.items():
            try:
                window_info = None
                for w in self.open_windows:
                    if w['id'] == window_id:
                        window_info = w
                        break
                
                if window_info:
                    title = window_info['title'][:25]
                    if len(window_info['title']) > 25:
                        title += "..."
                    
                    try:
                        button.config(text=f"{window_info['icon']} {title}")
                    except:
                        pass
                    
                    if window_info.get('is_active', False):
                        try:
                            button.config(bg='#3498DB', fg='white')
                        except:
                            pass
                    else:
                        try:
                            button.config(bg=self.theme_colors['taskbar_bg'], fg=self.theme_colors['taskbar_fg'])
                        except:
                            pass
            except:
                pass
        
        # Проверяем, все ли окна существуют
        windows_to_remove = []
        for window_info in self.open_windows:
            try:
                if not window_info['window'].winfo_exists():
                    windows_to_remove.append(window_info['id'])
            except:
                windows_to_remove.append(window_info['id'])
        
        for window_id in windows_to_remove:
            self._remove_window(window_id)

    def register_window(self, window, title=None):
        """Регистрация окна в панели задач извне"""
        if not title:
            try:
                title = window.title() or "Окно"
            except:
                title = "Окно"
        
        self._track_window(window)
        return self.window_counter - 1

    # ==================== УВЕДОМЛЕНИЯ ====================
    
    def toggle_notification_panel(self, event=None):
        """Открыть/закрыть панель уведомлений"""
        if self.notification_panel and self.notification_panel.winfo_exists():
            try:
                self.notification_panel.destroy()
            except:
                pass
            self.notification_panel = None
            return
        
        try:
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
        except:
            pass
    
    def close_notification_panel(self):
        """Закрыть панель уведомлений"""
        if self.notification_panel and self.notification_panel.winfo_exists():
            try:
                self.notification_panel.destroy()
            except:
                pass
        self.notification_panel = None
    
    def load_notifications(self):
        """Загрузка уведомлений в панель"""
        try:
            for widget in self.notify_frame.winfo_children():
                widget.destroy()
        except:
            return
        
        notifications = []
        if self.notification_center:
            notifications = self.notification_center.notifications
        
        if not notifications:
            try:
                tk.Label(self.notify_frame, text="📭 Нет уведомлений", bg='#2C3E50', fg='#95A5A6',
                        font=('Segoe UI', 12)).pack(pady=50)
            except:
                pass
            return
        
        for notif in reversed(notifications[-20:]):
            self.create_notification_item(notif)
    
    def create_notification_item(self, notification):
        """Создание элемента уведомления"""
        bg_color = '#34495E' if not notification.get('read', False) else '#2C3E50'
        
        try:
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
        except:
            pass
    
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
            try:
                self.notify_btn.config(text="🔴")
                self.notify_badge.config(text=str(count))
                self.notify_badge.place(x=self.notify_btn.winfo_x() + 15, y=0)
            except:
                pass
        else:
            try:
                self.notify_btn.config(text="🔔")
                self.notify_badge.place_forget()
            except:
                pass
    
    def check_notifications(self):
        """Периодическая проверка уведомлений"""
        if self.notification_center:
            unread = sum(1 for n in self.notification_center.notifications if not n.get('read', False))
            self.update_notification_badge(unread)
        try:
            self.parent.after(5000, self.check_notifications)
        except:
            pass

    # ==================== ГРОМКОСТЬ ====================
    
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
        try:
            self.volume_btn.config(text=self._get_volume_icon())
        except:
            pass
        state = "ВЫКЛЮЧЕН" if self.is_muted else f"{self.current_volume}%"
        self.create_tooltip(self.volume_btn, 
                           f"Громкость BITOS: {state}\nНажмите для настройки")

    def toggle_mixer(self, event=None):
        """Открыть/закрыть микшер громкости"""
        if self.mixer_window and self.mixer_window.winfo_exists():
            try:
                self.mixer_window.destroy()
            except:
                pass
            self.mixer_window = None
            return
        
        try:
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
        except:
            pass

    def _on_volume_change(self, value):
        """Изменение громкости"""
        try:
            vol = int(float(value))
            self.current_volume = vol
            self.is_muted = vol == 0
            self._save_volume()
            self._update_volume_icon()
            
            if hasattr(self, 'mixer_percent_label') and self.mixer_percent_label.winfo_exists():
                self.mixer_percent_label.config(text=f"{vol}%")
            
            if hasattr(self, 'mute_btn') and self.mute_btn.winfo_exists():
                self.mute_btn.config(text="🔇 Выключить звук" if vol > 0 else "🔊 Включить звук")
        except:
            pass

    def _toggle_mute(self):
        """Включить/выключить звук"""
        if self.is_muted:
            self.current_volume = 50 if self.current_volume == 0 else self.current_volume
            self.is_muted = False
        else:
            self.is_muted = True
        
        self._save_volume()
        self._update_volume_icon()
        
        try:
            if hasattr(self, 'volume_slider') and self.volume_slider.winfo_exists():
                self.volume_slider.set(self.current_volume if not self.is_muted else 0)
            if hasattr(self, 'mixer_percent_label') and self.mixer_percent_label.winfo_exists():
                self.mixer_percent_label.config(
                    text=f"{self.current_volume}%" if not self.is_muted else "ВЫКЛЮЧЕНО")
            if hasattr(self, 'mute_btn') and self.mute_btn.winfo_exists():
                self.mute_btn.config(
                    text="🔊 Включить звук" if self.is_muted else "🔇 Выключить звук")
        except:
            pass

    def _close_mixer(self):
        """Закрыть микшер"""
        if self.mixer_window and self.mixer_window.winfo_exists():
            try:
                self.mixer_window.destroy()
            except:
                pass
        self.mixer_window = None

    def get_volume(self):
        """Получить текущую громкость"""
        if self.is_muted:
            return 0
        return self.current_volume

    # ==================== ЯЗЫК ====================
    
    def toggle_language(self, event=None):
        """Переключение языка"""
        if self.current_lang == "RU":
            self.current_lang = "EN"
            try:
                self.lang_label.config(text="EN", fg='#3498DB')
            except:
                pass
            self.switch_keyboard_layout("EN")
        else:
            self.current_lang = "RU"
            try:
                self.lang_label.config(text="RU", fg=self.theme_colors['taskbar_fg'])
            except:
                pass
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
        except:
            pass

    # ==================== БАТАРЕЯ ====================
    
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
                
                try:
                    self.battery_label.config(text=f"{icon} {percent}%")
                    if percent <= 20 and not plugged:
                        self.battery_label.config(fg='#E74C3C')
                    else:
                        self.battery_label.config(fg=self.theme_colors['taskbar_fg'])
                except:
                    pass
                
                self.create_tooltip(self.battery_label, 
                    f"Батарея: {percent}%\n{'Заряжается' if plugged else 'От батареи'}")
            else:
                try:
                    self.battery_label.config(text="🔌 ПК", fg=self.theme_colors['taskbar_fg'])
                except:
                    pass
                self.create_tooltip(self.battery_label, "Питание от сети")
        except:
            try:
                self.battery_label.config(text="🔋 ---%", fg=self.theme_colors['taskbar_fg'])
            except:
                pass
        
        try:
            self.parent.after(10000, self.update_battery)
        except:
            pass

    # ==================== ВРЕМЯ ====================
    
    def update_time(self):
        """Обновление времени и даты"""
        try:
            now = datetime.now()
            self.time_label.config(text=now.strftime("%H:%M"))
            self.date_label.config(text=now.strftime("%d.%m.%Y"))
            self.parent.after(1000, self.update_time)
        except:
            pass

    # ==================== МЕНЮ ПУСК ====================
    
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
            try:
                self.start_menu.destroy()
            except:
                pass
            self.start_menu = None
            return
        
        try:
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
                ('🛒', 'Магазин приложений', 'app_store', 'Системные'),
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
                        try:
                            f.config(bg='#3498DB')
                            for child in f.winfo_children():
                                child.config(bg='#3498DB')
                        except:
                            pass
                    
                    def on_leave(e, f=app_frame):
                        try:
                            f.config(bg='#34495E')
                            for child in f.winfo_children():
                                child.config(bg='#34495E')
                        except:
                            pass
                    
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
                    try:
                        self.start_menu.destroy()
                    except:
                        pass
                    self.start_menu = None
            
            self.start_menu.bind('<FocusOut>', on_focus_out)
            self.start_menu.focus_set()
        except:
            pass

    # ==================== ПЕРЕТАСКИВАНИЕ ====================
    
    drag_data = {"x": 0, "y": 0, "item": None, "icon": None, "name": None, "command": None}

    def start_drag(self, event):
        try:
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
        except:
            pass

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
                try:
                    self.launch_app(self.drag_data["command"], self.start_menu)
                except:
                    pass
            self.drag_data = {"x": 0, "y": 0, "item": None, "icon": None, 
                            "name": None, "command": None}
            return
        
        try:
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
        except:
            pass
        
        self.drag_data = {"x": 0, "y": 0, "item": None, "icon": None, 
                        "name": None, "command": None}

    def show_notification(self, message):
        if self.notification_center:
            try:
                self.notification_center.add_notification(
                    "Рабочий стол",
                    message,
                    icon="📌",
                    duration=3000
                )
            except:
                pass

    def launch_app(self, app_name, menu_window):
        if menu_window:
            try:
                menu_window.destroy()
            except:
                pass
            self.start_menu = None
        
        try:
            if app_name.startswith("bip:"):
                app_id = app_name.split(":", 1)[1]
                if self.desktop:
                    installer = BipInstaller(self.parent, self.desktop.bitos)
                    success, msg = installer.launch_app(app_id)
                    if not success:
                        messagebox.showerror("Ошибка", msg)
            elif app_name in self.commands:
                if hasattr(self, 'desktop') and self.desktop and hasattr(self.desktop.bitos, 'security'):
                    self.desktop.bitos.security.log_app_launch(app_name, self.username)
                self.commands[app_name]()
        except:
            pass

    # ==================== МЕНЮ ПИТАНИЯ ====================
    
    def show_power_menu(self):
        try:
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
        except:
            pass

    def shutdown_system(self):
        if messagebox.askyesno("Выключение", "Вы действительно хотите выключить компьютер?"):
            if hasattr(self, 'desktop') and self.desktop:
                if hasattr(self.desktop.bitos, 'security'):
                    self.desktop.bitos.security.log_shutdown(self.username)
                try:
                    self.desktop.save_desktop_shortcuts()
                except:
                    pass
                try:
                    self.desktop.save_widgets()
                except:
                    pass
            try:
                self.parent.destroy()
            except:
                pass
            shutdown_windows()

    def restart_system(self):
        if messagebox.askyesno("Перезагрузка", "Вы действительно хотите перезагрузить компьютер?"):
            if hasattr(self, 'desktop') and self.desktop:
                if hasattr(self.desktop.bitos, 'security'):
                    self.desktop.bitos.security.log_reboot(self.username)
                try:
                    self.desktop.save_desktop_shortcuts()
                except:
                    pass
                try:
                    self.desktop.save_widgets()
                except:
                    pass
            try:
                self.parent.destroy()
            except:
                pass
            restart_windows()

    # ==================== ТУЛТИПЫ ====================
    
    def create_tooltip(self, widget, text):
        def enter(event):
            try:
                x = widget.winfo_rootx() + 25
                y = widget.winfo_rooty() - 30
                self.tooltip = tk.Toplevel(widget)
                self.tooltip.wm_overrideredirect(True)
                self.tooltip.wm_geometry(f"+{x}+{y}")
                label = tk.Label(self.tooltip, text=text, background="#FFFFE0", 
                               relief=tk.SOLID, borderwidth=1, font=('Segoe UI', 9))
                label.pack()
            except:
                pass
        
        def leave(event):
            if self.tooltip:
                try:
                    self.tooltip.destroy()
                except:
                    pass
                self.tooltip = None
        
        try:
            widget.bind('<Enter>', enter)
            widget.bind('<Leave>', leave)
        except:
            pass

    def update_theme(self, theme_colors):
        self.theme_colors = theme_colors
        try:
            self.taskbar.config(bg=theme_colors['taskbar_bg'])
            
            self.user_label.config(bg=theme_colors['taskbar_bg'], fg=theme_colors['taskbar_fg'])
            self.time_label.config(bg=theme_colors['taskbar_bg'], fg=theme_colors['taskbar_fg'])
            self.date_label.config(bg=theme_colors['taskbar_bg'], fg=theme_colors['taskbar_fg'])
            self.battery_label.config(bg=theme_colors['taskbar_bg'], fg=theme_colors['taskbar_fg'])
            self.lang_label.config(bg=theme_colors['taskbar_bg'], fg=theme_colors['taskbar_fg'])
            self.volume_btn.config(bg=theme_colors['taskbar_bg'], fg=theme_colors['taskbar_fg'])
            self.notify_btn.config(bg=theme_colors['taskbar_bg'], fg=theme_colors['taskbar_fg'])
            self.power_btn.config(bg=theme_colors['taskbar_bg'])
            
            self.windows_container.config(bg=theme_colors['taskbar_bg'])
            self._update_windows_container()
        except:
            pass

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
    
    # ВСТРОЕННЫЕ ТЕМЫ С ОБОЯМИ
    THEMES = {
        "Базовая": {
            'name': 'Базовая', 
            'bg': '#2980B9', 
            'fg': 'white', 
            'taskbar_bg': '#1A5276', 
            'taskbar_fg': 'white', 
            'canvas_bg': '#2980B9', 
            'icon_fg': 'white',
            'widget_bg': '#1F618D', 
            'widget_fg': 'white',
            'wallpaper': 'System\\Config\\Wallpaper\\buinw1'
        },
        "Техно": {
            'name': 'Техно', 
            'bg': '#1B5E20', 
            'fg': '#00FF00', 
            'taskbar_bg': '#0D3B0D', 
            'taskbar_fg': '#00FF00', 
            'canvas_bg': '#1B5E20', 
            'icon_fg': '#00FF00',
            'widget_bg': '#0D3B0D', 
            'widget_fg': '#00FF00',
            'wallpaper': 'System\\Config\\Wallpaper\\buinw2'
        },
        "Эко": {
            'name': 'Эко', 
            'bg': '#27AE60', 
            'fg': '#FFFFFF', 
            'taskbar_bg': '#1E8449', 
            'taskbar_fg': '#FFFFFF', 
            'canvas_bg': '#27AE60', 
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
            'canvas_bg': '#0B1B3D', 
            'icon_fg': '#87CEEB',
            'widget_bg': '#060D1A', 
            'widget_fg': '#87CEEB',
            'wallpaper': 'System\\Config\\Wallpaper\\buinw4'
        },
    }
    
    # ПОЛЬЗОВАТЕЛЬСКИЕ ТЕМЫ (будут загружены из файла)
    USER_THEMES = {}

    def __init__(self, root, username, bitos_instance):
        self.root = root
        self.username = username
        self.bitos = bitos_instance
        
        # Сохраняем ссылку на desktop в bitos для доступа из других классов
        self.bitos.desktop_instance = self
        
        # Путь к виртуальному рабочему столу пользователя
        self.virtual_desktop_path = os.path.join(
            self.bitos.base_path, "System", "DesktopFile", self.username
        )
        os.makedirs(self.virtual_desktop_path, exist_ok=True)
        
        # Загрузка пользовательских тем
        self._load_user_themes()
        
        # Загрузка темы
        self.current_theme = self.load_theme()
        self.theme_colors = self._get_theme_colors(self.current_theme)
        
        # Менеджеры
        self.wallpaper_manager = WallpaperManager(bitos_instance)
        
        # Устанавливаем обои из темы если они есть
        self._apply_theme_wallpaper(self.current_theme)
        
        self.notification_center = NotificationCenter(root, bitos_instance)
        
        # Настройка окна
        self.root.overrideredirect(True)
        self.root.state('zoomed')
        self.root.configure(bg=self.theme_colors['bg'])
        
        # Таймер для отложенного ресайза
        self._resize_timer = None
        
        # Основной canvas для рабочего стола
        self.canvas = tk.Canvas(self.root, highlightthickness=0, 
                               bg=self.theme_colors['canvas_bg'], bd=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1, height=-40)
        
        # Списки для иконок и виджетов
        self.canvas.desktop_icons = []
        self.canvas.rearrange_icons = self.rearrange_icons
        self.canvas.save_shortcuts = self.save_desktop_shortcuts
        
        self.widgets = []
        self.widget_visible = True
        
        # Словарь команд для ярлыков
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
            'app_store': self.open_app_store,
        }
        
        # Рисуем обои
        self.update_wallpaper()
        
        # Создаем иконки
        self.create_desktop_icons()
        self.load_desktop_shortcuts()
        self.load_virtual_desktop_files()
        
        # Добавляем стандартные ярлыки
        self.add_default_shortcuts()
        
        # Загружаем виджеты
        self.load_widgets()
        
        # Создаем контекстное меню
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
            'app_store': self.open_app_store,
            'logout': self.logout,
            'shutdown': self.shutdown,
            'reboot': self.reboot,
        }
        
        # Создаем панель задач
        self.taskbar = Taskbar(self.root, username, taskbar_commands, 
                              self.theme_colors, self.canvas, 
                              self.canvas.desktop_icons, self)
        self.taskbar.desktop = self
        
        # Поднимаем иконки над обоями
        self.canvas.tag_raise('icon')
        
        # Показываем приветственное уведомление
        self.root.after(1000, self.show_welcome_notification)

    # ==================== МЕТОДЫ РАБОТЫ С ТЕМАМИ И ОБОЯМИ ====================
    
    def _load_user_themes(self):
        """Загрузка пользовательских тем из файла"""
        themes_file = os.path.join(self.bitos.system_paths["config"], "user_themes.json")
        if os.path.exists(themes_file):
            try:
                with open(themes_file, 'r', encoding='utf-8') as f:
                    self.USER_THEMES = json.load(f)
            except:
                self.USER_THEMES = {}
        else:
            self.USER_THEMES = {}
    
    def _save_user_themes(self):
        """Сохранение пользовательских тем в файл"""
        themes_file = os.path.join(self.bitos.system_paths["config"], "user_themes.json")
        try:
            with open(themes_file, 'w', encoding='utf-8') as f:
                json.dump(self.USER_THEMES, f, indent=4, ensure_ascii=False)
        except:
            pass
    
    def _get_theme_colors(self, theme_name):
        """Получение цветов темы по имени"""
        if theme_name in self.THEMES:
            return self.THEMES[theme_name].copy()
        if theme_name in self.USER_THEMES:
            return self.USER_THEMES[theme_name].copy()
        return self.THEMES["Базовая"].copy()
    
    def get_all_themes(self):
        """Получение всех доступных тем"""
        all_themes = {}
        all_themes.update(self.THEMES)
        all_themes.update(self.USER_THEMES)
        return all_themes
    
    def get_theme_names(self):
        """Получение списка названий всех тем"""
        return list(self.get_all_themes().keys())
    
    def create_user_theme(self, name, bg_color, fg_color, taskbar_bg, taskbar_fg, 
                          canvas_bg, icon_fg, widget_bg, widget_fg, wallpaper_path=None):
        """Создание пользовательской темы с обоями"""
        if name in self.THEMES:
            return False, "Тема с таким именем уже существует во встроенных темах"
        if name in self.USER_THEMES:
            return False, "Тема с таким именем уже существует"
        
        wallpaper_rel_path = None
        if wallpaper_path and os.path.exists(wallpaper_path):
            wallpaper_dir = os.path.join(self.bitos.base_path, "System", "Config", "Wallpaper")
            os.makedirs(wallpaper_dir, exist_ok=True)
            
            ext = os.path.splitext(wallpaper_path)[1]
            new_name = f"user_wallpaper_{int(time.time())}{ext}"
            new_path = os.path.join(wallpaper_dir, new_name)
            try:
                shutil.copy2(wallpaper_path, new_path)
                wallpaper_rel_path = f"System\\Config\\Wallpaper\\{new_name}"
            except Exception as e:
                return False, f"Не удалось скопировать обои: {str(e)}"
        
        self.USER_THEMES[name] = {
            'name': name,
            'bg': bg_color,
            'fg': fg_color,
            'taskbar_bg': taskbar_bg,
            'taskbar_fg': taskbar_fg,
            'canvas_bg': canvas_bg,
            'icon_fg': icon_fg,
            'widget_bg': widget_bg,
            'widget_fg': widget_fg,
            'wallpaper': wallpaper_rel_path,
            'is_user_theme': True,
            'created': datetime.now().isoformat()
        }
        
        self._save_user_themes()
        self.change_theme(name)
        
        if wallpaper_rel_path:
            full_wallpaper_path = os.path.join(self.bitos.base_path, wallpaper_rel_path.replace('\\', os.sep))
            if os.path.exists(full_wallpaper_path):
                self.wallpaper_manager.set_wallpaper(full_wallpaper_path)
                self.update_wallpaper()
        
        return True, "Тема успешно создана и применена!"
    
    def delete_user_theme(self, theme_name):
        """Удаление пользовательской темы"""
        if theme_name not in self.USER_THEMES:
            return False, "Тема не найдена"
        
        del self.USER_THEMES[theme_name]
        self._save_user_themes()
        
        if self.current_theme == theme_name:
            self.change_theme("Базовая")
        
        return True, "Тема удалена"
    
    def load_theme(self):
        """Загрузка темы"""
        theme_file = os.path.join(self.bitos.system_paths["config"], "theme.cfg")
        if os.path.exists(theme_file):
            try:
                with open(theme_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    theme = data.get('theme', 'Базовая')
                    all_themes = self.get_all_themes()
                    if theme in all_themes:
                        return theme
            except:
                pass
        return "Базовая"
    
    def save_theme(self, theme_name):
        """Сохранение темы"""
        theme_file = os.path.join(self.bitos.system_paths["config"], "theme.cfg")
        try:
            with open(theme_file, 'w', encoding='utf-8') as f:
                json.dump({'theme': theme_name}, f, indent=4)
        except:
            pass
    
    def _apply_theme_wallpaper(self, theme_name):
        """Применение обоев из темы"""
        all_themes = self.get_all_themes()
        if theme_name not in all_themes:
            return
        
        theme = all_themes[theme_name]
        wallpaper_path = theme.get('wallpaper')
        
        if wallpaper_path:
            full_path = os.path.join(
                self.bitos.base_path,
                wallpaper_path.replace('\\', os.sep)
            )
            
            if os.path.exists(full_path):
                self.wallpaper_manager.set_wallpaper(full_path)
                self.update_wallpaper()
            else:
                wallpaper_dir = os.path.join(self.bitos.base_path, "System", "Config", "Wallpaper")
                if os.path.exists(wallpaper_dir):
                    wallpaper_name = os.path.basename(wallpaper_path)
                    for f in os.listdir(wallpaper_dir):
                        if f == wallpaper_name or f.startswith(wallpaper_name):
                            full_path = os.path.join(wallpaper_dir, f)
                            self.wallpaper_manager.set_wallpaper(full_path)
                            self.update_wallpaper()
                            break
    
    def change_theme(self, theme_name):
        """Смена темы оформления с автоматической сменой обоев"""
        all_themes = self.get_all_themes()
        if theme_name not in all_themes:
            return False
        
        old_theme = self.current_theme
        self.current_theme = theme_name
        self.theme_colors = all_themes[theme_name].copy()
        self.save_theme(theme_name)
        
        self._apply_theme_wallpaper(theme_name)
        
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
            "🎨 Тема изменена",
            f"Применена тема: {theme_name} с обоями",
            icon="🎨",
            duration=3000
        )
        
        return True

    # ==================== МЕТОДЫ КАК БЫЛИ В ОРИГИНАЛЕ ====================
    
    def get_virtual_desktop_path(self):
        """Возвращает путь к виртуальному рабочему столу пользователя"""
        return self.virtual_desktop_path
    
    def get_trash_path(self):
        """Возвращает путь к корзине пользователя"""
        trash_path = os.path.join(
            self.bitos.base_path, "System", "DesktopFile", ".trash", self.username
        )
        os.makedirs(trash_path, exist_ok=True)
        return trash_path
    
    def show_welcome_notification(self):
        """Показывает приветственное уведомление"""
        self.notification_center.add_notification(
            "Добро пожаловать!",
            f"Пользователь {self.username} вошёл в систему BITOS",
            icon="👋",
            category="system"
        )

    # ==================== РАБОТА С ОБОЯМИ ====================
    
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
        except Exception as e:
            pass
    
    def draw_gradient_background(self, width, height):
        """Рисует градиентный фон если нет обоев"""
        try:
            for i in range(0, height, 2):
                factor = i / height
                color = self._interpolate_color(
                    self.theme_colors['canvas_bg'],
                    self._adjust_brightness(self.theme_colors['canvas_bg'], 0.85),
                    factor
                )
                self.canvas.create_line(0, i, width, i, fill=color, tags='wallpaper')
        except Exception as e:
            pass
    
    def _interpolate_color(self, color1, color2, factor):
        """Интерполяция между двумя цветами"""
        c1 = self._hex_to_rgb(color1)
        c2 = self._hex_to_rgb(color2)
        r = int(c1[0] + (c2[0] - c1[0]) * factor)
        g = int(c1[1] + (c2[1] - c1[1]) * factor)
        b = int(c1[2] + (c2[2] - c1[2]) * factor)
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def _hex_to_rgb(self, hex_color):
        """Преобразование HEX в RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _adjust_brightness(self, hex_color, factor):
        """Изменение яркости цвета"""
        r, g, b = self._hex_to_rgb(hex_color)
        r = min(255, int(r * factor))
        g = min(255, int(g * factor))
        b = min(255, int(b * factor))
        return f'#{r:02x}{g:02x}{b:02x}'

    # ==================== РАБОТА С ИКОНКАМИ ====================
    
    def create_desktop_icons(self):
        """Создание базовых иконок рабочего стола"""
        trash_icon = DesktopIcon(self.canvas, 0, 0, '🗑', 'Корзина', self.open_trash)
        trash_icon.update_theme(self.theme_colors['icon_fg'])
        self.canvas.desktop_icons.append(trash_icon)
        self.canvas.tag_raise('icon')
    
    def load_virtual_desktop_files(self):
        """Загрузка файлов и папок из виртуального рабочего стола"""
        if not os.path.exists(self.virtual_desktop_path):
            return
        
        try:
            items = os.listdir(self.virtual_desktop_path)
            items = [item for item in items if not item.startswith('.')]
            
            folders = []
            files = []
            for item in items:
                item_path = os.path.join(self.virtual_desktop_path, item)
                if os.path.isdir(item_path):
                    folders.append(item)
                else:
                    files.append(item)
            
            folders.sort(key=str.lower)
            files.sort(key=str.lower)
            
            for folder in folders:
                folder_path = os.path.join(self.virtual_desktop_path, folder)
                self._add_virtual_file_icon(folder_path, folder, is_dir=True)
            
            for file in files:
                file_path = os.path.join(self.virtual_desktop_path, file)
                self._add_virtual_file_icon(file_path, file, is_dir=False)
            
            self.rearrange_icons()
        except Exception as e:
            print(f"Ошибка загрузки файлов виртуального рабочего стола: {e}")
    
    def _add_virtual_file_icon(self, path, name, is_dir=False):
        """Добавление иконки файла/папки из виртуального рабочего стола"""
        for icon in self.canvas.desktop_icons:
            if hasattr(icon, 'virtual_path') and icon.virtual_path == path:
                return
            if hasattr(icon, 'file_path') and icon.file_path == path:
                return
        
        if is_dir:
            icon_symbol = "📁"
            command = lambda p=path: self.open_virtual_folder(p)
        else:
            icon_symbol = self._get_file_icon_symbol(name)
            command = lambda p=path: self.open_virtual_file(p)
        
        grid_x, grid_y = self._find_free_grid_position()
        
        desktop_icon = DesktopIcon(self.canvas, grid_x, grid_y, icon_symbol, name, command)
        desktop_icon.virtual_path = path
        desktop_icon.is_virtual_item = True
        desktop_icon.update_theme(self.theme_colors['icon_fg'])
        self.canvas.desktop_icons.append(desktop_icon)
        self.canvas.tag_raise('icon')
    
    def _get_file_icon_symbol(self, filename):
        """Получение иконки для файла по расширению"""
        ext = os.path.splitext(filename)[1].lower()
        icons = {
            '.txt': '📄', '.doc': '📝', '.docx': '📝',
            '.jpg': '🖼', '.jpeg': '🖼', '.png': '🖼', '.gif': '🖼', '.bmp': '🖼',
            '.mp3': '🎵', '.wav': '🎵', '.flac': '🎵',
            '.mp4': '🎬', '.avi': '🎬', '.mkv': '🎬',
            '.pdf': '📕', '.exe': '⚙', '.msi': '⚙',
            '.zip': '📦', '.rar': '📦', '.7z': '📦',
            '.py': '🐍', '.js': '📜', '.html': '🌐', '.css': '🎨',
            '.xls': '📊', '.xlsx': '📊', '.ppt': '📽', '.pptx': '📽',
            '.json': '📊', '.xml': '📝', '.csv': '📊',
            '.md': '📝', '.log': '📋', '.cfg': '⚙', '.ini': '⚙',
        }
        return icons.get(ext, '📄')
    
    def save_desktop_shortcuts(self):
        """Сохранение ярлыков рабочего стола"""
        shortcuts_file = os.path.join(self.bitos.user_paths["home"], "desktop_shortcuts.json")
        shortcuts = []
        for icon in self.canvas.desktop_icons:
            if icon.is_trash:
                continue
            if hasattr(icon, 'is_virtual_item') and icon.is_virtual_item:
                continue
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
        """Загрузка сохранённых ярлыков рабочего стола"""
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
    
    def add_default_shortcuts(self):
        """Добавление стандартных ярлыков на рабочий стол"""
        default_shortcuts = [
            ('🛒', 'Магазин приложений', self.open_app_store),
        ]
        
        for icon, name, command in default_shortcuts:
            exists = False
            for existing in self.canvas.desktop_icons:
                if existing.text == name and not existing.is_trash:
                    exists = True
                    break
            
            if not exists:
                grid_x, grid_y = self._find_free_grid_position()
                
                new_icon = DesktopIcon(
                    self.canvas, 
                    grid_x, grid_y, 
                    icon, 
                    name, 
                    command
                )
                new_icon.update_theme(self.theme_colors['icon_fg'])
                self.canvas.desktop_icons.append(new_icon)
        
        self.canvas.tag_raise('icon')
        self.save_desktop_shortcuts()
    
    def _find_free_grid_position(self):
        """Поиск свободной позиции в сетке"""
        used_positions = set()
        used_positions.add((0, 0))
        
        for icon in self.canvas.desktop_icons:
            used_positions.add((icon.grid_x, icon.grid_y))
        
        for row in range(20):
            start_col = 0 if row > 0 else 1
            for col in range(start_col, DesktopIcon.COLS):
                if (col, row) not in used_positions:
                    return col, row
        return 1, 0
    
    def rearrange_icons(self):
        """Упорядочивание иконок по сетке"""
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

    # ==================== ОТКРЫТИЕ ФАЙЛОВ И ПАПОК ====================
    
    def open_virtual_folder(self, folder_path):
        """Открытие виртуальной папки в проводнике"""
        if not os.path.exists(folder_path):
            messagebox.showerror("Ошибка", f"Папка не найдена:\n{folder_path}")
            self.refresh_virtual_desktop()
            return
        
        if hasattr(self.bitos, 'security'):
            self.bitos.security.log_app_launch("Explorer", self.username)
        
        ModernFileExplorer(self.root, self.bitos, folder_path)
    
    def open_virtual_file(self, file_path):
        """Открытие виртуального файла во встроенном редакторе"""
        if not os.path.exists(file_path):
            messagebox.showerror("Ошибка", f"Файл не найден:\n{file_path}")
            self.refresh_virtual_desktop()
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            dialog = tk.Toplevel(self.root)
            dialog.title(f"📄 {os.path.basename(file_path)}")
            dialog.geometry("800x600")
            dialog.transient(self.root)
            dialog.configure(bg='#F5F7FA')
            
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
            
        except UnicodeDecodeError:
            messagebox.showinfo("Информация", 
                               f"Файл '{os.path.basename(file_path)}' является бинарным.\n"
                               "Открытие в текстовом редакторе невозможно.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n{str(e)}")
    
    def refresh_virtual_desktop(self):
        """Обновление отображения файлов виртуального рабочего стола"""
        icons_to_remove = []
        for icon in self.canvas.desktop_icons:
            if hasattr(icon, 'is_virtual_item') and icon.is_virtual_item and not icon.is_trash:
                icons_to_remove.append(icon)
            elif hasattr(icon, 'is_file_item') and icon.is_file_item and not icon.is_trash:
                icons_to_remove.append(icon)
        
        for icon in icons_to_remove:
            try:
                self.canvas.delete(f'hitbox_{icon.icon_id}')
                self.canvas.delete(f'icon_{icon.icon_id}')
                self.canvas.delete(f'text_{icon.icon_id}')
                self.canvas.desktop_icons.remove(icon)
            except:
                pass
        
        self.load_virtual_desktop_files()
        self.canvas.tag_raise('icon')

    # ==================== СОЗДАНИЕ ФАЙЛОВ И ПАПОК ====================
    
    def create_new_folder(self):
        """Создание новой папки на виртуальном рабочем столе"""
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
            folder_path = os.path.join(self.virtual_desktop_path, name)
            
            if os.path.exists(folder_path):
                messagebox.showwarning("Предупреждение", f"Папка '{name}' уже существует", parent=dialog)
                return
            
            try:
                os.makedirs(folder_path, exist_ok=True)
                
                if hasattr(self.bitos, 'security'):
                    self.bitos.security.log_folder_create(self.username, folder_path)
                
                self._add_virtual_file_icon(folder_path, name, is_dir=True)
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
            
            file_path = os.path.join(self.virtual_desktop_path, name)
            
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
                
                self._add_virtual_file_icon(file_path, name, is_dir=False)
                self.rearrange_icons()
                
                self.notification_center.add_notification(
                    "Файл создан",
                    f"Файл '{name}' создан на рабочем столе",
                    icon="📄",
                    duration=3000
                )
                
                dialog.destroy()
                self.open_virtual_file(file_path)
                
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
            
            file_path = os.path.join(self.virtual_desktop_path, name)
            
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
                
                self._add_virtual_file_icon(file_path, name, is_dir=False)
                self.rearrange_icons()
                
                self.notification_center.add_notification(
                    "Файл создан",
                    f"Файл '{name}' создан на рабочем столе",
                    icon="📄",
                    duration=3000
                )
                
                dialog.destroy()
                self.open_virtual_file(file_path)
                
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

    # ==================== ДОБАВЛЕНИЕ ЯРЛЫКОВ ====================
    
    def show_add_shortcut_dialog(self):
        """Показать диалог добавления ярлыка"""
        dialog = tk.Toplevel(self.root)
        dialog.title("🔗 Добавить ярлык")
        dialog.geometry("550x520")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg='#F5F7FA')
        dialog.resizable(False, False)
        
        x = (dialog.winfo_screenwidth() - 550) // 2
        y = (dialog.winfo_screenheight() - 520) // 2
        dialog.geometry(f'+{x}+{y}')
        
        header = tk.Frame(dialog, bg='#3498DB', height=50)
        header.pack(fill=tk.X)
        tk.Label(header, text="🔗 Создание ярлыка", bg='#3498DB', fg='white',
                font=('Segoe UI', 14, 'bold')).pack(pady=12)
        
        main_frame = tk.Frame(dialog, bg='#F5F7FA')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(main_frame, text="Тип ярлыка:", font=('Segoe UI', 11, 'bold'),
                bg='#F5F7FA', fg='#2C3E50').pack(anchor='w', pady=(0, 5))
        
        type_var = tk.StringVar(value="website")
        
        type_frame = tk.Frame(main_frame, bg='#F5F7FA')
        type_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Radiobutton(type_frame, text="🌐 Веб-сайт", variable=type_var, value="website",
                      bg='#F5F7FA', fg='#2C3E50', font=('Segoe UI', 10),
                      activebackground='#F5F7FA', 
                      command=lambda: self._toggle_shortcut_fields(type_var, website_frame, app_frame)).pack(side=tk.LEFT, padx=10)
        
        tk.Radiobutton(type_frame, text="📄 Приложение (.exe)", variable=type_var, value="app",
                      bg='#F5F7FA', fg='#2C3E50', font=('Segoe UI', 10),
                      activebackground='#F5F7FA',
                      command=lambda: self._toggle_shortcut_fields(type_var, website_frame, app_frame)).pack(side=tk.LEFT, padx=10)
        
        website_frame = tk.Frame(main_frame, bg='#F5F7FA')
        website_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(website_frame, text="URL веб-сайта:", font=('Segoe UI', 10),
                bg='#F5F7FA', fg='#2C3E50').pack(anchor='w')
        url_entry = tk.Entry(website_frame, font=('Segoe UI', 11), bg='white', fg='#2C3E50',
                            bd=0, highlightthickness=2, highlightcolor='#3498DB',
                            highlightbackground='#BDC3C7')
        url_entry.pack(fill=tk.X, ipady=8, pady=(5, 10))
        url_entry.insert(0, "https://")
        
        app_frame = tk.Frame(main_frame, bg='#F5F7FA')
        app_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(app_frame, text="Путь к приложению:", font=('Segoe UI', 10),
                bg='#F5F7FA', fg='#2C3E50').pack(anchor='w')
        
        app_path_frame = tk.Frame(app_frame, bg='#F5F7FA')
        app_path_frame.pack(fill=tk.X, pady=(5, 10))
        
        app_entry = tk.Entry(app_path_frame, font=('Segoe UI', 11), bg='white', fg='#2C3E50',
                            bd=0, highlightthickness=2, highlightcolor='#3498DB',
                            highlightbackground='#BDC3C7')
        app_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8)
        app_entry.insert(0, "Выберите .exe файл...")
        app_entry.config(state='disabled')
        
        def browse_exe():
            file_path = filedialog.askopenfilename(
                title="Выберите приложение",
                filetypes=[("Исполняемые файлы", "*.exe"), ("Все файлы", "*.*")]
            )
            if file_path:
                app_entry.config(state='normal')
                app_entry.delete(0, tk.END)
                app_entry.insert(0, file_path)
                app_entry.config(state='disabled')
                name_entry.delete(0, tk.END)
                name_entry.insert(0, os.path.splitext(os.path.basename(file_path))[0])
        
        tk.Button(app_path_frame, text="📂 Обзор", bg='#3498DB', fg='white',
                 font=('Segoe UI', 10), bd=0, padx=15, pady=8,
                 cursor='hand2', command=browse_exe).pack(side=tk.RIGHT, padx=(10, 0))
        
        app_frame.pack_forget()
        
        tk.Label(main_frame, text="Имя ярлыка:", font=('Segoe UI', 10),
                bg='#F5F7FA', fg='#2C3E50').pack(anchor='w', pady=(10, 5))
        name_entry = tk.Entry(main_frame, font=('Segoe UI', 11), bg='white', fg='#2C3E50',
                             bd=0, highlightthickness=2, highlightcolor='#3498DB',
                             highlightbackground='#BDC3C7')
        name_entry.pack(fill=tk.X, ipady=8, pady=(5, 10))
        name_entry.insert(0, "Мой ярлык")
        
        tk.Label(main_frame, text="Иконка:", font=('Segoe UI', 10),
                bg='#F5F7FA', fg='#2C3E50').pack(anchor='w')
        
        icon_frame = tk.Frame(main_frame, bg='#F5F7FA')
        icon_frame.pack(fill=tk.X, pady=(5, 10))
        
        icon_var = tk.StringVar(value="🌐")
        
        icon_presets = [
            ("🌐", "Веб"), ("📁", "Папка"), ("⚙️", "Настройки"),
            ("📄", "Документ"), ("🎮", "Игра"), ("🎵", "Музыка"),
            ("🖼", "Изображение"), ("📦", "Пакет"), ("🔧", "Инструмент"),
            ("💻", "Компьютер"), ("📱", "Телефон"), ("📧", "Почта"),
            ("🛒", "Магазин"), ("📊", "График"), ("🔒", "Безопасность"),
        ]
        
        icon_grid = tk.Frame(icon_frame, bg='#F5F7FA')
        icon_grid.pack(fill=tk.X)
        
        for i, (icon, label) in enumerate(icon_presets):
            row = i // 8
            col = i % 8
            
            btn = tk.Button(icon_grid, text=icon, font=('Segoe UI', 14),
                           bg='white', fg='#2C3E50', relief=tk.RAISED, bd=1,
                           width=3, height=1, cursor='hand2')
            btn.grid(row=row, column=col, padx=2, pady=2)
            
            def on_click(e, b=btn, ic=icon):
                icon_var.set(ic)
                for child in icon_grid.winfo_children():
                    child.config(bg='white', relief=tk.RAISED)
                b.config(bg='#3498DB', relief=tk.SUNKEN)
            
            btn.bind('<Button-1>', on_click)
        
        custom_frame = tk.Frame(main_frame, bg='#F5F7FA')
        custom_frame.pack(fill=tk.X, pady=(5, 0))
        
        tk.Label(custom_frame, text="Или введите свой символ:", font=('Segoe UI', 9),
                bg='#F5F7FA', fg='#7F8C8D').pack(anchor='w')
        
        icon_entry = tk.Entry(custom_frame, font=('Segoe UI', 12), bg='white', fg='#2C3E50',
                             bd=0, highlightthickness=2, highlightcolor='#3498DB',
                             highlightbackground='#BDC3C7', width=5)
        icon_entry.pack(side=tk.LEFT, ipady=5, pady=(5, 10))
        icon_entry.insert(0, "🌐")
        icon_entry.bind('<KeyRelease>', lambda e: icon_var.set(icon_entry.get().strip() or "📄"))
        
        btn_frame = tk.Frame(main_frame, bg='#F5F7FA')
        btn_frame.pack(fill=tk.X, pady=10)
        
        def create_shortcut():
            shortcut_type = type_var.get()
            name = name_entry.get().strip()
            icon = icon_var.get().strip() or "📄"
            
            if not name:
                messagebox.showerror("Ошибка", "Введите имя ярлыка", parent=dialog)
                return
            
            for existing in self.canvas.desktop_icons:
                if existing.text == name and not existing.is_trash:
                    if not messagebox.askyesno("Ярлык существует", 
                                              f"Ярлык '{name}' уже существует. Заменить?", 
                                              parent=dialog):
                        return
                    try:
                        self.canvas.delete(f'hitbox_{existing.icon_id}')
                        self.canvas.delete(f'icon_{existing.icon_id}')
                        self.canvas.delete(f'text_{existing.icon_id}')
                        self.canvas.desktop_icons.remove(existing)
                    except:
                        pass
                    break
            
            if shortcut_type == "website":
                url = url_entry.get().strip()
                if not url or url == "https://":
                    messagebox.showerror("Ошибка", "Введите URL веб-сайта", parent=dialog)
                    return
                
                def open_website(u=url):
                    import webbrowser
                    webbrowser.open(u)
                    if hasattr(self.bitos, 'security'):
                        self.bitos.security.log_app_launch(f"Website: {u}", self.username)
                
                command = open_website
                
            else:
                app_path = app_entry.get().strip()
                if not app_path or app_path == "Выберите .exe файл...":
                    messagebox.showerror("Ошибка", "Выберите приложение", parent=dialog)
                    return
                
                if not os.path.exists(app_path):
                    messagebox.showerror("Ошибка", "Файл не найден", parent=dialog)
                    return
                
                def open_app(p=app_path):
                    try:
                        subprocess.Popen([p], shell=True)
                        if hasattr(self.bitos, 'security'):
                            self.bitos.security.log_app_launch(f"App: {os.path.basename(p)}", self.username)
                    except Exception as e:
                        messagebox.showerror("Ошибка", f"Не удалось запустить:\n{str(e)}")
                
                command = open_app
            
            grid_x, grid_y = self._find_free_grid_position()
            
            new_icon = DesktopIcon(self.canvas, grid_x, grid_y, icon, name, command)
            new_icon.update_theme(self.theme_colors['icon_fg'])
            self.canvas.desktop_icons.append(new_icon)
            
            self.save_desktop_shortcuts()
            
            if hasattr(self.bitos, 'security'):
                self.bitos.security.log_shortcut_create(self.username, name, (grid_x, grid_y))
            
            self.notification_center.add_notification(
                "🔗 Ярлык создан",
                f"Ярлык '{name}' добавлен на рабочий стол",
                icon="🔗",
                duration=3000
            )
            
            dialog.destroy()
            self.canvas.tag_raise('icon')
        
        tk.Button(btn_frame, text="✅ Создать ярлык", bg='#27AE60', fg='white',
                 font=('Segoe UI', 11, 'bold'), bd=0, padx=30, pady=10,
                 cursor='hand2', command=create_shortcut).pack(side=tk.RIGHT, padx=5)
        
        tk.Button(btn_frame, text="Отмена", bg='#95A5A6', fg='white',
                 font=('Segoe UI', 10), bd=0, padx=30, pady=10,
                 cursor='hand2', command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
        name_entry.bind('<Return>', lambda e: create_shortcut())
        url_entry.bind('<Return>', lambda e: create_shortcut())
        
        for child in icon_grid.winfo_children():
            if child.cget('text') == "🌐":
                child.config(bg='#3498DB', relief=tk.SUNKEN)
                break
    
    def _toggle_shortcut_fields(self, type_var, website_frame, app_frame):
        """Переключение полей в зависимости от типа ярлыка"""
        if type_var.get() == "website":
            website_frame.pack(fill=tk.X, pady=5)
            app_frame.pack_forget()
        else:
            website_frame.pack_forget()
            app_frame.pack(fill=tk.X, pady=5)

    # ==================== МАГАЗИН ПРИЛОЖЕНИЙ ====================
    
    def open_app_store(self):
        """Открыть магазин приложений (заглушка)"""
        if hasattr(self.bitos, 'security'):
            self.bitos.security.log_app_launch("App Store", self.username)
        
        store_window = tk.Toplevel(self.root)
        store_window.title("🛒 Магазин приложений BITOS")
        store_window.geometry("800x600")
        store_window.transient(self.root)
        store_window.configure(bg='#F5F7FA')
        store_window.resizable(False, False)
        
        x = (store_window.winfo_screenwidth() - 800) // 2
        y = (store_window.winfo_screenheight() - 600) // 2
        store_window.geometry(f'+{x}+{y}')
        
        header = tk.Frame(store_window, bg='#3498DB', height=70)
        header.pack(fill=tk.X)
        
        tk.Label(header, text="🛒 Магазин приложений BITOS", bg='#3498DB', fg='white',
                font=('Segoe UI', 18, 'bold')).pack(pady=15)
        
        tk.Label(header, text="Скоро здесь появятся приложения для скачивания", 
                bg='#3498DB', fg='#D4E6F1', font=('Segoe UI', 11)).pack()
        
        main_frame = tk.Frame(store_window, bg='#F5F7FA')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        dev_frame = tk.Frame(main_frame, bg='white', relief=tk.RIDGE, bd=2)
        dev_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(dev_frame, text="🚧", font=('Segoe UI', 80), bg='white').pack(expand=True, pady=20)
        
        tk.Label(dev_frame, text="Магазин приложений в разработке", 
                font=('Segoe UI', 18, 'bold'), bg='white', fg='#2C3E50').pack()
        
        tk.Label(dev_frame, text="В ближайшее время здесь появятся приложения для скачивания\n"
                                 "Вы сможете устанавливать новые программы прямо из магазина", 
                font=('Segoe UI', 11), bg='white', fg='#7F8C8D', justify='center').pack(pady=10)
        
        features_frame = tk.Frame(dev_frame, bg='white')
        features_frame.pack(pady=20)
        
        features = [
            "📦 Установка в один клик",
            "🔄 Автоматические обновления",
            "⭐ Рейтинги и отзывы",
            "🔒 Безопасная загрузка"
        ]
        
        for feature in features:
            tk.Label(features_frame, text=feature, font=('Segoe UI', 11), 
                    bg='white', fg='#27AE60').pack(anchor='w', pady=3)
        
        tk.Button(main_frame, text="Закрыть", bg='#95A5A6', fg='white',
                 font=('Segoe UI', 11), bd=0, padx=30, pady=10,
                 cursor='hand2', command=store_window.destroy).pack(pady=10)
        
        self.notification_center.add_notification(
            "🛒 Магазин приложений",
            "Магазин приложений открыт (в разработке)",
            icon="🛒",
            duration=3000
        )

    # ==================== НАСТРОЙКИ ====================
    
    def open_settings(self):
        """Открыть окно настроек"""
        if hasattr(self.bitos, 'security'):
            self.bitos.security.log_app_launch("Settings", self.username)
        
        SettingsWindow(self.root, self)

    # ==================== КОНТЕКСТНОЕ МЕНЮ ====================
    
    def create_context_menu(self):
        """Создание контекстного меню рабочего стола"""
        self.context_menu = tk.Menu(self.root, tearoff=0, bg='#2C3E50', fg='white', 
                                   activebackground='#3498DB', activeforeground='white')
        
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
        create_menu.add_separator()
        create_menu.add_command(label='📋 Другой файл...', command=self.create_custom_file)
        
        self.context_menu.add_cascade(label='➕ Создать', menu=create_menu)
        self.context_menu.add_separator()
        
        self.context_menu.add_command(label='🔗 Добавить ярлык', 
                                     command=self.show_add_shortcut_dialog)
        
        self.context_menu.add_separator()
        self.context_menu.add_command(label='🔄 Обновить', command=self.refresh_desktop)
        self.context_menu.add_command(label='📁 Открыть проводник', command=self.open_explorer)
        self.context_menu.add_command(label='🛒 Магазин приложений', 
                                     command=self.open_app_store)
        
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

    # ==================== ОБНОВЛЕНИЕ РАБОЧЕГО СТОЛА ====================
    
    def on_window_resize(self, event):
        """Обработчик изменения размера окна"""
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
    
    def toggle_fullscreen(self, event=None):
        """Переключение полноэкранного режима"""
        if not hasattr(self, 'fullscreen'):
            self.fullscreen = False
        self.fullscreen = not self.fullscreen
        self.root.attributes('-fullscreen', self.fullscreen)
    
    def refresh_desktop(self):
        """Обновить рабочий стол"""
        self.update_wallpaper()
        self.refresh_virtual_desktop()
        self.canvas.tag_raise('icon')
        self.notification_center.add_notification(
            "Рабочий стол обновлён",
            "Обои и файлы перезагружены",
            icon="🔄",
            duration=2000
        )

    # ==================== ЗАПУСК ПРИЛОЖЕНИЙ ====================
    
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
        import webbrowser
        webbrowser.open_new("")
        self.notification_center.add_notification(
            "Браузер",
            "Браузер запущен",
            icon="🌐",
            duration=2000
        )
    
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
    
    def open_wallpaper_settings(self):
        """Открыть настройки обоев"""
        self.wallpaper_manager.open_wallpaper_selector(
            self.root, 
            callback=self.update_wallpaper
        )

    # ==================== ВИДЖЕТЫ ====================
    
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

    # ==================== СИСТЕМНЫЕ ДЕЙСТВИЯ ====================
    
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
        self.version = "06V6_28.06"
        self.build = "2026.06 BETA"
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
        
        # СИСТЕМНЫЕ ПАПКИ
        self.system_paths = {
            "config": os.path.join(self.base_path, "System", "Config"),
            "security": os.path.join(self.base_path, "System", "Security"),
            "logs": os.path.join(self.base_path, "System", "Logs"),
            "temp": os.path.join(self.base_path, "System", "Temp"),
            "system": os.path.join(self.base_path, "System"),
            "apps": os.path.join(self.base_path, "System", "Apps"),
            "sounds": os.path.join(self.base_path, "System", "Sounds"),
            "desktop_files": os.path.join(self.base_path, "System", "DesktopFile"),
        }
        
        self._init_user_paths()
        
        self.system_files = {
            "serial": os.path.join(self.system_paths["security"], "serial.bin"),
            "license": os.path.join(self.system_paths["security"], "license.key"),
            "checksums": os.path.join(self.system_paths["security"], "checksums.db"),
            "dev_log": os.path.join(self.system_paths["logs"], "dev.log"),
            "system_config": os.path.join(self.system_paths["config"], "system.cfg"),
            "users_db": os.path.join(self.system_paths["config"], "users.db"),
            "pin_db": os.path.join(self.system_paths["security"], "pin.hash"),
            "icons_db": os.path.join(self.system_paths["config"], "icons.json"),
            "desktop_shortcuts": os.path.join(self.system_paths["config"], "desktop_shortcuts.json"),
            "widgets": os.path.join(self.system_paths["config"], "widgets.json"),
            "theme": os.path.join(self.system_paths["config"], "theme.cfg"),
            "wallpaper": os.path.join(self.system_paths["config"], "wallpaper.json"),
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
        
        # Перехват консоли
        self._console_buffer = []
        self._console_lock = threading.Lock()
        self._console_running = True
        self._console_log_path = os.path.join(self.system_paths["logs"], "console.log")
        self._error_log_path = self.log_files["error"]
        
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        
        self._init_console_log()
        sys.stdout = self._ConsoleRedirect(self, False)
        sys.stderr = self._ConsoleRedirect(self, True)
        self._start_console_writer()
        
        self.protected_files = [
            self.system_files["serial"],
            self.system_files["license"],
            self.system_files["pin_db"],
            self.system_files["icons_db"],
        ]
        
        # Звуковая система
        self.sound_enabled = True
        self.sound_path = os.path.join(self.base_path, "System", "Sounds")
        os.makedirs(self.sound_path, exist_ok=True)
        
        self.initialize_filesystem()
        self.security = SecurityManager(self)
        
        self._create_sound_files()
        self.play_sound("startup")
        
        # Менеджер мониторов - будет создан в after_login
        self.monitor_manager = None
        
        self.run()
    
    # ==================== МЕТОДЫ ПЕРЕХВАТА КОНСОЛИ ====================
    
    def _init_console_log(self):
        try:
            os.makedirs(os.path.dirname(self._console_log_path), exist_ok=True)
            if not os.path.exists(self._console_log_path):
                with open(self._console_log_path, 'w', encoding='utf-8') as f:
                    f.write(f"""
╔══════════════════════════════════════════════════════════════════╗
║                    BITOS CONSOLE LOG                            ║
╠══════════════════════════════════════════════════════════════════╣
║ Started:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
║ System:   {platform.system()} {platform.release()}
║ Python:   {platform.python_version()}
╠══════════════════════════════════════════════════════════════════╣
""")
        except:
            pass
    
    class _ConsoleRedirect:
        def __init__(self, bitos, is_error):
            self.bitos = bitos
            self.is_error = is_error
        
        def write(self, text):
            if text:
                if self.is_error:
                    self.bitos._original_stderr.write(text)
                else:
                    self.bitos._original_stdout.write(text)
                
                if text.strip():
                    with self.bitos._console_lock:
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        prefix = "[STDERR]" if self.is_error else "[STDOUT]"
                        lines = text.strip().split('\n')
                        for line in lines:
                            if line.strip():
                                entry = f"{timestamp} {prefix} {line.strip()}\n"
                                self.bitos._console_buffer.append(entry)
                                
                                if self.is_error or self._is_error_message(line):
                                    error_entry = f"""
┌─────────────────────────────────────────────────────────────────────
│ [{timestamp}] ❌ CONSOLE ERROR DETECTED
│ Source:   console_output
│ Type:     ConsoleError
│ Message:  {line.strip()[:500]}
└─────────────────────────────────────────────────────────────────────
"""
                                    try:
                                        with open(self.bitos._error_log_path, 'a', encoding='utf-8') as f:
                                            f.write(error_entry)
                                            f.flush()
                                    except:
                                        pass
        
        def _is_error_message(self, line):
            error_keywords = [
                "error", "ошибк", "exception", "исключени",
                "traceback", "failed", "не удалось",
                "invalid", "неверн", "cannot", "не мож",
                "permission", "доступ", "not found", "не найден",
                "TclError", "AttributeError", "TypeError", "ValueError",
                "KeyError", "IndexError", "FileNotFoundError",
            ]
            line_lower = line.lower()
            for keyword in error_keywords:
                if keyword.lower() in line_lower:
                    return True
            return False
        
        def flush(self):
            if self.is_error:
                self.bitos._original_stderr.flush()
            else:
                self.bitos._original_stdout.flush()
    
    def _start_console_writer(self):
        def writer():
            while self._console_running:
                time.sleep(0.3)
                if not self._console_buffer:
                    continue
                
                with self._console_lock:
                    entries = self._console_buffer.copy()
                    self._console_buffer.clear()
                
                try:
                    with open(self._console_log_path, 'a', encoding='utf-8') as f:
                        for entry in entries:
                            f.write(entry)
                        f.flush()
                except:
                    pass
        
        threading.Thread(target=writer, daemon=True, name="ConsoleWriter").start()
    
    def _stop_console_writer(self):
        self._console_running = False
        try:
            with self._console_lock:
                if self._console_buffer:
                    with open(self._console_log_path, 'a', encoding='utf-8') as f:
                        for entry in self._console_buffer:
                            f.write(entry)
                    self._console_buffer.clear()
        except:
            pass
        
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr
    
    # ==================== ИНИЦИАЛИЗАЦИЯ ПУТЕЙ ====================
    
    def _init_user_paths(self):
        home = os.path.expanduser("~")
        
        self.user_paths = {
            "home": home,
            "documents": os.path.join(home, "Documents"),
            "downloads": os.path.join(home, "Downloads"),
            "pictures": os.path.join(home, "Pictures"),
            "music": os.path.join(home, "Music"),
            "videos": os.path.join(home, "Videos"),
            "desktop": os.path.join(self.system_paths["desktop_files"], self.current_user),
            "appdata": os.path.join(home, "AppData"),
        }
        
        self.documents_path = self.user_paths["documents"]
        self.downloads_path = self.user_paths["downloads"]
        self.pictures_path = self.user_paths["pictures"]
        self.secure_path = self.user_paths["documents"]
        self.desktop_path = self.user_paths["desktop"]
        self.icons_path = self.system_paths["config"]
    
    # ==================== ЗВУКОВАЯ СИСТЕМА ====================
    
    def _create_sound_files(self):
        sounds = {
            "startup.wav": (0.5, 523, 0.7),
            "logon.wav": (0.4, 660, 0.5),
            "logoff.wav": (0.3, 392, 0.4),
            "shutdown.wav": (0.5, 330, 0.5),
            "error.wav": (0.3, 200, 0.3),
            "notification.wav": (0.2, 880, 0.3),
            "success.wav": (0.3, 660, 0.4),
            "warning.wav": (0.3, 440, 0.3),
            "usb_connect.wav": (0.3, 880, 0.3),
            "usb_disconnect.wav": (0.2, 440, 0.2),
        }
        
        for filename, params in sounds.items():
            filepath = os.path.join(self.sound_path, filename)
            if not os.path.exists(filepath):
                self._create_wav(filepath, *params)
    
    def _create_wav(self, filepath, duration, frequency, amplitude):
        try:
            import wave
            import struct
            
            sample_rate = 44100
            amplitude = int(amplitude * 20000)
            
            with wave.open(filepath, 'w') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(sample_rate)
                
                for i in range(int(duration * sample_rate)):
                    t = i / sample_rate
                    envelope = 1.0 - (t / duration) if t < duration else 0
                    value = int(amplitude * envelope * math.sin(2 * math.pi * frequency * t))
                    wav.writeframes(struct.pack('<h', value))
            return True
        except:
            return False
    
    def play_sound(self, sound_name):
        if not self.sound_enabled:
            return
        
        filename = f"{sound_name}.wav"
        filepath = os.path.join(self.sound_path, filename)
        
        if not os.path.exists(filepath):
            return
        
        try:
            if platform.system() == "Windows":
                import winsound
                winsound.PlaySound(filepath, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                try:
                    subprocess.Popen(['paplay', filepath], 
                                   stdout=subprocess.DEVNULL, 
                                   stderr=subprocess.DEVNULL)
                except:
                    try:
                        subprocess.Popen(['aplay', filepath],
                                       stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL)
                    except:
                        print('\a', end='', flush=True)
        except:
            try:
                print('\a', end='', flush=True)
            except:
                pass
    
    def play_logon(self):
        self.play_sound("logon")
    
    def play_logoff(self):
        self.play_sound("logoff")
    
    def play_shutdown(self):
        self.play_sound("shutdown")
    
    def play_error(self):
        self.play_sound("error")
    
    def play_notification(self):
        self.play_sound("notification")
    
    def play_success(self):
        self.play_sound("success")
    
    def play_warning(self):
        self.play_sound("warning")
    
    def play_usb_connect(self):
        self.play_sound("usb_connect")
    
    def play_usb_disconnect(self):
        self.play_sound("usb_disconnect")
    
    def toggle_sound(self):
        self.sound_enabled = not self.sound_enabled
        if self.sound_enabled:
            self.play_sound("notification")
        return self.sound_enabled
    
    # ==================== ФАЙЛОВАЯ СИСТЕМА ====================
    
    def initialize_filesystem(self):
        print("=" * 60)
        print("🔧 ИНИЦИАЛИЗАЦИЯ ФАЙЛОВОЙ СИСТЕМЫ BITOS")
        print("=" * 60)
        
        for name, path in self.system_paths.items():
            os.makedirs(path, exist_ok=True)
            print(f"  ✅ Создана папка: {name} -> {path}")
        
        default_desktop = os.path.join(self.system_paths["desktop_files"], self.current_user)
        os.makedirs(default_desktop, exist_ok=True)
        print(f"  ✅ Создан виртуальный рабочий стол: {default_desktop}")
        
        trash_path = os.path.join(self.system_paths["desktop_files"], ".trash")
        os.makedirs(trash_path, exist_ok=True)
        print(f"  ✅ Создана папка корзины: {trash_path}")
        
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
            config_data = {
                "version": self.version,
                "build": self.build,
                "first_boot": datetime.now().isoformat(),
                "last_boot": datetime.now().isoformat(),
                "boot_count": 1,
                "default_user": self.current_user,
                "os_name": "BITOS",
                "architecture": platform.machine(),
                "python_version": platform.python_version(),
                "use_virtual_desktop": True,
                "desktop_path": os.path.join(self.system_paths["desktop_files"], "{username}")
            }
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
            license_data = {
                "product": "BITOS",
                "version": self.version,
                "license_type": "Evaluation",
                "valid_until": "2026-12-31",
                "issued_to": self.current_user,
                "issued_date": datetime.now().isoformat(),
                "features": ["full_access", "updates", "support", "virtual_desktop"]
            }
            with open(self.system_files["license"], "w", encoding="utf-8") as f:
                json.dump(license_data, f, indent=4, ensure_ascii=False)
            print(f"  ✅ Создан license.key")
        
        if not os.path.exists(self.system_files["pin_db"]):
            default_pin_hash = hashlib.sha256("1234".encode()).hexdigest()
            with open(self.system_files["pin_db"], "w") as f:
                f.write(default_pin_hash)
            print(f"  ✅ Создан pin.hash (PIN по умолчанию: 1234)")
        
        if not os.path.exists(self.system_files["icons_db"]):
            default_icons = {
                "shortcuts": [],
                "widgets": [],
                "theme": "Базовая",
                "wallpaper": None
            }
            with open(self.system_files["icons_db"], "w", encoding="utf-8") as f:
                json.dump(default_icons, f, indent=4, ensure_ascii=False)
            print(f"  ✅ Создан icons.json")
        
        if not os.path.exists(self.system_files["users_db"]):
            users_data = {
                self.current_user: {
                    "created": datetime.now().isoformat(),
                    "last_login": None,
                    "is_admin": True,
                    "home": self.user_paths["home"],
                    "virtual_desktop": os.path.join(self.system_paths["desktop_files"], self.current_user),
                    "use_virtual_desktop": True
                }
            }
            with open(self.system_files["users_db"], "w", encoding="utf-8") as f:
                json.dump(users_data, f, indent=4, ensure_ascii=False)
            print(f"  ✅ Создан users.db")
    
    def init_log_files(self):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_headers = {
            "boot": f"╔══════════════════════════════════════════════════════════════════╗\n║                      BITOS BOOT LOG                               ║\n╠══════════════════════════════════════════════════════════════════╣\n║ Version: {self.version} ({self.build})\n║ Date: {datetime.now().strftime('%Y-%m-%d')}\n║ Time: {datetime.now().strftime('%H:%M:%S')}\n║ User: {self.current_user}\n║ Mode: Virtual Desktop (System/DesktopFile/)\n╠══════════════════════════════════════════════════════════════════╣\n",
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
        boot_info = f"\n{'='*66}\nBITOS BOOT SEQUENCE COMPLETED\n{'='*66}\nVersion:     {self.version} ({self.build})\nBoot time:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nUser:        {self.current_user}\nPython:      {platform.python_version()}\nPlatform:    {platform.system()} {platform.release()}\nMachine:     {platform.machine()}\nMode:        Virtual Desktop\nDesktop:     System/DesktopFile/{self.current_user}/\n{'='*66}\n"
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
        backup_dir = os.path.join(self.system_paths["temp"], "security_backups")
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
                license_data = {
                    "product": "BITOS",
                    "version": self.version,
                    "license_type": "Evaluation",
                    "valid_until": "2026-12-31",
                    "restored": True,
                    "restored_date": datetime.now().isoformat()
                }
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(license_data, f, indent=4)
                print(f"  🔄 Восстановлен license.key")
            elif filename == "pin.hash":
                default_pin_hash = hashlib.sha256("1234".encode()).hexdigest()
                with open(filepath, 'w') as f:
                    f.write(default_pin_hash)
                print(f"  🔄 Восстановлен pin.hash (сброшен до 1234)")
            elif filename == "icons.json":
                default_icons = {
                    "shortcuts": [],
                    "widgets": [],
                    "theme": "Базовая",
                    "wallpaper": None
                }
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(default_icons, f, indent=4, ensure_ascii=False)
                print(f"  🔄 Восстановлен icons.json")
            self.security_violations.append({
                "time": datetime.now().isoformat(),
                "file": filename,
                "backup": backup_name,
                "restored": True
            })
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
    
    # ==================== МЕТОДЫ ДЛЯ РАБОТЫ С МОНИТОРАМИ ====================
    
    def get_monitor_manager(self):
        """Получение менеджера мониторов"""
        return getattr(self, 'monitor_manager', None)
    
    # ==================== ЗАГРУЗКА ====================
    
    def boot_sequence(self):
        splash = SplashScreen()
        stages = [
            (10, "Проверка компонентов...", "Сканирование системных модулей"),
            (25, "Инициализация ядра...", "Загрузка драйверов устройств"),
            (40, "Проверка файловой системы...", "Виртуальный рабочий стол"),
            (55, "Загрузка конфигурации...", "Чтение системных настроек"),
            (70, "Проверка безопасности...", "Анализ защищенных файлов"),
            (85, "Запуск служб...", "Инициализация сервисов"),
            (95, "Подготовка интерфейса...", "Загрузка графических компонентов"),
            (100, "Готов к работе!", "Добро пожаловать в BITOS 06V6")
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
        self._init_user_paths()
        
        virtual_desktop = os.path.join(self.system_paths["desktop_files"], username)
        os.makedirs(virtual_desktop, exist_ok=True)
        print(f"[BITOS] Виртуальный рабочий стол создан: {virtual_desktop}")
        
        user_trash = os.path.join(self.system_paths["desktop_files"], ".trash", username)
        os.makedirs(user_trash, exist_ok=True)
        
        self.user_paths["desktop"] = virtual_desktop
        self.desktop_path = virtual_desktop
        
        self.security = SecurityManager(self)
        self.security.log_access(username, "LOGIN", "SUCCESS", f"Session: {self.security.session_id}")
        self.log(f"Пользователь {username} вошел в систему (виртуальный рабочий стол)")
        
        try:
            with open(self.system_files["users_db"], 'r', encoding='utf-8') as f:
                users = json.load(f)
            if username not in users:
                users[username] = {
                    "created": datetime.now().isoformat(),
                    "last_login": datetime.now().isoformat(),
                    "is_admin": False,
                    "home": self.user_paths["home"],
                    "virtual_desktop": virtual_desktop,
                    "use_virtual_desktop": True
                }
            else:
                users[username]["last_login"] = datetime.now().isoformat()
                users[username]["virtual_desktop"] = virtual_desktop
            with open(self.system_files["users_db"], 'w', encoding='utf-8') as f:
                json.dump(users, f, indent=4, ensure_ascii=False)
        except:
            pass
        
        self.play_sound("logon")
        
        desktop_root = tk.Tk()
        desktop = Desktop(desktop_root, username, self)
        
        # ============================================================
        # СОЗДАЁМ МЕНЕДЖЕР МОНИТОРОВ ПОСЛЕ СОЗДАНИЯ DESKTOP
        # ============================================================
        try:
            print("[BITOS] 🖥️ Создаём менеджер мониторов...")
            self.monitor_manager = MultiMonitorManager(self)
            
            # Устанавливаем main_desktop
            self.monitor_manager.main_desktop = desktop
            
            # Патчим desktop
            self.monitor_manager._patch_desktop(desktop)
            
            # Создаём рабочие столы для всех мониторов
            self.monitor_manager._create_extra_desktops()
            
            # ПРИНУДИТЕЛЬНО ПОКАЗЫВАЕМ ВСЕ РАБОЧИЕ СТОЛЫ
            self.monitor_manager.show_all_desktops()
            
            # ДИАГНОСТИКА
            self.monitor_manager.debug_windows()
            
            print("[BITOS] ✅ Менеджер мониторов инициализирован и рабочие столы созданы")
        except Exception as e:
            print(f"[BITOS] ⚠️ Ошибка инициализации менеджера мониторов: {e}")
            import traceback
            traceback.print_exc()
            self.monitor_manager = None
        
        self.autosafe = AutoSafe(self, desktop)
        
        def on_desktop_close():
            self.input_blocker.stop_blocking()
            self._stop_console_writer()
            if self.monitor_manager:
                try:
                    self.monitor_manager.stop()
                except:
                    pass
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
        
        # Храним хуки для отключения
        self.hooks = []
        self.blocked_keys = []
        
        if not self.available:
            print("⚠️ InputBlocker: библиотека keyboard не найдена")
            print("   Установите: pip install keyboard")
    
    def start_blocking(self):
        if not self.available:
            print("⚠️ InputBlocker: невозможно запустить - keyboard не установлен")
            return
        
        try:
            # Очищаем старые хуки
            self.stop_blocking()
            
            # Список системных клавиш для блокировки
            self.blocked_keys = [
                'win', 'left windows', 'right windows',
                'alt+tab', 'alt+f4', 'ctrl+esc',
                'win+d', 'win+r', 'win+l', 'win+e',
                'ctrl+shift+esc', 'ctrl+alt+del',
                'f4', 'alt', 'ctrl', 'esc', 'tab'
            ]
            
            # Блокируем системные клавиши
            for key in self.blocked_keys:
                try:
                    # Добавляем хук, который перехватывает и отменяет событие
                    keyboard.add_hotkey(key, lambda: None, suppress=True)
                    self.hooks.append(key)
                except Exception as e:
                    print(f"⚠️ Не удалось заблокировать {key}: {e}")
            
            # Вешаем обработчики на CapsLock и Tab для подсчета
            # Используем add_hotkey вместо on_press_key для более надежной работы
            keyboard.add_hotkey('caps lock', self._on_caps_press, suppress=False)
            self.hooks.append('caps lock')
            
            keyboard.add_hotkey('tab', self._on_tab_press, suppress=False)
            self.hooks.append('tab')
            
            self.blocking = True
            print("🔒 InputBlocker: Активирован. Чит-код: 5xCapsLock + 2xTab")
            print("   (Нажмите CapsLock 5 раз, затем Tab 2 раза для разблокировки)")
            
        except Exception as e:
            print(f"⚠️ Ошибка InputBlocker: {e}")
            self.blocking = False
    
    def _on_caps_press(self):
        """Обработчик нажатия CapsLock"""
        if not self.blocking:
            return
        self.caps_count += 1
        # Не сбрасываем tab_count, чтобы можно было нажимать в любом порядке
        print(f"🔑 CapsLock: {self.caps_count}/{self.TARGET_CAPS}")
        self._check_unlock()
    
    def _on_tab_press(self):
        """Обработчик нажатия Tab"""
        if not self.blocking:
            return
        self.tab_count += 1
        print(f"🔑 Tab: {self.tab_count}/{self.TARGET_TAB}")
        self._check_unlock()
    
    def _check_unlock(self):
        """Проверка чит-кода"""
        if self.caps_count >= self.TARGET_CAPS and self.tab_count >= self.TARGET_TAB:
            print("✅ ЧИТ-КОД АКТИВИРОВАН! Клавиатура разблокирована.")
            self.stop_blocking()
    
    def stop_blocking(self):
        """Остановка блокировки"""
        if not self.available:
            return
        
        try:
            # Удаляем все хуки
            keyboard.unhook_all()
            self.hooks.clear()
            self.blocking = False
            
            # Сбрасываем счетчики
            self.caps_count = 0
            self.tab_count = 0
            
            print("🔓 InputBlocker: Разблокировано")
        except Exception as e:
            print(f"⚠️ Ошибка при разблокировке: {e}")
    
    def is_active(self):
        return self.blocking
    
    def get_status(self):
        """Получить статус блокировки"""
        if self.blocking:
            return f"🔒 Заблокировано (Caps: {self.caps_count}/{self.TARGET_CAPS}, Tab: {self.tab_count}/{self.TARGET_TAB})"
        else:
            return "🔓 Разблокировано"

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
    """Центр уведомлений с историей, всплывающими сообщениями"""
    
    def __init__(self, parent, bitos):
        self.parent = parent
        self.bitos = bitos
        self.notifications = []
        self.max_notifications = 50
        self.active_popups = []
        self.popup_spacing = 110
        
        # Настройки звука - используем звуковую систему BITOS
        self.sound_enabled = True
        
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
    
    def add_notification(self, title, message, icon="🔔", category="system", duration=5000, play_sound=True):
        """Добавляет новое уведомление с возможностью звукового оповещения"""
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
        
        # Воспроизводим звук через звуковую систему BITOS
        if play_sound and self.sound_enabled and self.bitos:
            # ПРОВЕРЯЕМ СООБЩЕНИЕ - ЭТО ФЛЕШКА?
            sound_type = self._detect_sound_from_message(title, message)
            self.bitos.play_sound(sound_type)
        
        self.show_popup(notification, duration)
    
    def _detect_sound_from_message(self, title, message):
        """Определяет какой звук воспроизвести по тексту сообщения"""
        # Объединяем заголовок и сообщение для поиска
        full_text = f"{title} {message}".lower()
        
        # Проверяем ключевые слова
        if "флешка подключена" in full_text or "usb connect" in full_text or "подключено новое устройство" in full_text:
            return "usb_connect"
        elif "флешка отключена" in full_text or "usb disconnect" in full_text or "устройство было отключено" in full_text:
            return "usb_disconnect"
        elif "ошибк" in full_text or "error" in full_text:
            return "error"
        elif "предупреждени" in full_text or "warning" in full_text:
            return "warning"
        elif "успех" in full_text or "success" in full_text:
            return "success"
        else:
            return "notification"
    
    def show_popup(self, notification, duration=5000):
        """Показывает всплывающее уведомление"""
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
        
        # Анимация появления
        popup.attributes('-alpha', 0)
        self._fade_in(popup)
        
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
        
        # Ограничиваем длину сообщения
        display_message = notification['message'][:100]
        if len(notification['message']) > 100:
            display_message += "..."
        
        tk.Label(msg_frame, text=display_message, font=('Segoe UI', 9),
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
    
    def _fade_in(self, window, alpha=0):
        """Анимация появления окна"""
        if alpha < 1.0 and window.winfo_exists():
            alpha += 0.1
            window.attributes('-alpha', alpha)
            window.after(20, lambda: self._fade_in(window, alpha))
    
    def close_popup(self, popup):
        """Закрывает всплывающее уведомление с анимацией"""
        def fade_out(alpha=1.0):
            if alpha > 0 and popup.winfo_exists():
                alpha -= 0.1
                popup.attributes('-alpha', alpha)
                popup.after(20, lambda: fade_out(alpha))
            else:
                if popup in self.active_popups:
                    self.active_popups.remove(popup)
                try:
                    if popup.winfo_exists():
                        popup.destroy()
                except:
                    pass
                self.reposition_popups()
        
        fade_out()
    
    def reposition_popups(self):
        """Перемещает все активные уведомления вверх"""
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
    
    def toggle_sound(self):
        """Включить/выключить звук уведомлений"""
        self.sound_enabled = not self.sound_enabled
        status = "включены" if self.sound_enabled else "выключены"
        
        # Показываем уведомление об изменении настроек
        self.add_notification(
            "🔊 Звук уведомлений",
            f"Звуковые оповещения {status}",
            icon="🔊",
            duration=2000,
            play_sound=False
        )
        return self.sound_enabled
    
    def test_sound(self):
        """Тест звука уведомления"""
        if self.bitos:
            self.bitos.play_sound("notification")
        self.add_notification(
            "🔊 Тест звука",
            "Если вы слышите этот звук, уведомления работают корректно",
            icon="🔊",
            duration=3000,
            play_sound=False
        )

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

class ErrorManager:
    """
    Расширенный менеджер ошибок BITOS
    - Перехватывает ВСЕ ошибки и исключения
    - Сохраняет ВСЁ что выводится в консоль (console.log)
    - Отслеживает состояние приложения в реальном времени
    - Автоматически исправляет ошибки
    - Ведёт полный лог всех событий
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance
    
    def __init__(self, bitos_instance=None):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        # Основные параметры
        self.bitos = bitos_instance
        self.is_running = True
        self.start_time = datetime.now()
        
        # Счётчики
        self.error_count = 0
        self.fixed_count = 0
        self.unfixable_count = 0
        self.warning_count = 0
        self.info_count = 0
        
        # Очередь для асинхронной записи
        self._log_queue = queue.Queue()
        self._log_thread = None
        
        # Буфер для ошибок до инициализации
        self._buffer = []
        
        # Перехват консольного вывода
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        self._console_buffer = []
        
        # Инициализация путей
        self._init_paths()
        
        # Инициализация логов
        self._init_logs()
        
        # Перехват консоли
        self._redirect_console()
        
        # Патчим всё
        self._patch_everything()
        
        # Запускаем мониторинг
        self._start_monitoring()
        
        # Запускаем поток записи логов
        self._start_log_writer()
        
        # Записываем информацию о старте
        self._log_startup()
        
        print(f"[ErrorManager] ✅ Инициализирован")
        print(f"[ErrorManager] 📁 Логи: {self.logs_path}")
        print(f"[ErrorManager] 📄 console.log: {self.console_log_path}")
        print(f"[ErrorManager] 📄 error.log: {self.error_log_path}")
    
    def _init_paths(self):
        """Инициализация путей к логам"""
        if self.bitos and hasattr(self.bitos, 'system_paths'):
            self.logs_path = self.bitos.system_paths.get("logs")
        
        if not self.logs_path:
            base_path = os.path.dirname(os.path.abspath(__file__))
            self.logs_path = os.path.join(base_path, "System", "Logs")
        
        os.makedirs(self.logs_path, exist_ok=True)
        
        # Пути к лог-файлам
        self.error_log_path = os.path.join(self.logs_path, "error.log")
        self.fixed_log_path = os.path.join(self.logs_path, "fixed_errors.log")
        self.crash_log_path = os.path.join(self.logs_path, "crash_reports.log")
        self.debug_log_path = os.path.join(self.logs_path, "debug.log")
        self.console_log_path = os.path.join(self.logs_path, "console.log")
        self.event_log_path = os.path.join(self.logs_path, "events.log")
        self.warning_log_path = os.path.join(self.logs_path, "warnings.log")
        self.system_log_path = os.path.join(self.logs_path, "system.log")
        
        # Создаём все директории
        for path in [self.logs_path]:
            os.makedirs(path, exist_ok=True)
    
    def _init_logs(self):
        """Инициализация всех лог-файлов"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Заголовок для всех логов
        header = f"""
╔══════════════════════════════════════════════════════════════════╗
║              BITOS ERROR MANAGER v2.0                           ║
╠══════════════════════════════════════════════════════════════════╣
║ Started:  {timestamp}
║ System:   {platform.system()} {platform.release()}
║ Python:   {platform.python_version()}
║ BITOS:    {self.bitos.version if self.bitos and hasattr(self.bitos, 'version') else 'Unknown'}
║ PID:      {os.getpid()}
╠══════════════════════════════════════════════════════════════════╣
"""
        
        # Создаём все лог-файлы с заголовками
        log_files = {
            self.error_log_path: header + "║ ERROR LOG\n",
            self.fixed_log_path: header.replace("ERROR", "FIXED") + "║ FIXED ERRORS LOG\n",
            self.crash_log_path: header.replace("ERROR", "CRASH") + "║ CRASH REPORTS LOG\n",
            self.debug_log_path: header.replace("ERROR", "DEBUG") + "║ DEBUG LOG\n",
            self.console_log_path: header.replace("ERROR", "CONSOLE") + "║ CONSOLE OUTPUT LOG\n",
            self.event_log_path: header.replace("ERROR", "EVENT") + "║ EVENT LOG\n",
            self.warning_log_path: header.replace("ERROR", "WARNING") + "║ WARNING LOG\n",
            self.system_log_path: header.replace("ERROR", "SYSTEM") + "║ SYSTEM LOG\n",
        }
        
        for path, content in log_files.items():
            try:
                if not os.path.exists(path) or os.path.getsize(path) == 0:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(content + "\n")
            except:
                pass
    
    def _redirect_console(self):
        """Перехват всего консольного вывода"""
        class ConsoleRedirect:
            def __init__(self, manager, is_error=False):
                self.manager = manager
                self.is_error = is_error
                self.buffer = []
            
            def write(self, text):
                if text and text.strip():
                    # Сохраняем в буфер
                    self.buffer.append(text)
                    # Пишем в оригинальный вывод
                    if self.is_error:
                        self.manager._original_stderr.write(text)
                    else:
                        self.manager._original_stdout.write(text)
                    # Сохраняем в лог
                    self.manager._log_console(text, is_error=self.is_error)
                    # Проверяем на наличие ошибок
                    if self.is_error or "error" in text.lower() or "exception" in text.lower():
                        self.manager._detect_error_from_console(text)
            
            def flush(self):
                if self.is_error:
                    self.manager._original_stderr.flush()
                else:
                    self.manager._original_stdout.flush()
        
        # Перенаправляем вывод
        sys.stdout = ConsoleRedirect(self, is_error=False)
        sys.stderr = ConsoleRedirect(self, is_error=True)
    
    def _log_console(self, text, is_error=False):
        """Запись консольного вывода в лог"""
        if not text or not text.strip():
            return
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        prefix = "[STDERR]" if is_error else "[STDOUT]"
        
        entry = f"{timestamp} {prefix} {text.strip()}\n"
        
        # Добавляем в очередь
        try:
            self._log_queue.put(('console', entry))
        except:
            pass
    
    def _detect_error_from_console(self, text):
        """Обнаружение ошибок в консольном выводе"""
        if "Traceback" in text or "Error" in text or "Exception" in text:
            # Это похоже на ошибку
            self.error_count += 1
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            entry = f"""
┌─────────────────────────────────────────────────────────────────────
│ [{timestamp}] ⚠️ ОБНАРУЖЕНА ОШИБКА В КОНСОЛИ
│ Message: {text.strip()[:200]}
│ Источник: консольный вывод
└─────────────────────────────────────────────────────────────────────
"""
            try:
                with open(self.error_log_path, 'a', encoding='utf-8') as f:
                    f.write(entry)
            except:
                pass
    
    def _patch_everything(self):
        """Патчинг всех компонентов для перехвата ошибок"""
        self._patch_tkinter()
        self._patch_threading()
        self._patch_functions()
    
    def _patch_tkinter(self):
        """Патчинг tkinter для перехвата ошибок"""
        try:
            import tkinter as tk
            
            # Сохраняем оригинальные методы
            self._original_report_callback = tk.Tk.report_callback_exception
            self._original_after = tk.Misc.after
            self._original_destroy = tk.Misc.destroy
            
            # Создаём новый обработчик
            def custom_report_callback(self_widget, exc, val, tb):
                """Кастомный обработчик ошибок tkinter"""
                error_msg = f"tkinter error: {exc.__name__}: {val}"
                self._handle_exception(exc, val, tb, source="tkinter")
                
                # Вызываем оригинальный обработчик если есть
                if self._original_report_callback:
                    try:
                        self._original_report_callback(self_widget, exc, val, tb)
                    except:
                        pass
            
            # Применяем патч
            tk.Tk.report_callback_exception = custom_report_callback
            
            # Патчим after для безопасности
            def safe_after(self_widget, ms, func=None, *args):
                if not self_widget or not self_widget.winfo_exists():
                    return None
                try:
                    return self._original_after(self_widget, ms, func, *args)
                except tk.TclError as e:
                    self._log_error("TclError", str(e), traceback.format_exc(), source="after")
                    return None
            
            tk.Misc.after = safe_after
            
            # Патчим destroy
            def safe_destroy(self_widget):
                try:
                    if not self_widget or not self_widget.winfo_exists():
                        return
                    self._original_destroy(self_widget)
                except tk.TclError:
                    pass  # Игнорируем ошибки удаления уже удалённых виджетов
            
            tk.Misc.destroy = safe_destroy
            
        except Exception as e:
            print(f"[ErrorManager] ⚠️ Не удалось пропатчить tkinter: {e}")
    
    def _patch_threading(self):
        """Патчинг threading для перехвата ошибок в потоках"""
        try:
            original_thread_run = threading.Thread.run
            
            def safe_thread_run(self):
                try:
                    original_thread_run(self)
                except Exception as e:
                    self._handle_exception(
                        type(e), e, traceback.extract_tb(e.__traceback__),
                        source=f"thread:{self.name}"
                    )
            
            threading.Thread.run = safe_thread_run
            
        except Exception as e:
            print(f"[ErrorManager] ⚠️ Не удалось пропатчить threading: {e}")
    
    def _patch_functions(self):
        """Патчинг функций с декоратором @safe_call"""
        pass  # Реализовано через декоратор
    
    def _start_monitoring(self):
        """Запуск мониторинга"""
        # Перехватываем глобальные исключения
        sys.excepthook = self._global_exception_handler
        
        # Запускаем фоновый мониторинг
        self._start_background_monitor()
    
    def _start_background_monitor(self):
        """Фоновый мониторинг состояния системы"""
        def monitor():
            while self.is_running:
                try:
                    # Проверяем состояние каждые 5 секунд
                    time.sleep(5)
                    
                    # Проверяем наличие незакрытых окон
                    self._check_windows()
                    
                    # Проверяем состояние памяти
                    self._check_memory()
                    
                    # Проверяем состояние потоков
                    self._check_threads()
                    
                except Exception as e:
                    self._log_error("MonitorError", str(e), traceback.format_exc())
        
        thread = threading.Thread(target=monitor, daemon=True, name="ErrorMonitor")
        thread.start()
    
    def _check_windows(self):
        """Проверка состояния окон"""
        try:
            import tkinter as tk
            root = tk._default_root
            if root:
                # Проверяем дочерние окна
                for child in root.winfo_children():
                    try:
                        if not child.winfo_exists():
                            self._log_warning("WindowCheck", f"Обнаружено несуществующее окно: {child}")
                    except:
                        pass
        except:
            pass
    
    def _check_memory(self):
        """Проверка памяти"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                self._log_warning("MemoryCheck", f"Высокое использование памяти: {memory.percent}%")
        except:
            pass
    
    def _check_threads(self):
        """Проверка потоков"""
        try:
            threads = threading.enumerate()
            if len(threads) > 100:
                self._log_warning("ThreadCheck", f"Много потоков: {len(threads)}")
        except:
            pass
    
    def _global_exception_handler(self, exc_type, exc_value, exc_traceback):
        """Глобальный обработчик исключений"""
        self._handle_exception(exc_type, exc_value, exc_traceback, source="global")
        # Вызываем стандартный обработчик
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    
    def _handle_exception(self, exc_type, exc_value, exc_traceback, source="unknown"):
        """Обработка исключения"""
        error_name = exc_type.__name__ if hasattr(exc_type, '__name__') else str(exc_type)
        error_message = str(exc_value) if exc_value else "Unknown error"
        
        # Получаем трассировку
        tb_str = ""
        if exc_traceback:
            tb_str = ''.join(traceback.format_tb(exc_traceback))
        
        # Логируем ошибку
        self._log_error(error_name, error_message, tb_str, source)
        
        # Пытаемся исправить
        fix = self._try_fix(error_name, error_message, exc_value)
        if fix:
            self.fixed_count += 1
            self._log_fixed(error_name, error_message, fix)
        else:
            self.unfixable_count += 1
        
        return fix
    
    def _log_error(self, error_name, error_message, traceback_str="", source="unknown"):
        """Запись ошибки в лог"""
        with self._lock:
            self.error_count += 1
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            entry = f"""
┌─────────────────────────────────────────────────────────────────────
│ [{timestamp}] ❌ ERROR #{self.error_count}
│ Source:   {source}
│ Type:     {error_name}
│ Message:  {error_message[:200]}
"""
            if traceback_str:
                entry += "│ Traceback:\n"
                for line in traceback_str.split('\n')[-10:]:
                    if line.strip():
                        entry += f"│   {line}\n"
            entry += "└─────────────────────────────────────────────────────────────────────\n"
            
            # Добавляем в очередь
            try:
                self._log_queue.put(('error', entry))
            except:
                pass
    
    def _log_fixed(self, error_name, error_message, fix_description):
        """Запись исправления"""
        with self._lock:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            entry = f"""
┌─────────────────────────────────────────────────────────────────────
│ [{timestamp}] ✅ FIXED #{self.fixed_count}
│ Type:     {error_name}
│ Message:  {error_message[:200]}
│ Fix:      {fix_description}
└─────────────────────────────────────────────────────────────────────
"""
            try:
                self._log_queue.put(('fixed', entry))
            except:
                pass
    
    def _log_warning(self, warning_type, message):
        """Запись предупреждения"""
        with self._lock:
            self.warning_count += 1
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            entry = f"[{timestamp}] ⚠️ WARNING #{self.warning_count} [{warning_type}] {message}\n"
            
            try:
                self._log_queue.put(('warning', entry))
            except:
                pass
    
    def _log_info(self, message):
        """Запись информационного сообщения"""
        with self._lock:
            self.info_count += 1
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            entry = f"[{timestamp}] ℹ️ INFO #{self.info_count} {message}\n"
            
            try:
                self._log_queue.put(('info', entry))
            except:
                pass
    
    def _log_startup(self):
        """Запись информации о старте"""
        self._log_info(f"BITOS запущен. Версия: {self.bitos.version if self.bitos else 'Unknown'}")
        self._log_info(f"Пользователь: {self.bitos.current_user if self.bitos else 'Unknown'}")
        self._log_info(f"Путь: {os.getcwd()}")
    
    def _try_fix(self, error_name, error_message, exc_value):
        """Попытка исправить ошибку"""
        # Специальные обработчики
        fixes = {
            "invalid command name": lambda: "🔄 Пересоздание команды",
            "application has been destroyed": lambda: "🔄 Очистка уничтоженных виджетов",
            "can't invoke": lambda: "🔄 Обновление ссылок на виджеты",
            "window was deleted": lambda: "🔄 Удаление ссылок на уничтоженные окна",
            "NoneType has no attribute": lambda: "🔧 Добавлена проверка на None",
            "not found": lambda: "📁 Создание отсутствующего элемента",
            "permission denied": lambda: "🔑 Запрос прав администратора",
        }
        
        for key, fix_func in fixes.items():
            if key.lower() in error_message.lower() or key.lower() in error_name.lower():
                return fix_func()
        
        return None
    
    def _start_log_writer(self):
        """Запуск потока для записи логов"""
        def writer():
            while self.is_running:
                try:
                    # Получаем запись из очереди с таймаутом
                    try:
                        log_type, content = self._log_queue.get(timeout=1)
                    except queue.Empty:
                        continue
                    
                    # Определяем файл для записи
                    file_map = {
                        'console': self.console_log_path,
                        'error': self.error_log_path,
                        'fixed': self.fixed_log_path,
                        'warning': self.warning_log_path,
                        'info': self.event_log_path,
                        'system': self.system_log_path,
                        'debug': self.debug_log_path,
                    }
                    
                    file_path = file_map.get(log_type, self.debug_log_path)
                    
                    # Записываем
                    try:
                        with open(file_path, 'a', encoding='utf-8') as f:
                            f.write(content)
                            f.flush()
                    except:
                        pass
                    
                except Exception as e:
                    # Если не можем записать, выводим в консоль
                    print(f"[ErrorManager] Ошибка записи лога: {e}")
        
        self._log_thread = threading.Thread(target=writer, daemon=True, name="LogWriter")
        self._log_thread.start()
    
    # ==================== ПУБЛИЧНЫЕ МЕТОДЫ ====================
    
    def log_error(self, error_type, message, traceback_str=""):
        """Ручное логирование ошибки"""
        self._log_error(error_type, message, traceback_str, source="manual")
    
    def log_warning(self, warning_type, message):
        """Ручное логирование предупреждения"""
        self._log_warning(warning_type, message)
    
    def log_info(self, message):
        """Ручное логирование информации"""
        self._log_info(message)
    
    def log_system(self, message):
        """Запись системного сообщения"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        entry = f"[{timestamp}] 🖥️ {message}\n"
        try:
            self._log_queue.put(('system', entry))
        except:
            pass
    
    def log_debug(self, message):
        """Запись отладочного сообщения"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        entry = f"[{timestamp}] 🐛 DEBUG: {message}\n"
        try:
            self._log_queue.put(('debug', entry))
        except:
            pass
    
    def get_statistics(self):
        """Получение статистики"""
        return {
            'total_errors': self.error_count,
            'fixed_errors': self.fixed_count,
            'unfixable_errors': self.unfixable_count,
            'warnings': self.warning_count,
            'info_messages': self.info_count,
            'fix_rate': f"{(self.fixed_count / max(1, self.error_count) * 100):.1f}%",
            'uptime': str(datetime.now() - self.start_time),
            'log_files': {
                'error': os.path.getsize(self.error_log_path) if os.path.exists(self.error_log_path) else 0,
                'console': os.path.getsize(self.console_log_path) if os.path.exists(self.console_log_path) else 0,
                'events': os.path.getsize(self.event_log_path) if os.path.exists(self.event_log_path) else 0,
            }
        }
    
    def show_logs_dialog(self, parent=None):
        """Показать диалог с логами"""
        if not parent:
            parent = tk._default_root
        
        if not parent:
            parent = tk.Tk()
            parent.withdraw()
        
        dialog = tk.Toplevel(parent)
        dialog.title("📋 Журналы BITOS")
        dialog.geometry("900x600")
        dialog.transient(parent)
        dialog.configure(bg='#F5F7FA')
        
        # Центрируем
        x = (dialog.winfo_screenwidth() - 900) // 2
        y = (dialog.winfo_screenheight() - 600) // 2
        dialog.geometry(f'+{x}+{y}')
        
        # Заголовок
        header = tk.Frame(dialog, bg='#2C3E50', height=50)
        header.pack(fill=tk.X)
        tk.Label(header, text="📋 Журналы BITOS", bg='#2C3E50', fg='white',
                font=('Segoe UI', 14, 'bold')).pack(pady=10)
        
        # Вкладки
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Статистика
        stats = self.get_statistics()
        stats_frame = ttk.Frame(notebook)
        notebook.add(stats_frame, text="📊 Статистика")
        
        stats_text = f"""
╔══════════════════════════════════════════════════════════════════╗
║                    СТАТИСТИКА ОШИБОК                            ║
╠══════════════════════════════════════════════════════════════════╣
║ Всего ошибок:     {stats['total_errors']}
║ Исправлено:       {stats['fixed_errors']}
║ Не исправлено:    {stats['unfixable_errors']}
║ Эффективность:    {stats['fix_rate']}
║ Предупреждений:   {stats['warnings']}
║ Информационных:   {stats['info_messages']}
║ Время работы:     {stats['uptime']}
╠══════════════════════════════════════════════════════════════════╣
║ Размеры логов:                                                 ║
║ error.log:        {stats['log_files']['error'] / 1024:.1f} KB
║ console.log:      {stats['log_files']['console'] / 1024:.1f} KB
║ events.log:       {stats['log_files']['events'] / 1024:.1f} KB
╚══════════════════════════════════════════════════════════════════╝
"""
        tk.Label(stats_frame, text=stats_text, bg='white', fg='#2C3E50',
                font=('Consolas', 11), justify='left').pack(padx=20, pady=20)
        
        # Вкладки для логов
        log_files = {
            'error.log': self.error_log_path,
            'console.log': self.console_log_path,
            'events.log': self.event_log_path,
            'warnings.log': self.warning_log_path,
            'fixed_errors.log': self.fixed_log_path,
            'system.log': self.system_log_path,
            'debug.log': self.debug_log_path,
        }
        
        for name, path in log_files.items():
            if os.path.exists(path):
                frame = ttk.Frame(notebook)
                notebook.add(frame, text=name)
                
                text_area = scrolledtext.ScrolledText(frame, font=('Consolas', 9),
                                                      bg='#1E1E1E', fg='#00FF00',
                                                      wrap=tk.WORD)
                text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
                
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = content.split('\n')
                        if len(lines) > 500:
                            lines = lines[-500:]
                        text_area.insert('1.0', '\n'.join(lines))
                except:
                    text_area.insert('1.0', f"Не удалось прочитать {name}")
                
                text_area.config(state='disabled')
        
        # Кнопка закрытия
        btn_frame = tk.Frame(dialog, bg='#F5F7FA')
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(btn_frame, text="🔄 Обновить", bg='#3498DB', fg='white',
                 font=('Segoe UI', 10), bd=0, padx=20, pady=8,
                 command=lambda: self._refresh_logs_dialog(dialog, notebook)).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="🗑 Очистить логи", bg='#E74C3C', fg='white',
                 font=('Segoe UI', 10), bd=0, padx=20, pady=8,
                 command=lambda: self._clear_all_logs()).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="Закрыть", bg='#95A5A6', fg='white',
                 font=('Segoe UI', 10), bd=0, padx=20, pady=8,
                 command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def _refresh_logs_dialog(self, dialog, notebook):
        """Обновление диалога с логами"""
        dialog.destroy()
        self.show_logs_dialog(dialog.master)
    
    def _clear_all_logs(self):
        """Очистка всех логов"""
        if not messagebox.askyesno("Очистка", "Очистить все логи?"):
            return
        
        log_paths = [
            self.error_log_path,
            self.fixed_log_path,
            self.crash_log_path,
            self.debug_log_path,
            self.console_log_path,
            self.event_log_path,
            self.warning_log_path,
            self.system_log_path,
        ]
        
        for path in log_paths:
            try:
                if os.path.exists(path):
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write("")
            except:
                pass
        
        # Сбрасываем счётчики
        self.error_count = 0
        self.fixed_count = 0
        self.unfixable_count = 0
        self.warning_count = 0
        self.info_count = 0
        
        # Пересоздаём логи
        self._init_logs()
        
        messagebox.showinfo("Успех", "Все логи очищены")
    
    def stop(self):
        """Остановка менеджера"""
        self.is_running = False
        
        # Восстанавливаем вывод
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr
        
        # Восстанавливаем tkinter
        try:
            import tkinter as tk
            if hasattr(self, '_original_report_callback'):
                tk.Tk.report_callback_exception = self._original_report_callback
        except:
            pass
        
        # Восстанавливаем threading
        try:
            threading.Thread.run = self._original_thread_run
        except:
            pass
        
        print("[ErrorManager] ⏹️ Остановлен")
    
    def __del__(self):
        """Деструктор"""
        try:
            self.stop()
        except:
            pass


# ==================== ДЕКОРАТОР ДЛЯ БЕЗОПАСНОГО ВЫЗОВА ====================

def safe_call(func):
    """Декоратор для безопасного вызова функции с логированием ошибок"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Получаем менеджер ошибок
            error_manager = None
            for arg in args:
                if hasattr(arg, 'error_manager'):
                    error_manager = arg.error_manager
                    break
                if hasattr(arg, 'bitos') and hasattr(arg.bitos, 'error_manager'):
                    error_manager = arg.bitos.error_manager
                    break
            
            if not error_manager:
                # Пытаемся найти глобальный экземпляр
                try:
                    error_manager = ErrorManager._instance
                except:
                    pass
            
            if error_manager:
                error_manager.log_error(
                    func.__name__,
                    str(e),
                    traceback.format_exc()
                )
            else:
                print(f"[{func.__name__}] Ошибка: {e}")
            
            return None
    return wrapper


# ==================== ФУНКЦИЯ ИНИЦИАЛИЗАЦИИ ====================

def init_error_manager(bitos_instance=None):
    """
    Инициализация менеджера ошибок
    
    Args:
        bitos_instance: Экземпляр BITOS
    
    Returns:
        ErrorManager: Экземпляр менеджера ошибок
    """
    manager = ErrorManager(bitos_instance)
    
    # Если есть BITOS, добавляем методы
    if bitos_instance:
        bitos_instance.error_manager = manager
        bitos_instance.show_errors = lambda: manager.show_logs_dialog()
        bitos_instance.clear_errors = manager._clear_all_logs
        bitos_instance.log_info = manager.log_info
        bitos_instance.log_warning = manager.log_warning
        bitos_instance.log_error = manager.log_error
    
    return manager

# ==================== КЛАСС: SoundClickPlayer ====================
class SoundClickPlayer:
    """
    Проигрыватель звука с ПРЯМЫМ изменением системной громкости через WinAPI
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance
    
    def __init__(self, bitos=None):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        self.bitos = bitos
        self.enabled = False
        self._playing = False
        self._running = False
        
        # Громкость из файла конфигурации
        self.volume = self._load_volume_from_config()
        self._last_known_volume = self.volume
        
        # Поток для мониторинга громкости
        self._monitor_thread = None
        
        # Инициализация WinAPI
        self._init_winapi_volume()
        
        print(f"[SoundClickPlayer] ✅ Инициализирован (громкость {self.volume}%)")
    
    def _init_winapi_volume(self):
        """Инициализация WinAPI для контроля громкости"""
        import ctypes
        from ctypes import wintypes
        
        self.ctypes = ctypes
        self.wintypes = wintypes
        
        # Загружаем user32.dll
        self.user32 = ctypes.windll.user32
        
        # Константы для сообщений
        self.WM_APPCOMMAND = 0x0319
        self.APPCOMMAND_VOLUME_UP = 0x0A0000
        self.APPCOMMAND_VOLUME_DOWN = 0x090000
        self.APPCOMMAND_VOLUME_MUTE = 0x080000
        
        # Получаем handle рабочего стола
        self.hwnd = self.user32.GetDesktopWindow()
        
        print("[SoundClickPlayer] 🎵 WinAPI инициализирован")
    
    def _load_volume_from_config(self):
        """Загрузка громкости из файла System/Config/volume.cfg"""
        config_path = os.path.join('System', 'Config', 'volume.cfg')
        default_volume = 30
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    try:
                        volume = int(content)
                        if 0 <= volume <= 100:
                            return volume
                        else:
                            return default_volume
                    except ValueError:
                        return default_volume
            else:
                self._save_volume_to_config(default_volume)
                return default_volume
        except:
            return default_volume
    
    def _save_volume_to_config(self, volume):
        """Сохранение громкости в файл"""
        config_path = os.path.join('System', 'Config', 'volume.cfg')
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(str(volume))
            return True
        except:
            return False
    
    def _get_current_volume(self):
        """Получение текущей громкости через реестр"""
        try:
            import winreg
            
            # Открываем ключ реестра
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Internet Explorer\Main",
                0,
                winreg.KEY_READ
            )
            
            # Пробуем получить громкость (может не работать)
            try:
                value, _ = winreg.QueryValueEx(key, "Volume")
                winreg.CloseKey(key)
                return int(value)
            except:
                winreg.CloseKey(key)
                return 50
                
        except:
            return 50
    
    def _send_volume_command(self, command):
        """Отправка команды громкости через WinAPI"""
        try:
            # Отправляем сообщение рабочему столу
            self.user32.SendMessageW(
                self.hwnd,
                self.WM_APPCOMMAND,
                0,
                command
            )
            return True
        except Exception as e:
            print(f"[SoundClickPlayer] ⚠️ Ошибка отправки команды: {e}")
            return False
    
    def _set_system_volume(self, target_volume):
        """Установка системной громкости через WinAPI"""
        import time
        
        # Получаем текущую громкость
        current = self._get_current_volume()
        
        if target_volume == current:
            return
        
        # Определяем направление и количество нажатий
        if target_volume > current:
            command = self.APPCOMMAND_VOLUME_UP
            steps = (target_volume - current) // 2  # ~2% за нажатие
        else:
            command = self.APPCOMMAND_VOLUME_DOWN
            steps = (current - target_volume) // 2
        
        if steps <= 0:
            steps = 1
        
        print(f"[SoundClickPlayer] 🔊 {current}% -> {target_volume}% ({steps} шагов)")
        
        # Отправляем команды
        for i in range(steps):
            self._send_volume_command(command)
            time.sleep(0.05)  # Задержка между нажатиями
    
    def set_volume(self, volume):
        """Установка громкости"""
        try:
            volume = int(volume)
            if 0 <= volume <= 100:
                old_volume = self.volume
                self.volume = volume
                self._last_known_volume = volume
                self._save_volume_to_config(volume)
                
                # Устанавливаем системную громкость
                self._set_system_volume(volume)
                
                print(f"[SoundClickPlayer] 🔊 Громкость: {old_volume}% -> {volume}%")
                return True
            return False
        except:
            return False
    
    def enable(self):
        """Включение"""
        if not self.enabled:
            self.enabled = True
            
            # Устанавливаем громкость
            self._set_system_volume(self.volume)
            
            # Запускаем мониторинг
            self._start_volume_monitor()
            
            print(f"[SoundClickPlayer] 🔊 ВКЛЮЧЁН (громкость: {self.volume}%)")
            return True
        return True
    
    def disable(self):
        """Выключение"""
        if self.enabled:
            self.enabled = False
            self._stop_volume_monitor()
            print("[SoundClickPlayer] 🔇 ВЫКЛЮЧЁН")
            return True
        return True
    
    def toggle(self):
        """Переключение"""
        if self.enabled:
            self.disable()
        else:
            self.enable()
        return self.enabled
    
    def _check_volume_change(self):
        """Проверка изменения громкости"""
        try:
            current_volume = self._load_volume_from_config()
            
            if current_volume != self._last_known_volume:
                old_volume = self.volume
                self.volume = current_volume
                self._last_known_volume = current_volume
                
                # Меняем системную громкость
                self._set_system_volume(self.volume)
                
                print(f"[SoundClickPlayer] 📁 Громкость: {old_volume}% -> {self.volume}%")
                return True
            return False
        except:
            return False
    
    def _start_volume_monitor(self):
        """Запуск мониторинга"""
        if self._monitor_thread and self._monitor_thread.is_alive():
            return
        
        self._running = True
        self._monitor_thread = threading.Thread(target=self._volume_monitor_loop, daemon=True)
        self._monitor_thread.start()
    
    def _stop_volume_monitor(self):
        """Остановка мониторинга"""
        self._running = False
        self._monitor_thread = None
    
    def _volume_monitor_loop(self):
        """Цикл мониторинга"""
        import time
        
        while self._running and self.enabled:
            try:
                self._check_volume_change()
                time.sleep(1)
            except:
                time.sleep(1)
    
    def play_sound(self):
        """Воспроизведение системного звука"""
        try:
            import winsound
            winsound.Beep(1200, 50)
        except:
            pass
    
    def get_status(self):
        """Статус"""
        return {
            'enabled': self.enabled,
            'volume': self.volume,
            'method': 'WinAPI SendMessage'
        }

# ==================== КЛАСС: SettingsWindow (ПОЛНОСТЬЮ ПЕРЕПИСАННЫЙ) ====================
class SettingsWindow:
    """Окно настроек BITOS с полноценной системой обновлений"""
    
    def __init__(self, parent, desktop):
        self.parent = parent
        self.desktop = desktop
        self.bitos = desktop.bitos
        self.window = None
        self.notebook = None
        
        # Создаём менеджер обновлений
        self.update_manager = UpdateManager(self.bitos)
        
        # Переменные для UI обновлений
        self.update_status_label = None
        self.update_version_label = None
        self.update_progress_bar = None
        self.update_progress_label = None
        self.check_btn = None
        self.download_btn = None
        self.install_btn = None
        self.update_info_text = None
        self.update_log_text = None
        
        self.create_window()
    
    def create_window(self):
        """Создание окна настроек"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("⚙ Настройки BITOS")
        self.window.geometry("950x780")
        self.window.transient(self.parent)
        self.window.configure(bg='#F5F7FA')
        self.window.resizable(False, False)
        
        # Центрируем окно
        x = (self.window.winfo_screenwidth() - 950) // 2
        y = (self.window.winfo_screenheight() - 780) // 2
        self.window.geometry(f'+{x}+{y}')
        
        # Создаём вкладки
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Вкладки
        self._create_theme_tab()
        self._create_sound_tab()
        self._create_security_tab()
        self._create_account_tab()
        self._create_updates_tab()  # <--- ПОЛНОСТЬЮ ПЕРЕРАБОТАННАЯ ВКЛАДКА
        self._create_system_tab()
        
        # Нижняя панель
        bottom_frame = tk.Frame(self.window, bg='#F5F7FA', height=50)
        bottom_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Button(bottom_frame, text="Закрыть", bg='#95A5A6', fg='white',
                 font=('Segoe UI', 11), bd=0, padx=30, pady=8,
                 cursor='hand2', command=self.window.destroy).pack(side=tk.RIGHT, padx=5)

    # ==================== ВКЛАДКА 1: ТЕМЫ (БЕЗ ИЗМЕНЕНИЙ) ====================
    
    def _create_theme_tab(self):
        """Вкладка тем оформления"""
        theme_frame = ttk.Frame(self.notebook)
        self.notebook.add(theme_frame, text="🎨 Темы")
        
        main_frame = tk.Frame(theme_frame, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Заголовок
        header_frame = tk.Frame(main_frame, bg='white')
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(header_frame, text="🎨 Управление темами оформления", 
                font=('Segoe UI', 16, 'bold'), bg='white', fg='#2C3E50').pack(side=tk.LEFT)
        
        tk.Label(header_frame, text="Обои меняются автоматически вместе с темой", 
                font=('Segoe UI', 10), bg='white', fg='#27AE60').pack(side=tk.RIGHT)
        
        # Контейнер с темами
        themes_container = tk.Frame(main_frame, bg='white')
        themes_container.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(themes_container, bg='white', highlightthickness=0)
        scrollbar = tk.Scrollbar(themes_container, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')
        
        scrollable_frame.bind("<Configure>", 
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.theme_var = tk.StringVar(value=self.desktop.current_theme)
        
        all_themes = self.desktop.get_all_themes()
        
        # Встроенные темы
        tk.Label(scrollable_frame, text="📦 Встроенные темы:", 
                font=('Segoe UI', 13, 'bold'), bg='white', fg='#2C3E50').pack(anchor='w', pady=(10, 10))
        
        themes_grid = tk.Frame(scrollable_frame, bg='white')
        themes_grid.pack(fill=tk.X, pady=5)
        
        builtin_themes = ["Базовая", "Техно", "Эко", "Космо"]
        
        for i, theme_name in enumerate(builtin_themes):
            if theme_name in all_themes:
                theme = all_themes[theme_name]
                self._create_theme_card(themes_grid, i, theme_name, theme, is_user=False)
        
        # Пользовательские темы
        user_themes = [name for name in all_themes if name not in builtin_themes]
        if user_themes:
            tk.Label(scrollable_frame, text="👤 Пользовательские темы:", 
                    font=('Segoe UI', 13, 'bold'), bg='white', fg='#2C3E50').pack(anchor='w', pady=(20, 10))
            
            user_grid = tk.Frame(scrollable_frame, bg='white')
            user_grid.pack(fill=tk.X, pady=5)
            
            for i, theme_name in enumerate(user_themes):
                theme = all_themes[theme_name]
                self._create_theme_card(user_grid, i, theme_name, theme, is_user=True)
        
        # Кнопка создания темы
        create_frame = tk.Frame(main_frame, bg='white')
        create_frame.pack(fill=tk.X, pady=10)
        
        tk.Button(create_frame, text="➕ Создать свою тему", bg='#27AE60', fg='white',
                 font=('Segoe UI', 11, 'bold'), bd=0, padx=30, pady=10,
                 cursor='hand2', command=self._show_create_theme_dialog).pack()
    
    def _create_theme_card(self, parent, index, theme_name, theme, is_user=False):
        """Создание карточки темы с превью"""
        row = index // 3
        col = index % 3
        
        card = tk.Frame(parent, bg='#F0F3F4', relief=tk.RAISED, bd=1)
        card.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
        card.configure(width=250, height=200)
        card.grid_propagate(False)
        
        # Превью темы
        preview = tk.Canvas(card, bg=theme['bg'], width=230, height=120, 
                            highlightthickness=1, highlightcolor='#BDC3C7')
        preview.pack(pady=(10, 5))
        preview.pack_propagate(False)
        
        # Пытаемся показать превью обоев
        wallpaper_path = None
        if theme.get('wallpaper'):
            wallpaper_path = os.path.join(
                self.bitos.base_path,
                theme['wallpaper'].replace('\\', os.sep)
            )
        
        if wallpaper_path and os.path.exists(wallpaper_path) and PIL_AVAILABLE:
            try:
                img = Image.open(wallpaper_path)
                img.thumbnail((230, 120), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                preview.create_image(115, 60, image=photo, anchor='center')
                preview.image_ref = photo
            except Exception:
                self._draw_preview_gradient(preview, theme['bg'], 230, 120)
        else:
            self._draw_preview_gradient(preview, theme['bg'], 230, 120)
        
        # Название темы на превью
        icon_map = {
            "Базовая": "🔵",
            "Техно": "💻",
            "Эко": "🌿",
            "Космо": "🚀"
        }
        icon = icon_map.get(theme_name, "🎨")
        
        preview.create_text(115, 55, text=f"{icon} {theme_name}", 
                            font=('Segoe UI', 12, 'bold'), fill=theme['fg'])
        preview.create_text(115, 80, text="Нажмите для применения", 
                            font=('Segoe UI', 8), fill=theme['fg'])
        
        # Радиокнопка выбора темы
        rb = tk.Radiobutton(card, text=theme_name, variable=self.theme_var, 
                           value=theme_name, bg='#F0F3F4', fg='#2C3E50', 
                           font=('Segoe UI', 10, 'bold'), activebackground='#F0F3F4',
                           command=lambda t=theme_name: self._apply_theme_with_wallpaper(t))
        rb.pack(pady=2)
        
        # Кнопка предпросмотра обоев
        if wallpaper_path and os.path.exists(wallpaper_path):
            preview_btn = tk.Button(card, text="🖼 Показать обои", bg='#3498DB', fg='white',
                                   font=('Segoe UI', 8), bd=0, padx=10, pady=2,
                                   cursor='hand2',
                                   command=lambda p=wallpaper_path: self._show_wallpaper_preview(p))
            preview_btn.pack(pady=2)
        
        # Кнопка удаления для пользовательских тем
        if is_user:
            del_btn = tk.Button(card, text="🗑 Удалить тему", bg='#E74C3C', fg='white',
                               font=('Segoe UI', 8), bd=0, padx=10, pady=2,
                               cursor='hand2',
                               command=lambda t=theme_name: self._delete_user_theme(t))
            del_btn.pack(pady=2)
        
        # Hover эффекты
        def on_enter(e, f=card):
            f.config(bg='#E8F4FD')
        def on_leave(e, f=card):
            f.config(bg='#F0F3F4')
        
        card.bind('<Enter>', on_enter)
        card.bind('<Leave>', on_leave)
        card.bind('<Button-1>', lambda e, t=theme_name: self._apply_theme_with_wallpaper(t))
        preview.bind('<Button-1>', lambda e, t=theme_name: self._apply_theme_with_wallpaper(t))
        rb.bind('<Button-1>', lambda e, t=theme_name: self._apply_theme_with_wallpaper(t))
    
    def _draw_preview_gradient(self, canvas, bg_color, width, height):
        """Рисует градиентный фон на Canvas для превью"""
        try:
            r, g, b = self._hex_to_rgb(bg_color)
            for i in range(height):
                factor = i / height
                new_r = int(r + (255 - r) * factor * 0.2)
                new_g = int(g + (255 - g) * factor * 0.2)
                new_b = int(b + (255 - b) * factor * 0.2)
                color = f'#{new_r:02x}{new_g:02x}{new_b:02x}'
                canvas.create_line(0, i, width, i, fill=color, tags='gradient')
        except Exception:
            canvas.create_rectangle(0, 0, width, height, fill=bg_color, outline='')
    
    def _hex_to_rgb(self, hex_color):
        """Преобразование HEX в RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _apply_theme_with_wallpaper(self, theme_name):
        """Применение темы с автоматической сменой обоев"""
        try:
            all_themes = self.desktop.get_all_themes()
            
            if theme_name not in all_themes:
                return
            
            theme = all_themes[theme_name]
            
            # 1. Применяем тему (цвета)
            success = self.desktop.change_theme(theme_name)
            
            if not success:
                messagebox.showerror("Ошибка", f"Не удалось применить тему '{theme_name}'")
                return
            
            # 2. Применяем обои из темы если они есть
            if theme.get('wallpaper'):
                wallpaper_path = os.path.join(
                    self.bitos.base_path,
                    theme['wallpaper'].replace('\\', os.sep)
                )
                
                if os.path.exists(wallpaper_path):
                    self.desktop.wallpaper_manager.set_wallpaper(wallpaper_path)
                    self.desktop.update_wallpaper()
                    self.desktop.theme_colors['wallpaper'] = theme['wallpaper']
                    self.desktop.save_theme(theme_name)
                    
                    self.desktop.notification_center.add_notification(
                        "🖼 Обои обновлены",
                        f"Установлены обои для темы '{theme_name}'",
                        icon="🖼",
                        duration=3000
                    )
                else:
                    self.desktop.notification_center.add_notification(
                        "⚠️ Обои не найдены",
                        f"Файл обоев для темы '{theme_name}' отсутствует",
                        icon="⚠️",
                        duration=3000
                    )
            
            self.theme_var.set(theme_name)
            
            self.desktop.notification_center.add_notification(
                "🎨 Тема применена",
                f"Применена тема: {theme_name} с обоями",
                icon="🎨",
                duration=2000
            )
            
            self._refresh_theme_tab()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось применить тему с обоями:\n{str(e)}")
    
    def _show_wallpaper_preview(self, wallpaper_path):
        """Показывает полноэкранный предпросмотр обоев"""
        if not PIL_AVAILABLE:
            messagebox.showinfo("Информация", "Для просмотра обоев установите Pillow")
            return
        
        try:
            preview_window = tk.Toplevel(self.window)
            preview_window.title("🖼 Предпросмотр обоев")
            preview_window.geometry("800x600")
            preview_window.transient(self.window)
            preview_window.configure(bg='#2C3E50')
            
            x = (preview_window.winfo_screenwidth() - 800) // 2
            y = (preview_window.winfo_screenheight() - 600) // 2
            preview_window.geometry(f'+{x}+{y}')
            
            img = Image.open(wallpaper_path)
            img.thumbnail((750, 500), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            
            label = tk.Label(preview_window, image=photo, bg='#2C3E50')
            label.image = photo
            label.pack(expand=True, padx=20, pady=20)
            
            info_frame = tk.Frame(preview_window, bg='#2C3E50')
            info_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
            
            file_name = os.path.basename(wallpaper_path)
            file_size = os.path.getsize(wallpaper_path) / 1024
            tk.Label(info_frame, text=f"📄 {file_name}  •  {file_size:.1f} KB", 
                    font=('Segoe UI', 10), bg='#2C3E50', fg='#BDC3C7').pack()
            
            tk.Button(info_frame, text="Закрыть", bg='#E74C3C', fg='white',
                     font=('Segoe UI', 10), bd=0, padx=20, pady=5,
                     command=preview_window.destroy).pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть обои:\n{str(e)}")
    
    def _delete_user_theme(self, theme_name):
        """Удаление пользовательской темы"""
        if messagebox.askyesno("Удаление темы", f"Удалить тему '{theme_name}'?"):
            success, msg = self.desktop.delete_user_theme(theme_name)
            if success:
                messagebox.showinfo("Успех", msg)
                self._refresh_theme_tab()
            else:
                messagebox.showerror("Ошибка", msg)
    
    def _refresh_theme_tab(self):
        """Обновление вкладки тем"""
        for i, tab in enumerate(self.notebook.tabs()):
            if self.notebook.tab(tab, "text") == "🎨 Темы":
                self.notebook.forget(tab)
                self._create_theme_tab()
                self.notebook.select(len(self.notebook.tabs()) - 1)
                break
    
    def _show_create_theme_dialog(self):
        """Диалог создания пользовательской темы с обоями"""
        dialog = tk.Toplevel(self.window)
        dialog.title("➕ Создание темы")
        dialog.geometry("720x650")
        dialog.transient(self.window)
        dialog.grab_set()
        dialog.configure(bg='#F5F7FA')
        dialog.resizable(False, False)
        
        x = (dialog.winfo_screenwidth() - 720) // 2
        y = (dialog.winfo_screenheight() - 650) // 2
        dialog.geometry(f'+{x}+{y}')
        
        header = tk.Frame(dialog, bg='#3498DB', height=50)
        header.pack(fill=tk.X)
        tk.Label(header, text="➕ Создание пользовательской темы с обоями", 
                bg='#3498DB', fg='white', font=('Segoe UI', 14, 'bold')).pack(pady=12)
        
        main_container = tk.Frame(dialog, bg='#F5F7FA')
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        canvas = tk.Canvas(main_container, bg='#F5F7FA', highlightthickness=0)
        scrollbar = tk.Scrollbar(main_container, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#F5F7FA')
        
        scrollable_frame.bind("<Configure>", 
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        fields = {}
        
        def add_color_field(label, default_value):
            frame = tk.Frame(scrollable_frame, bg='#F5F7FA')
            frame.pack(fill=tk.X, pady=5)
            
            tk.Label(frame, text=label, font=('Segoe UI', 10),
                    bg='#F5F7FA', fg='#2C3E50', width=22, anchor='w').pack(side=tk.LEFT)
            
            entry = tk.Entry(frame, font=('Segoe UI', 10), bg='white', fg='#2C3E50',
                            bd=0, highlightthickness=2, highlightcolor='#3498DB',
                            highlightbackground='#BDC3C7', width=12)
            entry.pack(side=tk.LEFT, padx=5)
            entry.insert(0, default_value)
            
            def pick_color():
                from tkinter import colorchooser
                color = colorchooser.askcolor(title=f"Выберите цвет для {label}")[1]
                if color:
                    entry.delete(0, tk.END)
                    entry.insert(0, color)
                    update_preview()
            
            tk.Button(frame, text="🎨", bg='#F5F7FA', fg='#2C3E50',
                     font=('Segoe UI', 10), bd=0, cursor='hand2',
                     command=pick_color).pack(side=tk.LEFT, padx=2)
            
            return entry
        
        # Основные цвета
        tk.Label(scrollable_frame, text="🎨 Основные цвета темы:", 
                font=('Segoe UI', 12, 'bold'), bg='#F5F7FA', fg='#2C3E50').pack(anchor='w', pady=(10, 5))
        
        fields['bg'] = add_color_field("Фон рабочего стола:", "#2980B9")
        fields['fg'] = add_color_field("Цвет текста:", "#FFFFFF")
        fields['taskbar_bg'] = add_color_field("Фон панели задач:", "#1A5276")
        fields['taskbar_fg'] = add_color_field("Цвет текста панели:", "#FFFFFF")
        fields['canvas_bg'] = add_color_field("Фон холста:", "#2980B9")
        fields['icon_fg'] = add_color_field("Цвет иконок:", "#FFFFFF")
        fields['widget_bg'] = add_color_field("Фон виджетов:", "#1F618D")
        fields['widget_fg'] = add_color_field("Цвет виджетов:", "#FFFFFF")
        
        # Обои
        tk.Label(scrollable_frame, text="🖼 Обои для темы:", 
                font=('Segoe UI', 12, 'bold'), bg='#F5F7FA', fg='#2C3E50').pack(anchor='w', pady=(15, 5))
        
        wallpaper_frame = tk.Frame(scrollable_frame, bg='#F5F7FA')
        wallpaper_frame.pack(fill=tk.X, pady=5)
        
        wallpaper_path_var = tk.StringVar()
        wallpaper_entry = tk.Entry(wallpaper_frame, textvariable=wallpaper_path_var,
                                  font=('Segoe UI', 10), bg='white', fg='#7F8C8D',
                                  bd=0, highlightthickness=2, highlightcolor='#3498DB',
                                  highlightbackground='#BDC3C7', state='readonly')
        wallpaper_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        wallpaper_entry.insert(0, "Файл не выбран (будет градиент)")
        
        def browse_wallpaper():
            from tkinter import filedialog
            file_path = filedialog.askopenfilename(
                title="Выберите обои для темы",
                filetypes=[("Изображения", "*.png *.jpg *.jpeg *.gif *.bmp"), ("Все файлы", "*.*")]
            )
            if file_path:
                wallpaper_entry.config(state='normal')
                wallpaper_entry.delete(0, tk.END)
                wallpaper_entry.insert(0, file_path)
                wallpaper_entry.config(state='readonly')
                fields['wallpaper_path'] = file_path
                update_preview()
        
        tk.Button(wallpaper_frame, text="📂 Обзор", bg='#3498DB', fg='white',
                 font=('Segoe UI', 10), bd=0, padx=15, pady=5,
                 cursor='hand2', command=browse_wallpaper).pack(side=tk.RIGHT, padx=(5, 0))
        
        tk.Label(scrollable_frame, text="Название темы:", 
                font=('Segoe UI', 12, 'bold'), bg='#F5F7FA', fg='#2C3E50').pack(anchor='w', pady=(15, 5))
        
        name_frame = tk.Frame(scrollable_frame, bg='#F5F7FA')
        name_frame.pack(fill=tk.X, pady=5)
        
        name_entry = tk.Entry(name_frame, font=('Segoe UI', 12), bg='white', fg='#2C3E50',
                             bd=0, highlightthickness=2, highlightcolor='#3498DB',
                             highlightbackground='#BDC3C7')
        name_entry.pack(fill=tk.X, ipady=8)
        name_entry.insert(0, "Моя тема")
        fields['name'] = name_entry
        
        # Превью
        preview_frame = tk.Frame(scrollable_frame, bg='#F5F7FA')
        preview_frame.pack(fill=tk.X, pady=15)
        
        tk.Label(preview_frame, text="🖼 Превью темы:", font=('Segoe UI', 12, 'bold'),
                bg='#F5F7FA', fg='#2C3E50').pack(anchor='w', pady=(0, 5))
        
        preview_canvas = tk.Canvas(preview_frame, bg='#2980B9', width=660, height=100,
                                   highlightthickness=2, highlightcolor='#3498DB')
        preview_canvas.pack(fill=tk.X, pady=5)
        
        preview_text = preview_canvas.create_text(330, 30, text="Тема: Моя тема",
                                                   font=('Segoe UI', 14, 'bold'), fill='white')
        preview_subtext = preview_canvas.create_text(330, 55, text="Панель задач | Иконки | Виджеты",
                                                      font=('Segoe UI', 10), fill='white')
        preview_taskbar = preview_canvas.create_rectangle(0, 70, 660, 100, 
                                                         fill='#1A5276', outline='')
        preview_taskbar_text = preview_canvas.create_text(330, 85, text="ПУСК | 📁 Проводник | ⏰ 12:00",
                                                          fill='white', font=('Segoe UI', 8))
        
        def update_preview():
            try:
                bg_color = fields['bg'].get().strip() or "#2980B9"
                fg_color = fields['fg'].get().strip() or "#FFFFFF"
                taskbar_bg = fields['taskbar_bg'].get().strip() or "#1A5276"
                taskbar_fg = fields['taskbar_fg'].get().strip() or "#FFFFFF"
                theme_name = name_entry.get().strip() or "Моя тема"
                
                preview_canvas.config(bg=bg_color)
                preview_canvas.itemconfig(preview_text, fill=fg_color, text=f"Тема: {theme_name}")
                preview_canvas.itemconfig(preview_subtext, fill=fg_color)
                preview_canvas.itemconfig(preview_taskbar, fill=taskbar_bg)
                preview_canvas.itemconfig(preview_taskbar_text, fill=taskbar_fg)
            except Exception as e:
                pass
        
        for key, entry in fields.items():
            if key != 'name' and key != 'wallpaper_path' and hasattr(entry, 'bind'):
                entry.bind('<KeyRelease>', lambda e: update_preview())
        
        name_entry.bind('<KeyRelease>', lambda e: update_preview())
        
        btn_frame = tk.Frame(scrollable_frame, bg='#F5F7FA')
        btn_frame.pack(fill=tk.X, pady=15)
        
        def create_theme():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Ошибка", "Введите название темы", parent=dialog)
                return
            
            if name in self.desktop.THEMES:
                messagebox.showerror("Ошибка", "Тема с таким именем уже существует", parent=dialog)
                return
            
            try:
                bg_color = fields['bg'].get().strip() or "#2980B9"
                fg_color = fields['fg'].get().strip() or "#FFFFFF"
                taskbar_bg = fields['taskbar_bg'].get().strip() or "#1A5276"
                taskbar_fg = fields['taskbar_fg'].get().strip() or "#FFFFFF"
                canvas_bg = fields['canvas_bg'].get().strip() or "#2980B9"
                icon_fg = fields['icon_fg'].get().strip() or "#FFFFFF"
                widget_bg = fields['widget_bg'].get().strip() or "#1F618D"
                widget_fg = fields['widget_fg'].get().strip() or "#FFFFFF"
                wallpaper_path = fields.get('wallpaper_path')
            except Exception as e:
                messagebox.showerror("Ошибка", f"Некорректные цвета: {str(e)}", parent=dialog)
                return
            
            success, msg = self.desktop.create_user_theme(
                name, bg_color, fg_color, taskbar_bg, taskbar_fg,
                canvas_bg, icon_fg, widget_bg, widget_fg, wallpaper_path
            )
            
            if success:
                messagebox.showinfo("Успех", msg, parent=dialog)
                dialog.destroy()
                self._refresh_theme_tab()
                self._apply_theme_with_wallpaper(name)
            else:
                messagebox.showerror("Ошибка", msg, parent=dialog)
        
        tk.Button(btn_frame, text="✅ Создать и применить тему", bg='#27AE60', fg='white',
                 font=('Segoe UI', 11, 'bold'), bd=0, padx=30, pady=10,
                 cursor='hand2', command=create_theme).pack(side=tk.RIGHT, padx=5)
        
        tk.Button(btn_frame, text="Отмена", bg='#95A5A6', fg='white',
                 font=('Segoe UI', 11), bd=0, padx=30, pady=10,
                 cursor='hand2', command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
        dialog.after(100, update_preview)
        name_entry.focus_set()

    # ==================== ВКЛАДКА 2: ЗВУК (БЕЗ ИЗМЕНЕНИЙ) ====================
    
    def _create_sound_tab(self):
        """Вкладка настроек системных звуков"""
        sound_frame = ttk.Frame(self.notebook)
        self.notebook.add(sound_frame, text="🔊 Звук")
        
        main_frame = tk.Frame(sound_frame, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(main_frame, text="🔊 Системные звуки BITOS", 
                font=('Segoe UI', 16, 'bold'), bg='white', fg='#2C3E50').pack(anchor='w', pady=(0, 20))
        
        system_frame = tk.Frame(main_frame, bg='#F0F3F4', relief=tk.RIDGE, bd=1)
        system_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(system_frame, text="🔊 Системные звуки", 
                font=('Segoe UI', 14, 'bold'), bg='#F0F3F4', fg='#2C3E50').pack(anchor='w', padx=15, pady=10)
        
        tk.Label(system_frame, text="Включить/выключить все системные звуки BITOS",
                font=('Segoe UI', 10), bg='#F0F3F4', fg='#7F8C8D').pack(anchor='w', padx=15, pady=(0, 5))
        
        system_switch_frame = tk.Frame(system_frame, bg='#F0F3F4')
        system_switch_frame.pack(fill=tk.X, padx=15, pady=10)
        
        self.system_sound_var = tk.BooleanVar(value=self.bitos.sound_enabled if self.bitos else True)
        
        self.system_switch_canvas = tk.Canvas(system_switch_frame, width=60, height=30,
                                              bg='#F0F3F4', highlightthickness=0)
        self.system_switch_canvas.pack(side=tk.LEFT)
        
        self.system_switch_bg = self.system_switch_canvas.create_rectangle(
            5, 5, 55, 25,
            fill='#27AE60' if self.system_sound_var.get() else '#95A5A6',
            outline=''
        )
        self.system_switch_handle = self.system_switch_canvas.create_oval(
            37 if self.system_sound_var.get() else 7,
            7, 
            53 if self.system_sound_var.get() else 23, 
            23,
            fill='white', 
            outline='#7F8C8D'
        )
        
        self.system_switch_label = tk.Label(system_switch_frame,
                                            text="Включены" if self.system_sound_var.get() else "Выключены",
                                            font=('Segoe UI', 11, 'bold'),
                                            bg='#F0F3F4',
                                            fg='#27AE60' if self.system_sound_var.get() else '#7F8C8D')
        self.system_switch_label.pack(side=tk.LEFT, padx=(10, 0))
        
        self.system_switch_canvas.bind('<Button-1>', self._toggle_system_sound)
        self.system_switch_canvas.bind('<Enter>', lambda e: self.system_switch_canvas.config(cursor='hand2'))
        
        sounds_list_frame = tk.Frame(system_frame, bg='#F0F3F4')
        sounds_list_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        tk.Label(sounds_list_frame, text="Доступные системные звуки:", 
                font=('Segoe UI', 9, 'bold'), bg='#F0F3F4', fg='#2C3E50').pack(anchor='w', pady=(5, 5))
        
        sounds_grid = tk.Frame(sounds_list_frame, bg='#F0F3F4')
        sounds_grid.pack(fill=tk.X)
        
        sound_names = [
            ("🚀", "startup", "Запуск системы"),
            ("🔑", "logon", "Вход в систему"),
            ("🚪", "logoff", "Выход из системы"),
            ("⏻", "shutdown", "Выключение"),
            ("❌", "error", "Ошибка"),
            ("🔔", "notification", "Уведомление"),
            ("✅", "success", "Успех"),
            ("⚠️", "warning", "Предупреждение"),
            ("💾", "usb_connect", "USB подключение"),
            ("💾", "usb_disconnect", "USB отключение"),
        ]
        
        for i, (icon, name, label) in enumerate(sound_names):
            row = i // 5
            col = i % 5
            btn = tk.Button(sounds_grid, text=f"{icon} {label}", bg='#34495E', fg='white',
                           font=('Segoe UI', 8), bd=0, padx=8, pady=3,
                           cursor='hand2',
                           command=lambda n=name: self._test_system_sound(n))
            btn.grid(row=row, column=col, padx=3, pady=3, sticky='w')
            btn.bind('<Enter>', lambda e, b=btn: b.config(bg='#3498DB'))
            btn.bind('<Leave>', lambda e, b=btn: b.config(bg='#34495E'))
        
        save_frame = tk.Frame(main_frame, bg='white')
        save_frame.pack(fill=tk.X, pady=20)
        
        tk.Button(save_frame, text="✅ Применить настройки", bg='#27AE60', fg='white',
                 font=('Segoe UI', 11, 'bold'), bd=0, padx=30, pady=10,
                 cursor='hand2', command=self._save_sound_settings).pack(side=tk.RIGHT, padx=5)
    
    def _toggle_system_sound(self, event=None):
        """Переключение системных звуков"""
        new_state = not self.system_sound_var.get()
        self.system_sound_var.set(new_state)
        
        color = '#27AE60' if new_state else '#95A5A6'
        self.system_switch_canvas.itemconfig(self.system_switch_bg, fill=color)
        
        x_pos = 37 if new_state else 7
        self.system_switch_canvas.coords(self.system_switch_handle, x_pos, 7, x_pos + 16, 23)
        
        text = "Включены" if new_state else "Выключены"
        color_text = '#27AE60' if new_state else '#7F8C8D'
        self.system_switch_label.config(text=text, fg=color_text)
        
        if self.bitos:
            self.bitos.sound_enabled = new_state
            if new_state:
                self.bitos.play_sound("notification")
    
    def _test_system_sound(self, sound_name):
        """Тест системного звука"""
        if self.bitos:
            if self.bitos.sound_enabled:
                self.bitos.play_sound(sound_name)
            else:
                was_enabled = self.bitos.sound_enabled
                self.bitos.sound_enabled = True
                self.bitos.play_sound(sound_name)
                self.bitos.sound_enabled = was_enabled
    
    def _save_sound_settings(self):
        """Сохранение настроек звука"""
        try:
            if self.bitos:
                self.bitos.sound_enabled = self.system_sound_var.get()
            
            messagebox.showinfo("Успех", "Настройки звука сохранены!")
            
            if self.desktop and hasattr(self.desktop, 'notification_center'):
                self.desktop.notification_center.add_notification(
                    "🔊 Настройки звука",
                    "Настройки звука сохранены",
                    icon="🔊",
                    duration=2000
                )
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить настройки:\n{str(e)}")

    # ==================== ВКЛАДКА 3: БЕЗОПАСНОСТЬ (БЕЗ ИЗМЕНЕНИЙ) ====================
    
    def _create_security_tab(self):
        """Вкладка безопасности"""
        security_frame = ttk.Frame(self.notebook)
        self.notebook.add(security_frame, text="🔒 Безопасность")
        
        main_frame = tk.Frame(security_frame, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(main_frame, text="🔐 Изменение PIN-кода входа", 
                font=('Segoe UI', 14, 'bold'), bg='white', fg='#2C3E50').pack(anchor='w', pady=(0, 20))
        
        info_frame = tk.Frame(main_frame, bg='#F0F3F4', relief=tk.RIDGE, bd=1)
        info_frame.pack(fill=tk.X, pady=(0, 20))
        tk.Label(info_frame, text="💡 PIN-код используется для входа в систему. Должен содержать 4-8 цифр.",
                font=('Segoe UI', 10), bg='#F0F3F4', fg='#7F8C8D').pack(padx=10, pady=10)
        
        fields_frame = tk.Frame(main_frame, bg='white')
        fields_frame.pack(fill=tk.X, pady=10)
        
        labels = ["Текущий PIN-код:", "Новый PIN-код (4-8 цифр):", "Подтвердите новый PIN-код:"]
        self.pin_entries = []
        
        for i, label in enumerate(labels):
            tk.Label(fields_frame, text=label, font=('Segoe UI', 11), 
                    bg='white', fg='#2C3E50').pack(anchor='w', pady=(10, 5))
            
            entry = tk.Entry(fields_frame, font=('Segoe UI', 12), 
                           bg='#F5F7FA', fg='#2C3E50',
                           bd=0, highlightthickness=2, 
                           highlightcolor='#3498DB', highlightbackground='#BDC3C7',
                           show='•' if i > 0 else '')
            entry.pack(fill=tk.X, ipady=8, pady=(0, 5))
            self.pin_entries.append(entry)
        
        self.pin_status = tk.Label(main_frame, text="", bg='white', fg='#E74C3C', 
                                  font=('Segoe UI', 10))
        self.pin_status.pack(anchor='w', pady=5)
        
        btn_frame = tk.Frame(main_frame, bg='white')
        btn_frame.pack(fill=tk.X, pady=20)
        
        tk.Button(btn_frame, text="🔑 Изменить PIN-код", bg='#3498DB', fg='white',
                 font=('Segoe UI', 11, 'bold'), bd=0, padx=30, pady=10,
                 cursor='hand2', command=self._change_pin).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="🔄 Сбросить PIN (1234)", bg='#E67E22', fg='white',
                 font=('Segoe UI', 10), bd=0, padx=20, pady=10,
                 cursor='hand2', command=self._reset_pin).pack(side=tk.LEFT, padx=5)
    
    def _change_pin(self):
        """Изменение PIN-кода"""
        old_pin = self.pin_entries[0].get().strip()
        new_pin = self.pin_entries[1].get().strip()
        confirm_pin = self.pin_entries[2].get().strip()
        
        pin_file = os.path.join(self.bitos.base_path, "System", "Security", "pin.hash")
        saved_hash = ""
        if os.path.exists(pin_file):
            with open(pin_file, 'r') as f:
                saved_hash = f.read().strip()
        
        if hashlib.sha256(old_pin.encode()).hexdigest() != saved_hash:
            self.pin_status.config(text="❌ Неверный текущий PIN-код", fg='#E74C3C')
            return
        if not new_pin.isdigit():
            self.pin_status.config(text="❌ PIN-код должен состоять только из цифр", fg='#E74C3C')
            return
        if len(new_pin) < 4 or len(new_pin) > 8:
            self.pin_status.config(text="❌ PIN-код должен быть от 4 до 8 цифр", fg='#E74C3C')
            return
        if new_pin != confirm_pin:
            self.pin_status.config(text="❌ PIN-коды не совпадают", fg='#E74C3C')
            return
        
        os.makedirs(os.path.dirname(pin_file), exist_ok=True)
        with open(pin_file, 'w') as f:
            f.write(hashlib.sha256(new_pin.encode()).hexdigest())
        
        self.pin_status.config(text="✅ PIN-код успешно изменён!", fg='#27AE60')
        
        for entry in self.pin_entries:
            entry.delete(0, tk.END)
        
        if hasattr(self.bitos, 'security'):
            self.bitos.security.log_pin_change(self.desktop.username)
    
    def _reset_pin(self):
        """Сброс PIN-кода до 1234"""
        if messagebox.askyesno("Сброс PIN", "Сбросить PIN-код до значения по умолчанию (1234)?"):
            pin_file = os.path.join(self.bitos.base_path, "System", "Security", "pin.hash")
            os.makedirs(os.path.dirname(pin_file), exist_ok=True)
            with open(pin_file, 'w') as f:
                f.write(hashlib.sha256("1234".encode()).hexdigest())
            
            self.pin_status.config(text="✅ PIN-код сброшен до 1234", fg='#27AE60')
            for entry in self.pin_entries:
                entry.delete(0, tk.END)

    # ==================== ВКЛАДКА 4: АККАУНТ (УПРОЩЁННАЯ) ====================
    
    def _create_account_tab(self):
        """Вкладка аккаунта"""
        account_frame = ttk.Frame(self.notebook)
        self.notebook.add(account_frame, text="👤 Аккаунт")
        
        main_frame = tk.Frame(account_frame, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(main_frame, text="👤 Информация об аккаунте", 
                font=('Segoe UI', 16, 'bold'), bg='white', fg='#2C3E50').pack(anchor='w', pady=(0, 20))
        
        info_data = [
            ("Имя пользователя:", self.desktop.username),
            ("Домашняя папка:", self.bitos.user_paths["home"]),
            ("Виртуальный рабочий стол:", self.bitos.user_paths["desktop"]),
            ("Версия BITOS:", self.bitos.version),
        ]
        
        for label, value in info_data:
            frame = tk.Frame(main_frame, bg='white')
            frame.pack(fill=tk.X, pady=4)
            
            tk.Label(frame, text=label, font=('Segoe UI', 10, 'bold'), 
                    bg='white', fg='#2C3E50', width=22, anchor='w').pack(side=tk.LEFT)
            tk.Label(frame, text=value, font=('Segoe UI', 10), 
                    bg='white', fg='#7F8C8D', anchor='w').pack(side=tk.LEFT, padx=(10, 0))
        
        btn_frame = tk.Frame(main_frame, bg='white')
        btn_frame.pack(fill=tk.X, pady=20)
        
        tk.Button(btn_frame, text="🔑 Сменить пароль", bg='#3498DB', fg='white',
                 font=('Segoe UI', 11), bd=0, padx=20, pady=8,
                 cursor='hand2', command=self._show_coming_soon).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="🌐 Открыть Global ID", bg='#27AE60', fg='white',
                 font=('Segoe UI', 11), bd=0, padx=20, pady=8,
                 cursor='hand2', command=self._open_global_id).pack(side=tk.LEFT, padx=5)
    
    def _open_global_id(self):
        """Открыть сайт Global ID"""
        import webbrowser
        webbrowser.open("https://saryanich.github.io/Global-ID/")

    # ==================== ВКЛАДКА 5: ОБНОВЛЕНИЯ (ПОЛНОСТЬЮ ПЕРЕРАБОТАННАЯ) ====================
    
    def _create_updates_tab(self):
        """Вкладка обновлений - ПОЛНОСТЬЮ ПЕРЕРАБОТАННАЯ с системой автообновления"""
        updates_frame = ttk.Frame(self.notebook)
        self.notebook.add(updates_frame, text="📦 Обновления")
        
        main_frame = tk.Frame(updates_frame, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # ===== ЗАГОЛОВОК =====
        header_frame = tk.Frame(main_frame, bg='white')
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(header_frame, text="📦 Система обновлений BITOS", 
                font=('Segoe UI', 18, 'bold'), bg='white', fg='#2C3E50').pack(side=tk.LEFT)
        
        version_badge = tk.Label(header_frame, text=f"v{self.bitos.version}", 
                                 font=('Segoe UI', 12, 'bold'), bg='#3498DB', fg='white',
                                 padx=12, pady=4)
        version_badge.pack(side=tk.LEFT, padx=(15, 0))
        
        # ===== СТАТУСНАЯ ПАНЕЛЬ =====
        status_frame = tk.Frame(main_frame, bg='#F0F3F4', relief=tk.RIDGE, bd=1)
        status_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Текущая версия
        version_frame = tk.Frame(status_frame, bg='#F0F3F4')
        version_frame.pack(fill=tk.X, padx=15, pady=8)
        
        tk.Label(version_frame, text="📌 Текущая версия:", 
                font=('Segoe UI', 11), bg='#F0F3F4', fg='#2C3E50').pack(side=tk.LEFT)
        
        tk.Label(version_frame, text=f"{self.bitos.version} ({self.bitos.build})", 
                font=('Segoe UI', 11, 'bold'), bg='#F0F3F4', fg='#3498DB').pack(side=tk.LEFT, padx=(10, 0))
        
        # Статус обновления
        status_line = tk.Frame(status_frame, bg='#F0F3F4')
        status_line.pack(fill=tk.X, padx=15, pady=(0, 8))
        
        tk.Label(status_line, text="🔍 Статус:", 
                font=('Segoe UI', 11), bg='#F0F3F4', fg='#2C3E50').pack(side=tk.LEFT)
        
        # Проверяем сохранённый статус
        saved_status = self.update_manager.status
        if saved_status.get('update_available', False):
            status_text = f"✅ Доступно обновление v{saved_status.get('latest_version', '')}"
            status_color = '#E67E22'
        elif saved_status.get('checked_at'):
            status_text = "✅ Установлена последняя версия"
            status_color = '#27AE60'
        else:
            status_text = "⏳ Ожидание проверки"
            status_color = '#7F8C8D'
        
        self.update_status_label = tk.Label(status_line, text=status_text, 
                                           font=('Segoe UI', 11, 'bold'),
                                           bg='#F0F3F4', fg=status_color)
        self.update_status_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Время последней проверки
        if saved_status.get('checked_at'):
            try:
                check_time = datetime.fromisoformat(saved_status['checked_at'])
                time_str = check_time.strftime('%H:%M:%S %d.%m.%Y')
                tk.Label(status_line, text=f"(Проверено: {time_str})", 
                        font=('Segoe UI', 9), bg='#F0F3F4', fg='#95A5A6').pack(side=tk.LEFT, padx=(15, 0))
            except:
                pass
        
        # ===== КНОПКИ УПРАВЛЕНИЯ =====
        btn_frame = tk.Frame(main_frame, bg='white')
        btn_frame.pack(fill=tk.X, pady=5)
        
        # Кнопка проверки
        self.check_btn = tk.Button(btn_frame, text="🔍 Проверить обновления", 
                                  bg='#3498DB', fg='white',
                                  font=('Segoe UI', 10, 'bold'), bd=0, padx=20, pady=10,
                                  cursor='hand2', command=self._check_updates)
        self.check_btn.pack(side=tk.LEFT, padx=5)
        
        # Кнопка скачивания (изначально неактивна)
        self.download_btn = tk.Button(btn_frame, text="⬇️ Скачать обновление", 
                                     bg='#95A5A6', fg='white',
                                     font=('Segoe UI', 10, 'bold'), bd=0, padx=20, pady=10,
                                     cursor='hand2', state='disabled',
                                     command=self._download_update)
        self.download_btn.pack(side=tk.LEFT, padx=5)
        
        # Кнопка установки (изначально неактивна)
        self.install_btn = tk.Button(btn_frame, text="🔄 Установить и перезагрузить", 
                                    bg='#95A5A6', fg='white',
                                    font=('Segoe UI', 10, 'bold'), bd=0, padx=20, pady=10,
                                    cursor='hand2', state='disabled',
                                    command=self._install_update)
        self.install_btn.pack(side=tk.LEFT, padx=5)
        
        # ===== ПРОГРЕСС-БАР =====
        progress_frame = tk.Frame(main_frame, bg='white')
        progress_frame.pack(fill=tk.X, pady=(10, 5))
        
        self.update_progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=700)
        self.update_progress_bar.pack(fill=tk.X)
        
        self.update_progress_label = tk.Label(progress_frame, text="", 
                                             bg='white', fg='#7F8C8D', font=('Segoe UI', 9))
        self.update_progress_label.pack(anchor='w', pady=(5, 0))
        
        # ===== ИНФОРМАЦИЯ О РЕЛИЗЕ =====
        info_frame = tk.Frame(main_frame, bg='white', relief=tk.SUNKEN, bd=1)
        info_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 5))
        
        tk.Label(info_frame, text="📋 Информация о версии:", 
                font=('Segoe UI', 10, 'bold'), bg='white', fg='#2C3E50').pack(anchor='w', padx=10, pady=5)
        
        self.update_info_text = scrolledtext.ScrolledText(info_frame, font=('Consolas', 10), 
                                                          bg='#F5F7FA', fg='#2C3E50',
                                                          height=4, wrap=tk.WORD)
        self.update_info_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.update_info_text.insert('1.0', "🔍 Нажмите 'Проверить обновления' для получения информации\n")
        self.update_info_text.config(state='disabled')
        
        # ===== ЛОГ ОБНОВЛЕНИЙ =====
        log_frame = tk.Frame(main_frame, bg='white', relief=tk.SUNKEN, bd=1)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        log_header = tk.Frame(log_frame, bg='white')
        log_header.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(log_header, text="📝 Лог обновлений:", 
                font=('Segoe UI', 10, 'bold'), bg='white', fg='#2C3E50').pack(side=tk.LEFT)
        
        tk.Button(log_header, text="Очистить", bg='#E74C3C', fg='white',
                 font=('Segoe UI', 8), bd=0, padx=10, pady=2,
                 cursor='hand2', command=self._clear_update_log).pack(side=tk.RIGHT)
        
        self.update_log_text = scrolledtext.ScrolledText(log_frame, font=('Consolas', 9), 
                                                         bg='#1E1E1E', fg='#00FF00',
                                                         height=5, wrap=tk.WORD)
        self.update_log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.update_log_text.insert('1.0', "[INFO] Система обновлений готова\n")
        self.update_log_text.insert('end', "[INFO] Для проверки нажмите 'Проверить обновления'\n")
        self.update_log_text.config(state='disabled')
        
        # Обновляем состояние кнопок
        self._update_buttons_state()
    
    def _update_buttons_state(self):
        """Обновление состояния кнопок в зависимости от статуса"""
        if self.update_manager.update_available:
            self.download_btn.config(state='normal', bg='#27AE60')
            self.install_btn.config(state='disabled', bg='#95A5A6')
        else:
            self.download_btn.config(state='disabled', bg='#95A5A6')
            self.install_btn.config(state='disabled', bg='#95A5A6')
        
        if self.update_manager.is_downloading:
            self.check_btn.config(state='disabled', bg='#95A5A6')
            self.download_btn.config(state='disabled', bg='#95A5A6')
        
        if self.update_manager.is_installing:
            self.check_btn.config(state='disabled', bg='#95A5A6')
            self.download_btn.config(state='disabled', bg='#95A5A6')
            self.install_btn.config(state='disabled', bg='#95A5A6')
    
    def _log_update(self, message, log_type="INFO"):
        """Добавление записи в лог обновлений"""
        colors = {
            "INFO": "#00FF00",
            "WARNING": "#FFA500",
            "ERROR": "#FF0000",
            "SUCCESS": "#00FF00",
            "DOWNLOAD": "#00BFFF",
            "INSTALL": "#FFD700"
        }
        
        color = colors.get(log_type, "#00FF00")
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        self.update_log_text.config(state='normal')
        self.update_log_text.insert('end', f"[{timestamp}] ", "timestamp")
        self.update_log_text.insert('end', f"[{log_type}] ", log_type)
        self.update_log_text.insert('end', f"{message}\n", "message")
        
        # Настраиваем теги
        self.update_log_text.tag_config("timestamp", foreground="#7F8C8D")
        self.update_log_text.tag_config("INFO", foreground="#00FF00")
        self.update_log_text.tag_config("WARNING", foreground="#FFA500")
        self.update_log_text.tag_config("ERROR", foreground="#FF0000")
        self.update_log_text.tag_config("SUCCESS", foreground="#00FF00")
        self.update_log_text.tag_config("DOWNLOAD", foreground="#00BFFF")
        self.update_log_text.tag_config("INSTALL", foreground="#FFD700")
        self.update_log_text.tag_config("message", foreground=color)
        
        # Прокручиваем вниз
        self.update_log_text.see('end')
        self.update_log_text.config(state='disabled')
        self.update_log_text.update()
    
    def _check_updates(self):
        """Проверка обновлений"""
        if self.update_manager.check_in_progress:
            return
        
        self._log_update("Начинаем проверку обновлений...", "INFO")
        self.check_btn.config(state='disabled', text="⏳ Проверка...")
        self.update_status_label.config(text="⏳ Проверка обновлений...", fg='#3498DB')
        
        def callback(success, version, download_url, release_notes, error):
            self.window.after(0, lambda: self._check_callback(success, version, download_url, release_notes, error))
        
        # Запускаем проверку в потоке
        thread = threading.Thread(target=self.update_manager.check_for_updates, args=(callback,))
        thread.daemon = True
        thread.start()
    
    def _check_callback(self, success, version, download_url, release_notes, error):
        """Callback после проверки обновлений"""
        self.check_btn.config(state='normal', text="🔍 Проверить обновления")
        
        if error:
            self._log_update(f"❌ Ошибка: {error}", "ERROR")
            self.update_status_label.config(text=f"❌ {error}", fg='#E74C3C')
            
            # Показываем диалог с ошибкой
            if "requests" in error:
                messagebox.showerror("Ошибка", 
                    "Библиотека requests не установлена!\n\n"
                    "Установите её командой:\n"
                    "pip install requests")
            else:
                messagebox.showerror("Ошибка", f"Не удалось проверить обновления:\n{error}")
            return
        
        if success:
            self._log_update(f"✅ Доступно обновление v{version}!", "SUCCESS")
            self.update_status_label.config(text=f"✅ Доступно обновление v{version}", fg='#E67E22')
            
            # Показываем информацию о релизе
            self.update_info_text.config(state='normal')
            self.update_info_text.delete('1.0', tk.END)
            
            info = f"""
╔═══════════════════════════════════════════════════════════════
║ НОВАЯ ВЕРСИЯ: v{version}
╠═══════════════════════════════════════════════════════════════
║ Текущая версия: {self.bitos.version}
║
║ 📝 Описание релиза:
║ {release_notes if release_notes else 'Нет описания'}
╠═══════════════════════════════════════════════════════════════
║ 📥 Ссылка для скачивания: {download_url}
╚═══════════════════════════════════════════════════════════════
"""
            self.update_info_text.insert('1.0', info)
            self.update_info_text.config(state='disabled')
            
            # Активируем кнопку скачивания
            self.download_btn.config(state='normal', bg='#27AE60')
            self._log_update(f"📥 Нажмите 'Скачать обновление' для загрузки v{version}", "DOWNLOAD")
            
            # Показываем уведомление
            if self.desktop and hasattr(self.desktop, 'notification_center'):
                self.desktop.notification_center.add_notification(
                    "📦 Доступно обновление",
                    f"Версия {version} доступна для скачивания",
                    icon="📦",
                    duration=5000
                )
        else:
            self._log_update("✅ Установлена последняя версия", "INFO")
            self.update_status_label.config(text="✅ Установлена последняя версия", fg='#27AE60')
            
            self.update_info_text.config(state='normal')
            self.update_info_text.delete('1.0', tk.END)
            self.update_info_text.insert('1.0', "✅ Установлена последняя версия BITOS\n\n"
                                               f"Текущая версия: {self.bitos.version}\n"
                                               f"Дата проверки: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
            self.update_info_text.config(state='disabled')
            
            self.download_btn.config(state='disabled', bg='#95A5A6')
            self.install_btn.config(state='disabled', bg='#95A5A6')
    
    def _download_update(self):
        """Скачивание обновления"""
        if not self.update_manager.update_available:
            messagebox.showinfo("Информация", "Нет доступных обновлений для скачивания")
            return
        
        if self.update_manager.is_downloading:
            messagebox.showinfo("Информация", "Скачивание уже выполняется")
            return
        
        # Спрашиваем пользователя
        if not messagebox.askyesno("Скачивание обновления", 
                                  f"Начать скачивание обновления v{self.update_manager.latest_version}?\n\n"
                                  f"Размер: ~10-50 МБ\n"
                                  f"Время: зависит от скорости интернета"):
            return
        
        self._log_update(f"📥 Начинаем скачивание v{self.update_manager.latest_version}...", "DOWNLOAD")
        self.download_btn.config(state='disabled', text="⏳ Скачивание...")
        self.check_btn.config(state='disabled')
        self.update_progress_bar['value'] = 0
        self.update_progress_label.config(text="Подготовка к скачиванию...")
        
        def progress_callback(percent, status_text):
            self.window.after(0, lambda: self._download_progress(percent, status_text))
        
        def complete_callback(success, file_path, error):
            self.window.after(0, lambda: self._download_complete(success, file_path, error))
        
        # Запускаем скачивание в потоке
        thread = threading.Thread(target=self._download_thread, 
                                 args=(progress_callback, complete_callback))
        thread.daemon = True
        thread.start()
    
    def _download_thread(self, progress_callback, complete_callback):
        """Поток для скачивания"""
        try:
            import requests
            
            # Подготавливаем URL
            url = self.update_manager.download_url
            
            # Создаём имя файла
            filename = f"bitos_update_{self.update_manager.latest_version}.zip"
            filepath = os.path.join(self.update_manager.temp_dir, filename)
            
            # Скачиваем с прогрессом
            response = requests.get(url, stream=True, timeout=30)
            total_size = int(response.headers.get('content-length', 0))
            
            if total_size == 0:
                complete_callback(False, None, "Не удалось определить размер файла")
                return
            
            progress_callback(0, "Начинаем загрузку...")
            
            with open(filepath, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        percent = int((downloaded / total_size) * 100)
                        progress_callback(percent, f"Скачивание: {percent}% ({downloaded//1024} KB)")
            
            # Проверяем, что файл скачался
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                complete_callback(True, filepath, None)
            else:
                complete_callback(False, None, "Файл не скачан")
                
        except Exception as e:
            complete_callback(False, None, str(e))
    
    def _download_progress(self, percent, status_text):
        """Обновление прогресса скачивания"""
        self.update_progress_bar['value'] = percent
        self.update_progress_label.config(text=status_text)
        self._log_update(f"📥 {status_text}", "DOWNLOAD")
    
    def _download_complete(self, success, file_path, error):
        """Завершение скачивания"""
        self.download_btn.config(state='normal', text="⬇️ Скачать обновление")
        self.check_btn.config(state='normal')
        
        if success:
            self._log_update(f"✅ Скачивание завершено! Файл: {os.path.basename(file_path)}", "SUCCESS")
            self.update_progress_label.config(text="✅ Скачивание завершено!")
            self.update_status_label.config(text="✅ Обновление скачано, готово к установке", fg='#27AE60')
            
            # Активируем кнопку установки
            self.install_btn.config(state='normal', bg='#E67E22')
            self.update_manager.download_progress = 100
            
            # Показываем уведомление
            if self.desktop and hasattr(self.desktop, 'notification_center'):
                self.desktop.notification_center.add_notification(
                    "✅ Обновление скачано",
                    f"Версия {self.update_manager.latest_version} готова к установке",
                    icon="✅",
                    duration=5000
                )
            
            # Спрашиваем, устанавливать ли сейчас
            if messagebox.askyesno("Установка обновления", 
                                  f"Обновление v{self.update_manager.latest_version} скачано.\n\n"
                                  "Установить сейчас? (Потребуется перезагрузка)"):
                self._install_update()
        else:
            self._log_update(f"❌ Ошибка скачивания: {error}", "ERROR")
            self.update_progress_label.config(text=f"❌ Ошибка: {error}")
            self.update_status_label.config(text=f"❌ Ошибка скачивания", fg='#E74C3C')
            self.download_btn.config(state='normal', bg='#27AE60')
            
            messagebox.showerror("Ошибка скачивания", 
                f"Не удалось скачать обновление:\n{error}\n\n"
                "Попробуйте позже или скачайте вручную с GitHub.")
    
    def _install_update(self):
        """Установка обновления с перезагрузкой"""
        if self.update_manager.is_installing:
            return
        
        if not self.update_manager.download_progress == 100:
            messagebox.showinfo("Информация", "Сначала скачайте обновление")
            return
        
        # Проверяем, есть ли файл
        filename = f"bitos_update_{self.update_manager.latest_version}.zip"
        filepath = os.path.join(self.update_manager.temp_dir, filename)
        
        if not os.path.exists(filepath):
            messagebox.showerror("Ошибка", "Файл обновления не найден.\nПопробуйте скачать заново.")
            return
        
        # Спрашиваем пользователя
        if not messagebox.askyesno("Установка обновления", 
                                  f"Установить обновление v{self.update_manager.latest_version}?\n\n"
                                  "⚠️ ВНИМАНИЕ:\n"
                                  "• Программа будет перезагружена\n"
                                  "• Все несохранённые данные будут потеряны\n"
                                  "• Убедитесь, что вы сохранили все важные файлы"):
            return
        
        self._log_update(f"🔄 Начинаем установку v{self.update_manager.latest_version}...", "INSTALL")
        self.install_btn.config(state='disabled', text="⏳ Установка...")
        self.download_btn.config(state='disabled')
        self.check_btn.config(state='disabled')
        self.update_progress_label.config(text="⏳ Установка обновления...")
        self.update_progress_bar['value'] = 50
        
        # Запускаем установку в потоке
        thread = threading.Thread(target=self._install_thread, args=(filepath,))
        thread.daemon = True
        thread.start()
    
    def _install_thread(self, filepath):
        """Поток для установки обновления"""
        try:
            self.update_manager.is_installing = True
            
            # Создаём резервную копию текущей версии
            backup_path = os.path.join(self.update_manager.backup_dir, 
                                      f"bitos_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            os.makedirs(backup_path, exist_ok=True)
            
            self.window.after(0, lambda: self.update_progress_label.config(text="📦 Создание резервной копии..."))
            self._log_update("📦 Создание резервной копии текущей версии...", "INSTALL")
            
            # Копируем текущие файлы в резерв
            base_path = self.bitos.base_path
            for item in os.listdir(base_path):
                if item in ['System', 'venv', '__pycache__', '.git']:
                    continue
                src = os.path.join(base_path, item)
                dst = os.path.join(backup_path, item)
                if os.path.isdir(src):
                    shutil.copytree(src, dst, ignore_dangling_symlinks=True)
                else:
                    shutil.copy2(src, dst)
            
            self.window.after(0, lambda: self.update_progress_label.config(text="📦 Распаковка обновления..."))
            self.window.after(0, lambda: self.update_progress_bar.config(value=70))
            self._log_update("📦 Распаковка обновления...", "INSTALL")
            
            # Распаковываем архив
            import zipfile
            extract_path = os.path.join(self.update_manager.temp_dir, "extracted")
            os.makedirs(extract_path, exist_ok=True)
            
            with zipfile.ZipFile(filepath, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            
            # Находим папку с кодом (обычно она имеет имя вида Saryanich-BITOS-xxxxxxx)
            extracted_items = os.listdir(extract_path)
            extracted_dir = None
            for item in extracted_items:
                if os.path.isdir(os.path.join(extract_path, item)):
                    extracted_dir = os.path.join(extract_path, item)
                    break
            
            if not extracted_dir:
                self.window.after(0, lambda: self._install_error("Не удалось найти распакованные файлы"))
                return
            
            self.window.after(0, lambda: self.update_progress_label.config(text="📦 Замена файлов..."))
            self.window.after(0, lambda: self.update_progress_bar.config(value=85))
            self._log_update("📦 Замена файлов...", "INSTALL")
            
            # Копируем новые файлы поверх старых (кроме System)
            for item in os.listdir(extracted_dir):
                if item == 'System':
                    continue
                src = os.path.join(extracted_dir, item)
                dst = os.path.join(base_path, item)
                if os.path.exists(dst):
                    if os.path.isdir(dst):
                        shutil.rmtree(dst)
                    else:
                        os.remove(dst)
                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
            
            self.window.after(0, lambda: self.update_progress_label.config(text="✅ Установка завершена!"))
            self.window.after(0, lambda: self.update_progress_bar.config(value=100))
            self._log_update("✅ Установка завершена!", "SUCCESS")
            
            # Сохраняем статус
            self.update_manager.status['install_complete'] = True
            self.update_manager.status['installed_version'] = self.update_manager.latest_version
            self.update_manager.status['installed_at'] = datetime.now().isoformat()
            self.update_manager._save_status()
            
            # Показываем сообщение и перезагружаемся
            self.window.after(1000, self._restart_after_update)
            
        except Exception as e:
            self.window.after(0, lambda: self._install_error(str(e)))
    
    def _install_error(self, error):
        """Ошибка установки"""
        self._log_update(f"❌ Ошибка установки: {error}", "ERROR")
        self.update_progress_label.config(text=f"❌ Ошибка: {error}")
        self.update_status_label.config(text=f"❌ Ошибка установки", fg='#E74C3C')
        self.install_btn.config(state='normal', text="🔄 Установить и перезагрузить", bg='#E67E22')
        self.download_btn.config(state='normal')
        self.check_btn.config(state='normal')
        self.update_manager.is_installing = False
        
        messagebox.showerror("Ошибка установки", 
            f"Не удалось установить обновление:\n{error}\n\n"
            "Попробуйте скачать обновление вручную с GitHub.")
    
    def _restart_after_update(self):
        """Перезагрузка после установки обновления"""
        self._log_update("🔄 Перезагрузка системы...", "INSTALL")
        
        if self.desktop and hasattr(self.desktop, 'notification_center'):
            self.desktop.notification_center.add_notification(
                "🔄 Перезагрузка",
                "Система перезагружается для применения обновления",
                icon="🔄",
                duration=5000
            )
        
        # Сохраняем состояние
        try:
            self.desktop.save_desktop_shortcuts()
            self.desktop.save_widgets()
        except:
            pass
        
        # Закрываем окна
        try:
            self.window.destroy()
        except:
            pass
        
        # Перезапускаем приложение
        self._restart_application()
    
    def _restart_application(self):
        """Перезапуск приложения"""
        try:
            # Создаём скрипт для перезапуска
            restart_script = f'''
import sys, os, subprocess, time, json
import sys
import os
import subprocess
import time

# Ждём закрытия основного процесса
time.sleep(2)

# Запускаем заново
python_exe = sys.executable
script_path = sys.argv[0]

if os.path.exists(script_path):
    subprocess.Popen([python_exe, script_path], creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
'''
            restart_path = os.path.join(self.update_manager.temp_dir, "restart.pyw")
            with open(restart_path, 'w', encoding='utf-8') as f:
                f.write(restart_script)
            
            # Запускаем скрипт перезапуска
            subprocess.Popen([sys.executable, restart_path], 
                           creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0)
            
            # Закрываем текущее приложение
            sys.exit(0)
            
        except Exception as e:
            self._log_update(f"⚠️ Ошибка перезапуска: {e}", "WARNING")
            # Если не удалось перезапустить, просто закрываемся
            sys.exit(0)
    
    def _clear_update_log(self):
        """Очистка лога обновлений"""
        self.update_log_text.config(state='normal')
        self.update_log_text.delete('1.0', tk.END)
        self.update_log_text.insert('1.0', "[INFO] Лог очищен\n")
        self.update_log_text.insert('end', "[INFO] Система обновлений готова\n")
        self.update_log_text.config(state='disabled')
    
    def _show_coming_soon(self):
        """Показать сообщение о разработке"""
        messagebox.showinfo("В разработке", 
            "🚧 Эта функция находится в разработке.\n\n"
            "В ближайшее время будет добавлена.")

    # ==================== ВКЛАДКА 6: СИСТЕМА (БЕЗ ИЗМЕНЕНИЙ) ====================
    
    def _create_system_tab(self):
        """Вкладка системной информации"""
        system_frame = ttk.Frame(self.notebook)
        self.notebook.add(system_frame, text="💻 Система")
        
        main_frame = tk.Frame(system_frame, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(main_frame, text="💻 Системная информация", 
                font=('Segoe UI', 16, 'bold'), bg='white', fg='#2C3E50').pack(anchor='w', pady=(0, 20))
        
        info_data = [
            ("🖥️ Система:", platform.system()),
            ("📀 Версия ядра:", platform.release()),
            ("🔧 Архитектура:", platform.machine()),
            ("🐍 Python:", platform.python_version()),
            ("📦 BITOS версия:", self.bitos.version),
            ("🔨 Сборка:", self.bitos.build),
            ("👤 Пользователь:", self.desktop.username),
            ("📁 Директория:", self.bitos.base_path),
        ]
        
        for label, value in info_data:
            frame = tk.Frame(main_frame, bg='white')
            frame.pack(fill=tk.X, pady=4)
            
            tk.Label(frame, text=label, font=('Segoe UI', 10, 'bold'), 
                    bg='white', fg='#2C3E50', width=18, anchor='w').pack(side=tk.LEFT)
            tk.Label(frame, text=value, font=('Segoe UI', 10), 
                    bg='white', fg='#7F8C8D', anchor='w').pack(side=tk.LEFT, padx=(10, 0))
        
        stats_frame = tk.Frame(main_frame, bg='#F0F3F4', relief=tk.RIDGE, bd=1)
        stats_frame.pack(fill=tk.X, pady=20)
        
        tk.Label(stats_frame, text="📊 Статистика сессии", 
                font=('Segoe UI', 12, 'bold'), bg='#F0F3F4', fg='#2C3E50').pack(anchor='w', padx=15, pady=10)
        
        if hasattr(self.bitos, 'security'):
            stats = self.bitos.security.get_session_summary()
            stat_items = [
                ("⏱️ Длительность:", stats.get('duration', 'Unknown')),
                ("📱 Запущено приложений:", stats.get('apps_launched', 0)),
                ("📁 Открыто файлов:", stats.get('files_accessed', 0)),
                ("🗑️ Удалено файлов:", stats.get('files_deleted', 0)),
                ("⚠️ Ошибок:", stats.get('errors', 0)),
                ("🔐 Событий безопасности:", stats.get('security_events', 0)),
            ]
            
            for label, value in stat_items:
                frame = tk.Frame(stats_frame, bg='#F0F3F4')
                frame.pack(fill=tk.X, padx=15, pady=2)
                tk.Label(frame, text=label, font=('Segoe UI', 10), 
                        bg='#F0F3F4', fg='#2C3E50', width=20, anchor='w').pack(side=tk.LEFT)
                tk.Label(frame, text=str(value), font=('Segoe UI', 10, 'bold'), 
                        bg='#F0F3F4', fg='#3498DB').pack(side=tk.LEFT)
        
        tk.Button(main_frame, text="🔄 Обновить информацию", bg='#3498DB', fg='white',
                 font=('Segoe UI', 10), bd=0, padx=20, pady=8,
                 cursor='hand2', command=self._refresh_system_tab).pack(pady=10)
    
    def _refresh_system_tab(self):
        """Обновление системной информации"""
        for i, tab in enumerate(self.notebook.tabs()):
            if self.notebook.tab(tab, "text") == "💻 Система":
                self.notebook.forget(tab)
                break
        self._create_system_tab()

class AutoSafe:
    """
    Автоматическое сохранение состояния рабочего стола BITOS:
    - Позиции иконок на рабочем столе
    - ПОЛОЖЕНИЕ НА ЭКРАНЕ всех виджетов (часы, календарь, стикеры)
    - Текущая тема оформления
    - Настройки обоев
    
    Сохранение происходит:
    - Каждые 10 секунд (в фоновом режиме) - только если что-то изменилось
    - При смене темы
    - При изменении виджетов (добавление/удаление/перемещение)
    - При выходе из системы
    - При выключении/перезагрузке
    
    АВТОНОМНЫЙ КЛАСС - НЕ ТРЕБУЕТ ИЗМЕНЕНИЙ В ДРУГИХ КЛАССАХ!
    """
    
    # Константы
    SAVE_INTERVAL = 10  # секунд
    CONFIG_DIR = "System\\Config"
    SHORTCUTS_FILE = "desktop_shortcuts.json"
    WIDGETS_FILE = "widgets.json"
    THEME_FILE = "theme.cfg"
    WALLPAPER_FILE = "wallpaper.json"
    AUTOSAVE_FILE = "autosave_state.json"
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance
    
    def __init__(self, bitos=None, desktop=None):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        self.bitos = bitos
        self.desktop = desktop
        
        # Состояние сохранения
        self._is_running = True
        self._save_counter = 0
        self._last_save_time = 0
        self._save_in_progress = False
        
        # Хеш последнего сохранённого состояния (для отслеживания изменений)
        self._last_state_hash = None
        
        # Пути к файлам
        self._init_paths()
        
        # Запуск фонового сохранения
        self._start_auto_save()
        
        # Установка автономных триггеров
        self._setup_autonomous_triggers()
        
        print("[AutoSafe] ✅ Инициализирован. Сохранение каждые 10 секунд")
        print(f"[AutoSafe] 📁 Путь: {self.config_path}")
    
    def _init_paths(self):
        """Инициализация путей к файлам конфигурации"""
        if self.bitos and hasattr(self.bitos, 'system_paths'):
            self.config_path = self.bitos.system_paths.get("config", "")
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            self.config_path = os.path.join(base_path, "System", "Config")
        
        os.makedirs(self.config_path, exist_ok=True)
        
        # Полные пути к файлам
        self.shortcuts_path = os.path.join(self.config_path, self.SHORTCUTS_FILE)
        self.widgets_path = os.path.join(self.config_path, self.WIDGETS_FILE)
        self.theme_path = os.path.join(self.config_path, self.THEME_FILE)
        self.wallpaper_path = os.path.join(self.config_path, self.WALLPAPER_FILE)
        self.autosave_path = os.path.join(self.config_path, self.AUTOSAVE_FILE)
    
    def _setup_autonomous_triggers(self):
        """Установка автономных триггеров без изменения других классов"""
        if not self.desktop:
            print("[AutoSafe] ⚠️ Desktop не передан, триггеры не установлены")
            return
        
        try:
            # ===== ТРИГГЕР 1: СМЕНА ТЕМЫ =====
            original_change_theme = self.desktop.change_theme
            
            def patched_change_theme(theme_name):
                result = original_change_theme(theme_name)
                self.save_all()
                return result
            
            self.desktop.change_theme = patched_change_theme
            print("[AutoSafe] ✅ Триггер 'смена темы' установлен")
            
            # ===== ТРИГГЕР 2: ИЗМЕНЕНИЕ ВИДЖЕТОВ =====
            original_add_widget = self.desktop.add_widget
            original_remove_all_widgets = self.desktop.remove_all_widgets
            
            def patched_add_widget(widget_type):
                result = original_add_widget(widget_type)
                self.save_all()
                return result
            
            def patched_remove_all_widgets():
                result = original_remove_all_widgets()
                self.save_all()
                return result
            
            self.desktop.add_widget = patched_add_widget
            self.desktop.remove_all_widgets = patched_remove_all_widgets
            print("[AutoSafe] ✅ Триггер 'изменение виджетов' установлен")
            
            # ===== ТРИГГЕР 3: ПЕРЕМЕЩЕНИЕ ВИДЖЕТОВ =====
            self._patch_widget_drag()
            
            # ===== ТРИГГЕР 4: ВЫХОД ИЗ СИСТЕМЫ =====
            original_logout = self.desktop.logout
            
            def patched_logout():
                self.save_all()
                original_logout()
            
            self.desktop.logout = patched_logout
            print("[AutoSafe] ✅ Триггер 'выход из системы' установлен")
            
            # ===== ТРИГГЕР 5: ВЫКЛЮЧЕНИЕ/ПЕРЕЗАГРУЗКА =====
            original_shutdown = self.desktop.shutdown
            original_reboot = self.desktop.reboot
            
            def patched_shutdown():
                self.save_all()
                original_shutdown()
            
            def patched_reboot():
                self.save_all()
                original_reboot()
            
            self.desktop.shutdown = patched_shutdown
            self.desktop.reboot = patched_reboot
            print("[AutoSafe] ✅ Триггер 'выключение/перезагрузка' установлен")
            
            # ===== ТРИГГЕР 6: КОНТЕКСТНОЕ МЕНЮ =====
            self._add_to_context_menu()
            print("[AutoSafe] ✅ Триггер 'контекстное меню' установлен")
            
        except Exception as e:
            print(f"[AutoSafe] ⚠️ Ошибка установки триггеров: {e}")
    
    def _patch_widget_drag(self):
        """Патчинг методов перетаскивания виджетов для отслеживания перемещения"""
        # Патчим метод stop_drag у каждого класса виджетов
        widget_classes = [ClockWidget, CalendarWidget, StickerWidget]
        
        for widget_class in widget_classes:
            try:
                original_stop_drag = widget_class.stop_drag
                
                def patched_stop_drag(self, event):
                    # Вызываем оригинальный метод с event
                    original_stop_drag(self, event)
                    # Сохраняем после перемещения
                    try:
                        if hasattr(self, 'canvas') and hasattr(self.canvas, 'master'):
                            desktop = self.canvas.master
                            if hasattr(desktop, 'autosafe'):
                                desktop.autosafe.save_all()
                    except:
                        pass
                
                widget_class.stop_drag = patched_stop_drag
                print(f"[AutoSafe] ✅ Патчинг drag для {widget_class.__name__}")
            except Exception as e:
                print(f"[AutoSafe] ⚠️ Не удалось пропатчить {widget_class.__name__}: {e}")
        
        # Патчим метод save_text у StickerWidget
        try:
            original_save_text = StickerWidget.save_text
            
            def patched_save_text(self, event):
                # Вызываем оригинальный метод с event
                original_save_text(self, event)
                # Сохраняем после изменения текста
                try:
                    if hasattr(self, 'canvas') and hasattr(self.canvas, 'master'):
                        desktop = self.canvas.master
                        if hasattr(desktop, 'autosafe'):
                            desktop.autosafe.save_all()
                except:
                    pass
            
            StickerWidget.save_text = patched_save_text
            print("[AutoSafe] ✅ Патчинг сохранения текста стикера")
        except Exception as e:
            print(f"[AutoSafe] ⚠️ Не удалось пропатчить StickerWidget.save_text: {e}")
    
    def _add_to_context_menu(self):
        """Добавление пункта в контекстное меню"""
        try:
            if hasattr(self.desktop, 'context_menu'):
                self.desktop.context_menu.add_separator()
                self.desktop.context_menu.add_command(
                    label='💾 Сохранить состояние сейчас',
                    command=self.force_save
                )
                self.desktop.context_menu.add_command(
                    label='📊 Статус автосохранения',
                    command=self.show_status
                )
        except Exception as e:
            print(f"[AutoSafe] ⚠️ Не удалось добавить пункт в контекстное меню: {e}")
    
    def _start_auto_save(self):
        """Запуск фонового автоматического сохранения"""
        def saver():
            while self._is_running:
                try:
                    time.sleep(self.SAVE_INTERVAL)
                    if not self._save_in_progress:
                        if self._has_changes():
                            self.save_all()
                except Exception as e:
                    print(f"[AutoSafe] ⚠️ Ошибка в фоновом сохранении: {e}")
        
        thread = threading.Thread(target=saver, daemon=True, name="AutoSafe")
        thread.start()
    
    def _has_changes(self):
        """Проверка наличия изменений с последнего сохранения"""
        try:
            current_state = self._get_current_state_hash()
            if current_state != self._last_state_hash:
                self._last_state_hash = current_state
                return True
            return False
        except:
            return True
    
    def _get_current_state_hash(self):
        """Получение хеша текущего состояния"""
        try:
            state = {
                'shortcuts': self._get_shortcuts_data(),
                'widgets': self._get_widgets_data(),
                'theme': self._get_theme_data(),
                'wallpaper': self._get_wallpaper_data()
            }
            state_str = json.dumps(state, sort_keys=True, default=str)
            return hashlib.md5(state_str.encode()).hexdigest()
        except:
            return str(time.time())
    
    def _get_shortcuts_data(self):
        """Получение данных ярлыков для хеша"""
        if not self.desktop:
            return []
        
        shortcuts = []
        try:
            for icon in self.desktop.canvas.desktop_icons:
                if icon.is_trash:
                    continue
                if hasattr(icon, 'is_virtual_item') and icon.is_virtual_item:
                    continue
                if hasattr(icon, 'is_file_item') and icon.is_file_item:
                    continue
                
                icon_dict = icon.to_dict()
                if icon_dict.get('command'):
                    shortcuts.append(icon_dict)
        except:
            pass
        
        return sorted(shortcuts, key=lambda x: x.get('text', ''))
    
    def _get_widgets_data(self):
        """Получение данных виджетов для хеша"""
        if not self.desktop:
            return []
        
        widgets = []
        try:
            for widget in self.desktop.widgets:
                if hasattr(widget, 'frame') and widget.frame and widget.frame.winfo_exists():
                    config = widget.get_config()
                    if config:
                        widgets.append(config)
        except:
            pass
        
        return sorted(widgets, key=lambda x: (x.get('x', 0), x.get('y', 0), x.get('type', '')))
    
    def _get_theme_data(self):
        """Получение данных темы для хеша"""
        if not self.desktop:
            return {}
        return {'theme': self.desktop.current_theme}
    
    def _get_wallpaper_data(self):
        """Получение данных обоев для хеша"""
        if not self.desktop or not self.desktop.wallpaper_manager:
            return {}
        return {
            'path': self.desktop.wallpaper_manager.wallpaper_path,
            'style': self.desktop.wallpaper_manager.wallpaper_style
        }
    
    def save_all(self):
        """Сохранение всего состояния рабочего стола"""
        if self._save_in_progress:
            return False
        
        self._save_in_progress = True
        self._save_counter += 1
        
        try:
            # Сохраняем всё
            shortcuts = self._save_shortcuts()
            widgets = self._save_widgets()
            theme = self._save_theme()
            wallpaper = self._save_wallpaper()
            
            # Сохраняем состояние автосохранения
            state = {
                'timestamp': datetime.now().isoformat(),
                'counter': self._save_counter,
                'shortcuts': shortcuts,
                'widgets': widgets,
                'theme': theme,
                'wallpaper': wallpaper
            }
            
            self._save_state(state)
            self._last_save_time = time.time()
            self._last_state_hash = self._get_current_state_hash()
            
            return True
            
        except Exception as e:
            print(f"[AutoSafe] ❌ Ошибка сохранения: {e}")
            return False
        finally:
            self._save_in_progress = False
    
    def _save_shortcuts(self):
        """Сохранение ярлыков рабочего стола"""
        if not self.desktop:
            return None
        
        shortcuts = []
        try:
            for icon in self.desktop.canvas.desktop_icons:
                if icon.is_trash:
                    continue
                if hasattr(icon, 'is_virtual_item') and icon.is_virtual_item:
                    continue
                if hasattr(icon, 'is_file_item') and icon.is_file_item:
                    continue
                
                icon_dict = icon.to_dict()
                if icon_dict.get('command'):
                    shortcuts.append(icon_dict)
        except:
            pass
        
        try:
            with open(self.shortcuts_path, 'w', encoding='utf-8') as f:
                json.dump(shortcuts, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[AutoSafe] ⚠️ Ошибка сохранения ярлыков: {e}")
        
        return shortcuts
    
    def _save_widgets(self):
        """Сохранение виджетов (включая ПОЛОЖЕНИЕ НА ЭКРАНЕ)"""
        if not self.desktop:
            return None
        
        widgets = []
        try:
            for widget in self.desktop.widgets:
                if hasattr(widget, 'frame') and widget.frame and widget.frame.winfo_exists():
                    config = widget.get_config()
                    if config:
                        config['x'] = widget.x
                        config['y'] = widget.y
                        widgets.append(config)
        except:
            pass
        
        try:
            with open(self.widgets_path, 'w', encoding='utf-8') as f:
                json.dump(widgets, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[AutoSafe] ⚠️ Ошибка сохранения виджетов: {e}")
        
        return widgets
    
    def _save_theme(self):
        """Сохранение темы"""
        if not self.desktop:
            return None
        
        theme_data = {'theme': self.desktop.current_theme}
        
        try:
            with open(self.theme_path, 'w', encoding='utf-8') as f:
                json.dump(theme_data, f, indent=4)
        except Exception as e:
            print(f"[AutoSafe] ⚠️ Ошибка сохранения темы: {e}")
        
        return theme_data
    
    def _save_wallpaper(self):
        """Сохранение настроек обоев"""
        if not self.desktop or not self.desktop.wallpaper_manager:
            return None
        
        wallpaper_data = {
            'path': self.desktop.wallpaper_manager.wallpaper_path,
            'style': self.desktop.wallpaper_manager.wallpaper_style
        }
        
        try:
            with open(self.wallpaper_path, 'w', encoding='utf-8') as f:
                json.dump(wallpaper_data, f, indent=4)
        except Exception as e:
            print(f"[AutoSafe] ⚠️ Ошибка сохранения обоев: {e}")
        
        return wallpaper_data
    
    def _save_state(self, state):
        """Сохранение состояния в файл"""
        try:
            with open(self.autosave_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[AutoSafe] ⚠️ Ошибка сохранения состояния: {e}")
            return False
    
    def force_save(self):
        """Принудительное сохранение (вызывается из контекстного меню)"""
        print("[AutoSafe] 💾 Принудительное сохранение...")
        return self.save_all()
    
    def show_status(self):
        """Показать статус автосохранения в диалоге"""
        if not self.desktop:
            messagebox.showinfo("📊 Статус автосохранения", "AutoSafe не инициализирован")
            return
        
        status = self.get_status()
        info = [
            f"🔄 Автосохранение: {'✅ Активно' if status['is_running'] else '❌ Остановлено'}",
            f"📊 Сохранений: {status['save_counter']}",
            f"⏱️ Последнее: {status['last_save_time']}",
            f"⏱️ Интервал: {status['save_interval']} сек",
            f"📁 Папка: {status['config_path']}",
            "",
            "📄 Файлы:",
            f"  Ярлыки: {'✅' if status['files']['shortcuts'] else '❌'}",
            f"  Виджеты: {'✅' if status['files']['widgets'] else '❌'}",
            f"  Тема: {'✅' if status['files']['theme'] else '❌'}",
            f"  Обои: {'✅' if status['files']['wallpaper'] else '❌'}",
            f"  Состояние: {'✅' if status['files']['autosave'] else '❌'}",
        ]
        messagebox.showinfo("📊 Статус автосохранения", "\n".join(info))
    
    def get_status(self):
        """Получение статуса автосохранения"""
        return {
            'is_running': self._is_running,
            'save_counter': self._save_counter,
            'last_save_time': datetime.fromtimestamp(self._last_save_time).strftime('%H:%M:%S') if self._last_save_time else 'Никогда',
            'save_interval': self.SAVE_INTERVAL,
            'config_path': self.config_path,
            'files': {
                'shortcuts': os.path.exists(self.shortcuts_path),
                'widgets': os.path.exists(self.widgets_path),
                'theme': os.path.exists(self.theme_path),
                'wallpaper': os.path.exists(self.wallpaper_path),
                'autosave': os.path.exists(self.autosave_path),
            }
        }
    
    def stop(self):
        """Остановка автосохранения"""
        self._is_running = False
        print("[AutoSafe] ⏹️ Остановлен")

# ==================== MultiMonitorManager (ИСПРАВЛЕННЫЙ) ====================

import os
import sys
import json
import threading
import subprocess
import platform
import random
from datetime import datetime

# Проверка библиотек
try:
    from screeninfo import get_monitors
    SCREENINFO_AVAILABLE = True
except ImportError:
    SCREENINFO_AVAILABLE = False

try:
    from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QTextEdit
    from PyQt6.QtCore import Qt, QTimer, QPoint, QDateTime
    from PyQt6.QtGui import QFont, QPalette, QColor, QScreen, QGuiApplication, QPainter, QBrush, QLinearGradient
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

try:
    if platform.system() == "Windows":
        import ctypes
        from ctypes import wintypes
        WIN32_AVAILABLE = True
    else:
        WIN32_AVAILABLE = False
except ImportError:
    WIN32_AVAILABLE = False


class MultiMonitorManager:
    """Менеджер нескольких мониторов с точными размерами и синхронизацией узоров темы"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance
    
    def __init__(self, bitos=None):
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._initialized = True
        self.bitos = bitos
        self.main_desktop = None
        self.monitors = []
        self.processes = {}
        self.is_running = True
        
        self._init_paths()
        self._detect_monitors_accurate()
        
    def _init_paths(self):
        try:
            if self.bitos and hasattr(self.bitos, 'base_path'):
                base_path = self.bitos.base_path
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))
            
            self.config_path = os.path.join(base_path, "System", "Config")
            self.temp_dir = os.path.join(base_path, "System", "Temp")
            
            os.makedirs(self.config_path, exist_ok=True)
            os.makedirs(self.temp_dir, exist_ok=True)
            
            self.monitor_config_path = os.path.join(self.config_path, "monitors.json")
        except:
            base_path = os.path.dirname(os.path.abspath(__file__))
            self.config_path = os.path.join(base_path, "System", "Config")
            self.temp_dir = os.path.join(base_path, "System", "Temp")
            self.monitor_config_path = os.path.join(self.config_path, "monitors.json")
            os.makedirs(self.config_path, exist_ok=True)
            os.makedirs(self.temp_dir, exist_ok=True)
    
    def _detect_monitors_accurate(self):
        self.monitors = []
        
        if WIN32_AVAILABLE:
            try:
                monitors = self._get_monitors_win32()
                if monitors:
                    self.monitors = monitors
                    self._save_monitor_config()
                    return
            except Exception as e:
                pass
        
        if PYQT_AVAILABLE and not self.monitors:
            try:
                monitors = self._get_monitors_pyqt()
                if monitors:
                    self.monitors = monitors
                    self._save_monitor_config()
                    return
            except Exception as e:
                pass
        
        if SCREENINFO_AVAILABLE and not self.monitors:
            try:
                for i, m in enumerate(get_monitors()):
                    self.monitors.append({
                        'index': i,
                        'name': m.name or f"Монитор {i+1}",
                        'width': m.width,
                        'height': m.height,
                        'x': m.x,
                        'y': m.y,
                        'is_primary': m.is_primary
                    })
            except Exception as e:
                pass
        
        if not self.monitors:
            self.monitors = [
                {'index': 0, 'name': 'Монитор 1', 'width': 1920, 'height': 1080, 'x': 0, 'y': 0, 'is_primary': True}
            ]
        
        self._save_monitor_config()
    
    def _get_monitors_win32(self):
        monitors = []
        try:
            user32 = ctypes.windll.user32
            MONITORENUMPROC = ctypes.WINFUNCTYPE(
                ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.POINTER(wintypes.RECT), ctypes.c_double
            )
            monitors_list = []
            
            def callback(hMonitor, hdcMonitor, lprcMonitor, dwData):
                class MONITORINFOEXW(ctypes.Structure):
                    _fields_ = [
                        ("cbSize", wintypes.DWORD),
                        ("rcMonitor", wintypes.RECT),
                        ("rcWork", wintypes.RECT),
                        ("dwFlags", wintypes.DWORD),
                        ("szDevice", wintypes.WCHAR * 32)
                    ]
                monitor_info = MONITORINFOEXW()
                monitor_info.cbSize = ctypes.sizeof(MONITORINFOEXW)
                
                if user32.GetMonitorInfoW(hMonitor, ctypes.byref(monitor_info)):
                    name = monitor_info.szDevice
                    rc = monitor_info.rcMonitor
                    is_primary = bool(monitor_info.dwFlags & 0x00000001)
                    monitors_list.append({
                        'name': name, 'x': rc.left, 'y': rc.top,
                        'width': rc.right - rc.left, 'height': rc.bottom - rc.top,
                        'is_primary': is_primary
                    })
                return 1
            
            callback_func = MONITORENUMPROC(callback)
            hdc = user32.GetDC(0)
            if user32.EnumDisplayMonitors(hdc, None, callback_func, 0):
                monitors_list.sort(key=lambda m: m['x'])
                for i, mon in enumerate(monitors_list):
                    monitors.append({
                        'index': i, 'name': mon['name'], 'width': mon['width'], 'height': mon['height'],
                        'x': mon['x'], 'y': mon['y'], 'is_primary': mon['is_primary']
                    })
                user32.ReleaseDC(0, hdc)
        except:
            pass
        return monitors
    
    def _get_monitors_pyqt(self):
        monitors = []
        try:
            app = QApplication.instance() or QApplication(sys.argv)
            screens = QGuiApplication.screens()
            for i, screen in enumerate(screens):
                geom = screen.geometry()
                monitors.append({
                    'index': i, 'name': screen.name(), 'width': geom.width(), 'height': geom.height(),
                    'x': geom.x(), 'y': geom.y(), 'is_primary': screen == QGuiApplication.primaryScreen()
                })
        except:
            pass
        return monitors
    
    def _save_monitor_config(self):
        try:
            config = {'monitors': self.monitors, 'saved_at': datetime.now().isoformat()}
            with open(self.monitor_config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except:
            pass

    def _patch_desktop(self, desktop):
        """Интеграционный метод для связывания менеджера с рабочим столом BITOS"""
        self.main_desktop = desktop
        print("[MultiMonitorManager] ✅ Метод _patch_desktop успешно вызван для связи с основным окном.")
        return True
    
    def _create_extra_desktops(self):
        if len(self.monitors) <= 1:
            return
        
        for i, monitor in enumerate(self.monitors):
            if monitor.get('is_primary', False):
                continue
            
            if PYQT_AVAILABLE:
                self._create_pyqt_desktop(i)
            else:
                self._create_tkinter_desktop(i)
    
    def _create_pyqt_desktop(self, monitor_index):
        if monitor_index >= len(self.monitors):
            return False
        
        if monitor_index in self.processes:
            try:
                self.processes[monitor_index].kill()
            except:
                pass
            del self.processes[monitor_index]
        
        script_code = self._generate_accurate_script(monitor_index)
        script_path = os.path.join(self.temp_dir, f"monitor_{monitor_index}.py")
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_code)
        
        log_path = os.path.join(self.temp_dir, f"monitor_{monitor_index}_log.txt")
        try:
            python_exe = sys.executable
            with open(log_path, 'w', encoding='utf-8') as log_file:
                process = subprocess.Popen(
                    [python_exe, script_path],
                    stdout=log_file, stderr=subprocess.STDOUT,
                    creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
                )
            self.processes[monitor_index] = process
            return True
        except:
            return False
    
    def _create_tkinter_desktop(self, monitor_index):
        if monitor_index >= len(self.monitors):
            return False
        monitor = self.monitors[monitor_index]
        
        script_code = f'''# -*- coding: utf-8 -*-
import sys, json, tkinter as tk
from datetime import datetime
with open(r"{self.monitor_config_path}", 'r', encoding='utf-8') as f:
    config = json.load(f)
monitor = config['monitors'][{monitor_index}]
root = tk.Tk()
root.overrideredirect(True)
root.geometry(f"{{monitor['width']}}x{{monitor['height']}}+{{monitor['x']}}+{{monitor['y']}}")
root.configure(bg='#1e1e2e')
time_label = tk.Label(root, text="", font=('Segoe UI', 64, 'bold'), fg='#cdd6f4', bg='#1e1e2e')
time_label.pack(expand=True)
def update_time():
    time_label.config(text=datetime.now().strftime("%H:%M:%S"))
    root.after(1000, update_time)
update_time()
root.mainloop()
'''
        script_path = os.path.join(self.temp_dir, f"monitor_tk_{monitor_index}.py")
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_code)
        
        try:
            process = subprocess.Popen(
                [sys.executable, script_path],
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
            )
            self.processes[monitor_index] = process
            return True
        except:
            return False
    
    def _generate_accurate_script(self, monitor_index):
        theme_cfg_path = os.path.join(self.config_path, "theme.cfg")
        current_theme_name = "Базовая"
        
        if os.path.exists(theme_cfg_path):
            try:
                with open(theme_cfg_path, 'r', encoding='utf-8') as f:
                    theme_data = json.load(f)
                    current_theme_name = theme_data.get('theme', 'Базовая')
            except:
                pass

        themes_palette = {
            "Базовая": {"bg": "#2980B9", "canvas_bg": "#0a0a2a", "accent": "#00D4FF", "panel": "#1F618D", "text": "#cdd6f4"},
            "Техно": {"bg": "#1B5E20", "canvas_bg": "#0a0a1a", "accent": "#00FF00", "panel": "#0D3B0D", "text": "#00FF00"},
            "Эко": {"bg": "#27AE60", "canvas_bg": "#0a2a1a", "accent": "#2ECC71", "panel": "#1E8449", "text": "#FFFFFF"},
            "Космо": {"bg": "#0B1B3D", "canvas_bg": "#050a1a", "accent": "#87CEEB", "panel": "#060D1A", "text": "#87CEEB"}
        }
        
        selected_colors = themes_palette.get(current_theme_name, themes_palette["Базовая"])
        bg_color = selected_colors["canvas_bg"]
        accent_color = selected_colors["accent"]
        panel_color = selected_colors["panel"]
        text_color = selected_colors["text"]

        # Безопасное определение батареи до генерации f-строки
        percent = 100
        charging = "Сеть"
        try:
            import psutil
            battery = psutil.sensors_battery()
            if battery:
                percent = battery.percent
                charging = "Заряжается" if battery.power_plugged else "Разряжается"
        except:
            pass

        return f'''# -*- coding: utf-8 -*-
import sys, os, json, random
from pathlib import Path
from datetime import datetime

try:
    from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QTextEdit
    from PyQt6.QtCore import Qt, QTimer, QDateTime, QPoint
    from PyQt6.QtGui import QFont, QPainter, QColor, QBrush, QLinearGradient
except:
    sys.exit(1)

with open(r"{self.monitor_config_path}", 'r', encoding='utf-8') as f:
    config = json.load(f)

monitor = config['monitors'][{monitor_index}]
MONITOR_X = monitor['x']
MONITOR_Y = monitor['y']
MONITOR_W = monitor['width']
MONITOR_H = monitor['height']

class BeautyPatternWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bg_color = QColor("{bg_color}")
        self.stars = []
        for _ in range(100):
            x = random.randint(0, MONITOR_W)
            y = random.randint(0, MONITOR_H)
            size = random.randint(1, 3)
            speed = random.uniform(0.1, 0.5)
            brightness = random.randint(50, 255)
            self.stars.append([x, y, size, speed, brightness])
            
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.animate_stars)
        self.anim_timer.start(80)

    def animate_stars(self):
        for star in self.stars:
            star[4] += random.randint(-15, 15)
            star[4] = max(50, min(255, star[4]))
            star[1] += star[3]
            if star[1] > MONITOR_H:
                star[1] = 0
                star[0] = random.randint(0, MONITOR_W)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, self.bg_color)
        
        r, g, b = self.bg_color.red(), self.bg_color.green(), self.bg_color.blue()
        bottom_color = QColor(
            min(255, int(r + (255 - r) * 0.15)),
            min(255, int(g + (255 - g) * 0.15)),
            min(255, int(b + (255 - b) * 0.15))
        )
        gradient.setColorAt(1.0, bottom_color)
        painter.fillRect(self.rect(), QBrush(gradient))
        
        for x, y, size, speed, brightness in self.stars:
            color = QColor(brightness, brightness, brightness)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPoint(int(x), int(y)), size, size)


class MonitorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(MONITOR_X, MONITOR_Y, MONITOR_W, MONITOR_H)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnBottomHint)
        
        self.background_widget = BeautyPatternWidget(self)
        self.setCentralWidget(self.background_widget)
        
        root_layout = QVBoxLayout(self.background_widget)
        root_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        center_box = QWidget(self)
        center_box.setStyleSheet("background: transparent;")
        root_layout.addWidget(center_box)
        
        main_layout = QVBoxLayout(center_box)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.setSpacing(20)
        
        self.time_label = QLabel(self)
        self.time_label.setStyleSheet("color: {text_color}; font-size: 75px; font-family: 'Segoe UI', Arial; font-weight: bold;")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.time_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.date_label = QLabel(self)
        self.date_label.setStyleSheet("color: {text_color}; font-size: 22px; font-family: 'Segoe UI', Arial; opacity: 0.8;")
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.date_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.battery_label = QLabel("СИСТЕМА ПИТАНИЯ: {percent}% [{charging}]", self)
        self.battery_label.setStyleSheet("color: {accent_color}; font-size: 16px; font-family: 'Segoe UI', Arial; font-weight: bold;")
        self.battery_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.battery_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.notes_label = QLabel("ЗАМЕТКИ И ЗАДАЧИ", self)
        self.notes_label.setStyleSheet("color: {text_color}; font-size: 14px; font-family: 'Segoe UI', Arial; font-weight: bold; opacity: 0.6; margin-top: 15px;")
        self.notes_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.notes_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.notes_edit = QTextEdit(self)
        self.notes_edit.setFixedSize(500, 260)
        self.notes_edit.setStyleSheet(
            "background-color: {panel_color}; color: {text_color}; border: 2px solid {accent_color}; "
            "border-radius: 12px; font-size: 15px; font-family: 'Segoe UI', sans-serif; padding: 12px;"
        )
        self.notes_path = Path("C:/Users/Викторовна/OneDrive/Рабочий стол/System/Config/desktop_notes.txt")
        self.load_notes()
        self.notes_edit.textChanged.connect(self.save_notes)
        main_layout.addWidget(self.notes_edit, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_status)
        self.timer.start(1000)
        self.update_status()

    def update_status(self):
        current = QDateTime.currentDateTime()
        self.time_label.setText(current.toString("HH:mm:ss"))
        months = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]
        days = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
        dt = current.toPyDateTime()
        self.date_label.setText(f"{{dt.day}} {{months[dt.month-1]}} {{dt.year}} г., {{days[dt.weekday()]}}")
        try:
            import psutil
            battery = psutil.sensors_battery()
            if battery:
                state = "Заряжается" if battery.power_plugged else "Разряжается"
                self.battery_label.setText(f"СИСТЕМА ПИТАНИЯ: {{battery.percent}}% [{{state}}]")
        except:
            pass

    def load_notes(self):
        if self.notes_path.exists():
            try:
                self.notes_edit.setPlainText(self.notes_path.read_text(encoding='utf-8'))
            except:
                pass

    def save_notes(self):
        try:
            self.notes_path.parent.mkdir(parents=True, exist_ok=True)
            self.notes_path.write_text(self.notes_edit.toPlainText(), encoding='utf-8')
        except:
            pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MonitorWindow()
    window.show()
    sys.exit(app.exec())
'''

    def show_all_desktops(self):
        self._create_extra_desktops()
    
    def debug_windows(self):
        pass
    
    def get_monitor_info(self, index=None):
        if index is not None:
            return self.monitors[index] if 0 <= index < len(self.monitors) else None
        return self.monitors.copy()
    
    def refresh_monitors(self):
        self.stop()
        self._detect_monitors_accurate()
        self._create_extra_desktops()
    
    def stop(self):
        self.is_running = False
        for p in list(self.processes.values()):
            try:
                if p.poll() is None:
                    p.terminate()
                    p.wait(timeout=3)
            except:
                try:
                    p.kill()
                except:
                    pass
        self.processes.clear()
    
    def __del__(self):
        self.stop()

# ==================== КЛАСС: UpdateManager (ИСПРАВЛЕННЫЙ) ====================
class UpdateManager:
    """
    Менеджер обновлений BITOS
    - Проверка обновлений на GitHub
    - Скачивание и установка
    - Автоматическая перезагрузка
    - Отслеживание статуса
    """
    
    def __init__(self, bitos_instance):
        self.bitos = bitos_instance
        # Нормализуем текущую версию для сравнения
        self.current_version = self._normalize_version(
            bitos_instance.version if hasattr(bitos_instance, 'version') else "06V6"
        )
        self.current_version_raw = bitos_instance.version if hasattr(bitos_instance, 'version') else "06V6"
        self.repo_url = "https://api.github.com/repos/Saryanich/BITOS/releases/latest"
        
        # Состояние обновления
        self.latest_version = None
        self.latest_version_raw = None
        self.download_url = None
        self.release_notes = None
        self.update_available = False
        self.download_progress = 0
        self.is_downloading = False
        self.is_installing = False
        
        # Пути
        self.temp_dir = os.path.join(bitos_instance.system_paths["temp"], "updates")
        self.update_status_file = os.path.join(bitos_instance.system_paths["config"], "update_status.json")
        self.backup_dir = os.path.join(bitos_instance.system_paths["temp"], "backup")
        
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Загрузка сохранённого статуса
        self.status = self._load_status()
        
        # Флаг для UI
        self.check_in_progress = False
        self.last_check_time = None
        self.error_message = None
        
        print(f"[UpdateManager] ✅ Инициализирован. Версия: {self.current_version_raw}")
        print(f"[UpdateManager] 📌 Нормализованная версия для сравнения: {self.current_version}")
    
    def _normalize_version(self, version):
        """
        Нормализация версии для сравнения
        Преобразует "06V6_20.06" и "06V6" в сопоставимый формат
        
        Примеры:
        - "06V6_20.06" -> "6.6.20.06"
        - "06V6" -> "6.6.0"
        - "v1.2.3" -> "1.2.3"
        """
        # Убираем префикс v
        v = version.replace('v', '').strip()
        
        # Заменяем V на точку (06V6 -> 06.6)
        v = v.replace('V', '.')
        
        # Если есть подчёркивание, заменяем на точку
        v = v.replace('_', '.')
        
        # Разбиваем на части
        parts = v.split('.')
        
        # Нормализуем каждую часть (убираем ведущие нули)
        normalized_parts = []
        for part in parts:
            try:
                # Пытаемся преобразовать в число
                num = int(part)
                normalized_parts.append(str(num))
            except ValueError:
                # Если не число, оставляем как есть
                normalized_parts.append(part)
        
        # Собираем обратно
        return '.'.join(normalized_parts)
    
    def _parse_version_parts(self, version):
        """
        Разбор версии на числовые компоненты для сравнения
        """
        normalized = self._normalize_version(version)
        parts = normalized.split('.')
        result = []
        for p in parts:
            try:
                result.append(int(p))
            except ValueError:
                result.append(p)
        return result
    
    def _compare_versions(self, v1, v2):
        """
        Сравнение версий с поддержкой форматов:
        - "06V6" и "06V6_20.06"
        - "v1.2.3" и "1.2.3"
        
        Returns:
            1 if v1 > v2, -1 if v1 < v2, 0 if equal
        """
        parts1 = self._parse_version_parts(v1)
        parts2 = self._parse_version_parts(v2)
        
        # Сравниваем по частям
        for i in range(max(len(parts1), len(parts2))):
            p1 = parts1[i] if i < len(parts1) else 0
            p2 = parts2[i] if i < len(parts2) else 0
            
            # Если оба числа - сравниваем как числа
            if isinstance(p1, int) and isinstance(p2, int):
                if p1 > p2:
                    return 1
                elif p1 < p2:
                    return -1
            else:
                # Если строки - сравниваем как строки
                s1 = str(p1).lower()
                s2 = str(p2).lower()
                if s1 > s2:
                    return 1
                elif s1 < s2:
                    return -1
        
        return 0
    
    def _load_status(self):
        """Загрузка статуса обновления"""
        if os.path.exists(self.update_status_file):
            try:
                with open(self.update_status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_status(self):
        """Сохранение статуса обновления"""
        try:
            with open(self.update_status_file, 'w', encoding='utf-8') as f:
                json.dump(self.status, f, indent=4, ensure_ascii=False)
        except:
            pass
    
    def check_for_updates(self, callback=None):
        """
        Проверка наличия обновлений на GitHub
        
        Args:
            callback: функция обратного вызова (success, version, download_url, release_notes, error)
        
        Returns:
            tuple: (has_update, version, download_url, release_notes)
        """
        if self.check_in_progress:
            if callback:
                callback(False, None, None, None, "Проверка уже выполняется")
            return False, None, None, None
        
        self.check_in_progress = True
        self.error_message = None
        
        try:
            # Проверяем наличие requests
            if not REQUESTS_AVAILABLE:
                self.error_message = "Библиотека requests не установлена. Установите: pip install requests"
                self.check_in_progress = False
                if callback:
                    callback(False, None, None, None, self.error_message)
                return False, None, None, None
            
            # Запрос к GitHub API
            response = requests.get(self.repo_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Получаем версию (убираем 'v' если есть)
                latest_tag_raw = data.get("tag_name", "").replace("v", "").strip()
                self.latest_version_raw = latest_tag_raw
                self.latest_version = self._normalize_version(latest_tag_raw)
                self.download_url = data.get("zipball_url")
                self.release_notes = data.get("body", "Нет описания релиза")
                
                print(f"[UpdateManager] 📌 Сравнение: текущая={self.current_version} vs новая={self.latest_version}")
                
                # Сравниваем версии
                if self._compare_versions(self.latest_version, self.current_version) > 0:
                    self.update_available = True
                    self.status['update_available'] = True
                    self.status['latest_version'] = latest_tag_raw
                    self.status['checked_at'] = datetime.now().isoformat()
                    self._save_status()
                    
                    self.last_check_time = datetime.now()
                    self.check_in_progress = False
                    
                    if callback:
                        callback(True, latest_tag_raw, self.download_url, self.release_notes, None)
                    
                    return True, latest_tag_raw, self.download_url, self.release_notes
                else:
                    self.update_available = False
                    self.status['update_available'] = False
                    self.status['checked_at'] = datetime.now().isoformat()
                    self._save_status()
                    
                    self.last_check_time = datetime.now()
                    self.check_in_progress = False
                    
                    if callback:
                        callback(False, None, None, None, None)
                    
                    return False, None, None, None
            else:
                self.error_message = f"Ошибка API: {response.status_code}"
                self.check_in_progress = False
                if callback:
                    callback(False, None, None, None, self.error_message)
                return False, None, None, None
                
        except requests.exceptions.Timeout:
            self.error_message = "Таймаут подключения к GitHub"
            self.check_in_progress = False
            if callback:
                callback(False, None, None, None, self.error_message)
            return False, None, None, None
            
        except requests.exceptions.ConnectionError:
            self.error_message = "Нет подключения к интернету"
            self.check_in_progress = False
            if callback:
                callback(False, None, None, None, self.error_message)
            return False, None, None, None
            
        except Exception as e:
            self.error_message = f"Ошибка: {str(e)}"
            self.check_in_progress = False
            if callback:
                callback(False, None, None, None, self.error_message)
            return False, None, None, None
    
    def download_update(self, progress_callback=None, complete_callback=None):
        """
        Скачивание обновления с GitHub
        
        Args:
            progress_callback: функция (progress_percent, status_text)
            complete_callback: функция (success, file_path, error)
        """
        if not self.update_available or not self.download_url:
            if complete_callback:
                complete_callback(False, None, "Нет доступных обновлений")
            return
        
        if self.is_downloading:
            if complete_callback:
                complete_callback(False, None, "Скачивание уже выполняется")
            return
        
        self.is_downloading = True
        self.download_progress = 0
        
        if progress_callback:
            progress_callback(0, "Начинаем скачивание...")
        
        def download_thread():
            try:
                # Создаём имя файла
                filename = f"bitos_update_{self.latest_version_raw}.zip"
                filepath = os.path.join(self.temp_dir, filename)
                
                # Скачиваем с прогрессом
                import requests
                response = requests.get(self.download_url, stream=True, timeout=30)
                total_size = int(response.headers.get('content-length', 0))
                
                if total_size == 0:
                    self.is_downloading = False
                    if complete_callback:
                        complete_callback(False, None, "Не удалось определить размер файла")
                    return
                
                if progress_callback:
                    progress_callback(0, "Начинаем загрузку...")
                
                with open(filepath, 'wb') as f:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            percent = int((downloaded / total_size) * 100)
                            if progress_callback:
                                progress_callback(percent, f"Скачивание: {percent}% ({downloaded//1024} KB)")
                
                # Проверяем, что файл скачался
                if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                    self.download_progress = 100
                    self.is_downloading = False
                    if complete_callback:
                        complete_callback(True, filepath, None)
                else:
                    self.is_downloading = False
                    if complete_callback:
                        complete_callback(False, None, "Файл не скачан")
                    
            except Exception as e:
                self.is_downloading = False
                if complete_callback:
                    complete_callback(False, None, str(e))
        
        # Запускаем скачивание в потоке
        thread = threading.Thread(target=download_thread, daemon=True)
        thread.start()
    
    def get_status(self):
        """Получение статуса обновлений"""
        return {
            'current_version': self.current_version_raw,
            'latest_version': self.latest_version_raw,
            'update_available': self.update_available,
            'is_downloading': self.is_downloading,
            'download_progress': self.download_progress,
            'last_check': self.last_check_time,
            'error': self.error_message
        }

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
