"""
Uninstall Applications Tab with Cleanup
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import winreg
import os
import shutil


class UninstallTab:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.colors = app.colors
        self.installed_apps = []
        self.checkboxes = {}  # {app_name: (BooleanVar, app_data)}
        
        self.create_tab()
        
    def _update_selected(self):
        """Update selected applications."""
        selected_apps = [app_data for var, app_data in self.checkboxes.values() if var.get()]
        
        if not selected_apps:
            self.app.log_warning("Select at least one application to update")
            return
        
        # Filter to only Winget and Choco apps (Registry apps can't be updated this way)
        updatable = [(app, src) for app in selected_apps if (src := app[1]) in ("Winget", "Chocolatey")]
        
        if not updatable:
            self.app.log_warning("Selected apps cannot be updated (only Winget/Choco apps supported)")
            return
        
        self.app.log(f"🔄 Updating {len(updatable)} application(s)...")
        
        def update():
            self.app.root.after(0, self.progress.start)
            
            for app_data, source in updatable:
                name = app_data[0]
                self.app.root.after(0, lambda n=name: self.app.log(f"⬆️ Updating {n}..."))
                
                try:
                    if source == "Winget":
                        result = subprocess.run(
                            ["winget", "upgrade", "--name", name, "--silent", "--accept-package-agreements"],
                            capture_output=True, text=True, timeout=600,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                    elif source == "Chocolatey":
                        result = subprocess.run(
                            ["choco", "upgrade", name, "-y"],
                            capture_output=True, text=True, timeout=600,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                    
                    if result.returncode == 0:
                        self.app.root.after(0, lambda n=name: self.app.log(f"✅ {n} updated"))
                    else:
                        self.app.root.after(0, lambda n=name: self.app.log(f"⚠️ {n} - no update available or failed"))
                        
                except Exception as e:
                    self.app.root.after(0, lambda n=name, err=str(e): self.app.log(f"❌ {n} error: {err}"))
            
            self.app.root.after(0, lambda: self.app.log("🎉 Update complete!"))
            self.app.root.after(0, self.progress.stop)
        
        threading.Thread(target=update, daemon=True).start()
    
    def _update_all_winget(self):
        """Update all Winget applications."""
        self.app.log("⬆️ Updating all Winget applications...")
        
        def update():
            self.app.root.after(0, self.progress.start)
            
            try:
                result = subprocess.run(
                    ["winget", "upgrade", "--all", "--silent", "--accept-package-agreements"],
                    capture_output=True, text=True, timeout=1800,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                if result.returncode == 0:
                    self.app.root.after(0, lambda: self.app.log_success("All Winget apps updated"))
                else:
                    self.app.root.after(0, lambda: self.app.log_warning("Some updates may have failed"))
                    
                if self.app.log_script_output.get() and result.stdout:
                    for line in result.stdout.strip().split('\n')[-10:]:  # Last 10 lines
                        if line.strip():
                            self.app.root.after(0, lambda l=line: self.app.log(f"   {l}"))
                            
            except subprocess.TimeoutExpired:
                self.app.root.after(0, lambda: self.app.log_warning("Update timed out (may still be running)"))
            except FileNotFoundError:
                self.app.root.after(0, lambda: self.app.log_error("Winget not installed"))
            except Exception as e:
                self.app.root.after(0, lambda: self.app.log_error(f"Error: {str(e)}"))
            
            self.app.root.after(0, self.progress.stop)
        
        threading.Thread(target=update, daemon=True).start()
    
    def _update_all_choco(self):
        """Update all Chocolatey applications."""
        self.app.log("⬆️ Updating all Chocolatey applications...")
        
        def update():
            self.app.root.after(0, self.progress.start)
            
            try:
                result = subprocess.run(
                    ["choco", "upgrade", "all", "-y"],
                    capture_output=True, text=True, timeout=1800,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                if result.returncode == 0:
                    self.app.root.after(0, lambda: self.app.log_success("All Chocolatey apps updated"))
                else:
                    self.app.root.after(0, lambda: self.app.log_warning("Some updates may have failed"))
                    
                if self.app.log_script_output.get() and result.stdout:
                    for line in result.stdout.strip().split('\n')[-10:]:  # Last 10 lines
                        if line.strip():
                            self.app.root.after(0, lambda l=line: self.app.log(f"   {l}"))
                            
            except subprocess.TimeoutExpired:
                self.app.root.after(0, lambda: self.app.log_warning("Update timed out (may still be running)"))
            except FileNotFoundError:
                self.app.root.after(0, lambda: self.app.log_error("Chocolatey not installed"))
            except Exception as e:
                self.app.root.after(0, lambda: self.app.log_error(f"Error: {str(e)}"))
            
            self.app.root.after(0, self.progress.stop)
        
        threading.Thread(target=update, daemon=True).start()
    
    def create_tab(self):
        """Create the uninstall tab content."""
        tab = self.parent
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)
        
        # === HEADER / CONTROLS ===
        controls_frame = ttk.LabelFrame(tab, text="🗑️ Uninstall Applications", 
                                       padding="10", style='Dark.TLabelframe')
        controls_frame.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
        
        btn_row = ttk.Frame(controls_frame, style='Dark.TFrame')
        btn_row.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(btn_row, text="🔄 SCAN INSTALLED APPS", style='Dark.TButton',
                  command=self._scan_apps).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(btn_row, text="Filter:", style='DarkFrame.TLabel').pack(side=tk.LEFT, padx=(20, 5))
        
        self.filter_entry = ttk.Entry(btn_row, font=('Segoe UI', 10), width=30)
        self.filter_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.filter_entry.bind('<KeyRelease>', self._filter_apps)
        
        # Source filter
        ttk.Label(btn_row, text="Source:", style='DarkFrame.TLabel').pack(side=tk.LEFT, padx=(10, 5))
        self.source_var = tk.StringVar(value="All")
        source_combo = ttk.Combobox(btn_row, textvariable=self.source_var, 
                                    values=["All", "Registry", "Winget", "Chocolatey"],
                                    state='readonly', width=12)
        source_combo.pack(side=tk.LEFT)
        source_combo.bind('<<ComboboxSelected>>', self._filter_apps)
        
        # Cleanup options
        options_row = ttk.Frame(controls_frame, style='Dark.TFrame')
        options_row.pack(fill=tk.X)
        
        self.cleanup_registry = tk.BooleanVar(value=True)
        self.cleanup_files = tk.BooleanVar(value=True)
        self.cleanup_appdata = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(options_row, text="🔑 Clean Registry", variable=self.cleanup_registry,
                       style='DarkFrame.TCheckbutton').pack(side=tk.LEFT, padx=(0, 15))
        ttk.Checkbutton(options_row, text="📁 Clean Program Files", variable=self.cleanup_files,
                       style='DarkFrame.TCheckbutton').pack(side=tk.LEFT, padx=(0, 15))
        ttk.Checkbutton(options_row, text="📂 Clean AppData", variable=self.cleanup_appdata,
                       style='DarkFrame.TCheckbutton').pack(side=tk.LEFT)
        
# === APP LIST with CHECKBOXES ===
        list_frame = ttk.LabelFrame(tab, text="📦 Installed Applications (check to select)", 
                                   padding="5", style='Dark.TLabelframe')
        list_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Create canvas with scrollbar
        self.apps_canvas = tk.Canvas(list_frame, bg=self.colors['frame_bg'], 
                                    highlightthickness=0)
        apps_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, 
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
        
        self.apps_canvas.grid(row=0, column=0, sticky='nsew')
        apps_scrollbar.grid(row=0, column=1, sticky='ns')
        
        
 # === BUTTONS ===
        btn_frame = ttk.Frame(tab, style='DarkBg.TFrame')
        btn_frame.grid(row=2, column=0, sticky='ew', padx=5, pady=5)
        
        # Selection buttons
        ttk.Button(btn_frame, text="☑️ Select All", style='Dark.TButton',
                  command=self._select_all).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="☐ Deselect All", style='Dark.TButton',
                  command=self._deselect_all).pack(side=tk.LEFT, padx=(0, 20))
        
        self.uninstall_btn = ttk.Button(btn_frame, text="🗑️ UNINSTALL SELECTED", 
                                       style='Danger.TButton', command=self._uninstall_selected)
        self.uninstall_btn.pack(side=tk.LEFT, padx=(0, 10), ipadx=20)
        
        ttk.Button(btn_frame, text="🧹 CLEANUP ONLY", style='Warning.TButton',
                  command=self._cleanup_only).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(btn_frame, text="📋 EXPORT LIST", style='Dark.TButton',
                  command=self._export_list).pack(side=tk.LEFT)
        # Add a separator
        ttk.Separator(btn_frame, orient='vertical').pack(side=tk.LEFT, fill='y', padx=15)
        
        # Update buttons
        ttk.Button(btn_frame, text="🔄 Update Selected", style='Warning.TButton',
                  command=self._update_selected).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(btn_frame, text="⬆️ Update All Winget", style='Dark.TButton',
                  command=self._update_all_winget).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(btn_frame, text="⬆️ Update All Choco", style='Dark.TButton',
                  command=self._update_all_choco).pack(side=tk.LEFT, padx=(0, 5))
        
        # App count label
        self.count_label = ttk.Label(btn_frame, text="0 apps found", 
                                    style='DarkFrame.TLabel')
        self.count_label.pack(side=tk.RIGHT)
        
        # Progress bar
        self.progress = ttk.Progressbar(tab, mode='indeterminate')
        self.progress.grid(row=3, column=0, sticky='ew', padx=5, pady=5)
    
    def _on_canvas_configure(self, event):
        """Adjust the scrollable frame width when canvas is resized."""
        self.apps_canvas.itemconfig(self.canvas_window, width=event.width)
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        self.apps_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def _select_all(self):
        """Select all visible checkboxes."""
        for var, _ in self.checkboxes.values():
            var.set(True)
    
    def _deselect_all(self):
        """Deselect all checkboxes."""
        for var, _ in self.checkboxes.values():
            var.set(False)
    
    def _scan_apps(self):
        """Scan for installed applications from all sources."""
        self.app.log("🔍 Scanning installed applications...")
        self.installed_apps = []
        
        def scan():
            self.app.root.after(0, self.progress.start)
            
            # Scan Registry (32-bit and 64-bit)
            self._scan_registry()
            
            # Scan Winget
            self._scan_winget()
            
            # Scan Chocolatey
            self._scan_choco()
            
            # Update UI
            self.app.root.after(0, self._populate_apps)
            self.app.root.after(0, self.progress.stop)
            self.app.root.after(0, lambda: self.app.log(f"✅ Found {len(self.installed_apps)} installed applications"))
        
        threading.Thread(target=scan, daemon=True).start()
    
    def _scan_registry(self):
        """Scan Windows Registry for installed apps."""
        registry_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]
        
        for hkey, path in registry_paths:
            try:
                with winreg.OpenKey(hkey, path) as key:
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, subkey_name) as subkey:
                                try:
                                    name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                    if not name or name.strip() == "":
                                        continue
                                    
                                    # Get additional info
                                    version = ""
                                    uninstall_cmd = ""
                                    install_location = ""
                                    
                                    try:
                                        version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                                    except:
                                        pass
                                    
                                    try:
                                        uninstall_cmd = winreg.QueryValueEx(subkey, "UninstallString")[0]
                                    except:
                                        pass
                                    
                                    try:
                                        install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                                    except:
                                        pass
                                    
                                    # Avoid duplicates
                                    if not any(app[0] == name for app in self.installed_apps):
                                        self.installed_apps.append((
                                            name, 
                                            "Registry", 
                                            version,
                                            uninstall_cmd, 
                                            install_location,
                                            subkey_name  # Registry key name for cleanup
                                        ))
                                except WindowsError:
                                    pass
                        except WindowsError:
                            pass
            except WindowsError:
                pass
    
    def _scan_winget(self):
        """Scan Winget for installed apps."""
        try:
            result = subprocess.run(
                ["winget", "list", "--disable-interactivity"],
                capture_output=True, text=True, timeout=60,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                # Skip header lines
                data_started = False
                for line in lines:
                    if '---' in line:
                        data_started = True
                        continue
                    if data_started and line.strip():
                        # Parse winget output (name, id, version, source)
                        parts = line.split()
                        if len(parts) >= 2:
                            # Try to extract name and ID
                            name = ' '.join(parts[:-2]) if len(parts) > 2 else parts[0]
                            version = parts[-2] if len(parts) > 2 else ""
                            
                            if not any(app[0] == name and app[1] == "Winget" for app in self.installed_apps):
                                self.installed_apps.append((
                                    name,
                                    "Winget",
                                    version,
                                    f"winget uninstall \"{name}\"",
                                    "",
                                    ""
                                ))
        except Exception as e:
            self.app.root.after(0, lambda: self.app.debug_log(f"Winget scan error: {e}"))
    
    def _scan_choco(self):
        """Scan Chocolatey for installed apps."""
        try:
            result = subprocess.run(
                ["choco", "list", "--local-only", "--limit-output"],
                capture_output=True, text=True, timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if '|' in line:
                        parts = line.split('|')
                        name = parts[0]
                        version = parts[1] if len(parts) > 1 else ""
                        
                        if not any(app[0] == name and app[1] == "Chocolatey" for app in self.installed_apps):
                            self.installed_apps.append((
                                name,
                                "Chocolatey",
                                version,
                                f"choco uninstall {name} -y",
                                "",
                                ""
                            ))
        except Exception as e:
            self.app.root.after(0, lambda: self.app.debug_log(f"Choco scan error: {e}"))
    
    def _populate_apps(self):
            """Populate the scrollable frame with checkboxes."""
            # Clear existing
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
            self.checkboxes.clear()
            
            # Sort alphabetically
            sorted_apps = sorted(self.installed_apps, key=lambda x: x[0].lower())
            
            # Apply current filters
            filter_text = self.filter_entry.get().lower()
            source_filter = self.source_var.get()
            
            filtered_apps = []
            for app_data in sorted_apps:
                name, source = app_data[0], app_data[1]
                if filter_text and filter_text not in name.lower():
                    continue
                if source_filter != "All" and source != source_filter:
                    continue
                filtered_apps.append(app_data)
            
            # Create header
            header_frame = ttk.Frame(self.scrollable_frame, style='Dark.TFrame')
            header_frame.pack(fill=tk.X, padx=5, pady=(5, 10))
            
            ttk.Label(header_frame, text="Application", style='DarkFrame.TLabel',
                    font=('Segoe UI', 10, 'bold'), width=50).pack(side=tk.LEFT)
            ttk.Label(header_frame, text="Source", style='DarkFrame.TLabel',
                    font=('Segoe UI', 10, 'bold'), width=12).pack(side=tk.LEFT, padx=(10, 0))
            ttk.Label(header_frame, text="Version", style='DarkFrame.TLabel',
                    font=('Segoe UI', 10, 'bold'), width=15).pack(side=tk.LEFT, padx=(10, 0))
            
            # Separator
            ttk.Separator(self.scrollable_frame, orient='horizontal').pack(fill=tk.X, padx=5)
            
            # Create rows with checkboxes
            for app_data in filtered_apps:
                name, source, version = app_data[0], app_data[1], app_data[2]
                
                row_frame = ttk.Frame(self.scrollable_frame, style='Dark.TFrame')
                row_frame.pack(fill=tk.X, padx=5, pady=2)
                
                # Checkbox
                var = tk.BooleanVar(value=False)
                
                # Color based on source
                if source == "Registry":
                    source_color = '#888888'
                elif source == "Winget":
                    source_color = '#90EE90'
                else:  # Chocolatey
                    source_color = '#DEB887'
                
                cb = ttk.Checkbutton(row_frame, text=name, variable=var,
                                    style='DarkFrame.TCheckbutton', width=50)
                cb.pack(side=tk.LEFT)
                
                # Bind mousewheel to checkbox too
                cb.bind("<MouseWheel>", self._on_mousewheel)
                
                source_label = ttk.Label(row_frame, text=source, width=12,
                                        foreground=source_color, background=self.colors['frame_bg'])
                source_label.pack(side=tk.LEFT, padx=(10, 0))
                
                version_label = ttk.Label(row_frame, text=version[:20] if version else "", width=15,
                                        foreground='#aaaaaa', background=self.colors['frame_bg'])
                version_label.pack(side=tk.LEFT, padx=(10, 0))
                
                # Store checkbox reference with full app data
                self.checkboxes[f"{name}_{source}"] = (var, app_data)
            
            self.count_label.config(text=f"{len(filtered_apps)} apps shown")
    
    def _filter_apps(self, event=None):
            """Filter the app list based on search and source."""
            self._populate_apps()
 
    def _uninstall_selected(self):
        """Uninstall selected applications."""
        # Get selected apps from checkboxes
        apps_to_uninstall = [app_data for var, app_data in self.checkboxes.values() if var.get()]
        
        if not apps_to_uninstall:
            self.app.log_warning("Select at least one application to uninstall")
            return
        
        # Confirm
        app_names = "\n".join([f"  • {app[0]}" for app in apps_to_uninstall[:10]])
        if len(apps_to_uninstall) > 10:
            app_names += f"\n  ... and {len(apps_to_uninstall) - 10} more"
        
        result = messagebox.askyesno(
            "Confirm Uninstall",
            f"Are you sure you want to uninstall {len(apps_to_uninstall)} application(s)?\n\n{app_names}\n\n"
            f"Cleanup options:\n"
            f"  • Registry cleanup: {'Yes' if self.cleanup_registry.get() else 'No'}\n"
            f"  • Program files cleanup: {'Yes' if self.cleanup_files.get() else 'No'}\n"
            f"  • AppData cleanup: {'Yes' if self.cleanup_appdata.get() else 'No'}",
            icon='warning'
        )
        
        if not result:
            return
        
        def uninstall_all():
            self.app.root.after(0, lambda: self.uninstall_btn.config(state='disabled'))
            self.app.root.after(0, self.progress.start)
            
            # Track successfully uninstalled apps for cleanup
            uninstalled_apps = []
            
            # === PHASE 1: UNINSTALL ALL APPS ===
            self.app.root.after(0, lambda: self.app.log("═══ PHASE 1: Uninstalling Applications ═══"))
            
            for app_data in apps_to_uninstall:
                name, source, version, uninstall_cmd, install_location, reg_key = app_data
                
                self.app.root.after(0, lambda n=name: self.app.log(f"🗑️ Uninstalling {n}..."))
                
                try:
                    # Uninstall based on source
                    if source == "Chocolatey":
                        result = subprocess.run(
                            ["choco", "uninstall", name, "-y", "--remove-dependencies"],
                            capture_output=True, timeout=300,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                    elif source == "Winget":
                        result = subprocess.run(
                            ["winget", "uninstall", "--name", name, "--silent"],
                            capture_output=True, timeout=300,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                    elif source == "Registry" and uninstall_cmd:
                        # Run the uninstall command
                        if "msiexec" in uninstall_cmd.lower():
                            cmd = uninstall_cmd + " /quiet /norestart"
                        else:
                            cmd = uninstall_cmd
                        result = subprocess.run(
                            cmd, shell=True, capture_output=True, timeout=300,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                    else:
                        result = None
                    
                    self.app.root.after(0, lambda n=name: self.app.log(f"✅ {n} uninstalled"))
                    uninstalled_apps.append(app_data)
                    
                except subprocess.TimeoutExpired:
                    self.app.root.after(0, lambda n=name: self.app.log(f"⚠️ {n} timed out (may still be uninstalling)"))
                    uninstalled_apps.append(app_data)  # Still try cleanup
                except Exception as e:
                    self.app.root.after(0, lambda n=name, err=str(e): self.app.log(f"❌ {n} failed: {err}"))
            
            # === PHASE 2: CLEANUP ===
            if uninstalled_apps and (self.cleanup_registry.get() or self.cleanup_files.get() or self.cleanup_appdata.get()):
                self.app.root.after(0, lambda: self.app.log(""))
                self.app.root.after(0, lambda: self.app.log("═══ PHASE 2: Cleaning Up Remnants ═══"))
                
                # Wait a moment for uninstallers to fully complete
                import time
                time.sleep(2)
                
                for app_data in uninstalled_apps:
                    name, source, version, uninstall_cmd, install_location, reg_key = app_data
                    self.app.root.after(0, lambda n=name: self.app.log(f"🧹 Cleaning up {n}..."))
                    self._perform_cleanup(name, install_location, reg_key)
            
            # === DONE ===
            self.app.root.after(0, lambda: self.app.log(""))
            self.app.root.after(0, lambda: self.app.log("🎉 Uninstall complete! Click 'SCAN' to refresh."))
            self.app.root.after(0, self.progress.stop)
            self.app.root.after(0, lambda: self.uninstall_btn.config(state='normal'))
        
        threading.Thread(target=uninstall_all, daemon=True).start()
    
    def _perform_cleanup(self, app_name, install_location, reg_key):
        """Perform cleanup after uninstall."""
        cleaned = []
        
        # Registry cleanup
        if self.cleanup_registry.get():
            cleaned_reg = self._cleanup_registry(app_name, reg_key)
            if cleaned_reg:
                cleaned.append("registry")
        
        # Program Files cleanup
        if self.cleanup_files.get():
            cleaned_files = self._cleanup_program_files(app_name, install_location)
            if cleaned_files:
                cleaned.append("program files")
        
        # AppData cleanup
        if self.cleanup_appdata.get():
            cleaned_appdata = self._cleanup_appdata(app_name)
            if cleaned_appdata:
                cleaned.append("appdata")
        
        if cleaned:
            self.app.root.after(0, lambda c=cleaned: self.app.log(f"   🧹 Cleaned: {', '.join(c)}"))
    
    def _cleanup_registry(self, app_name, reg_key):
        """Clean up registry entries for an app."""
        cleaned = False
        search_term = app_name.lower().replace(" ", "")
        
        # Common registry locations to check
        registry_paths = [
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node"),
        ]
        
        for hkey, base_path in registry_paths:
            try:
                with winreg.OpenKey(hkey, base_path, 0, winreg.KEY_READ) as key:
                    i = 0
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            if search_term in subkey_name.lower().replace(" ", ""):
                                try:
                                    winreg.DeleteKey(hkey, f"{base_path}\\{subkey_name}")
                                    cleaned = True
                                except:
                                    pass
                            i += 1
                        except WindowsError:
                            break
            except:
                pass
        
        return cleaned
    
    def _cleanup_program_files(self, app_name, install_location):
        """Clean up program files for an app."""
        cleaned = False
        search_term = app_name.lower().replace(" ", "")
        
        # Check provided install location first
        if install_location and os.path.exists(install_location):
            try:
                shutil.rmtree(install_location, ignore_errors=True)
                cleaned = True
            except:
                pass
        
        # Search common locations
        search_paths = [
            os.environ.get('ProgramFiles', 'C:\\Program Files'),
            os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'),
            os.environ.get('ProgramW6432', 'C:\\Program Files'),
        ]
        
        for base_path in search_paths:
            if not base_path or not os.path.exists(base_path):
                continue
            try:
                for folder in os.listdir(base_path):
                    if search_term in folder.lower().replace(" ", ""):
                        folder_path = os.path.join(base_path, folder)
                        try:
                            shutil.rmtree(folder_path, ignore_errors=True)
                            cleaned = True
                        except:
                            pass
            except:
                pass
        
        return cleaned
    
    def _cleanup_appdata(self, app_name):
        """Clean up AppData folders for an app."""
        cleaned = False
        search_term = app_name.lower().replace(" ", "")
        
        appdata_paths = [
            os.environ.get('APPDATA', ''),           # Roaming
            os.environ.get('LOCALAPPDATA', ''),      # Local
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs'),
        ]
        
        for base_path in appdata_paths:
            if not base_path or not os.path.exists(base_path):
                continue
            try:
                for folder in os.listdir(base_path):
                    if search_term in folder.lower().replace(" ", ""):
                        folder_path = os.path.join(base_path, folder)
                        try:
                            shutil.rmtree(folder_path, ignore_errors=True)
                            cleaned = True
                        except:
                            pass
            except:
                pass
        
        return cleaned
    
    def _cleanup_only(self):
        """Run cleanup without uninstalling (for leftover files)."""
        selected_apps = [app_data for var, app_data in self.checkboxes.values() if var.get()]
        
        if not selected_apps:  # <-- CHANGED from 'selected' to 'selected_apps'
            self.app.log_warning("Select applications to clean up")
            return
        
        result = messagebox.askyesno(
            "Cleanup Only",
            "This will search for and remove leftover files/registry entries "
            "for the selected applications WITHOUT running the uninstaller.\n\n"
            "Use this for apps that are already uninstalled but left remnants.\n\n"
            "Continue?",
            icon='question'
        )
        
        if not result:
            return
        
        def cleanup():
            self.app.root.after(0, self.progress.start)
            
            for app_data in selected_apps:
                name = app_data[0]
                install_location = app_data[4]
                reg_key = app_data[5]
                
                self.app.root.after(0, lambda n=name: self.app.log(f"🧹 Cleaning up {n}..."))
                self._perform_cleanup(name, install_location, reg_key)
            
            self.app.root.after(0, lambda: self.app.log_success("Cleanup complete!"))
            self.app.root.after(0, self.progress.stop)
        
        threading.Thread(target=cleanup, daemon=True).start()
    
    def _export_list(self):
        """Export installed apps list to a text file."""
        if not self.installed_apps:
            self.app.log_warning("Scan for apps first")
            return
        
        from tkinter import filedialog
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv")],
            title="Export Installed Apps"
        )
        
        if not filepath:
            return
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                if filepath.endswith('.csv'):
                    f.write("Name,Source,Version\n")
                    for app_data in sorted(self.installed_apps, key=lambda x: x[0].lower()):
                        f.write(f'"{app_data[0]}","{app_data[1]}","{app_data[2]}"\n')
                else:
                    f.write("Installed Applications\n")
                    f.write("=" * 50 + "\n\n")
                    for app_data in sorted(self.installed_apps, key=lambda x: x[0].lower()):
                        f.write(f"{app_data[0]} ({app_data[1]}) - v{app_data[2]}\n")
            
            self.app.log(f"✅ Exported to {filepath}")
        except Exception as e:
            self.app.log(f"❌ Export failed: {e}")