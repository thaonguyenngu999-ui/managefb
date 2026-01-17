# FB Manager Pro - Hướng dẫn & Ngữ cảnh hiện tại

## Tổng quan
Phần mềm quản lý tài khoản Facebook, tích hợp Hidemium Browser API để tự động hóa các tác vụ.

## Kiến trúc

### Cấu trúc thư mục
```
managefb/
├── main.py                 # Entry point, tạo UI chính
├── db.py                   # Database SQLite (fb_manager.db)
├── config.py               # Cấu hình (COLORS, kích thước...)
├── api_service.py          # Giao tiếp với Hidemium API
├── automation/
│   └── window_manager.py   # Quản lý vị trí cửa sổ browser
├── tabs/
│   ├── __init__.py
│   ├── profiles_tab.py     # Quản lý profiles Hidemium
│   ├── login_tab.py        # Login Facebook
│   ├── pages_tab.py        # Quản lý & Tạo Page
│   ├── reels_page_tab.py   # Đăng Reels lên Page (MỚI)
│   ├── groups_tab.py       # Đăng bài vào Groups
│   ├── content_tab.py      # Soạn nội dung
│   ├── scripts_tab.py      # Kịch bản tự động
│   └── posts_tab.py        # Lịch sử bài đăng
└── widgets/                # Custom UI components
```

### Công nghệ
- **UI**: CustomTkinter (dark theme)
- **Database**: SQLite3 (`data/fb_manager.db`)
- **Browser Automation**: Chrome DevTools Protocol (CDP) qua WebSocket
- **Browser**: Hidemium (anti-detect browser)

---

## Các tính năng đã implement

### 1. Quản lý Page (`tabs/pages_tab.py`)

#### Scan Page
- Navigate đến `https://www.facebook.com/pages/?category=your_pages`
- Scroll để load tất cả pages
- Dùng JavaScript tìm links có pattern:
  - `profile.php?id=XXXXXX`
  - `/XXXXXX` (numeric ID 10+ digits)
- Lưu vào bảng `pages` trong database

#### Tạo Page
- Navigate đến `https://www.facebook.com/pages/create`
- Điền form với selectors đã xác nhận:
  - Tên Page: `input.x1i10hfl[type="text"]`
  - Hạng mục: `input[aria-label="Hạng mục (Bắt buộc)"]` + ArrowDown + Enter
  - Tiểu sử: `textarea.x1i10hfl`
- Click nút "Tạo Trang"
- Đợi URL thay đổi để lấy page_id thực

### 2. Đăng Reels Page (`tabs/reels_page_tab.py`) - MỚI

#### Flow đăng Reels
1. Mở browser với profile
2. Navigate đến page URL để switch context
3. Navigate đến `https://www.facebook.com/reels/create`
4. Upload video qua `DOM.setFileInputFiles`
5. Điền caption + hashtags
6. Click nút Share/Đăng

#### Lên lịch đăng
- Bảng `reel_schedules` trong database
- Các trạng thái: pending, completed, failed

---

## Vấn đề hiện tại cần fix

### 1. Scan Page không lưu vào database

**Triệu chứng:**
- Console hiện: `[Pages] JS found 1 pages` và `[Pages] Found 1 pages for local-12`
- Nhưng khi vào tab "Đăng Reels Page" và chọn profile, không thấy page nào

**Nguyên nhân có thể:**
- File database trên Windows (`C:\Users\V\managefb\managefb\data\fb_manager.db`) khác với Linux
- Exception bị nuốt silent khi save

**Debug đã thêm:**
```python
# db.py - sync_pages()
def sync_pages(profile_uuid: str, pages_from_scan: List[Dict]):
    saved_count = 0
    for page in pages_from_scan:
        try:
            page['profile_uuid'] = profile_uuid
            result = save_page(page)
            if result.get('id'):
                saved_count += 1
                print(f"[DB] Saved page: {page.get('page_name')} (ID: {result.get('id')})")
        except Exception as e:
            print(f"[DB] ERROR saving page {page.get('page_name')}: {e}")
    print(f"[DB] sync_pages completed: {saved_count}/{len(pages_from_scan)} pages saved")
```

**Cách test:**
1. Chạy app
2. Vào tab "Quản lý Page"
3. Chọn profile và bấm "Scan Pages"
4. Xem console - phải thấy:
   - `[DB] Saved page: V Giải Trí (ID: 1)`
   - `[DB] sync_pages completed: 1/1 pages saved`
5. Nếu không thấy → có exception, xem log ERROR

**Cách verify database:**
```python
# Chạy trong Python console
from db import get_pages, get_profiles

profiles = get_profiles()
print(f"Profiles: {len(profiles)}")

pages = get_pages()
print(f"Pages: {len(pages)}")
for p in pages:
    print(f"  - {p['page_name']} (profile: {p['profile_uuid'][:8]})")
```

### 2. Đăng Reels chưa test thực tế

**File:** `tabs/reels_page_tab.py`

**Những điểm cần kiểm tra:**
1. Selector cho caption field - có thể khác với code hiện tại
2. Selector cho nút Share/Đăng
3. Thời gian chờ video upload (hiện 8 giây, có thể cần tăng)

**Debug:**
- Tất cả bước đều có `print()` để theo dõi
- Xem console khi đăng để biết bước nào fail

---

## Cấu trúc Database

### Bảng `pages`
```sql
CREATE TABLE pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_uuid TEXT NOT NULL,
    page_id TEXT NOT NULL,        -- Facebook page ID
    page_name TEXT,
    page_url TEXT,
    category TEXT,
    follower_count INTEGER DEFAULT 0,
    role TEXT DEFAULT 'admin',
    note TEXT,
    is_selected INTEGER DEFAULT 0,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

### Bảng `reel_schedules`
```sql
CREATE TABLE reel_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_uuid TEXT NOT NULL,
    page_id INTEGER,
    page_name TEXT,
    video_path TEXT NOT NULL,
    cover_path TEXT,
    caption TEXT,
    hashtags TEXT,
    scheduled_time TIMESTAMP NOT NULL,
    delay_min INTEGER DEFAULT 30,
    delay_max INTEGER DEFAULT 60,
    status TEXT DEFAULT 'pending',  -- pending, completed, failed
    reel_url TEXT,
    error_message TEXT,
    executed_at TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

---

## CDP (Chrome DevTools Protocol) Pattern

### Kết nối
```python
import websocket
import json

# 1. Lấy danh sách tabs
cdp_base = f"http://127.0.0.1:{remote_port}"
tabs_url = f"{cdp_base}/json"
# GET request → list of tabs with webSocketDebuggerUrl

# 2. Kết nối WebSocket
ws = websocket.create_connection(page_ws, timeout=30, suppress_origin=True)
```

### Gửi command
```python
def _cdp_send(ws, method, params=None):
    msg = {"id": unique_id, "method": method, "params": params or {}}
    ws.send(json.dumps(msg))
    # Wait for response with matching id
    return response

# Navigate
_cdp_send(ws, "Page.navigate", {"url": "https://facebook.com"})

# Execute JavaScript
result = _cdp_send(ws, "Runtime.evaluate", {
    "expression": "document.title",
    "returnByValue": True
})

# Upload file
_cdp_send(ws, "DOM.setFileInputFiles", {
    "nodeId": input_node_id,
    "files": ["/path/to/video.mp4"]
})
```

### Tìm element
```python
# 1. Lấy document root
doc = _cdp_send(ws, "DOM.getDocument", {})
root_id = doc['result']['root']['nodeId']

# 2. Query selector
result = _cdp_send(ws, "DOM.querySelectorAll", {
    "nodeId": root_id,
    "selector": 'input[type="file"]'
})
node_ids = result['result']['nodeIds']
```

---

## React-compatible Input

Facebook dùng React nên cần set value đúng cách:

```javascript
function setValueAndTrigger(input, value) {
    input.focus();
    input.click();

    // Dùng native setter để bypass React
    if (input.tagName === 'INPUT') {
        var setter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype, 'value'
        ).set;
        setter.call(input, value);
    } else if (input.tagName === 'TEXTAREA') {
        var setter = Object.getOwnPropertyDescriptor(
            window.HTMLTextAreaElement.prototype, 'value'
        ).set;
        setter.call(input, value);
    }

    // Trigger events
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
}
```

---

## Checklist khi fix bug

1. **Luôn check console log** - tất cả operations đều có print()
2. **Test database riêng** - dùng Python shell để verify data
3. **Selenium selector** - có thể thay đổi khi FB update, cần inspect lại
4. **Timing** - Facebook load chậm, tăng time.sleep() nếu cần
5. **WebSocket close** - đảm bảo close() sau khi dùng xong, không close trước khi execute JS

---

## Commits gần đây

1. `Fix WebSocket closed prematurely in Scan Page` - ws.close() được gọi trước khi JS chạy
2. `Implement actual Reels posting via CDP` - thêm code đăng Reels thực tế
3. `Fix window_manager import path` - sửa `from window_manager` → `from automation.window_manager`
4. `Add debug logging to sync_pages` - thêm log để debug vấn đề lưu DB

---

## Liên hệ

- Branch: `claude/fix-chat-performance-gLl6v`
- Repo: `thaonguyenngu999-ui/managefb`
