"""
FB Manager Pro - PyQt6 Version
CYBERPUNK 2077 Theme
"""
import sys
import os
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QStackedWidget, QScrollArea,
    QSizePolicy, QSpacerItem, QTextEdit, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty, QPoint
from PyQt6.QtGui import QFont, QColor, QPalette, QPainter, QBrush, QPen, QPolygon, QFontDatabase

# Import config
from config import COLORS, TAB_COLORS, FONTS

# Import shared Cyberpunk widgets
from cyber_widgets_qt import (
    CyberTitle, CyberStatCard, CyberButton, CyberTerminal,
    CyberGlitchLabel, CyberTriangle, CYBER_COLORS
)

# Import PyQt6 tabs
from tabs_qt.profiles_tab_qt import ProfilesTab
from tabs_qt.login_tab_qt import LoginTab
from tabs_qt.pages_tab_qt import PagesTab
from tabs_qt.reels_tab_qt import ReelsTabQt
from tabs_qt.content_tab_qt import ContentTabQt
from tabs_qt.groups_tab_qt import GroupsTabQt
from tabs_qt.scripts_tab_qt import ScriptsTabQt
from tabs_qt.posts_tab_qt import PostsTabQt


class RGBGradientSidebar(QFrame):
    """Sidebar with RGB gradient border on the right"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self._gradient_offset = 0
        self._setup_animation()

    def _setup_animation(self):
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate_gradient)
        self._timer.start(50)

    def _animate_gradient(self):
        self._gradient_offset = (self._gradient_offset + 2) % 360
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        from PyQt6.QtGui import QLinearGradient
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw RGB gradient border on the right
        rect = self.rect()
        border_width = 3

        # Create gradient
        gradient = QLinearGradient(rect.right() - border_width, 0,
                                   rect.right() - border_width, rect.height())

        # RGB colors with offset for animation
        offset = self._gradient_offset / 360.0
        gradient.setColorAt((0.0 + offset) % 1.0, QColor("#00f0ff"))
        gradient.setColorAt((0.25 + offset) % 1.0, QColor("#ff00a8"))
        gradient.setColorAt((0.5 + offset) % 1.0, QColor("#bf00ff"))
        gradient.setColorAt((0.75 + offset) % 1.0, QColor("#00ff66"))
        gradient.setColorAt(1.0, QColor("#00f0ff"))

        # Draw the border
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawRect(rect.right() - border_width, 0, border_width, rect.height())


class RGBGradientLogPanel(QFrame):
    """Log panel with RGB gradient border on the left"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("logPanel")
        self._gradient_offset = 0
        self._setup_animation()

    def _setup_animation(self):
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate_gradient)
        self._timer.start(50)

    def _animate_gradient(self):
        self._gradient_offset = (self._gradient_offset + 2) % 360
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        from PyQt6.QtGui import QLinearGradient
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw RGB gradient border on the left
        rect = self.rect()
        border_width = 3

        # Create gradient (green-cyan for log panel)
        gradient = QLinearGradient(0, 0, 0, rect.height())

        # Green-cyan colors with offset for animation
        offset = self._gradient_offset / 360.0
        gradient.setColorAt((0.0 + offset) % 1.0, QColor("#00ff66"))
        gradient.setColorAt((0.33 + offset) % 1.0, QColor("#00f0ff"))
        gradient.setColorAt((0.66 + offset) % 1.0, QColor("#00ff66"))
        gradient.setColorAt(1.0, QColor("#00f0ff"))

        # Draw the border
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawRect(0, 0, border_width, rect.height())


class NavItem(QPushButton):
    """Navigation item for sidebar"""

    def __init__(self, text, icon, tab_id, color="cyan", parent=None):
        super().__init__(f"  {icon}   {text}", parent)

        self.tab_id = tab_id
        self.color = color
        self._is_active = False

        color_map = {
            "cyan": "#00f0ff",
            "green": "#00ff66",
            "purple": "#bf00ff",
            "magenta": "#ff00a8",
            "yellow": "#fcee0a",
            "orange": "#ff6b00",
        }
        self.accent_color = color_map.get(color, "#00f0ff")

        self.setObjectName("navItem")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)
        self._update_style()

    def _update_style(self):
        if self._is_active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, x2:1, stop:0 rgba({self._hex_to_rgb(self.accent_color)},0.15), stop:1 transparent);
                    border: 1px solid transparent;
                    border-left: 4px solid {self.accent_color};
                    border-radius: 8px;
                    color: {self.accent_color};
                    font-family: Consolas;
                    font-size: 14px;
                    font-weight: bold;
                    text-align: left;
                    padding: 14px 16px;
                    margin: 4px 12px;
                }}
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: 1px solid transparent;
                    border-radius: 8px;
                    color: #a1a1aa;
                    font-family: Consolas;
                    font-size: 14px;
                    font-weight: bold;
                    text-align: left;
                    padding: 14px 16px;
                    margin: 4px 12px;
                }
                QPushButton:hover {
                    background-color: rgba(0, 240, 255, 0.05);
                    border-color: rgba(0, 240, 255, 0.2);
                    color: #e4e4e7;
                }
            """)

    def _hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return ','.join(str(int(hex_color[i:i+2], 16)) for i in (0, 2, 4))

    def set_active(self, active):
        self._is_active = active
        self._update_style()


class Terminal(QTextEdit):
    """Terminal log viewer"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setObjectName("terminal")
        self.setStyleSheet("""
            QTextEdit {
                background-color: rgba(0, 0, 0, 0.5);
                border: 1px solid #1a1a2e;
                border-radius: 8px;
                color: #a1a1aa;
                font-family: Consolas;
                font-size: 11px;
                padding: 16px;
            }
        """)

    def add_log(self, message, log_type="info"):
        timestamp = datetime.now().strftime("[%H:%M:%S]")

        colors = {
            "info": "#00f0ff",
            "success": "#00ff66",
            "warning": "#fcee0a",
            "error": "#ff003c",
        }
        color = colors.get(log_type, "#a1a1aa")

        html = f'<span style="color: #52525b;">{timestamp}</span> <span style="color: {color};">{message}</span><br>'
        self.append(html)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())


class FBManagerApp(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("FB Manager Pro v2.0.77 - CYBERPUNK 2077")
        self.setMinimumSize(1400, 900)

        # Load stylesheet
        self._load_stylesheet()

        # Setup UI
        self._setup_ui()

        # Initialize
        self.current_tab = "profiles"
        self._switch_tab("profiles")

        # Add initial logs
        self.terminal.add_log("FB Manager Pro initialized", "success")
        self.terminal.add_log("CYBERPUNK 2077 theme loaded", "info")

    def _load_stylesheet(self):
        qss_path = Path(__file__).parent / "cyberpunk.qss"
        if qss_path.exists():
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

    def _setup_ui(self):
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        # Main layout
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create terminal first (needed for log callbacks)
        self.terminal = Terminal()

        # Sidebar
        self._create_sidebar(main_layout)

        # Main content
        self._create_main_content(main_layout)

        # Log panel
        self._create_log_panel(main_layout)

    def _create_sidebar(self, parent_layout):
        sidebar = RGBGradientSidebar()
        sidebar.setFixedWidth(240)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo section
        logo_section = QWidget()
        logo_layout = QHBoxLayout(logo_section)
        logo_layout.setContentsMargins(20, 24, 20, 24)
        logo_layout.setSpacing(14)

        # Logo box
        logo_box = QFrame()
        logo_box.setObjectName("logoBox")
        logo_box.setFixedSize(50, 50)
        logo_box_layout = QVBoxLayout(logo_box)
        logo_box_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fb_label = QLabel("FB")
        fb_label.setStyleSheet("color: #05050a; font-family: Consolas; font-size: 18px; font-weight: bold;")
        logo_box_layout.addWidget(fb_label)
        logo_layout.addWidget(logo_box)

        # Logo title
        title_widget = QWidget()
        title_layout = QVBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(2)

        main_title = QLabel("FB MANAGER")
        main_title.setObjectName("logoTitle")
        title_layout.addWidget(main_title)

        sub_title = QLabel("CYBERPUNK 2077")
        sub_title.setObjectName("logoSubtitle")
        title_layout.addWidget(sub_title)

        logo_layout.addWidget(title_widget)
        logo_layout.addStretch()

        layout.addWidget(logo_section)

        # Divider
        divider = QFrame()
        divider.setObjectName("divider")
        divider.setFixedHeight(1)
        layout.addWidget(divider)

        # Menu label
        menu_label = QLabel("◢ MAIN MENU")
        menu_label.setObjectName("menuLabel")
        layout.addWidget(menu_label)

        # Navigation items
        self.nav_items = {}
        nav_data = [
            ("profiles", "◆", "Profiles", "cyan"),
            ("login", "◆", "Login FB", "green"),
            ("pages", "◆", "Pages", "purple"),
            ("reels", "◆", "Reels", "magenta"),
            ("content", "◆", "Soan tin", "yellow"),
            ("groups", "◆", "Dang nhom", "orange"),
            ("scripts", "◆", "Kich ban", "cyan"),
            ("posts", "◆", "Bai dang", "green"),
        ]

        for tab_id, icon, text, color in nav_data:
            nav = NavItem(text, icon, tab_id, color)
            nav.clicked.connect(lambda checked, t=tab_id: self._switch_tab(t))
            layout.addWidget(nav)
            self.nav_items[tab_id] = nav

        layout.addStretch()

        # Connection status
        conn_frame = QFrame()
        conn_frame.setObjectName("connectionStatus")
        conn_layout = QHBoxLayout(conn_frame)
        conn_layout.setContentsMargins(12, 12, 12, 12)
        conn_layout.setSpacing(10)

        led = QFrame()
        led.setObjectName("ledIndicator")
        led.setFixedSize(10, 10)
        conn_layout.addWidget(led)

        conn_label = QLabel("HIDEMIUM ONLINE")
        conn_label.setStyleSheet("color: #00ff66; font-family: Consolas; font-size: 11px;")
        conn_layout.addWidget(conn_label)
        conn_layout.addStretch()

        layout.addWidget(conn_frame)

        # Settings button
        settings_btn = NavItem("Settings", "◆", "settings", "cyan")
        layout.addWidget(settings_btn)

        # Version
        version = QLabel("v2.0.77 // CYBERPUNK")
        version.setObjectName("versionLabel")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)

        layout.addSpacing(16)

        parent_layout.addWidget(sidebar)

    def _create_main_content(self, parent_layout):
        main_content = QWidget()
        main_content.setObjectName("mainContent")

        layout = QVBoxLayout(main_content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Content area (stacked widget for tabs)
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("contentArea")

        # Create tabs
        self.tabs = {}

        # Profiles tab
        profiles_tab = ProfilesTab(self._add_log)
        self.tabs["profiles"] = profiles_tab
        self.content_stack.addWidget(profiles_tab)

        # Login tab
        login_tab = LoginTab(self._add_log)
        self.tabs["login"] = login_tab
        self.content_stack.addWidget(login_tab)

        # Pages tab
        pages_tab = PagesTab(self._add_log)
        self.tabs["pages"] = pages_tab
        self.content_stack.addWidget(pages_tab)

        # Reels tab
        reels_tab = ReelsTabQt()
        self.tabs["reels"] = reels_tab
        self.content_stack.addWidget(reels_tab)

        # Content tab
        content_tab = ContentTabQt()
        self.tabs["content"] = content_tab
        self.content_stack.addWidget(content_tab)

        # Groups tab
        groups_tab = GroupsTabQt()
        self.tabs["groups"] = groups_tab
        self.content_stack.addWidget(groups_tab)

        # Scripts tab
        scripts_tab = ScriptsTabQt()
        self.tabs["scripts"] = scripts_tab
        self.content_stack.addWidget(scripts_tab)

        # Posts tab
        posts_tab = PostsTabQt()
        self.tabs["posts"] = posts_tab
        self.content_stack.addWidget(posts_tab)

        layout.addWidget(self.content_stack)

        # Status bar
        status_bar = QFrame()
        status_bar.setObjectName("statusBar")
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(20, 0, 20, 0)

        # Left side
        led = QFrame()
        led.setObjectName("ledIndicator")
        led.setFixedSize(8, 8)
        status_layout.addWidget(led)

        status_text = QLabel("ONLINE")
        status_text.setStyleSheet("color: #00ff66;")
        status_layout.addWidget(status_text)

        status_layout.addStretch()

        # Right side
        hidemium_status = QLabel("HIDEMIUM: OK")
        status_layout.addWidget(hidemium_status)

        version_label = QLabel("v2.0.77")
        version_label.setStyleSheet("color: #00f0ff;")
        status_layout.addWidget(version_label)

        layout.addWidget(status_bar)

        parent_layout.addWidget(main_content, 1)

    def _create_log_panel(self, parent_layout):
        log_panel = RGBGradientLogPanel()
        log_panel.setFixedWidth(360)

        layout = QVBoxLayout(log_panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setObjectName("logHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 18, 20, 18)

        title = QLabel("◢ TERMINAL LOG")
        title.setObjectName("logTitle")
        header_layout.addWidget(title)

        header_layout.addStretch()

        clear_btn = QPushButton("CLEAR")
        clear_btn.setObjectName("clearBtn")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_logs)
        header_layout.addWidget(clear_btn)

        layout.addWidget(header)

        # Terminal (already created in _setup_ui)
        layout.addWidget(self.terminal, 1)

        layout.addSpacing(16)

        parent_layout.addWidget(log_panel)

    def _switch_tab(self, tab_id):
        # Update nav items
        for nav_id, nav_item in self.nav_items.items():
            nav_item.set_active(nav_id == tab_id)

        # Switch content
        if tab_id in self.tabs:
            self.content_stack.setCurrentWidget(self.tabs[tab_id])
            self.current_tab = tab_id
            self._add_log(f"Switched to {tab_id.upper()}", "info")

    def _add_log(self, message, log_type="info"):
        self.terminal.add_log(message, log_type)

    def _clear_logs(self):
        self.terminal.clear()
        self._add_log("Terminal cleared", "info")


def main():
    app = QApplication(sys.argv)

    # Set application-wide font
    font = QFont("Consolas", 11)
    app.setFont(font)

    # Create and show main window
    window = FBManagerApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
