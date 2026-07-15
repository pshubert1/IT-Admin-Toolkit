"""
Chocolatey Installer Tab UI
"""

import tkinter as tk
from tkinter import ttk
import subprocess
import threading
import os

from config.choco_apps import get_choco_sections
from ui.collapsible_frame import CollapsibleFrame


class ChocoTab:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.colors = app.colors
        self.checkboxes = {}
        self.choco_sections = get_choco_sections()
        self.choco_exe = self._find_choco()
        
        self.create_tab()
    
    def _find_choco(self):
        """Find the choco.exe path."""
        default_path = r"C:\ProgramData\chocolatey\bin\choco.exe"
        if os.path.exists(default_path):
            return default_path
        
        import shutil
        found = shutil.which("choco")
        if found:
            return found
        
        return None
    
    def _refresh_choco_path(self):
        """Refresh the choco.exe path (call after install)."""
        self.choco_exe = self._find_choco()
        if self.choco_exe:
            self.app.log_success(f"Chocolatey found at: {self.choco_exe}")
        return self.choco_exe
    
    def _run_choco(self, args, **kwargs):
        """Run a choco command with the correct path."""
        if not self.choco_exe:
            self._refresh_choco_path()
        
        if not self.choco_exe:
            raise FileNotFoundError("Chocolatey not installed")
        
        cmd = [self.choco_exe] + args
        return subprocess.run(cmd, **kwargs)
    
    def create_tab(self):
        """Create the Chocolatey tab content."""
        tab = self.parent
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)
        
        # === INFO/SEARCH SECTION ===
        info_frame = ttk.LabelFrame(tab, text="🍫 Chocolatey Package Manager", 
                                   padding="10", style='Dark.TLabelframe')
        info_frame.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
        
        btn_row = ttk.Frame(info_frame, style='Dark.TFrame')
        btn_row.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(btn_row, text="🔍 CHECK CHOCO", style='Dark.TButton',
                  command=self._check_choco).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(btn_row, text="📥 INSTALL CHOCO", style='Warning.TButton',
                  command=self._install_choco).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(btn_row, text="🗑️ UNINSTALL CHOCO", style='Danger.TButton',
          command=self._uninstall_choco).pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Label(btn_row, text="Search:", style='DarkFrame.TLabel').pack(side=tk.LEFT, padx=(20, 5))
        
        self.search_entry = ttk.Entry(btn_row, font=('Segoe UI', 10), width=30)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.search_entry.bind('<Return>', self._search_choco)
        
        ttk.Button(btn_row, text="🔍 SEARCH", style='Dark.TButton',
                  command=self._search_choco).pack(side=tk.LEFT)
        
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
        
        self.apps_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        apps_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create 2-column layout
        left_frame = ttk.Frame(self.scrollable_frame, style='Dark.TFrame', padding="5")
        right_frame = ttk.Frame(self.scrollable_frame, style='Dark.TFrame', padding="5")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
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
        
        self.progress = ttk.Progressbar(tab, mode='indeterminate')
        self.progress.grid(row=3, column=0, sticky='ew', padx=5, pady=5)
    
    def _create_category(self, parent, category_name, apps):
        """Create a category section with checkboxes."""
        from ui.collapsible_frame import CollapsibleFrame

        section = CollapsibleFrame(parent, title=category_name, style_colors=self.colors)
        section.pack(fill=tk.X, pady=(0, 8))
        section_frame = section.content 
        
        # Button row (create frame first, add buttons later)
        btn_row = ttk.Frame(section_frame, style='Dark.TFrame')
        btn_row.pack(fill=tk.X, pady=(0, 4))
        
        # Build checkboxes and collect vars
        category_vars = []
        
        for app_entry in apps:
            app_name = app_entry[0]
            choco_id = app_entry[1]
            version = app_entry[2] if len(app_entry) > 2 else None
            
            var = tk.BooleanVar()
            category_vars.append(var)
            display = f"☐ {app_name}" + (f" (v{version})" if version else "")
            cb = ttk.Checkbutton(section_frame, text=display, variable=var,
                                style='DarkFrame.TCheckbutton')
            cb.pack(anchor='w', pady=2)
            self.checkboxes[app_name] = (var, choco_id, version)
        
        # NOW add buttons (category_vars is fully populated)
        ttk.Button(btn_row, text="Select All", style='Dark.TButton',
                  command=lambda vs=category_vars: [v.set(True) for v in vs]
        ).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_row, text="Deselect All", style='Dark.TButton',
                  command=lambda vs=category_vars: [v.set(False) for v in vs]
        ).pack(side=tk.LEFT)
    
    
    def _on_canvas_configure(self, event):
        self.apps_canvas.itemconfig(self.canvas_window, width=event.width)
    
    def _check_choco(self):
        """Check if Chocolatey is installed."""
        self.app.log("🔍 Checking Chocolatey installation...")
        
        def check():
            try:
                result = self._run_choco(["--version"], 
                                        capture_output=True, text=True, timeout=10,
                                        creationflags=subprocess.CREATE_NO_WINDOW)
                if result.returncode == 0:
                    version = result.stdout.strip()
                    self.app.root.after(0, lambda: self.app.log_success(f"Chocolatey v{version} installed"))
                else:
                    self.app.root.after(0, lambda: self.app.log_error("Chocolatey not working properly",
                        hint="Try reinstalling with the INSTALL CHOCO button"))
            except FileNotFoundError:
                self.app.root.after(0, lambda: self.app.log_error("Chocolatey not installed",
                    hint="Click 'INSTALL CHOCO' to install it"))
            except Exception as e:
                self.app.root.after(0, lambda: self.app.log_error(f"Choco check failed: {str(e)}"))
        
        threading.Thread(target=check, daemon=True).start()
    
    def _install_choco(self):
        """Install or repair Chocolatey."""
        if not self.app.is_admin():
            self.app.log_error("Admin required for Chocolatey install",
                hint="Click 'Run as Admin' in the toolbar")
            return
        
        self.app.log("📥 Installing Chocolatey (opening PowerShell window)...")
        
        script = r"""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Installing/Repairing Chocolatey" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072

$chocoPath = "C:\ProgramData\chocolatey\bin\choco.exe"
if (Test-Path $chocoPath) {
    Write-Host "🔄 Chocolatey found - checking version..." -ForegroundColor Yellow
    & $chocoPath --version
    Write-Host ""
    
    $choice = Read-Host "Chocolatey is already installed. Upgrade? (Y/N)"
    if ($choice -eq 'Y' -or $choice -eq 'y') {
        Write-Host "🔄 Upgrading Chocolatey..." -ForegroundColor Yellow
        & $chocoPath upgrade chocolatey -y
        Write-Host ""
        Write-Host "✅ Chocolatey upgraded!" -ForegroundColor Green
    } else {
        Write-Host "⏭️ Skipped upgrade" -ForegroundColor Gray
    }
} else {
    Write-Host "📦 Chocolatey not found - Installing fresh..." -ForegroundColor Yellow
    Write-Host ""
    
    if (Test-Path "C:\ProgramData\chocolatey") {
        Write-Host "🧹 Removing old partial install..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force "C:\ProgramData\chocolatey" -ErrorAction SilentlyContinue
    }
    
    Write-Host "📥 Downloading Chocolatey installer..." -ForegroundColor Yellow
    $installScript = (New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1')
    Invoke-Expression $installScript
    
    if (Test-Path "C:\ProgramData\chocolatey\bin\choco.exe") {
        Write-Host ""
        Write-Host "✅ Chocolatey installed successfully!" -ForegroundColor Green
        & "C:\ProgramData\chocolatey\bin\choco.exe" --version
    } else {
        Write-Host ""
        Write-Host "❌ Installation may have failed - choco.exe not found" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "🔄 Refreshing environment PATH..." -ForegroundColor Yellow
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Chocolatey Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Close and reopen the IT Admin Toolkit to use Chocolatey features." -ForegroundColor Yellow
"""
        
        self.app.powershell.run(script, "Install Chocolatey", interactive=True)
    
    def _search_choco(self, event=None):
        """Search Chocolatey repository."""
        query = self.search_entry.get().strip()
        if not query:
            self.app.log_warning("Enter a search term")
            return
        
        self.app.log(f"🔍 Searching Chocolatey for '{query}'...")
        self.results_listbox.delete(0, tk.END)
        
        def search():
            try:
                result = self._run_choco(["search", query, "--limit-output"],
                                        capture_output=True, text=True, timeout=30,
                                        creationflags=subprocess.CREATE_NO_WINDOW)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    self.app.root.after(0, lambda: self._populate_results(lines))
                else:
                    self.app.root.after(0, lambda: self.app.log_error("Choco search failed",
                        hint="Check internet connection or try a different term"))
            except FileNotFoundError:
                self.app.root.after(0, lambda: self.app.log_error("Chocolatey not installed",
                    hint="Click 'INSTALL CHOCO' first"))
            except Exception as e:
                self.app.root.after(0, lambda: self.app.log_error(f"Search error: {str(e)}"))
        
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
        
        self.app.log_success(f"Found {count} packages")
    
    def _install_from_search(self):
        """Install selected package from search results."""
        selection = self.results_listbox.curselection()
        if not selection:
            self.app.log_warning("Select a package from search results")
            return
        
        item = self.results_listbox.get(selection[0])
        package_name = item.split(' ')[0]
        
        self.app.log(f"📥 Installing {package_name}...")
        
        def install():
            self.app.root.after(0, self.progress.start)
            try:
                result = self._run_choco(["install", package_name, "-y"],
                                        capture_output=True, text=True, timeout=600,
                                        creationflags=subprocess.CREATE_NO_WINDOW)
                if result.returncode == 0:
                    self.app.root.after(0, lambda: self.app.log_success(f"{package_name} installed"))
                else:
                    error = result.stderr.strip() or result.stdout.strip()
                    self.app.root.after(0, lambda: self.app.log_error(f"{package_name} install failed",
                        hint=f"{error[:200]}" if error else "Check internet connection or run as admin"))
            except FileNotFoundError:
                self.app.root.after(0, lambda: self.app.log_error("Chocolatey not installed",
                    hint="Click 'INSTALL CHOCO' first"))
            except Exception as e:
                self.app.root.after(0, lambda: self.app.log_error(f"Install error: {str(e)}"))
            finally:
                self.app.root.after(0, self.progress.stop)
        
        threading.Thread(target=install, daemon=True).start()
    
    def _start_install(self):
        """Install all selected packages."""
        selected = []
        for name, entry in self.checkboxes.items():
            var = entry[0]
            choco_id = entry[1]
            version = entry[2] if len(entry) > 2 else None
            if var.get():
                selected.append((name, choco_id, version))
        
        if not selected:
            self.app.log_warning("Select at least one package")
            return
        
        self.app.log(f"🚀 Installing {len(selected)} packages...")
        
        def install_all():
            self.app.root.after(0, lambda: self.install_btn.config(state='disabled'))
            self.app.root.after(0, self.progress.start)
            
            for app_name, choco_id, version in selected:
                self.app.root.after(0, lambda n=app_name: self.app.log(f"📥 Installing {n}..."))
                
                try:
                    args = ["install", choco_id, "-y"]
                    if version:
                        args.extend(["--version", version])
                    
                    result = self._run_choco(args,
                                           capture_output=True, text=True, timeout=600,
                                           creationflags=subprocess.CREATE_NO_WINDOW)
                    if result.returncode == 0:
                        self.app.root.after(0, lambda n=app_name: self.app.log_success(f"{n} installed"))
                    else:
                        error = result.stderr.strip() or result.stdout.strip()
                        self.app.root.after(0, lambda n=app_name, e=error: 
                            self.app.log_error(f"{n} install failed",
                                hint=f"{e[:200]}" if e else "Run as admin or check internet"))
                except FileNotFoundError:
                    self.app.root.after(0, lambda: self.app.log_error("Chocolatey not installed",
                        hint="Click 'INSTALL CHOCO' first"))
                    break
                except Exception as e:
                    self.app.root.after(0, lambda n=app_name, err=str(e): 
                        self.app.log_error(f"{n} error: {err}"))
            
            self.app.root.after(0, lambda: self.app.log("🎉 All installations complete!"))
            self.app.root.after(0, self.progress.stop)
            self.app.root.after(0, lambda: self.install_btn.config(state='normal'))
        
        threading.Thread(target=install_all, daemon=True).start()
        
        
        def install_all():
            self.app.root.after(0, lambda: self.install_btn.config(state='disabled'))
            self.app.root.after(0, self.progress.start)
            
            for app_name, choco_id in selected:
                self.app.root.after(0, lambda n=app_name: self.app.log(f"📥 Installing {n}..."))
                
                try:
                    result = self._run_choco(["install", choco_id, "-y"],
                                           capture_output=True, text=True, timeout=600,
                                           creationflags=subprocess.CREATE_NO_WINDOW)
                    if result.returncode == 0:
                        self.app.root.after(0, lambda n=app_name: self.app.log_success(f"{n} installed"))
                    else:
                        error = result.stderr.strip() or result.stdout.strip()
                        self.app.root.after(0, lambda n=app_name, e=error: 
                            self.app.log_error(f"{n} install failed",
                                hint=f"{e[:200]}" if e else "Run as admin or check internet"))
                except FileNotFoundError:
                    self.app.root.after(0, lambda: self.app.log_error("Chocolatey not installed",
                        hint="Click 'INSTALL CHOCO' first"))
                    break
                except Exception as e:
                    self.app.root.after(0, lambda n=app_name, err=str(e): 
                        self.app.log_error(f"{n} error: {err}"))
            
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
        
    
    def _uninstall_choco(self):
        """Uninstall Chocolatey infrastructure only (leaves packages intact)."""
        from tkinter import messagebox
        
        confirm = messagebox.askyesno(
            "⚠️ Remove Chocolatey Only",
            "This will:\n"
            "• Remove C:\\ProgramData\\chocolatey\n"
            "• Clean Chocolatey PATH & env vars\n"
            "• **LEAVE all installed packages intact**\n\n"
            "Continue?",
        )
        if not confirm:
            return

        self.app.log("🍫 Removing Chocolatey infrastructure...")
        
        script = r'''
    $ErrorActionPreference = "Continue"
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  REMOVE CHOCOLATEY INFRASTRUCTURE ONLY" -ForegroundColor Cyan
    Write-Host "  (Packages will remain installed)" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    # 1. Remove main Chocolatey directory (but NOT lib folder with packages)
    Write-Host "🗑️ Removing Chocolatey core folders..." -ForegroundColor Yellow
    $chocoDir = "$env:ProgramData\chocolatey"
    $protectedFolders = @('lib')  # Don't touch installed packages

    if (Test-Path $chocoDir) {
        Get-ChildItem -Path $chocoDir -Directory | ForEach-Object {
            if ($protectedFolders -notcontains $_.Name) {
                Remove-Item -Path $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
                Write-Host "  Removed: $($_.Name)" -ForegroundColor Green
            } else {
                Write-Host "  ⚠️  Protected: $($_.Name) (packages remain)" -ForegroundColor Yellow
            }
        }
        # Remove empty root if no packages left
        if (-not (Get-ChildItem -Path $chocoDir -Directory)) {
            Remove-Item -Path $chocoDir -Force -ErrorAction SilentlyContinue
            Write-Host "✅ Removed empty $chocoDir" -ForegroundColor Green
        }
    } else {
        Write-Host "ℹ️ Chocolatey directory not found" -ForegroundColor Gray
    }
    Write-Host ""

    # 2. Clean ALL Chocolatey environment variables
    Write-Host "🧹 Cleaning environment variables..." -ForegroundColor Yellow
    $envVars = @('ChocolateyInstall', 'ChocolateyLastPathUpdate', 'ChocolateyToolsLocation')
    foreach ($var in $envVars) {
        [Environment]::SetEnvironmentVariable($var, $null, "Machine")
        [Environment]::SetEnvironmentVariable($var, $null, "User")
        Write-Host "  Removed: $var" -ForegroundColor Green
    }
    Write-Host ""

    # 3. Clean PATH entries (Machine + User)
    Write-Host "🧹 Cleaning PATH entries..." -ForegroundColor Yellow
    $scopes = @("Machine", "User")
    foreach ($scope in $scopes) {
        $path = [Environment]::GetEnvironmentVariable("Path", $scope)
        if ($path -and $path -match 'chocolatey') {
            $oldCount = ($path -split ';' | Where-Object { $_ -match 'chocolatey' }).Count
            $cleanPath = ($path -split ';' | Where-Object { $_ -notmatch 'chocolatey' -and $_ -ne '' }) -join ';'
            [Environment]::SetEnvironmentVariable("Path", $cleanPath, $scope)
            Write-Host "  ✅ Cleaned PATH ($scope): removed ${oldCount} entries" -ForegroundColor Green
        }
    }
    Write-Host ""

    # 4. Remove tools/shims if exist
    Write-Host "🗑️ Cleaning tools/shims + HTTP cache..." -ForegroundColor Yellow
    $toolsDir = [Environment]::GetEnvironmentVariable("ChocolateyToolsLocation", "Machine")
    $binDir = "$env:ProgramData\chocolatey\bin"
    $httpCacheDir = "$env:ProgramData\ChocolateyHttpCache"
    
    # Remove tools directory (if not lib-related)
    if ($toolsDir -and (Test-Path $toolsDir) -and $toolsDir -notlike '*lib*') {
        Remove-Item -Path $toolsDir -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "✅ Removed: $toolsDir" -ForegroundColor Green
    }
    # Remove HTTP cache (safe to delete)
    if (Test-Path $httpCacheDir) {
        Remove-Item -Path $httpCacheDir -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "✅ Removed HTTP cache: $httpCacheDir" -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  ✅ CHOCOLATEY INFRASTRUCTURE REMOVED!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "ℹ️ Packages remain in C:\ProgramData\chocolatey\lib" -ForegroundColor Cyan
    Write-Host "ℹ️ Restart app or reboot for PATH changes" -ForegroundColor Cyan
    Write-Host "ℹ️ Run 'choco' to verify removal" -ForegroundColor Cyan
    '''
        
        self.app.powershell.run(script, "Remove Chocolatey Infrastructure", interactive=True)
