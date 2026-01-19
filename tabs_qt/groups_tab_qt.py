"""
FB Manager Pro - Groups Tab (PyQt6)
Cyberpunk 2077 Theme
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QLineEdit, QComboBox, QCheckBox, QTextEdit, QSpinBox,
    QScrollArea, QGridLayout, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor

# Cyberpunk colors
CYBER_COLORS = {
    "cyan": "#00f0ff",
    "magenta": "#ff00a8",
    "green": "#00ff66",
    "yellow": "#f0ff00",
    "orange": "#ff6600",
    "purple": "#9d4edd",
    "bg_dark": "#0a0a12",
    "bg_card": "#12121f",
    "bg_lighter": "#1a1a2e",
    "text": "#e0e0e0",
    "text_dim": "#808080"
}


class CyberTitle(QFrame):
    """Cyberpunk styled title"""

    def __init__(self, text: str, color: str = "cyan", parent=None):
        super().__init__(parent)
        self.text = text
        self.color = CYBER_COLORS.get(color, color)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 10)

        triangle = QLabel("▶")
        triangle.setStyleSheet(f"color: {self.color}; font-size: 16px;")
        layout.addWidget(triangle)

        title = QLabel(self.text)
        title.setStyleSheet(f"""
            color: {self.color};
            font-size: 24px;
            font-weight: bold;
            font-family: 'Orbitron', 'Rajdhani', 'Consolas', monospace;
            letter-spacing: 2px;
        """)
        layout.addWidget(title)

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
    """Cyberpunk stat card"""

    def __init__(self, icon: str, label: str, value: str, color: str = "cyan", parent=None):
        super().__init__(parent)
        self.color = CYBER_COLORS.get(color, color)
        self.setObjectName("statCard")
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
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        top_row = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"font-size: 28px; color: {self.color};")
        top_row.addWidget(icon_label)
        top_row.addStretch()

        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: bold;
            color: {self.color};
            font-family: 'Orbitron', monospace;
        """)
        top_row.addWidget(value_label)
        self.value_label = value_label

        layout.addLayout(top_row)

        text_label = QLabel(label)
        text_label.setStyleSheet(f"""
            color: {CYBER_COLORS['text_dim']};
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
        """)
        layout.addWidget(text_label)


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


class GroupCard(QFrame):
    """Group preview card"""

    def __init__(self, name: str, members: str, role: str, posts: str, parent=None):
        super().__init__(parent)
        self.setObjectName("groupCard")
        self._setup_ui(name, members, role, posts)

    def _setup_ui(self, name: str, members: str, role: str, posts: str):
        role_colors = {
            "Admin": CYBER_COLORS["magenta"],
            "Moderator": CYBER_COLORS["cyan"],
            "Member": CYBER_COLORS["green"]
        }
        role_color = role_colors.get(role, CYBER_COLORS["text_dim"])

        self.setStyleSheet(f"""
            QFrame#groupCard {{
                background: {CYBER_COLORS['bg_lighter']};
                border: 1px solid {role_color}40;
                border-radius: 8px;
                padding: 15px;
            }}
            QFrame#groupCard:hover {{
                border: 1px solid {role_color};
                background: {role_color}10;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Header with role badge
        header = QHBoxLayout()

        checkbox = QCheckBox()
        checkbox.setStyleSheet(f"""
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {CYBER_COLORS['purple']};
                border-radius: 3px;
            }}
            QCheckBox::indicator:checked {{
                background: {CYBER_COLORS['purple']};
            }}
        """)
        header.addWidget(checkbox)

        header.addStretch()

        role_badge = QLabel(role)
        role_badge.setStyleSheet(f"""
            background: {role_color}30;
            color: {role_color};
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 10px;
            font-weight: bold;
        """)
        header.addWidget(role_badge)

        layout.addLayout(header)

        # Group name
        name_label = QLabel(name)
        name_label.setStyleSheet(f"""
            color: {CYBER_COLORS['text']};
            font-size: 14px;
            font-weight: bold;
        """)
        name_label.setWordWrap(True)
        layout.addWidget(name_label)

        # Stats
        stats_layout = QHBoxLayout()

        members_label = QLabel(f"👥 {members}")
        members_label.setStyleSheet(f"color: {CYBER_COLORS['cyan']}; font-size: 11px;")
        stats_layout.addWidget(members_label)

        posts_label = QLabel(f"📝 {posts} posts")
        posts_label.setStyleSheet(f"color: {CYBER_COLORS['green']}; font-size: 11px;")
        stats_layout.addWidget(posts_label)

        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Actions
        actions = QHBoxLayout()
        actions.setSpacing(5)

        post_btn = QPushButton("📝")
        post_btn.setFixedSize(30, 30)
        post_btn.setToolTip("Create Post")
        post_btn.setStyleSheet(f"""
            QPushButton {{
                background: {CYBER_COLORS['green']}20;
                border: 1px solid {CYBER_COLORS['green']}40;
                border-radius: 4px;
                color: {CYBER_COLORS['green']};
            }}
            QPushButton:hover {{
                background: {CYBER_COLORS['green']}40;
            }}
        """)
        actions.addWidget(post_btn)

        view_btn = QPushButton("👁️")
        view_btn.setFixedSize(30, 30)
        view_btn.setToolTip("View Group")
        view_btn.setStyleSheet(f"""
            QPushButton {{
                background: {CYBER_COLORS['cyan']}20;
                border: 1px solid {CYBER_COLORS['cyan']}40;
                border-radius: 4px;
                color: {CYBER_COLORS['cyan']};
            }}
            QPushButton:hover {{
                background: {CYBER_COLORS['cyan']}40;
            }}
        """)
        actions.addWidget(view_btn)

        leave_btn = QPushButton("🚪")
        leave_btn.setFixedSize(30, 30)
        leave_btn.setToolTip("Leave Group")
        leave_btn.setStyleSheet(f"""
            QPushButton {{
                background: {CYBER_COLORS['magenta']}20;
                border: 1px solid {CYBER_COLORS['magenta']}40;
                border-radius: 4px;
                color: {CYBER_COLORS['magenta']};
            }}
            QPushButton:hover {{
                background: {CYBER_COLORS['magenta']}40;
            }}
        """)
        actions.addWidget(leave_btn)

        actions.addStretch()
        layout.addLayout(actions)


class GroupsTabQt(QWidget):
    """Groups management tab with Cyberpunk styling"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("groupsTab")
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Left panel - Profile selection
        left_panel = self._create_profile_panel()
        main_layout.addWidget(left_panel)

        # Right panel - Groups management
        right_panel = self._create_groups_panel()
        main_layout.addWidget(right_panel, 1)

    def _create_profile_panel(self):
        """Create profile selection panel"""
        panel = QFrame()
        panel.setObjectName("profilePanel")
        panel.setFixedWidth(280)
        panel.setStyleSheet(f"""
            QFrame#profilePanel {{
                background: {CYBER_COLORS['bg_card']};
                border: 1px solid {CYBER_COLORS['purple']}40;
                border-radius: 10px;
            }}
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Title
        title = CyberTitle("PROFILES", "purple")
        layout.addWidget(title)

        # Search
        search = QLineEdit()
        search.setPlaceholderText("🔍 Search profiles...")
        search.setStyleSheet(f"""
            QLineEdit {{
                background: {CYBER_COLORS['bg_dark']};
                border: 1px solid {CYBER_COLORS['purple']}40;
                border-radius: 5px;
                padding: 10px;
                color: {CYBER_COLORS['text']};
            }}
            QLineEdit:focus {{
                border: 1px solid {CYBER_COLORS['purple']};
            }}
        """)
        layout.addWidget(search)

        # Profile list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        profile_container = QWidget()
        profile_layout = QVBoxLayout(profile_container)
        profile_layout.setSpacing(8)

        profiles = [
            ("John Doe", "5 groups", True),
            ("Jane Smith", "12 groups", False),
            ("Mike Johnson", "8 groups", True),
            ("Sarah Wilson", "3 groups", False),
        ]

        for name, groups, checked in profiles:
            item = self._create_profile_item(name, groups, checked)
            profile_layout.addWidget(item)

        profile_layout.addStretch()
        scroll.setWidget(profile_container)
        layout.addWidget(scroll, 1)

        # Select all
        select_all = QCheckBox("Select All")
        select_all.setStyleSheet(f"""
            QCheckBox {{
                color: {CYBER_COLORS['text']};
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {CYBER_COLORS['purple']};
                border-radius: 3px;
            }}
            QCheckBox::indicator:checked {{
                background: {CYBER_COLORS['purple']};
            }}
        """)
        layout.addWidget(select_all)

        return panel

    def _create_profile_item(self, name: str, groups: str, checked: bool):
        """Create profile item widget"""
        item = QFrame()
        item.setStyleSheet(f"""
            QFrame {{
                background: {CYBER_COLORS['bg_lighter']};
                border: 1px solid {CYBER_COLORS['purple']}30;
                border-radius: 5px;
                padding: 8px;
            }}
            QFrame:hover {{
                border: 1px solid {CYBER_COLORS['purple']};
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
                border: 2px solid {CYBER_COLORS['purple']};
                border-radius: 3px;
            }}
            QCheckBox::indicator:checked {{
                background: {CYBER_COLORS['purple']};
            }}
        """)
        layout.addWidget(checkbox)

        info = QVBoxLayout()
        info.setSpacing(2)

        name_label = QLabel(name)
        name_label.setStyleSheet(f"color: {CYBER_COLORS['text']}; font-weight: bold;")
        info.addWidget(name_label)

        groups_label = QLabel(groups)
        groups_label.setStyleSheet(f"color: {CYBER_COLORS['text_dim']}; font-size: 11px;")
        info.addWidget(groups_label)

        layout.addLayout(info, 1)

        return item

    def _create_groups_panel(self):
        """Create main groups panel"""
        panel = QFrame()
        panel.setObjectName("groupsPanel")
        panel.setStyleSheet(f"""
            QFrame#groupsPanel {{
                background: {CYBER_COLORS['bg_card']};
                border: 1px solid {CYBER_COLORS['purple']}40;
                border-radius: 10px;
            }}
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title = CyberTitle("GROUPS MANAGER", "purple")
        layout.addWidget(title)

        # Stats row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(15)

        stats = [
            ("👥", "Total Groups", "28", "purple"),
            ("👑", "Admin", "5", "magenta"),
            ("🛡️", "Moderator", "8", "cyan"),
            ("👤", "Member", "15", "green"),
        ]

        for icon, label, value, color in stats:
            card = CyberStatCard(icon, label, value, color)
            stats_row.addWidget(card)

        layout.addLayout(stats_row)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        # Search
        search = QLineEdit()
        search.setPlaceholderText("🔍 Search groups...")
        search.setStyleSheet(f"""
            QLineEdit {{
                background: {CYBER_COLORS['bg_dark']};
                border: 1px solid {CYBER_COLORS['purple']}40;
                border-radius: 5px;
                padding: 10px;
                color: {CYBER_COLORS['text']};
                min-width: 200px;
            }}
            QLineEdit:focus {{
                border: 1px solid {CYBER_COLORS['purple']};
            }}
        """)
        toolbar.addWidget(search)

        # Filter
        filter_combo = QComboBox()
        filter_combo.addItems(["All Groups", "Admin", "Moderator", "Member"])
        filter_combo.setStyleSheet(f"""
            QComboBox {{
                background: {CYBER_COLORS['bg_dark']};
                border: 1px solid {CYBER_COLORS['purple']}40;
                border-radius: 4px;
                padding: 8px 15px;
                color: {CYBER_COLORS['text']};
            }}
        """)
        toolbar.addWidget(filter_combo)

        toolbar.addStretch()

        # Action buttons
        scan_btn = CyberButton("🔄 Scan Groups", "cyan")
        toolbar.addWidget(scan_btn)

        join_btn = CyberButton("➕ Join Group", "green")
        toolbar.addWidget(join_btn)

        post_btn = CyberButton("📝 Post to Selected", "purple")
        toolbar.addWidget(post_btn)

        layout.addLayout(toolbar)

        # Groups grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #1a1a2e;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #9d4edd40;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #9d4edd;
            }
        """)

        grid_container = QWidget()
        grid_layout = QGridLayout(grid_container)
        grid_layout.setSpacing(15)

        # Sample groups
        groups = [
            ("Python Developers Community", "125K", "Admin", "45"),
            ("Web Development Hub", "89K", "Moderator", "32"),
            ("AI & Machine Learning", "256K", "Member", "12"),
            ("Startup Founders Network", "45K", "Admin", "28"),
            ("Digital Marketing Pro", "78K", "Member", "8"),
            ("Tech News Daily", "312K", "Member", "5"),
            ("Freelancers United", "67K", "Moderator", "22"),
            ("UI/UX Design Masters", "98K", "Member", "15"),
        ]

        row, col = 0, 0
        for name, members, role, posts in groups:
            card = GroupCard(name, members, role, posts)
            grid_layout.addWidget(card, row, col)
            col += 1
            if col >= 3:
                col = 0
                row += 1

        scroll.setWidget(grid_container)
        layout.addWidget(scroll, 1)

        # Bottom action bar
        action_bar = QHBoxLayout()
        action_bar.setSpacing(15)

        select_all = QCheckBox("Select All Groups")
        select_all.setStyleSheet(f"""
            QCheckBox {{
                color: {CYBER_COLORS['text']};
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {CYBER_COLORS['purple']};
                border-radius: 3px;
            }}
            QCheckBox::indicator:checked {{
                background: {CYBER_COLORS['purple']};
            }}
        """)
        action_bar.addWidget(select_all)

        action_bar.addStretch()

        selected_label = QLabel("Selected: 0 groups")
        selected_label.setStyleSheet(f"color: {CYBER_COLORS['text_dim']};")
        action_bar.addWidget(selected_label)

        leave_btn = CyberButton("🚪 Leave Selected", "magenta")
        action_bar.addWidget(leave_btn)

        layout.addLayout(action_bar)

        return panel
