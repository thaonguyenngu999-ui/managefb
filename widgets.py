"""
Custom Widgets - SonCuto FB Pro
Modern UI components
"""
import customtkinter as ctk
from typing import Callable, Optional, List, Dict
from config import COLORS


class ModernCard(ctk.CTkFrame):
    """Card component - GitHub style"""
    def __init__(self, master, title: str = "", **kwargs):
        bg = COLORS.get("bg_card", "#21262d")
        border = COLORS.get("border", "#30363d")
        super().__init__(
            master,
            fg_color=bg,
            corner_radius=8,
            border_width=1,
            border_color=border,
            **kwargs
        )

        if title:
            self.title_label = ctk.CTkLabel(
                self,
                text=title,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=COLORS.get("text_primary", "#f0f6fc")
            )
            self.title_label.pack(anchor="w", padx=12, pady=(10, 6))


class ModernButton(ctk.CTkButton):
    """Button component - Modern style"""
    def __init__(self, master, text: str, variant: str = "primary", icon: str = None, **kwargs):
        # Color mappings
        bg_main = COLORS.get("bg_main", "#0d1117")
        colors = {
            "primary": (COLORS.get("primary", "#00d97e"), COLORS.get("primary_hover", "#2ee89a"), bg_main),
            "secondary": (COLORS.get("secondary", "#ff6b9d"), COLORS.get("secondary_hover", "#ff85b1"), "#fff"),
            "success": (COLORS.get("success", "#00d97e"), COLORS.get("primary_hover", "#2ee89a"), bg_main),
            "warning": (COLORS.get("warning", "#f0b429"), "#f5c842", bg_main),
            "danger": (COLORS.get("error", "#f85149"), "#ff6b6b", "#fff"),
            "ghost": (COLORS.get("bg_card", "#21262d"), COLORS.get("bg_card_hover", "#30363d"), COLORS.get("text_primary", "#f0f6fc"))
        }

        fg, hover, txt = colors.get(variant, colors["primary"])

        super().__init__(
            master,
            text=f"{icon} {text}" if icon else text,
            fg_color=fg,
            hover_color=hover,
            corner_radius=6,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=txt,
            height=34,
            **kwargs
        )


class ModernEntry(ctk.CTkEntry):
    """Entry field component"""
    def __init__(self, master, placeholder: str = "", **kwargs):
        super().__init__(
            master,
            placeholder_text=placeholder,
            fg_color=COLORS.get("bg_input", "#0d1117"),
            border_color=COLORS.get("border", "#30363d"),
            text_color=COLORS.get("text_primary", "#f0f6fc"),
            placeholder_text_color=COLORS.get("text_muted", "#6e7681"),
            corner_radius=6,
            height=34,
            font=ctk.CTkFont(size=12),
            **kwargs
        )


class ModernTextbox(ctk.CTkTextbox):
    """Textbox component"""
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            fg_color=COLORS.get("bg_input", "#0d1117"),
            border_color=COLORS.get("border", "#30363d"),
            text_color=COLORS.get("text_primary", "#f0f6fc"),
            corner_radius=6,
            font=ctk.CTkFont(family="Consolas", size=11),
            border_width=1,
            **kwargs
        )


class ProfileCard(ctk.CTkFrame):
    """Profile card - Compact modern style"""
    def __init__(self, master, profile_data: Dict,
                 on_toggle: Callable = None,
                 on_edit: Callable = None,
                 on_select: Callable = None,
                 **kwargs):
        super().__init__(
            master,
            fg_color=COLORS.get("bg_card", "#21262d"),
            corner_radius=6,
            border_width=1,
            border_color=COLORS.get("border", "#30363d"),
            height=72,
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
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _create_widgets(self):
        # Checkbox
        self.checkbox_var = ctk.BooleanVar(value=False)
        self.checkbox = ctk.CTkCheckBox(
            self,
            text="",
            variable=self.checkbox_var,
            width=18,
            height=18,
            fg_color=COLORS.get("primary", "#00d97e"),
            hover_color=COLORS.get("primary_hover", "#2ee89a"),
            command=self._on_checkbox_change
        )
        self.checkbox.place(x=12, y=27)

        # Avatar
        self.avatar = ctk.CTkLabel(
            self,
            text="👤",
            font=ctk.CTkFont(size=20),
            width=32,
            height=32
        )
        self.avatar.place(x=40, y=20)

        # Info
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.place(x=80, y=14)

        # Name
        name = self.profile_data.get('name', 'Unknown')
        ctk.CTkLabel(
            info_frame,
            text=name[:22] + "..." if len(name) > 22 else name,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS.get("text_primary", "#f0f6fc")
        ).pack(anchor="w")

        # UUID + Status
        meta_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        meta_frame.pack(anchor="w")

        uuid = self.profile_data.get('uuid', '')[:10]
        ctk.CTkLabel(
            meta_frame,
            text=f"{uuid}...",
            font=ctk.CTkFont(family="Consolas", size=9),
            text_color=COLORS.get("text_muted", "#6e7681")
        ).pack(side="left")

        self.is_running = self.profile_data.get('check_open', 0) == 1
        status_color = COLORS.get("online", "#3fb950") if self.is_running else COLORS.get("offline", "#6e7681")
        status_text = "● ON" if self.is_running else "● OFF"
        ctk.CTkLabel(
            meta_frame,
            text=f"  {status_text}",
            font=ctk.CTkFont(size=9),
            text_color=status_color
        ).pack(side="left")

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.place(relx=1.0, x=-10, y=22, anchor="ne")

        bg_main = COLORS.get("bg_main", "#0d1117")
        if self.is_running:
            btn_text = "Stop"
            btn_color = COLORS.get("error", "#f85149")
            btn_hover = "#ff6b6b"
        else:
            btn_text = "Start"
            btn_color = COLORS.get("primary", "#00d97e")
            btn_hover = COLORS.get("primary_hover", "#2ee89a")

        self.toggle_btn = ctk.CTkButton(
            btn_frame,
            text=btn_text,
            width=55,
            height=26,
            fg_color=btn_color,
            hover_color=btn_hover,
            corner_radius=4,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=bg_main if not self.is_running else "#fff",
            command=self._on_toggle_click
        )
        self.toggle_btn.pack(side="left", padx=2)

        self.edit_btn = ctk.CTkButton(
            btn_frame,
            text="✏️",
            width=26,
            height=26,
            fg_color=COLORS.get("bg_card_hover", "#30363d"),
            hover_color=COLORS.get("border_light", "#3d444d"),
            corner_radius=4,
            command=lambda: self.on_edit(self.profile_data) if self.on_edit else None
        )
        self.edit_btn.pack(side="left", padx=2)
    
    def _on_toggle_click(self):
        if self.on_toggle:
            self.on_toggle(self.profile_data, not self.is_running)

    def _on_enter(self, event):
        self.configure(border_color=COLORS.get("primary", "#00d97e"))

    def _on_leave(self, event):
        if not self.is_selected:
            self.configure(border_color=COLORS.get("border", "#30363d"))

    def _on_checkbox_change(self):
        self.is_selected = self.checkbox_var.get()
        self.configure(border_color=COLORS.get("primary", "#00d97e") if self.is_selected else COLORS.get("border", "#30363d"))
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
    """Status bar - Modern compact"""
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            fg_color=COLORS.get("bg_header", "#161b22"),
            height=26,
            corner_radius=0,
            **kwargs
        )

        self.pack_propagate(False)

        self.status_label = ctk.CTkLabel(
            self,
            text="● Ready",
            font=ctk.CTkFont(size=10),
            text_color=COLORS.get("online", "#3fb950")
        )
        self.status_label.pack(side="left", padx=12)

        self.info_label = ctk.CTkLabel(
            self,
            text="SonCuto FB v2.0",
            font=ctk.CTkFont(size=9),
            text_color=COLORS.get("text_muted", "#6e7681")
        )
        self.info_label.pack(side="right", padx=12)

    def set_status(self, text: str, status_type: str = "info"):
        colors = {
            "success": COLORS.get("online", "#3fb950"),
            "error": COLORS.get("error", "#f85149"),
            "warning": COLORS.get("warning", "#f0b429"),
            "info": COLORS.get("text_muted", "#6e7681")
        }
        self.status_label.configure(text=f"● {text}", text_color=colors.get(status_type, colors["info"]))


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
