"""
Main Application Class for IT Admin Toolkit.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import sys
import os
import ctypes
import time

from config.colors import COLORS
from ui.styles import setup_styles
from ui.winget_tab import WingetTab
from ui.scripts_tab import ScriptsTab
from ui.choco_tab import ChocoTab
from utils.powershell import PowerShellRunner
from ui.uninstall_tab import UninstallTab
from utils.winget import WingetManager
from utils.admin import is_admin, restart_as_admin
from ui.logs_tab import LogsTab
from ui.network_tab import NetworkTab
from ui.updates_tab import UpdatesTab
from version import VERSION
from ui.health_dashboard_tab import HealthDashboardTab
from ui.bsod_tab import BSODTab
from ui.eventlog_tab import EventLogTab
from ui.setup_checklist_tab import SetupChecklistTab
from ui.bloatware_tab import BloatwareTab
from ui.printer_tab import PrinterTab
from ui.bitlocker_tab import BitLockerTab


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class AppInstaller:
    def __init__(self, root):
        self.root = root
        self.root.title(f"IT Admin Toolkit v{VERSION}")
        self.root.geometry("950x750")
        self.root.minsize(600, 500)
        self.root.resizable(True, True)
        self._set_icon()
        self.admin_status = self.is_admin()
        if self.admin_status:
            self.root.title(f"IT Admin Toolkit v{VERSION} [Administrator]")
        else:
            self.root.title(f"IT Admin Toolkit v{VERSION} [Limited Mode]")
        self.colors = COLORS
        self.debug_mode = tk.BooleanVar(value=False)
        self.log_script_output = tk.BooleanVar(value=True)
        self.debug_mode.trace_add('write', self.toggle_debug_output)
        self.root.configure(bg=self.colors['bg'])
        setup_styles(self.colors)
        self.powershell = PowerShellRunner(self)
        self.winget = WingetManager(self)
        self.create_notebook()
        if self.admin_status:
            self.log("🚀 GUI loaded successfully! (Running as Administrator)")
        else:
            self.log("🚀 GUI loaded (Limited Mode - Some features may not work)")
            self.log("⚠️ Click 'Run as Admin' for full functionality")
        self.root.bind_all("<MouseWheel>", self._global_mousewheel)
        self.root.bind_all("<Button-4>", self._global_mousewheel)
        self.root.bind_all("<Button-5>", self._global_mousewheel)

    def is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    def _global_mousewheel(self, event):
        widget = event.widget
        while widget:
            if isinstance(widget, tk.Canvas):
                if event.num == 5 or event.delta < 0:
                    widget.yview_scroll(3, "units")
                elif event.num == 4 or event.delta > 0:
                    widget.yview_scroll(-3, "units")
                return "break"
            widget = widget.master
        return None

    def create_notebook(self):
        """Create the main tabbed interface with grouped sub-tabs."""
        main_container = ttk.Frame(self.root, style='DarkBg.TFrame', padding="10")
        main_container.pack(fill=tk.BOTH, expand=True)
        main_container.columnconfigure(0, weight=1)
        main_container.rowconfigure(1, weight=1)

        # Header
        header_frame = ttk.Frame(main_container, style='DarkBg.TFrame')
        header_frame.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        title_text = "🛠️ IT Admin Toolkit"
        if self.admin_status:
            title_text += " 🛡️"
        title = ttk.Label(header_frame, text=title_text, style='Dark.Title.TLabel')
        title.pack(side=tk.LEFT)
        if self.admin_status:
            admin_label = ttk.Label(header_frame, text="✅ Administrator",
                                   foreground='#4ec64b', background=self.colors['bg'],
                                   font=('Segoe UI', 9, 'bold'))
            admin_label.pack(side=tk.RIGHT, padx=(10, 0))
        else:
            admin_btn = ttk.Button(header_frame, text="🛡️ Run as Admin",
                                  style='Danger.TButton', command=self._request_admin)
            admin_btn.pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Checkbutton(header_frame, text="🐛 Debug", variable=self.debug_mode,
                       style='Dark.TCheckbutton').pack(side=tk.RIGHT)
        ttk.Checkbutton(header_frame, text="📋 Log Output", variable=self.log_script_output,
                       style='Dark.TCheckbutton').pack(side=tk.RIGHT, padx=(0, 15))

        # Paned window
        self.main_paned = tk.PanedWindow(main_container, orient=tk.VERTICAL,
                                         sashwidth=6, sashrelief=tk.RAISED,
                                         bg=self.colors['bg'])
        self.main_paned.grid(row=1, column=0, sticky='nsew')

        notebook_frame = ttk.Frame(self.main_paned, style='DarkBg.TFrame')
        self.notebook = ttk.Notebook(notebook_frame, style='Dark.TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # === TAB 1: Dashboard ===
        dashboard_frame = ttk.Frame(self.notebook, style='DarkBg.TFrame')
        self.notebook.add(dashboard_frame, text='  📊 Dashboard  ')
        self.health_tab = HealthDashboardTab(dashboard_frame, self)

        # === TAB 2: Setup ===
        setup_frame = ttk.Frame(self.notebook, style='DarkBg.TFrame')
        self.notebook.add(setup_frame, text='  📋 Setup  ')
        self.setup_tab = SetupChecklistTab(setup_frame, self)

        # === TAB 3: Install / Remove ===
        install_frame = ttk.Frame(self.notebook, style='DarkBg.TFrame')
        self.notebook.add(install_frame, text='  📦 Install / Remove  ')
        install_notebook = ttk.Notebook(install_frame, style='Dark.TNotebook')
        install_notebook.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        winget_frame = ttk.Frame(install_notebook, style='DarkBg.TFrame')
        choco_frame = ttk.Frame(install_notebook, style='DarkBg.TFrame')
        bloatware_frame = ttk.Frame(install_notebook, style='DarkBg.TFrame')
        uninstall_frame = ttk.Frame(install_notebook, style='DarkBg.TFrame')
        install_notebook.add(winget_frame, text='  Winget  ')
        install_notebook.add(choco_frame, text='  Chocolatey  ')
        install_notebook.add(bloatware_frame, text='  Bloatware  ')
        install_notebook.add(uninstall_frame, text='  Uninstall  ')
        self.winget_tab = WingetTab(winget_frame, self)
        self.choco_tab = ChocoTab(choco_frame, self)
        self.bloatware_tab = BloatwareTab(bloatware_frame, self)
        self.uninstall_tab = UninstallTab(uninstall_frame, self)

        # === TAB 4: Tools ===
        tools_frame = ttk.Frame(self.notebook, style='DarkBg.TFrame')
        self.notebook.add(tools_frame, text='  ⚡ Tools  ')
        tools_notebook = ttk.Notebook(tools_frame, style='Dark.TNotebook')
        tools_notebook.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        scripts_frame = ttk.Frame(tools_notebook, style='DarkBg.TFrame')
        network_frame = ttk.Frame(tools_notebook, style='DarkBg.TFrame')
        tools_notebook.add(scripts_frame, text='  PowerShell Scripts  ')
        tools_notebook.add(network_frame, text='  Network  ')
        self.scripts_tab = ScriptsTab(scripts_frame, self)
        self.network_tab = NetworkTab(network_frame, self)

        # === TAB 5: System ===
        system_frame = ttk.Frame(self.notebook, style='DarkBg.TFrame')
        self.notebook.add(system_frame, text='  🔧 System  ')
        system_notebook = ttk.Notebook(system_frame, style='Dark.TNotebook')
        system_notebook.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        updates_frame = ttk.Frame(system_notebook, style='DarkBg.TFrame')
        printer_frame = ttk.Frame(system_notebook, style='DarkBg.TFrame')
        bitlocker_frame = ttk.Frame(system_notebook, style='DarkBg.TFrame')
        system_notebook.add(updates_frame, text='  Updates  ')
        system_notebook.add(printer_frame, text='  Printers  ')
        system_notebook.add(bitlocker_frame, text='  BitLocker  ')
        self.updates_tab = UpdatesTab(updates_frame, self)
        self.printer_tab = PrinterTab(printer_frame, self)
        self.bitlocker_tab = BitLockerTab(bitlocker_frame, self)

        # === TAB 6: Diagnostics ===
        diag_frame = ttk.Frame(self.notebook, style='DarkBg.TFrame')
        self.notebook.add(diag_frame, text='  🔍 Diagnostics  ')
        diag_notebook = ttk.Notebook(diag_frame, style='Dark.TNotebook')
        diag_notebook.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        events_frame = ttk.Frame(diag_notebook, style='DarkBg.TFrame')
        crashes_frame = ttk.Frame(diag_notebook, style='DarkBg.TFrame')
        logs_frame = ttk.Frame(diag_notebook, style='DarkBg.TFrame')
        diag_notebook.add(events_frame, text='  Event Log  ')
        diag_notebook.add(crashes_frame, text='  Crashes  ')
        diag_notebook.add(logs_frame, text='  App Logs  ')
        self.eventlog_tab = EventLogTab(events_frame, self)
        self.bsod_tab = BSODTab(crashes_frame, self)
        self.logs_tab = LogsTab(logs_frame, self)

        # Compatibility
        self.installer_tab = self.winget_tab

        # Add to paned window
        self.main_paned.add(notebook_frame, minsize=200, stretch="always")
        self.create_resizable_logs(self.main_paned)

    def _request_admin(self):
        result = messagebox.askyesno(
            "Administrator Required",
            "Some features require administrator privileges.\n\n"
            "Do you want to restart the application as Administrator?\n\n"
            "(You may see a UAC prompt)", icon='question')
        if result:
            self.log("🛡️ Restarting as Administrator...")
            self.root.update()
            if not restart_as_admin():
                messagebox.showerror("Error",
                    "Failed to restart as Administrator.\n"
                    "Try right-clicking the app and selecting 'Run as administrator'.")

    def create_resizable_logs(self, parent_paned):
        logs_container = ttk.Frame(parent_paned, style='DarkBg.TFrame')
        self.debug_frame = ttk.LabelFrame(logs_container, text="🐛 Debug Output",
                                         padding="5", style='Dark.TLabelframe')
        self.debug_text = tk.Text(self.debug_frame, height=5, bg='#1a1a1a', fg='#00ff00',
                                 font=('Consolas', 9), state=tk.NORMAL)
        debug_scroll = ttk.Scrollbar(self.debug_frame, orient=tk.VERTICAL,
                                    command=self.debug_text.yview)
        self.debug_text.config(yscrollcommand=debug_scroll.set)
        self.debug_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        debug_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        log_frame = ttk.LabelFrame(logs_container, text="📋 Activity Log",
                                  padding="5", style='Dark.TLabelframe')
        log_frame.pack(fill=tk.BOTH, expand=True)
        log_btn_frame = ttk.Frame(log_frame, style='Dark.TFrame')
        log_btn_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(log_btn_frame, text="🗑️ Clear", style='Dark.TButton',
                  command=self._clear_activity_log).pack(side=tk.LEFT, padx=(0, 5))
        self._log_collapsed = False
        self._log_toggle_btn = ttk.Button(log_btn_frame, text="▼ Collapse",
                                          style='Dark.TButton', command=self._toggle_log)
        self._log_toggle_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.test_log_btn = ttk.Button(log_btn_frame, text="🧪 TEST", style='Dark.TButton',
                                       command=self.run_log_tests)
        def toggle_test_btn(*args):
            if self.debug_mode.get():
                self.test_log_btn.pack(side=tk.LEFT, padx=(0, 5))
            else:
                self.test_log_btn.pack_forget()
        self.debug_mode.trace_add('write', toggle_test_btn)

        self._log_text_frame = ttk.Frame(log_frame, style='Dark.TFrame')
        self._log_text_frame.pack(fill=tk.BOTH, expand=True)
        self.log_text = tk.Text(self._log_text_frame, height=4, bg=self.colors['bg'],
                               fg=self.colors['fg'], font=('Consolas', 9),
                               state=tk.NORMAL, wrap=tk.WORD)
        log_scroll = ttk.Scrollbar(self._log_text_frame, orient=tk.VERTICAL,
                                  command=self.log_text.yview)
        self.log_text.config(yscrollcommand=log_scroll.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        parent_paned.add(logs_container, minsize=60, stretch="always")

    def _toggle_log(self):
        if self._log_collapsed:
            self._log_text_frame.pack(fill=tk.BOTH, expand=True)
            self._log_toggle_btn.configure(text="▼ Collapse")
            self._log_collapsed = False
        else:
            self._log_text_frame.pack_forget()
            self._log_toggle_btn.configure(text="▲ Expand")
            self._log_collapsed = True

    @staticmethod
    def create_scrollable_frame(parent):
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        scrollable = ttk.Frame(canvas, style='DarkBg.TFrame')
        scrollable.bind("<Configure>",
                       lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.configure(bg=parent.cget('background') if parent.cget('background') != 'SystemButtonFace' else '#1e1e2e')
        return scrollable

    def _clear_activity_log(self):
        self.log_text.delete('1.0', tk.END)

    def toggle_debug_output(self, *args):
        if self.debug_mode.get():
            self.debug_frame.pack(fill=tk.X, pady=(0, 5), before=self.debug_frame.master.winfo_children()[-1])
        else:
            self.debug_frame.pack_forget()

    def debug_log(self, message):
        if self.debug_mode.get():
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.debug_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.debug_text.see(tk.END)
            self.root.update_idletasks()

    def _set_icon(self):
        icon_path = resource_path('icon.ico')
        try:
            self.root.iconbitmap(icon_path)
        except:
            pass
        try:
            from PIL import Image, ImageTk
            img = Image.open(icon_path)
            photos = []
            for size in [16, 32, 48, 64, 128, 256]:
                resized = img.resize((size, size), Image.LANCZOS)
                photo = ImageTk.PhotoImage(resized)
                photos.append(photo)
            self.root.wm_iconphoto(True, *photos)
            self._icon_refs = photos
        except ImportError:
            try:
                png_path = icon_path.replace('.ico', '.png')
                if os.path.exists(png_path):
                    photo = tk.PhotoImage(file=png_path)
                    self.root.wm_iconphoto(True, photo)
                    self._icon_ref = photo
            except:
                pass
        except:
            pass

    # ==========================================
    # Centralized Logging Methods
    # ==========================================

    def log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)

    def log_error(self, message, hint=None):
        self.log(f"❌ {message}")
        if hint:
            self.log(f"   💡 {hint}")
        if not self.debug_mode.get():
            self.log(f"   🔧 Enable Debug Mode for more details")

    def log_warning(self, message, hint=None):
        self.log(f"⚠️ {message}")
        if hint:
            self.log(f"   💡 {hint}")

    def log_success(self, message):
        self.log(f"✅ {message}")

    # ==========================================
    # Test Method
    # ==========================================

    def run_log_tests(self):
        import threading
        def _test():
            self.root.after(0, lambda: self.log("🧪 Running log tests..."))
            time.sleep(0.3)
            self.root.after(0, lambda: self.log("📋 Normal log message"))
            time.sleep(0.1)
            self.root.after(0, lambda: self.log_success("Success message"))
            time.sleep(0.1)
            self.root.after(0, lambda: self.log_warning("Warning message", "Hint text"))
            time.sleep(0.1)
            self.root.after(0, lambda: self.log_error("Error message", "Hint text"))
            time.sleep(0.1)
            self.root.after(0, lambda: self.log("🧪 Test complete"))
        threading.Thread(target=_test, daemon=True).start()