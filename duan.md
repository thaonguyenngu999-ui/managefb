# FB Manager Pro - Tài Liệu Dự Án Chi Tiết

## Mục Lục
1. [Tổng Quan](#tổng-quan)
2. [Công Nghệ Sử Dụng](#công-nghệ-sử-dụng)
3. [Cấu Trúc Dự Án](#cấu-trúc-dự-án)
4. [Chi Tiết Từng File](#chi-tiết-từng-file)
5. [Database Schema](#database-schema)
6. [Luồng Hoạt Động](#luồng-hoạt-động)
7. [API Hidemium](#api-hidemium)
8. [Hướng Dẫn Chỉnh Sửa](#hướng-dẫn-chỉnh-sửa)

---

## Tổng Quan

**FB Manager Pro** là ứng dụng desktop để quản lý và tự động hóa các thao tác Facebook sử dụng **Hidemium Browser API**.

### Chức Năng Chính:
- **Quản lý Profile**: Quản lý nhiều tài khoản Facebook thông qua Hidemium
- **Đăng nhập tự động**: Import tài khoản từ Excel, đăng nhập hàng loạt
- **Quản lý Page**: Quét và tạo Facebook Page
- **Quản lý Group**: Quét group, đăng bài, boost bài viết
- **Thư viện nội dung**: Quản lý nội dung bài đăng với ảnh/sticker
- **Tương tác bài viết**: Auto like, comment với nhiều profile
- **Lên lịch tự động**: Đặt lịch đăng bài theo thời gian

---

## Công Nghệ Sử Dụng

| Công nghệ | Mục đích |
|-----------|----------|
| **Python 3.9+** | Ngôn ngữ lập trình chính |
| **CustomTkinter** | Framework giao diện desktop hiện đại |
| **SQLite** | Cơ sở dữ liệu local |
| **Chrome DevTools Protocol (CDP)** | Điều khiển trình duyệt |
| **Hidemium API** | API quản lý profile trình duyệt (localhost:2222) |
| **Requests** | HTTP client cho API calls |
| **Pillow** | Xử lý hình ảnh |
| **tkcalendar** | Component chọn ngày |
| **PyInstaller** | Build file .exe |
| **BeautifulSoup4** | Parse HTML (optional) |

### Cài Đặt Dependencies:
```bash
pip install -r requirements.txt
```

---

## Cấu Trúc Dự Án

```
managefb/
│
├── main.py                    # [13 KB] Entry point - Cửa sổ chính + Settings
├── config.py                  # Cấu hình global (API URL, token, màu sắc UI)
├── api_service.py             # [18.5 KB] Wrapper class gọi Hidemium API
├── db.py                      # [40.6 KB] Quản lý database SQLite
├── database.py                # [11.5 KB] Module database cũ (legacy)
├── widgets.py                 # [17.9 KB] Custom UI components
├── check_version.py           # Kiểm tra phiên bản
├── requirements.txt           # Dependencies Python
├── build.spec                 # Cấu hình PyInstaller
├── README.md                  # Tài liệu dự án
├── api.txt                    # Tài liệu tham khảo Hidemium API
│
├── data/                      # Thư mục lưu trữ dữ liệu
│   ├── fbmanager.db           # File database SQLite
│   ├── profiles.json          # (Legacy) Backup profiles
│   ├── scripts.json           # (Legacy) Backup scripts
│   └── settings.json          # (Legacy) Backup settings
│
├── tabs/                      # Các tab giao diện (7 tabs)
│   ├── __init__.py            # Export tất cả tab classes
│   ├── profiles_tab.py        # [46.7 KB] Tab quản lý Profile
│   ├── login_tab.py           # [60 KB] Tab đăng nhập Facebook
│   ├── pages_tab.py           # [60.4 KB] Tab quản lý Page
│   ├── content_tab.py         # [30.3 KB] Tab quản lý nội dung
│   ├── groups_tab.py          # [135 KB] Tab quản lý Group (lớn nhất)
│   ├── posts_tab.py           # [32.3 KB] Tab tương tác bài viết
│   └── scripts_tab.py         # [48.3 KB] Tab lên lịch tự động
│
└── automation/                # Engine tự động hóa trình duyệt
    ├── __init__.py            # Export chính
    ├── engine.py              # [11.5 KB] State machine
    ├── jobs.py                # [45.7 KB] Định nghĩa job
    ├── cdp_client.py          # [21.7 KB] CDP client cũ
    ├── cdp_helper.py          # [22.5 KB] CDP helper cao cấp
    ├── human_behavior.py      # [12.8 KB] Hành vi giống người
    ├── artifacts.py           # [10.1 KB] Thu thập artifacts
    ├── window_manager.py      # [6.9 KB] Quản lý vị trí cửa sổ
    │
    └── cdp_max/               # CDP production-grade
        ├── __init__.py
        ├── session.py         # [18.9 KB] Quản lý session CDP
        ├── targets.py         # [12.5 KB] Quản lý target/tab
        ├── client.py          # [19.5 KB] Client chính CDPClientMAX
        ├── events.py          # [13.3 KB] Hệ thống event
        ├── actions.py         # [23.6 KB] Thực thi action
        ├── selectors.py       # [22 KB] Engine tìm element
        ├── waits.py           # [23.8 KB] Engine chờ điều kiện
        ├── navigation.py      # [19 KB] Điều hướng trang
        ├── file_io.py         # [15.8 KB] Upload/download file
        ├── concurrency.py     # [12.7 KB] Xử lý đồng thời
        ├── recovery.py        # [16.8 KB] Phục hồi lỗi
        ├── watchdog.py        # [13.8 KB] Giám sát health
        ├── performance.py     # [12.6 KB] Tối ưu hiệu suất
        ├── observability.py   # [12.5 KB] Tracing và logging
        └── stealth.py         # [42.6 KB] Chống phát hiện bot
```

---

## Chi Tiết Từng File

### 1. File Chính (Root)

#### `main.py` - Entry Point
```python
class FBManagerApp(ctk.CTk):
    """Cửa sổ chính của ứng dụng"""

    def __init__(self):
        # Tạo sidebar với các nút navigation
        # Khởi tạo 7 tabs
        # Tạo status bar
        # Kiểm tra kết nối Hidemium

    def create_sidebar(self):
        """Tạo sidebar bên trái với các nút điều hướng"""

    def show_tab(self, tab_name):
        """Chuyển đổi giữa các tab"""

    def check_connection(self):
        """Kiểm tra kết nối đến Hidemium API"""

class SettingsDialog(ctk.CTkToplevel):
    """Dialog cài đặt API token và cấu hình"""
```

**Cách sửa:** Thay đổi giao diện chính, thêm/xóa tab, sửa sidebar

---

#### `config.py` - Cấu Hình Global
```python
# URL Hidemium API
HIDEMIUM_API_URL = "http://127.0.0.1:2222"
API_TOKEN = "your-token-here"

# Màu sắc UI
COLORS = {
    "bg_dark": "#1a1a2e",
    "bg_medium": "#16213e",
    "accent": "#0f3460",
    "text": "#eaeaea",
    "success": "#4ade80",
    "error": "#f87171"
}

# Cấu hình cửa sổ
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
```

**Cách sửa:** Thay đổi màu sắc, kích thước cửa sổ, URL API

---

#### `api_service.py` - Hidemium API Wrapper
```python
class HidemiumAPI:
    """Wrapper class để gọi Hidemium REST API"""

    def get_profiles(self, folder_id=None):
        """Lấy danh sách profiles từ Hidemium"""

    def open_browser(self, profile_id):
        """Mở trình duyệt cho profile"""
        # Returns: {"browser_location": "...", "ws_url": "ws://..."}

    def close_browser(self, profile_id):
        """Đóng trình duyệt"""

    def update_profile(self, profile_id, data):
        """Cập nhật thông tin profile"""

    def get_folders(self):
        """Lấy danh sách folders"""

    def create_profile(self, data):
        """Tạo profile mới"""
```

**Endpoints chính:**
- `GET /api/v2/profiles` - Lấy danh sách profiles
- `GET /api/v2/profiles/{id}/start` - Mở browser
- `GET /api/v2/profiles/{id}/stop` - Đóng browser
- `PUT /api/v2/profiles/{id}` - Cập nhật profile
- `GET /api/v2/folders` - Lấy folders

---

#### `db.py` - Database Manager
```python
class DatabaseManager:
    """Quản lý SQLite database"""

    def __init__(self, db_path="data/fbmanager.db"):
        self.conn = sqlite3.connect(db_path)
        self.create_tables()

    # === Categories ===
    def get_categories(self): ...
    def add_category(self, name): ...
    def delete_category(self, category_id): ...

    # === Contents ===
    def get_contents(self, category_id=None): ...
    def add_content(self, content, images, sticker, category_id): ...
    def update_content(self, content_id, data): ...

    # === Profiles ===
    def sync_profiles_from_api(self, profiles): ...
    def get_profiles(self, folder_id=None): ...

    # === Pages ===
    def add_page(self, profile_id, page_id, name, url, followers): ...
    def get_pages(self): ...

    # === Groups ===
    def add_group(self, profile_id, group_id, name, url, members): ...
    def get_groups(self): ...

    # === Posts ===
    def add_post(self, url, title, target_likes, target_comments): ...
    def get_posts(self): ...

    # === Schedules ===
    def add_schedule(self, time_slot, content_id, group_ids): ...
    def get_schedules(self): ...

    # === Post History ===
    def add_post_history(self, schedule_id, group_id, status): ...
```

---

#### `widgets.py` - Custom UI Components
```python
class ModernCard(ctk.CTkFrame):
    """Card với shadow và border radius"""

class ModernButton(ctk.CTkButton):
    """Button với hover effect"""

class ModernEntry(ctk.CTkEntry):
    """Input field với placeholder"""

class ModernTextbox(ctk.CTkTextbox):
    """Textarea với scrollbar"""

class ModernComboBox(ctk.CTkComboBox):
    """Dropdown selection"""

class StatusLabel(ctk.CTkLabel):
    """Label hiển thị trạng thái với màu"""
```

---

### 2. Tabs (Giao Diện)

#### `tabs/profiles_tab.py` - Quản Lý Profile
```python
class ProfilesTab(ctk.CTkFrame):
    """Tab quản lý profiles Hidemium"""

    def create_widgets(self):
        """Tạo giao diện: filter bar, table, action buttons"""

    def load_profiles(self):
        """Load profiles từ API và hiển thị"""

    def filter_profiles(self, folder_id):
        """Lọc profiles theo folder"""

    def open_profile(self, profile_id):
        """Mở browser cho profile"""

    def close_profile(self, profile_id):
        """Đóng browser"""

    def refresh_status(self):
        """Cập nhật trạng thái running/stopped"""

    def edit_profile(self, profile_id):
        """Mở dialog chỉnh sửa profile"""
```

**Chức năng:**
- Hiển thị danh sách profiles dạng bảng
- Filter theo folder
- Hiển thị trạng thái (Running/Stopped)
- Mở/đóng browser
- Chỉnh sửa thông tin profile

---

#### `tabs/login_tab.py` - Đăng Nhập Tự Động
```python
class LoginTab(ctk.CTkFrame):
    """Tab đăng nhập Facebook tự động"""

    def import_from_excel(self):
        """Import accounts từ file XLSX"""
        # Format: email|password hoặc columns

    def start_login(self):
        """Bắt đầu đăng nhập hàng loạt"""

    def login_single_profile(self, profile_id, email, password):
        """Đăng nhập một profile"""
        # 1. Mở browser
        # 2. Navigate đến facebook.com
        # 3. Nhập email/password
        # 4. Click login
        # 5. Xử lý 2FA nếu có

    def manage_windows(self):
        """Sắp xếp cửa sổ browser khi đăng nhập nhiều"""
```

**Chức năng:**
- Import tài khoản từ Excel (email|password)
- Đăng nhập tự động nhiều profile cùng lúc
- Quản lý vị trí cửa sổ browser
- Xử lý 2FA, captcha

---

#### `tabs/pages_tab.py` - Quản Lý Page
```python
class PagesTab(ctk.CTkFrame):
    """Tab quản lý Facebook Pages"""

    def scan_pages(self, profile_ids):
        """Quét pages mà profile quản lý"""
        # Navigate đến facebook.com/pages/?category=your_pages
        # Parse danh sách pages

    def create_page(self, profile_id, page_name, category):
        """Tạo page mới"""
        # Navigate đến facebook.com/pages/creation
        # Điền form tạo page

    def load_pages(self):
        """Load pages từ database"""

    def sync_pages(self):
        """Đồng bộ pages với Facebook"""
```

**Database table `pages`:**
```sql
CREATE TABLE pages (
    id INTEGER PRIMARY KEY,
    profile_id TEXT,
    page_id TEXT,
    name TEXT,
    url TEXT,
    followers INTEGER,
    created_at TIMESTAMP
);
```

---

#### `tabs/content_tab.py` - Quản Lý Nội Dung
```python
class ContentTab(ctk.CTkFrame):
    """Tab quản lý thư viện nội dung"""

    def create_category(self, name):
        """Tạo category mới"""

    def add_content(self, text, images, sticker, category_id):
        """Thêm nội dung mới"""
        # images: list đường dẫn ảnh
        # sticker: đường dẫn sticker

    def edit_content(self, content_id):
        """Chỉnh sửa nội dung"""

    def delete_content(self, content_id):
        """Xóa nội dung"""

    def preview_content(self, content_id):
        """Xem trước nội dung"""
```

**Database tables:**
```sql
CREATE TABLE categories (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE
);

CREATE TABLE contents (
    id INTEGER PRIMARY KEY,
    content TEXT,
    images TEXT,  -- JSON array of paths
    sticker TEXT,
    category_id INTEGER,
    created_at TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);
```

---

#### `tabs/groups_tab.py` - Quản Lý Group (FILE LỚN NHẤT - 135KB)
```python
class GroupsTab(ctk.CTkFrame):
    """Tab quản lý Facebook Groups"""

    # === Quét Groups ===
    def scan_groups(self, profile_ids):
        """Quét groups mà profile tham gia"""
        # Navigate: facebook.com/groups/joins
        # Scroll và thu thập groups

    def parse_group_info(self, element):
        """Parse thông tin group từ DOM"""
        # Returns: {id, name, url, members}

    # === Đăng Bài ===
    def post_to_groups(self, profile_id, group_ids, content):
        """Đăng bài vào nhiều groups"""

    def post_single(self, profile_id, group_id, content):
        """Đăng bài vào một group"""
        # 1. Navigate đến group
        # 2. Click vào ô đăng bài
        # 3. Nhập nội dung
        # 4. Upload ảnh nếu có
        # 5. Click đăng

    # === Boost Bài Viết ===
    def boost_post(self, post_url, profile_ids):
        """Đẩy bài viết lên đầu group"""
        # Like/comment với nhiều profile

    # === Cài Đặt ===
    def set_delay(self, min_delay, max_delay):
        """Đặt delay giữa các lần đăng"""
```

**Đây là tab phức tạp nhất với các chức năng:**
- Quét groups từ nhiều profile
- Đăng bài hàng loạt vào groups
- Boost bài viết (like, comment)
- Quản lý delay để tránh spam
- Xử lý lỗi và retry

---

#### `tabs/posts_tab.py` - Tương Tác Bài Viết
```python
class PostsTab(ctk.CTkFrame):
    """Tab tương tác với bài viết"""

    def add_post(self, url, target_likes, target_comments):
        """Thêm bài viết cần boost"""

    def auto_like(self, post_url, profile_ids):
        """Auto like bài viết với nhiều profile"""

    def auto_comment(self, post_url, profile_ids, comments):
        """Auto comment với nội dung tùy chỉnh"""
        # comments: list các comment ngẫu nhiên

    def track_engagement(self, post_id):
        """Theo dõi số like/comment hiện tại"""
```

---

#### `tabs/scripts_tab.py` - Lên Lịch Tự Động
```python
class ScriptsTab(ctk.CTkFrame):
    """Tab lên lịch đăng bài tự động"""

    def add_schedule(self, time_slot, content_id, group_ids):
        """Thêm lịch đăng bài"""
        # time_slot: "08:00", "12:00", etc.

    def start_scheduler(self):
        """Bắt đầu scheduler thread"""

    def scheduler_loop(self):
        """Vòng lặp kiểm tra và thực thi lịch"""
        while running:
            current_time = get_current_time()
            for schedule in get_due_schedules(current_time):
                execute_schedule(schedule)
            sleep(60)  # Check mỗi phút

    def execute_schedule(self, schedule):
        """Thực thi một lịch đăng bài"""

    def view_history(self):
        """Xem lịch sử đăng bài"""
```

**Database tables:**
```sql
CREATE TABLE schedules (
    id INTEGER PRIMARY KEY,
    time_slot TEXT,
    content_id INTEGER,
    group_ids TEXT,  -- JSON array
    is_active BOOLEAN,
    created_at TIMESTAMP
);

CREATE TABLE post_history (
    id INTEGER PRIMARY KEY,
    schedule_id INTEGER,
    group_id TEXT,
    status TEXT,  -- success/failed
    posted_at TIMESTAMP,
    error_message TEXT
);
```

---

### 3. Automation Engine

#### `automation/engine.py` - State Machine
```python
class JobState(Enum):
    """Các trạng thái của job"""
    INIT = "init"
    OPEN_BROWSER = "open_browser"
    NAVIGATE = "navigate"
    READY_CHECK = "ready_check"
    ACTION_PREPARE = "action_prepare"
    ACTION_EXECUTE = "action_execute"
    ACTION_VERIFY = "action_verify"
    CLEANUP = "cleanup"
    DONE = "done"
    FAILED = "failed"

class StateMachine:
    """Điều phối thực thi job qua các state"""

    def run(self, job):
        """Chạy job qua từng state"""
        state = JobState.INIT
        while state not in [JobState.DONE, JobState.FAILED]:
            handler = self.get_handler(state)
            result = handler(job)
            state = result.next_state
```

---

#### `automation/jobs.py` - Job Definitions
```python
@dataclass
class JobContext:
    """Context cho một job"""
    profile_id: str
    action_type: str  # login, post, like, comment, scan
    target_url: str
    data: dict  # Dữ liệu cần thiết cho action

@dataclass
class JobResult:
    """Kết quả job"""
    success: bool
    data: dict
    error: str = None
    artifacts: list = None  # Screenshots, logs

class Job:
    """Base class cho tất cả jobs"""

    def __init__(self, context: JobContext):
        self.context = context
        self.cdp_client = None

    async def execute(self):
        """Override trong subclass"""
        raise NotImplementedError
```

---

#### `automation/cdp_helper.py` - CDP Helper
```python
class CDPHelper:
    """Helper cao cấp cho Chrome DevTools Protocol"""

    def __init__(self, ws_url):
        self.ws_url = ws_url
        self.client = None

    async def connect(self):
        """Kết nối đến browser qua WebSocket"""

    async def navigate(self, url, wait_until="load"):
        """Navigate đến URL"""

    async def click(self, selector, timeout=10000):
        """Click vào element"""

    async def type_text(self, selector, text, delay=50):
        """Nhập text vào input (giống người)"""

    async def wait_for_selector(self, selector, timeout=30000):
        """Chờ element xuất hiện"""

    async def get_text(self, selector):
        """Lấy text từ element"""

    async def screenshot(self, path):
        """Chụp screenshot"""

    async def evaluate(self, expression):
        """Chạy JavaScript trong page"""
```

---

#### `automation/human_behavior.py` - Chống Phát Hiện Bot
```python
class HumanBehavior:
    """Tạo hành vi giống người thật"""

    def random_delay(self, min_ms=100, max_ms=500):
        """Delay ngẫu nhiên theo phân phối normal"""

    def typing_delay(self, char):
        """Delay giữa các phím khi gõ (40-80 WPM)"""

    def reading_time(self, text_length):
        """Thời gian đọc dựa trên độ dài text"""

    def thinking_pause(self):
        """Pause ngẫu nhiên như đang suy nghĩ"""

    def scroll_behavior(self):
        """Scroll từ từ, không đều"""

class AntiDetection:
    """Các kỹ thuật chống phát hiện bot"""

    def randomize_fingerprint(self):
        """Làm ngẫu nhiên browser fingerprint"""

    def mask_automation(self):
        """Ẩn dấu hiệu automation"""
```

---

#### `automation/cdp_max/` - CDP Production-Grade

Đây là engine CDP chuyên nghiệp với các module:

| File | Chức năng |
|------|-----------|
| `session.py` | Quản lý vòng đời session CDP |
| `targets.py` | Quản lý tabs/targets |
| `client.py` | Client chính CDPClientMAX |
| `events.py` | Hệ thống event emitter |
| `actions.py` | Thực thi actions (click, type, submit) |
| `selectors.py` | Tìm elements (CSS, XPath, ARIA, text) |
| `waits.py` | Chờ điều kiện (DOM, network, stability) |
| `navigation.py` | Điều hướng (SPA, redirects) |
| `file_io.py` | Upload/download files |
| `concurrency.py` | Xử lý đồng thời nhiều targets |
| `recovery.py` | Phục hồi từ lỗi (multi-tier) |
| `watchdog.py` | Phát hiện crash/freeze |
| `performance.py` | Tối ưu (batching, caching) |
| `observability.py` | Logging và tracing |
| `stealth.py` | Chống phát hiện bot |

---

## Database Schema

### ERD (Entity Relationship Diagram)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  categories  │     │   contents   │     │   profiles   │
├──────────────┤     ├──────────────┤     ├──────────────┤
│ id (PK)      │◄────│ category_id  │     │ id (PK)      │
│ name         │     │ id (PK)      │     │ hidemium_id  │
│ created_at   │     │ content      │     │ name         │
└──────────────┘     │ images       │     │ folder_id    │
                     │ sticker      │     │ proxy        │
                     │ created_at   │     │ status       │
                     └──────────────┘     │ synced_at    │
                                          └──────┬───────┘
                                                 │
                     ┌───────────────────────────┼───────────────────────────┐
                     │                           │                           │
                     ▼                           ▼                           ▼
              ┌──────────────┐           ┌──────────────┐           ┌──────────────┐
              │    pages     │           │    groups    │           │    posts     │
              ├──────────────┤           ├──────────────┤           ├──────────────┤
              │ id (PK)      │           │ id (PK)      │           │ id (PK)      │
              │ profile_id   │           │ profile_id   │           │ url          │
              │ page_id      │           │ group_id     │           │ title        │
              │ name         │           │ name         │           │ target_likes │
              │ url          │           │ url          │           │ target_cmts  │
              │ followers    │           │ members      │           │ current_likes│
              │ created_at   │           │ created_at   │           │ current_cmts │
              └──────────────┘           └──────────────┘           └──────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  schedules   │     │ post_history │     │   settings   │
├──────────────┤     ├──────────────┤     ├──────────────┤
│ id (PK)      │◄────│ schedule_id  │     │ key (PK)     │
│ time_slot    │     │ id (PK)      │     │ value        │
│ content_id   │     │ group_id     │     │ updated_at   │
│ group_ids    │     │ status       │     └──────────────┘
│ is_active    │     │ posted_at    │
│ created_at   │     │ error_msg    │
└──────────────┘     └──────────────┘
```

---

## Luồng Hoạt Động

### 1. Luồng Đăng Nhập Facebook

```
User clicks "Import Excel"
         │
         ▼
┌─────────────────┐
│ Parse XLSX file │
│ email|password  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Match accounts  │
│ with profiles   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ For each profile│────►│ Open Hidemium   │
│                 │     │ browser via API │
└────────┬────────┘     └────────┬────────┘
         │                       │
         │              ┌────────┴────────┐
         │              │ Get WebSocket   │
         │              │ URL (ws://)     │
         │              └────────┬────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│ CDPHelper       │◄────│ Connect to      │
│ connect()       │     │ browser CDP     │
└────────┬────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐
│ Navigate to     │
│ facebook.com    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Find email      │────►│ Type email with │
│ input field     │     │ human delay     │
└─────────────────┘     └────────┬────────┘
                                 │
         ┌───────────────────────┘
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Find password   │────►│ Type password   │
│ input field     │     │ with human delay│
└─────────────────┘     └────────┬────────┘
                                 │
         ┌───────────────────────┘
         ▼
┌─────────────────┐
│ Click login     │
│ button          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Wait for        │────►│ Handle 2FA if   │
│ navigation      │     │ required        │
└────────┬────────┘     └────────┬────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│ Check login     │     │ Save login      │
│ success         │     │ status to DB    │
└─────────────────┘     └─────────────────┘
```

### 2. Luồng Đăng Bài Group

```
User selects content + groups
         │
         ▼
┌─────────────────┐
│ For each group  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Open browser    │
│ for profile     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Navigate to     │
│ group URL       │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│ Find "Write something" input    │
│ Selectors:                      │
│ - [aria-label*="Viết gì đó"]    │
│ - [role="button"][tabindex="0"] │
│ - div[data-pagelet*="Composer"] │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────┐
│ Click to open   │
│ composer modal  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Type content    │
│ with delays     │
└────────┬────────┘
         │
         ▼ (if has images)
┌─────────────────┐
│ Click photo     │
│ button          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Upload images   │
│ via file input  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Click "Đăng"    │
│ (Post) button   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Wait for post   │────►│ Random delay    │
│ success         │     │ before next     │
└─────────────────┘     └─────────────────┘
```

---

## API Hidemium

### Endpoints Chính

```
Base URL: http://127.0.0.1:2222/api/v2

Headers:
  Authorization: Bearer {API_TOKEN}
  Content-Type: application/json
```

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/profiles` | Lấy tất cả profiles |
| GET | `/profiles?folder_id={id}` | Lấy profiles theo folder |
| GET | `/profiles/{id}` | Lấy chi tiết profile |
| POST | `/profiles` | Tạo profile mới |
| PUT | `/profiles/{id}` | Cập nhật profile |
| DELETE | `/profiles/{id}` | Xóa profile |
| GET | `/profiles/{id}/start` | Mở browser |
| GET | `/profiles/{id}/stop` | Đóng browser |
| GET | `/folders` | Lấy danh sách folders |
| POST | `/folders` | Tạo folder mới |

### Response Format

```json
// Success
{
    "success": true,
    "data": {
        "id": "profile-uuid",
        "name": "Profile Name",
        "browser_location": "/path/to/chrome",
        "ws_url": "ws://127.0.0.1:xxxxx/devtools/browser/..."
    }
}

// Error
{
    "success": false,
    "message": "Error description"
}
```

---

## Hướng Dẫn Chỉnh Sửa

### 1. Thêm Tab Mới

**Bước 1:** Tạo file trong `tabs/`
```python
# tabs/new_tab.py
import customtkinter as ctk

class NewTab(ctk.CTkFrame):
    def __init__(self, parent, api, db):
        super().__init__(parent)
        self.api = api  # HidemiumAPI instance
        self.db = db    # DatabaseManager instance
        self.create_widgets()

    def create_widgets(self):
        # Tạo UI ở đây
        pass
```

**Bước 2:** Export trong `tabs/__init__.py`
```python
from .new_tab import NewTab
```

**Bước 3:** Thêm vào `main.py`
```python
# Trong FBManagerApp.__init__
self.tabs["new_tab"] = NewTab(self.content_frame, self.api, self.db)

# Trong create_sidebar
self.add_nav_button("New Tab", "new_tab", "icon.png")
```

---

### 2. Thêm Chức Năng Mới Vào Tab

```python
# Trong tab class
def new_feature(self, params):
    """Mô tả chức năng"""
    # 1. Lấy dữ liệu từ UI
    # 2. Gọi API hoặc CDP
    # 3. Lưu kết quả vào DB
    # 4. Cập nhật UI
    pass
```

---

### 3. Thêm Database Table

**Bước 1:** Thêm CREATE TABLE trong `db.py`
```python
def create_tables(self):
    # ... existing tables ...

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS new_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            field1 TEXT,
            field2 INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
```

**Bước 2:** Thêm CRUD methods
```python
def add_new_record(self, field1, field2):
    cursor.execute('''
        INSERT INTO new_table (field1, field2)
        VALUES (?, ?)
    ''', (field1, field2))
    return cursor.lastrowid

def get_new_records(self):
    cursor.execute('SELECT * FROM new_table')
    return cursor.fetchall()
```

---

### 4. Thêm Automation Action

**Bước 1:** Định nghĩa job trong `automation/jobs.py`
```python
class NewActionJob(Job):
    async def execute(self):
        try:
            # 1. Navigate
            await self.cdp.navigate(self.context.target_url)

            # 2. Wait for element
            await self.cdp.wait_for_selector("#target-element")

            # 3. Perform action
            await self.cdp.click("#target-element")

            # 4. Return result
            return JobResult(success=True, data={"action": "completed"})
        except Exception as e:
            return JobResult(success=False, error=str(e))
```

**Bước 2:** Gọi từ tab
```python
async def run_new_action(self, profile_id, target_url):
    # Mở browser
    browser_info = self.api.open_browser(profile_id)

    # Tạo job
    context = JobContext(
        profile_id=profile_id,
        action_type="new_action",
        target_url=target_url,
        data={}
    )
    job = NewActionJob(context)

    # Kết nối CDP
    job.cdp = CDPHelper(browser_info['ws_url'])
    await job.cdp.connect()

    # Thực thi
    result = await job.execute()
    return result
```

---

### 5. Thay Đổi UI Style

Sửa trong `config.py`:
```python
COLORS = {
    "bg_dark": "#1a1a2e",      # Màu nền tối
    "bg_medium": "#16213e",     # Màu nền trung bình
    "accent": "#0f3460",        # Màu nhấn
    "text": "#eaeaea",          # Màu chữ
    "success": "#4ade80",       # Màu thành công
    "error": "#f87171",         # Màu lỗi
    "warning": "#fbbf24",       # Màu cảnh báo
}
```

---

### 6. Debug Tips

```python
# Thêm logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Trong function
logger.debug(f"Variable value: {var}")
logger.info("Action completed")
logger.error(f"Error: {e}")

# Screenshot khi lỗi
await self.cdp.screenshot("debug_screenshot.png")

# Print DOM
html = await self.cdp.evaluate("document.body.innerHTML")
print(html)
```

---

## Lưu Ý Quan Trọng

1. **Hidemium phải chạy** trước khi mở ứng dụng (localhost:2222)

2. **API Token** phải đúng trong `config.py`

3. **Facebook selectors** có thể thay đổi, cần cập nhật trong:
   - `tabs/login_tab.py` - selectors đăng nhập
   - `tabs/pages_tab.py` - selectors tạo/quét page
   - `tabs/groups_tab.py` - selectors đăng bài group

4. **Vietnamese UI** - App hỗ trợ cả English và Vietnamese Facebook UI

5. **Anti-detection** - Luôn sử dụng `HumanBehavior` để tránh bị phát hiện bot

6. **Error handling** - Luôn wrap CDP calls trong try-catch

7. **Database** - Backup `data/fbmanager.db` định kỳ

---

## Liên Hệ & Hỗ Trợ

- **Repository**: managefb
- **Database**: `data/fbmanager.db`
- **Config**: `config.py`
- **Dependencies**: `requirements.txt`

---

*Tài liệu được tạo tự động - Cập nhật: 2026-01-17*
