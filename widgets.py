"""
Modern UI Widgets - Premium Design System for FB Manager Pro
Glassmorphism, Gradient Accents, Smooth Interactions
"""
import customtkinter as ctk
from typing import Callable, Optional, List, Dict
from config import COLORS, FONTS, SPACING, RADIUS, HEIGHTS


# ============================================================
# MODERN CARD - Glassmorphism Style
# ============================================================
class ModernCard(ctk.CTkFrame):
    """Premium card with glassmorphism effect and optional gradient border"""

    def __init__(
        self,
        master,
        title: str = "",
        subtitle: str = "",
        icon: str = "",
        gradient_border: bool = False,
        **kwargs
    ):
        # Default styling
        kwargs.setdefault("fg_color", COLORS["bg_card"])
        kwargs.setdefault("corner_radius", RADIUS["lg"])
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", COLORS["border"])

        super().__init__(master, **kwargs)

        self._gradient_border = gradient_border
        self._is_hovered = False

        # Header with icon and title
        if title or icon:
            header = ctk.CTkFrame(self, fg_color="transparent")
            header.pack(fill="x", padx=SPACING["lg"], pady=(SPACING["lg"], SPACING["sm"]))

            if icon:
                ctk.CTkLabel(
                    header,
                    text=icon,
                    font=ctk.CTkFont(size=FONTS["size_xl"]),
                    text_color=COLORS["accent"]
                ).pack(side="left", padx=(0, SPACING["sm"]))

            title_frame = ctk.CTkFrame(header, fg_color="transparent")
            title_frame.pack(side="left", fill="x", expand=True)

            if title:
                ctk.CTkLabel(
                    title_frame,
                    text=title,
                    font=ctk.CTkFont(
                        family=FONTS["family"],
                        size=FONTS["size_lg"],
                        weight="bold"
                    ),
                    text_color=COLORS["text_primary"]
                ).pack(anchor="w")

            if subtitle:
                ctk.CTkLabel(
                    title_frame,
                    text=subtitle,
                    font=ctk.CTkFont(size=FONTS["size_sm"]),
                    text_color=COLORS["text_secondary"]
                ).pack(anchor="w")

        # Hover effects
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, event):
        self._is_hovered = True
        self.configure(
            fg_color=COLORS["bg_card_hover"],
            border_color=COLORS["border_hover"]
        )

    def _on_leave(self, event):
        self._is_hovered = False
        self.configure(
            fg_color=COLORS["bg_card"],
            border_color=COLORS["border"]
        )


# ============================================================
# MODERN BUTTON - Multiple Variants
# ============================================================
class ModernButton(ctk.CTkButton):
    """Premium button with multiple variants and smooth interactions"""

    VARIANTS = {
        "primary": {
            "fg": COLORS["accent"],
            "hover": COLORS["accent_hover"],
            "text": COLORS["text_primary"]
        },
        "secondary": {
            "fg": COLORS["bg_elevated"],
            "hover": COLORS["border_hover"],
            "text": COLORS["text_primary"]
        },
        "success": {
            "fg": COLORS["success"],
            "hover": COLORS["success_hover"],
            "text": COLORS["text_primary"]
        },
        "warning": {
            "fg": COLORS["warning"],
            "hover": COLORS["warning_hover"],
            "text": COLORS["bg_dark"]
        },
        "danger": {
            "fg": COLORS["error"],
            "hover": COLORS["error_hover"],
            "text": COLORS["text_primary"]
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
        icon: str = None,
        size: str = "md",  # sm, md, lg
        **kwargs
    ):
        style = self.VARIANTS.get(variant, self.VARIANTS["primary"])

        # Size presets
        sizes = {
            "sm": {"height": HEIGHTS["button_sm"], "font_size": FONTS["size_sm"], "padding": SPACING["sm"]},
            "md": {"height": HEIGHTS["button_md"], "font_size": FONTS["size_base"], "padding": SPACING["md"]},
            "lg": {"height": HEIGHTS["button_lg"], "font_size": FONTS["size_md"], "padding": SPACING["lg"]}
        }
        size_config = sizes.get(size, sizes["md"])

        # Build button text
        display_text = f"{icon}  {text}" if icon else text

        super().__init__(
            master,
            text=display_text,
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
# MODERN INPUT - Clean Entry Field
# ============================================================
class ModernEntry(ctk.CTkEntry):
    """Premium text input with focus states"""

    def __init__(
        self,
        master,
        placeholder: str = "",
        icon: str = None,
        **kwargs
    ):
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

        # Focus effects
        self.bind("<FocusIn>", self._on_focus)
        self.bind("<FocusOut>", self._on_blur)

    def _on_focus(self, event):
        self.configure(border_color=COLORS["accent"])

    def _on_blur(self, event):
        self.configure(border_color=COLORS["border"])


# ============================================================
# MODERN TEXTBOX - Multi-line Input
# ============================================================
class ModernTextbox(ctk.CTkTextbox):
    """Premium multi-line text editor"""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("corner_radius", RADIUS["md"])
        kwargs.setdefault("border_width", 1)

        super().__init__(
            master,
            fg_color=COLORS["bg_secondary"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont(family="Consolas", size=FONTS["size_base"]),
            **kwargs
        )

        self.bind("<FocusIn>", lambda e: self.configure(border_color=COLORS["accent"]))
        self.bind("<FocusOut>", lambda e: self.configure(border_color=COLORS["border"]))


# ============================================================
# PROFILE CARD - Premium Profile Display
# ============================================================
class ProfileCard(ctk.CTkFrame):
    """Premium profile card with avatar, status, and actions"""

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

        # Hover effects
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _create_widgets(self):
        # Main content frame
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=SPACING["md"], pady=SPACING["sm"])

        # Left section: Checkbox + Avatar
        left = ctk.CTkFrame(content, fg_color="transparent")
        left.pack(side="left", fill="y")

        # Checkbox
        self.checkbox_var = ctk.BooleanVar(value=False)
        self.checkbox = ctk.CTkCheckBox(
            left,
            text="",
            variable=self.checkbox_var,
            width=22,
            checkbox_width=20,
            checkbox_height=20,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            border_color=COLORS["border"],
            command=self._on_checkbox_change
        )
        self.checkbox.pack(side="left", padx=(0, SPACING["sm"]))

        # Avatar with gradient background
        avatar_frame = ctk.CTkFrame(
            left,
            width=48,
            height=48,
            corner_radius=RADIUS["lg"],
            fg_color=COLORS["accent"]
        )
        avatar_frame.pack(side="left")
        avatar_frame.pack_propagate(False)

        # Avatar icon
        name = self.profile_data.get('name', 'U')
        initial = name[0].upper() if name else 'U'
        ctk.CTkLabel(
            avatar_frame,
            text=initial,
            font=ctk.CTkFont(size=FONTS["size_xl"], weight="bold"),
            text_color=COLORS["text_primary"]
        ).place(relx=0.5, rely=0.5, anchor="center")

        # Middle section: Info
        info = ctk.CTkFrame(content, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=SPACING["md"])

        # Name
        name_display = self.profile_data.get('name', 'Unknown')
        if len(name_display) > 28:
            name_display = name_display[:28] + "..."

        self.name_label = ctk.CTkLabel(
            info,
            text=name_display,
            font=ctk.CTkFont(
                family=FONTS["family"],
                size=FONTS["size_md"],
                weight="bold"
            ),
            text_color=COLORS["text_primary"],
            anchor="w"
        )
        self.name_label.pack(anchor="w")

        # UUID
        uuid_display = self.profile_data.get('uuid', '')[:16] + "..."
        ctk.CTkLabel(
            info,
            text=uuid_display,
            font=ctk.CTkFont(family="Consolas", size=FONTS["size_xs"]),
            text_color=COLORS["text_tertiary"],
            anchor="w"
        ).pack(anchor="w")

        # Status row
        status_row = ctk.CTkFrame(info, fg_color="transparent")
        status_row.pack(anchor="w", pady=(SPACING["xs"], 0))

        # Status badge
        status_color = COLORS["success"] if self.is_running else COLORS["text_tertiary"]
        status_text = "RUNNING" if self.is_running else "STOPPED"

        self.status_label = ctk.CTkLabel(
            status_row,
            text=f"  {status_text}",
            font=ctk.CTkFont(size=FONTS["size_xs"], weight="bold"),
            text_color=status_color
        )
        self.status_label.pack(side="left")

        # Folder badge
        folder_name = self.profile_data.get('folder_name', '')
        if folder_name:
            folder_badge = ctk.CTkFrame(
                status_row,
                fg_color=COLORS["bg_elevated"],
                corner_radius=RADIUS["sm"]
            )
            folder_badge.pack(side="left", padx=(SPACING["sm"], 0))
            ctk.CTkLabel(
                folder_badge,
                text=f" {folder_name}",
                font=ctk.CTkFont(size=FONTS["size_xs"]),
                text_color=COLORS["text_secondary"]
            ).pack(padx=SPACING["xs"], pady=2)

        # Right section: Actions
        actions = ctk.CTkFrame(content, fg_color="transparent")
        actions.pack(side="right", fill="y")

        # Toggle button (Open/Close)
        if self.is_running:
            btn_text = "Dung"
            btn_color = COLORS["error"]
            btn_hover = COLORS["error_hover"]
            btn_icon = ""
        else:
            btn_text = "Mo"
            btn_color = COLORS["success"]
            btn_hover = COLORS["success_hover"]
            btn_icon = ""

        self.toggle_btn = ctk.CTkButton(
            actions,
            text=f"{btn_icon} {btn_text}",
            width=75,
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
            text="",
            width=36,
            height=HEIGHTS["button_sm"],
            fg_color=COLORS["bg_elevated"],
            hover_color=COLORS["border_hover"],
            corner_radius=RADIUS["md"],
            font=ctk.CTkFont(size=FONTS["size_md"]),
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
            self.configure(
                fg_color=COLORS["bg_card_hover"],
                border_color=COLORS["border_hover"]
            )

    def _on_leave(self, event):
        if not self.is_selected:
            self.configure(
                fg_color=COLORS["bg_card"],
                border_color=COLORS["border"]
            )


# ============================================================
# POST CARD - Content Display
# ============================================================
class PostCard(ctk.CTkFrame):
    """Premium post card with stats and actions"""

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

        # Hover effects
        self.bind("<Enter>", lambda e: self.configure(fg_color=COLORS["bg_card_hover"]))
        self.bind("<Leave>", lambda e: self.configure(fg_color=COLORS["bg_card"]))

    def _create_widgets(self):
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="x", padx=SPACING["lg"], pady=SPACING["md"])

        # URL
        url = self.post_data.get('url', '')
        url_display = url[:55] + "..." if len(url) > 55 else url

        url_label = ctk.CTkLabel(
            content,
            text=url_display,
            font=ctk.CTkFont(size=FONTS["size_sm"]),
            text_color=COLORS["text_link"],
            cursor="hand2"
        )
        url_label.pack(anchor="w")

        # Title
        title = self.post_data.get('title', 'Khong co tieu de')
        title_display = title[:70] + "..." if len(title) > 70 else title

        ctk.CTkLabel(
            content,
            text=title_display,
            font=ctk.CTkFont(
                family=FONTS["family"],
                size=FONTS["size_md"],
                weight="bold"
            ),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", pady=(SPACING["xs"], 0))

        # Bottom row: Stats + Actions
        bottom = ctk.CTkFrame(content, fg_color="transparent")
        bottom.pack(fill="x", pady=(SPACING["sm"], 0))

        # Stats
        stats = ctk.CTkFrame(bottom, fg_color="transparent")
        stats.pack(side="left")

        like_count = self.post_data.get('like_count', 0)
        comment_count = self.post_data.get('comment_count', 0)

        # Like stat
        like_frame = ctk.CTkFrame(stats, fg_color=COLORS["bg_elevated"], corner_radius=RADIUS["sm"])
        like_frame.pack(side="left", padx=(0, SPACING["sm"]))
        ctk.CTkLabel(
            like_frame,
            text=f" {like_count}",
            font=ctk.CTkFont(size=FONTS["size_sm"]),
            text_color=COLORS["error"]
        ).pack(padx=SPACING["sm"], pady=2)

        # Comment stat
        comment_frame = ctk.CTkFrame(stats, fg_color=COLORS["bg_elevated"], corner_radius=RADIUS["sm"])
        comment_frame.pack(side="left")
        ctk.CTkLabel(
            comment_frame,
            text=f" {comment_count}",
            font=ctk.CTkFont(size=FONTS["size_sm"]),
            text_color=COLORS["info"]
        ).pack(padx=SPACING["sm"], pady=2)

        # Actions
        actions = ctk.CTkFrame(bottom, fg_color="transparent")
        actions.pack(side="right")

        ModernButton(
            actions,
            text="Like",
            icon="",
            variant="danger",
            size="sm",
            width=70,
            command=lambda: self.on_like(self.post_data) if self.on_like else None
        ).pack(side="left", padx=2)

        ModernButton(
            actions,
            text="Comment",
            icon="",
            variant="primary",
            size="sm",
            width=90,
            command=lambda: self.on_comment(self.post_data) if self.on_comment else None
        ).pack(side="left", padx=2)

        ModernButton(
            actions,
            text="",
            variant="ghost",
            size="sm",
            width=36,
            command=lambda: self.on_delete(self.post_data) if self.on_delete else None
        ).pack(side="left", padx=2)


# ============================================================
# SCRIPT CARD - Script Display
# ============================================================
class ScriptCard(ctk.CTkFrame):
    """Premium script card with actions"""

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

        # Hover
        self.bind("<Enter>", lambda e: self.configure(fg_color=COLORS["bg_card_hover"]))
        self.bind("<Leave>", lambda e: self.configure(fg_color=COLORS["bg_card"]))

    def _create_widgets(self):
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="x", padx=SPACING["lg"], pady=SPACING["md"])

        # Header with icon
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x")

        # Script icon
        icon_frame = ctk.CTkFrame(
            header,
            width=40,
            height=40,
            corner_radius=RADIUS["md"],
            fg_color=COLORS["accent"]
        )
        icon_frame.pack(side="left")
        icon_frame.pack_propagate(False)
        ctk.CTkLabel(
            icon_frame,
            text="",
            font=ctk.CTkFont(size=18),
            text_color=COLORS["text_primary"]
        ).place(relx=0.5, rely=0.5, anchor="center")

        # Name and description
        info = ctk.CTkFrame(header, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True, padx=SPACING["md"])

        name = self.script_data.get('name', 'Untitled Script')
        ctk.CTkLabel(
            info,
            text=name,
            font=ctk.CTkFont(
                family=FONTS["family"],
                size=FONTS["size_md"],
                weight="bold"
            ),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")

        desc = self.script_data.get('description', '')
        if desc:
            desc_display = desc[:80] + "..." if len(desc) > 80 else desc
            ctk.CTkLabel(
                info,
                text=desc_display,
                font=ctk.CTkFont(size=FONTS["size_sm"]),
                text_color=COLORS["text_secondary"]
            ).pack(anchor="w")

        # Updated time
        updated = self.script_data.get('updated_at', '')
        if updated:
            ctk.CTkLabel(
                content,
                text=f" {updated[:16]}",
                font=ctk.CTkFont(size=FONTS["size_xs"]),
                text_color=COLORS["text_tertiary"]
            ).pack(anchor="w", pady=(SPACING["sm"], 0))

        # Actions
        actions = ctk.CTkFrame(content, fg_color="transparent")
        actions.pack(fill="x", pady=(SPACING["md"], 0))

        ModernButton(
            actions,
            text="Chay",
            icon="",
            variant="success",
            size="sm",
            width=85,
            command=lambda: self.on_run(self.script_data) if self.on_run else None
        ).pack(side="left", padx=2)

        ModernButton(
            actions,
            text="Sua",
            icon="",
            variant="secondary",
            size="sm",
            width=75,
            command=lambda: self.on_edit(self.script_data) if self.on_edit else None
        ).pack(side="left", padx=2)

        ModernButton(
            actions,
            text="Xoa",
            icon="",
            variant="danger",
            size="sm",
            width=75,
            command=lambda: self.on_delete(self.script_data) if self.on_delete else None
        ).pack(side="left", padx=2)


# ============================================================
# STATUS BAR - Bottom Status
# ============================================================
class StatusBar(ctk.CTkFrame):
    """Premium status bar with indicator and version"""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", COLORS["bg_secondary"])
        kwargs.setdefault("height", HEIGHTS["status_bar"])
        kwargs.setdefault("corner_radius", 0)

        super().__init__(master, **kwargs)
        self.pack_propagate(False)

        # Left: Status
        self.status_label = ctk.CTkLabel(
            self,
            text="  San sang",
            font=ctk.CTkFont(size=FONTS["size_sm"]),
            text_color=COLORS["success"]
        )
        self.status_label.pack(side="left", padx=SPACING["lg"])

        # Right: Version
        from config import APP_VERSION
        self.version_label = ctk.CTkLabel(
            self,
            text=f"FB Manager Pro v{APP_VERSION}",
            font=ctk.CTkFont(size=FONTS["size_sm"]),
            text_color=COLORS["text_tertiary"]
        )
        self.version_label.pack(side="right", padx=SPACING["lg"])

    def set_status(self, text: str, status_type: str = "info"):
        """Update status with icon and color"""
        icons = {
            "success": "",
            "error": "",
            "warning": "",
            "info": ""
        }
        colors = {
            "success": COLORS["success"],
            "error": COLORS["error"],
            "warning": COLORS["warning"],
            "info": COLORS["text_secondary"]
        }

        icon = icons.get(status_type, "")
        color = colors.get(status_type, COLORS["text_secondary"])

        self.status_label.configure(
            text=f"{icon}  {text}",
            text_color=color
        )


# ============================================================
# SEARCH BAR - Search Input with Button
# ============================================================
class SearchBar(ctk.CTkFrame):
    """Premium search bar with icon"""

    def __init__(
        self,
        master,
        placeholder: str = "Tim kiem...",
        on_search: Callable = None,
        **kwargs
    ):
        kwargs.setdefault("fg_color", COLORS["bg_secondary"])
        kwargs.setdefault("corner_radius", RADIUS["lg"])
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", COLORS["border"])

        super().__init__(master, **kwargs)

        self.on_search = on_search

        # Container
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x", padx=SPACING["sm"], pady=SPACING["xs"])

        # Search icon
        ctk.CTkLabel(
            container,
            text="",
            font=ctk.CTkFont(size=FONTS["size_md"]),
            text_color=COLORS["text_tertiary"]
        ).pack(side="left", padx=(SPACING["xs"], SPACING["sm"]))

        # Entry
        self.search_entry = ctk.CTkEntry(
            container,
            placeholder_text=placeholder,
            fg_color="transparent",
            border_width=0,
            text_color=COLORS["text_primary"],
            placeholder_text_color=COLORS["text_tertiary"],
            font=ctk.CTkFont(size=FONTS["size_base"]),
            height=34
        )
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<Return>", self._do_search)

        # Search button
        self.search_btn = ctk.CTkButton(
            container,
            text="",
            width=36,
            height=32,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            corner_radius=RADIUS["md"],
            command=self._do_search
        )
        self.search_btn.pack(side="right")

        # Focus effects
        self.search_entry.bind("<FocusIn>", lambda e: self.configure(border_color=COLORS["accent"]))
        self.search_entry.bind("<FocusOut>", lambda e: self.configure(border_color=COLORS["border"]))

    def _do_search(self, event=None):
        if self.on_search:
            self.on_search(self.search_entry.get())

    def get_value(self) -> str:
        return self.search_entry.get()


# ============================================================
# BADGE - Small Label Tag
# ============================================================
class Badge(ctk.CTkFrame):
    """Small badge/tag for status indicators"""

    def __init__(
        self,
        master,
        text: str,
        variant: str = "default",  # default, success, warning, error, info
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
# DIVIDER - Horizontal Line
# ============================================================
class Divider(ctk.CTkFrame):
    """Simple horizontal divider"""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", COLORS["border"])
        kwargs.setdefault("height", 1)

        super().__init__(master, **kwargs)


# ============================================================
# EMPTY STATE - Placeholder for Empty Lists
# ============================================================
class EmptyState(ctk.CTkFrame):
    """Empty state placeholder with icon and message"""

    def __init__(
        self,
        master,
        icon: str = "",
        title: str = "Khong co du lieu",
        description: str = "",
        action_text: str = None,
        on_action: Callable = None,
        **kwargs
    ):
        kwargs.setdefault("fg_color", "transparent")

        super().__init__(master, **kwargs)

        # Icon
        ctk.CTkLabel(
            self,
            text=icon,
            font=ctk.CTkFont(size=48),
            text_color=COLORS["text_tertiary"]
        ).pack(pady=(SPACING["2xl"], SPACING["md"]))

        # Title
        ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(
                family=FONTS["family"],
                size=FONTS["size_lg"],
                weight="bold"
            ),
            text_color=COLORS["text_secondary"]
        ).pack()

        # Description
        if description:
            ctk.CTkLabel(
                self,
                text=description,
                font=ctk.CTkFont(size=FONTS["size_base"]),
                text_color=COLORS["text_tertiary"]
            ).pack(pady=(SPACING["xs"], 0))

        # Action button
        if action_text and on_action:
            ModernButton(
                self,
                text=action_text,
                variant="primary",
                command=on_action
            ).pack(pady=SPACING["lg"])
