"""
FB Manager Pro - Cyberpunk 2077 Widgets (PyQt6)
Các widget chuẩn theo HTML preview
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTextEdit, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QColor, QPainter, QBrush, QPolygon, QFont

# ========================================
# COLORS - Đúng theo HTML
# ========================================
CYBER_COLORS = {
    # Nền
    "bg_dark": "#05050a",
    "bg_darker": "#020204",
    "bg_card": "#0a0a12",
    "bg_secondary": "#08080f",
    "bg_hover": "#12121f",

    # Neon
    "neon_cyan": "#00f0ff",
    "neon_magenta": "#ff00a8",
    "neon_yellow": "#fcee0a",
    "neon_green": "#00ff66",
    "neon_purple": "#bf00ff",
    "neon_orange": "#ff6b00",
    "neon_red": "#ff003c",

    # Text
    "text_primary": "#e4e4e7",
    "text_secondary": "#a1a1aa",
    "text_muted": "#52525b",

    # Border
    "border": "#1a1a2e",
}

# Tab colors
TAB_COLORS = {
    "profiles": "#00f0ff",
    "login": "#00ff66",
    "pages": "#bf00ff",
    "reels": "#ff00a8",
    "content": "#fcee0a",
    "groups": "#ff6b00",
    "scripts": "#00f0ff",
    "posts": "#00ff66",
}


# ========================================
# GLITCH LABEL - Với cyan/magenta offset
# ========================================
class CyberGlitchLabel(QWidget):
    """
    Label với hiệu ứng glitch như HTML:
    - 3 layers: main, cyan offset, magenta offset
    - Glitch ngẫu nhiên mỗi vài giây
    """

    def __init__(self, text: str, color: str = "#00f0ff", font_size: int = 42, parent=None):
        super().__init__(parent)
        self.text = text
        self.color = color
        self.font_size = font_size
        self._is_glitching = False
        self._glitch_step = 0

        self._setup_ui()
        self._start_animation()

    def _setup_ui(self):
        self.setMinimumHeight(self.font_size + 20)

        font_style = f"""
            font-family: 'Orbitron', 'Consolas', monospace;
            font-size: {self.font_size}px;
            font-weight: bold;
            letter-spacing: 8px;
            background: transparent;
        """

        # Layer 1: Magenta (phía sau, dịch trái)
        self.magenta_layer = QLabel(self.text, self)
        self.magenta_layer.setStyleSheet(f"color: transparent; {font_style}")
        self.magenta_layer.move(-3, 0)
        self.magenta_layer.adjustSize()

        # Layer 2: Cyan (phía sau, dịch phải)
        self.cyan_layer = QLabel(self.text, self)
        self.cyan_layer.setStyleSheet(f"color: transparent; {font_style}")
        self.cyan_layer.move(3, 0)
        self.cyan_layer.adjustSize()

        # Layer 3: Main (phía trước)
        self.main_layer = QLabel(self.text, self)
        self.main_layer.setStyleSheet(f"color: {self.color}; {font_style}")
        self.main_layer.move(0, 0)
        self.main_layer.adjustSize()

        # Set widget size
        self.setMinimumWidth(self.main_layer.width() + 10)
        self.setMinimumHeight(self.main_layer.height())

    def _start_animation(self):
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(100)  # 100ms per frame

    def _animate(self):
        import random

        self._glitch_step = (self._glitch_step + 1) % 80  # 80 frames = 8 giây

        try:
            # Glitch trong 3 frames đầu (frame 0, 1, 2)
            if self._glitch_step < 3:
                # Hiện các layer offset
                offset = 3 if self._glitch_step % 2 == 0 else -3

                self.cyan_layer.setStyleSheet(f"""
                    color: rgba(0, 240, 255, 0.8);
                    font-family: 'Orbitron', 'Consolas', monospace;
                    font-size: {self.font_size}px;
                    font-weight: bold;
                    letter-spacing: 8px;
                    background: transparent;
                """)
                self.cyan_layer.move(offset + random.randint(-2, 2), random.randint(-1, 1))

                self.magenta_layer.setStyleSheet(f"""
                    color: rgba(255, 0, 168, 0.8);
                    font-family: 'Orbitron', 'Consolas', monospace;
                    font-size: {self.font_size}px;
                    font-weight: bold;
                    letter-spacing: 8px;
                    background: transparent;
                """)
                self.magenta_layer.move(-offset + random.randint(-2, 2), random.randint(-1, 1))

            else:
                # Ẩn các layer offset
                self.cyan_layer.setStyleSheet(f"""
                    color: transparent;
                    font-family: 'Orbitron', 'Consolas', monospace;
                    font-size: {self.font_size}px;
                    font-weight: bold;
                    letter-spacing: 8px;
                    background: transparent;
                """)
                self.magenta_layer.setStyleSheet(f"""
                    color: transparent;
                    font-family: 'Orbitron', 'Consolas', monospace;
                    font-size: {self.font_size}px;
                    font-weight: bold;
                    letter-spacing: 8px;
                    background: transparent;
                """)
                self.cyan_layer.move(3, 0)
                self.magenta_layer.move(-3, 0)
        except:
            pass  # Widget đã bị destroy


# ========================================
# TRIANGLE WIDGET - Tam giác accent
# ========================================
class CyberTriangle(QWidget):
    """Tam giác accent ◢"""

    def __init__(self, color: str = "#00f0ff", size: int = 50, parent=None):
        super().__init__(parent)
        self.color = QColor(color)
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(self.color))
        painter.setPen(Qt.PenStyle.NoPen)

        # Tam giác góc dưới phải
        size = self.width()
        points = [
            QPoint(5, size - 5),
            QPoint(size - 5, size - 5),
            QPoint(size - 5, 5)
        ]
        painter.drawPolygon(QPolygon(points))

    def set_color(self, color: str):
        self.color = QColor(color)
        self.update()


# ========================================
# CYBER TITLE - Title với glitch và animated lines
# ========================================
class CyberTitle(QWidget):
    """
    Title chuẩn Cyberpunk:
    - Tam giác accent
    - Đường kẻ animated
    - Text với glitch effect
    - Subtitle với prefix //
    """

    def __init__(self, title: str, subtitle: str = "", color: str = "cyan", parent=None):
        super().__init__(parent)

        color_map = {
            "cyan": "#00f0ff",
            "green": "#00ff66",
            "purple": "#bf00ff",
            "magenta": "#ff00a8",
            "yellow": "#fcee0a",
            "orange": "#ff6b00",
        }
        self.accent_color = color_map.get(color, "#00f0ff")
        self._line_step = 0

        self._setup_ui(title, subtitle)
        self._start_line_animation()

    def _setup_ui(self, title: str, subtitle: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 10)
        layout.setSpacing(0)

        # Row chứa triangle + title
        title_row = QHBoxLayout()
        title_row.setSpacing(15)

        # Triangle accent
        self.triangle = CyberTriangle(self.accent_color, 50)
        title_row.addWidget(self.triangle)

        # Text wrapper
        text_wrapper = QVBoxLayout()
        text_wrapper.setSpacing(8)

        # Đường kẻ trên (animated)
        self.top_line = QFrame()
        self.top_line.setFixedHeight(2)
        self.top_line.setFixedWidth(300)
        self.top_line.setStyleSheet(f"background-color: {self.accent_color};")
        text_wrapper.addWidget(self.top_line)

        # Title với glitch
        self.title_label = CyberGlitchLabel(title.upper(), self.accent_color, 42)
        text_wrapper.addWidget(self.title_label)

        # Đường kẻ dưới (ngắn hơn, animated)
        self.bottom_line = QFrame()
        self.bottom_line.setFixedHeight(2)
        self.bottom_line.setFixedWidth(150)
        self.bottom_line.setStyleSheet(f"background-color: {self.accent_color};")
        text_wrapper.addWidget(self.bottom_line)

        title_row.addLayout(text_wrapper)
        title_row.addStretch()
        layout.addLayout(title_row)

        # Subtitle
        if subtitle:
            sub_layout = QHBoxLayout()
            sub_layout.setContentsMargins(65, 12, 0, 0)

            prefix = QLabel("//")
            prefix.setStyleSheet(f"""
                color: {self.accent_color};
                font-family: 'Share Tech Mono', 'Consolas', monospace;
                font-size: 13px;
            """)
            sub_layout.addWidget(prefix)

            sub_text = QLabel(f" {subtitle}")
            sub_text.setStyleSheet(f"""
                color: {CYBER_COLORS['text_muted']};
                font-family: 'Share Tech Mono', 'Consolas', monospace;
                font-size: 13px;
                letter-spacing: 3px;
            """)
            sub_layout.addWidget(sub_text)
            sub_layout.addStretch()

            layout.addLayout(sub_layout)

    def _start_line_animation(self):
        self._line_timer = QTimer(self)
        self._line_timer.timeout.connect(self._animate_lines)
        self._line_timer.start(50)

    def _animate_lines(self):
        self._line_step = (self._line_step + 1) % 40

        # Tính factor: 0.6 -> 1.0 -> 0.6
        if self._line_step < 20:
            factor = 0.6 + (self._line_step / 20) * 0.4
        else:
            factor = 1.0 - ((self._line_step - 20) / 20) * 0.4

        try:
            self.top_line.setFixedWidth(int(300 * factor))
            self.bottom_line.setFixedWidth(int(200 * factor))
        except:
            pass


# ========================================
# STAT CARD - Card thống kê với accent bar
# ========================================
class CyberStatCard(QFrame):
    """
    Card thống kê chuẩn Cyberpunk:
    - Accent bar 3px trên cùng
    - Label nhỏ (text_muted)
    - Value lớn (neon color)
    - Change text (optional)
    - Icon (optional)

    Supports two signatures:
    1. CyberStatCard(label, value, change="", color="cyan") - profiles style
    2. CyberStatCard(icon, label, value, color) - reels/posts style
    """

    def __init__(self, arg1: str, arg2: str, arg3: str = "", arg4: str = "cyan", parent=None):
        super().__init__(parent)

        # Detect signature based on arg3 - if it's a color name, use icon style
        color_names = {"cyan", "green", "purple", "yellow", "magenta", "orange", "red"}

        if arg3 in color_names or (arg4 in color_names and len(arg3) <= 3):
            # Icon style: (icon, label, value, color)
            self.icon = arg1
            self.label_text = arg2
            self.value_text = arg3
            self.color_name = arg4
            self.change_text = ""
        else:
            # Label style: (label, value, change, color)
            self.icon = ""
            self.label_text = arg1
            self.value_text = arg2
            self.change_text = arg3
            self.color_name = arg4

        color_map = {
            "cyan": "#00f0ff",
            "green": "#00ff66",
            "purple": "#bf00ff",
            "yellow": "#fcee0a",
            "magenta": "#ff00a8",
            "orange": "#ff6b00",
            "red": "#ff003c",
        }
        self.accent_color = color_map.get(self.color_name, "#00f0ff")

        self.setObjectName("statCard")
        self.setStyleSheet(f"""
            QFrame#statCard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(10,10,20,0.8),
                    stop:1 rgba(5,5,15,0.9));
                border: 1px solid {CYBER_COLORS['border']};
                border-radius: 12px;
            }}
            QFrame#statCard:hover {{
                border-color: {self.accent_color}50;
            }}
        """)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Accent bar trên cùng
        accent_bar = QFrame()
        accent_bar.setFixedHeight(3)
        accent_bar.setStyleSheet(f"background-color: {self.accent_color}; border-radius: 0;")
        layout.addWidget(accent_bar)

        # Content
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 20, 24, 20)

        # Icon (if present)
        if self.icon:
            icon_lbl = QLabel(self.icon)
            icon_lbl.setStyleSheet(f"font-size: 28px; color: {self.accent_color};")
            content_layout.addWidget(icon_lbl)

        # Label
        lbl = QLabel(self.label_text.upper())
        lbl.setStyleSheet(f"""
            color: {CYBER_COLORS['text_muted']};
            font-family: 'Share Tech Mono', 'Consolas', monospace;
            font-size: 10px;
            letter-spacing: 2px;
        """)
        content_layout.addWidget(lbl)

        # Value (số lớn)
        self.value_label = QLabel(self.value_text)
        self.value_label.setStyleSheet(f"""
            color: {self.accent_color};
            font-family: 'Orbitron', 'Consolas', monospace;
            font-size: 42px;
            font-weight: bold;
        """)
        content_layout.addWidget(self.value_label)

        # Change
        if self.change_text:
            change_color = CYBER_COLORS['neon_green'] if self.change_text.startswith("+") or self.change_text.startswith("▲") else CYBER_COLORS['text_muted']
            change_lbl = QLabel(self.change_text)
            change_lbl.setStyleSheet(f"""
                color: {change_color};
                font-family: 'Share Tech Mono', 'Consolas', monospace;
                font-size: 11px;
            """)
            content_layout.addWidget(change_lbl)

        layout.addWidget(content)

    def set_value(self, value: str):
        self.value_label.setText(value)

    # Alias for backwards compatibility
    def update_value(self, value: str):
        self.set_value(value)


# ========================================
# CYBER BUTTON - Nút với viền neon
# ========================================
class CyberButton(QPushButton):
    """
    Button chuẩn Cyberpunk:
    - Viền neon
    - Hover đổi màu nền
    """

    def __init__(self, text: str, variant: str = "primary", icon: str = "", parent=None):
        display_text = f"{icon} {text}" if icon else text
        super().__init__(display_text.upper(), parent)

        self.setCursor(Qt.CursorShape.PointingHandCursor)

        colors = {
            "primary": ("#00f0ff", "transparent"),
            "success": ("#00ff66", "transparent"),
            "danger": ("#ff003c", "transparent"),
            "ghost": ("#1a1a2e", "transparent"),
            "secondary": ("#ff00a8", "transparent"),
        }

        border_color, bg_color = colors.get(variant, colors["primary"])

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 6px;
                color: {border_color};
                font-family: 'Orbitron', 'Consolas', monospace;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 2px;
                padding: 12px 24px;
            }}
            QPushButton:hover {{
                background-color: {border_color};
                color: {CYBER_COLORS['bg_dark']};
            }}
        """)


# ========================================
# CYBER BADGE - Nhãn trạng thái
# ========================================
class CyberBadge(QFrame):
    """
    Badge với LED indicator:
    - Border left 3px
    - LED pulse (optional)
    """

    def __init__(self, text: str, color: str = "cyan", show_led: bool = False, pulse: bool = False, parent=None):
        super().__init__(parent)

        color_map = {
            "cyan": "#00f0ff",
            "green": "#00ff66",
            "purple": "#bf00ff",
            "yellow": "#fcee0a",
            "gray": "#52525b",
            "red": "#ff003c",
        }
        self.accent_color = color_map.get(color, "#00f0ff")
        self._pulse_on = True

        self.setStyleSheet(f"""
            QFrame {{
                background: {self.accent_color}15;
                border-left: 3px solid {self.accent_color};
                border-radius: 6px;
                padding: 6px 14px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 12, 6)
        layout.setSpacing(6)

        # LED
        if show_led:
            self.led = QLabel("●")
            self.led.setStyleSheet(f"""
                color: {self.accent_color};
                font-size: 8px;
            """)
            layout.addWidget(self.led)

            if pulse:
                self._start_pulse()

        # Text
        label = QLabel(text.upper())
        label.setStyleSheet(f"""
            color: {self.accent_color};
            font-family: 'Orbitron', 'Consolas', monospace;
            font-size: 10px;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        layout.addWidget(label)

    def _start_pulse(self):
        def pulse():
            try:
                if self._pulse_on:
                    self.led.setStyleSheet(f"color: {self.accent_color}; font-size: 8px;")
                else:
                    self.led.setStyleSheet(f"color: transparent; font-size: 8px;")
                self._pulse_on = not self._pulse_on
                QTimer.singleShot(750, pulse)
            except:
                pass
        pulse()


# ========================================
# CYBER TERMINAL - Log viewer
# ========================================
class CyberTerminal(QTextEdit):
    """
    Terminal log với màu theo level:
    - info: cyan
    - success: green
    - warning: yellow
    - error: red
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: rgba(0, 0, 0, 0.5);
                border: 1px solid {CYBER_COLORS['border']};
                border-radius: 8px;
                color: {CYBER_COLORS['text_secondary']};
                font-family: 'Share Tech Mono', 'Consolas', monospace;
                font-size: 11px;
                padding: 16px;
            }}
        """)

    def add_log(self, message: str, level: str = "info"):
        from datetime import datetime
        timestamp = datetime.now().strftime("[%H:%M:%S]")

        colors = {
            "info": CYBER_COLORS['neon_cyan'],
            "success": CYBER_COLORS['neon_green'],
            "warning": CYBER_COLORS['neon_yellow'],
            "error": CYBER_COLORS['neon_red'],
        }
        color = colors.get(level, CYBER_COLORS['text_secondary'])

        html = f'<span style="color: {CYBER_COLORS["text_muted"]};">{timestamp}</span> '
        html += f'<span style="color: {color};">{message}</span><br>'

        self.append(html)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def clear_logs(self):
        self.clear()


# ========================================
# CYBER CARD - Container với header
# ========================================
class CyberCard(QFrame):
    """Card container với header optional"""

    def __init__(self, title: str = "", accent_color: str = "#00f0ff", count: str = "", parent=None):
        super().__init__(parent)
        self.accent_color = accent_color

        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(10,10,20,0.9),
                    stop:1 rgba(5,5,15,0.95));
                border: 1px solid {CYBER_COLORS['border']};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header (optional)
        if title:
            header = QFrame()
            header.setStyleSheet(f"""
                QFrame {{
                    background: rgba(0, 240, 255, 0.02);
                    border-bottom: 1px solid {CYBER_COLORS['border']};
                    border-radius: 12px 12px 0 0;
                }}
            """)
            header_layout = QHBoxLayout(header)
            header_layout.setContentsMargins(16, 14, 16, 14)

            # Accent bar
            accent = QFrame()
            accent.setFixedSize(4, 24)
            accent.setStyleSheet(f"background: {accent_color}; border-radius: 2px;")
            header_layout.addWidget(accent)

            # Title
            title_lbl = QLabel(title.upper())
            title_lbl.setStyleSheet(f"""
                color: {CYBER_COLORS['text_primary']};
                font-family: 'Orbitron', 'Consolas', monospace;
                font-size: 12px;
                font-weight: bold;
                letter-spacing: 2px;
            """)
            header_layout.addWidget(title_lbl)

            # Count
            if count:
                count_lbl = QLabel(count)
                count_lbl.setStyleSheet(f"""
                    color: {accent_color};
                    font-family: 'Orbitron', 'Consolas', monospace;
                    font-size: 12px;
                    font-weight: bold;
                """)
                header_layout.addWidget(count_lbl)

            header_layout.addStretch()
            layout.addWidget(header)

        # Content frame
        self.content = QFrame()
        self.content.setStyleSheet("background: transparent; border: none;")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(16, 16, 16, 16)
        layout.addWidget(self.content, 1)
