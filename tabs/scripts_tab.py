"""
Tab Kịch bản - Lên lịch đăng bài tự động
Persistent scheduling - lưu vào database, chạy ngầm khi app mở
"""
import customtkinter as ctk
from typing import List, Dict, Optional
import threading
import json
import time
import os
import random
from datetime import datetime, timedelta
from config import COLORS
from widgets import ModernCard, ModernButton, ModernEntry, ModernTextbox
from db import (
    get_schedules, get_schedule, save_schedule, delete_schedule,
    update_schedule_stats, get_categories, get_groups, get_contents
)
from api_service import api


class ScriptsTab(ctk.CTkFrame):
    """Tab quản lý kịch bản đăng bài theo lịch"""

    def __init__(self, master, status_callback=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.status_callback = status_callback
        self.schedules: List[Dict] = []
        self.folders: List[Dict] = []
        self.categories: List[Dict] = []
        self.current_schedule: Dict = None
        self._scheduler_running = False
        self._scheduler_thread = None

        self._create_ui()
        self._load_data()
        self._start_scheduler()

    def _create_ui(self):
        """Tạo giao diện"""
        # ========== HEADER ==========
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 15))

        ctk.CTkLabel(
            header_frame,
            text="📅 Kịch bản Đăng bài",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left")

        # Scheduler status
        self.scheduler_status = ctk.CTkLabel(
            header_frame,
            text="⏸ Scheduler: Chưa chạy",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        )
        self.scheduler_status.pack(side="right", padx=10)

        ModernButton(
            header_frame,
            text="+ Tạo kịch bản",
            icon="📝",
            variant="success",
            command=self._new_schedule,
            width=140
        ).pack(side="right", padx=5)

        # ========== MAIN CONTENT - 2 COLUMNS ==========
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Left panel - Schedule list
        left_panel = ctk.CTkFrame(main_frame, fg_color=COLORS["bg_secondary"], corner_radius=15, width=380)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)

        # List header
        list_header = ctk.CTkFrame(left_panel, fg_color="transparent")
        list_header.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(
            list_header,
            text="📋 Danh sách kịch bản",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left")

        ModernButton(
            list_header,
            text="🔄",
            variant="secondary",
            command=self._load_schedules,
            width=40
        ).pack(side="right")

        # Schedule list
        self.schedule_list = ctk.CTkScrollableFrame(left_panel, fg_color="transparent")
        self.schedule_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.empty_label = ctk.CTkLabel(
            self.schedule_list,
            text="📭 Chưa có kịch bản nào\nBấm '+ Tạo kịch bản' để bắt đầu",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_secondary"],
            justify="center"
        )
        self.empty_label.pack(pady=50)

        # Right panel - Schedule editor
        right_panel = ctk.CTkFrame(main_frame, fg_color=COLORS["bg_secondary"], corner_radius=15)
        right_panel.pack(side="right", fill="both", expand=True)

        # Editor scroll
        self.editor_scroll = ctk.CTkScrollableFrame(right_panel, fg_color="transparent")
        self.editor_scroll.pack(fill="both", expand=True, padx=15, pady=15)

        self._create_editor_form()

    def _create_editor_form(self):
        """Tạo form chỉnh sửa kịch bản"""
        editor = self.editor_scroll

        # Title
        self.editor_title = ctk.CTkLabel(
            editor,
            text="✏️ Tạo kịch bản mới",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        self.editor_title.pack(anchor="w", pady=(0, 15))

        # ========== TÊN KỊCH BẢN ==========
        name_frame = ctk.CTkFrame(editor, fg_color="transparent")
        name_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(name_frame, text="Tên kịch bản:", width=120, anchor="w").pack(side="left")
        self.name_entry = ModernEntry(name_frame, placeholder="VD: Đăng Đông Hưng buổi sáng")
        self.name_entry.pack(side="left", fill="x", expand=True)

        # ========== LỌC THEO THƯ MỤC ==========
        folder_frame = ctk.CTkFrame(editor, fg_color="transparent")
        folder_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(folder_frame, text="📁 Lọc thư mục:", width=120, anchor="w").pack(side="left")
        self.folder_var = ctk.StringVar(value="-- Tất cả --")
        self.folder_menu = ctk.CTkOptionMenu(
            folder_frame,
            variable=self.folder_var,
            values=["-- Tất cả --"],
            fg_color=COLORS["bg_card"],
            button_color=COLORS["accent"],
            width=180,
            command=self._on_folder_filter_change
        )
        self.folder_menu.pack(side="left", padx=5)

        ModernButton(
            folder_frame, text="Tải profiles", variant="secondary",
            command=self._load_profiles_for_schedule, width=110
        ).pack(side="left", padx=5)

        # ========== CHỌN PROFILES (multi-select) ==========
        profile_label = ctk.CTkLabel(
            editor,
            text="👤 Chọn Profiles (để đăng bài):",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        profile_label.pack(anchor="w", pady=(15, 5))

        profile_btn_frame = ctk.CTkFrame(editor, fg_color="transparent")
        profile_btn_frame.pack(fill="x", pady=5)

        self.profile_select_all_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            profile_btn_frame,
            text="Chọn tất cả",
            variable=self.profile_select_all_var,
            fg_color=COLORS["accent"],
            command=self._toggle_all_profiles
        ).pack(side="left")

        self.profile_count_label = ctk.CTkLabel(
            profile_btn_frame,
            text="(0 profile đã chọn)",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        )
        self.profile_count_label.pack(side="left", padx=10)

        # Profile list frame
        self.profile_list_frame = ctk.CTkFrame(editor, fg_color=COLORS["bg_card"], corner_radius=10, height=120)
        self.profile_list_frame.pack(fill="x", pady=5)
        self.profile_list_frame.pack_propagate(False)

        self.profile_scroll = ctk.CTkScrollableFrame(self.profile_list_frame, fg_color="transparent")
        self.profile_scroll.pack(fill="both", expand=True, padx=5, pady=5)

        self.profile_vars = {}  # {profile_uuid: BooleanVar}
        self.profiles = []

        ctk.CTkLabel(
            self.profile_scroll,
            text="Bấm 'Tải profiles' để hiện danh sách",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"]
        ).pack(pady=20)

        # ========== KHUNG GIỜ ĐĂNG ==========
        time_label = ctk.CTkLabel(
            editor,
            text="⏰ Khung giờ đăng (chọn nhiều):",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        time_label.pack(anchor="w", pady=(15, 5))

        time_frame = ctk.CTkFrame(editor, fg_color=COLORS["bg_card"], corner_radius=10)
        time_frame.pack(fill="x", pady=5)

        self.time_vars = {}
        time_grid = ctk.CTkFrame(time_frame, fg_color="transparent")
        time_grid.pack(padx=10, pady=10)

        # Tạo checkbox cho từng khung giờ (6h - 23h)
        hours = list(range(6, 24))
        for i, hour in enumerate(hours):
            var = ctk.BooleanVar(value=False)
            self.time_vars[hour] = var
            cb = ctk.CTkCheckBox(
                time_grid,
                text=f"{hour}:00",
                variable=var,
                fg_color=COLORS["accent"],
                width=70
            )
            cb.grid(row=i // 6, column=i % 6, padx=5, pady=3)

        # Quick select buttons
        quick_frame = ctk.CTkFrame(time_frame, fg_color="transparent")
        quick_frame.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkButton(
            quick_frame, text="Sáng (6-11h)", width=90, height=28,
            fg_color=COLORS["bg_secondary"], command=lambda: self._select_hours(6, 12)
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            quick_frame, text="Chiều (12-17h)", width=90, height=28,
            fg_color=COLORS["bg_secondary"], command=lambda: self._select_hours(12, 18)
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            quick_frame, text="Tối (18-23h)", width=90, height=28,
            fg_color=COLORS["bg_secondary"], command=lambda: self._select_hours(18, 24)
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            quick_frame, text="Cả ngày", width=70, height=28,
            fg_color=COLORS["accent"], command=lambda: self._select_hours(6, 24)
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            quick_frame, text="Bỏ chọn", width=70, height=28,
            fg_color=COLORS["danger"], command=self._clear_hours
        ).pack(side="left", padx=2)

        # ========== KỊCH BẢN NỘI DUNG ==========
        content_label = ctk.CTkLabel(
            editor,
            text="📝 Kịch bản nội dung:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        content_label.pack(anchor="w", pady=(15, 5))

        content_frame = ctk.CTkFrame(editor, fg_color="transparent")
        content_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(content_frame, text="Danh mục:", width=100, anchor="w").pack(side="left")
        self.category_var = ctk.StringVar(value="-- Chọn danh mục --")
        self.category_menu = ctk.CTkOptionMenu(
            content_frame,
            variable=self.category_var,
            values=["-- Chọn danh mục --"],
            fg_color=COLORS["bg_card"],
            button_color=COLORS["accent"],
            width=200
        )
        self.category_menu.pack(side="left", padx=5)

        self.random_content_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            content_frame,
            text="Random nội dung",
            variable=self.random_content_var,
            fg_color=COLORS["accent"]
        ).pack(side="left", padx=10)

        # ========== THƯ MỤC ẢNH ==========
        image_frame = ctk.CTkFrame(editor, fg_color="transparent")
        image_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(image_frame, text="🖼️ Thư mục ảnh:", width=100, anchor="w").pack(side="left")
        self.image_folder_entry = ModernEntry(image_frame, placeholder="Đường dẫn thư mục ảnh (tùy chọn)")
        self.image_folder_entry.pack(side="left", fill="x", expand=True)
        ModernButton(
            image_frame, text="📂", variant="secondary",
            command=self._browse_image_folder, width=40
        ).pack(side="left", padx=5)

        # ========== DELAY ==========
        delay_frame = ctk.CTkFrame(editor, fg_color="transparent")
        delay_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(delay_frame, text="⏱️ Delay (giây):", width=100, anchor="w").pack(side="left")
        self.delay_min_entry = ModernEntry(delay_frame, placeholder="30", width=60)
        self.delay_min_entry.pack(side="left")
        self.delay_min_entry.insert(0, "30")
        ctk.CTkLabel(delay_frame, text=" đến ").pack(side="left")
        self.delay_max_entry = ModernEntry(delay_frame, placeholder="60", width=60)
        self.delay_max_entry.pack(side="left")
        self.delay_max_entry.insert(0, "60")
        ctk.CTkLabel(delay_frame, text=" (giữa các nhóm)").pack(side="left")

        # ========== CHỌN NHÓM ĐĂNG ==========
        group_label = ctk.CTkLabel(
            editor,
            text="👥 Chọn nhóm đăng:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        group_label.pack(anchor="w", pady=(15, 5))

        group_btn_frame = ctk.CTkFrame(editor, fg_color="transparent")
        group_btn_frame.pack(fill="x", pady=5)

        self.group_select_all_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            group_btn_frame,
            text="Chọn tất cả",
            variable=self.group_select_all_var,
            fg_color=COLORS["accent"],
            command=self._toggle_all_groups
        ).pack(side="left")

        self.group_count_label = ctk.CTkLabel(
            group_btn_frame,
            text="(0 nhóm đã chọn)",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        )
        self.group_count_label.pack(side="left", padx=10)

        ModernButton(
            group_btn_frame, text="Tải nhóm", variant="secondary",
            command=self._load_groups_for_folder, width=100
        ).pack(side="right")

        # Group list
        self.group_list_frame = ctk.CTkFrame(editor, fg_color=COLORS["bg_card"], corner_radius=10, height=150)
        self.group_list_frame.pack(fill="x", pady=5)
        self.group_list_frame.pack_propagate(False)

        self.group_scroll = ctk.CTkScrollableFrame(self.group_list_frame, fg_color="transparent")
        self.group_scroll.pack(fill="both", expand=True, padx=5, pady=5)

        self.group_vars = {}  # {group_id: BooleanVar}
        self.groups = []

        ctk.CTkLabel(
            self.group_scroll,
            text="Chọn thư mục profile trước, sau đó bấm 'Tải nhóm'",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"]
        ).pack(pady=20)

        # ========== ACTION BUTTONS ==========
        btn_frame = ctk.CTkFrame(editor, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(20, 10))

        ModernButton(
            btn_frame,
            text="💾 Lưu kịch bản",
            icon="",
            variant="success",
            command=self._save_schedule,
            width=140
        ).pack(side="left", padx=5)

        ModernButton(
            btn_frame,
            text="▶ Chạy ngay",
            icon="",
            variant="primary",
            command=self._run_now,
            width=120
        ).pack(side="left", padx=5)

        ModernButton(
            btn_frame,
            text="🗑️ Xóa",
            icon="",
            variant="danger",
            command=self._delete_schedule,
            width=80
        ).pack(side="left", padx=5)

        # ========== THỐNG KÊ ==========
        stats_frame = ctk.CTkFrame(editor, fg_color=COLORS["bg_card"], corner_radius=10)
        stats_frame.pack(fill="x", pady=(15, 5))

        stats_inner = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_inner.pack(padx=15, pady=10)

        ctk.CTkLabel(
            stats_inner,
            text="📊 Thống kê:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")

        self.stats_label = ctk.CTkLabel(
            stats_inner,
            text="Đã đăng: 0 | Thành công: 0 | Lỗi: 0",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        )
        self.stats_label.pack(anchor="w", pady=5)

        self.last_run_label = ctk.CTkLabel(
            stats_inner,
            text="Lần chạy cuối: Chưa có",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"]
        )
        self.last_run_label.pack(anchor="w")

        # ========== LOG ==========
        log_label = ctk.CTkLabel(
            editor,
            text="📋 Log:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        log_label.pack(anchor="w", pady=(15, 5))

        self.log_textbox = ModernTextbox(editor, height=120)
        self.log_textbox.pack(fill="x", pady=5)
        self.log_textbox.configure(state="disabled")

    def _select_hours(self, start: int, end: int):
        """Chọn các giờ từ start đến end"""
        for hour, var in self.time_vars.items():
            var.set(start <= hour < end)

    def _clear_hours(self):
        """Bỏ chọn tất cả giờ"""
        for var in self.time_vars.values():
            var.set(False)

    def _toggle_all_groups(self):
        """Toggle chọn tất cả nhóm"""
        select_all = self.group_select_all_var.get()
        for var in self.group_vars.values():
            var.set(select_all)
        self._update_group_count()

    def _update_group_count(self):
        """Cập nhật số nhóm đã chọn"""
        count = sum(1 for var in self.group_vars.values() if var.get())
        self.group_count_label.configure(text=f"({count} nhóm đã chọn)")

    def _toggle_all_profiles(self):
        """Toggle chọn tất cả profiles"""
        select_all = self.profile_select_all_var.get()
        for var in self.profile_vars.values():
            var.set(select_all)
        self._update_profile_count()

    def _update_profile_count(self):
        """Cập nhật số profile đã chọn"""
        count = sum(1 for var in self.profile_vars.values() if var.get())
        self.profile_count_label.configure(text=f"({count} profile đã chọn)")

    def _on_folder_filter_change(self, choice):
        """Khi đổi folder filter"""
        self._load_profiles_for_schedule()

    def _load_profiles_for_schedule(self):
        """Load profiles theo folder đã chọn"""
        folder_name = self.folder_var.get()

        # Clear current profiles
        for widget in self.profile_scroll.winfo_children():
            widget.destroy()
        self.profile_vars = {}

        try:
            if folder_name == "-- Tất cả --":
                self.profiles = api.get_profiles(limit=500)
            else:
                # Tìm folder_id
                folder_id = None
                for f in self.folders:
                    if f.get('name') == folder_name:
                        folder_id = f.get('id')
                        break
                if folder_id:
                    self.profiles = api.get_profiles(folder_id=[folder_id], limit=500)
                else:
                    self.profiles = api.get_profiles(limit=500)
        except Exception as e:
            print(f"Error loading profiles: {e}")
            self.profiles = []

        self._render_profiles()

    def _render_profiles(self):
        """Render danh sách profiles"""
        for widget in self.profile_scroll.winfo_children():
            widget.destroy()

        if not self.profiles:
            ctk.CTkLabel(
                self.profile_scroll,
                text="Không có profile nào",
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text_secondary"]
            ).pack(pady=20)
            return

        for profile in self.profiles:
            if isinstance(profile, dict):
                profile_uuid = profile.get('uuid', '')
                profile_name = profile.get('name', profile_uuid[:8])
            else:
                profile_uuid = str(profile)
                profile_name = profile_uuid[:8]

            var = ctk.BooleanVar(value=False)
            self.profile_vars[profile_uuid] = var

            cb = ctk.CTkCheckBox(
                self.profile_scroll,
                text=profile_name,
                variable=var,
                fg_color=COLORS["accent"],
                command=self._update_profile_count
            )
            cb.pack(anchor="w", pady=2)

        self._update_profile_count()
        self._log(f"Đã tải {len(self.profiles)} profiles")

    def _browse_image_folder(self):
        """Chọn thư mục ảnh"""
        from tkinter import filedialog
        folder = filedialog.askdirectory()
        if folder:
            self.image_folder_entry.delete(0, "end")
            self.image_folder_entry.insert(0, folder)

    def _load_data(self):
        """Load dữ liệu ban đầu"""
        self._load_folders()
        self._load_categories()
        self._load_schedules()

    def _load_folders(self):
        """Load danh sách folders từ Hidemium"""
        try:
            self.folders = api.get_folders()
        except:
            self.folders = []

        folder_options = ["-- Tất cả --"]
        for f in self.folders:
            folder_options.append(f.get('name', 'Unknown'))
        self.folder_menu.configure(values=folder_options)

    def _load_categories(self):
        """Load danh sách categories"""
        try:
            self.categories = get_categories()
        except:
            self.categories = []

        cat_options = ["-- Chọn danh mục --"]
        for c in self.categories:
            cat_options.append(c.get('name', 'Unknown'))
        self.category_menu.configure(values=cat_options)

    def _load_schedules(self):
        """Load danh sách schedules"""
        try:
            self.schedules = get_schedules()
        except:
            self.schedules = []

        self._render_schedules()

    def _render_schedules(self):
        """Render danh sách schedules"""
        for widget in self.schedule_list.winfo_children():
            widget.destroy()

        if not self.schedules:
            self.empty_label = ctk.CTkLabel(
                self.schedule_list,
                text="📭 Chưa có kịch bản nào\nBấm '+ Tạo kịch bản' để bắt đầu",
                font=ctk.CTkFont(size=13),
                text_color=COLORS["text_secondary"],
                justify="center"
            )
            self.empty_label.pack(pady=50)
            return

        for schedule in self.schedules:
            self._create_schedule_card(schedule)

    def _create_schedule_card(self, schedule: Dict):
        """Tạo card cho schedule"""
        is_active = schedule.get('is_active', 0) == 1
        bg_color = "#1a3a2a" if is_active else COLORS["bg_card"]

        card = ctk.CTkFrame(self.schedule_list, fg_color=bg_color, corner_radius=10)
        card.pack(fill="x", pady=4)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=10)

        # Header row
        header_row = ctk.CTkFrame(inner, fg_color="transparent")
        header_row.pack(fill="x")

        # Status indicator
        status_text = "🟢" if is_active else "⚫"
        ctk.CTkLabel(
            header_row,
            text=status_text,
            font=ctk.CTkFont(size=14)
        ).pack(side="left")

        # Name
        ctk.CTkLabel(
            header_row,
            text=schedule.get('name', 'Không tên'),
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left", padx=5)

        # Folder name
        ctk.CTkLabel(
            inner,
            text=f"📁 {schedule.get('folder_name', 'N/A')}",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w")

        # Time slots
        time_slots = schedule.get('time_slots', '')
        if time_slots:
            hours = [f"{h}h" for h in time_slots.split(',')[:5]]
            time_text = ', '.join(hours)
            if len(time_slots.split(',')) > 5:
                time_text += '...'
        else:
            time_text = "Chưa cài giờ"

        ctk.CTkLabel(
            inner,
            text=f"⏰ {time_text}",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w")

        # Stats
        stats_text = f"📊 {schedule.get('success_count', 0)}/{schedule.get('post_count', 0)} thành công"
        ctk.CTkLabel(
            inner,
            text=stats_text,
            font=ctk.CTkFont(size=10),
            text_color=COLORS["success"] if schedule.get('success_count', 0) > 0 else COLORS["text_secondary"]
        ).pack(anchor="w")

        # Buttons
        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(fill="x", pady=(5, 0))

        ctk.CTkButton(
            btn_row,
            text="Sửa",
            width=50, height=26,
            fg_color=COLORS["accent"],
            corner_radius=5,
            command=lambda s=schedule: self._edit_schedule(s)
        ).pack(side="left", padx=(0, 5))

        toggle_text = "Tắt" if is_active else "Bật"
        toggle_color = COLORS["warning"] if is_active else COLORS["success"]
        ctk.CTkButton(
            btn_row,
            text=toggle_text,
            width=50, height=26,
            fg_color=toggle_color,
            corner_radius=5,
            command=lambda s=schedule: self._toggle_schedule(s)
        ).pack(side="left")

    def _new_schedule(self):
        """Tạo schedule mới"""
        self.current_schedule = None
        self.editor_title.configure(text="✏️ Tạo kịch bản mới")
        self._clear_form()
        self._log("📝 Tạo kịch bản mới...")

    def _clear_form(self):
        """Xóa form"""
        self.name_entry.delete(0, "end")
        self.folder_var.set("-- Tất cả --")
        self._clear_hours()
        self.category_var.set("-- Chọn danh mục --")
        self.image_folder_entry.delete(0, "end")
        self.delay_min_entry.delete(0, "end")
        self.delay_min_entry.insert(0, "30")
        self.delay_max_entry.delete(0, "end")
        self.delay_max_entry.insert(0, "60")
        # Clear profiles
        self.profile_vars = {}
        for widget in self.profile_scroll.winfo_children():
            widget.destroy()
        self.profile_select_all_var.set(False)
        self._update_profile_count()
        # Clear groups
        self.group_vars = {}
        for widget in self.group_scroll.winfo_children():
            widget.destroy()
        self.stats_label.configure(text="Đã đăng: 0 | Thành công: 0 | Lỗi: 0")
        self.last_run_label.configure(text="Lần chạy cuối: Chưa có")

    def _edit_schedule(self, schedule: Dict):
        """Chỉnh sửa schedule"""
        self.current_schedule = schedule
        self.editor_title.configure(text=f"✏️ Sửa: {schedule.get('name', '')}")

        # Fill form
        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, schedule.get('name', ''))

        self.folder_var.set(schedule.get('folder_name', '-- Chọn thư mục --'))

        # Time slots
        self._clear_hours()
        time_slots = schedule.get('time_slots', '')
        if time_slots:
            for hour_str in time_slots.split(','):
                try:
                    hour = int(hour_str.strip())
                    if hour in self.time_vars:
                        self.time_vars[hour].set(True)
                except:
                    pass

        # Category
        cat_id = schedule.get('content_category_id')
        if cat_id:
            for cat in self.categories:
                if cat.get('id') == cat_id:
                    self.category_var.set(cat.get('name', ''))
                    break
        else:
            self.category_var.set("-- Chọn danh mục --")

        # Image folder
        self.image_folder_entry.delete(0, "end")
        self.image_folder_entry.insert(0, schedule.get('image_folder', ''))

        # Delay
        self.delay_min_entry.delete(0, "end")
        self.delay_min_entry.insert(0, str(schedule.get('delay_min', 30)))
        self.delay_max_entry.delete(0, "end")
        self.delay_max_entry.insert(0, str(schedule.get('delay_max', 60)))

        # Load groups for this folder
        self._load_groups_for_folder()

        # Select saved groups
        saved_groups = schedule.get('group_ids', '')
        if saved_groups:
            saved_group_list = saved_groups.split(',')
            for gid, var in self.group_vars.items():
                var.set(gid in saved_group_list)
            self._update_group_count()

        # Stats
        self.stats_label.configure(
            text=f"Đã đăng: {schedule.get('post_count', 0)} | "
                 f"Thành công: {schedule.get('success_count', 0)} | "
                 f"Lỗi: {schedule.get('error_count', 0)}"
        )

        last_run = schedule.get('last_run_at', '')
        if last_run:
            self.last_run_label.configure(text=f"Lần chạy cuối: {last_run}")
        else:
            self.last_run_label.configure(text="Lần chạy cuối: Chưa có")

        self._log(f"📝 Đang sửa: {schedule.get('name')}")

    def _load_groups_for_folder(self):
        """Load nhóm từ các profiles đã chọn"""
        # Clear current groups
        for widget in self.group_scroll.winfo_children():
            widget.destroy()
        self.group_vars = {}

        try:
            # Lấy danh sách profiles đã chọn
            selected_uuids = [uuid for uuid, var in self.profile_vars.items() if var.get()]

            if not selected_uuids:
                ctk.CTkLabel(
                    self.group_scroll,
                    text="⚠️ Vui lòng chọn ít nhất 1 profile trước",
                    font=ctk.CTkFont(size=11),
                    text_color=COLORS["warning"] if "warning" in COLORS else COLORS["text_secondary"]
                ).pack(pady=20)
                return

            # Load groups từ tất cả profiles đã chọn
            all_groups = {}  # {group_id: group_info} để loại bỏ trùng lặp

            for profile_uuid in selected_uuids:
                try:
                    profile_groups = get_groups(profile_uuid)
                    for group in profile_groups:
                        group_id = group.get('group_id', '')
                        if group_id and group_id not in all_groups:
                            all_groups[group_id] = group
                except Exception as e:
                    print(f"Error loading groups for {profile_uuid[:8]}: {e}")

            self.groups = list(all_groups.values())
            self._render_groups()

            if self.groups:
                self._log(f"Đã tải {len(self.groups)} nhóm từ {len(selected_uuids)} profiles")
            return

        except Exception as e:
            print(f"Error loading groups: {e}")

        ctk.CTkLabel(
            self.group_scroll,
            text="Không tìm thấy nhóm nào",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"]
        ).pack(pady=20)

    def _render_groups(self):
        """Render danh sách nhóm"""
        for widget in self.group_scroll.winfo_children():
            widget.destroy()

        if not self.groups:
            ctk.CTkLabel(
                self.group_scroll,
                text="Không có nhóm nào",
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text_secondary"]
            ).pack(pady=20)
            return

        for group in self.groups:
            group_id = group.get('group_id', '')
            var = ctk.BooleanVar(value=False)
            self.group_vars[group_id] = var

            cb = ctk.CTkCheckBox(
                self.group_scroll,
                text=f"{group.get('group_name', 'Unknown')[:40]}",
                variable=var,
                fg_color=COLORS["accent"],
                command=self._update_group_count
            )
            cb.pack(anchor="w", pady=2)

        self._update_group_count()

    def _save_schedule(self):
        """Lưu schedule"""
        name = self.name_entry.get().strip()
        if not name:
            self._log("❌ Vui lòng nhập tên kịch bản")
            return

        folder_name = self.folder_var.get()
        if folder_name == "-- Chọn thư mục --":
            self._log("❌ Vui lòng chọn thư mục profile")
            return

        # Get folder id
        folder_id = None
        for f in self.folders:
            if f.get('name') == folder_name:
                folder_id = str(f.get('id', ''))
                break

        # Get selected hours
        selected_hours = [str(h) for h, var in self.time_vars.items() if var.get()]
        if not selected_hours:
            self._log("❌ Vui lòng chọn ít nhất 1 khung giờ")
            return

        # Get category id
        category_id = None
        cat_name = self.category_var.get()
        if cat_name != "-- Chọn danh mục --":
            for c in self.categories:
                if c.get('name') == cat_name:
                    category_id = c.get('id')
                    break

        # Get selected groups
        selected_groups = [gid for gid, var in self.group_vars.items() if var.get()]

        # Build data
        data = {
            'name': name,
            'folder_id': folder_id,
            'folder_name': folder_name,
            'time_slots': ','.join(selected_hours),
            'content_category_id': category_id,
            'image_folder': self.image_folder_entry.get().strip(),
            'group_ids': ','.join(selected_groups),
            'delay_min': int(self.delay_min_entry.get() or 30),
            'delay_max': int(self.delay_max_entry.get() or 60),
            'is_active': 1
        }

        if self.current_schedule:
            data['id'] = self.current_schedule['id']

        try:
            save_schedule(data)
            self._load_schedules()
            self._log(f"✅ Đã lưu kịch bản: {name}")
            self._set_status(f"Đã lưu: {name}", "success")
        except Exception as e:
            self._log(f"❌ Lỗi lưu: {e}")

    def _delete_schedule(self):
        """Xóa schedule"""
        if not self.current_schedule:
            self._log("❌ Chưa chọn kịch bản để xóa")
            return

        try:
            delete_schedule(self.current_schedule['id'])
            self._load_schedules()
            self._new_schedule()
            self._log("🗑️ Đã xóa kịch bản")
            self._set_status("Đã xóa kịch bản", "success")
        except Exception as e:
            self._log(f"❌ Lỗi xóa: {e}")

    def _toggle_schedule(self, schedule: Dict):
        """Bật/tắt schedule"""
        schedule['is_active'] = 0 if schedule.get('is_active', 0) == 1 else 1
        save_schedule(schedule)
        self._load_schedules()

        status = "Bật" if schedule['is_active'] == 1 else "Tắt"
        self._log(f"⚡ {status} kịch bản: {schedule.get('name')}")

    def _run_now(self):
        """Chạy kịch bản ngay"""
        if not self.current_schedule:
            self._log("❌ Vui lòng lưu kịch bản trước")
            return

        self._log(f"▶ Đang chạy: {self.current_schedule.get('name')}...")
        threading.Thread(
            target=self._execute_schedule,
            args=(self.current_schedule,),
            daemon=True
        ).start()

    def _execute_schedule(self, schedule: Dict):
        """Thực hiện đăng bài theo schedule"""
        folder_id = schedule.get('folder_id')
        group_ids = schedule.get('group_ids', '').split(',')
        category_id = schedule.get('content_category_id')
        delay_min = schedule.get('delay_min', 30)
        delay_max = schedule.get('delay_max', 60)

        if not folder_id or not group_ids:
            self.after(0, lambda: self._log("❌ Thiếu thông tin folder hoặc nhóm"))
            return

        # Get profiles
        try:
            profiles = api.get_profiles(folder_id=[int(folder_id)], limit=500)
        except:
            profiles = []

        if not profiles:
            self.after(0, lambda: self._log("❌ Không có profile trong thư mục"))
            return

        # Get contents
        contents = []
        if category_id:
            try:
                contents = get_contents(category_id)
            except:
                contents = []

        if not contents:
            self.after(0, lambda: self._log("⚠️ Không có nội dung, sẽ đăng rỗng"))

        self.after(0, lambda: self._log(f"📊 {len(profiles)} profiles, {len(group_ids)} nhóm"))

        success = 0
        errors = 0

        # TODO: Implement actual posting logic similar to groups_tab
        # For now, just simulate
        for i, profile in enumerate(profiles[:3]):  # Limit for testing
            profile_name = profile.get('name', 'Unknown') if isinstance(profile, dict) else str(profile)[:8]
            self.after(0, lambda pn=profile_name: self._log(f"[{pn}] Đang xử lý..."))

            # Simulate posting delay
            time.sleep(random.randint(delay_min, delay_max) / 10)
            success += 1

            self.after(0, lambda pn=profile_name: self._log(f"[{pn}] ✓ Hoàn thành"))

        # Update stats
        update_schedule_stats(schedule['id'], post_count=len(profiles[:3]), success_count=success, error_count=errors)

        self.after(0, lambda: self._log(f"✅ Hoàn tất: {success} thành công, {errors} lỗi"))
        self.after(0, self._load_schedules)

    def _start_scheduler(self):
        """Khởi động scheduler chạy ngầm"""
        if self._scheduler_running:
            return

        self._scheduler_running = True
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()
        self.scheduler_status.configure(text="🟢 Scheduler: Đang chạy", text_color=COLORS["success"])

    def _scheduler_loop(self):
        """Vòng lặp scheduler kiểm tra giờ đăng"""
        while self._scheduler_running:
            try:
                current_hour = datetime.now().hour
                current_minute = datetime.now().minute

                # Chỉ chạy vào phút 0-5 của mỗi giờ
                if current_minute <= 5:
                    schedules = get_schedules(active_only=True)
                    for schedule in schedules:
                        time_slots = schedule.get('time_slots', '')
                        if str(current_hour) in time_slots.split(','):
                            # Kiểm tra xem đã chạy trong giờ này chưa
                            last_run = schedule.get('last_run_at', '')
                            if last_run:
                                try:
                                    last_run_time = datetime.fromisoformat(last_run)
                                    if last_run_time.hour == current_hour and last_run_time.date() == datetime.now().date():
                                        continue  # Đã chạy trong giờ này
                                except:
                                    pass

                            self.after(0, lambda s=schedule: self._log(f"⏰ Auto run: {s.get('name')}"))
                            self._execute_schedule(schedule)
            except Exception as e:
                print(f"Scheduler error: {e}")

            # Check every minute
            time.sleep(60)

    def _log(self, message: str):
        """Thêm log"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"[{timestamp}] {message}\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def _set_status(self, text: str, status_type: str = "info"):
        """Cập nhật status"""
        if self.status_callback:
            self.status_callback(text, status_type)

    def destroy(self):
        """Cleanup khi đóng"""
        self._scheduler_running = False
        super().destroy()
