"""
Tab Soạn tin - Quản lý nội dung bài đăng với categories, macros, hình ảnh
"""
import customtkinter as ctk
from tkinter import filedialog
from typing import List, Dict, Optional
import os
import re
import random
from datetime import datetime
from config import COLORS
from widgets import ModernButton, ModernEntry, ModernTextbox
from database import (
    get_categories, save_category, delete_category,
    get_contents, get_content_by_id, save_content, delete_content
)


class ContentTab(ctk.CTkFrame):
    """Tab soạn tin - Quản lý nội dung bài đăng"""

    def __init__(self, master, status_callback=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.status_callback = status_callback
        self.categories: List[Dict] = []
        self.contents: List[Dict] = []
        self.current_category_id: int = 1  # Mặc định
        self.current_content: Optional[Dict] = None
        self.selected_items: List[int] = []

        self._create_ui()
        self._load_data()

    def _create_ui(self):
        """Tạo giao diện"""
        # Main container - 2 columns
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # ========== LEFT PANEL - Content List ==========
        left_panel = ctk.CTkFrame(main_container, fg_color=COLORS["bg_secondary"], corner_radius=12, width=380)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)

        # Category row
        cat_row = ctk.CTkFrame(left_panel, fg_color="transparent")
        cat_row.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            cat_row,
            text="Chọn mục:",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        ).pack(side="left")

        self.category_var = ctk.StringVar(value="Mặc định")
        self.category_menu = ctk.CTkOptionMenu(
            cat_row,
            variable=self.category_var,
            values=["Mặc định"],
            fg_color=COLORS["bg_card"],
            button_color=COLORS["accent"],
            width=150,
            command=self._on_category_change
        )
        self.category_menu.pack(side="left", padx=5)

        ctk.CTkButton(
            cat_row,
            text="Xóa mục",
            width=70,
            height=28,
            fg_color=COLORS["error"],
            hover_color="#c0392b",
            corner_radius=5,
            command=self._delete_category
        ).pack(side="left", padx=2)

        # Stats row
        stats_row = ctk.CTkFrame(left_panel, fg_color="transparent")
        stats_row.pack(fill="x", padx=10, pady=(0, 5))

        self.count_label = ctk.CTkLabel(
            stats_row,
            text="Count: 0",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["accent"]
        )
        self.count_label.pack(side="left")

        self.checked_label = ctk.CTkLabel(
            stats_row,
            text="Checked: 0",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"]
        )
        self.checked_label.pack(side="left", padx=10)

        self.selected_label = ctk.CTkLabel(
            stats_row,
            text="Selected: 0",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["success"]
        )
        self.selected_label.pack(side="left")

        # Table header
        header_frame = ctk.CTkFrame(left_panel, fg_color=COLORS["bg_card"], corner_radius=5, height=30)
        header_frame.pack(fill="x", padx=10, pady=(5, 0))
        header_frame.pack_propagate(False)

        # Checkbox column
        self.select_all_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            header_frame,
            text="",
            variable=self.select_all_var,
            width=20,
            checkbox_width=18,
            checkbox_height=18,
            fg_color=COLORS["accent"],
            command=self._toggle_select_all
        ).pack(side="left", padx=5)

        ctk.CTkLabel(header_frame, text="ID", width=40, font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
        ctk.CTkLabel(header_frame, text="Tiêu đề", width=100, font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
        ctk.CTkLabel(header_frame, text="Nội dung", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=10)

        # Content list
        self.content_list = ctk.CTkScrollableFrame(left_panel, fg_color="transparent")
        self.content_list.pack(fill="both", expand=True, padx=10, pady=5)

        # Search row
        search_row = ctk.CTkFrame(left_panel, fg_color="transparent")
        search_row.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(search_row, text="Tìm kiếm:", font=ctk.CTkFont(size=11)).pack(side="left")
        self.search_entry = ModernEntry(search_row, placeholder="Từ khóa", width=200)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<KeyRelease>", self._on_search)

        ctk.CTkButton(
            search_row,
            text="Tìm",
            width=50,
            height=28,
            fg_color=COLORS["accent"],
            corner_radius=5,
            command=self._on_search
        ).pack(side="left")

        # ========== RIGHT PANEL - Editor ==========
        right_panel = ctk.CTkFrame(main_container, fg_color=COLORS["bg_secondary"], corner_radius=12)
        right_panel.pack(side="right", fill="both", expand=True)

        # New category row
        new_cat_row = ctk.CTkFrame(right_panel, fg_color="transparent")
        new_cat_row.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(new_cat_row, text="Tạo mục chứa tin đăng:", font=ctk.CTkFont(size=12)).pack(side="left")
        self.new_cat_entry = ModernEntry(new_cat_row, placeholder="Tên mục mới", width=200)
        self.new_cat_entry.pack(side="left", padx=10)

        ctk.CTkButton(
            new_cat_row,
            text="Thêm mục",
            width=90,
            height=30,
            fg_color=COLORS["accent"],
            corner_radius=5,
            command=self._add_category
        ).pack(side="left")

        # Import/Export buttons
        ctk.CTkButton(
            new_cat_row,
            text="Nạp <<",
            width=70,
            height=30,
            fg_color=COLORS["success"],
            corner_radius=5,
            command=self._import_contents
        ).pack(side="right", padx=2)

        ctk.CTkButton(
            new_cat_row,
            text="Xuất >>",
            width=70,
            height=30,
            fg_color=COLORS["accent"],
            corner_radius=5,
            command=self._export_contents
        ).pack(side="right", padx=2)

        # Editor section
        editor_section = ctk.CTkFrame(right_panel, fg_color=COLORS["bg_card"], corner_radius=10)
        editor_section.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        # Title
        ctk.CTkLabel(
            editor_section,
            text="Tạo Tin",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=15, pady=(10, 5))

        # Warning message
        ctk.CTkLabel(
            editor_section,
            text="Thông báo: Chúng tôi không chịu trách nhiệm với nội dung đăng tải lên mạng của người dùng.",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["warning"]
        ).pack(anchor="w", padx=15, pady=(0, 10))

        # Title input
        title_row = ctk.CTkFrame(editor_section, fg_color="transparent")
        title_row.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(title_row, text="Tiêu đề:", width=80, anchor="w").pack(side="left")
        self.title_entry = ModernEntry(title_row, placeholder="Nhập tiêu đề bài viết")
        self.title_entry.pack(side="left", fill="x", expand=True)

        # Content label
        ctk.CTkLabel(
            editor_section,
            text="Nội dung:",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=15, pady=(10, 5))

        # Content editor with line numbers
        editor_container = ctk.CTkFrame(editor_section, fg_color=COLORS["bg_dark"], corner_radius=8)
        editor_container.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        # Line numbers
        self.line_numbers = ctk.CTkTextbox(
            editor_container,
            width=35,
            fg_color=COLORS["bg_secondary"],
            text_color=COLORS["text_secondary"],
            font=ctk.CTkFont(family="Consolas", size=12),
            activate_scrollbars=False
        )
        self.line_numbers.pack(side="left", fill="y", padx=(2, 0), pady=2)
        self.line_numbers.configure(state="disabled")

        # Main editor
        self.content_editor = ctk.CTkTextbox(
            editor_container,
            fg_color=COLORS["bg_card"],
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.content_editor.pack(side="left", fill="both", expand=True, padx=(0, 2), pady=2)
        self.content_editor.bind("<KeyRelease>", self._update_line_numbers)
        self.content_editor.bind("<MouseWheel>", self._sync_scroll)

        # Initialize line numbers
        self._update_line_numbers()

        # Hint text
        hint_frame = ctk.CTkFrame(editor_section, fg_color="transparent")
        hint_frame.pack(fill="x", padx=15, pady=(0, 5))

        ctk.CTkLabel(
            hint_frame,
            text="Gợi ý: Thêm {r} hoặc {rrr} đầu nội dung để đăng tin ngẫu nhiên.",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["warning"]
        ).pack(anchor="w")

        # Macro help link
        macro_link = ctk.CTkLabel(
            hint_frame,
            text="Hướng dẫn chèn Macro không giới hạn.",
            font=ctk.CTkFont(size=10, underline=True),
            text_color=COLORS["accent"],
            cursor="hand2"
        )
        macro_link.pack(anchor="w")
        macro_link.bind("<Button-1>", lambda e: self._show_macro_help())

        # Image attachment
        img_row = ctk.CTkFrame(editor_section, fg_color="transparent")
        img_row.pack(fill="x", padx=15, pady=5)

        self.img_check_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            img_row,
            text="Đính kèm hình ảnh",
            variable=self.img_check_var,
            fg_color=COLORS["accent"],
            command=self._toggle_image
        ).pack(side="left")

        self.img_path_entry = ModernEntry(img_row, placeholder="Đường dẫn hình ảnh...", width=300)
        self.img_path_entry.pack(side="left", padx=10)
        self.img_path_entry.configure(state="disabled")

        ctk.CTkButton(
            img_row,
            text="Chọn ảnh",
            width=80,
            height=28,
            fg_color=COLORS["accent"],
            corner_radius=5,
            command=self._select_image
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            img_row,
            text="Xem ảnh",
            width=70,
            height=28,
            fg_color=COLORS["bg_card"],
            corner_radius=5,
            command=self._preview_image
        ).pack(side="left", padx=2)

        # Sticker attachment
        sticker_row = ctk.CTkFrame(editor_section, fg_color="transparent")
        sticker_row.pack(fill="x", padx=15, pady=5)

        self.sticker_check_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            sticker_row,
            text="Đính kèm Sticker",
            variable=self.sticker_check_var,
            fg_color=COLORS["accent"]
        ).pack(side="left")

        self.sticker_entry = ModernEntry(sticker_row, placeholder="Sticker ID; Sticker ID; ...", width=300)
        self.sticker_entry.pack(side="left", padx=10)

        ctk.CTkButton(
            sticker_row,
            text="Chọn Sticker",
            width=90,
            height=28,
            fg_color=COLORS["accent"],
            corner_radius=5
        ).pack(side="left", padx=2)

        # Action buttons
        btn_row = ctk.CTkFrame(editor_section, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=15)

        ModernButton(
            btn_row,
            text="Lưu",
            icon="💾",
            variant="primary",
            command=self._save_content,
            width=100
        ).pack(side="left", padx=5)

        ModernButton(
            btn_row,
            text="Sửa",
            icon="✏️",
            variant="secondary",
            command=self._edit_selected,
            width=100
        ).pack(side="left", padx=5)

        ModernButton(
            btn_row,
            text="Xóa",
            icon="🗑️",
            variant="danger",
            command=self._delete_content,
            width=100
        ).pack(side="left", padx=5)

        ModernButton(
            btn_row,
            text="Mới",
            icon="➕",
            variant="success",
            command=self._new_content,
            width=100
        ).pack(side="left", padx=5)

    # ==================== DATA LOADING ====================

    def _load_data(self):
        """Load categories và contents"""
        self._load_categories()
        self._load_contents()

    def _load_categories(self):
        """Load danh sách categories"""
        self.categories = get_categories()
        cat_names = [c.get('name', 'Unknown') for c in self.categories]
        self.category_menu.configure(values=cat_names)

        # Set current category
        for cat in self.categories:
            if cat['id'] == self.current_category_id:
                self.category_var.set(cat['name'])
                break

    def _load_contents(self):
        """Load nội dung theo category hiện tại"""
        self.contents = get_contents(self.current_category_id)
        self._render_content_list()

    def _render_content_list(self, contents: List[Dict] = None):
        """Render danh sách nội dung"""
        # Clear existing
        for widget in self.content_list.winfo_children():
            widget.destroy()

        display_contents = contents if contents is not None else self.contents

        # Update stats
        self.count_label.configure(text=f"Count: {len(display_contents)}")
        self.checked_label.configure(text=f"Checked: {len(self.selected_items)}")
        self.selected_label.configure(text=f"Selected: {1 if self.current_content else 0}")

        if not display_contents:
            ctk.CTkLabel(
                self.content_list,
                text="Chưa có nội dung nào\nBấm 'Mới' để tạo",
                font=ctk.CTkFont(size=12),
                text_color=COLORS["text_secondary"]
            ).pack(pady=30)
            return

        for content in display_contents:
            self._create_content_row(content)

    def _create_content_row(self, content: Dict):
        """Tạo row cho content trong list"""
        row = ctk.CTkFrame(self.content_list, fg_color=COLORS["bg_card"], corner_radius=5, height=35)
        row.pack(fill="x", pady=2)
        row.pack_propagate(False)

        # Checkbox
        var = ctk.BooleanVar(value=content['id'] in self.selected_items)
        cb = ctk.CTkCheckBox(
            row,
            text="",
            variable=var,
            width=20,
            checkbox_width=16,
            checkbox_height=16,
            fg_color=COLORS["accent"],
            command=lambda cid=content['id'], v=var: self._toggle_item(cid, v)
        )
        cb.pack(side="left", padx=5)

        # ID
        ctk.CTkLabel(
            row,
            text=str(content.get('id', '')),
            width=40,
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"]
        ).pack(side="left")

        # Title
        title = content.get('title', '')[:15]
        ctk.CTkLabel(
            row,
            text=title,
            width=100,
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_primary"],
            anchor="w"
        ).pack(side="left")

        # Content preview
        text = content.get('content', '')[:30].replace('\n', ' ')
        ctk.CTkLabel(
            row,
            text=text,
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"],
            anchor="w"
        ).pack(side="left", padx=5, fill="x", expand=True)

        # Click to select
        row.bind("<Button-1>", lambda e, c=content: self._select_content(c))
        for child in row.winfo_children():
            if not isinstance(child, ctk.CTkCheckBox):
                child.bind("<Button-1>", lambda e, c=content: self._select_content(c))

    # ==================== CATEGORY MANAGEMENT ====================

    def _on_category_change(self, choice: str):
        """Khi chọn category khác"""
        for cat in self.categories:
            if cat['name'] == choice:
                self.current_category_id = cat['id']
                break
        self._load_contents()

    def _add_category(self):
        """Thêm category mới"""
        name = self.new_cat_entry.get().strip()
        if not name:
            self._set_status("Vui lòng nhập tên mục!", "warning")
            return

        cat = save_category({'name': name})
        self.new_cat_entry.delete(0, "end")

        # Chuyển sang category mới vừa tạo
        self.current_category_id = cat['id']
        self._load_categories()
        self.category_var.set(name)  # Update dropdown để hiển thị category mới
        self._load_contents()  # Load contents của category mới (sẽ trống)
        self._new_content()  # Reset form
        self._set_status(f"Đã tạo mục: {name}", "success")

    def _delete_category(self):
        """Xóa category hiện tại"""
        if self.current_category_id == 1:
            self._set_status("Không thể xóa mục Mặc định!", "warning")
            return

        delete_category(self.current_category_id)
        self.current_category_id = 1
        self._load_categories()
        self._load_contents()
        self._set_status("Đã xóa mục", "success")

    # ==================== CONTENT MANAGEMENT ====================

    def _select_content(self, content: Dict):
        """Chọn content để edit"""
        self.current_content = content

        # Fill editor
        self.title_entry.delete(0, "end")
        self.title_entry.insert(0, content.get('title', ''))

        self.content_editor.delete("1.0", "end")
        self.content_editor.insert("1.0", content.get('content', ''))

        # Image
        img_path = content.get('image_path', '')
        if img_path:
            self.img_check_var.set(True)
            self.img_path_entry.configure(state="normal")
            self.img_path_entry.delete(0, "end")
            self.img_path_entry.insert(0, img_path)
        else:
            self.img_check_var.set(False)
            self.img_path_entry.configure(state="disabled")

        # Sticker
        stickers = content.get('stickers', '')
        if stickers:
            self.sticker_check_var.set(True)
            self.sticker_entry.delete(0, "end")
            self.sticker_entry.insert(0, stickers)

        self._update_line_numbers()
        self._render_content_list()
        self._set_status(f"Đã chọn: {content.get('title', 'Untitled')}", "info")

    def _new_content(self):
        """Tạo content mới - Reset form về trạng thái ban đầu"""
        self.current_content = None
        self.title_entry.delete(0, "end")
        self.content_editor.delete("1.0", "end")

        # Reset image
        self.img_check_var.set(False)
        self.img_path_entry.configure(state="normal")  # Enable trước khi xóa
        self.img_path_entry.delete(0, "end")
        self.img_path_entry.configure(state="disabled")  # Disable lại

        # Reset sticker
        self.sticker_check_var.set(False)
        self.sticker_entry.delete(0, "end")

        self._update_line_numbers()
        self._render_content_list()

    def _save_content(self):
        """Lưu content"""
        title = self.title_entry.get().strip()
        content_text = self.content_editor.get("1.0", "end").strip()

        if not title:
            self._set_status("Vui lòng nhập tiêu đề!", "warning")
            return

        content_data = {
            'title': title,
            'content': content_text,
            'category_id': self.current_category_id,
            'image_path': self.img_path_entry.get() if self.img_check_var.get() else '',
            'stickers': self.sticker_entry.get() if self.sticker_check_var.get() else ''
        }

        # Nếu đang edit content cũ thì giữ ID, ngược lại tạo mới
        if self.current_content:
            content_data['id'] = self.current_content['id']

        saved = save_content(content_data)
        self._load_contents()  # Reload danh sách
        self._new_content()  # Reset form sau khi lưu
        self._set_status(f"Đã lưu: {title}", "success")

    def _edit_selected(self):
        """Edit content được chọn trong list"""
        if self.selected_items:
            content = get_content_by_id(self.selected_items[0])
            if content:
                self._select_content(content)

    def _delete_content(self):
        """Xóa content"""
        if self.current_content:
            delete_content(self.current_content['id'])
            self._new_content()
            self._load_contents()
            self._set_status("Đã xóa nội dung", "success")
        elif self.selected_items:
            for item_id in self.selected_items:
                delete_content(item_id)
            self.selected_items = []
            self._load_contents()
            self._set_status(f"Đã xóa {len(self.selected_items)} nội dung", "success")

    # ==================== SELECTION ====================

    def _toggle_item(self, content_id: int, var: ctk.BooleanVar):
        """Toggle chọn item"""
        if var.get():
            if content_id not in self.selected_items:
                self.selected_items.append(content_id)
        else:
            if content_id in self.selected_items:
                self.selected_items.remove(content_id)
        self._update_stats()

    def _toggle_select_all(self):
        """Toggle chọn tất cả"""
        if self.select_all_var.get():
            self.selected_items = [c['id'] for c in self.contents]
        else:
            self.selected_items = []
        self._render_content_list()

    def _update_stats(self):
        """Cập nhật thống kê"""
        self.checked_label.configure(text=f"Checked: {len(self.selected_items)}")
        self.selected_label.configure(text=f"Selected: {1 if self.current_content else 0}")

    # ==================== EDITOR HELPERS ====================

    def _update_line_numbers(self, event=None):
        """Cập nhật số dòng"""
        content = self.content_editor.get("1.0", "end")
        lines = content.count('\n')
        if lines == 0:
            lines = 1

        line_nums = "\n".join(str(i) for i in range(1, lines + 1))

        self.line_numbers.configure(state="normal")
        self.line_numbers.delete("1.0", "end")
        self.line_numbers.insert("1.0", line_nums)
        self.line_numbers.configure(state="disabled")

    def _sync_scroll(self, event):
        """Đồng bộ scroll giữa line numbers và editor"""
        self.line_numbers.yview_moveto(self.content_editor.yview()[0])

    # ==================== IMAGE ====================

    def _toggle_image(self):
        """Toggle đính kèm hình ảnh"""
        if self.img_check_var.get():
            self.img_path_entry.configure(state="normal")
        else:
            self.img_path_entry.configure(state="disabled")

    def _select_image(self):
        """Chọn file hình ảnh"""
        if not self.img_check_var.get():
            self.img_check_var.set(True)
            self.img_path_entry.configure(state="normal")

        filetypes = [
            ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
            ("All files", "*.*")
        ]
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            self.img_path_entry.delete(0, "end")
            self.img_path_entry.insert(0, path)

    def _preview_image(self):
        """Xem trước hình ảnh"""
        path = self.img_path_entry.get()
        if path and os.path.exists(path):
            os.startfile(path) if os.name == 'nt' else os.system(f'xdg-open "{path}"')

    # ==================== IMPORT/EXPORT ====================

    def _import_contents(self):
        """Nạp nội dung từ file"""
        filetypes = [("Text files", "*.txt"), ("All files", "*.*")]
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                count = 0
                for line in lines:
                    line = line.strip()
                    if line:
                        save_content({
                            'title': f"Imported {count + 1}",
                            'content': line,
                            'category_id': self.current_category_id
                        })
                        count += 1

                self._load_contents()
                self._set_status(f"Đã nạp {count} nội dung", "success")
            except Exception as e:
                self._set_status(f"Lỗi: {e}", "error")

    def _export_contents(self):
        """Xuất nội dung ra file"""
        if not self.contents:
            self._set_status("Không có nội dung để xuất!", "warning")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")]
        )
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    for c in self.contents:
                        f.write(f"{c.get('title', '')}\n")
                        f.write(f"{c.get('content', '')}\n")
                        f.write("-" * 50 + "\n")
                self._set_status(f"Đã xuất {len(self.contents)} nội dung", "success")
            except Exception as e:
                self._set_status(f"Lỗi: {e}", "error")

    # ==================== SEARCH ====================

    def _on_search(self, event=None):
        """Tìm kiếm nội dung"""
        query = self.search_entry.get().lower()
        if not query:
            self._render_content_list()
            return

        filtered = [
            c for c in self.contents
            if query in c.get('title', '').lower()
            or query in c.get('content', '').lower()
        ]
        self._render_content_list(filtered)

    # ==================== MACRO HELP ====================

    def _show_macro_help(self):
        """Hiển thị hướng dẫn macro"""
        help_text = """
HƯỚNG DẪN SỬ DỤNG MACRO

1. {r} - Random chọn 1 dòng từ nội dung
   Ví dụ:
   {r}
   Xin chào!
   Hello!
   Hi there!
   → Sẽ random chọn 1 trong 3 dòng

2. {rrr} - Random tất cả các dòng
   Tương tự {r} nhưng shuffle tất cả

3. {name} - Thay thế biến
   Định nghĩa biến khi chạy script

4. {time} - Thời gian hiện tại
5. {date} - Ngày hiện tại

Mẹo: Kết hợp nhiều macro trong 1 bài viết
để tạo nội dung đa dạng!
"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Hướng dẫn Macro")
        dialog.geometry("450x400")
        dialog.configure(fg_color=COLORS["bg_dark"])

        text = ctk.CTkTextbox(dialog, fg_color=COLORS["bg_card"])
        text.pack(fill="both", expand=True, padx=20, pady=20)
        text.insert("1.0", help_text)
        text.configure(state="disabled")

    def _set_status(self, text: str, status_type: str = "info"):
        """Cập nhật status bar"""
        if self.status_callback:
            self.status_callback(text, status_type)

    # ==================== MACRO PROCESSING ====================

    def process_macros(self, content: str) -> str:
        """Xử lý macros trong nội dung"""
        # {r} - random 1 dòng
        if content.startswith('{r}'):
            lines = content[3:].strip().split('\n')
            lines = [l.strip() for l in lines if l.strip()]
            if lines:
                return random.choice(lines)

        # {rrr} - shuffle all
        if content.startswith('{rrr}'):
            lines = content[5:].strip().split('\n')
            lines = [l.strip() for l in lines if l.strip()]
            random.shuffle(lines)
            return '\n'.join(lines)

        # {time} - current time
        content = content.replace('{time}', datetime.now().strftime('%H:%M:%S'))

        # {date} - current date
        content = content.replace('{date}', datetime.now().strftime('%d/%m/%Y'))

        return content
