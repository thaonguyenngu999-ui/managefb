"""
Tab Đăng Nhóm - Quét nhóm, đăng bài và đẩy tin vào các nhóm Facebook
"""
import customtkinter as ctk
from typing import List, Dict, Optional
import threading
import random
import os
import re
import time
from datetime import datetime, date
from tkinter import filedialog
from config import COLORS
from widgets import ModernButton, ModernEntry
from db import (
    get_profiles, get_groups, save_group, delete_group,
    update_group_selection, get_selected_groups, sync_groups, clear_groups,
    get_contents, get_categories, save_post_history, get_post_history
)
from api_service import api

# Import for web scraping
import requests
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


class GroupsTab(ctk.CTkFrame):
    """Tab Đăng Nhóm - Quét, đăng bài và đẩy tin vào các nhóm"""

    def __init__(self, master, status_callback=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.status_callback = status_callback
        self.profiles: List[Dict] = []
        self.groups: List[Dict] = []
        self.current_profile_uuid: Optional[str] = None
        self.selected_group_ids: List[int] = []
        self.contents: List[Dict] = []
        self.categories: List[Dict] = []
        self.posted_urls: List[Dict] = []  # Lưu URLs đã đăng
        self._is_scanning = False
        self._is_posting = False
        self._is_boosting = False

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

        ModernButton(
            header_inner,
            text="Làm mới",
            icon="🔄",
            variant="secondary",
            command=self._load_profiles,
            width=100
        ).pack(side="left")

        self.profile_status = ctk.CTkLabel(
            header_inner,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        )
        self.profile_status.pack(side="right")

        # ========== TABVIEW - 3 Sub-tabs ==========
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

        # Tab 3: Đẩy tin
        self.tab_boost = self.tabview.add("Đẩy tin")
        self._create_boost_tab()

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

        headers = [("", 30), ("ID", 50), ("Tên nhóm", 220), ("Group ID", 150), ("Thành viên", 90), ("Ngày quét", 100)]
        for text, width in headers:
            ctk.CTkLabel(
                table_header,
                text=text,
                width=width,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=COLORS["text_primary"]
            ).pack(side="left", padx=3)

        # Groups list
        self.scan_list = ctk.CTkScrollableFrame(self.tab_scan, fg_color="transparent")
        self.scan_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))

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
        left_panel = ctk.CTkFrame(main_container, fg_color=COLORS["bg_card"], corner_radius=10, width=350)
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

        self.select_all_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            left_header,
            text="Tất cả",
            variable=self.select_all_var,
            fg_color=COLORS["accent"],
            width=60,
            command=self._toggle_select_all
        ).pack(side="right")

        self.post_stats = ctk.CTkLabel(
            left_panel,
            text="Đã chọn: 0 / 0",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["accent"]
        )
        self.post_stats.pack(anchor="w", padx=10, pady=(0, 5))

        # Groups checkboxes list
        self.post_groups_list = ctk.CTkScrollableFrame(left_panel, fg_color="transparent")
        self.post_groups_list.pack(fill="both", expand=True, padx=5, pady=(0, 10))

        self.post_empty_label = ctk.CTkLabel(
            self.post_groups_list,
            text="Chưa có nhóm\nQuét nhóm trước",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        )
        self.post_empty_label.pack(pady=30)

        # ========== RIGHT PANEL - Post Content ==========
        right_panel = ctk.CTkFrame(main_container, fg_color=COLORS["bg_card"], corner_radius=10)
        right_panel.pack(side="right", fill="both", expand=True)

        # Scrollable right panel
        right_scroll = ctk.CTkScrollableFrame(right_panel, fg_color="transparent")
        right_scroll.pack(fill="both", expand=True, padx=5, pady=5)

        # Right header
        ctk.CTkLabel(
            right_scroll,
            text="Nội dung đăng",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=10, pady=(10, 5))

        # Category selector
        cat_row = ctk.CTkFrame(right_scroll, fg_color="transparent")
        cat_row.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(cat_row, text="Mục:", width=80, anchor="w").pack(side="left")
        self.category_var = ctk.StringVar(value="Mặc định")
        self.category_menu = ctk.CTkOptionMenu(
            cat_row,
            variable=self.category_var,
            values=["Mặc định"],
            fg_color=COLORS["bg_secondary"],
            button_color=COLORS["accent"],
            width=180,
            command=self._on_category_change
        )
        self.category_menu.pack(side="left", padx=5)

        # Random content checkbox
        self.random_content_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            cat_row,
            text="Random nội dung",
            variable=self.random_content_var,
            fg_color=COLORS["success"],
            command=self._toggle_random_content
        ).pack(side="left", padx=10)

        # Content selector (disabled when random)
        content_row = ctk.CTkFrame(right_scroll, fg_color="transparent")
        content_row.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(content_row, text="Tin đăng:", width=80, anchor="w").pack(side="left")
        self.content_var = ctk.StringVar(value="-- Random từ mục --")
        self.content_menu = ctk.CTkOptionMenu(
            content_row,
            variable=self.content_var,
            values=["-- Random từ mục --"],
            fg_color=COLORS["bg_secondary"],
            button_color=COLORS["accent"],
            width=250,
            command=self._on_content_change
        )
        self.content_menu.pack(side="left", padx=5)

        # Content preview
        ctk.CTkLabel(
            right_scroll,
            text="Nội dung / Mô tả:",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=10, pady=(10, 3))

        self.content_preview = ctk.CTkTextbox(
            right_scroll,
            fg_color=COLORS["bg_secondary"],
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont(size=11),
            height=100
        )
        self.content_preview.pack(fill="x", padx=10, pady=(0, 5))
        self.content_preview.configure(state="disabled")

        # ===== IMAGE SECTION =====
        img_section = ctk.CTkFrame(right_scroll, fg_color=COLORS["bg_secondary"], corner_radius=8)
        img_section.pack(fill="x", padx=10, pady=5)

        img_header = ctk.CTkFrame(img_section, fg_color="transparent")
        img_header.pack(fill="x", padx=10, pady=(8, 5))

        self.attach_img_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            img_header,
            text="Kèm hình ảnh",
            variable=self.attach_img_var,
            fg_color=COLORS["accent"],
            command=self._toggle_attach_image
        ).pack(side="left")

        # Image folder path
        img_path_row = ctk.CTkFrame(img_section, fg_color="transparent")
        img_path_row.pack(fill="x", padx=10, pady=3)

        ctk.CTkLabel(img_path_row, text="Thư mục ảnh:", width=90, anchor="w",
                     font=ctk.CTkFont(size=11)).pack(side="left")
        self.img_folder_entry = ModernEntry(img_path_row, placeholder="Đường dẫn thư mục...", width=200)
        self.img_folder_entry.pack(side="left", padx=5)
        self.img_folder_entry.configure(state="disabled")

        ctk.CTkButton(
            img_path_row,
            text="Chọn",
            width=60,
            height=26,
            fg_color=COLORS["accent"],
            corner_radius=5,
            command=self._select_image_folder
        ).pack(side="left", padx=3)

        # Image count
        img_count_row = ctk.CTkFrame(img_section, fg_color="transparent")
        img_count_row.pack(fill="x", padx=10, pady=(3, 8))

        ctk.CTkLabel(img_count_row, text="Số ảnh random:", width=90, anchor="w",
                     font=ctk.CTkFont(size=11)).pack(side="left")
        self.img_count_entry = ModernEntry(img_count_row, placeholder="5", width=60)
        self.img_count_entry.pack(side="left", padx=5)
        self.img_count_entry.insert(0, "5")
        self.img_count_entry.configure(state="disabled")

        self.img_count_label = ctk.CTkLabel(
            img_count_row,
            text="(Tổng: 0 ảnh)",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_secondary"]
        )
        self.img_count_label.pack(side="left", padx=5)

        # ===== POSTING OPTIONS =====
        options_frame = ctk.CTkFrame(right_scroll, fg_color=COLORS["bg_secondary"], corner_radius=8)
        options_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            options_frame,
            text="Tùy chọn đăng:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=10, pady=(8, 5))

        options_inner = ctk.CTkFrame(options_frame, fg_color="transparent")
        options_inner.pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkLabel(options_inner, text="Delay (giây):", width=80, anchor="w",
                     font=ctk.CTkFont(size=11)).pack(side="left")
        self.delay_entry = ModernEntry(options_inner, placeholder="5", width=60)
        self.delay_entry.pack(side="left", padx=3)
        self.delay_entry.insert(0, "5")

        self.random_delay_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            options_inner,
            text="Random (1-10s)",
            variable=self.random_delay_var,
            fg_color=COLORS["accent"],
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=10)

        # Post buttons
        post_btn_frame = ctk.CTkFrame(right_scroll, fg_color="transparent")
        post_btn_frame.pack(fill="x", padx=10, pady=10)

        ModernButton(
            post_btn_frame,
            text="Đăng tường",
            icon="📤",
            variant="success",
            command=self._start_posting,
            width=120
        ).pack(side="left", padx=3)

        ModernButton(
            post_btn_frame,
            text="Dừng",
            icon="⏹️",
            variant="danger",
            command=self._stop_posting,
            width=80
        ).pack(side="left", padx=3)

        # Progress
        self.post_progress = ctk.CTkProgressBar(
            right_scroll,
            fg_color=COLORS["bg_secondary"],
            progress_color=COLORS["success"]
        )
        self.post_progress.pack(fill="x", padx=10, pady=(0, 5))
        self.post_progress.set(0)

        self.post_status_label = ctk.CTkLabel(
            right_scroll,
            text="Tiến trình: 0 / 0",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"]
        )
        self.post_status_label.pack(anchor="w", padx=10, pady=(0, 5))

        # ===== POSTED URLS LOG =====
        ctk.CTkLabel(
            right_scroll,
            text="Nhật ký đăng tường:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=10, pady=(10, 5))

        # Posted URLs table header
        url_header = ctk.CTkFrame(right_scroll, fg_color=COLORS["bg_secondary"], corner_radius=5, height=28)
        url_header.pack(fill="x", padx=10, pady=(0, 3))
        url_header.pack_propagate(False)

        headers = [("Nhóm", 150), ("Link bài đăng", 250), ("Thời gian", 80)]
        for text, width in headers:
            ctk.CTkLabel(
                url_header,
                text=text,
                width=width,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=COLORS["text_primary"]
            ).pack(side="left", padx=3)

        # Posted URLs list
        self.posted_urls_list = ctk.CTkScrollableFrame(right_scroll, fg_color="transparent", height=120)
        self.posted_urls_list.pack(fill="x", padx=10, pady=(0, 10))

        self.posted_empty = ctk.CTkLabel(
            self.posted_urls_list,
            text="Chưa có bài đăng nào",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"]
        )
        self.posted_empty.pack(pady=20)

    def _create_boost_tab(self):
        """Tạo tab Đẩy tin (Bình luận)"""
        # Main container
        main_container = ctk.CTkFrame(self.tab_boost, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=5, pady=5)

        # ========== LEFT PANEL - Posted URLs List ==========
        left_panel = ctk.CTkFrame(main_container, fg_color=COLORS["bg_card"], corner_radius=10, width=400)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)

        # Header
        left_header = ctk.CTkFrame(left_panel, fg_color="transparent")
        left_header.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            left_header,
            text="Danh sách bài đã đăng",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left")

        ModernButton(
            left_header,
            text="Làm mới",
            icon="🔄",
            variant="secondary",
            command=self._load_today_posts,
            width=90
        ).pack(side="right")

        # Filter by date
        date_row = ctk.CTkFrame(left_panel, fg_color="transparent")
        date_row.pack(fill="x", padx=10, pady=(0, 5))

        ctk.CTkLabel(date_row, text="Lọc:", font=ctk.CTkFont(size=11)).pack(side="left")

        self.date_filter_var = ctk.StringVar(value="Hôm nay")
        self.date_filter_menu = ctk.CTkOptionMenu(
            date_row,
            variable=self.date_filter_var,
            values=["Hôm nay", "7 ngày", "30 ngày", "Tất cả"],
            fg_color=COLORS["bg_secondary"],
            button_color=COLORS["accent"],
            width=100,
            command=self._on_date_filter_change
        )
        self.date_filter_menu.pack(side="left", padx=5)

        self.boost_stats = ctk.CTkLabel(
            date_row,
            text="0 bài",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["accent"]
        )
        self.boost_stats.pack(side="right")

        # Select all for boost
        self.boost_select_all_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            left_panel,
            text="Chọn tất cả",
            variable=self.boost_select_all_var,
            fg_color=COLORS["accent"],
            command=self._toggle_select_all_boost
        ).pack(anchor="w", padx=10, pady=(0, 5))

        # Posted URLs list for boost
        self.boost_urls_list = ctk.CTkScrollableFrame(left_panel, fg_color="transparent")
        self.boost_urls_list.pack(fill="both", expand=True, padx=5, pady=(0, 10))

        self.boost_empty_label = ctk.CTkLabel(
            self.boost_urls_list,
            text="Chưa có bài đăng nào\nĐăng bài ở tab trước",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        )
        self.boost_empty_label.pack(pady=40)

        # ========== RIGHT PANEL - Comment Content ==========
        right_panel = ctk.CTkFrame(main_container, fg_color=COLORS["bg_card"], corner_radius=10)
        right_panel.pack(side="right", fill="both", expand=True)

        # Header
        ctk.CTkLabel(
            right_panel,
            text="Nội dung bình luận",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=15, pady=(15, 10))

        # Comment content
        ctk.CTkLabel(
            right_panel,
            text="Nội dung comment (mỗi dòng 1 comment, sẽ random):",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=15, pady=(0, 5))

        self.comment_textbox = ctk.CTkTextbox(
            right_panel,
            fg_color=COLORS["bg_secondary"],
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont(size=12),
            height=150
        )
        self.comment_textbox.pack(fill="x", padx=15, pady=(0, 10))
        self.comment_textbox.insert("1.0", "Hay quá!\nCảm ơn bạn!\nThông tin hữu ích!\nĐã lưu lại!")

        # Comment options
        options_row = ctk.CTkFrame(right_panel, fg_color="transparent")
        options_row.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(options_row, text="Delay (giây):", width=80, anchor="w").pack(side="left")
        self.comment_delay_entry = ModernEntry(options_row, placeholder="3", width=60)
        self.comment_delay_entry.pack(side="left", padx=5)
        self.comment_delay_entry.insert(0, "3")

        self.random_comment_delay_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            options_row,
            text="Random delay (1-5s)",
            variable=self.random_comment_delay_var,
            fg_color=COLORS["accent"]
        ).pack(side="left", padx=10)

        # Comment buttons
        btn_row = ctk.CTkFrame(right_panel, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=10)

        ModernButton(
            btn_row,
            text="Bình luận",
            icon="💬",
            variant="success",
            command=self._start_commenting,
            width=120
        ).pack(side="left", padx=5)

        ModernButton(
            btn_row,
            text="Dừng",
            icon="⏹️",
            variant="danger",
            command=self._stop_commenting,
            width=80
        ).pack(side="left", padx=5)

        # Progress
        self.comment_progress = ctk.CTkProgressBar(
            right_panel,
            fg_color=COLORS["bg_secondary"],
            progress_color=COLORS["success"]
        )
        self.comment_progress.pack(fill="x", padx=15, pady=(0, 5))
        self.comment_progress.set(0)

        self.comment_status_label = ctk.CTkLabel(
            right_panel,
            text="Tiến trình: 0 / 0",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"]
        )
        self.comment_status_label.pack(anchor="w", padx=15, pady=(0, 10))

        # ===== COMMENT LOG =====
        ctk.CTkLabel(
            right_panel,
            text="Nhật ký bình luận:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=15, pady=(10, 5))

        self.comment_log = ctk.CTkTextbox(
            right_panel,
            fg_color=COLORS["bg_secondary"],
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont(size=10),
            height=150
        )
        self.comment_log.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.comment_log.configure(state="disabled")

    # ==================== PROFILE MANAGEMENT ====================

    def _load_profiles(self):
        """Load danh sách profiles"""
        self.profiles = get_profiles()

        if not self.profiles:
            self.profile_menu.configure(values=["-- Chưa có profile --"])
            self.profile_var.set("-- Chưa có profile --")
            self.profile_status.configure(text="Chưa có profile")
            return

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

        for p in self.profiles:
            name = p.get('name', 'Unknown')
            uuid = p.get('uuid', '')
            if choice.startswith(name) and uuid[:8] in choice:
                self.current_profile_uuid = uuid
                self._load_groups_for_profile()
                self._load_contents()
                self._load_today_posts()
                break

    def _clear_groups_ui(self):
        """Clear UI khi không có profile"""
        self.groups = []
        self.selected_group_ids = []
        self._render_scan_list()
        self._render_post_groups_list()

    # ==================== SCAN TAB ====================

    def _scan_groups(self):
        """Quét danh sách nhóm"""
        if not self.current_profile_uuid:
            self._set_status("Vui lòng chọn profile trước!", "warning")
            return

        if self._is_scanning:
            return

        self._is_scanning = True
        self.scan_progress.set(0)
        self._set_status("Đang quét nhóm...", "info")

        def do_scan():
            try:
                result = self._execute_group_scan()
                self.after(0, lambda: self._on_scan_complete(result))
            except Exception as e:
                self.after(0, lambda: self._on_scan_error(str(e)))

        threading.Thread(target=do_scan, daemon=True).start()

    def _execute_group_scan(self) -> List[Dict]:
        """Thực hiện quét nhóm từ Facebook sử dụng CDP"""
        if not BS4_AVAILABLE:
            self.after(0, lambda: self._set_status("Cần cài: pip install beautifulsoup4", "error"))
            return []

        groups_found = []

        try:
            # Bước 1: Mở browser qua Hidemium API
            self.after(0, lambda: self._set_status("Đang mở browser...", "info"))
            self.after(0, lambda: self.scan_progress.set(0.05))

            result = api.open_browser(self.current_profile_uuid)
            print(f"[DEBUG] open_browser response: {result}")

            # Kiểm tra response
            status = result.get('status') or result.get('type')
            if status not in ['successfully', 'success', True]:
                if 'already' not in str(result).lower() and 'running' not in str(result).lower():
                    error = result.get('message') or result.get('title') or str(result)
                    self.after(0, lambda e=error: self._set_status(f"Lỗi mở browser: {e}", "error"))
                    return []

            # Lấy thông tin CDP
            data = result.get('data', {})
            remote_port = data.get('remote_port')
            ws_url = data.get('web_socket', '')

            if not remote_port:
                match = re.search(r':(\d+)/', ws_url)
                if match:
                    remote_port = int(match.group(1))

            if not remote_port:
                self.after(0, lambda: self._set_status("Không lấy được remote_port", "error"))
                return []

            cdp_base = f"http://127.0.0.1:{remote_port}"
            print(f"[DEBUG] CDP base: {cdp_base}")

            # Đợi browser khởi động
            self.after(0, lambda: self._set_status("Đợi browser khởi động...", "info"))
            self.after(0, lambda: self.scan_progress.set(0.1))
            time.sleep(3)

            # Bước 2: Lấy danh sách tabs qua CDP
            self.after(0, lambda: self._set_status("Đang kết nối CDP...", "info"))
            self.after(0, lambda: self.scan_progress.set(0.15))

            try:
                resp = requests.get(f"{cdp_base}/json", timeout=10)
                tabs = resp.json()
                print(f"[DEBUG] Found {len(tabs)} tabs")
            except Exception as e:
                print(f"[DEBUG] CDP connection error: {e}")
                self.after(0, lambda err=str(e): self._set_status(f"Lỗi kết nối CDP: {err}", "error"))
                return []

            # Tìm tab page (không phải devtools, extension...)
            page_ws = None
            for tab in tabs:
                if tab.get('type') == 'page':
                    page_ws = tab.get('webSocketDebuggerUrl')
                    break

            if not page_ws:
                self.after(0, lambda: self._set_status("Không tìm thấy tab page", "error"))
                return []

            print(f"[DEBUG] Page WebSocket: {page_ws}")

            # Bước 3: Kết nối WebSocket và điều khiển browser
            import websocket
            import json as json_module

            self.after(0, lambda: self._set_status("Đang mở trang nhóm...", "info"))
            self.after(0, lambda: self.scan_progress.set(0.2))

            # Kết nối WebSocket - thử nhiều cách để bypass CORS
            ws = None
            connection_error = None

            # Cách 1: Không gửi Origin (suppress_origin)
            try:
                ws = websocket.create_connection(
                    page_ws,
                    timeout=30,
                    suppress_origin=True
                )
                print("[DEBUG] WebSocket connected (suppress_origin)")
            except Exception as e1:
                connection_error = str(e1)
                print(f"[DEBUG] suppress_origin failed: {e1}")

            # Cách 2: Dùng origin parameter
            if ws is None:
                try:
                    ws = websocket.create_connection(
                        page_ws,
                        timeout=30,
                        origin=f"http://127.0.0.1:{remote_port}"
                    )
                    print("[DEBUG] WebSocket connected (origin param)")
                except Exception as e2:
                    connection_error = str(e2)
                    print(f"[DEBUG] origin param failed: {e2}")

            # Cách 3: Không có gì đặc biệt
            if ws is None:
                try:
                    ws = websocket.create_connection(page_ws, timeout=30)
                    print("[DEBUG] WebSocket connected (default)")
                except Exception as e3:
                    connection_error = str(e3)
                    print(f"[DEBUG] default failed: {e3}")

            if ws is None:
                self.after(0, lambda err=connection_error: self._set_status(f"Lỗi WebSocket: {err}", "error"))
                return []

            # Navigate đến trang nhóm
            groups_url = "https://www.facebook.com/groups/joins/?nav_source=tab&ordering=viewer_added"
            ws.send(json_module.dumps({
                "id": 1,
                "method": "Page.navigate",
                "params": {"url": groups_url}
            }))
            ws.recv()  # Nhận response

            # Đợi trang load
            self.after(0, lambda: self._set_status("Đợi trang load...", "info"))
            self.after(0, lambda: self.scan_progress.set(0.25))
            time.sleep(8)

            # Bước 4: Scroll để load nhóm
            self.after(0, lambda: self._set_status("Đang scroll load nhóm...", "info"))
            self.after(0, lambda: self.scan_progress.set(0.3))

            for i in range(10):
                # Scroll xuống
                ws.send(json_module.dumps({
                    "id": 100 + i,
                    "method": "Runtime.evaluate",
                    "params": {"expression": "window.scrollTo(0, document.body.scrollHeight);"}
                }))
                ws.recv()
                time.sleep(2)

                progress = 0.3 + (i / 10) * 0.4
                self.after(0, lambda p=progress, s=i+1: self._set_status(f"Scroll lần {s}...", "info"))
                self.after(0, lambda p=progress: self.scan_progress.set(p))

            # Bước 5: Lấy HTML content
            self.after(0, lambda: self._set_status("Đang lấy nội dung trang...", "info"))
            self.after(0, lambda: self.scan_progress.set(0.75))

            ws.send(json_module.dumps({
                "id": 200,
                "method": "Runtime.evaluate",
                "params": {"expression": "document.documentElement.outerHTML"}
            }))
            result = json_module.loads(ws.recv())
            html_content = result.get('result', {}).get('result', {}).get('value', '')

            ws.close()

            if not html_content:
                self.after(0, lambda: self._set_status("Không lấy được HTML", "error"))
                return []

            print(f"[DEBUG] Got HTML length: {len(html_content)}")

            # Bước 6: Parse HTML
            self.after(0, lambda: self._set_status("Đang phân tích...", "info"))
            self.after(0, lambda: self.scan_progress.set(0.85))

            soup = BeautifulSoup(html_content, 'html.parser')
            links = soup.find_all('a', {'aria-label': 'Xem nhóm'})

            print(f"[DEBUG] Found {len(links)} group links")
            self.after(0, lambda n=len(links): self._set_status(f"Tìm thấy {n} link nhóm...", "info"))

            for link in links:
                href = link.get('href', '')
                if '/groups/' in href:
                    match = re.search(r'/groups/([^/?]+)', href)
                    if match:
                        group_id = match.group(1)

                        if group_id in ['joins', 'feed', 'discover']:
                            continue

                        group_name = group_id

                        # Tìm tên nhóm
                        parent = link
                        for _ in range(10):
                            parent = parent.find_parent()
                            if parent is None:
                                break
                            spans = parent.find_all(['span', 'div'], recursive=False)
                            for span in spans:
                                text = span.get_text(strip=True)
                                if text and len(text) > 3 and text != "Xem nhóm" and not text.startswith('http'):
                                    if len(text) < 150:
                                        group_name = text
                                        break
                            if group_name != group_id:
                                break

                        group_url = f"https://www.facebook.com/groups/{group_id}/"

                        if not any(g['group_id'] == group_id for g in groups_found):
                            groups_found.append({
                                'group_id': group_id,
                                'group_name': group_name,
                                'group_url': group_url,
                                'member_count': 0
                            })

            self.after(0, lambda: self.scan_progress.set(0.95))
            self.after(0, lambda n=len(groups_found): self._set_status(f"Tìm thấy {n} nhóm!", "info"))

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"Scan error: {error_detail}")
            self.after(0, lambda err=str(e): self._set_status(f"Lỗi: {err}", "error"))

        return groups_found

    def _on_scan_complete(self, groups: List[Dict]):
        """Xử lý kết quả quét"""
        self._is_scanning = False
        self.scan_progress.set(1)

        if groups:
            # Lưu vào database
            sync_groups(self.current_profile_uuid, groups)
            self._load_groups_for_profile()
            self._set_status(f"Đã quét và lưu {len(groups)} nhóm!", "success")
        else:
            self._load_groups_for_profile()
            if not BS4_AVAILABLE:
                self._set_status("Cần cài: pip install beautifulsoup4 websocket-client", "warning")
            else:
                self._set_status("Không tìm thấy nhóm nào hoặc chưa đăng nhập Facebook", "warning")

    def _on_scan_error(self, error: str):
        """Xử lý lỗi quét"""
        self._is_scanning = False
        self.scan_progress.set(0)
        self._set_status(f"Lỗi: {error}", "error")

    def _load_groups_for_profile(self):
        """Load nhóm của profile"""
        if not self.current_profile_uuid:
            self.groups = []
        else:
            self.groups = get_groups(self.current_profile_uuid)

        self.selected_group_ids = [g['id'] for g in self.groups if g.get('is_selected')]
        self._render_scan_list()
        self._render_post_groups_list()
        self._update_stats()

    def _render_scan_list(self):
        """Render danh sách nhóm trong tab Quét"""
        for widget in self.scan_list.winfo_children():
            widget.destroy()

        if not self.groups:
            self.scan_empty_label = ctk.CTkLabel(
                self.scan_list,
                text="Chưa có nhóm nào\nChọn profile và bấm 'Quét nhóm'",
                font=ctk.CTkFont(size=13),
                text_color=COLORS["text_secondary"]
            )
            self.scan_empty_label.pack(pady=50)
            return

        for group in self.groups:
            self._create_scan_row(group)

    def _create_scan_row(self, group: Dict):
        """Tạo row cho group"""
        row = ctk.CTkFrame(self.scan_list, fg_color=COLORS["bg_secondary"], corner_radius=5, height=36)
        row.pack(fill="x", pady=2)
        row.pack_propagate(False)

        var = ctk.BooleanVar(value=group['id'] in self.selected_group_ids)
        cb = ctk.CTkCheckBox(
            row, text="", variable=var, width=25,
            checkbox_width=18, checkbox_height=18,
            fg_color=COLORS["accent"],
            command=lambda gid=group['id'], v=var: self._toggle_group_selection(gid, v)
        )
        cb.pack(side="left", padx=3)

        ctk.CTkLabel(row, text=str(group.get('id', '')), width=50,
                     font=ctk.CTkFont(size=10), text_color=COLORS["text_secondary"]).pack(side="left")

        name = group.get('group_name', 'Unknown')[:25]
        ctk.CTkLabel(row, text=name, width=220, font=ctk.CTkFont(size=10),
                     text_color=COLORS["text_primary"], anchor="w").pack(side="left", padx=3)

        gid = group.get('group_id', '')[:18]
        ctk.CTkLabel(row, text=gid, width=150, font=ctk.CTkFont(size=9),
                     text_color=COLORS["accent"], anchor="w").pack(side="left", padx=3)

        members = group.get('member_count', 0)
        ctk.CTkLabel(row, text=f"{members:,}" if members else "-", width=90,
                     font=ctk.CTkFont(size=10), text_color=COLORS["text_secondary"]).pack(side="left")

        created = group.get('created_at', '')[:10] if group.get('created_at') else '-'
        ctk.CTkLabel(row, text=created, width=100, font=ctk.CTkFont(size=9),
                     text_color=COLORS["text_secondary"]).pack(side="left")

        ctk.CTkButton(row, text="X", width=25, height=22, fg_color=COLORS["error"],
                      hover_color="#ff4757", corner_radius=4,
                      command=lambda gid=group['id']: self._delete_group(gid)).pack(side="right", padx=3)

    def _toggle_group_selection(self, group_id: int, var: ctk.BooleanVar):
        """Toggle chọn group"""
        is_selected = var.get()
        update_group_selection(group_id, 1 if is_selected else 0)

        if is_selected and group_id not in self.selected_group_ids:
            self.selected_group_ids.append(group_id)
        elif not is_selected and group_id in self.selected_group_ids:
            self.selected_group_ids.remove(group_id)

        self._update_stats()
        self._render_post_groups_list()

    def _delete_group(self, group_id: int):
        """Xóa group"""
        delete_group(group_id)
        if group_id in self.selected_group_ids:
            self.selected_group_ids.remove(group_id)
        self._load_groups_for_profile()

    def _clear_all_groups(self):
        """Xóa tất cả groups"""
        if not self.current_profile_uuid:
            return
        clear_groups(self.current_profile_uuid)
        self.selected_group_ids = []
        self._load_groups_for_profile()

    def _update_stats(self):
        """Cập nhật thống kê"""
        total = len(self.groups)
        selected = len(self.selected_group_ids)
        self.scan_stats.configure(text=f"Tổng: {total} nhóm")
        self.post_stats.configure(text=f"Đã chọn: {selected} / {total}")

    # ==================== POST TAB ====================

    def _render_post_groups_list(self):
        """Render danh sách nhóm với checkbox"""
        for widget in self.post_groups_list.winfo_children():
            widget.destroy()

        if not self.groups:
            self.post_empty_label = ctk.CTkLabel(
                self.post_groups_list,
                text="Chưa có nhóm\nQuét nhóm trước",
                font=ctk.CTkFont(size=12),
                text_color=COLORS["text_secondary"]
            )
            self.post_empty_label.pack(pady=30)
            return

        for group in self.groups:
            row = ctk.CTkFrame(self.post_groups_list, fg_color="transparent", height=30)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)

            var = ctk.BooleanVar(value=group['id'] in self.selected_group_ids)
            cb = ctk.CTkCheckBox(
                row,
                text=group.get('group_name', 'Unknown')[:30],
                variable=var, width=280,
                checkbox_width=16, checkbox_height=16,
                fg_color=COLORS["accent"],
                font=ctk.CTkFont(size=10),
                command=lambda gid=group['id'], v=var: self._toggle_group_selection_post(gid, v)
            )
            cb.pack(side="left", padx=3)

    def _toggle_group_selection_post(self, group_id: int, var: ctk.BooleanVar):
        """Toggle group từ tab Đăng"""
        is_selected = var.get()
        update_group_selection(group_id, 1 if is_selected else 0)

        if is_selected and group_id not in self.selected_group_ids:
            self.selected_group_ids.append(group_id)
        elif not is_selected and group_id in self.selected_group_ids:
            self.selected_group_ids.remove(group_id)

        self._update_stats()
        self._render_scan_list()

    def _toggle_select_all(self):
        """Toggle chọn tất cả"""
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

        if self.random_content_var.get():
            content_titles = ["-- Random từ mục --"]
        else:
            content_titles = []

        content_titles.extend([c.get('title', 'Untitled')[:35] for c in self.contents])
        self.content_menu.configure(values=content_titles)

        if self.random_content_var.get():
            self.content_var.set("-- Random từ mục --")
            self._update_preview(f"[Random từ {len(self.contents)} nội dung trong mục này]")
        else:
            self.content_var.set(content_titles[0])
            self._update_preview(self.contents[0].get('content', ''))

    def _toggle_random_content(self):
        """Toggle random content"""
        cat_id = None
        for cat in self.categories:
            if cat.get('name') == self.category_var.get():
                cat_id = cat.get('id')
                break
        if cat_id:
            self._load_contents_for_category(cat_id)

    def _on_content_change(self, choice: str):
        """Khi đổi content"""
        if choice == "-- Random từ mục --":
            self._update_preview(f"[Random từ {len(self.contents)} nội dung trong mục này]")
            return

        for c in self.contents:
            if c.get('title', '')[:35] == choice:
                self._update_preview(c.get('content', ''))
                break

    def _update_preview(self, content: str):
        """Cập nhật preview"""
        self.content_preview.configure(state="normal")
        self.content_preview.delete("1.0", "end")
        self.content_preview.insert("1.0", content)
        self.content_preview.configure(state="disabled")

    def _toggle_attach_image(self):
        """Toggle đính kèm ảnh"""
        if self.attach_img_var.get():
            self.img_folder_entry.configure(state="normal")
            self.img_count_entry.configure(state="normal")
        else:
            self.img_folder_entry.configure(state="disabled")
            self.img_count_entry.configure(state="disabled")

    def _select_image_folder(self):
        """Chọn thư mục ảnh"""
        if not self.attach_img_var.get():
            self.attach_img_var.set(True)
            self.img_folder_entry.configure(state="normal")
            self.img_count_entry.configure(state="normal")

        path = filedialog.askdirectory(title="Chọn thư mục chứa hình ảnh")
        if path:
            self.img_folder_entry.delete(0, "end")
            self.img_folder_entry.insert(0, path)
            count = self._count_images_in_folder(path)
            self.img_count_label.configure(text=f"(Tổng: {count} ảnh)")

    def _count_images_in_folder(self, folder_path: str) -> int:
        """Đếm số ảnh trong thư mục"""
        if not os.path.isdir(folder_path):
            return 0
        img_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
        count = 0
        for f in os.listdir(folder_path):
            if os.path.splitext(f)[1].lower() in img_extensions:
                count += 1
        return count

    def _get_random_images(self, folder_path: str, count: int) -> List[str]:
        """Lấy random ảnh từ thư mục"""
        if not os.path.isdir(folder_path):
            return []
        img_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
        images = []
        for f in os.listdir(folder_path):
            if os.path.splitext(f)[1].lower() in img_extensions:
                images.append(os.path.join(folder_path, f))
        if len(images) <= count:
            return images
        return random.sample(images, count)

    def _get_random_content(self) -> Optional[Dict]:
        """Lấy random content hoặc content được chọn"""
        if not self.contents:
            return None

        if self.random_content_var.get():
            return random.choice(self.contents)

        selected_title = self.content_var.get()
        for c in self.contents:
            if c.get('title', '')[:35] == selected_title:
                return c
        return None

    def _start_posting(self):
        """Bắt đầu đăng bài"""
        if not self.current_profile_uuid:
            self._set_status("Vui lòng chọn profile!", "warning")
            return

        if not self.selected_group_ids:
            self._set_status("Vui lòng chọn nhóm!", "warning")
            return

        if not self.contents:
            self._set_status("Vui lòng có nội dung trong mục!", "warning")
            return

        if self._is_posting:
            return

        self._is_posting = True
        self.post_progress.set(0)
        self.posted_urls = []
        self._render_posted_urls()

        selected_groups = [g for g in self.groups if g['id'] in self.selected_group_ids]

        def do_post():
            try:
                self._execute_posting(selected_groups)
            except Exception as e:
                self.after(0, lambda: self._on_posting_error(str(e)))

        threading.Thread(target=do_post, daemon=True).start()

    def _execute_posting(self, groups: List[Dict]):
        """Thực hiện đăng bài"""
        import time

        total = len(groups)

        for i, group in enumerate(groups):
            if not self._is_posting:
                break

            group_name = group.get('group_name', 'Unknown')
            self.after(0, lambda g=group_name, n=i+1, t=total:
                       self.post_status_label.configure(text=f"Đang đăng: {g} ({n}/{t})"))

            progress = (i + 1) / total
            self.after(0, lambda p=progress: self.post_progress.set(p))

            # Get random content
            content = self._get_random_content()
            if not content:
                continue

            content_text = content.get('content', '')

            # Get random images if enabled
            images = []
            if self.attach_img_var.get():
                folder = self.img_folder_entry.get()
                try:
                    img_count = int(self.img_count_entry.get())
                except ValueError:
                    img_count = 5
                images = self._get_random_images(folder, img_count)

            # TODO: Implement actual posting via Hidemium API
            result = self._post_to_group(group, content_text, images)

            # Generate fake URL for demo
            post_url = f"https://facebook.com/groups/{group.get('group_id', '')}/posts/{random.randint(100000, 999999)}"

            # Save to history
            save_post_history({
                'profile_uuid': self.current_profile_uuid,
                'group_id': group.get('group_id'),
                'content_id': content.get('id'),
                'post_url': post_url if result else '',
                'status': 'success' if result else 'failed',
                'error_message': '' if result else 'Posting failed'
            })

            # Add to posted URLs
            if result:
                self.posted_urls.append({
                    'group_name': group_name,
                    'post_url': post_url,
                    'time': datetime.now().strftime('%H:%M:%S')
                })
                self.after(0, self._render_posted_urls)

            # Delay
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

    def _post_to_group(self, group: Dict, content: str, images: List[str]) -> bool:
        """Đăng bài vào group - placeholder"""
        import time
        time.sleep(1)
        return True

    def _on_posting_complete(self, total: int):
        """Hoàn tất đăng bài"""
        self._is_posting = False
        self.post_progress.set(1)
        self.post_status_label.configure(text=f"Hoàn tất: {total} nhóm")
        self._set_status(f"Đã đăng {total} nhóm", "success")
        self._load_today_posts()

    def _on_posting_error(self, error: str):
        """Lỗi đăng bài"""
        self._is_posting = False
        self.post_progress.set(0)
        self._set_status(f"Lỗi: {error}", "error")

    def _stop_posting(self):
        """Dừng đăng bài"""
        if self._is_posting:
            self._is_posting = False
            self._set_status("Đã dừng", "warning")

    def _render_posted_urls(self):
        """Render danh sách URLs đã đăng"""
        for widget in self.posted_urls_list.winfo_children():
            widget.destroy()

        if not self.posted_urls:
            self.posted_empty = ctk.CTkLabel(
                self.posted_urls_list,
                text="Chưa có bài đăng nào",
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text_secondary"]
            )
            self.posted_empty.pack(pady=20)
            return

        for item in self.posted_urls:
            row = ctk.CTkFrame(self.posted_urls_list, fg_color=COLORS["bg_secondary"], corner_radius=4, height=26)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)

            ctk.CTkLabel(row, text=item['group_name'][:18], width=150,
                         font=ctk.CTkFont(size=9), text_color=COLORS["text_primary"],
                         anchor="w").pack(side="left", padx=3)

            url_label = ctk.CTkLabel(row, text=item['post_url'][:40], width=250,
                                     font=ctk.CTkFont(size=9), text_color=COLORS["accent"],
                                     anchor="w", cursor="hand2")
            url_label.pack(side="left", padx=3)

            ctk.CTkLabel(row, text=item['time'], width=80,
                         font=ctk.CTkFont(size=9), text_color=COLORS["text_secondary"]).pack(side="left")

    # ==================== BOOST TAB ====================

    def _load_today_posts(self):
        """Load bài đăng theo filter"""
        if not self.current_profile_uuid:
            return

        filter_val = self.date_filter_var.get()
        if filter_val == "Hôm nay":
            limit = 50
        elif filter_val == "7 ngày":
            limit = 100
        elif filter_val == "30 ngày":
            limit = 200
        else:
            limit = 500

        posts = get_post_history(self.current_profile_uuid, limit)

        # Filter by date
        today = date.today()
        if filter_val == "Hôm nay":
            posts = [p for p in posts if p.get('created_at', '')[:10] == str(today)]
        elif filter_val == "7 ngày":
            from datetime import timedelta
            week_ago = today - timedelta(days=7)
            posts = [p for p in posts if p.get('created_at', '')[:10] >= str(week_ago)]
        elif filter_val == "30 ngày":
            from datetime import timedelta
            month_ago = today - timedelta(days=30)
            posts = [p for p in posts if p.get('created_at', '')[:10] >= str(month_ago)]

        # Only successful posts with URLs
        posts = [p for p in posts if p.get('status') == 'success' and p.get('post_url')]

        self._render_boost_urls(posts)
        self.boost_stats.configure(text=f"{len(posts)} bài")

    def _on_date_filter_change(self, choice: str):
        """Khi đổi filter ngày"""
        self._load_today_posts()

    def _render_boost_urls(self, posts: List[Dict]):
        """Render danh sách URLs để boost"""
        for widget in self.boost_urls_list.winfo_children():
            widget.destroy()

        if not posts:
            self.boost_empty_label = ctk.CTkLabel(
                self.boost_urls_list,
                text="Chưa có bài đăng nào\nĐăng bài ở tab trước",
                font=ctk.CTkFont(size=12),
                text_color=COLORS["text_secondary"]
            )
            self.boost_empty_label.pack(pady=40)
            return

        self.boost_post_vars = {}
        for post in posts:
            row = ctk.CTkFrame(self.boost_urls_list, fg_color="transparent", height=28)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)

            var = ctk.BooleanVar(value=False)
            self.boost_post_vars[post.get('id')] = var

            url = post.get('post_url', '')[:40]
            cb = ctk.CTkCheckBox(
                row,
                text=url,
                variable=var,
                width=350,
                checkbox_width=16, checkbox_height=16,
                fg_color=COLORS["accent"],
                font=ctk.CTkFont(size=10)
            )
            cb.pack(side="left", padx=3)

    def _toggle_select_all_boost(self):
        """Toggle chọn tất cả bài để boost"""
        select_all = self.boost_select_all_var.get()
        for var in self.boost_post_vars.values():
            var.set(select_all)

    def _start_commenting(self):
        """Bắt đầu bình luận"""
        if not self.current_profile_uuid:
            self._set_status("Vui lòng chọn profile!", "warning")
            return

        selected_ids = [pid for pid, var in self.boost_post_vars.items() if var.get()]
        if not selected_ids:
            self._set_status("Vui lòng chọn bài để bình luận!", "warning")
            return

        comments = self.comment_textbox.get("1.0", "end").strip().split('\n')
        comments = [c.strip() for c in comments if c.strip()]
        if not comments:
            self._set_status("Vui lòng nhập nội dung bình luận!", "warning")
            return

        if self._is_boosting:
            return

        self._is_boosting = True
        self.comment_progress.set(0)
        self._clear_comment_log()

        posts = get_post_history(self.current_profile_uuid, 500)
        selected_posts = [p for p in posts if p.get('id') in selected_ids]

        def do_comment():
            try:
                self._execute_commenting(selected_posts, comments)
            except Exception as e:
                self.after(0, lambda: self._on_commenting_error(str(e)))

        threading.Thread(target=do_comment, daemon=True).start()

    def _execute_commenting(self, posts: List[Dict], comments: List[str]):
        """Thực hiện bình luận"""
        import time

        total = len(posts)

        for i, post in enumerate(posts):
            if not self._is_boosting:
                break

            url = post.get('post_url', '')
            self.after(0, lambda n=i+1, t=total:
                       self.comment_status_label.configure(text=f"Đang comment: {n}/{t}"))

            progress = (i + 1) / total
            self.after(0, lambda p=progress: self.comment_progress.set(p))

            # Random comment
            comment = random.choice(comments)

            # TODO: Implement actual commenting via Hidemium API
            result = self._comment_on_post(post, comment)

            # Log
            timestamp = datetime.now().strftime('%H:%M:%S')
            log_text = f"[{timestamp}] {'OK' if result else 'FAIL'}: {url[:50]}... - '{comment[:30]}...'"
            self.after(0, lambda t=log_text: self._append_comment_log(t))

            # Delay
            if i < total - 1:
                if self.random_comment_delay_var.get():
                    delay = random.uniform(1, 5)
                else:
                    try:
                        delay = float(self.comment_delay_entry.get())
                    except ValueError:
                        delay = 3
                time.sleep(delay)

        self.after(0, lambda: self._on_commenting_complete(total))

    def _comment_on_post(self, post: Dict, comment: str) -> bool:
        """Bình luận vào bài - placeholder"""
        import time
        time.sleep(0.5)
        return True

    def _on_commenting_complete(self, total: int):
        """Hoàn tất bình luận"""
        self._is_boosting = False
        self.comment_progress.set(1)
        self.comment_status_label.configure(text=f"Hoàn tất: {total} bài")
        self._set_status(f"Đã comment {total} bài", "success")

    def _on_commenting_error(self, error: str):
        """Lỗi bình luận"""
        self._is_boosting = False
        self.comment_progress.set(0)
        self._set_status(f"Lỗi: {error}", "error")

    def _stop_commenting(self):
        """Dừng bình luận"""
        if self._is_boosting:
            self._is_boosting = False
            self._set_status("Đã dừng", "warning")

    def _clear_comment_log(self):
        """Clear log"""
        self.comment_log.configure(state="normal")
        self.comment_log.delete("1.0", "end")
        self.comment_log.configure(state="disabled")

    def _append_comment_log(self, text: str):
        """Thêm log"""
        self.comment_log.configure(state="normal")
        self.comment_log.insert("end", text + "\n")
        self.comment_log.see("end")
        self.comment_log.configure(state="disabled")

    def _set_status(self, text: str, status_type: str = "info"):
        """Cập nhật status"""
        if self.status_callback:
            self.status_callback(text, status_type)
