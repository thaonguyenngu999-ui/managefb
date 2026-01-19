"""
FB Manager Pro - Cyberpunk Edition
Professional Facebook Manager with Neon Dark Theme
"""
import customtkinter as ctk
import sys
import io
from datetime import datetime
from config import COLORS, WINDOW_WIDTH, WINDOW_HEIGHT, APP_NAME, APP_VERSION, TAB_COLORS, FONTS, SPACING, RADIUS, HEIGHTS
from widgets import StatusBar
from cyber_widgets import CyberNavItem, CyberTerminal
from tabs import ProfilesTab, ScriptsTab, PostsTab, ContentTab, GroupsTab, LoginTab, PagesTab, ReelsPageTab


class LogRedirector(io.StringIO):
    """Redirect stdout/stderr to a callback function"""
    def __init__(self, callback, original_stream):
        super().__init__()
        self.callback = callback
        self.original_stream = original_stream

    def write(self, text):
        if text.strip():
            self.callback(text)
        if self.original_stream:
            self.original_stream.write(text)
            self.original_stream.flush()

    def flush(self):
        if self.original_stream:
            self.original_stream.flush()


class FBManagerApp(ctk.CTk):
    """FB Manager Pro - Cyberpunk Edition"""

    def __init__(self):
        super().__init__()

        # Window setup
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry(f"{WINDOW_WIDTH + 380}x{WINDOW_HEIGHT}")
        self.minsize(1500, 700)

        # Theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color=COLORS["bg_main"])

        # State
        self.current_tab = "profiles"
        self.status_bar = None

        # Build UI
        self._create_sidebar()
        self._create_content_area()
        self._create_log_panel()
        self._create_tabs()
        self._setup_log_redirector()

        # Show default
        self._show_tab("profiles")
        self._add_log("FB Manager Pro initialized", "success")

    def _create_sidebar(self):
        """Cyberpunk sidebar with neon accents"""
        self.sidebar = ctk.CTkFrame(
            self,
            width=SIDEBAR_WIDTH if 'SIDEBAR_WIDTH' in dir() else 240,
            corner_radius=0,
            fg_color=COLORS["bg_sidebar"]
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo at top
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=80)
        logo_frame.pack(fill="x")
        logo_frame.pack_propagate(False)

        # Cyberpunk brand logo
        logo_container = ctk.CTkFrame(logo_frame, fg_color="transparent")
        logo_container.place(relx=0.5, rely=0.5, anchor="center")

        # Glitch-style logo
        ctk.CTkLabel(
            logo_container,
            text="◢",
            font=ctk.CTkFont(size=32),
            text_color=COLORS["neon_cyan"]
        ).pack(side="left")

        brand_frame = ctk.CTkFrame(logo_container, fg_color="transparent")
        brand_frame.pack(side="left", padx=(8, 0))

        ctk.CTkLabel(
            brand_frame,
            text="FB",
            font=ctk.CTkFont(family=FONTS["family_display"], size=20, weight="bold"),
            text_color=COLORS["neon_cyan"]
        ).pack(side="left")

        ctk.CTkLabel(
            brand_frame,
            text="MANAGER",
            font=ctk.CTkFont(family=FONTS["family_display"], size=20, weight="bold"),
            text_color=COLORS["neon_magenta"]
        ).pack(side="left", padx=(4, 0))

        # Divider
        ctk.CTkFrame(self.sidebar, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=16)

        # Navigation items
        nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_frame.pack(fill="both", expand=True, pady=16)

        self.nav_items = {}
        nav_config = [
            ("profiles", "◢", "PROFILES"),
            ("login", "◆", "LOGIN"),
            ("pages", "◈", "PAGES"),
            ("reels_page", "◇", "REELS"),
            ("content", "◆", "CONTENT"),
            ("groups", "◢", "GROUPS"),
            ("scripts", "◇", "SCRIPTS"),
            ("posts", "◈", "POSTS"),
        ]

        for tab_id, icon, text in nav_config:
            nav_item = CyberNavItem(
                nav_frame,
                tab_id=tab_id,
                icon=icon,
                text=text,
                command=self._show_tab
            )
            nav_item.pack(fill="x", pady=2, padx=8)
            self.nav_items[tab_id] = nav_item

        # Bottom section
        bottom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=120)
        bottom_frame.pack(side="bottom", fill="x", pady=16)
        bottom_frame.pack_propagate(False)

        # Divider
        ctk.CTkFrame(bottom_frame, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=16, pady=(0, 16))

        # Settings button
        settings_btn = ctk.CTkButton(
            bottom_frame,
            text="◆ SETTINGS",
            height=HEIGHTS["nav_item"],
            fg_color="transparent",
            hover_color=COLORS["bg_hover"],
            corner_radius=RADIUS["md"],
            font=ctk.CTkFont(family=FONTS["family_display"], size=FONTS["size_sm"], weight="bold"),
            text_color=COLORS["text_secondary"],
            anchor="w",
            command=self._open_settings
        )
        settings_btn.pack(fill="x", padx=12)

        # Connection indicator
        conn_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        conn_frame.pack(fill="x", padx=16, pady=(12, 0))

        ctk.CTkLabel(
            conn_frame,
            text="HIDEMIUM",
            font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_xs"]),
            text_color=COLORS["text_muted"]
        ).pack(side="left")

        self.connection_indicator = ctk.CTkLabel(
            conn_frame,
            text="● CONNECTING",
            font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_xs"]),
            text_color=COLORS["neon_yellow"]
        )
        self.connection_indicator.pack(side="right")

        self.after(1000, self._check_hidemium_connection)

    def _create_content_area(self):
        """Main content area with cyberpunk header"""
        self.content_area = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_main"],
            corner_radius=0
        )
        self.content_area.pack(side="left", fill="both", expand=True)

        # Header bar
        self.header = ctk.CTkFrame(
            self.content_area,
            height=HEIGHTS["header"],
            fg_color=COLORS["bg_header"],
            corner_radius=0
        )
        self.header.pack(fill="x")
        self.header.pack_propagate(False)

        # Header left - Page title with accent
        header_left = ctk.CTkFrame(self.header, fg_color="transparent")
        header_left.pack(side="left", padx=24)

        self.page_icon = ctk.CTkLabel(
            header_left,
            text="◢",
            font=ctk.CTkFont(size=20),
            text_color=TAB_COLORS["profiles"]
        )
        self.page_icon.pack(side="left")

        self.page_title = ctk.CTkLabel(
            header_left,
            text="PROFILES",
            font=ctk.CTkFont(family=FONTS["family_display"], size=FONTS["size_lg"], weight="bold"),
            text_color=COLORS["text_primary"]
        )
        self.page_title.pack(side="left", padx=(8, 0))

        # Header right - Version badge
        header_right = ctk.CTkFrame(self.header, fg_color="transparent")
        header_right.pack(side="right", padx=24)

        version_badge = ctk.CTkFrame(
            header_right,
            fg_color=COLORS["bg_secondary"],
            corner_radius=RADIUS["md"]
        )
        version_badge.pack()

        ctk.CTkLabel(
            version_badge,
            text=f"v{APP_VERSION}",
            font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_xs"]),
            text_color=COLORS["neon_cyan"]
        ).pack(padx=12, pady=4)

        # Main frame for tabs
        self.main_frame = ctk.CTkFrame(
            self.content_area,
            fg_color=COLORS["bg_main"],
            corner_radius=0
        )
        self.main_frame.pack(fill="both", expand=True)

        # Status bar
        self.status_bar = StatusBar(self.content_area)
        self.status_bar.pack(side="bottom", fill="x")

    def _create_log_panel(self):
        """Log panel with cyberpunk terminal style"""
        self.log_panel = ctk.CTkFrame(
            self,
            width=360,
            fg_color=COLORS["bg_sidebar"],
            corner_radius=0
        )
        self.log_panel.pack(side="right", fill="y")
        self.log_panel.pack_propagate(False)

        # Header
        header = ctk.CTkFrame(self.log_panel, fg_color=COLORS["bg_header"], height=HEIGHTS["header"], corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(fill="x", padx=16, pady=16)

        ctk.CTkLabel(
            header_content,
            text="◢",
            font=ctk.CTkFont(size=16),
            text_color=COLORS["neon_green"]
        ).pack(side="left")

        ctk.CTkLabel(
            header_content,
            text="SYSTEM LOG",
            font=ctk.CTkFont(family=FONTS["family_display"], size=FONTS["size_sm"], weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left", padx=(8, 0))

        ctk.CTkButton(
            header_content,
            text="CLEAR",
            width=60,
            height=28,
            corner_radius=RADIUS["md"],
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["neon_red"],
            hover_color=COLORS["neon_red"],
            font=ctk.CTkFont(family=FONTS["family_display"], size=FONTS["size_xs"], weight="bold"),
            text_color=COLORS["neon_red"],
            command=self._clear_logs
        ).pack(side="right")

        # Log terminal
        log_container = ctk.CTkFrame(self.log_panel, fg_color="transparent")
        log_container.pack(fill="both", expand=True, padx=8, pady=8)

        self.log_terminal = CyberTerminal(log_container)
        self.log_terminal.pack(fill="both", expand=True)

        # Keep reference to textbox for compatibility
        self.log_text = self.log_terminal.textbox

    def _create_tabs(self):
        """Initialize all tabs"""
        self.tabs = {}
        self.tabs["profiles"] = ProfilesTab(self.main_frame, status_callback=self._update_status)
        self.tabs["login"] = LoginTab(self.main_frame, status_callback=self._update_status)
        self.tabs["pages"] = PagesTab(self.main_frame, status_callback=self._update_status)
        self.tabs["reels_page"] = ReelsPageTab(self.main_frame, status_callback=self._update_status)
        self.tabs["content"] = ContentTab(self.main_frame, status_callback=self._update_status)
        self.tabs["groups"] = GroupsTab(self.main_frame, status_callback=self._update_status)
        self.tabs["scripts"] = ScriptsTab(self.main_frame, status_callback=self._update_status)
        self.tabs["posts"] = PostsTab(self.main_frame, status_callback=self._update_status)

    def _show_tab(self, tab_id: str):
        """Switch to selected tab with cyberpunk effects"""
        # Hide all
        for tab in self.tabs.values():
            tab.pack_forget()

        # Update nav items
        for nav_id, nav_item in self.nav_items.items():
            nav_item.set_active(nav_id == tab_id)

        # Tab titles and icons
        tab_info = {
            "profiles": ("PROFILES", "◢"),
            "login": ("LOGIN", "◆"),
            "pages": ("PAGES", "◈"),
            "reels_page": ("REELS", "◇"),
            "content": ("CONTENT", "◆"),
            "groups": ("GROUPS", "◢"),
            "scripts": ("SCRIPTS", "◇"),
            "posts": ("POSTS", "◈")
        }

        title, icon = tab_info.get(tab_id, (tab_id.upper(), "◢"))
        accent_color = TAB_COLORS.get(tab_id, COLORS["neon_cyan"])

        # Update header
        self.page_icon.configure(text=icon, text_color=accent_color)
        self.page_title.configure(text=title)

        # Show tab
        if tab_id in self.tabs:
            self.tabs[tab_id].pack(fill="both", expand=True)
            if tab_id == "posts" and hasattr(self.tabs[tab_id], '_load_data'):
                self.tabs[tab_id]._load_data()

        self.current_tab = tab_id

    def _setup_log_redirector(self):
        """Setup log capture"""
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        sys.stdout = LogRedirector(self._on_log_output, self._original_stdout)
        sys.stderr = LogRedirector(self._on_log_output, self._original_stderr)

    def _on_log_output(self, text):
        """Handle log output"""
        level = "info"
        text_upper = text.upper()
        if "ERROR" in text_upper:
            level = "error"
        elif "WARNING" in text_upper or "WARN" in text_upper:
            level = "warning"
        elif "SUCCESS" in text_upper or "[OK]" in text:
            level = "success"
        self.after(0, lambda: self._add_log(text.strip(), level))

    def _add_log(self, text: str, level: str = "info"):
        """Add log entry to terminal"""
        if hasattr(self, 'log_terminal') and self.log_terminal:
            self.log_terminal.add_line(text, level)

    def _clear_logs(self):
        """Clear log panel"""
        if hasattr(self, 'log_terminal') and self.log_terminal:
            self.log_terminal.clear()
            self._add_log("Log cleared", "info")

    def _update_status(self, text: str, status_type: str = "info"):
        """Update status bar"""
        if self.status_bar:
            self.status_bar.set_status(text, status_type)

    def _check_hidemium_connection(self):
        """Check Hidemium connection"""
        from api_service import api
        import threading

        def check():
            connected = api.check_connection()
            self.after(0, lambda: self._set_connection_status(connected))

        threading.Thread(target=check, daemon=True).start()

    def _set_connection_status(self, connected: bool):
        """Update connection indicator"""
        if connected:
            self.connection_indicator.configure(
                text="● ONLINE",
                text_color=COLORS["neon_green"]
            )
        else:
            self.connection_indicator.configure(
                text="● OFFLINE",
                text_color=COLORS["neon_red"]
            )

    def _open_settings(self):
        """Open settings dialog"""
        settings = SettingsDialog(self)
        settings.grab_set()


class SettingsDialog(ctk.CTkToplevel):
    """Settings Dialog - Cyberpunk style"""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("SETTINGS")
        self.geometry("500x400")
        self.configure(fg_color=COLORS["bg_main"])
        self.transient(parent)
        self._create_ui()

    def _create_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_header"], height=HEIGHTS["header"], corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(fill="x", padx=20, pady=16)

        ctk.CTkLabel(
            header_content,
            text="◆",
            font=ctk.CTkFont(size=20),
            text_color=COLORS["neon_cyan"]
        ).pack(side="left")

        ctk.CTkLabel(
            header_content,
            text="SETTINGS",
            font=ctk.CTkFont(family=FONTS["family_display"], size=FONTS["size_lg"], weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left", padx=(8, 0))

        # Content
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)

        # Hidemium section
        section = ctk.CTkFrame(content, fg_color=COLORS["bg_card"], corner_radius=RADIUS["lg"])
        section.pack(fill="x", pady=(0, 12))

        section_header = ctk.CTkFrame(section, fg_color="transparent")
        section_header.pack(fill="x", padx=16, pady=(12, 8))

        ctk.CTkLabel(
            section_header,
            text="◢",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["neon_cyan"]
        ).pack(side="left")

        ctk.CTkLabel(
            section_header,
            text="HIDEMIUM API",
            font=ctk.CTkFont(family=FONTS["family_display"], size=FONTS["size_sm"], weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left", padx=(8, 0))

        # API URL
        url_frame = ctk.CTkFrame(section, fg_color="transparent")
        url_frame.pack(fill="x", padx=16, pady=4)

        ctk.CTkLabel(
            url_frame,
            text="URL",
            width=60,
            anchor="w",
            font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_xs"]),
            text_color=COLORS["text_muted"]
        ).pack(side="left")

        self.api_url = ctk.CTkEntry(
            url_frame,
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_sm"]),
            height=36,
            corner_radius=RADIUS["md"]
        )
        self.api_url.pack(side="left", fill="x", expand=True)
        self.api_url.insert(0, "http://127.0.0.1:2222")

        # Token
        token_frame = ctk.CTkFrame(section, fg_color="transparent")
        token_frame.pack(fill="x", padx=16, pady=(4, 12))

        ctk.CTkLabel(
            token_frame,
            text="TOKEN",
            width=60,
            anchor="w",
            font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_xs"]),
            text_color=COLORS["text_muted"]
        ).pack(side="left")

        self.api_token = ctk.CTkEntry(
            token_frame,
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_sm"]),
            show="*",
            height=36,
            corner_radius=RADIUS["md"]
        )
        self.api_token.pack(side="left", fill="x", expand=True)

        # Buttons
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x", pady=20)

        ctk.CTkButton(
            btn_frame,
            text="SAVE",
            width=100,
            height=40,
            corner_radius=RADIUS["md"],
            fg_color=COLORS["neon_green"],
            hover_color=COLORS["success_hover"],
            font=ctk.CTkFont(family=FONTS["family_display"], size=FONTS["size_sm"], weight="bold"),
            text_color=COLORS["bg_dark"],
            command=self._save_settings
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_frame,
            text="CANCEL",
            width=80,
            height=40,
            corner_radius=RADIUS["md"],
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["border"],
            hover_color=COLORS["bg_hover"],
            font=ctk.CTkFont(family=FONTS["family_display"], size=FONTS["size_sm"], weight="bold"),
            text_color=COLORS["text_secondary"],
            command=self.destroy
        ).pack(side="left")

    def _save_settings(self):
        """Save settings"""
        from db import save_settings
        settings = {
            'api_url': self.api_url.get(),
            'api_token': self.api_token.get()
        }
        save_settings(settings)
        self.destroy()


def main():
    """Main entry point"""
    app = FBManagerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
