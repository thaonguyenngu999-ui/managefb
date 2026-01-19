"""
SonCuto CYBER v3.0 - Phần mềm quản lý tài khoản Facebook
Tích hợp Hidemium Browser API
"""
import customtkinter as ctk
from config import COLORS, WINDOW_WIDTH, WINDOW_HEIGHT, APP_NAME, APP_VERSION, APP_SUBTITLE, FONT_FAMILY
from widgets import CyberStatusBar, NavButton, QuickStatsCard, CyberButton
from tabs import ProfilesTab, ScriptsTab, PostsTab, ContentTab, GroupsTab


class FBManagerApp(ctk.CTk):
    """Ứng dụng chính SonCuto - Cyberpunk Theme"""

    def __init__(self):
        super().__init__()

        # Window setup
        self.title(f"{APP_NAME} {APP_SUBTITLE}")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(1200, 700)

        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Configure colors
        self.configure(fg_color=COLORS["bg_dark"])

        # Initialize status_bar as None first
        self.status_bar = None
        self.quick_stats = None

        # Create UI
        self._create_sidebar()
        self._create_main_frame()
        self._create_status_bar()
        self._create_tabs()

        # Show default tab
        self._show_tab("profiles")

    def _create_sidebar(self):
        """Tạo sidebar navigation với style cyberpunk"""
        self.sidebar = ctk.CTkFrame(
            self,
            width=220,
            corner_radius=0,
            fg_color=COLORS["bg_secondary"]
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # ========== LOGO SECTION ==========
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=15, pady=(20, 5))

        # Logo icon (diamond shape representing SonCuto)
        logo_icon_frame = ctk.CTkFrame(
            logo_frame,
            fg_color=COLORS["bg_card"],
            corner_radius=10,
            width=45,
            height=45,
            border_width=1,
            border_color=COLORS["cyan"]
        )
        logo_icon_frame.pack(side="left")
        logo_icon_frame.pack_propagate(False)

        ctk.CTkLabel(
            logo_icon_frame,
            text="◆",
            font=ctk.CTkFont(size=22),
            text_color=COLORS["cyan"]
        ).place(relx=0.5, rely=0.5, anchor="center")

        # Logo text
        title_frame = ctk.CTkFrame(logo_frame, fg_color="transparent")
        title_frame.pack(side="left", padx=10)

        ctk.CTkLabel(
            title_frame,
            text="SONCUTO",
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")

        # Version badge
        badge_frame = ctk.CTkFrame(
            title_frame,
            fg_color="#0a3020",  # Dark green background
            corner_radius=4,
        )
        badge_frame.pack(anchor="w", pady=(2, 0))

        ctk.CTkLabel(
            badge_frame,
            text=APP_SUBTITLE,
            font=ctk.CTkFont(family=FONT_FAMILY, size=9, weight="bold"),
            text_color=COLORS["success"]
        ).pack(padx=6, pady=2)

        # ========== MAIN MENU SECTION ==========
        menu_label = ctk.CTkLabel(
            self.sidebar,
            text="◄ MAIN MENU",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10),
            text_color=COLORS["text_muted"]
        )
        menu_label.pack(anchor="w", padx=15, pady=(25, 10))

        # Navigation buttons
        self.nav_buttons = {}
        nav_items = [
            ("profiles", "◎", "PROFILES", "Quản lý tài khoản"),
            ("content", "✎", "SOẠN TIN", "Tạo nội dung"),
            ("groups", "◉", "DĂNG NHÓM", "Đăng vào nhóm"),
            ("scripts", "⚡", "KỊCH BẢN", "Automation"),
            ("posts", "◈", "BÀI ĐĂNG", "Theo dõi bài"),
        ]

        for tab_id, icon, text, subtitle in nav_items:
            btn_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
            btn_frame.pack(fill="x", padx=10, pady=2)

            btn = NavButton(
                btn_frame,
                text=text,
                icon=icon,
                command=lambda t=tab_id: self._show_tab(t)
            )
            btn.pack(fill="x")

            # Subtitle under the button
            sub_label = ctk.CTkLabel(
                btn_frame,
                text=subtitle,
                font=ctk.CTkFont(family=FONT_FAMILY, size=9),
                text_color=COLORS["text_muted"]
            )
            sub_label.pack(anchor="w", padx=50)

            self.nav_buttons[tab_id] = btn

        # ========== BOTTOM SECTION ==========
        bottom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", padx=15, pady=15)

        # Quick Stats
        self.quick_stats = QuickStatsCard(bottom_frame)
        self.quick_stats.pack(fill="x", pady=(0, 15))

        # Settings button
        settings_btn = ctk.CTkButton(
            bottom_frame,
            text="  ⚙  CÀI ĐẶT",
            fg_color="transparent",
            hover_color=COLORS["bg_hover"],
            text_color=COLORS["text_secondary"],
            anchor="w",
            height=40,
            corner_radius=8,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            command=self._open_settings
        )
        settings_btn.pack(fill="x")

        # Settings subtitle
        ctk.CTkLabel(
            bottom_frame,
            text="Cấu hình hệ thống",
            font=ctk.CTkFont(family=FONT_FAMILY, size=9),
            text_color=COLORS["text_muted"]
        ).pack(anchor="w", padx=35)

        # Check Hidemium connection
        self.after(1000, self._check_hidemium_connection)

    def _create_main_frame(self):
        """Tạo main content frame"""
        self.main_frame = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_dark"],
            corner_radius=0
        )
        self.main_frame.pack(side="left", fill="both", expand=True)

    def _create_tabs(self):
        """Tạo các tabs"""
        self.tabs = {}

        # Profiles tab
        self.tabs["profiles"] = ProfilesTab(
            self.main_frame,
            status_callback=self._update_status,
            stats_callback=self._update_quick_stats
        )

        # Content tab (Soạn tin)
        self.tabs["content"] = ContentTab(
            self.main_frame,
            status_callback=self._update_status
        )

        # Groups tab (Đăng Nhóm)
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
        """Tạo status bar"""
        self.status_bar = CyberStatusBar(self.main_frame)
        self.status_bar.pack(side="bottom", fill="x")

    def _show_tab(self, tab_id: str):
        """Hiển thị tab được chọn"""
        # Hide all tabs
        for tab in self.tabs.values():
            tab.pack_forget()

        # Update nav buttons
        for btn_id, btn in self.nav_buttons.items():
            btn.set_active(btn_id == tab_id)

        # Show selected tab
        if tab_id in self.tabs:
            self.tabs[tab_id].pack(fill="both", expand=True, before=self.status_bar)

    def _update_status(self, text: str, status_type: str = "info"):
        """Cập nhật status bar"""
        if self.status_bar:
            self.status_bar.set_status(text, status_type)

    def _update_quick_stats(self, profiles: int, running: int, scripts: int = 0):
        """Cập nhật quick stats trong sidebar"""
        if self.quick_stats:
            self.quick_stats.update_stats(profiles, running, scripts)

    def _check_hidemium_connection(self):
        """Kiểm tra kết nối Hidemium"""
        from api_service import api
        import threading

        def check():
            connected = api.check_connection()
            self.after(0, lambda: self._set_connection_status(connected))

        threading.Thread(target=check, daemon=True).start()

    def _set_connection_status(self, connected: bool):
        """Cập nhật trạng thái kết nối"""
        if connected:
            self._update_status("SYSTEM READY - CONNECTED TO HIDEMIUM API", "success")
        else:
            self._update_status("HIDEMIUM API NOT CONNECTED", "error")

    def _open_settings(self):
        """Mở cửa sổ cài đặt"""
        settings = SettingsDialog(self)
        settings.grab_set()


class SettingsDialog(ctk.CTkToplevel):
    """Dialog cài đặt - Cyberpunk style"""

    def __init__(self, parent):
        super().__init__(parent)

        self.title("⚙ CÀI ĐẶT")
        self.geometry("600x500")
        self.configure(fg_color=COLORS["bg_dark"])
        self.transient(parent)

        self._create_ui()

        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 600) // 2
        y = (self.winfo_screenheight() - 500) // 2
        self.geometry(f"+{x}+{y}")

    def _create_ui(self):
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=30, pady=25)

        ctk.CTkLabel(
            header_frame,
            text="⚙",
            font=ctk.CTkFont(size=28),
            text_color=COLORS["cyan"]
        ).pack(side="left")

        ctk.CTkLabel(
            header_frame,
            text="CÀI ĐẶT HỆ THỐNG",
            font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left", padx=15)

        # Hidemium settings section
        hidemium_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=12)
        hidemium_frame.pack(fill="x", padx=30, pady=10)

        section_header = ctk.CTkFrame(hidemium_frame, fg_color="transparent")
        section_header.pack(fill="x", padx=20, pady=(15, 10))

        ctk.CTkLabel(
            section_header,
            text="🌐",
            font=ctk.CTkFont(size=16),
            text_color=COLORS["cyan"]
        ).pack(side="left")

        ctk.CTkLabel(
            section_header,
            text="HIDEMIUM API",
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left", padx=10)

        # API URL
        url_frame = ctk.CTkFrame(hidemium_frame, fg_color="transparent")
        url_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(
            url_frame,
            text="API URL",
            width=100,
            anchor="w",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=COLORS["text_secondary"]
        ).pack(side="left")

        self.api_url = ctk.CTkEntry(
            url_frame,
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            height=36
        )
        self.api_url.pack(side="left", fill="x", expand=True)
        self.api_url.insert(0, "http://127.0.0.1:2222")

        # Token
        token_frame = ctk.CTkFrame(hidemium_frame, fg_color="transparent")
        token_frame.pack(fill="x", padx=20, pady=(5, 20))

        ctk.CTkLabel(
            token_frame,
            text="API TOKEN",
            width=100,
            anchor="w",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=COLORS["text_secondary"]
        ).pack(side="left")

        self.api_token = ctk.CTkEntry(
            token_frame,
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            show="*",
            height=36
        )
        self.api_token.pack(side="left", fill="x", expand=True)
        self.api_token.insert(0, "your_token_here")

        # UI Settings section
        ui_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=12)
        ui_frame.pack(fill="x", padx=30, pady=10)

        ui_header = ctk.CTkFrame(ui_frame, fg_color="transparent")
        ui_header.pack(fill="x", padx=20, pady=(15, 10))

        ctk.CTkLabel(
            ui_header,
            text="🎨",
            font=ctk.CTkFont(size=16),
            text_color=COLORS["accent"]
        ).pack(side="left")

        ctk.CTkLabel(
            ui_header,
            text="GIAO DIỆN",
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left", padx=10)

        # Theme
        theme_frame = ctk.CTkFrame(ui_frame, fg_color="transparent")
        theme_frame.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(
            theme_frame,
            text="THEME",
            width=100,
            anchor="w",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=COLORS["text_secondary"]
        ).pack(side="left")

        theme_menu = ctk.CTkOptionMenu(
            theme_frame,
            values=["Cyberpunk Dark", "Classic Dark", "Light"],
            fg_color=COLORS["bg_input"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            dropdown_fg_color=COLORS["bg_card"],
            width=200,
            height=36
        )
        theme_menu.pack(side="left")

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=30)

        CyberButton(
            btn_frame,
            text="LƯU CÀI ĐẶT",
            icon="💾",
            variant="success",
            command=self._save_settings,
            width=140,
            height=40
        ).pack(side="left", padx=5)

        CyberButton(
            btn_frame,
            text="ĐÓNG",
            variant="secondary",
            command=self.destroy,
            width=100,
            height=40
        ).pack(side="left", padx=5)

    def _save_settings(self):
        """Lưu cài đặt"""
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
