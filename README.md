# 🚀 Facebook Manager Pro

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/CustomTkinter-5.2.2-green" alt="CustomTkinter">
  <img src="https://img.shields.io/badge/Hidemium-API-orange" alt="Hidemium">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License">
</p>

**Facebook Manager Pro** là ứng dụng desktop chuyên nghiệp để quản lý nhiều tài khoản Facebook thông qua tích hợp **Hidemium Browser API**. Ứng dụng cho phép quản lý profiles, chạy scripts tự động hóa, và theo dõi các bài đăng.

---

## 📋 Mục lục

- [Tính năng](#-tính-năng)
- [Screenshots](#-screenshots)
- [Yêu cầu hệ thống](#-yêu-cầu-hệ-thống)
- [Cài đặt](#-cài-đặt)
- [Cấu hình](#-cấu-hình)
- [Hướng dẫn sử dụng](#-hướng-dẫn-sử-dụng)
- [Cấu trúc dự án](#-cấu-trúc-dự-án)
- [API Reference](#-api-reference)
- [Build EXE](#-build-exe)
- [Troubleshooting](#-troubleshooting)
- [Đóng góp](#-đóng-góp)
- [License](#-license)

---

## ✨ Tính năng

### 📋 Tab Profiles - Quản lý Profile

| Tính năng | Mô tả |
|-----------|-------|
| 🔄 **Auto Refresh** | Tự động cập nhật trạng thái profiles mỗi 5 giây |
| 🟢 **Real-time Status** | Hiển thị trạng thái Running/Stopped theo thời gian thực |
| 📂 **Folder Filter** | Lọc profiles theo thư mục (folder) |
| ▶️ **Open/Close Browser** | Mở/đóng browser Hidemium cho từng profile |
| ➕ **Create Profile** | Tạo profile mới với đầy đủ tùy chọn OS |
| 🔍 **Search** | Tìm kiếm profile theo tên |

**Hỗ trợ tạo profile cho các nền tảng:**
- 🪟 **Windows** (10, 11)
- 🍎 **macOS** (14.3.0, 13.6.0, 12.7.0, ...)
- 🐧 **Linux** (Ubuntu 24.04, 22.04, Debian 12, ...)
- 🤖 **Android** (8.1 → 15)
- 📱 **iOS** (15.0 → 18.0)

### 📜 Tab Scripts - Quản lý Kịch bản

| Tính năng | Mô tả |
|-----------|-------|
| ☁️ **Hidemium Scripts** | Đồng bộ scripts từ Hidemium Cloud |
| 💻 **Local Python Scripts** | Viết và chạy scripts Python tự động hóa |
| 📝 **Script Templates** | Templates sẵn có: Auto Like, Auto Comment, Auto Scroll |
| ▶️ **Run Script** | Chạy script trên profile đã chọn |
| 📊 **Log Output** | Xem kết quả chạy script real-time |

**Templates có sẵn:**
```python
# 🎯 Auto Like - Tự động like bài viết
# 💬 Auto Comment - Tự động comment
# 📜 Auto Scroll - Tự động scroll newfeed
# ✏️ Custom Script - Viết script tùy chỉnh
```

### 📝 Tab Posts - Quản lý Bài đăng

| Tính năng | Mô tả |
|-----------|-------|
| 📋 **Post List** | Danh sách các bài đã đăng với URL |
| ❤️ **Auto Like** | Like bài viết tự động |
| 💬 **Auto Comment** | Comment bài viết tự động |
| 📊 **Statistics** | Thống kê tương tác |

---

## 📸 Screenshots

```
┌─────────────────────────────────────────────────────────────────┐
│  🔵 Facebook Manager Pro                              ─ □ ✕    │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                        │
│  │📋 Profiles│ │📜 Scripts │ │📝 Posts  │                        │
│  └──────────┘ └──────────┘ └──────────┘                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🔍 Search...                    📂 All Folders ▼              │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Profile Name          │ Status    │ Folder   │ Actions  │   │
│  ├───────────────────────┼───────────┼──────────┼──────────┤   │
│  │ FB Account 1          │ 🟢 Running │ Main     │ [Close]  │   │
│  │ FB Account 2          │ ⚫ Stopped │ Backup   │ [Open]   │   │
│  │ FB Account 3          │ ⚫ Stopped │ Main     │ [Open]   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  [🔄 Refresh]  [➕ Create Profile]                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 💻 Yêu cầu hệ thống

| Thành phần | Yêu cầu |
|------------|---------|
| **OS** | Windows 10/11 (64-bit) |
| **Python** | 3.10+ (khuyến nghị 3.12) |
| **RAM** | 4GB+ |
| **Hidemium Browser** | Phiên bản mới nhất với API enabled |
| **Kết nối** | Localhost port 2222 |

---

## 📦 Cài đặt

### 1. Clone repository

```bash
git clone https://github.com/thaonguyenngu999-ui/managefb.git
cd managefb
```

### 2. Tạo môi trường ảo

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### 3. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 4. Chạy ứng dụng

```bash
python main.py
```

---

## ⚙️ Cấu hình

### Hidemium API Configuration

Chỉnh sửa file `config.py`:

```python
# Hidemium Browser API Configuration
HIDEMIUM_API_URL = "http://127.0.0.1:2222"
HIDEMIUM_TOKEN = "Your_API_Token_Here"

# App Settings
APP_TITLE = "Facebook Manager Pro"
REFRESH_INTERVAL = 5000  # milliseconds (5 giây)
```

### Lấy API Token từ Hidemium

1. Mở **Hidemium Browser**
2. Vào **Settings** → **API**
3. Enable **API Server**
4. Copy **API Token**
5. Dán vào `config.py`

---

## 📖 Hướng dẫn sử dụng

### 1️⃣ Quản lý Profiles

**Xem danh sách profiles:**
- Mở ứng dụng → Tab "📋 Profiles"
- Profiles tự động load từ Hidemium

**Mở/Đóng browser:**
- Click nút **[Open]** để mở browser cho profile
- Click nút **[Close]** để đóng browser đang chạy

**Lọc theo folder:**
- Chọn folder từ dropdown "📂 All Folders"

**Tạo profile mới:**
1. Click **[➕ Create Profile]**
2. Điền thông tin:
   - **Name**: Tên profile
   - **OS**: Chọn hệ điều hành (Windows/macOS/Linux/Android/iOS)
   - **OS Version**: Chọn phiên bản OS
   - **Browser Version**: Phiên bản Chrome (mặc định: 143)
3. Click **[Create]**

### 2️⃣ Chạy Scripts

**Hidemium Scripts:**
1. Vào Tab "📜 Scripts" → "☁️ Hidemium Scripts"
2. Click **[🔄 Sync Scripts]** để lấy scripts từ cloud
3. Chọn script → Chọn profile → Click **[▶️ Run]**

**Local Python Scripts:**
1. Vào Tab "📜 Scripts" → "💻 Local Scripts"
2. Chọn template hoặc viết code tùy chỉnh
3. Click **[💾 Save]** để lưu
4. Chọn profile → Click **[▶️ Run Script]**

### 3️⃣ Quản lý Posts

1. Vào Tab "📝 Posts"
2. Thêm URL bài đăng cần theo dõi
3. Sử dụng các nút Like/Comment để tương tác

---

## 📁 Cấu trúc dự án

```
managefb/
├── 📄 main.py              # Entry point - Khởi động ứng dụng
├── 📄 config.py            # Cấu hình API, settings
├── 📄 api_service.py       # Hidemium API client
├── 📄 database.py          # Local JSON database
├── 📄 widgets.py           # Custom widgets
├── 📄 requirements.txt     # Python dependencies
├── 📄 build.spec           # PyInstaller spec file
├── 📄 README.md            # Tài liệu này
│
├── 📁 tabs/                # Các tab UI
│   ├── 📄 __init__.py
│   ├── 📄 profiles_tab.py  # Tab quản lý profiles
│   ├── 📄 scripts_tab.py   # Tab quản lý scripts
│   └── 📄 posts_tab.py     # Tab quản lý posts
│
└── 📁 data/                # Local data storage
    ├── 📄 profiles.json    # Cache profiles
    ├── 📄 scripts.json     # Saved scripts
    └── 📄 settings.json    # App settings
```

---

## 🔌 API Reference

### Hidemium Browser API Endpoints

| Endpoint | Method | Mô tả |
|----------|--------|-------|
| `/api/v2/profiles` | GET | Lấy danh sách profiles |
| `/api/v2/profiles` | POST | Tạo profile mới |
| `/api/v2/profiles/{id}` | PUT | Cập nhật profile |
| `/api/v2/profiles/{id}` | DELETE | Xóa profile |
| `/api/v2/browser/open/{id}` | GET | Mở browser |
| `/api/v2/browser/close/{id}` | GET | Đóng browser |
| `/api/v2/status-profile` | GET | Lấy profiles đang chạy |
| `/api/v2/folders` | GET | Lấy danh sách folders |
| `/api/v2/scripts` | GET | Lấy danh sách scripts |
| `/api/v2/scripts/run` | POST | Chạy script |

### Request Headers

```
Authorization: Bearer {HIDEMIUM_TOKEN}
Content-Type: application/json
```

### Ví dụ API Call

```python
import requests

API_URL = "http://127.0.0.1:2222"
TOKEN = "Your_Token"

# Lấy danh sách profiles
response = requests.get(
    f"{API_URL}/api/v2/profiles",
    headers={"Authorization": f"Bearer {TOKEN}"}
)
profiles = response.json()
```

---

## 🏗️ Build EXE

### Sử dụng PyInstaller

```bash
# Cài đặt PyInstaller
pip install pyinstaller

# Build EXE với spec file
pyinstaller build.spec

# Hoặc build trực tiếp
pyinstaller --onefile --windowed --name="FacebookManagerPro" main.py
```

### File build.spec

```python
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('data', 'data')],
    hiddenimports=['customtkinter'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='FacebookManagerPro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='icon.ico'  # Optional
)
```

**Output:** `dist/FacebookManagerPro.exe`

---

## 🛠️ Troubleshooting

### Lỗi thường gặp

| Lỗi | Nguyên nhân | Giải pháp |
|-----|-------------|-----------|
| `Connection refused` | Hidemium API chưa bật | Mở Hidemium → Settings → Enable API |
| `401 Unauthorized` | Token sai | Kiểm tra lại token trong config.py |
| `RuntimeError: main thread` | Threading issue | Đã fix với `_safe_after()` wrapper |
| `osVersion invalid` | OS version không hợp lệ | Sử dụng version từ dropdown |
| `git not recognized` | Git chưa cài hoặc PATH chưa refresh | Restart terminal hoặc cài Git |

### Debug Mode

```python
# Bật debug trong config.py
DEBUG = True
LOG_LEVEL = "DEBUG"
```

### Reset Database

```bash
# Xóa cache local để làm mới
rm -rf data/*.json
```

---

## 🎨 Giao diện

- **Theme tối** - Dễ nhìn, hiện đại với CustomTkinter
- **UI responsive** - Tự điều chỉnh theo kích thước cửa sổ
- **Tab Navigation** - Chuyển tab dễ dàng
- **Auto-refresh** - Cập nhật trạng thái real-time
- **Status indicators** - Icon màu cho trạng thái Running/Stopped

---

## 🤝 Đóng góp

1. Fork repository
2. Tạo branch mới (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push branch (`git push origin feature/AmazingFeature`)
5. Tạo Pull Request

### Coding Standards

- Python PEP8 style guide
- Docstrings cho functions
- Type hints khi có thể
- Comments tiếng Việt/Anh

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.

---

## 👨‍💻 Tác giả

**thaonguyenngu999-ui**

- GitHub: [@thaonguyenngu999-ui](https://github.com/thaonguyenngu999-ui)
- Repository: [managefb](https://github.com/thaonguyenngu999-ui/managefb)

---

## 🙏 Acknowledgments

- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) - Modern UI framework cho Python
- [Hidemium Browser](https://hidemium.io) - Anti-detect browser với API mạnh mẽ
- [Python Requests](https://requests.readthedocs.io) - HTTP library đơn giản và hiệu quả

---

## 📝 Changelog

### v1.0.0 (2026-01-15)
- ✅ Initial release
- ✅ Profiles Tab với auto-refresh
- ✅ Scripts Tab với Hidemium + Local Python scripts
- ✅ Posts Tab (basic UI)
- ✅ Create Profile hỗ trợ Windows/macOS/Linux/Android/iOS
- ✅ Thread-safe callbacks với `_safe_after()` wrapper

---

<p align="center">
  Made with ❤️ by thaonguyenngu999-ui
</p>


### ⚠️ Lưu ý

- Đảm bảo Hidemium Browser đang chạy trước khi mở ứng dụng
- Token API có thể lấy từ cài đặt Hidemium
- Dữ liệu kịch bản và bài đăng được lưu local trong thư mục `data/`

### 📄 License

Private - Chỉ sử dụng nội bộ

---
Made with ❤️ by FB Manager Team
