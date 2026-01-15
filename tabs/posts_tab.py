"""
Tab Bài đăng - Quản lý các bài đăng và tương tác
"""
import customtkinter as ctk
from typing import List, Dict
import webbrowser
from config import COLORS
from widgets import ModernCard, ModernButton, ModernEntry, ModernTextbox, PostCard, SearchBar
from db import get_posts, save_post, delete_post, update_post_stats


class PostsTab(ctk.CTkFrame):
    """Tab quản lý bài đăng và tương tác"""
    
    def __init__(self, master, status_callback=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.status_callback = status_callback
        self.posts: List[Dict] = []
        
        self._create_ui()
        self._load_posts()
    
    def _create_ui(self):
        # ========== HEADER ==========
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 15))
        
        ctk.CTkLabel(
            header_frame,
            text="📰 Quản lý Bài đăng",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left")
        
        ModernButton(
            header_frame,
            text="Làm mới",
            icon="🔄",
            variant="secondary",
            command=self._load_posts,
            width=120
        ).pack(side="right", padx=5)
        
        # ========== ADD POST SECTION ==========
        add_section = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_secondary"],
            corner_radius=15
        )
        add_section.pack(fill="x", padx=20, pady=(0, 15))
        
        # Section header
        ctk.CTkLabel(
            add_section,
            text="➕ Thêm bài đăng mới",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=20, pady=(15, 10))
        
        # Input fields
        input_frame = ctk.CTkFrame(add_section, fg_color="transparent")
        input_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        # URL input
        url_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        url_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            url_frame,
            text="URL bài viết:",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_secondary"],
            width=100
        ).pack(side="left")
        
        self.url_entry = ModernEntry(
            url_frame,
            placeholder="https://facebook.com/post/123456789"
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        # Title input
        title_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            title_frame,
            text="Tiêu đề:",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_secondary"],
            width=100
        ).pack(side="left")
        
        self.title_entry = ModernEntry(
            title_frame,
            placeholder="Mô tả ngắn về bài viết"
        )
        self.title_entry.pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        # Target interactions
        target_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        target_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            target_frame,
            text="Mục tiêu:",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_secondary"],
            width=100
        ).pack(side="left")
        
        self.like_target = ModernEntry(target_frame, placeholder="Số like", width=100)
        self.like_target.pack(side="left", padx=(10, 5))
        
        ctk.CTkLabel(
            target_frame,
            text="Like",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        ).pack(side="left", padx=(0, 20))
        
        self.comment_target = ModernEntry(target_frame, placeholder="Số CMT", width=100)
        self.comment_target.pack(side="left", padx=(0, 5))
        
        ctk.CTkLabel(
            target_frame,
            text="Comment",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        ).pack(side="left")
        
        # Add button
        btn_frame = ctk.CTkFrame(add_section, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ModernButton(
            btn_frame,
            text="Thêm bài đăng",
            icon="➕",
            variant="success",
            command=self._add_post,
            width=150
        ).pack(side="left")
        
        # ========== POSTS LIST ==========
        list_header = ctk.CTkFrame(self, fg_color="transparent")
        list_header.pack(fill="x", padx=20, pady=(10, 10))
        
        ctk.CTkLabel(
            list_header,
            text="📋 Danh sách bài đăng",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left")
        
        self.count_label = ctk.CTkLabel(
            list_header,
            text="(0 bài)",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_secondary"]
        )
        self.count_label.pack(side="left", padx=10)
        
        # Search bar
        search_frame = ctk.CTkFrame(list_header, fg_color="transparent")
        search_frame.pack(side="right")
        
        self.search_entry = ModernEntry(
            search_frame,
            placeholder="Tìm kiếm...",
            width=250
        )
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<KeyRelease>", self._on_search)
        
        # Sort options
        self.sort_var = ctk.StringVar(value="newest")
        sort_menu = ctk.CTkOptionMenu(
            search_frame,
            variable=self.sort_var,
            values=["Mới nhất", "Cũ nhất", "Nhiều like nhất", "Nhiều CMT nhất"],
            fg_color=COLORS["bg_card"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            dropdown_fg_color=COLORS["bg_card"],
            dropdown_hover_color=COLORS["border"],
            width=150,
            command=self._on_sort
        )
        sort_menu.pack(side="left", padx=5)
        
        # Posts scroll area
        self.posts_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["accent"]
        )
        self.posts_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Empty state
        self.empty_label = ctk.CTkLabel(
            self.posts_scroll,
            text="📭 Chưa có bài đăng nào\nThêm URL bài viết Facebook ở phần trên để bắt đầu",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text_secondary"],
            justify="center"
        )
    
    def _load_posts(self):
        """Load danh sách bài đăng từ database"""
        self.posts = get_posts()
        self._render_posts()
    
    def _render_posts(self, posts: List[Dict] = None):
        """Render danh sách bài đăng"""
        # Clear existing
        for widget in self.posts_scroll.winfo_children():
            widget.destroy()
        
        display_posts = posts if posts is not None else self.posts
        
        self.count_label.configure(text=f"({len(display_posts)} bài)")
        
        if not display_posts:
            self.empty_label = ctk.CTkLabel(
                self.posts_scroll,
                text="📭 Chưa có bài đăng nào\nThêm URL bài viết Facebook ở phần trên để bắt đầu",
                font=ctk.CTkFont(size=14),
                text_color=COLORS["text_secondary"],
                justify="center"
            )
            self.empty_label.pack(pady=50)
            return
        
        for post in display_posts:
            card = PostCard(
                self.posts_scroll,
                post_data=post,
                on_like=self._like_post,
                on_comment=self._comment_post,
                on_delete=self._delete_post
            )
            card.pack(fill="x", pady=5)
    
    def _add_post(self):
        """Thêm bài đăng mới"""
        url = self.url_entry.get().strip()
        title = self.title_entry.get().strip()
        
        if not url:
            self._set_status("Vui lòng nhập URL bài viết", "warning")
            return
        
        # Validate URL (basic)
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        post_data = {
            'url': url,
            'title': title or 'Bài viết Facebook',
            'target_likes': int(self.like_target.get() or 0),
            'target_comments': int(self.comment_target.get() or 0)
        }
        
        saved = save_post(post_data)
        
        # Clear inputs
        self.url_entry.delete(0, "end")
        self.title_entry.delete(0, "end")
        self.like_target.delete(0, "end")
        self.comment_target.delete(0, "end")
        
        self._load_posts()
        self._set_status(f"Đã thêm bài đăng: {title or url}", "success")
    
    def _like_post(self, post: Dict):
        """Mở dialog like bài đăng"""
        dialog = LikeDialog(self, post, self.status_callback)
        dialog.grab_set()
    
    def _comment_post(self, post: Dict):
        """Mở dialog comment bài đăng"""
        dialog = CommentDialog(self, post, self.status_callback)
        dialog.grab_set()
    
    def _delete_post(self, post: Dict):
        """Xóa bài đăng"""
        post_id = post.get('id')
        if post_id:
            delete_post(post_id)
            self._load_posts()
            self._set_status("Đã xóa bài đăng", "success")
    
    def _on_search(self, event=None):
        """Tìm kiếm bài đăng"""
        query = self.search_entry.get().lower()
        if not query:
            self._render_posts()
            return
        
        filtered = [
            p for p in self.posts
            if query in p.get('url', '').lower()
            or query in p.get('title', '').lower()
        ]
        self._render_posts(filtered)
    
    def _on_sort(self, choice: str):
        """Sắp xếp bài đăng"""
        posts = self.posts.copy()
        
        if choice == "Mới nhất":
            posts.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        elif choice == "Cũ nhất":
            posts.sort(key=lambda x: x.get('created_at', ''))
        elif choice == "Nhiều like nhất":
            posts.sort(key=lambda x: x.get('like_count', 0), reverse=True)
        elif choice == "Nhiều CMT nhất":
            posts.sort(key=lambda x: x.get('comment_count', 0), reverse=True)
        
        self._render_posts(posts)
    
    def _set_status(self, text: str, status_type: str = "info"):
        """Cập nhật status bar"""
        if self.status_callback:
            self.status_callback(text, status_type)


class LikeDialog(ctk.CTkToplevel):
    """Dialog cấu hình like bài đăng"""
    
    def __init__(self, parent, post: Dict, status_callback=None):
        super().__init__(parent)
        
        self.post = post
        self.status_callback = status_callback
        
        self.title("❤️ Like bài đăng")
        self.geometry("550x450")
        self.configure(fg_color=COLORS["bg_dark"])
        self.transient(parent)
        
        self._create_ui()
    
    def _create_ui(self):
        # Header
        ctk.CTkLabel(
            self,
            text="❤️ Cấu hình Like bài đăng",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(pady=20)
        
        # Post info
        info_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=12)
        info_frame.pack(fill="x", padx=30, pady=10)
        
        url = self.post.get('url', '')[:50]
        ctk.CTkLabel(
            info_frame,
            text=f"🔗 {url}...",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["accent"]
        ).pack(anchor="w", padx=15, pady=10)
        
        # Config form
        form_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=12)
        form_frame.pack(fill="x", padx=30, pady=10)
        
        # Number of likes
        ctk.CTkLabel(
            form_frame,
            text="Số lượng like:",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=20, pady=(15, 5))
        
        self.like_count = ModernEntry(form_frame, placeholder="VD: 10", width=200)
        self.like_count.pack(anchor="w", padx=20, pady=(0, 15))
        self.like_count.insert(0, "10")
        
        # Delay between likes
        ctk.CTkLabel(
            form_frame,
            text="Thời gian chờ giữa mỗi like (giây):",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=20, pady=(0, 5))
        
        self.delay_entry = ModernEntry(form_frame, placeholder="VD: 5", width=200)
        self.delay_entry.pack(anchor="w", padx=20, pady=(0, 15))
        self.delay_entry.insert(0, "5")
        
        # Select profiles
        ctk.CTkLabel(
            form_frame,
            text="Chọn profiles để sử dụng:",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=20, pady=(0, 5))
        
        self.profile_option = ctk.CTkOptionMenu(
            form_frame,
            values=["Tất cả profiles", "Profiles đang chạy", "Chọn thủ công"],
            fg_color=COLORS["bg_card"],
            button_color=COLORS["accent"],
            width=300
        )
        self.profile_option.pack(anchor="w", padx=20, pady=(0, 20))
        
        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=20)
        
        ModernButton(
            btn_frame,
            text="Bắt đầu Like",
            icon="▶",
            variant="success",
            command=self._start_like,
            width=140
        ).pack(side="left", padx=5)
        
        ModernButton(
            btn_frame,
            text="Hủy",
            variant="secondary",
            command=self.destroy,
            width=100
        ).pack(side="left", padx=5)
    
    def _start_like(self):
        """Bắt đầu quá trình like"""
        count = int(self.like_count.get() or 10)
        delay = int(self.delay_entry.get() or 5)
        
        if self.status_callback:
            self.status_callback(f"Đang thực hiện {count} likes với delay {delay}s...", "info")
        
        # Update post stats (simulation)
        update_post_stats(self.post['id'], likes=count)
        
        self.destroy()


class CommentDialog(ctk.CTkToplevel):
    """Dialog cấu hình comment bài đăng"""
    
    def __init__(self, parent, post: Dict, status_callback=None):
        super().__init__(parent)
        
        self.post = post
        self.status_callback = status_callback
        
        self.title("💬 Comment bài đăng")
        self.geometry("600x550")
        self.configure(fg_color=COLORS["bg_dark"])
        self.transient(parent)
        
        self._create_ui()
    
    def _create_ui(self):
        # Header
        ctk.CTkLabel(
            self,
            text="💬 Cấu hình Comment bài đăng",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(pady=20)
        
        # Post info
        info_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=12)
        info_frame.pack(fill="x", padx=30, pady=10)
        
        url = self.post.get('url', '')[:50]
        ctk.CTkLabel(
            info_frame,
            text=f"🔗 {url}...",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["accent"]
        ).pack(anchor="w", padx=15, pady=10)
        
        # Comment templates
        form_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=12)
        form_frame.pack(fill="x", padx=30, pady=10)
        
        ctk.CTkLabel(
            form_frame,
            text="Danh sách comment (mỗi dòng 1 comment):",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=20, pady=(15, 5))
        
        self.comments_text = ModernTextbox(form_frame, height=150)
        self.comments_text.pack(fill="x", padx=20, pady=(0, 15))
        self.comments_text.insert("1.0", "Bài viết hay quá! 👍\nThanks for sharing!\nRất hữu ích ❤️\n🔥🔥🔥")
        
        # Config
        config_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        config_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(
            config_frame,
            text="Số comment:",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        ).pack(side="left")
        
        self.comment_count = ModernEntry(config_frame, width=80)
        self.comment_count.pack(side="left", padx=(5, 20))
        self.comment_count.insert(0, "5")
        
        ctk.CTkLabel(
            config_frame,
            text="Delay (giây):",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        ).pack(side="left")
        
        self.delay_entry = ModernEntry(config_frame, width=80)
        self.delay_entry.pack(side="left", padx=5)
        self.delay_entry.insert(0, "10")
        
        # Random option
        self.random_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            form_frame,
            text="Random thứ tự comment",
            variable=self.random_var,
            fg_color=COLORS["accent"]
        ).pack(anchor="w", padx=20, pady=(0, 15))
        
        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=20)
        
        ModernButton(
            btn_frame,
            text="Bắt đầu Comment",
            icon="▶",
            variant="success",
            command=self._start_comment,
            width=160
        ).pack(side="left", padx=5)
        
        ModernButton(
            btn_frame,
            text="Hủy",
            variant="secondary",
            command=self.destroy,
            width=100
        ).pack(side="left", padx=5)
    
    def _start_comment(self):
        """Bắt đầu quá trình comment"""
        count = int(self.comment_count.get() or 5)
        delay = int(self.delay_entry.get() or 10)
        
        if self.status_callback:
            self.status_callback(f"Đang thực hiện {count} comments với delay {delay}s...", "info")
        
        # Update post stats (simulation)
        update_post_stats(self.post['id'], comments=count)
        
        self.destroy()
