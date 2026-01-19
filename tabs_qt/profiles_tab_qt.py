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

# Import shared Cyberpunk widgets
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cyber_widgets_qt import CyberTitle, CyberStatCard, CyberButton, CYBER_COLORS


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

        self.stat_total.set_value(str(total))
        self.stat_running.set_value(str(running))
        self.stat_selected.set_value("0")
        self.stat_used.set_value(str(total))

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
