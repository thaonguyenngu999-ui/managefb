"""
Login Tab - PyQt6 Version
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QLineEdit, QComboBox, QProgressBar,
    QTextEdit, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor

from config import COLORS, TAB_COLORS


class GlitchLabel(QLabel):
    """Label with glitch effect"""
    def __init__(self, text, color="#00ff66", font_size=42, parent=None):
        super().__init__(text, parent)
        self.base_color = color
        self._is_glitching = False

        self.setStyleSheet(f"""
            color: {color};
            font-family: Consolas;
            font-size: {font_size}px;
            font-weight: bold;
            letter-spacing: 8px;
        """)

        self.glitch_timer = QTimer(self)
        self.glitch_timer.timeout.connect(self._check_glitch)
        self.glitch_timer.start(100)

    def _check_glitch(self):
        import random
        if random.random() > 0.97 and not self._is_glitching:
            self._trigger_glitch()

    def _trigger_glitch(self):
        self._is_glitching = True
        self.setStyleSheet(self.styleSheet().replace(self.base_color, "#ff00a8"))
        QTimer.singleShot(50, lambda: self.setStyleSheet(self.styleSheet().replace("#ff00a8", "#00f0ff")))
        QTimer.singleShot(100, lambda: self.setStyleSheet(self.styleSheet().replace("#00f0ff", self.base_color)))
        QTimer.singleShot(150, self._end_glitch)

    def _end_glitch(self):
        self._is_glitching = False


class TriangleWidget(QWidget):
    """Triangle accent"""
    def __init__(self, color="#00ff66", parent=None):
        super().__init__(parent)
        self.color = QColor(color)
        self.setFixedSize(50, 50)

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QBrush, QPolygon
        from PyQt6.QtCore import QPoint
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(self.color))
        painter.setPen(Qt.PenStyle.NoPen)
        points = [QPoint(5, 45), QPoint(45, 45), QPoint(45, 5)]
        painter.drawPolygon(QPolygon(points))


class CyberTitle(QWidget):
    """Cyberpunk title"""
    def __init__(self, title, subtitle="", color="green", parent=None):
        super().__init__(parent)

        color_map = {
            "cyan": "#00f0ff", "green": "#00ff66", "purple": "#bf00ff",
            "magenta": "#ff00a8", "yellow": "#fcee0a", "orange": "#ff6b00",
        }
        self.accent_color = color_map.get(color, "#00ff66")
        self._line_step = 0

        self._setup_ui(title, subtitle)
        self._start_animations()

    def _setup_ui(self, title, subtitle):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 10)
        layout.setSpacing(0)

        title_row = QHBoxLayout()
        title_row.setSpacing(15)

        self.triangle = TriangleWidget(self.accent_color)
        title_row.addWidget(self.triangle)

        text_wrapper = QVBoxLayout()
        text_wrapper.setSpacing(8)

        self.top_line = QFrame()
        self.top_line.setFixedHeight(2)
        self.top_line.setStyleSheet(f"background-color: {self.accent_color};")
        text_wrapper.addWidget(self.top_line)

        self.title_label = GlitchLabel(title.upper(), self.accent_color)
        text_wrapper.addWidget(self.title_label)

        self.bottom_line = QFrame()
        self.bottom_line.setFixedHeight(2)
        self.bottom_line.setFixedWidth(150)
        self.bottom_line.setStyleSheet(f"background-color: {self.accent_color};")
        text_wrapper.addWidget(self.bottom_line)

        title_row.addLayout(text_wrapper)
        title_row.addStretch()
        layout.addLayout(title_row)

        if subtitle:
            subtitle_layout = QHBoxLayout()
            subtitle_layout.setContentsMargins(65, 12, 0, 0)

            prefix = QLabel("//")
            prefix.setStyleSheet(f"color: {self.accent_color}; font-family: Consolas; font-size: 13px;")
            subtitle_layout.addWidget(prefix)

            sub_label = QLabel(f" {subtitle}")
            sub_label.setStyleSheet("color: #52525b; font-family: Consolas; font-size: 13px;")
            subtitle_layout.addWidget(sub_label)
            subtitle_layout.addStretch()
            layout.addLayout(subtitle_layout)

    def _start_animations(self):
        self._line_timer = QTimer(self)
        self._line_timer.timeout.connect(self._animate_lines)
        self._line_timer.start(50)

    def _animate_lines(self):
        self._line_step = (self._line_step + 1) % 40
        factor = 0.6 + (self._line_step / 20) * 0.4 if self._line_step < 20 else 1.0 - ((self._line_step - 20) / 20) * 0.4
        self.top_line.setFixedWidth(int(300 * factor))
        self.bottom_line.setFixedWidth(int(200 * factor))


class CyberButton(QPushButton):
    """Cyber button"""
    def __init__(self, text, variant="primary", icon="", parent=None):
        display_text = f"{icon} {text}" if icon else text
        super().__init__(display_text.upper(), parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        colors = {
            "primary": ("#00f0ff", "transparent", "#00f0ff"),
            "success": ("#00ff66", "#00ff66", "#05050a"),
            "danger": ("#ff003c", "transparent", "#ff003c"),
            "ghost": ("#1a1a2e", "transparent", "#a1a1aa"),
        }
        border, bg, text_c = colors.get(variant, colors["primary"])

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 6px;
                color: {text_c};
                font-family: Consolas;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 2px;
                padding: 12px 24px;
            }}
            QPushButton:hover {{
                background-color: {border};
                color: #05050a;
            }}
        """)


class LoginTab(QWidget):
    """Facebook Login tab"""

    def __init__(self, log_callback=None, parent=None):
        super().__init__(parent)
        self.log_callback = log_callback

        self._setup_ui()

    def _log(self, msg, level="info"):
        if self.log_callback:
            self.log_callback(msg, level)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(20)

        # Title
        title = CyberTitle("LOGIN FB", "Dang nhap Facebook cho cac profiles", "green")
        layout.addWidget(title)

        # Main content - 2 columns
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # Left panel - Profile selection
        left_panel = QFrame()
        left_panel.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(10,10,20,0.9), stop:1 rgba(5,5,15,0.95));
                border: 1px solid #1a1a2e;
                border-radius: 12px;
            }
        """)
        left_panel.setFixedWidth(300)

        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(12)

        # Left header
        left_header = QLabel("CHON PROFILES")
        left_header.setStyleSheet("color: #00ff66; font-family: Consolas; font-size: 12px; font-weight: bold; letter-spacing: 2px; background: transparent;")
        left_layout.addWidget(left_header)

        # Folder filter
        self.folder_combo = QComboBox()
        self.folder_combo.addItem("-- Tat ca thu muc --")
        self.folder_combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(5, 5, 15, 0.8);
                border: 1px solid #1a1a2e;
                border-radius: 6px;
                color: #e4e4e7;
                font-family: Consolas;
                font-size: 12px;
                padding: 10px 16px;
            }
            QComboBox:focus { border-color: #00ff66; }
        """)
        left_layout.addWidget(self.folder_combo)

        # Select all / deselect all
        btn_row = QHBoxLayout()
        select_all = CyberButton("Chon tat ca", "ghost")
        select_all.setFixedHeight(32)
        btn_row.addWidget(select_all)
        deselect_all = CyberButton("Bo chon", "ghost")
        deselect_all.setFixedHeight(32)
        btn_row.addWidget(deselect_all)
        left_layout.addLayout(btn_row)

        # Profile list (scroll area)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical { background: #020204; width: 8px; }
            QScrollBar::handle:vertical { background: #1a1a2e; border-radius: 4px; }
        """)

        profile_list = QWidget()
        profile_list_layout = QVBoxLayout(profile_list)
        profile_list_layout.setSpacing(4)

        # Sample profiles
        for i in range(5):
            cb = QCheckBox(f"Profile {i+1}")
            cb.setStyleSheet("""
                QCheckBox { color: #e4e4e7; font-family: Consolas; spacing: 8px; }
                QCheckBox::indicator { width: 18px; height: 18px; border: 1px solid #1a1a2e; border-radius: 4px; background: #0a0a12; }
                QCheckBox::indicator:checked { background: #00ff66; border-color: #00ff66; }
            """)
            profile_list_layout.addWidget(cb)

        profile_list_layout.addStretch()
        scroll.setWidget(profile_list)
        left_layout.addWidget(scroll)

        # Stats
        stats_label = QLabel("Profiles: 5 | Da chon: 0")
        stats_label.setStyleSheet("color: #52525b; font-family: Consolas; font-size: 11px; background: transparent;")
        left_layout.addWidget(stats_label)

        content_layout.addWidget(left_panel)

        # Right panel - Login form
        right_panel = QFrame()
        right_panel.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(10,10,20,0.9), stop:1 rgba(5,5,15,0.95));
                border: 1px solid #1a1a2e;
                border-radius: 12px;
            }
        """)

        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(16)

        # Right header
        right_header = QLabel("THONG TIN DANG NHAP")
        right_header.setStyleSheet("color: #00ff66; font-family: Consolas; font-size: 12px; font-weight: bold; letter-spacing: 2px; background: transparent;")
        right_layout.addWidget(right_header)

        # Cookie input
        cookie_label = QLabel("COOKIE:")
        cookie_label.setStyleSheet("color: #a1a1aa; font-family: Consolas; font-size: 11px; background: transparent;")
        right_layout.addWidget(cookie_label)

        self.cookie_input = QTextEdit()
        self.cookie_input.setPlaceholderText("Nhap cookie Facebook...")
        self.cookie_input.setMaximumHeight(100)
        self.cookie_input.setStyleSheet("""
            QTextEdit {
                background-color: rgba(5, 5, 15, 0.8);
                border: 1px solid #1a1a2e;
                border-radius: 6px;
                color: #e4e4e7;
                font-family: Consolas;
                font-size: 12px;
                padding: 12px;
            }
            QTextEdit:focus { border-color: #00ff66; }
        """)
        right_layout.addWidget(self.cookie_input)

        # OR divider
        or_label = QLabel("--- HOAC ---")
        or_label.setStyleSheet("color: #52525b; font-family: Consolas; font-size: 11px; background: transparent;")
        or_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(or_label)

        # Email/Phone input
        email_label = QLabel("EMAIL / PHONE:")
        email_label.setStyleSheet("color: #a1a1aa; font-family: Consolas; font-size: 11px; background: transparent;")
        right_layout.addWidget(email_label)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email hoac so dien thoai...")
        self.email_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(5, 5, 15, 0.8);
                border: 1px solid #1a1a2e;
                border-radius: 6px;
                color: #e4e4e7;
                font-family: Consolas;
                font-size: 13px;
                padding: 12px 16px;
            }
            QLineEdit:focus { border-color: #00ff66; }
        """)
        right_layout.addWidget(self.email_input)

        # Password input
        pass_label = QLabel("PASSWORD:")
        pass_label.setStyleSheet("color: #a1a1aa; font-family: Consolas; font-size: 11px; background: transparent;")
        right_layout.addWidget(pass_label)

        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Mat khau...")
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(5, 5, 15, 0.8);
                border: 1px solid #1a1a2e;
                border-radius: 6px;
                color: #e4e4e7;
                font-family: Consolas;
                font-size: 13px;
                padding: 12px 16px;
            }
            QLineEdit:focus { border-color: #00ff66; }
        """)
        right_layout.addWidget(self.pass_input)

        # 2FA input
        twofa_label = QLabel("2FA CODE (neu co):")
        twofa_label.setStyleSheet("color: #a1a1aa; font-family: Consolas; font-size: 11px; background: transparent;")
        right_layout.addWidget(twofa_label)

        self.twofa_input = QLineEdit()
        self.twofa_input.setPlaceholderText("Ma 2FA...")
        self.twofa_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(5, 5, 15, 0.8);
                border: 1px solid #1a1a2e;
                border-radius: 6px;
                color: #e4e4e7;
                font-family: Consolas;
                font-size: 13px;
                padding: 12px 16px;
            }
            QLineEdit:focus { border-color: #00ff66; }
        """)
        right_layout.addWidget(self.twofa_input)

        right_layout.addStretch()

        # Login button
        login_btn = CyberButton("DANG NHAP", "success", "◆")
        login_btn.clicked.connect(self._do_login)
        right_layout.addWidget(login_btn)

        # Progress
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: #0a0a12;
                border: 1px solid #1a1a2e;
                border-radius: 4px;
                height: 8px;
            }
            QProgressBar::chunk { background-color: #00ff66; border-radius: 3px; }
        """)
        right_layout.addWidget(self.progress)

        content_layout.addWidget(right_panel)
        layout.addLayout(content_layout)

    def _do_login(self):
        self._log("Starting login process...", "info")
        self.progress.setVisible(True)
        self.progress.setValue(0)

        def update_progress():
            val = self.progress.value()
            if val < 100:
                self.progress.setValue(val + 10)
                QTimer.singleShot(200, update_progress)
            else:
                self.progress.setVisible(False)
                self._log("Login completed!", "success")

        QTimer.singleShot(100, update_progress)
