"""
Pages Tab - PyQt6 Version
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox, QLineEdit, QComboBox, QProgressBar,
    QAbstractItemView
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor

from config import COLORS, TAB_COLORS

# Import shared Cyberpunk widgets
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cyber_widgets_qt import CyberTitle, CyberButton, CYBER_COLORS


class PagesTab(QWidget):
    """Pages management tab"""

    def __init__(self, log_callback=None, parent=None):
        super().__init__(parent)
        self.log_callback = log_callback
        self.pages = []

        self._setup_ui()

    def _log(self, msg, level="info"):
        if self.log_callback:
            self.log_callback(msg, level)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(20)

        # Title
        title = CyberTitle("PAGES", "Quan ly cac Fanpage Facebook", "purple")
        layout.addWidget(title)

        # Main content - 2 columns
        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)

        # Left panel - Profile selection
        left_panel = QFrame()
        left_panel.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(10,10,20,0.9), stop:1 rgba(5,5,15,0.95));
                border: 1px solid #1a1a2e;
                border-radius: 12px;
            }
        """)
        left_panel.setFixedWidth(280)

        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(12)

        # Left header
        left_header_layout = QHBoxLayout()
        left_header = QLabel("CHON PROFILE")
        left_header.setStyleSheet("color: #bf00ff; font-family: Consolas; font-size: 12px; font-weight: bold; letter-spacing: 2px; background: transparent;")
        left_header_layout.addWidget(left_header)
        left_header_layout.addStretch()

        refresh_btn = CyberButton("", "ghost", "↻")
        refresh_btn.setFixedSize(35, 35)
        left_header_layout.addWidget(refresh_btn)
        left_layout.addLayout(left_header_layout)

        # Folder filter
        folder_frame = QHBoxLayout()
        folder_label = QLabel("Thu muc:")
        folder_label.setStyleSheet("color: #a1a1aa; font-family: Consolas; font-size: 12px; background: transparent;")
        folder_frame.addWidget(folder_label)

        self.folder_combo = QComboBox()
        self.folder_combo.addItem("-- Tat ca --")
        self.folder_combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(5, 5, 15, 0.8);
                border: 1px solid #1a1a2e;
                border-radius: 6px;
                color: #e4e4e7;
                font-family: Consolas;
                font-size: 12px;
                padding: 8px 12px;
            }
        """)
        folder_frame.addWidget(self.folder_combo)
        left_layout.addLayout(folder_frame)

        # Select buttons
        btn_row = QHBoxLayout()
        select_all = CyberButton("Chon tat ca", "ghost")
        select_all.setFixedHeight(28)
        btn_row.addWidget(select_all)
        deselect_all = CyberButton("Bo chon", "ghost")
        deselect_all.setFixedHeight(28)
        btn_row.addWidget(deselect_all)
        left_layout.addLayout(btn_row)

        # Profile list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        profile_list = QWidget()
        profile_list_layout = QVBoxLayout(profile_list)
        profile_list_layout.setSpacing(4)

        for i in range(8):
            cb = QCheckBox(f"Profile {i+1}")
            cb.setStyleSheet("""
                QCheckBox { color: #e4e4e7; font-family: Consolas; spacing: 8px; background: transparent; }
                QCheckBox::indicator { width: 18px; height: 18px; border: 1px solid #1a1a2e; border-radius: 4px; background: #0a0a12; }
                QCheckBox::indicator:checked { background: #bf00ff; border-color: #bf00ff; }
            """)
            profile_list_layout.addWidget(cb)

        profile_list_layout.addStretch()
        scroll.setWidget(profile_list)
        left_layout.addWidget(scroll)

        # Stats
        stats_label = QLabel("Profiles: 8 | Da chon: 0")
        stats_label.setStyleSheet("color: #52525b; font-family: Consolas; font-size: 11px; background: transparent;")
        left_layout.addWidget(stats_label)

        content_layout.addWidget(left_panel)

        # Right panel - Pages list
        right_panel = QFrame()
        right_panel.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(10,10,20,0.9), stop:1 rgba(5,5,15,0.95));
                border: 1px solid #1a1a2e;
                border-radius: 12px;
            }
        """)

        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(12)

        # Right header
        right_header_layout = QHBoxLayout()
        right_header = QLabel("DANH SACH PAGE")
        right_header.setStyleSheet("color: #bf00ff; font-family: Consolas; font-size: 12px; font-weight: bold; letter-spacing: 2px; background: transparent;")
        right_header_layout.addWidget(right_header)
        right_header_layout.addStretch()

        # Action buttons
        create_btn = CyberButton("Tao Page", "success", "+")
        right_header_layout.addWidget(create_btn)

        scan_btn = CyberButton("Scan Page", "primary", "⌕")
        scan_btn.clicked.connect(self._scan_pages)
        right_header_layout.addWidget(scan_btn)

        delete_btn = CyberButton("Xoa", "danger", "×")
        right_header_layout.addWidget(delete_btn)

        right_layout.addLayout(right_header_layout)

        # Search and filter row
        filter_row = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Tim kiem Page...")
        self.search_input.setFixedWidth(250)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(5, 5, 15, 0.8);
                border: 1px solid #1a1a2e;
                border-radius: 6px;
                color: #e4e4e7;
                font-family: Consolas;
                font-size: 12px;
                padding: 10px 14px;
            }
            QLineEdit:focus { border-color: #bf00ff; }
        """)
        filter_row.addWidget(self.search_input)

        filter_row.addStretch()

        # Select all pages checkbox
        self.select_all_cb = QCheckBox("Chon tat ca")
        self.select_all_cb.setStyleSheet("""
            QCheckBox { color: #a1a1aa; font-family: Consolas; spacing: 8px; background: transparent; }
            QCheckBox::indicator { width: 18px; height: 18px; border: 1px solid #1a1a2e; border-radius: 4px; background: #0a0a12; }
            QCheckBox::indicator:checked { background: #bf00ff; border-color: #bf00ff; }
        """)
        filter_row.addWidget(self.select_all_cb)

        # Stats
        self.page_stats = QLabel("Tong: 0 | Da chon: 0")
        self.page_stats.setStyleSheet("color: #bf00ff; font-family: Consolas; font-size: 11px; background: transparent;")
        filter_row.addWidget(self.page_stats)

        right_layout.addLayout(filter_row)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: #0a0a12;
                border: 1px solid #1a1a2e;
                border-radius: 4px;
                height: 6px;
            }
            QProgressBar::chunk { background-color: #bf00ff; border-radius: 3px; }
        """)
        right_layout.addWidget(self.progress)

        # Pages table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["", "TEN PAGE", "FOLLOWERS", "PROFILE", "VAI TRO", "NGAY TAO"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 150)
        self.table.setColumnWidth(4, 80)
        self.table.setColumnWidth(5, 100)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setShowGrid(False)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: transparent;
                border: none;
            }
            QTableWidget::item {
                padding: 12px 16px;
                border-bottom: 1px solid #1a1a2e;
                color: #e4e4e7;
            }
            QTableWidget::item:hover { background-color: rgba(191, 0, 255, 0.03); }
            QTableWidget::item:selected { background-color: rgba(191, 0, 255, 0.1); color: #bf00ff; }
            QHeaderView::section {
                background-color: rgba(191, 0, 255, 0.05);
                border: none;
                border-bottom: 1px solid #1a1a2e;
                color: #bf00ff;
                font-family: Consolas;
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 2px;
                padding: 14px;
            }
        """)

        # Empty state
        self.empty_label = QLabel("Chua co Page nao\nChon profile va bam 'Scan Page' de quet")
        self.empty_label.setStyleSheet("color: #52525b; font-family: Consolas; font-size: 13px; background: transparent;")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        right_layout.addWidget(self.empty_label)
        right_layout.addWidget(self.table)
        self.table.setVisible(False)

        content_layout.addWidget(right_panel)
        layout.addLayout(content_layout)

    def _scan_pages(self):
        self._log("Scanning pages...", "info")
        self.progress.setVisible(True)
        self.progress.setValue(0)

        def update_progress():
            val = self.progress.value()
            if val < 100:
                self.progress.setValue(val + 5)
                QTimer.singleShot(100, update_progress)
            else:
                self.progress.setVisible(False)
                self._load_sample_pages()
                self._log("Scan completed - Found 3 pages", "success")

        QTimer.singleShot(100, update_progress)

    def _load_sample_pages(self):
        self.empty_label.setVisible(False)
        self.table.setVisible(True)

        # Sample data
        pages = [
            ("My Business Page", "12,345", "Profile 1", "Admin", "2024-01-15"),
            ("Marketing Page", "5,678", "Profile 2", "Editor", "2024-02-20"),
            ("Personal Brand", "890", "Profile 1", "Admin", "2024-03-10"),
        ]

        self.table.setRowCount(len(pages))
        for row, (name, followers, profile, role, date) in enumerate(pages):
            # Checkbox
            cb = QCheckBox()
            cb.setStyleSheet("""
                QCheckBox::indicator { width: 18px; height: 18px; border: 1px solid #1a1a2e; border-radius: 4px; background: #0a0a12; }
                QCheckBox::indicator:checked { background: #bf00ff; border-color: #bf00ff; }
            """)
            self.table.setCellWidget(row, 0, cb)

            # Name
            name_item = QTableWidgetItem(name)
            self.table.setItem(row, 1, name_item)

            # Followers
            followers_item = QTableWidgetItem(followers)
            followers_item.setForeground(QColor("#bf00ff"))
            self.table.setItem(row, 2, followers_item)

            # Profile
            profile_item = QTableWidgetItem(profile)
            profile_item.setForeground(QColor("#a1a1aa"))
            self.table.setItem(row, 3, profile_item)

            # Role
            role_color = "#00ff66" if role == "Admin" else "#fcee0a"
            role_item = QTableWidgetItem(role)
            role_item.setForeground(QColor(role_color))
            self.table.setItem(row, 4, role_item)

            # Date
            date_item = QTableWidgetItem(date)
            date_item.setForeground(QColor("#52525b"))
            self.table.setItem(row, 5, date_item)

        self.page_stats.setText(f"Tong: {len(pages)} | Da chon: 0")
