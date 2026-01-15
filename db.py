"""
SQLite Database Manager for FB Manager Pro
Quản lý dữ liệu với SQLite thay vì JSON files
"""
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional
from contextlib import contextmanager

# Database path
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DATA_DIR, "fbmanager.db")


def ensure_data_dir():
    """Đảm bảo thư mục data tồn tại"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


@contextmanager
def get_connection():
    """Context manager để quản lý kết nối database"""
    ensure_data_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Trả về dict-like rows
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_database():
    """Khởi tạo database và tạo các bảng"""
    with get_connection() as conn:
        cursor = conn.cursor()

        # ============ CATEGORIES TABLE ============
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ============ CONTENTS TABLE ============
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                image_path TEXT,
                stickers TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
            )
        """)

        # ============ PROFILES TABLE ============
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uuid TEXT UNIQUE,
                name TEXT,
                browser TEXT,
                os TEXT,
                status TEXT DEFAULT 'stopped',
                proxy TEXT,
                note TEXT,
                tags TEXT,
                local_notes TEXT,
                fb_uid TEXT,
                fb_name TEXT,
                check_open INTEGER DEFAULT 0,
                last_sync TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ============ SCRIPTS TABLE ============
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                type TEXT DEFAULT 'python',
                content TEXT,
                hidemium_key TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ============ POSTS TABLE ============
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                title TEXT,
                target_likes INTEGER DEFAULT 0,
                target_comments INTEGER DEFAULT 0,
                like_count INTEGER DEFAULT 0,
                comment_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ============ SETTINGS TABLE ============
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tạo category mặc định nếu chưa có
        cursor.execute("SELECT COUNT(*) FROM categories")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO categories (name, description) VALUES (?, ?)",
                ("Mặc định", "Category mặc định")
            )

        # Tạo indexes để tăng tốc query
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_contents_category ON contents(category_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_profiles_uuid ON profiles(uuid)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scripts_type ON scripts(type)")


def row_to_dict(row) -> Dict:
    """Chuyển sqlite3.Row thành dict"""
    if row is None:
        return None
    return dict(row)


def rows_to_list(rows) -> List[Dict]:
    """Chuyển list of sqlite3.Row thành list of dict"""
    return [dict(row) for row in rows]


# ==================== CATEGORIES ====================

def get_categories() -> List[Dict]:
    """Lấy danh sách tất cả categories"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categories ORDER BY id")
        return rows_to_list(cursor.fetchall())


def get_category_by_id(category_id: int) -> Optional[Dict]:
    """Lấy category theo ID"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
        return row_to_dict(cursor.fetchone())


def save_category(data: Dict) -> Dict:
    """Lưu category (tạo mới hoặc cập nhật)"""
    with get_connection() as conn:
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        if data.get('id'):
            # Update
            cursor.execute("""
                UPDATE categories
                SET name = ?, description = ?, updated_at = ?
                WHERE id = ?
            """, (data.get('name'), data.get('description', ''), now, data['id']))
            return get_category_by_id(data['id'])
        else:
            # Insert
            cursor.execute("""
                INSERT INTO categories (name, description, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """, (data.get('name'), data.get('description', ''), now, now))
            data['id'] = cursor.lastrowid
            return data


def delete_category(category_id: int) -> bool:
    """Xóa category (không cho xóa category mặc định id=1)"""
    if category_id == 1:
        return False
    with get_connection() as conn:
        cursor = conn.cursor()
        # Xóa contents thuộc category này trước
        cursor.execute("DELETE FROM contents WHERE category_id = ?", (category_id,))
        cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        return cursor.rowcount > 0


# ==================== CONTENTS ====================

def get_contents(category_id: int = None) -> List[Dict]:
    """Lấy danh sách contents, có thể lọc theo category"""
    with get_connection() as conn:
        cursor = conn.cursor()
        if category_id:
            cursor.execute(
                "SELECT * FROM contents WHERE category_id = ? ORDER BY id DESC",
                (category_id,)
            )
        else:
            cursor.execute("SELECT * FROM contents ORDER BY id DESC")
        return rows_to_list(cursor.fetchall())


def get_content_by_id(content_id: int) -> Optional[Dict]:
    """Lấy content theo ID"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM contents WHERE id = ?", (content_id,))
        return row_to_dict(cursor.fetchone())


def save_content(data: Dict) -> Dict:
    """Lưu content (tạo mới hoặc cập nhật)"""
    with get_connection() as conn:
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        if data.get('id'):
            # Update
            cursor.execute("""
                UPDATE contents
                SET category_id = ?, title = ?, content = ?,
                    image_path = ?, stickers = ?, updated_at = ?
                WHERE id = ?
            """, (
                data.get('category_id', 1),
                data.get('title', ''),
                data.get('content', ''),
                data.get('image_path', ''),
                data.get('stickers', ''),
                now,
                data['id']
            ))
            return get_content_by_id(data['id'])
        else:
            # Insert
            cursor.execute("""
                INSERT INTO contents (category_id, title, content, image_path, stickers, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('category_id', 1),
                data.get('title', ''),
                data.get('content', ''),
                data.get('image_path', ''),
                data.get('stickers', ''),
                now, now
            ))
            data['id'] = cursor.lastrowid
            return data


def delete_content(content_id: int) -> bool:
    """Xóa content"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM contents WHERE id = ?", (content_id,))
        return cursor.rowcount > 0


def get_contents_count(category_id: int = None) -> int:
    """Đếm số contents"""
    with get_connection() as conn:
        cursor = conn.cursor()
        if category_id:
            cursor.execute("SELECT COUNT(*) FROM contents WHERE category_id = ?", (category_id,))
        else:
            cursor.execute("SELECT COUNT(*) FROM contents")
        return cursor.fetchone()[0]


# ==================== PROFILES ====================

def get_profiles() -> List[Dict]:
    """Lấy danh sách profiles"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM profiles ORDER BY id DESC")
        return rows_to_list(cursor.fetchall())


def get_profile_by_uuid(uuid: str) -> Optional[Dict]:
    """Lấy profile theo UUID"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM profiles WHERE uuid = ?", (uuid,))
        return row_to_dict(cursor.fetchone())


def save_profile(data: Dict) -> Dict:
    """Lưu profile"""
    import json as json_module

    with get_connection() as conn:
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        # Convert lists to JSON strings
        tags = data.get('tags', '')
        if isinstance(tags, list):
            tags = json_module.dumps(tags, ensure_ascii=False)

        existing = get_profile_by_uuid(data.get('uuid', ''))

        if existing:
            # Update - giữ lại local data nếu không được cung cấp
            cursor.execute("""
                UPDATE profiles
                SET name = ?, browser = ?, os = ?, status = ?,
                    proxy = ?, note = ?, tags = ?,
                    local_notes = ?, fb_uid = ?, fb_name = ?, check_open = ?,
                    last_sync = ?, updated_at = ?
                WHERE uuid = ?
            """, (
                data.get('name', ''),
                data.get('browser', ''),
                data.get('os', ''),
                data.get('status', 'stopped'),
                data.get('proxy', ''),
                data.get('note', ''),
                tags,
                data.get('local_notes', existing.get('local_notes', '')),
                data.get('fb_uid', existing.get('fb_uid', '')),
                data.get('fb_name', existing.get('fb_name', '')),
                data.get('check_open', existing.get('check_open', 0)),
                now, now,
                data['uuid']
            ))
            return get_profile_by_uuid(data['uuid'])
        else:
            # Insert
            cursor.execute("""
                INSERT INTO profiles (uuid, name, browser, os, status, proxy, note, tags,
                    local_notes, fb_uid, fb_name, check_open, last_sync, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('uuid', ''),
                data.get('name', ''),
                data.get('browser', ''),
                data.get('os', ''),
                data.get('status', 'stopped'),
                data.get('proxy', ''),
                data.get('note', ''),
                tags,
                data.get('local_notes', ''),
                data.get('fb_uid', ''),
                data.get('fb_name', ''),
                data.get('check_open', 0),
                now, now, now
            ))
            data['id'] = cursor.lastrowid
            return data


def delete_profile(uuid: str) -> bool:
    """Xóa profile"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM profiles WHERE uuid = ?", (uuid,))
        return cursor.rowcount > 0


def sync_profiles(profiles_from_api: List[Dict]):
    """Đồng bộ profiles từ API vào database, giữ lại thông tin local"""
    for profile in profiles_from_api:
        uuid = profile.get('uuid')
        existing = get_profile_by_uuid(uuid)

        if existing:
            # Giữ lại thông tin local
            profile['local_notes'] = existing.get('local_notes', '')
            profile['fb_uid'] = existing.get('fb_uid', '')
            profile['fb_name'] = existing.get('fb_name', '')
            profile['check_open'] = existing.get('check_open', 0)
        else:
            profile['check_open'] = 0

        save_profile(profile)


def update_profile_local(uuid: str, data: Dict) -> bool:
    """Cập nhật thông tin local của profile (notes, fb_uid, fb_name, etc.)"""
    existing = get_profile_by_uuid(uuid)
    if not existing:
        return False

    # Merge data
    existing.update(data)
    save_profile(existing)
    return True


# ==================== SCRIPTS ====================

def get_scripts(script_type: str = None) -> List[Dict]:
    """Lấy danh sách scripts"""
    with get_connection() as conn:
        cursor = conn.cursor()
        if script_type:
            cursor.execute(
                "SELECT * FROM scripts WHERE type = ? ORDER BY id DESC",
                (script_type,)
            )
        else:
            cursor.execute("SELECT * FROM scripts ORDER BY id DESC")
        return rows_to_list(cursor.fetchall())


def get_script_by_id(script_id: int) -> Optional[Dict]:
    """Lấy script theo ID"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM scripts WHERE id = ?", (script_id,))
        return row_to_dict(cursor.fetchone())


def save_script(data: Dict) -> Dict:
    """Lưu script"""
    with get_connection() as conn:
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        if data.get('id'):
            cursor.execute("""
                UPDATE scripts
                SET name = ?, description = ?, type = ?, content = ?,
                    hidemium_key = ?, updated_at = ?
                WHERE id = ?
            """, (
                data.get('name', ''),
                data.get('description', ''),
                data.get('type', 'python'),
                data.get('content', ''),
                data.get('hidemium_key', ''),
                now, data['id']
            ))
            return get_script_by_id(data['id'])
        else:
            cursor.execute("""
                INSERT INTO scripts (name, description, type, content, hidemium_key, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('name', ''),
                data.get('description', ''),
                data.get('type', 'python'),
                data.get('content', ''),
                data.get('hidemium_key', ''),
                now, now
            ))
            data['id'] = cursor.lastrowid
            return data


def delete_script(script_id: int) -> bool:
    """Xóa script"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM scripts WHERE id = ?", (script_id,))
        return cursor.rowcount > 0


# ==================== POSTS ====================

def get_posts() -> List[Dict]:
    """Lấy danh sách posts"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM posts ORDER BY id DESC")
        return rows_to_list(cursor.fetchall())


def get_post_by_id(post_id: int) -> Optional[Dict]:
    """Lấy post theo ID"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
        return row_to_dict(cursor.fetchone())


def save_post(data: Dict) -> Dict:
    """Lưu post"""
    with get_connection() as conn:
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        if data.get('id'):
            cursor.execute("""
                UPDATE posts
                SET url = ?, title = ?, target_likes = ?, target_comments = ?,
                    like_count = ?, comment_count = ?, status = ?, updated_at = ?
                WHERE id = ?
            """, (
                data.get('url', ''),
                data.get('title', ''),
                data.get('target_likes', 0),
                data.get('target_comments', 0),
                data.get('like_count', 0),
                data.get('comment_count', 0),
                data.get('status', 'pending'),
                now, data['id']
            ))
            return get_post_by_id(data['id'])
        else:
            cursor.execute("""
                INSERT INTO posts (url, title, target_likes, target_comments, like_count, comment_count, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('url', ''),
                data.get('title', ''),
                data.get('target_likes', 0),
                data.get('target_comments', 0),
                data.get('like_count', 0),
                data.get('comment_count', 0),
                data.get('status', 'pending'),
                now, now
            ))
            data['id'] = cursor.lastrowid
            return data


def delete_post(post_id: int) -> bool:
    """Xóa post"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        return cursor.rowcount > 0


def update_post_stats(post_id: int, likes: int = 0, comments: int = 0):
    """Cập nhật thống kê post"""
    with get_connection() as conn:
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute("""
            UPDATE posts
            SET like_count = like_count + ?, comment_count = comment_count + ?, updated_at = ?
            WHERE id = ?
        """, (likes, comments, now, post_id))


# ==================== SETTINGS ====================

def get_settings() -> Dict:
    """Lấy tất cả settings"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        return {row['key']: row['value'] for row in cursor.fetchall()}


def get_setting(key: str, default=None):
    """Lấy một setting"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row['value'] if row else default


def set_setting(key: str, value):
    """Lưu một setting"""
    with get_connection() as conn:
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT OR REPLACE INTO settings (key, value, updated_at)
            VALUES (?, ?, ?)
        """, (key, str(value), now))


def save_settings(settings: Dict):
    """Lưu nhiều settings"""
    for key, value in settings.items():
        set_setting(key, value)


# ==================== MIGRATION ====================

def migrate_from_json():
    """Migrate dữ liệu từ JSON files sang SQLite"""
    import json

    json_files = {
        'categories': os.path.join(DATA_DIR, 'categories.json'),
        'contents': os.path.join(DATA_DIR, 'contents.json'),
        'profiles': os.path.join(DATA_DIR, 'profiles.json'),
        'scripts': os.path.join(DATA_DIR, 'scripts.json'),
        'posts': os.path.join(DATA_DIR, 'posts.json'),
        'settings': os.path.join(DATA_DIR, 'settings.json'),
    }

    for name, filepath in json_files.items():
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if name == 'categories' and data:
                    for item in data:
                        if item.get('id') != 1:  # Skip default
                            save_category(item)
                    print(f"Migrated {len(data)} categories")

                elif name == 'contents' and data:
                    for item in data:
                        save_content(item)
                    print(f"Migrated {len(data)} contents")

                elif name == 'profiles' and data:
                    for item in data:
                        save_profile(item)
                    print(f"Migrated {len(data)} profiles")

                elif name == 'scripts' and data:
                    for item in data:
                        save_script(item)
                    print(f"Migrated {len(data)} scripts")

                elif name == 'posts' and data:
                    for item in data:
                        save_post(item)
                    print(f"Migrated {len(data)} posts")

                elif name == 'settings' and data:
                    save_settings(data)
                    print(f"Migrated settings")

                # Rename old file
                os.rename(filepath, filepath + '.bak')
                print(f"Backed up {filepath}")

            except Exception as e:
                print(f"Error migrating {name}: {e}")


# Khởi tạo database khi import module
init_database()
