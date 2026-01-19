"""
Tab Quản lý Profiles - Cyberpunk UI với Table Layout
FB Manager Pro v3.0 CYBER
"""
import customtkinter as ctk
from typing import List, Dict, Callable
import threading
from config import COLORS, FONT_FAMILY, FONT_FAMILY_MONO
from widgets import (
    CyberButton, CyberEntry, CyberSearchBar, FolderDropdown,
    StatsCard, ProfileTableRow, TableHeader, ModernEntry
)
from api_service import api
from db import get_profiles as db_get_profiles, sync_profiles, update_profile_local


class ProfilesTab(ctk.CTkFrame):
    """Tab quản lý danh sách profiles - Cyberpunk Theme"""

    def __init__(self, master, status_callback: Callable = None,
                 stats_callback: Callable = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.status_callback = status_callback
        self.stats_callback = stats_callback  # Callback to update quick stats in sidebar
        self.profiles: List[Dict] = []
        self.selected_profiles: List[Dict] = []
        self.profile_rows: List[ProfileTableRow] = []
        self.folders: List[Dict] = []
        self.folder_id_to_name: Dict[int, str] = {}
        self._auto_refresh_job = None
        self._is_polling = False

        self._create_ui()
        self._load_folders()
        self._load_profiles()
        self._start_auto_refresh()

    def _start_auto_refresh(self):
        """Bắt đầu auto-refresh running status mỗi 5 giây"""
        self._auto_refresh_silent()

    def _safe_after(self, delay, callback):
        """Thread-safe wrapper cho self.after"""
        try:
            if self.winfo_exists():
                self.after(delay, callback)
        except (RuntimeError, Exception):
            pass

    def _auto_refresh_silent(self):
        """Auto refresh running status không hiện status message"""
        if self._is_polling:
            self._auto_refresh_job = self.after(5000, self._auto_refresh_silent)
            return

        self._is_polling = True

        def fetch():
            try:
                running_uuids = api.get_running_profiles(is_local=True)
                self._safe_after(0, lambda: self._on_auto_refresh_complete(running_uuids))
            except Exception:
                self._safe_after(0, lambda: self._on_auto_refresh_error())

        threading.Thread(target=fetch, daemon=True).start()

    def _on_auto_refresh_complete(self, running_uuids: List[str]):
        """Xử lý kết quả auto-refresh"""
        self._is_polling = False

        changed = False
        for profile in self.profiles:
            uuid = profile.get('uuid')
            new_status = 1 if uuid in running_uuids else 0
            if profile.get('check_open') != new_status:
                profile['check_open'] = new_status
                update_profile_local(uuid, {'check_open': new_status})
                self._update_row_status(uuid, new_status)
                changed = True

        if changed:
            self._update_stats()

        self._auto_refresh_job = self.after(5000, self._auto_refresh_silent)

    def _on_auto_refresh_error(self):
        """Xử lý lỗi auto-refresh"""
        self._is_polling = False
        self._auto_refresh_job = self.after(5000, self._auto_refresh_silent)

    def destroy(self):
        """Cleanup khi destroy widget"""
        if self._auto_refresh_job:
            self.after_cancel(self._auto_refresh_job)
        super().destroy()

    def _create_ui(self):
        """Tạo giao diện cyberpunk"""
        # ========== PAGE HEADER ==========
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=25, pady=(25, 15))

        # Left side - Title with icon
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(side="left")

        # Title with neon effect
        title_container = ctk.CTkFrame(
            title_frame,
            fg_color=COLORS["accent"] + "20",
            corner_radius=8
        )
        title_container.pack(side="left")

        ctk.CTkLabel(
            title_container,
            text="⚡ QUẢN LÝ PROFILES",
            font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"),
            text_color=COLORS["accent"]
        ).pack(padx=15, pady=8)

        # Subtitle
        ctk.CTkLabel(
            title_frame,
            text="Quản lý và điều khiển browser profiles",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=5, pady=(8, 0))

        # Right side - Action buttons
        action_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        action_frame.pack(side="right")

        CyberButton(
            action_frame,
            text="SYNC",
            icon="⟳",
            variant="secondary",
            command=self._sync_profiles,
            width=100
        ).pack(side="left", padx=5)

        CyberButton(
            action_frame,
            text="TẠO PROFILE",
            icon="+",
            variant="cyan",
            command=self._show_create_dialog,
            width=130
        ).pack(side="left", padx=5)

        # ========== STATS CARDS ROW ==========
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(fill="x", padx=25, pady=(0, 15))

        # Configure grid for equal columns
        stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="stats")

        # Card 1: Total Profiles
        self.stats_total = StatsCard(
            stats_frame,
            icon="◎",
            title="Tổng Profiles",
            value="0",
            color="cyan"
        )
        self.stats_total.grid(row=0, column=0, padx=5, sticky="nsew")

        # Card 2: Running
        self.stats_running = StatsCard(
            stats_frame,
            icon="▶",
            title="Đang Chạy",
            value="0",
            trend="↑+0 hôm nay",
            color="success"
        )
        self.stats_running.grid(row=0, column=1, padx=5, sticky="nsew")

        # Card 3: Folders
        self.stats_folders = StatsCard(
            stats_frame,
            icon="📁",
            title="Folders",
            value="0",
            color="purple"
        )
        self.stats_folders.grid(row=0, column=2, padx=5, sticky="nsew")

        # Card 4: Scripts
        self.stats_scripts = StatsCard(
            stats_frame,
            icon="⚡",
            title="Scripts",
            value="0",
            trend="↑+0 tuần này",
            color="warning"
        )
        self.stats_scripts.grid(row=0, column=3, padx=5, sticky="nsew")

        # ========== TOOLBAR ==========
        toolbar = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_card"],
            corner_radius=10,
            height=55
        )
        toolbar.pack(fill="x", padx=25, pady=(0, 10))
        toolbar.pack_propagate(False)

        toolbar_inner = ctk.CTkFrame(toolbar, fg_color="transparent")
        toolbar_inner.pack(fill="both", expand=True, padx=15, pady=8)

        # Search bar
        self.search_bar = CyberSearchBar(
            toolbar_inner,
            placeholder="TÌM KIẾM PROFILE...",
            on_search=self._search_profiles
        )
        self.search_bar.pack(side="left")

        # Folder dropdown
        self.folder_dropdown = FolderDropdown(
            toolbar_inner,
            on_select=self._filter_by_folder
        )
        self.folder_dropdown.pack(side="left", padx=25)

        # Bulk action buttons (right side)
        bulk_frame = ctk.CTkFrame(toolbar_inner, fg_color="transparent")
        bulk_frame.pack(side="right")

        CyberButton(
            bulk_frame,
            text="ĐÓNG TẤT CẢ",
            variant="outline_danger",
            command=self._close_all,
            width=110
        ).pack(side="left", padx=5)

        CyberButton(
            bulk_frame,
            text="MỞ TẤT CẢ",
            variant="outline_cyan",
            command=self._open_all,
            width=100
        ).pack(side="left", padx=5)

        # ========== TABLE SECTION ==========
        table_container = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_card"],
            corner_radius=10
        )
        table_container.pack(fill="both", expand=True, padx=25, pady=(0, 15))

        # Table header
        self.table_header = TableHeader(
            table_container,
            on_select_all=self._on_select_all
        )
        self.table_header.pack(fill="x")

        # Separator line
        separator = ctk.CTkFrame(table_container, fg_color=COLORS["border"], height=1)
        separator.pack(fill="x")

        # Scrollable table body
        self.table_body = ctk.CTkScrollableFrame(
            table_container,
            fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["accent"]
        )
        self.table_body.pack(fill="both", expand=True)

        # Loading indicator
        self.loading_label = ctk.CTkLabel(
            self.table_body,
            text="⏳ Đang tải danh sách profiles...",
            font=ctk.CTkFont(family=FONT_FAMILY, size=14),
            text_color=COLORS["text_secondary"]
        )
        self.loading_label.pack(pady=50)

    def _load_profiles(self):
        """Load profiles từ local database"""
        self.profiles = db_get_profiles()

        if self.profiles:
            self._apply_folder_names_to_profiles()
            self._render_profiles(self.profiles)
            self._update_stats()
            self._refresh_running_status()
        else:
            self._sync_profiles()

    def _sync_profiles(self):
        """Đồng bộ profiles từ Hidemium API"""
        self._set_status("Đang đồng bộ profiles từ Hidemium...", "info")
        self.loading_label.configure(text="⏳ Đang đồng bộ từ Hidemium...")
        self.loading_label.pack(pady=50)

        # Clear existing rows
        for row in self.profile_rows:
            row.destroy()
        self.profile_rows.clear()

        def fetch():
            profiles_result = api.get_profiles(limit=100, is_local=True)
            running_uuids = api.get_running_profiles(is_local=True)
            self._safe_after(0, lambda: self._on_sync_complete(profiles_result, running_uuids))

        threading.Thread(target=fetch, daemon=True).start()

    def _on_sync_complete(self, result, running_uuids: List[str] = None):
        """Xử lý kết quả sync"""
        self.loading_label.pack_forget()
        running_uuids = running_uuids or []

        if isinstance(result, list) and result:
            for profile in result:
                uuid = profile.get('uuid')
                profile['check_open'] = 1 if uuid in running_uuids else 0

            sync_profiles(result)
            self.profiles = result
            self._apply_folder_names_to_profiles()

            running_count = len(running_uuids)
            self._set_status(f"Đã đồng bộ {len(result)} profiles ({running_count} đang chạy)", "success")
        elif isinstance(result, dict) and result.get('type') == 'error':
            self._set_status(result.get('title', 'Lỗi'), "error")
            self.loading_label.configure(text=f"❌ {result.get('title', 'Không thể đồng bộ')}")
            self.loading_label.pack(pady=50)
            return
        else:
            self.profiles = []
            self._set_status("Không có profiles", "warning")

        self._render_profiles(self.profiles)
        self._update_stats()

    def _refresh_running_status(self):
        """Cập nhật trạng thái running từ API"""
        self._set_status("Đang kiểm tra trạng thái profiles...", "info")

        def fetch():
            running_uuids = api.get_running_profiles(is_local=True)
            self._safe_after(0, lambda: self._on_running_status_received(running_uuids))

        threading.Thread(target=fetch, daemon=True).start()

    def _on_running_status_received(self, running_uuids: List[str]):
        """Xử lý khi nhận running status"""
        for profile in self.profiles:
            uuid = profile.get('uuid')
            new_status = 1 if uuid in running_uuids else 0
            if profile.get('check_open') != new_status:
                profile['check_open'] = new_status
                update_profile_local(uuid, {'check_open': new_status})
                self._update_row_status(uuid, new_status)

        self._update_stats()
        running_count = len(running_uuids)
        self._set_status(f"Đã cập nhật: {running_count} profile đang chạy", "success")

    def _render_profiles(self, profiles: List[Dict]):
        """Render danh sách profiles dạng table rows"""
        # Clear existing rows
        for row in self.profile_rows:
            row.destroy()
        self.profile_rows.clear()

        if not profiles:
            self.loading_label.configure(text="📭 Không có profile nào")
            self.loading_label.pack(pady=50)
            return

        self.loading_label.pack_forget()

        for profile in profiles:
            row = ProfileTableRow(
                self.table_body,
                profile_data=profile,
                on_toggle=self._toggle_profile,
                on_select=self._on_profile_select
            )
            row.pack(fill="x", pady=1)
            self.profile_rows.append(row)

    def _update_stats(self):
        """Cập nhật thống kê"""
        total = len(self.profiles)
        running = sum(1 for p in self.profiles if p.get('check_open') == 1)
        folders = len(self.folders)

        # Update stats cards
        # For stats cards, we need to recreate them or update their values
        # Since StatsCard doesn't have dynamic update, we'll update the labels directly

        # Update quick stats in sidebar
        if self.stats_callback:
            self.stats_callback(total, running, 0)

        # Update folder filter
        self._update_folder_filter()

    def _search_profiles(self, query: str):
        """Tìm kiếm profiles"""
        if not query:
            self._render_profiles(self.profiles)
            return

        filtered = [
            p for p in self.profiles
            if query.lower() in p.get('name', '').lower()
            or query.lower() in p.get('uuid', '').lower()
        ]
        self._render_profiles(filtered)

    def _filter_by_folder(self, folder_name: str):
        """Lọc profiles theo folder"""
        if folder_name == "TẤT CẢ":
            filtered = self.profiles
        else:
            target_folder_id = None
            for fid, fname in self.folder_id_to_name.items():
                if fname == folder_name:
                    target_folder_id = fid
                    break

            if target_folder_id is not None:
                filtered = [p for p in self.profiles if p.get('folder_id') == target_folder_id]
            else:
                filtered = [p for p in self.profiles if p.get('folder_name', '') == folder_name]

        self._render_profiles(filtered)

    def _load_folders(self):
        """Load danh sách folders"""
        def fetch():
            folders = api.get_folders(is_local=True)
            self._safe_after(0, lambda: self._on_folders_loaded(folders))

        threading.Thread(target=fetch, daemon=True).start()

    def _on_folders_loaded(self, folders: List):
        """Xử lý khi load folders xong"""
        self.folders = folders if folders else []

        self.folder_id_to_name = {}
        for folder in self.folders:
            fid = folder.get('id') or folder.get('folder_id')
            fname = folder.get('name') or folder.get('folder_name')
            if fid is not None and fname:
                self.folder_id_to_name[fid] = fname

        self._apply_folder_names_to_profiles()
        self._update_folder_filter()

    def _apply_folder_names_to_profiles(self):
        """Áp dụng folder_name cho profiles"""
        for p in self.profiles:
            fid = p.get('folder_id')
            if fid and fid in self.folder_id_to_name:
                p['folder_name'] = self.folder_id_to_name[fid]

    def _update_folder_filter(self):
        """Cập nhật dropdown folders"""
        folder_list = ["TẤT CẢ"]

        for folder in self.folders:
            name = folder.get('name') or folder.get('folder_name')
            if name:
                folder_list.append(name)

        if len(folder_list) == 1:
            folder_names = set()
            for p in self.profiles:
                folder = p.get('folder_name')
                if folder:
                    folder_names.add(folder)
            folder_list.extend(sorted(folder_names))

        self.folder_dropdown.set_values(folder_list)

    def _on_select_all(self, selected: bool):
        """Chọn/bỏ chọn tất cả"""
        self.selected_profiles.clear()

        for row in self.profile_rows:
            row.set_selected(selected)
            if selected:
                self.selected_profiles.append(row.profile_data)

    def _on_profile_select(self, profile: Dict, selected: bool):
        """Xử lý khi chọn profile"""
        if selected:
            if profile not in self.selected_profiles:
                self.selected_profiles.append(profile)
        else:
            if profile in self.selected_profiles:
                self.selected_profiles.remove(profile)

    def _toggle_profile(self, profile: Dict, open_browser: bool):
        """Toggle mở/đóng browser"""
        uuid = profile.get('uuid')
        name = profile.get('name', 'Unknown')

        if open_browser:
            self._set_status(f"Đang mở profile {name}...", "info")

            def do_action():
                result = api.open_browser(uuid)
                self._safe_after(0, lambda: self._on_toggle_complete(result, profile, True))
        else:
            self._set_status(f"Đang đóng profile {name}...", "info")

            def do_action():
                result = api.close_browser(uuid)
                self._safe_after(0, lambda: self._on_toggle_complete(result, profile, False))

        threading.Thread(target=do_action, daemon=True).start()

    def _on_toggle_complete(self, result, profile: Dict, was_opening: bool):
        """Xử lý kết quả toggle"""
        action = "mở" if was_opening else "đóng"
        uuid = profile.get('uuid')

        is_success = False
        if was_opening:
            is_success = result.get('status') == 'successfully'
        else:
            message = result.get('message', '')
            is_success = 'closed' in message.lower() or message == 'Profile closed'

        if is_success:
            self._set_status(f"Đã {action} profile {profile.get('name')} thành công", "success")

            new_check_open = 1 if was_opening else 0
            for i, p in enumerate(self.profiles):
                if p.get('uuid') == uuid:
                    self.profiles[i]['check_open'] = new_check_open
                    break

            update_profile_local(uuid, {'check_open': new_check_open})
            self._update_row_status(uuid, new_check_open)
            self._update_stats()
        else:
            error_msg = result.get('message') or result.get('title') or 'Lỗi không xác định'
            self._set_status(f"Lỗi {action}: {error_msg}", "error")

    def _update_row_status(self, uuid: str, check_open: int):
        """Cập nhật trạng thái row"""
        for row in self.profile_rows:
            if row.profile_data.get('uuid') == uuid:
                row.update_status(check_open == 1)
                break

    def _open_all(self):
        """Mở tất cả profiles đã chọn hoặc tất cả nếu không chọn"""
        profiles_to_open = self.selected_profiles if self.selected_profiles else self.profiles

        if not profiles_to_open:
            self._set_status("Không có profile nào để mở", "warning")
            return

        self._set_status(f"Đang mở {len(profiles_to_open)} profiles...", "info")

        for profile in profiles_to_open:
            if profile.get('check_open') != 1:
                self._toggle_profile(profile, True)

    def _close_all(self):
        """Đóng tất cả profiles đang chạy"""
        running_profiles = [p for p in self.profiles if p.get('check_open') == 1]

        if not running_profiles:
            self._set_status("Không có profile nào đang chạy", "warning")
            return

        self._set_status(f"Đang đóng {len(running_profiles)} profiles...", "info")

        for profile in running_profiles:
            self._toggle_profile(profile, False)

    def _set_status(self, text: str, status_type: str = "info"):
        """Cập nhật status bar"""
        if self.status_callback:
            self.status_callback(text, status_type)

    def _show_create_dialog(self):
        """Hiển thị dialog tạo profile mới"""
        dialog = CreateProfileDialog(self)
        self.wait_window(dialog)

        if dialog.result:
            self._set_status("Đang tạo profile mới...", "info")

            def do_create():
                result = api.create_profile(dialog.result)
                self._safe_after(0, lambda: self._on_create_complete(result))

            threading.Thread(target=do_create, daemon=True).start()

    def _on_create_complete(self, result):
        """Xử lý kết quả tạo profile"""
        if result and (result.get('uuid') or result.get('type') == 'success'):
            self._set_status("Đã tạo profile mới thành công!", "success")
            self._load_folders()
            self._sync_profiles()
        else:
            error_msg = ''
            if result:
                error_msg = result.get('title') or result.get('message') or result.get('error') or str(result)
            else:
                error_msg = 'Không thể tạo profile - không có response'
            self._set_status(f"Lỗi: {error_msg}", "error")


class CreateProfileDialog(ctk.CTkToplevel):
    """Dialog tạo profile mới - Cyberpunk style"""

    def __init__(self, parent):
        super().__init__(parent)

        self.result = None

        self.title("+ TẠO PROFILE MỚI")
        self.geometry("600x750")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg_dark"])

        self.transient(parent)
        self.grab_set()

        self._create_ui()

        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 600) // 2
        y = (self.winfo_screenheight() - 750) // 2
        self.geometry(f"+{x}+{y}")

    def _create_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 15))

        ctk.CTkLabel(
            header,
            text="+ TẠO PROFILE MỚI",
            font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"),
            text_color=COLORS["cyan"]
        ).pack(side="left")

        # Scrollable form
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", height=580)
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # ===== BASIC INFO =====
        basic_frame = ctk.CTkFrame(scroll, fg_color=COLORS["bg_card"], corner_radius=12)
        basic_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            basic_frame,
            text="📝 THÔNG TIN CƠ BẢN",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            text_color=COLORS["cyan"]
        ).pack(anchor="w", padx=15, pady=(12, 8))

        # Name
        name_row = ctk.CTkFrame(basic_frame, fg_color="transparent")
        name_row.pack(fill="x", padx=15, pady=3)
        ctk.CTkLabel(name_row, text="Tên Profile:", width=120, anchor="w",
                    font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                    text_color=COLORS["text_secondary"]).pack(side="left")
        self.name_entry = ModernEntry(name_row, placeholder="VD: FB Account 01", width=350)
        self.name_entry.pack(side="left", fill="x", expand=True)

        # Folder
        folder_row = ctk.CTkFrame(basic_frame, fg_color="transparent")
        folder_row.pack(fill="x", padx=15, pady=3)
        ctk.CTkLabel(folder_row, text="Thư mục:", width=120, anchor="w",
                    font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                    text_color=COLORS["text_secondary"]).pack(side="left")
        self.folder_entry = ModernEntry(folder_row, placeholder="Tên folder", width=350)
        self.folder_entry.pack(side="left", fill="x", expand=True)

        # Start URL
        url_row = ctk.CTkFrame(basic_frame, fg_color="transparent")
        url_row.pack(fill="x", padx=15, pady=(3, 12))
        ctk.CTkLabel(url_row, text="Start URL:", width=120, anchor="w",
                    font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                    text_color=COLORS["text_secondary"]).pack(side="left")
        self.url_entry = ModernEntry(url_row, placeholder="https://facebook.com", width=350)
        self.url_entry.pack(side="left", fill="x", expand=True)

        # ===== SYSTEM CONFIG =====
        sys_frame = ctk.CTkFrame(scroll, fg_color=COLORS["bg_card"], corner_radius=12)
        sys_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            sys_frame,
            text="💻 CẤU HÌNH HỆ THỐNG",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            text_color=COLORS["cyan"]
        ).pack(anchor="w", padx=15, pady=(12, 8))

        # OS
        os_row = ctk.CTkFrame(sys_frame, fg_color="transparent")
        os_row.pack(fill="x", padx=15, pady=3)
        ctk.CTkLabel(os_row, text="Hệ điều hành:", width=120, anchor="w",
                    font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                    text_color=COLORS["text_secondary"]).pack(side="left")
        self.os_var = ctk.StringVar(value="win")
        self.os_menu = ctk.CTkOptionMenu(
            os_row, variable=self.os_var,
            values=["win", "mac", "linux", "android", "ios"],
            fg_color=COLORS["bg_input"], button_color=COLORS["cyan"],
            width=150, command=self._on_os_change
        )
        self.os_menu.pack(side="left")

        # OS Version
        ver_row = ctk.CTkFrame(sys_frame, fg_color="transparent")
        ver_row.pack(fill="x", padx=15, pady=3)
        ctk.CTkLabel(ver_row, text="Phiên bản OS:", width=120, anchor="w",
                    font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                    text_color=COLORS["text_secondary"]).pack(side="left")
        self.os_version_var = ctk.StringVar(value="11")

        self.os_versions = {
            "win": ["11", "10"],
            "mac": ["14.3.0", "14.2.1", "14.2.0", "14.1.2", "14.1.1", "14.1.0", "14.0.0", "13.6.2", "13.6.1"],
            "linux": ["ubuntu_24.04", "linux_x86_64", "fedora", "kali_linux"],
            "android": ["15", "14", "13", "12", "11", "10"],
            "ios": ["18.0", "17.6", "17.5", "17.4.1", "17.4", "17.3.1"]
        }

        self.os_version_menu = ctk.CTkOptionMenu(
            ver_row, variable=self.os_version_var,
            values=self.os_versions["win"],
            fg_color=COLORS["bg_input"], button_color=COLORS["cyan"],
            width=150
        )
        self.os_version_menu.pack(side="left")

        # Browser
        browser_row = ctk.CTkFrame(sys_frame, fg_color="transparent")
        browser_row.pack(fill="x", padx=15, pady=3)
        ctk.CTkLabel(browser_row, text="Trình duyệt:", width=120, anchor="w",
                    font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                    text_color=COLORS["text_secondary"]).pack(side="left")
        self.browser_var = ctk.StringVar(value="chrome")
        self.browser_menu = ctk.CTkOptionMenu(
            browser_row, variable=self.browser_var,
            values=["chrome", "edge", "opera", "brave"],
            fg_color=COLORS["bg_input"], button_color=COLORS["cyan"],
            width=150, command=self._on_browser_change
        )
        self.browser_menu.pack(side="left")

        # Browser Version
        bver_row = ctk.CTkFrame(sys_frame, fg_color="transparent")
        bver_row.pack(fill="x", padx=15, pady=3)
        ctk.CTkLabel(bver_row, text="Version Browser:", width=120, anchor="w",
                    font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                    text_color=COLORS["text_secondary"]).pack(side="left")
        self.browser_version_var = ctk.StringVar(value="143")

        self.browser_versions = {
            "chrome": ["143", "142", "141", "140", "139", "138", "137", "136"],
            "edge": ["131", "130", "129", "128", "127", "126"],
            "opera": ["115", "114", "113", "112", "111"],
            "brave": ["1.73", "1.72", "1.71", "1.70", "1.69"]
        }

        self.browser_version_menu = ctk.CTkOptionMenu(
            bver_row, variable=self.browser_version_var,
            values=self.browser_versions["chrome"],
            fg_color=COLORS["bg_input"], button_color=COLORS["cyan"],
            width=150
        )
        self.browser_version_menu.pack(side="left")

        # Resolution
        res_row = ctk.CTkFrame(sys_frame, fg_color="transparent")
        res_row.pack(fill="x", padx=15, pady=3)
        ctk.CTkLabel(res_row, text="Độ phân giải:", width=120, anchor="w",
                    font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                    text_color=COLORS["text_secondary"]).pack(side="left")
        self.resolution_var = ctk.StringVar(value="1280x800")
        self.resolution_menu = ctk.CTkOptionMenu(
            res_row, variable=self.resolution_var,
            values=["1280x800", "1366x768", "1440x900", "1920x1080", "2560x1440"],
            fg_color=COLORS["bg_input"], button_color=COLORS["cyan"],
            width=150
        )
        self.resolution_menu.pack(side="left")

        # Language
        lang_row = ctk.CTkFrame(sys_frame, fg_color="transparent")
        lang_row.pack(fill="x", padx=15, pady=(3, 12))
        ctk.CTkLabel(lang_row, text="Ngôn ngữ:", width=120, anchor="w",
                    font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                    text_color=COLORS["text_secondary"]).pack(side="left")
        self.language_var = ctk.StringVar(value="vi-VN")
        self.language_menu = ctk.CTkOptionMenu(
            lang_row, variable=self.language_var,
            values=["vi-VN", "en-US", "en-GB", "ja-JP", "ko-KR", "zh-CN"],
            fg_color=COLORS["bg_input"], button_color=COLORS["cyan"],
            width=150
        )
        self.language_menu.pack(side="left")

        # ===== FINGERPRINT =====
        fp_frame = ctk.CTkFrame(scroll, fg_color=COLORS["bg_card"], corner_radius=12)
        fp_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            fp_frame,
            text="🔒 FINGERPRINT PROTECTION",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            text_color=COLORS["cyan"]
        ).pack(anchor="w", padx=15, pady=(12, 8))

        fp_grid = ctk.CTkFrame(fp_frame, fg_color="transparent")
        fp_grid.pack(fill="x", padx=15, pady=(0, 12))

        self.canvas_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(fp_grid, text="Canvas", variable=self.canvas_var,
                       fg_color=COLORS["success"], hover_color=COLORS["success_hover"],
                       font=ctk.CTkFont(family=FONT_FAMILY, size=12)).pack(side="left", padx=10)

        self.webgl_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(fp_grid, text="WebGL", variable=self.webgl_var,
                       fg_color=COLORS["success"], hover_color=COLORS["success_hover"],
                       font=ctk.CTkFont(family=FONT_FAMILY, size=12)).pack(side="left", padx=10)

        self.audio_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(fp_grid, text="Audio", variable=self.audio_var,
                       fg_color=COLORS["success"], hover_color=COLORS["success_hover"],
                       font=ctk.CTkFont(family=FONT_FAMILY, size=12)).pack(side="left", padx=10)

        self.font_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(fp_grid, text="Font", variable=self.font_var,
                       fg_color=COLORS["success"], hover_color=COLORS["success_hover"],
                       font=ctk.CTkFont(family=FONT_FAMILY, size=12)).pack(side="left", padx=10)

        # ===== PROXY =====
        proxy_frame = ctk.CTkFrame(scroll, fg_color=COLORS["bg_card"], corner_radius=12)
        proxy_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            proxy_frame,
            text="🌐 PROXY (TÙY CHỌN)",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            text_color=COLORS["cyan"]
        ).pack(anchor="w", padx=15, pady=(12, 5))

        ctk.CTkLabel(
            proxy_frame,
            text="Format: TYPE|IP|PORT|USER|PASS",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10),
            text_color=COLORS["text_muted"]
        ).pack(anchor="w", padx=15)

        self.proxy_entry = ModernEntry(proxy_frame, placeholder="HTTP|1.1.1.1|8080|user|pass", width=530)
        self.proxy_entry.pack(padx=15, pady=(5, 12))

        # ===== BUTTONS =====
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=15)

        CyberButton(
            btn_frame,
            text="TẠO PROFILE",
            icon="✓",
            variant="success",
            command=self._create,
            width=150
        ).pack(side="left", padx=5)

        CyberButton(
            btn_frame,
            text="HỦY",
            variant="secondary",
            command=self.destroy,
            width=100
        ).pack(side="left", padx=5)

    def _on_os_change(self, selected_os):
        """Cập nhật khi đổi OS"""
        versions = self.os_versions.get(selected_os, ["10"])
        self.os_version_menu.configure(values=versions)
        self.os_version_var.set(versions[0])

        if selected_os in ["android", "ios"]:
            if selected_os == "ios":
                self.browser_menu.configure(values=["safari"])
                self.browser_var.set("safari")
                self.browser_version_menu.configure(values=["18", "17", "16", "15"])
                self.browser_version_var.set("18")
            else:
                self.browser_menu.configure(values=["chrome"])
                self.browser_var.set("chrome")
                self.browser_version_menu.configure(values=self.browser_versions["chrome"])
                self.browser_version_var.set(self.browser_versions["chrome"][0])

            mobile_resolutions = ["390x844", "393x873", "414x896", "428x926", "375x812"]
            self.resolution_menu.configure(values=mobile_resolutions)
            self.resolution_var.set(mobile_resolutions[0])
        else:
            self.browser_menu.configure(values=["chrome", "edge", "opera", "brave"])
            self.browser_var.set("chrome")
            self.browser_version_menu.configure(values=self.browser_versions["chrome"])
            self.browser_version_var.set(self.browser_versions["chrome"][0])

            desktop_resolutions = ["1920x1080", "1440x900", "1366x768", "1280x800", "2560x1440"]
            self.resolution_menu.configure(values=desktop_resolutions)
            self.resolution_var.set(desktop_resolutions[0])

    def _on_browser_change(self, selected_browser):
        """Cập nhật khi đổi browser"""
        versions = self.browser_versions.get(selected_browser, ["143"])
        self.browser_version_menu.configure(values=versions)
        self.browser_version_var.set(versions[0])

    def _create(self):
        name = self.name_entry.get().strip()
        if not name:
            self.name_entry.configure(border_color=COLORS["error"])
            return

        os_type = self.os_var.get()

        self.result = {
            "name": name,
            "folder_name": self.folder_entry.get().strip() or None,
            "StartURL": self.url_entry.get().strip() or None,
            "os": os_type,
            "osVersion": self.os_version_var.get(),
            "browser": self.browser_var.get(),
            "browserVersion": self.browser_version_var.get(),
            "resolution": self.resolution_var.get(),
            "language": self.language_var.get(),
            "canvas": self.canvas_var.get(),
            "webGLImage": "true" if self.webgl_var.get() else "false",
            "audioContext": "true" if self.audio_var.get() else "false",
            "noiseFont": "true" if self.font_var.get() else "false",
            "proxy": self.proxy_entry.get().strip() or None,
            "command": f"--lang={self.language_var.get().split('-')[0]}"
        }

        if os_type == "ios":
            self.result["device_type"] = "iphone"
        elif os_type == "android":
            self.result["device_type"] = "phone"

        self.destroy()
