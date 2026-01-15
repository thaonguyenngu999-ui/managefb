"""
Custom Widgets - Các widget tùy chỉnh cho UI
"""
import customtkinter as ctk
from typing import Callable, Optional, List, Dict
from config import COLORS


class ModernCard(ctk.CTkFrame):
    """Card hiện đại với shadow effect"""
    def __init__(self, master, title: str = "", **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_card"],
            corner_radius=15,
            border_width=1,
            border_color=COLORS["border"],
            **kwargs
        )
        
        if title:
            self.title_label = ctk.CTkLabel(
                self,
                text=title,
                font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
                text_color=COLORS["text_primary"]
            )
            self.title_label.pack(anchor="w", padx=20, pady=(15, 10))


class ModernButton(ctk.CTkButton):
    """Button hiện đại với hover effects"""
    def __init__(self, master, text: str, variant: str = "primary", icon: str = None, **kwargs):
        colors = {
            "primary": (COLORS["accent"], COLORS["accent_hover"]),
            "success": (COLORS["success"], "#00f5b5"),
            "warning": (COLORS["warning"], "#ffda3d"),
            "danger": (COLORS["error"], "#ff4757"),
            "secondary": (COLORS["bg_secondary"], COLORS["border"])
        }
        
        fg, hover = colors.get(variant, colors["primary"])
        
        super().__init__(
            master,
            text=f"  {icon} {text}" if icon else text,
            fg_color=fg,
            hover_color=hover,
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=38,
            **kwargs
        )


class ModernEntry(ctk.CTkEntry):
    """Entry field hiện đại"""
    def __init__(self, master, placeholder: str = "", **kwargs):
        super().__init__(
            master,
            placeholder_text=placeholder,
            fg_color=COLORS["bg_secondary"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            placeholder_text_color=COLORS["text_secondary"],
            corner_radius=10,
            height=40,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            **kwargs
        )


class ModernTextbox(ctk.CTkTextbox):
    """Textbox hiện đại"""
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_secondary"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            corner_radius=10,
            font=ctk.CTkFont(family="Consolas", size=12),
            border_width=1,
            **kwargs
        )


class ProfileCard(ctk.CTkFrame):
    """Card hiển thị thông tin profile"""
    def __init__(self, master, profile_data: Dict, 
                 on_toggle: Callable = None,
                 on_edit: Callable = None,
                 on_select: Callable = None,
                 **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
            height=100,
            **kwargs
        )
        
        self.profile_data = profile_data
        self.on_toggle = on_toggle
        self.on_edit = on_edit
        self.on_select = on_select
        self.is_selected = False
        # Chỉ check_open == 1 để xác định browser đang mở
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
            width=24,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self._on_checkbox_change
        )
        self.checkbox.place(x=15, y=38)
        
        # Avatar placeholder
        self.avatar = ctk.CTkLabel(
            self,
            text="👤",
            font=ctk.CTkFont(size=32),
            width=50,
            height=50
        )
        self.avatar.place(x=50, y=25)
        
        # Profile info
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.place(x=115, y=15)
        
        # Name
        name = self.profile_data.get('name', 'Unknown')
        self.name_label = ctk.CTkLabel(
            info_frame,
            text=name[:30] + "..." if len(name) > 30 else name,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        self.name_label.pack(anchor="w")
        
        # UUID
        uuid = self.profile_data.get('uuid', '')[:20]
        self.uuid_label = ctk.CTkLabel(
            info_frame,
            text=f"ID: {uuid}...",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=COLORS["text_secondary"]
        )
        self.uuid_label.pack(anchor="w")
        
        # Status
        status = self.profile_data.get('status') or 'NOSTATUS'
        check_open = self.profile_data.get('check_open', 0)
        self.is_running = check_open == 1
        status_text = "RUNNING" if self.is_running else status.upper()
        status_color = COLORS["success"] if self.is_running else COLORS["text_secondary"]
        self.status_label = ctk.CTkLabel(
            info_frame,
            text=f"● {status_text}",
            font=ctk.CTkFont(size=11),
            text_color=status_color
        )
        self.status_label.pack(anchor="w")
        
        # Folder info
        folder_name = self.profile_data.get('folder_name', '')
        if folder_name:
            folder_label = ctk.CTkLabel(
                info_frame,
                text=f"📁 {folder_name}",
                font=ctk.CTkFont(size=10),
                text_color=COLORS["accent"]
            )
            folder_label.pack(anchor="w")
        
        # Action buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.place(relx=1.0, x=-15, y=30, anchor="ne")
        
        # Toggle Open/Close button
        if self.is_running:
            btn_text = "■ Đóng"
            btn_color = COLORS["error"]
            btn_hover = "#ff4757"
        else:
            btn_text = "▶ Mở"
            btn_color = COLORS["success"]
            btn_hover = "#00f5b5"
            
        self.toggle_btn = ctk.CTkButton(
            btn_frame,
            text=btn_text,
            width=80,
            height=32,
            fg_color=btn_color,
            hover_color=btn_hover,
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._on_toggle_click
        )
        self.toggle_btn.pack(side="left", padx=3)
        
        # Edit button
        self.edit_btn = ctk.CTkButton(
            btn_frame,
            text="✏️",
            width=35,
            height=32,
            fg_color=COLORS["warning"],
            hover_color="#ffda3d",
            corner_radius=8,
            command=lambda: self.on_edit(self.profile_data) if self.on_edit else None
        )
        self.edit_btn.pack(side="left", padx=3)
    
    def _on_toggle_click(self):
        """Xử lý toggle mở/đóng"""
        if self.on_toggle:
            self.on_toggle(self.profile_data, not self.is_running)
    
    def _on_click(self, event):
        pass
    
    def _on_enter(self, event):
        self.configure(border_color=COLORS["accent"])
    
    def _on_leave(self, event):
        if not self.is_selected:
            self.configure(border_color=COLORS["border"])
    
    def _on_checkbox_change(self):
        self.is_selected = self.checkbox_var.get()
        if self.is_selected:
            self.configure(border_color=COLORS["accent"])
        else:
            self.configure(border_color=COLORS["border"])
        if self.on_select:
            self.on_select(self.profile_data, self.is_selected)


class PostCard(ctk.CTkFrame):
    """Card hiển thị bài đăng"""
    def __init__(self, master, post_data: Dict,
                 on_like: Callable = None,
                 on_comment: Callable = None,
                 on_delete: Callable = None,
                 **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_card"],
            corner_radius=12,
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
        # URL
        url = self.post_data.get('url', '')
        url_display = url[:60] + "..." if len(url) > 60 else url
        
        self.url_label = ctk.CTkLabel(
            self,
            text=f"🔗 {url_display}",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["accent"],
            cursor="hand2"
        )
        self.url_label.pack(anchor="w", padx=15, pady=(12, 5))
        
        # Title/Description
        title = self.post_data.get('title', 'Không có tiêu đề')
        self.title_label = ctk.CTkLabel(
            self,
            text=title[:80] + "..." if len(title) > 80 else title,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        self.title_label.pack(anchor="w", padx=15, pady=2)
        
        # Stats and buttons frame
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=15, pady=(5, 12))
        
        # Stats
        stats_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        stats_frame.pack(side="left")
        
        like_count = self.post_data.get('like_count', 0)
        comment_count = self.post_data.get('comment_count', 0)
        
        ctk.CTkLabel(
            stats_frame,
            text=f"❤️ {like_count}",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["accent"]
        ).pack(side="left", padx=(0, 15))
        
        ctk.CTkLabel(
            stats_frame,
            text=f"💬 {comment_count}",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        ).pack(side="left")
        
        # Action buttons
        btn_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        btn_frame.pack(side="right")
        
        ctk.CTkButton(
            btn_frame,
            text="❤️ Like",
            width=80,
            height=28,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            corner_radius=8,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda: self.on_like(self.post_data) if self.on_like else None
        ).pack(side="left", padx=3)
        
        ctk.CTkButton(
            btn_frame,
            text="💬 Comment",
            width=90,
            height=28,
            fg_color=COLORS["success"],
            hover_color="#00f5b5",
            corner_radius=8,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda: self.on_comment(self.post_data) if self.on_comment else None
        ).pack(side="left", padx=3)
        
        ctk.CTkButton(
            btn_frame,
            text="🗑️",
            width=35,
            height=28,
            fg_color=COLORS["error"],
            hover_color="#ff4757",
            corner_radius=8,
            command=lambda: self.on_delete(self.post_data) if self.on_delete else None
        ).pack(side="left", padx=3)


class ScriptCard(ctk.CTkFrame):
    """Card hiển thị kịch bản"""
    def __init__(self, master, script_data: Dict,
                 on_edit: Callable = None,
                 on_run: Callable = None,
                 on_delete: Callable = None,
                 **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_card"],
            corner_radius=12,
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
        # Icon + Name
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(12, 5))
        
        ctk.CTkLabel(
            header_frame,
            text="📜",
            font=ctk.CTkFont(size=24)
        ).pack(side="left", padx=(0, 10))
        
        name = self.script_data.get('name', 'Untitled Script')
        ctk.CTkLabel(
            header_frame,
            text=name,
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left")
        
        # Description
        desc = self.script_data.get('description', '')
        if desc:
            ctk.CTkLabel(
                self,
                text=desc[:100] + "..." if len(desc) > 100 else desc,
                font=ctk.CTkFont(size=12),
                text_color=COLORS["text_secondary"]
            ).pack(anchor="w", padx=15, pady=2)
        
        # Updated time
        updated = self.script_data.get('updated_at', '')
        if updated:
            ctk.CTkLabel(
                self,
                text=f"🕐 {updated[:19]}",
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text_secondary"]
            ).pack(anchor="w", padx=15, pady=(2, 5))
        
        # Action buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=(5, 12))
        
        ctk.CTkButton(
            btn_frame,
            text="▶ Chạy",
            width=80,
            height=30,
            fg_color=COLORS["success"],
            hover_color="#00f5b5",
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self.on_run(self.script_data) if self.on_run else None
        ).pack(side="left", padx=3)
        
        ctk.CTkButton(
            btn_frame,
            text="✏️ Sửa",
            width=80,
            height=30,
            fg_color=COLORS["warning"],
            hover_color="#ffda3d",
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self.on_edit(self.script_data) if self.on_edit else None
        ).pack(side="left", padx=3)
        
        ctk.CTkButton(
            btn_frame,
            text="🗑️ Xóa",
            width=80,
            height=30,
            fg_color=COLORS["error"],
            hover_color="#ff4757",
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self.on_delete(self.script_data) if self.on_delete else None
        ).pack(side="left", padx=3)


class StatusBar(ctk.CTkFrame):
    """Status bar ở cuối ứng dụng"""
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_secondary"],
            height=30,
            corner_radius=0,
            **kwargs
        )
        
        self.pack_propagate(False)
        
        self.status_label = ctk.CTkLabel(
            self,
            text="● Sẵn sàng",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["success"]
        )
        self.status_label.pack(side="left", padx=15)
        
        self.info_label = ctk.CTkLabel(
            self,
            text="FB Manager Pro v1.0.0",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"]
        )
        self.info_label.pack(side="right", padx=15)
    
    def set_status(self, text: str, status_type: str = "info"):
        colors = {
            "success": COLORS["success"],
            "error": COLORS["error"],
            "warning": COLORS["warning"],
            "info": COLORS["text_secondary"]
        }
        color = colors.get(status_type, COLORS["text_secondary"])
        self.status_label.configure(text=f"● {text}", text_color=color)


class SearchBar(ctk.CTkFrame):
    """Thanh tìm kiếm"""
    def __init__(self, master, placeholder: str = "Tìm kiếm...", on_search: Callable = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.on_search = on_search
        
        self.search_entry = ModernEntry(
            self,
            placeholder=placeholder,
            width=300
        )
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind("<Return>", self._do_search)
        
        self.search_btn = ctk.CTkButton(
            self,
            text="🔍",
            width=40,
            height=40,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            corner_radius=10,
            command=self._do_search
        )
        self.search_btn.pack(side="left")
    
    def _do_search(self, event=None):
        if self.on_search:
            self.on_search(self.search_entry.get())
    
    def get_value(self) -> str:
        return self.search_entry.get()
