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
    
