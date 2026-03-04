"""
Windows Updates Tab UI
"""

import tkinter as tk
from tkinter import ttk
import subprocess
import threading


class UpdatesTab:
    def __init__(self, parent, app):
        """
        Initialize the Windows Updates tab.
        
        Args:
            parent: The parent notebook tab frame
            app: Reference to main AppInstaller instance
        """
        self.parent = parent
        self.app = app
        self.colors = app.colors
        self.checkboxes = {}  # {update_title: (var, kb_id)}
        self.updates = []  # List of available updates
        
        self.create_tab()
    
    def create_tab(self):
        """Create the Windows Updates tab content."""
        tab = self.parent
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)
        
        # === CONTROLS SECTION ===
        controls_frame = ttk.LabelFrame(tab, text="🔄 Windows Updates", 
                                       padding="10", style='Dark.TLabelframe')
        controls_frame.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
        
        ttk.Button(controls_frame, text="🔍 SCAN FOR UPDATES", style='Dark.TButton',
                  command=self._scan_updates).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(controls_frame, text="⚡ INSTALL SELECTED", style='Warning.TButton',
                  command=self._install_selected).pack(side=tk.LEFT)
        
        # === UPDATES LIST with SCROLLABLE CANVAS ===
        updates_outer_frame = ttk.LabelFrame(tab, text="📋 Available Updates", 
                                            padding="5", style='Dark.TLabelframe')
        updates_outer_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        updates_outer_frame.columnconfigure(0, weight=1)
        updates_outer_frame.rowconfigure(0, weight=1)
        
        self.updates_canvas = tk.Canvas(updates_outer_frame, bg=self.colors['frame_bg'], 
                                        highlightthickness=0)
        scrollbar = ttk.Scrollbar(updates_outer_frame, orient=tk.VERTICAL, 
                                  command=self.updates_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.updates_canvas, style='Dark.TFrame')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.updates_canvas.configure(scrollregion=self.updates_canvas.bbox("all"))
        )
        
        self.canvas_window = self.updates_canvas.create_window((0, 0), window=self.scrollable_frame, 
                                                              anchor="nw")
        self.updates_canvas.configure(yscrollcommand=scrollbar.set)
        self.updates_canvas.bind('<Configure>', self._on_canvas_configure)
        
        # Mouse wheel scrolling
        self.updates_canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.scrollable_frame.bind("<MouseWheel>", self._on_mousewheel)
        
        self.updates_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Progress bar
        self.progress = ttk.Progressbar(tab, mode='indeterminate')
        self.progress.grid(row=2, column=0, sticky='ew', padx=5, pady=5)
    
    def _on_canvas_configure(self, event):
        """Adjust the scrollable frame width."""
        self.updates_canvas.itemconfig(self.canvas_window, width=event.width)
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        if event.num == 5 or event.delta < 0:
            self.updates_canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0:
            self.updates_canvas.yview_scroll(-1, "units")
    
    def _scan_updates(self):
        """Scan for available Windows updates."""
        if not self.app.is_admin():
            tk.messagebox.showwarning("Admin Required", 
                                      "Please run the app as administrator to scan/install updates.")
            self.app.log_error("Admin required", hint="Click 'Run as Admin' in toolbar")
            return
        
        self.app.log("🔍 Scanning for Windows updates...")
        self.progress.start()
        self.checkboxes.clear()
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        def scan():
            try:
                # Step 1: Install NuGet provider if missing
                nuget_result = subprocess.run(
                    ['powershell.exe', '-Command', 
                     'if (-not (Get-PackageProvider -Name NuGet -ErrorAction SilentlyContinue)) { '
                     'Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Force -ErrorAction Stop; '
                     'Write-Output "✅ NuGet provider installed" } else { '
                     'Write-Output "✅ NuGet provider already installed" }'],
                    capture_output=True, text=True, timeout=120
                )
                self.app.root.after(0, lambda: self.app.log(nuget_result.stdout.strip()))
                if nuget_result.returncode != 0:
                    error_msg = nuget_result.stderr.strip() or "Unknown error"
                    self.app.root.after(0, lambda: self.app.log(
                        f"❌ Failed to install NuGet: {error_msg}"))
                
                # Step 2: Install/Force Reinstall PSWindowsUpdate module
                module_result = subprocess.run(
                    ['powershell.exe', '-Command', 
                     'Install-Module -Name PSWindowsUpdate -Force -Scope CurrentUser '
                     '-AllowClobber -ErrorAction Stop; '
                     'Write-Output "✅ PSWindowsUpdate module (re)installed"'],
                    capture_output=True, text=True, timeout=120
                )
                self.app.root.after(0, lambda: self.app.log(module_result.stdout.strip()))
                if module_result.returncode != 0:
                    error_msg = module_result.stderr.strip() or "Unknown error"
                    self.app.root.after(0, lambda: self.app.log(
                        f"❌ Failed to (re)install PSWindowsUpdate: {error_msg}"))
                    self.app.root.after(0, lambda: tk.messagebox.showerror(
                        "Module Install Failed", 
                        "Could not install PSWindowsUpdate module.\n\n"
                        "Troubleshooting:\n"
                        "- Ensure internet connection.\n"
                        "- Run as admin.\n"
                        "- In PowerShell (as admin): Set-ExecutionPolicy RemoteSigned\n"
                        "- Then retry scan."))
                    self.app.root.after(0, self.progress.stop)
                    return
                
                # Step 3: Debug - Log module path and import
                debug_result = subprocess.run(
                    ['powershell.exe', '-Command', 
                     'Import-Module PSWindowsUpdate -Force -ErrorAction Stop; '
                     'Write-Output "✅ Module imported from: $(Get-Module PSWindowsUpdate).Path"'],
                    capture_output=True, text=True, timeout=30
                )
                self.app.root.after(0, lambda: self.app.log(debug_result.stdout.strip()))
                if debug_result.returncode != 0:
                    error_msg = debug_result.stderr.strip() or "Unknown error"
                    self.app.root.after(0, lambda: self.app.log(
                        f"❌ Failed to import module: {error_msg}"))
                    self.app.root.after(0, self.progress.stop)
                    return
                
                # Step 4: Get list of updates using Get-WUList with details
                scan_result = subprocess.run(
                    ['powershell.exe', '-Command', 
                     'Import-Module PSWindowsUpdate -Force; '
                     '$updates = Get-WUList; '
                     'foreach ($update in $updates) { '
                     ' $kb = if ($update.KB) { $update.KB -join "," } else { "Unknown" }; '
                     ' $size = if ($update.Size) { $update.Size } else { "Unknown" }; '
                     ' Write-Output "$($update.Title)|$kb|$size" }'],
                    capture_output=True, text=True, timeout=300
                )
                self.app.root.after(0, lambda: self.app.log(
                    f"Raw scan output: {scan_result.stdout.strip()}"))
                if scan_result.returncode == 0 and scan_result.stdout:
                    self.updates = []
                    lines = scan_result.stdout.strip().split('\n')
                    for line in lines:
                        if '|' in line:
                            parts = line.split('|')
                            title = parts[0].strip() if len(parts) > 0 else "Unknown Update"
                            kb = parts[1].strip() if len(parts) > 1 else "Unknown"
                            size = parts[2].strip() if len(parts) > 2 else "Unknown"
                            if not title:
                                title = f"Update KB{kb}"
                            self.updates.append((title, kb, size))
                    self.app.root.after(0, self._populate_updates)
                else:
                    error_msg = scan_result.stderr.strip() or "Unknown error"
                    self.app.root.after(0, lambda: self.app.log(
                        f"❌ Failed to scan updates: {error_msg}"))
            except Exception as e:
                self.app.root.after(0, lambda: self.app.log(
                    f"❌ Error during scan: {str(e)}"))
            finally:
                self.app.root.after(0, self.progress.stop)
        
        threading.Thread(target=scan, daemon=True).start()
    
    def _populate_updates(self):
        """Populate the list of updates with checkboxes."""
        if not self.updates:
            self.app.log_success("No updates available")
            ttk.Label(self.scrollable_frame, text="No updates found", 
                      style='DarkFrame.TLabel').pack(pady=10)
            return
        
        self.app.log_success(f"Found {len(self.updates)} updates")
        
        for title, kb, size in self.updates:
            label = f"☐ {title} (KB{kb}, Size: {size})"
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(self.scrollable_frame, text=label, variable=var,
                                style='DarkFrame.TCheckbutton')
            cb.pack(anchor='w', pady=2)
            self.checkboxes[title] = (var, kb)
    
    def _install_selected(self):
        """Install selected updates."""
        if not self.app.is_admin():
            tk.messagebox.showwarning("Admin Required", 
                                      "Please run the app as administrator to install updates.")
            self.app.log_error("Admin required", hint="Click 'Run as Admin' in toolbar")
            return
        
        selected = [(title, kb) for title, (var, kb) in self.checkboxes.items() if var.get()]
        if not selected:
            self.app.log_warning("Select at least one update")
            return
        
        self.app.log(f"🚀 Installing {len(selected)} updates...")
        self.progress.start()
        
        def install():
            try:
                for title, kb in selected:
                    if kb == "Unknown" or not kb:
                        self.app.root.after(0, lambda t=title: self.app.log(
                            f"⚠️ Skipping {t} (Unknown KB - cannot install)"))
                        continue
                    
                    self.app.root.after(0, lambda t=title: self.app.log(
                        f"📥 Installing {t} (KB{kb})..."))
                    
                    # Handle multiple KBs (split by comma)
                    kb_list = kb.split(',')
                    for single_kb in kb_list:
                        single_kb = single_kb.strip()
                        if not single_kb:
                            continue
                        
                        # Import module AND install in the SAME PowerShell session
                        install_cmd = (
                            'Import-Module PSWindowsUpdate -Force; '
                            f'Install-WindowsUpdate -KBArticleID {single_kb} '
                            '-AcceptAll -Confirm:$false'
                        )
                        result = subprocess.run(
                            ['powershell.exe', '-Command', install_cmd],
                            capture_output=True, text=True, timeout=600
                        )
                        if result.returncode == 0:
                            self.app.root.after(0, lambda t=title: self.app.log(
                                f"✅ {t} installed (output: {result.stdout.strip()})"))
                        else:
                            error_msg = result.stderr.strip() or "Unknown error"
                            self.app.root.after(0, lambda t=title: self.app.log(
                                f"❌ {t} failed: {error_msg}"))
                
                self.app.root.after(0, lambda: self.app.log(
                    "🎉 Installations complete! Restart may be needed."))
                self.app.root.after(0, lambda: tk.messagebox.showinfo(
                    "Install Complete", 
                    "Updates installed. A restart may be required for changes to take effect."))
            except Exception as e:
                self.app.root.after(0, lambda: self.app.log(
                    f"❌ Error during install: {str(e)}"))
            finally:
                self.app.root.after(0, self.progress.stop)
                self.app.root.after(0, self._scan_updates)  # Refresh list
        
        threading.Thread(target=install, daemon=True).start()