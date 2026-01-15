"""
Tab Đăng Nhóm - Quét nhóm và đăng bài vào các nhóm Facebook
"""
import customtkinter as ctk
from typing import List, Dict, Optional
import threading
from datetime import datetime
from config import COLORS
from widgets import ModernButton, ModernEntry
from db import (
    get_profiles, get_groups, save_group, delete_group,
    update_group_selection, get_selected_groups, sync_groups, clear_groups,
    get_contents, get_categories, save_post_history
)
from api_service import api


class GroupsTab(ctk.CTkFrame):
    """Tab Đăng Nhóm - Quét và đăng bài vào các nhóm"""

    def __init__(self, master, status_callback=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.status_callback = status_callback
        self.profiles: List[Dict] = []
        self.groups: List[Dict] = []
        self.current_profile_uuid: Optional[str] = None
        self.selected_group_ids: List[int] = []
        self.contents: List[Dict] = []
        self.categories: List[Dict] = []
        self._is_scanning = False
        self._is_posting = False

        self._create_ui()
        self._load_profiles()

    def _create_ui(self):
        """Tạo giao diện"""
        # ========== HEADER - Profile Selector ==========
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=12)
        header.pack(fill="x", padx=15, pady=(15, 10))

        header_inner = ctk.CTkFrame(header, fg_color="transparent")
        header_inner.pack(fill="x", padx=15, pady=12)

        ctk.CTkLabel(
            header_inner,
            text="📱 Chọn Profile:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left")

        self.profile_var = ctk.StringVar(value="-- Chọn profile --")
        self.profile_menu = ctk.CTkOptionMenu(
            header_inner,
            variable=self.profile_var,
            values=["-- Chọn profile --"],
            fg_color=COLORS["bg_card"],
            button_color=COLORS["accent"],
            width=300,
            command=self._on_profile_change
        )
        self.profile_menu.pack(side="left", padx=15)

        # Refresh profiles button
        ModernButton(
            header_inner,
            text="Làm mới",
            icon="🔄",
            variant="secondary",
            command=self._load_profiles,
            width=100
        ).pack(side="left")

        # Profile status
        self.profile_status = ctk.CTkLabel(
            header_inner,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        )
        self.profile_status.pack(side="right")

        # ========== TABVIEW - 2 Sub-tabs ==========
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=COLORS["bg_secondary"],
            segmented_button_fg_color=COLORS["bg_card"],
            segmented_button_selected_color=COLORS["accent"],
            segmented_button_unselected_color=COLORS["bg_card"]
        )
        self.tabview.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Tab 1: Quét nhóm
        self.tab_scan = self.tabview.add("Quét nhóm")
        self._create_scan_tab()

        # Tab 2: Đăng nhóm
        self.tab_post = self.tabview.add("Đăng nhóm")
        self._create_post_tab()

    def _create_scan_tab(self):
        """Tạo tab Quét nhóm"""
        # Action bar
        action_bar = ctk.CTkFrame(self.tab_scan, fg_color="transparent")
        action_bar.pack(fill="x", padx=10, pady=10)

        ModernButton(
            action_bar,
            text="Quét nhóm",
            icon="🔍",
            variant="primary",
            command=self._scan_groups,
            width=130
        ).pack(side="left", padx=5)

        ModernButton(
            action_bar,
            text="Xóa tất cả",
            icon="🗑️",
            variant="danger",
            command=self._clear_all_groups,
            width=110
        ).pack(side="left", padx=5)

        # Stats
        self.scan_stats = ctk.CTkLabel(
            action_bar,
            text="Tổng: 0 nhóm",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        )
        self.scan_stats.pack(side="right", padx=10)

        # Progress bar
        self.scan_progress = ctk.CTkProgressBar(
            self.tab_scan,
            fg_color=COLORS["bg_card"],
            progress_color=COLORS["accent"]
        )
        self.scan_progress.pack(fill="x", padx=10, pady=(0, 10))
        self.scan_progress.set(0)

        # Groups table header
        table_header = ctk.CTkFrame(self.tab_scan, fg_color=COLORS["bg_card"], corner_radius=5, height=35)
        table_header.pack(fill="x", padx=10, pady=(0, 5))
        table_header.pack_propagate(False)

        headers = [("", 30), ("ID", 60), ("Tên nhóm", 250), ("URL", 200), ("Thành viên", 100), ("Ngày quét", 120)]
        for text, width in headers:
            ctk.CTkLabel(
                table_header,
                text=text,
                width=width,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=COLORS["text_primary"]
            ).pack(side="left", padx=5)

        # Groups list
        self.scan_list = ctk.CTkScrollableFrame(self.tab_scan, fg_color="transparent")
        self.scan_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Empty message
        self.scan_empty_label = ctk.CTkLabel(
            self.scan_list,
            text="Chưa có nhóm nào\nChọn profile và bấm 'Quét nhóm' để bắt đầu",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_secondary"]
        )
        self.scan_empty_label.pack(pady=50)

    def _create_post_tab(self):
        """Tạo tab Đăng nhóm"""
        # Main container - 2 columns
        main_container = ctk.CTkFrame(self.tab_post, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=5, pady=5)

        # ========== LEFT PANEL - Groups List ==========
        left_panel = ctk.CTkFrame(main_container, fg_color=COLORS["bg_card"], corner_radius=10, width=400)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)

        # Left header
        left_header = ctk.CTkFrame(left_panel, fg_color="transparent")
        left_header.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            left_header,
            text="Danh sách nhóm",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left")

        # Select all checkbox
        self.select_all_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            left_header,
            text="Chọn tất cả",
            variable=self.select_all_var,
            fg_color=COLORS["accent"],
            command=self._toggle_select_all
        ).pack(side="right")

        # Groups stats
        self.post_stats = ctk.CTkLabel(
            left_panel,
            text="Đã chọn: 0 / 0 nhóm",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["accent"]
        )
        self.post_stats.pack(anchor="w", padx=10, pady=(0, 5))

        # Groups checkboxes list
        self.post_groups_list = ctk.CTkScrollableFrame(left_panel, fg_color="transparent")
        self.post_groups_list.pack(fill="both", expand=True, padx=5, pady=(0, 10))

        self.post_empty_label = ctk.CTkLabel(
            self.post_groups_list,
            text="Chưa có nhóm nào\nHãy quét nhóm ở tab trước",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        )
        self.post_empty_label.pack(pady=30)

        # ========== RIGHT PANEL - Post Content ==========
        right_panel = ctk.CTkFrame(main_container, fg_color=COLORS["bg_card"], corner_radius=10)
        right_panel.pack(side="right", fill="both", expand=True)

        # Right header
        ctk.CTkLabel(
            right_panel,
            text="Nội dung đăng",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=15, pady=(15, 10))

        # Category selector
        cat_row = ctk.CTkFrame(right_panel, fg_color="transparent")
        cat_row.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(cat_row, text="Chuyên mục:", width=100, anchor="w").pack(side="left")
        self.category_var = ctk.StringVar(value="Mặc định")
        self.category_menu = ctk.CTkOptionMenu(
            cat_row,
            variable=self.category_var,
            values=["Mặc định"],
            fg_color=COLORS["bg_secondary"],
            button_color=COLORS["accent"],
            width=200,
            command=self._on_category_change
        )
        self.category_menu.pack(side="left", padx=10)

        # Content selector
        content_row = ctk.CTkFrame(right_panel, fg_color="transparent")
        content_row.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(content_row, text="Nội dung:", width=100, anchor="w").pack(side="left")
        self.content_var = ctk.StringVar(value="-- Chọn nội dung --")
        self.content_menu = ctk.CTkOptionMenu(
            content_row,
            variable=self.content_var,
            values=["-- Chọn nội dung --"],
            fg_color=COLORS["bg_secondary"],
            button_color=COLORS["accent"],
            width=300,
            command=self._on_content_change
        )
        self.content_menu.pack(side="left", padx=10)

        # Content preview
        ctk.CTkLabel(
            right_panel,
            text="Xem trước nội dung:",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=15, pady=(15, 5))

        self.content_preview = ctk.CTkTextbox(
            right_panel,
            fg_color=COLORS["bg_secondary"],
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont(size=12),
            height=200
        )
        self.content_preview.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        self.content_preview.configure(state="disabled")

        # Posting options
        options_frame = ctk.CTkFrame(right_panel, fg_color=COLORS["bg_secondary"], corner_radius=8)
        options_frame.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(
            options_frame,
            text="Tùy chọn đăng:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))

        options_inner = ctk.CTkFrame(options_frame, fg_color="transparent")
        options_inner.pack(fill="x", padx=10, pady=(0, 10))

        # Delay between posts
        ctk.CTkLabel(options_inner, text="Delay (giây):", width=100, anchor="w").pack(side="left")
        self.delay_entry = ModernEntry(options_inner, placeholder="5", width=80)
        self.delay_entry.pack(side="left", padx=5)
        self.delay_entry.insert(0, "5")

        # Random delay
        self.random_delay_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            options_inner,
            text="Random delay (1-10s)",
            variable=self.random_delay_var,
            fg_color=COLORS["accent"]
        ).pack(side="left", padx=20)

        # Post button
        post_btn_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        post_btn_frame.pack(fill="x", padx=15, pady=15)

        ModernButton(
            post_btn_frame,
            text="Đăng bài",
            icon="📤",
            variant="success",
            command=self._start_posting,
            width=150
        ).pack(side="left", padx=5)

        ModernButton(
            post_btn_frame,
            text="Dừng",
            icon="⏹️",
            variant="danger",
            command=self._stop_posting,
            width=100
        ).pack(side="left", padx=5)

        # Posting progress
        self.post_progress = ctk.CTkProgressBar(
            right_panel,
            fg_color=COLORS["bg_secondary"],
            progress_color=COLORS["success"]
        )
        self.post_progress.pack(fill="x", padx=15, pady=(0, 10))
        self.post_progress.set(0)

        self.post_status_label = ctk.CTkLabel(
            right_panel,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"]
        )
        self.post_status_label.pack(anchor="w", padx=15, pady=(0, 15))

    # ==================== PROFILE MANAGEMENT ====================

    def _load_profiles(self):
        """Load danh sách profiles"""
        self.profiles = get_profiles()

        if not self.profiles:
            self.profile_menu.configure(values=["-- Chưa có profile --"])
            self.profile_var.set("-- Chưa có profile --")
            self.profile_status.configure(text="Chưa có profile. Hãy đồng bộ profiles trước.")
            return

        # Build profile list: "Name (UUID short)"
        profile_options = ["-- Chọn profile --"]
        for p in self.profiles:
            name = p.get('name', 'Unknown')
            uuid = p.get('uuid', '')[:8]
            profile_options.append(f"{name} ({uuid})")

        self.profile_menu.configure(values=profile_options)
        self.profile_var.set("-- Chọn profile --")
        self.profile_status.configure(text=f"Có {len(self.profiles)} profiles")

    def _on_profile_change(self, choice: str):
        """Khi chọn profile khác"""
        if choice == "-- Chọn profile --" or choice == "-- Chưa có profile --":
            self.current_profile_uuid = None
            self._clear_groups_ui()
            return

        # Extract UUID from choice
        for p in self.profiles:
            name = p.get('name', 'Unknown')
            uuid = p.get('uuid', '')
            if choice.startswith(name) and uuid[:8] in choice:
                self.current_profile_uuid = uuid
                self._load_groups_for_profile()
                self._load_contents()
                break

    def _clear_groups_ui(self):
        """Clear UI khi không có profile được chọn"""
        self.groups = []
        self.selected_group_ids = []
        self._render_scan_list()
        self._render_post_groups_list()

    # ==================== SCAN TAB ====================

    def _scan_groups(self):
        """Quét danh sách nhóm của profile"""
        if not self.current_profile_uuid:
            self._set_status("Vui lòng chọn profile trước!", "warning")
            return

        if self._is_scanning:
            self._set_status("Đang quét, vui lòng đợi...", "warning")
            return

        self._is_scanning = True
        self.scan_progress.set(0)
        self._set_status("Đang quét nhóm...", "info")

        def do_scan():
            try:
                # Scan groups via API/script
                # This would need to be implemented based on Hidemium API or automation script
                # For now, simulate with placeholder data
                result = self._execute_group_scan()
                self.after(0, lambda: self._on_scan_complete(result))
            except Exception as e:
                self.after(0, lambda: self._on_scan_error(str(e)))

        threading.Thread(target=do_scan, daemon=True).start()

    def _execute_group_scan(self) -> List[Dict]:
        """
        Thực hiện quét nhóm - cần kết nối với Hidemium script
        Trả về danh sách groups đã quét được
        """
        # TODO: Implement actual scanning logic via Hidemium API
        # This is a placeholder that would need to be connected to actual automation
        import time
        time.sleep(2)  # Simulate scanning

        # Placeholder - in real implementation, this would scan Facebook groups
        # via browser automation using Hidemium
        return []

    def _on_scan_complete(self, groups: List[Dict]):
        """Xử lý kết quả quét nhóm"""
        self._is_scanning = False
        self.scan_progress.set(1)

        if groups:
            # Save groups to database
            sync_groups(self.current_profile_uuid, groups)
            self._load_groups_for_profile()
            self._set_status(f"Đã quét được {len(groups)} nhóm", "success")
        else:
            self._set_status("Không tìm thấy nhóm mới. Hãy chạy script quét nhóm.", "warning")
            # Still reload from database in case there are existing groups
            self._load_groups_for_profile()

    def _on_scan_error(self, error: str):
        """Xử lý lỗi quét nhóm"""
        self._is_scanning = False
        self.scan_progress.set(0)
        self._set_status(f"Lỗi quét nhóm: {error}", "error")

    def _load_groups_for_profile(self):
        """Load danh sách nhóm của profile hiện tại"""
        if not self.current_profile_uuid:
            self.groups = []
        else:
            self.groups = get_groups(self.current_profile_uuid)

        # Update selected_group_ids from database
        self.selected_group_ids = [g['id'] for g in self.groups if g.get('is_selected')]

        self._render_scan_list()
        self._render_post_groups_list()
        self._update_stats()

    def _render_scan_list(self):
        """Render danh sách nhóm trong tab Quét"""
        # Clear existing
        for widget in self.scan_list.winfo_children():
            widget.destroy()

        if not self.groups:
            self.scan_empty_label = ctk.CTkLabel(
                self.scan_list,
                text="Chưa có nhóm nào\nChọn profile và bấm 'Quét nhóm' để bắt đầu",
                font=ctk.CTkFont(size=13),
                text_color=COLORS["text_secondary"]
            )
            self.scan_empty_label.pack(pady=50)
            return

        for group in self.groups:
            self._create_scan_row(group)

    def _create_scan_row(self, group: Dict):
        """Tạo row cho group trong danh sách quét"""
        row = ctk.CTkFrame(self.scan_list, fg_color=COLORS["bg_secondary"], corner_radius=5, height=40)
        row.pack(fill="x", pady=2)
        row.pack_propagate(False)

        # Checkbox
        var = ctk.BooleanVar(value=group['id'] in self.selected_group_ids)
        cb = ctk.CTkCheckBox(
            row,
            text="",
            variable=var,
            width=25,
            checkbox_width=18,
            checkbox_height=18,
            fg_color=COLORS["accent"],
            command=lambda gid=group['id'], v=var: self._toggle_group_selection(gid, v)
        )
        cb.pack(side="left", padx=5)

        # ID
        ctk.CTkLabel(
            row,
            text=str(group.get('id', '')),
            width=60,
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"]
        ).pack(side="left")

        # Group name
        name = group.get('group_name', 'Unknown')[:30]
        ctk.CTkLabel(
            row,
            text=name,
            width=250,
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_primary"],
            anchor="w"
        ).pack(side="left", padx=5)

        # URL
        url = group.get('group_url', '')[:25]
        ctk.CTkLabel(
            row,
            text=url,
            width=200,
            font=ctk.CTkFont(size=10),
            text_color=COLORS["accent"],
            anchor="w"
        ).pack(side="left", padx=5)

        # Member count
        members = group.get('member_count', 0)
        ctk.CTkLabel(
            row,
            text=f"{members:,}" if members else "-",
            width=100,
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"]
        ).pack(side="left", padx=5)

        # Created date
        created = group.get('created_at', '')[:10] if group.get('created_at') else '-'
        ctk.CTkLabel(
            row,
            text=created,
            width=120,
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_secondary"]
        ).pack(side="left", padx=5)

        # Delete button
        ctk.CTkButton(
            row,
            text="X",
            width=30,
            height=25,
            fg_color=COLORS["error"],
            hover_color="#ff4757",
            corner_radius=5,
            command=lambda gid=group['id']: self._delete_group(gid)
        ).pack(side="right", padx=5)

    def _toggle_group_selection(self, group_id: int, var: ctk.BooleanVar):
        """Toggle chọn group"""
        is_selected = var.get()
        update_group_selection(group_id, 1 if is_selected else 0)

        if is_selected:
            if group_id not in self.selected_group_ids:
                self.selected_group_ids.append(group_id)
        else:
            if group_id in self.selected_group_ids:
                self.selected_group_ids.remove(group_id)

        self._update_stats()
        self._render_post_groups_list()

    def _delete_group(self, group_id: int):
        """Xóa một group"""
        delete_group(group_id)
        if group_id in self.selected_group_ids:
            self.selected_group_ids.remove(group_id)
        self._load_groups_for_profile()
        self._set_status("Đã xóa nhóm", "success")

    def _clear_all_groups(self):
        """Xóa tất cả groups của profile hiện tại"""
        if not self.current_profile_uuid:
            self._set_status("Vui lòng chọn profile trước!", "warning")
            return

        clear_groups(self.current_profile_uuid)
        self.selected_group_ids = []
        self._load_groups_for_profile()
        self._set_status("Đã xóa tất cả nhóm", "success")

    def _update_stats(self):
        """Cập nhật thống kê"""
        total = len(self.groups)
        selected = len(self.selected_group_ids)

        self.scan_stats.configure(text=f"Tổng: {total} nhóm")
        self.post_stats.configure(text=f"Đã chọn: {selected} / {total} nhóm")

    # ==================== POST TAB ====================

    def _render_post_groups_list(self):
        """Render danh sách nhóm với checkbox trong tab Đăng"""
        # Clear existing
        for widget in self.post_groups_list.winfo_children():
            widget.destroy()

        if not self.groups:
            self.post_empty_label = ctk.CTkLabel(
                self.post_groups_list,
                text="Chưa có nhóm nào\nHãy quét nhóm ở tab trước",
                font=ctk.CTkFont(size=12),
                text_color=COLORS["text_secondary"]
            )
            self.post_empty_label.pack(pady=30)
            return

        for group in self.groups:
            self._create_post_group_row(group)

    def _create_post_group_row(self, group: Dict):
        """Tạo row cho group trong tab Đăng"""
        row = ctk.CTkFrame(self.post_groups_list, fg_color="transparent", height=35)
        row.pack(fill="x", pady=2)
        row.pack_propagate(False)

        var = ctk.BooleanVar(value=group['id'] in self.selected_group_ids)

        cb = ctk.CTkCheckBox(
            row,
            text=group.get('group_name', 'Unknown')[:35],
            variable=var,
            width=350,
            checkbox_width=18,
            checkbox_height=18,
            fg_color=COLORS["accent"],
            font=ctk.CTkFont(size=11),
            command=lambda gid=group['id'], v=var: self._toggle_group_selection_post(gid, v)
        )
        cb.pack(side="left", padx=5)

        # Member count
        members = group.get('member_count', 0)
        if members:
            ctk.CTkLabel(
                row,
                text=f"({members:,})",
                font=ctk.CTkFont(size=10),
                text_color=COLORS["text_secondary"]
            ).pack(side="right", padx=5)

    def _toggle_group_selection_post(self, group_id: int, var: ctk.BooleanVar):
        """Toggle chọn group từ tab Đăng"""
        is_selected = var.get()
        update_group_selection(group_id, 1 if is_selected else 0)

        if is_selected:
            if group_id not in self.selected_group_ids:
                self.selected_group_ids.append(group_id)
        else:
            if group_id in self.selected_group_ids:
                self.selected_group_ids.remove(group_id)

        self._update_stats()
        # Also update scan list
        self._render_scan_list()

    def _toggle_select_all(self):
        """Toggle chọn tất cả groups"""
        if self.select_all_var.get():
            self.selected_group_ids = [g['id'] for g in self.groups]
            for g in self.groups:
                update_group_selection(g['id'], 1)
        else:
            for gid in self.selected_group_ids:
                update_group_selection(gid, 0)
            self.selected_group_ids = []

        self._render_scan_list()
        self._render_post_groups_list()
        self._update_stats()

    def _load_contents(self):
        """Load nội dung và categories"""
        self.categories = get_categories()
        cat_names = [c.get('name', 'Unknown') for c in self.categories]
        self.category_menu.configure(values=cat_names if cat_names else ["Mặc định"])

        if self.categories:
            self.category_var.set(self.categories[0].get('name', 'Mặc định'))
            self._load_contents_for_category(self.categories[0].get('id', 1))

    def _on_category_change(self, choice: str):
        """Khi đổi category"""
        for cat in self.categories:
            if cat.get('name') == choice:
                self._load_contents_for_category(cat.get('id'))
                break

    def _load_contents_for_category(self, category_id: int):
        """Load contents của category"""
        self.contents = get_contents(category_id)

        if not self.contents:
            self.content_menu.configure(values=["-- Chưa có nội dung --"])
            self.content_var.set("-- Chưa có nội dung --")
            self._update_preview("")
            return

        content_titles = [c.get('title', 'Untitled')[:40] for c in self.contents]
        self.content_menu.configure(values=content_titles)
        self.content_var.set(content_titles[0])
        self._update_preview(self.contents[0].get('content', ''))

    def _on_content_change(self, choice: str):
        """Khi đổi content"""
        for c in self.contents:
            if c.get('title', '')[:40] == choice:
                self._update_preview(c.get('content', ''))
                break

    def _update_preview(self, content: str):
        """Cập nhật preview content"""
        self.content_preview.configure(state="normal")
        self.content_preview.delete("1.0", "end")
        self.content_preview.insert("1.0", content)
        self.content_preview.configure(state="disabled")

    def _get_selected_content(self) -> Optional[Dict]:
        """Lấy content được chọn"""
        selected_title = self.content_var.get()
        for c in self.contents:
            if c.get('title', '')[:40] == selected_title:
                return c
        return None

    def _start_posting(self):
        """Bắt đầu đăng bài vào các nhóm đã chọn"""
        if not self.current_profile_uuid:
            self._set_status("Vui lòng chọn profile!", "warning")
            return

        if not self.selected_group_ids:
            self._set_status("Vui lòng chọn ít nhất 1 nhóm!", "warning")
            return

        content = self._get_selected_content()
        if not content:
            self._set_status("Vui lòng chọn nội dung để đăng!", "warning")
            return

        if self._is_posting:
            self._set_status("Đang đăng bài, vui lòng đợi...", "warning")
            return

        self._is_posting = True
        self.post_progress.set(0)

        # Get selected groups
        selected_groups = [g for g in self.groups if g['id'] in self.selected_group_ids]

        def do_post():
            try:
                self._execute_posting(selected_groups, content)
            except Exception as e:
                self.after(0, lambda: self._on_posting_error(str(e)))

        threading.Thread(target=do_post, daemon=True).start()

    def _execute_posting(self, groups: List[Dict], content: Dict):
        """Thực hiện đăng bài vào các nhóm"""
        import time
        import random

        total = len(groups)
        content_text = content.get('content', '')

        for i, group in enumerate(groups):
            if not self._is_posting:
                break

            group_name = group.get('group_name', 'Unknown')
            self.after(0, lambda g=group_name, n=i+1, t=total:
                       self.post_status_label.configure(text=f"Đang đăng: {g} ({n}/{t})"))

            # Update progress
            progress = (i + 1) / total
            self.after(0, lambda p=progress: self.post_progress.set(p))

            # TODO: Implement actual posting via Hidemium API
            # This would need browser automation to post to each group
            result = self._post_to_group(group, content_text)

            # Save to history
            save_post_history({
                'profile_uuid': self.current_profile_uuid,
                'group_id': group.get('group_id'),
                'content_id': content.get('id'),
                'status': 'success' if result else 'failed',
                'error_message': '' if result else 'Posting failed'
            })

            # Delay between posts
            if i < total - 1:
                if self.random_delay_var.get():
                    delay = random.uniform(1, 10)
                else:
                    try:
                        delay = float(self.delay_entry.get())
                    except ValueError:
                        delay = 5

                time.sleep(delay)

        self.after(0, lambda: self._on_posting_complete(total))

    def _post_to_group(self, group: Dict, content: str) -> bool:
        """
        Đăng bài vào một nhóm - cần kết nối với Hidemium script
        Trả về True nếu thành công
        """
        # TODO: Implement actual posting logic via Hidemium API
        # This is a placeholder
        import time
        time.sleep(1)  # Simulate posting
        return True

    def _on_posting_complete(self, total: int):
        """Xử lý khi đăng bài hoàn tất"""
        self._is_posting = False
        self.post_progress.set(1)
        self.post_status_label.configure(text=f"Hoàn tất! Đã đăng {total} nhóm")
        self._set_status(f"Đã đăng bài vào {total} nhóm", "success")

    def _on_posting_error(self, error: str):
        """Xử lý lỗi đăng bài"""
        self._is_posting = False
        self.post_progress.set(0)
        self.post_status_label.configure(text=f"Lỗi: {error}")
        self._set_status(f"Lỗi đăng bài: {error}", "error")

    def _stop_posting(self):
        """Dừng đăng bài"""
        if self._is_posting:
            self._is_posting = False
            self.post_status_label.configure(text="Đã dừng đăng bài")
            self._set_status("Đã dừng đăng bài", "warning")

    def _set_status(self, text: str, status_type: str = "info"):
        """Cập nhật status bar"""
        if self.status_callback:
            self.status_callback(text, status_type)
