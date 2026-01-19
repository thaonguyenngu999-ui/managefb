# Cấu hình ứng dụng
APP_NAME = "FB Manager Pro"
APP_VERSION = "2.0.0"

# Hidemium API Config
HIDEMIUM_BASE_URL = "http://127.0.0.1:2222"
HIDEMIUM_TOKEN = "Cu6tDTR2N1HhTxlMyrQubY2ad56eQzWOjVrrb"  # API Token

# ========== CLEAN UI DESIGN SYSTEM ==========

# Color Palette - Clean Dark Theme
COLORS = {
    # Background Colors
    "bg_dark": "#111111",           # Main background
    "bg_secondary": "#1a1a1a",      # Secondary panels
    "bg_card": "#222222",           # Card backgrounds
    "bg_card_hover": "#2a2a2a",     # Card hover state
    "bg_hover": "#2a2a2a",          # General hover state
    "bg_elevated": "#333333",       # Elevated elements

    # Accent Colors - Clean Blue
    "accent": "#3b82f6",            # Primary blue
    "accent_hover": "#60a5fa",      # Primary hover
    "accent_light": "#93c5fd",      # Light accent
    "accent_gradient_start": "#3b82f6",
    "accent_gradient_end": "#06b6d4",

    # Secondary Accent
    "secondary": "#6366f1",         # Indigo
    "secondary_hover": "#818cf8",

    # Status Colors
    "success": "#22c55e",           # Green
    "success_hover": "#4ade80",
    "success_bg": "#14532d",

    "warning": "#f59e0b",           # Amber
    "warning_hover": "#fbbf24",
    "warning_bg": "#78350f",

    "error": "#ef4444",             # Red
    "error_hover": "#f87171",
    "error_bg": "#7f1d1d",

    "info": "#0ea5e9",              # Sky blue
    "info_hover": "#38bdf8",

    # Text Colors
    "text_primary": "#ffffff",      # Primary text - white
    "text_secondary": "#a3a3a3",    # Secondary text - gray
    "text_tertiary": "#737373",     # Tertiary text - darker gray
    "text_link": "#60a5fa",         # Link color

    # Border Colors
    "border": "#333333",            # Default border
    "border_hover": "#444444",      # Border on hover
    "border_active": "#3b82f6",     # Active border (accent)

    # Special
    "glass": "rgba(255, 255, 255, 0.05)",
    "overlay": "rgba(0, 0, 0, 0.7)",
    "shadow": "#000000",
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
    "size_2xl": 22,
    "size_3xl": 28,
    "weight_normal": "normal",
    "weight_medium": "bold",
    "weight_bold": "bold",
}

# Spacing System (in pixels)
SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 20,
    "2xl": 24,
    "3xl": 32,
    "4xl": 40,
}

# Border Radius
RADIUS = {
    "xs": 4,
    "sm": 6,
    "md": 8,
    "lg": 10,
    "xl": 12,
    "2xl": 16,
    "full": 9999,
}

# Component Heights
HEIGHTS = {
    "button_sm": 30,
    "button_md": 36,
    "button_lg": 42,
    "input": 38,
    "card_profile": 72,
    "sidebar_item": 42,
    "header": 60,
    "status_bar": 32,
}

# Window settings
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 850
MIN_WIDTH = 1100
MIN_HEIGHT = 700

# Sidebar
SIDEBAR_WIDTH = 220
SIDEBAR_COLLAPSED_WIDTH = 60

# Animation durations (ms)
ANIMATION = {
    "fast": 150,
    "normal": 250,
    "slow": 350,
}
