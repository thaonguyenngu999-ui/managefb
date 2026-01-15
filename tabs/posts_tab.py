"""
Tab Bài đăng - Quản lý các bài đăng và tăng tương tác (Like)
"""
import customtkinter as ctk
from typing import List, Dict, Optional
import threading
import random
import time
import re
import requests
from datetime import datetime, date, timedelta
from config import COLORS
from widgets import ModernButton, ModernEntry
from db import get_post_history
from api_service import api


class PostsTab(ctk.CTkFrame):
    """Tab quản lý bài đăng và tăng like"""

    def __init__(self, master, status_callback=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.status_callback = status_callback
        self.posts: List[Dict] = []
        self.profiles: List[Dict] = []
        self.folders: List[Dict] = []
        self._is_running = False
        self._stop_requested = False

        # Store post status
        self.post_vars = {}  # {post_id: BooleanVar}
        self.post_widgets = {}  # {post_id: widget dict}
        self.post_status = {}  # {post_id: {target, liked, completed, error}}

        self._create_ui()
        self._load_data()

    def _create_ui(self):
        """Tạo giao diện"""
        # ========== HEADER ==========
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 15))

        ctk.CTkLabel(
            header_frame,
            text="📰 Quản lý Bài đăng",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left")

        ModernButton(
            header_frame,
            text="Làm mới",
            icon="🔄",
            variant="secondary",
            command=self._load_data,
            width=120
        ).pack(side="right", padx=5)

        # ========== SETTINGS SECTION ==========
        settings_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=15)
        settings_frame.pack(fill="x", padx=20, pady=(0, 15))

        # Row 1: Date filter
        row1 = ctk.CTkFrame(settings_frame, fg_color="transparent")
        row1.pack(fill="x", padx=20, pady=(15, 8))

        ctk.CTkLabel(
            row1,
            text="📅 Lọc theo ngày:",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_primary"]
        ).pack(side="left")

        self.date_filter_var = ctk.StringVar(value="Hôm nay")
        self.date_filter_menu = ctk.CTkOptionMenu(
            row1,
            variable=self.date_filter_var,
            values=["Hôm nay", "Hôm qua", "7 ngày", "30 ngày", "Tất cả"],
            fg_color=COLORS["bg_card"],
            button_color=COLORS["accent"],
            width=120,
            command=self._on_date_filter_change
        )
        self.date_filter_menu.pack(side="left", padx=10)

        ctk.CTkLabel(row1, text="hoặc chọn ngày:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(15, 5))
        self.custom_date_entry = ModernEntry(row1, placeholder="dd/mm/yyyy", width=100)
        self.custom_date_entry.pack(side="left")

        ModernButton(
            row1,
            text="Lọc",
            variant="secondary",
            command=self._filter_by_custom_date,
            width=60
        ).pack(side="left", padx=5)

        self.post_count_label = ctk.CTkLabel(
            row1,
            text="0 bài",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["accent"]
        )
        self.post_count_label.pack(side="right")

        # Row 2: Profile folder & Thread count & Like count
        row2 = ctk.CTkFrame(settings_frame, fg_color="transparent")
        row2.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkLabel(
            row2,
            text="📁 Thư mục profile:",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_primary"]
        ).pack(side="left")

        self.folder_var = ctk.StringVar(value="-- Tất cả --")
        self.folder_menu = ctk.CTkOptionMenu(
            row2,
            variable=self.folder_var,
            values=["-- Tất cả --"],
            fg_color=COLORS["bg_card"],
            button_color=COLORS["accent"],
            width=180,
            command=self._on_folder_change
        )
        self.folder_menu.pack(side="left", padx=10)

        ctk.CTkLabel(row2, text="Số luồng:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(20, 5))
        self.thread_count_entry = ModernEntry(row2, placeholder="3", width=50)
        self.thread_count_entry.pack(side="left")
        self.thread_count_entry.insert(0, "3")

        ctk.CTkLabel(row2, text="Số like/bài:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(20, 5))
        self.like_count_entry = ModernEntry(row2, placeholder="5", width=50)
        self.like_count_entry.pack(side="left")
        self.like_count_entry.insert(0, "5")

        self.profile_count_label = ctk.CTkLabel(
            row2,
            text="0 profiles",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        )
        self.profile_count_label.pack(side="right")

        # ========== POST LIST SECTION ==========
        list_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=15)
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        # List header with select all
        list_header = ctk.CTkFrame(list_frame, fg_color="transparent")
        list_header.pack(fill="x", padx=15, pady=(15, 10))

        self.select_all_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            list_header,
            text="Chọn tất cả",
            variable=self.select_all_var,
            fg_color=COLORS["accent"],
            command=self._toggle_select_all
        ).pack(side="left")

        ctk.CTkLabel(
            list_header,
            text="📋 Danh sách bài đăng",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left", padx=20)

        # Table header
        table_header = ctk.CTkFrame(list_frame, fg_color=COLORS["bg_card"], corner_radius=8, height=35)
        table_header.pack(fill="x", padx=15, pady=(0, 5))
        table_header.pack_propagate(False)

        headers = [("", 35), ("Link bài viết", 300), ("Mục tiêu", 60), ("Đã like", 60), ("Trạng thái", 110), ("Lỗi", 40)]
        for text, width in headers:
            ctk.CTkLabel(
                table_header,
                text=text,
                width=width,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=COLORS["text_primary"]
            ).pack(side="left", padx=3)

        # Scrollable post list
        self.post_list_scroll = ctk.CTkScrollableFrame(list_frame, fg_color="transparent")
        self.post_list_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.empty_label = ctk.CTkLabel(
            self.post_list_scroll,
            text="📭 Chưa có bài đăng nào\nĐăng bài ở tab 'Đăng Nhóm' trước",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text_secondary"],
            justify="center"
        )
        self.empty_label.pack(pady=50)

        # ========== ACTION SECTION ==========
        action_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=15)
        action_frame.pack(fill="x", padx=20, pady=(0, 20))

        # Buttons row
        btn_row = ctk.CTkFrame(action_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=15)

        ModernButton(
            btn_row,
            text="Bắt đầu Like",
            icon="👍",
            variant="success",
            command=self._start_liking,
            width=140
        ).pack(side="left", padx=5)

        ModernButton(
            btn_row,
            text="Dừng",
            icon="⏹️",
            variant="danger",
            command=self._stop_liking,
            width=80
        ).pack(side="left", padx=5)

        # Progress
        self.progress_bar = ctk.CTkProgressBar(
            btn_row,
            fg_color=COLORS["bg_card"],
            progress_color=COLORS["success"],
            width=200
        )
        self.progress_bar.pack(side="left", padx=20)
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(
            btn_row,
            text="Sẵn sàng",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        )
        self.status_label.pack(side="left", padx=10)

        # Log
        self.log_textbox = ctk.CTkTextbox(
            action_frame,
            fg_color=COLORS["bg_card"],
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont(size=11),
            height=100
        )
        self.log_textbox.pack(fill="x", padx=20, pady=(0, 15))
        self.log_textbox.configure(state="disabled")

    def _load_data(self):
        """Load posts và profiles"""
        self._load_folders()
        self._load_profiles()
        self._load_posts()

    def _load_folders(self):
        """Load danh sách folders từ Hidemium"""
        try:
            self.folders = api.get_folders()
            print(f"[DEBUG PostsTab] _load_folders got {len(self.folders)} folders")
        except Exception as e:
            print(f"[DEBUG PostsTab] _load_folders error: {e}")
            self.folders = []

        folder_options = ["-- Tất cả --"]
        for f in self.folders:
            name = f.get('name', 'Unknown')
            folder_options.append(name)
            print(f"[DEBUG PostsTab] Added folder: {name}")
        print(f"[DEBUG PostsTab] folder_options: {folder_options}")
        self.folder_menu.configure(values=folder_options)

    def _load_profiles(self):
        """Load profiles từ Hidemium API"""
        folder_name = self.folder_var.get()
        print(f"[DEBUG] _load_profiles called, folder: {folder_name}")

        try:
            if folder_name == "-- Tất cả --":
                # Load tất cả profiles từ API
                self.profiles = api.get_profiles(limit=500)
            else:
                # Tìm folder_id (API cần numeric id, không phải uuid)
                folder_id = None
                for f in self.folders:
                    if f.get('name') == folder_name:
                        folder_id = f.get('id')  # Dùng numeric id
                        print(f"[DEBUG] Found folder {folder_name} with id={folder_id}")
                        break
                if folder_id:
                    self.profiles = api.get_profiles(folder_id=[folder_id], limit=500)
                else:
                    self.profiles = api.get_profiles(limit=500)

            # Debug: in ra profiles
            print(f"[DEBUG] Loaded {len(self.profiles)} profiles")
            if self.profiles and len(self.profiles) > 0:
                print(f"[DEBUG] First profile type: {type(self.profiles[0])}")
                print(f"[DEBUG] First profile: {self.profiles[0]}")
                if len(self.profiles) > 1:
                    print(f"[DEBUG] Second profile: {self.profiles[1]}")
        except Exception as e:
            print(f"[ERROR] Load profiles: {e}")
            import traceback
            traceback.print_exc()
            self.profiles = []

        self.profile_count_label.configure(text=f"{len(self.profiles)} profiles")

    def _load_posts(self):
        """Load danh sách bài đăng theo filter"""
        filter_value = self.date_filter_var.get()
        today = date.today()

        if filter_value == "Hôm nay":
            start_date = today
        elif filter_value == "Hôm qua":
            start_date = today - timedelta(days=1)
        elif filter_value == "7 ngày":
            start_date = today - timedelta(days=7)
        elif filter_value == "30 ngày":
            start_date = today - timedelta(days=30)
        else:
            start_date = None

        # Get posts from history (tăng limit để lấy nhiều hơn)
        all_posts = get_post_history(limit=1000)

        if start_date:
            self.posts = []
            for p in all_posts:
                post_date_str = p.get('created_at', '')
                if post_date_str:
                    try:
                        post_date = datetime.strptime(post_date_str[:10], '%Y-%m-%d').date()
                        if filter_value == "Hôm qua":
                            # Chỉ lấy đúng ngày hôm qua
                            if post_date == start_date:
                                self.posts.append(p)
                        else:
                            # Lấy từ ngày start_date trở đi
                            if post_date >= start_date:
                                self.posts.append(p)
                    except:
                        pass
        else:
            self.posts = all_posts

        self.post_count_label.configure(text=f"{len(self.posts)} bài")
        self._render_post_list()

    def _filter_by_custom_date(self):
        """Lọc theo ngày nhập vào"""
        date_str = self.custom_date_entry.get().strip()
        if not date_str:
            return

        try:
            # Parse dd/mm/yyyy
            custom_date = datetime.strptime(date_str, '%d/%m/%Y').date()
        except:
            self._log("Định dạng ngày không hợp lệ (dd/mm/yyyy)")
            return

        all_posts = get_post_history(limit=1000)
        self.posts = []

        for p in all_posts:
            post_date_str = p.get('created_at', '')
            if post_date_str:
                try:
                    post_date = datetime.strptime(post_date_str[:10], '%Y-%m-%d').date()
                    if post_date == custom_date:
                        self.posts.append(p)
                except:
                    pass

        self.post_count_label.configure(text=f"{len(self.posts)} bài")
        self._render_post_list()

    def _render_post_list(self):
        """Render danh sách bài đăng"""
        # Clear existing
        for widget in self.post_list_scroll.winfo_children():
            widget.destroy()

        self.post_vars = {}
        self.post_widgets = {}

        if not self.posts:
            self.empty_label = ctk.CTkLabel(
                self.post_list_scroll,
                text="📭 Chưa có bài đăng nào\nĐăng bài ở tab 'Đăng Nhóm' trước",
                font=ctk.CTkFont(size=14),
                text_color=COLORS["text_secondary"],
                justify="center"
            )
            self.empty_label.pack(pady=50)
            return

        target_likes = int(self.like_count_entry.get() or 5)

        for i, post in enumerate(self.posts):
            post_id = post.get('id', i)
            post_url = post.get('post_url', '')

            # Initialize status if not exists
            if post_id not in self.post_status:
                self.post_status[post_id] = {
                    'target': target_likes,
                    'liked': 0,
                    'completed': False,
                    'error': False
                }

            row = ctk.CTkFrame(self.post_list_scroll, fg_color=COLORS["bg_card"], corner_radius=8, height=40)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)

            # Checkbox
            var = ctk.BooleanVar(value=False)
            self.post_vars[post_id] = var
            cb = ctk.CTkCheckBox(
                row,
                text="",
                variable=var,
                fg_color=COLORS["accent"],
                width=35
            )
            cb.pack(side="left", padx=5)

            # Link (clickable)
            link_label = ctk.CTkLabel(
                row,
                text=post_url[:50] + "..." if len(post_url) > 50 else post_url,
                width=300,
                font=ctk.CTkFont(size=11),
                text_color=COLORS["accent"],
                cursor="hand2",
                anchor="w"
            )
            link_label.pack(side="left", padx=3)
            link_label.bind("<Button-1>", lambda e, url=post_url: self._open_url(url))

            # Target
            target_label = ctk.CTkLabel(
                row,
                text=str(self.post_status[post_id]['target']),
                width=60,
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text_primary"]
            )
            target_label.pack(side="left", padx=3)

            # Liked count
            liked_label = ctk.CTkLabel(
                row,
                text=str(self.post_status[post_id]['liked']),
                width=60,
                font=ctk.CTkFont(size=11),
                text_color=COLORS["success"]
            )
            liked_label.pack(side="left", padx=3)

            # Status (Completed)
            completed = self.post_status[post_id]['completed']
            completed_label = ctk.CTkLabel(
                row,
                text="Đã like hôm nay" if completed else "-",
                width=110,
                font=ctk.CTkFont(size=10),
                text_color=COLORS["success"] if completed else COLORS["text_secondary"]
            )
            completed_label.pack(side="left", padx=3)

            # Error
            error = self.post_status[post_id]['error']
            error_label = ctk.CTkLabel(
                row,
                text="✗" if error else "-",
                width=40,
                font=ctk.CTkFont(size=11),
                text_color=COLORS["danger"] if error else COLORS["text_secondary"]
            )
            error_label.pack(side="left", padx=3)

            # Store widgets for updating
            self.post_widgets[post_id] = {
                'row': row,
                'target': target_label,
                'liked': liked_label,
                'completed': completed_label,
                'error': error_label
            }

    def _toggle_select_all(self):
        """Toggle chọn tất cả"""
        select_all = self.select_all_var.get()
        for var in self.post_vars.values():
            var.set(select_all)

    def _on_date_filter_change(self, choice):
        """Khi đổi filter ngày"""
        self._load_posts()

    def _on_folder_change(self, choice):
        """Khi đổi folder"""
        self._load_profiles()

    def _open_url(self, url):
        """Mở URL trong browser"""
        import webbrowser
        if url:
            webbrowser.open(url)

    def _log(self, message: str):
        """Thêm log"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"[{timestamp}] {message}\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def _update_post_status(self, post_id, target=None, liked=None, completed=None, error=None):
        """Cập nhật status của post"""
        if post_id not in self.post_status:
            return

        if target is not None:
            self.post_status[post_id]['target'] = target
        if liked is not None:
            self.post_status[post_id]['liked'] = liked
        if completed is not None:
            self.post_status[post_id]['completed'] = completed
        if error is not None:
            self.post_status[post_id]['error'] = error

        # Update UI
        if post_id in self.post_widgets:
            widgets = self.post_widgets[post_id]
            if target is not None:
                widgets['target'].configure(text=str(target))
            if liked is not None:
                widgets['liked'].configure(text=str(liked))
            if completed is not None:
                widgets['completed'].configure(
                    text="Đã like hôm nay" if completed else "-",
                    text_color=COLORS["success"] if completed else COLORS["text_secondary"]
                )
                # Đổi màu nền row thành xanh khi hoàn thành
                if completed:
                    widgets['row'].configure(fg_color="#1a472a")  # Dark green
            if error is not None:
                widgets['error'].configure(
                    text="✗" if error else "-",
                    text_color=COLORS["danger"] if error else COLORS["text_secondary"]
                )

    def _set_status(self, text: str, status_type: str = "info"):
        """Cập nhật status"""
        if self.status_callback:
            self.status_callback(text, status_type)
        self.status_label.configure(text=text)

    def _start_liking(self):
        """Bắt đầu like bài viết"""
        if self._is_running:
            return

        # Get selected posts
        selected_posts = []
        for post in self.posts:
            post_id = post.get('id', self.posts.index(post))
            if post_id in self.post_vars and self.post_vars[post_id].get():
                selected_posts.append(post)

        if not selected_posts:
            self._log("Vui lòng chọn ít nhất 1 bài để like")
            return

        # Refresh profiles trước khi chạy
        self._log("Đang tải danh sách profiles...")
        self._load_profiles()

        if not self.profiles:
            self._log("Không có profile nào để sử dụng. Kiểm tra kết nối Hidemium.")
            return

        self._log(f"Đã tải {len(self.profiles)} profiles")

        # Get settings
        try:
            thread_count = int(self.thread_count_entry.get() or 3)
            like_count = int(self.like_count_entry.get() or 5)
        except:
            thread_count = 3
            like_count = 5

        # Update target for selected posts
        for post in selected_posts:
            post_id = post.get('id', self.posts.index(post))
            if post_id in self.post_status:
                self.post_status[post_id]['target'] = like_count
                self.post_status[post_id]['liked'] = 0
                self.post_status[post_id]['completed'] = False
                self.post_status[post_id]['error'] = False
            # Update target in UI as well
            self._update_post_status(post_id, target=like_count, liked=0, completed=False, error=False)
            # Reset row color
            if post_id in self.post_widgets:
                self.post_widgets[post_id]['row'].configure(fg_color=COLORS["bg_card"])

        self._is_running = True
        self._stop_requested = False

        self._log(f"Bắt đầu like {len(selected_posts)} bài với {thread_count} luồng, {like_count} like/bài")
        self._set_status(f"Đang chạy... 0/{len(selected_posts)}")

        # Start in background
        threading.Thread(
            target=self._execute_liking,
            args=(selected_posts, thread_count, like_count),
            daemon=True
        ).start()

    def _execute_liking(self, posts: List[Dict], thread_count: int, like_count: int):
        """Thực hiện like với multiple threads"""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        total_posts = len(posts)
        completed_posts = 0

        # Sắp xếp profiles theo tên (00, 01, 02, ...)
        # Đảm bảo profiles là list of dicts
        available_profiles = []
        print(f"[DEBUG] Processing {len(self.profiles)} profiles from self.profiles")
        for i, p in enumerate(self.profiles):
            print(f"[DEBUG] Profile {i}: type={type(p)}, value={str(p)[:100]}")
            if isinstance(p, dict):
                available_profiles.append(p)
            elif isinstance(p, str):
                # Nếu là string (uuid), tạo dict với uuid
                available_profiles.append({'uuid': p, 'name': p[:8]})

        available_profiles = sorted(available_profiles, key=lambda p: p.get('name', ''))

        # Log profile names
        profile_names = [p.get('name', 'N/A') for p in available_profiles[:10]]
        self.after(0, lambda pn=profile_names: self._log(f"Profiles: {', '.join(pn)}{'...' if len(available_profiles) > 10 else ''}"))
        self.after(0, lambda: self._log(f"Có {len(available_profiles)} profiles sẵn sàng"))

        for post in posts:
            if self._stop_requested:
                break

            post_id = post.get('id', posts.index(post))
            post_url = post.get('post_url', '')

            if not post_url:
                self.after(0, lambda pid=post_id: self._update_post_status(pid, error=True))
                completed_posts += 1
                continue

            self.after(0, lambda msg=f"Đang like: {post_url[:50]}...": self._log(msg))

            # Get profiles for this post
            profiles_to_use = available_profiles[:like_count]
            if len(profiles_to_use) < like_count:
                # Not enough profiles, reuse
                profiles_to_use = (available_profiles * ((like_count // len(available_profiles)) + 1))[:like_count]

            liked_count = 0
            error_occurred = False

            def like_with_profile(profile):
                """Like bài với 1 profile"""
                return self._like_post_with_profile(profile, post_url)

            # Execute with thread pool
            with ThreadPoolExecutor(max_workers=min(thread_count, len(profiles_to_use))) as executor:
                futures = {executor.submit(like_with_profile, p): p for p in profiles_to_use}

                for future in as_completed(futures):
                    if self._stop_requested:
                        break

                    try:
                        success = future.result()
                        if success:
                            liked_count += 1
                            self.after(0, lambda pid=post_id, lc=liked_count: self._update_post_status(pid, liked=lc))
                    except Exception as e:
                        error_occurred = True
                        self.after(0, lambda msg=f"Lỗi: {e}": self._log(msg))

            # Update final status
            is_completed = liked_count >= like_count
            self.after(0, lambda pid=post_id, c=is_completed, e=error_occurred:
                       self._update_post_status(pid, completed=c, error=e if not c else False))

            completed_posts += 1
            progress = completed_posts / total_posts
            self.after(0, lambda p=progress: self.progress_bar.set(p))
            self.after(0, lambda cp=completed_posts, tp=total_posts:
                       self._set_status(f"Đang chạy... {cp}/{tp}"))

            # Delay between posts
            if not self._stop_requested and completed_posts < total_posts:
                time.sleep(random.uniform(2, 5))

        self._is_running = False
        self.after(0, lambda: self._set_status("Hoàn tất"))
        self.after(0, lambda: self._log(f"Hoàn tất like {completed_posts}/{total_posts} bài"))

    def _like_post_with_profile(self, profile: Dict, post_url: str) -> bool:
        """Like bài viết với 1 profile qua CDP"""
        import websocket
        import json

        profile_uuid = profile.get('uuid', '')
        profile_name = profile.get('name', 'Unknown')

        if not profile_uuid:
            self.after(0, lambda: self._log(f"[{profile_name}] Không có UUID"))
            return False

        try:
            self.after(0, lambda pn=profile_name, pu=profile_uuid[:8]: self._log(f"[{pn}] ({pu}) Đang mở browser..."))

            # Mở browser
            result = api.open_browser(profile_uuid)
            print(f"[DEBUG] open_browser response for {profile_name}: {result}")

            # Kiểm tra lỗi
            if result.get('type') == 'error':
                err_msg = result.get('message') or result.get('title', 'Unknown error')
                self.after(0, lambda pn=profile_name, e=err_msg: self._log(f"[{pn}] Lỗi: {e}"))
                return False

            # Kiểm tra status
            status = result.get('status') or result.get('type')
            if status not in ['successfully', 'success', True]:
                # Browser có thể đã mở sẵn
                if 'already' not in str(result).lower() and 'running' not in str(result).lower():
                    err_msg = result.get('message') or result.get('title', f'Status: {status}')
                    self.after(0, lambda pn=profile_name, e=err_msg: self._log(f"[{pn}] Lỗi: {e}"))
                    return False

            # Lấy data - có thể ở nhiều vị trí khác nhau
            data = result.get('data', {})
            if not isinstance(data, dict):
                print(f"[DEBUG] data is not dict: {type(data)} = {data}")
                data = {}

            remote_port = data.get('remote_port') or data.get('port')
            ws_url = data.get('web_socket', '') or data.get('webSocketDebuggerUrl', '')

            print(f"[DEBUG] From data: remote_port={remote_port}, ws_url={ws_url}")

            # Thử lấy từ root nếu không có trong data
            if not remote_port:
                remote_port = result.get('remote_port') or result.get('port')
            if not ws_url:
                ws_url = result.get('web_socket', '') or result.get('webSocketDebuggerUrl', '')

            print(f"[DEBUG] After root check: remote_port={remote_port}, ws_url={ws_url}")

            # Parse port từ ws_url
            if not remote_port and ws_url:
                match = re.search(r':(\d+)/', ws_url)
                if match:
                    remote_port = int(match.group(1))
                    print(f"[DEBUG] Parsed port from ws_url: {remote_port}")

            if not remote_port:
                self.after(0, lambda pn=profile_name, r=str(result)[:300]: self._log(f"[{pn}] Không có port. Response: {r}"))
                return False

            self.after(0, lambda pn=profile_name, p=remote_port: self._log(f"[{pn}] Đã mở, port: {p}"))

            cdp_base = f"http://127.0.0.1:{remote_port}"
            time.sleep(2)

            # Lấy page websocket
            page_ws = None
            for _ in range(5):
                try:
                    resp = requests.get(f"{cdp_base}/json", timeout=10)
                    pages = resp.json()
                    for p in pages:
                        if p.get('type') == 'page':
                            page_ws = p.get('webSocketDebuggerUrl')
                            break
                    if page_ws:
                        break
                except:
                    time.sleep(1)

            if not page_ws:
                return False

            # Kết nối WebSocket
            ws = None
            try:
                ws = websocket.create_connection(page_ws, timeout=30, suppress_origin=True)
            except:
                try:
                    ws = websocket.create_connection(page_ws, timeout=30)
                except:
                    return False

            cdp_id = 1

            def cdp_send(method, params=None):
                nonlocal cdp_id
                cdp_id += 1
                msg = {"id": cdp_id, "method": method, "params": params or {}}
                ws.send(json.dumps(msg))
                while True:
                    try:
                        ws.settimeout(30)
                        resp = ws.recv()
                        data = json.loads(resp)
                        if data.get('id') == cdp_id:
                            return data
                    except:
                        return {}

            def cdp_eval(expr):
                result = cdp_send("Runtime.evaluate", {
                    "expression": expr,
                    "returnByValue": True,
                    "awaitPromise": True
                })
                return result.get('result', {}).get('result', {}).get('value')

            # Navigate đến bài viết
            cdp_send("Page.navigate", {"url": post_url})
            time.sleep(random.uniform(4, 6))

            # Đợi page load
            for _ in range(10):
                ready = cdp_eval("document.readyState")
                if ready == 'complete':
                    break
                time.sleep(1)

            time.sleep(random.uniform(1, 2))

            # Click Like
            click_like_js = '''
            (function() {
                let all = document.querySelectorAll('[aria-label="Thích"], [aria-label="Like"]');
                for (let btn of all) {
                    let rect = btn.getBoundingClientRect();
                    if (rect.top > 0 && rect.top < window.innerHeight && rect.width > 0) {
                        btn.click();
                        return true;
                    }
                }
                return false;
            })()
            '''
            like_result = cdp_eval(click_like_js)

            if like_result:
                self.after(0, lambda pn=profile_name: self._log(f"[{pn}] ✓ Đã like thành công"))
            else:
                self.after(0, lambda pn=profile_name: self._log(f"[{pn}] ✗ Không tìm thấy nút Like"))

            time.sleep(random.uniform(1, 2))

            # Đóng WebSocket
            try:
                ws.close()
            except:
                pass

            return like_result == True

        except Exception as e:
            self.after(0, lambda pn=profile_name, err=str(e): self._log(f"[{pn}] Lỗi: {err}"))
            return False

    def _stop_liking(self):
        """Dừng quá trình like"""
        if self._is_running:
            self._stop_requested = True
            self._log("Đang dừng...")
            self._set_status("Đang dừng...")
