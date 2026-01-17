"""
Tab Đăng Reels Page - Lên kế hoạch và đăng Reels cho các Facebook Pages
Sử dụng CDPHelper (CDPClientMAX) cho automation
"""
import customtkinter as ctk
from typing import List, Dict, Optional, Any
import threading
import os
import re
import time
import random
import json as json_module
from datetime import datetime, timedelta
from tkinter import filedialog
from config import COLORS
from widgets import ModernButton, ModernEntry
from db import (
    get_profiles, get_pages, get_pages_for_profiles,
    save_reel_schedule, get_reel_schedules, update_reel_schedule,
    delete_reel_schedule, save_posted_reel, get_posted_reels
)
from api_service import api
from automation.window_manager import acquire_window_slot, release_window_slot, get_window_bounds
from automation.cdp_helper import CDPHelper


class ReelsPageTab(ctk.CTkFrame):
    """Tab Đăng Reels Page - Đăng và lên lịch Reels cho các Pages"""

    def __init__(self, master, status_callback=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.status_callback = status_callback
        self.profiles: List[Dict] = []
        self.pages: List[Dict] = []
        self.current_profile_uuid: Optional[str] = None
        self.selected_page_ids: List[int] = []
        self.video_path: Optional[str] = None
        self.cover_path: Optional[str] = None
        self._is_posting = False
        self._is_scheduling = False

        # Pagination state
        self._history_page = 0
        self._history_page_size = 20
        self._schedule_page = 0
        self._schedule_page_size = 20

        # Widget caches
        self._page_checkbox_vars: Dict[int, ctk.BooleanVar] = {}

        # CDP counter for unique message IDs
        self._cdp_id = 0

        self._create_ui()
        self._load_profiles()

    def _create_ui(self):
        """Tạo giao diện chính"""
        # ========== HEADER - Profile & Page Selector ==========
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=12)
        header.pack(fill="x", padx=15, pady=(15, 10))

        # Row 1: Profile selector
        header_row1 = ctk.CTkFrame(header, fg_color="transparent")
        header_row1.pack(fill="x", padx=15, pady=(12, 5))

        ctk.CTkLabel(
            header_row1,
            text="👤 Profile:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left")

        self.profile_var = ctk.StringVar(value="-- Chọn profile --")
        self.profile_menu = ctk.CTkOptionMenu(
            header_row1,
            variable=self.profile_var,
            values=["-- Chọn profile --"],
            fg_color=COLORS["bg_card"],
            button_color=COLORS["accent"],
            width=280,
            command=self._on_profile_change
        )
        self.profile_menu.pack(side="left", padx=10)

        ModernButton(
            header_row1,
            text="Làm mới",
            icon="🔄",
            variant="secondary",
            command=self._load_profiles,
            width=100
        ).pack(side="left", padx=5)

        self.status_label = ctk.CTkLabel(
            header_row1,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        )
        self.status_label.pack(side="right", padx=10)

        # Row 2: Pages selection info
        header_row2 = ctk.CTkFrame(header, fg_color="transparent")
        header_row2.pack(fill="x", padx=15, pady=(0, 12))

        ctk.CTkLabel(
            header_row2,
            text="📄 Pages đã chọn:",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_primary"]
        ).pack(side="left")

        self.pages_selected_label = ctk.CTkLabel(
            header_row2,
            text="0 pages",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["accent"]
        )
        self.pages_selected_label.pack(side="left", padx=10)

        # ========== MAIN CONTENT - Tabview ==========
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=COLORS["bg_secondary"],
            segmented_button_fg_color=COLORS["bg_card"],
            segmented_button_selected_color=COLORS["accent"],
            segmented_button_unselected_color=COLORS["bg_card"],
            corner_radius=12
        )
        self.tabview.pack(fill="both", expand=True, padx=15, pady=10)

        # Tabs
        self.tabview.add("📹 Đăng Reels")
        self.tabview.add("📅 Lên lịch")
        self.tabview.add("📊 Lịch sử")

        self._create_post_reels_tab()
        self._create_schedule_tab()
        self._create_history_tab()

    def _create_post_reels_tab(self):
        """Tab đăng Reels"""
        tab = self.tabview.tab("📹 Đăng Reels")

        # Container với 2 cột
        container = ctk.CTkFrame(tab, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        # ===== CỘT TRÁI: Chọn Pages =====
        left_col = ctk.CTkFrame(container, fg_color=COLORS["bg_card"], corner_radius=10, width=320)
        left_col.pack(side="left", fill="y", padx=(0, 10))
        left_col.pack_propagate(False)

        # Header
        pages_header = ctk.CTkFrame(left_col, fg_color="transparent")
        pages_header.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            pages_header,
            text="📄 Chọn Pages",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left")

        # Select all / Deselect all
        btn_frame = ctk.CTkFrame(pages_header, fg_color="transparent")
        btn_frame.pack(side="right")

        ctk.CTkButton(
            btn_frame,
            text="Chọn tất cả",
            width=80,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color=COLORS["accent"],
            command=self._select_all_pages
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            btn_frame,
            text="Bỏ chọn",
            width=70,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color=COLORS["border"],
            command=self._deselect_all_pages
        ).pack(side="left", padx=2)

        # Pages list với scrollable
        self.pages_scroll = ctk.CTkScrollableFrame(
            left_col,
            fg_color="transparent",
            height=400
        )
        self.pages_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.no_pages_label = ctk.CTkLabel(
            self.pages_scroll,
            text="Chọn profile để xem danh sách Pages",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        )
        self.no_pages_label.pack(pady=50)

        # ===== CỘT PHẢI: Nội dung Reels =====
        right_col = ctk.CTkFrame(container, fg_color=COLORS["bg_card"], corner_radius=10)
        right_col.pack(side="left", fill="both", expand=True)

        # Header
        ctk.CTkLabel(
            right_col,
            text="🎬 Nội dung Reels",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=15, pady=(15, 10))

        # Video upload section
        video_frame = ctk.CTkFrame(right_col, fg_color=COLORS["bg_secondary"], corner_radius=8)
        video_frame.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(
            video_frame,
            text="📹 Video Reels:",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=10, pady=(10, 5))

        video_btn_frame = ctk.CTkFrame(video_frame, fg_color="transparent")
        video_btn_frame.pack(fill="x", padx=10, pady=(0, 10))

        ModernButton(
            video_btn_frame,
            text="Chọn Video",
            icon="📂",
            variant="secondary",
            command=self._select_video,
            width=120
        ).pack(side="left")

        self.video_label = ctk.CTkLabel(
            video_btn_frame,
            text="Chưa chọn video",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"]
        )
        self.video_label.pack(side="left", padx=10)

        # Caption
        caption_frame = ctk.CTkFrame(right_col, fg_color=COLORS["bg_secondary"], corner_radius=8)
        caption_frame.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(
            caption_frame,
            text="✏️ Caption:",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=10, pady=(10, 5))

        self.caption_text = ctk.CTkTextbox(
            caption_frame,
            height=100,
            fg_color=COLORS["bg_card"],
            border_color=COLORS["border"],
            border_width=1,
            font=ctk.CTkFont(size=12)
        )
        self.caption_text.pack(fill="x", padx=10, pady=(0, 10))

        # Hashtags
        hashtag_frame = ctk.CTkFrame(right_col, fg_color=COLORS["bg_secondary"], corner_radius=8)
        hashtag_frame.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(
            hashtag_frame,
            text="#️⃣ Hashtags (cách nhau bởi dấu cách):",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=10, pady=(10, 5))

        self.hashtags_entry = ModernEntry(
            hashtag_frame,
            placeholder="#reels #facebook #viral"
        )
        self.hashtags_entry.pack(fill="x", padx=10, pady=(0, 10))

        # Cover image (optional)
        cover_frame = ctk.CTkFrame(right_col, fg_color=COLORS["bg_secondary"], corner_radius=8)
        cover_frame.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(
            cover_frame,
            text="🖼️ Ảnh bìa (tùy chọn):",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=10, pady=(10, 5))

        cover_btn_frame = ctk.CTkFrame(cover_frame, fg_color="transparent")
        cover_btn_frame.pack(fill="x", padx=10, pady=(0, 10))

        ModernButton(
            cover_btn_frame,
            text="Chọn ảnh",
            icon="🖼️",
            variant="secondary",
            command=self._select_cover,
            width=100
        ).pack(side="left")

        self.cover_label = ctk.CTkLabel(
            cover_btn_frame,
            text="Tự động từ video",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"]
        )
        self.cover_label.pack(side="left", padx=10)

        # Delay settings
        delay_frame = ctk.CTkFrame(right_col, fg_color=COLORS["bg_secondary"], corner_radius=8)
        delay_frame.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(
            delay_frame,
            text="⏱️ Delay giữa các đăng (giây):",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=10, pady=(10, 5))

        delay_input_frame = ctk.CTkFrame(delay_frame, fg_color="transparent")
        delay_input_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.delay_min_entry = ModernEntry(delay_input_frame, placeholder="30", width=80)
        self.delay_min_entry.pack(side="left")
        self.delay_min_entry.insert(0, "30")

        ctk.CTkLabel(
            delay_input_frame,
            text=" đến ",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        ).pack(side="left", padx=5)

        self.delay_max_entry = ModernEntry(delay_input_frame, placeholder="60", width=80)
        self.delay_max_entry.pack(side="left")
        self.delay_max_entry.insert(0, "60")

        ctk.CTkLabel(
            delay_input_frame,
            text=" giây",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        ).pack(side="left", padx=5)

        # Action buttons
        action_frame = ctk.CTkFrame(right_col, fg_color="transparent")
        action_frame.pack(fill="x", padx=15, pady=15)

        self.post_btn = ModernButton(
            action_frame,
            text="Đăng Reels Ngay",
            icon="🚀",
            variant="primary",
            command=self._start_posting,
            width=160
        )
        self.post_btn.pack(side="left", padx=5)

        self.schedule_btn = ModernButton(
            action_frame,
            text="Lên lịch đăng",
            icon="📅",
            variant="secondary",
            command=self._show_schedule_dialog,
            width=140
        )
        self.schedule_btn.pack(side="left", padx=5)

        self.stop_btn = ModernButton(
            action_frame,
            text="Dừng",
            icon="⏹️",
            variant="danger",
            command=self._stop_posting,
            width=100
        )
        self.stop_btn.pack(side="left", padx=5)
        self.stop_btn.configure(state="disabled")

        # Progress
        self.progress_label = ctk.CTkLabel(
            right_col,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        )
        self.progress_label.pack(anchor="w", padx=15, pady=(0, 10))

    def _create_schedule_tab(self):
        """Tab lên lịch"""
        tab = self.tabview.tab("📅 Lên lịch")

        # Header
        header = ctk.CTkFrame(tab, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            header,
            text="📅 Lịch đăng Reels",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left")

        ModernButton(
            header,
            text="Làm mới",
            icon="🔄",
            variant="secondary",
            command=self._load_schedules,
            width=100
        ).pack(side="right")

        # Schedule list
        self.schedule_scroll = ctk.CTkScrollableFrame(
            tab,
            fg_color=COLORS["bg_card"],
            corner_radius=10
        )
        self.schedule_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.no_schedule_label = ctk.CTkLabel(
            self.schedule_scroll,
            text="Chưa có lịch đăng nào",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_secondary"]
        )
        self.no_schedule_label.pack(pady=50)

    def _create_history_tab(self):
        """Tab lịch sử đăng"""
        tab = self.tabview.tab("📊 Lịch sử")

        # Header
        header = ctk.CTkFrame(tab, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            header,
            text="📊 Lịch sử đăng Reels",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left")

        # Filter
        filter_frame = ctk.CTkFrame(header, fg_color="transparent")
        filter_frame.pack(side="right")

        self.history_filter_var = ctk.StringVar(value="Tất cả")
        ctk.CTkOptionMenu(
            filter_frame,
            variable=self.history_filter_var,
            values=["Tất cả", "Thành công", "Thất bại", "Đang chờ"],
            fg_color=COLORS["bg_card"],
            button_color=COLORS["accent"],
            width=120,
            command=self._on_history_filter_change
        ).pack(side="left", padx=5)

        ModernButton(
            filter_frame,
            text="Làm mới",
            icon="🔄",
            variant="secondary",
            command=self._load_history,
            width=100
        ).pack(side="left", padx=5)

        # History list
        self.history_scroll = ctk.CTkScrollableFrame(
            tab,
            fg_color=COLORS["bg_card"],
            corner_radius=10
        )
        self.history_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.no_history_label = ctk.CTkLabel(
            self.history_scroll,
            text="Chưa có lịch sử đăng",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_secondary"]
        )
        self.no_history_label.pack(pady=50)

        # Pagination
        pagination = ctk.CTkFrame(tab, fg_color="transparent")
        pagination.pack(fill="x", padx=10, pady=5)

        self.history_prev_btn = ModernButton(
            pagination,
            text="Trước",
            icon="◀",
            variant="secondary",
            command=self._history_prev_page,
            width=80
        )
        self.history_prev_btn.pack(side="left")

        self.history_page_label = ctk.CTkLabel(
            pagination,
            text="Trang 1",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        )
        self.history_page_label.pack(side="left", padx=20)

        self.history_next_btn = ModernButton(
            pagination,
            text="Sau",
            icon="▶",
            variant="secondary",
            command=self._history_next_page,
            width=80
        )
        self.history_next_btn.pack(side="left")

    # ========== DATA LOADING ==========

    def _load_profiles(self):
        """Load danh sách profiles"""
        def load():
            self.profiles = get_profiles()
            self.after(0, self._update_profile_menu)

        threading.Thread(target=load, daemon=True).start()

    def _update_profile_menu(self):
        """Cập nhật dropdown profiles"""
        if not self.profiles:
            self.profile_menu.configure(values=["-- Không có profile --"])
            return

        values = ["-- Chọn profile --"]
        for p in self.profiles:
            name = p.get('name', p.get('uuid', '')[:8])
            values.append(name)

        self.profile_menu.configure(values=values)
        self.status_label.configure(text=f"{len(self.profiles)} profiles")

    def _on_profile_change(self, selection):
        """Xử lý khi thay đổi profile"""
        if selection == "-- Chọn profile --" or selection == "-- Không có profile --":
            self.current_profile_uuid = None
            self._clear_pages_list()
            return

        # Tìm profile UUID từ tên
        for p in self.profiles:
            name = p.get('name', p.get('uuid', '')[:8])
            if name == selection:
                self.current_profile_uuid = p.get('uuid')
                break

        if self.current_profile_uuid:
            self._load_pages()

    def _load_pages(self):
        """Load danh sách pages của profile"""
        if not self.current_profile_uuid:
            return

        def load():
            self.pages = get_pages_for_profiles([self.current_profile_uuid])
            self.after(0, self._update_pages_list)

        threading.Thread(target=load, daemon=True).start()

    def _clear_pages_list(self):
        """Xóa danh sách pages"""
        for widget in self.pages_scroll.winfo_children():
            widget.destroy()

        self.no_pages_label = ctk.CTkLabel(
            self.pages_scroll,
            text="Chọn profile để xem danh sách Pages",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        )
        self.no_pages_label.pack(pady=50)
        self.pages_selected_label.configure(text="0 pages")

    def _update_pages_list(self):
        """Cập nhật danh sách pages"""
        # Clear old widgets
        for widget in self.pages_scroll.winfo_children():
            widget.destroy()

        self._page_checkbox_vars.clear()
        self.selected_page_ids.clear()

        if not self.pages:
            self.no_pages_label = ctk.CTkLabel(
                self.pages_scroll,
                text="Profile này chưa có Page nào.\nHãy tạo Page trước.",
                font=ctk.CTkFont(size=12),
                text_color=COLORS["text_secondary"]
            )
            self.no_pages_label.pack(pady=50)
            self.pages_selected_label.configure(text="0 pages")
            return

        # Render pages
        for page in self.pages:
            self._render_page_item(page)

        self._update_selected_count()

    def _render_page_item(self, page: Dict):
        """Render một page item"""
        page_id = page.get('id', 0)

        frame = ctk.CTkFrame(self.pages_scroll, fg_color=COLORS["bg_secondary"], corner_radius=8)
        frame.pack(fill="x", pady=3)

        # Checkbox
        var = ctk.BooleanVar(value=False)
        self._page_checkbox_vars[page_id] = var

        cb = ctk.CTkCheckBox(
            frame,
            text="",
            variable=var,
            width=24,
            command=self._update_selected_count
        )
        cb.pack(side="left", padx=10, pady=8)

        # Page info
        info_frame = ctk.CTkFrame(frame, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True, pady=5)

        page_name = page.get('page_name', 'Unknown')
        ctk.CTkLabel(
            info_frame,
            text=page_name,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")

        category = page.get('category', '')
        if category:
            ctk.CTkLabel(
                info_frame,
                text=f"📁 {category}",
                font=ctk.CTkFont(size=10),
                text_color=COLORS["text_secondary"]
            ).pack(anchor="w")

    def _update_selected_count(self):
        """Cập nhật số pages đã chọn"""
        self.selected_page_ids = [
            pid for pid, var in self._page_checkbox_vars.items()
            if var.get()
        ]
        count = len(self.selected_page_ids)
        self.pages_selected_label.configure(text=f"{count} pages")

    def _select_all_pages(self):
        """Chọn tất cả pages"""
        for var in self._page_checkbox_vars.values():
            var.set(True)
        self._update_selected_count()

    def _deselect_all_pages(self):
        """Bỏ chọn tất cả pages"""
        for var in self._page_checkbox_vars.values():
            var.set(False)
        self._update_selected_count()

    # ========== VIDEO & COVER SELECTION ==========

    def _select_video(self):
        """Chọn video Reels"""
        filetypes = [
            ("Video files", "*.mp4 *.mov *.avi *.mkv"),
            ("All files", "*.*")
        ]
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            self.video_path = path
            filename = os.path.basename(path)
            self.video_label.configure(text=filename[:40] + "..." if len(filename) > 40 else filename)
            self._set_status(f"Đã chọn video: {filename}", "info")

    def _select_cover(self):
        """Chọn ảnh bìa"""
        filetypes = [
            ("Image files", "*.jpg *.jpeg *.png *.webp"),
            ("All files", "*.*")
        ]
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            self.cover_path = path
            filename = os.path.basename(path)
            self.cover_label.configure(text=filename[:30] + "..." if len(filename) > 30 else filename)

    # ========== POSTING ==========

    def _start_posting(self):
        """Bắt đầu đăng Reels"""
        if self._is_posting:
            return

        # Validate
        if not self.video_path:
            self._set_status("Vui lòng chọn video!", "error")
            return

        if not os.path.exists(self.video_path):
            self._set_status("File video không tồn tại!", "error")
            return

        if not self.selected_page_ids:
            self._set_status("Vui lòng chọn ít nhất 1 Page!", "error")
            return

        self._is_posting = True
        self.post_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

        # Get content
        caption = self.caption_text.get("1.0", "end-1c").strip()
        hashtags = self.hashtags_entry.get().strip()

        try:
            delay_min = int(self.delay_min_entry.get() or "30")
            delay_max = int(self.delay_max_entry.get() or "60")
        except ValueError:
            delay_min, delay_max = 30, 60

        # Start posting thread
        threading.Thread(
            target=self._posting_worker,
            args=(caption, hashtags, delay_min, delay_max),
            daemon=True
        ).start()

    def _posting_worker(self, caption: str, hashtags: str, delay_min: int, delay_max: int):
        """Worker thread đăng Reels"""
        import random

        total = len(self.selected_page_ids)
        success = 0
        failed = 0

        for idx, page_id in enumerate(self.selected_page_ids):
            if not self._is_posting:
                break

            # Find page info
            page = next((p for p in self.pages if p.get('id') == page_id), None)
            if not page:
                continue

            page_name = page.get('page_name', 'Unknown')
            self.after(0, lambda n=page_name, i=idx, t=total:
                self.progress_label.configure(text=f"Đang đăng lên {n} ({i+1}/{t})...")
            )

            # TODO: Implement actual Reels posting via CDP
            # For now, simulate posting
            try:
                self._post_reel_to_page(page, caption, hashtags)
                success += 1
                self._set_status(f"Đã đăng Reels lên {page_name}", "success")
            except Exception as e:
                failed += 1
                self._set_status(f"Lỗi đăng lên {page_name}: {str(e)}", "error")

            # Delay between posts
            if idx < total - 1 and self._is_posting:
                delay = random.randint(delay_min, delay_max)
                self.after(0, lambda d=delay:
                    self.progress_label.configure(text=f"Đợi {d} giây...")
                )
                time.sleep(delay)

        # Done
        self._is_posting = False
        self.after(0, lambda: self.post_btn.configure(state="normal"))
        self.after(0, lambda: self.stop_btn.configure(state="disabled"))
        self.after(0, lambda s=success, f=failed:
            self.progress_label.configure(text=f"Hoàn tất: {s} thành công, {f} thất bại")
        )
        self._set_status(f"Hoàn tất đăng Reels: {success}/{total}", "success" if failed == 0 else "warning")

    def _open_browser_with_cdp(self, profile_uuid: str, max_browser_retries: int = 2):
        """
        Mở browser và kết nối CDP với logic retry.
        Nếu CDP fail, đóng browser và mở lại.
        Returns: (remote_port, tabs) hoặc raise Exception
        """
        import urllib.request

        for browser_attempt in range(max_browser_retries):
            # Mở browser
            print(f"[ReelsPage] Opening browser (attempt {browser_attempt + 1}/{max_browser_retries})...")
            result = api.open_browser(profile_uuid)

            if not result or result.get('status') != 'successfully':
                raise Exception(f"Không mở được browser: {result}")

            browser_info = result.get('data', {})
            remote_port = browser_info.get('remote_port') or browser_info.get('remote_debugging_port')

            if not remote_port:
                raise Exception("Không lấy được remote debugging port")

            print(f"[ReelsPage] Browser opened, port: {remote_port}")
            time.sleep(3)

            # Thử kết nối CDP
            cdp_base = f"http://127.0.0.1:{remote_port}"
            tabs_url = f"{cdp_base}/json"

            cdp_connected = False
            tabs = None

            for cdp_attempt in range(5):
                try:
                    with urllib.request.urlopen(tabs_url, timeout=10) as resp:
                        tabs = json_module.loads(resp.read().decode())
                        cdp_connected = True
                        break
                except Exception as e:
                    print(f"[ReelsPage] CDP retry {cdp_attempt + 1}/5: {e}")
                    time.sleep(2)

            if cdp_connected and tabs:
                print(f"[ReelsPage] CDP connected successfully!")
                return remote_port, tabs

            # CDP fail - đóng browser và thử lại
            if browser_attempt < max_browser_retries - 1:
                print(f"[ReelsPage] CDP connection failed, closing browser and retrying...")
                try:
                    api.close_browser(profile_uuid)
                    time.sleep(3)
                except Exception as e:
                    print(f"[ReelsPage] Error closing browser: {e}")
                    time.sleep(2)
            else:
                raise Exception("Không kết nối được CDP sau nhiều lần thử")

        raise Exception("Không kết nối được CDP")

    def _post_reel_to_page(self, page: Dict, caption: str, hashtags: str):
        """Đăng Reels lên một Page qua CDPHelper (CDPClientMAX)"""
        profile_uuid = page.get('profile_uuid')
        page_id = page.get('page_id')
        page_name = page.get('page_name', 'Unknown')
        page_url = page.get('page_url', f"https://www.facebook.com/{page_id}")

        print(f"[ReelsPage] Đang đăng Reels lên {page_name}...")
        print(f"[ReelsPage] Video: {self.video_path}")
        print(f"[ReelsPage] Caption: {caption[:50] if caption else 'N/A'}...")
        print(f"[ReelsPage] Hashtags: {hashtags}")

        # Acquire window slot
        slot_id = acquire_window_slot()
        cdp = None

        try:
            # Bước 1: Mở browser và kết nối CDP
            remote_port, tabs = self._open_browser_with_cdp(profile_uuid)

            # Tìm WebSocket URL
            page_ws = None
            for tab in tabs:
                if tab.get('type') == 'page':
                    ws_url = tab.get('webSocketDebuggerUrl', '')
                    if ws_url:
                        page_ws = ws_url
                        break

            if not page_ws:
                raise Exception("Không tìm thấy tab Facebook")

            # Bước 2: Kết nối CDPHelper
            cdp = CDPHelper()
            if not cdp.connect(remote_port=remote_port, ws_url=page_ws):
                raise Exception("Không kết nối được CDPHelper")

            print(f"[ReelsPage] CDPHelper connected!")

            # Set window position
            bounds = get_window_bounds(slot_id)
            if bounds:
                x, y, w, h = bounds
                cdp.set_window_bounds(x, y, w, h)
                print(f"[ReelsPage] Window positioned at ({x}, {y})")

            # Bước 3: Navigate đến page để switch context
            print(f"[ReelsPage] Navigating to page: {page_url}")
            cdp.navigate(page_url)
            cdp.wait_for_page_load()
            time.sleep(3)

            # Bước 4: Click "Chuyển ngay" để switch sang Page context
            print(f"[ReelsPage] Looking for 'Chuyển ngay' button...")
            js_click_switch = '''
            (function() {
                var buttons = document.querySelectorAll('div[role="button"], span[role="button"]');
                for (var i = 0; i < buttons.length; i++) {
                    var btn = buttons[i];
                    var ariaLabel = btn.getAttribute('aria-label') || '';
                    var text = (btn.innerText || '').trim();
                    if (ariaLabel === 'Chuyển ngay' || text === 'Chuyển ngay' ||
                        ariaLabel === 'Switch now' || text === 'Switch now') {
                        btn.click();
                        return 'clicked_switch: ' + (ariaLabel || text);
                    }
                }
                return 'no_switch_button_found';
            })();
            '''
            switch_result = cdp.execute_js(js_click_switch)
            print(f"[ReelsPage] Switch result: {switch_result}")

            if 'no_switch_button_found' not in str(switch_result):
                time.sleep(3)

            # Bước 5: Navigate đến Reels creator
            reels_create_url = "https://www.facebook.com/reels/create"
            print(f"[ReelsPage] Navigating to Reels creator: {reels_create_url}")
            cdp.navigate(reels_create_url)
            cdp.wait_for_page_load(timeout_ms=20000)
            time.sleep(3)

            current_url = cdp.execute_js("window.location.href")
            print(f"[ReelsPage] Current URL: {current_url}")

            # Bước 6: Upload video
            print(f"[ReelsPage] Preparing to upload video...")
            video_path = self.video_path.replace('\\', '/')

            # Click vào vùng upload
            js_click_upload_area = '''
            (function() {
                var uploadSelectors = [
                    '[aria-label*="video"]', '[aria-label*="Tải"]', '[aria-label*="Upload"]',
                    '[aria-label*="Thêm video"]', '[aria-label*="Add video"]'
                ];
                for (var i = 0; i < uploadSelectors.length; i++) {
                    try {
                        var el = document.querySelector(uploadSelectors[i]);
                        if (el) {
                            var btn = el.closest('[role="button"]') || el;
                            if (btn && btn.click) {
                                btn.click();
                                return 'clicked: ' + uploadSelectors[i];
                            }
                        }
                    } catch(e) {}
                }
                return 'no_upload_area';
            })();
            '''
            upload_result = cdp.execute_js(js_click_upload_area)
            print(f"[ReelsPage] Upload area: {upload_result}")
            time.sleep(2)

            # Upload file sử dụng CDPHelper
            selectors_to_try = [
                'input[type="file"][accept*="video"]',
                'input[type="file"][accept*="mp4"]',
                'input[type="file"]'
            ]

            uploaded = False
            for selector in selectors_to_try:
                try:
                    if cdp.upload_file(selector, video_path):
                        print(f"[ReelsPage] Video uploaded via: {selector}")
                        uploaded = True
                        break
                except Exception as e:
                    print(f"[ReelsPage] Upload error: {e}")
                    continue

            if not uploaded:
                raise Exception("Không upload được video")

            # Đợi video xử lý
            print(f"[ReelsPage] Waiting for video processing...")
            time.sleep(15)

            # Bước 7: Click nút "Tiếp"
            js_click_next = '''
            (function() {
                var spans = document.querySelectorAll('span');
                for (var i = 0; i < spans.length; i++) {
                    var text = (spans[i].innerText || '').trim();
                    if (text === 'Tiếp' || text === 'Next') {
                        var clickable = spans[i].closest('div[role="none"]') ||
                                       spans[i].closest('div[role="button"]') ||
                                       spans[i].parentElement.parentElement;
                        if (clickable && clickable.offsetParent !== null) {
                            clickable.click();
                            return 'clicked: ' + text;
                        }
                    }
                }
                return 'no_next_button';
            })();
            '''

            print(f"[ReelsPage] Looking for 'Tiếp' button...")
            next_result = cdp.execute_js(js_click_next)
            print(f"[ReelsPage] First 'Tiếp': {next_result}")
            if 'clicked' in str(next_result):
                time.sleep(5)

            print(f"[ReelsPage] Looking for second 'Tiếp' button...")
            next_result2 = cdp.execute_js(js_click_next)
            print(f"[ReelsPage] Second 'Tiếp': {next_result2}")
            if 'clicked' in str(next_result2):
                time.sleep(5)

            # Bước 8: Nhập caption
            full_caption = f"{caption}\n\n{hashtags}" if hashtags else caption

            if full_caption:
                print(f"[ReelsPage] Adding caption: {full_caption[:50]}...")

                js_focus_caption = '''
                (function() {
                    var editors = document.querySelectorAll('[contenteditable="true"][data-lexical-editor="true"]');
                    for (var i = 0; i < editors.length; i++) {
                        var ed = editors[i];
                        var placeholder = (ed.getAttribute('aria-placeholder') || '').toLowerCase();
                        if (placeholder.includes('mô tả') || placeholder.includes('thước phim')) {
                            ed.click();
                            ed.focus();
                            return 'focused: ' + placeholder;
                        }
                    }
                    // Fallback
                    var allEditors = document.querySelectorAll('[contenteditable="true"]');
                    for (var i = 0; i < allEditors.length; i++) {
                        var ed = allEditors[i];
                        var ariaLabel = (ed.getAttribute('aria-label') || '').toLowerCase();
                        var placeholder = (ed.getAttribute('aria-placeholder') || '').toLowerCase();

                        if (!ariaLabel.includes('bình luận') && !ariaLabel.includes('comment') &&
                            !placeholder.includes('bình luận') && !placeholder.includes('comment')) {
                            ed.click();
                            ed.focus();
                            return 'found_fallback_editor: ' + (placeholder || ariaLabel);
                        }
                    }

                    return 'no_editor';
                })();
                '''
                focus_result = cdp.execute_js(js_focus_caption)
                print(f"[ReelsPage] Focus caption: {focus_result}")
                time.sleep(0.5)

                # Gõ caption human-like qua CDPHelper
                print(f"[ReelsPage] Typing caption ({len(full_caption)} chars)...")
                cdp.type_human_like(full_caption)
                time.sleep(2)

            # Bước 9: Click nút đăng
            print(f"[ReelsPage] Looking for 'Đăng' button...")
            js_click_post = '''
            (function() {
                var spans = document.querySelectorAll('span');
                for (var i = 0; i < spans.length; i++) {
                    var text = (spans[i].innerText || '').trim();
                    if (text === 'Đăng' || text === 'Share' || text === 'Post') {
                        var clickable = spans[i].closest('div[role="none"]') ||
                                       spans[i].closest('div[role="button"]') ||
                                       spans[i].parentElement.parentElement;
                        if (clickable && clickable.offsetParent !== null) {
                            clickable.click();
                            return 'clicked: ' + text;
                        }
                    }
                }
                return 'no_post_button';
            })();
            '''
            click_result = cdp.execute_js(js_click_post)
            print(f"[ReelsPage] Post button: {click_result}")

            if 'no_post_button' in str(click_result):
                raise Exception("Không tìm thấy nút đăng")

            # Đợi đăng xong
            print(f"[ReelsPage] Waiting for Reel to be posted...")
            time.sleep(15)

            # Bước 10: Lấy link Reel
            js_get_reel_url = '''
            (function() {
                var url = window.location.href;
                if (url.includes('/reel/')) return url;

                var links = document.querySelectorAll('a[href*="/reel/"]');
                for (var i = links.length - 1; i >= 0; i--) {
                    if (links[i].href.match(/\\/reel\\/\\d+/)) return links[i].href;
                }

                var html = document.documentElement.innerHTML;
                var match = html.match(/facebook\\.com\\/reel\\/(\\d+)/);
                if (match) return 'https://www.facebook.com/reel/' + match[1];

                return 'no_reel_url';
            })();
            '''

            reel_url = None
            for attempt in range(8):
                reel_url = cdp.execute_js(js_get_reel_url)
                print(f"[ReelsPage] Attempt {attempt + 1}/8 - Reel URL: {reel_url}")

                if reel_url and 'no_reel_url' not in str(reel_url) and '/reel/' in str(reel_url):
                    print(f"[ReelsPage] Found Reel URL!")
                    break
                time.sleep(4)

            # Clean URL
            final_reel_url = None
            if reel_url and 'no_reel_url' not in str(reel_url):
                match = re.search(r'(https?://[^?#\s]+/reel/\d+)', str(reel_url))
                final_reel_url = match.group(1) if match else str(reel_url).split('?')[0]

            print(f"[ReelsPage] Clean Reel URL: {final_reel_url}")

            # Lưu vào database
            save_posted_reel({
                'profile_uuid': profile_uuid,
                'page_id': page_id,
                'page_name': page_name,
                'reel_url': final_reel_url or '',
                'caption': caption,
                'hashtags': hashtags,
                'video_path': self.video_path,
                'status': 'success'
            })

            print(f"[ReelsPage] SUCCESS - Đã đăng Reels lên {page_name}")
            if final_reel_url:
                print(f"[ReelsPage] REEL URL: {final_reel_url}")
            return final_reel_url

        except Exception as e:
            print(f"[ReelsPage] ERROR: {e}")
            import traceback
            traceback.print_exc()

            try:
                save_posted_reel({
                    'profile_uuid': profile_uuid,
                    'page_id': page_id,
                    'page_name': page_name,
                    'reel_url': '',
                    'caption': caption,
                    'hashtags': hashtags,
                    'video_path': self.video_path if hasattr(self, 'video_path') else '',
                    'status': 'failed',
                    'error_message': str(e)
                })
            except:
                pass
            raise e

        finally:
            if cdp:
                cdp.close()
            release_window_slot(slot_id)

    def _cdp_send(self, ws, method: str, params: Dict = None) -> Dict:
        """Gửi CDP command và nhận response"""
        self._cdp_id += 1
        msg = {"id": self._cdp_id, "method": method, "params": params or {}}
        ws.send(json_module.dumps(msg))

        while True:
            try:
                ws.settimeout(30)
                resp = ws.recv()
                data = json_module.loads(resp)
                if data.get('id') == self._cdp_id:
                    return data
            except:
                return {}

    def _cdp_evaluate(self, ws, expression: str) -> Any:
        """Evaluate JavaScript trong browser"""
        result = self._cdp_send(ws, "Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": True
        })
        return result.get('result', {}).get('result', {}).get('value')

    def _cdp_type_human_like(self, ws, text: str, typo_chance: float = 0.03):
        """
        Gõ text từng ký tự như người thật qua CDP Input.insertText
        - Tốc độ gõ random (50-150ms mỗi ký tự)
        - Pause dài hơn sau dấu câu
        - Occasionally có typo và sửa lại
        """
        # Typo map - các phím gần nhau
        typo_map = {
            'a': ['s', 'q'], 'b': ['v', 'n'], 'c': ['x', 'v'],
            'd': ['s', 'f'], 'e': ['w', 'r'], 'f': ['d', 'g'],
            'g': ['f', 'h'], 'h': ['g', 'j'], 'i': ['u', 'o'],
            'j': ['h', 'k'], 'k': ['j', 'l'], 'l': ['k', 'o'],
            'm': ['n', 'k'], 'n': ['b', 'm'], 'o': ['i', 'p'],
            'p': ['o', 'l'], 'r': ['e', 't'], 's': ['a', 'd'],
            't': ['r', 'y'], 'u': ['y', 'i'], 'v': ['c', 'b'],
            'w': ['q', 'e'], 'x': ['z', 'c'], 'y': ['t', 'u'],
        }

        for char in text:
            # Random typo cho lowercase letters
            if char.lower() in typo_map and random.random() < typo_chance:
                # Gõ sai
                wrong_char = random.choice(typo_map[char.lower()])
                self._cdp_send(ws, "Input.insertText", {"text": wrong_char})
                time.sleep(random.uniform(0.1, 0.25))

                # Nhận ra sai, pause một chút
                time.sleep(random.uniform(0.15, 0.35))

                # Backspace để xóa
                self._cdp_send(ws, "Input.dispatchKeyEvent", {
                    "type": "keyDown", "key": "Backspace", "code": "Backspace",
                    "windowsVirtualKeyCode": 8, "nativeVirtualKeyCode": 8
                })
                self._cdp_send(ws, "Input.dispatchKeyEvent", {
                    "type": "keyUp", "key": "Backspace", "code": "Backspace",
                    "windowsVirtualKeyCode": 8, "nativeVirtualKeyCode": 8
                })
                time.sleep(random.uniform(0.08, 0.15))

            # Gõ ký tự đúng
            self._cdp_send(ws, "Input.insertText", {"text": char})

            # Delay phụ thuộc vào loại ký tự
            if char in ' .,!?;:':
                # Pause dài hơn sau dấu câu/space
                time.sleep(random.uniform(0.1, 0.25))
            elif char == '\n':
                # Pause dài sau xuống dòng
                time.sleep(random.uniform(0.3, 0.6))
            else:
                # Tốc độ gõ bình thường: 50-150ms
                time.sleep(random.uniform(0.05, 0.15))

            # Occasionally pause dài (như đang nghĩ)
            if random.random() < 0.02:
                time.sleep(random.uniform(0.4, 1.0))

    def _stop_posting(self):
        """Dừng đăng"""
        self._is_posting = False
        self.stop_btn.configure(state="disabled")
        self._set_status("Đã dừng đăng", "warning")

    # ========== SCHEDULING ==========

    def _show_schedule_dialog(self):
        """Hiển thị dialog lên lịch"""
        if not self.video_path:
            self._set_status("Vui lòng chọn video!", "error")
            return

        if not self.selected_page_ids:
            self._set_status("Vui lòng chọn ít nhất 1 Page!", "error")
            return

        # Create schedule dialog
        dialog = ScheduleDialog(self, self._on_schedule_confirm)
        dialog.grab_set()

    def _on_schedule_confirm(self, schedule_time: datetime):
        """Xử lý khi confirm lên lịch"""
        caption = self.caption_text.get("1.0", "end-1c").strip()
        hashtags = self.hashtags_entry.get().strip()

        try:
            delay_min = int(self.delay_min_entry.get() or "30")
            delay_max = int(self.delay_max_entry.get() or "60")
        except ValueError:
            delay_min, delay_max = 30, 60

        # Save schedule for each selected page
        for page_id in self.selected_page_ids:
            page = next((p for p in self.pages if p.get('id') == page_id), None)
            if not page:
                continue

            schedule_data = {
                'profile_uuid': self.current_profile_uuid,
                'page_id': page_id,
                'page_name': page.get('page_name', ''),
                'video_path': self.video_path,
                'cover_path': self.cover_path or '',
                'caption': caption,
                'hashtags': hashtags,
                'scheduled_time': schedule_time.strftime('%Y-%m-%d %H:%M:%S'),
                'delay_min': delay_min,
                'delay_max': delay_max,
                'status': 'pending'
            }
            save_reel_schedule(schedule_data)

        self._set_status(f"Đã lên lịch đăng Reels cho {len(self.selected_page_ids)} Pages", "success")
        self._load_schedules()
        self.tabview.set("📅 Lên lịch")

    def _load_schedules(self):
        """Load danh sách lịch đăng"""
        def load():
            schedules = get_reel_schedules(self.current_profile_uuid if self.current_profile_uuid else None)
            self.after(0, lambda s=schedules: self._update_schedules_list(s))

        threading.Thread(target=load, daemon=True).start()

    def _update_schedules_list(self, schedules: List[Dict]):
        """Cập nhật danh sách lịch đăng"""
        for widget in self.schedule_scroll.winfo_children():
            widget.destroy()

        if not schedules:
            self.no_schedule_label = ctk.CTkLabel(
                self.schedule_scroll,
                text="Chưa có lịch đăng nào",
                font=ctk.CTkFont(size=13),
                text_color=COLORS["text_secondary"]
            )
            self.no_schedule_label.pack(pady=50)
            return

        for schedule in schedules:
            self._render_schedule_item(schedule)

    def _render_schedule_item(self, schedule: Dict):
        """Render một schedule item"""
        frame = ctk.CTkFrame(self.schedule_scroll, fg_color=COLORS["bg_secondary"], corner_radius=8)
        frame.pack(fill="x", pady=5, padx=10)

        # Status indicator
        status = schedule.get('status', 'pending')
        status_colors = {
            'pending': COLORS["warning"],
            'completed': COLORS["success"],
            'failed': COLORS["error"]
        }
        status_text = {'pending': '⏳', 'completed': '✅', 'failed': '❌'}

        ctk.CTkLabel(
            frame,
            text=status_text.get(status, '⏳'),
            font=ctk.CTkFont(size=20),
            text_color=status_colors.get(status, COLORS["text_secondary"])
        ).pack(side="left", padx=10, pady=10)

        # Info
        info_frame = ctk.CTkFrame(frame, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True, pady=10)

        page_name = schedule.get('page_name', 'Unknown Page')
        ctk.CTkLabel(
            info_frame,
            text=page_name,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")

        scheduled_time = schedule.get('scheduled_time', '')
        ctk.CTkLabel(
            info_frame,
            text=f"📅 {scheduled_time}",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w")

        caption = schedule.get('caption', '')[:50]
        if caption:
            ctk.CTkLabel(
                info_frame,
                text=f"✏️ {caption}...",
                font=ctk.CTkFont(size=10),
                text_color=COLORS["text_secondary"]
            ).pack(anchor="w")

        # Actions
        if status == 'pending':
            action_frame = ctk.CTkFrame(frame, fg_color="transparent")
            action_frame.pack(side="right", padx=10)

            ctk.CTkButton(
                action_frame,
                text="Xóa",
                width=60,
                height=28,
                fg_color=COLORS["error"],
                hover_color="#ff5555",
                command=lambda s=schedule: self._delete_schedule(s)
            ).pack()

    def _delete_schedule(self, schedule: Dict):
        """Xóa lịch đăng"""
        schedule_id = schedule.get('id')
        if schedule_id:
            delete_reel_schedule(schedule_id)
            self._load_schedules()
            self._set_status("Đã xóa lịch đăng", "info")

    # ========== HISTORY ==========

    def _load_history(self):
        """Load lịch sử đăng từ posted_reels"""
        # Clear current items
        for widget in self.history_scroll.winfo_children():
            widget.destroy()

        # Get posted reels from database
        profile_uuid = self.current_profile_uuid
        reels = get_posted_reels(profile_uuid=profile_uuid, limit=self._history_page_size, offset=self._history_page * self._history_page_size)

        if not reels:
            self.no_history_label = ctk.CTkLabel(
                self.history_scroll,
                text="Chưa có lịch sử đăng",
                font=ctk.CTkFont(size=13),
                text_color=COLORS["text_secondary"]
            )
            self.no_history_label.pack(pady=50)
            return

        # Display each reel
        for reel in reels:
            self._create_history_item(reel)

        # Update pagination
        self.history_page_label.configure(text=f"Trang {self._history_page + 1}")

    def _create_history_item(self, reel: Dict):
        """Tạo item cho lịch sử"""
        item = ctk.CTkFrame(self.history_scroll, fg_color=COLORS["bg_secondary"], corner_radius=8)
        item.pack(fill="x", padx=5, pady=5)

        # Left: Info
        info_frame = ctk.CTkFrame(item, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True, padx=10, pady=8)

        # Page name and status
        status_color = COLORS["success"] if reel.get('status') == 'success' else COLORS["error"]
        status_icon = "✓" if reel.get('status') == 'success' else "✗"

        ctk.CTkLabel(
            info_frame,
            text=f"{status_icon} {reel.get('page_name', 'Unknown')}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=status_color
        ).pack(anchor="w")

        # Reel URL (truncated)
        reel_url = reel.get('reel_url', '')
        if reel_url:
            url_display = reel_url[:50] + "..." if len(reel_url) > 50 else reel_url
            url_label = ctk.CTkLabel(
                info_frame,
                text=url_display,
                font=ctk.CTkFont(size=11),
                text_color=COLORS["accent"],
                cursor="hand2"
            )
            url_label.pack(anchor="w")
            url_label.bind("<Button-1>", lambda e, url=reel_url: self._open_url(url))

        # Caption (truncated)
        caption = reel.get('caption', '')
        if caption:
            caption_display = caption[:40] + "..." if len(caption) > 40 else caption
            ctk.CTkLabel(
                info_frame,
                text=f"📝 {caption_display}",
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text_secondary"]
            ).pack(anchor="w")

        # Time
        posted_at = reel.get('posted_at', '')
        if posted_at:
            ctk.CTkLabel(
                info_frame,
                text=f"🕐 {posted_at}",
                font=ctk.CTkFont(size=10),
                text_color=COLORS["text_secondary"]
            ).pack(anchor="w")

        # Right: Action buttons
        btn_frame = ctk.CTkFrame(item, fg_color="transparent")
        btn_frame.pack(side="right", padx=10, pady=8)

        # CMT button
        if reel_url:
            ModernButton(
                btn_frame,
                text="💬 CMT",
                variant="primary",
                command=lambda r=reel: self._comment_on_reel(r),
                width=80
            ).pack(side="left", padx=2)

        # Copy URL button
        if reel_url:
            ModernButton(
                btn_frame,
                text="📋",
                variant="secondary",
                command=lambda url=reel_url: self._copy_to_clipboard(url),
                width=40
            ).pack(side="left", padx=2)

    def _open_url(self, url: str):
        """Mở URL trong browser"""
        import webbrowser
        webbrowser.open(url)

    def _copy_to_clipboard(self, text: str):
        """Copy text vào clipboard"""
        self.clipboard_clear()
        self.clipboard_append(text)
        print(f"[ReelsPage] Copied to clipboard: {text}")

    def _comment_on_reel(self, reel: Dict):
        """Mở dialog comment cho Reel"""
        CommentDialog(self, reel, self._do_comment_on_reel)

    def _do_comment_on_reel(self, reel: Dict, comment_text: str):
        """Thực hiện comment lên Reel"""
        if not comment_text.strip():
            print("[ReelsPage] Comment text is empty")
            return

        reel_url = reel.get('reel_url', '')
        profile_uuid = reel.get('profile_uuid', self.current_profile_uuid)

        if not reel_url:
            print("[ReelsPage] No Reel URL to comment")
            return

        print(f"[ReelsPage] Commenting on Reel: {reel_url}")
        print(f"[ReelsPage] Comment: {comment_text}")

        # Run in thread
        import threading
        thread = threading.Thread(
            target=self._post_comment_thread,
            args=(profile_uuid, reel_url, comment_text),
            daemon=True
        )
        thread.start()

    def _on_history_filter_change(self, selection):
        """Xử lý khi thay đổi filter"""
        self._history_page = 0
        self._load_history()

    def _history_prev_page(self):
        """Trang trước"""
        if self._history_page > 0:
            self._history_page -= 1
            self._load_history()

    def _history_next_page(self):
        """Trang sau"""
        self._history_page += 1
        self._load_history()

    def _post_comment_thread(self, profile_uuid: str, reel_url: str, comment_text: str):
        """Thread để đăng comment lên Reel"""
        if not WEBSOCKET_AVAILABLE:
            print("[ReelsPage] ERROR: websocket-client chưa được cài đặt")
            return

        slot_id = acquire_window_slot()
        ws = None

        try:
            # Mở browser và kết nối CDP với retry logic
            remote_port, tabs = self._open_browser_with_cdp(profile_uuid)

            # Tìm tab
            page_ws = None
            for tab in tabs:
                if tab.get('type') == 'page':
                    ws_url = tab.get('webSocketDebuggerUrl', '')
                    if ws_url:
                        page_ws = ws_url
                        break

            if not page_ws:
                raise Exception("Không tìm thấy tab")

            # Kết nối WebSocket
            try:
                ws = websocket.create_connection(page_ws, timeout=30, suppress_origin=True)
            except:
                ws = websocket.create_connection(page_ws, timeout=30)

            # Navigate đến Reel
            print(f"[ReelsPage] Navigating to Reel: {reel_url}")
            self._cdp_send(ws, "Page.navigate", {"url": reel_url})
            time.sleep(8)

            # Đợi page load
            for _ in range(10):
                ready = self._cdp_evaluate(ws, "document.readyState")
                if ready == 'complete':
                    break
                time.sleep(1)

            time.sleep(3)

            # Tìm và click vào ô comment - ưu tiên Lexical editor với aria-label chứa "Bình luận"
            js_click_comment_box = '''
            (function() {
                // Debug: list all contenteditable elements
                var allEditors = document.querySelectorAll('[contenteditable="true"]');
                console.log('Found contenteditable elements:', allEditors.length);
                for (var i = 0; i < allEditors.length; i++) {
                    console.log('Editor ' + i + ':', allEditors[i].getAttribute('aria-label'));
                }

                // Ưu tiên 1: Tìm Lexical editor với aria-label chứa "Bình luận"
                var lexicalEditors = document.querySelectorAll('[contenteditable="true"][data-lexical-editor="true"]');
                for (var i = 0; i < lexicalEditors.length; i++) {
                    var editor = lexicalEditors[i];
                    var ariaLabel = (editor.getAttribute('aria-label') || '').toLowerCase();
                    // Tìm ô bình luận (không phải caption/mô tả)
                    if (ariaLabel.includes('bình luận') || ariaLabel.includes('comment')) {
                        if (editor.offsetParent !== null) {
                            editor.click();
                            editor.focus();
                            return 'clicked_lexical_comment: ' + editor.getAttribute('aria-label');
                        }
                    }
                }

                // Ưu tiên 2: Tìm contenteditable với aria-label chứa bình luận
                var commentInputs = document.querySelectorAll(
                    '[contenteditable="true"][aria-label*="bình luận" i], ' +
                    '[contenteditable="true"][aria-label*="comment" i]'
                );
                for (var i = 0; i < commentInputs.length; i++) {
                    var input = commentInputs[i];
                    if (input.offsetParent !== null) {
                        input.click();
                        input.focus();
                        return 'clicked_comment_box: ' + input.getAttribute('aria-label');
                    }
                }

                // Ưu tiên 3: Tìm role="textbox" với aria-label bình luận
                var textboxes = document.querySelectorAll('[role="textbox"]');
                for (var i = 0; i < textboxes.length; i++) {
                    var tb = textboxes[i];
                    var ariaLabel = (tb.getAttribute('aria-label') || '').toLowerCase();
                    if (ariaLabel.includes('bình luận') || ariaLabel.includes('comment')) {
                        if (tb.offsetParent !== null) {
                            tb.click();
                            tb.focus();
                            return 'clicked_textbox: ' + tb.getAttribute('aria-label');
                        }
                    }
                }

                // Fallback: tìm div với text "Viết bình luận" hoặc "Write a comment"
                var spans = document.querySelectorAll('span');
                for (var i = 0; i < spans.length; i++) {
                    var text = (spans[i].innerText || '').toLowerCase();
                    if (text.includes('viết bình luận') || text.includes('write a comment')) {
                        var parent = spans[i].closest('[role="button"]') || spans[i].parentElement;
                        if (parent) {
                            parent.click();
                            return 'clicked_comment_placeholder';
                        }
                    }
                }

                return 'no_comment_box_found';
            })();
            '''
            click_result = self._cdp_evaluate(ws, js_click_comment_box)
            print(f"[ReelsPage] Click comment box: {click_result}")
            time.sleep(2)

            # Gõ comment từng ký tự như người thật
            print(f"[ReelsPage] Typing comment human-like ({len(comment_text)} chars)...")
            self._cdp_type_human_like(ws, comment_text, typo_chance=0.03)
            time.sleep(1)

            # Click nút gửi comment
            js_submit_comment = '''
            (function() {
                // Tìm nút gửi (Enter hoặc nút Submit)
                // Phương pháp 1: Tìm nút có icon gửi
                var submitBtns = document.querySelectorAll(
                    '[aria-label*="send" i], [aria-label*="gửi" i], ' +
                    '[aria-label*="submit" i], [aria-label*="đăng" i]'
                );

                for (var i = 0; i < submitBtns.length; i++) {
                    var btn = submitBtns[i];
                    if (btn.offsetParent !== null) {
                        btn.click();
                        return 'clicked_submit';
                    }
                }

                // Phương pháp 2: Simulate Enter key
                var active = document.activeElement;
                if (active) {
                    active.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true}));
                    return 'sent_enter';
                }

                return 'no_submit_found';
            })();
            '''
            submit_result = self._cdp_evaluate(ws, js_submit_comment)
            print(f"[ReelsPage] Submit comment: {submit_result}")
            time.sleep(3)

            print(f"[ReelsPage] SUCCESS - Comment đã được gửi!")

        except Exception as e:
            print(f"[ReelsPage] ERROR commenting: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if ws:
                try:
                    ws.close()
                except:
                    pass
            release_window_slot(slot_id)

    # ========== HELPERS ==========

    def _set_status(self, text: str, status_type: str = "info"):
        """Cập nhật status"""
        if self.status_callback:
            self.status_callback(text, status_type)


class CommentDialog(ctk.CTkToplevel):
    """Dialog để nhập comment cho Reel"""

    def __init__(self, parent, reel: Dict, callback):
        super().__init__(parent)

        self.reel = reel
        self.callback = callback

        self.title("💬 Comment vào Reel")
        self.geometry("500x400")
        self.configure(fg_color=COLORS["bg_dark"])
        self.transient(parent)

        self._create_ui()
        self._load_contents()

    def _create_ui(self):
        """Tạo giao diện"""
        # Header
        ctk.CTkLabel(
            self,
            text="💬 Comment vào Reel",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(pady=(20, 10))

        # Reel info
        reel_url = self.reel.get('reel_url', '')
        if reel_url:
            url_display = reel_url[:60] + "..." if len(reel_url) > 60 else reel_url
            ctk.CTkLabel(
                self,
                text=url_display,
                font=ctk.CTkFont(size=11),
                text_color=COLORS["accent"]
            ).pack()

        # Content selector
        content_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=10)
        content_frame.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(
            content_frame,
            text="📝 Chọn từ Soạn tin:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=15, pady=(10, 5))

        self.content_var = ctk.StringVar(value="-- Chọn nội dung --")
        self.content_menu = ctk.CTkOptionMenu(
            content_frame,
            variable=self.content_var,
            values=["-- Chọn nội dung --"],
            fg_color=COLORS["bg_card"],
            button_color=COLORS["accent"],
            width=400,
            command=self._on_content_select
        )
        self.content_menu.pack(padx=15, pady=(0, 10))

        # Comment text
        ctk.CTkLabel(
            self,
            text="Nội dung comment:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=20, pady=(10, 5))

        self.comment_text = ctk.CTkTextbox(
            self,
            fg_color=COLORS["bg_card"],
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont(size=12),
            height=100,
            corner_radius=8
        )
        self.comment_text.pack(fill="x", padx=20, pady=(0, 15))

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)

        ModernButton(
            btn_frame,
            text="💬 Gửi Comment",
            variant="primary",
            command=self._submit,
            width=150
        ).pack(side="left", padx=5)

        ModernButton(
            btn_frame,
            text="Đóng",
            variant="secondary",
            command=self.destroy,
            width=100
        ).pack(side="left", padx=5)

    def _load_contents(self):
        """Load nội dung từ Soạn tin"""
        from db import get_contents
        contents = get_contents()

        self.contents_map = {}
        values = ["-- Chọn nội dung --"]

        for content in contents:
            title = content.get('title', 'Untitled')
            content_id = content.get('id')
            display = f"{title[:40]}..." if len(title) > 40 else title
            values.append(display)
            self.contents_map[display] = content

        self.content_menu.configure(values=values)

    def _on_content_select(self, selection):
        """Khi chọn nội dung từ Soạn tin"""
        if selection in self.contents_map:
            content = self.contents_map[selection]
            text = content.get('content', '')
            self.comment_text.delete("1.0", "end")
            self.comment_text.insert("1.0", text)

    def _submit(self):
        """Gửi comment"""
        comment = self.comment_text.get("1.0", "end").strip()
        if comment:
            self.callback(self.reel, comment)
            self.destroy()


class ScheduleDialog(ctk.CTkToplevel):
    """Dialog lên lịch đăng Reels"""

    def __init__(self, parent, callback):
        super().__init__(parent)

        self.callback = callback

        self.title("📅 Lên lịch đăng Reels")
        self.geometry("400x300")
        self.configure(fg_color=COLORS["bg_dark"])
        self.transient(parent)

        self._create_ui()

    def _create_ui(self):
        """Tạo giao diện"""
        ctk.CTkLabel(
            self,
            text="📅 Chọn thời gian đăng",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(pady=20)

        # Date selection
        date_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=10)
        date_frame.pack(fill="x", padx=30, pady=10)

        ctk.CTkLabel(
            date_frame,
            text="Ngày:",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=15, pady=(10, 5))

        date_input = ctk.CTkFrame(date_frame, fg_color="transparent")
        date_input.pack(fill="x", padx=15, pady=(0, 10))

        now = datetime.now()

        self.day_entry = ModernEntry(date_input, width=60, placeholder="DD")
        self.day_entry.pack(side="left")
        self.day_entry.insert(0, str(now.day))

        ctk.CTkLabel(date_input, text="/", text_color=COLORS["text_secondary"]).pack(side="left", padx=5)

        self.month_entry = ModernEntry(date_input, width=60, placeholder="MM")
        self.month_entry.pack(side="left")
        self.month_entry.insert(0, str(now.month))

        ctk.CTkLabel(date_input, text="/", text_color=COLORS["text_secondary"]).pack(side="left", padx=5)

        self.year_entry = ModernEntry(date_input, width=80, placeholder="YYYY")
        self.year_entry.pack(side="left")
        self.year_entry.insert(0, str(now.year))

        # Time selection
        time_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=10)
        time_frame.pack(fill="x", padx=30, pady=10)

        ctk.CTkLabel(
            time_frame,
            text="Giờ:",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=15, pady=(10, 5))

        time_input = ctk.CTkFrame(time_frame, fg_color="transparent")
        time_input.pack(fill="x", padx=15, pady=(0, 10))

        self.hour_entry = ModernEntry(time_input, width=60, placeholder="HH")
        self.hour_entry.pack(side="left")
        self.hour_entry.insert(0, str(now.hour))

        ctk.CTkLabel(time_input, text=":", text_color=COLORS["text_secondary"]).pack(side="left", padx=5)

        self.minute_entry = ModernEntry(time_input, width=60, placeholder="MM")
        self.minute_entry.pack(side="left")
        self.minute_entry.insert(0, str(now.minute))

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=20)

        ModernButton(
            btn_frame,
            text="Xác nhận",
            icon="✅",
            variant="primary",
            command=self._confirm,
            width=120
        ).pack(side="left", padx=5)

        ModernButton(
            btn_frame,
            text="Hủy",
            icon="❌",
            variant="secondary",
            command=self.destroy,
            width=100
        ).pack(side="left", padx=5)

    def _confirm(self):
        """Xác nhận lên lịch"""
        try:
            day = int(self.day_entry.get())
            month = int(self.month_entry.get())
            year = int(self.year_entry.get())
            hour = int(self.hour_entry.get())
            minute = int(self.minute_entry.get())

            schedule_time = datetime(year, month, day, hour, minute)

            if schedule_time < datetime.now():
                # Show error
                return

            self.callback(schedule_time)
            self.destroy()

        except ValueError:
            pass
