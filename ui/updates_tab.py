"""
Update Tab - Windows Update integration using WUA COM API.
Replaces the old update tab with full search/install/feature-update functionality.
"""

import os
import sys
import queue
import logging
import ctypes
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List

logger = logging.getLogger(__name__)

# Try importing the update services
try:
    from services.update_service import UpdateService
    from services.install_service import InstallService
    from services.feature_update_service import FeatureUpdateService
    from services.reboot_service import RebootService
    from models.update_info import UpdateInfo
    HAS_UPDATE_SERVICES = True
except ImportError as e:
    logger.warning(f"Update services not available: {e}")
    HAS_UPDATE_SERVICES = False

_POLL_INTERVAL_MS = 50

class UpdatesTab(ttk.Frame):
    """Windows Update tab with search, install, and feature update capabilities."""

    def __init__(self, parent, app_instance):
        super().__init__(parent, style='Dark.TFrame')
        self.app = app_instance
        self._queue = queue.Queue()
        self._updates: List = []
        self._is_admin = self._check_admin()

        self._create_widgets()
        self._poll_queue()
        self.pack(fill=tk.BOTH, expand=True) 

    # ─── Admin Check ─────────────────────────────────────────────
    @staticmethod
    def _check_admin() -> bool:
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False

    # ─── UI Construction ─────────────────────────────────────────
    def _create_widgets(self):
        """Build the update tab UI."""
        # Top toolbar
        toolbar = ttk.Frame(self, style='Dark.TFrame')
        toolbar.pack(fill=tk.X, padx=10, pady=(10, 5))

        self.btn_check = ttk.Button(
            toolbar, text="🔍 Check for Updates", style='Dark.TButton',
            command=self._on_check_updates
        )
        self.btn_check.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6)

        self.btn_install_selected = ttk.Button(
            toolbar, text="📥 Install Selected", style='Dark.TButton',
            command=self._on_install_selected, state="disabled"
        )
        self.btn_install_selected.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_install_all = ttk.Button(
            toolbar, text="📦 Install All", style='Dark.TButton',
            command=self._on_install_all, state="disabled"
        )
        self.btn_install_all.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6)

        self.btn_feature_update = ttk.Button(
            toolbar, text="⬆️ Feature Update", style='Dark.TButton',
            command=self._on_feature_update
        )
        self.btn_feature_update.pack(side=tk.LEFT, padx=(0, 5))

        # Reboot checkbox
        self.reboot_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            toolbar, text="Reboot After Install",
            variable=self.reboot_var, style='Dark.TCheckbutton'
        ).pack(side=tk.LEFT, padx=(10, 0))


        # ─── Version Info Bar ─────────────────────────────────────
        if HAS_UPDATE_SERVICES:
            info_frame = ttk.Frame(self, style='Dark.TFrame')
            info_frame.pack(fill=tk.X, padx=10, pady=(5, 0))
            try:
                ver_info = FeatureUpdateService.get_current_version_info()
                ver_text = (f"Windows {ver_info.get('major_version', '?')} | "
                           f"Version: {ver_info.get('display_version', '?')} | "
                           f"Build: {ver_info.get('full_build', '?')}")
                ttk.Label(info_frame, text=ver_text,
                         style='Dark.TLabel', foreground='#8be9fd').pack(side=tk.LEFT)
            except Exception:
                pass

        # ─── Update List (Treeview) ──────────────────────────────
        list_frame = ttk.Frame(self, style='Dark.TFrame')
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ("title", "kb", "size", "severity")
        self.tree = ttk.Treeview(
            list_frame, columns=columns, show="tree headings",
            selectmode="extended", style='Dark.Treeview'
        )
        self.tree.heading("#0", text="✓")
        self.tree.column("#0", width=40, stretch=False)
        self.tree.heading("title", text="Update Title")
        self.tree.column("title", width=500)
        self.tree.heading("kb", text="KB Article")
        self.tree.column("kb", width=100)
        self.tree.heading("size", text="Size")
        self.tree.column("size", width=80)
        self.tree.heading("severity", text="Severity")
        self.tree.column("severity", width=100)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Checkboxes via tags
        self.tree.tag_configure("checked", foreground="#50fa7b")
        self.tree.tag_configure("unchecked", foreground="#f8f8f2")
        self.tree.bind("<Button-1>", self._on_tree_click)

        # Track checked items
        self._checked_items = set()

        # ─── Log Panel ────────────────────────────────────────────
        log_frame = ttk.LabelFrame(self, text="Update Log", 
                                   padding="5", style='Dark.TLabelframe')
        log_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.log_text = tk.Text(
            log_frame, height=8, wrap=tk.WORD,
            bg='#1e1e2e', fg='#cdd6f4', font=('Consolas', 9),
            state=tk.DISABLED, relief=tk.FLAT
        )
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # ─── Status Bar ──────────────────────────────────────────
        self.status_var = tk.StringVar(value="Ready — click 'Check for Updates' to begin")
        status_bar = ttk.Label(self, textvariable=self.status_var,
                              style='Dark.TLabel', foreground='#a6adc8')
        status_bar.pack(fill=tk.X, padx=10, pady=(0, 5))


    # ─── Tree Checkbox Toggle ────────────────────────────────────
    def _on_tree_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region == "tree":
            item = self.tree.identify_row(event.y)
            if item:
                if item in self._checked_items:
                    self._checked_items.discard(item)
                    self.tree.item(item, text="☐", tags=("unchecked",))
                else:
                    self._checked_items.add(item)
                    self.tree.item(item, text="☑", tags=("checked",))
                self._update_install_buttons()

    def _update_install_buttons(self):
        has_checked = len(self._checked_items) > 0
        has_updates = len(self._updates) > 0
        self.btn_install_selected.configure(state="normal" if has_checked else "disabled")
        self.btn_install_all.configure(state="normal" if has_updates else "disabled")

    # ─── Logging ─────────────────────────────────────────────────
    def _log(self, message, level="info"):
        self.log_text.configure(state=tk.NORMAL)
        prefix = {"info": "ℹ️", "step": "▶️", "success": "✅", 
                  "error": "❌", "warning": "⚠️"}.get(level, "•")
        self.log_text.insert(tk.END, f"{prefix} {message}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    # ─── Queue Polling ───────────────────────────────────────────
    def _poll_queue(self):
        try:
            while True:
                msg_type, data = self._queue.get_nowait()
                if msg_type == "progress":
                    self._log(data[0], data[1])
                    self.status_var.set(data[0])
                elif msg_type == "search_done":
                    self._on_search_complete(data)
                elif msg_type == "install_done":
                    self._on_install_complete(data)
                elif msg_type == "error":
                    self._log(str(data), "error")
                    self.status_var.set(f"Error: {data}")
                    self._set_buttons_enabled(True)
        except queue.Empty:
            pass
        self.after(_POLL_INTERVAL_MS, self._poll_queue)

    # ─── Button Handlers ─────────────────────────────────────────
    def _on_check_updates(self):
        if not HAS_UPDATE_SERVICES:
            messagebox.showerror("Error", 
                "Update services not available.\n"
                "Install: pip install pywin32")
            return

        self._set_buttons_enabled(False)
        self.tree.delete(*self.tree.get_children())
        self._checked_items.clear()
        self._updates.clear()
        self._log("Starting update search...", "step")

        def _search():
            try:
                results = UpdateService.search_missing_updates(
                    progress_callback=lambda msg, lvl: self._queue.put(("progress", (msg, lvl)))
                )
                self._queue.put(("search_done", results))
            except Exception as e:
                self._queue.put(("error", str(e)))

        threading.Thread(target=_search, daemon=True).start()

    def _on_search_complete(self, updates):
        self._updates = updates
        self.tree.delete(*self.tree.get_children())
        self._checked_items.clear()

        if not updates:
            self._log("✅ Your system is up to date!", "success")
            self.status_var.set("No updates available")
        else:
            for i, upd in enumerate(updates):
                item_id = self.tree.insert(
                    "", tk.END,
                    text="☐",
                    values=(
                        upd.title,
                        upd.kb_article_ids if hasattr(upd, 'kb_article_ids') else "",
                        self._format_size(upd.size if hasattr(upd, 'size') else 0),
                        upd.severity if hasattr(upd, 'severity') else ""
                    ),
                    tags=("unchecked",)
                )
            self._log(f"Found {len(updates)} update(s)", "success")
            self.status_var.set(f"{len(updates)} update(s) available")

        self._set_buttons_enabled(True)
        self._update_install_buttons()

    def _on_install_selected(self):
        if not self._checked_items:
            return
        indices = []
        all_items = self.tree.get_children()
        for i, item in enumerate(all_items):
            if item in self._checked_items:
                indices.append(i)
        selected_updates = [self._updates[i] for i in indices if i < len(self._updates)]
        self._do_install(selected_updates)

    def _on_install_all(self):
        self._do_install(self._updates)

    def _do_install(self, updates_to_install):
        if not updates_to_install:
            return
        if not self._is_admin:
            messagebox.showwarning("Admin Required",
                "Installing updates requires Administrator privileges.\n"
                "Please restart the app as Administrator.")
            return

        self._set_buttons_enabled(False)
        self._log(f"Installing {len(updates_to_install)} update(s)...", "step")

        def _install():
            try:
                # Extract titles — InstallService expects a list of title strings
                titles = [upd.title for upd in updates_to_install]
                result = InstallService.download_and_install(
                    titles,
                    progress_callback=lambda msg, lvl: self._queue.put(("progress", (msg, lvl)))
                )
                self._queue.put(("install_done", result))
            except Exception as e:
                self._queue.put(("error", str(e)))

        threading.Thread(target=_install, daemon=True).start()


    def _on_install_complete(self, result):
        self._set_buttons_enabled(True)
        self._log("Installation complete!", "success")
        self.status_var.set("Installation complete")

        if self.reboot_var.get():
            if messagebox.askyesno("Reboot", "Updates installed. Reboot now?"):
                RebootService.reboot()

    def _on_feature_update(self):
        if not HAS_UPDATE_SERVICES:
            return
        try:
            ver_info = FeatureUpdateService.get_current_version_info()
            msg = (f"Current: Windows {ver_info.get('major_version')} "
                   f"v{ver_info.get('display_version')} "
                   f"(Build {ver_info.get('full_build')})\n\n"
                   f"This will download and run the Windows Update Assistant.\n"
                   f"Continue?")
            if messagebox.askyesno("Feature Update", msg):
                self._log("Launching Windows Update Assistant...", "step")
                threading.Thread(
                    target=self._run_feature_update, daemon=True
                ).start()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _run_feature_update(self):
        try:
            self._queue.put(("progress", ("Downloading Update Assistant...", "step")))
            FeatureUpdateService.download_and_run_assistant(
                progress_callback=lambda msg, lvl: self._queue.put(("progress", (msg, lvl)))
            )
            self._queue.put(("progress", ("Feature Update Assistant launched.", "success")))
        except Exception as e:
            self._queue.put(("error", str(e)))


    # ─── Helpers ─────────────────────────────────────────────────
    def _set_buttons_enabled(self, enabled):
        state = "normal" if enabled else "disabled"
        self.btn_check.configure(state=state)
        self.btn_feature_update.configure(state=state)
        if not enabled:
            self.btn_install_selected.configure(state="disabled")
            self.btn_install_all.configure(state="disabled")

    @staticmethod
    def _format_size(size_bytes):
        if not size_bytes:
            return ""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024*1024):.1f} MB"
        else:
            return f"{size_bytes / (1024*1024*1024):.2f} GB"