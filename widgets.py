"""
Clean UI Widgets - FB Manager Pro
Simple, clean design without emoji icons
"""
import customtkinter as ctk
from typing import Callable, Optional, Dict
from config import COLORS, FONTS, SPACING, RADIUS, HEIGHTS


# ============================================================
# MODERN BUTTON - Clean Design
# ============================================================
class ModernButton(ctk.CTkButton):
    """Clean button with multiple variants"""

    VARIANTS = {
        "primary": {
            "fg": COLORS["accent"],
            "hover": COLORS["accent_hover"],
            "text": "#ffffff"
        },
        "secondary": {
            "fg": COLORS["bg_elevated"],
            "hover": COLORS["border_hover"],
            "text": COLORS["text_primary"]
        },
        "success": {
            "fg": COLORS["success"],
            "hover": COLORS["success_hover"],
            "text": "#ffffff"
        },
        "warning": {
            "fg": COLORS["warning"],
            "hover": COLORS["warning_hover"],
            "text": "#000000"
        },
        "danger": {
            "fg": COLORS["error"],
            "hover": COLORS["error_hover"],
            "text": "#ffffff"
        },
        "ghost": {
            "fg": "transparent",
            "hover": COLORS["bg_card"],
            "text": COLORS["text_secondary"]
        },
        "outline": {
            "fg": "transparent",
            "hover": COLORS["accent"],
            "text": COLORS["accent"]
        }
    }

    def __init__(
        self,
        master,
        text: str,
        variant: str = "primary",
        icon: str = None,  # Ignored - no icons
        size: str = "md",
        **kwargs
    ):
        style = self.VARIANTS.get(variant, self.VARIANTS["primary"])

        sizes = {
            "sm": {"height": HEIGHTS["button_sm"], "font_size": FONTS["size_sm"]},
            "md": {"height": HEIGHTS["button_md"], "font_size": FONTS["size_base"]},
            "lg": {"height": HEIGHTS["button_lg"], "font_size": FONTS["size_md"]}
        }
        size_config = sizes.get(size, sizes["md"])

        super().__init__(
            master,
            text=text,
            fg_color=style["fg"],
            hover_color=style["hover"],
            text_color=style["text"],
            corner_radius=RADIUS["md"],
            font=ctk.CTkFont(
                family=FONTS["family"],
                size=size_config["font_size"],
                weight="bold"
            ),
            height=size_config["height"],
            border_width=1 if variant == "outline" else 0,
            border_color=COLORS["accent"] if variant == "outline" else None,
            **kwargs
        )


# ============================================================
# MODERN INPUT
# ============================================================
class ModernEntry(ctk.CTkEntry):
    """Clean text input"""

    def __init__(self, master, placeholder: str = "", **kwargs):
        kwargs.setdefault("height", HEIGHTS["input"])
        kwargs.setdefault("corner_radius", RADIUS["md"])

        super().__init__(
            master,
            placeholder_text=placeholder,
            fg_color=COLORS["bg_secondary"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            placeholder_text_color=COLORS["text_tertiary"],
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_base"]),
            border_width=1,
            **kwargs
        )

        self.bind("<FocusIn>", lambda e: self.configure(border_color=COLORS["accent"]))
        self.bind("<FocusOut>", lambda e: self.configure(border_color=COLORS["border"]))


# ============================================================
# MODERN TEXTBOX
# ============================================================
class ModernTextbox(ctk.CTkTextbox):
    """Clean multi-line text editor"""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("corner_radius", RADIUS["md"])
        kwargs.setdefault("border_width", 1)

        super().__init__(
            master,
            fg_color=COLORS["bg_secondary"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_base"]),
            **kwargs
        )

        self.bind("<FocusIn>", lambda e: self.configure(border_color=COLORS["accent"]))
        self.bind("<FocusOut>", lambda e: self.configure(border_color=COLORS["border"]))


# ============================================================
# PROFILE CARD - Clean Design
# ============================================================
class ProfileCard(ctk.CTkFrame):
    """Clean profile card"""

    def __init__(
        self,
        master,
        profile_data: Dict,
        on_toggle: Callable = None,
        on_edit: Callable = None,
        on_select: Callable = None,
        **kwargs
    ):
        kwargs.setdefault("fg_color", COLORS["bg_card"])
        kwargs.setdefault("corner_radius", RADIUS["lg"])
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", COLORS["border"])
        kwargs.setdefault("height", HEIGHTS["card_profile"])

        super().__init__(master, **kwargs)

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
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=SPACING["md"], pady=SPACING["sm"])

        # Left: Checkbox + Avatar
        left = ctk.CTkFrame(content, fg_color="transparent")
        left.pack(side="left", fill="y")

        self.checkbox_var = ctk.BooleanVar(value=False)
        self.checkbox = ctk.CTkCheckBox(
            left,
            text="",
            variable=self.checkbox_var,
            width=20,
            checkbox_width=18,
            checkbox_height=18,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            border_color=COLORS["border"],
            corner_radius=RADIUS["xs"],
            command=self._on_checkbox_change
        )
        self.checkbox.pack(side="left", padx=(0, SPACING["sm"]))

        # Avatar - simple circle with initial
        avatar = ctk.CTkFrame(
            left,
            width=44,
            height=44,
            corner_radius=22,
            fg_color=COLORS["accent"]
        )
        avatar.pack(side="left")
        avatar.pack_propagate(False)

        name = self.profile_data.get('name', 'U')
        initial = name[0].upper() if name else 'U'
        ctk.CTkLabel(
            avatar,
            text=initial,
            font=ctk.CTkFont(size=FONTS["size_lg"], weight="bold"),
            text_color="#ffffff"
        ).place(relx=0.5, rely=0.5, anchor="center")

        # Middle: Info
        info = ctk.CTkFrame(content, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=SPACING["md"])

        # Name
        name_display = self.profile_data.get('name', 'Unknown')
        if len(name_display) > 30:
            name_display = name_display[:30] + "..."

        self.name_label = ctk.CTkLabel(
            info,
            text=name_display,
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_md"], weight="bold"),
            text_color=COLORS["text_primary"],
            anchor="w"
        )
        self.name_label.pack(anchor="w")

        # UUID
        uuid_display = self.profile_data.get('uuid', '')[:20] + "..."
        ctk.CTkLabel(
            info,
            text=uuid_display,
            font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_xs"]),
            text_color=COLORS["text_tertiary"],
            anchor="w"
        ).pack(anchor="w")

        # Status
        status_color = COLORS["success"] if self.is_running else COLORS["text_tertiary"]
        status_text = "RUNNING" if self.is_running else "STOPPED"

        self.status_label = ctk.CTkLabel(
            info,
            text=status_text,
            font=ctk.CTkFont(size=FONTS["size_xs"], weight="bold"),
            text_color=status_color
        )
        self.status_label.pack(anchor="w", pady=(SPACING["xs"], 0))

        # Right: Actions
        actions = ctk.CTkFrame(content, fg_color="transparent")
        actions.pack(side="right", fill="y")

        # Toggle button
        if self.is_running:
            btn_text = "Dung"
            btn_color = COLORS["error"]
            btn_hover = COLORS["error_hover"]
        else:
            btn_text = "Mo"
            btn_color = COLORS["success"]
            btn_hover = COLORS["success_hover"]

        self.toggle_btn = ctk.CTkButton(
            actions,
            text=btn_text,
            width=70,
            height=HEIGHTS["button_sm"],
            fg_color=btn_color,
            hover_color=btn_hover,
            corner_radius=RADIUS["md"],
            font=ctk.CTkFont(size=FONTS["size_sm"], weight="bold"),
            command=self._on_toggle_click
        )
        self.toggle_btn.pack(side="left", padx=SPACING["xs"])

        # Edit button
        self.edit_btn = ctk.CTkButton(
            actions,
            text="Edit",
            width=50,
            height=HEIGHTS["button_sm"],
            fg_color=COLORS["bg_elevated"],
            hover_color=COLORS["border_hover"],
            corner_radius=RADIUS["md"],
            font=ctk.CTkFont(size=FONTS["size_sm"]),
            command=lambda: self.on_edit(self.profile_data) if self.on_edit else None
        )
        self.edit_btn.pack(side="left", padx=SPACING["xs"])

    def _on_toggle_click(self):
        if self.on_toggle:
            self.on_toggle(self.profile_data, not self.is_running)

    def _on_checkbox_change(self):
        self.is_selected = self.checkbox_var.get()
        if self.is_selected:
            self.configure(border_color=COLORS["accent"])
        else:
            self.configure(border_color=COLORS["border"])
        if self.on_select:
            self.on_select(self.profile_data, self.is_selected)

    def _on_enter(self, event):
        if not self.is_selected:
            self.configure(fg_color=COLORS["bg_card_hover"])

    def _on_leave(self, event):
        if not self.is_selected:
            self.configure(fg_color=COLORS["bg_card"])


# ============================================================
# POST CARD
# ============================================================
class PostCard(ctk.CTkFrame):
    """Clean post card"""

    def __init__(
        self,
        master,
        post_data: Dict,
        on_like: Callable = None,
        on_comment: Callable = None,
        on_delete: Callable = None,
        **kwargs
    ):
        kwargs.setdefault("fg_color", COLORS["bg_card"])
        kwargs.setdefault("corner_radius", RADIUS["lg"])
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", COLORS["border"])

        super().__init__(master, **kwargs)

        self.post_data = post_data
        self.on_like = on_like
        self.on_comment = on_comment
        self.on_delete = on_delete

        self._create_widgets()

        self.bind("<Enter>", lambda e: self.configure(fg_color=COLORS["bg_card_hover"]))
        self.bind("<Leave>", lambda e: self.configure(fg_color=COLORS["bg_card"]))

    def _create_widgets(self):
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="x", padx=SPACING["lg"], pady=SPACING["md"])

        # URL
        url = self.post_data.get('url', '')
        url_display = url[:55] + "..." if len(url) > 55 else url

        ctk.CTkLabel(
            content,
            text=url_display,
            font=ctk.CTkFont(size=FONTS["size_sm"]),
            text_color=COLORS["text_link"],
            cursor="hand2"
        ).pack(anchor="w")

        # Title
        title = self.post_data.get('title', 'No title')
        title_display = title[:70] + "..." if len(title) > 70 else title

        ctk.CTkLabel(
            content,
            text=title_display,
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_md"], weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", pady=(SPACING["xs"], 0))

        # Bottom: Stats + Actions
        bottom = ctk.CTkFrame(content, fg_color="transparent")
        bottom.pack(fill="x", pady=(SPACING["sm"], 0))

        # Stats
        like_count = self.post_data.get('like_count', 0)
        comment_count = self.post_data.get('comment_count', 0)

        ctk.CTkLabel(
            bottom,
            text=f"Likes: {like_count}  |  Comments: {comment_count}",
            font=ctk.CTkFont(size=FONTS["size_xs"]),
            text_color=COLORS["text_secondary"]
        ).pack(side="left")

        # Actions
        actions = ctk.CTkFrame(bottom, fg_color="transparent")
        actions.pack(side="right")

        ModernButton(
            actions,
            text="Like",
            variant="danger",
            size="sm",
            width=60,
            command=lambda: self.on_like(self.post_data) if self.on_like else None
        ).pack(side="left", padx=2)

        ModernButton(
            actions,
            text="Comment",
            variant="primary",
            size="sm",
            width=80,
            command=lambda: self.on_comment(self.post_data) if self.on_comment else None
        ).pack(side="left", padx=2)

        ModernButton(
            actions,
            text="X",
            variant="ghost",
            size="sm",
            width=30,
            command=lambda: self.on_delete(self.post_data) if self.on_delete else None
        ).pack(side="left", padx=2)


# ============================================================
# SCRIPT CARD
# ============================================================
class ScriptCard(ctk.CTkFrame):
    """Clean script card"""

    def __init__(
        self,
        master,
        script_data: Dict,
        on_edit: Callable = None,
        on_run: Callable = None,
        on_delete: Callable = None,
        **kwargs
    ):
        kwargs.setdefault("fg_color", COLORS["bg_card"])
        kwargs.setdefault("corner_radius", RADIUS["lg"])
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", COLORS["border"])

        super().__init__(master, **kwargs)

        self.script_data = script_data
        self.on_edit = on_edit
        self.on_run = on_run
        self.on_delete = on_delete

        self._create_widgets()

        self.bind("<Enter>", lambda e: self.configure(fg_color=COLORS["bg_card_hover"]))
        self.bind("<Leave>", lambda e: self.configure(fg_color=COLORS["bg_card"]))

    def _create_widgets(self):
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="x", padx=SPACING["lg"], pady=SPACING["md"])

        # Header
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x")

        # Name
        name = self.script_data.get('name', 'Untitled Script')
        ctk.CTkLabel(
            header,
            text=name,
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_md"], weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left")

        # Description
        desc = self.script_data.get('description', '')
        if desc:
            desc_display = desc[:80] + "..." if len(desc) > 80 else desc
            ctk.CTkLabel(
                content,
                text=desc_display,
                font=ctk.CTkFont(size=FONTS["size_sm"]),
                text_color=COLORS["text_secondary"]
            ).pack(anchor="w", pady=(SPACING["xs"], 0))

        # Actions
        actions = ctk.CTkFrame(content, fg_color="transparent")
        actions.pack(fill="x", pady=(SPACING["md"], 0))

        ModernButton(
            actions,
            text="Run",
            variant="success",
            size="sm",
            width=70,
            command=lambda: self.on_run(self.script_data) if self.on_run else None
        ).pack(side="left", padx=2)

        ModernButton(
            actions,
            text="Edit",
            variant="secondary",
            size="sm",
            width=60,
            command=lambda: self.on_edit(self.script_data) if self.on_edit else None
        ).pack(side="left", padx=2)

        ModernButton(
            actions,
            text="Delete",
            variant="danger",
            size="sm",
            width=70,
            command=lambda: self.on_delete(self.script_data) if self.on_delete else None
        ).pack(side="left", padx=2)


# ============================================================
# STATUS BAR
# ============================================================
class StatusBar(ctk.CTkFrame):
    """Clean status bar"""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", COLORS["bg_secondary"])
        kwargs.setdefault("height", HEIGHTS["status_bar"])
        kwargs.setdefault("corner_radius", 0)

        super().__init__(master, **kwargs)
        self.pack_propagate(False)

        # Left: Status
        self.status_label = ctk.CTkLabel(
            self,
            text="Ready",
            font=ctk.CTkFont(size=FONTS["size_sm"]),
            text_color=COLORS["success"]
        )
        self.status_label.pack(side="left", padx=SPACING["lg"])

        # Right: Version
        from config import APP_VERSION
        ctk.CTkLabel(
            self,
            text=f"FB Manager Pro v{APP_VERSION}",
            font=ctk.CTkFont(size=FONTS["size_sm"]),
            text_color=COLORS["text_tertiary"]
        ).pack(side="right", padx=SPACING["lg"])

    def set_status(self, text: str, status_type: str = "info"):
        """Update status"""
        colors = {
            "success": COLORS["success"],
            "error": COLORS["error"],
            "warning": COLORS["warning"],
            "info": COLORS["text_secondary"]
        }
        color = colors.get(status_type, COLORS["text_secondary"])
        self.status_label.configure(text=text, text_color=color)


# ============================================================
# SEARCH BAR
# ============================================================
class SearchBar(ctk.CTkFrame):
    """Clean search bar"""

    def __init__(
        self,
        master,
        placeholder: str = "Search...",
        on_search: Callable = None,
        **kwargs
    ):
        kwargs.setdefault("fg_color", COLORS["bg_secondary"])
        kwargs.setdefault("corner_radius", RADIUS["lg"])
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", COLORS["border"])

        super().__init__(master, **kwargs)

        self.on_search = on_search

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x", padx=SPACING["sm"], pady=SPACING["xs"])

        self.search_entry = ctk.CTkEntry(
            container,
            placeholder_text=placeholder,
            fg_color="transparent",
            border_width=0,
            text_color=COLORS["text_primary"],
            placeholder_text_color=COLORS["text_tertiary"],
            font=ctk.CTkFont(size=FONTS["size_base"]),
            height=32,
            width=200
        )
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<Return>", self._do_search)

        self.search_btn = ctk.CTkButton(
            container,
            text="Go",
            width=40,
            height=28,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            corner_radius=RADIUS["md"],
            font=ctk.CTkFont(size=FONTS["size_sm"]),
            command=self._do_search
        )
        self.search_btn.pack(side="right")

        self.search_entry.bind("<FocusIn>", lambda e: self.configure(border_color=COLORS["accent"]))
        self.search_entry.bind("<FocusOut>", lambda e: self.configure(border_color=COLORS["border"]))

    def _do_search(self, event=None):
        if self.on_search:
            self.on_search(self.search_entry.get())

    def get_value(self) -> str:
        return self.search_entry.get()


# ============================================================
# BADGE
# ============================================================
class Badge(ctk.CTkFrame):
    """Small badge/tag"""

    def __init__(
        self,
        master,
        text: str,
        variant: str = "default",
        **kwargs
    ):
        colors = {
            "default": (COLORS["bg_elevated"], COLORS["text_secondary"]),
            "success": (COLORS["success_bg"], COLORS["success"]),
            "warning": (COLORS["warning_bg"], COLORS["warning"]),
            "error": (COLORS["error_bg"], COLORS["error"]),
            "info": (COLORS["bg_card"], COLORS["info"]),
            "accent": (COLORS["accent"], COLORS["text_primary"])
        }

        bg, fg = colors.get(variant, colors["default"])

        kwargs.setdefault("fg_color", bg)
        kwargs.setdefault("corner_radius", RADIUS["sm"])

        super().__init__(master, **kwargs)

        ctk.CTkLabel(
            self,
            text=text,
            font=ctk.CTkFont(size=FONTS["size_xs"], weight="bold"),
            text_color=fg
        ).pack(padx=SPACING["sm"], pady=2)


# ============================================================
# EMPTY STATE
# ============================================================
class EmptyState(ctk.CTkFrame):
    """Empty state placeholder"""

    def __init__(
        self,
        master,
        icon: str = "",  # Ignored
        title: str = "No data",
        description: str = "",
        action_text: str = None,
        on_action: Callable = None,
        **kwargs
    ):
        kwargs.setdefault("fg_color", "transparent")

        super().__init__(master, **kwargs)

        # Title
        ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_lg"], weight="bold"),
            text_color=COLORS["text_secondary"]
        ).pack(pady=(SPACING["2xl"], SPACING["sm"]))

        # Description
        if description:
            ctk.CTkLabel(
                self,
                text=description,
                font=ctk.CTkFont(size=FONTS["size_base"]),
                text_color=COLORS["text_tertiary"]
            ).pack()

        # Action button
        if action_text and on_action:
            ModernButton(
                self,
                text=action_text,
                variant="primary",
                command=on_action
            ).pack(pady=SPACING["lg"])


# ============================================================
# MODERN CARD (for backwards compatibility)
# ============================================================
class ModernCard(ctk.CTkFrame):
    """Simple card container"""

    def __init__(self, master, title: str = "", subtitle: str = "", icon: str = "", **kwargs):
        kwargs.setdefault("fg_color", COLORS["bg_card"])
        kwargs.setdefault("corner_radius", RADIUS["lg"])
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", COLORS["border"])

        super().__init__(master, **kwargs)

        if title:
            header = ctk.CTkFrame(self, fg_color="transparent")
            header.pack(fill="x", padx=SPACING["lg"], pady=(SPACING["lg"], SPACING["sm"]))

            ctk.CTkLabel(
                header,
                text=title,
                font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_lg"], weight="bold"),
                text_color=COLORS["text_primary"]
            ).pack(anchor="w")

            if subtitle:
                ctk.CTkLabel(
                    header,
                    text=subtitle,
                    font=ctk.CTkFont(size=FONTS["size_sm"]),
                    text_color=COLORS["text_secondary"]
                ).pack(anchor="w")

        self.bind("<Enter>", lambda e: self.configure(fg_color=COLORS["bg_card_hover"]))
        self.bind("<Leave>", lambda e: self.configure(fg_color=COLORS["bg_card"]))


# ============================================================
# DIVIDER
# ============================================================
class Divider(ctk.CTkFrame):
    """Horizontal divider"""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", COLORS["border"])
        kwargs.setdefault("height", 1)
        super().__init__(master, **kwargs)
