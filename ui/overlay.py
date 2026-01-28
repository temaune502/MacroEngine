from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QPoint
from PyQt6.QtGui import QFont, QColor, QGuiApplication

class OverlaySignals(QObject):
    update_text = pyqtSignal(str, object) # label_id, text or list of args
    show_overlay = pyqtSignal(bool)
    move_overlay = pyqtSignal(int, int) # x, y
    resize_overlay = pyqtSignal(int, int) # w, h
    set_font_size = pyqtSignal(str, int) # label_id, size
    set_scale = pyqtSignal(float)
    set_color = pyqtSignal(str, str) # label_id, hex_color
    set_bg_opacity = pyqtSignal(int) # 0-255
    set_anchor = pyqtSignal(str) # "top_left", "top_right", etc.
    set_template = pyqtSignal(str, str) # label_id, template_string

class HUDOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.signals = OverlaySignals()
        self.signals.update_text.connect(self._set_text)
        self.signals.show_overlay.connect(self._set_visible)
        self.signals.move_overlay.connect(self._move_to)
        self.signals.resize_overlay.connect(self._resize_to)
        self.signals.set_font_size.connect(self._set_font_size)
        self.signals.set_scale.connect(self._set_scale)
        self.signals.set_color.connect(self._set_color)
        self.signals.set_bg_opacity.connect(self._set_bg_opacity)
        self.signals.set_anchor.connect(self._set_anchor)
        self.signals.set_template.connect(self._set_template)
        
        self.labels = {}
        self.templates = {} # label_id -> template string
        self.font_sizes = {} # label_id -> size
        self.colors = {} # label_id -> hex_color
        self.scale = 1.0
        self.bg_opacity = 180
        self.anchor_pos = None # "top_left", "top_right", "bottom_left", "bottom_right"
        
        # Налаштування вікна
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )
        
        # Виправлення "білого вікна": WA_TranslucentBackground має бути True
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        
        # ВАЖЛИВО: Для Windows, щоб прибрати білий фон, іноді треба примусово встановити прозору палітру
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor(0, 0, 0, 0))
        self.setPalette(palette)
        
        # Щоб вікно не перекривало кліки, якщо воно на весь екран (хоча ми його зменшимо)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.layout.setContentsMargins(0, 0, 0, 0) # Прибираємо відступи, щоб точніше позиціонувати
        self.layout.setSpacing(5)
        
        # Початкова позиція
        self.setGeometry(10, 10, 200, 50) # Маленьке за замовчуванням
        
    def _move_to(self, x, y):
        self.anchor_pos = None # Скасовуємо якір при ручному переміщенні
        self.move(x, y)

    def _resize_to(self, w, h):
        self.setFixedSize(w, h)
        if self.anchor_pos:
            self._update_anchor_position()

    def _set_font_size(self, label_id, size):
        self.font_sizes[label_id] = size
        if label_id in self.labels:
            self._apply_style(label_id)
            self.adjustSize()
            if self.anchor_pos:
                self._update_anchor_position()

    def _set_scale(self, scale):
        self.scale = scale
        for label_id in self.labels:
            self._apply_style(label_id)
        self.layout.setSpacing(int(5 * self.scale))
        self.adjustSize()
        if self.anchor_pos:
            self._update_anchor_position()

    def _set_color(self, label_id, hex_color):
        self.colors[label_id] = hex_color
        if label_id in self.labels:
            self._apply_style(label_id)

    def _set_bg_opacity(self, opacity):
        self.bg_opacity = max(0, min(255, opacity))
        for label_id in self.labels:
            self._apply_style(label_id)

    def _set_anchor(self, anchor):
        self.anchor_pos = anchor
        self._update_anchor_position()

    def _set_template(self, label_id, template):
        self.templates[label_id] = template

    def _update_anchor_position(self):
        if not self.anchor_pos:
            return
            
        screen = QGuiApplication.primaryScreen().geometry()
        sw, sh = screen.width(), screen.height()
        self.adjustSize()
        w, h = self.width(), self.height()
        
        margin = int(10 * self.scale)
        
        if self.anchor_pos == "top_left":
            self.move(margin, margin)
        elif self.anchor_pos == "top_right":
            self.move(sw - w - margin, margin)
        elif self.anchor_pos == "bottom_left":
            self.move(margin, sh - h - margin)
        elif self.anchor_pos == "bottom_right":
            self.move(sw - w - margin, sh - h - margin)
        elif self.anchor_pos == "top_center":
            self.move((sw - w) // 2, margin)
        elif self.anchor_pos == "bottom_center":
            self.move((sw - w) // 2, sh - h - margin)

    def _apply_style(self, label_id):
        if label_id not in self.labels:
            return
            
        label = self.labels[label_id]
        size = int(self.font_sizes.get(label_id, 14) * self.scale)
        color = self.colors.get(label_id, "#a6e22e")
        padding = int(5 * self.scale)
        radius = int(5 * self.scale)
        
        font = label.font()
        font.setPointSize(size)
        label.setFont(font)
        
        label.setStyleSheet(f"""
            QLabel {{
                color: {color}; 
                background-color: rgba(0, 0, 0, {self.bg_opacity}); 
                padding: {padding}px {padding*2}px; 
                border-radius: {radius}px;
                border: 1px solid rgba(166, 226, 46, 80);
            }}
        """)

    def _set_text(self, label_id, text_or_args):
        try:
            if label_id not in self.labels:
                label = QLabel("")
                label.setFont(QFont("Consolas", 14, QFont.Weight.Bold))
                self.layout.addWidget(label)
                self.labels[label_id] = label
                self._apply_style(label_id)
            
            target_label = self.labels[label_id]
            
            display_text = ""
            if isinstance(text_or_args, (list, tuple)):
                # Позиційне форматування за шаблоном
                template = self.templates.get(label_id, "")
                if template:
                    try:
                        # Підставляємо аргументи {0}, {1}, ...
                        display_text = template.format(*text_or_args)
                    except Exception as fe:
                        display_text = f"Format Error: {fe}"
                else:
                    # Якщо шаблону немає, просто з'єднуємо
                    display_text = "".join(map(str, text_or_args))
            else:
                display_text = str(text_or_args)

            if not display_text:
                target_label.hide()
            else:
                target_label.setText(display_text)
                target_label.show()
                
            self.adjustSize()
            if self.anchor_pos:
                self._update_anchor_position()
            self.update()
        except Exception as e:
            print(f"[HUD] Update error: {e}")

    def _set_visible(self, visible):
        if visible:
            self.show()
            self.raise_() # Поверх усіх вікон
        else:
            self.hide()
