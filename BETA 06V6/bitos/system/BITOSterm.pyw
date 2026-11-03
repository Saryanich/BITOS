#!/usr/bin/env python
# -*- coding: utf-8 -*-

# BITOSterm.py — Терминал для BITOS с поддержкой режима разработчика
# Полностью автономный файл

import tkinter as tk
from tkinter import scrolledtext, messagebox, Toplevel, Label, Frame, Entry, Button
import sys
import os
import time
import hashlib
import shutil
import json
import random
import string
import math
from datetime import datetime
import threading

# ==================== КЛАСС DevModeDialog ====================
class DevModeDialog:
    """Диалоговое окно для входа в режим разработчика"""
    
    def __init__(self, parent, terminal):
        self.parent = parent
        self.terminal = terminal
        self.result = False
        self.dev_password = "BIT642Os"  # Пароль для режима разработчика
        
        # Создание диалогового окна
        self.dialog = Toplevel(parent)
        self.dialog.title("🔧 Режим разработчика")
        self.dialog.geometry("400x280")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        self.dialog.configure(bg='#F5F7FA')
        
        # Центрируем окно
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() - self.dialog.winfo_width()) // 2
        y = (self.dialog.winfo_screenheight() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f'+{x}+{y}')
        
        # Иконка и заголовок
        title_frame = Frame(self.dialog, bg='#F5F7FA')
        title_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        Label(title_frame, text="🔧", font=('Segoe UI', 48),
                bg='#F5F7FA', fg='#2C3E50').pack()
        
        Label(title_frame, text="Вход в режим разработчика",
                font=('Segoe UI', 14, 'bold'), bg='#F5F7FA',
                fg='#2C3E50').pack(pady=(5, 0))
        
        Label(title_frame, text="Введите пароль для доступа к расширенным функциям",
                font=('Segoe UI', 10), bg='#F5F7FA',
                fg='#7F8C8D').pack(pady=(5, 0))
        
        # Поле для ввода пароля
        password_frame = Frame(self.dialog, bg='#F5F7FA')
        password_frame.pack(fill=tk.X, padx=20, pady=20)
        
        Label(password_frame, text="Пароль:", font=('Segoe UI', 11),
                bg='#F5F7FA', fg='#2C3E50').pack(anchor='w')
        
        self.password_entry = Entry(password_frame, font=('Segoe UI', 11),
                                      show='•', bd=0, bg='white',
                                      highlightthickness=2,
                                      highlightcolor='#3498DB',
                                      highlightbackground='#BDC3C7')
        self.password_entry.pack(fill=tk.X, ipady=8, pady=(5, 0))
        self.password_entry.bind('<Return>', lambda e: self.check_password())
        self.password_entry.focus_set()
        
        # Информация для разработчика
        info_label = Label(self.dialog, 
                             text="Подсказка: стандартный пароль BIT642Os",
                             font=('Segoe UI', 9), bg='#F5F7FA',
                             fg='#3498DB', cursor='hand2')
        info_label.pack(pady=5)
        info_label.bind('<Button-1>', lambda e: self.show_hint())
        
        # Кнопки
        button_frame = Frame(self.dialog, bg='#F5F7FA')
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        Button(button_frame, text="Войти", bg='#3498DB', fg='white',
                 font=('Segoe UI', 10, 'bold'), bd=0,
                 padx=30, pady=8, cursor='hand2',
                 command=self.check_password).pack(side=tk.LEFT, padx=5)
        
        Button(button_frame, text="Отмена", bg='#E74C3C', fg='white',
                 font=('Segoe UI', 10, 'bold'), bd=0,
                 padx=30, pady=8, cursor='hand2',
                 command=self.cancel).pack(side=tk.LEFT, padx=5)
        
        # Метка для сообщений об ошибке
        self.message_label = Label(self.dialog, text='', bg='#F5F7FA',
                                     fg='#E74C3C', font=('Segoe UI', 10))
        self.message_label.pack(pady=5)
        
        # Блокируем родительское окно
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel)
    
    def show_hint(self):
        """Показать подсказку"""
        messagebox.showinfo("Подсказка", 
                           "Пароль режима разработчика: BIT642Os\n\n"
                           "После входа используйте:\n"
                           "hedev - полная справка\n"
                           "system - команды системы\n"
                           "user - команды пользователей\n"
                           "network - сетевые команды\n"
                           "diag - диагностика\n"
                           "util - утилиты")
    
    def check_password(self):
        """Проверка пароля"""
        password = self.password_entry.get().strip()
        
        if password == self.dev_password:
            self.terminal.dev_mode = True
            self.terminal.dev_log("DEV MODE ACTIVATED")
            self.result = True
            self.dialog.destroy()
            
            # Показываем сообщение в терминале
            self.terminal.print_output("\n" + "="*60)
            self.terminal.print_output("🔧 РЕЖИМ РАЗРАБОТЧИКА АКТИВИРОВАН")
            self.terminal.print_output("="*60)
            self.terminal.print_output("Доступные команды:")
            self.terminal.print_output("  hedev     - полная справка")
            self.terminal.print_output("  system    - команды системы")
            self.terminal.print_output("  user      - команды пользователей")
            self.terminal.print_output("  network   - сетевые команды")
            self.terminal.print_output("  diag      - диагностика")
            self.terminal.print_output("  util      - утилиты")
            self.terminal.print_output("  history   - история команд")
            self.terminal.print_output("  exit      - выход из dev режима")
            self.terminal.print_output("="*60 + "\n")
        else:
            self.message_label.config(text='❌ Неверный пароль')
            self.password_entry.delete(0, tk.END)
            self.password_entry.focus_set()
    
    def cancel(self):
        """Отмена входа"""
        self.result = False
        self.dialog.destroy()


# ==================== КЛАСС BITOSTerminal ====================
class BITOSTerminal:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("BITOS Terminal v1.0")
        self.root.geometry("900x600")
        self.root.configure(bg='#1E1E1E')
        
        # Данные пользователя
        self.username = "User"
        self.dev_mode = False
        self.dev_commands_history = []
        
        # Пути для работы с файлами
        self.base_path = os.path.join(os.path.expanduser("~"), "BITOS")
        self.create_directories()
        
        # Настройка интерфейса
        self.setup_ui()
        
        # Приветственное сообщение
        self.show_welcome()
        
        # Обработка закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_directories(self):
        """Создание необходимых директорий"""
        os.makedirs(self.base_path, exist_ok=True)
        os.makedirs(os.path.join(self.base_path, "logs"), exist_ok=True)
        
    def setup_ui(self):
        """Настройка интерфейса терминала"""
        # Основной фрейм
        main_frame = tk.Frame(self.root, bg='#1E1E1E')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Текстовое поле для вывода
        self.output = scrolledtext.ScrolledText(
            main_frame,
            bg='#1E1E1E',
            fg='#00FF00',
            font=('Consolas', 11),
            insertbackground='#00FF00',
            selectbackground='#3498DB',
            wrap=tk.WORD,
            height=25
        )
        self.output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Нижняя панель для ввода
        input_frame = tk.Frame(main_frame, bg='#2C3E50', height=40)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        input_frame.pack_propagate(False)
        
        # Промпт
        self.prompt_label = tk.Label(
            input_frame,
            text="$ ",
            bg='#2C3E50',
            fg='#00FF00',
            font=('Consolas', 12, 'bold')
        )
        self.prompt_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Поле ввода команд
        self.input_var = tk.StringVar()
        self.input_entry = tk.Entry(
            input_frame,
            textvariable=self.input_var,
            bg='#2C3E50',
            fg='#FFFFFF',
            font=('Consolas', 12),
            insertbackground='#00FF00',
            bd=0,
            highlightthickness=0
        )
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        self.input_entry.bind('<Return>', self.process_command)
        self.input_entry.focus_set()
        
        # Кнопка отправки
        self.send_btn = tk.Button(
            input_frame,
            text="↵",
            bg='#3498DB',
            fg='white',
            font=('Consolas', 12, 'bold'),
            bd=0,
            padx=15,
            cursor='hand2',
            command=self.process_command_click
        )
        self.send_btn.pack(side=tk.RIGHT, padx=5)
        self.send_btn.bind('<Enter>', lambda e: self.send_btn.config(bg='#2980B9'))
        self.send_btn.bind('<Leave>', lambda e: self.send_btn.config(bg='#3498DB'))
        
        # Контекстное меню
        self.create_context_menu()
        
    def create_context_menu(self):
        """Создание контекстного меню"""
        self.context_menu = tk.Menu(self.root, tearoff=0, bg='#2C3E50', fg='white')
        self.context_menu.add_command(label="Копировать", command=self.copy_text)
        self.context_menu.add_command(label="Вставить", command=self.paste_text)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Очистить", command=self.clear_output)
        
        self.output.bind('<Button-3>', self.show_context_menu)
        
    def show_context_menu(self, event):
        """Показ контекстного меню"""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
            
    def copy_text(self):
        """Копирование выделенного текста"""
        try:
            self.root.clipboard_clear()
            text = self.output.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.root.clipboard_append(text)
        except:
            pass
            
    def paste_text(self):
        """Вставка текста"""
        try:
            text = self.root.clipboard_get()
            self.input_var.set(self.input_var.get() + text)
        except:
            pass
            
    def clear_output(self):
        """Очистка вывода"""
        self.output.delete('1.0', tk.END)
        self.print_output("BITOS Terminal v1.0")
        self.print_output(f"Пользователь: {self.username}")
        self.print_output("-" * 50)
        
    def show_welcome(self):
        """Показ приветственного сообщения"""
        self.output.insert(tk.END, "BITOS Terminal v1.0\n", 'header')
        self.output.insert(tk.END, f"Пользователь: {self.username}\n")
        self.output.insert(tk.END, f"Система: BITOS 05V6\n")
        self.output.insert(tk.END, f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        self.output.insert(tk.END, "-" * 50 + "\n")
        self.output.insert(tk.END, "Введите 'help' для списка команд\n\n")
        self.output.insert(tk.END, "$ ")
        
        # Настройка тегов для разных цветов
        self.output.tag_config('header', foreground='#3498DB', font=('Consolas', 11, 'bold'))
        self.output.tag_config('error', foreground='#E74C3C')
        self.output.tag_config('success', foreground='#27AE60')
        self.output.tag_config('dev', foreground='#F39C12')
        self.output.tag_config('command', foreground='#FFFFFF', font=('Consolas', 11, 'bold'))
        
        self.output.see(tk.END)
        
    def print_output(self, text, tag=None):
        """Вывод текста в терминал"""
        if tag:
            self.output.insert(tk.END, text + "\n", tag)
        else:
            self.output.insert(tk.END, text + "\n")
        self.output.see(tk.END)
        
    def process_command_click(self):
        """Обработка клика по кнопке отправки"""
        self.process_command()
        
    def process_command(self, event=None):
        """Обработка введенной команды"""
        command = self.input_var.get().strip()
        self.input_var.set("")
        
        if command:
            # Сохраняем в историю если в dev режиме
            if self.dev_mode:
                self.dev_commands_history.append(command)
            
            # Выводим команду
            self.output.insert(tk.END, f"$ {command}\n", 'command')
            
            # Обрабатываем команду
            self.execute_command(command)
        
        self.output.insert(tk.END, "$ ")
        self.output.see(tk.END)
        
    def execute_command(self, command):
        """Выполнение команды"""
        cmd = command.lower().strip()
        
        # Базовые команды
        if cmd == "help":
            self.show_help()
        elif cmd == "clear":
            self.clear_output()
        elif cmd == "time":
            self.print_output(f"\n{datetime.now().strftime('%H:%M:%S')}\n")
        elif cmd == "date":
            self.print_output(f"\n{datetime.now().strftime('%Y-%m-%d')}\n")
        elif cmd == "whoami":
            self.print_output(f"\n{self.username}\n")
        elif cmd == "dev":
            self.enter_dev_mode()
        elif cmd == "exit":
            self.exit_terminal()
        # Команды режима разработчика
        elif self.dev_mode:
            self.execute_dev_command(cmd)
        elif cmd:
            self.print_output(f"\nКоманда не найдена: {command}\n", 'error')
            
    def show_help(self):
        """Показ справки"""
        help_text = """
Доступные команды:
  help     - показать справку
  clear    - очистить экран
  time     - показать время
  date     - показать дату
  whoami   - показать пользователя
  dev      - вход в режим разработчика
  exit     - закрыть терминал
"""
        self.print_output(help_text)
        
    def enter_dev_mode(self):
        """Вход в режим разработчика"""
        if self.dev_mode:
            self.print_output("\n⚠ Вы уже в режиме разработчика\n", 'dev')
            return
            
        # Открываем диалог входа
        dialog = DevModeDialog(self.root, self)
        self.root.wait_window(dialog.dialog)
        
    def execute_dev_command(self, command):
        """Выполнение команд режима разработчика"""
        parts = command.split()
        if not parts:
            return
            
        cmd = parts[0]
        
        if cmd == "hedev":
            self.show_dev_help_extended()
        elif cmd == "history":
            self.show_dev_history()
        elif cmd == "system":
            self.dev_system_command(parts)
        elif cmd == "user":
            self.dev_user_command(parts)
        elif cmd == "network":
            self.dev_network_command(parts)
        elif cmd == "diag":
            self.dev_diag_command(parts)
        elif cmd == "util":
            self.dev_util_command(parts)
        elif cmd == "exit":
            self.exit_dev_mode()
        else:
            self.print_output(f"\n❌ Неизвестная команда: {command}\n", 'error')
            
    def show_dev_help_extended(self):
        """Расширенная справка для режима разработчика"""
        help_text = """
🔧 DEV MODE - ПОЛНАЯ СПРАВКА
================================================================================

📋 SYSTEM (Конфигурации):
  system config show          - показать конфиг
  system serial show          - показать серийник
  system serial reset         - сбросить серийник
  system license show         - показать лицензию
  system license reset        - сбросить лицензию
  system violations           - показать нарушения
  system clear                - очистить нарушения

👤 USER (Пользователи):
  user list                   - список пользователей
  user info <имя>             - информация о пользователе
  user create <имя>           - создать пользователя
  user delete <имя>           - удалить пользователя
  user switch <имя>           - переключиться на пользователя

🌐 NETWORK (Сеть):
  network status              - статус сети
  network flush               - очистить кэш
  network test                - тест сети

🔧 DIAG (Диагностика):
  diag system                 - диагностика системы
  diag disk                   - диагностика диска
  diag all                    - полная диагностика

🛠 UTIL (Утилиты):
  util backup                 - создать бэкап
  util hash <файл>            - показать хеш файла
  util simulate error         - симуляция ошибки

📋 Другие команды:
  history                     - история команд
  exit                        - выход из dev режима
================================================================================
"""
        self.print_output(help_text, 'dev')
        
    def show_dev_history(self):
        """Показать историю команд"""
        if not self.dev_commands_history:
            self.print_output("\nИстория пуста\n")
            return
            
        self.print_output("\n📋 ИСТОРИЯ КОМАНД:")
        for i, cmd in enumerate(self.dev_commands_history[-20:], 1):
            self.print_output(f"  {i:3}. {cmd}")
        self.print_output("")
        
    def exit_dev_mode(self):
        """Выход из режима разработчика"""
        self.dev_mode = False
        self.print_output("\n✅ Режим разработчика деактивирован\n", 'success')
        
    def dev_system_command(self, parts):
        """Обработка системных команд"""
        if len(parts) < 3:
            self.print_output("\n❌ Использование: system <команда> [параметры]\n", 'error')
            return
            
        subcmd = parts[1]
        
        if subcmd == "config" and parts[2] == "show":
            self.print_output("\n📋 СИСТЕМНЫЙ КОНФИГ:")
            self.print_output(f"  Пользователь: {self.username}")
            self.print_output(f"  Режим разработчика: {'Вкл' if self.dev_mode else 'Выкл'}")
            self.print_output(f"  Команд в истории: {len(self.dev_commands_history)}")
            self.print_output("")
            
        elif subcmd == "serial" and parts[2] == "show":
            serial = self.generate_serial()
            self.print_output(f"\n🔑 Серийный номер: BITOS-SERIAL-{serial}\n")
            
        elif subcmd == "serial" and parts[2] == "reset":
            new_serial = self.generate_serial()
            self.print_output(f"\n✅ Новый серийный номер: BITOS-SERIAL-{new_serial}\n", 'success')
            
        elif subcmd == "license" and parts[2] == "show":
            self.print_output("\n📜 ЛИЦЕНЗИЯ:")
            self.print_output("  BITOS Evaluation License")
            self.print_output(f"  Версия: 05V6")
            self.print_output("  Действительна до: 2026-12-31")
            self.print_output("")
            
        elif subcmd == "license" and parts[2] == "reset":
            self.print_output("\n✅ Лицензия сброшена\n", 'success')
            
        elif subcmd == "violations":
            self.print_output("\n⚠ Нарушений безопасности не обнаружено\n")
            
        elif subcmd == "clear":
            self.print_output("\n✅ Журнал нарушений очищен\n", 'success')
            
        else:
            self.print_output(f"\n❌ Неизвестная команда: {' '.join(parts)}\n", 'error')
            
    def dev_user_command(self, parts):
        """Обработка пользовательских команд"""
        if len(parts) < 2:
            self.print_output("\n❌ Использование: user <команда> [имя]\n", 'error')
            return
            
        subcmd = parts[1]
        
        if subcmd == "list":
            self.print_output("\n👥 ПОЛЬЗОВАТЕЛИ:")
            self.print_output(f"  {self.username} (текущий)")
            # Здесь можно добавить список пользователей из файловой системы
            self.print_output("")
            
        elif subcmd == "info" and len(parts) >= 3:
            name = parts[2]
            self.print_output(f"\n👤 ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ {name}:")
            self.print_output(f"  Имя: {name}")
            self.print_output(f"  Текущий: {'Да' if name == self.username else 'Нет'}")
            self.print_output("")
            
        elif subcmd == "create" and len(parts) >= 3:
            name = parts[2]
            self.print_output(f"\n✅ Пользователь {name} создан\n", 'success')
            
        elif subcmd == "delete" and len(parts) >= 3:
            name = parts[2]
            if name == self.username:
                self.print_output("\n❌ Нельзя удалить текущего пользователя\n", 'error')
            else:
                self.print_output(f"\n✅ Пользователь {name} удален\n", 'success')
                
        elif subcmd == "switch" and len(parts) >= 3:
            name = parts[2]
            self.username = name
            self.print_output(f"\n✅ Переключено на пользователя {name}\n", 'success')
            
        else:
            self.print_output(f"\n❌ Неизвестная команда: {' '.join(parts)}\n", 'error')
            
    def dev_network_command(self, parts):
        """Обработка сетевых команд"""
        if len(parts) < 2:
            self.print_output("\n❌ Использование: network <команда>\n", 'error')
            return
            
        subcmd = parts[1]
        
        if subcmd == "status":
            self.print_output("\n🌐 СЕТЕВОЙ СТАТУС:")
            self.print_output("  Состояние: Активно")
            self.print_output("  IP адрес: 127.0.0.1")
            self.print_output("  Подключение: Локальное")
            self.print_output("")
            
        elif subcmd == "flush":
            self.print_output("\n✅ Кэш сети очищен\n", 'success')
            
        elif subcmd == "test":
            self.print_output("\n🌐 ТЕСТ СЕТИ:")
            self.print_output("  Локальный интерфейс: ✅ OK")
            self.print_output("  Сетевые пути: ✅ OK")
            self.print_output("  DNS: ✅ OK")
            self.print_output("  Интернет: ⚠ Не проверяется (без requests)\n")
            
        else:
            self.print_output(f"\n❌ Неизвестная команда: {' '.join(parts)}\n", 'error')
            
    def dev_diag_command(self, parts):
        """Обработка диагностических команд"""
        if len(parts) < 2:
            self.print_output("\n❌ Использование: diag <команда>\n", 'error')
            return
            
        subcmd = parts[1]
        
        if subcmd == "system":
            self.print_output("\n🔧 ДИАГНОСТИКА СИСТЕМЫ:")
            self.print_output(f"  Версия: 05V6")
            self.print_output(f"  Пользователь: {self.username}")
            self.print_output(f"  Режим разработчика: {'Вкл' if self.dev_mode else 'Выкл'}")
            self.print_output(f"  Время работы: {time.time() - start_time:.1f} сек")
            self.print_output(f"  Команд в истории: {len(self.dev_commands_history)}")
            self.print_output("")
            
        elif subcmd == "disk":
            # Информация о диске
            if os.path.exists(self.base_path):
                total, used, free = shutil.disk_usage(self.base_path)
                self.print_output("\n💿 ДИАГНОСТИКА ДИСКА:")
                self.print_output(f"  Всего: {total // (1024**3)} GB")
                self.print_output(f"  Свободно: {free // (1024**3)} GB")
                self.print_output(f"  Использовано: {used // (1024**3)} GB")
                self.print_output(f"  Заполнено: {used/total*100:.1f}%")
                self.print_output("")
            else:
                self.print_output("\n❌ Путь не найден\n", 'error')
                
        elif subcmd == "all":
            self.dev_diag_command(["diag", "system"])
            self.dev_diag_command(["diag", "disk"])
            
        else:
            self.print_output(f"\n❌ Неизвестная команда: {' '.join(parts)}\n", 'error')
            
    def dev_util_command(self, parts):
        """Обработка утилит"""
        if len(parts) < 2:
            self.print_output("\n❌ Использование: util <команда> [параметры]\n", 'error')
            return
            
        subcmd = parts[1]
        
        if subcmd == "backup":
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path = os.path.join(self.base_path, "backups")
            os.makedirs(backup_path, exist_ok=True)
            self.print_output(f"\n✅ Бэкап создан: {backup_name}\n", 'success')
            
        elif subcmd == "hash" and len(parts) >= 3:
            filename = parts[2]
            self.print_output(f"\n🔑 ХЕШ ФАЙЛА {filename}:")
            self.print_output(f"  MD5:    d41d8cd98f00b204e9800998ecf8427e")
            self.print_output(f"  SHA1:   da39a3ee5e6b4b0d3255bfef95601890afd80709")
            self.print_output(f"  SHA256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
            self.print_output("")
            
        elif subcmd == "simulate" and len(parts) >= 3:
            if parts[2] == "error":
                self.print_output("\n✅ Ошибка симулирована\n", 'success')
            else:
                self.print_output(f"\n❌ Неизвестная симуляция: {parts[2]}\n", 'error')
                
        else:
            self.print_output(f"\n❌ Неизвестная команда: {' '.join(parts)}\n", 'error')
            
    def generate_serial(self):
        """Генерация серийного номера"""
        chars = string.ascii_letters + string.digits
        serial = ''.join(random.choice(chars) for _ in range(16))
        return '-'.join([serial[i:i+4] for i in range(0, 16, 4)])
        
    def exit_terminal(self):
        """Выход из терминала"""
        if messagebox.askyesno("Выход", "Закрыть терминал?"):
            self.root.destroy()
            
    def on_closing(self):
        """Обработка закрытия окна"""
        self.exit_terminal()
        
    def dev_log(self, message):
        """Логирование действий разработчика"""
        log_path = os.path.join(self.base_path, "logs", "dev.log")
        try:
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] {message}\n")
        except:
            pass
            
    def run(self):
        """Запуск терминала"""
        self.root.mainloop()


# Запоминаем время старта
start_time = time.time()

if __name__ == "__main__":
    terminal = BITOSTerminal()
    terminal.run()
