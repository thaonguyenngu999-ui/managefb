"""
Tab Quản Lý Page - Quản lý các Fanpage Facebook
"""
import customtkinter as ctk
from typing import List, Dict, Optional
import threading
import random
import time
from datetime import datetime
from config import COLORS
from widgets import ModernButton, ModernEntry
from db import (
    get_pages, get_pages_for_profiles, save_page, delete_page, delete_pages_bulk,
    update_page_selection, sync_pages, clear_pages, get_pages_count
)
from api_service import api

# Import CDP helper (optional)
try:
    from automation import CDPHelper
    CDP_AVAILABLE = True
except ImportError:
    CDP_AVAILABLE = False


class PagesTab(ctk.CTkFrame):
    """Tab Quản Lý Page - Quản lý các Fanpage Facebook"""

    def __init__(self, master, status_callback=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.status_callback = status_callback
        self.profiles: List[Dict] = []
        self.pages: List[Dict] = []
        self.folders: List[Dict] = []

        # Multi-profile support
        self.selected_profile_uuids: List[str] = []
        self.profile_checkbox_vars: Dict = {}

        # Page selection
        self.page_checkbox_vars: Dict = {}
        self.page_checkbox_widgets: Dict = {}

        # State flags
        self._is_scanning = False
        self._is_creating = False

        self._create_ui()
        self._load_profiles()

    def _create_ui(self):
        """Tạo giao diện"""
        # Main container - 2 columns
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=15, pady=15)

        # ========== LEFT PANEL - Profile Selection ==========
        left_panel = ctk.CTkFrame(main_container, fg_color=COLORS["bg_secondary"], corner_radius=12, width=280)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)

        # Left header
        left_header = ctk.CTkFrame(left_panel, fg_color="transparent")
        left_header.pack(fill="x", padx=15, pady=(15, 10))

        ctk.CTkLabel(
            left_header,
            text="Chọn Profile",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left")

        ModernButton(
            left_header,
            text="",
            icon="🔄",
            variant="secondary",
            command=self._load_profiles,
            width=35
        ).pack(side="right")

        # Folder filter
        folder_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        folder_frame.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(
            folder_frame,
            text="📁 Thư mục:",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        ).pack(side="left")

        self.folder_var = ctk.StringVar(value="-- Tất cả --")
        self.folder_menu = ctk.CTkOptionMenu(
            folder_frame,
            variable=self.folder_var,
            values=["-- Tất cả --"],
            fg_color=COLORS["bg_card"],
            button_color=COLORS["accent"],
            width=150,
            command=self._on_folder_change
        )
        self.folder_menu.pack(side="left", padx=(10, 0))

        # Select all / Deselect all buttons
        select_btns = ctk.CTkFrame(left_panel, fg_color="transparent")
        select_btns.pack(fill="x", padx=15, pady=(0, 5))

        ctk.CTkButton(
            select_btns,
            text="Chọn tất cả",
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["border"],
            width=115,
            height=28,
            corner_radius=5,
            command=self._select_all_profiles
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            select_btns,
            text="Bỏ chọn",
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["border"],
            width=115,
            height=28,
            corner_radius=5,
            command=self._deselect_all_profiles
        ).pack(side="left")

        # Profile list
        self.profile_list = ctk.CTkScrollableFrame(left_panel, fg_color="transparent")
        self.profile_list.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        # Profile stats
        self.profile_stats = ctk.CTkLabel(
            left_panel,
            text="Profiles: 0 | Đã chọn: 0",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"]
        )
        self.profile_stats.pack(pady=(0, 10))

        # ========== RIGHT PANEL - Pages List ==========
        right_panel = ctk.CTkFrame(main_container, fg_color=COLORS["bg_secondary"], corner_radius=12)
        right_panel.pack(side="right", fill="both", expand=True)

        # Right header with action buttons
        right_header = ctk.CTkFrame(right_panel, fg_color="transparent")
        right_header.pack(fill="x", padx=15, pady=(15, 10))

        ctk.CTkLabel(
            right_header,
            text="Danh sách Page",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left")

        # Action buttons
        btn_frame = ctk.CTkFrame(right_header, fg_color="transparent")
        btn_frame.pack(side="right")

        ModernButton(
            btn_frame,
            text="Tạo Page",
            icon="➕",
            variant="success",
            command=self._show_create_page_dialog,
            width=100
        ).pack(side="left", padx=3)

        ModernButton(
            btn_frame,
            text="Scan Page",
            icon="🔍",
            variant="primary",
            command=self._scan_pages,
            width=110
        ).pack(side="left", padx=3)

        ModernButton(
            btn_frame,
            text="Xóa",
            icon="🗑️",
            variant="danger",
            command=self._delete_selected_pages,
            width=80
        ).pack(side="left", padx=3)

        # Search and filter
        filter_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        filter_frame.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(filter_frame, text="🔍", width=20).pack(side="left")
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self._on_search_change)
        self.search_entry = ctk.CTkEntry(
            filter_frame,
            placeholder_text="Tìm kiếm Page...",
            textvariable=self.search_var,
            fg_color=COLORS["bg_card"],
            width=250,
            height=32
        )
        self.search_entry.pack(side="left", padx=5)

        # Select all pages checkbox
        self.select_all_pages_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            filter_frame,
            text="Chọn tất cả",
            variable=self.select_all_pages_var,
            fg_color=COLORS["accent"],
            command=self._toggle_select_all_pages
        ).pack(side="right", padx=10)

        # Page stats
        self.page_stats = ctk.CTkLabel(
            filter_frame,
            text="Tổng: 0 | Đã chọn: 0",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["accent"]
        )
        self.page_stats.pack(side="right", padx=10)

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            right_panel,
            fg_color=COLORS["bg_card"],
            progress_color=COLORS["accent"]
        )
        self.progress_bar.pack(fill="x", padx=15, pady=(0, 10))
        self.progress_bar.set(0)

        # Pages table header
        table_header = ctk.CTkFrame(right_panel, fg_color=COLORS["bg_card"], corner_radius=5, height=35)
        table_header.pack(fill="x", padx=15, pady=(0, 5))
        table_header.pack_propagate(False)

        headers = [("", 30), ("Tên Page", 200), ("Followers", 80), ("Profile", 150), ("Vai trò", 70), ("Ngày tạo", 100)]
        for text, width in headers:
            ctk.CTkLabel(
                table_header,
                text=text,
                width=width,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=COLORS["text_primary"]
            ).pack(side="left", padx=3)

        # Pages list
        self.pages_list = ctk.CTkScrollableFrame(right_panel, fg_color="transparent")
        self.pages_list.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Empty state
        self.empty_label = ctk.CTkLabel(
            self.pages_list,
            text="Chưa có Page nào\nChọn profile và bấm 'Scan Page' để quét",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_secondary"]
        )
        self.empty_label.pack(pady=50)

    def _load_profiles(self):
        """Load danh sách profiles từ Hidemium"""
        def load():
            try:
                result = api.get_profiles()
                if result.get('success'):
                    profiles = result.get('data', [])
                    folders = []
                    folder_set = set()

                    for p in profiles:
                        folder_id = p.get('folder_id')
                        folder_name = p.get('folder_name', 'Không có thư mục')
                        if folder_id and folder_id not in folder_set:
                            folder_set.add(folder_id)
                            folders.append({'id': folder_id, 'name': folder_name})

                    self.after(0, lambda: self._update_profiles(profiles, folders))
                else:
                    self.after(0, lambda: self._set_status("Không thể load profiles", "error"))
            except Exception as e:
                self.after(0, lambda: self._set_status(f"Lỗi: {e}", "error"))

        threading.Thread(target=load, daemon=True).start()

    def _update_profiles(self, profiles: List[Dict], folders: List[Dict]):
        """Cập nhật danh sách profiles"""
        self.profiles = profiles
        self.folders = folders

        # Update folder menu
        folder_names = ["-- Tất cả --"] + [f['name'] for f in folders]
        self.folder_menu.configure(values=folder_names)

        # Render profiles
        self._render_profiles()
        self._set_status(f"Đã load {len(profiles)} profiles", "success")

    def _render_profiles(self, filter_folder: str = None):
        """Render danh sách profiles"""
        # Clear existing
        for widget in self.profile_list.winfo_children():
            widget.destroy()
        self.profile_checkbox_vars.clear()

        # Filter by folder
        profiles_to_show = self.profiles
        if filter_folder and filter_folder != "-- Tất cả --":
            profiles_to_show = [p for p in self.profiles if p.get('folder_name') == filter_folder]

        for profile in profiles_to_show:
            uuid = profile.get('uuid', '')
            name = profile.get('name', 'Unknown')
            status = profile.get('status', 'stopped')

            frame = ctk.CTkFrame(self.profile_list, fg_color=COLORS["bg_card"], corner_radius=8, height=40)
            frame.pack(fill="x", pady=2)
            frame.pack_propagate(False)

            var = ctk.BooleanVar(value=uuid in self.selected_profile_uuids)
            self.profile_checkbox_vars[uuid] = var

            cb = ctk.CTkCheckBox(
                frame,
                text="",
                variable=var,
                fg_color=COLORS["accent"],
                width=20,
                command=lambda u=uuid: self._on_profile_select(u)
            )
            cb.pack(side="left", padx=(10, 5))

            # Status indicator
            status_color = COLORS["success"] if status == "running" else COLORS["text_secondary"]
            ctk.CTkLabel(
                frame,
                text="●",
                font=ctk.CTkFont(size=10),
                text_color=status_color,
                width=15
            ).pack(side="left")

            ctk.CTkLabel(
                frame,
                text=name[:25] + "..." if len(name) > 25 else name,
                font=ctk.CTkFont(size=12),
                text_color=COLORS["text_primary"],
                anchor="w"
            ).pack(side="left", fill="x", expand=True, padx=5)

        self._update_profile_stats()

    def _on_folder_change(self, folder_name: str):
        """Khi thay đổi thư mục"""
        self._render_profiles(folder_name if folder_name != "-- Tất cả --" else None)

    def _on_profile_select(self, uuid: str):
        """Khi chọn/bỏ chọn profile"""
        var = self.profile_checkbox_vars.get(uuid)
        if var:
            if var.get():
                if uuid not in self.selected_profile_uuids:
                    self.selected_profile_uuids.append(uuid)
            else:
                if uuid in self.selected_profile_uuids:
                    self.selected_profile_uuids.remove(uuid)

        self._update_profile_stats()
        self._load_pages_for_selected()

    def _select_all_profiles(self):
        """Chọn tất cả profiles đang hiển thị"""
        for uuid, var in self.profile_checkbox_vars.items():
            var.set(True)
            if uuid not in self.selected_profile_uuids:
                self.selected_profile_uuids.append(uuid)
        self._update_profile_stats()
        self._load_pages_for_selected()

    def _deselect_all_profiles(self):
        """Bỏ chọn tất cả profiles"""
        for uuid, var in self.profile_checkbox_vars.items():
            var.set(False)
        self.selected_profile_uuids.clear()
        self._update_profile_stats()
        self._load_pages_for_selected()

    def _update_profile_stats(self):
        """Cập nhật thống kê profiles"""
        total = len(self.profile_checkbox_vars)
        selected = len(self.selected_profile_uuids)
        self.profile_stats.configure(text=f"Profiles: {total} | Đã chọn: {selected}")

    def _load_pages_for_selected(self):
        """Load pages cho các profiles đã chọn"""
        if not self.selected_profile_uuids:
            self.pages = []
            self._render_pages()
            return

        self.pages = get_pages_for_profiles(self.selected_profile_uuids)
        self._render_pages()

    def _render_pages(self, search_text: str = None):
        """Render danh sách pages"""
        # Clear existing
        for widget in self.pages_list.winfo_children():
            widget.destroy()
        self.page_checkbox_vars.clear()
        self.page_checkbox_widgets.clear()

        # Filter by search
        pages_to_show = self.pages
        if search_text:
            search_lower = search_text.lower()
            pages_to_show = [p for p in self.pages if search_lower in p.get('page_name', '').lower()]

        if not pages_to_show:
            self.empty_label = ctk.CTkLabel(
                self.pages_list,
                text="Chưa có Page nào\nChọn profile và bấm 'Scan Page' để quét",
                font=ctk.CTkFont(size=13),
                text_color=COLORS["text_secondary"]
            )
            self.empty_label.pack(pady=50)
            self._update_page_stats()
            return

        # Get profile name map
        profile_map = {p['uuid']: p.get('name', 'Unknown') for p in self.profiles}

        for page in pages_to_show:
            page_id = page.get('id')
            page_name = page.get('page_name', 'Unknown')
            followers = page.get('follower_count', 0)
            profile_uuid = page.get('profile_uuid', '')
            profile_name = profile_map.get(profile_uuid, 'Unknown')
            role = page.get('role', 'admin')
            created = page.get('created_at', '')[:10] if page.get('created_at') else ''

            frame = ctk.CTkFrame(self.pages_list, fg_color=COLORS["bg_card"], corner_radius=8, height=40)
            frame.pack(fill="x", pady=2)
            frame.pack_propagate(False)

            var = ctk.BooleanVar(value=False)
            self.page_checkbox_vars[page_id] = var

            cb = ctk.CTkCheckBox(
                frame,
                text="",
                variable=var,
                fg_color=COLORS["accent"],
                width=30,
                command=self._update_page_stats
            )
            cb.pack(side="left", padx=(10, 5))
            self.page_checkbox_widgets[page_id] = cb

            # Page name
            ctk.CTkLabel(
                frame,
                text=page_name[:30] + "..." if len(page_name) > 30 else page_name,
                font=ctk.CTkFont(size=12),
                text_color=COLORS["text_primary"],
                width=200,
                anchor="w"
            ).pack(side="left", padx=3)

            # Followers
            followers_text = f"{followers:,}" if followers else "0"
            ctk.CTkLabel(
                frame,
                text=followers_text,
                font=ctk.CTkFont(size=11),
                text_color=COLORS["accent"],
                width=80,
                anchor="w"
            ).pack(side="left", padx=3)

            # Profile name
            ctk.CTkLabel(
                frame,
                text=profile_name[:20] + "..." if len(profile_name) > 20 else profile_name,
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text_secondary"],
                width=150,
                anchor="w"
            ).pack(side="left", padx=3)

            # Role
            role_color = COLORS["success"] if role == "admin" else COLORS["warning"]
            ctk.CTkLabel(
                frame,
                text=role.capitalize(),
                font=ctk.CTkFont(size=11),
                text_color=role_color,
                width=70,
                anchor="w"
            ).pack(side="left", padx=3)

            # Created date
            ctk.CTkLabel(
                frame,
                text=created,
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text_secondary"],
                width=100,
                anchor="w"
            ).pack(side="left", padx=3)

        self._update_page_stats()

    def _on_search_change(self, *args):
        """Khi thay đổi search text"""
        self._render_pages(self.search_var.get())

    def _toggle_select_all_pages(self):
        """Toggle chọn tất cả pages"""
        select_all = self.select_all_pages_var.get()
        for page_id, var in self.page_checkbox_vars.items():
            var.set(select_all)
        self._update_page_stats()

    def _update_page_stats(self):
        """Cập nhật thống kê pages"""
        total = len(self.page_checkbox_vars)
        selected = sum(1 for var in self.page_checkbox_vars.values() if var.get())
        self.page_stats.configure(text=f"Tổng: {total} | Đã chọn: {selected}")

    def _get_selected_page_ids(self) -> List[int]:
        """Lấy danh sách page IDs đã chọn"""
        return [pid for pid, var in self.page_checkbox_vars.items() if var.get()]

    def _scan_pages(self):
        """Scan pages từ các profiles đã chọn"""
        if self._is_scanning:
            self._set_status("Đang scan...", "warning")
            return

        if not self.selected_profile_uuids:
            self._set_status("Vui lòng chọn ít nhất 1 profile", "warning")
            return

        self._is_scanning = True
        self.progress_bar.set(0)

        def scan():
            try:
                total = len(self.selected_profile_uuids)
                scanned_count = 0

                for i, uuid in enumerate(self.selected_profile_uuids):
                    profile = next((p for p in self.profiles if p['uuid'] == uuid), None)
                    if not profile:
                        continue

                    profile_name = profile.get('name', 'Unknown')
                    self.after(0, lambda n=profile_name: self._set_status(f"Đang scan: {n}...", "info"))

                    # Scan pages for this profile
                    pages = self._scan_pages_for_profile(uuid)
                    if pages:
                        sync_pages(uuid, pages)
                        scanned_count += len(pages)

                    # Update progress
                    progress = (i + 1) / total
                    self.after(0, lambda p=progress: self.progress_bar.set(p))

                    # Random delay
                    if i < total - 1:
                        time.sleep(random.uniform(1, 2))

                self.after(0, lambda: self._on_scan_complete(scanned_count))

            except Exception as e:
                self.after(0, lambda: self._set_status(f"Lỗi scan: {e}", "error"))
            finally:
                self._is_scanning = False

        threading.Thread(target=scan, daemon=True).start()

    def _scan_pages_for_profile(self, profile_uuid: str) -> List[Dict]:
        """Scan pages cho 1 profile (placeholder - cần implement với CDP)"""
        # TODO: Implement actual scanning with CDP
        # For now, return empty list
        # Real implementation would:
        # 1. Open browser with profile
        # 2. Navigate to facebook.com/pages
        # 3. Extract page list
        return []

    def _on_scan_complete(self, count: int):
        """Khi scan hoàn tất"""
        self._load_pages_for_selected()
        self._set_status(f"Đã scan được {count} pages", "success")
        self.progress_bar.set(1)

    def _show_create_page_dialog(self):
        """Hiển thị dialog tạo Page mới"""
        if not self.selected_profile_uuids:
            self._set_status("Vui lòng chọn ít nhất 1 profile", "warning")
            return

        dialog = CreatePageDialog(self, self.selected_profile_uuids, self.profiles, self._on_page_created)
        dialog.grab_set()

    def _on_page_created(self, count: int):
        """Khi tạo page hoàn tất"""
        self._load_pages_for_selected()
        self._set_status(f"Đã tạo {count} pages", "success")

    def _delete_selected_pages(self):
        """Xóa các pages đã chọn"""
        selected_ids = self._get_selected_page_ids()
        if not selected_ids:
            self._set_status("Vui lòng chọn ít nhất 1 page để xóa", "warning")
            return

        # Confirm dialog
        confirm = ConfirmDialog(self, f"Xóa {len(selected_ids)} page?", "Hành động này không thể hoàn tác.")
        self.wait_window(confirm)

        if confirm.result:
            deleted = delete_pages_bulk(selected_ids)
            self._load_pages_for_selected()
            self._set_status(f"Đã xóa {deleted} pages", "success")

    def _set_status(self, text: str, status_type: str = "info"):
        """Cập nhật status bar"""
        if self.status_callback:
            self.status_callback(text, status_type)


class CreatePageDialog(ctk.CTkToplevel):
    """Dialog tạo Page mới"""

    def __init__(self, parent, profile_uuids: List[str], profiles: List[Dict], callback):
        super().__init__(parent)

        self.profile_uuids = profile_uuids
        self.profiles = profiles
        self.callback = callback
        self._is_creating = False

        self.title("Tạo Fanpage mới")
        self.geometry("500x400")
        self.configure(fg_color=COLORS["bg_dark"])
        self.transient(parent)

        self._create_ui()

    def _create_ui(self):
        # Header
        ctk.CTkLabel(
            self,
            text="➕ Tạo Fanpage mới",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(pady=(20, 15))

        # Profile info
        profile_count = len(self.profile_uuids)
        ctk.CTkLabel(
            self,
            text=f"Sẽ tạo Page cho {profile_count} profile đã chọn",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["accent"]
        ).pack(pady=(0, 15))

        # Form
        form_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=12)
        form_frame.pack(fill="x", padx=30, pady=10)

        # Page name
        name_row = ctk.CTkFrame(form_frame, fg_color="transparent")
        name_row.pack(fill="x", padx=20, pady=(15, 10))

        ctk.CTkLabel(
            name_row,
            text="Tên Page:",
            width=100,
            anchor="w",
            text_color=COLORS["text_secondary"]
        ).pack(side="left")

        self.name_entry = ctk.CTkEntry(
            name_row,
            fg_color=COLORS["bg_card"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            placeholder_text="Nhập tên Page..."
        )
        self.name_entry.pack(side="left", fill="x", expand=True)

        # Category
        cat_row = ctk.CTkFrame(form_frame, fg_color="transparent")
        cat_row.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            cat_row,
            text="Danh mục:",
            width=100,
            anchor="w",
            text_color=COLORS["text_secondary"]
        ).pack(side="left")

        self.category_var = ctk.StringVar(value="Doanh nghiệp địa phương")
        categories = [
            "Doanh nghiệp địa phương",
            "Công ty",
            "Thương hiệu hoặc sản phẩm",
            "Nghệ sĩ, ban nhạc hoặc nhân vật công chúng",
            "Giải trí",
            "Cộng đồng hoặc trang web"
        ]
        self.category_menu = ctk.CTkOptionMenu(
            cat_row,
            variable=self.category_var,
            values=categories,
            fg_color=COLORS["bg_card"],
            button_color=COLORS["accent"],
            width=280
        )
        self.category_menu.pack(side="left")

        # Description
        desc_row = ctk.CTkFrame(form_frame, fg_color="transparent")
        desc_row.pack(fill="x", padx=20, pady=(10, 15))

        ctk.CTkLabel(
            desc_row,
            text="Mô tả:",
            width=100,
            anchor="w",
            text_color=COLORS["text_secondary"]
        ).pack(side="left", anchor="n")

        self.desc_entry = ctk.CTkTextbox(
            desc_row,
            fg_color=COLORS["bg_card"],
            text_color=COLORS["text_primary"],
            height=60
        )
        self.desc_entry.pack(side="left", fill="x", expand=True)

        # Options
        options_frame = ctk.CTkFrame(self, fg_color="transparent")
        options_frame.pack(fill="x", padx=30, pady=10)

        ctk.CTkLabel(
            options_frame,
            text="Delay giữa các lần tạo (giây):",
            text_color=COLORS["text_secondary"]
        ).pack(side="left")

        self.delay_entry = ctk.CTkEntry(
            options_frame,
            fg_color=COLORS["bg_card"],
            width=60
        )
        self.delay_entry.pack(side="left", padx=10)
        self.delay_entry.insert(0, "5")

        # Progress
        self.progress_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"]
        )
        self.progress_label.pack(pady=5)

        self.progress_bar = ctk.CTkProgressBar(
            self,
            fg_color=COLORS["bg_card"],
            progress_color=COLORS["success"]
        )
        self.progress_bar.pack(fill="x", padx=30, pady=5)
        self.progress_bar.set(0)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=20)

        ctk.CTkButton(
            btn_frame,
            text="Tạo Page",
            fg_color=COLORS["success"],
            hover_color="#00f5b5",
            width=120,
            height=40,
            corner_radius=10,
            command=self._create_pages
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

    def _create_pages(self):
        """Tạo pages cho các profiles đã chọn"""
        if self._is_creating:
            return

        page_name = self.name_entry.get().strip()
        if not page_name:
            self.progress_label.configure(text="Vui lòng nhập tên Page", text_color=COLORS["error"])
            return

        self._is_creating = True
        category = self.category_var.get()
        description = self.desc_entry.get("1.0", "end-1c").strip()

        try:
            delay = int(self.delay_entry.get())
        except ValueError:
            delay = 5

        def create():
            try:
                total = len(self.profile_uuids)
                created_count = 0

                for i, uuid in enumerate(self.profile_uuids):
                    profile = next((p for p in self.profiles if p['uuid'] == uuid), None)
                    if not profile:
                        continue

                    profile_name = profile.get('name', 'Unknown')
                    self.after(0, lambda n=profile_name, idx=i+1, t=total:
                        self.progress_label.configure(text=f"Đang tạo Page cho {n} ({idx}/{t})..."))

                    # Create page (placeholder - needs CDP implementation)
                    success = self._create_page_for_profile(uuid, page_name, category, description)
                    if success:
                        created_count += 1

                    # Update progress
                    progress = (i + 1) / total
                    self.after(0, lambda p=progress: self.progress_bar.set(p))

                    # Delay
                    if i < total - 1:
                        time.sleep(delay + random.uniform(0, 2))

                self.after(0, lambda: self._on_create_complete(created_count))

            except Exception as e:
                self.after(0, lambda: self.progress_label.configure(
                    text=f"Lỗi: {e}", text_color=COLORS["error"]))
            finally:
                self._is_creating = False

        threading.Thread(target=create, daemon=True).start()

    def _create_page_for_profile(self, profile_uuid: str, name: str, category: str, description: str) -> bool:
        """Tạo page cho 1 profile (placeholder)"""
        # TODO: Implement with CDP
        # For now, just save to database as placeholder
        import uuid as uuid_module
        page_data = {
            'profile_uuid': profile_uuid,
            'page_id': str(uuid_module.uuid4())[:8],
            'page_name': name,
            'page_url': '',
            'category': category,
            'follower_count': 0,
            'role': 'admin',
            'note': description
        }
        save_page(page_data)
        return True

    def _on_create_complete(self, count: int):
        """Khi tạo xong"""
        self.progress_label.configure(text=f"Đã tạo {count} pages!", text_color=COLORS["success"])
        self.progress_bar.set(1)
        if self.callback:
            self.callback(count)


class ConfirmDialog(ctk.CTkToplevel):
    """Dialog xác nhận"""

    def __init__(self, parent, title: str, message: str):
        super().__init__(parent)

        self.result = False

        self.title("Xác nhận")
        self.geometry("350x150")
        self.configure(fg_color=COLORS["bg_dark"])
        self.transient(parent)

        ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(pady=(20, 10))

        ctk.CTkLabel(
            self,
            text=message,
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        ).pack(pady=(0, 20))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack()

        ctk.CTkButton(
            btn_frame,
            text="Xác nhận",
            fg_color=COLORS["error"],
            hover_color="#ff6b6b",
            width=100,
            command=self._confirm
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="Hủy",
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["border"],
            width=100,
            command=self.destroy
        ).pack(side="left", padx=5)

    def _confirm(self):
        self.result = True
        self.destroy()
