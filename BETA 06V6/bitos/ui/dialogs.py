import os
import tkinter as tk
from tkinter import messagebox

class FlatCustomThemeDialog:
    """Плоский диалог создания темы Windows 10 1909"""
    def __init__(self, parent, desktop):
        self.parent = parent
        self.desktop = desktop
        self.colors = desktop.theme_colors
        self.ui = desktop.bitos.ui_manager
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Создание темы")
        self.dialog.geometry("520x460")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.configure(bg=self.colors['window_bg'])
        self.dialog.resizable(False, False)
        
        fonts = self.ui.get_fonts()
        
        title_bar = tk.Frame(self.dialog, bg=self.colors['window_bg'], height=40)
        title_bar.pack(fill=tk.X, padx=16, pady=(16, 8))
        tk.Label(title_bar, text="Создание пользовательской темы", font=fonts['header'],
                 bg=self.colors['window_bg'], fg=self.colors['fg']).pack(side=tk.LEFT)
        
        body = tk.Frame(self.dialog, bg=self.colors['window_bg'])
        body.pack(fill=tk.BOTH, expand=True, padx=16, pady=8)
        
        tk.Label(body, text="Название темы:", font=fonts['main'],
                 bg=self.colors['window_bg'], fg=self.colors['fg']).pack(anchor='w', pady=(4, 2))
        self.name_entry = tk.Entry(body, font=fonts['main'], bg='#2D2D2D', fg='#FFFFFF',
                                  bd=0, insertbackground='white')
        self.name_entry.pack(fill=tk.X, ipady=4, pady=(0, 8))
        self.name_entry.insert(0, "Моя Тема")
        
        tk.Label(body, text="Цвет фона (HEX):", font=fonts['main'],
                 bg=self.colors['window_bg'], fg=self.colors['fg']).pack(anchor='w', pady=(4, 2))
        self.bg_entry = tk.Entry(body, font=fonts['main'], bg='#2D2D2D', fg='#FFFFFF',
                                bd=0, insertbackground='white')
        self.bg_entry.pack(fill=tk.X, ipady=4, pady=(0, 8))
        self.bg_entry.insert(0, "#1E1E1E")
        
        tk.Label(body, text="Цвет акцента (HEX):", font=fonts['main'],
                 bg=self.colors['window_bg'], fg=self.colors['fg']).pack(anchor='w', pady=(4, 2))
        self.accent_entry = tk.Entry(body, font=fonts['main'], bg='#2D2D2D', fg='#FFFFFF',
                                    bd=0, insertbackground='white')
        self.accent_entry.pack(fill=tk.X, ipady=4, pady=(0, 8))
        self.accent_entry.insert(0, "#0078D4")
        
        btn_bar = tk.Frame(self.dialog, bg=self.colors['window_bg'])
        btn_bar.pack(fill=tk.X, padx=16, pady=16)
        
        cancel_btn = tk.Button(btn_bar, text="Отмена", bg='#333333', fg='white',
                               font=fonts['main'], bd=0, padx=16, pady=6,
                               relief=tk.FLAT, command=self.dialog.destroy)
        cancel_btn.pack(side=tk.RIGHT, padx=4)
        
        save_btn = tk.Button(btn_bar, text="Сохранить", bg=self.colors['accent'], fg='white',
                             font=fonts['main_bold'], bd=0, padx=16, pady=6,
                             relief=tk.FLAT, command=self.save)
        save_btn.pack(side=tk.RIGHT, padx=4)

    def save(self):
        name = self.name_entry.get().strip()
        bg = self.bg_entry.get().strip()
        accent = self.accent_entry.get().strip()
        if not name or not bg or not accent:
            messagebox.showwarning("Ошибка", "Заполните все поля", parent=self.dialog)
            return
        self.desktop.create_user_theme(
            name=name, bg_color=bg, fg_color="#FFFFFF",
            taskbar_bg="#101010", taskbar_fg="#FFFFFF",
            canvas_bg=bg, icon_fg="#FFFFFF",
            widget_bg="#252525", widget_fg="#FFFFFF"
        )
        self.dialog.destroy()
