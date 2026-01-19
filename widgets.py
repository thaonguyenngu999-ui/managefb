"""
Cyberpunk UI Widgets - FB Manager Pro
Neon style with glow effects
"""
import customtkinter as ctk
from typing import Callable, Optional, Dict
from config import COLORS, FONTS, SPACING, RADIUS, HEIGHTS


# ============================================================
# NEON BUTTON - Cyberpunk Style
# ============================================================
class ModernButton(ctk.CTkButton):
    """Cyberpunk neon button with glow effect"""

    VARIANTS = {
        "primary": {
            "fg": COLORS["accent"],
            "hover": COLORS["accent_hover"],
            "text": "#000000",
            "border": COLORS["accent"]
        },
        "secondary": {
            "fg": "transparent",
            "hover": COLORS["bg_elevated"],
            "text": COLORS["accent"],
            "border": COLORS["accent"]
        },
        "success": {
            "fg": COLORS["success"],
            "hover": COLORS["success_hover"],
            "text": "#000000",
            "border": COLORS["success"]
        },
        "warning": {
            "fg": COLORS["warning"],
            "hover": COLORS["warning_hover"],
            "text": "#000000",
            "border": COLORS["warning"]
        },
        "danger": {
            "fg": COLORS["error"],
            "hover": COLORS["error_hover"],
            "text": "#ffffff",
            "border": COLORS["error"]
        },
        "ghost": {
            "fg": "transparent",
            "hover": COLORS["bg_card"],
            "text": COLORS["text_secondary"],
            "border": COLORS["border"]
        },
        "neon": {
            "fg": "transparent",
            "hover": COLORS["secondary"],
            "text": COLORS["secondary"],
            "border": COLORS["secondary"]
        }
    }

    def __init__(
        self,
        master,
        text: str,
        variant: str = "primary",
        icon: str = None,
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
            text=text.upper(),  # Cyberpunk style - uppercase
            fg_color=style["fg"],
            hover_color=style["hover"],
            text_color=style["text"],
            corner_radius=RADIUS["sm"],
            font=ctk.CTkFont(
                family=FONTS["family"],
                size=size_config["font_size"],
                weight="bold"
            ),
            height=size_config["height"],
            border_width=2,
            border_color=style["border"],
            **kwargs
        )


# ============================================================
# NEON INPUT - Cyberpunk Style
# ============================================================
class ModernEntry(ctk.CTkEntry):
    """Cyberpunk neon input field"""

    def __init__(self, master, placeholder: str = "", **kwargs):
        kwargs.setdefault("height", HEIGHTS["input"])
        kwargs.setdefault("corner_radius", RADIUS["sm"])

        super().__init__(
            master,
            placeholder_text=placeholder,
            fg_color=COLORS["bg_secondary"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            placeholder_text_color=COLORS["text_tertiary"],
            font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_base"]),
            border_width=2,
            **kwargs
        )

        # Neon glow on focus
        self.bind("<FocusIn>", lambda e: self.configure(border_color=COLORS["accent"]))
        self.bind("<FocusOut>", lambda e: self.configure(border_color=COLORS["border"]))


# ============================================================
# NEON TEXTBOX
# ============================================================
class ModernTextbox(ctk.CTkTextbox):
    """Cyberpunk neon text editor"""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("corner_radius", RADIUS["sm"])
        kwargs.setdefault("border_width", 2)

        super().__init__(
            master,
            fg_color=COLORS["bg_secondary"],
            border_color=COLORS["border"],
            text_color=COLORS["accent_light"],  # Neon text
            font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_base"]),
            **kwargs
        )

        self.bind("<FocusIn>", lambda e: self.configure(border_color=COLORS["accent"]))
        self.bind("<FocusOut>", lambda e: self.configure(border_color=COLORS["border"]))


# ============================================================
# PROFILE CARD - Cyberpunk Style
# ============================================================
class ProfileCard(ctk.CTkFrame):
    """Cyberpunk profile card with neon accents"""

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
        kwargs.setdefault("corner_radius", RADIUS["md"])
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

        # Left: Checkbox + Neon Avatar
        left = ctk.CTkFrame(content, fg_color="transparent")
        left.pack(side="left", fill="y")

        self.checkbox_var = ctk.BooleanVar(value=False)
        self.checkbox = ctk.CTkCheckBox(
            left,
            text="",
            variable=self.checkbox_var,
            width=20,
            checkbox_width=20,
            checkbox_height=20,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            border_color=COLORS["accent"],
            checkmark_color="#000000",
            corner_radius=RADIUS["xs"],
            command=self._on_checkbox_change
        )
        self.checkbox.pack(side="left", padx=(0, SPACING["md"]))

        # Neon avatar circle
        avatar_color = COLORS["success"] if self.is_running else COLORS["secondary"]
        avatar = ctk.CTkFrame(
            left,
            width=48,
            height=48,
            corner_radius=24,
            fg_color="transparent",
            border_width=2,
            border_color=avatar_color
        )
        avatar.pack(side="left")
        avatar.pack_propagate(False)

        name = self.profile_data.get('name', 'U')
        initial = name[0].upper() if name else 'U'
        ctk.CTkLabel(
            avatar,
            text=initial,
            font=ctk.CTkFont(size=FONTS["size_xl"], weight="bold"),
            text_color=avatar_color
        ).place(relx=0.5, rely=0.5, anchor="center")

        # Middle: Info
        info = ctk.CTkFrame(content, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=SPACING["lg"])

        # Name with neon effect
        name_display = self.profile_data.get('name', 'Unknown')
        if len(name_display) > 28:
            name_display = name_display[:28] + "..."

        self.name_label = ctk.CTkLabel(
            info,
            text=name_display,
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_md"], weight="bold"),
            text_color=COLORS["text_primary"],
            anchor="w"
        )
        self.name_label.pack(anchor="w")

        # UUID - monospace
        uuid_display = self.profile_data.get('uuid', '')[:24] + "..."
        ctk.CTkLabel(
            info,
            text=uuid_display,
            font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_xs"]),
            text_color=COLORS["text_tertiary"],
            anchor="w"
        ).pack(anchor="w")

        # Status indicator - neon style
        status_color = COLORS["success"] if self.is_running else COLORS["error"]
        status_text = "[ ONLINE ]" if self.is_running else "[ OFFLINE ]"

        self.status_label = ctk.CTkLabel(
            info,
            text=status_text,
            font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_xs"], weight="bold"),
            text_color=status_color
        )
        self.status_label.pack(anchor="w", pady=(SPACING["xs"], 0))

        # Right: Actions
        actions = ctk.CTkFrame(content, fg_color="transparent")
        actions.pack(side="right", fill="y")

        # Toggle button - neon style
        if self.is_running:
            btn_text = "STOP"
            btn_variant = "danger"
        else:
            btn_text = "START"
            btn_variant = "success"

        self.toggle_btn = ModernButton(
            actions,
            text=btn_text,
            variant=btn_variant,
            size="sm",
            width=80,
            command=self._on_toggle_click
        )
        self.toggle_btn.pack(side="left", padx=SPACING["xs"])

        # Edit button
        self.edit_btn = ModernButton(
            actions,
            text="EDIT",
            variant="secondary",
            size="sm",
            width=60,
            command=lambda: self.on_edit(self.profile_data) if self.on_edit else None
        )
        self.edit_btn.pack(side="left", padx=SPACING["xs"])

    def _on_toggle_click(self):
        if self.on_toggle:
            self.on_toggle(self.profile_data, not self.is_running)

    def _on_checkbox_change(self):
        self.is_selected = self.checkbox_var.get()
        if self.is_selected:
            self.configure(border_color=COLORS["accent"], border_width=2)
        else:
            self.configure(border_color=COLORS["border"], border_width=1)
        if self.on_select:
            self.on_select(self.profile_data, self.is_selected)

    def _on_enter(self, event):
        if not self.is_selected:
            self.configure(fg_color=COLORS["bg_card_hover"], border_color=COLORS["border_hover"])

    def _on_leave(self, event):
        if not self.is_selected:
            self.configure(fg_color=COLORS["bg_card"], border_color=COLORS["border"])


# ============================================================
# STATUS BAR - Cyberpunk Style
# ============================================================
class StatusBar(ctk.CTkFrame):
    """Cyberpunk status bar with neon accents"""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", COLORS["bg_secondary"])
        kwargs.setdefault("height", HEIGHTS["status_bar"])
        kwargs.setdefault("corner_radius", 0)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", COLORS["border"])

        super().__init__(master, **kwargs)
        self.pack_propagate(False)

        # Neon accent line at top
        accent_line = ctk.CTkFrame(
            self,
            height=2,
            fg_color=COLORS["accent"],
            corner_radius=0
        )
        accent_line.pack(fill="x", side="top")

        # Left: Status
        self.status_label = ctk.CTkLabel(
            self,
            text="[ SYSTEM READY ]",
            font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_sm"]),
            text_color=COLORS["success"]
        )
        self.status_label.pack(side="left", padx=SPACING["lg"])

        # Right: Version
        from config import APP_VERSION
        ctk.CTkLabel(
            self,
            text=f"// FB MANAGER v{APP_VERSION}",
            font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_sm"]),
            text_color=COLORS["text_tertiary"]
        ).pack(side="right", padx=SPACING["lg"])

    def set_status(self, text: str, status_type: str = "info"):
        """Update status with neon color"""
        colors = {
            "success": COLORS["success"],
            "error": COLORS["error"],
            "warning": COLORS["warning"],
            "info": COLORS["accent"]
        }
        color = colors.get(status_type, COLORS["accent"])
        self.status_label.configure(text=f"[ {text.upper()} ]", text_color=color)


# ============================================================
# SEARCH BAR - Cyberpunk Style
# ============================================================
class SearchBar(ctk.CTkFrame):
    """Cyberpunk search bar with neon border"""

    def __init__(
        self,
        master,
        placeholder: str = "SEARCH...",
        on_search: Callable = None,
        **kwargs
    ):
        kwargs.setdefault("fg_color", COLORS["bg_secondary"])
        kwargs.setdefault("corner_radius", RADIUS["sm"])
        kwargs.setdefault("border_width", 2)
        kwargs.setdefault("border_color", COLORS["border"])

        super().__init__(master, **kwargs)

        self.on_search = on_search

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x", padx=SPACING["sm"], pady=SPACING["xs"])

        # Search icon text
        ctk.CTkLabel(
            container,
            text=">",
            font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_md"], weight="bold"),
            text_color=COLORS["accent"],
            width=20
        ).pack(side="left")

        self.search_entry = ctk.CTkEntry(
            container,
            placeholder_text=placeholder.upper(),
            fg_color="transparent",
            border_width=0,
            text_color=COLORS["text_primary"],
            placeholder_text_color=COLORS["text_tertiary"],
            font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_base"]),
            height=32,
            width=180
        )
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<Return>", self._do_search)

        self.search_btn = ModernButton(
            container,
            text="GO",
            variant="primary",
            size="sm",
            width=50,
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
# BADGE - Cyberpunk Style
# ============================================================
class Badge(ctk.CTkFrame):
    """Cyberpunk badge/tag"""

    def __init__(
        self,
        master,
        text: str,
        variant: str = "default",
        **kwargs
    ):
        colors = {
            "default": (COLORS["bg_elevated"], COLORS["text_secondary"], COLORS["border"]),
            "success": ("transparent", COLORS["success"], COLORS["success"]),
            "warning": ("transparent", COLORS["warning"], COLORS["warning"]),
            "error": ("transparent", COLORS["error"], COLORS["error"]),
            "info": ("transparent", COLORS["accent"], COLORS["accent"]),
            "neon": ("transparent", COLORS["secondary"], COLORS["secondary"])
        }

        bg, fg, border = colors.get(variant, colors["default"])

        kwargs.setdefault("fg_color", bg)
        kwargs.setdefault("corner_radius", RADIUS["xs"])
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", border)

        super().__init__(master, **kwargs)

        ctk.CTkLabel(
            self,
            text=text.upper(),
            font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_xs"], weight="bold"),
            text_color=fg
        ).pack(padx=SPACING["sm"], pady=2)


# ============================================================
# EMPTY STATE - Cyberpunk Style
# ============================================================
class EmptyState(ctk.CTkFrame):
    """Cyberpunk empty state"""

    def __init__(
        self,
        master,
        icon: str = "",
        title: str = "NO DATA",
        description: str = "",
        action_text: str = None,
        on_action: Callable = None,
        **kwargs
    ):
        kwargs.setdefault("fg_color", "transparent")

        super().__init__(master, **kwargs)

        # Cyberpunk ASCII art style
        ctk.CTkLabel(
            self,
            text="[ ! ]",
            font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_3xl"], weight="bold"),
            text_color=COLORS["accent"]
        ).pack(pady=(SPACING["2xl"], SPACING["md"]))

        # Title
        ctk.CTkLabel(
            self,
            text=title.upper(),
            font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_lg"], weight="bold"),
            text_color=COLORS["text_secondary"]
        ).pack()

        # Description
        if description:
            ctk.CTkLabel(
                self,
                text=description,
                font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_sm"]),
                text_color=COLORS["text_tertiary"]
            ).pack(pady=SPACING["sm"])

        # Action button
        if action_text and on_action:
            ModernButton(
                self,
                text=action_text,
                variant="neon",
                command=on_action
            ).pack(pady=SPACING["lg"])


# ============================================================
# MODERN CARD - Cyberpunk Style
# ============================================================
class ModernCard(ctk.CTkFrame):
    """Cyberpunk card container"""

    def __init__(self, master, title: str = "", subtitle: str = "", icon: str = "", **kwargs):
        kwargs.setdefault("fg_color", COLORS["bg_card"])
        kwargs.setdefault("corner_radius", RADIUS["md"])
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", COLORS["border"])

        super().__init__(master, **kwargs)

        if title:
            header = ctk.CTkFrame(self, fg_color="transparent")
            header.pack(fill="x", padx=SPACING["lg"], pady=(SPACING["lg"], SPACING["sm"]))

            # Neon accent
            ctk.CTkFrame(
                header,
                width=3,
                height=20,
                fg_color=COLORS["accent"],
                corner_radius=1
            ).pack(side="left", padx=(0, SPACING["sm"]))

            title_frame = ctk.CTkFrame(header, fg_color="transparent")
            title_frame.pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(
                title_frame,
                text=title.upper(),
                font=ctk.CTkFont(family=FONTS["family"], size=FONTS["size_md"], weight="bold"),
                text_color=COLORS["text_primary"]
            ).pack(anchor="w")

            if subtitle:
                ctk.CTkLabel(
                    title_frame,
                    text=subtitle,
                    font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_xs"]),
                    text_color=COLORS["text_tertiary"]
                ).pack(anchor="w")

        # Hover effect
        self.bind("<Enter>", lambda e: self.configure(border_color=COLORS["border_hover"]))
        self.bind("<Leave>", lambda e: self.configure(border_color=COLORS["border"]))


# ============================================================
# DIVIDER - Cyberpunk Style
# ============================================================
class Divider(ctk.CTkFrame):
    """Cyberpunk divider with neon accent"""

    def __init__(self, master, neon: bool = False, **kwargs):
        color = COLORS["accent"] if neon else COLORS["border"]
        kwargs.setdefault("fg_color", color)
        kwargs.setdefault("height", 1 if not neon else 2)
        super().__init__(master, **kwargs)


# ============================================================
# STAT CARD - Cyberpunk Style
# ============================================================
class StatCard(ctk.CTkFrame):
    """Cyberpunk statistics card"""

    def __init__(
        self,
        master,
        label: str,
        value: str,
        color: str = None,
        **kwargs
    ):
        kwargs.setdefault("fg_color", COLORS["bg_card"])
        kwargs.setdefault("corner_radius", RADIUS["md"])
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", COLORS["border"])

        super().__init__(master, **kwargs)

        color = color or COLORS["accent"]

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=SPACING["md"], pady=SPACING["md"])

        # Value with neon color
        self.value_label = ctk.CTkLabel(
            inner,
            text=value,
            font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_2xl"], weight="bold"),
            text_color=color
        )
        self.value_label.pack(anchor="w")

        # Label
        ctk.CTkLabel(
            inner,
            text=label.upper(),
            font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_xs"]),
            text_color=COLORS["text_tertiary"]
        ).pack(anchor="w")

        # Neon bottom line
        ctk.CTkFrame(
            self,
            height=2,
            fg_color=color,
            corner_radius=0
        ).pack(fill="x", side="bottom")

    def set_value(self, value: str):
        self.value_label.configure(text=value)
