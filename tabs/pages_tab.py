"""
Tab Quản Lý Page - Quản lý các Fanpage Facebook
"""
import customtkinter as ctk
from typing import List, Dict, Optional
import threading
import random
import time
import re
import requests
from datetime import datetime
from config import COLORS
from widgets import ModernButton, ModernEntry
from db import (
    get_profiles, get_pages, get_pages_for_profiles, save_page, delete_page, delete_pages_bulk,
    update_page_selection, sync_pages, clear_pages, get_pages_count
)
from api_service import api
from automation.window_manager import acquire_window_slot, release_window_slot, get_window_bounds
from automation.cdp_helper import CDPHelper

# Import BeautifulSoup for HTML parsing
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

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
        """Load danh sách profiles và folders từ database"""
        # Load profiles từ database (giống groups_tab)
        self.profiles = get_profiles()

        # Load folders từ Hidemium API
        try:
            self.folders = api.get_folders()
            if not isinstance(self.folders, list):
                self.folders = []
        except:
            self.folders = []

        # Update folder menu
        folder_names = ["-- Tất cả --"]
        for f in self.folders:
            fname = f.get('name') or f.get('folderName') or 'Unknown'
            folder_names.append(fname)
        self.folder_menu.configure(values=folder_names)

        # Render profiles
        self._render_profiles()
        self._set_status(f"Đã load {len(self.profiles)} profiles, {len(self.folders)} thư mục", "success")

    def _render_profiles(self):
        """Render danh sách profiles"""
        # Clear existing
        for widget in self.profile_list.winfo_children():
            widget.destroy()
        self.profile_checkbox_vars.clear()

        if not self.profiles:
            ctk.CTkLabel(
                self.profile_list,
                text="Không có profile",
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text_secondary"]
            ).pack(pady=10)
            self._update_profile_stats()
            return

        for profile in self.profiles:
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
        if folder_name == "-- Tất cả --":
            # Load tất cả profiles từ database
            self.profiles = get_profiles()
        else:
            # Tìm folder_id và load profiles theo folder từ API (giống login_tab)
            folder_id = None
            for f in self.folders:
                if f.get('name') == folder_name:
                    folder_id = f.get('id')
                    break

            if folder_id:
                try:
                    # Load profiles từ API với folder filter
                    self.profiles = api.get_profiles(folder_id=[folder_id]) or []
                except:
                    self.profiles = get_profiles()
            else:
                self.profiles = get_profiles()

        self._render_profiles()

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

        print(f"[Pages UI] Loading pages for profiles: {self.selected_profile_uuids}")
        self.pages = get_pages_for_profiles(self.selected_profile_uuids)
        print(f"[Pages UI] Loaded {len(self.pages)} pages from DB")
        for p in self.pages:
            print(f"[Pages UI]   - {p.get('page_name')} (page_id={p.get('page_id')}, profile={p.get('profile_uuid', '')[:12]})")
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
        """Scan pages cho 1 profile sử dụng CDPHelper"""
        pages_found = []
        slot_id = acquire_window_slot()
        cdp = None

        try:
            # Bước 1: Mở browser qua Hidemium API
            result = api.open_browser(profile_uuid)
            print(f"[Pages] open_browser {profile_uuid[:8]}: {result.get('status', result.get('type', 'unknown'))}")

            # Kiểm tra response
            status = result.get('status') or result.get('type')
            if status not in ['successfully', 'success', True]:
                if 'already' not in str(result).lower() and 'running' not in str(result).lower():
                    release_window_slot(slot_id)
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
                release_window_slot(slot_id)
                return []

            # Đợi browser khởi động
            time.sleep(2)

            # Bước 2: Lấy WebSocket URL
            cdp_base = f"http://127.0.0.1:{remote_port}"
            try:
                resp = requests.get(f"{cdp_base}/json", timeout=10)
                tabs = resp.json()
            except Exception as e:
                print(f"[Pages] CDP error for {profile_uuid[:8]}: {e}")
                return []

            page_ws = None
            for tab in tabs:
                if tab.get('type') == 'page':
                    page_ws = tab.get('webSocketDebuggerUrl')
                    break

            if not page_ws:
                print(f"[Pages] No page tab found")
                return []

            # Bước 3: Kết nối CDPHelper
            cdp = CDPHelper()
            if not cdp.connect(remote_port=remote_port, ws_url=page_ws):
                print(f"[Pages] Failed to connect CDPHelper")
                return []

            print(f"[Pages] CDPHelper connected!")

            # Giữ nguyên vị trí window hiện tại - không di chuyển

            # Navigate đến trang Pages
            pages_url = "https://www.facebook.com/pages/?category=your_pages&ref=bookmarks"
            print(f"[Pages] Navigating to: {pages_url}")
            cdp.navigate(pages_url)
            cdp.wait_for_page_load(timeout_ms=15000)
            time.sleep(5)

            # Scroll để load pages
            for i in range(5):
                cdp.execute_js("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.5)

            # Tìm pages bằng JavaScript
            js_find_pages = '''
            (function() {
                var pages = [];

                // Tìm tất cả links có chứa page ID
                var links = document.querySelectorAll('a[href*="profile.php?id="], a[href*="facebook.com/"][role="link"]');

                links.forEach(function(link) {
                    var href = link.getAttribute('href') || '';
                    var pageId = null;
                    var pageUrl = null;
                    var pageName = '';

                    // Pattern 1: profile.php?id=xxx
                    var match = href.match(/profile\\.php\\?id=(\\d+)/);
                    if (match) {
                        pageId = match[1];
                        pageUrl = 'https://www.facebook.com/profile.php?id=' + pageId;
                    }

                    // Pattern 2: /123456789 (numeric ID)
                    if (!pageId) {
                        match = href.match(/facebook\\.com\\/(\\d{10,})/);
                        if (match) {
                            pageId = match[1];
                            pageUrl = 'https://www.facebook.com/' + pageId;
                        }
                    }

                    if (!pageId) return;

                    // Skip nếu đã có
                    if (pages.some(function(p) { return p.page_id === pageId; })) return;

                    // Tìm tên page từ aria-label hoặc text gần nhất
                    var ariaLabel = link.getAttribute('aria-label');
                    if (ariaLabel && ariaLabel.length > 2 && ariaLabel.length < 100) {
                        pageName = ariaLabel.replace(/^Ảnh đại diện của /i, '').replace(/^Avatar of /i, '');
                    }

                    // Nếu chưa có tên, tìm trong parent elements
                    if (!pageName) {
                        var parent = link;
                        for (var i = 0; i < 8 && parent; i++) {
                            parent = parent.parentElement;
                            if (!parent) break;

                            var spans = parent.querySelectorAll('span, div');
                            for (var j = 0; j < spans.length; j++) {
                                var text = (spans[j].innerText || '').trim();
                                if (text.length > 2 && text.length < 80) {
                                    var skipTexts = ['Like', 'Follow', 'Message', 'Thích', 'Theo dõi', 'Nhắn tin',
                                        'Your Pages', 'Trang của bạn', 'Pages', 'Trang', 'Trang bạn quản lý',
                                        'thông báo', 'Tin nhắn', 'Tạo bài viết', 'Quảng cáo', 'Xem thêm'];
                                    if (!skipTexts.some(function(s) { return text.toLowerCase().includes(s.toLowerCase()); })) {
                                        pageName = text;
                                        break;
                                    }
                                }
                            }
                            if (pageName) break;
                        }
                    }

                    if (!pageName) pageName = pageId;

                    pages.push({
                        page_id: pageId,
                        page_name: pageName,
                        page_url: pageUrl
                    });
                });

                return JSON.stringify(pages);
            })();
            '''

            pages_json = cdp.execute_js(js_find_pages)
            print(f"[Pages] JS result: {pages_json[:200] if pages_json else 'None'}...")

            try:
                import json as json_module
                js_pages = json_module.loads(pages_json) if pages_json else []
                print(f"[Pages] JS found {len(js_pages)} pages")

                for p in js_pages:
                    page_id = p.get('page_id')
                    if page_id and not any(existing['page_id'] == page_id for existing in pages_found):
                        pages_found.append({
                            'page_id': page_id,
                            'page_name': p.get('page_name', page_id),
                            'page_url': p.get('page_url', f"https://www.facebook.com/{page_id}"),
                            'category': '',
                            'follower_count': 0,
                            'role': 'admin',
                            'profile_uuid': profile_uuid
                        })
            except Exception as e:
                print(f"[Pages] JS parse error: {e}")

            # Lưu vào database
            if pages_found:
                sync_pages(profile_uuid, pages_found)
                print(f"[Pages] Found and saved {len(pages_found)} pages for {profile_uuid[:8]}")
            else:
                print(f"[Pages] No pages found for {profile_uuid[:8]}")

        except Exception as e:
            import traceback
            print(f"[Pages] ERROR scan {profile_uuid[:8]}: {traceback.format_exc()}")

        finally:
            if cdp:
                cdp.close()
            release_window_slot(slot_id)

        return pages_found

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
        """Tạo page cho 1 profile sử dụng CDP"""
        slot_id = acquire_window_slot()
        created_page_id = None

        try:
            # Bước 1: Mở browser qua Hidemium API
            result = api.open_browser(profile_uuid)
            print(f"[CreatePage] open_browser {profile_uuid[:8]}: {result.get('status', result.get('type', 'unknown'))}")

            # Kiểm tra response
            status = result.get('status') or result.get('type')
            if status not in ['successfully', 'success', True]:
                if 'already' not in str(result).lower() and 'running' not in str(result).lower():
                    release_window_slot(slot_id)
                    return False

            # Lấy thông tin CDP
            data = result.get('data', {})
            remote_port = data.get('remote_port')
            ws_url = data.get('web_socket', '')

            if not remote_port:
                match = re.search(r':(\d+)/', ws_url)
                if match:
                    remote_port = int(match.group(1))

            if not remote_port:
                release_window_slot(slot_id)
                return False

            cdp_base = f"http://127.0.0.1:{remote_port}"

            # Đợi browser khởi động
            time.sleep(2)

            # Giữ nguyên vị trí window hiện tại - không di chuyển

            # Bước 2: Lấy danh sách tabs qua CDP
            try:
                resp = requests.get(f"{cdp_base}/json", timeout=10)
                tabs = resp.json()
            except Exception as e:
                print(f"[CreatePage] CDP error for {profile_uuid[:8]}: {e}")
                return False

            # Tìm tab page
            page_ws = None
            for tab in tabs:
                if tab.get('type') == 'page':
                    page_ws = tab.get('webSocketDebuggerUrl')
                    break

            if not page_ws:
                return False

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
                        return False

            if not ws:
                return False

            # Navigate đến trang tạo Page công khai
            create_url = "https://www.facebook.com/pages/create"
            ws.send(json_module.dumps({
                "id": 1,
                "method": "Page.navigate",
                "params": {"url": create_url}
            }))
            ws.recv()

            # Đợi trang load
            time.sleep(6)

            # Tìm và nhập tên Page - sử dụng selector đã xác nhận hoạt động
            js_fill_name = f'''
            (function() {{
                var pageName = "{name}";

                // Helper function để set value và trigger events (React-compatible)
                function setValueAndTrigger(input, value) {{
                    input.focus();
                    input.click();

                    if (input.tagName === 'INPUT') {{
                        var nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                        nativeInputValueSetter.call(input, value);
                    }} else if (input.tagName === 'TEXTAREA') {{
                        var nativeTextAreaSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
                        nativeTextAreaSetter.call(input, value);
                    }} else {{
                        input.innerText = value;
                    }}

                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                }}

                // Cách 1 (CONFIRMED WORKING): Selector input.x1i10hfl[type="text"]
                var confirmedInput = document.querySelector('input.x1i10hfl[type="text"]');
                if (confirmedInput && confirmedInput.offsetParent !== null) {{
                    setValueAndTrigger(confirmedInput, pageName);
                    return 'filled_via_confirmed_selector: input.x1i10hfl[type=text]';
                }}

                // Cách 2: Tìm label chứa "Tên Trang" rồi tìm input gần đó
                var labels = document.querySelectorAll('label, span, div');
                for (var i = 0; i < labels.length; i++) {{
                    var label = labels[i];
                    var text = (label.innerText || '').toLowerCase();
                    if (text.includes('tên trang') || text.includes('page name')) {{
                        // Tìm input trong cùng parent hoặc siblings
                        var parent = label.parentElement;
                        for (var j = 0; j < 5 && parent; j++) {{
                            var input = parent.querySelector('input:not([type="hidden"]):not([type="search"]), textarea, div[contenteditable="true"]');
                            if (input && input.offsetParent !== null) {{
                                setValueAndTrigger(input, pageName);
                                return 'filled_via_label: ' + text.substring(0, 30);
                            }}
                            parent = parent.parentElement;
                        }}
                    }}
                }}

                // Cách 3: Tìm input có aria-label hoặc placeholder
                var inputs = document.querySelectorAll('input:not([type="hidden"]):not([type="search"]), textarea, div[contenteditable="true"]');
                for (var i = 0; i < inputs.length; i++) {{
                    var input = inputs[i];
                    var ariaLabel = (input.getAttribute('aria-label') || '').toLowerCase();
                    var placeholder = (input.getAttribute('placeholder') || '').toLowerCase();

                    if (ariaLabel.includes('tên') || ariaLabel.includes('name') ||
                        placeholder.includes('tên') || placeholder.includes('name')) {{
                        setValueAndTrigger(input, pageName);
                        return 'filled_via_attr: ' + (ariaLabel || placeholder);
                    }}
                }}

                // Cách 4: Tìm bằng class x1i10hfl với các type khác
                var classBasedInputs = document.querySelectorAll('input.x1i10hfl');
                for (var i = 0; i < classBasedInputs.length; i++) {{
                    var input = classBasedInputs[i];
                    if (input.offsetParent !== null && !input.value) {{
                        setValueAndTrigger(input, pageName);
                        return 'filled_via_class_x1i10hfl: idx=' + i;
                    }}
                }}

                // Cách 5: Fallback - điền vào input text đầu tiên visible trong form
                var formInputs = document.querySelectorAll('input[type="text"], input:not([type]), textarea');
                for (var i = 0; i < formInputs.length; i++) {{
                    var input = formInputs[i];
                    if (input.offsetParent !== null && !input.value) {{
                        setValueAndTrigger(input, pageName);
                        return 'filled_first_empty: idx=' + i;
                    }}
                }}

                return 'no_name_input_found';
            }})();
            '''
            ws.send(json_module.dumps({
                "id": 10,
                "method": "Runtime.evaluate",
                "params": {"expression": js_fill_name}
            }))
            name_result = json_module.loads(ws.recv())
            name_val = name_result.get('result', {}).get('result', {}).get('value', 'N/A')
            print(f"[CreatePage] Fill name result: {name_val}")
            time.sleep(1.5)

            # Tìm và nhập Category - sử dụng aria-label selector (CONFIRMED)
            js_fill_category = f'''
            (function() {{
                var categoryText = "{category}";

                // Helper function
                function setValueAndTrigger(input, value) {{
                    input.focus();
                    input.click();
                    var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    setter.call(input, value);
                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                }}

                // Cách 1 (CONFIRMED): Selector bằng aria-label
                var categoryInput = document.querySelector('input[aria-label="Hạng mục (Bắt buộc)"]');
                if (categoryInput && categoryInput.offsetParent !== null) {{
                    setValueAndTrigger(categoryInput, categoryText);
                    return 'filled_via_aria_label: Hạng mục (Bắt buộc)';
                }}

                // Cách 2: Tìm input type="search" có class x1i10hfl (thứ 2 sau search FB)
                var searchInputs = document.querySelectorAll('input.x1i10hfl[type="search"]');
                for (var i = 0; i < searchInputs.length; i++) {{
                    var input = searchInputs[i];
                    var ariaLabel = input.getAttribute('aria-label') || '';
                    // Skip FB search box
                    if (!ariaLabel.includes('Tìm kiếm') && input.offsetParent !== null) {{
                        setValueAndTrigger(input, categoryText);
                        return 'filled_via_search_input: ' + ariaLabel;
                    }}
                }}

                // Cách 3: Fallback - tìm theo label
                var labels = document.querySelectorAll('label, span, div');
                for (var i = 0; i < labels.length; i++) {{
                    var label = labels[i];
                    var text = (label.innerText || '').toLowerCase();
                    if (text.includes('hạng mục') && !text.includes('nhập hạng mục')) {{
                        var parent = label.parentElement;
                        for (var j = 0; j < 5 && parent; j++) {{
                            var input = parent.querySelector('input[type="search"], input:not([type="hidden"])');
                            if (input && input.offsetParent !== null) {{
                                setValueAndTrigger(input, categoryText);
                                return 'filled_via_label_search';
                            }}
                            parent = parent.parentElement;
                        }}
                    }}
                }}

                return 'no_category_input_found';
            }})();
            '''
            ws.send(json_module.dumps({
                "id": 11,
                "method": "Runtime.evaluate",
                "params": {"expression": js_fill_category}
            }))
            cat_result = json_module.loads(ws.recv())
            cat_val = cat_result.get('result', {}).get('result', {}).get('value', 'N/A')
            print(f"[CreatePage] Fill category result: {cat_val}")
            time.sleep(2)

            # Chọn suggestion đầu tiên bằng keyboard (ArrowDown + Enter) - đáng tin cậy hơn click
            js_select_suggestion = '''
            (function() {
                // Tìm input category đang focus
                var categoryInput = document.querySelector('input[aria-label="Hạng mục (Bắt buộc)"]');
                if (!categoryInput) {
                    categoryInput = document.activeElement;
                }

                if (categoryInput && categoryInput.tagName === 'INPUT') {
                    // Gửi ArrowDown để chọn suggestion đầu tiên
                    categoryInput.dispatchEvent(new KeyboardEvent('keydown', {
                        key: 'ArrowDown',
                        code: 'ArrowDown',
                        keyCode: 40,
                        which: 40,
                        bubbles: true
                    }));

                    return 'sent_arrow_down';
                }
                return 'no_input_focused';
            })();
            '''
            ws.send(json_module.dumps({
                "id": 12,
                "method": "Runtime.evaluate",
                "params": {"expression": js_select_suggestion}
            }))
            arrow_result = json_module.loads(ws.recv())
            print(f"[CreatePage] ArrowDown: {arrow_result.get('result', {}).get('result', {}).get('value', 'N/A')}")
            time.sleep(0.5)

            # Nhấn Enter để chọn suggestion
            js_press_enter = '''
            (function() {
                var categoryInput = document.querySelector('input[aria-label="Hạng mục (Bắt buộc)"]');
                if (!categoryInput) {
                    categoryInput = document.activeElement;
                }

                if (categoryInput) {
                    categoryInput.dispatchEvent(new KeyboardEvent('keydown', {
                        key: 'Enter',
                        code: 'Enter',
                        keyCode: 13,
                        which: 13,
                        bubbles: true
                    }));
                    return 'sent_enter';
                }
                return 'no_input';
            })();
            '''
            ws.send(json_module.dumps({
                "id": 13,
                "method": "Runtime.evaluate",
                "params": {"expression": js_press_enter}
            }))
            enter_result = json_module.loads(ws.recv())
            print(f"[CreatePage] Enter: {enter_result.get('result', {}).get('result', {}).get('value', 'N/A')}")
            time.sleep(1.5)

            # Điền Tiểu sử (Bio) - TEXTAREA (CONFIRMED selector: textarea.x1i10hfl)
            if description:
                js_fill_bio = f'''
                (function() {{
                    var bioText = "{description.replace('"', '\\"').replace('\n', '\\n')}";

                    // Helper function cho textarea
                    function setTextareaValue(textarea, value) {{
                        textarea.focus();
                        textarea.click();
                        var setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
                        setter.call(textarea, value);
                        textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        textarea.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    }}

                    // Cách 1 (CONFIRMED): Selector textarea.x1i10hfl
                    var bioTextarea = document.querySelector('textarea.x1i10hfl');
                    if (bioTextarea && bioTextarea.offsetParent !== null) {{
                        setTextareaValue(bioTextarea, bioText);
                        return 'filled_via_confirmed_selector: textarea.x1i10hfl';
                    }}

                    // Cách 2: Tìm theo label "Tiểu sử"
                    var labels = document.querySelectorAll('span, label, div');
                    for (var i = 0; i < labels.length; i++) {{
                        var text = (labels[i].innerText || '').toLowerCase();
                        if (text.includes('tiểu sử') || text.includes('bio')) {{
                            var parent = labels[i].parentElement;
                            for (var j = 0; j < 5 && parent; j++) {{
                                var textarea = parent.querySelector('textarea');
                                if (textarea && textarea.offsetParent !== null) {{
                                    setTextareaValue(textarea, bioText);
                                    return 'filled_via_label_search';
                                }}
                                parent = parent.parentElement;
                            }}
                        }}
                    }}

                    return 'no_bio_textarea_found';
                }})();
                '''
                ws.send(json_module.dumps({
                    "id": 15,
                    "method": "Runtime.evaluate",
                    "params": {"expression": js_fill_bio}
                }))
                bio_result = json_module.loads(ws.recv())
                bio_val = bio_result.get('result', {}).get('result', {}).get('value', 'N/A')
                print(f"[CreatePage] Fill bio result: {bio_val}")
                time.sleep(1)

            # Click nút Create Page / Tạo Trang
            js_click_create = '''
            (function() {
                // Tìm nút Create Page - thường ở cuối form
                var buttons = document.querySelectorAll('div[role="button"], button, span[role="button"], [aria-label*="Create"], [aria-label*="Tạo"]');
                var createBtn = null;
                var allBtnTexts = [];

                for (var i = 0; i < buttons.length; i++) {
                    var btn = buttons[i];
                    var text = (btn.innerText || btn.textContent || '').trim().toLowerCase();
                    var ariaLabel = (btn.getAttribute('aria-label') || '').toLowerCase();
                    allBtnTexts.push(text.substring(0, 30));

                    // Ưu tiên nút có text chính xác
                    if (text === 'create page' || text === 'tạo trang') {
                        createBtn = btn;
                        break;
                    }
                    // Fallback: nút có chứa "create page" hoặc "tạo trang"
                    if (!createBtn && (text.includes('create page') || text.includes('tạo trang'))) {
                        createBtn = btn;
                    }
                    // Check aria-label
                    if (!createBtn && (ariaLabel.includes('create page') || ariaLabel.includes('tạo trang'))) {
                        createBtn = btn;
                    }
                }

                // Nếu không tìm thấy, thử tìm nút submit trong form
                if (!createBtn) {
                    var submitBtns = document.querySelectorAll('button[type="submit"], input[type="submit"]');
                    if (submitBtns.length > 0) {
                        createBtn = submitBtns[0];
                    }
                }

                if (createBtn) {
                    // Scroll to button and click
                    createBtn.scrollIntoView({behavior: 'smooth', block: 'center'});
                    setTimeout(function() {
                        createBtn.click();
                    }, 300);
                    return 'clicked: ' + (createBtn.innerText || createBtn.getAttribute('aria-label') || '').trim().substring(0, 50);
                }
                return 'no_button_found. Buttons: ' + allBtnTexts.slice(0, 10).join(', ');
            })();
            '''
            ws.send(json_module.dumps({
                "id": 13,
                "method": "Runtime.evaluate",
                "params": {"expression": js_click_create}
            }))
            result = json_module.loads(ws.recv())
            click_result = result.get('result', {}).get('result', {}).get('value', '')
            print(f"[CreatePage] Click result: {click_result}")

            # Đợi page được tạo - kiểm tra URL thay đổi (tối đa 30 giây)
            page_url = ""
            for wait_attempt in range(15):  # 15 lần x 2 giây = 30 giây
                time.sleep(2)
                ws.send(json_module.dumps({
                    "id": 14 + wait_attempt,
                    "method": "Runtime.evaluate",
                    "params": {"expression": "window.location.href"}
                }))
                result = json_module.loads(ws.recv())
                current_url = result.get('result', {}).get('result', {}).get('value', '')
                print(f"[CreatePage] URL check {wait_attempt + 1}: {current_url}")

                # Kiểm tra nếu đã redirect khỏi trang create
                if '/pages/create' not in current_url and current_url != 'https://www.facebook.com/pages/create':
                    page_url = current_url
                    print(f"[CreatePage] Page created! URL: {page_url}")
                    break

            # Tìm page ID từ URL - hỗ trợ nhiều định dạng
            # Format 1: /profile.php?id=123456789
            # Format 2: /123456789
            # Format 3: /pagename (username)
            if page_url:
                # Thử tìm numeric ID
                match = re.search(r'id=(\d+)', page_url)
                if not match:
                    match = re.search(r'facebook\.com/(\d{10,})', page_url)
                if not match:
                    # Lấy page username từ URL
                    match = re.search(r'facebook\.com/([^/?]+)', page_url)

                if match:
                    created_page_id = match.group(1)

            ws.close()

            # Lưu vào database nếu tạo thành công
            if created_page_id and page_url:
                page_data = {
                    'profile_uuid': profile_uuid,
                    'page_id': created_page_id,
                    'page_name': name,
                    'page_url': page_url,  # Lưu URL thực tế
                    'category': category,
                    'follower_count': 0,
                    'role': 'admin',
                    'note': description
                }
                save_page(page_data)
                print(f"[CreatePage] SUCCESS! Page ID: {created_page_id}")
                print(f"[CreatePage] Page URL: {page_url}")
                return True
            else:
                # Vẫn lưu vào DB với ID tạm
                import uuid as uuid_module
                page_data = {
                    'profile_uuid': profile_uuid,
                    'page_id': f"temp_{str(uuid_module.uuid4())[:8]}",
                    'page_name': name,
                    'page_url': '',
                    'category': category,
                    'follower_count': 0,
                    'role': 'admin',
                    'note': f"{description}\n[Cần scan lại để lấy Page ID thực]"
                }
                save_page(page_data)
                print(f"[CreatePage] Created page (temp ID) for {profile_uuid[:8]}")
                return True

        except Exception as e:
            import traceback
            print(f"[CreatePage] ERROR {profile_uuid[:8]}: {traceback.format_exc()}")
            return False
        finally:
            release_window_slot(slot_id)

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
