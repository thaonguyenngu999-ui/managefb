"""
FB Manager Pro - Phần mềm quản lý tài khoản Facebook
Tích hợp Hidemium Browser API
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
        if text.strip():  # Chỉ log text có nội dung
            self.callback(text)
        # Vẫn ghi ra stream gốc
        if self.original_stream:
            self.original_stream.write(text)
            self.original_stream.flush()

    def flush(self):
        if self.original_stream:
            self.original_stream.flush()


class FBManagerApp(ctk.CTk):
    """Ứng dụng chính FB Manager Pro"""
    
    def __init__(self):
        super().__init__()

        # Window setup - tăng kích thước để có chỗ cho LOG panel
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry(f"{WINDOW_WIDTH + 400}x{WINDOW_HEIGHT}")  # +400 cho LOG panel
        self.minsize(1600, 700)

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
        self._create_log_panel()   # Create LOG panel on the right
        self._create_status_bar()  # Create status bar BEFORE tabs
        self._create_tabs()  # Create tabs last

        # Setup log redirector AFTER UI is created
        self._setup_log_redirector()

        # Show default tab
        self._show_tab("profiles")

        # Initial log message
        self._add_log("[App] FB Manager Pro started", "INFO")
    
    def _create_sidebar(self):
        """Tạo sidebar navigation"""
        self.sidebar = ctk.CTkFrame(
            self,
            width=250,
            corner_radius=0,
            fg_color=COLORS["bg_secondary"]
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        # Logo/Title
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=20, pady=25)
        
        ctk.CTkLabel(
            logo_frame,
            text="🔥",
            font=ctk.CTkFont(size=40)
        ).pack(side="left")
        
        title_frame = ctk.CTkFrame(logo_frame, fg_color="transparent")
        title_frame.pack(side="left", padx=10)
        
        ctk.CTkLabel(
            title_frame,
            text="FB Manager",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            title_frame,
            text="Pro Edition",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS["accent"]
        ).pack(anchor="w")
        
        # Separator
        separator = ctk.CTkFrame(self.sidebar, height=2, fg_color=COLORS["border"])
        separator.pack(fill="x", padx=20, pady=10)
        
        # Navigation buttons
        self.nav_buttons = {}
        nav_items = [
            ("profiles", "📋", "Quản lý Profiles"),
            ("login", "🔐", "Login FB"),
            ("pages", "📄", "Quản lý Page"),
            ("reels_page", "🎬", "Đăng Reels Page"),
            ("content", "✏️", "Soạn tin"),
            ("groups", "👥", "Đăng Nhóm"),
            ("scripts", "📜", "Kịch bản"),
            ("posts", "📰", "Bài đăng"),
        ]
        
        for tab_id, icon, text in nav_items:
            btn = self._create_nav_button(tab_id, icon, text)
            btn.pack(fill="x", padx=15, pady=5)
            self.nav_buttons[tab_id] = btn
        
        # Bottom section
        bottom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", padx=20, pady=20)
        
        # Settings button
        settings_btn = ctk.CTkButton(
            bottom_frame,
            text="⚙️ Cài đặt",
            fg_color="transparent",
            hover_color=COLORS["border"],
            anchor="w",
            height=40,
            font=ctk.CTkFont(size=14),
            command=self._open_settings
        )
        settings_btn.pack(fill="x", pady=5)
        
        # Connection status
        self.connection_frame = ctk.CTkFrame(bottom_frame, fg_color=COLORS["bg_card"], corner_radius=10)
        self.connection_frame.pack(fill="x", pady=10)
        
        self.connection_label = ctk.CTkLabel(
            self.connection_frame,
            text="● Hidemium: Đang kết nối...",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["warning"]
        )
        self.connection_label.pack(padx=15, pady=10)
        
        # Check connection
        self.after(1000, self._check_hidemium_connection)
    
    def _create_nav_button(self, tab_id: str, icon: str, text: str):
        """Tạo navigation button"""
        btn = ctk.CTkButton(
            self.sidebar,
            text=f"  {icon}  {text}",
            fg_color="transparent",
            hover_color=COLORS["bg_card"],
            anchor="w",
            height=50,
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=14),
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

    def _create_log_panel(self):
        """Tạo LOG panel bên phải"""
        # Container cho LOG panel
        self.log_panel = ctk.CTkFrame(
            self,
            width=400,
            fg_color=COLORS["bg_secondary"],
            corner_radius=0
        )
        self.log_panel.pack(side="right", fill="y")
        self.log_panel.pack_propagate(False)

        # Header
        header_frame = ctk.CTkFrame(self.log_panel, fg_color=COLORS["bg_card"], corner_radius=0)
        header_frame.pack(fill="x")

        ctk.CTkLabel(
            header_frame,
            text="📋 LOG & DEBUG",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left", padx=15, pady=12)

        # Clear button
        ctk.CTkButton(
            header_frame,
            text="🗑️ Clear",
            width=70,
            height=28,
            fg_color=COLORS["error"],
            hover_color="#ff6b6b",
            corner_radius=5,
            font=ctk.CTkFont(size=12),
            command=self._clear_logs
        ).pack(side="right", padx=10, pady=8)

        # Log text area with scrollbar
        log_container = ctk.CTkFrame(self.log_panel, fg_color="transparent")
        log_container.pack(fill="both", expand=True, padx=10, pady=10)

        self.log_text = ctk.CTkTextbox(
            log_container,
            fg_color=COLORS["bg_dark"],
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont(family="Consolas", size=11),
            corner_radius=8,
            wrap="word"
        )
        self.log_text.pack(fill="both", expand=True)

        # Configure tags for different log levels
        self.log_text._textbox.tag_config("INFO", foreground="#00d9ff")
        self.log_text._textbox.tag_config("ERROR", foreground="#ff5555")
        self.log_text._textbox.tag_config("WARNING", foreground="#ffaa00")
        self.log_text._textbox.tag_config("SUCCESS", foreground="#00d97e")
        self.log_text._textbox.tag_config("DEBUG", foreground="#888888")
        self.log_text._textbox.tag_config("TIMESTAMP", foreground="#666666")

    def _setup_log_redirector(self):
        """Setup stdout/stderr redirector để capture logs"""
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr

        # Redirect stdout và stderr
        sys.stdout = LogRedirector(self._on_log_output, self._original_stdout)
        sys.stderr = LogRedirector(self._on_log_output, self._original_stderr)

    def _on_log_output(self, text):
        """Callback khi có log output"""
        # Xác định log level từ text
        level = "INFO"
        if "ERROR" in text.upper():
            level = "ERROR"
        elif "WARNING" in text.upper() or "WARN" in text.upper():
            level = "WARNING"
        elif "SUCCESS" in text.upper() or "✓" in text:
            level = "SUCCESS"
        elif "DEBUG" in text.upper():
            level = "DEBUG"

        # Schedule UI update on main thread
        self.after(0, lambda: self._add_log(text.strip(), level))

    def _add_log(self, text: str, level: str = "INFO"):
        """Thêm log vào panel"""
        if not hasattr(self, 'log_text') or not self.log_text:
            return

        timestamp = datetime.now().strftime("%H:%M:%S")

        # Insert timestamp
        self.log_text._textbox.insert("end", f"[{timestamp}] ", "TIMESTAMP")

        # Insert log message với màu tương ứng
        self.log_text._textbox.insert("end", f"{text}\n", level)

        # Auto scroll to bottom
        self.log_text._textbox.see("end")

    def _clear_logs(self):
        """Clear tất cả logs"""
        if hasattr(self, 'log_text') and self.log_text:
            self.log_text._textbox.delete("1.0", "end")
            self._add_log("[App] Logs cleared", "INFO")

    def _create_tabs(self):
        """Tạo các tabs"""
        # Tab containers
        self.tabs = {}

        # Profiles tab
        self.tabs["profiles"] = ProfilesTab(
            self.main_frame,
            status_callback=self._update_status
        )

        # Login FB tab
        self.tabs["login"] = LoginTab(
            self.main_frame,
            status_callback=self._update_status
        )

        # Pages tab (Quản lý Page)
        self.tabs["pages"] = PagesTab(
            self.main_frame,
            status_callback=self._update_status
        )

        # Reels Page tab (Đăng Reels Page)
        self.tabs["reels_page"] = ReelsPageTab(
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

        # Update nav buttons
        for btn_id, btn in self.nav_buttons.items():
            if btn_id == tab_id:
                btn.configure(fg_color=COLORS["accent"])
            else:
                btn.configure(fg_color="transparent")

        # Show selected tab
        if tab_id in self.tabs:
            self.tabs[tab_id].pack(fill="both", expand=True, before=self.status_bar)

            # Auto-refresh posts tab when shown (to show new posts from groups tab)
            if tab_id == "posts" and hasattr(self.tabs[tab_id], '_load_data'):
                self.tabs[tab_id]._load_data()
    
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
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(pady=25)
        
        # Hidemium settings
        hidemium_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=15)
        hidemium_frame.pack(fill="x", padx=30, pady=10)
        
        ctk.CTkLabel(
            hidemium_frame,
            text="🌐 Cấu hình Hidemium",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=20, pady=(15, 10))
        
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
        
        # UI Settings
        ui_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=15)
        ui_frame.pack(fill="x", padx=30, pady=10)
        
        ctk.CTkLabel(
            ui_frame,
            text="🎨 Giao diện",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=20, pady=(15, 10))
        
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
        
        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=30)
        
        ctk.CTkButton(
            btn_frame,
            text="💾 Lưu cài đặt",
            fg_color=COLORS["success"],
            hover_color="#00f5b5",
            width=140,
            height=40,
            corner_radius=10,
            command=self._save_settings
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Đóng",
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["border"],
            width=100,
            height=40,
            corner_radius=10,
            command=self.destroy
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
