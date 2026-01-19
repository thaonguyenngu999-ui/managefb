"""
FB Manager Pro - Reels Tab (PyQt6)
Cyberpunk 2077 Theme
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QLineEdit, QComboBox, QCheckBox, QProgressBar, QTextEdit,
    QSpinBox, QFileDialog, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon

# Cyberpunk colors
CYBER_COLORS = {
    "cyan": "#00f0ff",
    "magenta": "#ff00a8",
    "green": "#00ff66",
    "yellow": "#f0ff00",
    "orange": "#ff6600",
    "bg_dark": "#0a0a12",
    "bg_card": "#12121f",
    "bg_lighter": "#1a1a2e",
    "text": "#e0e0e0",
    "text_dim": "#808080"
}


class CyberTitle(QFrame):
    """Cyberpunk styled title with glitch effect"""

    def __init__(self, text: str, color: str = "cyan", parent=None):
        super().__init__(parent)
        self.text = text
        self.color = CYBER_COLORS.get(color, color)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 10)

        # Triangle accent
        triangle = QLabel("▶")
        triangle.setStyleSheet(f"color: {self.color}; font-size: 16px;")
        layout.addWidget(triangle)

        # Title text
        title = QLabel(self.text)
        title.setStyleSheet(f"""
            color: {self.color};
            font-size: 24px;
            font-weight: bold;
            font-family: 'Orbitron', 'Rajdhani', 'Consolas', monospace;
            letter-spacing: 2px;
        """)
        layout.addWidget(title)

        # Glowing line
        line = QFrame()
        line.setFixedHeight(2)
        line.setStyleSheet(f"""
            background: qlineargradient(x1:0, x2:1,
                stop:0 {self.color},
                stop:0.5 {self.color}80,
                stop:1 transparent);
        """)
        layout.addWidget(line, 1)


class CyberStatCard(QFrame):
    """Cyberpunk stat card with icon and value"""

    def __init__(self, icon: str, label: str, value: str, color: str = "cyan", parent=None):
        super().__init__(parent)
        self.color = CYBER_COLORS.get(color, color)
        self.setObjectName("statCard")
        self.setProperty("color", color)
        self._setup_ui(icon, label, value)

    def _setup_ui(self, icon: str, label: str, value: str):
        self.setStyleSheet(f"""
            QFrame#statCard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {CYBER_COLORS['bg_card']},
                    stop:1 {CYBER_COLORS['bg_lighter']});
                border: 1px solid {self.color}40;
                border-radius: 8px;
                padding: 15px;
            }}
            QFrame#statCard:hover {{
                border: 1px solid {self.color};
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {self.color}15,
                    stop:1 {CYBER_COLORS['bg_card']});
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Icon and value row
        top_row = QHBoxLayout()

        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"font-size: 28px; color: {self.color};")
        top_row.addWidget(icon_label)

        top_row.addStretch()

        value_label = QLabel(value)
        value_label.setObjectName("statValue")
        value_label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: bold;
            color: {self.color};
            font-family: 'Orbitron', 'Rajdhani', monospace;
        """)
        top_row.addWidget(value_label)
        self.value_label = value_label

        layout.addLayout(top_row)

        # Label
        text_label = QLabel(label)
        text_label.setStyleSheet(f"""
            color: {CYBER_COLORS['text_dim']};
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
        """)
        layout.addWidget(text_label)

    def set_value(self, value: str):
        self.value_label.setText(value)


class CyberButton(QPushButton):
    """Cyberpunk styled button"""

    def __init__(self, text: str, color: str = "cyan", icon: str = None, parent=None):
        display_text = f"{icon} {text}" if icon and text else (icon or text)
        super().__init__(display_text, parent)
        self.color = CYBER_COLORS.get(color, color)
        self.setObjectName("cyberButton")
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(f"""
            QPushButton#cyberButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.color}30,
                    stop:1 {self.color}10);
                border: 1px solid {self.color};
                border-radius: 4px;
                color: {self.color};
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            QPushButton#cyberButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.color}50,
                    stop:1 {self.color}30);
                border: 2px solid {self.color};
            }}
            QPushButton#cyberButton:pressed {{
                background: {self.color}60;
            }}
        """)


class ReelsTabQt(QWidget):
    """Reels management tab with Cyberpunk styling"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("reelsTab")
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Left panel - Profile selection
        left_panel = self._create_profile_panel()
        main_layout.addWidget(left_panel)

        # Right panel - Reels management
        right_panel = self._create_reels_panel()
        main_layout.addWidget(right_panel, 1)

    def _create_profile_panel(self):
        """Create profile selection panel"""
        panel = QFrame()
        panel.setObjectName("profilePanel")
        panel.setFixedWidth(280)
        panel.setStyleSheet(f"""
            QFrame#profilePanel {{
                background: {CYBER_COLORS['bg_card']};
                border: 1px solid {CYBER_COLORS['magenta']}40;
                border-radius: 10px;
            }}
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Title
        title = CyberTitle("PROFILES", "magenta")
        layout.addWidget(title)

        # Search
        search = QLineEdit()
        search.setPlaceholderText("🔍 Search profiles...")
        search.setStyleSheet(f"""
            QLineEdit {{
                background: {CYBER_COLORS['bg_dark']};
                border: 1px solid {CYBER_COLORS['magenta']}40;
                border-radius: 5px;
                padding: 10px;
                color: {CYBER_COLORS['text']};
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1px solid {CYBER_COLORS['magenta']};
            }}
        """)
        layout.addWidget(search)

        # Profile list (scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)

        profile_container = QWidget()
        profile_layout = QVBoxLayout(profile_container)
        profile_layout.setSpacing(8)

        # Sample profiles
        profiles = [
            ("John Doe", "Active", True),
            ("Jane Smith", "Idle", False),
            ("Mike Johnson", "Active", True),
            ("Sarah Wilson", "Offline", False),
        ]

        for name, status, checked in profiles:
            profile_item = self._create_profile_item(name, status, checked)
            profile_layout.addWidget(profile_item)

        profile_layout.addStretch()
        scroll.setWidget(profile_container)
        layout.addWidget(scroll, 1)

        # Select all checkbox
        select_all = QCheckBox("Select All Profiles")
        select_all.setStyleSheet(f"""
            QCheckBox {{
                color: {CYBER_COLORS['text']};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {CYBER_COLORS['magenta']};
                border-radius: 3px;
                background: transparent;
            }}
            QCheckBox::indicator:checked {{
                background: {CYBER_COLORS['magenta']};
            }}
        """)
        layout.addWidget(select_all)

        return panel

    def _create_profile_item(self, name: str, status: str, checked: bool):
        """Create a single profile item"""
        item = QFrame()
        item.setStyleSheet(f"""
            QFrame {{
                background: {CYBER_COLORS['bg_lighter']};
                border: 1px solid {CYBER_COLORS['magenta']}30;
                border-radius: 5px;
                padding: 8px;
            }}
            QFrame:hover {{
                border: 1px solid {CYBER_COLORS['magenta']};
                background: {CYBER_COLORS['magenta']}10;
            }}
        """)

        layout = QHBoxLayout(item)
        layout.setContentsMargins(8, 8, 8, 8)

        checkbox = QCheckBox()
        checkbox.setChecked(checked)
        checkbox.setStyleSheet(f"""
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid {CYBER_COLORS['magenta']};
                border-radius: 3px;
            }}
            QCheckBox::indicator:checked {{
                background: {CYBER_COLORS['magenta']};
            }}
        """)
        layout.addWidget(checkbox)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        name_label = QLabel(name)
        name_label.setStyleSheet(f"color: {CYBER_COLORS['text']}; font-weight: bold;")
        info_layout.addWidget(name_label)

        status_color = CYBER_COLORS['green'] if status == "Active" else (
            CYBER_COLORS['yellow'] if status == "Idle" else CYBER_COLORS['text_dim']
        )
        status_label = QLabel(f"● {status}")
        status_label.setStyleSheet(f"color: {status_color}; font-size: 11px;")
        info_layout.addWidget(status_label)

        layout.addLayout(info_layout, 1)

        return item

    def _create_reels_panel(self):
        """Create main reels management panel"""
        panel = QFrame()
        panel.setObjectName("reelsPanel")
        panel.setStyleSheet(f"""
            QFrame#reelsPanel {{
                background: {CYBER_COLORS['bg_card']};
                border: 1px solid {CYBER_COLORS['cyan']}40;
                border-radius: 10px;
            }}
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title = CyberTitle("REELS AUTOMATION", "cyan")
        layout.addWidget(title)

        # Stats row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(15)

        stats = [
            ("🎬", "Total Reels", "0", "cyan"),
            ("▶️", "Playing", "0", "green"),
            ("⏸️", "Paused", "0", "yellow"),
            ("❌", "Failed", "0", "magenta"),
        ]

        for icon, label, value, color in stats:
            card = CyberStatCard(icon, label, value, color)
            stats_row.addWidget(card)

        layout.addLayout(stats_row)

        # Configuration section
        config_frame = QFrame()
        config_frame.setStyleSheet(f"""
            QFrame {{
                background: {CYBER_COLORS['bg_lighter']};
                border: 1px solid {CYBER_COLORS['cyan']}30;
                border-radius: 8px;
                padding: 15px;
            }}
        """)

        config_layout = QVBoxLayout(config_frame)
        config_layout.setSpacing(15)

        # Config title
        config_title = QLabel("⚙️ CONFIGURATION")
        config_title.setStyleSheet(f"""
            color: {CYBER_COLORS['cyan']};
            font-weight: bold;
            font-size: 14px;
            letter-spacing: 1px;
        """)
        config_layout.addWidget(config_title)

        # Config options grid
        config_grid = QHBoxLayout()
        config_grid.setSpacing(20)

        # Left config column
        left_config = QVBoxLayout()
        left_config.setSpacing(10)

        # Watch time
        watch_time_layout = QHBoxLayout()
        watch_time_label = QLabel("Watch Time (sec):")
        watch_time_label.setStyleSheet(f"color: {CYBER_COLORS['text']};")
        watch_time_layout.addWidget(watch_time_label)

        watch_time_spin = QSpinBox()
        watch_time_spin.setRange(5, 60)
        watch_time_spin.setValue(15)
        watch_time_spin.setStyleSheet(f"""
            QSpinBox {{
                background: {CYBER_COLORS['bg_dark']};
                border: 1px solid {CYBER_COLORS['cyan']}40;
                border-radius: 4px;
                padding: 5px;
                color: {CYBER_COLORS['text']};
                min-width: 80px;
            }}
        """)
        watch_time_layout.addWidget(watch_time_spin)
        watch_time_layout.addStretch()
        left_config.addLayout(watch_time_layout)

        # Number of reels
        num_reels_layout = QHBoxLayout()
        num_reels_label = QLabel("Number of Reels:")
        num_reels_label.setStyleSheet(f"color: {CYBER_COLORS['text']};")
        num_reels_layout.addWidget(num_reels_label)

        num_reels_spin = QSpinBox()
        num_reels_spin.setRange(1, 100)
        num_reels_spin.setValue(10)
        num_reels_spin.setStyleSheet(f"""
            QSpinBox {{
                background: {CYBER_COLORS['bg_dark']};
                border: 1px solid {CYBER_COLORS['cyan']}40;
                border-radius: 4px;
                padding: 5px;
                color: {CYBER_COLORS['text']};
                min-width: 80px;
            }}
        """)
        num_reels_layout.addWidget(num_reels_spin)
        num_reels_layout.addStretch()
        left_config.addLayout(num_reels_layout)

        config_grid.addLayout(left_config)

        # Right config column
        right_config = QVBoxLayout()
        right_config.setSpacing(10)

        # Action after watch
        action_layout = QHBoxLayout()
        action_label = QLabel("Action After Watch:")
        action_label.setStyleSheet(f"color: {CYBER_COLORS['text']};")
        action_layout.addWidget(action_label)

        action_combo = QComboBox()
        action_combo.addItems(["Like", "Like + Comment", "Like + Share", "Random"])
        action_combo.setStyleSheet(f"""
            QComboBox {{
                background: {CYBER_COLORS['bg_dark']};
                border: 1px solid {CYBER_COLORS['cyan']}40;
                border-radius: 4px;
                padding: 5px 10px;
                color: {CYBER_COLORS['text']};
                min-width: 150px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background: {CYBER_COLORS['bg_dark']};
                border: 1px solid {CYBER_COLORS['cyan']};
                color: {CYBER_COLORS['text']};
                selection-background-color: {CYBER_COLORS['cyan']}30;
            }}
        """)
        action_layout.addWidget(action_combo)
        action_layout.addStretch()
        right_config.addLayout(action_layout)

        # Delay between reels
        delay_layout = QHBoxLayout()
        delay_label = QLabel("Delay (sec):")
        delay_label.setStyleSheet(f"color: {CYBER_COLORS['text']};")
        delay_layout.addWidget(delay_label)

        delay_spin = QSpinBox()
        delay_spin.setRange(1, 30)
        delay_spin.setValue(3)
        delay_spin.setStyleSheet(f"""
            QSpinBox {{
                background: {CYBER_COLORS['bg_dark']};
                border: 1px solid {CYBER_COLORS['cyan']}40;
                border-radius: 4px;
                padding: 5px;
                color: {CYBER_COLORS['text']};
                min-width: 80px;
            }}
        """)
        delay_layout.addWidget(delay_spin)
        delay_layout.addStretch()
        right_config.addLayout(delay_layout)

        config_grid.addLayout(right_config)
        config_layout.addLayout(config_grid)

        # Checkboxes
        checkbox_layout = QHBoxLayout()

        auto_scroll = QCheckBox("Auto Scroll")
        auto_scroll.setChecked(True)
        auto_scroll.setStyleSheet(f"""
            QCheckBox {{
                color: {CYBER_COLORS['text']};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {CYBER_COLORS['cyan']};
                border-radius: 3px;
            }}
            QCheckBox::indicator:checked {{
                background: {CYBER_COLORS['cyan']};
            }}
        """)
        checkbox_layout.addWidget(auto_scroll)

        random_like = QCheckBox("Random Like (70%)")
        random_like.setStyleSheet(auto_scroll.styleSheet())
        checkbox_layout.addWidget(random_like)

        save_videos = QCheckBox("Save Videos")
        save_videos.setStyleSheet(auto_scroll.styleSheet())
        checkbox_layout.addWidget(save_videos)

        checkbox_layout.addStretch()
        config_layout.addLayout(checkbox_layout)

        layout.addWidget(config_frame)

        # Progress section
        progress_frame = QFrame()
        progress_frame.setStyleSheet(f"""
            QFrame {{
                background: {CYBER_COLORS['bg_lighter']};
                border: 1px solid {CYBER_COLORS['green']}30;
                border-radius: 8px;
                padding: 15px;
            }}
        """)

        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setSpacing(10)

        progress_title = QLabel("📊 PROGRESS")
        progress_title.setStyleSheet(f"""
            color: {CYBER_COLORS['green']};
            font-weight: bold;
            font-size: 14px;
            letter-spacing: 1px;
        """)
        progress_layout.addWidget(progress_title)

        # Progress bar
        progress_bar = QProgressBar()
        progress_bar.setValue(0)
        progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background: {CYBER_COLORS['bg_dark']};
                border: 1px solid {CYBER_COLORS['green']}40;
                border-radius: 5px;
                height: 25px;
                text-align: center;
                color: {CYBER_COLORS['text']};
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, x2:1,
                    stop:0 {CYBER_COLORS['green']},
                    stop:1 {CYBER_COLORS['cyan']});
                border-radius: 4px;
            }}
        """)
        progress_layout.addWidget(progress_bar)

        # Status text
        status_text = QLabel("Ready to start...")
        status_text.setStyleSheet(f"color: {CYBER_COLORS['text_dim']}; font-size: 12px;")
        progress_layout.addWidget(status_text)

        layout.addWidget(progress_frame)

        # Action buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)

        start_btn = CyberButton("▶ START", "green", parent=self)
        start_btn.setFixedHeight(45)
        buttons_layout.addWidget(start_btn)

        pause_btn = CyberButton("⏸ PAUSE", "yellow", parent=self)
        pause_btn.setFixedHeight(45)
        buttons_layout.addWidget(pause_btn)

        stop_btn = CyberButton("⏹ STOP", "magenta", parent=self)
        stop_btn.setFixedHeight(45)
        buttons_layout.addWidget(stop_btn)

        layout.addLayout(buttons_layout)

        # Log area
        log_frame = QFrame()
        log_frame.setStyleSheet(f"""
            QFrame {{
                background: {CYBER_COLORS['bg_dark']};
                border: 1px solid {CYBER_COLORS['cyan']}30;
                border-radius: 8px;
            }}
        """)

        log_layout = QVBoxLayout(log_frame)
        log_layout.setContentsMargins(10, 10, 10, 10)

        log_title = QLabel("📋 Activity Log")
        log_title.setStyleSheet(f"""
            color: {CYBER_COLORS['cyan']};
            font-weight: bold;
            font-size: 12px;
        """)
        log_layout.addWidget(log_title)

        log_text = QTextEdit()
        log_text.setReadOnly(True)
        log_text.setStyleSheet(f"""
            QTextEdit {{
                background: transparent;
                border: none;
                color: {CYBER_COLORS['text']};
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
            }}
        """)
        log_text.setPlainText("[SYSTEM] Reels automation ready\n[INFO] Select profiles and configure settings\n[INFO] Click START to begin automation")
        log_layout.addWidget(log_text)

        layout.addWidget(log_frame, 1)

        return panel
