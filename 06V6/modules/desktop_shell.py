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
        
        tk.Label(
            self.dialog,
            text="Пароль задаётся через переменную среды BITOS_DEV_PASSWORD",
            font=('Segoe UI', 9), bg='#F5F7FA', fg='#3498DB', wraplength=350
        ).pack(pady=5)
        
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
        messagebox.showinfo(
            "Режим разработчика",
            "Для включения задайте переменную среды BITOS_DEV_PASSWORD и перезапустите BITOS."
        )
    
    def check_password(self):
        password = self.password_entry.get().strip()
        if not self.bitos.dev_password:
            self.message_label.config(text='Режим разработчика не настроен')
            messagebox.showwarning(
                "Режим разработчика",
                "Для включения задайте переменную среды BITOS_DEV_PASSWORD и перезапустите BITOS."
            )
            return
        if hmac.compare_digest(password, self.bitos.dev_password):
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
                        subprocess.Popen([p])
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

