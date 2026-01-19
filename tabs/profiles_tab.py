"""
Profiles Tab - Cyberpunk Profile Management Interface
Neon design with glitch effects and smooth interactions
"""
import customtkinter as ctk
from typing import List, Dict
import threading
from config import COLORS, FONTS, SPACING, RADIUS, HEIGHTS, TAB_COLORS
from widgets import ModernCard, ModernButton, ModernEntry, ProfileCard, SearchBar, Badge, EmptyState
from cyber_widgets import CyberTitle, CyberStatCard, CyberButton
from api_service import api
from db import get_profiles as db_get_profiles, sync_profiles, update_profile_local


class ProfilesTab(ctk.CTkFrame):
    """Premium Profile Management Tab"""

    def __init__(self, master, status_callback=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.status_callback = status_callback
        self.profiles: List[Dict] = []
        self.selected_profiles: List[Dict] = []
        self.profile_cards: List[ProfileCard] = []
        self.folders: List[Dict] = []
        self.folder_id_to_name: Dict[int, str] = {}
        self._auto_refresh_job = None
        self._is_polling = False

        self._create_ui()
        self._load_folders()
        self._load_profiles()
        self._start_auto_refresh()

    def _start_auto_refresh(self):
        """Start auto-refresh every 5 seconds"""
        self._auto_refresh_silent()

    def _safe_after(self, delay, callback):
        """Thread-safe wrapper for self.after"""
        try:
            if self.winfo_exists():
                self.after(delay, callback)
        except (RuntimeError, Exception):
            pass

    def _auto_refresh_silent(self):
        """Silent auto-refresh of running status"""
        if self._is_polling:
            self._auto_refresh_job = self.after(5000, self._auto_refresh_silent)
            return

        self._is_polling = True

        def fetch():
            try:
                running_uuids = api.get_running_profiles(is_local=True)
                self._safe_after(0, lambda: self._on_auto_refresh_complete(running_uuids))
            except Exception:
                self._safe_after(0, lambda: self._on_auto_refresh_error())

        threading.Thread(target=fetch, daemon=True).start()

    def _on_auto_refresh_complete(self, running_uuids: List[str]):
        """Handle auto-refresh completion"""
        self._is_polling = False

        changed = False
        for profile in self.profiles:
            uuid = profile.get('uuid')
            new_status = 1 if uuid in running_uuids else 0
            if profile.get('check_open') != new_status:
                profile['check_open'] = new_status
                update_profile_local(uuid, {'check_open': new_status})
                self._update_card_status(uuid, new_status)
                changed = True

        if changed:
            self._update_stats()

        self._auto_refresh_job = self.after(5000, self._auto_refresh_silent)

    def _on_auto_refresh_error(self):
        """Handle auto-refresh error"""
        self._is_polling = False
        self._auto_refresh_job = self.after(5000, self._auto_refresh_silent)

    def destroy(self):
        """Cleanup on destroy"""
        if self._auto_refresh_job:
            self.after_cancel(self._auto_refresh_job)
        super().destroy()

    def _create_ui(self):
        """Create cyberpunk UI"""
        # ========== HEADER SECTION ==========
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=SPACING["2xl"], pady=(SPACING["xl"], SPACING["lg"]))

        # Title row
        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(fill="x")

        # Cyberpunk Title with glitch effect
        self.cyber_title = CyberTitle(
            title_row,
            title="PROFILES",
            subtitle="Quan ly va dieu khien cac tai khoan Facebook",
            tab_id="profiles"
        )
        self.cyber_title.pack(side="left")

        # Action buttons with neon style
        actions = ctk.CTkFrame(title_row, fg_color="transparent")
        actions.pack(side="right")

        CyberButton(
            actions,
            text="TAO PROFILE",
            variant="success",
            command=self._show_create_dialog,
            width=130
        ).pack(side="left", padx=SPACING["xs"])

        CyberButton(
            actions,
            text="DONG BO",
            variant="primary",
            command=self._sync_profiles,
            width=120
        ).pack(side="left", padx=SPACING["xs"])

        CyberButton(
            actions,
            text="LAM MOI",
            variant="secondary",
            command=self._refresh_running_status,
            width=110
        ).pack(side="left", padx=SPACING["xs"])

        # ========== STATS CARDS - CYBERPUNK STYLE ==========
        stats_row = ctk.CTkFrame(self, fg_color="transparent")
        stats_row.pack(fill="x", padx=SPACING["2xl"], pady=(0, SPACING["lg"]))

        # Total profiles card
        self.total_card = CyberStatCard(
            stats_row, "TONG SO", "0", "", "cyan"
        )
        self.total_card.pack(side="left", fill="x", expand=True, padx=(0, SPACING["md"]))

        # Running profiles card
        self.running_card = CyberStatCard(
            stats_row, "DANG CHAY", "0", "", "green"
        )
        self.running_card.pack(side="left", fill="x", expand=True, padx=(0, SPACING["md"]))

        # Selected profiles card
        self.selected_card = CyberStatCard(
            stats_row, "DA CHON", "0", "", "magenta"
        )
        self.selected_card.pack(side="left", fill="x", expand=True, padx=(0, SPACING["md"]))

        # Stopped profiles card
        self.stopped_card = CyberStatCard(
            stats_row, "DA DUNG", "0", "", "purple"
        )
        self.stopped_card.pack(side="left", fill="x", expand=True)

        # ========== TOOLBAR ==========
        toolbar = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=COLORS["border"]
        )
        toolbar.pack(fill="x", padx=SPACING["2xl"], pady=(0, SPACING["lg"]))

        toolbar_inner = ctk.CTkFrame(toolbar, fg_color="transparent")
        toolbar_inner.pack(fill="x", padx=SPACING["lg"], pady=SPACING["md"])

        # Search
        self.search_bar = SearchBar(
            toolbar_inner,
            placeholder="Tim kiem profile...",
            on_search=self._search_profiles
        )
        self.search_bar.pack(side="left")

        # Filters
        filter_frame = ctk.CTkFrame(toolbar_inner, fg_color="transparent")
        filter_frame.pack(side="left", padx=SPACING["2xl"])

        self.filter_var = ctk.StringVar(value="all")

        filters = [
            ("all", "Tat ca"),
            ("running", "Dang chay"),
            ("stopped", "Da dung")
        ]

        for value, text in filters:
            ctk.CTkRadioButton(
                filter_frame,
                text=text,
                variable=self.filter_var,
                value=value,
                fg_color=COLORS["accent"],
                hover_color=COLORS["accent_hover"],
                border_color=COLORS["border"],
                font=ctk.CTkFont(size=FONTS["size_sm"]),
                command=self._filter_profiles
            ).pack(side="left", padx=SPACING["sm"])

        # Folder filter
        folder_frame = ctk.CTkFrame(toolbar_inner, fg_color="transparent")
        folder_frame.pack(side="left", padx=SPACING["lg"])

        ctk.CTkLabel(
            folder_frame,
            text="",
            font=ctk.CTkFont(size=FONTS["size_md"]),
            text_color=COLORS["text_secondary"]
        ).pack(side="left", padx=(0, SPACING["xs"]))

        self.folder_var = ctk.StringVar(value="Tat ca thu muc")
        self.folder_menu = ctk.CTkOptionMenu(
            folder_frame,
            variable=self.folder_var,
            values=["Tat ca thu muc"],
            fg_color=COLORS["bg_secondary"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            dropdown_fg_color=COLORS["bg_card"],
            dropdown_hover_color=COLORS["bg_elevated"],
            width=160,
            command=self._filter_by_folder
        )
        self.folder_menu.pack(side="left")

        # Bulk actions - Cyberpunk style
        bulk_frame = ctk.CTkFrame(toolbar_inner, fg_color="transparent")
        bulk_frame.pack(side="right")

        CyberButton(
            bulk_frame,
            text="MO TAT CA",
            variant="success",
            size="sm",
            command=self._open_selected,
            width=100
        ).pack(side="left", padx=2)

        CyberButton(
            bulk_frame,
            text="DONG TAT CA",
            variant="danger",
            size="sm",
            command=self._close_selected,
            width=110
        ).pack(side="left", padx=2)

        CyberButton(
            bulk_frame,
            text="XOA",
            variant="ghost",
            size="sm",
            command=self._delete_selected,
            width=70
        ).pack(side="left", padx=2)

        # ========== PROFILES LIST ==========
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["accent"]
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=SPACING["2xl"], pady=(0, SPACING["xl"]))

        # Loading state - Cyberpunk style
        self.loading_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.loading_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(
            self.loading_frame,
            text="◢",
            font=ctk.CTkFont(size=48),
            text_color=COLORS["neon_cyan"]
        ).pack(pady=(SPACING["4xl"], SPACING["md"]))

        self.loading_label = ctk.CTkLabel(
            self.loading_frame,
            text="// LOADING PROFILES...",
            font=ctk.CTkFont(family=FONTS["family_mono"], size=FONTS["size_md"]),
            text_color=COLORS["text_secondary"]
        )
        self.loading_label.pack()

    def _load_profiles(self):
        """Load profiles from local database"""
        self.profiles = db_get_profiles()

        if self.profiles:
            self._apply_folder_names_to_profiles()
            self._render_profiles(self.profiles)
            self._update_stats()
            self._refresh_running_status()
        else:
            self._sync_profiles()

    def _sync_profiles(self):
        """Sync profiles from Hidemium API"""
        self._set_status("Dang dong bo profiles tu Hidemium...", "info")
        self.loading_label.configure(text="Dang dong bo tu Hidemium...")
        self.loading_frame.pack(fill="both", expand=True)

        for card in self.profile_cards:
            card.destroy()
        self.profile_cards.clear()

        def fetch():
            profiles_result = api.get_profiles(limit=100, is_local=True)
            running_uuids = api.get_running_profiles(is_local=True)
            self._safe_after(0, lambda: self._on_sync_complete(profiles_result, running_uuids))

        threading.Thread(target=fetch, daemon=True).start()

    def _on_sync_complete(self, result, running_uuids: List[str] = None):
        """Handle sync completion"""
        self.loading_frame.pack_forget()
        running_uuids = running_uuids or []

        if isinstance(result, list) and result:
            for profile in result:
                uuid = profile.get('uuid')
                profile['check_open'] = 1 if uuid in running_uuids else 0

            sync_profiles(result)
            self.profiles = result
            self._apply_folder_names_to_profiles()

            running_count = len(running_uuids)
            self._set_status(f"Da dong bo {len(result)} profiles ({running_count} dang chay)", "success")
        elif isinstance(result, dict) and result.get('type') == 'error':
            self._set_status(result.get('title', 'Loi'), "error")
            self._show_empty_state("Khong the dong bo", result.get('title', ''))
            return
        else:
            self.profiles = []
            self._set_status("Khong co profiles", "warning")

        self._render_profiles(self.profiles)
        self._update_stats()

    def _refresh_running_status(self):
        """Refresh running status from API"""
        self._set_status("Dang kiem tra trang thai...", "info")

        def fetch():
            running_uuids = api.get_running_profiles(is_local=True)
            self._safe_after(0, lambda: self._on_running_status_received(running_uuids))

        threading.Thread(target=fetch, daemon=True).start()

    def _on_running_status_received(self, running_uuids: List[str]):
        """Handle running status update"""
        for profile in self.profiles:
            uuid = profile.get('uuid')
            new_status = 1 if uuid in running_uuids else 0
            if profile.get('check_open') != new_status:
                profile['check_open'] = new_status
                update_profile_local(uuid, {'check_open': new_status})
                self._update_card_status(uuid, new_status)

        self._update_stats()
        running_count = len(running_uuids)
        self._set_status(f"Da cap nhat: {running_count} profile dang chay", "success")

    def _render_profiles(self, profiles: List[Dict]):
        """Render profile cards"""
        for card in self.profile_cards:
            card.destroy()
        self.profile_cards.clear()

        if not profiles:
            self._show_empty_state("Chua co profile nao", "Bam 'Tao Profile' de bat dau")
            return

        # Create cards
        for profile in profiles:
            card = ProfileCard(
                self.scroll_frame,
                profile_data=profile,
                on_toggle=self._toggle_profile,
                on_edit=self._edit_profile,
                on_select=self._on_profile_select
            )
            card.pack(fill="x", pady=SPACING["xs"])
            self.profile_cards.append(card)

    def _show_empty_state(self, title: str, description: str):
        """Show empty state"""
        self.loading_frame.pack(fill="both", expand=True)
        for widget in self.loading_frame.winfo_children():
            widget.destroy()

        empty = EmptyState(
            self.loading_frame,
            icon="",
            title=title,
            description=description,
            action_text="Tao Profile",
            on_action=self._show_create_dialog
        )
        empty.pack(expand=True)

    def _update_stats(self):
        """Update statistics cards"""
        total = len(self.profiles)
        selected = len(self.selected_profiles)
        running = sum(1 for p in self.profiles if p.get('check_open') == 1)
        stopped = total - running

        self.total_card.value_label.configure(text=str(total))
        self.running_card.value_label.configure(text=str(running))
        self.selected_card.value_label.configure(text=str(selected))
        self.stopped_card.value_label.configure(text=str(stopped))

        self._update_folder_filter()

    def _search_profiles(self, query: str):
        """Search profiles"""
        if not query:
            self._render_profiles(self.profiles)
            return

        filtered = [
            p for p in self.profiles
            if query.lower() in p.get('name', '').lower()
            or query.lower() in p.get('uuid', '').lower()
        ]
        self._render_profiles(filtered)

    def _filter_profiles(self):
        """Filter profiles by status"""
        filter_type = self.filter_var.get()

        if filter_type == "all":
            filtered = self.profiles
        elif filter_type == "running":
            filtered = [p for p in self.profiles if p.get('check_open') == 1]
        else:
            filtered = [p for p in self.profiles if p.get('check_open') != 1]

        # Apply folder filter
        folder_filter = self.folder_var.get()
        if folder_filter != "Tat ca thu muc":
            target_folder_id = None
            for fid, fname in self.folder_id_to_name.items():
                if fname == folder_filter:
                    target_folder_id = fid
                    break
            if target_folder_id is not None:
                filtered = [p for p in filtered if p.get('folder_id') == target_folder_id]

        self._render_profiles(filtered)

    def _filter_by_folder(self, folder_name: str):
        """Filter by folder"""
        self._filter_profiles()

    def _load_folders(self):
        """Load folders from API"""
        def fetch():
            folders = api.get_folders(is_local=True)
            self._safe_after(0, lambda: self._on_folders_loaded(folders))

        threading.Thread(target=fetch, daemon=True).start()

    def _on_folders_loaded(self, folders: List):
        """Handle folders loaded"""
        self.folders = folders if folders else []

        self.folder_id_to_name = {}
        for folder in self.folders:
            fid = folder.get('id') or folder.get('folder_id')
            fname = folder.get('name') or folder.get('folder_name')
            if fid is not None and fname:
                self.folder_id_to_name[fid] = fname

        self._apply_folder_names_to_profiles()
        self._update_folder_filter()

    def _apply_folder_names_to_profiles(self):
        """Apply folder names to profiles"""
        for p in self.profiles:
            fid = p.get('folder_id')
            if fid and fid in self.folder_id_to_name:
                p['folder_name'] = self.folder_id_to_name[fid]

    def _update_folder_filter(self):
        """Update folder dropdown"""
        folder_list = ["Tat ca thu muc"]

        for folder in self.folders:
            name = folder.get('name') or folder.get('folder_name')
            if name:
                folder_list.append(name)

        if len(folder_list) == 1:
            folder_names = set()
            for p in self.profiles:
                folder = p.get('folder_name')
                if folder:
                    folder_names.add(folder)
            folder_list.extend(sorted(folder_names))

        self.folder_menu.configure(values=folder_list)

    def _on_profile_select(self, profile: Dict, selected: bool):
        """Handle profile selection"""
        if selected:
            if profile not in self.selected_profiles:
                self.selected_profiles.append(profile)
        else:
            if profile in self.selected_profiles:
                self.selected_profiles.remove(profile)
        self._update_stats()

    def _toggle_profile(self, profile: Dict, open_browser: bool):
        """Toggle browser open/close"""
        uuid = profile.get('uuid')
        name = profile.get('name', 'Unknown')

        if open_browser:
            self._set_status(f"Dang mo profile {name}...", "info")

            def do_action():
                result = api.open_browser(uuid)
                self._safe_after(0, lambda: self._on_toggle_complete(result, profile, True))
        else:
            self._set_status(f"Dang dong profile {name}...", "info")

            def do_action():
                result = api.close_browser(uuid)
                self._safe_after(0, lambda: self._on_toggle_complete(result, profile, False))

        threading.Thread(target=do_action, daemon=True).start()

    def _on_toggle_complete(self, result, profile: Dict, was_opening: bool):
        """Handle toggle completion"""
        action = "mo" if was_opening else "dong"
        uuid = profile.get('uuid')

        is_success = False
        if was_opening:
            is_success = result.get('status') == 'successfully'
        else:
            message = result.get('message', '')
            is_success = 'closed' in message.lower() or message == 'Profile closed'

        if is_success:
            self._set_status(f"Da {action} profile {profile.get('name')} thanh cong", "success")

            new_check_open = 1 if was_opening else 0
            for i, p in enumerate(self.profiles):
                if p.get('uuid') == uuid:
                    self.profiles[i]['check_open'] = new_check_open
                    break

            update_profile_local(uuid, {'check_open': new_check_open})
            self._update_card_status(uuid, new_check_open)
            self._update_stats()
        else:
            error_msg = result.get('message') or result.get('title') or 'Loi khong xac dinh'
            self._set_status(f"Loi {action}: {error_msg}", "error")

    def _update_card_status(self, uuid: str, check_open: int):
        """Update card status without reloading"""
        for card in self.profile_cards:
            if card.profile_data.get('uuid') == uuid:
                card.profile_data['check_open'] = check_open
                card.is_running = check_open == 1

                if card.is_running:
                    card.toggle_btn.configure(
                        text=" Dung",
                        fg_color=COLORS["error"],
                        hover_color=COLORS["error_hover"]
                    )
                    card.status_label.configure(
                        text="  RUNNING",
                        text_color=COLORS["success"]
                    )
                else:
                    card.toggle_btn.configure(
                        text=" Mo",
                        fg_color=COLORS["success"],
                        hover_color=COLORS["success_hover"]
                    )
                    card.status_label.configure(
                        text="  STOPPED",
                        text_color=COLORS["text_tertiary"]
                    )
                break

    def _edit_profile(self, profile: Dict):
        """Open edit dialog"""
        dialog = EditProfileDialog(self, profile)
        dialog.grab_set()

    def _open_selected(self):
        """Open all selected profiles"""
        if not self.selected_profiles:
            self._set_status("Chua chon profile nao", "warning")
            return

        for profile in self.selected_profiles:
            self._toggle_profile(profile, True)

    def _close_selected(self):
        """Close all selected profiles"""
        if not self.selected_profiles:
            self._set_status("Chua chon profile nao", "warning")
            return

        for profile in self.selected_profiles:
            self._toggle_profile(profile, False)

    def _delete_selected(self):
        """Delete selected profiles"""
        if not self.selected_profiles:
            self._set_status("Chua chon profile nao", "warning")
            return

        uuids = [p.get('uuid') for p in self.selected_profiles]
        self._set_status(f"Dang xoa {len(uuids)} profiles...", "info")

        def do_delete():
            result = api.delete_profiles(uuids)
            self._safe_after(0, lambda: self._on_delete_complete(result))

        threading.Thread(target=do_delete, daemon=True).start()

    def _on_delete_complete(self, result):
        """Handle delete completion"""
        if result.get('type') == 'success':
            self._set_status("Da xoa thanh cong", "success")
            self.selected_profiles.clear()
            self._load_profiles()
        else:
            self._set_status(f"Loi xoa: {result.get('title', 'Unknown')}", "error")

    def _set_status(self, text: str, status_type: str = "info"):
        """Update status bar"""
        if self.status_callback:
            self.status_callback(text, status_type)

    def _show_create_dialog(self):
        """Show create profile dialog"""
        dialog = CreateProfileDialog(self)
        self.wait_window(dialog)

        if dialog.result:
            self._set_status("Dang tao profile moi...", "info")

            def do_create():
                result = api.create_profile(dialog.result)
                self._safe_after(0, lambda: self._on_create_complete(result))

            threading.Thread(target=do_create, daemon=True).start()

    def _on_create_complete(self, result):
        """Handle create completion"""
        if result and (result.get('uuid') or result.get('type') == 'success'):
            self._set_status("Da tao profile moi thanh cong!", "success")
            self._load_folders()
            self._sync_profiles()
        else:
            error_msg = ''
            if result:
                error_msg = result.get('title') or result.get('message') or result.get('error') or str(result)
            else:
                error_msg = 'Khong the tao profile'
            self._set_status(f"Loi: {error_msg}", "error")


class CreateProfileDialog(ctk.CTkToplevel):
    """Modern Create Profile Dialog"""

    def __init__(self, parent):
        super().__init__(parent)

        self.result = None

        self.title("Tao Profile Moi")
        self.geometry("650x800")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg_dark"])

        self.transient(parent)
        self.grab_set()

        self._create_ui()

        self.update_idletasks()
        x = (self.winfo_screenwidth() - 650) // 2
        y = (self.winfo_screenheight() - 800) // 2
        self.geometry(f"+{x}+{y}")

    def _create_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=SPACING["2xl"], pady=SPACING["xl"])

        ctk.CTkLabel(
            header,
            text="  Tao Profile Moi",
            font=ctk.CTkFont(
                family=FONTS["family"],
                size=FONTS["size_2xl"],
                weight="bold"
            ),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")

        # Scrollable content
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=SPACING["2xl"])

        # ===== BASIC INFO =====
        basic_card = self._create_section_card(scroll, "", "Thong tin co ban")

        # Name
        self._create_form_row(basic_card, "Ten Profile")
        self.name_entry = ModernEntry(basic_card, placeholder="VD: FB Account 01")
        self.name_entry.pack(fill="x", padx=SPACING["lg"], pady=(0, SPACING["sm"]))

        # Folder
        self._create_form_row(basic_card, "Thu muc")
        self.folder_entry = ModernEntry(basic_card, placeholder="Ten folder (tu dong tao neu chua co)")
        self.folder_entry.pack(fill="x", padx=SPACING["lg"], pady=(0, SPACING["sm"]))

        # Start URL
        self._create_form_row(basic_card, "Start URL")
        self.url_entry = ModernEntry(basic_card, placeholder="https://facebook.com")
        self.url_entry.pack(fill="x", padx=SPACING["lg"], pady=(0, SPACING["lg"]))

        # ===== SYSTEM CONFIG =====
        sys_card = self._create_section_card(scroll, "", "Cau hinh he thong")

        # OS row
        os_row = ctk.CTkFrame(sys_card, fg_color="transparent")
        os_row.pack(fill="x", padx=SPACING["lg"], pady=SPACING["xs"])

        os_col = ctk.CTkFrame(os_row, fg_color="transparent")
        os_col.pack(side="left", fill="x", expand=True, padx=(0, SPACING["sm"]))
        self._create_form_row(os_col, "He dieu hanh")
        self.os_var = ctk.StringVar(value="win")
        self.os_menu = ctk.CTkOptionMenu(
            os_col,
            variable=self.os_var,
            values=["win", "mac", "linux", "android", "ios"],
            fg_color=COLORS["bg_secondary"],
            button_color=COLORS["accent"],
            command=self._on_os_change
        )
        self.os_menu.pack(fill="x")

        ver_col = ctk.CTkFrame(os_row, fg_color="transparent")
        ver_col.pack(side="left", fill="x", expand=True)
        self._create_form_row(ver_col, "Phien ban")
        self.os_version_var = ctk.StringVar(value="11")
        self.os_versions = {
            "win": ["11", "10"],
            "mac": ["14.3.0", "14.2.1", "14.1.0", "13.6.0"],
            "linux": ["ubuntu_24.04", "linux_x86_64"],
            "android": ["15", "14", "13", "12"],
            "ios": ["18.0", "17.6", "17.4", "16.7"]
        }
        self.os_version_menu = ctk.CTkOptionMenu(
            ver_col,
            variable=self.os_version_var,
            values=self.os_versions["win"],
            fg_color=COLORS["bg_secondary"],
            button_color=COLORS["accent"]
        )
        self.os_version_menu.pack(fill="x")

        # Browser row
        browser_row = ctk.CTkFrame(sys_card, fg_color="transparent")
        browser_row.pack(fill="x", padx=SPACING["lg"], pady=SPACING["xs"])

        browser_col = ctk.CTkFrame(browser_row, fg_color="transparent")
        browser_col.pack(side="left", fill="x", expand=True, padx=(0, SPACING["sm"]))
        self._create_form_row(browser_col, "Trinh duyet")
        self.browser_var = ctk.StringVar(value="chrome")
        self.browser_menu = ctk.CTkOptionMenu(
            browser_col,
            variable=self.browser_var,
            values=["chrome", "edge", "opera", "brave"],
            fg_color=COLORS["bg_secondary"],
            button_color=COLORS["accent"],
            command=self._on_browser_change
        )
        self.browser_menu.pack(fill="x")

        bver_col = ctk.CTkFrame(browser_row, fg_color="transparent")
        bver_col.pack(side="left", fill="x", expand=True)
        self._create_form_row(bver_col, "Version")
        self.browser_version_var = ctk.StringVar(value="143")
        self.browser_versions = {
            "chrome": ["143", "142", "141", "140"],
            "edge": ["131", "130", "129"],
            "opera": ["115", "114", "113"],
            "brave": ["1.73", "1.72", "1.71"]
        }
        self.browser_version_menu = ctk.CTkOptionMenu(
            bver_col,
            variable=self.browser_version_var,
            values=self.browser_versions["chrome"],
            fg_color=COLORS["bg_secondary"],
            button_color=COLORS["accent"]
        )
        self.browser_version_menu.pack(fill="x")

        # Resolution and language row
        res_row = ctk.CTkFrame(sys_card, fg_color="transparent")
        res_row.pack(fill="x", padx=SPACING["lg"], pady=(SPACING["xs"], SPACING["lg"]))

        res_col = ctk.CTkFrame(res_row, fg_color="transparent")
        res_col.pack(side="left", fill="x", expand=True, padx=(0, SPACING["sm"]))
        self._create_form_row(res_col, "Do phan giai")
        self.resolution_var = ctk.StringVar(value="1920x1080")
        self.resolution_menu = ctk.CTkOptionMenu(
            res_col,
            variable=self.resolution_var,
            values=["1920x1080", "1440x900", "1366x768", "1280x800"],
            fg_color=COLORS["bg_secondary"],
            button_color=COLORS["accent"]
        )
        self.resolution_menu.pack(fill="x")

        lang_col = ctk.CTkFrame(res_row, fg_color="transparent")
        lang_col.pack(side="left", fill="x", expand=True)
        self._create_form_row(lang_col, "Ngon ngu")
        self.language_var = ctk.StringVar(value="vi-VN")
        self.language_menu = ctk.CTkOptionMenu(
            lang_col,
            variable=self.language_var,
            values=["vi-VN", "en-US", "en-GB", "ja-JP"],
            fg_color=COLORS["bg_secondary"],
            button_color=COLORS["accent"]
        )
        self.language_menu.pack(fill="x")

        # ===== FINGERPRINT =====
        fp_card = self._create_section_card(scroll, "", "Bao ve Fingerprint")

        fp_grid = ctk.CTkFrame(fp_card, fg_color="transparent")
        fp_grid.pack(fill="x", padx=SPACING["lg"], pady=SPACING["md"])

        self.canvas_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            fp_grid, text="Canvas", variable=self.canvas_var,
            fg_color=COLORS["success"], hover_color=COLORS["success_hover"]
        ).pack(side="left", padx=SPACING["md"])

        self.webgl_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            fp_grid, text="WebGL", variable=self.webgl_var,
            fg_color=COLORS["success"], hover_color=COLORS["success_hover"]
        ).pack(side="left", padx=SPACING["md"])

        self.audio_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            fp_grid, text="Audio", variable=self.audio_var,
            fg_color=COLORS["success"], hover_color=COLORS["success_hover"]
        ).pack(side="left", padx=SPACING["md"])

        self.font_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            fp_grid, text="Font", variable=self.font_var,
            fg_color=COLORS["success"], hover_color=COLORS["success_hover"]
        ).pack(side="left", padx=SPACING["md"])

        # ===== PROXY =====
        proxy_card = self._create_section_card(scroll, "", "Proxy (tuy chon)")

        ctk.CTkLabel(
            proxy_card,
            text="Format: TYPE|IP|PORT|USER|PASS",
            font=ctk.CTkFont(size=FONTS["size_xs"]),
            text_color=COLORS["text_tertiary"]
        ).pack(anchor="w", padx=SPACING["lg"])

        self.proxy_entry = ModernEntry(proxy_card, placeholder="HTTP|1.1.1.1|8080|user|pass")
        self.proxy_entry.pack(fill="x", padx=SPACING["lg"], pady=(SPACING["xs"], SPACING["lg"]))

        # ===== BUTTONS =====
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=SPACING["2xl"], pady=SPACING["xl"])

        ModernButton(
            btn_frame,
            text="Tao Profile",
            icon="",
            variant="success",
            command=self._create,
            width=140
        ).pack(side="left", padx=SPACING["xs"])

        ModernButton(
            btn_frame,
            text="Huy",
            variant="secondary",
            command=self.destroy,
            width=100
        ).pack(side="left", padx=SPACING["xs"])

    def _create_section_card(self, parent, icon: str, title: str):
        """Create a section card"""
        card = ctk.CTkFrame(
            parent,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=COLORS["border"]
        )
        card.pack(fill="x", pady=SPACING["sm"])

        # Header
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=SPACING["lg"], pady=(SPACING["md"], SPACING["sm"]))

        ctk.CTkLabel(
            header,
            text=icon,
            font=ctk.CTkFont(size=FONTS["size_lg"]),
            text_color=COLORS["accent"]
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text=title,
            font=ctk.CTkFont(size=FONTS["size_md"], weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left", padx=SPACING["sm"])

        return card

    def _create_form_row(self, parent, label: str):
        """Create form label"""
        ctk.CTkLabel(
            parent,
            text=label,
            font=ctk.CTkFont(size=FONTS["size_sm"]),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w")

    def _on_os_change(self, selected_os):
        """Handle OS change"""
        versions = self.os_versions.get(selected_os, ["10"])
        self.os_version_menu.configure(values=versions)
        self.os_version_var.set(versions[0])

        if selected_os in ["android", "ios"]:
            if selected_os == "ios":
                self.browser_menu.configure(values=["safari"])
                self.browser_var.set("safari")
            else:
                self.browser_menu.configure(values=["chrome"])
                self.browser_var.set("chrome")
            self.resolution_menu.configure(values=["390x844", "393x873", "414x896"])
            self.resolution_var.set("390x844")
        else:
            self.browser_menu.configure(values=["chrome", "edge", "opera", "brave"])
            self.browser_var.set("chrome")
            self.resolution_menu.configure(values=["1920x1080", "1440x900", "1366x768"])
            self.resolution_var.set("1920x1080")

    def _on_browser_change(self, selected_browser):
        """Handle browser change"""
        versions = self.browser_versions.get(selected_browser, ["143"])
        self.browser_version_menu.configure(values=versions)
        self.browser_version_var.set(versions[0])

    def _create(self):
        """Create profile"""
        name = self.name_entry.get().strip()
        if not name:
            self.name_entry.configure(border_color=COLORS["error"])
            return

        self.result = {
            "name": name,
            "folder_name": self.folder_entry.get().strip() or None,
            "StartURL": self.url_entry.get().strip() or None,
            "os": self.os_var.get(),
            "osVersion": self.os_version_var.get(),
            "browser": self.browser_var.get(),
            "browserVersion": self.browser_version_var.get(),
            "resolution": self.resolution_var.get(),
            "language": self.language_var.get(),
            "canvas": self.canvas_var.get(),
            "webGLImage": "true" if self.webgl_var.get() else "false",
            "audioContext": "true" if self.audio_var.get() else "false",
            "noiseFont": "true" if self.font_var.get() else "false",
            "proxy": self.proxy_entry.get().strip() or None,
            "command": f"--lang={self.language_var.get().split('-')[0]}"
        }

        os_type = self.os_var.get()
        if os_type == "ios":
            self.result["device_type"] = "iphone"
        elif os_type == "android":
            self.result["device_type"] = "phone"

        self.destroy()


class EditProfileDialog(ctk.CTkToplevel):
    """Modern Edit Profile Dialog"""

    def __init__(self, parent, profile: Dict):
        super().__init__(parent)

        self.profile = profile

        self.title("Chinh sua Profile")
        self.geometry("550x450")
        self.configure(fg_color=COLORS["bg_dark"])
        self.transient(parent)

        self._create_ui()

    def _create_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=SPACING["2xl"], pady=SPACING["xl"])

        ctk.CTkLabel(
            header,
            text="  Chinh sua Profile",
            font=ctk.CTkFont(
                family=FONTS["family"],
                size=FONTS["size_2xl"],
                weight="bold"
            ),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")

        # Form card
        form_card = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=COLORS["border"]
        )
        form_card.pack(fill="x", padx=SPACING["2xl"], pady=SPACING["md"])

        form_inner = ctk.CTkFrame(form_card, fg_color="transparent")
        form_inner.pack(fill="x", padx=SPACING["lg"], pady=SPACING["lg"])

        # Name
        ctk.CTkLabel(
            form_inner,
            text="Ten Profile",
            font=ctk.CTkFont(size=FONTS["size_sm"]),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w")

        self.name_entry = ModernEntry(form_inner)
        self.name_entry.pack(fill="x", pady=(SPACING["xs"], SPACING["md"]))
        self.name_entry.insert(0, self.profile.get('name') or '')

        # Note
        ctk.CTkLabel(
            form_inner,
            text="Ghi chu",
            font=ctk.CTkFont(size=FONTS["size_sm"]),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w")

        self.note_entry = ModernEntry(form_inner)
        self.note_entry.pack(fill="x", pady=(SPACING["xs"], SPACING["md"]))
        self.note_entry.insert(0, self.profile.get('note') or '')

        # Proxy
        ctk.CTkLabel(
            form_inner,
            text="Proxy (Type|IP|Port|User|Pass)",
            font=ctk.CTkFont(size=FONTS["size_sm"]),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w")

        self.proxy_entry = ModernEntry(form_inner, placeholder="HTTP|1.1.1.1|8080|user|pass")
        self.proxy_entry.pack(fill="x", pady=(SPACING["xs"], 0))

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=SPACING["2xl"], pady=SPACING["xl"])

        ModernButton(
            btn_frame,
            text="Luu",
            icon="",
            variant="success",
            command=self._save,
            width=120
        ).pack(side="left", padx=SPACING["xs"])

        ModernButton(
            btn_frame,
            text="Huy",
            variant="secondary",
            command=self.destroy,
            width=100
        ).pack(side="left", padx=SPACING["xs"])

    def _save(self):
        """Save changes"""
        uuid = self.profile.get('uuid')

        new_name = self.name_entry.get()
        if new_name and new_name != self.profile.get('name'):
            api.update_profile_name(uuid, new_name)

        new_note = self.note_entry.get()
        if new_note != self.profile.get('note', ''):
            api.update_profile_note(uuid, new_note)

        self.destroy()
