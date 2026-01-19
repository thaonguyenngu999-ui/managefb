"""
FB Manager Pro - Scripts Tab (PyQt6)
Cyberpunk 2077 Theme
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QLineEdit, QComboBox, QCheckBox, QTextEdit, QSpinBox,
    QScrollArea, QSplitter, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QSyntaxHighlighter, QTextCharFormat

# Import shared Cyberpunk widgets
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cyber_widgets_qt import CyberTitle, CyberButton, CYBER_COLORS


class ScriptItem(QFrame):
    """Script list item"""

    def __init__(self, name: str, script_type: str, last_run: str, status: str, parent=None):
        super().__init__(parent)
        self.setObjectName("scriptItem")
        self._setup_ui(name, script_type, last_run, status)

    def _setup_ui(self, name: str, script_type: str, last_run: str, status: str):
        status_colors = {
            "Ready": CYBER_COLORS["green"],
            "Running": CYBER_COLORS["cyan"],
            "Error": CYBER_COLORS["red"],
            "Stopped": CYBER_COLORS["yellow"]
        }
        status_color = status_colors.get(status, CYBER_COLORS["text_dim"])

        self.setStyleSheet(f"""
            QFrame#scriptItem {{
                background: {CYBER_COLORS['bg_lighter']};
                border: 1px solid {status_color}40;
                border-radius: 6px;
                padding: 10px;
            }}
            QFrame#scriptItem:hover {{
                border: 1px solid {status_color};
                background: {status_color}10;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # Icon based on type
        type_icons = {
            "Auto Post": "📝",
            "Auto Like": "❤️",
            "Auto Comment": "💬",
            "Auto Share": "🔄",
            "Auto Follow": "👤",
            "Scraper": "🔍",
            "Custom": "⚙️"
        }
        icon = type_icons.get(script_type, "📜")

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px;")
        layout.addWidget(icon_label)

        # Info section
        info = QVBoxLayout()
        info.setSpacing(4)

        name_label = QLabel(name)
        name_label.setStyleSheet(f"""
            color: {CYBER_COLORS['text']};
            font-weight: bold;
            font-size: 14px;
        """)
        info.addWidget(name_label)

        meta = QHBoxLayout()
        meta.setSpacing(15)

        type_label = QLabel(script_type)
        type_label.setStyleSheet(f"""
            background: {CYBER_COLORS['cyan']}30;
            color: {CYBER_COLORS['cyan']};
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 10px;
        """)
        meta.addWidget(type_label)

        last_run_label = QLabel(f"Last: {last_run}")
        last_run_label.setStyleSheet(f"color: {CYBER_COLORS['text_dim']}; font-size: 11px;")
        meta.addWidget(last_run_label)

        meta.addStretch()
        info.addLayout(meta)

        layout.addLayout(info, 1)

        # Status
        status_label = QLabel(f"● {status}")
        status_label.setStyleSheet(f"color: {status_color}; font-size: 12px; font-weight: bold;")
        layout.addWidget(status_label)

        # Actions
        run_btn = QPushButton("▶")
        run_btn.setFixedSize(32, 32)
        run_btn.setToolTip("Run Script")
        run_btn.setStyleSheet(f"""
            QPushButton {{
                background: {CYBER_COLORS['green']}20;
                border: 1px solid {CYBER_COLORS['green']}40;
                border-radius: 4px;
                color: {CYBER_COLORS['green']};
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: {CYBER_COLORS['green']}40;
            }}
        """)
        layout.addWidget(run_btn)

        edit_btn = QPushButton("✏️")
        edit_btn.setFixedSize(32, 32)
        edit_btn.setToolTip("Edit Script")
        edit_btn.setStyleSheet(f"""
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
        layout.addWidget(edit_btn)

        delete_btn = QPushButton("🗑️")
        delete_btn.setFixedSize(32, 32)
        delete_btn.setToolTip("Delete Script")
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background: {CYBER_COLORS['red']}20;
                border: 1px solid {CYBER_COLORS['red']}40;
                border-radius: 4px;
                color: {CYBER_COLORS['red']};
            }}
            QPushButton:hover {{
                background: {CYBER_COLORS['red']}40;
            }}
        """)
        layout.addWidget(delete_btn)


class ScriptsTabQt(QWidget):
    """Scripts management tab with Cyberpunk styling"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("scriptsTab")
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Title
        title = CyberTitle("SCRIPT MANAGER", "yellow")
        main_layout.addWidget(title)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background: #1a1a2e;
                width: 2px;
            }
        """)

        # Left panel - Script list
        left_panel = self._create_script_list_panel()
        splitter.addWidget(left_panel)

        # Right panel - Script editor
        right_panel = self._create_editor_panel()
        splitter.addWidget(right_panel)

        splitter.setSizes([400, 600])
        main_layout.addWidget(splitter, 1)

    def _create_script_list_panel(self):
        """Create script list panel"""
        panel = QFrame()
        panel.setObjectName("scriptListPanel")
        panel.setStyleSheet(f"""
            QFrame#scriptListPanel {{
                background: {CYBER_COLORS['bg_card']};
                border: 1px solid {CYBER_COLORS['yellow']}40;
                border-radius: 10px;
            }}
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Header
        header = QHBoxLayout()

        list_title = QLabel("📜 SCRIPTS")
        list_title.setStyleSheet(f"""
            color: {CYBER_COLORS['yellow']};
            font-weight: bold;
            font-size: 16px;
            letter-spacing: 1px;
        """)
        header.addWidget(list_title)

        header.addStretch()

        new_btn = CyberButton("+ New", "green")
        header.addWidget(new_btn)

        layout.addLayout(header)

        # Search and filter
        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)

        search = QLineEdit()
        search.setPlaceholderText("🔍 Search scripts...")
        search.setStyleSheet(f"""
            QLineEdit {{
                background: {CYBER_COLORS['bg_dark']};
                border: 1px solid {CYBER_COLORS['yellow']}40;
                border-radius: 5px;
                padding: 8px;
                color: {CYBER_COLORS['text']};
            }}
            QLineEdit:focus {{
                border: 1px solid {CYBER_COLORS['yellow']};
            }}
        """)
        filter_row.addWidget(search, 1)

        type_filter = QComboBox()
        type_filter.addItems(["All Types", "Auto Post", "Auto Like", "Auto Comment", "Scraper", "Custom"])
        type_filter.setStyleSheet(f"""
            QComboBox {{
                background: {CYBER_COLORS['bg_dark']};
                border: 1px solid {CYBER_COLORS['yellow']}40;
                border-radius: 4px;
                padding: 6px 10px;
                color: {CYBER_COLORS['text']};
            }}
        """)
        filter_row.addWidget(type_filter)

        layout.addLayout(filter_row)

        # Script list
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
                background: #f0ff0040;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #f0ff00;
            }
        """)

        list_container = QWidget()
        list_layout = QVBoxLayout(list_container)
        list_layout.setSpacing(10)

        # Sample scripts
        scripts = [
            ("Auto Post Campaign", "Auto Post", "2 hours ago", "Ready"),
            ("Engagement Booster", "Auto Like", "Running...", "Running"),
            ("Comment Generator", "Auto Comment", "Yesterday", "Ready"),
            ("Profile Scraper", "Scraper", "3 days ago", "Error"),
            ("Share Automation", "Auto Share", "1 hour ago", "Stopped"),
            ("Custom Workflow", "Custom", "Never", "Ready"),
        ]

        for name, script_type, last_run, status in scripts:
            item = ScriptItem(name, script_type, last_run, status)
            list_layout.addWidget(item)

        list_layout.addStretch()
        scroll.setWidget(list_container)
        layout.addWidget(scroll, 1)

        return panel

    def _create_editor_panel(self):
        """Create script editor panel"""
        panel = QFrame()
        panel.setObjectName("editorPanel")
        panel.setStyleSheet(f"""
            QFrame#editorPanel {{
                background: {CYBER_COLORS['bg_card']};
                border: 1px solid {CYBER_COLORS['cyan']}40;
                border-radius: 10px;
            }}
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Editor header
        header = QHBoxLayout()

        editor_title = QLabel("✏️ SCRIPT EDITOR")
        editor_title.setStyleSheet(f"""
            color: {CYBER_COLORS['cyan']};
            font-weight: bold;
            font-size: 16px;
            letter-spacing: 1px;
        """)
        header.addWidget(editor_title)

        header.addStretch()

        # Script name input
        name_input = QLineEdit()
        name_input.setPlaceholderText("Script name...")
        name_input.setStyleSheet(f"""
            QLineEdit {{
                background: {CYBER_COLORS['bg_dark']};
                border: 1px solid {CYBER_COLORS['cyan']}40;
                border-radius: 4px;
                padding: 8px 12px;
                color: {CYBER_COLORS['text']};
                min-width: 200px;
            }}
        """)
        header.addWidget(name_input)

        layout.addLayout(header)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        # Script type
        type_label = QLabel("Type:")
        type_label.setStyleSheet(f"color: {CYBER_COLORS['text']};")
        toolbar.addWidget(type_label)

        type_combo = QComboBox()
        type_combo.addItems(["Auto Post", "Auto Like", "Auto Comment", "Auto Share", "Auto Follow", "Scraper", "Custom"])
        type_combo.setStyleSheet(f"""
            QComboBox {{
                background: {CYBER_COLORS['bg_dark']};
                border: 1px solid {CYBER_COLORS['cyan']}40;
                border-radius: 4px;
                padding: 6px 12px;
                color: {CYBER_COLORS['text']};
            }}
        """)
        toolbar.addWidget(type_combo)

        # Target profiles
        target_label = QLabel("Target:")
        target_label.setStyleSheet(f"color: {CYBER_COLORS['text']};")
        toolbar.addWidget(target_label)

        target_combo = QComboBox()
        target_combo.addItems(["All Profiles", "Selected Profiles", "Active Only"])
        target_combo.setStyleSheet(type_combo.styleSheet())
        toolbar.addWidget(target_combo)

        toolbar.addStretch()

        # Validate button
        validate_btn = CyberButton("✓ Validate", "cyan")
        toolbar.addWidget(validate_btn)

        layout.addLayout(toolbar)

        # Code editor
        code_frame = QFrame()
        code_frame.setStyleSheet(f"""
            QFrame {{
                background: {CYBER_COLORS['bg_dark']};
                border: 1px solid {CYBER_COLORS['cyan']}30;
                border-radius: 8px;
            }}
        """)

        code_layout = QVBoxLayout(code_frame)
        code_layout.setContentsMargins(0, 0, 0, 0)

        # Line numbers + editor would go here
        code_editor = QTextEdit()
        code_editor.setStyleSheet(f"""
            QTextEdit {{
                background: transparent;
                border: none;
                color: {CYBER_COLORS['text']};
                font-family: 'Fira Code', 'Consolas', 'Monaco', monospace;
                font-size: 13px;
                padding: 15px;
            }}
        """)
        code_editor.setPlainText("""# FB Manager Pro - Script Template
# Type: Auto Post
# Target: All Profiles

async def run(profiles, config):
    \"\"\"
    Main script entry point

    Args:
        profiles: List of active profiles
        config: Script configuration
    \"\"\"
    for profile in profiles:
        # Post content
        content = config.get('content', 'Hello World!')

        # Execute post
        result = await profile.post(content)

        # Log result
        log(f"Posted to {profile.name}: {result}")

        # Delay between posts
        await sleep(config.get('delay', 5))

    return {'status': 'completed', 'count': len(profiles)}
""")
        code_layout.addWidget(code_editor)

        layout.addWidget(code_frame, 1)

        # Configuration section
        config_frame = QFrame()
        config_frame.setStyleSheet(f"""
            QFrame {{
                background: {CYBER_COLORS['bg_lighter']};
                border: 1px solid {CYBER_COLORS['yellow']}30;
                border-radius: 8px;
                padding: 15px;
            }}
        """)

        config_layout = QVBoxLayout(config_frame)
        config_layout.setSpacing(10)

        config_title = QLabel("⚙️ CONFIGURATION")
        config_title.setStyleSheet(f"""
            color: {CYBER_COLORS['yellow']};
            font-weight: bold;
            font-size: 14px;
        """)
        config_layout.addWidget(config_title)

        config_grid = QHBoxLayout()
        config_grid.setSpacing(20)

        # Delay setting
        delay_layout = QHBoxLayout()
        delay_label = QLabel("Delay (sec):")
        delay_label.setStyleSheet(f"color: {CYBER_COLORS['text']};")
        delay_layout.addWidget(delay_label)

        delay_spin = QSpinBox()
        delay_spin.setRange(1, 300)
        delay_spin.setValue(5)
        delay_spin.setStyleSheet(f"""
            QSpinBox {{
                background: {CYBER_COLORS['bg_dark']};
                border: 1px solid {CYBER_COLORS['yellow']}40;
                border-radius: 4px;
                padding: 5px;
                color: {CYBER_COLORS['text']};
                min-width: 80px;
            }}
        """)
        delay_layout.addWidget(delay_spin)
        config_grid.addLayout(delay_layout)

        # Retry setting
        retry_layout = QHBoxLayout()
        retry_label = QLabel("Retries:")
        retry_label.setStyleSheet(f"color: {CYBER_COLORS['text']};")
        retry_layout.addWidget(retry_label)

        retry_spin = QSpinBox()
        retry_spin.setRange(0, 10)
        retry_spin.setValue(3)
        retry_spin.setStyleSheet(delay_spin.styleSheet())
        retry_layout.addWidget(retry_spin)
        config_grid.addLayout(retry_layout)

        # Checkboxes
        log_check = QCheckBox("Enable Logging")
        log_check.setChecked(True)
        log_check.setStyleSheet(f"""
            QCheckBox {{
                color: {CYBER_COLORS['text']};
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid {CYBER_COLORS['yellow']};
                border-radius: 3px;
            }}
            QCheckBox::indicator:checked {{
                background: {CYBER_COLORS['yellow']};
            }}
        """)
        config_grid.addWidget(log_check)

        notify_check = QCheckBox("Notify on Complete")
        notify_check.setStyleSheet(log_check.styleSheet())
        config_grid.addWidget(notify_check)

        config_grid.addStretch()
        config_layout.addLayout(config_grid)

        layout.addWidget(config_frame)

        # Action buttons
        actions = QHBoxLayout()
        actions.setSpacing(15)

        save_btn = CyberButton("💾 Save", "cyan")
        save_btn.setFixedHeight(45)
        actions.addWidget(save_btn)

        test_btn = CyberButton("🧪 Test Run", "yellow")
        test_btn.setFixedHeight(45)
        actions.addWidget(test_btn)

        run_btn = CyberButton("▶ Run Script", "green")
        run_btn.setFixedHeight(45)
        actions.addWidget(run_btn)

        stop_btn = CyberButton("⏹ Stop", "red")
        stop_btn.setFixedHeight(45)
        actions.addWidget(stop_btn)

        layout.addLayout(actions)

        return panel
