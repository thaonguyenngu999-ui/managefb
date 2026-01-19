"""
Profiles Tab - PyQt6 Version
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox, QLineEdit, QComboBox, QProgressBar,
    QAbstractItemView, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor

from config import COLORS, TAB_COLORS

# Import from main_qt for widgets
import sys
sys.path.insert(0, '..')


class GlitchLabel(QLabel):
    """Label with glitch effect"""
    def __init__(self, text, color="#00f0ff", font_size=42, parent=None):
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
    def __init__(self, color="#00f0ff", parent=None):
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
    def __init__(self, title, subtitle="", color="cyan", parent=None):
        super().__init__(parent)

        color_map = {
            "cyan": "#00f0ff", "green": "#00ff66", "purple": "#bf00ff",
            "magenta": "#ff00a8", "yellow": "#fcee0a", "orange": "#ff6b00",
        }
        self.accent_color = color_map.get(color, "#00f0ff")
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


class CyberStatCard(QFrame):
    """Stat card"""
    def __init__(self, label, value, change="", color="cyan", parent=None):
        super().__init__(parent)
        color_map = {"cyan": "#00f0ff", "green": "#00ff66", "purple": "#bf00ff", "yellow": "#fcee0a"}
        self.accent_color = color_map.get(color, "#00f0ff")

        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(10,10,20,0.8), stop:1 rgba(5,5,15,0.9));
                border: 1px solid #1a1a2e;
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        top_bar = QFrame()
        top_bar.setFixedHeight(3)
        top_bar.setStyleSheet(f"background-color: {self.accent_color}; border-radius: 0;")
        layout.addWidget(top_bar)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 20, 24, 20)

        lbl = QLabel(label.upper())
        lbl.setStyleSheet("color: #52525b; font-family: Consolas; font-size: 10px; letter-spacing: 2px; background: transparent;")
        content_layout.addWidget(lbl)

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"color: {self.accent_color}; font-family: Consolas; font-size: 42px; font-weight: bold; background: transparent;")
        content_layout.addWidget(self.value_label)

        if change:
            change_color = "#00ff66" if change.startswith("+") else "#52525b"
            change_lbl = QLabel(change)
            change_lbl.setStyleSheet(f"color: {change_color}; font-family: Consolas; font-size: 11px; background: transparent;")
            content_layout.addWidget(change_lbl)

        layout.addWidget(content)

    def update_value(self, new_value):
        self.value_label.setText(new_value)


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


class ProfilesTab(QWidget):
    """Profiles management tab"""

    def __init__(self, log_callback=None, parent=None):
        super().__init__(parent)
        self.log_callback = log_callback
        self.profiles = []

        self._setup_ui()
        self._load_profiles()

    def _log(self, msg, level="info"):
        if self.log_callback:
            self.log_callback(msg, level)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(20)

        # Title
        title = CyberTitle("PROFILES", "Quan ly va dieu khien cac tai khoan Facebook", "cyan")
        layout.addWidget(title)

        # Stats row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(20)

        self.stat_total = CyberStatCard("TONG SO", "0", "", "cyan")
        stats_row.addWidget(self.stat_total)

        self.stat_running = CyberStatCard("DANG CHAY", "0", "● Active", "green")
        stats_row.addWidget(self.stat_running)

        self.stat_selected = CyberStatCard("DA CHON", "0", "", "purple")
        stats_row.addWidget(self.stat_selected)

        self.stat_used = CyberStatCard("DA DUNG", "0", "", "yellow")
        stats_row.addWidget(self.stat_used)

        layout.addLayout(stats_row)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(14)

        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Tim kiem profile...")
        self.search_input.setObjectName("cyberInput")
        self.search_input.setFixedWidth(280)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(5, 5, 15, 0.8);
                border: 1px solid #1a1a2e;
                border-radius: 6px;
                color: #e4e4e7;
                font-family: Consolas;
                font-size: 13px;
                padding: 12px 16px;
            }
            QLineEdit:focus { border-color: #00f0ff; }
        """)
        toolbar.addWidget(self.search_input)

        # Scan button
        scan_btn = CyberButton("SCAN", "primary", "⌕")
        scan_btn.clicked.connect(self._scan_profiles)
        toolbar.addWidget(scan_btn)

        # Filters
        self.filter_all = QPushButton("○ Tat ca")
        self.filter_all.setCheckable(True)
        self.filter_all.setChecked(True)
        self.filter_all.setStyleSheet("""
            QPushButton { background: transparent; border: none; color: #00f0ff; font-family: Consolas; padding: 8px 16px; }
            QPushButton:checked { color: #00f0ff; }
        """)
        toolbar.addWidget(self.filter_all)

        self.filter_running = QPushButton("○ Dang chay")
        self.filter_running.setCheckable(True)
        self.filter_running.setStyleSheet("""
            QPushButton { background: transparent; border: none; color: #a1a1aa; font-family: Consolas; padding: 8px 16px; }
            QPushButton:checked { color: #00ff66; }
        """)
        toolbar.addWidget(self.filter_running)

        self.filter_stopped = QPushButton("○ Da dung")
        self.filter_stopped.setCheckable(True)
        self.filter_stopped.setStyleSheet("""
            QPushButton { background: transparent; border: none; color: #a1a1aa; font-family: Consolas; padding: 8px 16px; }
        """)
        toolbar.addWidget(self.filter_stopped)

        toolbar.addStretch()

        # Folder dropdown
        self.folder_combo = QComboBox()
        self.folder_combo.addItem("Tat ca thu muc")
        self.folder_combo.setObjectName("cyberDropdown")
        self.folder_combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(5, 5, 15, 0.8);
                border: 1px solid #1a1a2e;
                border-radius: 6px;
                color: #e4e4e7;
                font-family: Consolas;
                font-size: 12px;
                padding: 10px 16px;
                min-width: 150px;
            }
            QComboBox:focus { border-color: #00f0ff; }
            QComboBox::drop-down { border: none; width: 30px; }
            QComboBox::down-arrow { border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 5px solid #00f0ff; }
        """)
        toolbar.addWidget(self.folder_combo)

        # Action buttons
        open_all_btn = CyberButton("MO TAT CA", "success")
        open_all_btn.clicked.connect(self._open_all)
        toolbar.addWidget(open_all_btn)

        close_all_btn = CyberButton("DONG TAT CA", "danger")
        close_all_btn.clicked.connect(self._close_all)
        toolbar.addWidget(close_all_btn)

        delete_btn = CyberButton("XOA", "ghost", "×")
        toolbar.addWidget(delete_btn)

        layout.addLayout(toolbar)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: #0a0a12;
                border: 1px solid #1a1a2e;
                border-radius: 4px;
                height: 8px;
            }
            QProgressBar::chunk { background-color: #00f0ff; border-radius: 3px; }
        """)
        layout.addWidget(self.progress)

        # Loading indicator
        self.loading_label = QLabel("// LOADING PROFILES...")
        self.loading_label.setStyleSheet("color: #00f0ff; font-family: Consolas; font-size: 13px;")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.loading_label)

        # Table
        self.table = QTableWidget()
        self.table.setObjectName("cyberTable")
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["", "PROFILE", "STATUS", "FOLDER", "LAST", "ACTION"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 80)
        self.table.setColumnWidth(5, 100)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(False)
        self.table.setShowGrid(False)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: rgba(10,10,20,0.9);
                border: 1px solid #1a1a2e;
                border-radius: 12px;
                gridline-color: #1a1a2e;
            }
            QTableWidget::item {
                padding: 12px 16px;
                border-bottom: 1px solid #1a1a2e;
                color: #e4e4e7;
            }
            QTableWidget::item:hover { background-color: rgba(0, 240, 255, 0.03); }
            QTableWidget::item:selected { background-color: rgba(0, 240, 255, 0.1); color: #00f0ff; }
            QHeaderView::section {
                background-color: rgba(0, 240, 255, 0.05);
                border: none;
                border-bottom: 1px solid #1a1a2e;
                color: #00f0ff;
                font-family: Consolas;
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 2px;
                padding: 16px;
            }
        """)
        layout.addWidget(self.table)

    def _load_profiles(self):
        """Load profiles from database/API"""
        self.loading_label.setVisible(True)
        self._log("Loading profiles...", "info")

        # Simulate loading
        QTimer.singleShot(500, self._on_profiles_loaded)

    def _on_profiles_loaded(self):
        """Called when profiles are loaded"""
        try:
            from db import get_profiles
            self.profiles = get_profiles() or []
        except Exception as e:
            self.profiles = []
            self._log(f"Error loading profiles: {e}", "error")

        self.loading_label.setVisible(False)
        self._update_stats()
        self._render_table()
        self._log(f"Loaded {len(self.profiles)} profiles", "success")

    def _update_stats(self):
        total = len(self.profiles)
        running = sum(1 for p in self.profiles if p.get('status') == 'running')

        self.stat_total.update_value(str(total))
        self.stat_running.update_value(str(running))
        self.stat_selected.update_value("0")
        self.stat_used.update_value(str(total))

    def _render_table(self):
        self.table.setRowCount(len(self.profiles))

        for row, profile in enumerate(self.profiles):
            # Checkbox
            cb = QCheckBox()
            cb.setStyleSheet("""
                QCheckBox::indicator { width: 18px; height: 18px; border: 1px solid #1a1a2e; border-radius: 4px; background: #0a0a12; }
                QCheckBox::indicator:checked { background: #00f0ff; border-color: #00f0ff; }
            """)
            self.table.setCellWidget(row, 0, cb)

            # Profile name
            name = profile.get('name', 'Unknown')
            uuid_short = profile.get('uuid', '')[:12] + '...'
            name_widget = QWidget()
            name_layout = QVBoxLayout(name_widget)
            name_layout.setContentsMargins(8, 8, 8, 8)
            name_label = QLabel(name)
            name_label.setStyleSheet("color: #e4e4e7; font-weight: bold;")
            name_layout.addWidget(name_label)
            uuid_label = QLabel(uuid_short)
            uuid_label.setStyleSheet("color: #52525b; font-size: 10px;")
            name_layout.addWidget(uuid_label)
            self.table.setCellWidget(row, 1, name_widget)

            # Status
            status = profile.get('status', 'stopped')
            status_widget = QWidget()
            status_layout = QHBoxLayout(status_widget)
            status_layout.setContentsMargins(8, 8, 8, 8)

            if status == 'running':
                badge = QFrame()
                badge.setStyleSheet("""
                    background-color: rgba(0, 255, 102, 0.1);
                    border-left: 3px solid #00ff66;
                    border-radius: 6px;
                    padding: 6px 14px;
                """)
                badge_layout = QHBoxLayout(badge)
                badge_layout.setContentsMargins(10, 6, 14, 6)
                dot = QFrame()
                dot.setFixedSize(8, 8)
                dot.setStyleSheet("background-color: #00ff66; border-radius: 4px;")
                badge_layout.addWidget(dot)
                text = QLabel("RUNNING")
                text.setStyleSheet("color: #00ff66; font-family: Consolas; font-size: 10px; font-weight: bold;")
                badge_layout.addWidget(text)
                status_layout.addWidget(badge)
            else:
                badge = QFrame()
                badge.setStyleSheet("""
                    background-color: rgba(100, 100, 100, 0.1);
                    border-left: 3px solid #52525b;
                    border-radius: 6px;
                """)
                badge_layout = QHBoxLayout(badge)
                badge_layout.setContentsMargins(10, 6, 14, 6)
                dot = QFrame()
                dot.setFixedSize(8, 8)
                dot.setStyleSheet("background-color: #52525b; border-radius: 4px;")
                badge_layout.addWidget(dot)
                text = QLabel("STOPPED")
                text.setStyleSheet("color: #52525b; font-family: Consolas; font-size: 10px; font-weight: bold;")
                badge_layout.addWidget(text)
                status_layout.addWidget(badge)

            status_layout.addStretch()
            self.table.setCellWidget(row, 2, status_widget)

            # Folder
            folder = profile.get('folder_name', 'Default')
            folder_item = QTableWidgetItem(folder)
            folder_item.setForeground(QColor("#a1a1aa"))
            self.table.setItem(row, 3, folder_item)

            # Last used
            last = "2m"
            last_item = QTableWidgetItem(last)
            last_item.setForeground(QColor("#52525b"))
            self.table.setItem(row, 4, last_item)

            # Action button
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(8, 8, 8, 8)

            if status == 'running':
                btn = CyberButton("STOP", "ghost")
            else:
                btn = CyberButton("MO", "success")
            btn.setFixedWidth(80)
            action_layout.addWidget(btn)
            self.table.setCellWidget(row, 5, action_widget)

        self.table.resizeRowsToContents()

    def _scan_profiles(self):
        self._log("Scanning profiles...", "info")
        self.progress.setVisible(True)
        self.progress.setValue(0)

        # Simulate scan
        def update_progress():
            val = self.progress.value()
            if val < 100:
                self.progress.setValue(val + 10)
                QTimer.singleShot(100, update_progress)
            else:
                self.progress.setVisible(False)
                self._load_profiles()

        QTimer.singleShot(100, update_progress)

    def _open_all(self):
        self._log("Opening all selected profiles...", "info")

    def _close_all(self):
        self._log("Closing all running profiles...", "warning")
