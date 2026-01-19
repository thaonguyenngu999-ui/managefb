"""
CYBERPUNK 2077 THEME CONFIG
FB Manager Pro - Neon Dark Theme
"""

# ==================== APP INFO ====================
APP_NAME = "FB Manager Pro"
APP_VERSION = "2.0.77"

# ==================== HIDEMIUM API ====================
HIDEMIUM_BASE_URL = "http://127.0.0.1:2222"
HIDEMIUM_TOKEN = "Cu6tDTR2N1HhTxlMyrQubY2ad56eQzWOjVrrb"

# ==================== CYBERPUNK COLORS ====================
COLORS = {
    # Backgrounds - Deep dark with cyber tint
    "bg_dark": "#05050a",
    "bg_darker": "#020204",
    "bg_main": "#05050a",
    "bg_sidebar": "#020204",
    "bg_card": "#0a0a12",
    "bg_secondary": "#08080f",
    "bg_elevated": "#0f0f1a",
    "bg_hover": "#12121f",
    "bg_input": "#08080f",
    "bg_header": "#0a0a12",
    "bg_card_hover": "#12121f",

    # Neon Colors - CYBERPUNK
    "neon_cyan": "#00f0ff",
    "neon_magenta": "#ff00a8",
    "neon_yellow": "#fcee0a",
    "neon_green": "#00ff66",
    "neon_purple": "#bf00ff",
    "neon_orange": "#ff6b00",
    "neon_red": "#ff003c",
    "neon_pink": "#ff2a6d",

    # Primary = Cyan
    "primary": "#00f0ff",
    "primary_hover": "#00c8d4",
    "primary_dark": "#00a0aa",
    "primary_light": "rgba(0, 240, 255, 0.15)",
    "primary_glow": "rgba(0, 240, 255, 0.4)",

    # Secondary = Magenta
    "secondary": "#ff00a8",
    "secondary_hover": "#d4008c",
    "secondary_dark": "#aa0070",
    "secondary_light": "rgba(255, 0, 168, 0.15)",

    # Accent
    "accent": "#00f0ff",
    "accent_hover": "#00c8d4",
    "accent_pink": "#ff00a8",
    "accent_pink_hover": "#d4008c",

    # Status Colors
    "success": "#00ff66",
    "success_hover": "#00d956",
    "warning": "#fcee0a",
    "error": "#ff003c",
    "error_hover": "#d40032",
    "danger": "#ff003c",
    "info": "#00f0ff",
    "online": "#00ff66",
    "offline": "#52525b",

    # Text
    "text_primary": "#e4e4e7",
    "text_secondary": "#a1a1aa",
    "text_muted": "#71717a",
    "text_tertiary": "#52525b",
    "text_link": "#00f0ff",

    # Borders
    "border": "#1a1a2e",
    "border_light": "#27273a",
    "border_hover": "#3f3f5a",
    "border_focus": "#00f0ff",
    "divider": "#1a1a2e",

    # Special
    "gradient_start": "#00f0ff",
    "gradient_end": "#ff00a8",
    "shadow": "rgba(0,0,0,0.5)",
    "overlay": "rgba(0,0,0,0.7)",
    "glow_cyan": "rgba(0, 240, 255, 0.4)",
    "glow_magenta": "rgba(255, 0, 168, 0.4)",
    "glow_green": "rgba(0, 255, 102, 0.4)",
}

# ==================== TAB ACCENT COLORS ====================
TAB_COLORS = {
    "profiles": "#00f0ff",      # Cyan
    "login": "#00ff66",         # Green
    "pages": "#bf00ff",         # Purple
    "reels_page": "#ff00a8",    # Magenta
    "content": "#fcee0a",       # Yellow
    "groups": "#ff6b00",        # Orange
    "scripts": "#00f0ff",       # Cyan
    "posts": "#00ff66",         # Green
}

# ==================== OS BADGE COLORS ====================
OS_COLORS = {
    "win": "#00f0ff",
    "mac": "#bf00ff",
    "linux": "#fcee0a",
    "android": "#00ff66",
    "ios": "#ff00a8",
}

# ==================== FONTS ====================
FONTS = {
    # Primary: Display fonts
    "family_display": "Segoe UI",  # Windows - SF Pro Display on Mac
    "family_mono": "Consolas",     # Windows - SF Mono on Mac
    "family": "Segoe UI",

    # Sizes
    "size_xs": 10,
    "size_sm": 11,
    "size_base": 13,
    "size_md": 13,
    "size_lg": 15,
    "size_xl": 18,
    "size_2xl": 24,
    "size_3xl": 32,
    "size_title": 28,
}

# ==================== SPACING ====================
SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 24,
    "2xl": 32,
    "3xl": 48,
    "4xl": 64,
    "xxl": 32,  # Legacy alias
}

# ==================== BORDER RADIUS ====================
RADIUS = {
    "sm": 4,
    "md": 6,
    "lg": 8,
    "xl": 12,
    "2xl": 16,
    "full": 9999,
}

# ==================== HEIGHTS ====================
HEIGHTS = {
    "input": 40,
    "button": 40,
    "button_sm": 32,
    "button_lg": 48,
    "header": 56,
    "status_bar": 36,
    "nav_item": 44,
}

# ==================== WINDOW ====================
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 850
SIDEBAR_WIDTH = 240
SIDEBAR_EXPANDED = 240
LOG_PANEL_WIDTH = 360

# ==================== ANIMATION TIMING ====================
GLITCH_INTERVAL = 100
GLITCH_DURATION = 3
GLITCH_CYCLE = 80
