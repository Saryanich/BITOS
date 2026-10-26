class BITOS:
    """Ядро операционной системы BITOS"""
    
    def __init__(self):
        self.version = "06V6_20.07"
        self.build = "2026.07 BETA"
        self.running = True
        self.start_time = time.time()
        self.current_user = "User"
        self.last_logged_minute = None
        self.check_results = []
        self.security_violations = []
        
        self.input_blocker = InputBlocker()
         
        self.dev_mode = False
        # Общий пароль режима разработчика не должен находиться в исходниках.
        # Задайте BITOS_DEV_PASSWORD в переменных среды перед запуском.
        self.dev_password = os.environ.get("BITOS_DEV_PASSWORD", "")
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
        
        # PIN не создаётся со стандартным значением. При первом входе
        # LoginScreen запросит владельца задать личный PIN.
        
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
                # Не сбрасываем защиту до известного PIN 1234. Удаление
                # повреждённого хеша заставит BITOS запросить новый PIN.
                if os.path.exists(filepath):
                    os.remove(filepath)
                print("  🔄 PIN-хеш сброшен; при следующем входе потребуется создать новый PIN")
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

