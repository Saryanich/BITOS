# -*- coding: utf-8 -*-
"""PyQt6-backed compatibility layer for the existing BITOS widget API.

The application keeps its existing widget construction and callbacks while every
visible control, timer and drawing operation is handled by Qt.
"""
from __future__ import annotations

import os
import re
import sys
import math
import itertools
from types import SimpleNamespace

from PyQt6.QtCore import Qt, QTimer, QObject, QEvent, QPointF, QRectF, pyqtSignal, QThread
from PyQt6.QtGui import (
    QColor, QFont, QFontMetricsF, QPainter, QPen, QBrush, QPixmap, QImage,
    QCursor, QTextCursor, QPolygonF
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QDialog, QWidget, QLabel as QLabelQt,
    QPushButton, QLineEdit, QTextEdit, QPlainTextEdit, QFrame as QFrameQt,
    QCheckBox, QRadioButton, QSlider, QScrollBar, QProgressBar, QComboBox,
    QTabWidget, QTreeWidget, QTreeWidgetItem, QMenu as QMenuQt,
    QVBoxLayout, QHBoxLayout, QGridLayout, QBoxLayout, QSizePolicy,
    QMessageBox, QFileDialog, QColorDialog, QStyleFactory, QAbstractItemView
)

_default_root = None
_app = None
_loop_running = False
_root_windows = set()
_global_bindings = {}
_item_ids = itertools.count(1)
_after_ids = itertools.count(1)


class TclError(RuntimeError):
    pass


def _ensure_app():
    global _app
    current = QApplication.instance()
    if current is None:
        current = QApplication(sys.argv[:1])
        current.setQuitOnLastWindowClosed(False)
        try:
            current.setStyle(QStyleFactory.create("Fusion"))
        except Exception:
            pass
    else:
        current.setQuitOnLastWindowClosed(False)
    _app = current
    return current


class _Dispatcher(QObject):
    invoke = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.invoke.connect(self._run, Qt.ConnectionType.QueuedConnection)

    def _run(self, payload):
        delay, callback = payload
        QTimer.singleShot(max(0, int(delay)), callback)


_dispatcher = None


def _dispatch_after(delay, callback):
    global _dispatcher
    app = _ensure_app()
    try:
        if QThread.currentThread() == app.thread():
            return QTimer.singleShot(max(0, int(delay)), callback)
    except Exception:
        pass
    if _dispatcher is None:
        _dispatcher = _Dispatcher()
        _dispatcher.moveToThread(app.thread())
    _dispatcher.invoke.emit((delay, callback))
    return None


def _parent_widget(parent):
    if parent is None:
        return None
    if isinstance(parent, QMainWindow):
        return parent.centralWidget()
    return parent


def _root_of(parent):
    current = parent
    while current is not None:
        if getattr(current, "_tk_is_root", False):
            return current
        try:
            current = current.parentWidget()
        except Exception:
            break
    return _default_root


def _font_from(value, fallback=None):
    if isinstance(value, QFont):
        return QFont(value)
    if isinstance(value, (tuple, list)):
        family = str(value[0]) if value else "Segoe UI"
        size = int(value[1]) if len(value) > 1 and isinstance(value[1], (int, float)) else 10
        weight = QFont.Weight.Bold if any(str(x).lower() == "bold" for x in value[2:]) else QFont.Weight.Normal
        font = QFont(family, size, weight)
        font.setItalic(any(str(x).lower() == "italic" for x in value[2:]))
        return font
    if isinstance(value, str):
        return QFont(value, 10)
    return QFont(fallback or "Segoe UI", 10)


def _event_data(widget, event):
    try:
        pos = event.position().toPoint()
    except Exception:
        try:
            pos = event.pos()
        except Exception:
            pos = QPointF(0, 0)
    try:
        global_pos = widget.mapToGlobal(pos)
        gx, gy = global_pos.x(), global_pos.y()
    except Exception:
        gx, gy = 0, 0
    button = getattr(event, "button", lambda: Qt.MouseButton.NoButton)()
    buttons = getattr(event, "buttons", lambda: Qt.MouseButton.NoButton)()
    key = getattr(event, "key", lambda: 0)()
    key_names = {
        Qt.Key.Key_Return: "Return", Qt.Key.Key_Enter: "Return",
        Qt.Key.Key_Escape: "Escape", Qt.Key.Key_Tab: "Tab",
        Qt.Key.Key_Backspace: "BackSpace", Qt.Key.Key_Delete: "Delete",
        Qt.Key.Key_Space: "space"
    }
    keysym = key_names.get(key, "")
    if not keysym and key:
        try:
            keysym = chr(key)
        except Exception:
            keysym = str(key)
    try:
        event_size = event.size()
        event_width, event_height = int(event_size.width()), int(event_size.height())
    except Exception:
        event_width, event_height = int(widget.width()), int(widget.height())
    return SimpleNamespace(
        x=int(pos.x()), y=int(pos.y()), x_root=int(gx), y_root=int(gy),
        width=event_width, height=event_height,
        widget=widget, keysym=keysym, keycode=key,
        num=1 if (button == Qt.MouseButton.LeftButton or buttons & Qt.MouseButton.LeftButton) else 3 if button == Qt.MouseButton.RightButton else 0,
        delta=getattr(event, "angleDelta", lambda: QPointF(0, 0))().y()
    )


_EVENT_TYPES = {
    "<Button-1>": QEvent.Type.MouseButtonPress,
    "<Button-3>": QEvent.Type.MouseButtonPress,
    "<ButtonRelease-1>": QEvent.Type.MouseButtonRelease,
    "<B1-Motion>": QEvent.Type.MouseMove,
    "<Motion>": QEvent.Type.MouseMove,
    "<Double-1>": QEvent.Type.MouseButtonDblClick,
    "<Double-Button-1>": QEvent.Type.MouseButtonDblClick,
    "<Enter>": QEvent.Type.Enter,
    "<Leave>": QEvent.Type.Leave,
    "<Configure>": QEvent.Type.Resize,
    "<FocusIn>": QEvent.Type.FocusIn,
    "<FocusOut>": QEvent.Type.FocusOut,
    "<KeyRelease>": QEvent.Type.KeyRelease,
    "<Return>": QEvent.Type.KeyPress,
    "<Escape>": QEvent.Type.KeyPress,
    "<Control-s>": QEvent.Type.KeyPress,
    "<Control-S>": QEvent.Type.KeyPress,
}


class Misc:
    def _init_misc(self, parent=None, is_root=False):
        self._tk_parent = parent
        self.master = parent
        self._root_owner = self if is_root else _root_of(parent)
        self._tk_is_root = bool(is_root)
        self._tk_bindings = {}
        self._tk_after = {}
        self._tk_options = {}
        self._tk_visible = False
        try:
            self.setMouseTracking(True)
            self.installEventFilter(self)
        except Exception:
            pass

    def after(self, milliseconds, callback=None, *args):
        if callback is None:
            callback = lambda: None
        elif args:
            original_callback = callback
            callback = lambda: original_callback(*args)
        timer_id = next(_after_ids)
        holder = {"cancelled": False}

        def invoke():
            if holder["cancelled"]:
                return
            self._tk_after.pop(timer_id, None)
            try:
                if self.winfo_exists():
                    callback()
            except RuntimeError:
                pass
            except Exception as exc:
                try:
                    root = _root_of(self)
                    if root:
                        root.report_callback_exception(type(exc), exc, exc.__traceback__)
                except Exception:
                    pass

        self._tk_after[timer_id] = holder
        _dispatch_after(milliseconds, invoke)
        return timer_id

    def after_cancel(self, timer_id):
        holder = self._tk_after.pop(timer_id, None)
        if holder:
            holder["cancelled"] = True

    def destroy(self):
        for holder in list(getattr(self, "_tk_after", {}).values()):
            holder["cancelled"] = True
        try:
            self._deleted = True
            self.hide()
            if self._tk_is_root:
                _root_windows.discard(self)
                self.deleteLater()
                _dispatch_after(0, _maybe_quit)
            else:
                self.deleteLater()
        except RuntimeError:
            pass

    def winfo_exists(self):
        try:
            return not self.isHidden() and not self._deleted
        except Exception:
            try:
                return self.isVisible()
            except Exception:
                return False

    def winfo_children(self):
        try:
            return [x for x in self.findChildren(QWidget, options=Qt.FindChildOption.FindDirectChildrenOnly)]
        except Exception:
            return []

    def winfo_parent(self):
        p = self.parentWidget()
        return str(id(p)) if p else ""

    def iconbitmap(self, *args, **kwargs):
        return None

    def grid_rowconfigure(self, *args, **kwargs):
        return None

    def grid_columnconfigure(self, *args, **kwargs):
        return None

    rowconfigure = grid_rowconfigure
    columnconfigure = grid_columnconfigure

    def winfo_toplevel(self):
        root = _root_of(self)
        return root if root else self.window()

    def winfo_screenwidth(self):
        screen = _ensure_app().primaryScreen()
        return screen.availableGeometry().width() if screen else 1024

    def winfo_screenheight(self):
        screen = _ensure_app().primaryScreen()
        return screen.availableGeometry().height() if screen else 768

    def winfo_width(self):
        return self.width()

    def winfo_height(self):
        return self.height()

    def winfo_x(self):
        return self.x()

    def winfo_y(self):
        return self.y()

    def winfo_rootx(self):
        return self.mapToGlobal(QPointF(0, 0).toPoint()).x()

    def winfo_rooty(self):
        return self.mapToGlobal(QPointF(0, 0).toPoint()).y()

    def winfo_containing(self, x, y):
        return _ensure_app().widgetAt(int(x), int(y))

    def bind(self, sequence, callback, add=None):
        self._tk_bindings.setdefault(sequence, [])
        if not add:
            self._tk_bindings[sequence] = []
        self._tk_bindings[sequence].append(callback)
        return str(id(callback))

    def bind_all(self, sequence, callback, add=None):
        _global_bindings.setdefault(sequence, [])
        if not add:
            _global_bindings[sequence] = []
        _global_bindings[sequence].append(callback)
        return str(id(callback))

    def unbind_all(self, sequence):
        _global_bindings.pop(sequence, None)

    def eventFilter(self, watched, event):
        event_type = event.type()
        data = _event_data(self, event)
        for sequence, callbacks in list(getattr(self, "_tk_bindings", {}).items()):
            expected = _EVENT_TYPES.get(sequence)
            if expected != event_type:
                continue
            if sequence == "<Button-3>" and data.num != 3:
                continue
            if sequence == "<Button-1>" and data.num != 1:
                continue
            if sequence in ("<Return>", "<Escape>"):
                wanted = "Return" if sequence == "<Return>" else "Escape"
                if data.keysym != wanted:
                    continue
            if sequence in ("<Control-s>", "<Control-S>"):
                modifiers = getattr(event, "modifiers", lambda: Qt.KeyboardModifier.NoModifier)()
                if data.keysym.lower() != "s" or not (modifiers & Qt.KeyboardModifier.ControlModifier):
                    continue
            for callback in list(callbacks):
                try:
                    callback(data)
                except Exception as exc:
                    root = _root_of(self)
                    if root:
                        root.report_callback_exception(type(exc), exc, exc.__traceback__)
        return False

    def pack(self, **options):
        parent = _parent_widget(self.parentWidget())
        if parent is None:
            return
        layout = parent.layout()
        side = options.get("side", "top")
        if layout is None:
            layout = QHBoxLayout() if side in ("left", "right") else QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            parent.setLayout(layout)
        # Keep the direction selected by the first packed child. Reversing a
        # populated Qt layout for each Tk side= argument would reorder every widget.
        padx, pady = options.get("padx", 0), options.get("pady", 0)
        try:
            if isinstance(padx, (tuple, list)):
                left, right = int(padx[0]), int(padx[1])
            else:
                left = right = int(padx)
            if isinstance(pady, (tuple, list)):
                top, bottom = int(pady[0]), int(pady[1])
            else:
                top = bottom = int(pady)
            self.setContentsMargins(left, top, right, bottom)
        except Exception:
            pass
        fill = options.get("fill")
        expand = bool(options.get("expand"))
        horizontal_policy = QSizePolicy.Policy.Expanding if fill in ("both", "x") else QSizePolicy.Policy.Preferred
        vertical_policy = QSizePolicy.Policy.Expanding if fill in ("both", "y") else QSizePolicy.Policy.Preferred
        if expand:
            if layout.direction() == QBoxLayout.Direction.LeftToRight:
                horizontal_policy = QSizePolicy.Policy.Expanding
            else:
                vertical_policy = QSizePolicy.Policy.Expanding
        self.setSizePolicy(horizontal_policy, vertical_policy)
        anchor = options.get("anchor")
        alignment = Qt.AlignmentFlag(0)
        if anchor in ("w", "nw", "sw"):
            alignment |= Qt.AlignmentFlag.AlignLeft
        elif anchor in ("e", "ne", "se"):
            alignment |= Qt.AlignmentFlag.AlignRight
        if anchor in ("n", "nw", "ne"):
            alignment |= Qt.AlignmentFlag.AlignTop
        elif anchor in ("s", "sw", "se"):
            alignment |= Qt.AlignmentFlag.AlignBottom
        stretch = 1 if expand else 0
        if side in ("right", "bottom"):
            layout.insertWidget(0, self, stretch, alignment)
        else:
            layout.addWidget(self, stretch, alignment)
        self._show_parent()

    def grid(self, **options):
        parent = _parent_widget(self.parentWidget())
        if parent is None:
            return
        layout = parent.layout()
        if not isinstance(layout, QGridLayout):
            layout = QGridLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            parent.setLayout(layout)
        row, col = int(options.get("row", 0)), int(options.get("column", 0))
        rowspan, colspan = int(options.get("rowspan", 1)), int(options.get("columnspan", 1))
        sticky = str(options.get("sticky", ""))
        alignment = Qt.AlignmentFlag(0)
        if "w" in sticky: alignment |= Qt.AlignmentFlag.AlignLeft
        if "e" in sticky: alignment |= Qt.AlignmentFlag.AlignRight
        if "n" in sticky: alignment |= Qt.AlignmentFlag.AlignTop
        if "s" in sticky: alignment |= Qt.AlignmentFlag.AlignBottom
        layout.addWidget(self, row, col, rowspan, colspan, alignment)
        self._show_parent()

    def place(self, **options):
        parent = self.parentWidget()
        if parent is None:
            return
        x, y = int(options.get("x", 0)), int(options.get("y", 0))
        w, h = options.get("width"), options.get("height")
        self.move(x, y)
        if w is not None or h is not None:
            self.resize(int(w or self.width()), int(h or self.height()))
        self.show()
        self._show_parent()

    def place_forget(self):
        self.hide()

    def pack_forget(self):
        try:
            if self.parentWidget() and self.parentWidget().layout():
                self.parentWidget().layout().removeWidget(self)
            self.hide()
        except Exception:
            pass

    grid_forget = pack_forget

    def pack_propagate(self, value=True):
        if not value:
            self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    grid_propagate = pack_propagate

    def focus_set(self):
        self.setFocus()

    focus_force = focus_set

    def grab_set(self):
        try:
            self.window().setModal(True)
            self.window().raise_()
            self.window().activateWindow()
        except Exception:
            pass

    def grab_release(self):
        try:
            self.window().setModal(False)
        except Exception:
            pass

    def update(self):
        try:
            if self._tk_is_root:
                self.repaint()
                _ensure_app().processEvents()
            else:
                QWidget.update(self)
        except Exception:
            pass

    def update_idletasks(self):
        try:
            _ensure_app().processEvents()
        except Exception:
            pass

    def _show_parent(self):
        root = _root_of(self)
        if root and not root.isVisible():
            root.show()
        try:
            if isinstance(self.window(), QDialog) and self.window() is not root and not self.window().isVisible():
                self.window().show()
        except Exception:
            pass

    def _apply_options(self, options):
        self._tk_options.update(options)
        bg = options.get("bg", options.get("background"))
        fg = options.get("fg", options.get("foreground"))
        font = options.get("font")
        state = options.get("state")
        cursor = options.get("cursor")
        if font is not None:
            try: self.setFont(_font_from(font))
            except Exception: pass
        if state is not None:
            try: self.setEnabled(str(state).lower() not in ("disabled",))
            except Exception: pass
        if cursor:
            try:
                self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor if cursor == "hand2" else Qt.CursorShape.ArrowCursor))
            except Exception:
                pass
        css = []
        if bg:
            css.append("background-color: " + str(bg) + ";")
        if fg:
            css.append("color: " + str(fg) + ";")
        if options.get("bd") == 0 or options.get("borderwidth") == 0:
            css.append("border: 0px;")
        if isinstance(self, QPushButton):
            css.append("padding: %spx %spx;" % (int(options.get("pady", 5)), int(options.get("padx", 8))))
            if options.get("activebackground"):
                css.append("QPushButton:hover { background-color: %s; }" % options["activebackground"])
        if css:
            try: self.setStyleSheet(" ".join(css))
            except Exception: pass
        if isinstance(self, QProgressBar):
            if "maximum" in options:
                self.setMaximum(int(options["maximum"]))
            if "value" in options:
                self.setValue(int(float(options["value"])))
        if isinstance(self, QSlider):
            if "from_" in options:
                self.setMinimum(int(options["from_"]))
            if "to" in options:
                self.setMaximum(int(options["to"]))
        if "width" in options:
            try:
                metrics = QFontMetricsF(self.font())
                self.setMinimumWidth(max(1, int(metrics.averageCharWidth() * float(options["width"]))))
            except Exception:
                pass
        if "height" in options and not isinstance(self, (QTextEdit,)):
            try: self.setMinimumHeight(max(1, int(options["height"] * 1.5)))
            except Exception: pass
        if "text" in options:
            try:
                if hasattr(self, "setText"): self.setText(str(options["text"]))
            except Exception:
                pass
        if "anchor" in options and isinstance(self, QLabelQt):
            anchor = options["anchor"]
            flags = {
                "w": Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                "e": Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                "n": Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                "s": Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom,
                "nw": Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                "ne": Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop,
                "sw": Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom,
                "se": Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom,
                "center": Qt.AlignmentFlag.AlignCenter
            }
            self.setAlignment(flags.get(anchor, Qt.AlignmentFlag.AlignCenter))
        if isinstance(self, QLabelQt):
            self.setWordWrap(bool(options.get("wraplength") or options.get("wrap")))
        if "relief" in options and options["relief"] not in ("flat",):
            try: self.setFrameShape(QFrameQt.Shape.Panel)
            except Exception: pass
        self.update()

    def config(self, **options):
        self._apply_options(options)

    configure = config

    def cget(self, key):
        return self._tk_options.get(key)


class Tk(Misc, QMainWindow):
    def __init__(self, *args, **kwargs):
        _ensure_app()
        QMainWindow.__init__(self)
        self._init_misc(None, True)
        self._deleted = False
        self._content = QWidget(self)
        self.setCentralWidget(self._content)
        self.setWindowTitle("BITOS")
        self.resize(1024, 768)
        _root_windows.add(self)
        global _default_root
        _default_root = self

    def mainloop(self, *args, **kwargs):
        global _loop_running
        if _loop_running:
            return
        self.show()
        _loop_running = True
        try:
            _ensure_app().exec()
        finally:
            _loop_running = False

    def title(self, value=None):
        if value is None: return self.windowTitle()
        self.setWindowTitle(str(value))

    def geometry(self, value=None):
        if value is None:
            return "%dx%d+%d+%d" % (self.width(), self.height(), self.x(), self.y())
        value = str(value)
        position = re.match(r"^\s*([+-]\d+)([+-]\d+)\s*$", value)
        if position:
            self.move(int(position.group(1)), int(position.group(2)))
            return
        match = re.match(r"^\s*(\d+)x(\d+)(?:([+-]\d+)([+-]\d+))?\s*$", value)
        if match:
            self.resize(int(match.group(1)), int(match.group(2)))
            if match.group(3) is not None:
                self.move(int(match.group(3)), int(match.group(4)))

    def state(self, value=None):
        if value is None: return "zoomed" if self.isMaximized() else "normal"
        if value == "zoomed": self.showMaximized()
        elif value == "normal": self.showNormal()
        elif value == "iconic": self.showMinimized()

    def overrideredirect(self, value=True):
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, bool(value))

    def resizable(self, width=True, height=True):
        if not width: self.setFixedWidth(self.width())
        if not height: self.setFixedHeight(self.height())

    def minsize(self, width=None, height=None):
        if width is not None or height is not None:
            self.setMinimumSize(int(width or 0), int(height or 0))

    def maxsize(self, width=None, height=None):
        if width is not None or height is not None:
            self.setMaximumSize(int(width or 16777215), int(height or 16777215))

    def lift(self):
        self.raise_()
        self.activateWindow()

    def iconify(self):
        self.showMinimized()

    def protocol(self, name, callback):
        self._close_callback = callback

    def attributes(self, name, value=None):
        if name in ("-alpha", "alpha") and value is not None:
            self.setWindowOpacity(float(value))
        if name in ("-topmost", "topmost") and value is not None:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, bool(value))

    def report_callback_exception(self, exc, value, tb):
        import traceback
        traceback.print_exception(exc, value, tb)

    def closeEvent(self, event):
        callback = getattr(self, "_close_callback", None)
        if callback:
            event.ignore()
            try: callback()
            except Exception: event.accept()
        else:
            event.accept()
            _root_windows.discard(self)
            _dispatch_after(0, _maybe_quit)

    def withdraw(self):
        self.hide()

    def deiconify(self):
        self.show()


class Toplevel(Misc, QDialog):
    def __init__(self, parent=None, *args, **kwargs):
        _ensure_app()
        host = parent if isinstance(parent, QWidget) else None
        QDialog.__init__(self, host)
        self._init_misc(parent, False)
        self._deleted = False
        self.setWindowTitle("BITOS")
        self.resize(480, 360)
        self.setModal(False)

    def title(self, value=None):
        if value is None: return self.windowTitle()
        self.setWindowTitle(str(value))

    def geometry(self, value=None):
        if value is None:
            return "%dx%d+%d+%d" % (self.width(), self.height(), self.x(), self.y())
        value = str(value)
        position = re.match(r"^\s*([+-]\d+)([+-]\d+)\s*$", value)
        if position:
            self.move(int(position.group(1)), int(position.group(2)))
            return
        match = re.match(r"^\s*(\d+)x(\d+)(?:([+-]\d+)([+-]\d+))?\s*$", value)
        if match:
            if int(match.group(1)) > 0 and int(match.group(2)) > 0:
                self.resize(int(match.group(1)), int(match.group(2)))
            if match.group(3) is not None:
                self.move(int(match.group(3)), int(match.group(4)))

    def state(self, value=None):
        if value is None: return "zoomed" if self.isMaximized() else "normal"
        if value == "zoomed": self.showMaximized()
        elif value == "normal": self.showNormal()
        elif value == "iconic": self.showMinimized()

    def overrideredirect(self, value=True):
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, bool(value))

    def resizable(self, width=True, height=True):
        if not width: self.setFixedWidth(self.width())
        if not height: self.setFixedHeight(self.height())

    def protocol(self, name, callback):
        self._close_callback = callback

    def transient(self, parent=None):
        if parent and isinstance(parent, QWidget):
            self.setParent(parent, self.windowFlags())

    def attributes(self, name, value=None):
        if name in ("-alpha", "alpha") and value is not None:
            self.setWindowOpacity(float(value))

    def closeEvent(self, event):
        callback = getattr(self, "_close_callback", None)
        if callback:
            event.ignore()
            callback()
        else:
            event.accept()

    def withdraw(self):
        self.hide()

    def deiconify(self):
        self.show()


class Frame(Misc, QFrameQt):
    def __init__(self, parent=None, **options):
        host = _parent_widget(parent)
        QFrameQt.__init__(self, host)
        self._init_misc(parent)
        self._deleted = False
        self._apply_options(options)


class Label(Misc, QLabelQt):
    def __init__(self, parent=None, **options):
        host = _parent_widget(parent)
        text = str(options.pop("text", ""))
        QLabelQt.__init__(self, text, host)
        self._init_misc(parent)
        self._deleted = False
        self._apply_options(options)


class Button(Misc, QPushButton):
    def __init__(self, parent=None, **options):
        host = _parent_widget(parent)
        text = str(options.pop("text", ""))
        command = options.pop("command", None)
        QPushButton.__init__(self, text, host)
        self._init_misc(parent)
        self._deleted = False
        if command:
            self.clicked.connect(lambda _checked=False: command())
        self._apply_options(options)

    def invoke(self):
        self.click()


class Entry(Misc, QLineEdit):
    def __init__(self, parent=None, **options):
        host = _parent_widget(parent)
        QLineEdit.__init__(self, host)
        self._init_misc(parent)
        self._deleted = False
        show = options.pop("show", None)
        if show: self.setEchoMode(QLineEdit.EchoMode.Password)
        self._apply_options(options)

    def get(self):
        return self.text()

    def delete(self, first=0, last=None):
        start = 0 if first in (0, "0") else max(0, int(first))
        end = len(self.text())
        if last not in (None, "end", "END"):
            end = max(start, int(last))
        self.setText(self.text()[:start] + self.text()[end:])

    def insert(self, index, value):
        if index in (0, "0", "insert"):
            self.setText(str(value) + self.text())
        elif index in ("end", "END"):
            self.setText(self.text() + str(value))
        else:
            pos = max(0, int(index))
            self.setText(self.text()[:pos] + str(value) + self.text()[pos:])

    def icursor(self, index):
        self.setCursorPosition(len(self.text()) if index == "end" else int(index))


class Text(Misc, QTextEdit):
    def __init__(self, parent=None, **options):
        host = _parent_widget(parent)
        QTextEdit.__init__(self, host)
        self._init_misc(parent)
        self._deleted = False
        if options.get("wrap") == "none":
            self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self._apply_options(options)

    def insert(self, index, value):
        cursor = self.textCursor()
        if index in ("1.0", "0.0", "0"):
            cursor.movePosition(QTextCursor.MoveOperation.Start)
        else:
            cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(str(value))
        self.setTextCursor(cursor)

    def delete(self, first="1.0", last="end"):
        if first in ("1.0", "0.0", "0") and last in ("end", "END", "end-1c"):
            self.clear()
        else:
            cursor = self.textCursor()
            cursor.select(QTextCursor.SelectionType.Document)
            cursor.removeSelectedText()

    def get(self, first="1.0", last="end"):
        value = self.toPlainText()
        return value + ("\n" if last in ("end", "END") else "")

    def see(self, index):
        self.moveCursor(QTextCursor.MoveOperation.End)


class Checkbutton(Misc, QCheckBox):
    def __init__(self, parent=None, **options):
        host = _parent_widget(parent)
        text = str(options.pop("text", ""))
        variable = options.pop("variable", None)
        command = options.pop("command", None)
        QCheckBox.__init__(self, text, host)
        self._init_misc(parent)
        self._deleted = False
        self._variable = variable
        if variable is not None:
            self.setChecked(bool(variable.get()))
        self.stateChanged.connect(lambda value: variable.set(bool(value)) if variable is not None else None)
        if command: self.clicked.connect(command)
        self._apply_options(options)


class Radiobutton(Misc, QRadioButton):
    def __init__(self, parent=None, **options):
        host = _parent_widget(parent)
        text = str(options.pop("text", ""))
        variable = options.pop("variable", None)
        value = options.pop("value", text)
        command = options.pop("command", None)
        QRadioButton.__init__(self, text, host)
        self._init_misc(parent)
        self._deleted = False
        self._variable = variable
        self._value = value
        if variable is not None:
            self.setChecked(variable.get() == value)
        def sync(checked):
            if checked and variable is not None:
                variable.set(value)
            if checked and command:
                command()
        self.toggled.connect(sync)
        self._apply_options(options)


class Scale(Misc, QSlider):
    def __init__(self, parent=None, **options):
        host = _parent_widget(parent)
        orient = options.pop("orient", "horizontal")
        QSlider.__init__(self, Qt.Orientation.Horizontal if orient == "horizontal" else Qt.Orientation.Vertical, host)
        self._init_misc(parent)
        self._deleted = False
        self.setRange(int(options.pop("from_", 0)), int(options.pop("to", 100)))
        command = options.pop("command", None)
        if command:
            self.valueChanged.connect(lambda value: command(str(value)))
        self._apply_options(options)

    def get(self):
        return self.value()

    def set(self, value):
        self.setValue(int(float(value)))


class Scrollbar(Misc, QScrollBar):
    def __init__(self, parent=None, **options):
        host = _parent_widget(parent)
        orient = options.pop("orient", "vertical")
        QScrollBar.__init__(self, Qt.Orientation.Vertical if orient == "vertical" else Qt.Orientation.Horizontal, host)
        self._init_misc(parent)
        self._deleted = False
        self._command = options.pop("command", None)
        self.setRange(0, 1000)
        self.valueChanged.connect(self._notify)
        self._apply_options(options)

    def _notify(self, value):
        if self._command:
            try: self._command("moveto", value / max(1, self.maximum()))
            except Exception: pass

    def set(self, first, last=None):
        try:
            first_value = max(0.0, min(1.0, float(first)))
            last_value = max(first_value, min(1.0, float(last if last is not None else 1.0)))
            self.setPageStep(max(1, int((last_value - first_value) * max(1, self.maximum()))))
            self.setValue(int(first_value * max(1, self.maximum())))
        except Exception:
            pass


class _Variable:
    def __init__(self, master=None, value=None):
        self._value = value
        self._traces = []

    def get(self):
        return self._value

    def set(self, value):
        self._value = value
        for callback in list(self._traces):
            try: callback()
            except Exception: pass

    def trace_add(self, mode, callback):
        self._traces.append(lambda: callback("", "", mode))

    trace = trace_add


class StringVar(_Variable):
    def __init__(self, master=None, value=""):
        super().__init__(master, value)


class BooleanVar(_Variable):
    def __init__(self, master=None, value=False):
        super().__init__(master, bool(value))


class IntVar(_Variable):
    def __init__(self, master=None, value=0):
        super().__init__(master, int(value))


class DoubleVar(_Variable):
    def __init__(self, master=None, value=0.0):
        super().__init__(master, float(value))


class Canvas(Misc, QWidget):
    def __init__(self, parent=None, **options):
        host = _parent_widget(parent)
        QWidget.__init__(self, host)
        self._init_misc(parent)
        self._deleted = False
        self.items = []
        self._ids = {}
        self._tag_bindings = {}
        self._scroll_y = 0
        self._scrollregion = None
        self._yscrollcommand = None
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setMinimumSize(int(options.pop("width", 1)), int(options.pop("height", 1)))
        self._apply_options(options)

    def _add(self, kind, coords, **options):
        item_id = next(_item_ids)
        tags = options.pop("tags", ())
        if isinstance(tags, str): tags = (tags,)
        self.items.append({"id": item_id, "kind": kind, "coords": list(coords), "options": options, "tags": tuple(tags)})
        self._ids[item_id] = self.items[-1]
        self.update()
        return item_id

    def create_text(self, x, y, **options):
        return self._add("text", (x, y), **options)

    def create_line(self, *coords, **options):
        if len(coords) == 1 and isinstance(coords[0], (list, tuple)):
            coords = tuple(coords[0])
        return self._add("line", coords, **options)

    def create_rectangle(self, x1, y1, x2, y2, **options):
        return self._add("rect", (x1, y1, x2, y2), **options)

    def create_oval(self, x1, y1, x2, y2, **options):
        return self._add("oval", (x1, y1, x2, y2), **options)

    def create_polygon(self, *coords, **options):
        return self._add("polygon", coords, **options)

    def create_image(self, x, y, **options):
        return self._add("image", (x, y), **options)

    def create_window(self, coords, **options):
        widget = options.pop("window", None)
        item_id = self._add("window", coords, widget=widget, **options)
        if widget is not None:
            try:
                widget.setParent(self)
                widget.show()
                self._place_canvas_window(self._ids[item_id])
            except Exception:
                pass
        return item_id

    def _place_canvas_window(self, item):
        widget = item["options"].get("widget")
        if widget is None: return
        coords = item["coords"]
        x, y = float(coords[0]), float(coords[1])
        anchor = item["options"].get("anchor", "center")
        width = int(item["options"].get("width", widget.sizeHint().width() or widget.width() or 200))
        height = int(item["options"].get("height", widget.sizeHint().height() or widget.height() or 100))
        if anchor in ("n", "ne", "nw"): pass
        elif anchor in ("s", "se", "sw"): y -= height
        else: y -= height / 2
        if anchor in ("w", "nw", "sw"): pass
        elif anchor in ("e", "ne", "se"): x -= width
        else: x -= width / 2
        widget.setGeometry(int(x), int(y - self._scroll_y), width, height)

    def delete(self, target):
        if target in ("all", "ALL"):
            for item in list(self.items):
                widget = item["options"].get("widget")
                if widget is not None: widget.hide()
            self.items.clear()
            self._ids.clear()
        else:
            remove = []
            for item in self.items:
                if item["id"] == target or target in item["tags"]:
                    remove.append(item)
            for item in remove:
                widget = item["options"].get("widget")
                if widget is not None: widget.hide()
                self.items.remove(item)
                self._ids.pop(item["id"], None)
        self.update()

    def itemconfig(self, target, **options):
        for item in self.items:
            if item["id"] == target or target in item["tags"]:
                item["options"].update(options)
        self.update()

    itemconfigure = itemconfig

    def coords(self, target, *coords):
        item = self._ids.get(target)
        if item is None: return []
        if coords:
            item["coords"] = list(coords)
            if item["kind"] == "window": self._place_canvas_window(item)
            self.update()
        return list(item["coords"])

    def move(self, target, dx, dy):
        for item in self.items:
            if item["id"] == target or target in item["tags"]:
                c = item["coords"]
                item["coords"] = [v + (dx if i % 2 == 0 else dy) for i, v in enumerate(c)]
                if item["kind"] == "window": self._place_canvas_window(item)
        self.update()

    def gettags(self, target):
        item = self._ids.get(target)
        return item["tags"] if item else ()

    def find_overlapping(self, x1, y1, x2, y2):
        found = []
        for item in self.items:
            box = self._item_bbox(item)
            if box and box[0] <= x2 and box[2] >= x1 and box[1] <= y2 and box[3] >= y1:
                found.append(item["id"])
        return tuple(found)

    def bbox(self, target="all"):
        selected = self.items if target in ("all", "ALL") else [i for i in self.items if i["id"] == target or target in i["tags"]]
        boxes = [self._item_bbox(i) for i in selected]
        boxes = [b for b in boxes if b]
        if not boxes: return None
        return (int(min(b[0] for b in boxes)), int(min(b[1] for b in boxes)),
                int(max(b[2] for b in boxes)), int(max(b[3] for b in boxes)))

    def _item_bbox(self, item):
        c = item["coords"]
        if not c: return None
        if item["kind"] == "text":
            text = str(item["options"].get("text", ""))
            font = _font_from(item["options"].get("font"))
            fm = QFontMetricsF(font)
            rect = fm.boundingRect(text)
            return (c[0] - rect.width()/2, c[1] - rect.height()/2, c[0] + rect.width()/2, c[1] + rect.height()/2)
        if item["kind"] in ("rect", "oval"):
            return (min(c[0], c[2]), min(c[1], c[3]), max(c[0], c[2]), max(c[1], c[3]))
        if item["kind"] in ("line", "polygon"):
            xs, ys = c[0::2], c[1::2]
            return (min(xs), min(ys), max(xs), max(ys))
        if item["kind"] == "image":
            image = item["options"].get("image")
            pixmap = getattr(image, "pixmap", image)
            if isinstance(pixmap, QPixmap):
                anchor = item["options"].get("anchor", "center")
                x, y = float(c[0]), float(c[1])
                x0 = x if anchor in ("nw", "w", "sw") else x - pixmap.width() / 2
                y0 = y if anchor in ("nw", "n", "ne") else y - pixmap.height() / 2
                return (x0, y0, x0 + pixmap.width(), y0 + pixmap.height())
            return (c[0]-10, c[1]-10, c[0]+10, c[1]+10)
        if item["kind"] == "window":
            widget = item["options"].get("widget")
            width = int(item["options"].get("width", widget.sizeHint().width() if widget else 200) or 200)
            height = int(item["options"].get("height", widget.sizeHint().height() if widget else 100) or 100)
            x, y = float(c[0]), float(c[1])
            anchor = item["options"].get("anchor", "center")
            x0 = x if anchor in ("nw", "w", "sw") else x - width if anchor in ("ne", "e", "se") else x - width / 2
            y0 = y if anchor in ("nw", "n", "ne") else y - height if anchor in ("sw", "s", "se") else y - height / 2
            return (x0, y0, x0 + width, y0 + height)
        return None

    def tag_bind(self, tag, sequence, callback, add=None):
        self._tag_bindings.setdefault((tag, sequence), []).append(callback)

    def tag_raise(self, target, above=None):
        selected = [i for i in self.items if i["id"] == target or target in i["tags"]]
        self.items = [i for i in self.items if i not in selected] + selected
        self.update()

    lift = tag_raise

    def tag_lower(self, target, below=None):
        selected = [i for i in self.items if i["id"] == target or target in i["tags"]]
        self.items = selected + [i for i in self.items if i not in selected]
        self.update()

    lower = tag_lower

    def yview(self, *args):
        if args and args[0] == "moveto":
            self._scroll_y = max(0, int(float(args[1]) * (self._scrollregion[3] if self._scrollregion else self.height())))
        elif args and args[0] == "scroll":
            amount = int(args[1]) * (20 if len(args) < 3 or args[2] == "units" else self.height())
            self._scroll_y = max(0, self._scroll_y + amount)
        self._update_canvas_windows()
        self._notify_scroll()
        self.update()

    def yview_scroll(self, amount, what="units"):
        self.yview("scroll", amount, what)

    def yview_moveto(self, fraction):
        self.yview("moveto", fraction)

    def xview(self, *args):
        return (0.0, 1.0)

    def _update_canvas_windows(self):
        for item in self.items:
            if item["kind"] == "window": self._place_canvas_window(item)

    def _notify_scroll(self):
        if not self._yscrollcommand:
            return
        total = max(self.height(), self._scrollregion[3] if self._scrollregion else self.height())
        first = min(1.0, self._scroll_y / max(1, total))
        last = min(1.0, (self._scroll_y + self.height()) / max(1, total))
        try:
            self._yscrollcommand(first, last)
        except Exception:
            pass

    def configure(self, **options):
        self._tk_options.update(options)
        if "scrollregion" in options:
            self._scrollregion = options["scrollregion"]
        if "yscrollcommand" in options:
            self._yscrollcommand = options["yscrollcommand"]
        self._apply_options({k:v for k,v in options.items() if k in ("bg","background","cursor")})
        self._notify_scroll()

    config = configure

    def paintEvent(self, event):
        painter = QPainter(self)
        bg = self._tk_options.get("bg", self._tk_options.get("background", "white"))
        painter.fillRect(self.rect(), QColor(bg))
        for item in self.items:
            kind, c, opt = item["kind"], item["coords"], item["options"]
            if kind == "window": continue
            painter.save()
            fill = opt.get("fill")
            outline = opt.get("outline")
            width = float(opt.get("width", 1) or 1)
            pen = QPen(QColor(outline if outline else fill if fill else "transparent"), width)
            if not outline or outline == "": pen.setStyle(Qt.PenStyle.NoPen)
            painter.setPen(pen)
            painter.setBrush(QBrush(QColor(fill)) if fill else Qt.BrushStyle.NoBrush)
            if kind == "line" and len(c) >= 4:
                for i in range(0, len(c)-2, 2):
                    painter.drawLine(QPointF(float(c[i]), float(c[i+1])-self._scroll_y),
                                     QPointF(float(c[i+2]), float(c[i+3])-self._scroll_y))
            elif kind == "rect" and len(c) >= 4:
                rect = QRectF(float(c[0]), float(c[1])-self._scroll_y, float(c[2])-float(c[0]), float(c[3])-float(c[1]))
                painter.drawRect(rect)
            elif kind == "oval" and len(c) >= 4:
                rect = QRectF(float(c[0]), float(c[1])-self._scroll_y, float(c[2])-float(c[0]), float(c[3])-float(c[1]))
                painter.drawEllipse(rect)
            elif kind == "polygon" and len(c) >= 6:
                pts = [QPointF(float(c[i]), float(c[i+1])-self._scroll_y) for i in range(0, len(c)-1, 2)]
                painter.drawPolygon(QPolygonF(pts))
            elif kind == "text" and len(c) >= 2:
                painter.setFont(_font_from(opt.get("font")))
                painter.setPen(QPen(QColor(fill or "black")))
                text = str(opt.get("text", ""))
                anchor = opt.get("anchor", "center")
                fm = QFontMetricsF(painter.font())
                rect = fm.boundingRect(text)
                x, y = float(c[0]), float(c[1])-self._scroll_y
                if anchor in ("w","nw","sw"): x0=x
                elif anchor in ("e","ne","se"): x0=x-rect.width()
                else: x0=x-rect.width()/2
                if anchor in ("n","nw","ne"): y0=y
                elif anchor in ("s","sw","se"): y0=y-rect.height()
                else: y0=y-rect.height()/2
                flags = Qt.AlignmentFlag.AlignLeft
                if opt.get("justify") == "center": flags = Qt.AlignmentFlag.AlignHCenter
                elif opt.get("justify") == "right": flags = Qt.AlignmentFlag.AlignRight
                painter.drawText(QRectF(x0, y0, max(rect.width(), 1), max(rect.height(), 1)), flags | Qt.AlignmentFlag.AlignVCenter, text)
            elif kind == "image" and len(c) >= 2:
                image = opt.get("image")
                pixmap = getattr(image, "pixmap", image)
                if isinstance(pixmap, QPixmap):
                    x, y = float(c[0]), float(c[1])-self._scroll_y
                    anchor = opt.get("anchor", "center")
                    if anchor in ("nw","w","sw"): x0=x
                    else: x0=x-pixmap.width()/2
                    if anchor in ("nw","n","ne"): y0=y
                    else: y0=y-pixmap.height()/2
                    painter.drawPixmap(int(x0), int(y0), pixmap)
            painter.restore()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_canvas_windows()

    def mousePressEvent(self, event):
        data = _event_data(self, event)
        for item in reversed(self.items):
            box = self._item_bbox(item)
            if box and box[0] <= data.x <= box[2] and box[1]-self._scroll_y <= data.y <= box[3]-self._scroll_y:
                sequence = "<Button-3>" if data.num == 3 else "<Button-1>"
                for tag in item["tags"] + (item["id"],):
                    for cb in self._tag_bindings.get((tag, sequence), []):
                        cb(data)
        super().mousePressEvent(event)


class Menu(Misc, QMenuQt):
    def __init__(self, parent=None, **options):
        host = parent if isinstance(parent, QWidget) else None
        QMenuQt.__init__(self, host)
        self._init_misc(parent)
        self._deleted = False
        self._apply_options(options)

    def add_command(self, label="", command=None, **options):
        action = self.addAction(str(label))
        if command: action.triggered.connect(command)
        return action

    def add_separator(self):
        self.addSeparator()

    def add_cascade(self, label="", menu=None, **options):
        self.addMenu(menu)

    def tk_popup(self, x, y):
        self.popup(QPointF(int(x), int(y)).toPoint())

    post = tk_popup


class Progressbar(Misc, QProgressBar):
    def __init__(self, parent=None, **options):
        host = _parent_widget(parent)
        QProgressBar.__init__(self, host)
        self._init_misc(parent)
        self._deleted = False
        self.setRange(0, int(options.pop("maximum", 100)))
        if "length" in options: self.setMinimumWidth(int(options.pop("length")))
        self._apply_options(options)

    def start(self, interval=50):
        self._timer = QTimer(self)
        self._timer.timeout.connect(lambda: self.setValue((self.value()+1) % max(1, self.maximum()+1)))
        self._timer.start(int(interval))

    def stop(self):
        if hasattr(self, "_timer"): self._timer.stop()


class Combobox(Misc, QComboBox):
    def __init__(self, parent=None, **options):
        host = _parent_widget(parent)
        QComboBox.__init__(self, host)
        self._init_misc(parent)
        self._deleted = False
        self._variable = options.pop("textvariable", None)
        values = options.pop("values", [])
        self.addItems([str(x) for x in values])
        state = options.pop("state", None)
        if state == "readonly": self.setEditable(False)
        if self._variable is not None:
            self.setCurrentText(str(self._variable.get()))
            self.currentTextChanged.connect(self._variable.set)
        self._apply_options(options)

    def get(self):
        return self.currentText()

    def set(self, value):
        self.setCurrentText(str(value))

    def current(self, index=None):
        if index is None:
            return self.currentIndex()
        self.setCurrentIndex(int(index))


class Notebook(Misc, QTabWidget):
    def __init__(self, parent=None, **options):
        host = _parent_widget(parent)
        QTabWidget.__init__(self, host)
        self._init_misc(parent)
        self._deleted = False
        self._apply_options(options)

    def add(self, child, text=""):
        self.addTab(child, str(text))

    def select(self, index=None):
        if index is None: return self.currentIndex()
        if isinstance(index, int): self.setCurrentIndex(index)
        else:
            for i in range(self.count()):
                if self.widget(i) is index: self.setCurrentIndex(i)


class Treeview(Misc, QTreeWidget):
    def __init__(self, parent=None, **options):
        host = _parent_widget(parent)
        QTreeWidget.__init__(self, host)
        self._init_misc(parent)
        self._deleted = False
        self._columns = list(options.pop("columns", []))
        self.setColumnCount(len(self._columns))
        self.setHeaderLabels(self._columns)
        if options.get("show") == "tree": self.setRootIsDecorated(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        if "height" in options: self.setMinimumHeight(int(options["height"] * 20))
        self._iid_map = {}
        self._apply_options(options)

    def heading(self, column, text=None, **options):
        idx = self._column_index(column)
        if text is not None: self.headerItem().setText(idx, str(text))

    def column(self, column, width=None, anchor=None, **options):
        idx = self._column_index(column)
        if width is not None: self.setColumnWidth(idx, int(width))

    def _column_index(self, col):
        if isinstance(col, int): return col
        try: return self._columns.index(col)
        except ValueError: return 0

    def insert(self, parent, index, iid=None, text="", values=(), **options):
        if self._tk_options.get("show") == "headings":
            item = QTreeWidgetItem([str(v) for v in values])
        else:
            item = QTreeWidgetItem([str(text)] + [str(v) for v in values])
        key = str(iid or id(item))
        item.setData(0, Qt.ItemDataRole.UserRole, key)
        self._iid_map[key] = item
        if parent:
            parent_item = self._iid_map.get(str(parent))
            if parent_item: parent_item.addChild(item)
            else: self.addTopLevelItem(item)
        else:
            self.addTopLevelItem(item)
        return key

    def get_children(self, item=None):
        if not item:
            return tuple(str(self.topLevelItem(i).data(0, Qt.ItemDataRole.UserRole)) for i in range(self.topLevelItemCount()))
        node = self._iid_map.get(str(item))
        if not node: return ()
        return tuple(str(node.child(i).data(0, Qt.ItemDataRole.UserRole)) for i in range(node.childCount()))

    def item(self, iid, option=None, **kwargs):
        node = self._iid_map.get(str(iid))
        if not node: return {}
        if "values" in kwargs:
            values = kwargs["values"]
            for i, value in enumerate(values, start=1):
                if i < self.columnCount(): node.setText(i, str(value))
        if "text" in kwargs: node.setText(0, str(kwargs["text"]))
        result = {"text": node.text(0), "values": [node.text(i) for i in range(1, self.columnCount())]}
        return result.get(option, result) if option else result

    def delete(self, *iids):
        for iid in iids:
            node = self._iid_map.pop(str(iid), None)
            if node:
                parent = node.parent()
                if parent: parent.removeChild(node)
                else:
                    idx = self.indexOfTopLevelItem(node)
                    if idx >= 0: self.takeTopLevelItem(idx)

    def selection(self):
        return tuple(str(x.data(0, Qt.ItemDataRole.UserRole)) for x in self.selectedItems())

    def selection_anchor(self):
        item = self.currentItem()
        return str(item.data(0, Qt.ItemDataRole.UserRole)) if item else ""

    def focus(self, iid=None):
        if iid is None:
            item = self.currentItem()
            return str(item.data(0, Qt.ItemDataRole.UserRole)) if item else ""
        item = self._iid_map.get(str(iid))
        if item:
            self.setCurrentItem(item)

    def selection_set(self, *iids):
        self.clearSelection()
        for iid in iids:
            node = self._iid_map.get(str(iid))
            if node: node.setSelected(True)

    def selection_remove(self, *iids):
        for iid in iids:
            node = self._iid_map.get(str(iid))
            if node: node.setSelected(False)

    def identify_row(self, y):
        node = self.itemAt(1, int(y))
        return str(node.data(0, Qt.ItemDataRole.UserRole)) if node else ""

    def yview(self, *args):
        bar = self.verticalScrollBar()
        if args and args[0] == "moveto":
            bar.setValue(int(float(args[1]) * bar.maximum()))
        elif args and args[0] == "scroll":
            bar.setValue(bar.value() + int(args[1]) * 20)

    def xview(self, *args):
        bar = self.horizontalScrollBar()
        if args and args[0] == "moveto": bar.setValue(int(float(args[1]) * bar.maximum()))

    def tag_configure(self, tag, **options):
        pass


class Style:
    def configure(self, *args, **kwargs):
        pass
    def map(self, *args, **kwargs):
        pass
    def theme_use(self, *args, **kwargs):
        pass


class _Ttk:
    Frame = Frame
    Scrollbar = Scrollbar
    Progressbar = Progressbar
    Combobox = Combobox
    Notebook = Notebook
    Treeview = Treeview
    Style = Style


class _ScrolledText:
    ScrolledText = Text


class _MessageBox:
    @staticmethod
    def _show(icon, title, message, parent=None):
        box = QMessageBox(parent if isinstance(parent, QWidget) else None)
        box.setIcon(icon)
        box.setWindowTitle(str(title))
        box.setText(str(message))
        box.exec()
        return "ok"

    @classmethod
    def showerror(cls, title, message, **kwargs):
        return cls._show(QMessageBox.Icon.Critical, title, message, kwargs.get("parent"))

    @classmethod
    def showwarning(cls, title, message, **kwargs):
        return cls._show(QMessageBox.Icon.Warning, title, message, kwargs.get("parent"))

    @classmethod
    def showinfo(cls, title, message, **kwargs):
        return cls._show(QMessageBox.Icon.Information, title, message, kwargs.get("parent"))

    @staticmethod
    def askyesno(title, message, **kwargs):
        box = QMessageBox(kwargs.get("parent") if isinstance(kwargs.get("parent"), QWidget) else None)
        box.setIcon(QMessageBox.Icon.Question)
        box.setWindowTitle(str(title))
        box.setText(str(message))
        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        return box.exec() == QMessageBox.StandardButton.Yes


class _FileDialog:
    @staticmethod
    def askopenfilename(**kwargs):
        path, _ = QFileDialog.getOpenFileName(kwargs.get("parent"), kwargs.get("title", "Открыть файл"),
                                               kwargs.get("initialdir", ""), _filetypes(kwargs.get("filetypes")))
        return path


def _filetypes(values):
    result = []
    for entry in values or []:
        try:
            label, patterns = entry
            result.append("%s (%s)" % (label, " ".join(patterns) if isinstance(patterns, (list, tuple)) else patterns))
        except Exception:
            pass
    return ";;".join(result)


class _ColorChooser:
    @staticmethod
    def askcolor(color=None, **kwargs):
        initial = QColor(color) if color else QColor("white")
        chosen = QColorDialog.getColor(initial, kwargs.get("parent"), kwargs.get("title", "Выберите цвет"))
        if not chosen.isValid(): return (None, None)
        return ((chosen.red(), chosen.green(), chosen.blue()), chosen.name())


class _ImageTk:
    class PhotoImage:
        def __init__(self, image=None, **kwargs):
            self.pixmap = QPixmap()
            if isinstance(image, QPixmap):
                self.pixmap = image
            elif image is not None:
                try:
                    rgba = image.convert("RGBA")
                    raw = rgba.tobytes("raw", "RGBA")
                    qimage = QImage(raw, rgba.width, rgba.height, QImage.Format.Format_RGBA8888).copy()
                    self.pixmap = QPixmap.fromImage(qimage)
                except Exception:
                    pass


ttk = _Ttk()
messagebox = _MessageBox()
filedialog = _FileDialog()
colorchooser = _ColorChooser()
scrolledtext = _ScrolledText()
ImageTk = _ImageTk()

LEFT, RIGHT, TOP, BOTTOM = "left", "right", "top", "bottom"
X, Y, BOTH = "x", "y", "both"
HORIZONTAL, VERTICAL = "horizontal", "vertical"
END, INSERT = "end", "insert"
WORD, CHAR, NONE = "word", "char", "none"
RAISED, SUNKEN, RIDGE, GROOVE, FLAT, SOLID = "raised", "sunken", "ridge", "groove", "flat", "solid"
ROUND = "round"


def _maybe_quit():
    if not _loop_running:
        return
    visible = False
    for root in list(_root_windows):
        try:
            if root.isVisible():
                visible = True
                break
        except Exception:
            _root_windows.discard(root)
    if not visible:
        try: _ensure_app().quit()
        except Exception: pass


def mainloop():
    global _loop_running
    if _loop_running: return
    _loop_running = True
    try: _ensure_app().exec()
    finally: _loop_running = False


def TkVersion():
    return 8.6


__all__ = [
    "Tk", "Toplevel", "Frame", "Label", "Button", "Entry", "Text", "Canvas",
    "Menu", "Scrollbar", "Checkbutton", "Radiobutton", "Scale", "StringVar",
    "BooleanVar", "IntVar", "DoubleVar", "Misc", "TclError", "ttk", "messagebox",
    "filedialog", "colorchooser", "scrolledtext", "ImageTk", "LEFT", "RIGHT",
    "TOP", "BOTTOM", "X", "Y", "BOTH", "HORIZONTAL", "VERTICAL", "END",
    "INSERT", "WORD", "CHAR", "NONE", "RAISED", "SUNKEN", "RIDGE", "GROOVE",
    "FLAT", "SOLID", "ROUND", "_default_root", "QTimer", "QApplication", "Qt",
    "mainloop"
]
