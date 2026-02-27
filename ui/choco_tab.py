"""
Chocolatey Installer Tab UI
"""

import tkinter as tk
from tkinter import ttk
import subprocess
import threading

# Import apps from config
from config.choco_apps import get_choco_sections


class ChocoTab:
    def __init__(self, parent, app):
        """
        Initialize the Chocolatey tab.
        
        Args:
            parent: The parent notebook tab frame
            app: Reference to main AppInstaller instance
        """
        self.parent = parent
        self.app = app
        self.colors = app.colors
        self.checkboxes = {}
        
        # Get the app sections from config
        self.choco_sections = get_choco_sections()
        
        self.create_tab()
    
    def create_tab(self):
        """Create the Chocolatey tab content."""
        tab = self.parent
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)
        
        # === INFO/SEARCH SECTION ===
        info_frame = ttk.LabelFrame(tab, text="🍫 Chocolatey Package Manager", 
                                   padding="10", style='Dark.TLabelframe')
        info_frame.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
        
        # Check Choco button and search
        btn_row = ttk.Frame(info_frame, style='Dark.TFrame')
        btn_row.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(btn_row, text="🔍 CHECK CHOCO", style='Dark.TButton',
                  command=self._check_choco).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(btn_row, text="📥 INSTALL CHOCO", style='Warning.TButton',
                  command=self._install_choco).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(btn_row, text="Search:", style='DarkFrame.TLabel').pack(side=tk.LEFT, padx=(20, 5))
        
        self.search_entry = ttk.Entry(btn_row, font=('Segoe UI', 10), width=30)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.search_entry.bind('<Return>', self._search_choco)
        
        ttk.Button(btn_row, text="🔍 SEARCH", style='Dark.TButton',
                  command=self._search_choco).pack(side=tk.LEFT)
        
        # Search results
        self.results_listbox = tk.Listbox(info_frame, height=3, bg=self.colors['bg'],
                                         fg=self.colors['fg'], font=('Consolas', 9),
                                         selectbackground=self.colors['accent'])
        self.results_listbox.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(info_frame, text="⚡ INSTALL SELECTED FROM SEARCH", style='Dark.TButton',
                  command=self._install_from_search).pack()
        
        # === PRESET APPS with SCROLLABLE CANVAS ===
        apps_outer_frame = ttk.LabelFrame(tab, text="📦 Preset Chocolatey Packages", 
                                         padding="5", style='Dark.TLabelframe')
        apps_outer_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        apps_outer_frame.columnconfigure(0, weight=1)
        apps_outer_frame.rowconfigure(0, weight=1)
        
        # Create canvas with scrollbar
        self.apps_canvas = tk.Canvas(apps_outer_frame, bg=self.colors['frame_bg'], 
                                    highlightthickness=0)
        apps_scrollbar = ttk.Scrollbar(apps_outer_frame, orient=tk.VERTICAL, 
                                      command=self.apps_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.apps_canvas, style='Dark.TFrame')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.apps_canvas.configure(scrollregion=self.apps_canvas.bbox("all"))
        )
        
        self.canvas_window = self.apps_canvas.create_window((0, 0), window=self.scrollable_frame, 
                                                           anchor="nw")
        self.apps_canvas.configure(yscrollcommand=apps_scrollbar.set)
        self.apps_canvas.bind('<Configure>', self._on_canvas_configure)
        
        # Mouse wheel scrolling
        self.apps_canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.scrollable_frame.bind("<MouseWheel>", self._on_mousewheel)
        
        self.apps_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        apps_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create 2-column layout
        left_frame = ttk.Frame(self.scrollable_frame, style='Dark.TFrame', padding="5")
        right_frame = ttk.Frame(self.scrollable_frame, style='Dark.TFrame', padding="5")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Distribute categories between columns (from get_choco_sections list)
        mid_point = len(self.choco_sections) // 2 + 1
        left_sections = self.choco_sections[:mid_point]
        right_sections = self.choco_sections[mid_point:]
        
        for section_name, apps in left_sections:
            self._create_category(left_frame, section_name, apps)
        
        for section_name, apps in right_sections:
            self._create_category(right_frame, section_name, apps)
        
        # === BUTTONS ===
        btn_frame = ttk.Frame(tab, style='DarkBg.TFrame')
        btn_frame.grid(row=2, column=0, sticky='ew', padx=5, pady=5)
        
        self.install_btn = ttk.Button(btn_frame, text="⚡ INSTALL ALL SELECTED", 
                                     style='Dark.TButton', command=self._start_install)
        self.install_btn.pack(side=tk.LEFT, padx=(0, 10), ipadx=20)
        
        ttk.Button(btn_frame, text="🔄 UPDATE ALL", style='Warning.TButton',
                  command=self._update_all).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(btn_frame, text="📋 LIST INSTALLED", style='Dark.TButton',
                  command=self._list_installed).pack(side=tk.LEFT)
        
        # Progress bar
        self.progress = ttk.Progressbar(tab, mode='indeterminate')
        self.progress.grid(row=3, column=0, sticky='ew', padx=5, pady=5)
    
    def _create_category(self, parent, category_name, apps):
        """Create a category section with checkboxes."""
        section_frame = ttk.LabelFrame(parent, text=category_name, 
                                      padding="8", style='Dark.TLabelframe')
        section_frame.pack(fill=tk.X, pady=(0, 8))
        
        for app_name, choco_id in apps:
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(section_frame, text=f"☐ {app_name}", variable=var,
                                style='DarkFrame.TCheckbutton')
            cb.pack(anchor='w', pady=2)
            self.checkboxes[app_name] = (var, choco_id)
    
    def _on_canvas_configure(self, event):
        """Adjust the scrollable frame width when canvas is resized."""
        self.apps_canvas.itemconfig(self.canvas_window, width=event.width)
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        if event.num == 5 or event.delta < 0:
            self.apps_canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0:
            self.apps_canvas.yview_scroll(-1, "units")
    
    def _check_choco(self):
        """Check if Chocolatey is installed."""
        self.app.log("🔍 Checking Chocolatey installation...")
        
        def check():
            try:
                result = subprocess.run(["choco", "--version"], 
                                       capture_output=True, text=True, timeout=10,
                                       creationflags=subprocess.CREATE_NO_WINDOW)
                if result.returncode == 0:
                    version = result.stdout.strip()
                    self.app.root.after(0, lambda: self.app.log(f"✅ Chocolatey v{version} installed"))
                else:
                    self.app.root.after(0, lambda: self.app.log("❌ Chocolatey not found"))
            except FileNotFoundError:
                self.app.root.after(0, lambda: self.app.log("❌ Chocolatey not installed - Click 'INSTALL CHOCO' to install"))
            except Exception as e:
                self.app.root.after(0, lambda: self.app.log(f"❌ Error: {str(e)}"))
        
        threading.Thread(target=check, daemon=True).start()
    
    def _install_choco(self):
        """Install or repair Chocolatey (requires admin)."""
        if not self.app.is_admin():
            tk.messagebox.showwarning("Admin Required", "Please run the app as administrator to install/repair Chocolatey.")
            self.app.log("❌ Admin required for Chocolatey install")
            return
        
        self.app.log("📥 Installing/Repairing Chocolatey (opening PowerShell window)...")
        
        script = r"""Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Installing/Repairing Chocolatey" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

try {
    # Check if Choco is installed and try to upgrade first
    choco --version
    if ($LASTEXITCODE -eq 0) {
        Write-Host "🔄 Upgrading Chocolatey..." -ForegroundColor Yellow
        choco upgrade chocolatey -y
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Chocolatey upgraded successfully" -ForegroundColor Green
            exit 0
        } else {
            Write-Host "⚠️ Upgrade failed - proceeding to reinstall" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠️ Chocolatey not found - proceeding to install" -ForegroundColor Yellow
    }

    # Clean old install
    Write-Host "🧹 Removing old Chocolatey folder..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "C:\ProgramData\chocolatey" -ErrorAction SilentlyContinue

    # Install
    Write-Host "📦 Installing Chocolatey..." -ForegroundColor Yellow
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Chocolatey installed successfully" -ForegroundColor Green
        choco --version
    } else {
        Write-Host "❌ Chocolatey install failed" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Error during install/repair: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Chocolatey Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "You may need to restart this application to use Chocolatey." -ForegroundColor Yellow
Write-Host ""
"""
        
        self.app.powershell.run(script, "Install Chocolatey", interactive=True)
    
    def _search_choco(self, event=None):
        """Search Chocolatey repository."""
        query = self.search_entry.get().strip()
        if not query:
            self.app.log("⚠️ Enter a search term")
            return
        
        self.app.log(f"🔍 Searching Chocolatey for '{query}'...")
        self.results_listbox.delete(0, tk.END)
        
        def search():
            try:
                result = subprocess.run(["choco", "search", query, "--limit-output"],
                                       capture_output=True, text=True, timeout=30,
                                       creationflags=subprocess.CREATE_NO_WINDOW)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    self.app.root.after(0, lambda: self._populate_results(lines))
                else:
                    self.app.root.after(0, lambda: self.app.log("❌ Search failed"))
            except FileNotFoundError:
                self.app.root.after(0, lambda: self.app.log("❌ Chocolatey not installed"))
            except Exception as e:
                self.app.root.after(0, lambda: self.app.log(f"❌ Error: {str(e)}"))
        
        threading.Thread(target=search, daemon=True).start()
    
    def _populate_results(self, lines):
        """Populate search results."""
        self.results_listbox.delete(0, tk.END)
        count = 0
        for line in lines:
            if line.strip() and '|' in line:
                parts = line.split('|')
                name = parts[0]
                version = parts[1] if len(parts) > 1 else "latest"
                self.results_listbox.insert(tk.END, f"{name} ({version})")
                count += 1
        
        self.app.log(f"✅ Found {count} packages")
    
    def _install_from_search(self):
        """Install selected package from search results."""
        selection = self.results_listbox.curselection()
        if not selection:
            self.app.log("⚠️ Select a package from search results")
            return
        
        item = self.results_listbox.get(selection[0])
        package_name = item.split(' ')[0]
        
        self.app.log(f"📥 Installing {package_name}...")
        
        def install():
            self.app.root.after(0, self.progress.start)
            try:
                result = subprocess.run(["choco", "install", package_name, "-y"],
                                       capture_output=True, text=True, timeout=600,
                                       creationflags=subprocess.CREATE_NO_WINDOW)
                if result.returncode == 0:
                    self.app.root.after(0, lambda: self.app.log(f"✅ {package_name} installed"))
                else:
                    self.app.root.after(0, lambda: self.app.log(f"❌ {package_name} failed"))
                    if self.app.debug_mode.get():
                        self.app.root.after(0, lambda: self.app.debug_log(result.stderr))
            except FileNotFoundError:
                self.app.root.after(0, lambda: self.app.log("❌ Chocolatey not installed"))
            except Exception as e:
                self.app.root.after(0, lambda: self.app.log(f"❌ Error: {str(e)}"))
            finally:
                self.app.root.after(0, self.progress.stop)
        
        threading.Thread(target=install, daemon=True).start()
    
    def _start_install(self):
        """Install all selected packages."""
        selected = [(name, choco_id) for name, (var, choco_id) in self.checkboxes.items() if var.get()]
        
        if not selected:
            self.app.log("⚠️ Select at least one package")
            return
        
        self.app.log(f"🚀 Installing {len(selected)} packages...")
        
        def install_all():
            self.app.root.after(0, lambda: self.install_btn.config(state='disabled'))
            self.app.root.after(0, self.progress.start)
            
            for app_name, choco_id in selected:
                self.app.root.after(0, lambda n=app_name: self.app.log(f"📥 Installing {n}..."))
                
                try:
                    result = subprocess.run(["choco", "install", choco_id, "-y"],
                                           capture_output=True, text=True, timeout=600,
                                           creationflags=subprocess.CREATE_NO_WINDOW)
                    if result.returncode == 0:
                        self.app.root.after(0, lambda n=app_name: self.app.log(f"✅ {n} installed"))
                    else:
                        self.app.root.after(0, lambda n=app_name: self.app.log(f"❌ {n} failed"))
                except FileNotFoundError:
                    self.app.root.after(0, lambda: self.app.log("❌ Chocolatey not installed"))
                    break
                except Exception as e:
                    self.app.root.after(0, lambda n=app_name, err=str(e): self.app.log(f"❌ {n} error: {err}"))
            
            self.app.root.after(0, lambda: self.app.log("🎉 All installations complete!"))
            self.app.root.after(0, self.progress.stop)
            self.app.root.after(0, lambda: self.install_btn.config(state='normal'))
        
        threading.Thread(target=install_all, daemon=True).start()
    
    def _update_all(self):
        """Update all Chocolatey packages."""
        self.app.log("🔄 Updating all Chocolatey packages...")
        
        script = """Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Updating All Chocolatey Packages" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

choco upgrade all -y

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Update Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green"""
        
        self.app.powershell.run(script, "Update All Packages", interactive=True)
    
    def _list_installed(self):
        """List installed Chocolatey packages."""
        self.app.log("📋 Listing installed packages...")
        
        script = """Write-Host "Installed Chocolatey Packages:" -ForegroundColor Cyan
Write-Host "===============================" -ForegroundColor Cyan
Write-Host ""

$packages = choco list --local-only
$packages

Write-Host ""
Write-Host "----------------------------------------" -ForegroundColor Gray
$count = ($packages | Measure-Object -Line).Lines - 1
Write-Host "Total packages installed: $count" -ForegroundColor Green"""
        
        self.app.powershell.run(script, "List Installed Packages")