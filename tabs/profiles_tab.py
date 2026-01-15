"""
Tab Quản lý Profiles - Danh sách và quản lý các profile Facebook
"""
import customtkinter as ctk
from typing import List, Dict
import threading
from config import COLORS
from widgets import ModernCard, ModernButton, ModernEntry, ProfileCard, SearchBar
from api_service import api
from database import get_profiles as db_get_profiles, sync_profiles, update_profile_local


class ProfilesTab(ctk.CTkFrame):
    """Tab quản lý danh sách profiles"""
    
    def __init__(self, master, status_callback=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.status_callback = status_callback
        self.profiles: List[Dict] = []
        self.selected_profiles: List[Dict] = []
        self.profile_cards: List[ProfileCard] = []
        self.folders: List[Dict] = []  # Danh sách folders từ API
        self.folder_id_to_name: Dict[int, str] = {}  # Map folder_id -> name
        self._auto_refresh_job = None  # Job ID cho auto-refresh
        self._is_polling = False  # Tránh chồng chéo polling
        
        self._create_ui()
        self._load_folders()  # Load folders trước
        self._load_profiles()
        self._start_auto_refresh()  # Bắt đầu auto-refresh
    
    def _start_auto_refresh(self):
        """Bắt đầu auto-refresh running status mỗi 5 giây"""
        self._auto_refresh_silent()
    
    def _safe_after(self, delay, callback):
        """Thread-safe wrapper cho self.after"""
        try:
            if self.winfo_exists():
                self.after(delay, callback)
        except (RuntimeError, Exception):
            pass  # Widget destroyed hoặc lỗi khác
    
    def _auto_refresh_silent(self):
        """Auto refresh running status không hiện status message"""
        if self._is_polling:
            # Đặt lịch polling tiếp theo
            self._auto_refresh_job = self.after(5000, self._auto_refresh_silent)
            return
            
        self._is_polling = True
        
        def fetch():
            try:
                running_uuids = api.get_running_profiles(is_local=True)
                self._safe_after(0, lambda: self._on_auto_refresh_complete(running_uuids))
            except Exception as e:
                self._safe_after(0, lambda: self._on_auto_refresh_error())
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def _on_auto_refresh_complete(self, running_uuids: List[str]):
        """Xử lý kết quả auto-refresh - cập nhật silent"""
        self._is_polling = False
        
        # Cập nhật check_open trong memory và UI
        changed = False
        for profile in self.profiles:
            uuid = profile.get('uuid')
            new_status = 1 if uuid in running_uuids else 0
            if profile.get('check_open') != new_status:
                profile['check_open'] = new_status
                update_profile_local(uuid, {'check_open': new_status})
                self._update_card_status(uuid, new_status)
                changed = True
        
        if changed:
            self._update_stats()
        
        # Đặt lịch polling tiếp theo (5 giây)
        self._auto_refresh_job = self.after(5000, self._auto_refresh_silent)
    
    def _on_auto_refresh_error(self):
        """Xử lý lỗi auto-refresh"""
        self._is_polling = False
        # Vẫn tiếp tục polling dù có lỗi
        self._auto_refresh_job = self.after(5000, self._auto_refresh_silent)
    
    def destroy(self):
        """Cleanup khi destroy widget"""
        if self._auto_refresh_job:
            self.after_cancel(self._auto_refresh_job)
        super().destroy()
    
    def _create_ui(self):
        # ========== HEADER ==========
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 15))
        
        # Title
        ctk.CTkLabel(
            header_frame,
            text="📋 Quản lý Profiles",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left")
        
        # Header buttons frame
        header_btns = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_btns.pack(side="right")
        
        # Create profile button
        ModernButton(
            header_btns,
            text="Tạo Profile",
            icon="➕",
            variant="success",
            command=self._show_create_dialog,
            width=130
        ).pack(side="left", padx=5)
        
        # Sync button
        ModernButton(
            header_btns,
            text="Đồng bộ",
            icon="☁️",
            variant="primary",
            command=self._sync_profiles,
            width=120
        ).pack(side="left", padx=5)
        
        # Refresh button - chỉ cập nhật trạng thái running từ API
        ModernButton(
            header_btns,
            text="Làm mới",
            icon="🔄",
            variant="secondary",
            command=self._refresh_running_status,
            width=120
        ).pack(side="left", padx=5)
        
        # ========== TOOLBAR ==========
        toolbar = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=12, height=60)
        toolbar.pack(fill="x", padx=20, pady=(0, 15))
        toolbar.pack_propagate(False)
        
        toolbar_inner = ctk.CTkFrame(toolbar, fg_color="transparent")
        toolbar_inner.pack(expand=True, fill="both", padx=15, pady=10)
        
        # Search
        self.search_bar = SearchBar(
            toolbar_inner,
            placeholder="Tìm kiếm profile...",
            on_search=self._search_profiles
        )
        self.search_bar.pack(side="left")
        
        # Filter buttons
        filter_frame = ctk.CTkFrame(toolbar_inner, fg_color="transparent")
        filter_frame.pack(side="left", padx=30)
        
        self.filter_var = ctk.StringVar(value="all")
        
        ctk.CTkRadioButton(
            filter_frame,
            text="Tất cả",
            variable=self.filter_var,
            value="all",
            fg_color=COLORS["accent"],
            command=self._filter_profiles
        ).pack(side="left", padx=10)
        
        ctk.CTkRadioButton(
            filter_frame,
            text="Đang chạy",
            variable=self.filter_var,
            value="running",
            fg_color=COLORS["success"],
            command=self._filter_profiles
        ).pack(side="left", padx=10)
        
        ctk.CTkRadioButton(
            filter_frame,
            text="Đã dừng",
            variable=self.filter_var,
            value="stopped",
            fg_color=COLORS["text_secondary"],
            command=self._filter_profiles
        ).pack(side="left", padx=10)
        
        # Folder filter
        folder_frame = ctk.CTkFrame(toolbar_inner, fg_color="transparent")
        folder_frame.pack(side="left", padx=20)
        
        ctk.CTkLabel(
            folder_frame,
            text="📁",
            font=ctk.CTkFont(size=14)
        ).pack(side="left", padx=(0, 5))
        
        self.folder_var = ctk.StringVar(value="Tất cả thư mục")
        self.folder_menu = ctk.CTkOptionMenu(
            folder_frame,
            variable=self.folder_var,
            values=["Tất cả thư mục"],
            fg_color=COLORS["bg_card"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            dropdown_fg_color=COLORS["bg_card"],
            dropdown_hover_color=COLORS["border"],
            width=180,
            command=self._filter_by_folder
        )
        self.folder_menu.pack(side="left")
        
        # Bulk actions
        bulk_frame = ctk.CTkFrame(toolbar_inner, fg_color="transparent")
        bulk_frame.pack(side="right")
        
        ModernButton(
            bulk_frame,
            text="Mở tất cả",
            icon="▶",
            variant="success",
            command=self._open_selected,
            width=110
        ).pack(side="left", padx=3)
        
        ModernButton(
            bulk_frame,
            text="Đóng tất cả",
            icon="■",
            variant="danger",
            command=self._close_selected,
            width=110
        ).pack(side="left", padx=3)
        
        ModernButton(
            bulk_frame,
            text="Xóa",
            icon="🗑️",
            variant="danger",
            command=self._delete_selected,
            width=80
        ).pack(side="left", padx=3)
        
        # ========== STATS BAR ==========
        stats_bar = ctk.CTkFrame(self, fg_color="transparent")
        stats_bar.pack(fill="x", padx=20, pady=(0, 10))
        
        self.total_label = ctk.CTkLabel(
            stats_bar,
            text="Tổng: 0 profiles",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_secondary"]
        )
        self.total_label.pack(side="left")
        
        self.selected_label = ctk.CTkLabel(
            stats_bar,
            text="Đã chọn: 0",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["accent"]
        )
        self.selected_label.pack(side="left", padx=20)
        
        self.running_label = ctk.CTkLabel(
            stats_bar,
            text="● Đang chạy: 0",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["success"]
        )
        self.running_label.pack(side="left")
        
        # ========== PROFILES LIST ==========
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["accent"]
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Loading indicator
        self.loading_label = ctk.CTkLabel(
            self.scroll_frame,
            text="⏳ Đang tải danh sách profiles...",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text_secondary"]
        )
        self.loading_label.pack(pady=50)
    
    def _load_profiles(self):
        """Load danh sách profiles từ LOCAL DATABASE và check running status từ API"""
        # Load từ local database trước
        self.profiles = db_get_profiles()
        
        if self.profiles:
            # Apply folder names từ mapping (nếu folders đã load)
            self._apply_folder_names_to_profiles()
            self._render_profiles(self.profiles)
            self._update_stats()
            
            # Tự động check running status từ API để cập nhật trạng thái thực tế
            self._refresh_running_status()
        else:
            # Nếu chưa có data local, tự động sync lần đầu
            self._sync_profiles()
    
    def _sync_profiles(self):
        """Đồng bộ profiles từ Hidemium API vào local database"""
        self._set_status("Đang đồng bộ profiles từ Hidemium...", "info")
        self.loading_label.configure(text="⏳ Đang đồng bộ từ Hidemium...")
        self.loading_label.pack(pady=50)
        
        # Clear existing cards
        for card in self.profile_cards:
            card.destroy()
        self.profile_cards.clear()
        
        def fetch():
            # Lấy profiles và running status song song
            profiles_result = api.get_profiles(limit=100, is_local=True)
            running_uuids = api.get_running_profiles(is_local=True)
            self._safe_after(0, lambda: self._on_sync_complete(profiles_result, running_uuids))
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def _on_sync_complete(self, result, running_uuids: List[str] = None):
        """Xử lý kết quả sync profiles từ API"""
        self.loading_label.pack_forget()
        running_uuids = running_uuids or []
        
        if isinstance(result, list) and result:
            # Set check_open dựa trên running_uuids từ API
            for profile in result:
                uuid = profile.get('uuid')
                profile['check_open'] = 1 if uuid in running_uuids else 0
            
            # Lưu vào local database
            sync_profiles(result)
            self.profiles = result
            # Apply folder names sau khi sync
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
        """Chỉ cập nhật trạng thái running từ API mà không reload toàn bộ"""
        self._set_status("Đang kiểm tra trạng thái profiles...", "info")
        
        def fetch():
            running_uuids = api.get_running_profiles(is_local=True)
            self._safe_after(0, lambda: self._on_running_status_received(running_uuids))
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def _on_running_status_received(self, running_uuids: List[str]):
        """Cập nhật UI sau khi nhận running status"""
        # Cập nhật check_open trong memory và database
        for profile in self.profiles:
            uuid = profile.get('uuid')
            new_status = 1 if uuid in running_uuids else 0
            if profile.get('check_open') != new_status:
                profile['check_open'] = new_status
                update_profile_local(uuid, {'check_open': new_status})
                # Cập nhật card UI
                self._update_card_status(uuid, new_status)
        
        self._update_stats()
        running_count = len(running_uuids)
        self._set_status(f"Đã cập nhật: {running_count} profile đang chạy", "success")
    
    def _render_profiles(self, profiles: List[Dict]):
        """Render danh sách profiles"""
        # Clear existing
        for card in self.profile_cards:
            card.destroy()
        self.profile_cards.clear()
        
        if not profiles:
            self.loading_label.configure(text="📭 Không có profile nào")
            self.loading_label.pack(pady=50)
            return
        
        # Create grid layout
        for i, profile in enumerate(profiles):
            card = ProfileCard(
                self.scroll_frame,
                profile_data=profile,
                on_toggle=self._toggle_profile,
                on_edit=self._edit_profile,
                on_select=self._on_profile_select
            )
            card.pack(fill="x", pady=5)
            self.profile_cards.append(card)
    
    def _update_stats(self):
        """Cập nhật thống kê"""
        total = len(self.profiles)
        selected = len(self.selected_profiles)
        # Chỉ đếm running khi check_open == 1 (đang thực sự mở browser)
        running = sum(1 for p in self.profiles if p.get('check_open') == 1)
        
        self.total_label.configure(text=f"Tổng: {total} profiles")
        self.selected_label.configure(text=f"Đã chọn: {selected}")
        self.running_label.configure(text=f"● Đang chạy: {running}")
        
        # Cập nhật folder filter
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
    
    def _filter_profiles(self):
        """Lọc profiles theo status"""
        filter_type = self.filter_var.get()
        
        if filter_type == "all":
            filtered = self.profiles
        elif filter_type == "running":
            filtered = [p for p in self.profiles if p.get('check_open') == 1]
        else:
            filtered = [p for p in self.profiles if p.get('check_open') != 1]
        
        # Apply folder filter as well
        folder_filter = self.folder_var.get()
        if folder_filter != "Tất cả thư mục":
            # Tìm folder_id từ folder_name
            target_folder_id = None
            for fid, fname in self.folder_id_to_name.items():
                if fname == folder_filter:
                    target_folder_id = fid
                    break
            if target_folder_id is not None:
                filtered = [p for p in filtered if p.get('folder_id') == target_folder_id]
        
        self._render_profiles(filtered)
    
    def _filter_by_folder(self, folder_name: str):
        """Lọc profiles theo thư mục"""
        if folder_name == "Tất cả thư mục":
            filtered = self.profiles
        else:
            # Tìm folder_id từ folder_name
            target_folder_id = None
            for fid, fname in self.folder_id_to_name.items():
                if fname == folder_name:
                    target_folder_id = fid
                    break
            
            if target_folder_id is not None:
                filtered = [p for p in self.profiles if p.get('folder_id') == target_folder_id]
            else:
                # Fallback: filter by folder_name nếu có
                filtered = [p for p in self.profiles if p.get('folder_name', '') == folder_name]
        
        # Also apply status filter
        filter_type = self.filter_var.get()
        if filter_type == "running":
            filtered = [p for p in filtered if p.get('check_open') == 1]
        elif filter_type == "stopped":
            filtered = [p for p in filtered if p.get('check_open') != 1]
        
        self._render_profiles(filtered)
    
    def _load_folders(self):
        """Load danh sách folders từ API"""
        def fetch():
            folders = api.get_folders(is_local=True)
            self._safe_after(0, lambda: self._on_folders_loaded(folders))
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def _on_folders_loaded(self, folders: List):
        """Xử lý khi load folders xong"""
        self.folders = folders if folders else []
        
        # Tạo mapping folder_id -> name
        self.folder_id_to_name = {}
        for folder in self.folders:
            fid = folder.get('id') or folder.get('folder_id')
            fname = folder.get('name') or folder.get('folder_name')
            if fid is not None and fname:
                self.folder_id_to_name[fid] = fname
        
        # Cập nhật folder_name cho các profiles đã load
        self._apply_folder_names_to_profiles()
        self._update_folder_filter()
    
    def _apply_folder_names_to_profiles(self):
        """Áp dụng folder_name cho profiles dựa trên folder_id"""
        for p in self.profiles:
            fid = p.get('folder_id')
            if fid and fid in self.folder_id_to_name:
                p['folder_name'] = self.folder_id_to_name[fid]
    
    def _update_folder_filter(self):
        """Cập nhật danh sách folders trong dropdown từ API"""
        folder_list = ["Tất cả thư mục"]
        
        # Thêm folders từ API
        for folder in self.folders:
            name = folder.get('name') or folder.get('folder_name')
            if name:
                folder_list.append(name)
        
        # Fallback: lấy folder_name từ profiles nếu API không có
        if len(folder_list) == 1:
            folder_names = set()
            for p in self.profiles:
                folder = p.get('folder_name')
                if folder:
                    folder_names.add(folder)
            folder_list.extend(sorted(folder_names))
        
        self.folder_menu.configure(values=folder_list)
    
    def _on_profile_select(self, profile: Dict, selected: bool):
        """Xử lý khi chọn/bỏ chọn profile"""
        if selected:
            if profile not in self.selected_profiles:
                self.selected_profiles.append(profile)
        else:
            if profile in self.selected_profiles:
                self.selected_profiles.remove(profile)
        self._update_stats()
    
    def _toggle_profile(self, profile: Dict, open_browser: bool):
        """Toggle mở/đóng browser cho profile"""
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
        """Xử lý kết quả toggle - cập nhật UI local mà không reload"""
        action = "mở" if was_opening else "đóng"
        uuid = profile.get('uuid')
        
        # Check success based on API response format:
        # Open success: {"status": "successfully", ...}
        # Close success: {"message": "Profile closed", ...}
        # Close fail: {"message": "Close profile fail", ...}
        is_success = False
        if was_opening:
            is_success = result.get('status') == 'successfully'
        else:
            # Close trả về message thay vì status
            message = result.get('message', '')
            is_success = 'closed' in message.lower() or message == 'Profile closed'
        
        if is_success:
            self._set_status(f"Đã {action} profile {profile.get('name')} thành công", "success")
            
            # Cập nhật trạng thái local trong memory và database
            new_check_open = 1 if was_opening else 0
            for i, p in enumerate(self.profiles):
                if p.get('uuid') == uuid:
                    self.profiles[i]['check_open'] = new_check_open
                    break
            
            # Lưu vào database
            update_profile_local(uuid, {'check_open': new_check_open})
            
            # Cập nhật card UI trực tiếp mà không reload
            self._update_card_status(uuid, new_check_open)
            self._update_stats()
        else:
            error_msg = result.get('message') or result.get('title') or 'Lỗi không xác định'
            self._set_status(f"Lỗi {action}: {error_msg}", "error")
    
    def _update_card_status(self, uuid: str, check_open: int):
        """Cập nhật trạng thái card mà không reload toàn bộ"""
        for card in self.profile_cards:
            if card.profile_data.get('uuid') == uuid:
                card.profile_data['check_open'] = check_open
                card.is_running = check_open == 1
                
                # Cập nhật button
                if card.is_running:
                    card.toggle_btn.configure(
                        text="■ Đóng",
                        fg_color=COLORS["error"],
                        hover_color="#ff4757"
                    )
                    card.status_label.configure(
                        text="● RUNNING",
                        text_color=COLORS["success"]
                    )
                else:
                    card.toggle_btn.configure(
                        text="▶ Mở",
                        fg_color=COLORS["success"],
                        hover_color="#00f5b5"
                    )
                    card.status_label.configure(
                        text="● STOPPED",
                        text_color=COLORS["text_secondary"]
                    )
                break
    
    def _edit_profile(self, profile: Dict):
        """Mở dialog chỉnh sửa profile"""
        dialog = EditProfileDialog(self, profile)
        dialog.grab_set()
    
    def _open_selected(self):
        """Mở tất cả profiles đã chọn"""
        if not self.selected_profiles:
            self._set_status("Chưa chọn profile nào", "warning")
            return
        
        for profile in self.selected_profiles:
            self._toggle_profile(profile, True)
    
    def _close_selected(self):
        """Đóng tất cả profiles đã chọn"""
        if not self.selected_profiles:
            self._set_status("Chưa chọn profile nào", "warning")
            return
        
        for profile in self.selected_profiles:
            self._toggle_profile(profile, False)
    
    def _delete_selected(self):
        """Xóa các profiles đã chọn"""
        if not self.selected_profiles:
            self._set_status("Chưa chọn profile nào", "warning")
            return
        
        uuids = [p.get('uuid') for p in self.selected_profiles]
        self._set_status(f"Đang xóa {len(uuids)} profiles...", "info")
        
        def do_delete():
            result = api.delete_profiles(uuids)
            self._safe_after(0, lambda: self._on_delete_complete(result))
        
        threading.Thread(target=do_delete, daemon=True).start()
    
    def _on_action_complete(self, result, action: str):
        """Xử lý kết quả action"""
        if result.get('success') or result.get('type') == 'success':
            self._set_status(f"Đã {action} thành công", "success")
            self._load_profiles()
        else:
            self._set_status(f"Lỗi {action}: {result.get('title', 'Unknown')}", "error")
    
    def _on_delete_complete(self, result):
        """Xử lý kết quả xóa"""
        if result.get('type') == 'success':
            self._set_status("Đã xóa thành công", "success")
            self.selected_profiles.clear()
            self._load_profiles()
        else:
            self._set_status(f"Lỗi xóa: {result.get('title', 'Unknown')}", "error")
    
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
        print(f"Create result: {result}")  # Debug
        if result and (result.get('uuid') or result.get('type') == 'success'):
            self._set_status("Đã tạo profile mới thành công!", "success")
            # Refresh folders để hiện folder mới (nếu có)
            self._load_folders()
            # Sync lại từ API để lấy profile mới
            self._sync_profiles()
        else:
            # Chi tiết lỗi hơn
            error_msg = ''
            if result:
                error_msg = result.get('title') or result.get('message') or result.get('error') or str(result)
            else:
                error_msg = 'Không thể tạo profile - không có response'
            self._set_status(f"Lỗi: {error_msg}", "error")
            print(f"Create error: {result}")  # Debug


class CreateProfileDialog(ctk.CTkToplevel):
    """Dialog tạo profile mới - UX cải tiến"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.result = None
        
        self.title("Tạo Profile Mới")
        self.geometry("600x750")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg_dark"])
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        self._create_ui()
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 600) // 2
        y = (self.winfo_screenheight() - 750) // 2
        self.geometry(f"+{x}+{y}")
    
    def _create_ui(self):
        # Title
        ctk.CTkLabel(
            self,
            text="➕ Tạo Profile Mới",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(pady=(20, 15))
        
        # Scrollable form
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", height=580)
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        # ===== BASIC INFO =====
        basic_frame = ctk.CTkFrame(scroll, fg_color=COLORS["bg_secondary"], corner_radius=12)
        basic_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            basic_frame, text="📝 Thông tin cơ bản",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["accent"]
        ).pack(anchor="w", padx=15, pady=(12, 8))
        
        # Name
        name_row = ctk.CTkFrame(basic_frame, fg_color="transparent")
        name_row.pack(fill="x", padx=15, pady=3)
        ctk.CTkLabel(name_row, text="Tên Profile:", width=120, anchor="w").pack(side="left")
        self.name_entry = ModernEntry(name_row, placeholder="VD: FB Account 01", width=350)
        self.name_entry.pack(side="left", fill="x", expand=True)
        
        # Folder
        folder_row = ctk.CTkFrame(basic_frame, fg_color="transparent")
        folder_row.pack(fill="x", padx=15, pady=3)
        ctk.CTkLabel(folder_row, text="Thư mục:", width=120, anchor="w").pack(side="left")
        self.folder_entry = ModernEntry(folder_row, placeholder="Tên folder (tự tạo nếu chưa có)", width=350)
        self.folder_entry.pack(side="left", fill="x", expand=True)
        
        # Start URL
        url_row = ctk.CTkFrame(basic_frame, fg_color="transparent")
        url_row.pack(fill="x", padx=15, pady=(3, 12))
        ctk.CTkLabel(url_row, text="Start URL:", width=120, anchor="w").pack(side="left")
        self.url_entry = ModernEntry(url_row, placeholder="https://facebook.com", width=350)
        self.url_entry.pack(side="left", fill="x", expand=True)
        
        # ===== SYSTEM CONFIG =====
        sys_frame = ctk.CTkFrame(scroll, fg_color=COLORS["bg_secondary"], corner_radius=12)
        sys_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            sys_frame, text="💻 Cấu hình hệ thống",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["accent"]
        ).pack(anchor="w", padx=15, pady=(12, 8))
        
        # OS
        os_row = ctk.CTkFrame(sys_frame, fg_color="transparent")
        os_row.pack(fill="x", padx=15, pady=3)
        ctk.CTkLabel(os_row, text="Hệ điều hành:", width=120, anchor="w").pack(side="left")
        self.os_var = ctk.StringVar(value="win")
        self.os_menu = ctk.CTkOptionMenu(
            os_row, variable=self.os_var,
            values=["win", "mac", "linux", "android", "ios"],
            fg_color=COLORS["bg_card"], button_color=COLORS["accent"],
            width=150, command=self._on_os_change
        )
        self.os_menu.pack(side="left")
        
        # OS Version - dynamic based on OS selection
        ver_row = ctk.CTkFrame(sys_frame, fg_color="transparent")
        ver_row.pack(fill="x", padx=15, pady=3)
        ctk.CTkLabel(ver_row, text="Phiên bản OS:", width=120, anchor="w").pack(side="left")
        self.os_version_var = ctk.StringVar(value="11")
        
        # OS Versions mapping - CHÍNH XÁC THEO API DOCUMENTATION
        self.os_versions = {
            "win": ["11", "10"],
            "mac": ["14.3.0", "14.2.1", "14.2.0", "14.1.2", "14.1.1", "14.1.0", "14.0.0", "13.6.2", "13.6.1", "13.6.0", "13.5.2", "13.5.1", "13.5.0", "12.7.1", "12.7.0", "12.6.9", "11.7.10", "11.7.9"],
            "linux": ["ubuntu_24.04", "linux_x86_64", "linux_i686", "mint_20", "fedora", "kali_linux", "freebsd", "chromeos_x86_64"],
            "android": ["15", "14", "13", "12", "11", "10", "9", "8.1"],
            "ios": ["18.0", "17.6", "17.5", "17.4.1", "17.4", "17.3.1", "17.3", "17.2.1", "17.2", "17.1.2", "17.1.1", "17.1", "17.0.3", "17.0", "16.7.2", "16.7.1", "16.7", "16.6.1", "16.6", "16.5.1", "16.5", "16.4.1", "16.4", "16.3.1", "16.3", "16.2", "16.1", "16.0", "15.8", "15.7.9", "15.7.8"]
        }
        
        self.os_version_menu = ctk.CTkOptionMenu(
            ver_row, variable=self.os_version_var,
            values=self.os_versions["win"],
            fg_color=COLORS["bg_card"], button_color=COLORS["accent"],
            width=150
        )
        self.os_version_menu.pack(side="left")
        
        # Browser
        browser_row = ctk.CTkFrame(sys_frame, fg_color="transparent")
        browser_row.pack(fill="x", padx=15, pady=3)
        ctk.CTkLabel(browser_row, text="Trình duyệt:", width=120, anchor="w").pack(side="left")
        self.browser_var = ctk.StringVar(value="chrome")
        self.browser_menu = ctk.CTkOptionMenu(
            browser_row, variable=self.browser_var,
            values=["chrome", "edge", "opera", "brave", "chromium"],
            fg_color=COLORS["bg_card"], button_color=COLORS["accent"],
            width=150, command=self._on_browser_change
        )
        self.browser_menu.pack(side="left")
        
        # Browser Version - latest versions
        bver_row = ctk.CTkFrame(sys_frame, fg_color="transparent")
        bver_row.pack(fill="x", padx=15, pady=3)
        ctk.CTkLabel(bver_row, text="Version Browser:", width=120, anchor="w").pack(side="left")
        self.browser_version_var = ctk.StringVar(value="143")
        
        # Browser versions mapping - latest first
        self.browser_versions = {
            "chrome": ["143", "142", "141", "140", "139", "138", "137", "136", "135", "134", "133", "132", "131", "130", "129", "128"],
            "edge": ["131", "130", "129", "128", "127", "126", "125", "124", "123", "122"],
            "opera": ["115", "114", "113", "112", "111", "110", "109", "108"],
            "brave": ["1.73", "1.72", "1.71", "1.70", "1.69", "1.68", "1.67"],
            "chromium": ["143", "142", "141", "140", "139", "138", "137", "136"]
        }
        
        self.browser_version_menu = ctk.CTkOptionMenu(
            bver_row, variable=self.browser_version_var,
            values=self.browser_versions["chrome"],
            fg_color=COLORS["bg_card"], button_color=COLORS["accent"],
            width=150
        )
        self.browser_version_menu.pack(side="left")
        
        # Resolution
        res_row = ctk.CTkFrame(sys_frame, fg_color="transparent")
        res_row.pack(fill="x", padx=15, pady=3)
        ctk.CTkLabel(res_row, text="Độ phân giải:", width=120, anchor="w").pack(side="left")
        self.resolution_var = ctk.StringVar(value="1280x800")
        self.resolution_menu = ctk.CTkOptionMenu(
            res_row, variable=self.resolution_var,
            values=["1280x800", "1366x768", "1440x900", "1920x1080", "2560x1440"],
            fg_color=COLORS["bg_card"], button_color=COLORS["accent"],
            width=150
        )
        self.resolution_menu.pack(side="left")
        
        # Language
        lang_row = ctk.CTkFrame(sys_frame, fg_color="transparent")
        lang_row.pack(fill="x", padx=15, pady=(3, 12))
        ctk.CTkLabel(lang_row, text="Ngôn ngữ:", width=120, anchor="w").pack(side="left")
        self.language_var = ctk.StringVar(value="vi-VN")
        self.language_menu = ctk.CTkOptionMenu(
            lang_row, variable=self.language_var,
            values=["vi-VN", "en-US", "en-GB", "ja-JP", "ko-KR", "zh-CN"],
            fg_color=COLORS["bg_card"], button_color=COLORS["accent"],
            width=150
        )
        self.language_menu.pack(side="left")
        
        # ===== FINGERPRINT =====
        fp_frame = ctk.CTkFrame(scroll, fg_color=COLORS["bg_secondary"], corner_radius=12)
        fp_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            fp_frame, text="🔒 Fingerprint Protection",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["accent"]
        ).pack(anchor="w", padx=15, pady=(12, 8))
        
        fp_grid = ctk.CTkFrame(fp_frame, fg_color="transparent")
        fp_grid.pack(fill="x", padx=15, pady=(0, 12))
        
        self.canvas_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(fp_grid, text="Canvas", variable=self.canvas_var,
                       fg_color=COLORS["success"]).pack(side="left", padx=10)
        
        self.webgl_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(fp_grid, text="WebGL", variable=self.webgl_var,
                       fg_color=COLORS["success"]).pack(side="left", padx=10)
        
        self.audio_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(fp_grid, text="Audio", variable=self.audio_var,
                       fg_color=COLORS["success"]).pack(side="left", padx=10)
        
        self.font_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(fp_grid, text="Font", variable=self.font_var,
                       fg_color=COLORS["success"]).pack(side="left", padx=10)
        
        # ===== PROXY =====
        proxy_frame = ctk.CTkFrame(scroll, fg_color=COLORS["bg_secondary"], corner_radius=12)
        proxy_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            proxy_frame, text="🌐 Proxy (tùy chọn)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["accent"]
        ).pack(anchor="w", padx=15, pady=(12, 5))
        
        ctk.CTkLabel(
            proxy_frame, text="Format: TYPE|IP|PORT|USER|PASS (VD: HTTP|1.1.1.1|8080|user|pass)",
            font=ctk.CTkFont(size=11), text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=15)
        
        self.proxy_entry = ModernEntry(proxy_frame, placeholder="HTTP|IP|Port|User|Pass", width=530)
        self.proxy_entry.pack(padx=15, pady=(5, 12))
        
        # ===== BUTTONS =====
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=15)
        
        ModernButton(
            btn_frame, text="Tạo Profile", icon="✅",
            variant="success", command=self._create, width=150
        ).pack(side="left", padx=5)
        
        ModernButton(
            btn_frame, text="Hủy", icon="❌",
            variant="secondary", command=self.destroy, width=100
        ).pack(side="left", padx=5)
    
    def _on_os_change(self, selected_os):
        """Cập nhật danh sách version khi đổi OS"""
        versions = self.os_versions.get(selected_os, ["10"])
        self.os_version_menu.configure(values=versions)
        self.os_version_var.set(versions[0])  # Set version mới nhất
        
        # Cập nhật browser options theo OS
        if selected_os in ["android", "ios"]:
            # Mobile - iOS chỉ có safari, Android có chrome
            if selected_os == "ios":
                self.browser_menu.configure(values=["safari"])
                self.browser_var.set("safari")
                # Safari không có version riêng
                self.browser_version_menu.configure(values=["18", "17", "16", "15"])
                self.browser_version_var.set("18")
            else:
                self.browser_menu.configure(values=["chrome"])
                self.browser_var.set("chrome")
                self.browser_version_menu.configure(values=self.browser_versions["chrome"])
                self.browser_version_var.set(self.browser_versions["chrome"][0])
            # Resolution mobile
            mobile_resolutions = ["390x844", "393x873", "414x896", "428x926", "375x812", "360x800"]
            self.resolution_menu.configure(values=mobile_resolutions)
            self.resolution_var.set(mobile_resolutions[0])
        else:
            # Desktop
            self.browser_menu.configure(values=["chrome", "edge", "opera", "brave", "chromium"])
            self.browser_var.set("chrome")
            self.browser_version_menu.configure(values=self.browser_versions["chrome"])
            self.browser_version_var.set(self.browser_versions["chrome"][0])
            desktop_resolutions = ["1920x1080", "1440x900", "1366x768", "1280x800", "2560x1440"]
            self.resolution_menu.configure(values=desktop_resolutions)
            self.resolution_var.set(desktop_resolutions[0])
    
    def _on_browser_change(self, selected_browser):
        """Cập nhật version khi đổi browser"""
        versions = self.browser_versions.get(selected_browser, ["143"])
        self.browser_version_menu.configure(values=versions)
        self.browser_version_var.set(versions[0])  # Set version mới nhất
    
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
        
        # Thêm device_type cho mobile
        if os_type == "ios":
            self.result["device_type"] = "iphone"
        elif os_type == "android":
            self.result["device_type"] = "phone"
            
        self.destroy()


class EditProfileDialog(ctk.CTkToplevel):
    """Dialog chỉnh sửa profile"""
    
    def __init__(self, parent, profile: Dict):
        super().__init__(parent)
        
        self.profile = profile
        self.result = None
        
        self.title("Chỉnh sửa Profile")
        self.geometry("500x400")
        self.configure(fg_color=COLORS["bg_dark"])
        
        # Center window
        self.transient(parent)
        
        self._create_ui()
    
    def _create_ui(self):
        # Header
        ctk.CTkLabel(
            self,
            text="✏️ Chỉnh sửa Profile",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(pady=20)
        
        # Form
        form_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=12)
        form_frame.pack(fill="x", padx=30, pady=10)
        
        # Name
        ctk.CTkLabel(
            form_frame,
            text="Tên Profile:",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=20, pady=(15, 5))
        
        self.name_entry = ModernEntry(form_frame, width=400)
        self.name_entry.pack(padx=20, pady=(0, 15))
        self.name_entry.insert(0, self.profile.get('name') or '')
        
        # Note
        ctk.CTkLabel(
            form_frame,
            text="Ghi chú:",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=20, pady=(0, 5))
        
        self.note_entry = ModernEntry(form_frame, width=400)
        self.note_entry.pack(padx=20, pady=(0, 20))
        self.note_entry.insert(0, self.profile.get('note') or '')
        
        # Proxy section
        proxy_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=12)
        proxy_frame.pack(fill="x", padx=30, pady=10)
        
        ctk.CTkLabel(
            proxy_frame,
            text="🌐 Proxy (Type|IP|Port|User|Pass):",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=20, pady=(15, 5))
        
        self.proxy_entry = ModernEntry(proxy_frame, placeholder="HTTP|1.1.1.1|8080|user|pass", width=400)
        self.proxy_entry.pack(padx=20, pady=(0, 20))
        
        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=20)
        
        ModernButton(
            btn_frame,
            text="Lưu",
            icon="💾",
            variant="success",
            command=self._save,
            width=120
        ).pack(side="left", padx=5)
        
        ModernButton(
            btn_frame,
            text="Hủy",
            variant="secondary",
            command=self.destroy,
            width=100
        ).pack(side="left", padx=5)
    
    def _save(self):
        """Lưu thay đổi"""
        uuid = self.profile.get('uuid')
        
        # Update name
        new_name = self.name_entry.get()
        if new_name and new_name != self.profile.get('name'):
            api.update_profile_name(uuid, new_name)
        
        # Update note
        new_note = self.note_entry.get()
        if new_note != self.profile.get('note', ''):
            api.update_profile_note(uuid, new_note)
        
        self.destroy()
