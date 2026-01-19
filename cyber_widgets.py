"""
CYBERPUNK 2077 Style Widgets for CustomTkinter
Version 2.0 - Enhanced with animations and effects

Widgets:
- CyberTitle: Glitchy title with accent triangle and animated lines
- CyberStatCard: Stats with top color bar and glow
- CyberButton: Neon buttons with hover effects
- CyberBadge: Status badges with LED indicator
- CyberTerminal: Log viewer with colored messages
- CyberNavItem: Sidebar navigation with active indicator
- CyberInput: Neon-styled input field
"""
import customtkinter as ctk
import tkinter as tk
from config import COLORS, TAB_COLORS, FONTS, SPACING, RADIUS, HEIGHTS
import random


class CyberTitle(ctk.CTkFrame):
    """
    Cyberpunk 2077 style title with:
    - Triangle accent (animated)
    - Glitch effect on text (cyan/magenta layers)
    - Animated lines above/below
    - Tab-specific colors

    Usage:
        title = CyberTitle(parent, title="PROFILES", subtitle="Manage accounts", tab_id="profiles")
        title.pack(fill="x", pady=20)
    """

    def __init__(self, master, title: str, subtitle: str = "", tab_id: str = "profiles", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.title_text = title.upper()
        self.subtitle_text = subtitle
        self.accent_color = TAB_COLORS.get(tab_id, COLORS["neon_cyan"])
        self._glitch_active = True
        self._glitch_step = 0
        self._line_anim_step = 0

        self._create_ui()
        self._start_animations()

    def _create_ui(self):
        # Main container
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x", pady=10)

        # Title row with accent
        title_row = ctk.CTkFrame(container, fg_color="transparent")
        title_row.pack(fill="x")

        # ===== ACCENT TRIANGLE using Canvas =====
        self.accent_canvas = tk.Canvas(
            title_row,
            width=50, height=50,
            bg=COLORS["bg_dark"],
            highlightthickness=0
        )
        self.accent_canvas.pack(side="left", padx=(0, 15))
        self._draw_triangle()

        # ===== TITLE TEXT WRAPPER =====
        text_wrapper = ctk.CTkFrame(title_row, fg_color="transparent")
        text_wrapper.pack(side="left", fill="x", expand=True)

        # Top line (animated width)
        self.top_line_container = ctk.CTkFrame(text_wrapper, fg_color="transparent", height=3)
        self.top_line_container.pack(fill="x", pady=(0, 8))
        self.top_line_container.pack_propagate(False)

        self.top_line = ctk.CTkFrame(
            self.top_line_container,
            height=3,
            fg_color=self.accent_color,
            corner_radius=0
        )
        self.top_line.pack(side="left", fill="y")

        # Title container for glitch layers
        title_container = ctk.CTkFrame(text_wrapper, fg_color="transparent", height=50)
        title_container.pack(anchor="w")

        # Glitch layer - CYAN (offset left)
        self.glitch_cyan = ctk.CTkLabel(
            title_container,
            text=self.title_text,
            font=ctk.CTkFont(family="Consolas", size=32, weight="bold"),
            text_color=COLORS["neon_cyan"]
        )

        # Glitch layer - MAGENTA (offset right)
        self.glitch_magenta = ctk.CTkLabel(
            title_container,
            text=self.title_text,
            font=ctk.CTkFont(family="Consolas", size=32, weight="bold"),
            text_color=COLORS["neon_magenta"]
        )

        # Main title (on top)
        self.title_main = ctk.CTkLabel(
            title_container,
            text=self.title_text,
            font=ctk.CTkFont(family="Consolas", size=32, weight="bold"),
            text_color=self.accent_color
        )
        self.title_main.pack(anchor="w")

        # Bottom line (shorter, animated)
        self.bottom_line_container = ctk.CTkFrame(text_wrapper, fg_color="transparent", height=3)
        self.bottom_line_container.pack(fill="x", pady=(8, 0))
        self.bottom_line_container.pack_propagate(False)

        self.bottom_line = ctk.CTkFrame(
            self.bottom_line_container,
            height=3,
            width=150,
            fg_color=self.accent_color,
            corner_radius=0
        )
        self.bottom_line.pack(side="left", fill="y")

        # ===== SUBTITLE with // prefix =====
        if self.subtitle_text:
            subtitle_frame = ctk.CTkFrame(container, fg_color="transparent")
            subtitle_frame.pack(fill="x", pady=(12, 0), padx=(65, 0))

            self.prefix_label = ctk.CTkLabel(
                subtitle_frame,
                text="//",
                font=ctk.CTkFont(family="Consolas", size=13),
                text_color=self.accent_color
            )
            self.prefix_label.pack(side="left")

            ctk.CTkLabel(
                subtitle_frame,
                text=f" {self.subtitle_text}",
                font=ctk.CTkFont(family="Consolas", size=13),
                text_color=COLORS["text_muted"]
            ).pack(side="left")

    def _draw_triangle(self):
        """Draw the accent triangle with glow effect"""
        self.accent_canvas.delete("all")
        # Triangle pointing bottom-right (cyberpunk style)
        points = [5, 45, 45, 45, 45, 5]
        self.accent_canvas.create_polygon(
            points,
            fill=self.accent_color,
            outline=""
        )

    def _start_animations(self):
        """Start all animations"""
        self._animate_glitch()
        self._animate_lines()
        self._animate_prefix()
        self._animate_triangle()

    def _animate_glitch(self):
        """Glitch effect - randomly show cyan/magenta offset layers"""
        if not self._glitch_active:
            return

        self._glitch_step += 1

        # Random glitch every ~3 seconds (30 steps * 100ms)
        if self._glitch_step >= 30:
            self._glitch_step = 0
            if random.random() > 0.5:  # 50% chance to glitch
                self._trigger_glitch()

        self.after(100, self._animate_glitch)

    def _trigger_glitch(self):
        """Show glitch effect briefly"""
        try:
            # Show offset layers
            self.glitch_cyan.place(x=-3, y=0)
            self.glitch_magenta.place(x=3, y=0)

            # Rapid glitch sequence
            self.after(50, lambda: self.glitch_cyan.place(x=2, y=-1))
            self.after(50, lambda: self.glitch_magenta.place(x=-2, y=1))
            self.after(100, lambda: self.glitch_cyan.place(x=-2, y=1))
            self.after(100, lambda: self.glitch_magenta.place(x=2, y=-1))
            self.after(150, self._end_glitch)
        except:
            pass

    def _end_glitch(self):
        """Hide glitch layers"""
        try:
            self.glitch_cyan.place_forget()
            self.glitch_magenta.place_forget()
        except:
            pass

    def _animate_lines(self):
        """Animate the line widths (pulse effect)"""
        if not self._glitch_active:
            return

        self._line_anim_step = (self._line_anim_step + 1) % 40

        # Calculate width factor (60% to 100%)
        if self._line_anim_step < 20:
            factor = 0.6 + (self._line_anim_step / 20) * 0.4
        else:
            factor = 1.0 - ((self._line_anim_step - 20) / 20) * 0.4

        try:
            # Top line - full width
            self.top_line.configure(width=int(300 * factor))
            # Bottom line - shorter
            self.bottom_line.configure(width=int(200 * factor))
        except:
            pass

        self.after(50, self._animate_lines)

    def _animate_prefix(self):
        """Blink the // prefix"""
        if not self._glitch_active:
            return

        if hasattr(self, 'prefix_label'):
            try:
                current = self.prefix_label.cget("text_color")
                if current == self.accent_color:
                    self.prefix_label.configure(text_color=COLORS["text_muted"])
                else:
                    self.prefix_label.configure(text_color=self.accent_color)
            except:
                pass
        self.after(800, self._animate_prefix)

    def _animate_triangle(self):
        """Pulse the triangle color"""
        if not self._glitch_active:
            return

        # Redraw with slight color variation
        self._draw_triangle()
        self.after(2000, self._animate_triangle)

    def destroy(self):
        """Cleanup"""
        self._glitch_active = False
        super().destroy()


class CyberStatCard(ctk.CTkFrame):
    """
    Stat card with:
    - Top color bar (animated glow)
    - Large number display
    - Label and change indicator

    Usage:
        card = CyberStatCard(parent, label="TOTAL", value="247", change="+12", color="cyan")
        card.pack()
    """

    def __init__(self, master, label: str, value: str, change: str = "",
                 color: str = "cyan", tab_id: str = None, **kwargs):
        super().__init__(master, fg_color=COLORS["bg_card"], corner_radius=12, **kwargs)

        if tab_id:
            self.accent_color = TAB_COLORS.get(tab_id, COLORS["neon_cyan"])
        else:
            color_map = {
                "cyan": COLORS["neon_cyan"],
                "green": COLORS["neon_green"],
                "purple": COLORS["neon_purple"],
                "yellow": COLORS["neon_yellow"],
                "magenta": COLORS["neon_magenta"],
                "orange": COLORS["neon_orange"],
            }
            self.accent_color = color_map.get(color, COLORS["neon_cyan"])

        self._create_ui(label, value, change)

    def _create_ui(self, label: str, value: str, change: str):
        # Top color bar
        self.top_bar = ctk.CTkFrame(
            self,
            height=4,
            fg_color=self.accent_color,
            corner_radius=0
        )
        self.top_bar.pack(fill="x")

        # Content
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=16)

        # Label (uppercase, mono font)
        ctk.CTkLabel(
            content,
            text=label.upper(),
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=COLORS["text_muted"]
        ).pack(anchor="w")

        # Value (large, bold, colored)
        self.value_label = ctk.CTkLabel(
            content,
            text=value,
            font=ctk.CTkFont(family="Consolas", size=42, weight="bold"),
            text_color=self.accent_color
        )
        self.value_label.pack(anchor="w", pady=(8, 4))

        # Change indicator
        if change:
            change_color = COLORS["neon_green"] if change.startswith("+") or change.startswith("▲") else COLORS["text_muted"]
            ctk.CTkLabel(
                content,
                text=change,
                font=ctk.CTkFont(family="Consolas", size=11),
                text_color=change_color
            ).pack(anchor="w")

    def update_value(self, new_value: str):
        """Update the displayed value"""
        self.value_label.configure(text=new_value)


class CyberButton(ctk.CTkButton):
    """
    Neon button with hover glow effect

    Variants: primary, success, danger, ghost, secondary

    Usage:
        btn = CyberButton(parent, text="SYNC", variant="primary", command=my_func)
        btn.pack()
    """

    def __init__(self, master, text: str, variant: str = "primary",
                 size: str = "md", icon: str = None, **kwargs):

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
            "sm": {"height": 28, "font_size": 10},
            "md": {"height": 36, "font_size": 11},
            "lg": {"height": 44, "font_size": 13},
        }
        size_config = sizes.get(size, sizes["md"])

        super().__init__(
            master,
            text=display_text.upper() if display_text else "",
            font=ctk.CTkFont(family="Consolas", size=size_config["font_size"], weight="bold"),
            fg_color=config["fg_color"],
            border_color=config["border_color"],
            text_color=config["text_color"],
            hover_color=config["hover_color"],
            border_width=1,
            corner_radius=6,
            height=size_config["height"],
            **kwargs
        )


class CyberCard(ctk.CTkFrame):
    """
    Card with left accent bar and header

    Usage:
        card = CyberCard(parent, "PROFILE DATABASE", accent_color="#00f0ff")
        card.pack(fill="both", expand=True)

        # Add content to card.content_frame
        label = ctk.CTkLabel(card.content_frame, text="Hello")
        label.pack()
    """

    def __init__(self, master, title: str = "", accent_color: str = None, count: str = "", **kwargs):
        super().__init__(master, fg_color=COLORS["bg_card"], corner_radius=12, **kwargs)

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
                text=title.upper(),
                font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
                text_color=COLORS["text_primary"]
            ).pack(side="left", padx=(12, 0))

            # Count (optional)
            if count:
                ctk.CTkLabel(
                    header_inner,
                    text=f"[{count}]",
                    font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
                    text_color=self.accent_color
                ).pack(side="left", padx=(8, 0))

        # Content frame
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=16, pady=16)


class CyberBadge(ctk.CTkFrame):
    """
    Badge with LED indicator and left border accent

    Usage:
        badge = CyberBadge(parent, "RUNNING", "green", show_led=True, pulse=True)
        badge.pack()
    """

    def __init__(self, master, text: str, color: str = "cyan",
                 show_led: bool = False, pulse: bool = False, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        color_map = {
            "cyan": COLORS["neon_cyan"],
            "green": COLORS["neon_green"],
            "purple": COLORS["neon_purple"],
            "yellow": COLORS["neon_yellow"],
            "gray": COLORS["text_muted"],
            "red": COLORS["neon_red"],
            "magenta": COLORS["neon_magenta"],
        }
        self.accent_color = color_map.get(color, COLORS["neon_cyan"])
        self._pulse_active = pulse
        self._led_on = True

        self._create_ui(text, show_led)
        if pulse:
            self._start_pulse()

    def _create_ui(self, text: str, show_led: bool):
        # Inner frame with left border effect
        inner = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_secondary"],
            corner_radius=6
        )
        inner.pack()

        # Left border
        border = ctk.CTkFrame(inner, width=3, fg_color=self.accent_color, corner_radius=0)
        border.pack(side="left", fill="y")

        content = ctk.CTkFrame(inner, fg_color="transparent")
        content.pack(side="left", padx=(10, 14), pady=6)

        # LED indicator
        if show_led:
            self.led_label = ctk.CTkLabel(
                content,
                text="●",
                font=ctk.CTkFont(size=10),
                text_color=self.accent_color
            )
            self.led_label.pack(side="left", padx=(0, 8))

        # Text
        ctk.CTkLabel(
            content,
            text=text.upper(),
            font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
            text_color=self.accent_color
        ).pack(side="left")

    def _start_pulse(self):
        """Pulse animation for LED"""
        if not self._pulse_active:
            return

        try:
            self._led_on = not self._led_on
            if hasattr(self, 'led_label'):
                if self._led_on:
                    self.led_label.configure(text_color=self.accent_color)
                else:
                    self.led_label.configure(text_color=COLORS["bg_dark"])
        except:
            pass
        self.after(750, self._start_pulse)

    def destroy(self):
        self._pulse_active = False
        super().destroy()


class CyberTerminal(ctk.CTkFrame):
    """
    Terminal-style log viewer with colored messages

    Usage:
        term = CyberTerminal(parent)
        term.pack(fill="both", expand=True)
        term.add_log("System started", "info")
        term.add_log("Connected!", "success")
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=COLORS["bg_darker"], corner_radius=8, **kwargs)

        self._create_ui()

    def _create_ui(self):
        # Terminal display
        self.text_widget = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="transparent",
            text_color=COLORS["text_secondary"],
            corner_radius=0,
            state="disabled",
            wrap="word"
        )
        self.text_widget.pack(fill="both", expand=True, padx=10, pady=10)

        # Configure tags for colors
        self.text_widget._textbox.tag_configure("time", foreground=COLORS["text_muted"])
        self.text_widget._textbox.tag_configure("info", foreground=COLORS["neon_cyan"])
        self.text_widget._textbox.tag_configure("success", foreground=COLORS["neon_green"])
        self.text_widget._textbox.tag_configure("warning", foreground=COLORS["neon_yellow"])
        self.text_widget._textbox.tag_configure("error", foreground=COLORS["neon_red"])

    def add_log(self, message: str, log_type: str = "info"):
        """Add a log entry"""
        from datetime import datetime
        timestamp = datetime.now().strftime("[%H:%M:%S]")

        self.text_widget.configure(state="normal")
        self.text_widget._textbox.insert("end", timestamp, "time")
        self.text_widget._textbox.insert("end", f" {message}\n", log_type)
        self.text_widget.configure(state="disabled")

        # Auto-scroll
        self.text_widget._textbox.see("end")

    def clear(self):
        """Clear all logs"""
        self.text_widget.configure(state="normal")
        self.text_widget._textbox.delete("1.0", "end")
        self.text_widget.configure(state="disabled")

    @property
    def textbox(self):
        """Return internal textbox for compatibility"""
        return self.text_widget._textbox


class CyberNavItem(ctk.CTkFrame):
    """
    Navigation item with active indicator bar

    Usage:
        nav = CyberNavItem(parent, tab_id="profiles", icon="◆", text="PROFILES", command=on_click)
        nav.pack(fill="x")
    """

    def __init__(self, master, tab_id: str, icon: str, text: str, command=None, **kwargs):
        super().__init__(master, fg_color="transparent", height=48, **kwargs)
        self.pack_propagate(False)

        self.tab_id = tab_id
        self.command = command
        self.accent_color = TAB_COLORS.get(tab_id, COLORS["neon_cyan"])
        self._is_active = False

        self._create_ui(icon, text)
        self._bind_events()

    def _create_ui(self, icon: str, text: str):
        # Inner container
        self.inner = ctk.CTkFrame(self, fg_color="transparent", corner_radius=8)
        self.inner.pack(fill="both", expand=True, padx=8, pady=2)

        # Active indicator bar (hidden by default)
        self.indicator = ctk.CTkFrame(
            self.inner,
            width=4,
            fg_color=self.accent_color,
            corner_radius=2
        )

        # Content
        content = ctk.CTkFrame(self.inner, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=12)

        # Icon
        self.icon_label = ctk.CTkLabel(
            content,
            text=icon,
            font=ctk.CTkFont(size=16),
            width=30
        )
        self.icon_label.pack(side="left")

        # Text
        self.text_label = ctk.CTkLabel(
            content,
            text=text.upper(),
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            text_color=COLORS["text_secondary"]
        )
        self.text_label.pack(side="left", padx=(8, 0))

    def _bind_events(self):
        """Bind hover and click events"""
        for widget in [self, self.inner, self.icon_label, self.text_label]:
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)
            widget.bind("<Button-1>", self._on_click)

    def _on_enter(self, event=None):
        if not self._is_active:
            self.inner.configure(fg_color=COLORS["bg_hover"])
            self.text_label.configure(text_color=COLORS["text_primary"])

    def _on_leave(self, event=None):
        if not self._is_active:
            self.inner.configure(fg_color="transparent")
            self.text_label.configure(text_color=COLORS["text_secondary"])

    def _on_click(self, event=None):
        if self.command:
            self.command(self.tab_id)

    def set_active(self, active: bool):
        """Set active state"""
        self._is_active = active
        if active:
            self.inner.configure(fg_color=COLORS["bg_card"])
            self.text_label.configure(text_color=self.accent_color)
            self.indicator.place(relx=0, rely=0.2, relheight=0.6)
        else:
            self.inner.configure(fg_color="transparent")
            self.text_label.configure(text_color=COLORS["text_secondary"])
            self.indicator.place_forget()


class CyberInput(ctk.CTkEntry):
    """
    Cyberpunk styled input field

    Usage:
        inp = CyberInput(parent, placeholder="Search...")
        inp.pack()
    """

    def __init__(self, master, placeholder: str = "", **kwargs):
        super().__init__(
            master,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color=COLORS["bg_dark"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            placeholder_text=placeholder,
            placeholder_text_color=COLORS["text_muted"],
            corner_radius=6,
            border_width=1,
            height=36,
            **kwargs
        )

        # Bind focus events for glow effect
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)

    def _on_focus_in(self, event=None):
        self.configure(border_color=COLORS["neon_cyan"])

    def _on_focus_out(self, event=None):
        self.configure(border_color=COLORS["border"])


class CyberSearchBar(ctk.CTkFrame):
    """
    Search bar with icon

    Usage:
        search = CyberSearchBar(parent, placeholder="Search profiles...")
        search.pack()
    """

    def __init__(self, master, placeholder: str = "Search...", on_search=None, **kwargs):
        super().__init__(master, fg_color=COLORS["bg_dark"], corner_radius=6, **kwargs)

        self.on_search = on_search
        self.configure(border_width=1, border_color=COLORS["border"])

        # Icon
        ctk.CTkLabel(
            self,
            text="⌕",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text_muted"],
            width=30
        ).pack(side="left", padx=(10, 0))

        # Entry
        self.entry = ctk.CTkEntry(
            self,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="transparent",
            border_width=0,
            text_color=COLORS["text_primary"],
            placeholder_text=placeholder,
            placeholder_text_color=COLORS["text_muted"]
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(5, 10), pady=8)

        # Bind events
        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        if on_search:
            self.entry.bind("<Return>", lambda e: on_search(self.entry.get()))

    def _on_focus_in(self, event=None):
        self.configure(border_color=COLORS["neon_cyan"])

    def _on_focus_out(self, event=None):
        self.configure(border_color=COLORS["border"])

    def get(self):
        return self.entry.get()

    def set(self, value: str):
        self.entry.delete(0, "end")
        self.entry.insert(0, value)
