import os
import json

class UIManager:
    """
    Единый менеджер темы, размеров, шрифтов, режима планшета
    и оптимизации производительности под слабые ПК.
    """
    LEVELS = (0, 25, 50, 75, 100)

    def __init__(self, bitos=None):
        self.bitos = bitos
        self.touch_mode = False
        self.second_screen_mode = "clock"
        self.optimization_level = 0
        if bitos and hasattr(bitos, "system_paths"):
            self.config_dir = bitos.system_paths["config"]
        else:
            package_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.config_dir = os.path.join(package_root, "system", "Config")
        self.perf_file = os.path.join(self.config_dir, "performance.json")
        os.makedirs(self.config_dir, exist_ok=True)
        self.load()

    def load(self):
        if os.path.isfile(self.perf_file):
            try:
                with open(self.perf_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.touch_mode = bool(data.get("touch_mode", False))
                mode = str(data.get("second_screen_mode", "clock"))
                self.second_screen_mode = mode if mode in ("clock", "black") else "clock"
                raw = int(data.get("optimization_level", 0))
                self.optimization_level = min(self.LEVELS, key=lambda x: abs(x - raw))
            except Exception:
                self.touch_mode = False
                self.second_screen_mode = "clock"
                self.optimization_level = 0
        else:
            self.save()

    def save(self):
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            tmp_file = self.perf_file + ".tmp"
            data = {
                "touch_mode": self.touch_mode,
                "second_screen_mode": self.second_screen_mode,
                "optimization_level": self.optimization_level,
            }
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_file, self.perf_file)
        except Exception as e:
            mgr = getattr(self.bitos, "error_manager", None)
            if mgr and self.logs_enabled:
                mgr._log_error("UIManager.save", str(e))

    def set_touch_mode(self, enabled: bool):
        self.touch_mode = bool(enabled)
        self.save()

    def set_second_screen_mode(self, mode: str):
        if mode in ("clock", "black"):
            self.second_screen_mode = mode
            self.save()

    def set_optimization_level(self, level: int):
        try:
            numeric = int(round(float(level) / 25.0) * 25)
        except (TypeError, ValueError):
            numeric = 0
        self.optimization_level = min(self.LEVELS, key=lambda x: abs(x - max(0, min(100, numeric))))
        self.save()
        return self.optimization_level

    def get_optimization_level(self):
        return self.optimization_level

    @property
    def animations_enabled(self):
        return self.optimization_level < 50

    @property
    def start_menu_animations_enabled(self):
        return self.optimization_level < 50

    @property
    def notification_popups_enabled(self):
        return self.optimization_level < 75

    @property
    def gradients_enabled(self):
        return self.optimization_level < 50

    @property
    def shadows_enabled(self):
        return self.optimization_level == 0

    @property
    def wallpaper_enabled(self):
        # Only the 100% survival profile removes wallpaper entirely.
        return self.optimization_level < 100

    @property
    def widgets_enabled(self):
        return self.optimization_level < 75

    @property
    def logs_enabled(self):
        return self.optimization_level < 100

    @property
    def automatic_checks_enabled(self):
        return self.optimization_level < 75

    @property
    def fast_timers_enabled(self):
        return self.optimization_level < 75

    @property
    def clock_interval_ms(self):
        if self.optimization_level == 100:
            return None
        if self.optimization_level == 75:
            return 60_000
        return 1_000

    @property
    def system_check_interval_ms(self):
        if self.optimization_level >= 75:
            return None
        if self.optimization_level == 50:
            return 10_000
        return 1_000

    @property
    def autosave_interval_ms(self):
        return {0: 10_000, 25: 15_000, 50: 30_000, 75: None, 100: None}[self.optimization_level]

    @property
    def log_flush_interval(self):
        return 5.0 if self.optimization_level == 50 else 0.0

    @property
    def wallpaper_scale(self):
        return {0: 1.0, 25: 1.0, 50: 0.5, 75: 0.25, 100: 0.0}[self.optimization_level]

    @property
    def worker_limit(self):
        return {0: 4, 25: 3, 50: 2, 75: 1, 100: 1}[self.optimization_level]

    def get_profile_description(self, level=None):
        level = self.optimization_level if level is None else int(level)
        return {
            0: "0% — Максимальное качество: все анимации, градиенты, тени и обои; часы обновляются каждую секунду.",
            25: "25% — Комфорт: анимация только важных элементов, уведомления без задержки, градиенты без теней.",
            50: "50% — Средний: анимации и тени отключены, системные проверки раз в 10 секунд, обои в половинном разрешении, логи пакетно раз в 5 секунд.",
            75: "75% — Высокая: таймер часов раз в минуту, виджеты и всплывающие уведомления отключены, обои снижены до четверти разрешения, автоматические проверки остановлены.",
            100: "100% — Режим выживания: только статичный интерфейс и ручные действия; без обоев, виджетов, фоновых проверок и записи логов.",
        }.get(level, "")

    def get_sizes(self):
        """Размеры элементов интерфейса в зависимости от режима планшета"""
        if self.touch_mode:
            return {
                'taskbar_height': 48,
                'start_btn_width': 56,
                'grid_step': 148,
                'icon_size': 136,
                'icon_font_size': 12,
                'start_w': 720,
                'start_h': 620,
                'touch_mode': True
            }
        return {
            'taskbar_height': 40,
            'start_btn_width': 44,
            'grid_step': 132,
            'icon_size': 120,
            'icon_font_size': 11,
            'start_w': 640,
            'start_h': 600,
            'touch_mode': False
        }

    def get_fonts(self):
        """Шрифты интерфейса Windows 10 (Segoe UI)"""
        return {
            'title_bold': ('Segoe UI', 16, 'bold'),
            'header': ('Segoe UI', 14, 'bold'),
            'sub': ('Segoe UI', 11, 'bold'),
            'main': ('Segoe UI', 10),
            'main_bold': ('Segoe UI', 10, 'bold'),
            'small': ('Segoe UI', 9),
            'clock_splash': ('Segoe UI', 64, 'bold'),
            'time_large': ('Segoe UI', 44, 'bold'),
            'mono': ('Consolas', 10)
        }

    def get_colors(self, theme_name="Базовая"):
        """Цветовые палитры BITOS в строгом плоском стиле Windows 10 1909"""
        themes = {
            "Базовая": {
                'name': 'Базовая',
                'bg': '#1E1E1E',
                'fg': '#FFFFFF',
                'accent': '#0078D4',
                'accent_hover': '#106EBE',
                'accent_pressed': '#005A9E',
                'taskbar_bg': '#101010',
                'taskbar_fg': '#FFFFFF',
                'taskbar_hover': '#2B2B2B',
                'taskbar_indicator': '#0078D4',
                'canvas_bg': '#1A1A1A',
                'icon_fg': '#FFFFFF',
                'widget_bg': '#252525',
                'widget_fg': '#FFFFFF',
                'window_bg': '#1F1F1F',
                'item_hover': '#2D2D2D',
                'item_selected': '#0078D4',
                'border': '#333333',
                'close_hover': '#E81123',
                'subtext': '#A0A0A0'
            },
            "Техно": {
                'name': 'Техно',
                'bg': '#0A0A0A',
                'fg': '#00FF00',
                'accent': '#00FF00',
                'accent_hover': '#00CC00',
                'accent_pressed': '#009900',
                'taskbar_bg': '#050505',
                'taskbar_fg': '#00FF00',
                'taskbar_hover': '#151515',
                'taskbar_indicator': '#00FF00',
                'canvas_bg': '#080808',
                'icon_fg': '#00FF00',
                'widget_bg': '#101010',
                'widget_fg': '#00FF00',
                'window_bg': '#0E0E0E',
                'item_hover': '#1F2A1F',
                'item_selected': '#005500',
                'border': '#004400',
                'close_hover': '#E81123',
                'subtext': '#00AA00'
            },
            "Эко": {
                'name': 'Эко',
                'bg': '#0F2A1A',
                'fg': '#FFFFFF',
                'accent': '#2ECC71',
                'accent_hover': '#27AE60',
                'accent_pressed': '#1E8449',
                'taskbar_bg': '#0A1C11',
                'taskbar_fg': '#FFFFFF',
                'taskbar_hover': '#153A23',
                'taskbar_indicator': '#2ECC71',
                'canvas_bg': '#0E2417',
                'icon_fg': '#FFFFFF',
                'widget_bg': '#143823',
                'widget_fg': '#FFFFFF',
                'window_bg': '#112F1E',
                'item_hover': '#1D4D31',
                'item_selected': '#27AE60',
                'border': '#1B472C',
                'close_hover': '#E81123',
                'subtext': '#9EDAB6'
            },
            "Космо": {
                'name': 'Космо',
                'bg': '#0A0A1A',
                'fg': '#87CEEB',
                'accent': '#00A4EF',
                'accent_hover': '#0082BD',
                'accent_pressed': '#005F8A',
                'taskbar_bg': '#05050F',
                'taskbar_fg': '#87CEEB',
                'taskbar_hover': '#14142B',
                'taskbar_indicator': '#00A4EF',
                'canvas_bg': '#070714',
                'icon_fg': '#87CEEB',
                'widget_bg': '#101026',
                'widget_fg': '#87CEEB',
                'window_bg': '#0D0D21',
                'item_hover': '#18183B',
                'item_selected': '#006B9E',
                'border': '#1A1A40',
                'close_hover': '#E81123',
                'subtext': '#6FA3C7'
            }
        }
        user_theme_file = os.path.join(self.config_dir, "user_themes.json")
        try:
            with open(user_theme_file, "r", encoding="utf-8") as f:
                custom_themes = json.load(f)
            if isinstance(custom_themes, dict):
                themes.update(custom_themes)
        except Exception:
            pass
        return themes.get(theme_name, themes["Базовая"])
