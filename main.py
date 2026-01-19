"""
SonCuto FB - Professional Facebook Manager
Modern UI inspired by GoLogin/Multilogin
"""
import customtkinter as ctk
import sys
import io
from datetime import datetime
from config import COLORS, WINDOW_WIDTH, WINDOW_HEIGHT, APP_NAME, APP_VERSION
from widgets import StatusBar
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
    """SonCuto FB - Main Application"""

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
        self._add_log("[App] SonCuto FB started", "SUCCESS")

    def _create_sidebar(self):
        """Modern icon-based sidebar"""
        self.sidebar = ctk.CTkFrame(
            self,
            width=68,
            corner_radius=0,
            fg_color=COLORS["bg_sidebar"]
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo at top
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=60)
        logo_frame.pack(fill="x")
        logo_frame.pack_propagate(False)

        # Brand icon - Gradient effect with 2 colors
        logo_btn = ctk.CTkButton(
            logo_frame,
            text="S",
            width=40,
            height=40,
            corner_radius=10,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS["bg_main"]
        )
        logo_btn.place(relx=0.5, rely=0.5, anchor="center")

        # Navigation items - Icon only
        nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_frame.pack(fill="both", expand=True, pady=10)

        self.nav_buttons = {}
        nav_items = [
            ("profiles", "👤", "Profiles"),
            ("login", "🔐", "Login"),
            ("pages", "📄", "Pages"),
            ("reels_page", "🎬", "Reels"),
            ("content", "✏️", "Content"),
            ("groups", "👥", "Groups"),
            ("scripts", "📜", "Scripts"),
            ("posts", "📊", "Posts"),
        ]

        for tab_id, icon, tooltip in nav_items:
            btn = self._create_nav_icon(nav_frame, tab_id, icon, tooltip)
            btn.pack(pady=2)
            self.nav_buttons[tab_id] = btn

        # Bottom section - Settings & Status
        bottom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=100)
        bottom_frame.pack(side="bottom", fill="x", pady=10)
        bottom_frame.pack_propagate(False)

        # Settings icon
        settings_btn = ctk.CTkButton(
            bottom_frame,
            text="⚙️",
            width=44,
            height=44,
            corner_radius=8,
            fg_color="transparent",
            hover_color=COLORS["bg_card"],
            font=ctk.CTkFont(size=18),
            command=self._open_settings
        )
        settings_btn.pack(pady=4)

        # Connection indicator
        self.connection_indicator = ctk.CTkLabel(
            bottom_frame,
            text="●",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["warning"]
        )
        self.connection_indicator.pack(pady=4)

        self.after(1000, self._check_hidemium_connection)

    def _create_nav_icon(self, parent, tab_id: str, icon: str, tooltip: str):
        """Create icon-only nav button with tooltip"""
        btn = ctk.CTkButton(
            parent,
            text=icon,
            width=44,
            height=44,
            corner_radius=8,
            fg_color="transparent",
            hover_color=COLORS["bg_card"],
            font=ctk.CTkFont(size=18),
            command=lambda: self._show_tab(tab_id)
        )
        # TODO: Add tooltip on hover
        return btn

    def _create_content_area(self):
        """Main content area with header"""
        self.content_area = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_main"],
            corner_radius=0
        )
        self.content_area.pack(side="left", fill="both", expand=True)

        # Header bar
        self.header = ctk.CTkFrame(
            self.content_area,
            height=56,
            fg_color=COLORS["bg_header"],
            corner_radius=0
        )
        self.header.pack(fill="x")
        self.header.pack_propagate(False)

        # Header left - Page title
        self.page_title = ctk.CTkLabel(
            self.header,
            text="👤  Profiles",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        self.page_title.pack(side="left", padx=20)

        # Header right - Brand
        brand_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        brand_frame.pack(side="right", padx=20)

        ctk.CTkLabel(
            brand_frame,
            text="SonCuto",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["primary"]
        ).pack(side="left")
        ctk.CTkLabel(
            brand_frame,
            text="FB",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["secondary"]
        ).pack(side="left", padx=(2, 0))

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
        """Log panel on right side"""
        self.log_panel = ctk.CTkFrame(
            self,
            width=360,
            fg_color=COLORS["bg_sidebar"],
            corner_radius=0
        )
        self.log_panel.pack(side="right", fill="y")
        self.log_panel.pack_propagate(False)

        # Header
        header = ctk.CTkFrame(self.log_panel, fg_color=COLORS["bg_header"], height=56, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="📋 Logs",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left", padx=16, pady=16)

        ctk.CTkButton(
            header,
            text="Clear",
            width=50,
            height=28,
            corner_radius=6,
            fg_color=COLORS["secondary"],
            hover_color=COLORS["secondary_hover"],
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_primary"],
            command=self._clear_logs
        ).pack(side="right", padx=16)

        # Log content
        log_container = ctk.CTkFrame(self.log_panel, fg_color="transparent")
        log_container.pack(fill="both", expand=True, padx=8, pady=8)

        self.log_text = ctk.CTkTextbox(
            log_container,
            fg_color=COLORS["bg_main"],
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont(family="Consolas", size=11),
            corner_radius=8,
            wrap="word"
        )
        self.log_text.pack(fill="both", expand=True)

        # Log tags
        self.log_text._textbox.tag_config("INFO", foreground=COLORS["info"])
        self.log_text._textbox.tag_config("ERROR", foreground=COLORS["error"])
        self.log_text._textbox.tag_config("WARNING", foreground=COLORS["warning"])
        self.log_text._textbox.tag_config("SUCCESS", foreground=COLORS["success"])
        self.log_text._textbox.tag_config("DEBUG", foreground=COLORS["text_muted"])
        self.log_text._textbox.tag_config("TIMESTAMP", foreground=COLORS["text_muted"])

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
        """Switch to selected tab"""
        # Hide all
        for tab in self.tabs.values():
            tab.pack_forget()

        # Update nav buttons
        titles = {
            "profiles": "👤  Profiles",
            "login": "🔐  Login FB",
            "pages": "📄  Pages",
            "reels_page": "🎬  Reels",
            "content": "✏️  Content",
            "groups": "👥  Groups",
            "scripts": "📜  Scripts",
            "posts": "📊  Posts"
        }

        for btn_id, btn in self.nav_buttons.items():
            if btn_id == tab_id:
                btn.configure(
                    fg_color=COLORS["primary"],
                    text_color=COLORS["bg_main"],
                    hover_color=COLORS["primary_hover"]
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=COLORS["text_primary"],
                    hover_color=COLORS["bg_card"]
                )

        # Update header title
        self.page_title.configure(text=titles.get(tab_id, tab_id))

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
        level = "INFO"
        if "ERROR" in text.upper():
            level = "ERROR"
        elif "WARNING" in text.upper() or "WARN" in text.upper():
            level = "WARNING"
        elif "SUCCESS" in text.upper() or "✓" in text or "[OK]" in text:
            level = "SUCCESS"
        elif "DEBUG" in text.upper():
            level = "DEBUG"
        self.after(0, lambda: self._add_log(text.strip(), level))

    def _add_log(self, text: str, level: str = "INFO"):
        """Add log entry"""
        if not hasattr(self, 'log_text') or not self.log_text:
            return
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text._textbox.insert("end", f"[{timestamp}] ", "TIMESTAMP")
        self.log_text._textbox.insert("end", f"{text}\n", level)
        self.log_text._textbox.see("end")

    def _clear_logs(self):
        """Clear log panel"""
        if hasattr(self, 'log_text') and self.log_text:
            self.log_text._textbox.delete("1.0", "end")
            self._add_log("[App] Logs cleared", "INFO")

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
            self.connection_indicator.configure(text_color=COLORS["online"])
        else:
            self.connection_indicator.configure(text_color=COLORS["error"])

    def _open_settings(self):
        """Open settings dialog"""
        settings = SettingsDialog(self)
        settings.grab_set()


class SettingsDialog(ctk.CTkToplevel):
    """Settings Dialog - Modern style"""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("⚙️ Settings")
        self.geometry("500x400")
        self.configure(fg_color=COLORS["bg_main"])
        self.transient(parent)
        self._create_ui()

    def _create_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_header"], height=56, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="⚙️  Settings",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left", padx=20, pady=16)

        # Content
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)

        # Hidemium section
        section = ctk.CTkFrame(content, fg_color=COLORS["bg_card"], corner_radius=8)
        section.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            section,
            text="🌐 Hidemium API",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=16, pady=(12, 8))

        # API URL
        url_frame = ctk.CTkFrame(section, fg_color="transparent")
        url_frame.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(url_frame, text="URL:", width=60, anchor="w", text_color=COLORS["text_secondary"]).pack(side="left")
        self.api_url = ctk.CTkEntry(url_frame, fg_color=COLORS["bg_input"], border_color=COLORS["border"], height=32)
        self.api_url.pack(side="left", fill="x", expand=True)
        self.api_url.insert(0, "http://127.0.0.1:2222")

        # Token
        token_frame = ctk.CTkFrame(section, fg_color="transparent")
        token_frame.pack(fill="x", padx=16, pady=(4, 12))
        ctk.CTkLabel(token_frame, text="Token:", width=60, anchor="w", text_color=COLORS["text_secondary"]).pack(side="left")
        self.api_token = ctk.CTkEntry(token_frame, fg_color=COLORS["bg_input"], border_color=COLORS["border"], show="*", height=32)
        self.api_token.pack(side="left", fill="x", expand=True)

        # Buttons
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x", pady=20)

        ctk.CTkButton(
            btn_frame,
            text="Save",
            width=100,
            height=36,
            corner_radius=6,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            font=ctk.CTkFont(weight="bold"),
            text_color=COLORS["bg_main"],
            command=self._save_settings
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            width=80,
            height=36,
            corner_radius=6,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["bg_card_hover"],
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
