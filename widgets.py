"""
Custom Widgets - Các widget tùy chỉnh cho UI
"""
import customtkinter as ctk
from typing import Callable, Optional, List, Dict
from config import COLORS


class ModernCard(ctk.CTkFrame):
    """Card hiện đại - SonCuto themed"""
    def __init__(self, master, title: str = "", **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_card"],
            corner_radius=10,  # Slightly smaller radius
            border_width=1,
            border_color=COLORS["border"],
            **kwargs
        )

        if title:
            self.title_label = ctk.CTkLabel(
                self,
                text=title,
                font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                text_color=COLORS["text_primary"]
            )
            self.title_label.pack(anchor="w", padx=16, pady=(12, 8))  # Compact


class ModernButton(ctk.CTkButton):
    """Button hiện đại - SonCuto themed"""
    def __init__(self, master, text: str, variant: str = "primary", icon: str = None, **kwargs):
        colors = {
            "primary": (COLORS["primary"], COLORS["primary_hover"]),  # Green
            "secondary": (COLORS["secondary"], COLORS["secondary_hover"]),  # Pink
            "success": (COLORS["success"], COLORS["primary_hover"]),
            "warning": (COLORS["warning"], "#ffda3d"),
            "danger": (COLORS["error"], "#ff7070"),
            "ghost": (COLORS["bg_card"], COLORS["border_light"])
        }

        fg, hover = colors.get(variant, colors["primary"])

        # Dark text for light buttons
        text_color = COLORS["bg_dark"] if variant in ["primary", "success", "warning"] else COLORS["text_primary"]

        super().__init__(
            master,
            text=f" {icon} {text}" if icon else text,
            fg_color=fg,
            hover_color=hover,
            corner_radius=8,  # Slightly smaller
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=text_color,
            height=36,  # Compact
            **kwargs
        )


class ModernEntry(ctk.CTkEntry):
    """Entry field - SonCuto themed"""
    def __init__(self, master, placeholder: str = "", **kwargs):
        # Get bg_input or fallback
        bg_input = COLORS.get("bg_input", COLORS["bg_secondary"])
        super().__init__(
            master,
            placeholder_text=placeholder,
            fg_color=bg_input,
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            placeholder_text_color=COLORS["text_muted"] if "text_muted" in COLORS else COLORS["text_secondary"],
            corner_radius=8,
            height=36,  # Compact
            font=ctk.CTkFont(family="Segoe UI", size=12),
            **kwargs
        )


class ModernTextbox(ctk.CTkTextbox):
    """Textbox - SonCuto themed"""
    def __init__(self, master, **kwargs):
        bg_input = COLORS.get("bg_input", COLORS["bg_secondary"])
        super().__init__(
            master,
            fg_color=bg_input,
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            corner_radius=8,
            font=ctk.CTkFont(family="Consolas", size=11),
            border_width=1,
            **kwargs
        )


class ProfileCard(ctk.CTkFrame):
    """Card hiển thị thông tin profile - SonCuto compact"""
    def __init__(self, master, profile_data: Dict,
                 on_toggle: Callable = None,
                 on_edit: Callable = None,
                 on_select: Callable = None,
                 **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_card"],
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
            height=80,  # More compact
            **kwargs
        )

        self.profile_data = profile_data
        self.on_toggle = on_toggle
        self.on_edit = on_edit
        self.on_select = on_select
        self.is_selected = False
        self.is_running = profile_data.get('check_open') == 1

        self.pack_propagate(False)
        self._create_widgets()

        # Bind click events
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _create_widgets(self):
        # Checkbox
        self.checkbox_var = ctk.BooleanVar(value=False)
        self.checkbox = ctk.CTkCheckBox(
            self,
            text="",
            variable=self.checkbox_var,
            width=20,
            height=20,
            fg_color=COLORS["primary"],  # Green
            hover_color=COLORS["primary_hover"],
            command=self._on_checkbox_change
        )
        self.checkbox.place(x=10, y=30)

        # Avatar - smaller
        self.avatar = ctk.CTkLabel(
            self,
            text="👤",
            font=ctk.CTkFont(size=24),
            width=40,
            height=40
        )
        self.avatar.place(x=40, y=20)

        # Profile info - compact
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.place(x=90, y=12)

        # Name
        name = self.profile_data.get('name', 'Unknown')
        self.name_label = ctk.CTkLabel(
            info_frame,
            text=name[:25] + "..." if len(name) > 25 else name,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        self.name_label.pack(anchor="w")

        # UUID + Status in one line
        status_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        status_frame.pack(anchor="w")

        uuid = self.profile_data.get('uuid', '')[:12]
        ctk.CTkLabel(
            status_frame,
            text=f"{uuid}...",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=COLORS["text_muted"] if "text_muted" in COLORS else COLORS["text_secondary"]
        ).pack(side="left")

        # Status dot
        self.is_running = self.profile_data.get('check_open', 0) == 1
        status_color = COLORS["primary"] if self.is_running else COLORS["text_muted"]
        status_text = "RUNNING" if self.is_running else "READY"
        ctk.CTkLabel(
            status_frame,
            text=f"  ● {status_text}",
            font=ctk.CTkFont(size=10),
            text_color=status_color
        ).pack(side="left")

        # Action buttons - compact
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.place(relx=1.0, x=-10, y=25, anchor="ne")

        # Toggle Open/Close button
        if self.is_running:
            btn_text = "Đóng"
            btn_color = COLORS["secondary"]  # Pink for close
            btn_hover = COLORS["secondary_hover"]
        else:
            btn_text = "Mở"
            btn_color = COLORS["primary"]  # Green for open
            btn_hover = COLORS["primary_hover"]

        self.toggle_btn = ctk.CTkButton(
            btn_frame,
            text=btn_text,
            width=60,
            height=28,
            fg_color=btn_color,
            hover_color=btn_hover,
            corner_radius=6,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLORS["bg_dark"],
            command=self._on_toggle_click
        )
        self.toggle_btn.pack(side="left", padx=2)

        # Edit button - smaller
        self.edit_btn = ctk.CTkButton(
            btn_frame,
            text="✏️",
            width=28,
            height=28,
            fg_color=COLORS["bg_secondary"],
            hover_color=COLORS["border_light"] if "border_light" in COLORS else COLORS["border"],
            corner_radius=6,
            command=lambda: self.on_edit(self.profile_data) if self.on_edit else None
        )
        self.edit_btn.pack(side="left", padx=2)
    
    def _on_toggle_click(self):
        """Xử lý toggle mở/đóng"""
        if self.on_toggle:
            self.on_toggle(self.profile_data, not self.is_running)

    def _on_click(self, event):
        pass

    def _on_enter(self, event):
        self.configure(border_color=COLORS["primary"])  # Green on hover

    def _on_leave(self, event):
        if not self.is_selected:
            self.configure(border_color=COLORS["border"])

    def _on_checkbox_change(self):
        self.is_selected = self.checkbox_var.get()
        if self.is_selected:
            self.configure(border_color=COLORS["primary"])  # Green when selected
        else:
            self.configure(border_color=COLORS["border"])
        if self.on_select:
            self.on_select(self.profile_data, self.is_selected)


class PostCard(ctk.CTkFrame):
    """Card hiển thị bài đăng - SonCuto compact"""
    def __init__(self, master, post_data: Dict,
                 on_like: Callable = None,
                 on_comment: Callable = None,
                 on_delete: Callable = None,
                 **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_card"],
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
            **kwargs
        )

        self.post_data = post_data
        self.on_like = on_like
        self.on_comment = on_comment
        self.on_delete = on_delete

        self._create_widgets()

    def _create_widgets(self):
        # URL - compact
        url = self.post_data.get('url', '')
        url_display = url[:50] + "..." if len(url) > 50 else url

        self.url_label = ctk.CTkLabel(
            self,
            text=f"🔗 {url_display}",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS["primary"],  # Green link
            cursor="hand2"
        )
        self.url_label.pack(anchor="w", padx=12, pady=(10, 4))

        # Title - compact
        title = self.post_data.get('title', 'Không có tiêu đề')
        self.title_label = ctk.CTkLabel(
            self,
            text=title[:70] + "..." if len(title) > 70 else title,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        self.title_label.pack(anchor="w", padx=12, pady=2)

        # Stats and buttons - compact
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=12, pady=(4, 10))

        # Stats
        stats_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        stats_frame.pack(side="left")

        like_count = self.post_data.get('like_count', 0)
        comment_count = self.post_data.get('comment_count', 0)

        ctk.CTkLabel(
            stats_frame,
            text=f"❤️ {like_count}",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["secondary"]  # Pink
        ).pack(side="left", padx=(0, 12))

        ctk.CTkLabel(
            stats_frame,
            text=f"💬 {comment_count}",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"] if "text_muted" in COLORS else COLORS["text_secondary"]
        ).pack(side="left")

        # Action buttons - compact
        btn_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        btn_frame.pack(side="right")

        ctk.CTkButton(
            btn_frame,
            text="Like",
            width=60,
            height=26,
            fg_color=COLORS["secondary"],  # Pink
            hover_color=COLORS["secondary_hover"],
            corner_radius=6,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=COLORS["text_primary"],
            command=lambda: self.on_like(self.post_data) if self.on_like else None
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            btn_frame,
            text="Comment",
            width=70,
            height=26,
            fg_color=COLORS["primary"],  # Green
            hover_color=COLORS["primary_hover"],
            corner_radius=6,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=COLORS["bg_dark"],
            command=lambda: self.on_comment(self.post_data) if self.on_comment else None
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            btn_frame,
            text="🗑️",
            width=26,
            height=26,
            fg_color=COLORS["bg_secondary"],
            hover_color=COLORS["error"],
            corner_radius=6,
            command=lambda: self.on_delete(self.post_data) if self.on_delete else None
        ).pack(side="left", padx=2)


class ScriptCard(ctk.CTkFrame):
    """Card hiển thị kịch bản - SonCuto compact"""
    def __init__(self, master, script_data: Dict,
                 on_edit: Callable = None,
                 on_run: Callable = None,
                 on_delete: Callable = None,
                 **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_card"],
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
            **kwargs
        )

        self.script_data = script_data
        self.on_edit = on_edit
        self.on_run = on_run
        self.on_delete = on_delete

        self._create_widgets()

    def _create_widgets(self):
        # Icon + Name - compact
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(
            header_frame,
            text="📜",
            font=ctk.CTkFont(size=18)
        ).pack(side="left", padx=(0, 8))

        name = self.script_data.get('name', 'Untitled Script')
        ctk.CTkLabel(
            header_frame,
            text=name,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left")

        # Description - compact
        desc = self.script_data.get('description', '')
        if desc:
            ctk.CTkLabel(
                self,
                text=desc[:80] + "..." if len(desc) > 80 else desc,
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text_muted"] if "text_muted" in COLORS else COLORS["text_secondary"]
            ).pack(anchor="w", padx=12, pady=2)

        # Action buttons - compact
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=12, pady=(4, 10))

        ctk.CTkButton(
            btn_frame,
            text="▶ Chạy",
            width=70,
            height=26,
            fg_color=COLORS["primary"],  # Green
            hover_color=COLORS["primary_hover"],
            corner_radius=6,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLORS["bg_dark"],
            command=lambda: self.on_run(self.script_data) if self.on_run else None
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            btn_frame,
            text="Sửa",
            width=60,
            height=26,
            fg_color=COLORS["bg_secondary"],
            hover_color=COLORS["border_light"] if "border_light" in COLORS else COLORS["border"],
            corner_radius=6,
            font=ctk.CTkFont(size=11),
            command=lambda: self.on_edit(self.script_data) if self.on_edit else None
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            btn_frame,
            text="🗑️",
            width=26,
            height=26,
            fg_color=COLORS["bg_secondary"],
            hover_color=COLORS["error"],
            corner_radius=6,
            command=lambda: self.on_delete(self.script_data) if self.on_delete else None
        ).pack(side="left", padx=2)


class StatusBar(ctk.CTkFrame):
    """Status bar - SonCuto themed"""
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_secondary"],
            height=28,  # Compact
            corner_radius=0,
            **kwargs
        )

        self.pack_propagate(False)

        self.status_label = ctk.CTkLabel(
            self,
            text="● Sẵn sàng",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["primary"]  # Green
        )
        self.status_label.pack(side="left", padx=12)

        self.info_label = ctk.CTkLabel(
            self,
            text="SonCuto FB v2.0",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_muted"] if "text_muted" in COLORS else COLORS["text_secondary"]
        )
        self.info_label.pack(side="right", padx=12)

    def set_status(self, text: str, status_type: str = "info"):
        colors = {
            "success": COLORS["primary"],  # Green
            "error": COLORS["error"],
            "warning": COLORS["warning"],
            "info": COLORS["text_muted"] if "text_muted" in COLORS else COLORS["text_secondary"]
        }
        color = colors.get(status_type, COLORS["text_secondary"])
        self.status_label.configure(text=f"● {text}", text_color=color)


class SearchBar(ctk.CTkFrame):
    """Thanh tìm kiếm - SonCuto themed"""
    def __init__(self, master, placeholder: str = "Tìm kiếm...", on_search: Callable = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.on_search = on_search

        self.search_entry = ModernEntry(
            self,
            placeholder=placeholder,
            width=250
        )
        self.search_entry.pack(side="left", padx=(0, 6))
        self.search_entry.bind("<Return>", self._do_search)

        self.search_btn = ctk.CTkButton(
            self,
            text="🔍",
            width=36,
            height=36,
            fg_color=COLORS["primary"],  # Green
            hover_color=COLORS["primary_hover"],
            corner_radius=8,
            command=self._do_search
        )
        self.search_btn.pack(side="left")

    def _do_search(self, event=None):
        if self.on_search:
            self.on_search(self.search_entry.get())

    def get_value(self) -> str:
        return self.search_entry.get()
