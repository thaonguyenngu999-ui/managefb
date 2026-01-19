"""
FB Manager Pro - Modern Facebook Account Manager
Premium Dark UI with Glassmorphism Design
"""
import customtkinter as ctk
from config import (
    COLORS, FONTS, SPACING, RADIUS, HEIGHTS,
    WINDOW_WIDTH, WINDOW_HEIGHT, MIN_WIDTH, MIN_HEIGHT,
    APP_NAME, APP_VERSION, SIDEBAR_WIDTH
)
from widgets import StatusBar, ModernButton, ModernEntry, Badge
from tabs import ProfilesTab, ScriptsTab, PostsTab, ContentTab, GroupsTab


class FBManagerApp(ctk.CTk):
    """Main Application - Premium Facebook Manager"""

    def __init__(self):
        super().__init__()

        # Window setup
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(MIN_WIDTH, MIN_HEIGHT)

        # Center window on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() - WINDOW_WIDTH) // 2
        y = (self.winfo_screenheight() - WINDOW_HEIGHT) // 2
        self.geometry(f"+{x}+{y}")

        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Configure colors
        self.configure(fg_color=COLORS["bg_dark"])

        # Initialize status_bar as None first
        self.status_bar = None

        # Create UI
        self._create_sidebar()
        self._create_main_frame()
        self._create_status_bar()
        self._create_tabs()

        # Show default tab
        self._show_tab("profiles")

    def _create_sidebar(self):
        """Create premium sidebar navigation"""
        self.sidebar = ctk.CTkFrame(
            self,
            width=SIDEBAR_WIDTH,
            corner_radius=0,
            fg_color=COLORS["bg_secondary"],
            border_width=0
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # ========== LOGO SECTION ==========
        logo_section = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_section.pack(fill="x", padx=SPACING["xl"], pady=SPACING["2xl"])

        # Logo container with gradient effect
        logo_container = ctk.CTkFrame(
            logo_section,
            fg_color=COLORS["accent"],
            corner_radius=RADIUS["lg"],
            width=52,
            height=52
        )
        logo_container.pack(side="left")
        logo_container.pack_propagate(False)

        # Logo icon
        ctk.CTkLabel(
            logo_container,
            text="",
            font=ctk.CTkFont(size=24),
            text_color=COLORS["text_primary"]
        ).place(relx=0.5, rely=0.5, anchor="center")

        # Title section
        title_section = ctk.CTkFrame(logo_section, fg_color="transparent")
        title_section.pack(side="left", padx=SPACING["md"])

        ctk.CTkLabel(
            title_section,
            text="FB Manager",
            font=ctk.CTkFont(
                family=FONTS["family"],
                size=FONTS["size_xl"],
                weight="bold"
            ),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_section,
            text="Pro Edition",
            font=ctk.CTkFont(size=FONTS["size_sm"]),
            text_color=COLORS["accent_light"]
        ).pack(anchor="w")

        # ========== NAVIGATION SECTION ==========
        nav_section = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_section.pack(fill="x", padx=SPACING["md"], pady=SPACING["md"])

        # Section label
        ctk.CTkLabel(
            nav_section,
            text="MENU CHINH",
            font=ctk.CTkFont(size=FONTS["size_xs"], weight="bold"),
            text_color=COLORS["text_tertiary"]
        ).pack(anchor="w", padx=SPACING["sm"], pady=(0, SPACING["sm"]))

        # Navigation items
        self.nav_buttons = {}
        nav_items = [
            ("profiles", "", "Quan ly Profiles", "Quan ly tai khoan"),
            ("content", "", "Soan tin", "Tao noi dung"),
            ("groups", "", "Dang Nhom", "Dang vao nhom"),
            ("scripts", "", "Kich ban", "Automation"),
            ("posts", "", "Bai dang", "Theo doi bai"),
        ]

        for tab_id, icon, text, subtitle in nav_items:
            btn = self._create_nav_item(tab_id, icon, text, subtitle)
            btn.pack(fill="x", pady=2)
            self.nav_buttons[tab_id] = btn

        # ========== BOTTOM SECTION ==========
        bottom_section = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_section.pack(side="bottom", fill="x", padx=SPACING["md"], pady=SPACING["xl"])

        # Divider
        ctk.CTkFrame(
            bottom_section,
            fg_color=COLORS["border"],
            height=1
        ).pack(fill="x", pady=SPACING["md"])

        # Settings button
        settings_btn = ctk.CTkButton(
            bottom_section,
            text="  Cai dat",
            fg_color="transparent",
            hover_color=COLORS["bg_card"],
            anchor="w",
            height=HEIGHTS["sidebar_item"],
            corner_radius=RADIUS["md"],
            font=ctk.CTkFont(size=FONTS["size_base"]),
            text_color=COLORS["text_secondary"],
            command=self._open_settings
        )
        settings_btn.pack(fill="x", pady=2)

        # Connection status card
        self.connection_card = ctk.CTkFrame(
            bottom_section,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=COLORS["border"]
        )
        self.connection_card.pack(fill="x", pady=SPACING["md"])

        connection_inner = ctk.CTkFrame(self.connection_card, fg_color="transparent")
        connection_inner.pack(fill="x", padx=SPACING["md"], pady=SPACING["md"])

        # Connection icon
        self.connection_icon = ctk.CTkLabel(
            connection_inner,
            text="",
            font=ctk.CTkFont(size=FONTS["size_lg"]),
            text_color=COLORS["warning"]
        )
        self.connection_icon.pack(side="left")

        # Connection text
        conn_text_frame = ctk.CTkFrame(connection_inner, fg_color="transparent")
        conn_text_frame.pack(side="left", padx=SPACING["sm"])

        ctk.CTkLabel(
            conn_text_frame,
            text="Hidemium",
            font=ctk.CTkFont(size=FONTS["size_sm"], weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")

        self.connection_status = ctk.CTkLabel(
            conn_text_frame,
            text="Dang ket noi...",
            font=ctk.CTkFont(size=FONTS["size_xs"]),
            text_color=COLORS["warning"]
        )
        self.connection_status.pack(anchor="w")

        # Check connection
        self.after(1000, self._check_hidemium_connection)

    def _create_nav_item(self, tab_id: str, icon: str, text: str, subtitle: str):
        """Create navigation item with icon and text"""
        btn_frame = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent",
            corner_radius=RADIUS["md"],
            height=HEIGHTS["sidebar_item"]
        )
        btn_frame.pack_propagate(False)

        # Main button
        btn = ctk.CTkButton(
            btn_frame,
            text="",
            fg_color="transparent",
            hover_color=COLORS["bg_card"],
            corner_radius=RADIUS["md"],
            height=HEIGHTS["sidebar_item"],
            command=lambda: self._show_tab(tab_id)
        )
        btn.pack(fill="both", expand=True)

        # Content overlay
        content = ctk.CTkFrame(btn_frame, fg_color="transparent")
        content.place(relx=0, rely=0.5, anchor="w", x=SPACING["md"])
        content.bind("<Button-1>", lambda e: self._show_tab(tab_id))

        # Icon
        icon_label = ctk.CTkLabel(
            content,
            text=icon,
            font=ctk.CTkFont(size=FONTS["size_lg"]),
            text_color=COLORS["text_secondary"]
        )
        icon_label.pack(side="left")
        icon_label.bind("<Button-1>", lambda e: self._show_tab(tab_id))

        # Text
        text_frame = ctk.CTkFrame(content, fg_color="transparent")
        text_frame.pack(side="left", padx=SPACING["md"])
        text_frame.bind("<Button-1>", lambda e: self._show_tab(tab_id))

        title_label = ctk.CTkLabel(
            text_frame,
            text=text,
            font=ctk.CTkFont(size=FONTS["size_base"], weight="bold"),
            text_color=COLORS["text_primary"]
        )
        title_label.pack(anchor="w")
        title_label.bind("<Button-1>", lambda e: self._show_tab(tab_id))

        # Store references for styling
        btn_frame._icon = icon_label
        btn_frame._title = title_label
        btn_frame._tab_id = tab_id
        btn_frame._btn = btn

        return btn_frame

    def _create_main_frame(self):
        """Create main content area"""
        self.main_frame = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_dark"],
            corner_radius=0
        )
        self.main_frame.pack(side="left", fill="both", expand=True)

    def _create_tabs(self):
        """Create tab views"""
        self.tabs = {}

        # Profiles tab
        self.tabs["profiles"] = ProfilesTab(
            self.main_frame,
            status_callback=self._update_status
        )

        # Content tab
        self.tabs["content"] = ContentTab(
            self.main_frame,
            status_callback=self._update_status
        )

        # Groups tab
        self.tabs["groups"] = GroupsTab(
            self.main_frame,
            status_callback=self._update_status
        )

        # Scripts tab
        self.tabs["scripts"] = ScriptsTab(
            self.main_frame,
            status_callback=self._update_status
        )

        # Posts tab
        self.tabs["posts"] = PostsTab(
            self.main_frame,
            status_callback=self._update_status
        )

    def _create_status_bar(self):
        """Create bottom status bar"""
        self.status_bar = StatusBar(self.main_frame)
        self.status_bar.pack(side="bottom", fill="x")

    def _show_tab(self, tab_id: str):
        """Show selected tab and update navigation styling"""
        # Hide all tabs
        for tab in self.tabs.values():
            tab.pack_forget()

        # Update nav button styles
        for btn_id, btn_frame in self.nav_buttons.items():
            if btn_id == tab_id:
                # Active state
                btn_frame._btn.configure(fg_color=COLORS["bg_card"])
                btn_frame._icon.configure(text_color=COLORS["accent"])
                btn_frame._title.configure(text_color=COLORS["accent"])
            else:
                # Inactive state
                btn_frame._btn.configure(fg_color="transparent")
                btn_frame._icon.configure(text_color=COLORS["text_secondary"])
                btn_frame._title.configure(text_color=COLORS["text_primary"])

        # Show selected tab
        if tab_id in self.tabs:
            self.tabs[tab_id].pack(fill="both", expand=True, before=self.status_bar)

    def _update_status(self, text: str, status_type: str = "info"):
        """Update status bar"""
        if self.status_bar:
            self.status_bar.set_status(text, status_type)

    def _check_hidemium_connection(self):
        """Check Hidemium connection status"""
        from api_service import api
        import threading

        def check():
            connected = api.check_connection()
            self.after(0, lambda: self._set_connection_status(connected))

        threading.Thread(target=check, daemon=True).start()

    def _set_connection_status(self, connected: bool):
        """Update connection status display"""
        if connected:
            self.connection_icon.configure(text_color=COLORS["success"])
            self.connection_status.configure(
                text="Da ket noi",
                text_color=COLORS["success"]
            )
            self.connection_card.configure(border_color=COLORS["success"])
        else:
            self.connection_icon.configure(text_color=COLORS["error"])
            self.connection_status.configure(
                text="Chua ket noi",
                text_color=COLORS["error"]
            )
            self.connection_card.configure(border_color=COLORS["error"])

    def _open_settings(self):
        """Open settings dialog"""
        settings = SettingsDialog(self)
        settings.grab_set()


class SettingsDialog(ctk.CTkToplevel):
    """Premium Settings Dialog"""

    def __init__(self, parent):
        super().__init__(parent)

        self.title("Cai dat")
        self.geometry("650x550")
        self.configure(fg_color=COLORS["bg_dark"])
        self.transient(parent)

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 650) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 550) // 2
        self.geometry(f"+{x}+{y}")

        self._create_ui()

    def _create_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=SPACING["2xl"], pady=SPACING["2xl"])

        ctk.CTkLabel(
            header,
            text="  Cai dat ung dung",
            font=ctk.CTkFont(
                family=FONTS["family"],
                size=FONTS["size_2xl"],
                weight="bold"
            ),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Cau hinh ket noi va giao dien",
            font=ctk.CTkFont(size=FONTS["size_base"]),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", pady=(SPACING["xs"], 0))

        # Content scroll
        content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=SPACING["2xl"])

        # ========== HIDEMIUM SETTINGS ==========
        hidemium_card = ctk.CTkFrame(
            content,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=COLORS["border"]
        )
        hidemium_card.pack(fill="x", pady=SPACING["sm"])

        hidemium_inner = ctk.CTkFrame(hidemium_card, fg_color="transparent")
        hidemium_inner.pack(fill="x", padx=SPACING["lg"], pady=SPACING["lg"])

        # Section header
        section_header = ctk.CTkFrame(hidemium_inner, fg_color="transparent")
        section_header.pack(fill="x", pady=(0, SPACING["md"]))

        ctk.CTkLabel(
            section_header,
            text="",
            font=ctk.CTkFont(size=FONTS["size_xl"]),
            text_color=COLORS["accent"]
        ).pack(side="left")

        ctk.CTkLabel(
            section_header,
            text="Cau hinh Hidemium",
            font=ctk.CTkFont(size=FONTS["size_lg"], weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left", padx=SPACING["sm"])

        # API URL
        url_row = ctk.CTkFrame(hidemium_inner, fg_color="transparent")
        url_row.pack(fill="x", pady=SPACING["xs"])

        ctk.CTkLabel(
            url_row,
            text="API URL",
            width=100,
            anchor="w",
            font=ctk.CTkFont(size=FONTS["size_base"]),
            text_color=COLORS["text_secondary"]
        ).pack(side="left")

        self.api_url = ModernEntry(url_row)
        self.api_url.pack(side="left", fill="x", expand=True)
        self.api_url.insert(0, "http://127.0.0.1:2222")

        # Token
        token_row = ctk.CTkFrame(hidemium_inner, fg_color="transparent")
        token_row.pack(fill="x", pady=SPACING["xs"])

        ctk.CTkLabel(
            token_row,
            text="API Token",
            width=100,
            anchor="w",
            font=ctk.CTkFont(size=FONTS["size_base"]),
            text_color=COLORS["text_secondary"]
        ).pack(side="left")

        self.api_token = ModernEntry(token_row)
        self.api_token.pack(side="left", fill="x", expand=True)
        self.api_token.configure(show="*")
        self.api_token.insert(0, "your_token_here")

        # ========== UI SETTINGS ==========
        ui_card = ctk.CTkFrame(
            content,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=COLORS["border"]
        )
        ui_card.pack(fill="x", pady=SPACING["sm"])

        ui_inner = ctk.CTkFrame(ui_card, fg_color="transparent")
        ui_inner.pack(fill="x", padx=SPACING["lg"], pady=SPACING["lg"])

        # Section header
        ui_header = ctk.CTkFrame(ui_inner, fg_color="transparent")
        ui_header.pack(fill="x", pady=(0, SPACING["md"]))

        ctk.CTkLabel(
            ui_header,
            text="",
            font=ctk.CTkFont(size=FONTS["size_xl"]),
            text_color=COLORS["secondary"]
        ).pack(side="left")

        ctk.CTkLabel(
            ui_header,
            text="Giao dien",
            font=ctk.CTkFont(size=FONTS["size_lg"], weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left", padx=SPACING["sm"])

        # Theme
        theme_row = ctk.CTkFrame(ui_inner, fg_color="transparent")
        theme_row.pack(fill="x", pady=SPACING["xs"])

        ctk.CTkLabel(
            theme_row,
            text="Theme",
            width=100,
            anchor="w",
            font=ctk.CTkFont(size=FONTS["size_base"]),
            text_color=COLORS["text_secondary"]
        ).pack(side="left")

        self.theme_menu = ctk.CTkOptionMenu(
            theme_row,
            values=["Dark", "Light", "System"],
            fg_color=COLORS["bg_secondary"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            dropdown_fg_color=COLORS["bg_card"],
            width=200
        )
        self.theme_menu.pack(side="left")

        # ========== ABOUT ==========
        about_card = ctk.CTkFrame(
            content,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=COLORS["border"]
        )
        about_card.pack(fill="x", pady=SPACING["sm"])

        about_inner = ctk.CTkFrame(about_card, fg_color="transparent")
        about_inner.pack(fill="x", padx=SPACING["lg"], pady=SPACING["lg"])

        ctk.CTkLabel(
            about_inner,
            text=f"FB Manager Pro v{APP_VERSION}",
            font=ctk.CTkFont(size=FONTS["size_lg"], weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")

        ctk.CTkLabel(
            about_inner,
            text="Premium Facebook Account Manager",
            font=ctk.CTkFont(size=FONTS["size_base"]),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w")

        # ========== BUTTONS ==========
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=SPACING["2xl"], pady=SPACING["xl"])

        ModernButton(
            btn_frame,
            text="Luu cai dat",
            icon="",
            variant="success",
            command=self._save_settings,
            width=140
        ).pack(side="left", padx=SPACING["xs"])

        ModernButton(
            btn_frame,
            text="Dong",
            variant="secondary",
            command=self.destroy,
            width=100
        ).pack(side="left", padx=SPACING["xs"])

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
