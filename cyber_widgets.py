"""
CYBERPUNK WIDGETS
Custom widgets with neon effects and glitch animations
"""
import customtkinter as ctk
from config import COLORS, TAB_COLORS, FONTS, SPACING, RADIUS, HEIGHTS


class CyberTitle(ctk.CTkFrame):
    """
    Cyberpunk Title with Glitch Effect

    Usage:
        title = CyberTitle(parent, "PROFILES", "Quan ly profiles", "profiles")
        title.pack(fill="x", pady=(0, 24))
    """

    def __init__(self, master, title: str, subtitle: str = "", tab_id: str = "profiles", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.title_text = title
        self.tab_id = tab_id
        self.accent_color = TAB_COLORS.get(tab_id, COLORS["neon_cyan"])

        # Animation state
        self._glitch_active = True
        self._glitch_step = 0

        self._create_ui(title, subtitle)
        self._start_glitch_animation()

    def _create_ui(self, title: str, subtitle: str):
        """Create UI"""
        # Container
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x")

        # Row with accent + title
        title_row = ctk.CTkFrame(container, fg_color="transparent")
        title_row.pack(fill="x")

        # ===== ACCENT SYMBOL =====
        self.accent_frame = ctk.CTkFrame(title_row, fg_color="transparent", width=50, height=50)
        self.accent_frame.pack(side="left")
        self.accent_frame.pack_propagate(False)

        self.accent_label = ctk.CTkLabel(
            self.accent_frame,
            text="◢",
            font=ctk.CTkFont(size=36),
            text_color=self.accent_color
        )
        self.accent_label.place(relx=0.5, rely=0.5, anchor="center")

        # ===== TITLE FRAME =====
        title_frame = ctk.CTkFrame(title_row, fg_color="transparent")
        title_frame.pack(side="left", padx=(12, 0))

        # Top line (decorative)
        self.top_line = ctk.CTkFrame(title_frame, height=2, fg_color=self.accent_color)
        self.top_line.pack(fill="x", pady=(0, 6))

        # Title text container
        text_container = ctk.CTkFrame(title_frame, fg_color="transparent")
        text_container.pack()

        # Glitch layer (behind)
        self.title_glitch = ctk.CTkLabel(
            text_container,
            text=title,
            font=ctk.CTkFont(family=FONTS["family_display"], size=FONTS["size_title"], weight="bold"),
            text_color=COLORS["bg_dark"]
        )
        self.title_glitch.place(x=0, y=0)

        # Main title
        self.title_main = ctk.CTkLabel(
            text_container,
            text=title,
            font=ctk.CTkFont(family=FONTS["family_display"], size=FONTS["size_title"], weight="bold"),
            text_color=COLORS["text_primary"]
        )
        self.title_main.pack()

        # Bottom line (shorter)
        self.bottom_line = ctk.CTkFrame(title_frame, height=2, width=150, fg_color=self.accent_color)
        self.bottom_line.pack(anchor="w", pady=(6, 0))

        # ===== SUBTITLE =====
        if subtitle:
            subtitle_frame = ctk.CTkFrame(container, fg_color="transparent")
            subtitle_frame.pack(fill="x", pady=(8, 0))

            # Prefix "//"
            ctk.CTkLabel(
                subtitle_frame,
                text="//",
                font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_base"]),
                text_color=self.accent_color
            ).pack(side="left", padx=(62, 4))

            ctk.CTkLabel(
                subtitle_frame,
                text=subtitle,
                font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_base"]),
                text_color=COLORS["text_muted"]
            ).pack(side="left")

    def _start_glitch_animation(self):
        """Start glitch animation"""
        def animate():
            if not self._glitch_active:
                return

            self._glitch_step = (self._glitch_step + 1) % 80

            try:
                if self._glitch_step < 3:
                    offset = 3 if self._glitch_step % 2 == 0 else -3
                    self.title_glitch.place(x=offset, y=0)

                    if self._glitch_step % 2 == 0:
                        self.title_glitch.configure(text_color=COLORS["neon_magenta"])
                        self.accent_label.configure(text_color=COLORS["neon_magenta"])
                    else:
                        self.title_glitch.configure(text_color=COLORS["neon_cyan"])
                        self.accent_label.configure(text_color=COLORS["neon_cyan"])
                else:
                    self.title_glitch.place(x=0, y=0)
                    self.title_glitch.configure(text_color=COLORS["bg_dark"])
                    self.accent_label.configure(text_color=self.accent_color)

                self.after(100, animate)
            except:
                pass

        animate()

    def destroy(self):
        """Cleanup"""
        self._glitch_active = False
        super().destroy()


class CyberCard(ctk.CTkFrame):
    """
    Card with left accent bar

    Usage:
        card = CyberCard(parent, "PROFILE DATABASE", accent_color="#00f0ff")
        card.pack(fill="both", expand=True)

        # Add content to card.content_frame
        label = ctk.CTkLabel(card.content_frame, text="Hello")
        label.pack()
    """

    def __init__(self, master, title: str = "", accent_color: str = None, count: str = "", **kwargs):
        super().__init__(master, fg_color=COLORS["bg_card"], corner_radius=RADIUS["lg"], **kwargs)

        self.accent_color = accent_color or COLORS["neon_cyan"]

        # Header (if title)
        if title:
            header = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=0)
            header.pack(fill="x")

            header_inner = ctk.CTkFrame(header, fg_color="transparent")
            header_inner.pack(fill="x", padx=16, pady=14)

            # Accent bar
            accent_bar = ctk.CTkFrame(header_inner, width=4, height=24, fg_color=self.accent_color, corner_radius=2)
            accent_bar.pack(side="left")

            # Title
            ctk.CTkLabel(
                header_inner,
                text=title,
                font=ctk.CTkFont(family=FONTS["family_display"], size=FONTS["size_sm"], weight="bold"),
                text_color=COLORS["text_primary"]
            ).pack(side="left", padx=(12, 0))

            # Count (optional)
            if count:
                ctk.CTkLabel(
                    header_inner,
                    text=count,
                    font=ctk.CTkFont(family=FONTS["family_display"], size=FONTS["size_sm"], weight="bold"),
                    text_color=self.accent_color
                ).pack(side="left", padx=(8, 0))

        # Content frame
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=16, pady=16)


class CyberStatCard(ctk.CTkFrame):
    """
    Stat Card with large number and top accent bar

    Usage:
        stat = CyberStatCard(parent, "TOTAL PROFILES", "247", "+12 this week", "cyan")
        stat.pack(side="left", fill="both", expand=True)
    """

    def __init__(self, master, label: str, value: str, change: str = "", color: str = "cyan", **kwargs):
        super().__init__(master, fg_color=COLORS["bg_card"], corner_radius=RADIUS["lg"], **kwargs)

        # Color mapping
        color_map = {
            "cyan": COLORS["neon_cyan"],
            "green": COLORS["neon_green"],
            "purple": COLORS["neon_purple"],
            "magenta": COLORS["neon_magenta"],
            "yellow": COLORS["neon_yellow"],
            "orange": COLORS["neon_orange"],
        }
        accent = color_map.get(color, COLORS["neon_cyan"])

        # Top accent bar
        accent_bar = ctk.CTkFrame(self, height=3, fg_color=accent, corner_radius=0)
        accent_bar.pack(fill="x")

        # Content
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)

        # Label
        ctk.CTkLabel(
            content,
            text=label,
            font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_xs"]),
            text_color=COLORS["text_muted"]
        ).pack(anchor="w")

        # Value (large number)
        self.value_label = ctk.CTkLabel(
            content,
            text=value,
            font=ctk.CTkFont(family=FONTS["family_display"], size=36, weight="bold"),
            text_color=accent
        )
        self.value_label.pack(anchor="w", pady=(8, 4))

        # Change indicator
        if change:
            ctk.CTkLabel(
                content,
                text=change,
                font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_xs"]),
                text_color=COLORS["neon_green"]
            ).pack(anchor="w")

        # Store value label reference for updates
        self._value_label = self.value_label


class CyberButton(ctk.CTkButton):
    """
    Neon Button with glow effect

    Variants: primary, success, danger, ghost

    Usage:
        btn = CyberButton(parent, "SYNC", variant="primary", command=my_func)
        btn.pack()
    """

    def __init__(self, master, text: str, variant: str = "primary", size: str = "md", icon: str = None, **kwargs):
        # Combine icon with text if provided
        display_text = f"{icon} {text}" if icon and text else (icon or text)

        # Color configs
        variants = {
            "primary": {
                "fg_color": "transparent",
                "border_color": COLORS["neon_cyan"],
                "text_color": COLORS["neon_cyan"],
                "hover_color": COLORS["neon_cyan"],
            },
            "success": {
                "fg_color": COLORS["neon_green"],
                "border_color": COLORS["neon_green"],
                "text_color": COLORS["bg_dark"],
                "hover_color": "#00d956",
            },
            "danger": {
                "fg_color": "transparent",
                "border_color": COLORS["neon_red"],
                "text_color": COLORS["neon_red"],
                "hover_color": COLORS["neon_red"],
            },
            "ghost": {
                "fg_color": "transparent",
                "border_color": COLORS["border"],
                "text_color": COLORS["text_secondary"],
                "hover_color": COLORS["bg_hover"],
            },
            "secondary": {
                "fg_color": COLORS["neon_magenta"],
                "border_color": COLORS["neon_magenta"],
                "text_color": COLORS["text_primary"],
                "hover_color": "#d4008c",
            },
        }

        config = variants.get(variant, variants["primary"])

        # Size configs
        sizes = {
            "sm": {"height": HEIGHTS["button_sm"], "font_size": FONTS["size_xs"]},
            "md": {"height": HEIGHTS["button"], "font_size": FONTS["size_sm"]},
            "lg": {"height": HEIGHTS["button_lg"], "font_size": FONTS["size_base"]},
        }
        size_config = sizes.get(size, sizes["md"])

        super().__init__(
            master,
            text=display_text,
            font=ctk.CTkFont(family=FONTS["family_display"], size=size_config["font_size"], weight="bold"),
            fg_color=config["fg_color"],
            border_color=config["border_color"],
            text_color=config["text_color"],
            hover_color=config["hover_color"],
            border_width=1,
            corner_radius=RADIUS["md"],
            height=size_config["height"],
            **kwargs
        )


class CyberBadge(ctk.CTkFrame):
    """
    Badge with LED indicator

    Usage:
        badge = CyberBadge(parent, "RUNNING", "green", show_led=True, pulse=True)
        badge.pack()
    """

    def __init__(self, master, text: str, color: str = "cyan", show_led: bool = False, pulse: bool = False, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        color_map = {
            "cyan": COLORS["neon_cyan"],
            "green": COLORS["neon_green"],
            "purple": COLORS["neon_purple"],
            "yellow": COLORS["neon_yellow"],
            "gray": COLORS["text_muted"],
            "red": COLORS["neon_red"],
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
            font=ctk.CTkFont(family=FONTS["family_display"], size=FONTS["size_xs"], weight="bold"),
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


class CyberTerminal(ctk.CTkFrame):
    """
    Terminal/Log display with neon colors

    Usage:
        terminal = CyberTerminal(parent)
        terminal.pack(fill="both", expand=True)

        terminal.add_line("System started", "success")
        terminal.add_line("Loading...", "info")
        terminal.add_line("Error occurred", "error")
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=COLORS["bg_darker"], corner_radius=RADIUS["lg"], **kwargs)

        # Textbox
        self.textbox = ctk.CTkTextbox(
            self,
            fg_color="transparent",
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_xs"]),
            corner_radius=0,
            wrap="word"
        )
        self.textbox.pack(fill="both", expand=True, padx=12, pady=12)

        # Configure tags
        self.textbox._textbox.tag_config("timestamp", foreground=COLORS["text_muted"])
        self.textbox._textbox.tag_config("info", foreground=COLORS["neon_cyan"])
        self.textbox._textbox.tag_config("success", foreground=COLORS["neon_green"])
        self.textbox._textbox.tag_config("warning", foreground=COLORS["neon_yellow"])
        self.textbox._textbox.tag_config("error", foreground=COLORS["neon_red"])

    def add_line(self, message: str, level: str = "info"):
        """Add log line"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")

        self.textbox.insert("end", f"[{timestamp}] ", "timestamp")
        self.textbox.insert("end", f"{message}\n", level)
        self.textbox.see("end")

    def clear(self):
        """Clear all logs"""
        self.textbox.delete("1.0", "end")


class CyberNavItem(ctk.CTkFrame):
    """
    Navigation item for sidebar

    Usage:
        nav = CyberNavItem(sidebar, "profiles", "User", "Profiles", command=switch_tab)
        nav.pack(fill="x")
        nav.set_active(True)
    """

    def __init__(self, master, tab_id: str, icon: str, text: str, command=None, **kwargs):
        super().__init__(master, fg_color="transparent", height=HEIGHTS["nav_item"], **kwargs)
        self.pack_propagate(False)

        self.tab_id = tab_id
        self.command = command
        self.accent_color = TAB_COLORS.get(tab_id, COLORS["neon_cyan"])
        self._active = False

        # Inner container
        self.inner = ctk.CTkFrame(self, fg_color="transparent")
        self.inner.pack(fill="both", expand=True, padx=4)

        # Indicator bar (hidden by default)
        self.indicator = ctk.CTkFrame(self.inner, width=4, fg_color=self.accent_color, corner_radius=2)

        # Content
        content = ctk.CTkFrame(self.inner, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=12)

        # Icon
        self.icon_label = ctk.CTkLabel(content, text=icon, font=ctk.CTkFont(size=18), width=28)
        self.icon_label.pack(side="left")

        # Text
        self.text_label = ctk.CTkLabel(
            content,
            text=text,
            font=ctk.CTkFont(size=FONTS["size_base"], weight="bold"),
            text_color=COLORS["text_secondary"]
        )
        self.text_label.pack(side="left", padx=8)

        # Bindings
        for widget in [self, self.inner, content, self.icon_label, self.text_label]:
            widget.bind("<Button-1>", self._on_click)
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)

    def _on_click(self, event):
        if self.command:
            self.command(self.tab_id)

    def _on_enter(self, event):
        if not self._active:
            self.inner.configure(fg_color=COLORS["bg_hover"])

    def _on_leave(self, event):
        if not self._active:
            self.inner.configure(fg_color="transparent")

    def set_active(self, active: bool):
        """Set active state"""
        self._active = active

        if active:
            self.inner.configure(fg_color=COLORS["bg_card"])
            self.indicator.place(relx=0, rely=0.5, anchor="w", relheight=0.5)
            self.text_label.configure(text_color=self.accent_color)
        else:
            self.inner.configure(fg_color="transparent")
            self.indicator.place_forget()
            self.text_label.configure(text_color=COLORS["text_secondary"])


class CyberInput(ctk.CTkEntry):
    """
    Cyberpunk styled input field

    Usage:
        entry = CyberInput(parent, placeholder="Enter text...")
        entry.pack(fill="x")
    """

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
        self.bind("<FocusIn>", lambda e: self.configure(border_color=COLORS["border_focus"]))
        self.bind("<FocusOut>", lambda e: self.configure(border_color=COLORS["border"]))


class CyberSearchBar(ctk.CTkFrame):
    """
    Cyberpunk search bar

    Usage:
        search = CyberSearchBar(parent, placeholder="Search...", on_search=callback)
        search.pack(fill="x")
    """

    def __init__(self, master, placeholder: str = "Search...", on_search=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.on_search = on_search

        self.search_entry = CyberInput(self, placeholder=placeholder, width=250)
        self.search_entry.pack(side="left", padx=(0, 8))
        self.search_entry.bind("<Return>", self._do_search)

        self.search_btn = CyberButton(
            self,
            text="SEARCH",
            variant="primary",
            size="sm",
            width=80,
            command=self._do_search
        )
        self.search_btn.pack(side="left")

    def _do_search(self, event=None):
        if self.on_search:
            self.on_search(self.search_entry.get())

    def get_value(self) -> str:
        return self.search_entry.get()
