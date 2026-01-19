"""
FB Manager Pro - Clean UI
"""
import customtkinter as ctk
from config import (
    COLORS, FONTS, SPACING, RADIUS, HEIGHTS,
    WINDOW_WIDTH, WINDOW_HEIGHT, MIN_WIDTH, MIN_HEIGHT,
    APP_NAME, APP_VERSION, SIDEBAR_WIDTH
)
from widgets import StatusBar, ModernButton, ModernEntry
from tabs import ProfilesTab, ScriptsTab, PostsTab, ContentTab, GroupsTab


class FBManagerApp(ctk.CTk):
    """Main Application"""

    def __init__(self):
        super().__init__()

        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(MIN_WIDTH, MIN_HEIGHT)

        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() - WINDOW_WIDTH) // 2
        y = (self.winfo_screenheight() - WINDOW_HEIGHT) // 2
        self.geometry(f"+{x}+{y}")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.configure(fg_color=COLORS["bg_dark"])

        self.status_bar = None

        self._create_sidebar()
        self._create_main_frame()
        self._create_status_bar()
        self._create_tabs()

        self._show_tab("profiles")

    def _create_sidebar(self):
        """Create clean sidebar"""
        self.sidebar = ctk.CTkFrame(
            self,
            width=SIDEBAR_WIDTH,
            corner_radius=0,
            fg_color=COLORS["bg_secondary"],
            border_width=0
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo Section
        logo_section = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_section.pack(fill="x", padx=SPACING["lg"], pady=SPACING["xl"])

        # Logo box
        logo_box = ctk.CTkFrame(
            logo_section,
            fg_color=COLORS["accent"],
            corner_radius=RADIUS["lg"],
            width=44,
            height=44
        )
        logo_box.pack(side="left")
        logo_box.pack_propagate(False)

        ctk.CTkLabel(
            logo_box,
            text="FB",
            font=ctk.CTkFont(size=FONTS["size_lg"], weight="bold"),
            text_color="#ffffff"
        ).place(relx=0.5, rely=0.5, anchor="center")

        # Title
        title_frame = ctk.CTkFrame(logo_section, fg_color="transparent")
        title_frame.pack(side="left", padx=SPACING["md"])

        ctk.CTkLabel(
            title_frame,
            text="FB Manager",
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_lg"], weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_frame,
            text="Pro Edition",
            font=ctk.CTkFont(size=FONTS["size_xs"]),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w")

        # Divider
        ctk.CTkFrame(
            self.sidebar,
            fg_color=COLORS["border"],
            height=1
        ).pack(fill="x", padx=SPACING["lg"], pady=SPACING["sm"])

        # Navigation Section
        nav_section = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_section.pack(fill="x", padx=SPACING["sm"], pady=SPACING["sm"])

        ctk.CTkLabel(
            nav_section,
            text="MENU",
            font=ctk.CTkFont(size=FONTS["size_xs"], weight="bold"),
            text_color=COLORS["text_tertiary"]
        ).pack(anchor="w", padx=SPACING["sm"], pady=(0, SPACING["sm"]))

        # Navigation items - clean text only
        self.nav_buttons = {}
        nav_items = [
            ("profiles", "Profiles"),
            ("content", "Soan tin"),
            ("groups", "Dang nhom"),
            ("scripts", "Kich ban"),
            ("posts", "Bai dang"),
        ]

        for tab_id, text in nav_items:
            btn = self._create_nav_button(nav_section, tab_id, text)
            btn.pack(fill="x", pady=1)
            self.nav_buttons[tab_id] = btn

        # Bottom Section
        bottom_section = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_section.pack(side="bottom", fill="x", padx=SPACING["md"], pady=SPACING["lg"])

        # Divider
        ctk.CTkFrame(
            bottom_section,
            fg_color=COLORS["border"],
            height=1
        ).pack(fill="x", pady=SPACING["md"])

        # Settings button
        ctk.CTkButton(
            bottom_section,
            text="Cai dat",
            fg_color="transparent",
            hover_color=COLORS["bg_card"],
            anchor="w",
            height=HEIGHTS["sidebar_item"],
            corner_radius=RADIUS["md"],
            font=ctk.CTkFont(size=FONTS["size_base"]),
            text_color=COLORS["text_secondary"],
            command=self._open_settings
        ).pack(fill="x", pady=2)

        # Connection status
        self.connection_card = ctk.CTkFrame(
            bottom_section,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=COLORS["border"]
        )
        self.connection_card.pack(fill="x", pady=SPACING["sm"])

        conn_inner = ctk.CTkFrame(self.connection_card, fg_color="transparent")
        conn_inner.pack(fill="x", padx=SPACING["md"], pady=SPACING["md"])

        ctk.CTkLabel(
            conn_inner,
            text="Hidemium",
            font=ctk.CTkFont(size=FONTS["size_sm"], weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")

        self.connection_status = ctk.CTkLabel(
            conn_inner,
            text="Dang ket noi...",
            font=ctk.CTkFont(size=FONTS["size_xs"]),
            text_color=COLORS["warning"]
        )
        self.connection_status.pack(anchor="w")

        self.after(1000, self._check_hidemium_connection)

    def _create_nav_button(self, parent, tab_id: str, text: str):
        """Create navigation button"""
        btn = ctk.CTkButton(
            parent,
            text=text,
            fg_color="transparent",
            hover_color=COLORS["bg_card"],
            anchor="w",
            height=HEIGHTS["sidebar_item"],
            corner_radius=RADIUS["md"],
            font=ctk.CTkFont(size=FONTS["size_base"]),
            text_color=COLORS["text_primary"],
            command=lambda: self._show_tab(tab_id)
        )
        btn._tab_id = tab_id
        return btn

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

        self.tabs["profiles"] = ProfilesTab(
            self.main_frame,
            status_callback=self._update_status
        )

        self.tabs["content"] = ContentTab(
            self.main_frame,
            status_callback=self._update_status
        )

        self.tabs["groups"] = GroupsTab(
            self.main_frame,
            status_callback=self._update_status
        )

        self.tabs["scripts"] = ScriptsTab(
            self.main_frame,
            status_callback=self._update_status
        )

        self.tabs["posts"] = PostsTab(
            self.main_frame,
            status_callback=self._update_status
        )

    def _create_status_bar(self):
        """Create status bar"""
        self.status_bar = StatusBar(self.main_frame)
        self.status_bar.pack(side="bottom", fill="x")

    def _show_tab(self, tab_id: str):
        """Show selected tab"""
        for tab in self.tabs.values():
            tab.pack_forget()

        for btn_id, btn in self.nav_buttons.items():
            if btn_id == tab_id:
                btn.configure(
                    fg_color=COLORS["accent"],
                    text_color="#ffffff"
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=COLORS["text_primary"]
                )

        if tab_id in self.tabs:
            self.tabs[tab_id].pack(fill="both", expand=True, before=self.status_bar)

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
        """Update connection status"""
        if connected:
            self.connection_status.configure(
                text="Da ket noi",
                text_color=COLORS["success"]
            )
            self.connection_card.configure(border_color=COLORS["success"])
        else:
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
    """Settings Dialog"""

    def __init__(self, parent):
        super().__init__(parent)

        self.title("Cai dat")
        self.geometry("600x500")
        self.configure(fg_color=COLORS["bg_dark"])
        self.transient(parent)

        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 600) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 500) // 2
        self.geometry(f"+{x}+{y}")

        self._create_ui()

    def _create_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=SPACING["2xl"], pady=SPACING["2xl"])

        ctk.CTkLabel(
            header,
            text="Cai dat ung dung",
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_2xl"], weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Cau hinh ket noi va giao dien",
            font=ctk.CTkFont(size=FONTS["size_base"]),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", pady=(SPACING["xs"], 0))

        # Content
        content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=SPACING["2xl"])

        # Hidemium Settings Card
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

        ctk.CTkLabel(
            hidemium_inner,
            text="Cau hinh Hidemium",
            font=ctk.CTkFont(size=FONTS["size_lg"], weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", pady=(0, SPACING["md"]))

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

        # UI Settings Card
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

        ctk.CTkLabel(
            ui_inner,
            text="Giao dien",
            font=ctk.CTkFont(size=FONTS["size_lg"], weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", pady=(0, SPACING["md"]))

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

        # About Card
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
            text="Facebook Account Manager",
            font=ctk.CTkFont(size=FONTS["size_base"]),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w")

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=SPACING["2xl"], pady=SPACING["xl"])

        ModernButton(
            btn_frame,
            text="Luu cai dat",
            variant="success",
            command=self._save_settings,
            width=120
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
