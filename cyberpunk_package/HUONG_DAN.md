# 🎮 HƯỚNG DẪN TÍCH HỢP CYBERPUNK THEME

## 📁 Cấu trúc Package

```
cyberpunk_package/
├── config_cyberpunk.py      # Màu sắc, fonts, constants
├── cyber_widgets.py         # Widgets tùy chỉnh (Title, Card, Button, Badge...)
├── main_cyberpunk.py        # Main app mẫu
├── tabs/
│   └── profiles_tab_cyber.py  # Tab mẫu với glitch effect
├── preview.html             # Preview HTML để xem trước
└── HUONG_DAN.md            # File này
```

---

## 🔧 CÁCH TÍCH HỢP VÀO DỰ ÁN

### Bước 1: Copy files

```bash
# Copy config
cp config_cyberpunk.py /path/to/your/project/config.py

# Copy widgets
cp cyber_widgets.py /path/to/your/project/

# Hoặc rename và import
cp cyber_widgets.py /path/to/your/project/widgets_cyber.py
```

### Bước 2: Sửa imports trong các file tab

**Trước:**
```python
from config import COLORS, FONTS, SPACING
from widgets import ModernCard, ModernButton
```

**Sau:**
```python
from config_cyberpunk import COLORS, FONTS, SPACING, TAB_COLORS
from cyber_widgets import CyberTitle, CyberCard, CyberButton, CyberBadge, CyberStatCard
```

### Bước 3: Thay thế header của mỗi tab

**Trước (code cũ):**
```python
def _create_ui(self):
    # Header
    header = ctk.CTkFrame(self, fg_color="transparent")
    header.pack(fill="x", padx=24, pady=24)
    
    ctk.CTkLabel(
        header,
        text="Quản lý Profiles",
        font=ctk.CTkFont(size=24, weight="bold")
    ).pack(anchor="w")
```

**Sau (Cyberpunk):**
```python
def _create_ui(self):
    # Cyberpunk Header với Glitch Effect
    self.cyber_title = CyberTitle(
        self,
        title="PROFILES",
        subtitle="Quản lý tài khoản Hidemium Browser",
        tab_id="profiles"  # Quyết định màu accent
    )
    self.cyber_title.pack(fill="x", padx=24, pady=(24, 0))
```

---

## 🎨 BẢNG MÀU NEON

| Tên | Hex Code | Dùng cho |
|-----|----------|----------|
| `neon_cyan` | `#00f0ff` | Primary, Profiles, Scripts |
| `neon_green` | `#00ff66` | Success, Login, Posts |
| `neon_magenta` | `#ff00a8` | Secondary, Reels |
| `neon_purple` | `#bf00ff` | Pages |
| `neon_yellow` | `#fcee0a` | Warning, Content |
| `neon_orange` | `#ff6b00` | Groups |
| `neon_red` | `#ff003c` | Error, Danger |

---

## 🔤 FONTS

CustomTkinter không hỗ trợ load font từ file, nên dùng system fonts:

| Mục đích | Windows | macOS |
|----------|---------|-------|
| Headers, Titles | Segoe UI Bold | SF Pro Display |
| Code, Logs | Consolas | SF Mono |
| Body text | Segoe UI | SF Pro Text |

**Trong code:**
```python
# Title
ctk.CTkFont(family="Segoe UI", size=28, weight="bold")

# Code/Log
ctk.CTkFont(family="Consolas", size=11)
```

---

## ✨ HIỆU ỨNG GLITCH

### Cách hoạt động:

1. **2 layer text**: `title_main` (hiển thị) + `title_glitch` (ẩn phía sau)
2. **Animation loop**: Mỗi 100ms check step
3. **Glitch phase**: 3 frames đầu - hiện glitch layer với offset và màu khác
4. **Normal phase**: Ẩn glitch layer

### Code mẫu:
```python
def _start_glitch_animation(self):
    self._glitch_step = 0
    
    def animate():
        self._glitch_step = (self._glitch_step + 1) % 80  # 8 giây cycle
        
        if self._glitch_step < 3:  # Glitch 3 frames
            offset = 3 if self._glitch_step % 2 == 0 else -3
            self.title_glitch.place(x=offset, y=0)
            color = COLORS["neon_magenta"] if self._glitch_step % 2 == 0 else COLORS["neon_cyan"]
            self.title_glitch.configure(text_color=color)
        else:
            self.title_glitch.configure(text_color=COLORS["bg_dark"])  # Hide
        
        self.after(100, animate)
    
    animate()
```

### Cleanup khi destroy:
```python
def destroy(self):
    self._glitch_active = False  # Stop animation
    super().destroy()
```

---

## 📊 STAT CARDS

```python
# Tạo grid 4 stat cards
stats_frame = ctk.CTkFrame(self, fg_color="transparent")
stats_frame.pack(fill="x", padx=24, pady=16)

# Configure grid
for i in range(4):
    stats_frame.grid_columnconfigure(i, weight=1)

# Stat cards
CyberStatCard(stats_frame, "TỔNG PROFILES", "247", "+12 tuần này", "cyan").grid(row=0, column=0, padx=8, sticky="nsew")
CyberStatCard(stats_frame, "ĐANG CHẠY", "18", "Active", "green").grid(row=0, column=1, padx=8, sticky="nsew")
CyberStatCard(stats_frame, "FOLDERS", "12", "Categories", "purple").grid(row=0, column=2, padx=8, sticky="nsew")
CyberStatCard(stats_frame, "SCRIPTS", "34", "Automation", "yellow").grid(row=0, column=3, padx=8, sticky="nsew")
```

---

## 🏷️ BADGES

```python
# Running badge với LED pulse
CyberBadge(parent, "RUNNING", color="green", show_led=True, pulse=True)

# Stopped badge
CyberBadge(parent, "STOPPED", color="gray", show_led=True, pulse=False)

# Platform badge
CyberBadge(parent, "WIN 11", color="cyan")
```

---

## 🔘 BUTTONS

```python
# Primary (cyan)
CyberButton(parent, "🔄 SYNC", variant="primary", command=sync_func)

# Success (green)
CyberButton(parent, "➕ CREATE", variant="success", command=create_func)

# Danger (red)
CyberButton(parent, "🗑 DELETE", variant="danger", command=delete_func)

# Ghost (subtle)
CyberButton(parent, "⟳ REFRESH", variant="ghost", command=refresh_func)
```

---

## 📋 CARDS

```python
# Card với header
card = CyberCard(parent, title="PROFILE DATABASE", accent_color=COLORS["neon_cyan"], count="[247]")
card.pack(fill="both", expand=True)

# Thêm content vào card.content_frame
table = ctk.CTkFrame(card.content_frame)
table.pack(fill="both", expand=True)
```

---

## 💻 TERMINAL LOG

```python
# Tạo terminal
terminal = CyberTerminal(parent)
terminal.pack(fill="both", expand=True)

# Thêm logs
terminal.add_line("System initialized", "info")      # Cyan
terminal.add_line("Login successful", "success")     # Green
terminal.add_line("Check required", "warning")       # Yellow
terminal.add_line("Connection failed", "error")      # Red

# Clear
terminal.clear()
```

---

## 🧭 SIDEBAR NAVIGATION

```python
# Trong main.py
nav_items = [
    ("profiles", "👤", "Profiles"),
    ("login", "🔐", "Login FB"),
    ("pages", "📄", "Pages"),
    # ...
]

self.nav_buttons = {}

for tab_id, icon, text in nav_items:
    nav = CyberNavItem(
        sidebar_nav_frame,
        tab_id=tab_id,
        icon=icon,
        text=text,
        command=self._switch_tab
    )
    nav.pack(fill="x", pady=2)
    self.nav_buttons[tab_id] = nav

def _switch_tab(self, tab_id):
    # Update nav buttons
    for tid, nav in self.nav_buttons.items():
        nav.set_active(tid == tab_id)
    
    # Switch content
    # ...
```

---

## 🎯 CHECKLIST TÍCH HỢP

- [ ] Copy `config_cyberpunk.py` → `config.py`
- [ ] Copy `cyber_widgets.py`
- [ ] Sửa imports trong `main.py`
- [ ] Sửa imports trong các file `tabs/*.py`
- [ ] Thay header mỗi tab bằng `CyberTitle`
- [ ] Thay stat cards bằng `CyberStatCard`
- [ ] Thay buttons bằng `CyberButton`
- [ ] Thay badges bằng `CyberBadge`
- [ ] Thêm `CyberTerminal` cho log panel
- [ ] Update sidebar với `CyberNavItem`
- [ ] Test từng tab

---

## ⚠️ LƯU Ý

1. **Cleanup animation**: Luôn set `_glitch_active = False` trong `destroy()` để tránh memory leak

2. **Colors**: Dùng màu từ `COLORS` dict, không hardcode hex

3. **Fonts**: Sử dụng `FONTS["family_display"]` và `FONTS["family_mono"]`

4. **Spacing**: Dùng `SPACING["lg"]`, `SPACING["xl"]` thay vì số cố định

5. **Tab colors**: Mỗi tab dùng màu từ `TAB_COLORS[tab_id]`

---

## 🆘 TROUBLESHOOTING

**Q: Glitch animation không chạy?**
A: Check xem `_start_glitch_animation()` có được gọi không, và `_glitch_active = True`

**Q: Màu không đúng?**
A: Đảm bảo import đúng `from config_cyberpunk import COLORS`

**Q: Font không đẹp?**
A: CustomTkinter dùng system fonts, không load được custom fonts

---

Chúc bạn thành công! 🎮🔥
