"""
Database Manager - Lưu trữ dữ liệu local
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Optional

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
PROFILES_FILE = os.path.join(DATA_DIR, "profiles.json")
SCRIPTS_FILE = os.path.join(DATA_DIR, "scripts.json")
POSTS_FILE = os.path.join(DATA_DIR, "posts.json")
CAMPAIGNS_FILE = os.path.join(DATA_DIR, "campaigns.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")


def ensure_data_dir():
    """Đảm bảo thư mục data tồn tại"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def load_json(filepath: str) -> List | Dict:
    """Load dữ liệu từ file JSON"""
    ensure_data_dir()
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError, OSError):
            # Return empty list on JSON parse errors or file read errors
            return []
    return []


def save_json(filepath: str, data: List | Dict):
    """Lưu dữ liệu vào file JSON"""
    ensure_data_dir()
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ============ PROFILES MANAGEMENT ============

def get_profiles() -> List[Dict]:
    """Lấy danh sách profiles từ local DB"""
    return load_json(PROFILES_FILE)


def sync_profiles(profiles: List[Dict]) -> bool:
    """Đồng bộ profiles từ Hidemium vào local DB"""
    existing = get_profiles()
    existing_uuids = {p.get('uuid'): p for p in existing}
    
    for profile in profiles:
        uuid = profile.get('uuid')
        if uuid in existing_uuids:
            # Cập nhật profile, giữ lại thông tin local
            local_data = existing_uuids[uuid]
            profile['local_notes'] = local_data.get('local_notes', '')
            profile['local_tags'] = local_data.get('local_tags', [])
            profile['fb_uid'] = local_data.get('fb_uid', '')
            profile['fb_name'] = local_data.get('fb_name', '')
            # Giữ lại trạng thái check_open local (do app quản lý, không phải từ API)
            profile['check_open'] = local_data.get('check_open', 0)
        else:
            # Profile mới, mặc định check_open = 0 (chưa mở)
            profile['check_open'] = 0
        profile['synced_at'] = datetime.now().isoformat()
    
    save_json(PROFILES_FILE, profiles)
    return True


def update_profile_local(uuid: str, data: Dict) -> bool:
    """Cập nhật thông tin local của profile"""
    profiles = get_profiles()
    for i, p in enumerate(profiles):
        if p.get('uuid') == uuid:
            profiles[i].update(data)
            profiles[i]['updated_at'] = datetime.now().isoformat()
            save_json(PROFILES_FILE, profiles)
            return True
    return False


def get_profile_by_uuid(uuid: str) -> Optional[Dict]:
    """Lấy profile theo UUID"""
    profiles = get_profiles()
    for p in profiles:
        if p.get('uuid') == uuid:
            return p
    return None


# ============ SCRIPTS MANAGEMENT ============

def get_scripts() -> List[Dict]:
    """Lấy danh sách scripts"""
    return load_json(SCRIPTS_FILE)


def get_script_by_id(script_id: int) -> Optional[Dict]:
    """Lấy script theo ID"""
    scripts = get_scripts()
    for s in scripts:
        if s.get('id') == script_id:
            return s
    return None


def save_script(script: Dict) -> Dict:
    """Lưu script mới hoặc cập nhật"""
    scripts = get_scripts()
    
    if script.get('id'):
        # Cập nhật script existing
        for i, s in enumerate(scripts):
            if s['id'] == script['id']:
                script['updated_at'] = datetime.now().isoformat()
                scripts[i] = script
                break
    else:
        # Tạo script mới
        script['id'] = max([s.get('id', 0) for s in scripts], default=0) + 1
        script['created_at'] = datetime.now().isoformat()
        script['updated_at'] = datetime.now().isoformat()
        scripts.append(script)
    
    save_json(SCRIPTS_FILE, scripts)
    return script


def delete_script(script_id: int) -> bool:
    """Xóa script"""
    scripts = get_scripts()
    scripts = [s for s in scripts if s.get('id') != script_id]
    save_json(SCRIPTS_FILE, scripts)
    return True


# ============ POSTS MANAGEMENT ============

def get_posts() -> List[Dict]:
    """Lấy danh sách bài đăng"""
    return load_json(POSTS_FILE)


def get_post_by_id(post_id: int) -> Optional[Dict]:
    """Lấy bài đăng theo ID"""
    posts = get_posts()
    for p in posts:
        if p.get('id') == post_id:
            return p
    return None


def save_post(post: Dict) -> Dict:
    """Lưu bài đăng mới hoặc cập nhật"""
    posts = get_posts()
    
    if post.get('id'):
        for i, p in enumerate(posts):
            if p['id'] == post['id']:
                post['updated_at'] = datetime.now().isoformat()
                posts[i] = post
                break
    else:
        post['id'] = max([p.get('id', 0) for p in posts], default=0) + 1
        post['created_at'] = datetime.now().isoformat()
        post['updated_at'] = datetime.now().isoformat()
        post['like_count'] = 0
        post['comment_count'] = 0
        post['interactions'] = []  # Lưu lịch sử tương tác
        posts.append(post)
    
    save_json(POSTS_FILE, posts)
    return post


def delete_post(post_id: int) -> bool:
    """Xóa bài đăng"""
    posts = get_posts()
    posts = [p for p in posts if p.get('id') != post_id]
    save_json(POSTS_FILE, posts)
    return True


def add_post_interaction(post_id: int, interaction: Dict):
    """Thêm tương tác vào bài đăng"""
    posts = get_posts()
    for post in posts:
        if post['id'] == post_id:
            if 'interactions' not in post:
                post['interactions'] = []
            interaction['timestamp'] = datetime.now().isoformat()
            post['interactions'].append(interaction)
            if interaction.get('type') == 'like':
                post['like_count'] = post.get('like_count', 0) + 1
            elif interaction.get('type') == 'comment':
                post['comment_count'] = post.get('comment_count', 0) + 1
            post['updated_at'] = datetime.now().isoformat()
            break
    save_json(POSTS_FILE, posts)


def update_post_stats(post_id: int, likes: int = 0, comments: int = 0):
    """Cập nhật thống kê bài đăng"""
    posts = get_posts()
    for post in posts:
        if post['id'] == post_id:
            post['like_count'] = post.get('like_count', 0) + likes
            post['comment_count'] = post.get('comment_count', 0) + comments
            post['updated_at'] = datetime.now().isoformat()
            break
    save_json(POSTS_FILE, posts)


# ============ CAMPAIGNS MANAGEMENT ============

def get_campaigns() -> List[Dict]:
    """Lấy danh sách campaigns local"""
    return load_json(CAMPAIGNS_FILE)


def save_campaign(campaign: Dict) -> Dict:
    """Lưu campaign"""
    campaigns = get_campaigns()
    
    if campaign.get('id'):
        for i, c in enumerate(campaigns):
            if c['id'] == campaign['id']:
                campaign['updated_at'] = datetime.now().isoformat()
                campaigns[i] = campaign
                break
    else:
        campaign['id'] = max([c.get('id', 0) for c in campaigns], default=0) + 1
        campaign['created_at'] = datetime.now().isoformat()
        campaign['updated_at'] = datetime.now().isoformat()
        campaigns.append(campaign)
    
    save_json(CAMPAIGNS_FILE, campaigns)
    return campaign


def delete_campaign(campaign_id: int) -> bool:
    """Xóa campaign"""
    campaigns = get_campaigns()
    campaigns = [c for c in campaigns if c.get('id') != campaign_id]
    save_json(CAMPAIGNS_FILE, campaigns)
    return True


# ============ SETTINGS ============

def get_settings() -> Dict:
    """Lấy settings"""
    data = load_json(SETTINGS_FILE)
    if isinstance(data, list):
        return {}
    return data


def save_settings(settings: Dict):
    """Lưu settings"""
    save_json(SETTINGS_FILE, settings)


def get_setting(key: str, default=None):
    """Lấy một setting cụ thể"""
    settings = get_settings()
    return settings.get(key, default)


def set_setting(key: str, value):
    """Lưu một setting cụ thể"""
    settings = get_settings()
    settings[key] = value
    save_settings(settings)
