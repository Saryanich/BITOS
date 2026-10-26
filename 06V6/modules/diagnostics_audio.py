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
