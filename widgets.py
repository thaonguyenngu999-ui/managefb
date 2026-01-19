"""
Custom Widgets - FB Manager Pro
Cyberpunk UI components
"""
import customtkinter as ctk
from typing import Callable, Optional, List, Dict
from config import COLORS, FONTS, SPACING, RADIUS, HEIGHTS, TAB_COLORS


class ModernCard(ctk.CTkFrame):
    """Card component - Cyberpunk style"""
    def __init__(self, master, title: str = "", **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=COLORS["border"],
            **kwargs
        )

        if title:
            self.title_label = ctk.CTkLabel(
                self,
                text=title,
                font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_base"], weight="bold"),
                text_color=COLORS["text_primary"]
            )
            self.title_label.pack(anchor="w", padx=12, pady=(10, 6))


class ModernButton(ctk.CTkButton):
    """Button component - Cyberpunk neon style"""
    def __init__(self, master, text: str, variant: str = "primary", icon: str = None, size: str = "md", **kwargs):
        # Color mappings for cyberpunk
        colors = {
            "primary": (COLORS["neon_cyan"], COLORS["primary_hover"], COLORS["bg_dark"]),
            "secondary": (COLORS["neon_magenta"], COLORS["secondary_hover"], COLORS["text_primary"]),
            "success": (COLORS["neon_green"], COLORS["success_hover"], COLORS["bg_dark"]),
            "warning": (COLORS["neon_yellow"], COLORS["warning"], COLORS["bg_dark"]),
            "danger": (COLORS["neon_red"], COLORS["error_hover"], COLORS["text_primary"]),
            "ghost": (COLORS["bg_card"], COLORS["bg_hover"], COLORS["text_primary"])
        }

        fg, hover, txt = colors.get(variant, colors["primary"])

        # Size configs
        sizes = {
            "sm": {"height": HEIGHTS["button_sm"], "font_size": FONTS["size_xs"]},
            "md": {"height": HEIGHTS["button"], "font_size": FONTS["size_sm"]},
            "lg": {"height": HEIGHTS["button_lg"], "font_size": FONTS["size_base"]},
        }
        size_config = sizes.get(size, sizes["md"])

        super().__init__(
            master,
            text=f"{icon} {text}" if icon else text,
            fg_color=fg,
            hover_color=hover,
            corner_radius=RADIUS["md"],
            font=ctk.CTkFont(family=FONTS["family"], size=size_config["font_size"], weight="bold"),
            text_color=txt,
            height=size_config["height"],
            **kwargs
        )


class ModernEntry(ctk.CTkEntry):
    """Entry field component - Cyberpunk style"""
    def __init__(self, master, placeholder: str = "", **kwargs):
        super().__init__(
            master,
            placeholder_text=placeholder,
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            placeholder_text_color=COLORS["text_muted"],
            corner_radius=RADIUS["md"],
            height=HEIGHTS["input"],
            font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_sm"]),
            border_width=1,
            **kwargs
        )

        # Focus effects
        self.bind("<FocusIn>", lambda e: self.configure(border_color=COLORS["neon_cyan"]))
        self.bind("<FocusOut>", lambda e: self.configure(border_color=COLORS["border"]))


class ModernTextbox(ctk.CTkTextbox):
    """Textbox component - Cyberpunk style"""
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            corner_radius=RADIUS["md"],
            font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_sm"]),
            border_width=1,
            **kwargs
        )


class Badge(ctk.CTkFrame):
    """Badge component with LED indicator - Cyberpunk style"""
    def __init__(self, master, text: str, color: str = "cyan", show_led: bool = False, pulse: bool = False, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        color_map = {
            "cyan": COLORS["neon_cyan"],
            "green": COLORS["neon_green"],
            "purple": COLORS["neon_purple"],
            "yellow": COLORS["neon_yellow"],
            "gray": COLORS["text_muted"],
            "red": COLORS["neon_red"],
            "magenta": COLORS["neon_magenta"],
            "orange": COLORS["neon_orange"],
        }
        accent = color_map.get(color, COLORS["neon_cyan"])

        # Inner frame
        inner = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_secondary"],
            corner_radius=RADIUS["md"]
        )
        inner.pack()

        # Border left effect
        border = ctk.CTkFrame(inner, width=3, fg_color=accent, corner_radius=0)
        border.pack(side="left", fill="y")

        content = ctk.CTkFrame(inner, fg_color="transparent")
        content.pack(side="left", padx=(8, 12), pady=6)

        # LED indicator
        if show_led:
            self.led = ctk.CTkLabel(
                content,
                text="●",
                font=ctk.CTkFont(size=8),
                text_color=accent
            )
            self.led.pack(side="left", padx=(0, 6))

            if pulse:
                self._start_pulse(accent)

        # Text
        ctk.CTkLabel(
            content,
            text=text,
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_xs"], weight="bold"),
            text_color=accent
        ).pack(side="left")

    def _start_pulse(self, color):
        """LED pulse animation"""
        self._pulse_on = True

        def pulse():
            if not hasattr(self, 'led'):
                return
            try:
                if self._pulse_on:
                    self.led.configure(text_color=color)
                else:
                    self.led.configure(text_color=COLORS["bg_dark"])
                self._pulse_on = not self._pulse_on
                self.after(750, pulse)
            except:
                pass

        pulse()


class EmptyState(ctk.CTkFrame):
    """Empty state component - Cyberpunk style"""
    def __init__(self, master, icon: str = "", title: str = "", description: str = "",
                 action_text: str = None, on_action: Callable = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        # Icon
        if icon:
            ctk.CTkLabel(
                self,
                text=icon,
                font=ctk.CTkFont(size=48),
                text_color=COLORS["neon_cyan"]
            ).pack(pady=(SPACING["2xl"], SPACING["md"]))

        # Title
        if title:
            ctk.CTkLabel(
                self,
                text=title,
                font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_xl"], weight="bold"),
                text_color=COLORS["text_primary"]
            ).pack(pady=(0, SPACING["sm"]))

        # Description
        if description:
            ctk.CTkLabel(
                self,
                text=description,
                font=ctk.CTkFont(size=FONTS["size_base"]),
                text_color=COLORS["text_muted"]
            ).pack(pady=(0, SPACING["lg"]))

        # Action button
        if action_text and on_action:
            ModernButton(
                self,
                text=action_text,
                variant="primary",
                command=on_action,
                width=150
            ).pack()


class ProfileCard(ctk.CTkFrame):
    """Profile card - Cyberpunk compact style"""
    def __init__(self, master, profile_data: Dict,
                 on_toggle: Callable = None,
                 on_edit: Callable = None,
                 on_select: Callable = None,
                 **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=COLORS["border"],
            height=80,
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
            fg_color=COLORS["neon_cyan"],
            hover_color=COLORS["primary_hover"],
            border_color=COLORS["border"],
            command=self._on_checkbox_change
        )
        self.checkbox.place(x=12, y=30)

        # Avatar
        self.avatar = ctk.CTkLabel(
            self,
            text="◢",
            font=ctk.CTkFont(size=24),
            text_color=COLORS["neon_cyan"] if self.is_running else COLORS["text_muted"],
            width=32,
            height=32
        )
        self.avatar.place(x=44, y=24)

        # Info
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.place(x=86, y=16)

        # Name
        name = self.profile_data.get('name', 'Unknown')
        ctk.CTkLabel(
            info_frame,
            text=name[:24] + "..." if len(name) > 24 else name,
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_base"], weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")

        # UUID + Status
        meta_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        meta_frame.pack(anchor="w", pady=(2, 0))

        uuid = self.profile_data.get('uuid', '')[:10]
        ctk.CTkLabel(
            meta_frame,
            text=f"{uuid}...",
            font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_xs"]),
            text_color=COLORS["text_muted"]
        ).pack(side="left")

        # Status indicator
        status_color = COLORS["neon_green"] if self.is_running else COLORS["text_tertiary"]
        status_text = "● RUNNING" if self.is_running else "● STOPPED"
        self.status_label = ctk.CTkLabel(
            meta_frame,
            text=f"  {status_text}",
            font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_xs"]),
            text_color=status_color
        )
        self.status_label.pack(side="left")

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.place(relx=1.0, x=-12, y=26, anchor="ne")

        if self.is_running:
            btn_text = "Dung"
            btn_color = COLORS["neon_red"]
            btn_hover = COLORS["error_hover"]
            txt_color = COLORS["text_primary"]
        else:
            btn_text = "Mo"
            btn_color = COLORS["neon_green"]
            btn_hover = COLORS["success_hover"]
            txt_color = COLORS["bg_dark"]

        self.toggle_btn = ctk.CTkButton(
            btn_frame,
            text=btn_text,
            width=60,
            height=28,
            fg_color=btn_color,
            hover_color=btn_hover,
            corner_radius=RADIUS["md"],
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_xs"], weight="bold"),
            text_color=txt_color,
            command=self._on_toggle_click
        )
        self.toggle_btn.pack(side="left", padx=2)

        self.edit_btn = ctk.CTkButton(
            btn_frame,
            text="Edit",
            width=50,
            height=28,
            fg_color=COLORS["bg_secondary"],
            hover_color=COLORS["bg_hover"],
            corner_radius=RADIUS["md"],
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_xs"]),
            text_color=COLORS["text_secondary"],
            command=lambda: self.on_edit(self.profile_data) if self.on_edit else None
        )
        self.edit_btn.pack(side="left", padx=2)

    def _on_toggle_click(self):
        if self.on_toggle:
            self.on_toggle(self.profile_data, not self.is_running)

    def _on_enter(self, event):
        self.configure(border_color=COLORS["neon_cyan"])

    def _on_leave(self, event):
        if not self.is_selected:
            self.configure(border_color=COLORS["border"])

    def _on_checkbox_change(self):
        self.is_selected = self.checkbox_var.get()
        self.configure(border_color=COLORS["neon_cyan"] if self.is_selected else COLORS["border"])
        if self.on_select:
            self.on_select(self.profile_data, self.is_selected)


class PostCard(ctk.CTkFrame):
    """Post card - Cyberpunk compact style"""
    def __init__(self, master, post_data: Dict,
                 on_like: Callable = None,
                 on_comment: Callable = None,
                 on_delete: Callable = None,
                 **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["lg"],
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
        url_display = url[:50] + "..." if len(url) > 50 else url

        self.url_label = ctk.CTkLabel(
            self,
            text=f"// {url_display}",
            font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_sm"]),
            text_color=COLORS["neon_cyan"],
            cursor="hand2"
        )
        self.url_label.pack(anchor="w", padx=12, pady=(12, 4))

        # Title
        title = self.post_data.get('title', 'No title')
        self.title_label = ctk.CTkLabel(
            self,
            text=title[:70] + "..." if len(title) > 70 else title,
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_base"], weight="bold"),
            text_color=COLORS["text_primary"]
        )
        self.title_label.pack(anchor="w", padx=12, pady=2)

        # Stats and buttons
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=12, pady=(4, 12))

        # Stats
        stats_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        stats_frame.pack(side="left")

        like_count = self.post_data.get('like_count', 0)
        comment_count = self.post_data.get('comment_count', 0)

        ctk.CTkLabel(
            stats_frame,
            text=f"♥ {like_count}",
            font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_sm"]),
            text_color=COLORS["neon_magenta"]
        ).pack(side="left", padx=(0, 12))

        ctk.CTkLabel(
            stats_frame,
            text=f"◆ {comment_count}",
            font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_sm"]),
            text_color=COLORS["text_muted"]
        ).pack(side="left")

        # Action buttons
        btn_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        btn_frame.pack(side="right")

        ModernButton(
            btn_frame,
            text="Like",
            variant="secondary",
            size="sm",
            width=60,
            command=lambda: self.on_like(self.post_data) if self.on_like else None
        ).pack(side="left", padx=2)

        ModernButton(
            btn_frame,
            text="Comment",
            variant="primary",
            size="sm",
            width=80,
            command=lambda: self.on_comment(self.post_data) if self.on_comment else None
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            btn_frame,
            text="X",
            width=28,
            height=HEIGHTS["button_sm"],
            fg_color=COLORS["bg_secondary"],
            hover_color=COLORS["neon_red"],
            corner_radius=RADIUS["md"],
            font=ctk.CTkFont(size=FONTS["size_sm"]),
            text_color=COLORS["text_muted"],
            command=lambda: self.on_delete(self.post_data) if self.on_delete else None
        ).pack(side="left", padx=2)


class ScriptCard(ctk.CTkFrame):
    """Script card - Cyberpunk compact style"""
    def __init__(self, master, script_data: Dict,
                 on_edit: Callable = None,
                 on_run: Callable = None,
                 on_delete: Callable = None,
                 **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["lg"],
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
        header_frame.pack(fill="x", padx=12, pady=(12, 4))

        ctk.CTkLabel(
            header_frame,
            text="◢",
            font=ctk.CTkFont(size=20),
            text_color=COLORS["neon_cyan"]
        ).pack(side="left", padx=(0, 8))

        name = self.script_data.get('name', 'Untitled Script')
        ctk.CTkLabel(
            header_frame,
            text=name,
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_base"], weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left")

        # Description
        desc = self.script_data.get('description', '')
        if desc:
            ctk.CTkLabel(
                self,
                text=desc[:80] + "..." if len(desc) > 80 else desc,
                font=ctk.CTkFont(size=FONTS["size_sm"]),
                text_color=COLORS["text_muted"]
            ).pack(anchor="w", padx=12, pady=2)

        # Action buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=12, pady=(4, 12))

        ModernButton(
            btn_frame,
            text="RUN",
            variant="success",
            size="sm",
            width=70,
            command=lambda: self.on_run(self.script_data) if self.on_run else None
        ).pack(side="left", padx=2)

        ModernButton(
            btn_frame,
            text="Edit",
            variant="ghost",
            size="sm",
            width=60,
            command=lambda: self.on_edit(self.script_data) if self.on_edit else None
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            btn_frame,
            text="X",
            width=28,
            height=HEIGHTS["button_sm"],
            fg_color=COLORS["bg_secondary"],
            hover_color=COLORS["neon_red"],
            corner_radius=RADIUS["md"],
            font=ctk.CTkFont(size=FONTS["size_sm"]),
            text_color=COLORS["text_muted"],
            command=lambda: self.on_delete(self.script_data) if self.on_delete else None
        ).pack(side="left", padx=2)


class StatusBar(ctk.CTkFrame):
    """Status bar - Cyberpunk style"""
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_header"],
            height=HEIGHTS["status_bar"],
            corner_radius=0,
            **kwargs
        )

        self.pack_propagate(False)

        self.status_label = ctk.CTkLabel(
            self,
            text="● READY",
            font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_xs"]),
            text_color=COLORS["neon_green"]
        )
        self.status_label.pack(side="left", padx=16)

        self.info_label = ctk.CTkLabel(
            self,
            text="FB Manager Pro v2.0.77",
            font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_xs"]),
            text_color=COLORS["text_muted"]
        )
        self.info_label.pack(side="right", padx=16)

    def set_status(self, text: str, status_type: str = "info"):
        colors = {
            "success": COLORS["neon_green"],
            "error": COLORS["neon_red"],
            "warning": COLORS["neon_yellow"],
            "info": COLORS["neon_cyan"]
        }
        self.status_label.configure(
            text=f"● {text.upper()}",
            text_color=colors.get(status_type, colors["info"])
        )


class SearchBar(ctk.CTkFrame):
    """Search bar - Cyberpunk style"""
    def __init__(self, master, placeholder: str = "Search...", on_search: Callable = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.on_search = on_search

        self.search_entry = ModernEntry(
            self,
            placeholder=placeholder,
            width=250
        )
        self.search_entry.pack(side="left", padx=(0, 8))
        self.search_entry.bind("<Return>", self._do_search)

        self.search_btn = ctk.CTkButton(
            self,
            text="SCAN",
            width=60,
            height=HEIGHTS["input"],
            fg_color=COLORS["neon_cyan"],
            hover_color=COLORS["primary_hover"],
            corner_radius=RADIUS["md"],
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_xs"], weight="bold"),
            text_color=COLORS["bg_dark"],
            command=self._do_search
        )
        self.search_btn.pack(side="left")

    def _do_search(self, event=None):
        if self.on_search:
            self.on_search(self.search_entry.get())

    def get_value(self) -> str:
        return self.search_entry.get()
