# Cấu hình ứng dụng
APP_NAME = "FB Manager Pro"
APP_VERSION = "2.0.0"

# Hidemium API Config
HIDEMIUM_BASE_URL = "http://127.0.0.1:2222"
HIDEMIUM_TOKEN = "Cu6tDTR2N1HhTxlMyrQubY2ad56eQzWOjVrrb"

# ========== CYBERPUNK UI DESIGN ==========

# Color Palette - Cyberpunk Neon
COLORS = {
    # Background - Deep dark with blue tint
    "bg_dark": "#0a0a0f",           # Almost black
    "bg_secondary": "#0f0f1a",      # Dark blue-black
    "bg_card": "#151520",           # Card background
    "bg_card_hover": "#1a1a2e",     # Card hover
    "bg_hover": "#1a1a2e",          # General hover
    "bg_elevated": "#1e1e30",       # Elevated elements

    # Neon Cyan - Primary
    "accent": "#00f0ff",            # Bright cyan
    "accent_hover": "#00d4e0",      # Cyan hover
    "accent_light": "#7df9ff",      # Light cyan
    "accent_glow": "#00f0ff",       # For glow effects

    # Neon Magenta - Secondary
    "secondary": "#ff00ff",         # Magenta
    "secondary_hover": "#e000e0",
    "secondary_light": "#ff80ff",

    # Neon Purple
    "purple": "#bf00ff",
    "purple_hover": "#a000d0",

    # Status Colors - Neon style
    "success": "#00ff88",           # Neon green
    "success_hover": "#00e077",
    "success_bg": "#002211",

    "warning": "#ffcc00",           # Neon yellow
    "warning_hover": "#e6b800",
    "warning_bg": "#1a1400",

    "error": "#ff0055",             # Neon red/pink
    "error_hover": "#e0004d",
    "error_bg": "#1a000a",

    "info": "#00aaff",              # Neon blue
    "info_hover": "#0099e6",

    # Text Colors
    "text_primary": "#ffffff",      # White
    "text_secondary": "#8888aa",    # Muted purple-gray
    "text_tertiary": "#555577",     # Darker
    "text_link": "#00f0ff",         # Cyan links
    "text_glow": "#00f0ff",         # Glowing text

    # Border Colors - Neon glow style
    "border": "#2a2a40",            # Dark border
    "border_hover": "#3a3a55",      # Hover border
    "border_active": "#00f0ff",     # Active cyan border
    "border_glow": "#00f0ff",       # Glow border

    # Special
    "glass": "rgba(15, 15, 30, 0.8)",
    "overlay": "rgba(0, 0, 0, 0.85)",
    "shadow": "#000000",
    "neon_line": "#00f0ff",
}

# Typography
FONTS = {
    "family": "Segoe UI",
    "family_mono": "Consolas",
    "size_xs": 11,
    "size_sm": 12,
    "size_base": 13,
    "size_md": 14,
    "size_lg": 16,
    "size_xl": 18,
    "size_2xl": 24,
    "size_3xl": 32,
    "weight_normal": "normal",
    "weight_medium": "bold",
    "weight_bold": "bold",
}

# Spacing System
SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 20,
    "2xl": 24,
    "3xl": 32,
    "4xl": 48,
}

# Border Radius
RADIUS = {
    "xs": 4,
    "sm": 6,
    "md": 8,
    "lg": 12,
    "xl": 16,
    "2xl": 20,
    "full": 9999,
}

# Component Heights
HEIGHTS = {
    "button_sm": 32,
    "button_md": 40,
    "button_lg": 48,
    "input": 42,
    "card_profile": 80,
    "sidebar_item": 48,
    "header": 64,
    "status_bar": 36,
}

# Window settings
WINDOW_WIDTH = 1440
WINDOW_HEIGHT = 900
MIN_WIDTH = 1200
MIN_HEIGHT = 750

# Sidebar
SIDEBAR_WIDTH = 240
SIDEBAR_COLLAPSED_WIDTH = 64

# Animation durations (ms)
ANIMATION = {
    "fast": 150,
    "normal": 250,
    "slow": 350,
}
