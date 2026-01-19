"""
Groups Tab - Modern Group Posting Interface
Premium design for group management and auto-posting
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
from config import COLORS, FONTS, SPACING, RADIUS
from widgets import ModernButton, ModernEntry, ModernTextbox, SearchBar, Badge, EmptyState
from db import (
    get_profiles, get_groups, save_group, delete_group,
    update_group_selection, get_selected_groups, sync_groups, clear_groups,
    get_contents, get_categories, save_post_history, get_post_history
)
from api_service import api

# Import for web scraping
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from bs4 import BeautifulSoup
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


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
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=RADIUS["lg"])
        header.pack(fill="x", padx=SPACING["lg"], pady=(SPACING["lg"], SPACING["md"]))

        header_inner = ctk.CTkFrame(header, fg_color="transparent")
        header_inner.pack(fill="x", padx=SPACING["lg"], pady=SPACING["md"])

        ctk.CTkLabel(
            header_inner,
            text="Chon Profile:",
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_md"], weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left")

        self.profile_var = ctk.StringVar(value="-- Chọn profile --")
        self.profile_menu = ctk.CTkOptionMenu(
            header_inner,
            variable=self.profile_var,
            values=["-- Chọn profile --"],
            fg_color=COLORS["bg_card"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            dropdown_fg_color=COLORS["bg_card"],
            dropdown_hover_color=COLORS["bg_hover"],
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_sm"]),
            width=300,
            corner_radius=RADIUS["md"],
            command=self._on_profile_change
        )
        self.profile_menu.pack(side="left", padx=SPACING["lg"])

        ModernButton(
            header_inner,
            text="Lam moi",
            variant="secondary",
            command=self._load_profiles,
            width=100
        ).pack(side="left")

        self.profile_status = ctk.CTkLabel(
            header_inner,
            text="",
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_sm"]),
            text_color=COLORS["text_secondary"]
        )
        self.profile_status.pack(side="right")

        # ========== TABVIEW - 3 Sub-tabs ==========
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=COLORS["bg_secondary"],
            segmented_button_fg_color=COLORS["bg_card"],
            segmented_button_selected_color=COLORS["accent"],
            segmented_button_selected_hover_color=COLORS["accent_hover"],
            segmented_button_unselected_color=COLORS["bg_card"],
            segmented_button_unselected_hover_color=COLORS["bg_hover"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=COLORS["border"]
        )
        self.tabview.pack(fill="both", expand=True, padx=SPACING["lg"], pady=(0, SPACING["lg"]))

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
        action_bar.pack(fill="x", padx=SPACING["md"], pady=SPACING["md"])

        ModernButton(
            action_bar,
            text="Quet nhom",
            variant="primary",
            command=self._scan_groups,
            width=130
        ).pack(side="left", padx=SPACING["xs"])

        ModernButton(
            action_bar,
            text="Xoa tat ca",
            variant="danger",
            command=self._clear_all_groups,
            width=110
        ).pack(side="left", padx=SPACING["xs"])

        self.scan_stats = ctk.CTkLabel(
            action_bar,
            text="Tổng: 0 nhóm",
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_sm"]),
            text_color=COLORS["text_secondary"]
        )
        self.scan_stats.pack(side="right", padx=SPACING["md"])

        # Progress bar
        self.scan_progress = ctk.CTkProgressBar(
            self.tab_scan,
            fg_color=COLORS["bg_card"],
            progress_color=COLORS["accent"],
            height=6,
            corner_radius=RADIUS["sm"]
        )
        self.scan_progress.pack(fill="x", padx=SPACING["md"], pady=(0, SPACING["md"]))
        self.scan_progress.set(0)

        # Groups table header
        table_header = ctk.CTkFrame(self.tab_scan, fg_color=COLORS["bg_card"], corner_radius=RADIUS["sm"], height=38)
        table_header.pack(fill="x", padx=SPACING["md"], pady=(0, SPACING["xs"]))
        table_header.pack_propagate(False)

        headers = [("", 30), ("ID", 50), ("Tên nhóm", 220), ("Group ID", 150), ("Thành viên", 90), ("Ngày quét", 100)]
        for text, width in headers:
            ctk.CTkLabel(
                table_header,
                text=text,
                width=width,
                font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_xs"], weight="bold"),
                text_color=COLORS["text_primary"]
            ).pack(side="left", padx=SPACING["xs"])

        # Groups list
        self.scan_list = ctk.CTkScrollableFrame(
            self.tab_scan,
            fg_color="transparent",
            scrollbar_button_color=COLORS["bg_hover"],
            scrollbar_button_hover_color=COLORS["accent"]
        )
        self.scan_list.pack(fill="both", expand=True, padx=SPACING["md"], pady=(0, SPACING["md"]))

        self.scan_empty_label = ctk.CTkLabel(
            self.scan_list,
            text="Chưa có nhóm nào\nChọn profile và bấm 'Quét nhóm' để bắt đầu",
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_base"]),
            text_color=COLORS["text_secondary"]
        )
        self.scan_empty_label.pack(pady=SPACING["4xl"])

    def _create_post_tab(self):
        """Tạo tab Đăng nhóm"""
        # Main container - 2 columns
        main_container = ctk.CTkFrame(self.tab_post, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=SPACING["xs"], pady=SPACING["xs"])

        # ========== LEFT PANEL - Groups List ==========
        left_panel = ctk.CTkFrame(
            main_container,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=COLORS["border"],
            width=350
        )
        left_panel.pack(side="left", fill="y", padx=(0, SPACING["md"]))
        left_panel.pack_propagate(False)

        # Left header
        left_header = ctk.CTkFrame(left_panel, fg_color="transparent")
        left_header.pack(fill="x", padx=SPACING["md"], pady=SPACING["md"])

        ctk.CTkLabel(
            left_header,
            text="Danh sách nhóm",
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_md"], weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left")

        self.select_all_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            left_header,
            text="Tất cả",
            variable=self.select_all_var,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_sm"]),
            width=60,
            corner_radius=RADIUS["sm"],
            command=self._toggle_select_all
        ).pack(side="right")

        self.post_stats = ctk.CTkLabel(
            left_panel,
            text="Đã chọn: 0 / 0",
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_xs"]),
            text_color=COLORS["accent"]
        )
        self.post_stats.pack(anchor="w", padx=SPACING["md"], pady=(0, SPACING["xs"]))

        # Groups checkboxes list
        self.post_groups_list = ctk.CTkScrollableFrame(
            left_panel,
            fg_color="transparent",
            scrollbar_button_color=COLORS["bg_hover"],
            scrollbar_button_hover_color=COLORS["accent"]
        )
        self.post_groups_list.pack(fill="both", expand=True, padx=SPACING["xs"], pady=(0, SPACING["md"]))

        self.post_empty_label = ctk.CTkLabel(
            self.post_groups_list,
            text="Chưa có nhóm\nQuét nhóm trước",
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_sm"]),
            text_color=COLORS["text_secondary"]
        )
        self.post_empty_label.pack(pady=SPACING["2xl"])

        # ========== RIGHT PANEL - Post Content ==========
        right_panel = ctk.CTkFrame(
            main_container,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=COLORS["border"]
        )
        right_panel.pack(side="right", fill="both", expand=True)

        # Scrollable right panel
        right_scroll = ctk.CTkScrollableFrame(
            right_panel,
            fg_color="transparent",
            scrollbar_button_color=COLORS["bg_hover"],
            scrollbar_button_hover_color=COLORS["accent"]
        )
        right_scroll.pack(fill="both", expand=True, padx=SPACING["xs"], pady=SPACING["xs"])

        # Right header
        ctk.CTkLabel(
            right_scroll,
            text="Nội dung đăng",
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_md"], weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=SPACING["md"], pady=(SPACING["md"], SPACING["xs"]))

        # Category selector
        cat_row = ctk.CTkFrame(right_scroll, fg_color="transparent")
        cat_row.pack(fill="x", padx=SPACING["md"], pady=SPACING["xs"])

        ctk.CTkLabel(
            cat_row,
            text="Mục:",
            width=80,
            anchor="w",
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_sm"]),
            text_color=COLORS["text_secondary"]
        ).pack(side="left")
        self.category_var = ctk.StringVar(value="Mặc định")
        self.category_menu = ctk.CTkOptionMenu(
            cat_row,
            variable=self.category_var,
            values=["Mặc định"],
            fg_color=COLORS["bg_secondary"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            dropdown_fg_color=COLORS["bg_card"],
            dropdown_hover_color=COLORS["bg_hover"],
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_sm"]),
            corner_radius=RADIUS["md"],
            width=180,
            command=self._on_category_change
        )
        self.category_menu.pack(side="left", padx=SPACING["xs"])

        # Random content checkbox
        self.random_content_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            cat_row,
            text="Random nội dung",
            variable=self.random_content_var,
            fg_color=COLORS["success"],
            hover_color="#059669",
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_sm"]),
            corner_radius=RADIUS["sm"],
            command=self._toggle_random_content
        ).pack(side="left", padx=SPACING["md"])

        # Content selector (disabled when random)
        content_row = ctk.CTkFrame(right_scroll, fg_color="transparent")
        content_row.pack(fill="x", padx=SPACING["md"], pady=SPACING["xs"])

        ctk.CTkLabel(
            content_row,
            text="Tin đăng:",
            width=80,
            anchor="w",
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_sm"]),
            text_color=COLORS["text_secondary"]
        ).pack(side="left")
        self.content_var = ctk.StringVar(value="-- Random từ mục --")
        self.content_menu = ctk.CTkOptionMenu(
            content_row,
            variable=self.content_var,
            values=["-- Random từ mục --"],
            fg_color=COLORS["bg_secondary"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            dropdown_fg_color=COLORS["bg_card"],
            dropdown_hover_color=COLORS["bg_hover"],
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_sm"]),
            corner_radius=RADIUS["md"],
            width=250,
            command=self._on_content_change
        )
        self.content_menu.pack(side="left", padx=SPACING["xs"])

        # Content preview
        ctk.CTkLabel(
            right_scroll,
            text="Nội dung / Mô tả:",
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_sm"]),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=SPACING["md"], pady=(SPACING["md"], SPACING["xs"]))

        self.content_preview = ctk.CTkTextbox(
            right_scroll,
            fg_color=COLORS["bg_secondary"],
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_sm"]),
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=RADIUS["md"],
            height=100
        )
        self.content_preview.pack(fill="x", padx=SPACING["md"], pady=(0, SPACING["xs"]))
        self.content_preview.configure(state="disabled")

        # ===== IMAGE SECTION =====
        img_section = ctk.CTkFrame(
            right_scroll,
            fg_color=COLORS["bg_secondary"],
            corner_radius=RADIUS["md"],
            border_width=1,
            border_color=COLORS["border"]
        )
        img_section.pack(fill="x", padx=SPACING["md"], pady=SPACING["xs"])

        img_header = ctk.CTkFrame(img_section, fg_color="transparent")
        img_header.pack(fill="x", padx=SPACING["md"], pady=(SPACING["sm"], SPACING["xs"]))

        self.attach_img_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            img_header,
            text="Kèm hình ảnh",
            variable=self.attach_img_var,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_sm"]),
            corner_radius=RADIUS["sm"],
            command=self._toggle_attach_image
        ).pack(side="left")

        # Image folder path
        img_path_row = ctk.CTkFrame(img_section, fg_color="transparent")
        img_path_row.pack(fill="x", padx=SPACING["md"], pady=SPACING["xs"])

        ctk.CTkLabel(
            img_path_row,
            text="Thư mục ảnh:",
            width=90,
            anchor="w",
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_xs"]),
            text_color=COLORS["text_secondary"]
        ).pack(side="left")
        self.img_folder_entry = ModernEntry(img_path_row, placeholder="Đường dẫn thư mục...", width=200)
        self.img_folder_entry.pack(side="left", padx=SPACING["xs"])
        self.img_folder_entry.configure(state="disabled")

        ModernButton(
            img_path_row,
            text="Chọn",
            variant="secondary",
            width=60,
            command=self._select_image_folder
        ).pack(side="left", padx=SPACING["xs"])

        # Image count
        img_count_row = ctk.CTkFrame(img_section, fg_color="transparent")
        img_count_row.pack(fill="x", padx=SPACING["md"], pady=(SPACING["xs"], SPACING["sm"]))

        ctk.CTkLabel(
            img_count_row,
            text="Số ảnh random:",
            width=90,
            anchor="w",
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_xs"]),
            text_color=COLORS["text_secondary"]
        ).pack(side="left")
        self.img_count_entry = ModernEntry(img_count_row, placeholder="5", width=60)
        self.img_count_entry.pack(side="left", padx=SPACING["xs"])
        self.img_count_entry.insert(0, "5")
        self.img_count_entry.configure(state="disabled")

        self.img_count_label = ctk.CTkLabel(
            img_count_row,
            text="(Tổng: 0 ảnh)",
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_xs"]),
            text_color=COLORS["text_secondary"]
        )
        self.img_count_label.pack(side="left", padx=SPACING["xs"])

        # ===== POSTING OPTIONS =====
        options_frame = ctk.CTkFrame(
            right_scroll,
            fg_color=COLORS["bg_secondary"],
            corner_radius=RADIUS["md"],
            border_width=1,
            border_color=COLORS["border"]
        )
        options_frame.pack(fill="x", padx=SPACING["md"], pady=SPACING["xs"])

        ctk.CTkLabel(
            options_frame,
            text="Tùy chọn đăng:",
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_sm"], weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=SPACING["md"], pady=(SPACING["sm"], SPACING["xs"]))

        options_inner = ctk.CTkFrame(options_frame, fg_color="transparent")
        options_inner.pack(fill="x", padx=SPACING["md"], pady=(0, SPACING["sm"]))

        ctk.CTkLabel(
            options_inner,
            text="Delay (giây):",
            width=80,
            anchor="w",
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_xs"]),
            text_color=COLORS["text_secondary"]
        ).pack(side="left")
        self.delay_entry = ModernEntry(options_inner, placeholder="5", width=60)
        self.delay_entry.pack(side="left", padx=SPACING["xs"])
        self.delay_entry.insert(0, "5")

        self.random_delay_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            options_inner,
            text="Random (1-10s)",
            variable=self.random_delay_var,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_xs"]),
            corner_radius=RADIUS["sm"]
        ).pack(side="left", padx=SPACING["md"])

        # Post buttons
        post_btn_frame = ctk.CTkFrame(right_scroll, fg_color="transparent")
        post_btn_frame.pack(fill="x", padx=SPACING["md"], pady=SPACING["md"])

        ModernButton(
            post_btn_frame,
            text="Dang tuong",
            variant="success",
            command=self._start_posting,
            width=120
        ).pack(side="left", padx=SPACING["xs"])

        ModernButton(
            post_btn_frame,
            text="Dung",
            variant="danger",
            command=self._stop_posting,
            width=80
        ).pack(side="left", padx=SPACING["xs"])

        # Progress
        self.post_progress = ctk.CTkProgressBar(
            right_scroll,
            fg_color=COLORS["bg_secondary"],
            progress_color=COLORS["success"],
            height=6,
            corner_radius=RADIUS["sm"]
        )
        self.post_progress.pack(fill="x", padx=SPACING["md"], pady=(0, SPACING["xs"]))
        self.post_progress.set(0)

        self.post_status_label = ctk.CTkLabel(
            right_scroll,
            text="Tiến trình: 0 / 0",
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_xs"]),
            text_color=COLORS["text_secondary"]
        )
        self.post_status_label.pack(anchor="w", padx=SPACING["md"], pady=(0, SPACING["xs"]))

        # ===== POSTED URLS LOG =====
        ctk.CTkLabel(
            right_scroll,
            text="Nhật ký đăng tường:",
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_sm"], weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=SPACING["md"], pady=(SPACING["md"], SPACING["xs"]))

        # Posted URLs table header
        url_header = ctk.CTkFrame(
            right_scroll,
            fg_color=COLORS["bg_secondary"],
            corner_radius=RADIUS["sm"],
            height=30
        )
        url_header.pack(fill="x", padx=SPACING["md"], pady=(0, SPACING["xs"]))
        url_header.pack_propagate(False)

        headers = [("Nhóm", 150), ("Link bài đăng", 250), ("Thời gian", 80)]
        for text, width in headers:
            ctk.CTkLabel(
                url_header,
                text=text,
                width=width,
                font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_xs"], weight="bold"),
                text_color=COLORS["text_primary"]
            ).pack(side="left", padx=SPACING["xs"])

        # Posted URLs list
        self.posted_urls_list = ctk.CTkScrollableFrame(
            right_scroll,
            fg_color="transparent",
            scrollbar_button_color=COLORS["bg_hover"],
            scrollbar_button_hover_color=COLORS["accent"],
            height=120
        )
        self.posted_urls_list.pack(fill="x", padx=SPACING["md"], pady=(0, SPACING["md"]))

        self.posted_empty = ctk.CTkLabel(
            self.posted_urls_list,
            text="Chưa có bài đăng nào",
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_xs"]),
            text_color=COLORS["text_secondary"]
        )
        self.posted_empty.pack(pady=SPACING["xl"])

    def _create_boost_tab(self):
        """Tạo tab Đẩy tin (Bình luận)"""
        # Main container
        main_container = ctk.CTkFrame(self.tab_boost, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=SPACING["xs"], pady=SPACING["xs"])

        # ========== LEFT PANEL - Posted URLs List ==========
        left_panel = ctk.CTkFrame(
            main_container,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=COLORS["border"],
            width=400
        )
        left_panel.pack(side="left", fill="y", padx=(0, SPACING["md"]))
        left_panel.pack_propagate(False)

        # Header
        left_header = ctk.CTkFrame(left_panel, fg_color="transparent")
        left_header.pack(fill="x", padx=SPACING["md"], pady=SPACING["md"])

        ctk.CTkLabel(
            left_header,
            text="Danh sách bài đã đăng",
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_md"], weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left")

        ModernButton(
            left_header,
            text="Lam moi",
            variant="secondary",
            command=self._load_today_posts,
            width=90
        ).pack(side="right")

        # Filter by date
        date_row = ctk.CTkFrame(left_panel, fg_color="transparent")
        date_row.pack(fill="x", padx=SPACING["md"], pady=(0, SPACING["xs"]))

        ctk.CTkLabel(
            date_row,
            text="Lọc:",
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_xs"]),
            text_color=COLORS["text_secondary"]
        ).pack(side="left")

        self.date_filter_var = ctk.StringVar(value="Hôm nay")
        self.date_filter_menu = ctk.CTkOptionMenu(
            date_row,
            variable=self.date_filter_var,
            values=["Hôm nay", "7 ngày", "30 ngày", "Tất cả"],
            fg_color=COLORS["bg_secondary"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            dropdown_fg_color=COLORS["bg_card"],
            dropdown_hover_color=COLORS["bg_hover"],
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_xs"]),
            corner_radius=RADIUS["md"],
            width=100,
            command=self._on_date_filter_change
        )
        self.date_filter_menu.pack(side="left", padx=SPACING["xs"])

        self.boost_stats = ctk.CTkLabel(
            date_row,
            text="0 bài",
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_xs"]),
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
            hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_sm"]),
            corner_radius=RADIUS["sm"],
            command=self._toggle_select_all_boost
        ).pack(anchor="w", padx=SPACING["md"], pady=(0, SPACING["xs"]))

        # Posted URLs list for boost
        self.boost_urls_list = ctk.CTkScrollableFrame(
            left_panel,
            fg_color="transparent",
            scrollbar_button_color=COLORS["bg_hover"],
            scrollbar_button_hover_color=COLORS["accent"]
        )
        self.boost_urls_list.pack(fill="both", expand=True, padx=SPACING["xs"], pady=(0, SPACING["md"]))

        self.boost_empty_label = ctk.CTkLabel(
            self.boost_urls_list,
            text="Chưa có bài đăng nào\nĐăng bài ở tab trước",
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_sm"]),
            text_color=COLORS["text_secondary"]
        )
        self.boost_empty_label.pack(pady=SPACING["3xl"])

        # ========== RIGHT PANEL - Comment Content ==========
        right_panel = ctk.CTkFrame(
            main_container,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=COLORS["border"]
        )
        right_panel.pack(side="right", fill="both", expand=True)

        # Header
        ctk.CTkLabel(
            right_panel,
            text="Nội dung bình luận",
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_md"], weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=SPACING["lg"], pady=(SPACING["lg"], SPACING["md"]))

        # Comment content
        ctk.CTkLabel(
            right_panel,
            text="Nội dung comment (mỗi dòng 1 comment, sẽ random):",
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_xs"]),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=SPACING["lg"], pady=(0, SPACING["xs"]))

        self.comment_textbox = ctk.CTkTextbox(
            right_panel,
            fg_color=COLORS["bg_secondary"],
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_sm"]),
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=RADIUS["md"],
            height=150
        )
        self.comment_textbox.pack(fill="x", padx=SPACING["lg"], pady=(0, SPACING["md"]))
        self.comment_textbox.insert("1.0", "Hay quá!\nCảm ơn bạn!\nThông tin hữu ích!\nĐã lưu lại!")

        # Comment options
        options_row = ctk.CTkFrame(right_panel, fg_color="transparent")
        options_row.pack(fill="x", padx=SPACING["lg"], pady=SPACING["xs"])

        ctk.CTkLabel(
            options_row,
            text="Delay (giây):",
            width=80,
            anchor="w",
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_xs"]),
            text_color=COLORS["text_secondary"]
        ).pack(side="left")
        self.comment_delay_entry = ModernEntry(options_row, placeholder="3", width=60)
        self.comment_delay_entry.pack(side="left", padx=SPACING["xs"])
        self.comment_delay_entry.insert(0, "3")

        self.random_comment_delay_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            options_row,
            text="Random delay (1-5s)",
            variable=self.random_comment_delay_var,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_xs"]),
            corner_radius=RADIUS["sm"]
        ).pack(side="left", padx=SPACING["md"])

        # Comment buttons
        btn_row = ctk.CTkFrame(right_panel, fg_color="transparent")
        btn_row.pack(fill="x", padx=SPACING["lg"], pady=SPACING["md"])

        ModernButton(
            btn_row,
            text="Binh luan",
            variant="success",
            command=self._start_commenting,
            width=120
        ).pack(side="left", padx=SPACING["xs"])

        ModernButton(
            btn_row,
            text="Dung",
            variant="danger",
            command=self._stop_commenting,
            width=80
        ).pack(side="left", padx=SPACING["xs"])

        # Progress
        self.comment_progress = ctk.CTkProgressBar(
            right_panel,
            fg_color=COLORS["bg_secondary"],
            progress_color=COLORS["success"],
            height=6,
            corner_radius=RADIUS["sm"]
        )
        self.comment_progress.pack(fill="x", padx=SPACING["lg"], pady=(0, SPACING["xs"]))
        self.comment_progress.set(0)

        self.comment_status_label = ctk.CTkLabel(
            right_panel,
            text="Tiến trình: 0 / 0",
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_xs"]),
            text_color=COLORS["text_secondary"]
        )
        self.comment_status_label.pack(anchor="w", padx=SPACING["lg"], pady=(0, SPACING["md"]))

        # ===== COMMENT LOG =====
        ctk.CTkLabel(
            right_panel,
            text="Nhật ký bình luận:",
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_sm"], weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=SPACING["lg"], pady=(SPACING["md"], SPACING["xs"]))

        self.comment_log = ctk.CTkTextbox(
            right_panel,
            fg_color=COLORS["bg_secondary"],
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_xs"]),
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=RADIUS["md"],
            height=150
        )
        self.comment_log.pack(fill="both", expand=True, padx=SPACING["lg"], pady=(0, SPACING["lg"]))
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
        """Thực hiện quét nhóm từ Facebook"""
        if not SELENIUM_AVAILABLE:
            self.after(0, lambda: self._set_status("Cần cài selenium: pip install selenium beautifulsoup4", "error"))
            return []

        groups_found = []
        driver = None

        try:
            # Bước 1: Mở browser qua Hidemium API
            self.after(0, lambda: self._set_status("Đang mở browser...", "info"))
            self.after(0, lambda: self.scan_progress.set(0.05))

            result = api.open_browser(self.current_profile_uuid)

            if result.get('status') != 'successfully':
                error = result.get('message', 'Không thể mở browser')
                self.after(0, lambda e=error: self._set_status(f"Lỗi: {e}", "error"))
                return []

            # Lấy debugger address để kết nối Selenium
            debugger_address = result.get('data', {}).get('debugger_address') or result.get('debugger_address')

            if not debugger_address:
                browser_data = result.get('data', {})
                if isinstance(browser_data, dict):
                    debugger_address = browser_data.get('debugger_address')

            if not debugger_address:
                self.after(0, lambda: self._set_status("Không lấy được debugger address", "error"))
                return []

            # ĐỢI BROWSER MỞ HOÀN TOÀN
            self.after(0, lambda: self._set_status("Đợi browser khởi động...", "info"))
            self.after(0, lambda: self.scan_progress.set(0.1))
            time.sleep(5)  # Đợi 5 giây để browser mở hoàn toàn

            # Bước 2: Kết nối Selenium đến browser đang chạy
            self.after(0, lambda: self._set_status("Đang kết nối Selenium...", "info"))
            self.after(0, lambda: self.scan_progress.set(0.15))

            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", debugger_address)

            driver = webdriver.Chrome(options=chrome_options)

            # Đợi kết nối ổn định
            time.sleep(2)

            # Bước 3: Mở trang danh sách nhóm đã tham gia
            self.after(0, lambda: self._set_status("Đang mở trang nhóm...", "info"))
            self.after(0, lambda: self.scan_progress.set(0.2))

            groups_url = "https://www.facebook.com/groups/joins/?nav_source=tab&ordering=viewer_added"
            driver.get(groups_url)

            # ĐỢI TRANG LOAD - quan trọng!
            self.after(0, lambda: self._set_status("Đợi trang load...", "info"))
            self.after(0, lambda: self.scan_progress.set(0.25))
            time.sleep(5)  # Đợi trang load

            # Đợi thêm cho JavaScript render
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except:
                pass

            time.sleep(3)  # Đợi thêm cho Facebook load AJAX

            # Bước 4: Scroll để load thêm nhóm
            self.after(0, lambda: self._set_status("Đang scroll load nhóm...", "info"))
            self.after(0, lambda: self.scan_progress.set(0.3))

            last_height = driver.execute_script("return document.body.scrollHeight")
            scroll_attempts = 0
            max_scrolls = 15  # Tăng số lần scroll

            while scroll_attempts < max_scrolls:
                # Scroll xuống cuối trang
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)  # Đợi lâu hơn để load

                # Kiểm tra có scroll thêm được không
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    # Thử scroll thêm 1 lần nữa
                    time.sleep(2)
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break

                last_height = new_height
                scroll_attempts += 1

                progress = 0.3 + (scroll_attempts / max_scrolls) * 0.4
                self.after(0, lambda p=progress, s=scroll_attempts: self._set_status(f"Scroll lần {s}...", "info"))
                self.after(0, lambda p=progress: self.scan_progress.set(p))

            # Bước 5: Parse HTML để lấy danh sách nhóm
            self.after(0, lambda: self._set_status("Đang phân tích danh sách nhóm...", "info"))
            self.after(0, lambda: self.scan_progress.set(0.75))

            html_content = driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')

            # Tìm các link nhóm với aria-label "Xem nhóm"
            links = soup.find_all('a', {'aria-label': 'Xem nhóm'})

            self.after(0, lambda n=len(links): self._set_status(f"Tìm thấy {n} link nhóm...", "info"))

            for link in links:
                href = link.get('href', '')
                if '/groups/' in href:
                    # Extract group ID từ URL
                    match = re.search(r'/groups/([^/?]+)', href)
                    if match:
                        group_id = match.group(1)

                        # Bỏ qua nếu là "joins" hoặc "feed"
                        if group_id in ['joins', 'feed', 'discover']:
                            continue

                        # Lấy tên nhóm - tìm trong các parent elements
                        group_name = group_id  # Default là group_id

                        # Tìm parent chứa tên nhóm
                        parent = link
                        for _ in range(10):  # Tìm lên 10 cấp
                            parent = parent.find_parent()
                            if parent is None:
                                break
                            # Tìm span hoặc div có text
                            spans = parent.find_all(['span', 'div'], recursive=False)
                            for span in spans:
                                text = span.get_text(strip=True)
                                if text and len(text) > 3 and text != "Xem nhóm" and not text.startswith('http'):
                                    if len(text) < 150:  # Tên nhóm hợp lệ
                                        group_name = text
                                        break
                            if group_name != group_id:
                                break

                        # Tạo full URL
                        group_url = f"https://www.facebook.com/groups/{group_id}/"

                        # Kiểm tra không trùng lặp
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

        finally:
            # Đóng kết nối Selenium nhưng KHÔNG đóng browser
            if driver:
                try:
                    driver.quit()
                except:
                    pass

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
            if not SELENIUM_AVAILABLE:
                self._set_status("Cần cài: pip install selenium beautifulsoup4 webdriver-manager", "warning")
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
                font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_base"]),
                text_color=COLORS["text_secondary"]
            )
            self.scan_empty_label.pack(pady=SPACING["4xl"])
            return

        for group in self.groups:
            self._create_scan_row(group)

    def _create_scan_row(self, group: Dict):
        """Tạo row cho group"""
        row = ctk.CTkFrame(
            self.scan_list,
            fg_color=COLORS["bg_secondary"],
            corner_radius=RADIUS["sm"],
            height=38
        )
        row.pack(fill="x", pady=2)
        row.pack_propagate(False)

        var = ctk.BooleanVar(value=group['id'] in self.selected_group_ids)
        cb = ctk.CTkCheckBox(
            row, text="", variable=var, width=25,
            checkbox_width=18, checkbox_height=18,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            corner_radius=RADIUS["xs"],
            command=lambda gid=group['id'], v=var: self._toggle_group_selection(gid, v)
        )
        cb.pack(side="left", padx=SPACING["xs"])

        ctk.CTkLabel(
            row,
            text=str(group.get('id', '')),
            width=50,
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_xs"]),
            text_color=COLORS["text_secondary"]
        ).pack(side="left")

        name = group.get('group_name', 'Unknown')[:25]
        ctk.CTkLabel(
            row,
            text=name,
            width=220,
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_xs"]),
            text_color=COLORS["text_primary"],
            anchor="w"
        ).pack(side="left", padx=SPACING["xs"])

        gid = group.get('group_id', '')[:18]
        ctk.CTkLabel(
            row,
            text=gid,
            width=150,
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_xs"]),
            text_color=COLORS["accent"],
            anchor="w"
        ).pack(side="left", padx=SPACING["xs"])

        members = group.get('member_count', 0)
        ctk.CTkLabel(
            row,
            text=f"{members:,}" if members else "-",
            width=90,
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_xs"]),
            text_color=COLORS["text_secondary"]
        ).pack(side="left")

        created = group.get('created_at', '')[:10] if group.get('created_at') else '-'
        ctk.CTkLabel(
            row,
            text=created,
            width=100,
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_xs"]),
            text_color=COLORS["text_secondary"]
        ).pack(side="left")

        ctk.CTkButton(
            row,
            text="✕",
            width=26,
            height=24,
            fg_color=COLORS["error"],
            hover_color="#dc2626",
            corner_radius=RADIUS["sm"],
            font=ctk.CTkFont(size=12),
            command=lambda gid=group['id']: self._delete_group(gid)
        ).pack(side="right", padx=SPACING["xs"])

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
                font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_sm"]),
                text_color=COLORS["text_secondary"]
            )
            self.post_empty_label.pack(pady=SPACING["2xl"])
            return

        for group in self.groups:
            row = ctk.CTkFrame(self.post_groups_list, fg_color="transparent", height=32)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)

            var = ctk.BooleanVar(value=group['id'] in self.selected_group_ids)
            cb = ctk.CTkCheckBox(
                row,
                text=group.get('group_name', 'Unknown')[:30],
                variable=var, width=280,
                checkbox_width=16, checkbox_height=16,
                fg_color=COLORS["accent"],
                hover_color=COLORS["accent_hover"],
                font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_xs"]),
                corner_radius=RADIUS["xs"],
                command=lambda gid=group['id'], v=var: self._toggle_group_selection_post(gid, v)
            )
            cb.pack(side="left", padx=SPACING["xs"])

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
                font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_xs"]),
                text_color=COLORS["text_secondary"]
            )
            self.posted_empty.pack(pady=SPACING["xl"])
            return

        for item in self.posted_urls:
            row = ctk.CTkFrame(
                self.posted_urls_list,
                fg_color=COLORS["bg_secondary"],
                corner_radius=RADIUS["sm"],
                height=28
            )
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)

            ctk.CTkLabel(
                row,
                text=item['group_name'][:18],
                width=150,
                font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_xs"]),
                text_color=COLORS["text_primary"],
                anchor="w"
            ).pack(side="left", padx=SPACING["xs"])

            url_label = ctk.CTkLabel(
                row,
                text=item['post_url'][:40],
                width=250,
                font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_xs"]),
                text_color=COLORS["accent"],
                anchor="w",
                cursor="hand2"
            )
            url_label.pack(side="left", padx=SPACING["xs"])

            ctk.CTkLabel(
                row,
                text=item['time'],
                width=80,
                font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_xs"]),
                text_color=COLORS["text_secondary"]
            ).pack(side="left")

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
                font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_sm"]),
                text_color=COLORS["text_secondary"]
            )
            self.boost_empty_label.pack(pady=SPACING["3xl"])
            return

        self.boost_post_vars = {}
        for post in posts:
            row = ctk.CTkFrame(self.boost_urls_list, fg_color="transparent", height=30)
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
                hover_color=COLORS["accent_hover"],
                font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_xs"]),
                corner_radius=RADIUS["xs"]
            )
            cb.pack(side="left", padx=SPACING["xs"])

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
