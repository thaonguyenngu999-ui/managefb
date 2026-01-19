"""
FB Manager Pro - Posts Tab (PyQt6)
Cyberpunk 2077 Theme
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QLineEdit, QComboBox, QCheckBox, QTextEdit, QSpinBox,
    QScrollArea, QGridLayout, QProgressBar, QSplitter
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor

# Import shared Cyberpunk widgets
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cyber_widgets_qt import CyberTitle, CyberStatCard, CyberButton, CYBER_COLORS


class PostCard(QFrame):
    """Post preview card"""

    def __init__(self, content: str, profile: str, date: str, reactions: str, comments: str, shares: str, parent=None):
        super().__init__(parent)
        self.setObjectName("postCard")
        self._setup_ui(content, profile, date, reactions, comments, shares)

    def _setup_ui(self, content: str, profile: str, date: str, reactions: str, comments: str, shares: str):
        self.setStyleSheet(f"""
            QFrame#postCard {{
                background: {CYBER_COLORS['bg_lighter']};
                border: 1px solid {CYBER_COLORS['green']}40;
                border-radius: 8px;
                padding: 15px;
            }}
            QFrame#postCard:hover {{
                border: 1px solid {CYBER_COLORS['green']};
                background: {CYBER_COLORS['green']}05;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()

        avatar = QLabel("👤")
        avatar.setStyleSheet(f"""
            background: {CYBER_COLORS['cyan']}30;
            border-radius: 15px;
            padding: 5px;
            font-size: 16px;
        """)
        avatar.setFixedSize(32, 32)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(avatar)

        profile_info = QVBoxLayout()
        profile_info.setSpacing(2)

        profile_name = QLabel(profile)
        profile_name.setStyleSheet(f"color: {CYBER_COLORS['text']}; font-weight: bold; font-size: 13px;")
        profile_info.addWidget(profile_name)

        date_label = QLabel(date)
        date_label.setStyleSheet(f"color: {CYBER_COLORS['text_dim']}; font-size: 11px;")
        profile_info.addWidget(date_label)

        header.addLayout(profile_info, 1)

        # Menu button
        menu_btn = QPushButton("⋮")
        menu_btn.setFixedSize(28, 28)
        menu_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {CYBER_COLORS['text_dim']};
                font-size: 16px;
            }}
            QPushButton:hover {{
                color: {CYBER_COLORS['text']};
            }}
        """)
        header.addWidget(menu_btn)

        layout.addLayout(header)

        # Content
        content_label = QLabel(content)
        content_label.setWordWrap(True)
        content_label.setStyleSheet(f"""
            color: {CYBER_COLORS['text']};
            font-size: 13px;
            line-height: 1.4;
        """)
        layout.addWidget(content_label)

        # Stats
        stats = QHBoxLayout()
        stats.setSpacing(20)

        reactions_label = QLabel(f"❤️ {reactions}")
        reactions_label.setStyleSheet(f"color: {CYBER_COLORS['magenta']}; font-size: 12px;")
        stats.addWidget(reactions_label)

        comments_label = QLabel(f"💬 {comments}")
        comments_label.setStyleSheet(f"color: {CYBER_COLORS['cyan']}; font-size: 12px;")
        stats.addWidget(comments_label)

        shares_label = QLabel(f"🔄 {shares}")
        shares_label.setStyleSheet(f"color: {CYBER_COLORS['green']}; font-size: 12px;")
        stats.addWidget(shares_label)

        stats.addStretch()
        layout.addLayout(stats)

        # Actions
        actions = QHBoxLayout()
        actions.setSpacing(8)

        like_btn = QPushButton("❤️ Like")
        like_btn.setStyleSheet(f"""
            QPushButton {{
                background: {CYBER_COLORS['magenta']}15;
                border: 1px solid {CYBER_COLORS['magenta']}30;
                border-radius: 4px;
                color: {CYBER_COLORS['magenta']};
                padding: 6px 12px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: {CYBER_COLORS['magenta']}30;
            }}
        """)
        actions.addWidget(like_btn)

        comment_btn = QPushButton("💬 Comment")
        comment_btn.setStyleSheet(f"""
            QPushButton {{
                background: {CYBER_COLORS['cyan']}15;
                border: 1px solid {CYBER_COLORS['cyan']}30;
                border-radius: 4px;
                color: {CYBER_COLORS['cyan']};
                padding: 6px 12px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: {CYBER_COLORS['cyan']}30;
            }}
        """)
        actions.addWidget(comment_btn)

        share_btn = QPushButton("🔄 Share")
        share_btn.setStyleSheet(f"""
            QPushButton {{
                background: {CYBER_COLORS['green']}15;
                border: 1px solid {CYBER_COLORS['green']}30;
                border-radius: 4px;
                color: {CYBER_COLORS['green']};
                padding: 6px 12px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: {CYBER_COLORS['green']}30;
            }}
        """)
        actions.addWidget(share_btn)

        actions.addStretch()

        delete_btn = QPushButton("🗑️")
        delete_btn.setFixedSize(28, 28)
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background: {CYBER_COLORS['red']}15;
                border: 1px solid {CYBER_COLORS['red']}30;
                border-radius: 4px;
                color: {CYBER_COLORS['red']};
            }}
            QPushButton:hover {{
                background: {CYBER_COLORS['red']}30;
            }}
        """)
        actions.addWidget(delete_btn)

        layout.addLayout(actions)


class PostsTabQt(QWidget):
    """Posts management tab with Cyberpunk styling"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("postsTab")
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Left panel - Profile selection
        left_panel = self._create_profile_panel()
        main_layout.addWidget(left_panel)

        # Right panel - Posts feed
        right_panel = self._create_posts_panel()
        main_layout.addWidget(right_panel, 1)

    def _create_profile_panel(self):
        """Create profile selection panel"""
        panel = QFrame()
        panel.setObjectName("profilePanel")
        panel.setFixedWidth(280)
        panel.setStyleSheet(f"""
            QFrame#profilePanel {{
                background: {CYBER_COLORS['bg_card']};
                border: 1px solid {CYBER_COLORS['green']}40;
                border-radius: 10px;
            }}
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Title
        title = CyberTitle("PROFILES", "green")
        layout.addWidget(title)

        # Search
        search = QLineEdit()
        search.setPlaceholderText("🔍 Search profiles...")
        search.setStyleSheet(f"""
            QLineEdit {{
                background: {CYBER_COLORS['bg_dark']};
                border: 1px solid {CYBER_COLORS['green']}40;
                border-radius: 5px;
                padding: 10px;
                color: {CYBER_COLORS['text']};
            }}
            QLineEdit:focus {{
                border: 1px solid {CYBER_COLORS['green']};
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
            ("John Doe", "15 posts", True),
            ("Jane Smith", "28 posts", False),
            ("Mike Johnson", "42 posts", True),
            ("Sarah Wilson", "8 posts", False),
        ]

        for name, posts, checked in profiles:
            item = self._create_profile_item(name, posts, checked)
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
                border: 2px solid {CYBER_COLORS['green']};
                border-radius: 3px;
            }}
            QCheckBox::indicator:checked {{
                background: {CYBER_COLORS['green']};
            }}
        """)
        layout.addWidget(select_all)

        # Load posts button
        load_btn = CyberButton("📥 Load Posts", "green")
        load_btn.setFixedHeight(40)
        layout.addWidget(load_btn)

        return panel

    def _create_profile_item(self, name: str, posts: str, checked: bool):
        """Create profile item widget"""
        item = QFrame()
        item.setStyleSheet(f"""
            QFrame {{
                background: {CYBER_COLORS['bg_lighter']};
                border: 1px solid {CYBER_COLORS['green']}30;
                border-radius: 5px;
                padding: 8px;
            }}
            QFrame:hover {{
                border: 1px solid {CYBER_COLORS['green']};
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
                border: 2px solid {CYBER_COLORS['green']};
                border-radius: 3px;
            }}
            QCheckBox::indicator:checked {{
                background: {CYBER_COLORS['green']};
            }}
        """)
        layout.addWidget(checkbox)

        info = QVBoxLayout()
        info.setSpacing(2)

        name_label = QLabel(name)
        name_label.setStyleSheet(f"color: {CYBER_COLORS['text']}; font-weight: bold;")
        info.addWidget(name_label)

        posts_label = QLabel(posts)
        posts_label.setStyleSheet(f"color: {CYBER_COLORS['text_dim']}; font-size: 11px;")
        info.addWidget(posts_label)

        layout.addLayout(info, 1)

        return item

    def _create_posts_panel(self):
        """Create posts feed panel"""
        panel = QFrame()
        panel.setObjectName("postsPanel")
        panel.setStyleSheet(f"""
            QFrame#postsPanel {{
                background: {CYBER_COLORS['bg_card']};
                border: 1px solid {CYBER_COLORS['green']}40;
                border-radius: 10px;
            }}
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title = CyberTitle("POSTS FEED", "green")
        layout.addWidget(title)

        # Stats row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(15)

        stats = [
            ("📝", "Total Posts", "93", "green"),
            ("❤️", "Reactions", "2.4K", "magenta"),
            ("💬", "Comments", "856", "cyan"),
            ("🔄", "Shares", "234", "orange"),
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
        search.setPlaceholderText("🔍 Search posts...")
        search.setStyleSheet(f"""
            QLineEdit {{
                background: {CYBER_COLORS['bg_dark']};
                border: 1px solid {CYBER_COLORS['green']}40;
                border-radius: 5px;
                padding: 10px;
                color: {CYBER_COLORS['text']};
                min-width: 200px;
            }}
            QLineEdit:focus {{
                border: 1px solid {CYBER_COLORS['green']};
            }}
        """)
        toolbar.addWidget(search)

        # Date filter
        date_combo = QComboBox()
        date_combo.addItems(["All Time", "Today", "This Week", "This Month", "This Year"])
        date_combo.setStyleSheet(f"""
            QComboBox {{
                background: {CYBER_COLORS['bg_dark']};
                border: 1px solid {CYBER_COLORS['green']}40;
                border-radius: 4px;
                padding: 8px 15px;
                color: {CYBER_COLORS['text']};
            }}
        """)
        toolbar.addWidget(date_combo)

        # Sort
        sort_combo = QComboBox()
        sort_combo.addItems(["Newest", "Most Reactions", "Most Comments", "Most Shares"])
        sort_combo.setStyleSheet(date_combo.styleSheet())
        toolbar.addWidget(sort_combo)

        toolbar.addStretch()

        # Actions
        new_post_btn = CyberButton("✏️ New Post", "green")
        toolbar.addWidget(new_post_btn)

        refresh_btn = CyberButton("🔄 Refresh", "cyan")
        toolbar.addWidget(refresh_btn)

        layout.addLayout(toolbar)

        # Create post area
        create_frame = QFrame()
        create_frame.setStyleSheet(f"""
            QFrame {{
                background: {CYBER_COLORS['bg_lighter']};
                border: 1px solid {CYBER_COLORS['cyan']}30;
                border-radius: 8px;
                padding: 15px;
            }}
        """)

        create_layout = QVBoxLayout(create_frame)
        create_layout.setSpacing(10)

        create_title = QLabel("✏️ CREATE NEW POST")
        create_title.setStyleSheet(f"""
            color: {CYBER_COLORS['cyan']};
            font-weight: bold;
            font-size: 12px;
            letter-spacing: 1px;
        """)
        create_layout.addWidget(create_title)

        post_input = QTextEdit()
        post_input.setPlaceholderText("What's on your mind?")
        post_input.setMaximumHeight(80)
        post_input.setStyleSheet(f"""
            QTextEdit {{
                background: {CYBER_COLORS['bg_dark']};
                border: 1px solid {CYBER_COLORS['cyan']}40;
                border-radius: 5px;
                padding: 10px;
                color: {CYBER_COLORS['text']};
                font-size: 13px;
            }}
            QTextEdit:focus {{
                border: 1px solid {CYBER_COLORS['cyan']};
            }}
        """)
        create_layout.addWidget(post_input)

        create_actions = QHBoxLayout()

        media_btn = QPushButton("📷 Photo")
        media_btn.setStyleSheet(f"""
            QPushButton {{
                background: {CYBER_COLORS['orange']}15;
                border: 1px solid {CYBER_COLORS['orange']}30;
                border-radius: 4px;
                color: {CYBER_COLORS['orange']};
                padding: 6px 12px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: {CYBER_COLORS['orange']}30;
            }}
        """)
        create_actions.addWidget(media_btn)

        video_btn = QPushButton("🎬 Video")
        video_btn.setStyleSheet(media_btn.styleSheet().replace(CYBER_COLORS['orange'], CYBER_COLORS['magenta']))
        create_actions.addWidget(video_btn)

        link_btn = QPushButton("🔗 Link")
        link_btn.setStyleSheet(media_btn.styleSheet().replace(CYBER_COLORS['orange'], CYBER_COLORS['cyan']))
        create_actions.addWidget(link_btn)

        create_actions.addStretch()

        post_btn = CyberButton("📤 Post", "green")
        create_actions.addWidget(post_btn)

        create_layout.addLayout(create_actions)
        layout.addWidget(create_frame)

        # Posts feed
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
                background: #00ff6640;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #00ff66;
            }
        """)

        posts_container = QWidget()
        posts_layout = QVBoxLayout(posts_container)
        posts_layout.setSpacing(15)

        # Sample posts
        posts = [
            ("Just launched our new product! Check it out at our website. #launch #newproduct #excited",
             "John Doe", "2 hours ago", "156", "42", "28"),
            ("Great meeting with the team today. So many exciting ideas for 2025! 🚀",
             "Jane Smith", "5 hours ago", "89", "15", "8"),
            ("Tips for better productivity: 1. Start early 2. Take breaks 3. Stay focused. What are yours?",
             "Mike Johnson", "Yesterday", "234", "67", "45"),
            ("Behind the scenes of our latest photoshoot! More content coming soon 📸",
             "Sarah Wilson", "2 days ago", "412", "93", "67"),
        ]

        for content, profile, date, reactions, comments, shares in posts:
            card = PostCard(content, profile, date, reactions, comments, shares)
            posts_layout.addWidget(card)

        posts_layout.addStretch()
        scroll.setWidget(posts_container)
        layout.addWidget(scroll, 1)

        return panel
