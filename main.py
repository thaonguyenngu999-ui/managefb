"""
FB Manager Pro - Phần mềm quản lý tài khoản Facebook
Tích hợp Hidemium Browser API
"""
import customtkinter as ctk
from config import COLORS, WINDOW_WIDTH, WINDOW_HEIGHT, APP_NAME, APP_VERSION
from widgets import StatusBar
from tabs import ProfilesTab, ScriptsTab, PostsTab, ContentTab, GroupsTab


class FBManagerApp(ctk.CTk):
    """Ứng dụng chính FB Manager Pro"""
    
    def __init__(self):
        super().__init__()
        
        # Window setup
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(1200, 700)
        
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Configure colors
        self.configure(fg_color=COLORS["bg_dark"])
        
        # Initialize status_bar as None first
        self.status_bar = None
        
        # Create UI
        self._create_sidebar()
        self._create_main_frame()  # Create main frame first
        self._create_status_bar()  # Create status bar BEFORE tabs
        self._create_tabs()  # Create tabs last
        
        # Show default tab
        self._show_tab("profiles")
    
    def _create_sidebar(self):
        """Tạo sidebar navigation"""
        self.sidebar = ctk.CTkFrame(
            self,
            width=260,
            corner_radius=0,
            fg_color=COLORS["bg_secondary"]
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo/Title - Enhanced design
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=18, pady=28)

        # Logo icon with better styling
        ctk.CTkLabel(
            logo_frame,
            text="🔥",
            font=ctk.CTkFont(size=42)
        ).pack(side="left", padx=(0, 12))

        title_frame = ctk.CTkFrame(logo_frame, fg_color="transparent")
        title_frame.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            title_frame,
            text="FB Manager",
            font=ctk.CTkFont(family="Segoe UI", size=21, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_frame,
            text="Pro Edition",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=COLORS["accent"]
        ).pack(anchor="w", pady=(2, 0))

        # Separator - Enhanced
        separator = ctk.CTkFrame(self.sidebar, height=1, fg_color=COLORS["border_light"])
        separator.pack(fill="x", padx=18, pady=14)
        
        # Navigation buttons
        self.nav_buttons = {}
        nav_items = [
            ("profiles", "📋", "Quản lý Profiles"),
            ("content", "✏️", "Soạn tin"),
            ("groups", "👥", "Đăng Nhóm"),
            ("scripts", "📜", "Kịch bản"),
            ("posts", "📰", "Bài đăng"),
        ]
        
        for tab_id, icon, text in nav_items:
            btn = self._create_nav_button(tab_id, icon, text)
            btn.pack(fill="x", padx=15, pady=5)
            self.nav_buttons[tab_id] = btn
        
        # Bottom section - Enhanced
        bottom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", padx=16, pady=20)

        # Connection status - Enhanced
        self.connection_frame = ctk.CTkFrame(
            bottom_frame,
            fg_color=COLORS["bg_tertiary"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border_light"]
        )
        self.connection_frame.pack(fill="x", pady=(0, 14))

        self.connection_label = ctk.CTkLabel(
            self.connection_frame,
            text="● Hidemium: Đang kết nối...",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLORS["warning"]
        )
        self.connection_label.pack(padx=14, pady=10)

        # Settings button - Enhanced
        settings_btn = ctk.CTkButton(
            bottom_frame,
            text="⚙️ Cài đặt",
            fg_color=COLORS["bg_tertiary"],
            hover_color=COLORS["bg_hover"],
            anchor="w",
            height=46,
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._open_settings
        )
        settings_btn.pack(fill="x")
        
        # Check connection
        self.after(1000, self._check_hidemium_connection)
    
    def _create_nav_button(self, tab_id: str, icon: str, text: str):
        """Tạo navigation button"""
        btn = ctk.CTkButton(
            self.sidebar,
            text=f"  {icon}  {text}",
            fg_color="transparent",
            hover_color=COLORS["bg_hover"],
            anchor="w",
            height=54,
            corner_radius=12,
            border_width=0,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=COLORS["text_primary"],
            command=lambda: self._show_tab(tab_id)
        )
        return btn
    
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
        # Tab containers
        self.tabs = {}

        # Profiles tab
        self.tabs["profiles"] = ProfilesTab(
            self.main_frame,
            status_callback=self._update_status
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
        self.status_bar = StatusBar(self.main_frame)
        self.status_bar.pack(side="bottom", fill="x")
    
    def _show_tab(self, tab_id: str):
        """Hiển thị tab được chọn"""
        # Hide all tabs
        for tab in self.tabs.values():
            tab.pack_forget()

        # Update nav buttons with better visual feedback
        for btn_id, btn in self.nav_buttons.items():
            if btn_id == tab_id:
                btn.configure(
                    fg_color=COLORS["accent"],
                    text_color=COLORS["text_primary"],
                    hover_color=COLORS["accent_hover"]
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=COLORS["text_primary"],
                    hover_color=COLORS["bg_hover"]
                )

        # Show selected tab
        if tab_id in self.tabs:
            self.tabs[tab_id].pack(fill="both", expand=True, before=self.status_bar)
    
    def _update_status(self, text: str, status_type: str = "info"):
        """Cập nhật status bar"""
        if self.status_bar:
            self.status_bar.set_status(text, status_type)
    
    def _check_hidemium_connection(self):
        """Kiểm tra kết nối Hidemium"""
        from api_service import api
        import threading
        
        def check():
            connected = api.check_connection()
            self.after(0, lambda: self._set_connection_status(connected))
        
        threading.Thread(target=check, daemon=True).start()
    
    def _set_connection_status(self, connected: bool, version: str = ""):
        """Cập nhật trạng thái kết nối"""
        if connected:
            self.connection_label.configure(
                text=f"● Hidemium: Đã kết nối",
                text_color=COLORS["success"]
            )
        else:
            self.connection_label.configure(
                text="● Hidemium: Chưa kết nối",
                text_color=COLORS["error"]
            )
    
    def _open_settings(self):
        """Mở cửa sổ cài đặt"""
        settings = SettingsDialog(self)
        settings.grab_set()


class SettingsDialog(ctk.CTkToplevel):
    """Dialog cài đặt"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("⚙️ Cài đặt")
        self.geometry("600x500")
        self.configure(fg_color=COLORS["bg_dark"])
        self.transient(parent)
        
        self._create_ui()
    
    def _create_ui(self):
        # Header
        ctk.CTkLabel(
            self,
            text="⚙️ Cài đặt ứng dụng",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(pady=28)

        # Hidemium settings - Enhanced
        hidemium_frame = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_card"],
            corner_radius=16,
            border_width=1,
            border_color=COLORS["border_light"]
        )
        hidemium_frame.pack(fill="x", padx=32, pady=12)

        ctk.CTkLabel(
            hidemium_frame,
            text="🌐 Cấu hình Hidemium",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=22, pady=(16, 12))
        
        # API URL
        url_frame = ctk.CTkFrame(hidemium_frame, fg_color="transparent")
        url_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(
            url_frame,
            text="API URL:",
            width=100,
            anchor="w",
            text_color=COLORS["text_secondary"]
        ).pack(side="left")
        
        self.api_url = ctk.CTkEntry(
            url_frame,
            fg_color=COLORS["bg_card"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"]
        )
        self.api_url.pack(side="left", fill="x", expand=True)
        self.api_url.insert(0, "http://127.0.0.1:2222")
        
        # Token
        token_frame = ctk.CTkFrame(hidemium_frame, fg_color="transparent")
        token_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(
            token_frame,
            text="API Token:",
            width=100,
            anchor="w",
            text_color=COLORS["text_secondary"]
        ).pack(side="left")
        
        self.api_token = ctk.CTkEntry(
            token_frame,
            fg_color=COLORS["bg_card"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            show="*"
        )
        self.api_token.pack(side="left", fill="x", expand=True, pady=(0, 15))
        self.api_token.insert(0, "your_token_here")
        
        # UI Settings - Enhanced
        ui_frame = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_card"],
            corner_radius=16,
            border_width=1,
            border_color=COLORS["border_light"]
        )
        ui_frame.pack(fill="x", padx=32, pady=12)

        ctk.CTkLabel(
            ui_frame,
            text="🎨 Giao diện",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=22, pady=(16, 12))
        
        # Theme
        theme_frame = ctk.CTkFrame(ui_frame, fg_color="transparent")
        theme_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(
            theme_frame,
            text="Theme:",
            width=100,
            anchor="w",
            text_color=COLORS["text_secondary"]
        ).pack(side="left")
        
        theme_menu = ctk.CTkOptionMenu(
            theme_frame,
            values=["Dark", "Light", "System"],
            fg_color=COLORS["bg_card"],
            button_color=COLORS["accent"],
            width=200
        )
        theme_menu.pack(side="left")
        
        # Buttons - Enhanced
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=32, pady=32)

        ctk.CTkButton(
            btn_frame,
            text="💾 Lưu cài đặt",
            fg_color=COLORS["success"],
            hover_color=COLORS["success_hover"],
            width=144,
            height=44,
            corner_radius=12,
            border_width=0,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._save_settings
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            btn_frame,
            text="Đóng",
            fg_color=COLORS["bg_tertiary"],
            hover_color=COLORS["bg_hover"],
            border_width=1,
            border_color=COLORS["border"],
            width=104,
            height=44,
            corner_radius=12,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.destroy
        ).pack(side="left", padx=6)
    
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
