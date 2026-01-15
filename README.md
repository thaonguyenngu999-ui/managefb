# FB Manager Pro

## 🔥 Phần mềm quản lý tài khoản Facebook

Phần mềm desktop tích hợp với **Hidemium Browser API** để quản lý và tự động hóa các tài khoản Facebook.

### ✨ Tính năng chính

1. **📋 Quản lý Profiles**
   - Xem danh sách tất cả profiles từ Hidemium
   - Mở/Đóng browser nhanh chóng
   - Chỉnh sửa tên, ghi chú, proxy
   - Lọc theo trạng thái (đang chạy/đã dừng)
   - Xóa nhiều profiles cùng lúc

2. **📜 Kịch bản tự động**
   - Viết và lưu các kịch bản tự động
   - Hỗ trợ nhiều loại: Like, Comment, Share, Add Friend, Post
   - Editor với syntax highlighting
   - Template có sẵn
   - Test kịch bản trước khi chạy

3. **📰 Quản lý Bài đăng**
   - Thêm URL bài viết Facebook
   - Tự động Like với nhiều tài khoản
   - Tự động Comment với nội dung tùy chỉnh
   - Theo dõi thống kê (likes, comments)
   - Đẩy bài lên bản tin mới nhất

### 🚀 Cài đặt

1. **Cài đặt Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Cấu hình Hidemium:**
   - Mở file `config.py`
   - Cập nhật `HIDEMIUM_TOKEN` với token của bạn
   - (Tùy chọn) Thay đổi `HIDEMIUM_BASE_URL` nếu cần

3. **Chạy ứng dụng:**
   ```bash
   python main.py
   ```

### 📦 Build EXE

Để build thành file `.exe`:

```bash
# Cài đặt PyInstaller
pip install pyinstaller

# Build
pyinstaller build.spec

# Hoặc build đơn giản
pyinstaller --onefile --windowed --name "FB Manager Pro" main.py
```

File exe sẽ được tạo trong thư mục `dist/`

### 📁 Cấu trúc thư mục

```
managefb/
├── main.py              # Entry point
├── config.py            # Cấu hình ứng dụng
├── api_service.py       # Hidemium API service
├── database.py          # Database local (JSON)
├── widgets.py           # Custom UI widgets
├── tabs/
│   ├── __init__.py
│   ├── profiles_tab.py  # Tab quản lý profiles
│   ├── scripts_tab.py   # Tab kịch bản
│   └── posts_tab.py     # Tab bài đăng
├── data/                # Dữ liệu local
│   ├── scripts.json     # Kịch bản đã lưu
│   ├── posts.json       # Bài đăng đã lưu
│   └── settings.json    # Cài đặt
├── requirements.txt     # Dependencies
├── build.spec          # PyInstaller config
└── README.md           # Documentation
```

### 🎨 Giao diện

- **Theme tối** - Dễ nhìn, hiện đại
- **UI responsive** - Tự điều chỉnh theo kích thước cửa sổ
- **Navigation sidebar** - Chuyển tab dễ dàng
- **Status bar** - Theo dõi trạng thái kết nối và hoạt động

### 🔧 Yêu cầu hệ thống

- Windows 10/11
- Python 3.9+
- Hidemium Browser đang chạy
- RAM: 4GB+
- Ổ cứng: 100MB

### 📝 API Reference

Xem chi tiết trong file `api.txt` - Tài liệu API Hidemium đầy đủ.

### ⚠️ Lưu ý

- Đảm bảo Hidemium Browser đang chạy trước khi mở ứng dụng
- Token API có thể lấy từ cài đặt Hidemium
- Dữ liệu kịch bản và bài đăng được lưu local trong thư mục `data/`

### 📄 License

Private - Chỉ sử dụng nội bộ

---
Made with ❤️ by FB Manager Team
