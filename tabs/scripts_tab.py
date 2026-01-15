"""
Tab Kịch bản - Quản lý Hidemium Scripts + Local Python Scripts
"""
import customtkinter as ctk
from typing import List, Dict
import threading
import json
import os
from datetime import datetime
from config import COLORS
from widgets import ModernCard, ModernButton, ModernEntry, ModernTextbox, ScriptCard, SearchBar
from database import get_scripts, save_script, delete_script
from api_service import api


class ScriptsTab(ctk.CTkFrame):
    """Tab quản lý kịch bản automation - 2 phần: Hidemium + Local"""
    
    def __init__(self, master, status_callback=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.status_callback = status_callback
        self.hidemium_scripts: List[Dict] = []
        self.local_scripts: List[Dict] = []
        self.current_script: Dict = None
        self.available_profiles: List[Dict] = []  # Profiles để chọn chạy script
        
        self._create_ui()
        self._load_all_scripts()
    
    def _create_ui(self):
        # ========== HEADER ==========
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(
            header_frame,
            text="📜 Quản lý Kịch bản",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left")
        
        # ========== SUB-TABS ==========
        tabs_frame = ctk.CTkFrame(self, fg_color="transparent")
        tabs_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        self.tab_var = ctk.StringVar(value="hidemium")
        
        self.hidemium_tab_btn = ctk.CTkButton(
            tabs_frame,
            text="☁️ Hidemium Scripts",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            corner_radius=8,
            height=40,
            width=180,
            command=lambda: self._switch_tab("hidemium")
        )
        self.hidemium_tab_btn.pack(side="left", padx=(0, 5))
        
        self.local_tab_btn = ctk.CTkButton(
            tabs_frame,
            text="💻 Local Scripts",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS["bg_secondary"],
            hover_color=COLORS["border"],
            corner_radius=8,
            height=40,
            width=180,
            command=lambda: self._switch_tab("local")
        )
        self.local_tab_btn.pack(side="left", padx=5)
        
        # ========== CONTENT CONTAINER ==========
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Create both panels but show only one
        self._create_hidemium_panel()
        self._create_local_panel()
        
        # Show hidemium by default
        self.local_container.pack_forget()
    
    def _switch_tab(self, tab: str):
        """Chuyển đổi giữa 2 tabs"""
        self.tab_var.set(tab)
        
        if tab == "hidemium":
            self.hidemium_tab_btn.configure(fg_color=COLORS["accent"])
            self.local_tab_btn.configure(fg_color=COLORS["bg_secondary"])
            self.local_container.pack_forget()
            self.hidemium_container.pack(fill="both", expand=True)
        else:
            self.local_tab_btn.configure(fg_color=COLORS["accent"])
            self.hidemium_tab_btn.configure(fg_color=COLORS["bg_secondary"])
            self.hidemium_container.pack_forget()
            self.local_container.pack(fill="both", expand=True)
    
    # ==================== HIDEMIUM SCRIPTS PANEL ====================
    
    def _create_hidemium_panel(self):
        """Panel cho Hidemium Scripts - chỉ sync và chạy"""
        self.hidemium_container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.hidemium_container.pack(fill="both", expand=True)
        
        # Top bar
        top_bar = ctk.CTkFrame(self.hidemium_container, fg_color=COLORS["bg_secondary"], corner_radius=12, height=60)
        top_bar.pack(fill="x", pady=(0, 10))
        top_bar.pack_propagate(False)
        
        top_inner = ctk.CTkFrame(top_bar, fg_color="transparent")
        top_inner.pack(expand=True, fill="both", padx=15, pady=10)
        
        ctk.CTkLabel(
            top_inner,
            text="Scripts từ Hidemium (chỉ xem và chạy)",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_secondary"]
        ).pack(side="left")
        
        ModernButton(
            top_inner,
            text="Đồng bộ từ Hidemium",
            icon="☁️",
            variant="primary",
            command=self._sync_hidemium_scripts,
            width=180
        ).pack(side="right")
        
        # Main content - 2 columns
        main_hidemium = ctk.CTkFrame(self.hidemium_container, fg_color="transparent")
        main_hidemium.pack(fill="both", expand=True)
        
        # Left - Scripts list
        left_panel = ctk.CTkFrame(main_hidemium, fg_color=COLORS["bg_secondary"], corner_radius=12, width=350)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)
        
        ctk.CTkLabel(
            left_panel,
            text="📋 Danh sách Scripts",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=15, pady=15)
        
        self.hidemium_list = ctk.CTkScrollableFrame(left_panel, fg_color="transparent")
        self.hidemium_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Right - Run panel
        right_panel = ctk.CTkFrame(main_hidemium, fg_color=COLORS["bg_secondary"], corner_radius=12)
        right_panel.pack(side="right", fill="both", expand=True)
        
        ctk.CTkLabel(
            right_panel,
            text="▶️ Chạy Script",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=20, pady=(15, 10))
        
        # Selected script info
        self.selected_script_frame = ctk.CTkFrame(right_panel, fg_color=COLORS["bg_card"], corner_radius=10)
        self.selected_script_frame.pack(fill="x", padx=20, pady=10)
        
        self.selected_script_label = ctk.CTkLabel(
            self.selected_script_frame,
            text="📌 Chưa chọn script nào\nBấm vào script bên trái để chọn",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_secondary"]
        )
        self.selected_script_label.pack(padx=15, pady=15)
        
        # Profile selection
        profile_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        profile_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            profile_frame,
            text="Chọn Profile để chạy:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", pady=(0, 5))
        
        self.profile_var = ctk.StringVar(value="Chọn profile...")
        self.profile_menu = ctk.CTkOptionMenu(
            profile_frame,
            variable=self.profile_var,
            values=["Chọn profile..."],
            fg_color=COLORS["bg_card"],
            button_color=COLORS["accent"],
            width=300
        )
        self.profile_menu.pack(anchor="w")
        
        # Run button
        btn_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)
        
        ModernButton(
            btn_frame,
            text="Chạy Script",
            icon="▶",
            variant="success",
            command=self._run_hidemium_script,
            width=150
        ).pack(side="left")
        
        ModernButton(
            btn_frame,
            text="Dừng",
            icon="■",
            variant="danger",
            command=self._stop_script,
            width=100
        ).pack(side="left", padx=10)
        
        # Log area
        ctk.CTkLabel(
            right_panel,
            text="📋 Log chạy script:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=20, pady=(20, 5))
        
        self.hidemium_log = ModernTextbox(right_panel, height=200)
        self.hidemium_log.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.hidemium_log.configure(state="disabled")
    
    # ==================== LOCAL SCRIPTS PANEL ====================
    
    def _create_local_panel(self):
        """Panel cho Local Python Scripts - viết và sửa được"""
        self.local_container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        
        # Main content - 2 columns
        main_local = ctk.CTkFrame(self.local_container, fg_color="transparent")
        main_local.pack(fill="both", expand=True)
        
        # Left - Scripts list
        left_panel = ctk.CTkFrame(main_local, fg_color=COLORS["bg_secondary"], corner_radius=12, width=320)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # Header
        header = ctk.CTkFrame(left_panel, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(
            header,
            text="📁 My Scripts",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left")
        
        ModernButton(
            header,
            text="+ Mới",
            variant="success",
            command=self._new_local_script,
            width=70
        ).pack(side="right")
        
        self.local_list = ctk.CTkScrollableFrame(left_panel, fg_color="transparent")
        self.local_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Right - Editor
        right_panel = ctk.CTkFrame(main_local, fg_color=COLORS["bg_secondary"], corner_radius=12)
        right_panel.pack(side="right", fill="both", expand=True)
        
        # Editor header
        editor_header = ctk.CTkFrame(right_panel, fg_color="transparent")
        editor_header.pack(fill="x", padx=20, pady=15)
        
        self.editor_title = ctk.CTkLabel(
            editor_header,
            text="✏️ Viết Script Python mới",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        self.editor_title.pack(side="left")
        
        # Form
        form_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        form_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        # Name row
        name_row = ctk.CTkFrame(form_frame, fg_color="transparent")
        name_row.pack(fill="x", pady=3)
        ctk.CTkLabel(name_row, text="Tên:", width=80, anchor="w").pack(side="left")
        self.local_name_entry = ModernEntry(name_row, placeholder="VD: Auto Like Posts")
        self.local_name_entry.pack(side="left", fill="x", expand=True)
        
        # Description row
        desc_row = ctk.CTkFrame(form_frame, fg_color="transparent")
        desc_row.pack(fill="x", pady=3)
        ctk.CTkLabel(desc_row, text="Mô tả:", width=80, anchor="w").pack(side="left")
        self.local_desc_entry = ModernEntry(desc_row, placeholder="Mô tả ngắn gọn")
        self.local_desc_entry.pack(side="left", fill="x", expand=True)
        
        # Code templates
        template_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        template_frame.pack(fill="x", padx=20, pady=(5, 10))
        
        ctk.CTkLabel(
            template_frame,
            text="📝 Template:",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        ).pack(side="left")
        
        templates = [
            ("Auto Like", self._template_like),
            ("Auto Comment", self._template_comment),
            ("Auto Scroll", self._template_scroll),
            ("Custom", self._template_custom)
        ]
        
        for name, cmd in templates:
            ctk.CTkButton(
                template_frame,
                text=name,
                width=90,
                height=28,
                fg_color=COLORS["bg_card"],
                hover_color=COLORS["border"],
                corner_radius=5,
                font=ctk.CTkFont(size=11),
                command=cmd
            ).pack(side="left", padx=3)
        
        # Code editor label
        ctk.CTkLabel(
            right_panel,
            text="🐍 Python Code:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=20, pady=(5, 5))
        
        # Code editor
        self.local_editor = ModernTextbox(right_panel, height=280)
        self.local_editor.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        self._template_custom()  # Load default template
        
        # Action buttons
        btn_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ModernButton(
            btn_frame,
            text="Lưu Script",
            icon="💾",
            variant="success",
            command=self._save_local_script,
            width=130
        ).pack(side="left", padx=3)
        
        ModernButton(
            btn_frame,
            text="Chạy thử",
            icon="▶",
            variant="primary",
            command=self._test_local_script,
            width=110
        ).pack(side="left", padx=3)
        
        ModernButton(
            btn_frame,
            text="Xóa",
            icon="🗑️",
            variant="danger",
            command=self._delete_current_local_script,
            width=80
        ).pack(side="left", padx=3)
        
        # Log area
        ctk.CTkLabel(
            right_panel,
            text="📋 Output:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=20, pady=(5, 3))
        
        self.local_log = ModernTextbox(right_panel, height=100)
        self.local_log.pack(fill="x", padx=20, pady=(0, 15))
        self.local_log.configure(state="disabled")
    
    # ==================== DATA LOADING ====================
    
    def _load_all_scripts(self):
        """Load tất cả scripts"""
        self._load_local_scripts()
        self._load_profiles_for_run()
    
    def _load_local_scripts(self):
        """Load local scripts từ database"""
        all_scripts = get_scripts()
        self.local_scripts = [s for s in all_scripts if s.get('type') != 'hidemium']
        self.hidemium_scripts = [s for s in all_scripts if s.get('type') == 'hidemium']
        self._render_local_scripts()
        self._render_hidemium_scripts()
    
    def _load_profiles_for_run(self):
        """Load danh sách profiles để chọn chạy script"""
        from database import get_profiles
        profiles = get_profiles()
        self.available_profiles = profiles
        
        profile_names = ["Chọn profile..."] + [
            f"{p.get('name', 'Unknown')} ({p.get('uuid', '')[:8]}...)"
            for p in profiles
        ]
        self.profile_menu.configure(values=profile_names)
    
    def _sync_hidemium_scripts(self):
        """Đồng bộ scripts từ Hidemium API"""
        self._log_hidemium("☁️ Đang đồng bộ scripts từ Hidemium...")
        self._set_status("Đang đồng bộ scripts...", "info")
        
        def do_sync():
            scripts = api.get_scripts(page=1, limit=100)
            self.after(0, lambda: self._on_hidemium_synced(scripts))
        
        threading.Thread(target=do_sync, daemon=True).start()
    
    def _on_hidemium_synced(self, scripts: List):
        """Xử lý khi sync xong"""
        if scripts:
            self._log_hidemium(f"✅ Tìm thấy {len(scripts)} scripts từ Hidemium")
            
            # Lưu vào local database
            for script in scripts:
                script_data = {
                    'name': script.get('name', 'Unnamed'),
                    'description': f"Hidemium Script (key: {script.get('key')})",
                    'type': 'hidemium',
                    'hidemium_key': script.get('key'),
                    'content': json.dumps(script, ensure_ascii=False)
                }
                save_script(script_data)
            
            self._load_local_scripts()
            self._set_status(f"Đã đồng bộ {len(scripts)} scripts", "success")
        else:
            self._log_hidemium("⚠️ Không tìm thấy scripts nào")
            self._set_status("Không có scripts từ Hidemium", "warning")
    
    # ==================== HIDEMIUM SCRIPTS RENDERING ====================
    
    def _render_hidemium_scripts(self):
        """Render danh sách Hidemium scripts"""
        for widget in self.hidemium_list.winfo_children():
            widget.destroy()
        
        if not self.hidemium_scripts:
            ctk.CTkLabel(
                self.hidemium_list,
                text="📭 Chưa có scripts\nBấm 'Đồng bộ từ Hidemium'",
                font=ctk.CTkFont(size=12),
                text_color=COLORS["text_secondary"]
            ).pack(pady=30)
            return
        
        for script in self.hidemium_scripts:
            self._create_hidemium_script_card(script)
    
    def _create_hidemium_script_card(self, script: Dict):
        """Tạo card cho Hidemium script"""
        card = ctk.CTkFrame(self.hidemium_list, fg_color=COLORS["bg_card"], corner_radius=10)
        card.pack(fill="x", pady=4)
        
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=10)
        
        # Name
        ctk.CTkLabel(
            inner,
            text=f"☁️ {script.get('name', 'Unknown')}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")
        
        # Key
        ctk.CTkLabel(
            inner,
            text=f"Key: {script.get('hidemium_key', 'N/A')}",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w")
        
        # Select button
        ctk.CTkButton(
            inner,
            text="Chọn để chạy",
            width=100,
            height=28,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            corner_radius=5,
            command=lambda s=script: self._select_hidemium_script(s)
        ).pack(anchor="w", pady=(5, 0))
    
    def _select_hidemium_script(self, script: Dict):
        """Chọn script để chạy"""
        self.current_script = script
        self.selected_script_label.configure(
            text=f"📌 {script.get('name', 'Unknown')}\nKey: {script.get('hidemium_key', 'N/A')}",
            text_color=COLORS["text_primary"]
        )
        self._log_hidemium(f"Đã chọn script: {script.get('name')}")
    
    def _run_hidemium_script(self):
        """Chạy Hidemium script"""
        if not self.current_script:
            self._log_hidemium("❌ Chưa chọn script!")
            return
        
        profile_text = self.profile_var.get()
        if profile_text == "Chọn profile...":
            self._log_hidemium("❌ Chưa chọn profile!")
            return
        
        # Tìm profile UUID
        idx = self.profile_menu.cget("values").index(profile_text) - 1
        if idx < 0 or idx >= len(self.available_profiles):
            self._log_hidemium("❌ Profile không hợp lệ!")
            return
        
        profile = self.available_profiles[idx]
        script_key = self.current_script.get('hidemium_key')
        
        self._log_hidemium(f"▶ Đang chạy script '{self.current_script.get('name')}' với profile '{profile.get('name')}'...")
        self._set_status("Đang chạy script...", "info")
        
        def do_run():
            result = api.run_script(script_key, profile.get('uuid'))
            self.after(0, lambda: self._on_script_run_complete(result))
        
        threading.Thread(target=do_run, daemon=True).start()
    
    def _on_script_run_complete(self, result):
        """Xử lý kết quả chạy script"""
        if result and result.get('type') != 'error':
            self._log_hidemium("✅ Script đã được khởi chạy!")
            self._set_status("Script đang chạy", "success")
        else:
            error = result.get('title', 'Lỗi không xác định') if result else 'Không có response'
            self._log_hidemium(f"❌ Lỗi: {error}")
            self._set_status(f"Lỗi: {error}", "error")
    
    def _stop_script(self):
        """Dừng script đang chạy"""
        self._log_hidemium("⏹ Đang dừng script...")
        # TODO: Implement stop API
    
    # ==================== LOCAL SCRIPTS RENDERING ====================
    
    def _render_local_scripts(self):
        """Render danh sách local scripts"""
        for widget in self.local_list.winfo_children():
            widget.destroy()
        
        if not self.local_scripts:
            ctk.CTkLabel(
                self.local_list,
                text="📭 Chưa có scripts\nBấm '+ Mới' để tạo",
                font=ctk.CTkFont(size=12),
                text_color=COLORS["text_secondary"]
            ).pack(pady=30)
            return
        
        for script in self.local_scripts:
            self._create_local_script_card(script)
    
    def _create_local_script_card(self, script: Dict):
        """Tạo card cho local script"""
        card = ctk.CTkFrame(self.local_list, fg_color=COLORS["bg_card"], corner_radius=10)
        card.pack(fill="x", pady=4)
        
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=10)
        
        # Name
        ctk.CTkLabel(
            inner,
            text=f"🐍 {script.get('name', 'Unknown')}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")
        
        # Description
        desc = script.get('description', '')[:40]
        if desc:
            ctk.CTkLabel(
                inner,
                text=desc,
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text_secondary"]
            ).pack(anchor="w")
        
        # Buttons
        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(anchor="w", pady=(5, 0))
        
        ctk.CTkButton(
            btn_row,
            text="Sửa",
            width=50,
            height=26,
            fg_color=COLORS["accent"],
            corner_radius=5,
            command=lambda s=script: self._edit_local_script(s)
        ).pack(side="left", padx=(0, 5))
        
        ctk.CTkButton(
            btn_row,
            text="▶ Chạy",
            width=60,
            height=26,
            fg_color=COLORS["success"],
            corner_radius=5,
            command=lambda s=script: self._run_local_script(s)
        ).pack(side="left")
    
    def _new_local_script(self):
        """Tạo local script mới"""
        self.current_script = None
        self.editor_title.configure(text="✏️ Viết Script Python mới")
        self.local_name_entry.delete(0, "end")
        self.local_desc_entry.delete(0, "end")
        self._template_custom()
        self._log_local("📝 Tạo script mới...")
    
    def _edit_local_script(self, script: Dict):
        """Chỉnh sửa local script"""
        self.current_script = script
        self.editor_title.configure(text=f"✏️ Sửa: {script.get('name', '')}")
        
        self.local_name_entry.delete(0, "end")
        self.local_name_entry.insert(0, script.get('name', ''))
        
        self.local_desc_entry.delete(0, "end")
        self.local_desc_entry.insert(0, script.get('description', ''))
        
        self.local_editor.delete("1.0", "end")
        self.local_editor.insert("1.0", script.get('content', ''))
        
        self._log_local(f"📝 Đang sửa: {script.get('name')}")
    
    def _save_local_script(self):
        """Lưu local script"""
        name = self.local_name_entry.get().strip()
        if not name:
            self._log_local("❌ Vui lòng nhập tên script!")
            return
        
        script_data = {
            'name': name,
            'description': self.local_desc_entry.get().strip(),
            'type': 'python',
            'content': self.local_editor.get("1.0", "end").strip()
        }
        
        if self.current_script and self.current_script.get('id'):
            script_data['id'] = self.current_script['id']
        
        save_script(script_data)
        self._load_local_scripts()
        self._log_local(f"✅ Đã lưu: {name}")
        self._set_status(f"Đã lưu script: {name}", "success")
    
    def _delete_current_local_script(self):
        """Xóa script hiện tại"""
        if not self.current_script:
            self._log_local("❌ Chưa chọn script để xóa!")
            return
        
        script_id = self.current_script.get('id')
        if script_id:
            delete_script(script_id)
            self._load_local_scripts()
            self._new_local_script()
            self._log_local("🗑️ Đã xóa script")
            self._set_status("Đã xóa script", "success")
    
    def _run_local_script(self, script: Dict):
        """Chạy local Python script"""
        self._log_local(f"▶ Đang chạy: {script.get('name')}...")
        # TODO: Implement actual execution with subprocess
    
    def _test_local_script(self):
        """Test script hiện tại"""
        code = self.local_editor.get("1.0", "end").strip()
        if not code:
            self._log_local("❌ Code trống!")
            return
        
        self._log_local("▶ Đang test script...\n" + "─" * 30)
        
        # Validate Python syntax
        try:
            compile(code, '<string>', 'exec')
            self._log_local("✅ Syntax OK!")
        except SyntaxError as e:
            self._log_local(f"❌ Syntax Error: {e}")
    
    # ==================== TEMPLATES ====================
    
    def _template_like(self):
        """Template Auto Like"""
        code = '''"""
Auto Like Posts Script
Sử dụng Selenium để tự động like các bài post
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def run(driver):
    """
    Hàm chính - được gọi khi chạy script
    driver: Selenium WebDriver instance
    """
    # Scroll để load posts
    driver.execute_script("window.scrollBy(0, 500)")
    time.sleep(2)
    
    # Tìm các nút Like
    like_buttons = driver.find_elements(
        By.CSS_SELECTOR, 
        '[data-testid="like-button"], [aria-label*="Like"]'
    )
    
    liked_count = 0
    for btn in like_buttons[:5]:  # Like tối đa 5 posts
        try:
            btn.click()
            liked_count += 1
            time.sleep(1)  # Delay giữa các like
        except Exception as e:
            print(f"Skip: {e}")
    
    return f"Đã like {liked_count} posts"

# Chạy thử
if __name__ == "__main__":
    print("Script sẵn sàng!")
'''
        self.local_editor.delete("1.0", "end")
        self.local_editor.insert("1.0", code)
    
    def _template_comment(self):
        """Template Auto Comment"""
        code = '''"""
Auto Comment Script
Tự động comment vào bài post
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import random

# Danh sách comments random
COMMENTS = [
    "Hay quá! 👍",
    "Cảm ơn bạn đã chia sẻ!",
    "Rất hữu ích!",
    "Nice post! 🔥",
    "Tuyệt vời!"
]

def run(driver, post_url=None):
    """
    Hàm chính
    driver: Selenium WebDriver
    post_url: URL bài post cần comment
    """
    if post_url:
        driver.get(post_url)
        time.sleep(3)
    
    # Tìm ô comment
    comment_box = driver.find_element(
        By.CSS_SELECTOR,
        '[data-testid="comment-box"] textarea, [contenteditable="true"]'
    )
    
    # Random comment
    comment_text = random.choice(COMMENTS)
    
    # Nhập comment
    comment_box.click()
    time.sleep(0.5)
    comment_box.send_keys(comment_text)
    comment_box.send_keys(Keys.ENTER)
    
    time.sleep(2)
    return f"Đã comment: {comment_text}"

if __name__ == "__main__":
    print("Script sẵn sàng!")
'''
        self.local_editor.delete("1.0", "end")
        self.local_editor.insert("1.0", code)
    
    def _template_scroll(self):
        """Template Auto Scroll"""
        code = '''"""
Auto Scroll Feed Script
Tự động scroll Facebook feed
"""
from selenium import webdriver
import time

def run(driver, scroll_count=10, delay=2):
    """
    Scroll feed
    driver: Selenium WebDriver
    scroll_count: Số lần scroll
    delay: Thời gian chờ giữa các lần (giây)
    """
    for i in range(scroll_count):
        # Scroll xuống
        driver.execute_script("window.scrollBy(0, 800)")
        print(f"Scroll {i+1}/{scroll_count}")
        time.sleep(delay)
    
    return f"Đã scroll {scroll_count} lần"

if __name__ == "__main__":
    print("Script sẵn sàng!")
'''
        self.local_editor.delete("1.0", "end")
        self.local_editor.insert("1.0", code)
    
    def _template_custom(self):
        """Template Custom"""
        code = '''"""
Custom Automation Script
Viết script tự động của bạn ở đây
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

def run(driver):
    """
    Hàm chính - được gọi khi chạy script
    
    Args:
        driver: Selenium WebDriver instance (đã kết nối với Hidemium profile)
    
    Returns:
        str: Kết quả thực thi
    """
    # Mở Facebook
    driver.get("https://facebook.com")
    time.sleep(3)
    
    # TODO: Thêm code automation của bạn ở đây
    
    return "Script hoàn thành!"

if __name__ == "__main__":
    print("Script sẵn sàng!")
'''
        self.local_editor.delete("1.0", "end")
        self.local_editor.insert("1.0", code)
    
    # ==================== LOGGING ====================
    
    def _log_hidemium(self, msg: str):
        """Log cho Hidemium panel"""
        self.hidemium_log.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.hidemium_log.insert("end", f"\n[{timestamp}] {msg}")
        self.hidemium_log.see("end")
        self.hidemium_log.configure(state="disabled")
    
    def _log_local(self, msg: str):
        """Log cho Local panel"""
        self.local_log.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.local_log.insert("end", f"\n[{timestamp}] {msg}")
        self.local_log.see("end")
        self.local_log.configure(state="disabled")
    
    def _set_status(self, text: str, status_type: str = "info"):
        """Cập nhật status bar"""
        if self.status_callback:
            self.status_callback(text, status_type)
