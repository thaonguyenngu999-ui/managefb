# Cấu hình ứng dụng
APP_NAME = "FB Manager Pro"
APP_VERSION = "2.0.0"

# Hidemium API Config
HIDEMIUM_BASE_URL = "http://127.0.0.1:2222"
HIDEMIUM_TOKEN = "Cu6tDTR2N1HhTxlMyrQubY2ad56eQzWOjVrrb"  # API Token

# ========== MODERN UI DESIGN SYSTEM ==========

# Color Palette - Modern Dark Theme with Purple/Blue Gradient Accents
COLORS = {
    # Background Colors - Deep dark with subtle blue tint
    "bg_dark": "#0d1117",           # Main background - GitHub dark
    "bg_secondary": "#161b22",       # Secondary panels
    "bg_card": "#21262d",            # Card backgrounds
    "bg_card_hover": "#2d333b",      # Card hover state
    "bg_elevated": "#30363d",        # Elevated elements

    # Accent Colors - Vibrant gradient feel
    "accent": "#7c3aed",             # Primary purple
    "accent_hover": "#8b5cf6",       # Primary hover
    "accent_light": "#a78bfa",       # Light accent
    "accent_gradient_start": "#7c3aed",
    "accent_gradient_end": "#06b6d4",

    # Secondary Accent - Cyan/Teal
    "secondary": "#06b6d4",          # Cyan accent
    "secondary_hover": "#22d3ee",    # Cyan hover

    # Status Colors
    "success": "#10b981",            # Emerald green
    "success_hover": "#34d399",
    "success_bg": "#064e3b",         # Success background

    "warning": "#f59e0b",            # Amber
    "warning_hover": "#fbbf24",
    "warning_bg": "#78350f",

    "error": "#ef4444",              # Red
    "error_hover": "#f87171",
    "error_bg": "#7f1d1d",

    "info": "#3b82f6",               # Blue
    "info_hover": "#60a5fa",

    # Text Colors
    "text_primary": "#f0f6fc",       # Primary text - almost white
    "text_secondary": "#8b949e",     # Secondary text - muted
    "text_tertiary": "#6e7681",      # Tertiary text - very muted
    "text_link": "#58a6ff",          # Link color

    # Border Colors
    "border": "#30363d",             # Default border
    "border_hover": "#484f58",       # Border on hover
    "border_active": "#7c3aed",      # Active border (accent)

    # Special
    "glass": "rgba(255, 255, 255, 0.05)",  # Glassmorphism
    "overlay": "rgba(0, 0, 0, 0.5)",        # Modal overlay
    "shadow": "#010409",                    # Shadow color

    # Gradient Presets (for reference)
    "gradient_purple": "#7c3aed",
    "gradient_blue": "#3b82f6",
    "gradient_cyan": "#06b6d4",
    "gradient_green": "#10b981",
}

# Typography
FONTS = {
    "family": "Segoe UI",
    "family_mono": "JetBrains Mono",  # Or Consolas fallback
    "size_xs": 10,
    "size_sm": 11,
    "size_base": 13,
    "size_md": 14,
    "size_lg": 16,
    "size_xl": 18,
    "size_2xl": 22,
    "size_3xl": 28,
    "weight_normal": "normal",
    "weight_medium": "bold",  # CTkFont uses "bold" instead of numeric
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
    "button_md": 38,
    "button_lg": 44,
    "input": 42,
    "card_profile": 80,
    "sidebar_item": 48,
    "header": 70,
    "status_bar": 36,
}

# Window settings
WINDOW_WIDTH = 1440
WINDOW_HEIGHT = 900
MIN_WIDTH = 1200
MIN_HEIGHT = 750

# Sidebar
SIDEBAR_WIDTH = 260
SIDEBAR_COLLAPSED_WIDTH = 70

# Animation durations (ms) - for reference
ANIMATION = {
    "fast": 150,
    "normal": 250,
    "slow": 350,
}
