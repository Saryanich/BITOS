#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BITOS Installer v1.0
Автономный установщик обновлений
Работает независимо от основной системы
"""

import os
import sys
import json
import time
import shutil
import zipfile
import subprocess
import platform
import threading
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from pathlib import Path

# ============================================================
# КОНСТАНТЫ
# ============================================================

VERSION = "1.0"
UPDATE_DIR = os.path.join("system", "Temp", "updates")
BACKUP_DIR = os.path.join("system", "Temp", "Backup")
CONFIG_DIR = os.path.join("system", "Config")
STATUS_FILE = os.path.join("system", "Config", "update_status.json")
EXTRACT_DIR = os.path.join("system", "Temp", "Extracted")

# ============================================================
# КЛАСС УСТАНОВЩИКА
# ============================================================

class BITOSInstaller:
    """Автономный установщик BITOS"""
    
    def __init__(self, update_zip_path=None):
        self.root = None
        self.canvas = None
        
        # Пути
        # Installer is stored in bitos/system; the project root is bitos/.
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.update_zip = update_zip_path
        self.update_version = "unknown"
        
        # Определяем пути
        self.update_dir = os.path.join(self.base_path, UPDATE_DIR)
        self.backup_dir = os.path.join(self.base_path, BACKUP_DIR)
        self.config_dir = os.path.join(self.base_path, CONFIG_DIR)
        self.extract_dir = os.path.join(self.base_path, EXTRACT_DIR)
        self.status_file = os.path.join(self.base_path, STATUS_FILE)
        
        # Создаём папки
        os.makedirs(self.update_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.extract_dir, exist_ok=True)
        
        # Статус установки
        self.install_status = {
            'phase': 'init',
            'progress': 0,
            'message': 'Подготовка к установке...',
            'sub_message': '',
            'error': None
        }
        
        # Флаги
        self.is_running = True
        self.install_complete = False
        
        # Загружаем информацию об обновлении
        self._load_update_info()
        
        # Создаём окно
        self._create_window()
        
        # Запускаем установку
        self.root.after(500, self._start_installation)
        
        # Запускаем обновление UI
        self._update_ui_loop()
    
    def _load_update_info(self):
        """Загрузка информации об обновлении"""
        if os.path.exists(self.status_file):
            try:
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.update_version = data.get('latest_version', 'unknown')
            except:
                pass
        
        # Если версия не определена, пытаемся из имени файла
        if self.update_version == 'unknown' and self.update_zip:
            filename = os.path.basename(self.update_zip)
            if 'bitos_update_' in filename:
                self.update_version = filename.replace('bitos_update_', '').replace('.zip', '')
    
    def _create_window(self):
        """Создание полноэкранного окна установщика"""
        self.root = tk.Tk()
        self.root.title("BITOS - Установка обновления")
        self.root.overrideredirect(True)
        self.root.state('zoomed')
        
        # Получаем размеры экрана
        self.width = self.root.winfo_screenwidth()
        self.height = self.root.winfo_screenheight()
        
        # Настройка фона
        self.root.configure(bg='#0a0a2a')
        
        # Создаём Canvas для рисования
        self.canvas = tk.Canvas(
            self.root,
            width=self.width,
            height=self.height,
            bg='#0a0a2a',
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Рисуем фон
        self._draw_background()
        
        # Создаём элементы интерфейса
        self._create_ui()
        
        # Центрируем элементы
        self._center_elements()
        
        # Закрытие по ESC (только если не в процессе установки)
        self.root.bind('<Escape>', lambda e: self._on_close())
        
        # Обновляем окно
        self.root.update()
    
    def _draw_background(self):
        """Рисует градиентный фон с узорами"""
        # Градиентный фон
        for i in range(self.height):
            t = i / self.height
            r = int(10 + (40 - 10) * t)
            g = int(10 + (30 - 10) * t)
            b = int(42 + (60 - 42) * t)
            color = f'#{r:02x}{g:02x}{b:02x}'
            self.canvas.create_line(0, i, self.width, i, fill=color, tags='bg')
        
        # Звёзды (декор)
        import random
        for _ in range(150):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            size = random.randint(1, 2)
            brightness = random.randint(100, 255)
            color = f'#{brightness:02x}{brightness:02x}{brightness:02x}'
            self.canvas.create_oval(x-size, y-size, x+size, y+size,
                                   fill=color, outline='', tags='stars')
    
    def _create_ui(self):
        """Создание элементов интерфейса"""
        # Главный контейнер
        self.main_frame = tk.Frame(self.root, bg='#0a0a2a')
        self.main_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Заголовок
        self.title_label = tk.Label(
            self.main_frame,
            text="🔄 УСТАНОВКА ОБНОВЛЕНИЯ",
            font=('Segoe UI', 36, 'bold'),
            bg='#0a0a2a',
            fg='#00D4FF'
        )
        self.title_label.pack(pady=(0, 10))
        
        # Версия
        self.version_label = tk.Label(
            self.main_frame,
            text=f"Версия {self.update_version}",
            font=('Segoe UI', 16),
            bg='#0a0a2a',
            fg='#A8D8EA'
        )
        self.version_label.pack(pady=(0, 30))
        
        # Статус
        self.status_label = tk.Label(
            self.main_frame,
            text="⏳ Подготовка к установке...",
            font=('Segoe UI', 14, 'bold'),
            bg='#0a0a2a',
            fg='#A8D8EA'
        )
        self.status_label.pack(pady=(0, 5))
        
        # Подстатус
        self.sub_status_label = tk.Label(
            self.main_frame,
            text="",
            font=('Segoe UI', 11),
            bg='#0a0a2a',
            fg='#7F8C8D'
        )
        self.sub_status_label.pack(pady=(0, 20))
        
        # Прогресс-бар
        self.progress_frame = tk.Frame(self.main_frame, bg='#0a0a2a')
        self.progress_frame.pack(pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode='determinate',
            length=600,
            height=20
        )
        self.progress_bar.pack()
        
        # Проценты
        self.percent_label = tk.Label(
            self.main_frame,
            text="0%",
            font=('Segoe UI', 13, 'bold'),
            bg='#0a0a2a',
            fg='#00D4FF'
        )
        self.percent_label.pack(pady=(5, 20))
        
        # Детали (логи)
        self.log_frame = tk.Frame(
            self.main_frame,
            bg='#0a0a2a',
            highlightbackground='#1a1a4e',
            highlightthickness=1
        )
        self.log_frame.pack(pady=(10, 0))
        
        self.log_text = tk.Text(
            self.log_frame,
            height=8,
            width=70,
            bg='#0a0a2a',
            fg='#00FF00',
            font=('Consolas', 9),
            bd=0,
            highlightthickness=0,
            wrap=tk.WORD
        )
        self.log_text.pack(padx=10, pady=10)
        
        # Скроллбар для лога
        scrollbar = tk.Scrollbar(
            self.log_frame,
            command=self.log_text.yview,
            bg='#0a0a2a'
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Кнопки (изначально скрыты)
        self.button_frame = tk.Frame(self.main_frame, bg='#0a0a2a')
        
        self.restart_btn = tk.Button(
            self.button_frame,
            text="🔄 Перезагрузить сейчас",
            font=('Segoe UI', 12, 'bold'),
            bg='#27AE60',
            fg='white',
            bd=0,
            padx=30,
            pady=10,
            cursor='hand2',
            command=self._restart_system
        )
        
        self.close_btn = tk.Button(
            self.button_frame,
            text="❌ Закрыть",
            font=('Segoe UI', 12),
            bg='#E74C3C',
            fg='white',
            bd=0,
            padx=30,
            pady=10,
            cursor='hand2',
            command=self._on_close
        )
    
    def _center_elements(self):
        """Центрирование элементов (все уже по центру)"""
        pass
    
    def _update_ui_loop(self):
        """Цикл обновления UI"""
        if not self.is_running:
            return
        
        try:
            # Обновляем статус
            self.status_label.config(text=self.install_status['message'])
            self.sub_status_label.config(text=self.install_status['sub_message'])
            self.progress_bar['value'] = self.install_status['progress']
            self.percent_label.config(text=f"{self.install_status['progress']}%")
            
            # Если есть ошибка
            if self.install_status['error']:
                self.status_label.config(fg='#E74C3C')
                self.percent_label.config(fg='#E74C3C')
            
            # Если установка завершена
            if self.install_complete:
                self._show_complete()
            
            self.root.update()
        except:
            pass
        
        # Продолжаем обновление
        if self.is_running:
            self.root.after(200, self._update_ui_loop)
    
    def _start_installation(self):
        """Запуск процесса установки"""
        threading.Thread(target=self._install_thread, daemon=True).start()
    
    def _install_thread(self):
        """Основной поток установки"""
        try:
            # ===== ФАЗА 1: ПОДГОТОВКА =====
            self._update_status(5, "📦 Подготовка к установке...", "Проверка файлов...")
            time.sleep(0.5)
            
            # Проверяем наличие архива
            if not self.update_zip or not os.path.exists(self.update_zip):
                # Ищем последний архив в папке Updates
                update_files = [f for f in os.listdir(self.update_dir) if f.endswith('.zip')]
                if update_files:
                    latest = sorted(update_files)[-1]
                    self.update_zip = os.path.join(self.update_dir, latest)
                    self._log(f"📦 Найден архив: {os.path.basename(self.update_zip)}")
                else:
                    raise Exception("Архив обновления не найден!")
            
            # ===== ФАЗА 2: СОЗДАНИЕ РЕЗЕРВНОЙ КОПИИ =====
            self._update_status(15, "💾 Создание резервной копии...", "Копирование системных файлов...")
            
            backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(self.backup_dir, f"backup_{backup_timestamp}")
            os.makedirs(backup_path, exist_ok=True)
            
            self._log("📁 Создание резервной копии...")
            
            # Копируем важные файлы
            files_to_backup = ['__init__.py', 'main.pyw']
            for file in files_to_backup:
                src = os.path.join(self.base_path, file)
                if os.path.exists(src):
                    shutil.copy2(src, backup_path)
                    self._log(f"  ✅ {file} скопирован")
            
            # Копируем папку System (конфиги)
            system_backup = os.path.join(backup_path, 'system')
            system_src = os.path.join(self.base_path, 'system')
            if os.path.exists(system_src):
                shutil.copytree(system_src, system_backup)
                self._log(f"  ✅ System/ скопирована")
            
            self._update_status(30, "💾 Резервная копия создана", f"Путь: {backup_path}")
            self._log(f"✅ Резервная копия: {backup_path}")
            time.sleep(0.5)
            
            # ===== ФАЗА 3: РАСПАКОВКА АРХИВА =====
            self._update_status(40, "📂 Распаковка обновления...", "Извлечение файлов...")
            
            # Очищаем папку извлечения
            if os.path.exists(self.extract_dir):
                shutil.rmtree(self.extract_dir)
            os.makedirs(self.extract_dir, exist_ok=True)
            
            self._log(f"📂 Распаковка: {os.path.basename(self.update_zip)}")
            
            with zipfile.ZipFile(self.update_zip, 'r') as zip_ref:
                total_files = len(zip_ref.namelist())
                for i, file_info in enumerate(zip_ref.infolist()):
                    if not self.is_running:
                        return
                    
                    # Обновляем прогресс
                    progress = 40 + int((i / total_files) * 25)
                    self._update_status(
                        progress,
                        f"📂 Распаковка... ({i+1}/{total_files})",
                        f"Файл: {os.path.basename(file_info.filename)}"
                    )
                    zip_ref.extract(file_info, self.extract_dir)
                
                self._log(f"✅ Распаковано {total_files} файлов")
            
            # Находим папку с кодом (GitHub создаёт папку с хешем)
            extracted_items = os.listdir(self.extract_dir)
            extracted_code_dir = None
            for item in extracted_items:
                item_path = os.path.join(self.extract_dir, item)
                if os.path.isdir(item_path) and ('BITOS' in item or ('server' in os.listdir(item_path) and 'ui' in os.listdir(item_path))):
                    extracted_code_dir = item_path
                    break
            
            if not extracted_code_dir:
                # Если не нашли, ищем любую папку с кодом
                for item in extracted_items:
                    item_path = os.path.join(self.extract_dir, item)
                    if os.path.isdir(item_path) and ('system' in os.listdir(item_path) or 'System' in os.listdir(item_path) or ('server' in os.listdir(item_path) and 'ui' in os.listdir(item_path))):
                        extracted_code_dir = item_path
                        break
            
            if not extracted_code_dir:
                extracted_code_dir = self.extract_dir
            
            self._log(f"📁 Код извлечён в: {os.path.basename(extracted_code_dir)}")
            
            # ===== ФАЗА 4: ЗАМЕНА ФАЙЛОВ =====
            self._update_status(70, "⚙️ Замена системных файлов...", "Обновление кода...")
            
            self._log("⚙️ Замена файлов...")
            
            # Список файлов для замены (кроме System)
            for item in os.listdir(extracted_code_dir):
                if not self.is_running:
                    return
                
                if item.lower() == 'system':
                    self._log("  ⏭ System/ пропущена (сохраняем настройки)")
                    continue
                
                src = os.path.join(extracted_code_dir, item)
                dst = os.path.join(self.base_path, item)
                
                try:
                    if os.path.exists(dst):
                        if os.path.isdir(dst):
                            shutil.rmtree(dst)
                            self._log(f"  🗑 Удалена папка: {item}")
                        else:
                            os.remove(dst)
                            self._log(f"  🗑 Удалён файл: {item}")
                    
                    if os.path.isdir(src):
                        shutil.copytree(src, dst)
                        self._log(f"  📁 Скопирована папка: {item}")
                    else:
                        shutil.copy2(src, dst)
                        self._log(f"  📄 Скопирован файл: {item}")
                        
                except Exception as e:
                    self._log(f"  ⚠️ Ошибка копирования {item}: {e}")
                    raise
            
            self._update_status(90, "⚙️ Замена завершена", "Все файлы обновлены")
            self._log("✅ Замена файлов завершена")
            time.sleep(0.5)
            
            # ===== ФАЗА 5: ЗАВЕРШЕНИЕ =====
            self._update_status(95, "✅ Установка завершена!", "Готово к перезагрузке")
            self._log("=" * 50)
            self._log("✅ УСТАНОВКА УСПЕШНО ЗАВЕРШЕНА!")
            self._log(f"📌 Новая версия: {self.update_version}")
            self._log("🔄 Система будет перезагружена")
            self._log("=" * 50)
            
            # Сохраняем статус
            status_data = {
                'install_complete': True,
                'installed_version': self.update_version,
                'installed_at': datetime.now().isoformat(),
                'backup_path': backup_path
            }
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(status_data, f, indent=4)
            
            self.install_complete = True
            self._update_status(100, "✅ Установка завершена!", "Перезагрузка через 10 секунд...")
            
            # ===== ФАЗА 6: ОЖИДАНИЕ ПЕРЕЗАГРУЗКИ =====
            self._log("⏳ Ожидание 10 секунд перед перезагрузкой...")
            
            # Обновляем кнопки
            self.root.after(0, self._show_complete_buttons)
            
            # Ждём 10 секунд с обратным отсчётом
            for i in range(10, 0, -1):
                if not self.is_running:
                    return
                self._update_status(
                    95 + int((10 - i) / 10 * 5),
                    f"🔄 Перезагрузка через {i} секунд...",
                    "Нажмите кнопку для немедленной перезагрузки"
                )
                time.sleep(1)
            
            # Перезагружаем систему
            self._restart_system()
            
        except Exception as e:
            self._update_status(
                0,
                "❌ ОШИБКА УСТАНОВКИ!",
                str(e)
            )
            self._log(f"❌ Ошибка: {e}")
            self.install_status['error'] = str(e)
            
            # Показываем кнопку закрытия
            self.root.after(0, self._show_error_buttons)
            import traceback
            traceback.print_exc()
    
    def _update_status(self, progress, message, sub_message=""):
        """Обновление статуса"""
        self.install_status['progress'] = min(100, max(0, progress))
        self.install_status['message'] = message
        self.install_status['sub_message'] = sub_message
    
    def _log(self, message):
        """Добавление записи в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        try:
            self.log_text.insert(tk.END, log_entry)
            self.log_text.see(tk.END)
            self.root.update()
        except:
            pass
    
    def _show_complete(self):
        """Показ финального экрана"""
        try:
            self.status_label.config(fg='#27AE60')
            self.percent_label.config(fg='#27AE60')
            self.progress_bar['value'] = 100
            self.percent_label.config(text="100%")
        except:
            pass
    
    def _show_complete_buttons(self):
        """Показ кнопок после установки"""
        self.button_frame.pack(pady=(15, 0))
        self.restart_btn.pack(side=tk.LEFT, padx=5)
        self.close_btn.pack(side=tk.LEFT, padx=5)
        
        # Добавляем эффект
        self.restart_btn.config(bg='#27AE60')
        self.restart_btn.bind('<Enter>', lambda e: self.restart_btn.config(bg='#219A52'))
        self.restart_btn.bind('<Leave>', lambda e: self.restart_btn.config(bg='#27AE60'))
    
    def _show_error_buttons(self):
        """Показ кнопок при ошибке"""
        self.button_frame.pack(pady=(15, 0))
        self.close_btn.pack(side=tk.LEFT, padx=5)
        self.close_btn.config(text="❌ Закрыть")
    
    def _restart_system(self):
        """Перезагрузка системы"""
        self._log("🔄 Перезагрузка системы...")
        
        try:
            # Закрываем окно
            self.is_running = False
            
            if platform.system() == "Windows":
                # Запускаем перезагрузку Windows
                subprocess.Popen(["shutdown", "/r", "/t", "2", "/f"], 
                               creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                # Для Linux/Mac
                subprocess.Popen(["reboot"])
            
            # Закрываемся
            self.root.after(100, self._on_close)
            
        except Exception as e:
            self._log(f"⚠️ Ошибка перезагрузки: {e}")
            # Показываем кнопку для ручной перезагрузки
            self._show_complete_buttons()
    
    def _on_close(self):
        """Закрытие установщика"""
        self.is_running = False
        try:
            self.root.destroy()
        except:
            pass
        sys.exit(0)
    
    def run(self):
        """Запуск установщика"""
        self.root.mainloop()


# ============================================================
# ЗАПУСК
# ============================================================

if __name__ == "__main__":
    # Получаем путь к архиву из аргументов командной строки
    update_zip = None
    if len(sys.argv) > 1:
        update_zip = sys.argv[1]
    
    installer = BITOSInstaller(update_zip)
    installer.run()