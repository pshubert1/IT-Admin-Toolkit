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
        self.root.title(f"IT Admin Toolkit v{VERSION}")
        self.root.geometry("950x750")
        self.root.minsize(600, 400)
        self.root.resizable(True, True)
        
        # Set window icon
        self._set_icon()
        
        # Check admin status
        self.admin_status = self.is_admin()
        
        # Update title to show admin status
        if self.admin_status:
            self.root.title(f"IT Admin Toolkit v{VERSION} [Administrator]")
        else:
            self.root.title(f"IT Admin Toolkit v{VERSION} [Limited Mode]")
        
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
        
        # Global mousewheel scrolling for all tabs
        self.root.bind_all("<MouseWheel>", self._global_mousewheel)
        self.root.bind_all("<Button-4>", self._global_mousewheel)
        self.root.bind_all("<Button-5>", self._global_mousewheel)
    
    def is_admin(self):
        """Check if running as administrator."""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    
    def _global_mousewheel(self, event):
        """Handle mousewheel scrolling for any canvas under the cursor."""
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
        
        # Create tab frames
        winget_frame = ttk.Frame(self.notebook, style='DarkBg.TFrame')
        scripts_frame = ttk.Frame(self.notebook, style='DarkBg.TFrame')
        choco_frame = ttk.Frame(self.notebook, style='DarkBg.TFrame')
        uninstall_frame = ttk.Frame(self.notebook, style='DarkBg.TFrame')
        logs_frame = ttk.Frame(self.notebook, style='DarkBg.TFrame')
        network_frame = ttk.Frame(self.notebook, style='DarkBg.TFrame')
        updates_frame = ttk.Frame(self.notebook, style='DarkBg.TFrame')
        
        # Add tabs to notebook
        self.notebook.add(winget_frame, text='📦 Winget')
        self.notebook.add(choco_frame, text='🍫 Chocolatey')
        self.notebook.add(scripts_frame, text='⚡ PowerShell Scripts')
        self.notebook.add(uninstall_frame, text='🗑️ Uninstall & Cleanup')
        self.notebook.add(logs_frame, text='📊 Logs')
        self.notebook.add(network_frame, text='🌐 Network')
        self.notebook.add(updates_frame, text="🔄 Updates")
        
        # Build each tab
        self.winget_tab = WingetTab(winget_frame, self)
        self.choco_tab = ChocoTab(choco_frame, self)
        self.scripts_tab = ScriptsTab(scripts_frame, self)
        self.uninstall_tab = UninstallTab(uninstall_frame, self)
        self.logs_tab = LogsTab(logs_frame, self)
        self.network_tab = NetworkTab(network_frame, self)
        self.updates_tab = UpdatesTab(updates_frame, self)
        
        # Also store as installer_tab for WingetManager compatibility
        self.installer_tab = self.winget_tab
        
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
        
        # Button row inside the log frame
        log_btn_frame = ttk.Frame(log_frame, style='Dark.TFrame')
        log_btn_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(log_btn_frame, text="🗑️ Clear Log", style='Dark.TButton',
                  command=self._clear_activity_log).pack(side=tk.LEFT, padx=(0, 5))
        
        # Test button - only visible in debug mode
        self.test_log_btn = ttk.Button(log_btn_frame, text="🧪 TEST LOGS", style='Dark.TButton',
                                       command=self.run_log_tests)
        
        def toggle_test_btn(*args):
            if self.debug_mode.get():
                self.test_log_btn.pack(side=tk.LEFT, padx=(0, 5))
            else:
                self.test_log_btn.pack_forget()
        
        self.debug_mode.trace_add('write', toggle_test_btn)
        
        # Activity log text widget
        self.log_text = tk.Text(log_frame, height=4, bg=self.colors['bg'], fg=self.colors['fg'], 
                               font=('Consolas', 9), state=tk.NORMAL, wrap=tk.WORD)
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=log_scroll.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        parent_paned.add(logs_container, weight=1)
    
    def _clear_activity_log(self):
        """Clear the activity log."""
        self.log_text.delete('1.0', tk.END)
    
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
            
    def _set_icon(self):
        """Set window icon for titlebar AND taskbar."""
        icon_path = resource_path('icon.ico')
        
        # Method 1: iconbitmap (titlebar)
        try:
            self.root.iconbitmap(icon_path)
        except:
            pass
        
        # Method 2: wm_iconphoto (taskbar) — needs PhotoImage
        try:
            from PIL import Image, ImageTk
            img = Image.open(icon_path)
            # Create multiple sizes for best quality
            photos = []
            for size in [16, 32, 48, 64, 128, 256]:
                resized = img.resize((size, size), Image.LANCZOS)
                photo = ImageTk.PhotoImage(resized)
                photos.append(photo)
            
            self.root.wm_iconphoto(True, *photos)
            self._icon_refs = photos  # Prevent garbage collection
        except ImportError:
            # Pillow not installed — try with tkinter's built-in PhotoImage
            try:
                # Only works with .png or .gif, so try .png first
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
        """Log a message to the activity log."""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def log_error(self, message, hint=None):
        """Log an error with standardized formatting."""
        self.log(f"❌🖕 {message}")
        if hint:
            self.log(f"   💡 {hint}")
        if not self.debug_mode.get():
            self.log(f"   🔧 Enable Debug Mode for more details")
    
    def log_warning(self, message, hint=None):
        """Log a warning with standardized formatting."""
        self.log(f"⚠️ 💩 {message}")
        if hint:
            self.log(f"   💡 {hint}")
    
    def log_success(self, message):
        """Log a success message."""
        self.log(f"✅ {message}")
    
    # ==========================================
    # Test Method
    # ==========================================
    
    def run_log_tests(self):
        """Test all centralized logging methods."""
        import threading
        
        def _test():
            tests = [
                ("SECTION", "=== Testing Log Types ==="),
                ("log", "📋 This is a normal log message"),
                ("success", "This is a success message"),
                ("warning", ("This is a warning with no hint", None)),
                ("warning", ("This is a warning WITH a hint", "This is the hint text")),
                ("error", ("This is an error with no hint", None)),
                ("error", ("This is an error WITH a hint", "This is the hint text")),
                
                ("SECTION", "=== Winget Error Codes ==="),
                ("error", ("Chrome - not found in repository", "Verify winget ID: Google.Chrome.Invalid")),
                ("error", ("Process Explorer - no installer for this system", "ID 'Microsoft.Sysinternals.ProcessExplorer' may not support this OS/architecture")),
                ("success", "Firefox already installed"),
                ("log", "⬆️ 7-Zip - already installed, newer version available"),
                ("error", ("VSCode - download failed", "Check internet connection")),
                ("error", ("Notepad++ failed (code 2316632084)", "Try installing with Chocolatey instead")),
                ("warning", ("Teams - silent failed (code 1), retrying...", None)),
                ("error", ("Teams - all install methods failed", "Try installing with Chocolatey instead")),
                ("success", "Teams installed"),
                ("success", "Chrome installed (reboot needed)"),
                ("error", ("winget not found", "Install 'App Installer' from Microsoft Store")),
                ("error", ("Chrome timed out after 300s", "Try installing manually or check internet speed")),
                
                ("SECTION", "=== Chocolatey Errors ==="),
                ("error", ("Chocolatey not installed", "Click 'INSTALL CHOCO' first")),
                ("error", ("Choco check failed: timeout", None)),
                ("error", ("Admin required for Chocolatey install", "Click 'Run as Admin' in the toolbar")),
                ("error", ("git install failed", "Run as admin or check internet")),
                ("success", "Chocolatey v2.4.0 installed"),
                ("success", "git installed"),
                ("warning", ("Enter a search term", None)),
                ("success", "Found 15 packages"),
                
                ("SECTION", "=== PowerShell Errors ==="),
                ("error", ("PowerShell not found", "Verify PowerShell is installed at C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\")),
                ("error", ("Permission denied launching Repair Script", "Try running the app as Administrator")),
                ("error", ("Failed to launch Update Script: [WinError 740]", None)),
                ("success", "Opened Defender Repair in new window"),
                ("success", "Network Diagnostics completed"),
                ("warning", ("Network Diagnostics completed with exit code: 1", "Check script output for details")),
                ("error", ("SFC Scan timed out after 600s", "The script may still be running in the background")),
                
                ("SECTION", "=== Network Errors ==="),
                ("error", ("No active network adapters", "Check if WiFi or Ethernet is enabled")),
                ("error", ("Gateway unreachable", "Check physical network connection")),
                ("error", ("No gateway configured", "Check network adapter settings or DHCP")),
                ("error", ("google.com - DNS resolution FAILED", "Try flushing DNS: ipconfig /flushdns")),
                ("error", ("Port 443 is CLOSED/FILTERED", "A firewall may be blocking this port")),
                ("error", ("Could not resolve server.local", "Check the hostname spelling")),
                ("error", ("Failed to flush DNS", "Run the app as Administrator")),
                ("success", "Internet connectivity: OK"),
                ("success", "Ping successful"),
                ("success", "DNS cache flushed"),
                ("success", "Port 443 is OPEN"),
                ("warning", ("Internet connectivity: Issues detected", "Check network adapter and router")),
                ("warning", ("IP renewal may have issues", "Check if DHCP server is reachable")),
                
                ("SECTION", "=== Device Join Status ==="),
                ("error", ("Failed to run dsregcmd", "Run as Administrator")),
                ("success", "Join Type: Hybrid Joined | Intune: Enrolled"),
                
                ("SECTION", "=== Log Analyzer Errors ==="),
                ("error", ("Invalid archive format: not a gzip file", "Ensure the file is a valid .tar, .tgz, or .tar.gz archive")),
                ("error", ("Permission denied extracting archive", "Try running as Administrator")),
                ("error", ("File not found: C:\\logs\\test.log", "Check the file path and try again")),
                ("error", ("Invalid regex pattern: unbalanced parenthesis", "Check your regex syntax")),
                ("error", ("Event log query timed out", "Try a shorter time range or fewer filters")),
                ("warning", ("No .log files found in archive", None)),
                ("warning", ("No events to export", None)),
                ("success", "Analysis complete!"),
                ("success", "Found 47 events"),
                ("success", "Complete: 150/10000 lines matched"),
                
                ("SECTION", "=== Windows Updates ==="),
                ("error", ("Admin required to install updates", "Click 'Run as Admin' in toolbar")),
                ("error", ("PSWindowsUpdate module not available", "Run: Install-Module PSWindowsUpdate -Force")),
                ("warning", ("Select at least one update", None)),
                ("success", "No updates available"),
                ("success", "3 updates installed"),
                
                ("SECTION", "=== Admin/Permission ==="),
                ("error", ("Admin required for Chocolatey install", "Click 'Run as Admin' in the toolbar")),
                ("error", ("Permission denied writing to: C:\\output.txt", "Try a different save location")),
                ("warning", ("Could not save report: access denied", None)),
            ]
            
            self.root.after(0, lambda: self.log(""))
            self.root.after(0, lambda: self.log("🧪 ═══════════════════════════════════════"))
            self.root.after(0, lambda: self.log("🧪 CENTRALIZED LOGGING TEST"))
            self.root.after(0, lambda: self.log("🧪 ═══════════════════════════════════════"))
            self.root.after(0, lambda: self.log(""))
            
            time.sleep(0.5)
            
            for test_type, data in tests:
                if test_type == "SECTION":
                    self.root.after(0, lambda d=data: self.log(""))
                    self.root.after(0, lambda d=data: self.log(f"🧪 {d}"))
                    self.root.after(0, lambda: self.log(""))
                    time.sleep(0.3)
                elif test_type == "log":
                    self.root.after(0, lambda d=data: self.log(d))
                elif test_type == "success":
                    self.root.after(0, lambda d=data: self.log_success(d))
                elif test_type == "warning":
                    msg, hint = data
                    self.root.after(0, lambda m=msg, h=hint: self.log_warning(m, h))
                elif test_type == "error":
                    msg, hint = data
                    self.root.after(0, lambda m=msg, h=hint: self.log_error(m, h))
                
                time.sleep(0.1)
            
            self.root.after(0, lambda: self.log(""))
            self.root.after(0, lambda: self.log("🧪 ═══════════════════════════════════════"))
            self.root.after(0, lambda: self.log("🧪 TEST COMPLETE"))
            self.root.after(0, lambda: self.log("🧪 ═══════════════════════════════════════"))
            
            error_count = sum(1 for t, _ in tests if t == "error")
            warn_count = sum(1 for t, _ in tests if t == "warning")
            success_count = sum(1 for t, _ in tests if t == "success")
            
            self.root.after(0, lambda: self.log(f"🧪 Errors: {error_count} | Warnings: {warn_count} | Success: {success_count}"))
            self.root.after(0, lambda: self.log(""))
        
        threading.Thread(target=_test, daemon=True).start()