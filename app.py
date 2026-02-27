"""
Main Application Class for IT Admin Toolkit.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import sys
import os
import ctypes 

from config.colors import COLORS
from ui.styles import setup_styles
from ui.winget_tab import WingetTab
from ui.scripts_tab import ScriptsTab
from ui.choco_tab import ChocoTab  # ADD THIS IMPORT
from utils.powershell import PowerShellRunner
from ui.uninstall_tab import UninstallTab
from utils.winget import WingetManager
from utils.admin import is_admin, restart_as_admin
from ui.logs_tab import LogsTab
from ui.network_tab import NetworkTab
from ui.updates_tab import UpdatesTab 


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class AppInstaller:
    def __init__(self, root):
        self.root = root
        self.root.title("IT Admin Toolkit - Dark Mode")
        self.root.geometry("950x750")
        self.root.minsize(600, 400)
        self.root.resizable(True, True)
        
        # Set window icon
        try:
            icon_path = resource_path('icon.ico')
            self.root.iconbitmap(icon_path)
        except:
            pass
        
        # Check admin status
        self.admin_status = self.is_admin()  # Store as boolean (renamed to avoid shadowing method)
        
        # Update title to show admin status
        if self.admin_status:
            self.root.title("IT Admin Toolkit [Administrator]")
        else:
            self.root.title("IT Admin Toolkit [Limited Mode]")
        
        # Settings
        self.colors = COLORS
        self.debug_mode = tk.BooleanVar(value=False)
        self.log_script_output = tk.BooleanVar(value=True)
        self.debug_mode.trace_add('write', self.toggle_debug_output)
        
        self.root.configure(bg=self.colors['bg'])
        
        # Setup styles
        setup_styles(self.colors)
        
        # Initialize utilities
        self.powershell = PowerShellRunner(self)
        self.winget = WingetManager(self)
        
        # Build UI
        self.create_notebook()
        
        # Log startup
        if self.admin_status:
            self.log("🚀 GUI loaded successfully! (Running as Administrator)")
        else:
            self.log("🚀 GUI loaded (Limited Mode - Some features may not work)")
            self.log("⚠️ Click 'Run as Admin' for full functionality")
    
    def is_admin(self):
        """Check if running as administrator."""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
        
    def create_notebook(self):
        """Create the main tabbed interface."""
        # Main container
        main_container = ttk.Frame(self.root, style='DarkBg.TFrame', padding="10")
        main_container.pack(fill=tk.BOTH, expand=True)
        main_container.columnconfigure(0, weight=1)
        main_container.rowconfigure(1, weight=1)
        
        # Header with checkboxes and admin button
        header_frame = ttk.Frame(main_container, style='DarkBg.TFrame')
        header_frame.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        
        # Title with admin indicator
        title_text = "🛠️ IT Admin Toolkit"
        if self.admin_status:
            title_text += " 🛡️"
        
        title = ttk.Label(header_frame, text=title_text, style='Dark.Title.TLabel')
        title.pack(side=tk.LEFT)
        
        # Admin status indicator and button
        if self.admin_status:
            admin_label = ttk.Label(header_frame, text="✅ Administrator", 
                                   foreground='#4ec64b', background=self.colors['bg'],
                                   font=('Segoe UI', 9, 'bold'))
            admin_label.pack(side=tk.RIGHT, padx=(10, 0))
        else:
            admin_btn = ttk.Button(header_frame, text="🛡️ Run as Admin", 
                                  style='Danger.TButton', command=self._request_admin)
            admin_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        ttk.Checkbutton(header_frame, text="🐛 Debug Mode", variable=self.debug_mode, 
                       style='Dark.TCheckbutton').pack(side=tk.RIGHT)
        
        ttk.Checkbutton(header_frame, text="📋 Log Script Output", variable=self.log_script_output, 
                       style='Dark.TCheckbutton').pack(side=tk.RIGHT, padx=(0, 15))
        
        # Paned window for resizable sections
        self.main_paned = ttk.PanedWindow(main_container, orient=tk.VERTICAL)
        self.main_paned.grid(row=1, column=0, sticky='nsew')
        
        # Top pane: Notebook (tabs)
        notebook_frame = ttk.Frame(self.main_paned, style='DarkBg.TFrame')
        
        self.notebook = ttk.Notebook(notebook_frame, style='Dark.TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        ###### Create tab frames (Edit This when Adding new tab)
        winget_frame = ttk.Frame(self.notebook, style='DarkBg.TFrame')
        scripts_frame = ttk.Frame(self.notebook, style='DarkBg.TFrame')
        choco_frame = ttk.Frame(self.notebook, style='DarkBg.TFrame')  # ADD THIS
        uninstall_frame = ttk.Frame(self.notebook, style='DarkBg.TFrame')
        logs_frame = ttk.Frame(self.notebook, style='DarkBg.TFrame')
        network_frame = ttk.Frame(self.notebook, style='DarkBg.TFrame')
        updates_frame = ttk.Frame(self.notebook, style='DarkBg.TFrame')

        
        ###### Add tabs to notebook (Edit This when Adding new tab)
        self.notebook.add(winget_frame, text='📦 Winget')
        self.notebook.add(choco_frame, text='🍫 Chocolatey')  # ADD THIS
        self.notebook.add(scripts_frame, text='⚡ PowerShell Scripts')
        self.notebook.add(uninstall_frame, text='🗑️ Uninstall & Cleanup')
        self.notebook.add(logs_frame, text='📊 Logs')
        self.notebook.add(network_frame, text='🌐 Network')
        self.notebook.add(updates_frame, text="🔄 Updates")
        
        ###### Build each tab (Edit This when Adding new tab)
        self.winget_tab = WingetTab(winget_frame, self)
        self.choco_tab = ChocoTab(choco_frame, self)  # ADD THIS
        self.scripts_tab = ScriptsTab(scripts_frame, self)
        self.uninstall_tab = UninstallTab(uninstall_frame, self)
        self.logs_tab = LogsTab(logs_frame, self)
        self.network_tab = NetworkTab(network_frame, self)
        self.updates_tab = UpdatesTab(updates_frame, self)
        
        # Add notebook frame to paned window
        self.main_paned.add(notebook_frame, weight=3)
        
        # Bottom pane: Logs (resizable)
        self.create_resizable_logs(self.main_paned)
    
    def _request_admin(self):
        """Request to restart with admin privileges."""
        result = messagebox.askyesno(
            "Administrator Required",
            "Some features require administrator privileges.\n\n"
            "Do you want to restart the application as Administrator?\n\n"
            "(You may see a UAC prompt)",
            icon='question'
        )
        
        if result:
            self.log("🛡️ Restarting as Administrator...")
            self.root.update()
            if not restart_as_admin():
                messagebox.showerror(
                    "Error",
                    "Failed to restart as Administrator.\n"
                    "Try right-clicking the app and selecting 'Run as administrator'."
                )
    
    def create_resizable_logs(self, parent_paned):
        """Create the resizable debug and activity log sections."""
        logs_container = ttk.Frame(parent_paned, style='DarkBg.TFrame')
        
        # Debug output (hidden by default)
        self.debug_frame = ttk.LabelFrame(logs_container, text="🐛 Debug Output", 
                                         padding="5", style='Dark.TLabelframe')
        
        self.debug_text = tk.Text(self.debug_frame, height=5, bg='#1a1a1a', fg='#00ff00', 
                                 font=('Consolas', 9), state=tk.NORMAL)
        debug_scroll = ttk.Scrollbar(self.debug_frame, orient=tk.VERTICAL, 
                                    command=self.debug_text.yview)
        self.debug_text.config(yscrollcommand=debug_scroll.set)
        self.debug_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        debug_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Activity Log (always visible)
        log_frame = ttk.LabelFrame(logs_container, text="📋 Activity Log (drag edge to resize)", 
                                  padding="5", style='Dark.TLabelframe')
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_frame, height=4, bg=self.colors['bg'], fg=self.colors['fg'], 
                               font=('Consolas', 9), state=tk.NORMAL, wrap=tk.WORD)
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=log_scroll.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        parent_paned.add(logs_container, weight=1)
    
    def toggle_debug_output(self, *args):
        """Show/hide debug output based on checkbox state."""
        if self.debug_mode.get():
            self.debug_frame.pack(fill=tk.X, pady=(0, 5), before=self.debug_frame.master.winfo_children()[-1])
        else:
            self.debug_frame.pack_forget()
    
    def debug_log(self, message):
        """Log a debug message."""
        if self.debug_mode.get():
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.debug_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.debug_text.see(tk.END)
            self.root.update_idletasks()
    
    def log(self, message):
        """Log a message to the activity log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()