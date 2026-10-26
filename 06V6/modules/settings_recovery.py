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
        self._create_recovery_tab()
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
        
        # Сброс к известному PIN 1234 удалён; смена PIN доступна выше.
    
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
        
        if not verify_pin_hash(old_pin, saved_hash):
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
            f.write(hash_pin(new_pin))
        
        self.pin_status.config(text="✅ PIN-код успешно изменён!", fg='#27AE60')
        
        for entry in self.pin_entries:
            entry.delete(0, tk.END)
        
        if hasattr(self.bitos, 'security'):
            self.bitos.security.log_pin_change(self.desktop.username)
    
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
        
        # ===== ПЕРЕКЛЮЧАТЕЛЬ РЕЗЕРВНОГО КОПИРОВАНИЯ =====
        backup_toggle_frame = tk.Frame(main_frame, bg='#FDF6E3', relief=tk.RIDGE, bd=1)
        backup_toggle_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.backup_before_install_var = tk.BooleanVar(value=True)
        
        backup_check = tk.Checkbutton(
            backup_toggle_frame,
            text="🗄️ Сделать бекап системы перед установкой?",
            variable=self.backup_before_install_var,
            bg='#FDF6E3', fg='#2C3E50', font=('Segoe UI', 11, 'bold'),
            activebackground='#FDF6E3', selectcolor='#FDF6E3',
            cursor='hand2'
        )
        backup_check.pack(side=tk.LEFT, padx=10, pady=8)
        
        tk.Label(backup_toggle_frame,
                text="(да — сохранятся старая версия, config, security и sounds; нет — установка без бекапа)",
                bg='#FDF6E3', fg='#7F8C8D', font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=(0, 10))
        
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
        
        self.update_manager.is_downloading = True
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
            filename = f"bitos_update_{safe_version_token(self.update_manager.latest_version)}.zip"
            filepath = os.path.join(self.update_manager.temp_dir, filename)
            
            from urllib.parse import urlparse
            allowed_hosts = {
                "api.github.com", "github.com", "codeload.github.com",
                "objects.githubusercontent.com", "release-assets.githubusercontent.com"
            }
            parsed = urlparse(url)
            if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
                raise ValueError("Недоверенный адрес обновления: разрешены только HTTPS-ссылки GitHub")

            headers = {"User-Agent": "BITOS-UpdateManager"}
            part_path = filepath + ".part"
            max_download_size = 1024 * 1024 * 1024
            try:
                with requests.get(url, stream=True, timeout=(10, 60), headers=headers,
                                  allow_redirects=True) as response:
                    response.raise_for_status()
                    final_url = urlparse(response.url)
                    if final_url.scheme != "https" or final_url.hostname not in allowed_hosts:
                        raise ValueError("Перенаправление ведёт на недоверенный адрес")
                    total_size = int(response.headers.get("content-length", 0) or 0)
                    if total_size > max_download_size:
                        raise ValueError("Архив обновления превышает лимит 1 ГБ")

                    progress_callback(0, "Начинаем загрузку...")
                    downloaded = 0
                    with open(part_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=65536):
                            if not chunk:
                                continue
                            downloaded += len(chunk)
                            if downloaded > max_download_size:
                                raise ValueError("Загрузка превышает лимит 1 ГБ")
                            f.write(chunk)
                            if total_size > 0:
                                percent = min(99, int(downloaded * 100 / total_size))
                                progress_callback(percent, f"Скачивание: {percent}% ({downloaded//1024} KB)")
                            else:
                                progress_callback(min(99, downloaded // (1024 * 1024)),
                                                  f"Скачано: {downloaded//1024} KB")

                import zipfile
                with zipfile.ZipFile(part_path, "r") as archive:
                    entries = archive.infolist()
                    if not entries or len(entries) > 20000:
                        raise ValueError("Архив пуст или содержит слишком много элементов")
                    total_uncompressed = sum(info.file_size for info in entries)
                    if total_uncompressed > 1024 * 1024 * 1024:
                        raise ValueError("Распакованный архив превышает лимит 1 ГБ")
                    if any(info.file_size > 256 * 1024 * 1024 for info in entries):
                        raise ValueError("В архиве найден файл больше 256 МБ")
                os.replace(part_path, filepath)
                progress_callback(100, "Скачивание завершено")
                complete_callback(True, filepath, None)
            except Exception:
                try:
                    if os.path.exists(part_path):
                        os.remove(part_path)
                except OSError:
                    pass
                raise
                
        except Exception as e:
            complete_callback(False, None, str(e))
    
    def _download_progress(self, percent, status_text):
        """Обновление прогресса скачивания"""
        self.update_progress_bar['value'] = percent
        self.update_progress_label.config(text=status_text)
        self._log_update(f"📥 {status_text}", "DOWNLOAD")
    
    def _download_complete(self, success, file_path, error):
        """Завершение скачивания"""
        self.update_manager.is_downloading = False
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
        filename = f"bitos_update_{safe_version_token(self.update_manager.latest_version)}.zip"
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
        
        # Считываем Tk-переменную в основном потоке: обращаться к ней из
        # рабочего потока Tkinter небезопасно.
        make_backup = True
        if hasattr(self, 'backup_before_install_var'):
            make_backup = bool(self.backup_before_install_var.get())

        # Запускаем установку в потоке
        thread = threading.Thread(target=self._install_thread, args=(filepath, make_backup))
        thread.daemon = True
        thread.start()
    
    def _install_thread(self, filepath, make_backup=True):
        """Поток для установки обновления"""
        try:
            self.update_manager.is_installing = True
            
            base_path = self.bitos.base_path
            backup_path = None
            
            if make_backup:
                # Создаём резервную копию: старая версия кода + Config/Security/Sounds
                backup_path = os.path.join(self.update_manager.backup_dir, 
                                          f"bitos_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                os.makedirs(backup_path, exist_ok=True)
                
                self.window.after(0, lambda: self.update_progress_label.config(text="📦 Создание резервной копии..."))
                self.window.after(0, lambda: self._log_update("📦 Создание резервной копии текущей версии...", "INSTALL"))
                
                # Копируем текущие файлы (старую версию кода) в резерв.
                # Каждый элемент копируем в своём try/except: если один файл
                # заблокирован (открыт, проверяется антивирусом и т.п.), это
                # не должно обрывать весь процесс резервного копирования.
                backup_errors = 0
                for item in os.listdir(base_path):
                    if item in ['System', 'venv', '__pycache__', '.git']:
                        continue
                    src = os.path.join(base_path, item)
                    dst = os.path.join(backup_path, item)
                    try:
                        if os.path.isdir(src):
                            shutil.copytree(src, dst, ignore_dangling_symlinks=True)
                        else:
                            shutil.copy2(src, dst)
                    except Exception as copy_err:
                        backup_errors += 1
                        print(f"[Install] ⚠️ Не удалось сохранить в бэкап {item}: {copy_err}")
                
                # Дополнительно бекапим Config, Security и Sounds — именно
                # их можно будет восстановить или пересоздать на вкладке
                # "Восстановление системы", отдельно от кода приложения.
                self.window.after(0, lambda: self._log_update("📦 Резервное копирование Config/Security/Sounds...", "INSTALL"))
                for folder_key in ("config", "security", "sounds"):
                    folder_src = self.bitos.system_paths.get(folder_key)
                    if not folder_src or not os.path.exists(folder_src):
                        continue
                    folder_dst = os.path.join(backup_path, "System", os.path.basename(folder_src))
                    try:
                        shutil.copytree(folder_src, folder_dst)
                    except Exception as copy_err:
                        backup_errors += 1
                        print(f"[Install] ⚠️ Не удалось сохранить в бэкап {folder_key}: {copy_err}")
                
                if backup_errors:
                    raise RuntimeError(
                        f"Резервная копия неполная: не удалось сохранить {backup_errors} элементов. "
                        "Установка отменена, чтобы не рисковать текущей версией."
                    )

                # Запоминаем, где лежит бекап, чтобы вкладка восстановления
                # могла им воспользоваться
                self.update_manager.status['last_backup_path'] = backup_path
                self.update_manager.status['last_backup_time'] = datetime.now().isoformat()
                self.update_manager.status['last_backup_from_version'] = self.update_manager.current_version_raw
                self.update_manager._save_status()
            else:
                self.window.after(0, lambda: self._log_update("⏭️ Бекап отключён пользователем — устанавливаем без резервной копии", "WARNING"))
            
            self.window.after(0, lambda: self.update_progress_label.config(text="📦 Распаковка обновления..."))
            self.window.after(0, lambda: self.update_progress_bar.config(value=70))
            self.window.after(0, lambda: self._log_update("📦 Распаковка обновления...", "INSTALL"))
            
            # Безопасная распаковка: запрещаем Zip Slip, symlink entries,
            # архивы чрезмерного размера и подозрительно большие файлы.
            import zipfile
            import stat
            extract_path = os.path.join(self.update_manager.temp_dir, "extracted")
            if os.path.exists(extract_path):
                shutil.rmtree(extract_path, ignore_errors=True)
            os.makedirs(extract_path, exist_ok=True)

            max_entries = 20000
            max_total_uncompressed = 1024 * 1024 * 1024
            max_single_file = 256 * 1024 * 1024
            total_uncompressed = 0

            with zipfile.ZipFile(filepath, 'r') as zip_ref:
                entries = zip_ref.infolist()
                if not entries or len(entries) > max_entries:
                    raise ValueError("Архив пуст или содержит слишком много элементов")

                for info in entries:
                    raw_name = info.filename.replace("\\", "/")
                    parts = raw_name.split("/")
                    mode = (info.external_attr >> 16) & 0o170000
                    if (raw_name.startswith("/") or
                            (parts and ":" in parts[0]) or
                            any(part in ("..", "") for part in parts[:-1]) or
                            mode == stat.S_IFLNK):
                        raise ValueError(f"Недопустимый путь в архиве: {info.filename}")
                    if info.file_size > max_single_file:
                        raise ValueError(f"Слишком большой файл в архиве: {info.filename}")
                    total_uncompressed += info.file_size
                    if total_uncompressed > max_total_uncompressed:
                        raise ValueError("Распакованный архив превышает допустимый размер")

                bad_member = zip_ref.testzip()
                if bad_member:
                    raise ValueError(f"Повреждённый файл в архиве: {bad_member}")

                for info in entries:
                    target = os.path.realpath(os.path.join(extract_path, *info.filename.replace("\\", "/").split("/")))
                    if os.path.commonpath([os.path.realpath(extract_path), target]) != os.path.realpath(extract_path):
                        raise ValueError(f"Путь выходит за пределы архива: {info.filename}")
                    zip_ref.extract(info, extract_path)

            # В релизном ZIP ожидается одна корневая папка проекта.
            extracted_items = os.listdir(extract_path)
            extracted_dirs = [
                os.path.join(extract_path, item) for item in extracted_items
                if os.path.isdir(os.path.join(extract_path, item)) and
                not os.path.islink(os.path.join(extract_path, item))
            ]
            if len(extracted_dirs) != 1:
                raise ValueError("В архиве должна находиться ровно одна корневая папка проекта")
            extracted_dir = extracted_dirs[0]

            self.window.after(0, lambda: self.update_progress_label.config(text="📦 Проверка и замена файлов..."))
            self.window.after(0, lambda: self.update_progress_bar.config(value=85))
            self.window.after(0, lambda: self._log_update("📦 Проверка и замена файлов...", "INSTALL"))

            # Транзакционная замена верхнеуровневых элементов: каждый старый
            # элемент сохраняется до замены; при любой ошибке уже заменённые
            # элементы восстанавливаются в обратном порядке.
            install_errors = []
            rollback_dir = os.path.join(
                self.update_manager.backup_dir,
                "rollback_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            )
            os.makedirs(rollback_dir, exist_ok=True)
            replaced = []
            try:
                for item in os.listdir(extracted_dir):
                    if item == "System":
                        continue
                    src = os.path.join(extracted_dir, item)
                    dst = os.path.join(base_path, item)
                    rollback_item = os.path.join(rollback_dir, item)

                    if os.path.islink(src):
                        raise ValueError(f"Символическая ссылка запрещена: {item}")
                    if os.path.islink(dst):
                        raise ValueError(f"Нельзя безопасно заменить символическую ссылку: {item}")

                    had_original = os.path.lexists(dst)
                    if had_original:
                        if os.path.isdir(dst):
                            shutil.copytree(dst, rollback_item, symlinks=True)
                        else:
                            shutil.copy2(dst, rollback_item)
                    replaced.append((dst, rollback_item, had_original))

                    if os.path.isdir(dst):
                        shutil.rmtree(dst)
                    elif os.path.lexists(dst):
                        os.remove(dst)

                    if os.path.isdir(src):
                        shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)

                # Успешная установка: оставляем резервную копию для ручного отката.
                self.update_manager.status["last_transactional_rollback"] = rollback_dir
                self.update_manager._save_status()
            except Exception as install_error:
                for dst, rollback_item, had_original in reversed(replaced):
                    try:
                        if os.path.isdir(dst) and not os.path.islink(dst):
                            shutil.rmtree(dst)
                        elif os.path.lexists(dst):
                            os.remove(dst)
                        if had_original and os.path.lexists(rollback_item):
                            if os.path.isdir(rollback_item) and not os.path.islink(rollback_item):
                                shutil.copytree(rollback_item, dst, symlinks=True)
                            else:
                                shutil.copy2(rollback_item, dst)
                    except Exception as rollback_error:
                        install_errors.append(
                            f"Не удалось откатить {os.path.basename(dst)}: {rollback_error}"
                        )
                if install_errors:
                    raise RuntimeError(
                        f"{install_error}; ОШИБКИ ОТКАТА: " + "; ".join(install_errors)
                    ) from install_error
                raise
            
            self.window.after(0, lambda: self.update_progress_label.config(text="✅ Установка завершена!"))
            self.window.after(0, lambda: self.update_progress_bar.config(value=100))
            self.window.after(0, lambda: self._log_update("✅ Установка завершена!", "SUCCESS"))
            
            # Сохраняем статус
            self.update_manager.status['install_complete'] = True
            self.update_manager.status['installed_version'] = self.update_manager.latest_version
            self.update_manager.status['installed_at'] = datetime.now().isoformat()
            self.update_manager._save_status()
            
            # Показываем сообщение и перезагружаемся
            self.window.after(1000, self._restart_after_update)
            
        except Exception as e:
            # ВАЖНО: нельзя использовать 'e' внутри lambda, вызываемого
            # асинхронно через .after() — Python автоматически удаляет
            # переменную исключения сразу после выхода из блока except,
            # из-за чего раньше вылетал NameError, маскируя настоящую
            # причину ошибки установки. Сохраняем текст сразу же.
            error_text = str(e)
            self.window.after(0, lambda err=error_text: self._install_error(err))
    
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
            # ВАЖНО: путь к главному скрипту нужно подставить как готовую
            # строку СЕЙЧАС, из текущего процесса. Раньше в шаблоне
            # использовался sys.argv[0] внутри самого restart.pyw — но при
            # его запуске sys.argv[0] указывает на сам restart.pyw, а не на
            # BITOS. В итоге скрипт бесконечно перезапускал сам себя, а
            # приложение так и не открывалось заново (выглядело как
            # "зависание" после установки).
            main_script_path = os.path.abspath(sys.argv[0])
            
            # Создаём скрипт для перезапуска
            restart_script = f'''# -*- coding: utf-8 -*-
import sys, os, subprocess, time

# Ждём закрытия основного процесса
time.sleep(2)

python_exe = sys.executable
script_path = r"{main_script_path}"

if os.path.exists(script_path):
    subprocess.Popen([python_exe, script_path],
                      creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
else:
    # Если файл почему-то не найден - хотя бы не завершаемся молча
    print(f"[restart] Не найден файл для перезапуска: {{script_path}}")
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
            error_text = str(e)
            self.window.after(0, lambda err=error_text: self._log_update(f"⚠️ Ошибка перезапуска: {err}", "WARNING"))
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

    # ==================== ВКЛАДКА: ВОССТАНОВЛЕНИЕ СИСТЕМЫ ====================

    def _get_available_backups(self):
        """Список доступных бекапов (папки bitos_backup_* в backup_dir), новые сверху"""
        backups = []
        backup_dir = self.update_manager.backup_dir
        if not os.path.exists(backup_dir):
            return backups
        
        for name in os.listdir(backup_dir):
            full_path = os.path.join(backup_dir, name)
            if os.path.isdir(full_path) and name.startswith("bitos_backup_"):
                backups.append((name, full_path, os.path.getmtime(full_path)))
        
        backups.sort(key=lambda b: b[2], reverse=True)
        return backups
    
    def _create_recovery_tab(self):
        """Вкладка восстановления системы: бекапы, пересоздание файлов, откат версии"""
        recovery_frame = ttk.Frame(self.notebook)
        self.notebook.add(recovery_frame, text="🩹 Восстановление системы")
        
        main_frame = tk.Frame(recovery_frame, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # ===== ЗАГОЛОВОК =====
        tk.Label(main_frame, text="🩹 Восстановление системы", 
                font=('Segoe UI', 18, 'bold'), bg='white', fg='#2C3E50').pack(anchor='w', pady=(0, 5))
        
        tk.Label(main_frame,
                text="Здесь можно восстановить систему из резервной копии, созданной перед установкой обновления,\n"
                     "пересоздать повреждённые системные файлы заново или полностью откатиться к прошлой версии.",
                font=('Segoe UI', 10), bg='white', fg='#7F8C8D', justify=tk.LEFT).pack(anchor='w', pady=(0, 15))
        
        # ===== ВЫБОР БЕКАПА =====
        backup_select_frame = tk.Frame(main_frame, bg='#F0F3F4', relief=tk.RIDGE, bd=1)
        backup_select_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(backup_select_frame, text="📦 Доступные резервные копии:", 
                font=('Segoe UI', 11, 'bold'), bg='#F0F3F4', fg='#2C3E50').pack(anchor='w', padx=12, pady=(10, 5))
        
        list_row = tk.Frame(backup_select_frame, bg='#F0F3F4')
        list_row.pack(fill=tk.X, padx=12, pady=(0, 10))
        
        self.recovery_backup_combo = ttk.Combobox(list_row, state='readonly', font=('Segoe UI', 10), width=60)
        self.recovery_backup_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Button(list_row, text="🔄 Обновить список", bg='#3498DB', fg='white',
                 font=('Segoe UI', 9, 'bold'), bd=0, padx=12, pady=6,
                 cursor='hand2', command=self._refresh_recovery_backups).pack(side=tk.LEFT, padx=(10, 0))
        
        self._recovery_backup_map = {}
        self._refresh_recovery_backups()
        
        # ===== ДЕЙСТВИЯ =====
        actions_frame = tk.Frame(main_frame, bg='white')
        actions_frame.pack(fill=tk.BOTH, expand=True)
        
        def make_action_card(parent, icon_title, description, btn_text, btn_color, command):
            card = tk.Frame(parent, bg='#FAFBFC', relief=tk.RIDGE, bd=1)
            card.pack(fill=tk.X, pady=6)
            
            text_col = tk.Frame(card, bg='#FAFBFC')
            text_col.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=15, pady=12)
            
            tk.Label(text_col, text=icon_title, font=('Segoe UI', 12, 'bold'),
                    bg='#FAFBFC', fg='#2C3E50').pack(anchor='w')
            tk.Label(text_col, text=description, font=('Segoe UI', 9),
                    bg='#FAFBFC', fg='#7F8C8D', justify=tk.LEFT, wraplength=560).pack(anchor='w', pady=(3, 0))
            
            tk.Button(card, text=btn_text, bg=btn_color, fg='white',
                     font=('Segoe UI', 10, 'bold'), bd=0, padx=18, pady=10,
                     cursor='hand2', command=command).pack(side=tk.RIGHT, padx=15, pady=12)
        
        make_action_card(
            actions_frame,
            "1️⃣ Восстановить системные файлы из бекапа",
            "Вернёт Config, Security и Sounds из выбранной резервной копии поверх текущих. "
            "Код приложения (сама версия) не затрагивается.",
            "♻️ Восстановить", "#E67E22",
            self._recovery_restore_system_files
        )
        
        make_action_card(
            actions_frame,
            "2️⃣ Пересоздать системные файлы",
            "Удалит текущие Config, Security и Sounds и создаст их заново со значениями по умолчанию "
            "(PIN сбросится на 1234, тема — на «Базовая», лицензия и серийный номер будут перевыпущены). "
            "Используйте, если файлы повреждены, а бекапа нет.",
            "🧹 Пересоздать", "#C0392B",
            self._recovery_recreate_system_files
        )
        
        make_action_card(
            actions_frame,
            "3️⃣ Вернуться в прошлую версию",
            "Полностью откатит код приложения к версии из выбранной резервной копии и перезапустит BITOS. "
            "Config, Security и Sounds не затрагиваются (если явно не выбрано восстановить их тоже).",
            "⏪ Откатить версию", "#8E44AD",
            self._recovery_revert_previous_version
        )
        
        # ===== ЛОГ ВОССТАНОВЛЕНИЯ =====
        log_frame = tk.Frame(main_frame, bg='white', relief=tk.SUNKEN, bd=1)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        tk.Label(log_frame, text="📝 Лог восстановления:", 
                font=('Segoe UI', 10, 'bold'), bg='white', fg='#2C3E50').pack(anchor='w', padx=10, pady=5)
        
        self.recovery_log_text = scrolledtext.ScrolledText(log_frame, font=('Consolas', 9), 
                                                           bg='#1E1E1E', fg='#00FF00',
                                                           height=6, wrap=tk.WORD)
        self.recovery_log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.recovery_log_text.insert('1.0', "[INFO] Выберите резервную копию и действие выше\n")
        self.recovery_log_text.config(state='disabled')
    
    def _refresh_recovery_backups(self):
        """Обновление списка бекапов в выпадающем списке"""
        backups = self._get_available_backups()
        self._recovery_backup_map = {}
        
        values = []
        for name, full_path, mtime in backups:
            label = f"{datetime.fromtimestamp(mtime).strftime('%d.%m.%Y %H:%M:%S')} — {name}"
            values.append(label)
            self._recovery_backup_map[label] = full_path
        
        self.recovery_backup_combo['values'] = values
        if values:
            self.recovery_backup_combo.current(0)
        else:
            self.recovery_backup_combo.set("")
    
    def _log_recovery(self, message, log_type="INFO"):
        """Запись в лог восстановления (безопасно вызывать только из главного потока)"""
        if not hasattr(self, 'recovery_log_text') or not self.recovery_log_text:
            return
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.recovery_log_text.config(state='normal')
        self.recovery_log_text.insert('end', f"[{timestamp}] [{log_type}] {message}\n")
        self.recovery_log_text.see('end')
        self.recovery_log_text.config(state='disabled')
    
    def _get_selected_backup_path(self):
        """Путь к выбранному в комбобоксе бекапу, либо None"""
        selected = self.recovery_backup_combo.get()
        if not selected:
            messagebox.showinfo("Информация", "Сначала выберите резервную копию из списка")
            return None
        backup_path = self._recovery_backup_map.get(selected)
        if not backup_path or not os.path.exists(backup_path):
            messagebox.showerror("Ошибка", "Выбранная резервная копия не найдена на диске")
            return None
        return backup_path
    
    def _recovery_restore_system_files(self):
        """Действие 1: восстановить Config/Security/Sounds из выбранного бекапа"""
        backup_path = self._get_selected_backup_path()
        if not backup_path:
            return
        
        backup_system_dir = os.path.join(backup_path, "System")
        available = [f for f in ("Config", "Security", "Sounds")
                     if os.path.exists(os.path.join(backup_system_dir, f))]
        
        if not available:
            messagebox.showerror("Ошибка", 
                "В этой резервной копии нет сохранённых Config/Security/Sounds.\n"
                "Она могла быть создана при отключённом переключателе бекапа.")
            return
        
        if not messagebox.askyesno("Восстановление системных файлов",
                f"Будут заменены текущие: {', '.join(available)}\n\n"
                "⚠️ Текущие настройки, темы, PIN и звуки будут заменены версией из бекапа.\n"
                "Продолжить?"):
            return
        
        self._log_recovery(f"Восстановление из бекапа: {os.path.basename(backup_path)}", "INSTALL")
        
        restored, errors = [], []
        for folder_name in available:
            src = os.path.join(backup_system_dir, folder_name)
            dst = self.bitos.system_paths.get(folder_name.lower())
            if not dst:
                continue
            try:
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
                restored.append(folder_name)
                self._log_recovery(f"✅ Восстановлено: {folder_name}", "SUCCESS")
            except Exception as e:
                errors.append(f"{folder_name}: {e}")
                self._log_recovery(f"❌ Ошибка восстановления {folder_name}: {e}", "ERROR")
        
        if errors:
            messagebox.showerror("Восстановление завершено с ошибками",
                "Восстановлено: " + (", ".join(restored) or "ничего") + "\n\n"
                "Ошибки:\n" + "\n".join(errors))
        else:
            messagebox.showinfo("Готово",
                f"Восстановлены: {', '.join(restored)}.\n\n"
                "Рекомендуется перезапустить BITOS, чтобы изменения точно применились.")
    
    def _recovery_recreate_system_files(self):
        """Действие 2: удалить и пересоздать Config/Security/Sounds со значениями по умолчанию"""
        if not messagebox.askyesno("Пересоздание системных файлов",
                "⚠️ ВНИМАНИЕ! Это действие:\n\n"
                "• Удалит текущие темы, настройки и ярлыки (Config)\n"
                "• Сбросит PIN-код на 1234 и перевыпустит лицензию/серийный номер (Security)\n"
                "• Удалит и заново сгенерирует системные звуки (Sounds)\n\n"
                "Это необратимо, если у вас нет резервной копии.\n"
                "Продолжить?", icon='warning'):
            return
        
        if not messagebox.askyesno("Подтверждение",
                "Вы точно уверены? Настройки и текущий PIN будут потеряны безвозвратно " 
                "(если не сделан бекап)."):
            return
        
        self._log_recovery("Пересоздание системных файлов...", "INSTALL")
        
        try:
            for folder_key in ("config", "security", "sounds"):
                folder_path = self.bitos.system_paths.get(folder_key)
                if folder_path and os.path.exists(folder_path):
                    shutil.rmtree(folder_path)
                if folder_path:
                    os.makedirs(folder_path, exist_ok=True)
            
            # Переиспользуем штатную логику BITOS для создания файлов по умолчанию
            self.bitos.create_system_files()
            self.bitos._create_sound_files()
            
            self._log_recovery("✅ Системные файлы пересозданы", "SUCCESS")
            messagebox.showinfo("Готово",
                "Системные файлы пересозданы со значениями по умолчанию.\n\n"
                "PIN-код по умолчанию: 1234\n"
                "Рекомендуется перезапустить BITOS.")
        except Exception as e:
            self._log_recovery(f"❌ Ошибка пересоздания: {e}", "ERROR")
            messagebox.showerror("Ошибка", f"Не удалось пересоздать системные файлы:\n{e}")
    
    def _recovery_revert_previous_version(self):
        """Действие 3: откатить код приложения к версии из выбранного бекапа и перезапустить"""
        backup_path = self._get_selected_backup_path()
        if not backup_path:
            return
        
        # В бекапе код лежит рядом с папкой System (System копируется отдельно)
        code_items = [item for item in os.listdir(backup_path) if item != 'System']
        if not code_items:
            messagebox.showerror("Ошибка",
                "В этой резервной копии не сохранён код приложения (только System).\n"
                "Откат версии невозможен из этого бекапа.")
            return
        
        if not messagebox.askyesno("Откат к прошлой версии",
                f"Код приложения будет заменён версией из:\n{os.path.basename(backup_path)}\n\n"
                "⚠️ BITOS перезапустится сразу после отката.\n"
                "Config/Security/Sounds останутся текущими (не откатятся).\n\n"
                "Продолжить?", icon='warning'):
            return
        
        self._log_recovery(f"Откат к версии из бекапа: {os.path.basename(backup_path)}", "INSTALL")
        
        base_path = self.bitos.base_path
        errors = []
        for item in code_items:
            src = os.path.join(backup_path, item)
            dst = os.path.join(base_path, item)
            try:
                if os.path.exists(dst):
                    if os.path.isdir(dst):
                        shutil.rmtree(dst)
                    else:
                        os.remove(dst)
                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
                self._log_recovery(f"✅ Откачен: {item}", "SUCCESS")
            except Exception as e:
                errors.append(f"{item}: {e}")
                self._log_recovery(f"❌ Не удалось откатить {item}: {e}", "ERROR")
        
        if errors:
            messagebox.showerror("Откат завершён с ошибками",
                "Не удалось откатить некоторые файлы:\n" + "\n".join(errors))
            return
        
        messagebox.showinfo("Готово", "Откат выполнен. BITOS сейчас перезапустится.")
        
        try:
            self.window.destroy()
        except Exception:
            pass
        
        # Переиспользуем ту же безопасную логику перезапуска приложения,
        # что и после установки обновления
        self._restart_application()

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


