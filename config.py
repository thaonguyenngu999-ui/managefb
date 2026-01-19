# Cấu hình ứng dụng
APP_NAME = "SonCuto FB"
APP_VERSION = "2.0.0"

# Hidemium API Config
HIDEMIUM_BASE_URL = "http://127.0.0.1:2222"
HIDEMIUM_TOKEN = "Cu6tDTR2N1HhTxlMyrQubY2ad56eQzWOjVrrb"  # API Token

# UI Colors - SonCuto Pro Theme (Modern Tool Style)
COLORS = {
    # Background - Deep dark with subtle blue tint (like GoLogin/Multilogin)
    "bg_main": "#0d1117",            # GitHub-style dark
    "bg_sidebar": "#161b22",         # Sidebar darker
    "bg_card": "#21262d",            # Cards
    "bg_card_hover": "#30363d",      # Card hover
    "bg_input": "#0d1117",           # Input fields
    "bg_header": "#161b22",          # Header bar

    # Legacy aliases
    "bg_dark": "#0d1117",
    "bg_secondary": "#161b22",

    # Brand colors - Green & Pink gradient
    "primary": "#00d97e",            # SonCuto Green
    "primary_hover": "#2ee89a",
    "primary_dark": "#00b368",
    "primary_light": "rgba(0, 217, 126, 0.15)",
    "primary_glow": "#00d97e40",

    "secondary": "#ff6b9d",          # SonCuto Pink
    "secondary_hover": "#ff85b1",
    "secondary_dark": "#e5527f",
    "secondary_light": "rgba(255, 107, 157, 0.15)",

    # Accent
    "accent": "#00d97e",
    "accent_hover": "#2ee89a",
    "accent_pink": "#ff6b9d",
    "accent_pink_hover": "#ff85b1",

    # Status
    "success": "#00d97e",
    "warning": "#f0b429",
    "error": "#f85149",
    "danger": "#f85149",
    "info": "#58a6ff",
    "online": "#3fb950",
    "offline": "#6e7681",

    # Text
    "text_primary": "#f0f6fc",
    "text_secondary": "#8b949e",
    "text_muted": "#6e7681",
    "text_link": "#58a6ff",

    # Borders
    "border": "#30363d",
    "border_light": "#3d444d",
    "border_focus": "#00d97e",
    "divider": "#21262d",

    # Special
    "gradient_start": "#00d97e",
    "gradient_end": "#ff6b9d",
    "shadow": "rgba(0,0,0,0.3)",
    "overlay": "rgba(0,0,0,0.5)",
}

# Spacing system
SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 24,
    "xxl": 32,
}

# Border radius
RADIUS = {
    "sm": 4,
    "md": 6,
    "lg": 8,
    "xl": 12,
    "full": 9999,
}

# Window settings
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 850

# Sidebar width
SIDEBAR_WIDTH = 64  # Icon-only mode
SIDEBAR_EXPANDED = 200  # Expanded mode
