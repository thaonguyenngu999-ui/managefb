# Cấu hình ứng dụng
APP_NAME = "SonCuto FB"
APP_VERSION = "2.0.0"

# Hidemium API Config
HIDEMIUM_BASE_URL = "http://127.0.0.1:2222"
HIDEMIUM_TOKEN = "Cu6tDTR2N1HhTxlMyrQubY2ad56eQzWOjVrrb"  # API Token

# UI Colors - SonCuto Theme (Green & Pink)
COLORS = {
    # Background colors - Dark modern
    "bg_dark": "#0f0f14",           # Nền chính tối
    "bg_secondary": "#16161d",       # Sidebar, panels
    "bg_card": "#1e1e28",            # Cards
    "bg_input": "#252530",           # Input fields

    # Brand colors - Green & Pink
    "primary": "#00d97e",            # Xanh lá chính (SonCuto green)
    "primary_hover": "#00f58c",      # Xanh lá hover
    "primary_light": "#00d97e20",    # Xanh lá nhạt (transparent)

    "secondary": "#ff6b9d",          # Hồng chính (SonCuto pink)
    "secondary_hover": "#ff85b1",    # Hồng hover
    "secondary_light": "#ff6b9d20",  # Hồng nhạt (transparent)

    # Accent (gradient feel)
    "accent": "#00d97e",             # Primary accent
    "accent_hover": "#00f58c",
    "accent_pink": "#ff6b9d",
    "accent_pink_hover": "#ff85b1",

    # Status colors
    "success": "#00d97e",            # Same as primary
    "warning": "#ffbe0b",            # Vàng warning
    "error": "#ff5c5c",              # Đỏ error
    "danger": "#ff5c5c",
    "info": "#3b82f6",               # Xanh dương info

    # Text colors
    "text_primary": "#ffffff",
    "text_secondary": "#8b8b9a",
    "text_muted": "#5c5c6d",

    # Border & misc
    "border": "#2a2a3a",
    "border_light": "#3a3a4a",
    "divider": "#252535",

    # Gradient stops (for CSS-like gradients in future)
    "gradient_start": "#00d97e",
    "gradient_end": "#ff6b9d",
}

# Compact spacing
SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 20,
}

# Window settings
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 850
