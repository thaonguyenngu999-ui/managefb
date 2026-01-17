"""
Tab Đăng Reels Page - Lên kế hoạch và đăng Reels cho các Facebook Pages
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

try:
    import websocket
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False


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

    def _post_reel_to_page(self, page: Dict, caption: str, hashtags: str):
        """Đăng Reels lên một Page qua CDP"""
        if not WEBSOCKET_AVAILABLE:
            raise Exception("websocket-client chưa được cài đặt")

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
        ws = None

        try:
            # Bước 1: Mở browser với profile
            result = api.open_browser(profile_uuid)
            # API trả về status: 'successfully' thay vì success: True
            if not result or result.get('status') != 'successfully':
                raise Exception(f"Không mở được browser: {result}")

            browser_info = result.get('data', {})
            # API trả về remote_port, không phải remote_debugging_port
            remote_port = browser_info.get('remote_port') or browser_info.get('remote_debugging_port')

            if not remote_port:
                raise Exception("Không lấy được remote debugging port")

            print(f"[ReelsPage] Browser opened, port: {remote_port}")
            time.sleep(3)

            # Lưu bounds để set sau khi kết nối CDP
            bounds = get_window_bounds(slot_id)

            # Bước 2: Kết nối CDP
            cdp_base = f"http://127.0.0.1:{remote_port}"
            import urllib.request
            tabs_url = f"{cdp_base}/json"

            for attempt in range(5):
                try:
                    with urllib.request.urlopen(tabs_url, timeout=10) as resp:
                        tabs = json_module.loads(resp.read().decode())
                        break
                except Exception as e:
                    print(f"[ReelsPage] CDP retry {attempt + 1}: {e}")
                    time.sleep(2)
            else:
                raise Exception("Không kết nối được CDP")

            # Tìm tab Facebook
            page_ws = None
            for tab in tabs:
                if tab.get('type') == 'page':
                    ws_url = tab.get('webSocketDebuggerUrl', '')
                    if ws_url:
                        page_ws = ws_url
                        break

            if not page_ws:
                raise Exception("Không tìm thấy tab Facebook")

            # Kết nối WebSocket
            try:
                ws = websocket.create_connection(page_ws, timeout=30, suppress_origin=True)
            except:
                try:
                    ws = websocket.create_connection(page_ws, timeout=30, origin=f"http://127.0.0.1:{remote_port}")
                except:
                    ws = websocket.create_connection(page_ws, timeout=30)

            # Set window position via CDP
            # bounds là tuple (x, y, width, height)
            try:
                window_result = self._cdp_send(ws, "Browser.getWindowForTarget", {})
                window_id = window_result.get('result', {}).get('windowId')
                if window_id and bounds:
                    x, y, w, h = bounds  # Unpack tuple
                    self._cdp_send(ws, "Browser.setWindowBounds", {
                        "windowId": window_id,
                        "bounds": {
                            "left": x,
                            "top": y,
                            "width": w,
                            "height": h,
                            "windowState": "normal"
                        }
                    })
                    print(f"[ReelsPage] Window positioned at ({x}, {y})")
            except Exception as e:
                print(f"[ReelsPage] Could not set window bounds: {e}")

            # Bước 3: Navigate đến page để switch context
            print(f"[ReelsPage] Navigating to page: {page_url}")
            self._cdp_send(ws, "Page.navigate", {"url": page_url})
            time.sleep(5)

            # Đợi page load
            for _ in range(10):
                ready = self._cdp_evaluate(ws, "document.readyState")
                if ready == 'complete':
                    break
                time.sleep(1)

            time.sleep(3)

            # Bước 4: Click "Chuyển ngay" để switch sang Page context
            print(f"[ReelsPage] Looking for 'Chuyển ngay' button...")
            js_click_switch = '''
            (function() {
                // Tìm nút "Chuyển ngay" để switch sang page
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
            switch_result = self._cdp_evaluate(ws, js_click_switch)
            print(f"[ReelsPage] Switch result: {switch_result}")

            if 'no_switch_button_found' in str(switch_result):
                print(f"[ReelsPage] No switch button found, may already be in page context")
            else:
                time.sleep(3)  # Đợi switch xong

            # Bước 5: Navigate trực tiếp đến Reels creator page
            # (Click vào "Thước phim" trên timeline không mở đúng creator)
            reels_create_url = "https://www.facebook.com/reels/create"
            print(f"[ReelsPage] Navigating directly to Reels creator: {reels_create_url}")
            self._cdp_send(ws, "Page.navigate", {"url": reels_create_url})
            time.sleep(8)

            # Đợi page load hoàn toàn
            for _ in range(15):
                ready = self._cdp_evaluate(ws, "document.readyState")
                if ready == 'complete':
                    break
                time.sleep(1)

            time.sleep(3)

            # Check current URL
            current_url = self._cdp_evaluate(ws, "window.location.href")
            print(f"[ReelsPage] Current URL: {current_url}")

            # Bước 6: Upload video
            print(f"[ReelsPage] Preparing to upload video...")

            # Normalize path cho Windows
            video_path = self.video_path.replace('\\', '/')

            # Debug: liệt kê tất cả input[type="file"] trên page
            js_debug_inputs = '''
            (function() {
                var inputs = document.querySelectorAll('input[type="file"]');
                var info = [];
                for (var i = 0; i < inputs.length; i++) {
                    var inp = inputs[i];
                    info.push({
                        accept: inp.getAttribute('accept') || 'none',
                        className: inp.className,
                        id: inp.id || 'no-id',
                        visible: inp.offsetParent !== null
                    });
                }
                return JSON.stringify(info);
            })();
            '''
            inputs_debug = self._cdp_evaluate(ws, js_debug_inputs)
            print(f"[ReelsPage] DEBUG - Found file inputs: {inputs_debug}")

            # Click vào vùng upload nếu cần (để trigger file input xuất hiện)
            js_click_upload_area = '''
            (function() {
                // Tìm vùng upload trong Reels creator dialog
                var uploadSelectors = [
                    '[aria-label*="video"]',
                    '[aria-label*="Video"]',
                    '[aria-label*="Tải"]',
                    '[aria-label*="Upload"]',
                    '[aria-label*="Thêm video"]',
                    '[aria-label*="Add video"]',
                    'div[role="button"]:has(input[type="file"])',
                    '.x1i10hfl input[type="file"]'
                ];

                for (var i = 0; i < uploadSelectors.length; i++) {
                    try {
                        var el = document.querySelector(uploadSelectors[i]);
                        if (el) {
                            // Nếu là parent của input, click vào nó
                            var btn = el.closest('[role="button"]') || el;
                            if (btn && btn.click) {
                                btn.click();
                                return 'clicked_upload_area: ' + uploadSelectors[i];
                            }
                        }
                    } catch(e) {}
                }

                return 'no_upload_area_clicked';
            })();
            '''
            upload_area_result = self._cdp_evaluate(ws, js_click_upload_area)
            print(f"[ReelsPage] Upload area click: {upload_area_result}")
            time.sleep(2)

            # Lấy DOM document
            doc_result = self._cdp_send(ws, "DOM.getDocument", {})
            root_id = doc_result.get('result', {}).get('root', {}).get('nodeId', 0)

            if not root_id:
                raise Exception("Không lấy được DOM root")

            # Tìm input[type="file"] cho video - thử nhiều selector
            selectors_to_try = [
                'input[type="file"][accept*="video"]',
                'input[type="file"][accept*="mp4"]',
                'input[type="file"][accept*=".mkv"]',
                'input[type="file"]'
            ]

            node_ids = []
            for selector in selectors_to_try:
                query_result = self._cdp_send(ws, "DOM.querySelectorAll", {
                    "nodeId": root_id,
                    "selector": selector
                })
                node_ids = query_result.get('result', {}).get('nodeIds', [])
                if node_ids:
                    print(f"[ReelsPage] Found {len(node_ids)} inputs with selector: {selector}")
                    break

            if not node_ids:
                # Thử JavaScript để tìm input
                js_find_input = '''
                (function() {
                    var inputs = document.querySelectorAll('input[type="file"]');
                    if (inputs.length > 0) {
                        return inputs.length + ' inputs found via JS';
                    }
                    return 'no inputs found';
                })();
                '''
                js_result = self._cdp_evaluate(ws, js_find_input)
                print(f"[ReelsPage] JS input search: {js_result}")
                raise Exception(f"Không tìm thấy input file để upload video. Debug: {inputs_debug}")

            # Set file cho input đầu tiên
            uploaded = False
            for node_id in node_ids:
                try:
                    self._cdp_send(ws, "DOM.setFileInputFiles", {
                        "nodeId": node_id,
                        "files": [video_path]
                    })
                    print(f"[ReelsPage] Video set to input nodeId: {node_id}")
                    uploaded = True
                    break
                except Exception as e:
                    print(f"[ReelsPage] Upload error for nodeId {node_id}: {e}")
                    continue

            if not uploaded:
                raise Exception("Không upload được video")

            # Đợi video được xử lý và kiểm tra bản quyền
            print(f"[ReelsPage] Waiting for video processing & copyright check...")
            time.sleep(15)  # Đợi lâu hơn cho copyright check

            # Bước 7: Click nút "Tiếp" (Next/Continue) sau khi copyright check xong
            print(f"[ReelsPage] Looking for 'Tiếp' (Next) button...")
            js_click_next = '''
            (function() {
                // Button "Tiếp" có role="none", không phải role="button"
                // Tìm tất cả span chứa text "Tiếp"
                var spans = document.querySelectorAll('span');
                for (var i = 0; i < spans.length; i++) {
                    var span = spans[i];
                    var text = (span.innerText || '').trim();

                    if (text === 'Tiếp' || text === 'Next' || text === 'Tiếp tục') {
                        // Tìm parent div có thể click (thường là div[role="none"] hoặc div gần nhất)
                        var clickable = span.closest('div.x1ja2u2z') ||
                                       span.closest('div[role="none"]') ||
                                       span.closest('div[role="button"]') ||
                                       span.parentElement.parentElement.parentElement;
                        if (clickable && clickable.offsetParent !== null) {
                            clickable.click();
                            return 'clicked_next_span: ' + text;
                        }
                    }
                }

                // Fallback: tìm theo innerText của bất kỳ div nào
                var divs = document.querySelectorAll('div');
                for (var i = 0; i < divs.length; i++) {
                    var div = divs[i];
                    var text = (div.innerText || '').trim();
                    if (text === 'Tiếp' || text === 'Next') {
                        if (div.offsetParent !== null) {
                            div.click();
                            return 'clicked_next_div: ' + text;
                        }
                    }
                }
                return 'no_next_button_found';
            })();
            '''
            next_result = self._cdp_evaluate(ws, js_click_next)
            print(f"[ReelsPage] First 'Tiếp' button result: {next_result}")

            if 'no_next_button_found' in str(next_result):
                print(f"[ReelsPage] No first 'Tiếp' button found")
            else:
                time.sleep(5)  # Đợi chuyển sang trang chỉnh sửa

            # Bước 7b: Click nút "Tiếp" lần 2 (sau khi chỉnh sửa)
            print(f"[ReelsPage] Looking for second 'Tiếp' button (after edit)...")
            next_result2 = self._cdp_evaluate(ws, js_click_next)
            print(f"[ReelsPage] Second 'Tiếp' button result: {next_result2}")

            if 'no_next_button_found' in str(next_result2):
                print(f"[ReelsPage] No second 'Tiếp' button found, maybe already on description page")
            else:
                time.sleep(5)  # Đợi chuyển sang trang mô tả

            # Bước 8: Nhập caption và hashtags (Mô tả thước phim)
            full_caption = f"{caption}\n\n{hashtags}" if hashtags else caption

            if full_caption:
                print(f"[ReelsPage] Adding caption...")

                # Tìm và điền caption
                js_fill_caption = f'''
                (function() {{
                    var captionText = `{full_caption.replace('`', '\\`')}`;

                    // Tìm textarea hoặc contenteditable cho caption
                    var editors = document.querySelectorAll('[contenteditable="true"], textarea');
                    for (var i = 0; i < editors.length; i++) {{
                        var ed = editors[i];
                        var ariaLabel = (ed.getAttribute('aria-label') || '').toLowerCase();
                        var placeholder = (ed.getAttribute('placeholder') || '').toLowerCase();

                        // Tìm field liên quan đến mô tả/caption
                        if (ariaLabel.includes('mô tả') || ariaLabel.includes('describe') ||
                            ariaLabel.includes('caption') || placeholder.includes('mô tả') ||
                            placeholder.includes('describe')) {{
                            ed.focus();
                            if (ed.tagName === 'TEXTAREA') {{
                                var setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
                                setter.call(ed, captionText);
                            }} else {{
                                ed.innerText = captionText;
                            }}
                            ed.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            ed.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            return 'caption_filled: ' + ariaLabel;
                        }}
                    }}

                    // Fallback: dùng contenteditable đầu tiên
                    var fallback = document.querySelector('[contenteditable="true"]');
                    if (fallback) {{
                        fallback.focus();
                        fallback.innerText = captionText;
                        fallback.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        return 'caption_fallback';
                    }}

                    return 'no_caption_field_found';
                }})();
                '''
                caption_result = self._cdp_evaluate(ws, js_fill_caption)
                print(f"[ReelsPage] Caption result: {caption_result}")
                time.sleep(2)

            # Bước 9: Click nút đăng/share
            print(f"[ReelsPage] Looking for 'Đăng' (Post) button...")

            js_click_post = '''
            (function() {
                // Button "Đăng" cũng có thể có role="none"
                // Tìm span chứa text "Đăng" trước
                var spans = document.querySelectorAll('span');
                for (var i = 0; i < spans.length; i++) {
                    var span = spans[i];
                    var text = (span.innerText || '').trim();

                    if (text === 'Đăng' || text === 'Share' || text === 'Post' ||
                        text === 'Chia sẻ' || text === 'Share Reel' || text === 'Chia sẻ Reel' ||
                        text === 'Đăng thước phim' || text === 'Share reel') {
                        var clickable = span.closest('div.x1ja2u2z') ||
                                       span.closest('div[role="none"]') ||
                                       span.closest('div[role="button"]') ||
                                       span.parentElement.parentElement.parentElement;
                        if (clickable && clickable.offsetParent !== null) {
                            clickable.click();
                            return 'clicked_post_span: ' + text;
                        }
                    }
                }

                // Fallback: tìm div với innerText
                var divs = document.querySelectorAll('div');
                for (var i = 0; i < divs.length; i++) {
                    var div = divs[i];
                    var text = (div.innerText || '').trim();
                    if (text === 'Đăng' || text === 'Share' || text === 'Post') {
                        if (div.offsetParent !== null) {
                            div.click();
                            return 'clicked_post_div: ' + text;
                        }
                    }
                }

                return 'no_post_button_found';
            })();
            '''
            click_result = self._cdp_evaluate(ws, js_click_post)
            print(f"[ReelsPage] Click post result: {click_result}")

            if 'no_post_button_found' in str(click_result):
                raise Exception("Không tìm thấy nút đăng")

            # Đợi đăng xong và lấy link Reel
            print(f"[ReelsPage] Waiting for Reel to be posted...")
            time.sleep(15)  # Đợi lâu hơn để đăng xong

            # Bước 10: Lấy link Reel đã đăng
            reel_url = None
            js_get_reel_url = '''
            (function() {
                // Cách 1: Check URL hiện tại nếu đã redirect đến Reel
                var currentUrl = window.location.href;
                if (currentUrl.includes('/reel/') || currentUrl.includes('/reels/')) {
                    return currentUrl;
                }

                // Cách 2: Tìm trong page có link đến Reel vừa tạo
                var links = document.querySelectorAll('a[href*="/reel/"], a[href*="/reels/"]');
                for (var i = links.length - 1; i >= 0; i--) {
                    var href = links[i].href;
                    if (href.includes('/reel/') && href.match(/\\/reel\\/\\d+/)) {
                        return href;
                    }
                }

                // Cách 3: Tìm trong notification/success message
                var successMsgs = document.querySelectorAll('[role="dialog"] a, [role="alert"] a');
                for (var i = 0; i < successMsgs.length; i++) {
                    var href = successMsgs[i].href || '';
                    if (href.includes('/reel/')) {
                        return href;
                    }
                }

                // Cách 4: Check body có chứa reel ID pattern không
                var bodyText = document.body.innerHTML;
                var match = bodyText.match(/\\/reel\\/(\\d+)/);
                if (match) {
                    return 'https://www.facebook.com/reel/' + match[1];
                }

                return 'no_reel_url_found';
            })();
            '''

            # Thử lấy URL nhiều lần
            for attempt in range(5):
                reel_url = self._cdp_evaluate(ws, js_get_reel_url)
                print(f"[ReelsPage] Attempt {attempt + 1} - Reel URL: {reel_url}")

                if reel_url and 'no_reel_url_found' not in str(reel_url) and '/reel/' in str(reel_url):
                    break
                time.sleep(3)

            # Lưu vào database
            final_reel_url = reel_url if (reel_url and 'no_reel_url_found' not in str(reel_url)) else None

            posted_data = {
                'profile_uuid': profile_uuid,
                'page_id': page_id,
                'page_name': page_name,
                'reel_url': final_reel_url or '',
                'caption': caption,
                'hashtags': hashtags,
                'video_path': self.video_path,
                'status': 'success'
            }
            save_posted_reel(posted_data)

            if final_reel_url:
                print(f"[ReelsPage] SUCCESS - Đã đăng Reels lên {page_name}")
                print(f"[ReelsPage] REEL URL: {final_reel_url}")
                return final_reel_url
            else:
                print(f"[ReelsPage] SUCCESS - Đã đăng Reels lên {page_name} (không lấy được link)")
                return None

        except Exception as e:
            print(f"[ReelsPage] ERROR: {e}")
            import traceback
            traceback.print_exc()

            # Lưu lỗi vào database
            error_data = {
                'profile_uuid': profile_uuid,
                'page_id': page_id,
                'page_name': page_name,
                'reel_url': '',
                'caption': caption,
                'hashtags': hashtags,
                'video_path': self.video_path if hasattr(self, 'video_path') else '',
                'status': 'failed',
                'error_message': str(e)
            }
            try:
                save_posted_reel(error_data)
            except:
                pass

            raise e
        finally:
            if ws:
                try:
                    ws.close()
                except:
                    pass
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
        """Load lịch sử đăng"""
        # TODO: Implement history loading
        pass

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

    # ========== HELPERS ==========

    def _set_status(self, text: str, status_type: str = "info"):
        """Cập nhật status"""
        if self.status_callback:
            self.status_callback(text, status_type)


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
