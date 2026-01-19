"""
FB Manager Pro - Content Tab (PyQt6)
Cyberpunk 2077 Theme
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QLineEdit, QComboBox, QCheckBox, QTextEdit, QSpinBox,
    QFileDialog, QScrollArea, QGridLayout, QSplitter
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor

# Import shared Cyberpunk widgets
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cyber_widgets_qt import CyberTitle, CyberStatCard, CyberButton, CYBER_COLORS


class ContentCard(QFrame):
    """Content preview card"""

    def __init__(self, title: str, content_type: str, status: str, date: str, parent=None):
        super().__init__(parent)
        self.setObjectName("contentCard")
        self._setup_ui(title, content_type, status, date)

    def _setup_ui(self, title: str, content_type: str, status: str, date: str):
        status_colors = {
            "Draft": CYBER_COLORS["yellow"],
            "Scheduled": CYBER_COLORS["cyan"],
            "Published": CYBER_COLORS["green"],
            "Failed": CYBER_COLORS["magenta"]
        }
        status_color = status_colors.get(status, CYBER_COLORS["text_dim"])

        self.setStyleSheet(f"""
            QFrame#contentCard {{
                background: {CYBER_COLORS['bg_lighter']};
                border: 1px solid {status_color}40;
                border-radius: 8px;
                padding: 15px;
            }}
            QFrame#contentCard:hover {{
                border: 1px solid {status_color};
                background: {status_color}10;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Header with type badge
        header = QHBoxLayout()

        type_badge = QLabel(content_type)
        type_badge.setStyleSheet(f"""
            background: {CYBER_COLORS['cyan']}30;
            color: {CYBER_COLORS['cyan']};
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 10px;
            font-weight: bold;
        """)
        header.addWidget(type_badge)

        header.addStretch()

        status_badge = QLabel(f"● {status}")
        status_badge.setStyleSheet(f"color: {status_color}; font-size: 11px;")
        header.addWidget(status_badge)

        layout.addLayout(header)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            color: {CYBER_COLORS['text']};
            font-size: 14px;
            font-weight: bold;
        """)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        # Date
        date_label = QLabel(f"📅 {date}")
        date_label.setStyleSheet(f"color: {CYBER_COLORS['text_dim']}; font-size: 11px;")
        layout.addWidget(date_label)

        # Actions
        actions = QHBoxLayout()
        actions.setSpacing(5)

        edit_btn = QPushButton("✏️")
        edit_btn.setFixedSize(30, 30)
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
        actions.addWidget(edit_btn)

        delete_btn = QPushButton("🗑️")
        delete_btn.setFixedSize(30, 30)
        delete_btn.setStyleSheet(f"""
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
        actions.addWidget(delete_btn)

        actions.addStretch()
        layout.addLayout(actions)


class ContentTabQt(QWidget):
    """Content management tab with Cyberpunk styling"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("contentTab")
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Title
        title = CyberTitle("CONTENT MANAGER", "orange")
        main_layout.addWidget(title)

        # Stats row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(15)

        stats = [
            ("📝", "Total Content", "24", "orange"),
            ("📋", "Drafts", "8", "yellow"),
            ("📆", "Scheduled", "12", "cyan"),
            ("✅", "Published", "4", "green"),
        ]

        for icon, label, value, color in stats:
            card = CyberStatCard(icon, label, value, color)
            stats_row.addWidget(card)

        main_layout.addLayout(stats_row)

        # Main content area - splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background: #1a1a2e;
                width: 2px;
            }
        """)

        # Left panel - Content editor
        editor_panel = self._create_editor_panel()
        splitter.addWidget(editor_panel)

        # Right panel - Content list
        list_panel = self._create_list_panel()
        splitter.addWidget(list_panel)

        splitter.setSizes([500, 400])
        main_layout.addWidget(splitter, 1)

    def _create_editor_panel(self):
        """Create content editor panel"""
        panel = QFrame()
        panel.setObjectName("editorPanel")
        panel.setStyleSheet(f"""
            QFrame#editorPanel {{
                background: {CYBER_COLORS['bg_card']};
                border: 1px solid {CYBER_COLORS['orange']}40;
                border-radius: 10px;
            }}
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Editor header
        header = QHBoxLayout()

        editor_title = QLabel("✏️ CREATE CONTENT")
        editor_title.setStyleSheet(f"""
            color: {CYBER_COLORS['orange']};
            font-weight: bold;
            font-size: 16px;
            letter-spacing: 1px;
        """)
        header.addWidget(editor_title)

        header.addStretch()

        # Content type selector
        type_combo = QComboBox()
        type_combo.addItems(["📝 Post", "🖼️ Photo", "🎬 Video", "📖 Story", "🎯 Reel"])
        type_combo.setStyleSheet(f"""
            QComboBox {{
                background: {CYBER_COLORS['bg_dark']};
                border: 1px solid {CYBER_COLORS['orange']}40;
                border-radius: 4px;
                padding: 8px 15px;
                color: {CYBER_COLORS['text']};
                min-width: 120px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background: {CYBER_COLORS['bg_dark']};
                border: 1px solid {CYBER_COLORS['orange']};
                color: {CYBER_COLORS['text']};
                selection-background-color: {CYBER_COLORS['orange']}30;
            }}
        """)
        header.addWidget(type_combo)

        layout.addLayout(header)

        # Title input
        title_input = QLineEdit()
        title_input.setPlaceholderText("Enter content title...")
        title_input.setStyleSheet(f"""
            QLineEdit {{
                background: {CYBER_COLORS['bg_dark']};
                border: 1px solid {CYBER_COLORS['orange']}40;
                border-radius: 5px;
                padding: 12px;
                color: {CYBER_COLORS['text']};
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 1px solid {CYBER_COLORS['orange']};
            }}
        """)
        layout.addWidget(title_input)

        # Content text area
        content_text = QTextEdit()
        content_text.setPlaceholderText("Write your content here...\n\nTip: Use hashtags and mentions for better reach!")
        content_text.setStyleSheet(f"""
            QTextEdit {{
                background: {CYBER_COLORS['bg_dark']};
                border: 1px solid {CYBER_COLORS['orange']}40;
                border-radius: 5px;
                padding: 12px;
                color: {CYBER_COLORS['text']};
                font-size: 13px;
            }}
            QTextEdit:focus {{
                border: 1px solid {CYBER_COLORS['orange']};
            }}
        """)
        layout.addWidget(content_text, 1)

        # Media upload section
        media_frame = QFrame()
        media_frame.setStyleSheet(f"""
            QFrame {{
                background: {CYBER_COLORS['bg_lighter']};
                border: 2px dashed {CYBER_COLORS['orange']}40;
                border-radius: 8px;
                padding: 20px;
            }}
        """)

        media_layout = QVBoxLayout(media_frame)
        media_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        upload_icon = QLabel("📁")
        upload_icon.setStyleSheet("font-size: 32px;")
        upload_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        media_layout.addWidget(upload_icon)

        upload_text = QLabel("Drop media files here or click to upload")
        upload_text.setStyleSheet(f"color: {CYBER_COLORS['text_dim']}; font-size: 12px;")
        upload_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        media_layout.addWidget(upload_text)

        upload_btn = CyberButton("📤 Upload Media", "orange")
        media_layout.addWidget(upload_btn)

        layout.addWidget(media_frame)

        # Schedule options
        schedule_frame = QFrame()
        schedule_frame.setStyleSheet(f"""
            QFrame {{
                background: {CYBER_COLORS['bg_lighter']};
                border: 1px solid {CYBER_COLORS['cyan']}30;
                border-radius: 8px;
                padding: 15px;
            }}
        """)

        schedule_layout = QHBoxLayout(schedule_frame)

        schedule_label = QLabel("📆 Schedule:")
        schedule_label.setStyleSheet(f"color: {CYBER_COLORS['text']};")
        schedule_layout.addWidget(schedule_label)

        schedule_combo = QComboBox()
        schedule_combo.addItems(["Post Now", "Schedule for Later", "Save as Draft"])
        schedule_combo.setStyleSheet(f"""
            QComboBox {{
                background: {CYBER_COLORS['bg_dark']};
                border: 1px solid {CYBER_COLORS['cyan']}40;
                border-radius: 4px;
                padding: 8px 15px;
                color: {CYBER_COLORS['text']};
                min-width: 150px;
            }}
        """)
        schedule_layout.addWidget(schedule_combo)

        schedule_layout.addStretch()

        # Target profiles
        target_label = QLabel("👥 Target:")
        target_label.setStyleSheet(f"color: {CYBER_COLORS['text']};")
        schedule_layout.addWidget(target_label)

        target_combo = QComboBox()
        target_combo.addItems(["All Profiles", "Selected Profiles", "Custom Group"])
        target_combo.setStyleSheet(schedule_combo.styleSheet())
        schedule_layout.addWidget(target_combo)

        layout.addWidget(schedule_frame)

        # Action buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)

        save_draft_btn = CyberButton("💾 Save Draft", "yellow")
        save_draft_btn.setFixedHeight(45)
        buttons_layout.addWidget(save_draft_btn)

        schedule_btn = CyberButton("📆 Schedule", "cyan")
        schedule_btn.setFixedHeight(45)
        buttons_layout.addWidget(schedule_btn)

        publish_btn = CyberButton("🚀 Publish Now", "green")
        publish_btn.setFixedHeight(45)
        buttons_layout.addWidget(publish_btn)

        layout.addLayout(buttons_layout)

        return panel

    def _create_list_panel(self):
        """Create content list panel"""
        panel = QFrame()
        panel.setObjectName("listPanel")
        panel.setStyleSheet(f"""
            QFrame#listPanel {{
                background: {CYBER_COLORS['bg_card']};
                border: 1px solid {CYBER_COLORS['cyan']}40;
                border-radius: 10px;
            }}
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header = QHBoxLayout()

        list_title = QLabel("📋 CONTENT LIBRARY")
        list_title.setStyleSheet(f"""
            color: {CYBER_COLORS['cyan']};
            font-weight: bold;
            font-size: 16px;
            letter-spacing: 1px;
        """)
        header.addWidget(list_title)

        header.addStretch()

        # Filter
        filter_combo = QComboBox()
        filter_combo.addItems(["All", "Drafts", "Scheduled", "Published"])
        filter_combo.setStyleSheet(f"""
            QComboBox {{
                background: {CYBER_COLORS['bg_dark']};
                border: 1px solid {CYBER_COLORS['cyan']}40;
                border-radius: 4px;
                padding: 5px 10px;
                color: {CYBER_COLORS['text']};
            }}
        """)
        header.addWidget(filter_combo)

        layout.addLayout(header)

        # Search
        search = QLineEdit()
        search.setPlaceholderText("🔍 Search content...")
        search.setStyleSheet(f"""
            QLineEdit {{
                background: {CYBER_COLORS['bg_dark']};
                border: 1px solid {CYBER_COLORS['cyan']}40;
                border-radius: 5px;
                padding: 10px;
                color: {CYBER_COLORS['text']};
            }}
            QLineEdit:focus {{
                border: 1px solid {CYBER_COLORS['cyan']};
            }}
        """)
        layout.addWidget(search)

        # Content cards scroll area
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
                background: #00f0ff40;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #00f0ff;
            }
        """)

        cards_container = QWidget()
        cards_layout = QVBoxLayout(cards_container)
        cards_layout.setSpacing(10)

        # Sample content cards
        contents = [
            ("New Product Launch Announcement", "Post", "Scheduled", "2025-01-20 10:00"),
            ("Behind the Scenes Video", "Video", "Draft", "2025-01-19"),
            ("Weekly Tips & Tricks", "Post", "Published", "2025-01-18 09:30"),
            ("Customer Testimonial", "Photo", "Scheduled", "2025-01-21 14:00"),
            ("Holiday Promotion", "Story", "Draft", "2025-01-22"),
            ("Team Introduction", "Video", "Published", "2025-01-17 11:00"),
        ]

        for title, content_type, status, date in contents:
            card = ContentCard(title, content_type, status, date)
            cards_layout.addWidget(card)

        cards_layout.addStretch()
        scroll.setWidget(cards_container)
        layout.addWidget(scroll, 1)

        return panel
