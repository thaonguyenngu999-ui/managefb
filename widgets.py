"""
Custom Widgets - Cyberpunk Neon Theme
FB Manager Pro v3.0 CYBER
"""
import customtkinter as ctk
from typing import Callable, Optional, List, Dict
from config import COLORS, FONT_FAMILY, FONT_FAMILY_MONO


# ============================================================
# BASIC CYBERPUNK WIDGETS
# ============================================================

class CyberButton(ctk.CTkButton):
    """Neon-styled button with glow effect"""
    def __init__(self, master, text: str, variant: str = "primary", icon: str = None, **kwargs):
        colors = {
            "primary": (COLORS["accent"], COLORS["accent_hover"], COLORS["text_primary"]),
            "cyan": (COLORS["cyan"], COLORS["cyan_hover"], "#000000"),
            "success": (COLORS["success"], COLORS["success_hover"], "#000000"),
            "warning": (COLORS["warning"], COLORS["warning_hover"], "#000000"),
            "danger": (COLORS["error"], COLORS["error_hover"], COLORS["text_primary"]),
            "secondary": (COLORS["bg_card"], COLORS["bg_hover"], COLORS["text_primary"]),
            "ghost": ("transparent", COLORS["bg_hover"], COLORS["text_secondary"]),
            "outline_cyan": ("transparent", COLORS["cyan"], COLORS["cyan"]),
            "outline_danger": ("transparent", COLORS["error"], COLORS["error"]),
        }

        fg, hover, text_color = colors.get(variant, colors["primary"])

        # Border for outline variants
        border_width = 1 if variant.startswith("outline") else 0
        border_color = text_color if variant.startswith("outline") else None

        display_text = f"{icon} {text}" if icon else text

        super().__init__(
            master,
            text=display_text,
            fg_color=fg,
            hover_color=hover,
            text_color=text_color,
            text_color_disabled=COLORS["text_muted"],
            corner_radius=6,
            border_width=border_width,
            border_color=border_color,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            height=36,
            **kwargs
        )


class CyberEntry(ctk.CTkEntry):
    """Cyberpunk-styled entry field"""
    def __init__(self, master, placeholder: str = "", icon: str = None, **kwargs):
        super().__init__(
            master,
            placeholder_text=f"{icon} {placeholder}" if icon else placeholder,
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            placeholder_text_color=COLORS["text_muted"],
            corner_radius=6,
            height=40,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            **kwargs
        )

        # Hover effect
        self.bind("<Enter>", lambda e: self.configure(border_color=COLORS["cyan"]))
        self.bind("<Leave>", lambda e: self.configure(border_color=COLORS["border"]))
        self.bind("<FocusIn>", lambda e: self.configure(border_color=COLORS["accent"]))
        self.bind("<FocusOut>", lambda e: self.configure(border_color=COLORS["border"]))


class CyberTextbox(ctk.CTkTextbox):
    """Cyberpunk-styled multiline textbox"""
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            corner_radius=8,
            font=ctk.CTkFont(family=FONT_FAMILY_MONO, size=12),
            border_width=1,
            **kwargs
        )


# ============================================================
# STATS CARD - For dashboard statistics
# ============================================================

class StatsCard(ctk.CTkFrame):
    """Statistics card with icon, value, and trend indicator"""
    def __init__(self, master, icon: str, title: str, value: str,
                 trend: str = None, color: str = "cyan", **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
            **kwargs
        )

        self.color = COLORS.get(color, COLORS["cyan"])
        self._create_widgets(icon, title, value, trend)

    def _create_widgets(self, icon: str, title: str, value: str, trend: str):
        # Icon and title row
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 5))

        ctk.CTkLabel(
            header,
            text=icon,
            font=ctk.CTkFont(size=16),
            text_color=self.color
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text=title.upper(),
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=COLORS["text_secondary"]
        ).pack(side="left", padx=(8, 0))

        # Value
        ctk.CTkLabel(
            self,
            text=value,
            font=ctk.CTkFont(family=FONT_FAMILY, size=36, weight="bold"),
            text_color=self.color
        ).pack(anchor="w", padx=15, pady=(0, 5))

        # Trend indicator (optional)
        if trend:
            trend_color = COLORS["success"] if trend.startswith("↑") or trend.startswith("+") else COLORS["text_secondary"]
            ctk.CTkLabel(
                self,
                text=trend,
                font=ctk.CTkFont(size=11),
                text_color=trend_color
            ).pack(anchor="w", padx=15, pady=(0, 15))
        else:
            # Spacer
            ctk.CTkFrame(self, fg_color="transparent", height=20).pack(fill="x", padx=15, pady=(0, 10))

    def update_value(self, value: str, trend: str = None):
        """Update the card value"""
        # This would need to store references to update dynamically
        pass


# ============================================================
# OS BADGE - Operating system indicator
# ============================================================

class OSBadge(ctk.CTkFrame):
    """Operating system badge with color coding"""

    OS_COLORS = {
        "win": ("WINDOWS", COLORS["os_windows"]),
        "windows": ("WINDOWS", COLORS["os_windows"]),
        "mac": ("MACOS", COLORS["os_macos"]),
        "macos": ("MACOS", COLORS["os_macos"]),
        "android": ("ANDROID", COLORS["os_android"]),
        "ios": ("IOS", COLORS["os_ios"]),
        "linux": ("LINUX", COLORS["os_linux"]),
    }

    def __init__(self, master, os_type: str, **kwargs):
        os_type_lower = os_type.lower() if os_type else "windows"
        label, color = self.OS_COLORS.get(os_type_lower, ("UNKNOWN", COLORS["text_secondary"]))

        super().__init__(
            master,
            fg_color="transparent",
            **kwargs
        )

        # Badge frame
        badge = ctk.CTkFrame(
            self,
            fg_color=color + "20",  # Add transparency
            corner_radius=4,
            border_width=1,
            border_color=color + "40"
        )
        badge.pack()

        ctk.CTkLabel(
            badge,
            text=label,
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            text_color=color,
            width=70
        ).pack(padx=8, pady=3)


# ============================================================
# PROFILE TABLE ROW
# ============================================================

class ProfileTableRow(ctk.CTkFrame):
    """A single row in the profiles table"""
    def __init__(self, master, profile_data: Dict,
                 on_toggle: Callable = None,
                 on_select: Callable = None,
                 **kwargs):

        self.profile_data = profile_data
        self.on_toggle = on_toggle
        self.on_select = on_select
        self.is_running = profile_data.get('check_open') == 1

        # Row background - green tint if running
        bg_color = "#0a1f0a" if self.is_running else COLORS["bg_card"]

        super().__init__(
            master,
            fg_color=bg_color,
            corner_radius=0,
            height=50,
            **kwargs
        )

        self.pack_propagate(False)
        self._create_widgets()

        # Hover effects
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _create_widgets(self):
        # Container with grid
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=5)

        # Checkbox (width: 40)
        self.checkbox_var = ctk.BooleanVar(value=False)
        self.checkbox = ctk.CTkCheckBox(
            container,
            text="",
            variable=self.checkbox_var,
            width=24,
            height=24,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            border_color=COLORS["border"],
            command=self._on_checkbox_change
        )
        self.checkbox.pack(side="left", padx=(0, 15))

        # Status indicator (width: 60)
        status_frame = ctk.CTkFrame(container, fg_color="transparent", width=60)
        status_frame.pack(side="left", padx=(0, 10))
        status_frame.pack_propagate(False)

        status_text = "ON" if self.is_running else "OFF"
        status_color = COLORS["success"] if self.is_running else COLORS["text_muted"]

        self.status_label = ctk.CTkLabel(
            status_frame,
            text=f"● {status_text}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=status_color
        )
        self.status_label.pack(side="left")

        # Profile name (expandable)
        name = self.profile_data.get('name', 'Unknown')
        self.name_label = ctk.CTkLabel(
            container,
            text=name,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=COLORS["text_primary"],
            anchor="w"
        )
        self.name_label.pack(side="left", fill="x", expand=True)

        # OS Badge (width: 100)
        os_type = self.profile_data.get('os', 'windows')
        os_badge = OSBadge(container, os_type)
        os_badge.pack(side="left", padx=10)

        # Browser (width: 100)
        browser = self.profile_data.get('browser', 'Chrome')
        browser_version = self.profile_data.get('browser_version', '')
        browser_text = f"{browser.title()} {browser_version}" if browser_version else browser.title()

        ctk.CTkLabel(
            container,
            text=browser_text,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=COLORS["text_secondary"],
            width=100
        ).pack(side="left", padx=10)

        # Proxy (width: 150)
        proxy = self.profile_data.get('proxy', '-')
        if proxy and proxy != '-':
            # Parse proxy and show partial
            parts = proxy.split('|') if '|' in proxy else proxy.split(':')
            if len(parts) >= 2:
                proxy_display = f"{parts[1][:10]}..." if len(parts[1]) > 10 else parts[1]
            else:
                proxy_display = proxy[:15] + "..." if len(proxy) > 15 else proxy
        else:
            proxy_display = "-"

        ctk.CTkLabel(
            container,
            text=proxy_display,
            font=ctk.CTkFont(family=FONT_FAMILY_MONO, size=11),
            text_color=COLORS["text_muted"],
            width=120
        ).pack(side="left", padx=10)

        # Action button (width: 100)
        if self.is_running:
            self.action_btn = CyberButton(
                container,
                text="CLOSE",
                icon="■",
                variant="danger",
                width=90,
                height=30,
                command=self._on_close
            )
        else:
            self.action_btn = CyberButton(
                container,
                text="OPEN",
                icon="▶",
                variant="success",
                width=90,
                height=30,
                command=self._on_open
            )
        self.action_btn.pack(side="right", padx=5)

    def _on_enter(self, event):
        if not self.is_running:
            self.configure(fg_color=COLORS["bg_hover"])

    def _on_leave(self, event):
        bg_color = "#0a1f0a" if self.is_running else COLORS["bg_card"]
        self.configure(fg_color=bg_color)

    def _on_checkbox_change(self):
        if self.on_select:
            self.on_select(self.profile_data, self.checkbox_var.get())

    def _on_open(self):
        if self.on_toggle:
            self.on_toggle(self.profile_data, True)

    def _on_close(self):
        if self.on_toggle:
            self.on_toggle(self.profile_data, False)

    def update_status(self, is_running: bool):
        """Update the row's running status"""
        self.is_running = is_running
        self.profile_data['check_open'] = 1 if is_running else 0

        # Update background
        bg_color = "#0a1f0a" if is_running else COLORS["bg_card"]
        self.configure(fg_color=bg_color)

        # Update status label
        status_text = "ON" if is_running else "OFF"
        status_color = COLORS["success"] if is_running else COLORS["text_muted"]
        self.status_label.configure(text=f"● {status_text}", text_color=status_color)

        # Update action button
        if is_running:
            self.action_btn.configure(
                text="■ CLOSE",
                fg_color=COLORS["error"],
                hover_color=COLORS["error_hover"],
                command=self._on_close
            )
        else:
            self.action_btn.configure(
                text="▶ OPEN",
                fg_color=COLORS["success"],
                hover_color=COLORS["success_hover"],
                command=self._on_open
            )

    def set_selected(self, selected: bool):
        """Set the checkbox state"""
        self.checkbox_var.set(selected)


# ============================================================
# TABLE HEADER
# ============================================================

class TableHeader(ctk.CTkFrame):
    """Header row for the profiles table"""
    def __init__(self, master, on_select_all: Callable = None, **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_secondary"],
            corner_radius=0,
            height=40,
            **kwargs
        )

        self.on_select_all = on_select_all
        self.pack_propagate(False)
        self._create_widgets()

    def _create_widgets(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=5)

        # Header checkbox
        self.checkbox_var = ctk.BooleanVar(value=False)
        self.checkbox = ctk.CTkCheckBox(
            container,
            text="",
            variable=self.checkbox_var,
            width=24,
            height=24,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            border_color=COLORS["border"],
            command=self._on_checkbox_change
        )
        self.checkbox.pack(side="left", padx=(0, 15))

        # Column headers
        headers = [
            ("STATUS", 60),
            ("TÊN PROFILE", None),  # expandable
            ("HỆ ĐIỀU HÀNH", 100),
            ("BROWSER", 100),
            ("PROXY", 120),
            ("HÀNH ĐỘNG", 100),
        ]

        for text, width in headers:
            if width:
                frame = ctk.CTkFrame(container, fg_color="transparent", width=width)
                frame.pack_propagate(False)
            else:
                frame = ctk.CTkFrame(container, fg_color="transparent")

            ctk.CTkLabel(
                frame,
                text=text,
                font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
                text_color=COLORS["text_secondary"],
                anchor="w"
            ).pack(side="left", fill="x", expand=True)

            if width:
                frame.pack(side="left", padx=10)
            else:
                frame.pack(side="left", fill="x", expand=True, padx=10)

    def _on_checkbox_change(self):
        if self.on_select_all:
            self.on_select_all(self.checkbox_var.get())


# ============================================================
# SEARCH BAR - Cyberpunk styled
# ============================================================

class CyberSearchBar(ctk.CTkFrame):
    """Cyberpunk-styled search bar with icon"""
    def __init__(self, master, placeholder: str = "Tìm kiếm...",
                 on_search: Callable = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.on_search = on_search

        # Search container with icon
        search_frame = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_input"],
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"]
        )
        search_frame.pack(side="left")

        # Search icon
        ctk.CTkLabel(
            search_frame,
            text="🔍",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text_muted"]
        ).pack(side="left", padx=(12, 5))

        # Entry
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text=placeholder,
            fg_color="transparent",
            border_width=0,
            text_color=COLORS["text_primary"],
            placeholder_text_color=COLORS["text_muted"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            width=250,
            height=36
        )
        self.search_entry.pack(side="left", padx=(0, 12))
        self.search_entry.bind("<Return>", self._do_search)

        # Hover effect on container
        search_frame.bind("<Enter>", lambda e: search_frame.configure(border_color=COLORS["cyan"]))
        search_frame.bind("<Leave>", lambda e: search_frame.configure(border_color=COLORS["border"]))

    def _do_search(self, event=None):
        if self.on_search:
            self.on_search(self.search_entry.get())

    def get_value(self) -> str:
        return self.search_entry.get()


# ============================================================
# FOLDER DROPDOWN
# ============================================================

class FolderDropdown(ctk.CTkFrame):
    """Folder selection dropdown with icon"""
    def __init__(self, master, on_select: Callable = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.on_select = on_select

        # Label
        ctk.CTkLabel(
            self,
            text="FOLDER:",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=COLORS["text_secondary"]
        ).pack(side="left", padx=(0, 8))

        # Dropdown
        self.folder_var = ctk.StringVar(value="TẤT CẢ")
        self.dropdown = ctk.CTkOptionMenu(
            self,
            variable=self.folder_var,
            values=["TẤT CẢ"],
            fg_color=COLORS["bg_input"],
            button_color=COLORS["border"],
            button_hover_color=COLORS["bg_hover"],
            dropdown_fg_color=COLORS["bg_card"],
            dropdown_hover_color=COLORS["bg_hover"],
            dropdown_text_color=COLORS["text_primary"],
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            width=150,
            height=36,
            corner_radius=6,
            command=self._on_select
        )
        self.dropdown.pack(side="left")

    def _on_select(self, value):
        if self.on_select:
            self.on_select(value)

    def set_values(self, values: List[str]):
        """Update dropdown values"""
        self.dropdown.configure(values=values)

    def get_value(self) -> str:
        return self.folder_var.get()


# ============================================================
# STATUS BAR - Bottom of window
# ============================================================

class CyberStatusBar(ctk.CTkFrame):
    """Cyberpunk-styled status bar"""
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_secondary"],
            height=32,
            corner_radius=0,
            **kwargs
        )

        self.pack_propagate(False)
        self._create_widgets()

    def _create_widgets(self):
        # Left side - status
        self.status_indicator = ctk.CTkLabel(
            self,
            text="●",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["success"]
        )
        self.status_indicator.pack(side="left", padx=(15, 5))

        self.status_label = ctk.CTkLabel(
            self,
            text="SYSTEM READY - CONNECTED TO HIDEMIUM API",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10),
            text_color=COLORS["text_secondary"]
        )
        self.status_label.pack(side="left")

        # Right side - version
        self.version_label = ctk.CTkLabel(
            self,
            text="FB MANAGER PRO v3.0 CYBER - © 2024",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10),
            text_color=COLORS["text_muted"]
        )
        self.version_label.pack(side="right", padx=15)

    def set_status(self, text: str, status_type: str = "info"):
        """Update status text and color"""
        colors = {
            "success": COLORS["success"],
            "error": COLORS["error"],
            "warning": COLORS["warning"],
            "info": COLORS["text_secondary"]
        }
        color = colors.get(status_type, COLORS["text_secondary"])

        self.status_indicator.configure(text_color=color)
        self.status_label.configure(text=text.upper())


# ============================================================
# SIDEBAR NAV BUTTON
# ============================================================

class NavButton(ctk.CTkButton):
    """Sidebar navigation button"""
    def __init__(self, master, text: str, icon: str, is_active: bool = False, **kwargs):
        self.is_active = is_active

        super().__init__(
            master,
            text=f"  {icon}  {text}",
            fg_color=COLORS["accent"] if is_active else "transparent",
            hover_color=COLORS["bg_hover"],
            text_color=COLORS["text_primary"],
            anchor="w",
            height=45,
            corner_radius=8,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            **kwargs
        )

    def set_active(self, active: bool):
        """Set active state"""
        self.is_active = active
        self.configure(fg_color=COLORS["accent"] if active else "transparent")


# ============================================================
# QUICK STATS CARD (for sidebar)
# ============================================================

class QuickStatsCard(ctk.CTkFrame):
    """Quick stats panel for sidebar"""
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_card"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"],
            **kwargs
        )

        self._create_widgets()

    def _create_widgets(self):
        # Header
        ctk.CTkLabel(
            self,
            text="⚡ QUICK STATS",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=15, pady=(12, 10))

        # Stats items container
        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.pack(fill="x", padx=15, pady=(0, 12))

        # Individual stats
        self.profiles_label = self._create_stat_row("PROFILES", "0", COLORS["cyan"])
        self.running_label = self._create_stat_row("RUNNING", "0", COLORS["success"])
        self.scripts_label = self._create_stat_row("SCRIPTS", "0", COLORS["warning"])

    def _create_stat_row(self, label: str, value: str, color: str):
        """Create a single stat row"""
        row = ctk.CTkFrame(self.stats_frame, fg_color="transparent")
        row.pack(fill="x", pady=2)

        ctk.CTkLabel(
            row,
            text=label,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=COLORS["text_secondary"]
        ).pack(side="left")

        value_label = ctk.CTkLabel(
            row,
            text=value,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=color
        )
        value_label.pack(side="right")

        return value_label

    def update_stats(self, profiles: int, running: int, scripts: int):
        """Update all stats"""
        self.profiles_label.configure(text=str(profiles))
        self.running_label.configure(text=str(running))
        self.scripts_label.configure(text=str(scripts))


# ============================================================
# LEGACY COMPATIBILITY - Keep old widget names working
# ============================================================

class ModernCard(ctk.CTkFrame):
    """Card hiện đại với shadow effect - Legacy compatibility"""
    def __init__(self, master, title: str = "", **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
            **kwargs
        )

        if title:
            self.title_label = ctk.CTkLabel(
                self,
                text=title,
                font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
                text_color=COLORS["text_primary"]
            )
            self.title_label.pack(anchor="w", padx=20, pady=(15, 10))


class ModernButton(CyberButton):
    """Legacy compatibility"""
    pass


class ModernEntry(CyberEntry):
    """Legacy compatibility"""
    pass


class ModernTextbox(CyberTextbox):
    """Legacy compatibility"""
    pass


class SearchBar(CyberSearchBar):
    """Legacy compatibility"""
    pass


class StatusBar(CyberStatusBar):
    """Legacy compatibility"""
    pass


# ============================================================
# PROFILE CARD - Legacy (for other tabs that might use it)
# ============================================================

class ProfileCard(ctk.CTkFrame):
    """Card hiển thị thông tin profile - Legacy"""
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
            width=24,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self._on_checkbox_change
        )
        self.checkbox.place(x=15, y=38)

        # Profile info
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.place(x=55, y=15)

        # Name
        name = self.profile_data.get('name', 'Unknown')
        self.name_label = ctk.CTkLabel(
            info_frame,
            text=name[:30] + "..." if len(name) > 30 else name,
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        self.name_label.pack(anchor="w")

        # UUID
        uuid = self.profile_data.get('uuid', '')[:20]
        ctk.CTkLabel(
            info_frame,
            text=f"ID: {uuid}...",
            font=ctk.CTkFont(family=FONT_FAMILY_MONO, size=11),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w")

        # Status
        status_text = "RUNNING" if self.is_running else "STOPPED"
        status_color = COLORS["success"] if self.is_running else COLORS["text_muted"]
        self.status_label = ctk.CTkLabel(
            info_frame,
            text=f"● {status_text}",
            font=ctk.CTkFont(size=11),
            text_color=status_color
        )
        self.status_label.pack(anchor="w")

        # Action buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.place(relx=1.0, x=-15, y=30, anchor="ne")

        if self.is_running:
            btn_text = "■ Đóng"
            btn_color = COLORS["error"]
            btn_hover = COLORS["error_hover"]
        else:
            btn_text = "▶ Mở"
            btn_color = COLORS["success"]
            btn_hover = COLORS["success_hover"]

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

        if self.on_edit:
            self.edit_btn = ctk.CTkButton(
                btn_frame,
                text="✏️",
                width=35,
                height=32,
                fg_color=COLORS["warning"],
                hover_color=COLORS["warning_hover"],
                corner_radius=8,
                command=lambda: self.on_edit(self.profile_data)
            )
            self.edit_btn.pack(side="left", padx=3)

    def _on_toggle_click(self):
        if self.on_toggle:
            self.on_toggle(self.profile_data, not self.is_running)

    def _on_enter(self, event):
        self.configure(border_color=COLORS["cyan"])

    def _on_leave(self, event):
        if not self.is_selected:
            self.configure(border_color=COLORS["border"])

    def _on_checkbox_change(self):
        self.is_selected = self.checkbox_var.get()
        border = COLORS["accent"] if self.is_selected else COLORS["border"]
        self.configure(border_color=border)
        if self.on_select:
            self.on_select(self.profile_data, self.is_selected)
