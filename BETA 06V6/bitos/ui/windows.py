import os
import sys
import time
import json
import math
import shutil
import platform
import subprocess
import csv
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog

from bitos.server.security import TrashManager
from bitos.server.updates import BipInstaller, UpdateManager
from bitos.server.core import shutdown_windows, restart_windows, WallpaperManager, NotificationCenter
from bitos.ui.dialogs import FlatCustomThemeDialog

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def _maximize_window(window):
    """Maximize a top-level window on Windows and use a geometry fallback elsewhere."""
    try:
        window.state('zoomed')
        return
    except Exception:
        pass
    try:
        width = window.winfo_screenwidth()
        height = window.winfo_screenheight()
        window.geometry(f"{width}x{height}+0+0")
    except Exception:
        pass


class BITOSOnScreenKeyboard:
    """Встроенная экранная клавиатура BITOS для Entry/Text-полей."""
    def __init__(self, parent, target):
        self.parent = parent
        self.target = target
        self.shifted = False
        self.language = 'EN'
        self.win = tk.Toplevel(parent)
        self.win.title('Экранная клавиатура BITOS')
        self.win.configure(bg='#171717')
        self.win.resizable(False, False)
        self.win.transient(parent)
        # Экранная клавиатура должна оставаться над окнами приложений BITOS
        # и обычными окнами Windows, в том числе при переключении фокуса.
        try:
            self.win.attributes('-topmost', True)
        except tk.TclError:
            pass
        width = min(760, max(500, parent.winfo_screenwidth() - 40))
        x = max(0, (parent.winfo_screenwidth() - width) // 2)
        y = max(0, parent.winfo_screenheight() - 340)
        self.win.geometry(f'{width}x300+{x}+{y}')
        self.win.protocol('WM_DELETE_WINDOW', self.close)
        self._build()
        # Некоторые приложения периодически поднимают своё окно поверх клавиатуры.
        # Повторный lift возвращает клавиатуру на передний план.
        self._keep_on_top()

    def _keep_on_top(self):
        try:
            if self.win.winfo_exists():
                self.win.attributes('-topmost', True)
                self.win.lift()
                self._topmost_after_id = self.win.after(300, self._keep_on_top)
        except (tk.TclError, AttributeError):
            pass

    def _build(self):
        header = tk.Frame(self.win, bg='#171717')
        header.pack(fill=tk.X, padx=8, pady=(7, 3))
        tk.Label(header, text='Клавиатура BITOS', bg='#171717', fg='white',
                 font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT)
        tk.Button(header, text=self.language, command=self._toggle_language,
                  bg='#303030', fg='white', bd=0, padx=12).pack(side=tk.RIGHT, padx=3)
        tk.Button(header, text='✕', command=self.close, bg='#303030', fg='white',
                  bd=0, padx=12).pack(side=tk.RIGHT, padx=3)
        self.keys_frame = tk.Frame(self.win, bg='#171717')
        self.keys_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self._draw_keys()

    def _draw_keys(self):
        for child in self.keys_frame.winfo_children():
            child.destroy()
        if self.language == 'EN':
            rows = [list('1234567890'), list('qwertyuiop'), list('asdfghjkl'),
                    ['SHIFT'] + list('zxcvbnm') + ['⌫'], ['RU/EN', 'SPACE', 'ENTER']]
        else:
            rows = [list('1234567890'), list('йцукенгшщзх'), list('фывапролджэ'),
                    ['SHIFT'] + list('ячсмитьбю') + ['⌫'], ['RU/EN', 'SPACE', 'ENTER']]
        for row in rows:
            frame = tk.Frame(self.keys_frame, bg='#171717')
            frame.pack(fill=tk.X, expand=True, pady=2)
            for key in row:
                label = key.upper() if len(key) == 1 and key.isalpha() and self.shifted else key
                text = {'SPACE': 'Пробел', 'ENTER': 'Ввод', 'SHIFT': '⇧', '⌫': '⌫', 'RU/EN': 'RU/EN'}.get(label, label)
                color = '#0078D4' if key in ('ENTER', 'SHIFT') else '#343434'
                tk.Button(frame, text=text, bg=color, fg='white', bd=0,
                         activebackground='#505050', activeforeground='white',
                         font=('Segoe UI', 10), padx=7, pady=5,
                         command=lambda k=key: self._press(k)).pack(
                             side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)

    def _toggle_language(self):
        self.language = 'RU' if self.language == 'EN' else 'EN'
        self._draw_keys()

    def _press(self, key):
        try:
            self.target.focus_set()
            if key == 'SHIFT':
                self.shifted = not self.shifted
                self._draw_keys()
                return
            if key == 'RU/EN':
                self._toggle_language()
                return
            if key == 'SPACE':
                value = ' '
            elif key == 'ENTER':
                self.target.event_generate('<Return>')
                return
            elif key == '⌫':
                try:
                    if self.target.winfo_class() == 'Text':
                        selected = self.target.tag_ranges('sel')
                        if selected:
                            self.target.delete('sel.first', 'sel.last')
                        else:
                            pos = self.target.index(tk.INSERT)
                            previous = self.target.index(f'{pos} - 1 chars')
                            if previous != pos:
                                self.target.delete(previous, pos)
                    elif self.target.selection_present():
                        self.target.delete(tk.SEL_FIRST, tk.SEL_LAST)
                    else:
                        pos = int(self.target.index(tk.INSERT))
                        if pos > 0:
                            self.target.delete(pos-1)
                except Exception:
                    pass
                return
            else:
                value = key.upper() if self.shifted and key.isalpha() else key
            self.target.insert(tk.INSERT, value)
            if self.shifted:
                self.shifted = False
                self._draw_keys()
        except Exception:
            pass

    def close(self):
        try:
            after_id = getattr(self, '_topmost_after_id', None)
            if after_id is not None:
                self.win.after_cancel(after_id)
            self.win.destroy()
        except Exception:
            pass


def _bind_touch_keyboard(root, touch_getter):
    """Open BITOS keyboard on double-click/tap of an input in touch mode."""
    def on_double_click(event=None):
        try:
            if not touch_getter():
                return
            target = root.focus_get()
            if target is None or target.winfo_class() not in ('Entry', 'TEntry', 'Text'):
                return
            existing = getattr(root, '_bitos_keyboard_window', None)
            if existing is not None:
                try:
                    if existing.win.winfo_exists():
                        existing.target = target
                        existing.win.lift()
                        return
                except Exception:
                    pass
            root._bitos_keyboard_window = BITOSOnScreenKeyboard(root, target)
        except Exception:
            pass
    root.bind_all('<Double-Button-1>', on_double_click, add='+')
    return on_double_click


class BITOSFileDialog:
    """Встроенный диалог выбора файлов BITOS; не вызывает системный Windows Explorer."""
    def __init__(self, parent, bitos, mode='open', title='Проводник BITOS', filetypes=None,
                 initialdir=None, initialfile=None, multiple=False):
        self.bitos = bitos
        self.mode = mode
        self.filetypes = filetypes or [('Все файлы', '*.*')]
        self.multiple = multiple
        self.result = None
        home = initialdir or getattr(bitos, 'user_paths', {}).get('home') or os.path.expanduser('~')
        self.current = os.path.abspath(home)
        self.win = tk.Toplevel(parent)
        self.win.title(title)
        self.win.geometry('760x480')
        self.win.configure(bg='#1F1F1F')
        self.win.transient(parent)
        self.win.grab_set()
        bar = tk.Frame(self.win, bg='#1F1F1F'); bar.pack(fill=tk.X, padx=10, pady=8)
        tk.Button(bar, text='←', command=self.up, bg='#303030', fg='white', bd=0, width=3).pack(side=tk.LEFT)
        self.path_var = tk.StringVar(value=self.current)
        path_entry = tk.Entry(bar, textvariable=self.path_var, bg='#2D2D2D', fg='white', insertbackground='white', bd=0)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6, ipady=4)
        path_entry.bind('<Return>', lambda e: self.navigate(self.path_var.get()))
        tk.Button(bar, text='Перейти', command=lambda: self.navigate(self.path_var.get()), bg='#303030', fg='white', bd=0).pack(side=tk.LEFT)
        quick = tk.Frame(self.win, bg='#141414'); quick.pack(fill=tk.X, padx=10)
        for label, path in [('Домой', home), ('Документы', getattr(bitos, 'documents_path', home)),
                           ('Загрузки', getattr(bitos, 'downloads_path', home)),
                           ('Рабочий стол', getattr(bitos, 'user_paths', {}).get('desktop', home))]:
            tk.Button(quick, text=label, command=lambda p=path: self.navigate(p), bg='#141414', fg='#DDD', bd=0).pack(side=tk.LEFT, padx=4, pady=4)
        self.listbox = tk.Listbox(self.win, selectmode=tk.EXTENDED if multiple else tk.SINGLE,
                                 bg='#202020', fg='white', selectbackground='#0078D4', bd=0,
                                 font=('Segoe UI', 10), activestyle='none')
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        self.listbox.bind('<Double-1>', self.activate)
        bottom = tk.Frame(self.win, bg='#1F1F1F'); bottom.pack(fill=tk.X, padx=10, pady=(0,10))
        self.name_var = tk.StringVar(value=initialfile or '')
        if mode in ('save', 'open'):
            tk.Entry(bottom, textvariable=self.name_var, bg='#2D2D2D', fg='white', insertbackground='white', bd=0).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,8), ipady=4)
        self.action_label = {'open':'Открыть', 'save':'Сохранить', 'folder':'Выбрать папку'}.get(mode, 'Выбрать')
        tk.Button(bottom, text=self.action_label, command=self.accept, bg='#0078D4', fg='white', bd=0, padx=16).pack(side=tk.RIGHT)
        tk.Button(bottom, text='Отмена', command=self.cancel, bg='#303030', fg='white', bd=0, padx=12).pack(side=tk.RIGHT, padx=6)
        self.items = []
        self.navigate(self.current)
        self.win.wait_window()

    def navigate(self, path):
        path = os.path.abspath(os.path.expanduser(path))
        if not os.path.isdir(path):
            return
        self.current = path
        self.path_var.set(path)
        self.listbox.delete(0, tk.END)
        self.items = []
        try:
            entries = sorted(os.scandir(path), key=lambda e: (not e.is_dir(), e.name.casefold()))
            for entry in entries:
                if entry.is_dir():
                    self.items.append((entry.name, entry.path, True))
                elif self.mode == 'folder':
                    continue
                elif self._matches(entry.name):
                    self.items.append((entry.name, entry.path, False))
            for name, _, is_dir in self.items:
                self.listbox.insert(tk.END, ('📁  ' if is_dir else '📄  ') + name)
        except OSError as exc:
            messagebox.showerror('Проводник BITOS', str(exc), parent=self.win)

    def _matches(self, name):
        import fnmatch
        patterns = []
        for _, pattern in self.filetypes:
            patterns.extend(pattern.split())
        return not patterns or any(fnmatch.fnmatch(name.lower(), p.lower()) for p in patterns if p != '*.*') or '*.*' in patterns

    def up(self):
        parent = os.path.dirname(self.current)
        if parent and parent != self.current:
            self.navigate(parent)

    def activate(self, _event=None):
        sel = self.listbox.curselection()
        if not sel: return
        _, path, is_dir = self.items[sel[0]]
        if is_dir:
            self.navigate(path)
        elif self.mode == 'open':
            self.result = path
            self.win.destroy()

    def accept(self):
        sel = [self.items[i] for i in self.listbox.curselection()]
        if self.mode == 'folder':
            if sel and sel[0][2]: self.result = sel[0][1]
            else: self.result = self.current
        elif self.mode == 'save':
            name = self.name_var.get().strip()
            if not name: return
            if not os.path.splitext(name)[1]:
                ext = next((p.replace('*','') for _, pat in self.filetypes for p in pat.split() if p.startswith('*.') and p != '*.*'), '')
                name += ext
            self.result = os.path.join(self.current, name)
        elif self.multiple:
            self.result = tuple(item[1] for item in sel if not item[2])
        elif sel and not sel[0][2]:
            self.result = sel[0][1]
        elif self.name_var.get().strip():
            self.result = os.path.join(self.current, self.name_var.get().strip())
        if self.result is not None:
            self.win.destroy()

    def cancel(self):
        self.result = None
        self.win.destroy()


def bitos_askopenfilename(parent, bitos, **kwargs):
    return BITOSFileDialog(parent, bitos, mode='open', **kwargs).result or ''

def bitos_askopenfilenames(parent, bitos, **kwargs):
    return BITOSFileDialog(parent, bitos, mode='open', multiple=True, **kwargs).result or ()

def bitos_asksaveasfilename(parent, bitos, **kwargs):
    return BITOSFileDialog(parent, bitos, mode='save', **kwargs).result or ''

def bitos_askdirectory(parent, bitos, **kwargs):
    return BITOSFileDialog(parent, bitos, mode='folder', **kwargs).result or ''

# ============================================================================
# 1. ИКОНКА РАБОЧЕГО СТОЛА
# ============================================================================

class DesktopIcon:
    """Строгая квадратная иконка сетки рабочего стола с динамическим обновлением размеров"""
    def __init__(self, canvas, grid_x, grid_y, icon, text, command, icon_id=None, size=104, step=116, font_size=11, command_key=None):
        self.canvas = canvas
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.icon = icon
        self.text = text
        self.command = command
        self.command_key = command_key
        self.icon_id = icon_id if icon_id else f"{text}_{int(time.time()*1000)}"
        self.selected = False
        self.hover = False
        self.is_trash = (text == "Корзина")
        
        self.size = size
        self.step = step
        self.font_size = font_size
        self.x = 24 + self.grid_x * self.step
        self.y = 24 + self.grid_y * self.step
        self.create()

    def create(self):
        x1, y1 = self.x, self.y
        x2, y2 = self.x + self.size, self.y + self.size
        
        self.rect_id = self.canvas.create_rectangle(
            x1, y1, x2, y2, fill='', outline='', tags=('icon', f'box_{self.icon_id}')
        )
        self.icon_id_obj = self.canvas.create_text(
            self.x + self.size // 2, self.y + int(self.size * 0.35), text=self.icon,
            font=('Segoe UI', max(34, int(self.size * 0.46))), fill='#FFFFFF', tags=('icon', f'ico_{self.icon_id}')
        )
        trunc_txt = self.text if len(self.text) <= 12 else self.text[:10] + "..."
        self.text_id = self.canvas.create_text(
            self.x + self.size // 2, self.y + int(self.size * 0.75), text=trunc_txt,
            font=('Segoe UI', max(10, self.font_size)), fill='#FFFFFF', width=self.size - 6, justify='center',
            tags=('icon', f'txt_{self.icon_id}')
        )
        
        for item in (f'box_{self.icon_id}', f'ico_{self.icon_id}', f'txt_{self.icon_id}'):
            self.canvas.tag_bind(item, '<Button-1>', self.on_click)
            self.canvas.tag_bind(item, '<ButtonPress-1>', self.start_drag)
            self.canvas.tag_bind(item, '<B1-Motion>', self.drag)
            self.canvas.tag_bind(item, '<ButtonRelease-1>', self.end_drag)
            self.canvas.tag_bind(item, '<Double-1>', self.on_double_click)
            self.canvas.tag_bind(item, '<Button-3>', self.show_shortcut_menu)
            self.canvas.tag_bind(item, '<Enter>', self.on_enter)
            self.canvas.tag_bind(item, '<Leave>', self.on_leave)

    def destroy(self):
        for item in (f'box_{self.icon_id}', f'ico_{self.icon_id}', f'txt_{self.icon_id}'):
            self.canvas.delete(item)

    def on_enter(self, e):
        self.hover = True
        if not self.selected:
            self.canvas.itemconfig(self.rect_id, fill='#2B2B2B', outline='#444444')

    def on_leave(self, e):
        self.hover = False
        if not self.selected:
            self.canvas.itemconfig(self.rect_id, fill='', outline='')

    def on_click(self, e):
        owner = getattr(self.canvas, "desktop_owner", None)
        if owner:
            owner.bitos.play_sound("click")
        if hasattr(self.canvas, 'desktop_icons'):
            for ic in self.canvas.desktop_icons:
                if ic != self:
                    ic.selected = False
                    self.canvas.itemconfig(ic.rect_id, fill='', outline='')
        self.selected = True
        self.canvas.itemconfig(self.rect_id, fill='#0078D4', outline='#005A9E')

    def start_drag(self, e):
        self._drag_origin = (e.x_root, e.y_root, self.x, self.y)
        self._drag_moved = False

    def drag(self, e):
        if not hasattr(self, "_drag_origin"):
            return
        sx, sy, ox, oy = self._drag_origin
        dx, dy = e.x_root - sx, e.y_root - sy
        if abs(dx) + abs(dy) > 3:
            self._drag_moved = True
        if self._drag_moved:
            self.x = max(4, ox + dx)
            self.y = max(4, oy + dy)
            self.canvas.coords(self.rect_id, self.x, self.y, self.x + self.size, self.y + self.size)
            self.canvas.coords(self.icon_id_obj, self.x + self.size // 2, self.y + int(self.size * 0.35))
            self.canvas.coords(self.text_id, self.x + self.size // 2, self.y + int(self.size * 0.75))

    def end_drag(self, e):
        if getattr(self, "_drag_moved", False):
            owner = getattr(self.canvas, "desktop_owner", None)
            if owner:
                self.grid_x = max(0, round((self.x - 24) / max(1, self.step)))
                self.grid_y = max(0, round((self.y - 24) / max(1, self.step)))
                self.x = 24 + self.grid_x * self.step
                self.y = 24 + self.grid_y * self.step
                self.canvas.coords(self.rect_id, self.x, self.y, self.x + self.size, self.y + self.size)
                self.canvas.coords(self.icon_id_obj, self.x + self.size // 2, self.y + int(self.size * 0.35))
                self.canvas.coords(self.text_id, self.x + self.size // 2, self.y + int(self.size * 0.75))
                owner._autosave_desktop_state()
        self._drag_origin = None

    def show_shortcut_menu(self, e):
        owner = getattr(self.canvas, "desktop_owner", None)
        if owner is None or self.text in ("Этот ПК", "Корзина"):
            return
        menu = tk.Menu(self.canvas, tearoff=0, bg="#1F1F1F", fg="white", activebackground="#0078D4")
        is_bip_app = str(getattr(self, "command_key", "") or "").startswith("bip:")
        virtual_path = getattr(self, "virtual_path", None)
        is_virtual_item = bool(getattr(self, "is_virtual_item", False) and virtual_path)
        is_document = bool(is_virtual_item and os.path.isfile(virtual_path))
        is_folder = bool(is_virtual_item and os.path.isdir(virtual_path))
        if is_document:
            menu.add_command(label="Удалить документ", command=lambda: owner.remove_desktop_document(self))
        elif is_folder:
            menu.add_command(label="Удалить папку", command=lambda: owner.remove_desktop_folder(self))
        else:
            menu.add_command(label="Информация о приложении", command=lambda: owner.show_shortcut_info(self))
            menu.add_command(label="Удалить с рабочего стола", command=lambda: owner.remove_desktop_shortcut(self))
            if is_bip_app:
                menu.add_command(label="Удалить приложение (BIP)", command=lambda: owner.remove_bip_shortcut(self))
        try:
            menu.tk_popup(e.x_root, e.y_root)
        finally:
            menu.grab_release()

    def on_double_click(self, e):
        if self.command:
            self.command()

    def update_metrics(self, size, step, font_size):
        self.size = size
        self.step = step
        self.font_size = font_size
        self.x = 24 + self.grid_x * self.step
        self.y = 24 + self.grid_y * self.step
        self.canvas.coords(self.rect_id, self.x, self.y, self.x + self.size, self.y + self.size)
        self.canvas.coords(self.icon_id_obj, self.x + self.size // 2, self.y + int(self.size * 0.35))
        self.canvas.coords(self.text_id, self.x + self.size // 2, self.y + int(self.size * 0.75))
        self.canvas.itemconfig(self.icon_id_obj, font=('Segoe UI', max(34, int(self.size * 0.46))))
        self.canvas.itemconfig(self.text_id, font=('Segoe UI', self.font_size))

    def update_theme(self, fg):
        self.canvas.itemconfig(self.text_id, fill=fg)

    def to_dict(self):
        cmd = None
        s = str(self.command)
        for key in ['explorer', 'trash']:
            if key in s:
                cmd = key
                break
        return {
            'icon': self.icon, 'text': self.text, 'grid_x': self.grid_x,
            'grid_y': self.grid_y, 'icon_id': self.icon_id, 'command': self.command_key or cmd
        }


# ============================================================================
# 2. ЭКРАНЫ ЗАГРУЗКИ И ВХОДА (SPLASH / LOGIN)
# ============================================================================

class SplashScreen:
    """Минималистичный Splash-экран: строгий дизайн, полоса 3 px, Segoe UI"""
    def __init__(self, bitos):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        _maximize_window(self.root)
        w = self.root.winfo_screenwidth()
        h = self.root.winfo_screenheight()
        
        self.canvas = tk.Canvas(self.root, width=w, height=h, bg='#0A0A0A', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.canvas.create_text(w//2, h//2 - 50, text="BITOS", font=('Segoe UI', 64, 'bold'), fill='#FFFFFF')
        self.canvas.create_text(w//2, h//2 + 20, text="Операционная система будущего", font=('Segoe UI', 13), fill='#808080')
        
        self.bar_w = 400
        self.bar_h = 3
        self.bx = w//2 - self.bar_w//2
        self.by = h//2 + 70
        
        self.canvas.create_rectangle(self.bx, self.by, self.bx + self.bar_w, self.by + self.bar_h, fill='#222222', outline='')
        self.prog = self.canvas.create_rectangle(self.bx, self.by, self.bx, self.by + self.bar_h, fill='#0078D4', outline='')
        self.lbl = self.canvas.create_text(w//2, self.by + 26, text="", font=('Segoe UI', 10), fill='#808080')
        self.root.update()

    def update_progress(self, val, txt=""):
        cur_w = (val / 100.0) * self.bar_w
        self.canvas.coords(self.prog, self.bx, self.by, self.bx + cur_w, self.by + self.bar_h)
        self.canvas.itemconfig(self.lbl, text=txt)
        self.root.update()

    def close(self):
        self.root.destroy()


class LoginScreen:
    """Экран входа в стиле Windows 10 1909"""
    def __init__(self, on_login, bitos):
        self.on_login = on_login
        self.bitos = bitos
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        _maximize_window(self.root)
        self.root.configure(bg='#101010')
        try:
            self.root.attributes('-alpha', 0.0)
            def fade_login(alpha=0.0):
                try:
                    alpha = min(1.0, alpha + 0.12)
                    self.root.attributes('-alpha', alpha)
                    if alpha < 1.0:
                        self.root.after(14, lambda: fade_login(alpha))
                except Exception:
                    pass
            self.root.after(10, fade_login)
        except Exception:
            pass
        self.failed_attempts = 0
        self.lock_until = 0.0
        self.max_attempts = 5
        self.lock_seconds = 60
        
        top_frame = tk.Frame(self.root, bg='#101010')
        top_frame.place(x=60, y=50)
        self.time_lbl = tk.Label(top_frame, text=datetime.now().strftime("%H:%M"), font=('Segoe UI', 52), fg='#FFFFFF', bg='#101010')
        self.time_lbl.pack(anchor='w')
        self.date_lbl = tk.Label(top_frame, text=datetime.now().strftime("%d %B, %A"), font=('Segoe UI', 18), fg='#A0A0A0', bg='#101010')
        self.date_lbl.pack(anchor='w')
        
        center = tk.Frame(self.root, bg='#101010')
        center.place(relx=0.5, rely=0.55, anchor=tk.CENTER)
        
        avatar = tk.Label(center, text="👤", font=('Segoe UI', 54), fg='#0078D4', bg='#1A1A1A', width=3, height=1)
        avatar.pack(pady=10)
        
        tk.Label(center, text="User", font=('Segoe UI', 18, 'bold'), fg='white', bg='#101010').pack(pady=(0, 15))
        
        self.pin_entry = tk.Entry(center, font=('Segoe UI', 14), bg='#1E1E1E', fg='white',
                                  bd=0, show='●', justify='center', insertbackground='white')
        self.pin_entry.pack(ipady=6, pady=4, fill=tk.X)
        self.pin_entry.focus_set()
        self.pin_entry.bind('<Return>', lambda e: self.do_login())
        _bind_touch_keyboard(self.root, lambda: bool(self.bitos.ui_manager.touch_mode))
        
        self.err_lbl = tk.Label(center, text="", font=('Segoe UI', 10), fg='#E81123', bg='#101010')
        self.err_lbl.pack(pady=4)
        
        login_btn = tk.Button(center, text="Войти ➔", font=('Segoe UI', 10, 'bold'),
                              bg='#0078D4', fg='white', bd=0, padx=20, pady=6,
                              relief=tk.FLAT, cursor='hand2', command=self.do_login)
        login_btn.pack(pady=6)
        keyboard_btn = tk.Button(center, text='⌨ Открыть экранную клавиатуру',
                                font=('Segoe UI', 10), bg='#303030', fg='white', bd=0,
                                padx=12, pady=6, relief=tk.FLAT, cursor='hand2',
                                command=lambda: BITOSOnScreenKeyboard(self.root, self.pin_entry))
        keyboard_btn.pack(pady=(2, 8))
        
        power = tk.Frame(self.root, bg='#101010')
        power.place(relx=0.95, rely=0.92, anchor=tk.CENTER)
        
        sh_btn = tk.Button(power, text="⏻", font=('Segoe UI', 14), bg='#101010', fg='#808080',
                           bd=0, activebackground='#101010', activeforeground='white',
                           command=shutdown_windows, cursor='hand2')
        sh_btn.pack(side=tk.RIGHT, padx=8)
        
        rb_btn = tk.Button(power, text="↻", font=('Segoe UI', 14), bg='#101010', fg='#808080',
                           bd=0, activebackground='#101010', activeforeground='white',
                           command=restart_windows, cursor='hand2')
        rb_btn.pack(side=tk.RIGHT, padx=8)

    def do_login(self):
        now = time.time()
        if now < self.lock_until:
            self.err_lbl.config(text=f"Вход заблокирован ещё {int(self.lock_until-now)} сек.")
            return
        pin = self.pin_entry.get().strip()
        pin_file = os.path.join(self.bitos.system_paths["security"], "pin.hash")
        default_hash = "03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4"  # 1234
        saved = default_hash
        if os.path.exists(pin_file):
            try:
                with open(pin_file, 'r', encoding='utf-8') as f:
                    saved = f.read().strip()
            except Exception:
                pass
        import hashlib
        success = hashlib.sha256(pin.encode()).hexdigest() == saved
        if success:
            self.failed_attempts = 0
            self.bitos.security.log_login_attempt("User", True)
            self.bitos.play_sound("logon")
            def finish_login(alpha=1.0):
                try:
                    alpha = max(0.0, alpha - 0.14)
                    self.root.attributes('-alpha', alpha)
                except Exception:
                    alpha = 0.0
                if alpha > 0:
                    try:
                        self.root.after(12, lambda: finish_login(alpha))
                    except Exception:
                        finish_login(0.0)
                else:
                    try: self.root.destroy()
                    except Exception: pass
                    self.on_login("User")
            self.root.after(0, finish_login)
        else:
            self.failed_attempts += 1
            remaining = self.max_attempts - self.failed_attempts
            self.bitos.security.log_login_attempt("User", False)
            self.bitos.play_sound("error")
            if self.failed_attempts >= self.max_attempts:
                self.lock_until = time.time() + self.lock_seconds
                self.failed_attempts = 0
                self.err_lbl.config(text=f"Слишком много попыток. Блокировка на {self.lock_seconds} сек.")
                self.bitos.security.log_security_event("BRUTE_FORCE_ATTEMPT", "User locked after failed PIN attempts")
            else:
                self.err_lbl.config(text=f"Неверный PIN-код. Осталось попыток: {remaining}")
            self.pin_entry.delete(0, tk.END)

    def run(self):
        self.root.mainloop()


# ============================================================================
# 3. ВИДЖЕТЫ РАБОЧЕГО СТОЛА (ЧАСЫ / КАЛЕНДАРЬ / СТИКЕРЫ)
# ============================================================================

class ClockWidget:
    """Виджет часов: плоский стиль, перетаскивание, секундное обновление"""
    def __init__(self, canvas, theme_colors, x=140, y=30):
        self.canvas = canvas
        self.theme_colors = theme_colors
        self.x = x
        self.y = y
        self.drag_data = {"x": 0, "y": 0}
        
        self.frame = tk.Frame(self.canvas, bg='#252525', bd=1, relief=tk.SOLID)
        self.win_id = self.canvas.create_window(self.x, self.y, window=self.frame, anchor='nw', tags='widget')
        
        self.title_bar = tk.Frame(self.frame, bg='#1F1F1F', height=24)
        self.title_bar.pack(fill=tk.X)
        
        tk.Label(self.title_bar, text="  Часы", bg='#1F1F1F', fg='#A0A0A0', font=('Segoe UI', 8)).pack(side=tk.LEFT)
        close_btn = tk.Label(self.title_bar, text="✕ ", bg='#1F1F1F', fg='#A0A0A0', font=('Segoe UI', 8), cursor='hand2')
        close_btn.pack(side=tk.RIGHT)
        close_btn.bind('<Button-1>', lambda e: self.destroy())
        
        self.title_bar.bind('<Button-1>', self._start_drag)
        self.title_bar.bind('<B1-Motion>', self._on_drag)
        
        self.time_lbl = tk.Label(self.frame, text="", font=('Segoe UI', 24, 'bold'), fg='#FFFFFF', bg='#252525')
        self.time_lbl.pack(padx=16, pady=(8, 2))
        
        self.date_lbl = tk.Label(self.frame, text="", font=('Segoe UI', 9), fg='#0078D4', bg='#252525')
        self.date_lbl.pack(padx=16, pady=(0, 10))
        
        self.alive = True
        self._after_id = None
        self._update_time()

    def _update_time(self):
        if not self.alive or not self.frame.winfo_exists():
            return
        now = datetime.now()
        self.time_lbl.config(text=now.strftime("%H:%M:%S"))
        self.date_lbl.config(text=now.strftime("%d %B %Y"))
        owner = getattr(self.canvas, "desktop_owner", None)
        interval = owner.ui.clock_interval_ms if owner and owner.ui.widgets_enabled else (1000 if owner is None else None)
        if interval is not None:
            self._after_id = self.frame.after(interval, self._update_time)

    def refresh_profile(self):
        if self._after_id is not None:
            try: self.frame.after_cancel(self._after_id)
            except Exception: pass
            self._after_id = None
        owner = getattr(self.canvas, "desktop_owner", None)
        if not self.alive or owner is None or not owner.ui.widgets_enabled:
            return
        interval = owner.ui.clock_interval_ms
        if interval is not None:
            self._after_id = self.frame.after(interval, self._update_time)

    def _start_drag(self, e):
        self.drag_data["x"] = e.x
        self.drag_data["y"] = e.y

    def _on_drag(self, e):
        dx = e.x - self.drag_data["x"]
        dy = e.y - self.drag_data["y"]
        self.x += dx
        self.y += dy
        self.canvas.coords(self.win_id, self.x, self.y)

    def destroy(self):
        self.alive = False
        if self._after_id is not None:
            try:
                self.frame.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None
        self.canvas.delete(self.win_id)
        self.frame.destroy()

    def update_position(self):
        self.canvas.coords(self.win_id, self.x, self.y)

    def update_theme(self, tc):
        self.theme_colors = tc

    def get_config(self):
        return {'type': 'clock', 'x': self.x, 'y': self.y}


class CalendarWidget:
    """Виджет календаря: плоский дизайн Windows 10, перетаскивание"""
    def __init__(self, canvas, theme_colors, x=140, y=160):
        self.canvas = canvas
        self.theme_colors = theme_colors
        self.x = x
        self.y = y
        self.drag_data = {"x": 0, "y": 0}
        
        self.frame = tk.Frame(self.canvas, bg='#252525', bd=1, relief=tk.SOLID)
        self.win_id = self.canvas.create_window(self.x, self.y, window=self.frame, anchor='nw', tags='widget')
        
        self.title_bar = tk.Frame(self.frame, bg='#1F1F1F', height=24)
        self.title_bar.pack(fill=tk.X)
        
        tk.Label(self.title_bar, text="  Календарь", bg='#1F1F1F', fg='#A0A0A0', font=('Segoe UI', 8)).pack(side=tk.LEFT)
        close_btn = tk.Label(self.title_bar, text="✕ ", bg='#1F1F1F', fg='#A0A0A0', font=('Segoe UI', 8), cursor='hand2')
        close_btn.pack(side=tk.RIGHT)
        close_btn.bind('<Button-1>', lambda e: self.destroy())
        
        self.title_bar.bind('<Button-1>', self._start_drag)
        self.title_bar.bind('<B1-Motion>', self._on_drag)
        
        now = datetime.now()
        tk.Label(self.frame, text=now.strftime("%B %Y"), font=('Segoe UI', 10, 'bold'), fg='#FFFFFF', bg='#252525').pack(pady=(6, 4))
        
        grid_f = tk.Frame(self.frame, bg='#252525')
        grid_f.pack(padx=10, pady=(0, 8))
        
        days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        for c, d in enumerate(days):
            tk.Label(grid_f, text=d, font=('Segoe UI', 8), bg='#252525', fg='#A0A0A0', width=3).grid(row=0, column=c)
            
        import calendar
        cal = calendar.monthcalendar(now.year, now.month)
        for r, week in enumerate(cal):
            for c, day in enumerate(week):
                if day != 0:
                    is_today = (day == now.day)
                    bg_c = '#0078D4' if is_today else '#252525'
                    fg_c = '#FFFFFF'
                    lbl = tk.Label(grid_f, text=str(day), font=('Segoe UI', 8), bg=bg_c, fg=fg_c, width=3)
                    lbl.grid(row=r+1, column=c, padx=1, pady=1)

    def _start_drag(self, e):
        self.drag_data["x"] = e.x
        self.drag_data["y"] = e.y

    def _on_drag(self, e):
        dx = e.x - self.drag_data["x"]
        dy = e.y - self.drag_data["y"]
        self.x += dx
        self.y += dy
        self.canvas.coords(self.win_id, self.x, self.y)

    def destroy(self):
        self.canvas.delete(self.win_id)
        self.frame.destroy()

    def update_position(self):
        self.canvas.coords(self.win_id, self.x, self.y)

    def update_theme(self, tc):
        self.theme_colors = tc

    def get_config(self):
        return {'type': 'calendar', 'x': self.x, 'y': self.y}


class StickerWidget:
    """Виджет заметок: перетаскивание, текстовое поле и сохранение текста"""
    def __init__(self, canvas, theme_colors, x=400, y=30, text=""):
        self.canvas = canvas
        self.theme_colors = theme_colors
        self.x = x
        self.y = y
        self.drag_data = {"x": 0, "y": 0}
        
        self.frame = tk.Frame(self.canvas, bg='#333333', bd=1, relief=tk.SOLID)
        self.win_id = self.canvas.create_window(self.x, self.y, window=self.frame, anchor='nw', tags='widget')
        
        self.title_bar = tk.Frame(self.frame, bg='#2B2B2B', height=24)
        self.title_bar.pack(fill=tk.X)
        
        tk.Label(self.title_bar, text="  Заметка", bg='#2B2B2B', fg='#E0E0E0', font=('Segoe UI', 8)).pack(side=tk.LEFT)
        close_btn = tk.Label(self.title_bar, text="✕ ", bg='#2B2B2B', fg='#A0A0A0', font=('Segoe UI', 8), cursor='hand2')
        close_btn.pack(side=tk.RIGHT)
        close_btn.bind('<Button-1>', lambda e: self.destroy())
        
        self.title_bar.bind('<Button-1>', self._start_drag)
        self.title_bar.bind('<B1-Motion>', self._on_drag)
        
        self.text_area = tk.Text(self.frame, font=('Segoe UI', 9), bg='#333333', fg='#FFFFFF',
                                 bd=0, width=24, height=8, insertbackground='white')
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        if text:
            self.text_area.insert('1.0', text)

    def _start_drag(self, e):
        self.drag_data["x"] = e.x
        self.drag_data["y"] = e.y

    def _on_drag(self, e):
        dx = e.x - self.drag_data["x"]
        dy = e.y - self.drag_data["y"]
        self.x += dx
        self.y += dy
        self.canvas.coords(self.win_id, self.x, self.y)

    def destroy(self):
        self.canvas.delete(self.win_id)
        self.frame.destroy()

    def update_position(self):
        self.canvas.coords(self.win_id, self.x, self.y)

    def update_theme(self, tc):
        self.theme_colors = tc

    def get_config(self):
        txt = self.text_area.get('1.0', tk.END).strip()
        return {'type': 'sticker', 'x': self.x, 'y': self.y, 'text': txt}


# ============================================================================
# 4. ПАНЕЛЬ ЗАДАЧ (TASKBAR С ПОЛНЫМ НАБОРОМ ПРИЛОЖЕНИЙ В ПУСК)
# ============================================================================

class Taskbar:
    """Панель задач: высота строго 40 px (или 48 px в Touch Mode), плоское меню Пуск"""
    def __init__(self, parent, username, commands, theme_colors, desktop_canvas, desktop_icons, desktop):
        self.parent = parent
        self.username = username
        self.commands = commands
        self.colors = theme_colors
        self.desktop = desktop
        self.start_menu_win = None
        self.window_buttons = {}
        self.active_window_key = None
        
        h = self.desktop.bitos.ui_manager.get_sizes()['taskbar_height']
        self.bar = tk.Frame(parent, bg='#101010', height=h)
        self.bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.bar.pack_propagate(False)
        
        start_icon = "☰" if self.desktop.bitos.ui_manager.touch_mode else "❖"
        self.start_btn = tk.Label(self.bar, text=start_icon, font=('Segoe UI', 14, 'bold'),
                                  bg='#101010', fg='#0078D4', width=4, cursor='hand2')
        self.start_btn.pack(side=tk.LEFT, fill=tk.Y)
        self.start_btn.bind('<Button-1>', lambda e: self.toggle_start())
        self.start_btn.bind('<Enter>', lambda e: self.start_btn.config(bg='#202020'))
        self.start_btn.bind('<Leave>', lambda e: self.start_btn.config(bg='#101010'))
        
        self.tasks_frame = tk.Frame(self.bar, bg='#101010')
        self.tasks_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)
        
        tray = tk.Frame(self.bar, bg='#101010')
        tray.pack(side=tk.RIGHT, fill=tk.Y, padx=8)
        
        self.time_lbl = tk.Label(tray, text="", font=('Segoe UI', 9), bg='#101010', fg='#FFFFFF')
        self.time_lbl.pack(side=tk.RIGHT, padx=4)
        
        self.date_lbl = tk.Label(tray, text="", font=('Segoe UI', 8), bg='#101010', fg='#A0A0A0')
        self.date_lbl.pack(side=tk.RIGHT, padx=4)

        self.battery_lbl = tk.Label(tray, text="⚡ --", font=('Segoe UI', 9),
                                    bg='#101010', fg='#A0A0A0', cursor='hand2')
        self.battery_lbl.pack(side=tk.RIGHT, padx=5)
        self.battery_lbl.bind('<Button-1>', lambda e: self.check_system_status())

        self.layout_lbl = tk.Label(tray, text=self._keyboard_layout(), font=('Segoe UI', 8, 'bold'),
                                   bg='#101010', fg='#FFFFFF', cursor='hand2')
        self.layout_lbl.pack(side=tk.RIGHT, padx=5)
        self.layout_lbl.bind('<Button-1>', lambda e: self.toggle_keyboard_layout())

        self.volume_btn = tk.Label(tray, text="🎚", font=('Segoe UI', 10), bg='#101010', fg='#FFFFFF', cursor='hand2')
        self.volume_btn.pack(side=tk.RIGHT, padx=5)
        self.volume_btn.bind('<Button-1>', lambda e: self.open_volume_mixer())

        self.sound_btn = tk.Label(tray, text="🔊" if self.desktop.bitos.sound_enabled else "🔇",
                                  font=('Segoe UI', 11), bg='#101010', fg='#FFFFFF', cursor='hand2')
        self.sound_btn.pack(side=tk.RIGHT, padx=5)
        self.sound_btn.bind('<Button-1>', lambda e: self.toggle_sound())
        self.notify_btn = tk.Label(tray, text="🔔", font=('Segoe UI', 11), bg='#101010', fg='#FFFFFF', cursor='hand2')
        self.notify_btn.pack(side=tk.RIGHT, padx=5)
        self.notify_btn.bind('<Button-1>', lambda e: self.show_notifications())
        self.touch_mode_btn = tk.Button(
            tray, text=self._touch_button_text(), font=('Segoe UI', 8),
            bg='#303030', fg='#FFFFFF', activebackground='#454545', activeforeground='#FFFFFF',
            bd=0, padx=7, cursor='hand2', command=self.toggle_touch_mode
        )
        self.touch_mode_btn.pack(side=tk.RIGHT, padx=5, pady=4)
        self._clock_after_id = None
        self._update_clock()

    def _touch_button_text(self):
        enabled = bool(self.desktop.bitos.ui_manager.touch_mode)
        return 'Сенсорный режим: ВКЛ' if enabled else 'Включить сенсорный режим'

    def toggle_touch_mode(self):
        ui = self.desktop.bitos.ui_manager
        ui.set_touch_mode(not ui.touch_mode)
        self.desktop.apply_ui_settings()
        try:
            self.touch_mode_btn.config(text=self._touch_button_text())
        except Exception:
            pass

    def _update_clock(self):
        now = datetime.now()
        self.time_lbl.config(text=now.strftime("%H:%M"))
        self.date_lbl.config(text=now.strftime("%d.%m.%Y"))
        interval = self.desktop.bitos.ui_manager.clock_interval_ms
        if interval is not None:
            self._clock_after_id = self.bar.after(interval, self._update_clock)

    @staticmethod
    def _keyboard_layout():
        if os.name != 'nt':
            return '⌨'
        try:
            import ctypes
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            thread_id = user32.GetWindowThreadProcessId(hwnd, None)
            layout = user32.GetKeyboardLayout(thread_id) & 0xFFFF
            lang = {0x0419: 'RU', 0x0409: 'EN', 0x0422: 'UK', 0x0407: 'DE', 0x040C: 'FR'}.get(layout)
            return lang or f'{layout:04X}'
        except Exception:
            return '⌨'

    def open_volume_mixer(self):
        try:
            if os.name == 'nt':
                subprocess.Popen(['sndvol.exe'])
            elif shutil.which('pavucontrol'):
                subprocess.Popen(['pavucontrol'])
            elif shutil.which('alsamixer'):
                subprocess.Popen(['x-terminal-emulator', '-e', 'alsamixer'])
        except Exception:
            pass

    def toggle_keyboard_layout(self):
        if os.name != 'nt':
            return
        try:
            import ctypes
            user32 = ctypes.windll.user32
            current = self._keyboard_layout()
            target = '00000409' if current == 'RU' else '00000419'
            hkl = user32.LoadKeyboardLayoutW(target, 0x00000001)
            user32.ActivateKeyboardLayout(hkl, 0)
            self.layout_lbl.config(text=self._keyboard_layout())
        except Exception:
            self.layout_lbl.config(text='⌨')

    def update_system_status(self, battery):
        """Update the compact battery / power indicator."""
        if not battery:
            text = "⚡ --"
        elif battery.get("percent") is None:
            text = "🔌" if battery.get("ac") else "⚡ --"
        else:
            percent = int(battery["percent"])
            if battery.get("charging"):
                text = f"⚡ {percent}%"
            elif battery.get("ac"):
                text = f"🔌 {percent}%"
            else:
                text = f"🔋 {percent}%"
        try:
            self.battery_lbl.config(text=text)
        except Exception:
            pass

    def check_system_status(self):
        monitor = getattr(self.desktop.bitos, "monitor_service", None)
        if monitor is not None:
            monitor.check_now(force=True)

    def toggle_sound(self):
        enabled = self.desktop.bitos.toggle_sound()
        self.sound_btn.config(text="🔊" if enabled else "🔇")

    def show_notifications(self):
        center = self.desktop.notification_center
        win = tk.Toplevel(self.parent)
        win.title("Центр уведомлений")
        win.geometry("380x440")
        win.configure(bg="#1F1F1F")
        header = tk.Frame(win, bg="#1F1F1F")
        header.pack(fill=tk.X, padx=12, pady=10)
        tk.Label(header, text="Уведомления", font=('Segoe UI', 14, 'bold'), bg="#1F1F1F", fg="white").pack(side=tk.LEFT)
        tk.Button(header, text="Очистить", bg="#333333", fg="white", bd=0,
                  command=lambda: (center.notifications.clear(), center.save_history(), win.destroy())).pack(side=tk.RIGHT)
        area = tk.Frame(win, bg="#1F1F1F")
        area.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        if not center.notifications:
            tk.Label(area, text="Новых уведомлений нет", bg="#1F1F1F", fg="#A0A0A0").pack(pady=30)
        else:
            for item in reversed(center.notifications[-30:]):
                card = tk.Frame(area, bg="#292929", padx=8, pady=7)
                card.pack(fill=tk.X, pady=3)
                tk.Label(card, text=f"{item.get('icon','🔔')}  {item.get('title','Уведомление')}",
                         bg="#292929", fg="#FFFFFF", font=('Segoe UI', 10, 'bold'), anchor="w").pack(fill=tk.X)
                tk.Label(card, text=item.get('message',''), bg="#292929", fg="#CFCFCF",
                         font=('Segoe UI', 9), wraplength=330, justify="left", anchor="w").pack(fill=tk.X, pady=(3,0))

    def register_window(self, window, title=None, icon="▣"):
        """Show application windows as live buttons in the BITOS taskbar."""
        key = id(window)
        if key in self.window_buttons:
            return
        try:
            if not window.winfo_exists():
                return
            title = (title or window.title() or "Окно").strip()
            button = tk.Button(
                self.tasks_frame, text=f"{icon} {title[:10]}",
                font=('Segoe UI', 8), bg=self.colors.get('taskbar_bg', '#101010'),
                fg=self.colors.get('taskbar_fg', '#FFFFFF'), bd=0,
                activebackground=self.colors.get('taskbar_hover', '#2B2B2B'),
                activeforeground=self.colors.get('taskbar_fg', '#FFFFFF'),
                padx=7, cursor='hand2',
                command=lambda w=window: self._focus_window(w),
            )
            button.pack(side=tk.LEFT, fill=tk.Y, padx=2, pady=3)
            self.window_buttons[key] = (window, button)
            try:
                window._bitos_desktop = self.desktop
                window.protocol("WM_DELETE_WINDOW", lambda w=window: self.desktop._animate_window_close(w))
                self.desktop._install_window_hover(window)
                self.desktop._animate_window_open(window)
            except Exception:
                pass
            window.bind('<FocusIn>', lambda e, k=key: self._activate_window(k), add='+')
            window.bind('<Destroy>', lambda e, k=key, w=window: self._on_window_destroy(e, k, w), add='+')
            button.bind('<Button-3>', lambda e, k=key: self._show_window_menu(e, k))
        except Exception:
            pass

    def _show_window_menu(self, event, key):
        item = self.window_buttons.get(key)
        if not item:
            return
        window, _button = item
        menu = tk.Menu(self.parent, tearoff=0, bg='#1F1F1F', fg='white', activebackground='#0078D4')
        menu.add_command(label='Переключиться', command=lambda: self._focus_window(window))
        menu.add_command(label='Закрыть окно', command=lambda: self._close_window(window))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    @staticmethod
    def _close_window(window):
        try:
            if window.winfo_exists():
                desktop = getattr(window, "_bitos_desktop", None)
                if desktop is not None:
                    desktop._animate_window_close(window)
                else:
                    window.destroy()
        except Exception:
            pass

    def _focus_window(self, window):
        try:
            if not window.winfo_exists():
                return
            desktop = getattr(window, "_bitos_desktop", None)
            key = id(window)
            if (desktop is not None and self.active_window_key == key
                    and window.state() not in ("withdrawn", "iconic")):
                desktop._animate_window_minimize(window)
                return
            window.deiconify()
            window.lift()
            window.focus_force()
            if desktop is not None:
                desktop._animate_window_open(window)
        except Exception:
            pass

    def _activate_window(self, key):
        self.active_window_key = key
        for item_key, (_, button) in list(self.window_buttons.items()):
            try:
                button.configure(relief=(tk.SUNKEN if item_key == key else tk.FLAT))
            except Exception:
                pass

    def _on_window_destroy(self, event, key, window):
        if event.widget is window:
            item = self.window_buttons.pop(key, None)
            if item:
                try: item[1].destroy()
                except Exception: pass

    def toggle_start(self):
        if self.start_menu_win and self.start_menu_win.winfo_exists():
            menu_window = self.start_menu_win
            self.start_menu_win = None
            self.desktop._animate_window_close(menu_window)
            return
        self.show_start()

    def show_start(self):
        """Меню Пуск: содержит ВСЕ приложения системы в плоской сетке плиток"""
        sizes = self.desktop.bitos.ui_manager.get_sizes()
        sm = tk.Toplevel(self.parent)
        sm.overrideredirect(True)
        w, h = sizes['start_w'], sizes['start_h']
        x = 0
        y = self.parent.winfo_screenheight() - sizes['taskbar_height'] - h
        sm.geometry(f"{w}x{h}+{x}+{y}")
        sm.configure(bg='#1F1F1F')
        self.start_menu_win = sm
        if self.desktop.bitos.ui_manager.start_menu_animations_enabled:
            try:
                sm.attributes('-alpha', 0.0)
                def fade_in(alpha=0.12):
                    if not sm.winfo_exists() or getattr(sm, "_bitos_closing", False):
                        return
                    alpha = min(1.0, alpha)
                    try: sm.attributes('-alpha', alpha)
                    except Exception: return
                    if alpha < 1.0:
                        sm.after(12, lambda: fade_in(alpha + 0.18))
                sm.after(12, fade_in)
            except Exception:
                pass
        
        nav_left = tk.Frame(sm, bg='#141414', width=48)
        nav_left.pack(side=tk.LEFT, fill=tk.Y)
        nav_left.pack_propagate(False)
        
        pwr_btn = tk.Label(nav_left, text="⏻", font=('Segoe UI', 13), bg='#141414', fg='white', cursor='hand2')
        pwr_btn.pack(side=tk.BOTTOM, pady=12)
        pwr_btn.bind('<Button-1>', lambda e: shutdown_windows())
        
        set_btn = tk.Label(nav_left, text="⚙", font=('Segoe UI', 13), bg='#141414', fg='white', cursor='hand2')
        set_btn.pack(side=tk.BOTTOM, pady=6)
        set_btn.bind('<Button-1>', lambda e: (sm.destroy(), self.commands['settings']()))
        
        grid_frame = tk.Frame(sm, bg='#1F1F1F')
        grid_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=12, pady=12)
        
        # ПОЛНЫЙ ПЕРЕЧЕНЬ ПРИЛОЖЕНИЙ
        apps = [
            ("📁", "Проводник", 'explorer'),
            ("⚙", "Настройки", 'settings'),
            ("🗑", "Корзина", 'trash'),
            ("🎨", "Paint", 'paint'),
            ("🖼", "Галерея", 'gallery'),
            ("🧮", "Калькулятор", 'calc'),
            ("📝", "Заметки", 'notes'),
            ("📦", "BIP Установщик", 'bip_installer'),
            ("🔧", "Разработчик", 'dev_mode'),
            ("📡", "Терминал", 'terminal'),
            ("🛒", "Магазин", 'app_store'),
            ("📊", "Диспетчер задач", 'task_manager'),
            ("🎵", "Медиаплеер", 'media_player')
        ]
        
        # Installed .bip apps appear in Start without changing the core launcher.
        try:
            bip = BipInstaller(self.parent, self.desktop.bitos)
            for item in bip.get_start_menu_apps():
                apps.append((item.get('icon', '📦'), item.get('name', 'Приложение'),
                             f"bip:{item.get('id', '')}"))
        except Exception:
            pass

        for i, (ico, name, cmd_name) in enumerate(apps):
            r = i // 4
            c = i % 4
            tile = tk.Frame(grid_frame, bg='#0078D4', width=104, height=100)
            tile.grid(row=r, column=c, padx=4, pady=4)
            tile.pack_propagate(False)
            
            lbl_ico = tk.Label(tile, text=ico, font=('Segoe UI', 30), bg='#0078D4', fg='white')
            lbl_ico.pack(expand=True)
            lbl_t = tk.Label(tile, text=name, font=('Segoe UI', 9), bg='#0078D4', fg='white')
            lbl_t.pack(side=tk.BOTTOM, pady=2)
            
            def bind_click(t, cn=cmd_name, nm=name, ic=ico):
                # Launch only on a click; a drag is handled by the same release
                # handler and must never accidentally open the application.
                t.bind('<ButtonPress-1>', lambda ev: self._start_app_drag(ev, cn, nm, ic))
                t.bind('<B1-Motion>', self._move_app_drag)
                t.bind('<ButtonRelease-1>', lambda ev: self._end_app_drag(ev, sm, cn))
                t.bind('<Enter>', lambda ev, w=t: self._tile_hover(w, True))
                t.bind('<Leave>', lambda ev, w=t: self._tile_hover(w, False))
            for el in (tile, lbl_ico, lbl_t):
                bind_click(el)
            if cmd_name.startswith('bip:'):
                def add_bip_shortcut(_event=None, aid=cmd_name.split(':', 1)[1]):
                    ok, message = BipInstaller(self.parent, self.desktop.bitos).add_to_desktop(aid)
                    if ok:
                        self.desktop.create_default_icons()
                        self.desktop.bitos.play_sound('success')
                    else:
                        messagebox.showerror('Ярлык приложения', message, parent=self.parent)
                for el in (tile, lbl_ico, lbl_t):
                    el.bind('<Button-3>', add_bip_shortcut)

        sm.bind('<FocusOut>', lambda e: self.desktop._animate_window_close(sm))
        sm.focus_set()

    def _start_app_drag(self, event, command_key, name, icon):
        self._app_drag = {"x": event.x_root, "y": event.y_root, "key": command_key, "name": name, "icon": icon, "moved": False}

    def _move_app_drag(self, event):
        drag = getattr(self, "_app_drag", None)
        if drag and (abs(event.x_root-drag["x"]) + abs(event.y_root-drag["y"]) > 8):
            drag["moved"] = True

    def _tile_hover(self, widget, active):
        # A short stepped transition gives tiles a hover animation without
        # introducing a heavy animation loop or blocking the Tk event thread.
        colors = ["#0078D4", "#0B82D9", "#168AE0", "#2695E8"]
        steps = colors if active else list(reversed(colors))
        try:
            if getattr(widget, "_hover_after", None):
                widget.after_cancel(widget._hover_after)
            def apply_step(index=0):
                if index >= len(steps) or not widget.winfo_exists():
                    return
                color = steps[index]
                widget.configure(bg=color)
                for child in widget.winfo_children():
                    child.configure(bg=color)
                widget._hover_after = widget.after(18, lambda: apply_step(index + 1))
            apply_step()
        except Exception:
            pass

    def _end_app_drag(self, event, start_menu=None, command_key=None):
        drag = getattr(self, "_app_drag", None)
        self._app_drag = None
        if drag and drag.get("moved"):
            desktop = self.desktop
            # Release over the taskbar pins the app; elsewhere creates a desktop shortcut.
            taskbar_top = self.parent.winfo_screenheight() - self.bar.winfo_height()
            if event.y_root >= taskbar_top:
                self.pin_app_to_taskbar(drag["icon"], drag["name"], drag["key"])
            else:
                desktop.add_desktop_shortcut(drag["icon"], drag["name"], drag["key"])
            try:
                if start_menu and start_menu.winfo_exists(): self.desktop._animate_window_close(start_menu)
            except Exception:
                pass
            return
        # A stationary release is a normal click and launches the app.
        if command_key:
            self.desktop.bitos.play_sound("click")
            try:
                if start_menu and start_menu.winfo_exists(): self.desktop._animate_window_close(start_menu)
            except Exception:
                pass
            if str(command_key).startswith('bip:'):
                app_id = str(command_key).split(':', 1)[1]
                ok, result = BipInstaller(self.parent, self.desktop.bitos).launch_app(app_id)
                if not ok:
                    messagebox.showerror('Запуск приложения', result, parent=self.parent)
            elif command_key in self.commands:
                self.commands[command_key]()

    def pin_app_to_taskbar(self, icon, name, key):
        cfg = os.path.join(self.desktop.bitos.system_paths["config"], "taskbar_pins.json")
        try:
            os.makedirs(os.path.dirname(cfg), exist_ok=True)
            pins = json.loads(Path(cfg).read_text(encoding="utf-8")) if os.path.exists(cfg) else []
            if not any(p.get("command") == key for p in pins):
                pins.append({"icon": icon, "name": name, "command": key})
                Path(cfg).write_text(json.dumps(pins, ensure_ascii=False, indent=2), encoding="utf-8")
            # Render pinned apps as launch buttons, persisted across sessions.
            self._render_pinned_apps()
        except Exception:
            pass

    def _render_pinned_apps(self):
        cfg = os.path.join(self.desktop.bitos.system_paths["config"], "taskbar_pins.json")
        try:
            pins = json.loads(Path(cfg).read_text(encoding="utf-8"))
            for pin in pins:
                key = pin.get("command")
                if key not in self.commands and not str(key).startswith("bip:"):
                    continue
                btn = tk.Button(self.tasks_frame, text=f'{pin.get("icon","")} {pin.get("name","")[:8]}',
                    bg="#101010", fg="white", bd=0, command=lambda k=key: self._launch_pin(k))
                btn.pack(side=tk.LEFT, fill=tk.Y, padx=1)
        except Exception:
            pass

    def _launch_pin(self, key):
        if str(key).startswith("bip:"):
            self.desktop.launch_bip_app(str(key).split(":", 1)[1])
        elif key in self.commands:
            self.commands[key]()

    def update_theme(self, colors):
        self.colors = colors
        bg = colors.get("taskbar_bg", "#101010")
        fg = colors.get("taskbar_fg", "#FFFFFF")
        for widget in (self.bar, self.start_btn, self.tasks_frame):
            try: widget.configure(bg=bg)
            except Exception: pass
        for widget in (self.time_lbl, self.date_lbl, self.battery_lbl, self.sound_btn, self.volume_btn, self.notify_btn, self.layout_lbl):
            try: widget.configure(bg=bg, fg=fg)
            except Exception: pass


# ============================================================================
# 5. РАБОЧИЙ СТОЛ (ТОЛЬКО 2 ИКОНКИ: ЭТОТ ПК И КОРЗИНА + ПОЛНОЕ МЕНЮ ПКМ)
# ============================================================================

class Desktop:
    """Рабочий стол: 2 постоянные иконки, виджеты, динамический режим планшета"""
    THEMES = {
        "Белая": {'name': 'Белая', 'bg': '#F4F4F4', 'fg': '#171717', 'accent': '#D8D8D8', 'taskbar_bg': '#E7E7E7', 'canvas_bg': '#F4F4F4', 'icon_fg': '#171717', 'taskbar_fg': '#171717'},
        "Чёрная": {'name': 'Чёрная', 'bg': '#101010', 'fg': '#FFFFFF', 'accent': '#303030', 'taskbar_bg': '#080808', 'canvas_bg': '#101010', 'icon_fg': '#FFFFFF', 'taskbar_fg': '#FFFFFF'},
        "Голубая": {'name': 'Голубая', 'bg': '#EAF7FF', 'fg': '#102D40', 'accent': '#79C8F2', 'taskbar_bg': '#D7F0FF', 'canvas_bg': '#EAF7FF', 'icon_fg': '#102D40', 'taskbar_fg': '#102D40'},
        "Розовая": {'name': 'Розовая', 'bg': '#FFF0F6', 'fg': '#482338', 'accent': '#F2A9C9', 'taskbar_bg': '#FADCE9', 'canvas_bg': '#FFF0F6', 'icon_fg': '#482338', 'taskbar_fg': '#482338'}
    }

    def __init__(self, root, username, bitos):
        self.root = root
        self.username = username
        self.bitos = bitos
        self.root.overrideredirect(True)
        _maximize_window(self.root)
        
        self.ui = bitos.ui_manager
        _bind_touch_keyboard(self.root, lambda: bool(self.ui.touch_mode))
        self.current_theme = self._load_saved_theme()
        self.theme_colors = dict(self.THEMES.get(self.current_theme, self.ui.get_colors(self.current_theme)))
        
        self.wallpaper_manager = WallpaperManager(bitos)
        self.notification_center = NotificationCenter(root, bitos)
        
        sizes = self.ui.get_sizes()
        self.canvas = tk.Canvas(self.root, bg=self.theme_colors['canvas_bg'], highlightthickness=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1, height=-sizes['taskbar_height'])
        self.canvas.desktop_icons = []
        self.canvas.desktop_owner = self
        self.widgets = []
        self.widgets_visible = True
        
        self.commands = {
            'explorer': self.open_explorer,
            'settings': self.open_settings,
            'trash': self.open_trash,
            'gallery': self.open_gallery,
            'paint': self.open_paint,
            'calc': self.open_calc,
            'notes': self.open_notes,
            'terminal': self.open_terminal,
            'app_store': self.open_app_store,
            'task_manager': self.open_task_manager,
            'media_player': self.open_media_player,
            'bip_installer': self.open_bip_installer,
            'dev_mode': self.open_dev_mode,
            'logout': self.logout,
            'shutdown': shutdown_windows,
            'reboot': restart_windows
        }
        
        self.taskbar = Taskbar(self.root, username, self.commands, self.theme_colors,
                               self.canvas, self.canvas.desktop_icons, self)
        self._desktop_autosave_after_id = None
        self._schedule_desktop_autosave()
        
        self.update_wallpaper()
        self.create_default_icons()
        self.load_virtual_desktop_files()
        self.load_widgets()
        
        self.context_menu = self.create_context_menu()
        self.canvas.bind('<Button-3>', self.show_context_menu)

    def refresh_desktop(self):
        """Rebuild the desktop from live filesystem contents and saved shortcut layout."""
        self.update_wallpaper()
        try:
            # Recreate system/app shortcuts from their config, then scan the real
            # desktop directory. A deleted/moved file or folder cannot be brought
            # back by a stale desktop_layout.json entry.
            self.create_default_icons()
            self.load_virtual_desktop_files()
            self._autosave_desktop_state()
        except Exception as exc:
            if getattr(self.ui, "logs_enabled", True):
                try:
                    self.bitos.error_manager._log_warning("Desktop.refresh", str(exc))
                except Exception:
                    pass
            messagebox.showerror("Рабочий стол", f"Не удалось обновить рабочий стол:\n{exc}", parent=self.root)
        try:
            self.canvas.tag_raise('widget')
            self.canvas.tag_raise('icon')
        except Exception:
            pass
        if getattr(self.bitos.ui_manager, "logs_enabled", True):
            self.notification_center.add_notification(
                "Рабочий стол обновлён", "Настройки и ярлыки обновлены", icon="🔄", duration=1600
            )

    def _load_saved_theme(self):
        config_dir = self.bitos.system_paths["config"]
        try:
            with open(os.path.join(config_dir, "user_themes.json"), "r", encoding="utf-8") as f:
                custom = json.load(f)
            if isinstance(custom, dict):
                self.THEMES.update(custom)
        except Exception:
            pass
        theme_file = os.path.join(config_dir, "theme.cfg")
        try:
            with open(theme_file, "r", encoding="utf-8") as f:
                name = json.load(f).get("theme", "Базовая")
            return name if name in self.THEMES else "Чёрная"
        except Exception:
            return "Чёрная"

    def update_wallpaper(self):
        """Отрисовывает обои и опускает их под все иконки и виджеты"""
        try:
            w = self.canvas.winfo_width()
            h = self.canvas.winfo_height()
            if w <= 1 or h <= 1:
                w = self.root.winfo_screenwidth()
                h = self.root.winfo_screenheight()
                
            self.canvas.delete('wallpaper')
            drawn = self.wallpaper_manager.draw_on_canvas(self.canvas, w, h)
            
            if not drawn:
                c1 = self.theme_colors.get('canvas_bg', '#1A1A1A')
                self.canvas.create_rectangle(0, 0, w, h, fill=c1, outline='', tags='wallpaper')

            self.canvas.tag_lower('wallpaper')
            self.canvas.tag_raise('widget')
            self.canvas.tag_raise('icon')
        except Exception:
            pass

    def apply_ui_settings(self):
        """Мгновенное применение настроек без перезапуска программы"""
        sizes = self._get_scaled_icon_sizes()
        new_tb_height = sizes['taskbar_height']
        
        self.canvas.place_configure(x=0, y=0, relwidth=1, relheight=1, height=-new_tb_height)
        self.taskbar.bar.config(height=new_tb_height)
        
        if sizes['touch_mode']:
            self.taskbar.start_btn.config(text="☰", width=5)
        else:
            self.taskbar.start_btn.config(text="❖", width=4)
        try:
            self.taskbar.touch_mode_btn.config(text=self.taskbar._touch_button_text())
        except Exception:
            pass
            
        for icon in self.canvas.desktop_icons:
            icon.update_metrics(
                size=sizes['icon_size'],
                step=sizes['grid_step'],
                font_size=sizes['icon_font_size']
            )
            
        self.widgets_visible = self.ui.widgets_enabled
        for widget in self.widgets:
            try:
                self.canvas.itemconfigure(widget.win_id, state=(tk.NORMAL if self.widgets_visible else tk.HIDDEN))
                if hasattr(widget, "refresh_profile"):
                    widget.refresh_profile()
            except Exception:
                pass
        self.update_wallpaper()
        if hasattr(self.bitos, "task_manager"):
            self.bitos.task_manager.refresh_profile()
        if hasattr(self.bitos, "security"):
            self.bitos.security.refresh_profile()
        if hasattr(self.bitos, "error_manager"):
            self.bitos.error_manager.refresh_profile()
        if hasattr(self.bitos, "monitor_service"):
            self.bitos.monitor_service.refresh_profile()
        if hasattr(self.bitos, "autosafe"):
            self.bitos.autosafe.refresh_profile()
        if hasattr(self.taskbar, "_clock_after_id"):
            if self.taskbar._clock_after_id is not None:
                try:
                    self.taskbar.bar.after_cancel(self.taskbar._clock_after_id)
                except Exception:
                    pass
                self.taskbar._clock_after_id = None
            self.taskbar._update_clock()
        self.root.update_idletasks()

    def _get_saved_icon_scale(self):
        path = os.path.join(self.bitos.system_paths['config'], 'desktop_icon_scale.json')
        try:
            value = int(json.loads(Path(path).read_text(encoding='utf-8')).get('scale', 100))
        except Exception:
            value = 100
        return max(60, min(140, value))

    def _get_scaled_icon_sizes(self):
        sizes = dict(self.ui.get_sizes())
        scale = self._get_saved_icon_scale() / 100.0
        sizes['icon_size'] = max(52, int(sizes['icon_size'] * scale))
        sizes['grid_step'] = max(sizes['icon_size'] + 12, int(sizes['grid_step'] * scale))
        sizes['icon_font_size'] = max(8, int(sizes['icon_font_size'] * scale))
        return sizes

    def create_default_icons(self):
        """Create the two system icons, then restore the user's saved shortcuts."""
        sizes = self._get_scaled_icon_sizes()
        for old in list(self.canvas.desktop_icons):
            try:
                old.destroy()
            except Exception:
                pass
        self.canvas.desktop_icons.clear()
        defaults = [
            ("📁", "Этот ПК", "explorer", self.open_explorer),
            ("🗑", "Корзина", "trash", self.open_trash),
        ]
        for i, (ico, name, key, cmd) in enumerate(defaults):
            self.canvas.desktop_icons.append(DesktopIcon(
                self.canvas, 0, i, ico, name, cmd, size=sizes['icon_size'],
                step=sizes['grid_step'], font_size=sizes['icon_font_size'], command_key=key
            ))
        shortcuts_file = os.path.join(self.bitos.system_paths["config"], "desktop_shortcuts.json")
        try:
            with open(shortcuts_file, "r", encoding="utf-8") as f:
                saved = json.load(f)
        except Exception:
            saved = []
        existing = {x.text.lower() for x in self.canvas.desktop_icons}
        for item in saved if isinstance(saved, list) else []:
            label = str(item.get("text", "Ярлык"))
            if label.lower() in existing:
                continue
            command_key = item.get("command") or item.get("command_key")
            command = self.commands.get(command_key)
            if command is None and str(command_key).startswith("bip:"):
                app_id = str(command_key).split(":", 1)[1]
                command = lambda aid=app_id: self.launch_bip_app(aid)
            if command is None:
                continue
            self.canvas.desktop_icons.append(DesktopIcon(
                self.canvas,
                int(item.get("grid_x", 1)),
                int(item.get("grid_y", 0)),
                item.get("icon", "📦"), label, command,
                icon_id=item.get("icon_id"), size=sizes['icon_size'],
                step=sizes['grid_step'], font_size=sizes['icon_font_size'],
                command_key=command_key
            ))
            existing.add(label.lower())

    def show_shortcut_info(self, icon):
        key = getattr(icon, "command_key", None) or "unknown"
        messagebox.showinfo("Информация о приложении",
                           f"Название: {icon.text}\\nКоманда: {key}\\nЯрлык BITOS",
                           parent=self.root)

    def remove_desktop_shortcut(self, icon):
        if icon.text in ("Этот ПК", "Корзина"):
            return
        try:
            icon.destroy()
            if icon in self.canvas.desktop_icons:
                self.canvas.desktop_icons.remove(icon)
            self.save_desktop_shortcuts()
        except Exception as exc:
            messagebox.showerror("Ярлык", str(exc), parent=self.root)

    def remove_desktop_document(self, icon):
        path = getattr(icon, "virtual_path", None)
        if not path or not os.path.isfile(path):
            messagebox.showerror("Удаление документа", "Документ не найден.", parent=self.root)
            self.refresh_desktop()
            return
        if not messagebox.askyesno("Удалить документ",
                f"Переместить документ «{os.path.basename(path)}» в корзину BITOS?", parent=self.root):
            return
        try:
            TrashManager(self.bitos).move_to_trash([path])
            icon.destroy()
            if icon in self.canvas.desktop_icons:
                self.canvas.desktop_icons.remove(icon)
            self._autosave_desktop_state()
            self.bitos.play_sound("success")
        except Exception as exc:
            messagebox.showerror("Удаление документа", str(exc), parent=self.root)

    def remove_desktop_folder(self, icon):
        """Move the actual desktop folder (not merely its icon) into BITOS Trash."""
        path = getattr(icon, "virtual_path", None)
        if not path or not os.path.isdir(path):
            messagebox.showerror("Удаление папки", "Папка не найдена.", parent=self.root)
            self.refresh_desktop()
            return
        if not messagebox.askyesno(
                "Удалить папку",
                f"Переместить папку «{os.path.basename(path)}» и всё её содержимое в корзину BITOS?",
                parent=self.root
        ):
            return
        try:
            TrashManager(self.bitos).move_to_trash([path])
            icon.destroy()
            if icon in self.canvas.desktop_icons:
                self.canvas.desktop_icons.remove(icon)
            # Persist the new icon/layout state immediately; disk contents are
            # represented by the actual desktop directory, never by a snapshot.
            self._autosave_desktop_state()
            self.bitos.play_sound("success")
        except Exception as exc:
            messagebox.showerror("Удаление папки", str(exc), parent=self.root)

    def remove_bip_shortcut(self, icon):
        key = str(getattr(icon, "command_key", "") or "")
        if not key.startswith("bip:"):
            messagebox.showinfo("Удаление приложения", "Удалить приложение можно только для BIP-приложений.", parent=self.root)
            return
        app_id = key.split(":", 1)[1]
        if not messagebox.askyesno("Удалить приложение (BIP)", f"Удалить приложение «{icon.text}»?", parent=self.root):
            return
        try:
            installer = BipInstaller(self.root, self.bitos)
            result = installer.uninstall_app(app_id)
            self.remove_desktop_shortcut(icon)
            messagebox.showinfo("Удаление приложения", str(result), parent=self.root)
        except Exception as exc:
            messagebox.showerror("Удаление приложения", str(exc), parent=self.root)

    def _find_free_desktop_grid_position(self):
        occupied = {(icon.grid_x, icon.grid_y) for icon in self.canvas.desktop_icons}
        for row in range(40):
            for col in range(20):
                if (col, row) not in occupied:
                    return col, row
        return 0, 40

    @staticmethod
    def _get_file_icon_symbol(filename, is_dir=False):
        if is_dir:
            return "📁"
        ext = os.path.splitext(filename)[1].lower()
        icons = {
            ".txt": "📄", ".md": "📝", ".doc": "📝", ".docx": "📝",
            ".png": "🖼", ".jpg": "🖼", ".jpeg": "🖼", ".gif": "🖼", ".bmp": "🖼", ".webp": "🖼",
            ".wav": "🎵", ".mp3": "🎵", ".flac": "🎵", ".mp4": "🎬", ".mkv": "🎬", ".avi": "🎬",
            ".pdf": "📕", ".zip": "📦", ".rar": "📦", ".7z": "📦", ".py": "🐍",
            ".js": "📜", ".html": "🌐", ".css": "🎨", ".xlsx": "📊", ".xls": "📊",
            ".json": "📊", ".xml": "📝", ".csv": "📊", ".log": "📋", ".cfg": "⚙"
        }
        return icons.get(ext, "📄")

    def load_virtual_desktop_files(self):
        """Restore file and folder icons from the user's portable BITOS desktop folder."""
        folder = self.bitos.user_paths.get("desktop")
        if not folder:
            return
        os.makedirs(folder, exist_ok=True)
        layout_map = {}
        try:
            layout_path = os.path.join(self.bitos.system_paths["config"], "desktop_layout.json")
            with open(layout_path, "r", encoding="utf-8") as f:
                saved_layout = json.load(f)
            if isinstance(saved_layout, list):
                layout_map = {os.path.abspath(item.get("virtual_path", "")): item
                              for item in saved_layout if isinstance(item, dict) and item.get("virtual_path")}
        except Exception:
            layout_map = {}
        try:
            entries = sorted(os.scandir(folder), key=lambda e: (not e.is_dir(follow_symlinks=False), e.name.casefold()))
        except OSError as exc:
            if self.ui.logs_enabled:
                self.bitos.error_manager._log_warning("Desktop.files", str(exc))
            return
        for entry in entries:
            if entry.name.startswith("."):
                continue
            try:
                is_dir = entry.is_dir(follow_symlinks=False)
                if not is_dir and not entry.is_file(follow_symlinks=False):
                    continue
                path = entry.path
                if any(getattr(icon, "virtual_path", None) == path for icon in self.canvas.desktop_icons):
                    continue
                saved_position = layout_map.get(os.path.abspath(path), {})
                if saved_position:
                    gx, gy = int(saved_position.get("grid_x", 0)), int(saved_position.get("grid_y", 0))
                else:
                    gx, gy = self._find_free_desktop_grid_position()
                scaled_sizes = self._get_scaled_icon_sizes()
                icon = DesktopIcon(
                    self.canvas, gx, gy, self._get_file_icon_symbol(entry.name, is_dir),
                    entry.name, (lambda p=path: self.open_virtual_folder(p)) if is_dir
                    else (lambda p=path: self.open_virtual_file(p)),
                    size=scaled_sizes["icon_size"], step=scaled_sizes["grid_step"],
                    font_size=scaled_sizes["icon_font_size"]
                )
                icon.virtual_path = path
                icon.is_virtual_item = True
                icon.update_theme(self.theme_colors.get("icon_fg", "#FFFFFF"))
                self.canvas.desktop_icons.append(icon)
            except OSError:
                continue
        self.canvas.tag_raise("icon")

    def open_virtual_folder(self, folder_path):
        if os.path.isdir(folder_path):
            return self.open_explorer(folder_path)
        messagebox.showerror("Рабочий стол", "Папка больше не существует", parent=self.root)
        self.refresh_desktop()

    def open_virtual_file(self, file_path):
        if not os.path.isfile(file_path):
            messagebox.showerror("Рабочий стол", "Файл больше не существует", parent=self.root)
            self.refresh_desktop()
            return
        ext = os.path.splitext(file_path)[1].lower()
        text_extensions = {".txt", ".md", ".py", ".pyw", ".json", ".cfg", ".ini", ".log", ".html", ".css", ".js", ".xml", ".csv"}
        if ext not in text_extensions:
            try:
                if os.name == "nt":
                    os.startfile(file_path)
                else:
                    import webbrowser
                    webbrowser.open(Path(file_path).resolve().as_uri())
                return
            except Exception as exc:
                messagebox.showerror("Открытие файла", str(exc), parent=self.root)
                return
        try:
            if os.path.getsize(file_path) > 2 * 1024 * 1024:
                messagebox.showwarning("Редактор", "Файл больше 2 МБ. Откройте его через проводник.", parent=self.root)
                return
            content = Path(file_path).read_text(encoding="utf-8")
        except UnicodeError:
            messagebox.showwarning("Редактор", "Файл не является текстовым UTF-8 документом.", parent=self.root)
            return
        except OSError as exc:
            messagebox.showerror("Редактор", str(exc), parent=self.root)
            return
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Редактор — {os.path.basename(file_path)}")
        dialog.geometry("800x560")
        dialog.configure(bg="#1F1F1F")
        editor = scrolledtext.ScrolledText(dialog, bg="#242424", fg="#EAEAEA", insertbackground="white",
                                           font=("Consolas", 10), undo=True)
        editor.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        editor.insert("1.0", content)
        def select_all(_event=None):
            editor.tag_add("sel", "1.0", "end-1c")
            editor.mark_set("insert", "end-1c")
            editor.see("insert")
            return "break"
        def cut_text(_event=None):
            try:
                selected = editor.get("sel.first", "sel.last")
                dialog.clipboard_clear(); dialog.clipboard_append(selected)
                editor.delete("sel.first", "sel.last")
            except tk.TclError:
                pass
            return "break"
        def copy_text(_event=None):
            try:
                dialog.clipboard_clear(); dialog.clipboard_append(editor.get("sel.first", "sel.last"))
            except tk.TclError:
                pass
            return "break"
        def paste_text(_event=None):
            try:
                value = dialog.clipboard_get()
                editor.insert("insert", value)
            except tk.TclError:
                pass
            return "break"
        def undo_text(_event=None):
            try: editor.edit_undo()
            except tk.TclError: pass
            return "break"
        def redo_text(_event=None):
            try: editor.edit_redo()
            except tk.TclError: pass
            return "break"
        editor.bind("<Control-a>", select_all)
        editor.bind("<Control-A>", select_all)
        editor.bind("<Control-s>", lambda _e: (save(), "break")[1])
        editor.bind("<Control-S>", lambda _e: (save(), "break")[1])
        editor.bind("<Control-x>", cut_text); editor.bind("<Control-X>", cut_text)
        editor.bind("<Control-c>", copy_text); editor.bind("<Control-C>", copy_text)
        editor.bind("<Control-v>", paste_text); editor.bind("<Control-V>", paste_text)
        editor.bind("<Control-z>", undo_text); editor.bind("<Control-Z>", undo_text)
        editor.bind("<Control-y>", redo_text); editor.bind("<Control-Y>", redo_text)
        def save():
            try:
                Path(file_path).write_text(editor.get("1.0", "end-1c"), encoding="utf-8")
                self.bitos.security.log_file_access(self.username, file_path, "EDIT")
                self.bitos.play_sound("success")
            except OSError as exc:
                messagebox.showerror("Сохранение", str(exc), parent=dialog)
        bar = tk.Frame(dialog, bg="#1F1F1F")
        bar.pack(fill=tk.X, padx=10, pady=(0, 10))
        tk.Button(bar, text="Сохранить", bg="#0078D4", fg="white", bd=0, padx=14, command=save).pack(side=tk.LEFT)
        tk.Button(bar, text="Закрыть", bg="#333333", fg="white", bd=0, padx=14, command=dialog.destroy).pack(side=tk.LEFT, padx=6)

    def load_widgets(self):
        """Restore only explicitly saved widgets; a fresh profile starts empty."""
        cfg_path = os.path.join(self.bitos.system_paths["config"], "widgets.json")
        data = []
        if os.path.isfile(cfg_path):
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                data = loaded if isinstance(loaded, list) else []
            except Exception:
                data = []
        for item in data:
            try:
                widget_type = item.get("type")
                x, y = int(item.get("x", 140)), int(item.get("y", 30))
                if widget_type == "clock":
                    widget = ClockWidget(self.canvas, self.theme_colors, x, y)
                elif widget_type == "calendar":
                    widget = CalendarWidget(self.canvas, self.theme_colors, x, y)
                elif widget_type == "sticker":
                    widget = StickerWidget(self.canvas, self.theme_colors, x, y, item.get("text", ""))
                else:
                    continue
                self.widgets.append(widget)
            except Exception as exc:
                if self.ui.logs_enabled:
                    self.bitos.error_manager._log_warning("Desktop.load_widgets", str(exc))
        self.widgets_visible = self.ui.widgets_enabled
        if not self.widgets_visible:
            for widget in self.widgets:
                self.canvas.itemconfigure(widget.win_id, state=tk.HIDDEN)
        self.save_widgets()

    def save_widgets(self):
        """Сохранение конфигурации виджетов"""
        cfg_path = os.path.join(self.bitos.system_paths["config"], "widgets.json")
        try:
            data = [w.get_config() for w in self.widgets if hasattr(w, 'get_config')]
            with open(cfg_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

    def create_context_menu(self):
        """Контекстное меню рабочего стола ПКМ с полным перечнем действий"""
        menu = tk.Menu(self.root, tearoff=0, bg='#1F1F1F', fg='white',
                       activebackground='#0078D4', bd=1, relief=tk.SOLID)
        
        menu.add_command(label="📁 Создать папку", command=self._ctx_create_folder)
        menu.add_command(label="📄 Создать документ", command=self._ctx_create_document_dialog)
        menu.add_separator()
        menu.add_command(label="🔄 Обновить", command=self.refresh_desktop)
        menu.add_separator()
        menu.add_command(label="🖼 Обои рабочего стола", command=self.open_wallpaper_settings)
        widget_menu = tk.Menu(menu, tearoff=0, bg="#1F1F1F", fg="white", activebackground="#0078D4")
        widget_menu.add_command(label="🕒 Добавить часы", command=lambda: self.add_widget("clock"))
        widget_menu.add_command(label="📅 Добавить календарь", command=lambda: self.add_widget("calendar"))
        widget_menu.add_command(label="📝 Добавить заметку", command=lambda: self.add_widget("sticker"))
        widget_menu.add_separator()
        widget_menu.add_command(label="Показать / скрыть", command=self.toggle_widgets)
        widget_menu.add_command(label="Удалить все виджеты", command=self.remove_all_widgets)
        menu.add_cascade(label="🧩 Виджеты", menu=widget_menu)
        menu.add_separator()
        shortcut_menu = tk.Menu(menu, tearoff=0, bg="#1F1F1F", fg="white", activebackground="#0078D4")
        for label, icon, key in [
            ("Проводник", "📁", "explorer"), ("Настройки", "⚙", "settings"),
            ("Галерея", "🖼", "gallery"), ("Paint", "🎨", "paint"),
            ("Калькулятор", "🧮", "calc"), ("Заметки", "📝", "notes"),
            ("Терминал", "📡", "terminal"), ("Магазин", "🛒", "app_store"),
            ("Диспетчер задач", "📊", "task_manager"), ("Медиаплеер", "🎵", "media_player"),
        ]:
            shortcut_menu.add_command(label=f"{icon} {label}", command=lambda k=key, i=icon, n=label: self.add_desktop_shortcut(i, n, k))
        menu.add_cascade(label="➕ Добавить ярлык", menu=shortcut_menu)
        menu.add_separator()
        menu.add_command(label="🖥️ Параметры экрана", command=lambda: self.open_settings_section("Функции"))
        menu.add_command(label="🎨 Персонализация", command=lambda: self.open_settings_section("Темы"))
        menu.add_separator()
        menu.add_command(label="❖ Все приложения", command=self.taskbar.show_start)
        return menu

    def _ctx_create_folder(self):
        desktop_dir = self.bitos.user_paths["desktop"]
        os.makedirs(desktop_dir, exist_ok=True)
        base = "Новая папка"
        idx = 1
        path = os.path.join(desktop_dir, base)
        while os.path.exists(path):
            path = os.path.join(desktop_dir, f"{base} ({idx})")
            idx += 1
        os.makedirs(path, exist_ok=True)
        self.load_virtual_desktop_files()
        self._autosave_desktop_state()
        messagebox.showinfo("Проводник", f"Папка создана:\n{os.path.basename(path)}")

    def _ctx_create_document_dialog(self):
        """Создать документ с произвольным расширением, введённым пользователем."""
        dlg = tk.Toplevel(self.root)
        dlg.title("Создать документ")
        dlg.geometry("360x190")
        dlg.resizable(False, False)
        dlg.configure(bg="#1F1F1F")
        dlg.transient(self.root)
        dlg.grab_set()

        tk.Label(dlg, text="Введите расширение файла", font=("Segoe UI", 11),
                 bg="#1F1F1F", fg="white").pack(anchor="w", padx=18, pady=(18, 6))
        ext_var = tk.StringVar(value="txt")
        entry = tk.Entry(dlg, textvariable=ext_var, font=("Segoe UI", 11),
                        bg="#2D2D2D", fg="white", insertbackground="white", bd=0)
        entry.pack(fill=tk.X, padx=18, ipady=7)
        tk.Label(dlg, text="Можно указать любое расширение: txt, py, html, json…",
                 font=("Segoe UI", 8), bg="#1F1F1F", fg="#A0A0A0").pack(anchor="w", padx=18, pady=6)

        def create():
            extension = ext_var.get().strip().lstrip(".")
            # Расширение — только часть имени файла, запрещаем путь и спецсимволы Windows.
            if not extension or any(ch in extension for ch in '<>:"/\\|?*') or extension in (".", ".."):
                messagebox.showerror("Создание документа", "Введите корректное расширение файла.", parent=dlg)
                return
            self._ctx_create_file(extension)
            dlg.destroy()

        buttons = tk.Frame(dlg, bg="#1F1F1F")
        buttons.pack(fill=tk.X, padx=18, pady=(6, 12))
        tk.Button(buttons, text="Создать", bg="#0078D4", fg="white", bd=0,
                 command=create).pack(side=tk.RIGHT, padx=(6, 0), ipadx=12, ipady=4)
        tk.Button(buttons, text="Отмена", bg="#333333", fg="white", bd=0,
                 command=dlg.destroy).pack(side=tk.RIGHT, ipadx=12, ipady=4)
        entry.focus_set()
        entry.bind("<Return>", lambda _e: create())

    def _ctx_create_file(self, extension):
        extension = str(extension).strip().lstrip(".")
        if not extension or any(ch in extension for ch in '<>:"/\\|?*'):
            messagebox.showerror("Создание документа", "Некорректное расширение файла.", parent=self.root)
            return
        folder = self.bitos.user_paths["desktop"]
        os.makedirs(folder, exist_ok=True)
        filename = f"Новый документ.{extension}"
        path = os.path.join(folder, filename)
        counter = 1
        while os.path.exists(path):
            path = os.path.join(folder, f"Новый документ ({counter}).{extension}")
            counter += 1
        try:
            # Создаётся пустой файл с указанным расширением; содержимое не подменяется шаблоном.
            Path(path).touch(exist_ok=False)
            self.load_virtual_desktop_files()
            self._autosave_desktop_state()
            self.bitos.play_sound("success")
        except OSError as exc:
            messagebox.showerror("Создание документа", str(exc), parent=self.root)

    def show_context_menu(self, e):
        try:
            self.context_menu.tk_popup(e.x_root, e.y_root)
        finally:
            self.context_menu.grab_release()

    def _install_window_hover(self, window):
        """Attach small, non-blocking color transitions to clickable widgets."""
        def rgb(value):
            value = str(value)
            if len(value) == 7 and value.startswith("#"):
                try:
                    return tuple(int(value[i:i + 2], 16) for i in (1, 3, 5))
                except Exception:
                    pass
            return None

        def animate(widget, start, end, step=0, steps=4):
            try:
                if not widget.winfo_exists():
                    return
                a, b = rgb(start), rgb(end)
                if a is None or b is None:
                    widget.configure(bg=end)
                    return
                ratio = min(1.0, step / steps)
                color = "#" + "".join(f"{int(a[i] + (b[i] - a[i]) * ratio):02x}" for i in range(3))
                widget.configure(bg=color)
                if step < steps:
                    widget.after(15, lambda: animate(widget, start, end, step + 1, steps))
            except Exception:
                pass

        def visit(parent):
            try:
                children = parent.winfo_children()
            except Exception:
                return
            for widget in children:
                try:
                    if isinstance(widget, tk.Button) or (isinstance(widget, tk.Label) and str(widget.cget("cursor")) == "hand2"):
                        normal = str(widget.cget("bg"))
                        hover = "#168AE0" if normal.lower() == "#0078d4" else "#3A3A3A"
                        widget.bind("<Enter>", lambda _e, w=widget, n=normal, h=hover: animate(w, n, h), add="+")
                        widget.bind("<Leave>", lambda _e, w=widget, n=normal, h=hover: animate(w, h, n), add="+")
                    visit(widget)
                except Exception:
                    pass
        visit(window)


    def _animate_window_open(self, window):
        """Fade in an application window asynchronously."""
        try:
            window._bitos_closing = False
            window.attributes("-alpha", 0.0)
            def step(alpha=0.0):
                try:
                    if not window.winfo_exists() or getattr(window, "_bitos_closing", False):
                        return
                    alpha = min(1.0, alpha + 0.14)
                    window.attributes("-alpha", alpha)
                    if alpha < 1.0:
                        window.after(12, lambda: step(alpha))
                except tk.TclError:
                    return
            window.after(10, step)
        except Exception:
            pass

    def _animate_window_close(self, window):
        """Fade out then destroy the window; ignore repeated close requests."""
        try:
            if not window.winfo_exists() or getattr(window, "_bitos_closing", False):
                return
            window._bitos_closing = True
            try:
                alpha = float(window.attributes("-alpha"))
            except Exception:
                alpha = 1.0
            def step(value=alpha):
                try:
                    if not window.winfo_exists():
                        return
                    value = max(0.0, value - 0.16)
                    window.attributes("-alpha", value)
                    if value > 0:
                        window.after(12, lambda: step(value))
                    else:
                        window.destroy()
                except Exception:
                    try:
                        window.destroy()
                    except Exception:
                        pass
            window.after(0, step)
        except Exception:
            try:
                window.destroy()
            except Exception:
                pass

    def _animate_window_minimize(self, window):
        """Fade an app window out and withdraw it instead of destroying it."""
        try:
            if not window.winfo_exists() or getattr(window, "_bitos_closing", False):
                return
            window._bitos_minimizing = True
            try:
                alpha = float(window.attributes("-alpha"))
            except Exception:
                alpha = 1.0
            def step(value=alpha):
                try:
                    if not window.winfo_exists():
                        return
                    value = max(0.0, value - 0.16)
                    window.attributes("-alpha", value)
                    if value > 0:
                        window.after(12, lambda: step(value))
                    else:
                        window.withdraw()
                        window.attributes("-alpha", 1.0)
                        window._bitos_minimizing = False
                        self.taskbar.active_window_key = None
                except Exception:
                    try:
                        window.withdraw()
                    except Exception:
                        pass
            window.after(0, step)
        except Exception:
            try:
                window.iconify()
            except Exception:
                pass

    def _register_app_window(self, controller, title, icon):
        window = getattr(controller, "win", None)
        if window is not None:
            self.taskbar.register_window(window, title, icon)
        return controller

    def launch_bip_app(self, app_id):
        installer = BipInstaller(self.root, self.bitos)
        ok, result = installer.launch_app(app_id)
        if not ok:
            messagebox.showerror("Запуск приложения", result, parent=self.root)
        elif hasattr(self.bitos, "security"):
            info = installer.installed_apps.get(app_id, {})
            self.bitos.security.log_app_launch(info.get("name", app_id), self.username)
        return ok

    def open_explorer(self, path=None):
        return self._register_app_window(ModernFileExplorer(self.root, self.bitos, path), "Проводник", "📁")

    def open_settings(self):
        return self._register_app_window(SettingsWindow(self.root, self), "Настройки", "⚙")

    def open_settings_section(self, section_name):
        sw = SettingsWindow(self.root, self)
        sw.switch_section(section_name)
        return self._register_app_window(sw, "Настройки", "⚙")

    def open_trash(self):
        return self._register_app_window(TrashWindow(self.root, self.bitos), "Корзина", "🗑")

    def open_gallery(self):
        return self._register_app_window(Gallery(self.root, self.bitos), "Галерея", "🖼")

    def open_paint(self):
        return self._register_app_window(Paint(self.root, self.bitos), "Paint", "🎨")

    def open_bip_installer(self):
        return self._register_app_window(BipInstallWindow(self.root, self.bitos), "Установщик BIP", "📦")

    def open_dev_mode(self):
        return self._register_app_window(DevModeDialog(self.root, self.bitos), "Разработчик", "🔧")

    def open_calc(self):
        top = tk.Toplevel(self.root)
        self.taskbar.register_window(top, "Калькулятор", "🧮")
        top.title("Калькулятор BITOS")
        top.geometry("320x430")
        top.configure(bg="#1F1F1F")
        value = tk.StringVar()
        entry = tk.Entry(top, textvariable=value, font=("Segoe UI", 22), bg="#2D2D2D", fg="white",
                         bd=0, justify="right", insertbackground="white")
        entry.pack(fill=tk.X, padx=12, pady=12, ipady=10)
        grid = tk.Frame(top, bg="#1F1F1F")
        grid.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        buttons = ["7", "8", "9", "÷", "4", "5", "6", "×", "1", "2", "3", "−", "0", ".", "C", "+", "⌫", "(", ")", "="]
        def press(symbol):
            current = value.get()
            if symbol == "C":
                value.set("")
            elif symbol == "⌫":
                value.set(current[:-1])
            elif symbol == "=":
                try:
                    import ast, operator
                    ops = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
                           ast.Div: operator.truediv, ast.USub: operator.neg, ast.UAdd: operator.pos}
                    def evaluate(node):
                        if isinstance(node, ast.Expression): return evaluate(node.body)
                        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)): return node.value
                        if isinstance(node, ast.BinOp) and type(node.op) in ops: return ops[type(node.op)](evaluate(node.left), evaluate(node.right))
                        if isinstance(node, ast.UnaryOp) and type(node.op) in ops: return ops[type(node.op)](evaluate(node.operand))
                        raise ValueError("Недопустимое выражение")
                    expression = current.replace("×", "*").replace("÷", "/").replace("−", "-")
                    result = evaluate(ast.parse(expression, mode="eval"))
                    value.set(str(result))
                except Exception:
                    value.set("Ошибка")
            else:
                mapping = {"+":"+", "−":"−", "×":"×", "÷":"÷"}
                value.set(current + mapping.get(symbol, symbol))
        for i, symbol in enumerate(buttons):
            btn = tk.Button(grid, text=symbol, font=("Segoe UI", 14, "bold"), bg="#303030", fg="white",
                            activebackground="#0078D4", bd=0, command=lambda x=symbol: press(x))
            btn.grid(row=i//4, column=i%4, sticky="nsew", padx=3, pady=3)
        for r in range(5): grid.rowconfigure(r, weight=1)
        for c in range(4): grid.columnconfigure(c, weight=1)
        entry.bind("<Return>", lambda e: press("="))

    def open_notes(self):
        top = tk.Toplevel(self.root)
        self.taskbar.register_window(top, "Заметки", "📝")
        top.title("Заметки BITOS")
        top.geometry("560x420")
        top.configure(bg="#1F1F1F")
        bar = tk.Frame(top, bg="#1F1F1F")
        bar.pack(fill=tk.X, padx=8, pady=8)
        text = scrolledtext.ScrolledText(top, bg="#2B2B2B", fg="white", insertbackground="white",
                                         font=("Segoe UI", 10), bd=0, undo=True)
        text.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0,8))
        current = {"path": None}
        def new_note():
            text.delete("1.0", tk.END); current["path"] = None
        def open_note():
            path = bitos_askopenfilename(top, self.bitos, filetypes=[("Текст", "*.txt *.md *.py *.log"), ("Все файлы", "*.*")])
            if path:
                try:
                    content = Path(path).read_text(encoding="utf-8")
                    text.delete("1.0", tk.END); text.insert("1.0", content); current["path"] = path
                except Exception as exc: messagebox.showerror("Заметки", str(exc), parent=top)
        def save_note():
            path = current["path"] or bitos_asksaveasfilename(top, self.bitos, filetypes=[("Текст", "*.txt")])
            if path:
                try:
                    Path(path).write_text(text.get("1.0", "end-1c"), encoding="utf-8"); current["path"] = path
                except Exception as exc: messagebox.showerror("Заметки", str(exc), parent=top)
        for label, action in [("Новая", new_note), ("Открыть", open_note), ("Сохранить", save_note)]:
            tk.Button(bar, text=label, bg="#333333", fg="white", bd=0, padx=12, command=action).pack(side=tk.LEFT, padx=3)

    def open_terminal(self):
        """Строгий запуск внешнего BITOSterm.pyw"""
        term_path = os.path.join(self.bitos.system_paths["root"], "BITOSterm.pyw")
        if not os.path.isfile(term_path):
            term_path = os.path.join(self.bitos.base_path, "system", "BITOSterm.pyw")
        if not os.path.isfile(term_path):
            term_path = os.path.join(self.bitos.base_path, "System", "BITOSterm.pyw")
        if os.path.exists(term_path):
            subprocess.Popen([sys.executable, term_path])
        else:
            messagebox.showerror("Ошибка", f"Файл не найден:\n{term_path}")

    def open_app_store(self):
        top = tk.Toplevel(self.root)
        self.taskbar.register_window(top, "Магазин", "🛒")
        top.title("Магазин BITOS")
        top.geometry("600x400")
        top.configure(bg='#1F1F1F')
        tk.Label(top, text="Магазин приложений BITOS (Windows 10 1909)", font=('Segoe UI', 14),
                 bg='#1F1F1F', fg='white').pack(pady=40)

    def open_task_manager(self):
        window = TaskManagerWindow(self.root, self)
        self.taskbar.register_window(window.win, "Диспетчер задач", "📊")
        return window

    def open_media_player(self):
        window = MediaPlayerWindow(self.root, self)
        self.taskbar.register_window(window.win, "Медиаплеер", "🎵")
        return window

    def logout(self):
        self.save_widgets()
        self.root.destroy()
        from bitos.ui.windows import LoginScreen
        LoginScreen(self.bitos.after_login, self.bitos).run()

    def create_user_theme(self, **kwargs):
        name = str(kwargs.get("name", "Моя тема")).strip()
        if not name:
            return False
        theme = self.ui.get_colors("Базовая").copy()
        theme.update({"name": name, "bg": kwargs.get("bg_color", "#1E1E1E"),
                      "canvas_bg": kwargs.get("canvas_bg", kwargs.get("bg_color", "#1E1E1E")),
                      "accent": kwargs.get("fg_color", "#0078D4"),
                      "fg": kwargs.get("widget_fg", "#FFFFFF")})
        path = os.path.join(self.bitos.system_paths["config"], "user_themes.json")
        try:
            try: data = json.loads(Path(path).read_text(encoding="utf-8"))
            except Exception: data = {}
            data[name] = theme
            Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            self.THEMES[name] = theme
            return True
        except Exception as exc:
            messagebox.showerror("Темы", str(exc), parent=self.root)
            return False

    def get_all_themes(self):
        return dict(self.THEMES)

    def save_theme(self, name):
        path = os.path.join(self.bitos.system_paths["config"], "theme.cfg")
        try:
            Path(path).write_text(json.dumps({"theme": name}, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def change_theme(self, name):
        if name not in self.get_all_themes():
            return
        old = self.current_theme
        self.current_theme = name
        self.theme_colors = dict(self.THEMES.get(name, self.ui.get_colors(name)))
        self.canvas.config(bg=self.theme_colors['canvas_bg'])
        self.taskbar.update_theme(self.theme_colors)
        if hasattr(self, "wallpaper_manager"):
            self.wallpaper_manager.set_builtin(name)
        self.save_theme(name)
        for widget in self.widgets:
            try: widget.update_theme(self.theme_colors)
            except Exception: pass
        for icon in self.canvas.desktop_icons:
            icon.update_theme(self.theme_colors.get("icon_fg", "#FFFFFF"))
        if hasattr(self.bitos, "security"):
            self.bitos.security.log_theme_change(self.username, old, name)
        self.update_wallpaper()

    def _schedule_desktop_autosave(self):
        try:
            if self.root.winfo_exists():
                self._desktop_autosave_after_id = self.root.after(10000, self._desktop_autosave_tick)
        except Exception:
            self._desktop_autosave_after_id = None

    def _desktop_autosave_tick(self):
        self.save_desktop_shortcuts()
        self._schedule_desktop_autosave()

    def _autosave_desktop_state(self):
        self.save_desktop_shortcuts()

    def save_desktop_shortcuts(self):
        path = os.path.join(self.bitos.system_paths["config"], "desktop_shortcuts.json")
        try:
            data = [icon.to_dict() for icon in self.canvas.desktop_icons
                    if not getattr(icon, "is_virtual_item", False)]
            Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            layout_path = os.path.join(self.bitos.system_paths["config"], "desktop_layout.json")
            layout = []
            for icon in self.canvas.desktop_icons:
                item = {"grid_x": icon.grid_x, "grid_y": icon.grid_y}
                virtual_path = getattr(icon, "virtual_path", None)
                if virtual_path:
                    item["virtual_path"] = os.path.abspath(virtual_path)
                else:
                    item["icon_id"] = icon.icon_id
                    item["text"] = icon.text
                layout.append(item)
            Path(layout_path).write_text(json.dumps(layout, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            if self.ui.logs_enabled: self.bitos.error_manager._log_warning("Desktop.shortcuts", str(exc))

    def add_desktop_shortcut(self, icon, name, command_key):
        if command_key not in self.commands and not str(command_key).startswith("bip:"):
            return
        if any(x.text == name for x in self.canvas.desktop_icons):
            return
        sizes = self.ui.get_sizes()
        used = {(x.grid_x, x.grid_y) for x in self.canvas.desktop_icons}
        grid_x, grid_y = 0, 0
        for grid_y in range(40):
            for grid_x in range(20):
                if (grid_x, grid_y) not in used:
                    break
            else:
                continue
            break
        command = self.commands.get(command_key)
        if command is None and str(command_key).startswith("bip:"):
            app_id = str(command_key).split(":", 1)[1]
            command = lambda aid=app_id: self.launch_bip_app(aid)
        new_icon = DesktopIcon(self.canvas, grid_x, grid_y, icon, name, command,
                               size=sizes["icon_size"], step=sizes["grid_step"],
                               font_size=sizes["icon_font_size"], command_key=command_key)
        self.canvas.desktop_icons.append(new_icon)
        self._autosave_desktop_state()
        self.bitos.play_sound("success")

    def add_widget(self, widget_type):
        if not self.ui.widgets_enabled:
            messagebox.showinfo("Виджеты отключены",
                                "Виджеты отключены текущим уровнем оптимизации. Установите 0–50%, чтобы добавлять их.",
                                parent=self.root)
            return
        sizes = self.ui.get_sizes()
        x = 260 + (len(self.widgets) % 3) * 220
        y = 30 + (len(self.widgets) // 3) * 180
        if widget_type == "clock":
            widget = ClockWidget(self.canvas, self.theme_colors, x, y)
        elif widget_type == "calendar":
            widget = CalendarWidget(self.canvas, self.theme_colors, x, y)
        elif widget_type == "sticker":
            widget = StickerWidget(self.canvas, self.theme_colors, x, y, "")
        else:
            return
        self.widgets.append(widget)
        if not self.ui.widgets_enabled:
            self.canvas.itemconfigure(widget.win_id, state=tk.HIDDEN)
        self.save_widgets()
        self.bitos.play_sound("success")

    def toggle_widgets(self):
        self.widgets_visible = not self.widgets_visible
        state = tk.NORMAL if self.widgets_visible and self.ui.widgets_enabled else tk.HIDDEN
        for widget in self.widgets:
            try: self.canvas.itemconfigure(widget.win_id, state=state)
            except Exception: pass

    def remove_all_widgets(self):
        for widget in list(self.widgets):
            try: widget.destroy()
            except Exception: pass
        self.widgets.clear()
        self.save_widgets()

    def open_wallpaper_settings(self):
        win = tk.Toplevel(self.root)
        win.title("Обои рабочего стола")
        win.geometry("460x300")
        win.configure(bg="#1F1F1F")
        tk.Label(win, text="Персонализация рабочего стола", bg="#1F1F1F", fg="white",
                 font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=18, pady=(16,10))
        tk.Label(win, text=f"Текущие обои: {os.path.basename(self.wallpaper_manager.get_wallpaper() or 'сплошной цвет')}",
                 bg="#1F1F1F", fg="#BDBDBD").pack(anchor="w", padx=18, pady=4)
        style_var = tk.StringVar(value=self.wallpaper_manager.wallpaper_style)
        row = tk.Frame(win, bg="#1F1F1F"); row.pack(fill=tk.X, padx=18, pady=8)
        tk.Label(row, text="Расположение:", bg="#1F1F1F", fg="white").pack(side=tk.LEFT)
        combo = ttk.Combobox(row, textvariable=style_var, state="readonly", values=["fill", "fit", "stretch", "tile", "center"], width=14)
        combo.pack(side=tk.RIGHT)
        def choose():
            path = bitos_askopenfilename(win, self.bitos, filetypes=[("Изображения", "*.png *.jpg *.jpeg *.webp *.bmp"), ("Все файлы", "*.*")])
            if not path: return
            ok, result = self.wallpaper_manager.set_wallpaper(path, style_var.get())
            if ok:
                self.update_wallpaper(); win.destroy()
            else: messagebox.showerror("Обои", result, parent=win)
        def choose_builtin():
            ok, result = self.wallpaper_manager.set_builtin(self.current_theme)
            if ok: self.update_wallpaper(); win.destroy()
            else: messagebox.showerror("Обои", result, parent=win)
        def remove():
            self.wallpaper_manager.remove_wallpaper(); self.update_wallpaper(); win.destroy()
        for label, action in [("Выбрать изображение…", choose), ("Встроенные обои темы", choose_builtin), ("Сплошной цвет", remove)]:
            tk.Button(win, text=label, bg="#303030", fg="white", bd=0, padx=12, pady=7,
                      command=action).pack(fill=tk.X, padx=18, pady=4)
        tk.Label(win, text="Поддерживаются PNG, JPG, WEBP и BMP. Обои копируются в папку BITOS, поэтому не теряются при переносе системы.",
                 bg="#1F1F1F", fg="#909090", wraplength=410, justify="left").pack(anchor="w", padx=18, pady=8)


# ============================================================================
# 6. ПРОВОДНИК (MODERN FILE EXPLORER: КОПИРОВАНИЕ, ВСТАВКА, УДАЛЕНИЕ)
# ============================================================================

class ModernFileExplorer:
    """Полнофункциональный проводник Windows 10 с тулбаром и контекстным меню"""
    def __init__(self, parent, bitos, start_path=None):
        self.parent = parent
        self.bitos = bitos
        self.current_path = start_path or bitos.user_paths["home"]
        self.trash_manager = TrashManager(bitos)
        self.clipboard = None
        self.clipboard_action = None
        self.history = [self.current_path]
        self.history_index = 0
        self._load_request = 0
        self._active_search = False
        self._search_after_id = None
        
        self.win = tk.Toplevel(parent)
        self.win.title("Проводник")
        self.win.geometry("900x560")
        self.win.configure(bg='#1F1F1F')
        
        toolbar = tk.Frame(self.win, bg='#1F1F1F', height=36)
        toolbar.pack(fill=tk.X, padx=8, pady=(4, 2))
        self.tabs = [self.current_path]
        self.active_tab = 0
        self.tabs_frame = tk.Frame(self.win, bg="#181818")
        self.tabs_frame.pack(fill=tk.X, padx=8, pady=(0, 4))
        self._render_tabs()
        
        for icon, cmd in [("←", self.go_back), ("→", self.go_forward), ("↑", self.go_up), ("↻", self.refresh)]:
            btn = tk.Button(toolbar, text=icon, font=('Segoe UI', 10), bg='#1F1F1F', fg='white',
                            bd=0, padx=8, relief=tk.FLAT, command=cmd)
            btn.pack(side=tk.LEFT, padx=1)
            
        self.addr = tk.Entry(toolbar, font=('Segoe UI', 9), bg='#2D2D2D', fg='white', bd=0)
        self.addr.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6, ipady=3)
        self.addr.insert(0, self.current_path)
        self.addr.bind('<Return>', lambda e: self.navigate_to(self.addr.get()))
        
        actions = tk.Frame(self.win, bg='#1F1F1F')
        actions.pack(fill=tk.X, padx=8, pady=(0, 4))
        
        tk.Button(actions, text="📁 Новая папка", font=('Segoe UI', 8), bg='#2D2D2D', fg='white',
                  bd=0, padx=8, pady=2, command=self.new_folder).pack(side=tk.LEFT, padx=2)
        tk.Button(actions, text="📋 Копировать", font=('Segoe UI', 8), bg='#2D2D2D', fg='white',
                  bd=0, padx=8, pady=2, command=self.copy_item).pack(side=tk.LEFT, padx=2)
        tk.Button(actions, text="✂ Вырезать", font=('Segoe UI', 8), bg='#2D2D2D', fg='white',
                  bd=0, padx=8, pady=2, command=self.cut_item).pack(side=tk.LEFT, padx=2)
        tk.Button(actions, text="📌 Вставить", font=('Segoe UI', 8), bg='#2D2D2D', fg='white',
                  bd=0, padx=8, pady=2, command=self.paste_item).pack(side=tk.LEFT, padx=2)
        tk.Button(actions, text="✏ Переименовать", font=('Segoe UI', 8), bg='#2D2D2D', fg='white',
                  bd=0, padx=8, pady=2, command=self.rename_item).pack(side=tk.LEFT, padx=2)
        tk.Button(actions, text="🗑 В корзину", font=('Segoe UI', 8), bg='#A80000', fg='white',
                  bd=0, padx=8, pady=2, command=self.delete_to_trash).pack(side=tk.LEFT, padx=2)

        search_bar = tk.Frame(self.win, bg='#1F1F1F')
        search_bar.pack(fill=tk.X, padx=8, pady=(0, 5))
        tk.Label(search_bar, text='Поиск:', bg='#1F1F1F', fg='#CFCFCF', font=('Segoe UI', 8)).pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_bar, textvariable=self.search_var, font=('Segoe UI', 9),
                                     bg='#2D2D2D', fg='white', insertbackground='white', bd=0)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        self.search_subdirs = tk.BooleanVar(value=True)
        self.search_content = tk.BooleanVar(value=False)
        tk.Checkbutton(search_bar, text='Во вложенных', variable=self.search_subdirs,
                       bg='#1F1F1F', fg='#CFCFCF', selectcolor='#2D2D2D', activebackground='#1F1F1F',
                       activeforeground='white', font=('Segoe UI', 8)).pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(search_bar, text='По содержимому', variable=self.search_content,
                       bg='#1F1F1F', fg='#CFCFCF', selectcolor='#2D2D2D', activebackground='#1F1F1F',
                       activeforeground='white', font=('Segoe UI', 8)).pack(side=tk.LEFT, padx=5)
        tk.Button(search_bar, text='Найти', bg='#0078D4', fg='white', bd=0, padx=10,
                  command=self.start_search).pack(side=tk.LEFT, padx=3)
        tk.Button(search_bar, text='✕', bg='#333333', fg='white', bd=0, padx=8,
                  command=self.clear_search).pack(side=tk.LEFT)
        self.search_entry.bind('<Return>', lambda e: self.start_search())

        body = tk.Frame(self.win, bg='#1F1F1F')
        body.pack(fill=tk.BOTH, expand=True)
        
        nav = tk.Frame(body, bg='#141414', width=160)
        nav.pack(side=tk.LEFT, fill=tk.Y)
        nav.pack_propagate(False)
        
        quick = [("Домой", bitos.user_paths["home"]),
                 ("Документы", bitos.documents_path),
                 ("Загрузки", bitos.downloads_path),
                 ("Рабочий стол", bitos.user_paths["desktop"]),
                 ("Корзина", os.path.join(bitos.system_paths["temp"], "Trash"))]
        for name, p in quick:
            b = tk.Button(nav, text=f"  {name}", font=('Segoe UI', 9), bg='#141414', fg='#E0E0E0',
                          bd=0, anchor='w', relief=tk.FLAT, command=lambda pt=p: self.navigate_to(pt))
            b.pack(fill=tk.X, pady=2)
            
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Win10.Treeview", background="#1F1F1F", foreground="#FFFFFF",
                        fieldbackground="#1F1F1F", rowheight=24, borderwidth=0, font=('Segoe UI', 9))
        style.map("Win10.Treeview", background=[('selected', '#0078D4')], foreground=[('selected', '#FFFFFF')])
        
        tree_container = tk.Frame(body, bg="#1F1F1F")
        tree_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree = ttk.Treeview(tree_container, columns=('Name', 'Date', 'Type', 'Size'), show='headings',
                                 style="Win10.Treeview")
        self.sort_column = "Name"
        self.sort_reverse = False
        self.tree.heading('Name', text='Имя', command=lambda: self._sort_by("Name"))
        self.tree.heading('Date', text='Дата изменения', command=lambda: self._sort_by("Date"))
        self.tree.heading('Type', text='Тип', command=lambda: self._sort_by("Type"))
        self.tree.heading('Size', text='Размер', command=lambda: self._sort_by("Size"))
        
        self.tree.column('Name', width=420, minwidth=180, stretch=True)
        self.tree.column('Date', width=150, minwidth=100, stretch=False)
        self.tree.column('Type', width=90, minwidth=60, stretch=False)
        self.tree.column('Size', width=90, minwidth=60, stretch=False)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_vscroll = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.tree.yview)
        tree_vscroll.pack(side=tk.RIGHT, fill=tk.Y)
        tree_hscroll = ttk.Scrollbar(self.win, orient=tk.HORIZONTAL, command=self.tree.xview)
        tree_hscroll.pack(side=tk.BOTTOM, fill=tk.X, padx=8)
        self.tree.configure(yscrollcommand=tree_vscroll.set, xscrollcommand=tree_hscroll.set)
        self.tree.bind('<MouseWheel>', lambda event: self.tree.yview_scroll(int(-1 * (event.delta / 120)), 'units'))
        
        self.tree.bind('<Double-1>', self.on_double_click)
        self.tree.bind('<Button-3>', self.show_context_menu)
        
        self.ctx_menu = tk.Menu(self.win, tearoff=0, bg='#1F1F1F', fg='white', activebackground='#0078D4')
        self.ctx_menu.add_command(label="Открыть", command=self._open_selected)
        self.ctx_menu.add_command(label="Копировать", command=self.copy_item)
        self.ctx_menu.add_command(label="Вырезать", command=self.cut_item)
        self.ctx_menu.add_command(label="Вставить", command=self.paste_item)
        self.ctx_menu.add_separator()
        self.ctx_menu.add_command(label="Переименовать", command=self.rename_item)
        self.ctx_menu.add_command(label="Свойства", command=self.show_properties)
        self.ctx_menu.add_command(label="Удалить в корзину", command=self.delete_to_trash)
        
        self.load_dir()

    def _render_tabs(self):
        for child in self.tabs_frame.winfo_children():
            child.destroy()
        for index, path in enumerate(self.tabs):
            title = os.path.basename(os.path.normpath(path)) or path
            if len(title) > 18:
                title = title[:17] + "…"
            bg = "#0078D4" if index == self.active_tab else "#2A2A2A"
            tab = tk.Frame(self.tabs_frame, bg=bg)
            tab.pack(side=tk.LEFT, padx=(0, 3))
            tk.Button(tab, text=title, bg=bg, fg="white", bd=0, padx=8,
                     command=lambda i=index: self._switch_tab(i)).pack(side=tk.LEFT)
            if len(self.tabs) > 1:
                tk.Button(tab, text="×", bg=bg, fg="#D0D0D0", bd=0, padx=4,
                         command=lambda i=index: self._close_tab(i)).pack(side=tk.LEFT)
        tk.Button(self.tabs_frame, text="＋", bg="#303030", fg="white", bd=0, padx=8,
                 command=self._new_tab).pack(side=tk.LEFT, padx=2)

    def _new_tab(self):
        self.tabs.append(self.current_path)
        self.active_tab = len(self.tabs) - 1
        self._render_tabs()
        self.load_dir()

    def _switch_tab(self, index):
        if not 0 <= index < len(self.tabs):
            return
        self.active_tab = index
        self.current_path = self.tabs[index]
        self.addr.delete(0, tk.END)
        self.addr.insert(0, self.current_path)
        self._render_tabs()
        self.load_dir()

    def _close_tab(self, index):
        if len(self.tabs) <= 1 or not 0 <= index < len(self.tabs):
            return
        self.tabs.pop(index)
        if self.active_tab >= index:
            self.active_tab = max(0, self.active_tab - 1)
        self.current_path = self.tabs[self.active_tab]
        self.addr.delete(0, tk.END)
        self.addr.insert(0, self.current_path)
        self._render_tabs()
        self.load_dir()

    def show_context_menu(self, e):
        item = self.tree.identify_row(e.y)
        if item:
            self.tree.selection_set(item)
        try:
            self.ctx_menu.tk_popup(e.x_root, e.y_root)
        finally:
            self.ctx_menu.grab_release()

    def load_dir(self):
        """List the current directory asynchronously; Tk is only touched in callbacks."""
        self._load_request += 1
        request_id = self._load_request
        path = self.current_path
        query = self.search_var.get().strip().casefold() if hasattr(self, 'search_var') else ''
        recursive = bool(self.search_subdirs.get()) if query else False
        content_search = bool(self.search_content.get()) if query else False
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.tree.insert("", tk.END, values=("Поиск…" if query else "Загрузка…", "", "", ""))

        def scan():
            rows = []
            visited = 0
            def inspect_file(entry):
                nonlocal visited
                try:
                    is_dir = entry.is_dir(follow_symlinks=False)
                    stat = entry.stat(follow_symlinks=False)
                    name_match = query in entry.name.casefold() if query else True
                    content_match = False
                    if query and content_search and not is_dir and stat.st_size <= 262_144 and visited < 400:
                        try:
                            with open(entry.path, 'r', encoding='utf-8', errors='ignore') as f:
                                content_match = query in f.read(262_144).casefold()
                        except (OSError, UnicodeError):
                            pass
                    if not query or name_match or content_match:
                        type_name = "Папка" if is_dir else "Файл"
                        size = "" if is_dir else f"{stat.st_size // 1024} КБ"
                        mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M")
                        rows.append((is_dir, entry.name.lower(), ("📁 " if is_dir else "📄 ") + entry.name,
                                     mtime, type_name, size, entry.path))
                    visited += 1
                except (PermissionError, FileNotFoundError, OSError):
                    pass
            try:
                if query and recursive:
                    for root, dirs, files in os.walk(path, topdown=True, onerror=lambda _e: None):
                        dirs[:] = [d for d in dirs if not d.startswith(('$', '.'))]
                        try:
                            with os.scandir(root) as it:
                                for entry in it:
                                    if visited >= 5000:
                                        break
                                    inspect_file(entry)
                        except OSError:
                            continue
                        if visited >= 5000:
                            break
                else:
                    with os.scandir(path) as it:
                        for entry in it:
                            inspect_file(entry)
            except OSError as exc:
                raise RuntimeError(str(exc))
            rows.sort(key=lambda row: (not row[0], row[1]))
            return rows, visited

        def apply_rows(result):
            rows, scanned = result
            try:
                if not self.win.winfo_exists() or request_id != self._load_request:
                    return
                for item in self.tree.get_children():
                    self.tree.delete(item)
                for is_dir, _, name, mtime, type_name, size, full_path in rows:
                    self.tree.insert("", tk.END, values=(name, mtime, type_name, size), tags=(full_path,))
                if not rows:
                    label = "Совпадений нет" if query else "Папка пуста"
                    self.tree.insert("", tk.END, values=(label, "", "", ""))
                self.win.title(f"Проводник — {len(rows)} результатов" if query else f"Проводник — {path}")
            except Exception:
                pass

        def failed(exc):
            try:
                if self.win.winfo_exists() and request_id == self._load_request:
                    for item in self.tree.get_children(): self.tree.delete(item)
                    self.tree.insert("", tk.END, values=(f"Ошибка: {exc}", "", "", ""))
            except Exception:
                pass

        tasks = getattr(self.bitos, "task_manager", None)
        future = tasks.submit(scan, on_success=apply_rows, on_error=failed) if tasks else None
        if future is None:
            try: apply_rows(scan())
            except Exception as exc: failed(exc)

    def _sort_by(self, column):
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False
        items = []
        for iid in self.tree.get_children():
            values = self.tree.item(iid, "values")
            tags = self.tree.item(iid, "tags")
            if not values or not tags:
                continue
            path = tags[0]
            try:
                is_dir = os.path.isdir(path)
                if column == "Name":
                    key = os.path.basename(path).casefold()
                elif column == "Date":
                    key = os.path.getmtime(path)
                elif column == "Type":
                    key = "Папка" if is_dir else os.path.splitext(path)[1].casefold()
                else:
                    key = os.path.getsize(path) if os.path.isfile(path) else -1
                items.append((not is_dir, key, iid))
            except OSError:
                items.append((True, str(values[0]).casefold(), iid))
        items.sort(key=lambda item: item[1], reverse=self.sort_reverse)
        items.sort(key=lambda item: item[0])  # keep folders before files for either sort direction
        for index, (_, _, iid) in enumerate(items):
            self.tree.move(iid, "", index)

    def start_search(self):
        self._active_search = bool(self.search_var.get().strip())
        self.load_dir()

    def clear_search(self):
        self.search_var.set('')
        self._active_search = False
        self.load_dir()

    def show_shortcut_menu(self, e):
        owner = getattr(self.canvas, "desktop_owner", None)
        if owner is None or self.text in ("Этот ПК", "Корзина"):
            return
        menu = tk.Menu(self.canvas, tearoff=0, bg="#1F1F1F", fg="white", activebackground="#0078D4")
        menu.add_command(label="Информация о приложении", command=lambda: owner.show_shortcut_info(self))
        menu.add_command(label="Удалить с рабочего стола", command=lambda: owner.remove_desktop_shortcut(self))
        menu.add_command(label="Удалить приложение (BIP)", command=lambda: owner.remove_bip_shortcut(self))
        try:
            menu.tk_popup(e.x_root, e.y_root)
        finally:
            menu.grab_release()

    def on_double_click(self, e):
        self._open_selected()

    def _open_selected(self):
        sel = self.tree.selection()
        if not sel: return
        tags = self.tree.item(sel[0], 'tags')
        if not tags:
            return
        fp = tags[0]
        if os.path.isdir(fp):
            self.navigate_to(fp)
        else:
            try:
                if platform.system() == "Windows":
                    os.startfile(fp)
                else:
                    subprocess.Popen(['xdg-open', fp])
            except Exception:
                pass

    def new_folder(self):
        dlg = tk.Toplevel(self.win)
        dlg.title("Создание папки")
        dlg.geometry("320x110")
        dlg.configure(bg='#1F1F1F')
        tk.Label(dlg, text="Имя новой папки:", bg='#1F1F1F', fg='white', font=('Segoe UI', 9)).pack(pady=4)
        e = tk.Entry(dlg, bg='#2D2D2D', fg='white', bd=0)
        e.pack(padx=10, pady=4, fill=tk.X, ipady=3)
        e.insert(0, "Новая папка")
        def create():
            name = e.get().strip()
            if name:
                os.makedirs(os.path.join(self.current_path, name), exist_ok=True)
                dlg.destroy()
                self.load_dir()
        tk.Button(dlg, text="Создать", bg='#0078D4', fg='white', bd=0, command=create).pack(pady=4)

    def copy_item(self):
        sel = self.tree.selection()
        if sel:
            self.clipboard = self.tree.item(sel[0], 'tags')[0]
            self.clipboard_action = 'copy'

    def cut_item(self):
        sel = self.tree.selection()
        if sel:
            self.clipboard = self.tree.item(sel[0], 'tags')[0]
            self.clipboard_action = 'cut'

    def paste_item(self):
        if not self.clipboard or not os.path.exists(self.clipboard):
            return
        source = self.clipboard
        action = self.clipboard_action
        dst = os.path.join(self.current_path, os.path.basename(source))
        if os.path.abspath(dst) == os.path.abspath(source):
            return
        if os.path.exists(dst):
            base, ext = os.path.splitext(dst)
            i = 1
            while os.path.exists(f"{base} ({i}){ext}"):
                i += 1
            dst = f"{base} ({i}){ext}"
        self.win.title('Проводник — выполнение операции…')
        def operation():
            if action == 'copy':
                if os.path.isdir(source): shutil.copytree(source, dst)
                else: shutil.copy2(source, dst)
            elif action == 'cut':
                shutil.move(source, dst)
            return dst
        def completed(result):
            if action == 'cut': self.clipboard = None
            self.win.title('Проводник')
            self.load_dir()
        def failed(exc):
            self.win.title('Проводник')
            messagebox.showerror("Ошибка операции", str(exc), parent=self.win)
        tasks = getattr(self.bitos, 'task_manager', None)
        future = tasks.submit(operation, on_success=completed, on_error=failed) if tasks else None
        if future is None:
            try: completed(operation())
            except Exception as exc: failed(exc)

    def delete_to_trash(self):
        sel = self.tree.selection()
        if not sel: return
        tags = self.tree.item(sel[0], 'tags')
        if not tags: return
        fp = tags[0]
        if not messagebox.askyesno('Корзина', f'Переместить в корзину?\n{os.path.basename(fp)}', parent=self.win):
            return
        self.win.title('Проводник — перемещение в корзину…')
        def operation():
            return self.trash_manager.move_to_trash([fp])
        def completed(_result):
            self.win.title('Проводник')
            self.load_dir()
        def failed(exc):
            self.win.title('Проводник')
            messagebox.showerror('Корзина', str(exc), parent=self.win)
        tasks = getattr(self.bitos, 'task_manager', None)
        future = tasks.submit(operation, on_success=completed, on_error=failed) if tasks else None
        if future is None:
            try: completed(operation())
            except Exception as exc: failed(exc)

    def navigate_to(self, path, add_history=True):
        if os.path.exists(path) and os.path.isdir(path):
            self.current_path = os.path.abspath(path)
            if hasattr(self, "tabs") and self.tabs:
                self.tabs[self.active_tab] = self.current_path
                self._render_tabs()
            self.addr.delete(0, tk.END)
            self.addr.insert(0, self.current_path)
            if add_history:
                self.history = self.history[:self.history_index + 1]
                if not self.history or self.history[-1] != self.current_path:
                    self.history.append(self.current_path)
                self.history_index = len(self.history) - 1
            self.load_dir()

    def go_back(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.navigate_to(self.history[self.history_index], add_history=False)

    def go_forward(self):
        if self.history_index + 1 < len(self.history):
            self.history_index += 1
            self.navigate_to(self.history[self.history_index], add_history=False)

    def rename_item(self):
        sel = self.tree.selection()
        if not sel: return
        source = self.tree.item(sel[0], "tags")[0]
        dlg = tk.Toplevel(self.win); dlg.title("Переименование"); dlg.geometry("340x120"); dlg.configure(bg="#1F1F1F")
        entry = tk.Entry(dlg, bg="#2D2D2D", fg="white", bd=0); entry.pack(fill=tk.X, padx=12, pady=14, ipady=5)
        entry.insert(0, os.path.basename(source)); entry.select_range(0, tk.END)
        def apply():
            name = entry.get().strip()
            if not name: return
            target = os.path.join(os.path.dirname(source), name)
            try:
                os.rename(source, target); dlg.destroy(); self.load_dir()
            except Exception as exc: messagebox.showerror("Переименование", str(exc), parent=dlg)
        tk.Button(dlg, text="Переименовать", bg="#0078D4", fg="white", bd=0, command=apply).pack(pady=4)
        entry.bind("<Return>", lambda e: apply())

    def show_properties(self):
        sel = self.tree.selection()
        if not sel: return
        path = self.tree.item(sel[0], "tags")[0]
        try:
            stat = os.stat(path)
            info = [f"Имя: {os.path.basename(path)}", f"Путь: {path}",
                    f"Тип: {'Папка' if os.path.isdir(path) else 'Файл'}",
                    f"Размер: {stat.st_size:,} байт", f"Изменён: {datetime.fromtimestamp(stat.st_mtime)}"]
            messagebox.showinfo("Свойства", "\n".join(info), parent=self.win)
        except Exception as exc: messagebox.showerror("Свойства", str(exc), parent=self.win)

    def go_up(self):
        self.navigate_to(os.path.dirname(self.current_path))
    def refresh(self):
        self.load_dir()


# ============================================================================
# 7. ГАЛЕРЕЯ И PAINT (ПОЛНЫЙ ФУНКЦИОНАЛ)
# ============================================================================

class Gallery:
    """Галерея изображений с асинхронным сканированием и просмотром."""
    EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')

    def __init__(self, parent, bitos):
        self.win = tk.Toplevel(parent)
        self.win.title("Галерея изображений")
        self.win.geometry("820x560")
        self.win.configure(bg='#1F1F1F')
        self.bitos = bitos
        self.images_keep = []
        self.selected_path = None
        self._load_request = 0
        self.trash = TrashManager(bitos)

        top = tk.Frame(self.win, bg='#1F1F1F')
        top.pack(fill=tk.X, padx=12, pady=8)
        tk.Label(top, text="Изображения", font=('Segoe UI', 12, 'bold'), bg='#1F1F1F', fg='white').pack(side=tk.LEFT)
        tk.Button(top, text='↻ Обновить', bg='#303030', fg='white', bd=0, padx=10,
                  command=self.load_images).pack(side=tk.RIGHT, padx=3)
        tk.Button(top, text='🗑 В корзину', bg='#7A2020', fg='white', bd=0, padx=10,
                  command=self.delete_selected).pack(side=tk.RIGHT, padx=3)
        tk.Button(top, text='Открыть', bg='#0078D4', fg='white', bd=0, padx=10,
                  command=self.open_selected).pack(side=tk.RIGHT, padx=3)
        self.status = tk.Label(self.win, text='', bg='#1F1F1F', fg='#A0A0A0', anchor='w', font=('Segoe UI', 8))
        self.status.pack(fill=tk.X, padx=12)
        self.canvas = tk.Canvas(self.win, bg='#1F1F1F', highlightthickness=0)
        self.scroll = ttk.Scrollbar(self.win, orient=tk.VERTICAL, command=self.canvas.yview)
        self.grid_frame = tk.Frame(self.canvas, bg='#1F1F1F')
        self.grid_window = self.canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")
        self.grid_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfigure(self.grid_window, width=e.width))
        self.canvas.configure(yscrollcommand=self.scroll.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0), pady=4)
        self.scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 8), pady=4)
        self.load_images()

    def load_images(self):
        self._load_request += 1
        request_id = self._load_request
        folder = self.bitos.pictures_path
        self.status.config(text='Загрузка изображений…')
        def scan():
            found = []
            if not os.path.isdir(folder):
                return found
            try:
                with os.scandir(folder) as entries:
                    for entry in entries:
                        if entry.is_file() and entry.name.lower().endswith(self.EXTENSIONS):
                            try:
                                st = entry.stat()
                                found.append((entry.path, st.st_mtime, st.st_size))
                            except OSError:
                                pass
            except OSError:
                pass
            found.sort(key=lambda x: x[1], reverse=True)
            return found
        def render(files):
            if not self.win.winfo_exists() or request_id != self._load_request:
                return
            for child in self.grid_frame.winfo_children(): child.destroy()
            self.images_keep.clear()
            self.items = [item[0] for item in files]
            self.status.config(text=f'Найдено изображений: {len(files)}')
            if not files:
                tk.Label(self.grid_frame, text='В папке изображений пока нет', bg='#1F1F1F', fg='#A0A0A0').grid(row=0, column=0, padx=20, pady=30)
                return
            # Decode/resize in workers; only PhotoImage construction happens on Tk thread.
            def make_thumbs():
                thumbs = []
                if not PIL_AVAILABLE:
                    return [(path, None) for path, *_ in files]
                for path, *_ in files:
                    try:
                        with Image.open(path) as im:
                            im.thumbnail((138, 112))
                            thumbs.append((path, im.copy()))
                    except Exception:
                        thumbs.append((path, None))
                return thumbs
            def show_thumbs(thumbs):
                if not self.win.winfo_exists() or request_id != self._load_request:
                    return
                for i, (path, img) in enumerate(thumbs):
                    box = tk.Frame(self.grid_frame, bg='#252525', width=150, height=160, highlightthickness=1, highlightbackground='#3A3A3A')
                    box.grid(row=i//5, column=i%5, padx=5, pady=5, sticky='n')
                    box.pack_propagate(False)
                    if img is not None:
                        photo = ImageTk.PhotoImage(img)
                        self.images_keep.append(photo)
                        pic = tk.Label(box, image=photo, bg='#252525', cursor='hand2')
                    else:
                        pic = tk.Label(box, text='🖼', font=('Segoe UI', 36), bg='#252525', fg='white', cursor='hand2')
                    pic.pack(expand=True, pady=3)
                    name = os.path.basename(path)
                    lbl = tk.Label(box, text=name[:18] + ('…' if len(name) > 18 else ''), font=('Segoe UI', 8), bg='#252525', fg='#E0E0E0')
                    lbl.pack(side=tk.BOTTOM, pady=4)
                    for widget in (box, pic, lbl):
                        widget.bind('<Button-1>', lambda e, fp=path, w=box: self.select(fp, w))
                        widget.bind('<Double-1>', lambda e, fp=path: self.view_full(fp))
            tasks = getattr(self.bitos, 'task_manager', None)
            fut = tasks.submit(make_thumbs, on_success=show_thumbs) if tasks and PIL_AVAILABLE else None
            if fut is None:
                show_thumbs(make_thumbs())
        tasks = getattr(self.bitos, 'task_manager', None)
        future = tasks.submit(scan, on_success=render) if tasks else None
        if future is None:
            render(scan())

    def select(self, path, box=None):
        self.selected_path = path
        for child in self.grid_frame.winfo_children():
            try: child.configure(highlightbackground='#3A3A3A')
            except Exception: pass
        if box:
            box.configure(highlightbackground='#0078D4')
        self.status.config(text=os.path.basename(path))

    def open_selected(self):
        if self.selected_path and os.path.isfile(self.selected_path):
            self.view_full(self.selected_path)

    def delete_selected(self):
        path = self.selected_path
        if not path or not os.path.exists(path):
            messagebox.showinfo('Галерея', 'Сначала выберите изображение.', parent=self.win)
            return
        if not messagebox.askyesno('Галерея', f'Переместить в корзину?\n{os.path.basename(path)}', parent=self.win):
            return
        self.trash.move_to_trash([path])
        self.selected_path = None
        self.load_images()

    def view_full(self, path):
        if not os.path.isfile(path): return
        top = tk.Toplevel(self.win)
        top.title(os.path.basename(path))
        top.geometry("760x560")
        top.configure(bg="#0F0F0F")
        if not PIL_AVAILABLE:
            tk.Label(top, text='Для просмотра изображений установите Pillow (pip install Pillow)', bg='#0F0F0F', fg='white').pack(expand=True)
            return
        try:
            img = Image.open(path)
            img.thumbnail((730, 510))
            photo = ImageTk.PhotoImage(img)
            l = tk.Label(top, image=photo, bg='#0F0F0F')
            l.image = photo
            l.pack(expand=True)
        except Exception as exc:
            top.destroy()
            messagebox.showerror('Галерея', str(exc), parent=self.win)


class Paint:
    """Рисование с размером кисти, ластиком, палитрой и сохранением PNG."""
    def __init__(self, parent, bitos):
        self.bitos = bitos
        self.win = tk.Toplevel(parent)
        self.win.title("Paint")
        self.win.geometry("820x600")
        self.win.configure(bg='#1F1F1F')
        self.color = "#000000"
        self.brush_size = 3
        self.eraser = False
        self.last_x = self.last_y = None
        self.strokes = []
        self.current_stroke = None

        bar = tk.Frame(self.win, bg='#252525', height=42)
        bar.pack(fill=tk.X)
        palette = ['#000000', '#FFFFFF', '#E81123', '#0078D4', '#107C10', '#FFB900', '#B4009E', '#795548']
        for color in palette:
            tk.Button(bar, bg=color, width=2, height=1, bd=0, relief=tk.FLAT,
                      command=lambda col=color: self.set_color(col)).pack(side=tk.LEFT, padx=3, pady=4)
        tk.Button(bar, text="Ластик", bg='#333333', fg='white', bd=0, padx=8,
                  command=self.toggle_eraser).pack(side=tk.LEFT, padx=5)
        tk.Label(bar, text='Кисть', bg='#252525', fg='#D0D0D0', font=('Segoe UI', 8)).pack(side=tk.LEFT)
        self.size_var = tk.IntVar(value=3)
        tk.Scale(bar, from_=1, to=20, orient=tk.HORIZONTAL, variable=self.size_var,
                 command=lambda v: setattr(self, 'brush_size', int(float(v))), length=105,
                 bg='#252525', fg='white', troughcolor='#444444', highlightthickness=0).pack(side=tk.LEFT, padx=3)
        tk.Button(bar, text="Сохранить PNG", bg='#0078D4', fg='white', bd=0, padx=8,
                  command=self.save_image).pack(side=tk.RIGHT, padx=5)
        tk.Button(bar, text="Очистить", bg='#A80000', fg='white', bd=0, padx=8,
                  command=self.clear_canvas).pack(side=tk.RIGHT, padx=5)

        self.canvas = tk.Canvas(self.win, bg='#FFFFFF', cursor='tcross')
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.canvas.bind('<ButtonPress-1>', self.begin_stroke)
        self.canvas.bind('<B1-Motion>', self.draw)
        self.canvas.bind('<ButtonRelease-1>', self.reset)

    def set_color(self, color):
        self.color = color
        self.eraser = False

    def toggle_eraser(self):
        self.eraser = not self.eraser

    def begin_stroke(self, event):
        self.last_x, self.last_y = event.x, event.y
        self.current_stroke = {'color': '#FFFFFF' if self.eraser else self.color,
                               'size': 18 if self.eraser else self.brush_size,
                               'points': [(event.x, event.y)]}
        self.strokes.append(self.current_stroke)

    def draw(self, event):
        if self.last_x is None or self.last_y is None:
            self.begin_stroke(event)
            return
        color = '#FFFFFF' if self.eraser else self.color
        size = 18 if self.eraser else self.brush_size
        self.canvas.create_line(self.last_x, self.last_y, event.x, event.y, width=size, fill=color,
                                capstyle=tk.ROUND, joinstyle=tk.ROUND, smooth=True)
        if self.current_stroke is not None:
            self.current_stroke['points'].append((event.x, event.y))
        self.last_x, self.last_y = event.x, event.y

    def reset(self, _event=None):
        self.last_x = self.last_y = None
        self.current_stroke = None

    def clear_canvas(self):
        self.canvas.delete('all')
        self.strokes.clear()
        self.reset()

    def save_image(self):
        if not PIL_AVAILABLE:
            messagebox.showerror('Paint', 'Для сохранения PNG установите Pillow.', parent=self.win)
            return
        path = bitos_asksaveasfilename(self.win, self.bitos, filetypes=[('PNG image', '*.png')], initialfile='Рисунок.png')
        if not path: return
        try:
            from PIL import ImageDraw
            width = max(1, self.canvas.winfo_width())
            height = max(1, self.canvas.winfo_height())
            image = Image.new('RGB', (width, height), 'white')
            draw = ImageDraw.Draw(image)
            for stroke in self.strokes:
                points = stroke['points']
                if len(points) == 1:
                    x, y = points[0]; radius = max(1, stroke['size'] // 2)
                    draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=stroke['color'])
                elif len(points) > 1:
                    draw.line(points, fill=stroke['color'], width=stroke['size'], joint='curve')
            image.save(path, 'PNG')
            messagebox.showinfo('Paint', f'Изображение сохранено:\n{path}', parent=self.win)
        except Exception as exc:
            messagebox.showerror('Paint', f'Не удалось сохранить изображение:\n{exc}', parent=self.win)


# ============================================================================
# 8. УСТАНОВЩИК BIP И ДИАЛОГ РАЗРАБОТЧИКА (ПОЛНЫЙ ФУНКЦИОНАЛ)
# ============================================================================

class BipInstallWindow:
    """Установщик пакетов .bip"""
    def __init__(self, parent, bitos):
        self.win = tk.Toplevel(parent)
        self.win.title("Установщик BIP")
        self.win.geometry("440x260")
        self.win.configure(bg='#1F1F1F')
        self.bitos = bitos
        self.installer = BipInstaller(parent, bitos)
        
        tk.Label(self.win, text="Установка пакетов программ (.bip)", font=('Segoe UI', 11, 'bold'),
                 bg='#1F1F1F', fg='white').pack(pady=12)
                 
        self.path_lbl = tk.Label(self.win, text="Файл не выбран", font=('Segoe UI', 9),
                                 bg='#1F1F1F', fg='#A0A0A0')
        self.path_lbl.pack(pady=4)
        
        tk.Button(self.win, text="Выбрать файл .bip", bg='#252525', fg='white', bd=0, padx=12, pady=4,
                  command=self.browse).pack(pady=4)
                  
        self.inst_btn = tk.Button(self.win, text="Установить", bg='#0078D4', fg='white', bd=0, padx=20, pady=6,
                                  state='disabled', command=self.install)
        self.inst_btn.pack(pady=12)
        self.selected_file = None

    def browse(self):
        f = bitos_askopenfilename(self.win, self.bitos, filetypes=[("BIP Packages", "*.bip"), ("All Files", "*.*")])
        if f:
            self.selected_file = f
            self.path_lbl.config(text=os.path.basename(f), fg='white')
            self.inst_btn.config(state='normal')

    def install(self):
        if not self.selected_file: return
        ok, res = self.installer.install_bip(self.selected_file)
        if ok:
            messagebox.showinfo("Успех", f"Пакет '{res.get('name')}' успешно установлен", parent=self.win)
            self.win.destroy()
        else:
            messagebox.showerror("Ошибка", f"Не удалось установить пакет:\n{res}", parent=self.win)


class DevModeDialog:
    """Вход в режим разработчика с проверкой пароля BIT642Os"""
    def __init__(self, parent, bitos):
        self.win = tk.Toplevel(parent)
        self.win.title("Режим разработчика")
        self.win.geometry("340x180")
        self.win.configure(bg='#1F1F1F')
        self.bitos = bitos
        
        tk.Label(self.win, text="Вход в режим разработчика", font=('Segoe UI', 10, 'bold'),
                 bg='#1F1F1F', fg='white').pack(pady=(16, 6))
                 
        self.entry = tk.Entry(self.win, font=('Segoe UI', 10), bg='#2D2D2D', fg='white', bd=0, show='●', justify='center')
        self.entry.pack(fill=tk.X, padx=30, pady=6, ipady=3)
        self.entry.focus_set()
        self.entry.bind('<Return>', lambda e: self.check())
        
        self.err_lbl = tk.Label(self.win, text="", font=('Segoe UI', 8), bg='#1F1F1F', fg='#E81123')
        self.err_lbl.pack(pady=2)
        
        tk.Button(self.win, text="Подтвердить", bg='#0078D4', fg='white', bd=0, padx=16, pady=4,
                  command=self.check).pack(pady=6)

    def check(self):
        if self.entry.get().strip() == self.bitos.dev_password:
            self.bitos.dev_mode = True
            messagebox.showinfo("Успех", "Режим разработчика активирован", parent=self.win)
            self.win.destroy()
        else:
            self.err_lbl.config(text="Неверный пароль разработчика")
            self.entry.delete(0, tk.END)


# ============================================================================
# 9. ПАРАМЕТРЫ (SETTINGS С ПОЛЗУНКОМ ПРОИЗВОДИТЕЛЬНОСТИ И ВКЛАДКОЙ ФУНКЦИИ)
# ============================================================================

class TaskManagerWindow:
    """BITOS task manager: live app windows, process list and system metrics."""
    def __init__(self, parent, desktop):
        self.desktop = desktop
        self.bitos = desktop.bitos
        self.win = tk.Toplevel(parent)
        self.win.title("Диспетчер задач BITOS")
        self.win.geometry("820x520")
        self.win.configure(bg="#1F1F1F")
        self._refresh_after = None
        self._psutil = None
        try:
            import psutil
            self._psutil = psutil
            psutil.cpu_percent(interval=None)
        except Exception:
            pass

        header = tk.Frame(self.win, bg="#1F1F1F")
        header.pack(fill=tk.X, padx=12, pady=10)
        tk.Label(header, text="Диспетчер задач", font=("Segoe UI", 15, "bold"),
                 bg="#1F1F1F", fg="white").pack(side=tk.LEFT)
        self.summary = tk.Label(header, text="Обновление…", bg="#1F1F1F", fg="#A0A0A0")
        self.summary.pack(side=tk.RIGHT)
        self.tabs = ttk.Notebook(self.win)
        self.tabs.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        apps_tab = tk.Frame(self.tabs, bg="#1F1F1F")
        self.tabs.add(apps_tab, text="Приложения")
        self.apps_tree = ttk.Treeview(apps_tab, columns=("name", "state"), show="headings")
        self.apps_tree.heading("name", text="Приложение")
        self.apps_tree.heading("state", text="Состояние")
        self.apps_tree.column("name", width=480, stretch=True)
        self.apps_tree.column("state", width=150, stretch=False)
        self.apps_tree.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        app_buttons = tk.Frame(apps_tab, bg="#1F1F1F")
        app_buttons.pack(fill=tk.X, padx=6, pady=(0, 6))
        tk.Button(app_buttons, text="Переключиться", bg="#0078D4", fg="white", bd=0,
                 command=self.focus_selected_app).pack(side=tk.LEFT, padx=3)
        tk.Button(app_buttons, text="Завершить приложение", bg="#8B2020", fg="white", bd=0,
                 command=self.close_selected_app).pack(side=tk.LEFT, padx=3)

        proc_tab = tk.Frame(self.tabs, bg="#1F1F1F")
        self.tabs.add(proc_tab, text="Процессы")
        self.proc_tree = ttk.Treeview(proc_tab, columns=("name", "pid", "memory"), show="headings")
        for col, label, width in (("name", "Процесс", 440), ("pid", "PID", 100), ("memory", "Память", 130)):
            self.proc_tree.heading(col, text=label)
            self.proc_tree.column(col, width=width, stretch=(col == "name"))
        self.proc_tree.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        proc_buttons = tk.Frame(proc_tab, bg="#1F1F1F")
        proc_buttons.pack(fill=tk.X, padx=6, pady=(0, 6))
        tk.Button(proc_buttons, text="Завершить процесс", bg="#8B2020", fg="white", bd=0,
                 command=self.terminate_selected_process).pack(side=tk.LEFT, padx=3)
        tk.Button(proc_buttons, text="Обновить", bg="#333333", fg="white", bd=0,
                 command=self.refresh).pack(side=tk.LEFT, padx=3)

        perf_tab = tk.Frame(self.tabs, bg="#1F1F1F")
        self.tabs.add(perf_tab, text="Производительность")
        self.performance = tk.Label(perf_tab, text="", justify=tk.LEFT, anchor="nw",
                                   font=("Consolas", 12), bg="#1F1F1F", fg="#E5E5E5")
        self.performance.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        self.refresh()
        self._schedule_refresh()

    def _schedule_refresh(self):
        try:
            if self.win.winfo_exists():
                self._refresh_after = self.win.after(2000, self._scheduled_refresh)
        except Exception:
            pass

    def _scheduled_refresh(self):
        self.refresh()
        self._schedule_refresh()

    def _get_processes(self):
        result = []
        if self._psutil:
            try:
                for proc in self._psutil.process_iter(["pid", "name", "memory_info"]):
                    try:
                        info = proc.info
                        rss = getattr(info.get("memory_info"), "rss", 0)
                        result.append((str(info.get("name") or "Процесс"), int(info["pid"]), int(rss)))
                    except Exception:
                        pass
                return sorted(result, key=lambda row: row[0].casefold())
            except Exception:
                pass
        try:
            if os.name == "nt":
                completed = subprocess.run(["tasklist", "/FO", "CSV", "/NH"], capture_output=True,
                                          text=True, encoding="utf-8", errors="replace", timeout=5,
                                          creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                for row in csv.reader(completed.stdout.splitlines()):
                    if len(row) >= 5:
                        try:
                            pid = int(row[1].replace('"', '').strip())
                            mem = int(row[4].replace('"', '').replace(',', '').replace(' K', '').replace('K', '').strip() or 0) * 1024
                            result.append((row[0].strip(), pid, mem))
                        except Exception:
                            continue
            else:
                completed = subprocess.run(["ps", "-eo", "pid,comm,rss"], capture_output=True,
                                          text=True, timeout=5)
                for line in completed.stdout.splitlines()[1:]:
                    parts = line.strip().split(None, 2)
                    if len(parts) == 3:
                        try: result.append((parts[1], int(parts[0]), int(parts[2]) * 1024))
                        except Exception: pass
        except Exception:
            pass
        return sorted(result, key=lambda row: row[0].casefold())

    @staticmethod
    def _memory_text(value):
        return f"{value / (1024 * 1024):.1f} МБ" if value else "—"

    def _fallback_system_metrics(self):
        cpu_percent = memory_percent = None
        memory_used = memory_total = 0
        if os.name == "nt":
            try:
                import ctypes
                from ctypes import wintypes
                class FILETIME(ctypes.Structure):
                    _fields_ = [("dwLowDateTime", wintypes.DWORD), ("dwHighDateTime", wintypes.DWORD)]
                idle, kernel, user = FILETIME(), FILETIME(), FILETIME()
                if ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)):
                    def ft(value):
                        return (value.dwHighDateTime << 32) | value.dwLowDateTime
                    current = (ft(idle), ft(kernel), ft(user))
                    previous = getattr(self, "_cpu_previous", None)
                    self._cpu_previous = current
                    if previous:
                        delta_idle = current[0] - previous[0]
                        delta_kernel = current[1] - previous[1]
                        delta_user = current[2] - previous[2]
                        total = delta_kernel + delta_user
                        if total > 0:
                            cpu_percent = max(0.0, min(100.0, 100.0 * (total - delta_idle) / total))
                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [("dwLength", wintypes.DWORD), ("dwMemoryLoad", wintypes.DWORD),
                                ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                                ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                                ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
                status = MEMORYSTATUSEX()
                status.dwLength = ctypes.sizeof(status)
                if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                    memory_percent = float(status.dwMemoryLoad)
                    memory_total = int(status.ullTotalPhys)
                    memory_used = memory_total - int(status.ullAvailPhys)
            except Exception:
                pass
        disk_percent = disk_used = disk_total = None
        try:
            disk = shutil.disk_usage(os.path.abspath(os.sep))
            disk_total, disk_used = disk.total, disk.used
            disk_percent = 100.0 * disk.used / max(1, disk.total)
        except Exception:
            pass
        return cpu_percent, memory_percent, memory_used, memory_total, disk_percent, disk_used, disk_total

    def refresh(self):
        try:
            if not self.win.winfo_exists():
                return
            for item in self.apps_tree.get_children():
                self.apps_tree.delete(item)
            for key, (window, button) in list(self.desktop.taskbar.window_buttons.items()):
                try:
                    if window.winfo_exists():
                        title = window.title() or "Окно приложения"
                        state = "Свернуто" if window.state() == "iconic" else "Запущено"
                        self.apps_tree.insert("", tk.END, iid=str(key), values=(title, state))
                except Exception:
                    pass
            for item in self.proc_tree.get_children():
                self.proc_tree.delete(item)
            processes = self._get_processes()
            for name, pid, memory in processes:
                self.proc_tree.insert("", tk.END, iid=f"proc_{pid}", values=(name, pid, self._memory_text(memory)))
            total_mem = sum(row[2] for row in processes)
            self.summary.config(text=f"Окон: {len(self.apps_tree.get_children())}  •  Процессов: {len(processes)}")
            try:
                if self._psutil:
                    cpu = self._psutil.cpu_percent(interval=None)
                    mem = self._psutil.virtual_memory()
                    disk = self._psutil.disk_usage(os.path.abspath(os.sep))
                    cpu_text = f"{cpu:.0f}%"
                    mem_text = f"{mem.percent:.0f}%  ({mem.used / (1024**3):.1f} / {mem.total / (1024**3):.1f} ГБ)"
                    disk_text = f"{disk.percent:.0f}%  ({disk.used / (1024**3):.1f} / {disk.total / (1024**3):.1f} ГБ)"
                else:
                    cpu, mem_pct, mem_used, mem_total, disk_pct, disk_used, disk_total = self._fallback_system_metrics()
                    cpu_text = f"{cpu:.0f}%" if cpu is not None else "сбор…"
                    mem_text = (f"{mem_pct:.0f}%  ({mem_used / (1024**3):.1f} / {mem_total / (1024**3):.1f} ГБ)"
                               if mem_pct is not None else "недоступно")
                    disk_text = (f"{disk_pct:.0f}%  ({disk_used / (1024**3):.1f} / {disk_total / (1024**3):.1f} ГБ)"
                                if disk_pct is not None else "недоступно")
                self.performance.config(text=(
                    f"CPU: {cpu_text}\n"
                    f"ОЗУ: {mem_text}\n"
                    f"Диск: {disk_text}\n\n"
                    f"Суммарная память процессов: {self._memory_text(total_mem)}\n"
                    "Данные обновляются каждые 2 секунды."
                ))
            except Exception:
                self.performance.config(text="Не удалось получить показатели производительности.")
        except Exception:
            pass

    def focus_selected_app(self):
        selected = self.apps_tree.selection()
        if not selected:
            return
        item = self.desktop.taskbar.window_buttons.get(int(selected[0]))
        if item:
            self.desktop.taskbar._focus_window(item[0])

    def close_selected_app(self):
        selected = self.apps_tree.selection()
        if not selected:
            return
        item = self.desktop.taskbar.window_buttons.get(int(selected[0]))
        if item:
            self.desktop._animate_window_close(item[0])

    def terminate_selected_process(self):
        selected = self.proc_tree.selection()
        if not selected:
            return
        values = self.proc_tree.item(selected[0], "values")
        try:
            pid = int(values[1])
        except Exception:
            return
        if not messagebox.askyesno("Завершить процесс", f"Завершить процесс {values[0]} (PID {pid})?", parent=self.win):
            return
        try:
            if self._psutil:
                self._psutil.Process(pid).terminate()
            else:
                if os.name == "nt":
                    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], check=True,
                                  capture_output=True, timeout=5,
                                  creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                else:
                    os.kill(pid, 15)
            self.refresh()
        except Exception as exc:
            messagebox.showerror("Диспетчер задач", f"Не удалось завершить процесс:\n{exc}", parent=self.win)


class MediaPlayerWindow:
    """Simple BITOS playlist player. pygame is optional for audio playback."""
    AUDIO_EXTS = (".mp3", ".wav", ".ogg", ".flac", ".mid")
    VIDEO_EXTS = (".mp4", ".mkv", ".avi", ".mov", ".wmv", ".webm")

    def __init__(self, parent, desktop):
        self.desktop = desktop
        self.bitos = desktop.bitos
        self.win = tk.Toplevel(parent)
        self.win.title("Медиаплеер BITOS")
        self.win.geometry("720x500")
        self.win.configure(bg="#1F1F1F")
        self.playlist = []
        self.current_index = -1
        self._pygame = None
        self._vlc_instance = None
        self._vlc_player = None
        self._playing = False
        self._paused = False
        self._position_after = None
        try:
            import vlc
            self._vlc_instance = vlc.Instance()
            self._vlc_player = self._vlc_instance.media_player_new()
        except Exception:
            self._vlc_instance = self._vlc_player = None
        try:
            import pygame
            pygame.mixer.init()
            self._pygame = pygame
        except Exception:
            self._pygame = None

        top = tk.Frame(self.win, bg="#1F1F1F")
        top.pack(fill=tk.X, padx=12, pady=10)
        tk.Label(top, text="Медиаплеер", font=("Segoe UI", 15, "bold"), bg="#1F1F1F", fg="white").pack(side=tk.LEFT)
        tk.Button(top, text="＋ Добавить файлы", bg="#0078D4", fg="white", bd=0,
                 command=self.add_files).pack(side=tk.RIGHT, padx=3)
        tk.Button(top, text="Добавить папку", bg="#333333", fg="white", bd=0,
                 command=self.add_folder).pack(side=tk.RIGHT, padx=3)

        self.track_label = tk.Label(self.win, text="Выберите аудиофайл", bg="#1F1F1F", fg="#E0E0E0",
                                   font=("Segoe UI", 11), wraplength=650)
        self.track_label.pack(fill=tk.X, padx=12, pady=(4, 8))
        self.video_panel = tk.Frame(self.win, bg="#050505", height=150)
        self.video_panel.pack(fill=tk.X, padx=12, pady=(0, 8))
        self.video_panel.pack_propagate(False)
        tk.Label(self.video_panel, text="Видеопанель BITOS", bg="#050505", fg="#555555").pack(expand=True)
        body = tk.Frame(self.win, bg="#1F1F1F")
        body.pack(fill=tk.BOTH, expand=True, padx=12)
        self.listbox = tk.Listbox(body, bg="#292929", fg="white", selectbackground="#0078D4",
                                  bd=0, font=("Segoe UI", 9), activestyle="none")
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll = ttk.Scrollbar(body, orient=tk.VERTICAL, command=self.listbox.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.configure(yscrollcommand=scroll.set)
        self.listbox.bind("<Double-1>", lambda _e: self.play_selected())

        controls = tk.Frame(self.win, bg="#1F1F1F")
        controls.pack(fill=tk.X, padx=12, pady=8)
        for label, action in (("⏮", self.previous), ("▶", self.play_selected), ("⏸", self.pause),
                              ("⏹", self.stop), ("⏭", self.next)):
            tk.Button(controls, text=label, bg="#333333", fg="white", bd=0, width=5,
                     command=action).pack(side=tk.LEFT, padx=3)
        tk.Label(controls, text="Громкость", bg="#1F1F1F", fg="#A0A0A0").pack(side=tk.LEFT, padx=(14, 4))
        self.volume = tk.DoubleVar(value=0.75)
        tk.Scale(controls, from_=0, to=1, resolution=0.05, orient=tk.HORIZONTAL,
                 variable=self.volume, length=130, bg="#1F1F1F", fg="white", troughcolor="#444444",
                 highlightthickness=0, command=self.set_volume).pack(side=tk.LEFT)
        self.status = tk.Label(self.win, text="Готово", bg="#1F1F1F", fg="#A0A0A0", anchor="w")
        self.status.pack(fill=tk.X, padx=12, pady=(0, 8))
        if self._pygame is None and self._vlc_player is None:
            self.status.config(text="Для встроенного воспроизведения установите pygame либо VLC + python-vlc.")
        self.win.bind("<Destroy>", self._cleanup, add="+")

    def _cleanup(self, event=None):
        if event is not None and getattr(event, "widget", None) is not self.win:
            return
        try:
            if self._vlc_player is not None:
                self._vlc_player.stop()
        except Exception:
            pass
        try:
            if self._pygame is not None:
                self._pygame.mixer.music.stop()
        except Exception:
            pass

    def add_files(self):
        paths = bitos_askopenfilenames(self.win, self.bitos,
            filetypes=[("Медиафайлы", "*.mp3 *.wav *.ogg *.flac *.mid *.mp4 *.mkv *.avi *.mov *.wmv *.webm"),
                      ("Все файлы", "*.*")])
        self._add_paths(paths)

    def add_folder(self):
        folder = bitos_askdirectory(self.win, self.bitos)
        if not folder:
            return
        found = []
        try:
            for name in os.listdir(folder):
                path = os.path.join(folder, name)
                if os.path.isfile(path) and os.path.splitext(name)[1].lower() in self.AUDIO_EXTS + self.VIDEO_EXTS:
                    found.append(path)
        except OSError as exc:
            messagebox.showerror("Медиаплеер", str(exc), parent=self.win)
        self._add_paths(found)

    def _add_paths(self, paths):
        for path in paths:
            if path and os.path.isfile(path) and path not in self.playlist:
                self.playlist.append(path)
                self.listbox.insert(tk.END, os.path.basename(path))
        self.status.config(text=f"В плейлисте: {len(self.playlist)}")

    def play_selected(self):
        selected = self.listbox.curselection()
        if selected:
            self.current_index = selected[0]
        if not 0 <= self.current_index < len(self.playlist):
            if self.playlist:
                self.current_index = 0
            else:
                self.add_files()
                if not self.playlist:
                    return
                self.current_index = 0
        path = self.playlist[self.current_index]
        ext = os.path.splitext(path)[1].lower()
        if ext in self.VIDEO_EXTS:
            if self._vlc_player is not None:
                try:
                    self.video_panel.update_idletasks()
                    if os.name == "nt":
                        self._vlc_player.set_hwnd(self.video_panel.winfo_id())
                    elif sys.platform == "darwin":
                        self._vlc_player.set_nsobject(self.video_panel.winfo_id())
                    else:
                        self._vlc_player.set_xwindow(self.video_panel.winfo_id())
                    media = self._vlc_instance.media_new(path)
                    self._vlc_player.set_media(media)
                    self._vlc_player.audio_set_volume(int(float(self.volume.get()) * 100))
                    self._vlc_player.play()
                    self._playing = True
                    self._paused = False
                    self.track_label.config(text=os.path.basename(path))
                    self.status.config(text="Воспроизведение видео")
                except Exception as exc:
                    messagebox.showerror("Медиаплеер", f"Не удалось запустить видео:\n{exc}", parent=self.win)
            else:
                try:
                    if os.name == "nt": os.startfile(path)
                    elif sys.platform == "darwin": subprocess.Popen(["open", path])
                    else: subprocess.Popen(["xdg-open", path])
                    self.status.config(text="Видео открыто во внешнем плеере. Для встроенного установите VLC и python-vlc.")
                except Exception as exc:
                    messagebox.showerror("Медиаплеер", str(exc), parent=self.win)
            return
        if self._pygame is None and self._vlc_player is None:
            try:
                if os.name == "nt": os.startfile(path)
                elif sys.platform == "darwin": subprocess.Popen(["open", path])
                else: subprocess.Popen(["xdg-open", path])
                self.status.config(text="Открыто во внешнем аудиоплеере. Для встроенного установите pygame.")
            except Exception as exc:
                messagebox.showerror("Медиаплеер", str(exc), parent=self.win)
            return
        try:
            if self._vlc_player is not None:
                media = self._vlc_instance.media_new(path)
                self._vlc_player.set_media(media)
                self._vlc_player.audio_set_volume(int(float(self.volume.get()) * 100))
                self._vlc_player.play()
            else:
                self._pygame.mixer.music.load(path)
                self._pygame.mixer.music.set_volume(float(self.volume.get()))
                self._pygame.mixer.music.play()
            self._playing = True
            self._paused = False
            self.track_label.config(text=os.path.basename(path))
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(self.current_index)
            self.status.config(text="Воспроизведение")
        except Exception as exc:
            messagebox.showerror("Медиаплеер", f"Не удалось воспроизвести файл:\n{exc}", parent=self.win)

    def pause(self):
        if self._pygame is None and self._vlc_player is None:
            return
        try:
            if self._vlc_player is not None:
                if self._paused:
                    self._vlc_player.play()
                    self._paused = False
                    self.status.config(text="Воспроизведение")
                elif self._playing:
                    self._vlc_player.pause()
                    self._paused = True
                    self.status.config(text="Пауза")
                return
            if self._paused:
                self._pygame.mixer.music.unpause()
                self._paused = False
                self.status.config(text="Воспроизведение")
            elif self._playing:
                self._pygame.mixer.music.pause()
                self._paused = True
                self.status.config(text="Пауза")
        except Exception:
            pass

    def stop(self):
        if self._vlc_player is not None:
            try: self._vlc_player.stop()
            except Exception: pass
        if self._pygame is not None:
            try: self._pygame.mixer.music.stop()
            except Exception: pass
        self._playing = False
        self._paused = False
        self.status.config(text="Остановлено")

    def previous(self):
        if not self.playlist:
            return
        self.current_index = (self.current_index - 1) % len(self.playlist)
        self.play_selected()

    def next(self):
        if not self.playlist:
            return
        self.current_index = (self.current_index + 1) % len(self.playlist)
        self.play_selected()

    def set_volume(self, value):
        if self._vlc_player is not None:
            try: self._vlc_player.audio_set_volume(int(float(value) * 100))
            except Exception: pass
        if self._pygame is not None:
            try: self._pygame.mixer.music.set_volume(float(value))
            except Exception: pass


class SettingsWindow:
    """Окно параметров: левая колонка, переключение без пересоздания, вкладка Функции и Производительность"""
    def __init__(self, parent, desktop):
        self.parent = parent
        self.desktop = desktop
        self.bitos = desktop.bitos
        self.ui = desktop.bitos.ui_manager
        
        self.win = tk.Toplevel(parent)
        self.win.title("Параметры BITOS")
        self.win.geometry("880x560")
        self.win.configure(bg='#1F1F1F')
        
        self.sidebar = tk.Frame(self.win, bg='#141414', width=220)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)
        
        self.container = tk.Frame(self.win, bg='#1F1F1F')
        self.container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=16)
        
        self.sections = {}
        self.nav_buttons = {}
        
        menu_items = [
            ("Функции", self._create_features_tab),
            ("Производительность", self._create_performance_tab),
            ("Темы", self._create_theme_tab),
            ("Звук", self._create_sound_tab),
            ("Безопасность", self._create_sec_tab),
            ("Обновления", self._create_updates_tab),
            ("Система", self._create_sys_tab),
        ]
        
        for name, builder in menu_items:
            f = tk.Frame(self.container, bg='#1F1F1F')
            self.sections[name] = f
            builder(f)
            
            btn = tk.Button(self.sidebar, text=f"  {name}", font=('Segoe UI', 10),
                            bg='#141414', fg='white', bd=0, anchor='w', relief=tk.FLAT,
                            command=lambda n=name: self.switch_section(n))
            btn.pack(fill=tk.X, pady=2)
            self.nav_buttons[name] = btn
            
        self.switch_section("Функции")

    def switch_section(self, name):
        for n, f in self.sections.items():
            f.pack_forget()
            self.nav_buttons[n].config(bg='#141414')
        self.sections[name].pack(fill=tk.BOTH, expand=True)
        self.nav_buttons[name].config(bg='#252525')

    def _create_features_tab(self, parent):
        tk.Label(parent, text="Функции и режимы системы", font=('Segoe UI', 16, 'bold'),
                 bg='#1F1F1F', fg='white').pack(anchor='w', pady=(0, 20))
        
        row1 = tk.Frame(parent, bg='#252525', padx=16, pady=12)
        row1.pack(fill=tk.X, pady=8)
        tk.Label(row1, text="Режим планшета", font=('Segoe UI', 11, 'bold'),
                 bg='#252525', fg='white').pack(anchor='w')
        tk.Label(row1, text="Переключение масштабирования сетки и интерфейса без перезапуска",
                 font=('Segoe UI', 9), bg='#252525', fg='#A0A0A0').pack(anchor='w', pady=2)
        
        self.t_val = tk.BooleanVar(value=self.ui.touch_mode)
        t_btn = ttk.Checkbutton(row1, text="Включено" if self.t_val.get() else "Выключено",
                                variable=self.t_val, command=self._toggle_touch)
        t_btn.pack(anchor='w', pady=4)
        
        row2 = tk.Frame(parent, bg='#252525', padx=16, pady=12)
        row2.pack(fill=tk.X, pady=8)
        tk.Label(row2, text="Второй экран", font=('Segoe UI', 11, 'bold'),
                 bg='#252525', fg='white').pack(anchor='w')
        tk.Label(row2, text="Режим работы дополнительного монитора (мгновенное переключение)",
                 font=('Segoe UI', 9), bg='#252525', fg='#A0A0A0').pack(anchor='w', pady=2)
        
        self.m2_var = tk.StringVar(value=self.ui.second_screen_mode)
        rb1 = ttk.Radiobutton(row2, text="Режим часов", variable=self.m2_var, value="clock",
                              command=self._toggle_monitor_mode)
        rb1.pack(anchor='w', pady=2)
        rb2 = ttk.Radiobutton(row2, text="Черный экран", variable=self.m2_var, value="black",
                              command=self._toggle_monitor_mode)
        rb2.pack(anchor='w', pady=2)

    def _toggle_touch(self):
        self.ui.set_touch_mode(self.t_val.get())
        self.desktop.apply_ui_settings()

    def _toggle_monitor_mode(self):
        self.ui.set_second_screen_mode(self.m2_var.get())
        self.bitos.monitor_manager.restart_all_screens()

    def _create_performance_tab(self, parent):
        tk.Label(parent, text="Производительность системы", font=('Segoe UI', 16, 'bold'),
                 bg='#1F1F1F', fg='white').pack(anchor='w', pady=(0, 16))

        card = tk.Frame(parent, bg='#252525', padx=16, pady=16)
        card.pack(fill=tk.X, pady=8)

        tk.Label(card, text="Уровень оптимизации для слабых ПК", font=('Segoe UI', 10, 'bold'),
                 bg='#252525', fg='#FFFFFF').pack(anchor='w')

        self.perf_desc_label = tk.Label(card, text="", font=('Segoe UI', 9),
                                        bg='#252525', fg='#A0A0A0', justify='left')
        self.perf_desc_label.pack(anchor='w', pady=(6, 12))

        slider_frame = tk.Frame(card, bg='#252525')
        slider_frame.pack(fill=tk.X, pady=4)

        self._perf_updating = False
        self._last_perf_level = self.ui.get_optimization_level()
        self.perf_val_label = tk.Label(slider_frame, text=f"{self.ui.get_optimization_level()}%",
                                       font=('Segoe UI', 10, 'bold'), bg='#252525', fg='#0078D4', width=6)
        self.perf_val_label.pack(side=tk.RIGHT, padx=(8, 0))

        self.perf_scale = ttk.Scale(
            slider_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            command=self._on_perf_slide
        )
        self._perf_updating = True
        self.perf_scale.set(self.ui.get_optimization_level())
        self._perf_updating = False
        self.perf_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self._update_perf_description(self._last_perf_level)

    def _on_perf_slide(self, val):
        if getattr(self, "_perf_updating", False):
            return
        raw_val = float(val)
        steps = [0, 25, 50, 75, 100]
        nearest = min(steps, key=lambda x: abs(x - raw_val))
        self._perf_updating = True
        try:
            self.perf_scale.set(nearest)
        finally:
            self._perf_updating = False
        self.perf_val_label.config(text=f"{nearest}%")
        self._update_perf_description(nearest)
        if nearest == self._last_perf_level:
            return
        self._last_perf_level = nearest
        self.ui.set_optimization_level(nearest)
        self.desktop.apply_ui_settings()

    def _update_perf_description(self, level):
        descriptions = {
            0: "0% — Максимальное качество. Полные анимации, градиенты, тени и обои в исходном разрешении. Часы — каждую секунду. Автосохранение — каждые 10 секунд.",
            25: "25% — Комфорт. Анимация важных элементов (Пуск), уведомления появляются сразу. Градиенты остаются, тени отключены. Автосохранение — каждые 15 секунд.",
            50: "50% — Средний, для ПК с 4 ГБ ОЗУ. Анимации/тени отключены. Системные проверки — раз в 10 секунд. Обои — в половинном разрешении. Логи записываются пакетно раз в 5 секунд.",
            75: "75% — Высокая, для слабых ПК. Часы обновляются раз в минуту. Виджеты и всплывающие уведомления скрыты, обои уменьшаются до четверти разрешения. Автоматические проверки и обновления не запускаются; ручные действия доступны.",
            100: "100% — Режим выживания. Статичный интерфейс, однотонный фон, без виджетов, таймеров, автоматических проверок и записи логов. Ручные действия пользователя остаются доступны."
        }
        self.perf_desc_label.config(text=descriptions.get(level, ""))

    def _create_theme_tab(self, parent):
        tk.Label(parent, text="Оформление", font=('Segoe UI', 16, 'bold'),
                 bg='#1F1F1F', fg='white').pack(anchor='w', pady=(0, 16))

        # Personalization: desktop icon scale, saved in the BITOS config folder.
        scale_card = tk.Frame(parent, bg='#252525', padx=14, pady=10)
        scale_card.pack(fill=tk.X, pady=(0, 12))
        tk.Label(scale_card, text="Размер значков рабочего стола", font=('Segoe UI', 10, 'bold'),
                 bg='#252525', fg='white').pack(anchor='w')
        cfg = os.path.join(self.bitos.system_paths['config'], 'desktop_icon_scale.json')
        try:
            scale_value = int(json.loads(Path(cfg).read_text(encoding='utf-8')).get('scale', 100))
        except Exception:
            scale_value = 100
        scale_row = tk.Frame(scale_card, bg='#252525')
        scale_row.pack(fill=tk.X, pady=(6, 0))
        scale_label = tk.Label(scale_row, text=f"{scale_value}%", bg='#252525', fg='#79C8F2', width=6)
        scale_label.pack(side=tk.RIGHT)
        def set_icon_scale(value):
            scale = int(round(float(value) / 10) * 10)
            scale = max(60, min(140, scale))
            scale_label.config(text=f"{scale}%")
            try:
                Path(cfg).parent.mkdir(parents=True, exist_ok=True)
                Path(cfg).write_text(json.dumps({'scale': scale}, ensure_ascii=False), encoding='utf-8')
            except Exception:
                pass
            self.desktop.apply_ui_settings()
        icon_scale = ttk.Scale(scale_row, from_=60, to=140, value=scale_value,
                              orient=tk.HORIZONTAL, command=set_icon_scale)
        icon_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)

        for t in ["Белая", "Чёрная", "Голубая", "Розовая"]:
            btn = tk.Button(parent, text=f"Тема: {t}", font=('Segoe UI', 10),
                            bg='#0078D4', fg='white', bd=0, padx=16, pady=8, relief=tk.FLAT,
                            command=lambda tn=t: self.desktop.change_theme(tn))
            btn.pack(anchor='w', pady=4)
        tk.Button(parent, text="🖼 Настроить обои", font=('Segoe UI', 10),
                  bg='#303030', fg='white', bd=0, padx=16, pady=8,
                  command=self.desktop.open_wallpaper_settings).pack(anchor='w', pady=10)
        tk.Button(parent, text="＋ Создать свою тему", font=('Segoe UI', 10),
                  bg='#303030', fg='white', bd=0, padx=16, pady=8,
                  command=lambda: FlatCustomThemeDialog(self.win, self.desktop)).pack(anchor='w', pady=4)

    def _create_sound_tab(self, parent):
        tk.Label(parent, text="Звуки BITOS", font=('Segoe UI', 16, 'bold'),
                 bg='#1F1F1F', fg='white').pack(anchor='w', pady=(0, 16))
        tk.Label(parent, text="Системные звуки приложения хранятся в system/Sounds и работают независимо от звуков Windows.",
                 font=('Segoe UI', 9), bg='#1F1F1F', fg='#A0A0A0', wraplength=560, justify='left').pack(anchor='w', pady=6)
        self.sound_var = tk.BooleanVar(value=self.bitos.sound_enabled)
        ttk.Checkbutton(parent, text="Включить звуки приложения", variable=self.sound_var,
                        command=self._toggle_sound).pack(anchor='w', pady=10)
        row = tk.Frame(parent, bg='#1F1F1F'); row.pack(anchor='w', pady=8)
        for name, caption in [("startup", "Запуск"), ("click", "Нажатие"), ("notification", "Уведомление"),
                              ("success", "Успех"), ("warning", "Предупреждение"), ("error", "Ошибка"),
                              ("usb_connect", "USB подключён"), ("usb_disconnect", "USB отключён")]:
            tk.Button(row, text=caption, bg='#303030', fg='white', bd=0, padx=8, pady=6,
                      command=lambda n=name: self.bitos.play_sound(n)).pack(side=tk.LEFT, padx=3, pady=3)

    def _toggle_sound(self):
        self.bitos.sound_manager.set_enabled(self.sound_var.get())
        self.bitos.sound_enabled = self.bitos.sound_manager.enabled
        self.desktop.notification_center.sound_enabled = self.bitos.sound_enabled
        self.desktop.taskbar.sound_btn.config(text="🔊" if self.bitos.sound_enabled else "🔇")

    def _create_sec_tab(self, parent):
        tk.Label(parent, text="Безопасность", font=('Segoe UI', 16, 'bold'),
                 bg='#1F1F1F', fg='white').pack(anchor='w', pady=(0, 16))
        tk.Label(parent, text="PIN-код защищает вход в BITOS. После 5 неверных попыток вход блокируется на 60 секунд.",
                 font=('Segoe UI', 9), bg='#1F1F1F', fg='#A0A0A0', wraplength=560, justify='left').pack(anchor='w')
        tk.Button(parent, text="🔑 Изменить PIN-код", bg='#0078D4', fg='white', bd=0,
                  padx=16, pady=8, command=self._change_pin).pack(anchor='w', pady=12)
        tk.Label(parent, text="PIN по умолчанию при первом запуске: 1234", font=('Segoe UI', 9),
                 bg='#1F1F1F', fg='#777777').pack(anchor='w')

    def _change_pin(self):
        dialog = tk.Toplevel(self.win); dialog.title("Изменение PIN-кода"); dialog.geometry("360x300")
        dialog.configure(bg="#1F1F1F"); dialog.transient(self.win); dialog.grab_set()
        entries = {}
        for key, label in [("old", "Текущий PIN"), ("new", "Новый PIN (4–8 цифр)"), ("confirm", "Подтвердите PIN")]:
            tk.Label(dialog, text=label, bg="#1F1F1F", fg="white").pack(anchor="w", padx=20, pady=(12,3))
            ent = tk.Entry(dialog, show="●", bg="#2D2D2D", fg="white", insertbackground="white", bd=0)
            ent.pack(fill=tk.X, padx=20, ipady=6); entries[key] = ent
        status = tk.Label(dialog, text="", bg="#1F1F1F", fg="#E81123"); status.pack(pady=8)
        def save():
            import hashlib
            old, new_pin, confirm = (entries[k].get().strip() for k in ("old", "new", "confirm"))
            path = os.path.join(self.bitos.system_paths["security"], "pin.hash")
            expected = hashlib.sha256("1234".encode()).hexdigest()
            try:
                if os.path.isfile(path): expected = Path(path).read_text(encoding="utf-8").strip()
            except Exception: pass
            if hashlib.sha256(old.encode()).hexdigest() != expected:
                status.config(text="Неверный текущий PIN"); return
            if not new_pin.isdigit() or not 4 <= len(new_pin) <= 8:
                status.config(text="Новый PIN должен содержать 4–8 цифр"); return
            if new_pin != confirm:
                status.config(text="PIN-коды не совпадают"); return
            try:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                Path(path).write_text(hashlib.sha256(new_pin.encode()).hexdigest(), encoding="utf-8")
                self.bitos.security.log_pin_change(self.bitos.current_user)
                self.bitos.play_sound("success"); dialog.destroy()
                messagebox.showinfo("Безопасность", "PIN-код изменён", parent=self.win)
            except Exception as exc: status.config(text=str(exc))
        tk.Button(dialog, text="Сохранить", bg="#0078D4", fg="white", bd=0, padx=18, pady=7,
                  command=save).pack(pady=8)

    def _create_updates_tab(self, parent):
        tk.Label(parent, text="Обновления BITOS", font=('Segoe UI', 16, 'bold'),
                 bg='#1F1F1F', fg='white').pack(anchor='w', pady=(0, 12))
        tk.Label(parent, text="Проверка запускается только по запросу пользователя. На уровнях 75% и 100% автоматических проверок нет.",
                 bg='#1F1F1F', fg='#A0A0A0', wraplength=560, justify='left').pack(anchor='w', pady=5)
        self.update_manager = UpdateManager(self.bitos)
        self.update_status = tk.Label(parent, text="Проверка ещё не выполнялась", bg='#1F1F1F', fg='#E0E0E0',
                                      font=('Segoe UI', 10), justify='left', wraplength=560)
        self.update_status.pack(anchor='w', pady=12)
        buttons = tk.Frame(parent, bg='#1F1F1F'); buttons.pack(anchor='w', pady=6)
        tk.Button(buttons, text="Проверить обновления", bg='#0078D4', fg='white', bd=0,
                  padx=14, pady=8, command=self._check_updates).pack(side=tk.LEFT, padx=4)
        self.download_btn = tk.Button(buttons, text="Скачать обновление", bg='#303030', fg='white', bd=0,
                                      padx=14, pady=8, state='disabled', command=self._download_update)
        self.download_btn.pack(side=tk.LEFT, padx=4)
        self.update_manager.status = self.update_manager._load_status()
        if self.update_manager.status.get("update_available"):
            self.update_status.config(text=f"Доступно обновление: {self.update_manager.status.get('latest_version')}")

    def _check_updates(self):
        self.update_status.config(text="Проверка обновлений…")
        self.update_manager.check_for_updates(self._on_update_checked)

    def _on_update_checked(self, available, version, url, notes, error):
        if error:
            self.update_status.config(text=f"Не удалось проверить обновления: {error}")
            return
        if available:
            self.update_status.config(text=f"Доступна версия {version}\n{notes or 'Описание отсутствует.'}")
            self.download_btn.config(state="normal")
            self.bitos.play_sound("notification")
        else:
            self.update_status.config(text=f"Установлена актуальная версия {self.bitos.version}.")
            self.download_btn.config(state="disabled")

    def _download_update(self):
        self.download_btn.config(state="disabled", text="Загрузка…")
        def progress(value, status):
            try: self.win.after(0, lambda: self.update_status.config(text=status))
            except Exception: pass
        def complete(ok, path, error):
            self.download_btn.config(state="normal", text="Скачать обновление")
            if ok:
                self.update_status.config(text=f"Обновление загружено: {path}")
                if messagebox.askyesno("Обновление", "Запустить установщик обновления?", parent=self.win):
                    self.update_manager.install_update()
            else:
                self.update_status.config(text=f"Ошибка загрузки: {error}")
        self.update_manager.download_update(progress, complete)

    def _create_sys_tab(self, parent):
        tk.Label(parent, text="О системе", font=('Segoe UI', 16, 'bold'),
                 bg='#1F1F1F', fg='white').pack(anchor='w', pady=(0, 16))
        workers = getattr(getattr(self.bitos, "task_manager", None), "_workers", 1)
        lines = [f"BITOS Версия: {self.bitos.version}", f"Сборка: {self.bitos.build}",
                 f"Пользователь: {self.bitos.current_user}",
                 f"Оптимизация: {self.ui.get_optimization_level()}%",
                 f"Потоки фоновых задач: до {workers}",
                 f"Запись логов: {'включена' if self.ui.logs_enabled else 'отключена'}",
                 f"Звуки приложения: {'включены' if self.bitos.sound_enabled else 'отключены'}"]
        info_card = tk.Frame(parent, bg='#252525', padx=16, pady=14)
        info_card.pack(fill=tk.X, pady=(0, 12))
        tk.Label(info_card, text="Сведения об этой системе", font=('Segoe UI', 11, 'bold'),
                 bg='#252525', fg='#FFFFFF').pack(anchor='w', pady=(0, 8))
        tk.Label(info_card, text="\n".join(lines), font=('Segoe UI', 10), bg='#252525',
                 fg='#D8D8D8', justify='left', anchor='w').pack(anchor='w')

        # Documentation actions are intentionally anchored to the bottom of the System tab.
        docs_bar = tk.Frame(parent, bg='#1F1F1F')
        docs_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(14, 0))
        tk.Label(docs_bar, text="Документация BITOS", font=('Segoe UI', 10, 'bold'),
                 bg='#1F1F1F', fg='#A8A8A8').pack(anchor='w', pady=(0, 8))
        buttons = tk.Frame(docs_bar, bg='#1F1F1F')
        buttons.pack(fill=tk.X)
        tk.Button(buttons, text="📘  Руководство пользователя", font=('Segoe UI', 10, 'bold'),
                 bg='#0078D4', fg='white', activebackground='#1689E8', activeforeground='white',
                 bd=0, padx=16, pady=10, cursor='hand2',
                 command=lambda: self._open_bitos_documentation('user')).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(buttons, text="🧩  API документация", font=('Segoe UI', 10, 'bold'),
                 bg='#303030', fg='white', activebackground='#414141', activeforeground='white',
                 bd=0, padx=16, pady=10, cursor='hand2',
                 command=lambda: self._open_bitos_documentation('api')).pack(side=tk.LEFT)

    def _open_bitos_documentation(self, doc_type='user'):
        'Show built-in BITOS user or developer documentation in a sectioned reader.'
        user_sections = [
            ('Начало работы', '''BITOS — рабочая среда с рабочим столом, системными окнами и BIP-приложениями.

Первый запуск
• Войдите под своей учётной записью. Если система впервые настроена и PIN не менялся, первоначальный PIN может быть 1234 — смените его в «Настройки → Безопасность».
• Используйте меню «Пуск» для запуска встроенных приложений и установленных BIP.
• Двойной щелчок по значку рабочего стола запускает соответствующий объект.
• Панель задач показывает открытые окна; выберите окно на панели, чтобы вернуться к нему.'''),
            ('Рабочий стол и меню «Пуск»', '''Рабочий стол
• Значки можно использовать для запуска системных объектов и приложений.
• Положение и масштаб значков настраиваются системой; доступные параметры зависят от сборки.
• Контекстные меню объектов могут содержать действия открытия, перемещения и удаления.

Меню «Пуск»
• Откройте меню «Пуск» с панели задач.
• Выберите встроенное приложение или установленный BIP.
• Если приложение не запускается, проверьте, установлено ли оно и доступен ли его главный файл.'''),
            ('Проводник и файлы', '''Проводник BITOS
• Используйте проводник для перехода по папкам, выбора файлов и выполнения файловых операций.
• Двойной щелчок по файлу запускает зарегистрированный обработчик BITOS, если расширение связано с установленным BIP. В противном случае используется системное открытие.
• Для форматов, требующих внешнего приложения, проверьте ассоциации файлов Windows.
• Удалённые через поддерживаемую функцию файлы могут попадать в корзину BITOS; проверьте корзину перед окончательным удалением.'''),
            ('Настройки: функции и производительность', '''Функции
• «Режим планшета» меняет масштабирование и плотность интерфейса для сенсорного управления.
• «Второй экран» позволяет выбрать режим часов или чёрного экрана.

Производительность
• Уровень оптимизации снижает визуальные эффекты и частоту фоновых операций.
• Чем выше процент оптимизации, тем меньше нагрузка, но тем меньше анимаций и автоматических обновлений интерфейса.
• При проблемах с плавностью попробуйте увеличить оптимизацию; при мощном компьютере можно выбрать качество.
• Значения и влияние отдельных режимов зависят от текущей сборки BITOS.'''),
            ('Настройки: оформление и звук', '''Оформление
• Выберите одну из встроенных тем.
• Настройте масштаб значков рабочего стола.
• Измените обои или создайте пользовательскую тему, если эти элементы доступны в сборке.

Звук
• Включите или отключите системные звуки BITOS независимо от звуков Windows.
• Используйте кнопки проверки, чтобы прослушать отдельные системные события.'''),
            ('Безопасность и PIN', '''• PIN-код используется для защиты входа в BITOS.
• Меняйте PIN в разделе «Настройки → Безопасность».
• Новый PIN должен содержать от 4 до 8 цифр и совпадать с подтверждением.
• После нескольких неверных попыток вход может временно блокироваться.
• Не оставляйте стандартный PIN и не сообщайте его другим пользователям.'''),
            ('Установка BIP и обновления', '''BIP — пакет приложения BITOS.
• Устанавливайте BIP только из доверенного источника.
• После установки приложение должно появиться в меню «Пуск» (если пакет добавляет ярлык).
• Если приложение не запускается, проверьте совместимость пакета, его главный файл и зависимости Python.
• Раздел «Обновления» позволяет проверить доступность обновлений BITOS; доступность сетевых функций зависит от соединения и сборки.'''),
            ('Устранение неполадок', '''Если окно зависло
• Подождите немного, особенно если выполняется файловая операция.
• Закройте приложение штатно; при необходимости завершите его через диспетчер задач.

Если файл открылся не тем приложением
• Проверьте, что нужный BIP установлен и объявляет обработчик расширения.
• Откройте файл из проводника BITOS, а не из внешнего Windows Explorer.
• Для внешнего проводника Windows нужны системные ассоциации расширений.

Если проблема повторяется
• Зафиксируйте название приложения, путь к файлу и действия перед ошибкой.
• Не удаляйте системные папки и конфигурации вручную без резервной копии.'''),
        ]
        api_sections = [
            ('Обзор архитектуры', '''BITOS — Python-приложение с интерфейсом Tkinter.

Основные части исходного дерева
• bitos/main.pyw — точка запуска оболочки.
• bitos/server/ — системная логика и сервисы (ядро, безопасность, обновления, фоновые задачи).
• bitos/ui/ — окна и интерфейс рабочего стола.
• bitos/system/Apps/ — установленные BIP-пакеты.
• bitos/system/Config/ — пользовательские и системные настройки.

Рекомендация: изучайте существующий код и используемые интерфейсы перед добавлением новой функции. Не дублируйте системный сервис, если в проекте уже есть менеджер для этой задачи.'''),
            ('Создание BIP-приложения', '''BIP — текстовый пакет с разделами метаданных и кода. Текущий установщик разбирает строки метаданных формата key: value и записывает код в главный файл приложения.

Минимальная структура пакета:
---METADATA---
id: ExampleApp
name: Example App
version: 1.0
icon: 🧩
main: main.pyw
---CODE---
# Python code

Требования к полям
• id — уникальный идентификатор приложения; допустимы латинские буквы, цифры, _, . и -.
• name — имя, показываемое пользователю.
• version — версия приложения.
• icon — значок приложения.
• main — относительный путь к главному файлу внутри пакета.

Путь main не должен выходить за пределы каталога приложения. Используйте относительные пути и не размещайте секреты в исходном коде пакета.'''),
            ('Жизненный цикл BIP', '''• Установщик читает пакет .bip, извлекает метаданные и код, создаёт каталог приложения и package.json.
• Главный файл запускается через текущий интерпретатор Python.
• Приложение может создавать собственные окна Tkinter.
• Для корректного завершения сохраняйте состояние и освобождайте ресурсы.

Пакет устанавливается в Apps/<id>. Не рассчитывайте на запись в каталоги Windows или за пределы каталога приложения без явного обоснования.'''),
            ('Регистрация расширений файлов', '''Если BITOS/BIP installer в используемой версии поддерживает file_handlers, обработчик задаётся в метаданных, например:

file_handlers: .docx=words.open;.xlsx=table.open;.pdf=pdf.open

Смысл записи: расширение файла → команда BIP. Формат команд и способ передачи аргументов должны совпадать с реализацией установленной версии BITOS. При обработке файла приложение получает путь и команду запуска, а затем открывает документ соответствующим модулем.

Перед публикацией пакета обязательно проверьте реальный сценарий двойного щелчка в проводнике BITOS. Не предполагайте, что регистрация BIP автоматически меняет ассоциации внешнего Windows Explorer.'''),
            ('Модификация операционной системы', '''Безопасный порядок работы
1. Сделайте резервную копию исходников и конфигураций.
2. Изучите точку входа и связанные классы в bitos/ui/ и bitos/server/.
3. Добавляйте функцию в подходящий модуль, избегая монолитных изменений.
4. Сохраняйте совместимость с существующими настройками и BIP-пакетами.
5. Добавьте обработку ошибок и понятное сообщение пользователю.
6. Проверьте запуск, штатное закрытие и повторный запуск.
7. Подготовьте patch только с изменёнными файлами и краткий changelog.

Не меняйте структуру конфигураций или API без миграции старых данных.'''),
            ('UI и системные сервисы', '''UI
• Используйте существующие окна и общие стили BITOS, где это возможно.
• Не блокируйте Tkinter mainloop длительными операциями: сеть, большие файлы и вычисления должны выполняться вне UI-потока с безопасным возвратом результата в интерфейс.
• Для долгих операций показывайте состояние и возможность отмены, если отмена реализуема.

Системные сервисы
• Перед добавлением нового менеджера проверьте bitos/server/.
• Учитывайте корректное завершение фоновых потоков при выходе.
• Не храните пользовательские настройки в исходниках; используйте папку Config.'''),
            ('Тестирование и выпуск', '''Минимальный чек-лист
• BITOS стартует на чистом запуске.
• Основные окна открываются и закрываются.
• Существующие настройки сохраняются и читаются.
• BIP устанавливается, отображается в меню и запускается.
• Ошибочный пакет не повреждает уже установленные приложения.
• Проверены пути с пробелами и кириллицей.
• Проверены действия пользователя, повторный запуск и отсутствие зависания UI.

В issue/описании изменения укажите: сборку BITOS, шаги воспроизведения, ожидаемый и фактический результат, лог/traceback (если доступен).'''),
        ]
        sections = user_sections if doc_type == 'user' else api_sections
        title = 'Руководство пользователя BITOS' if doc_type == 'user' else 'BITOS — API и руководство разработчика'
        win = tk.Toplevel(self.win)
        win.title(title)
        win.geometry('980x680')
        win.minsize(760, 520)
        win.configure(bg='#181818')
        try:
            win.transient(self.win)
        except Exception:
            pass

        header = tk.Frame(win, bg='#181818', padx=20, pady=16)
        header.pack(fill=tk.X)
        tk.Label(header, text=title, font=('Segoe UI', 17, 'bold'),
                 bg='#181818', fg='#FFFFFF').pack(anchor='w')
        tk.Label(header, text=('Справочник по работе в BITOS.' if doc_type == 'user' else
                              'Практическое руководство по расширению BITOS и разработке BIP.'),
                 font=('Segoe UI', 10), bg='#181818', fg='#AFAFAF').pack(anchor='w', pady=(4, 0))

        body = tk.Frame(win, bg='#181818')
        body.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))
        nav = tk.Frame(body, bg='#222222', width=245)
        nav.pack(side=tk.LEFT, fill=tk.Y)
        nav.pack_propagate(False)
        content = tk.Frame(body, bg='#202020')
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(12, 0))
        text = scrolledtext.ScrolledText(content, wrap=tk.WORD, bg='#202020', fg='#E6E6E6',
                                         insertbackground='white', relief=tk.FLAT, bd=0,
                                         padx=20, pady=18, font=('Segoe UI', 10),
                                         spacing1=2, spacing3=5)
        text.pack(fill=tk.BOTH, expand=True)
        text.tag_configure('heading', font=('Segoe UI', 14, 'bold'), foreground='#79C8F2', spacing1=10, spacing3=8)
        text.tag_configure('bullet', lmargin1=14, lmargin2=26, spacing1=1, spacing3=3)
        text.tag_configure('code', font=('Consolas', 10), foreground='#A8D7A8', lmargin1=12, lmargin2=12)
        text.configure(state=tk.DISABLED)

        def show_section(index):
            for i, (name, _) in enumerate(sections):
                nav_buttons[i].configure(bg='#353535' if i == index else '#222222',
                                         fg='#FFFFFF' if i == index else '#D0D0D0')
            text.configure(state=tk.NORMAL)
            text.delete('1.0', tk.END)
            name, body_text = sections[index]
            text.insert(tk.END, name + '\n', 'heading')
            for line in body_text.splitlines():
                if line.startswith('• '):
                    text.insert(tk.END, line + '\n', 'bullet')
                elif line.startswith('file_handlers:') or line.startswith('---') or line.startswith('id:') or line.startswith('name:') or line.startswith('version:') or line.startswith('icon:') or line.startswith('main:') or line.startswith('# Python'):
                    text.insert(tk.END, line + '\n', 'code')
                else:
                    text.insert(tk.END, line + '\n')
            text.configure(state=tk.DISABLED)
            text.yview_moveto(0)

        nav_buttons = []
        for i, (name, _) in enumerate(sections):
            b = tk.Button(nav, text=name, anchor='w', justify='left', wraplength=215,
                          font=('Segoe UI', 9), bg='#222222', fg='#D0D0D0',
                          activebackground='#353535', activeforeground='white',
                          bd=0, padx=14, pady=8, cursor='hand2',
                          command=lambda idx=i: show_section(idx))
            b.pack(fill=tk.X, padx=5, pady=2)
            nav_buttons.append(b)
        footer = tk.Frame(win, bg='#181818')
        footer.pack(fill=tk.X, padx=16, pady=(0, 12))
        tk.Label(footer, text=f'{len(sections)} разделов · Документация встроена в BITOS',
                 bg='#181818', fg='#888888', font=('Segoe UI', 9)).pack(side=tk.LEFT)
        tk.Button(footer, text='Закрыть', bg='#303030', fg='white', bd=0,
                  padx=18, pady=7, command=win.destroy).pack(side=tk.RIGHT)
        show_section(0)


# ============================================================================
# 10. КОРЗИНА (TRASH WINDOW)
# ============================================================================

class TrashWindow:
    """Окно корзины: просмотр, очистка, восстановление"""
    def __init__(self, parent, bitos):
        self.win = tk.Toplevel(parent)
        self.win.title("Корзина")
        self.win.geometry("640x420")
        self.win.configure(bg='#1F1F1F')
        self.bitos = bitos
        self.tm = TrashManager(bitos)
        
        top = tk.Frame(self.win, bg='#1F1F1F')
        top.pack(fill=tk.X, padx=10, pady=8)
        
        tk.Button(top, text="Очистить корзину", bg='#E81123', fg='white', bd=0, padx=12, pady=4,
                  command=self.clear).pack(side=tk.LEFT)
        tk.Button(top, text="Восстановить", bg='#0078D4', fg='white', bd=0, padx=12, pady=4,
                  command=self.restore).pack(side=tk.LEFT, padx=6)
                  
        self.listb = tk.Listbox(self.win, bg='#2D2D2D', fg='white', bd=0, font=('Segoe UI', 9))
        self.listb.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        self.load()

    def load(self):
        self.listb.delete(0, tk.END)
        for it in self.tm.get_trash_items():
            self.listb.insert(tk.END, it['trash_name'])

    def clear(self):
        if messagebox.askyesno("Очистить", "Удалить все файлы из корзины навсегда?", parent=self.win):
            self.tm.empty_trash()
            self.load()

    def restore(self):
        sel = self.listb.curselection()
        if not sel: return
        name = self.listb.get(sel[0])
        ok, res = self.tm.restore_item(name)
        if ok:
            messagebox.showinfo("Восстановление", f"Файл восстановлен:\n{res}", parent=self.win)
            self.load()
        else:
            messagebox.showerror("Ошибка", res, parent=self.win)
