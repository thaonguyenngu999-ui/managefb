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
import unicodedata
from datetime import datetime, date
from tkinter import filedialog
from config import COLORS
from widgets import ModernButton, ModernEntry
from db import (
    get_profiles, get_groups, get_groups_for_profiles, save_group, delete_group,
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

        # Multi-profile support
        self.selected_profile_uuids: List[str] = []
        self.folders: List[Dict] = []
        self.profile_checkbox_vars: Dict = {}
        self.group_checkbox_widgets: Dict = {}
        self.group_checkbox_vars: Dict = {}

        self._create_ui()
        self._load_profiles()

    def _create_ui(self):
        """Tạo giao diện"""
        # ========== HEADER - Profile Selector with Multi-select ==========
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=12)
        header.pack(fill="x", padx=15, pady=(15, 10))

        # Row 1: Folder filter & Refresh
        header_row1 = ctk.CTkFrame(header, fg_color="transparent")
        header_row1.pack(fill="x", padx=15, pady=(12, 5))

        ctk.CTkLabel(
            header_row1,
            text="📁 Thư mục:",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_primary"]
        ).pack(side="left")

        self.folder_var = ctk.StringVar(value="-- Tất cả --")
        self.folder_menu = ctk.CTkOptionMenu(
            header_row1,
            variable=self.folder_var,
            values=["-- Tất cả --"],
            fg_color=COLORS["bg_card"],
            button_color=COLORS["accent"],
            width=180,
            command=self._on_folder_change
        )
        self.folder_menu.pack(side="left", padx=10)

        ModernButton(
            header_row1,
            text="Làm mới",
            icon="🔄",
            variant="secondary",
            command=self._load_profiles,
            width=100
        ).pack(side="left", padx=5)

        self.profile_status = ctk.CTkLabel(
            header_row1,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        )
        self.profile_status.pack(side="right")

        # Row 2: Profile selection
        header_row2 = ctk.CTkFrame(header, fg_color="transparent")
        header_row2.pack(fill="x", padx=15, pady=(0, 12))

        ctk.CTkLabel(
            header_row2,
            text="📱 Profiles:",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_primary"]
        ).pack(side="left")

        # Profile dropdown for quick single select
        self.profile_var = ctk.StringVar(value="-- Chọn profile --")
        self.profile_menu = ctk.CTkOptionMenu(
            header_row2,
            variable=self.profile_var,
            values=["-- Chọn profile --"],
            fg_color=COLORS["bg_card"],
            button_color=COLORS["accent"],
            width=250,
            command=self._on_profile_change
        )
        self.profile_menu.pack(side="left", padx=10)

        # Multi-select toggle
        self.multi_profile_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            header_row2,
            text="Multi-select",
            variable=self.multi_profile_var,
            fg_color=COLORS["accent"],
            font=ctk.CTkFont(size=11),
            command=self._toggle_multi_profile
        ).pack(side="left", padx=10)

        # Selected profiles count
        self.selected_profiles_label = ctk.CTkLabel(
            header_row2,
            text="Đã chọn: 0",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["accent"]
        )
        self.selected_profiles_label.pack(side="left", padx=5)

        # Load groups button (for multi-select mode)
        self.load_groups_btn = ModernButton(
            header_row2,
            text="Load nhóm",
            icon="📥",
            variant="secondary",
            command=self._load_groups_for_selected_profiles,
            width=100
        )
        self.load_groups_btn.pack(side="left", padx=5)

        # Multi-profile selection panel (hidden by default)
        self.multi_profile_panel = ctk.CTkFrame(header, fg_color=COLORS["bg_card"], corner_radius=8, height=120)
        self.multi_profile_panel.pack_propagate(False)
        # Don't pack initially - will be shown when multi-select is enabled

        # Inner scrollable list
        self.profile_list_scroll = ctk.CTkScrollableFrame(self.multi_profile_panel, fg_color="transparent", height=100)
        self.profile_list_scroll.pack(fill="both", expand=True, padx=5, pady=5)

        # Store profile checkbox vars
        self.profile_checkbox_vars = {}
        self.selected_profile_uuids = []
        self.folders = []

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

        # Search/Filter row
        filter_row = ctk.CTkFrame(left_panel, fg_color="transparent")
        filter_row.pack(fill="x", padx=10, pady=(0, 5))

        ctk.CTkLabel(filter_row, text="🔍", width=20).pack(side="left")
        self.group_filter_var = ctk.StringVar()
        self.group_filter_var.trace_add("write", self._on_group_filter_change)
        self.group_filter_entry = ctk.CTkEntry(
            filter_row,
            placeholder_text="Lọc theo tên nhóm...",
            textvariable=self.group_filter_var,
            fg_color=COLORS["bg_secondary"],
            width=280,
            height=28
        )
        self.group_filter_entry.pack(side="left", padx=5)

        # Groups checkboxes list
        self.post_groups_list = ctk.CTkScrollableFrame(left_panel, fg_color="transparent")
        self.post_groups_list.pack(fill="both", expand=True, padx=5, pady=(0, 10))

        # Store checkbox widgets for optimization
        self.group_checkbox_widgets = {}
        self.group_checkbox_vars = {}

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
        """Load danh sách profiles và folders"""
        self.profiles = get_profiles()

        # Load folders từ Hidemium
        try:
            self.folders = api.get_folders()
        except:
            self.folders = []

        # Update folder menu
        folder_options = ["-- Tất cả --"]
        for f in self.folders:
            folder_options.append(f.get('name', 'Unknown'))
        self.folder_menu.configure(values=folder_options)

        if not self.profiles:
            self.profile_menu.configure(values=["-- Chưa có profile --"])
            self.profile_var.set("-- Chưa có profile --")
            self.profile_status.configure(text="Chưa có profile")
            self._render_profile_list()
            return

        profile_options = ["-- Chọn profile --"]
        for p in self.profiles:
            name = p.get('name', 'Unknown')
            uuid = p.get('uuid', '')[:8]
            profile_options.append(f"{name} ({uuid})")

        self.profile_menu.configure(values=profile_options)
        self.profile_var.set("-- Chọn profile --")
        self.profile_status.configure(text=f"Có {len(self.profiles)} profiles")
        self._render_profile_list()

    def _on_folder_change(self, choice: str):
        """Khi đổi folder filter"""
        if choice == "-- Tất cả --":
            # Load all profiles
            self.profiles = get_profiles()
        else:
            # Load profiles by folder
            folder_id = None
            for f in self.folders:
                if f.get('name') == choice:
                    folder_id = f.get('uuid') or f.get('id')
                    break
            if folder_id:
                try:
                    self.profiles = api.get_profiles(folder_id=[folder_id])
                except:
                    self.profiles = get_profiles()
            else:
                self.profiles = get_profiles()

        # Update dropdown
        profile_options = ["-- Chọn profile --"]
        for p in self.profiles:
            name = p.get('name', 'Unknown')
            uuid = p.get('uuid', '')[:8]
            profile_options.append(f"{name} ({uuid})")

        self.profile_menu.configure(values=profile_options)
        self.profile_var.set("-- Chọn profile --")
        self.profile_status.configure(text=f"Có {len(self.profiles)} profiles")
        self._render_profile_list()

    def _toggle_multi_profile(self):
        """Toggle multi-profile mode"""
        if self.multi_profile_var.get():
            self.multi_profile_panel.pack(fill="x", padx=15, pady=(0, 12))
            self.profile_menu.configure(state="disabled")
            # Không auto-load để tránh lag
        else:
            self.multi_profile_panel.pack_forget()
            self.profile_menu.configure(state="normal")
            self.selected_profile_uuids = []
            self._update_selected_profiles_label()
            # Clear groups list khi tắt multi-mode
            self.groups = []
            self._render_scan_list()
            self._render_post_groups_list(force_rebuild=True)

    def _render_profile_list(self):
        """Render danh sách profiles với checkbox"""
        for widget in self.profile_list_scroll.winfo_children():
            widget.destroy()
        self.profile_checkbox_vars = {}

        if not self.profiles:
            ctk.CTkLabel(
                self.profile_list_scroll,
                text="Không có profile",
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text_secondary"]
            ).pack(pady=10)
            return

        for p in self.profiles:
            uuid = p.get('uuid', '')
            name = p.get('name', 'Unknown')

            var = ctk.BooleanVar(value=uuid in self.selected_profile_uuids)
            self.profile_checkbox_vars[uuid] = var

            cb = ctk.CTkCheckBox(
                self.profile_list_scroll,
                text=f"{name} ({uuid[:8]})",
                variable=var,
                fg_color=COLORS["accent"],
                font=ctk.CTkFont(size=10),
                command=lambda u=uuid, v=var: self._toggle_profile_selection(u, v)
            )
            cb.pack(anchor="w", pady=1)

    def _toggle_profile_selection(self, uuid: str, var: ctk.BooleanVar):
        """Toggle chọn profile - không auto-reload để tránh lag"""
        if var.get():
            if uuid not in self.selected_profile_uuids:
                self.selected_profile_uuids.append(uuid)
        else:
            if uuid in self.selected_profile_uuids:
                self.selected_profile_uuids.remove(uuid)
        self._update_selected_profiles_label()
        # Không auto-reload để tránh lag - user sẽ bấm nút Load hoặc Quét

    def _update_selected_profiles_label(self):
        """Cập nhật label số profiles đã chọn"""
        count = len(self.selected_profile_uuids)
        self.selected_profiles_label.configure(text=f"Đã chọn: {count}")

    def _load_groups_for_selected_profiles(self):
        """Load groups từ các profiles đã chọn - chạy background"""
        if not self.selected_profile_uuids and not self.current_profile_uuid:
            self._set_status("Vui lòng chọn profile trước!", "warning")
            return

        self._set_status("Đang load nhóm...", "info")

        def do_load():
            try:
                # Load groups
                if self.multi_profile_var.get() and self.selected_profile_uuids:
                    groups = get_groups_for_profiles(self.selected_profile_uuids)
                elif self.current_profile_uuid:
                    groups = get_groups(self.current_profile_uuid)
                else:
                    groups = []

                # Update UI on main thread
                self.after(0, lambda: self._on_groups_loaded(groups))
            except Exception as e:
                self.after(0, lambda: self._set_status(f"Lỗi: {e}", "error"))

        threading.Thread(target=do_load, daemon=True).start()

    def _on_groups_loaded(self, groups: List[Dict]):
        """Callback khi load groups xong"""
        self.groups = groups
        self.selected_group_ids = [g['id'] for g in self.groups if g.get('is_selected')]
        self._render_scan_list()
        self._render_post_groups_list(force_rebuild=True)
        self._update_stats()
        self._set_status(f"Đã load {len(groups)} nhóm!", "success")

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

    def _get_profiles_to_scan(self) -> List[str]:
        """Lấy danh sách profile UUIDs cần quét"""
        if self.multi_profile_var.get():
            # Multi-select mode
            return self.selected_profile_uuids.copy()
        elif self.current_profile_uuid:
            # Single-select mode
            return [self.current_profile_uuid]
        return []

    def _scan_groups(self):
        """Quét danh sách nhóm"""
        profiles_to_scan = self._get_profiles_to_scan()

        if not profiles_to_scan:
            self._set_status("Vui lòng chọn profile trước!", "warning")
            return

        if self._is_scanning:
            return

        self._is_scanning = True
        self.scan_progress.set(0)
        self._scan_completed_count = 0
        self._scan_total_count = len(profiles_to_scan)

        if len(profiles_to_scan) > 1:
            self._set_status(f"Đang mở {len(profiles_to_scan)} profiles song song...", "info")
        else:
            self._set_status("Đang quét nhóm...", "info")

        def do_parallel_scan():
            """Quét song song nhiều profiles"""
            from concurrent.futures import ThreadPoolExecutor, as_completed

            all_groups = []
            total = len(profiles_to_scan)

            def scan_single_profile(profile_uuid: str) -> List[Dict]:
                """Quét 1 profile"""
                try:
                    return self._execute_group_scan_for_profile(profile_uuid)
                except Exception as e:
                    print(f"[ERROR] Scan profile {profile_uuid}: {e}")
                    return []

            # Chạy song song tất cả profiles
            with ThreadPoolExecutor(max_workers=min(total, 10)) as executor:
                # Submit tất cả tasks
                future_to_uuid = {
                    executor.submit(scan_single_profile, uuid): uuid
                    for uuid in profiles_to_scan
                }

                # Thu thập kết quả khi hoàn thành
                for future in as_completed(future_to_uuid):
                    if not self._is_scanning:
                        break

                    uuid = future_to_uuid[future]
                    try:
                        result = future.result()
                        all_groups.extend(result)

                        # Update progress
                        self._scan_completed_count += 1
                        progress = self._scan_completed_count / total
                        self.after(0, lambda p=progress, c=self._scan_completed_count, t=total:
                                   self._update_scan_progress(p, c, t))
                    except Exception as e:
                        print(f"[ERROR] Future {uuid}: {e}")

            self.after(0, lambda: self._on_scan_complete(all_groups))

        threading.Thread(target=do_parallel_scan, daemon=True).start()

    def _update_scan_progress(self, progress: float, completed: int, total: int):
        """Cập nhật progress khi quét song song"""
        self.scan_progress.set(progress)
        self._set_status(f"Hoàn thành {completed}/{total} profiles...", "info")

    def _execute_group_scan_for_profile(self, profile_uuid: str) -> List[Dict]:
        """Quét nhóm cho 1 profile cụ thể (thread-safe)"""
        if not BS4_AVAILABLE:
            return []

        groups_found = []

        try:
            # Bước 1: Mở browser qua Hidemium API
            result = api.open_browser(profile_uuid)
            print(f"[DEBUG] open_browser {profile_uuid[:8]}: {result.get('status', result.get('type', 'unknown'))}")

            # Kiểm tra response
            status = result.get('status') or result.get('type')
            if status not in ['successfully', 'success', True]:
                if 'already' not in str(result).lower() and 'running' not in str(result).lower():
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
                return []

            cdp_base = f"http://127.0.0.1:{remote_port}"

            # Đợi browser khởi động
            time.sleep(3)

            # Bước 2: Lấy danh sách tabs qua CDP
            try:
                resp = requests.get(f"{cdp_base}/json", timeout=10)
                tabs = resp.json()
            except Exception as e:
                print(f"[DEBUG] CDP error for {profile_uuid[:8]}: {e}")
                return []

            # Tìm tab page
            page_ws = None
            for tab in tabs:
                if tab.get('type') == 'page':
                    page_ws = tab.get('webSocketDebuggerUrl')
                    break

            if not page_ws:
                return []

            # Bước 3: Kết nối WebSocket
            import websocket
            import json as json_module

            ws = None
            try:
                ws = websocket.create_connection(page_ws, timeout=30, suppress_origin=True)
            except:
                try:
                    ws = websocket.create_connection(page_ws, timeout=30, origin=f"http://127.0.0.1:{remote_port}")
                except:
                    try:
                        ws = websocket.create_connection(page_ws, timeout=30)
                    except:
                        return []

            if not ws:
                return []

            # Navigate đến trang nhóm
            groups_url = "https://www.facebook.com/groups/joins/?nav_source=tab&ordering=viewer_added"
            ws.send(json_module.dumps({
                "id": 1,
                "method": "Page.navigate",
                "params": {"url": groups_url}
            }))
            ws.recv()

            # Đợi trang load
            time.sleep(8)

            # Scroll để load nhóm
            for i in range(10):
                ws.send(json_module.dumps({
                    "id": 100 + i,
                    "method": "Runtime.evaluate",
                    "params": {"expression": "window.scrollTo(0, document.body.scrollHeight);"}
                }))
                ws.recv()
                time.sleep(2)

            # Lấy HTML content
            ws.send(json_module.dumps({
                "id": 200,
                "method": "Runtime.evaluate",
                "params": {"expression": "document.documentElement.outerHTML"}
            }))
            result = json_module.loads(ws.recv())
            html_content = result.get('result', {}).get('result', {}).get('value', '')

            ws.close()

            if not html_content:
                return []

            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            links = soup.find_all('a', {'aria-label': 'Xem nhóm'})

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
                                'member_count': 0,
                                'profile_uuid': profile_uuid  # Lưu profile nào quét được
                            })

            # Lưu vào database cho profile này
            if groups_found:
                sync_groups(profile_uuid, groups_found)

        except Exception as e:
            import traceback
            print(f"[ERROR] Scan {profile_uuid[:8]}: {traceback.format_exc()}")

        return groups_found

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
            # Groups đã được lưu trong _execute_group_scan_for_profile cho từng profile
            # Reload groups cho profile hiện tại hoặc profile đầu tiên
            if self.multi_profile_var.get() and self.selected_profile_uuids:
                # Multi-mode: set first profile as current và load groups
                self.current_profile_uuid = self.selected_profile_uuids[0]

            self._load_groups_for_profile()

            # Đếm số nhóm unique và số profiles
            profile_uuids = set(g.get('profile_uuid', '') for g in groups if g.get('profile_uuid'))
            self._set_status(f"Đã quét {len(groups)} nhóm từ {len(profile_uuids)} profiles!", "success")
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
        """Load nhóm của profile - hỗ trợ multi-profile mode"""
        if self.multi_profile_var.get() and self.selected_profile_uuids:
            # Multi-profile mode: load groups từ tất cả profiles đã chọn
            self.groups = get_groups_for_profiles(self.selected_profile_uuids)
        elif self.current_profile_uuid:
            # Single-profile mode
            self.groups = get_groups(self.current_profile_uuid)
        else:
            self.groups = []

        self.selected_group_ids = [g['id'] for g in self.groups if g.get('is_selected')]
        self._render_scan_list()
        self._render_post_groups_list(force_rebuild=True)  # Rebuild khi load profile mới
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

        # Sync với checkbox trong post tab (không render lại)
        if group_id in self.group_checkbox_vars:
            self.group_checkbox_vars[group_id].set(is_selected)

        self._update_stats()

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

    def _on_group_filter_change(self, *args):
        """Khi filter thay đổi"""
        self._apply_group_filter()

    def _normalize_vietnamese(self, text: str) -> str:
        """Chuẩn hóa text tiếng Việt để tìm kiếm - bỏ dấu, lowercase"""
        if not text:
            return ""
        # Lowercase
        text = text.lower()
        # Normalize unicode
        text = unicodedata.normalize('NFD', text)
        # Remove diacritics (combining characters)
        text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
        # Normalize back
        text = unicodedata.normalize('NFC', text)
        # Thay thế đ -> d
        text = text.replace('đ', 'd').replace('Đ', 'd')
        return text

    def _apply_group_filter(self):
        """Áp dụng filter cho danh sách nhóm - hỗ trợ tiếng Việt"""
        filter_text = self.group_filter_var.get().strip()

        if not filter_text:
            # Hiển thị tất cả nếu không có filter
            for widget in self.group_checkbox_widgets.values():
                widget.pack(fill="x", pady=1)
            return

        # Chuẩn hóa filter text
        filter_normalized = self._normalize_vietnamese(filter_text)
        filter_lower = filter_text.lower()

        for group_id, widget in self.group_checkbox_widgets.items():
            group = next((g for g in self.groups if g['id'] == group_id), None)
            if group:
                group_name = group.get('group_name', '')
                # Kiểm tra cả 2 cách: có dấu và không dấu
                name_lower = group_name.lower()
                name_normalized = self._normalize_vietnamese(group_name)

                # Match nếu tìm thấy trong bản gốc hoặc bản không dấu
                if filter_lower in name_lower or filter_normalized in name_normalized:
                    widget.pack(fill="x", pady=1)
                else:
                    widget.pack_forget()

    def _render_post_groups_list(self, force_rebuild=False):
        """Render danh sách nhóm với checkbox - tối ưu"""
        # Chỉ rebuild khi cần thiết
        if force_rebuild or not self.group_checkbox_widgets:
            for widget in self.post_groups_list.winfo_children():
                widget.destroy()
            self.group_checkbox_widgets = {}
            self.group_checkbox_vars = {}

        if not self.groups:
            self.post_empty_label = ctk.CTkLabel(
                self.post_groups_list,
                text="Chưa có nhóm\nQuét nhóm trước",
                font=ctk.CTkFont(size=12),
                text_color=COLORS["text_secondary"]
            )
            self.post_empty_label.pack(pady=30)
            return

        # Tạo hoặc cập nhật widgets
        for group in self.groups:
            group_id = group['id']

            if group_id in self.group_checkbox_widgets:
                # Cập nhật giá trị checkbox
                self.group_checkbox_vars[group_id].set(group_id in self.selected_group_ids)
            else:
                # Tạo mới
                row = ctk.CTkFrame(self.post_groups_list, fg_color="transparent", height=28)
                row.pack(fill="x", pady=1)
                row.pack_propagate(False)

                var = ctk.BooleanVar(value=group_id in self.selected_group_ids)
                self.group_checkbox_vars[group_id] = var

                cb = ctk.CTkCheckBox(
                    row,
                    text=group.get('group_name', 'Unknown')[:35],
                    variable=var, width=300,
                    checkbox_width=16, checkbox_height=16,
                    fg_color=COLORS["accent"],
                    font=ctk.CTkFont(size=10),
                    command=lambda gid=group_id, v=var: self._toggle_group_selection_post(gid, v)
                )
                cb.pack(side="left", padx=3)

                self.group_checkbox_widgets[group_id] = row

        # Áp dụng filter
        self._apply_group_filter()

    def _toggle_group_selection_post(self, group_id: int, var: ctk.BooleanVar):
        """Toggle group từ tab Đăng - không render lại"""
        is_selected = var.get()
        update_group_selection(group_id, 1 if is_selected else 0)

        if is_selected and group_id not in self.selected_group_ids:
            self.selected_group_ids.append(group_id)
        elif not is_selected and group_id in self.selected_group_ids:
            self.selected_group_ids.remove(group_id)

        self._update_stats()
        self._render_scan_list()

    def _get_visible_group_ids(self) -> List[int]:
        """Lấy danh sách group IDs đang hiển thị (sau khi lọc)"""
        visible_ids = []
        for group_id, widget in self.group_checkbox_widgets.items():
            # Check if widget is currently visible (packed)
            try:
                if widget.winfo_ismapped():
                    visible_ids.append(group_id)
            except:
                pass
        return visible_ids

    def _toggle_select_all(self):
        """Toggle chọn tất cả - chỉ chọn các nhóm đang hiển thị"""
        select_all = self.select_all_var.get()

        # Lấy danh sách group IDs đang hiển thị (sau filter)
        visible_group_ids = self._get_visible_group_ids()

        if select_all:
            # Chỉ chọn các nhóm đang hiển thị
            for gid in visible_group_ids:
                if gid not in self.selected_group_ids:
                    self.selected_group_ids.append(gid)
                update_group_selection(gid, 1)
                # Sync checkbox
                if gid in self.group_checkbox_vars:
                    self.group_checkbox_vars[gid].set(True)
        else:
            # Bỏ chọn các nhóm đang hiển thị
            for gid in visible_group_ids:
                if gid in self.selected_group_ids:
                    self.selected_group_ids.remove(gid)
                update_group_selection(gid, 0)
                # Sync checkbox
                if gid in self.group_checkbox_vars:
                    self.group_checkbox_vars[gid].set(False)

        self._render_scan_list()
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
