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
