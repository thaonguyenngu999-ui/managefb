"""
Content Tab - Modern Content Management Interface
Premium design with category system and rich content editor
"""
import customtkinter as ctk
from tkinter import filedialog
from typing import List, Dict, Optional
import os
import random
from datetime import datetime
from config import COLORS, FONTS, SPACING, RADIUS, TAB_COLORS
from widgets import ModernButton, ModernEntry, ModernTextbox, SearchBar, Badge, EmptyState
from cyber_widgets import CyberTitle, CyberButton
from db import (
    get_categories, save_category, delete_category,
    get_contents, get_content_by_id, save_content, delete_content
)


class ContentTab(ctk.CTkFrame):
    """Premium Content Management Tab"""

    def __init__(self, master, status_callback=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.status_callback = status_callback
        self.categories: List[Dict] = []
        self.contents: List[Dict] = []
        self.current_category_id: int = 1
        self.current_content: Optional[Dict] = None
        self.selected_items: List[int] = []
        self.content_frames: Dict[int, ctk.CTkFrame] = {}
        self.content_checkboxes: Dict[int, ctk.BooleanVar] = {}

        self._create_ui()
        self._load_data()

    def _create_ui(self):
        """Create premium UI"""
        # ========== HEADER SECTION ==========
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=SPACING["2xl"], pady=(SPACING["2xl"], SPACING["lg"]))

        # CyberTitle
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left")

        self.cyber_title = CyberTitle(
            title_frame,
            title="CONTENT",
            subtitle="Soan va quan ly noi dung dang bai",
            tab_id="content"
        )
        self.cyber_title.pack(anchor="w")

        # Action buttons
        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.pack(side="right")

        CyberButton(
            actions,
            text="Nap file",
            icon="↓",
            variant="secondary",
            command=self._import_contents,
            width=100
        ).pack(side="left", padx=SPACING["xs"])

        CyberButton(
            actions,
            text="Xuat file",
            icon="↑",
            variant="secondary",
            command=self._export_contents,
            width=100
        ).pack(side="left", padx=SPACING["xs"])

        # ========== MAIN CONTENT ==========
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=SPACING["2xl"], pady=(0, SPACING["xl"]))

        # Left panel (40%)
        left_panel = ctk.CTkFrame(main_container, fg_color="transparent", width=420)
        left_panel.pack(side="left", fill="both")
        left_panel.pack_propagate(False)

        # Categories section
        self._create_categories_section(left_panel)

        # Content list section
        self._create_content_list_section(left_panel)

        # Right panel (60%)
        right_panel = ctk.CTkFrame(main_container, fg_color="transparent")
        right_panel.pack(side="left", fill="both", expand=True, padx=(SPACING["lg"], 0))

        self._create_editor_section(right_panel)

    def _create_categories_section(self, parent):
        """Create categories panel"""
        cat_card = ctk.CTkFrame(
            parent,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=COLORS["border"]
        )
        cat_card.pack(fill="x", pady=(0, SPACING["md"]))

        cat_inner = ctk.CTkFrame(cat_card, fg_color="transparent")
        cat_inner.pack(fill="x", padx=SPACING["lg"], pady=SPACING["md"])

        # Header
        cat_header = ctk.CTkFrame(cat_inner, fg_color="transparent")
        cat_header.pack(fill="x")

        ctk.CTkLabel(
            cat_header,
            text="  Danh muc",
            font=ctk.CTkFont(size=FONTS["size_md"], weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left")

        # Add new category input
        add_frame = ctk.CTkFrame(cat_inner, fg_color="transparent")
        add_frame.pack(fill="x", pady=(SPACING["sm"], 0))

        self.new_cat_entry = ModernEntry(add_frame, placeholder="Ten danh muc moi...")
        self.new_cat_entry.pack(side="left", fill="x", expand=True)

        ModernButton(
            add_frame,
            text="",
            variant="success",
            size="sm",
            command=self._add_category,
            width=36
        ).pack(side="left", padx=(SPACING["xs"], 0))

        # Category selector row
        cat_select_row = ctk.CTkFrame(cat_inner, fg_color="transparent")
        cat_select_row.pack(fill="x", pady=(SPACING["sm"], 0))

        ctk.CTkLabel(
            cat_select_row,
            text="Chon danh muc:",
            font=ctk.CTkFont(size=FONTS["size_sm"]),
            text_color=COLORS["text_secondary"]
        ).pack(side="left")

        self.category_var = ctk.StringVar(value="Mac dinh")
        self.category_menu = ctk.CTkOptionMenu(
            cat_select_row,
            variable=self.category_var,
            values=["Mac dinh"],
            fg_color=COLORS["bg_secondary"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            width=160,
            command=self._on_category_change
        )
        self.category_menu.pack(side="left", padx=SPACING["sm"])

        ModernButton(
            cat_select_row,
            text="Xoa",
            icon="",
            variant="danger",
            size="sm",
            command=self._delete_category,
            width=70
        ).pack(side="left")

    def _create_content_list_section(self, parent):
        """Create content list panel"""
        list_card = ctk.CTkFrame(
            parent,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=COLORS["border"]
        )
        list_card.pack(fill="both", expand=True)

        list_inner = ctk.CTkFrame(list_card, fg_color="transparent")
        list_inner.pack(fill="both", expand=True, padx=SPACING["lg"], pady=SPACING["md"])

        # Header with stats
        list_header = ctk.CTkFrame(list_inner, fg_color="transparent")
        list_header.pack(fill="x")

        ctk.CTkLabel(
            list_header,
            text="  Danh sach noi dung",
            font=ctk.CTkFont(size=FONTS["size_md"], weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left")

        # Stats
        self.count_label = ctk.CTkLabel(
            list_header,
            text="0 muc",
            font=ctk.CTkFont(size=FONTS["size_sm"]),
            text_color=COLORS["text_tertiary"]
        )
        self.count_label.pack(side="right")

        # Search bar
        self.search_bar = SearchBar(
            list_inner,
            placeholder="Tim kiem...",
            on_search=self._on_search
        )
        self.search_bar.pack(fill="x", pady=SPACING["sm"])

        # Toolbar
        toolbar = ctk.CTkFrame(list_inner, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0, SPACING["sm"]))

        # Select all checkbox
        self.select_all_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            toolbar,
            text="Chon tat ca",
            variable=self.select_all_var,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(size=FONTS["size_sm"]),
            command=self._toggle_select_all
        ).pack(side="left")

        ModernButton(
            toolbar,
            text="Xoa da chon",
            icon="",
            variant="danger",
            size="sm",
            command=self._delete_selected,
            width=110
        ).pack(side="right")

        # Scrollable content list
        self.content_scroll = ctk.CTkScrollableFrame(
            list_inner,
            fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["accent"]
        )
        self.content_scroll.pack(fill="both", expand=True)

    def _create_editor_section(self, parent):
        """Create content editor panel"""
        editor_card = ctk.CTkFrame(
            parent,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=COLORS["border"]
        )
        editor_card.pack(fill="both", expand=True)

        editor_inner = ctk.CTkFrame(editor_card, fg_color="transparent")
        editor_inner.pack(fill="both", expand=True, padx=SPACING["lg"], pady=SPACING["lg"])

        # Header
        editor_header = ctk.CTkFrame(editor_inner, fg_color="transparent")
        editor_header.pack(fill="x")

        ctk.CTkLabel(
            editor_header,
            text="  Trinh soan thao",
            font=ctk.CTkFont(size=FONTS["size_lg"], weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left")

        # Title input
        title_row = ctk.CTkFrame(editor_inner, fg_color="transparent")
        title_row.pack(fill="x", pady=(SPACING["md"], SPACING["xs"]))

        ctk.CTkLabel(
            title_row,
            text="Tieu de",
            font=ctk.CTkFont(size=FONTS["size_sm"]),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w")

        self.title_entry = ModernEntry(title_row, placeholder="Nhap tieu de noi dung...")
        self.title_entry.pack(fill="x", pady=(SPACING["xs"], 0))

        # Content editor
        content_row = ctk.CTkFrame(editor_inner, fg_color="transparent")
        content_row.pack(fill="both", expand=True, pady=SPACING["sm"])

        ctk.CTkLabel(
            content_row,
            text="Noi dung",
            font=ctk.CTkFont(size=FONTS["size_sm"]),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w")

        self.content_editor = ModernTextbox(content_row, height=200)
        self.content_editor.pack(fill="both", expand=True, pady=(SPACING["xs"], 0))

        # Macro buttons
        macro_frame = ctk.CTkFrame(editor_inner, fg_color="transparent")
        macro_frame.pack(fill="x", pady=SPACING["sm"])

        ctk.CTkLabel(
            macro_frame,
            text="Macro:",
            font=ctk.CTkFont(size=FONTS["size_sm"]),
            text_color=COLORS["text_secondary"]
        ).pack(side="left", padx=(0, SPACING["sm"]))

        macros = [
            ("{r}", "Random"),
            ("{time}", "Gio"),
            ("{date}", "Ngay"),
        ]

        for macro, label in macros:
            btn = ctk.CTkButton(
                macro_frame,
                text=label,
                width=60,
                height=28,
                fg_color=COLORS["bg_elevated"],
                hover_color=COLORS["border_hover"],
                text_color=COLORS["text_secondary"],
                corner_radius=RADIUS["sm"],
                font=ctk.CTkFont(size=FONTS["size_xs"]),
                command=lambda m=macro: self._insert_macro(m)
            )
            btn.pack(side="left", padx=2)

        # Image attachment
        img_row = ctk.CTkFrame(editor_inner, fg_color="transparent")
        img_row.pack(fill="x", pady=SPACING["xs"])

        self.img_check_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            img_row,
            text="Dinh kem hinh anh",
            variable=self.img_check_var,
            fg_color=COLORS["accent"],
            font=ctk.CTkFont(size=FONTS["size_sm"]),
            command=self._toggle_image
        ).pack(side="left")

        self.img_path_entry = ModernEntry(img_row, placeholder="Thu muc chua anh...")
        self.img_path_entry.pack(side="left", fill="x", expand=True, padx=SPACING["sm"])
        self.img_path_entry.configure(state="disabled")

        ModernButton(
            img_row,
            text="Chon",
            variant="secondary",
            size="sm",
            command=self._select_image_folder,
            width=60
        ).pack(side="left")

        # Action buttons
        btn_frame = ctk.CTkFrame(editor_inner, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(SPACING["md"], 0))

        ModernButton(
            btn_frame,
            text="Luu",
            icon="",
            variant="success",
            command=self._save_content,
            width=100
        ).pack(side="left", padx=2)

        ModernButton(
            btn_frame,
            text="Xoa",
            icon="",
            variant="danger",
            command=self._delete_content,
            width=90
        ).pack(side="left", padx=2)

        ModernButton(
            btn_frame,
            text="Moi",
            icon="",
            variant="secondary",
            command=self._new_content,
            width=90
        ).pack(side="left", padx=2)

    def _load_data(self):
        """Load categories and contents"""
        self._load_categories()
        self._load_contents()

    def _load_categories(self):
        """Load categories list"""
        self.categories = get_categories()
        cat_names = [c.get('name', 'Unknown') for c in self.categories]
        if not cat_names:
            cat_names = ["Mac dinh"]
        self.category_menu.configure(values=cat_names)

        for cat in self.categories:
            if cat['id'] == self.current_category_id:
                self.category_var.set(cat['name'])
                break

    def _load_contents(self):
        """Load contents for current category"""
        self.contents = get_contents(self.current_category_id)
        self._render_content_list()

    def _render_content_list(self, contents: List[Dict] = None):
        """Render content list"""
        for widget in self.content_scroll.winfo_children():
            widget.destroy()

        self.content_frames.clear()
        self.content_checkboxes.clear()

        display_contents = contents if contents is not None else self.contents
        self.count_label.configure(text=f"{len(display_contents)} muc")

        if not display_contents:
            empty = EmptyState(
                self.content_scroll,
                icon="",
                title="Chua co noi dung",
                description="Bam 'Moi' de tao noi dung"
            )
            empty.pack(expand=True)
            return

        for content in display_contents:
            self._create_content_item(content)

    def _create_content_item(self, content: Dict):
        """Create content list item"""
        content_id = content.get('id')

        item = ctk.CTkFrame(
            self.content_scroll,
            fg_color=COLORS["bg_secondary"],
            corner_radius=RADIUS["md"],
            border_width=1,
            border_color=COLORS["border"]
        )
        item.pack(fill="x", pady=2)

        inner = ctk.CTkFrame(item, fg_color="transparent")
        inner.pack(fill="x", padx=SPACING["sm"], pady=SPACING["sm"])

        # Checkbox
        cb_var = ctk.BooleanVar(value=content_id in self.selected_items)
        self.content_checkboxes[content_id] = cb_var

        cb = ctk.CTkCheckBox(
            inner,
            text="",
            variable=cb_var,
            width=20,
            checkbox_width=18,
            checkbox_height=18,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=lambda cid=content_id, v=cb_var: self._toggle_item(cid, v)
        )
        cb.pack(side="left")

        # Content info
        info = ctk.CTkFrame(inner, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True, padx=SPACING["sm"])
        info.bind("<Button-1>", lambda e, c=content: self._select_content(c))

        title = content.get('title') or content.get('content', '')[:30] or 'Khong co tieu de'
        if len(title) > 32:
            title = title[:32] + "..."

        title_label = ctk.CTkLabel(
            info,
            text=title,
            font=ctk.CTkFont(size=FONTS["size_sm"], weight="bold"),
            text_color=COLORS["text_primary"],
            anchor="w"
        )
        title_label.pack(anchor="w")
        title_label.bind("<Button-1>", lambda e, c=content: self._select_content(c))

        # Preview text
        preview = content.get('content', '')[:40].replace('\n', ' ')
        if preview:
            ctk.CTkLabel(
                info,
                text=preview + "..." if len(content.get('content', '')) > 40 else preview,
                font=ctk.CTkFont(size=FONTS["size_xs"]),
                text_color=COLORS["text_tertiary"],
                anchor="w"
            ).pack(anchor="w")

        self.content_frames[content_id] = item

        # Hover effects
        def on_enter(e):
            item.configure(border_color=COLORS["border_hover"])

        def on_leave(e):
            if self.current_content and self.current_content.get('id') == content_id:
                item.configure(border_color=COLORS["accent"])
            else:
                item.configure(border_color=COLORS["border"])

        item.bind("<Enter>", on_enter)
        item.bind("<Leave>", on_leave)

    def _on_category_change(self, choice: str):
        """Handle category change"""
        for cat in self.categories:
            if cat['name'] == choice:
                self.current_category_id = cat['id']
                break
        self._load_contents()

    def _add_category(self):
        """Add new category"""
        name = self.new_cat_entry.get().strip()
        if not name:
            self._set_status("Vui long nhap ten danh muc!", "warning")
            return

        cat = save_category({'name': name})
        self.new_cat_entry.delete(0, "end")
        self.current_category_id = cat['id']
        self.categories = get_categories()
        cat_names = [c.get('name', 'Unknown') for c in self.categories]
        self.category_menu.configure(values=cat_names)
        self.category_var.set(name)
        self._load_contents()
        self._new_content()
        self._set_status(f"Da tao danh muc: {name}", "success")

    def _delete_category(self):
        """Delete current category"""
        if self.current_category_id == 1:
            self._set_status("Khong the xoa danh muc mac dinh!", "warning")
            return

        delete_category(self.current_category_id)
        self.current_category_id = 1
        self._load_categories()
        self._load_contents()
        self._set_status("Da xoa danh muc", "success")

    def _select_content(self, content: Dict):
        """Select content for editing"""
        self.current_content = content

        # Highlight selected item
        for cid, frame in self.content_frames.items():
            if cid == content.get('id'):
                frame.configure(border_color=COLORS["accent"])
            else:
                frame.configure(border_color=COLORS["border"])

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

        self._set_status(f"Da chon: {content.get('title', 'Untitled')}", "info")

    def _new_content(self):
        """Create new content"""
        self.current_content = None
        self.title_entry.delete(0, "end")
        self.content_editor.delete("1.0", "end")

        self.img_check_var.set(False)
        self.img_path_entry.configure(state="normal")
        self.img_path_entry.delete(0, "end")
        self.img_path_entry.configure(state="disabled")

        for frame in self.content_frames.values():
            frame.configure(border_color=COLORS["border"])

    def _save_content(self):
        """Save content"""
        title = self.title_entry.get().strip()
        content_text = self.content_editor.get("1.0", "end").strip()

        if not title:
            self._set_status("Vui long nhap tieu de!", "warning")
            return

        content_data = {
            'title': title,
            'content': content_text,
            'category_id': self.current_category_id,
            'image_path': self.img_path_entry.get() if self.img_check_var.get() else ''
        }

        if self.current_content:
            content_data['id'] = self.current_content['id']

        save_content(content_data)
        self._load_contents()
        self._new_content()
        self._set_status(f"Da luu: {title}", "success")

    def _delete_content(self):
        """Delete current content"""
        if self.current_content:
            delete_content(self.current_content['id'])
            self._new_content()
            self._load_contents()
            self._set_status("Da xoa noi dung", "success")

    def _delete_selected(self):
        """Delete selected contents"""
        if not self.selected_items:
            self._set_status("Chua chon noi dung nao", "warning")
            return

        count = len(self.selected_items)
        for item_id in self.selected_items:
            delete_content(item_id)
        self.selected_items = []
        self._load_contents()
        self._set_status(f"Da xoa {count} noi dung", "success")

    def _toggle_item(self, content_id: int, var: ctk.BooleanVar):
        """Toggle item selection"""
        if var.get():
            if content_id not in self.selected_items:
                self.selected_items.append(content_id)
        else:
            if content_id in self.selected_items:
                self.selected_items.remove(content_id)

    def _toggle_select_all(self):
        """Toggle select all"""
        if self.select_all_var.get():
            self.selected_items = [c['id'] for c in self.contents]
        else:
            self.selected_items = []
        self._render_content_list()

    def _on_search(self, query: str = None):
        """Search contents"""
        if query is None:
            query = self.search_bar.get_value()

        if not query:
            self._render_content_list()
            return

        filtered = [
            c for c in self.contents
            if query.lower() in c.get('title', '').lower()
            or query.lower() in c.get('content', '').lower()
        ]
        self._render_content_list(filtered)

    def _insert_macro(self, macro: str):
        """Insert macro into editor"""
        self.content_editor.insert("insert", macro)

    def _toggle_image(self):
        """Toggle image attachment"""
        if self.img_check_var.get():
            self.img_path_entry.configure(state="normal")
        else:
            self.img_path_entry.configure(state="disabled")

    def _select_image_folder(self):
        """Select image folder"""
        if not self.img_check_var.get():
            self.img_check_var.set(True)
            self.img_path_entry.configure(state="normal")

        path = filedialog.askdirectory(title="Chon thu muc chua hinh anh")
        if path:
            self.img_path_entry.delete(0, "end")
            self.img_path_entry.insert(0, path)
            img_count = self._count_images_in_folder(path)
            self._set_status(f"Da chon thu muc voi {img_count} anh", "success")

    def _count_images_in_folder(self, folder_path: str) -> int:
        """Count images in folder"""
        if not os.path.isdir(folder_path):
            return 0
        img_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
        count = 0
        for f in os.listdir(folder_path):
            if os.path.splitext(f)[1].lower() in img_extensions:
                count += 1
        return count

    def _import_contents(self):
        """Import contents from file"""
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
                self._set_status(f"Da nap {count} noi dung", "success")
            except Exception as e:
                self._set_status(f"Loi: {e}", "error")

    def _export_contents(self):
        """Export contents to file"""
        if not self.contents:
            self._set_status("Khong co noi dung de xuat!", "warning")
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
                self._set_status(f"Da xuat {len(self.contents)} noi dung", "success")
            except Exception as e:
                self._set_status(f"Loi: {e}", "error")

    def process_macros(self, content: str) -> str:
        """Process macros in content"""
        if content.startswith('{r}'):
            lines = content[3:].strip().split('\n')
            lines = [l.strip() for l in lines if l.strip()]
            if lines:
                return random.choice(lines)

        if content.startswith('{rrr}'):
            lines = content[5:].strip().split('\n')
            lines = [l.strip() for l in lines if l.strip()]
            random.shuffle(lines)
            return '\n'.join(lines)

        content = content.replace('{time}', datetime.now().strftime('%H:%M:%S'))
        content = content.replace('{date}', datetime.now().strftime('%d/%m/%Y'))

        return content

    def _set_status(self, text: str, status_type: str = "info"):
        """Update status bar"""
        if self.status_callback:
            self.status_callback(text, status_type)
