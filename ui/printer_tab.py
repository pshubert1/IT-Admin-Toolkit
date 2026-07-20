"""
Printer Manager Tab UI
Add, remove, and manage printers with one-click actions.
"""

import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import threading
import subprocess


class PrinterTab:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.colors = app.colors
        self.printers = []
        
        self.create_tab()
        # Auto-scan on load
        self._refresh_printers()
    
    def create_tab(self):
        """Create the Printer Manager tab."""
        tab = self.parent
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)
        
        # Header / Actions
        header = ttk.Frame(tab, style='DarkBg.TFrame')
        header.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
        
        ttk.Button(header, text="🔄 REFRESH", style='Dark.TButton',
                  command=self._refresh_printers).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(header, text="➕ ADD PRINTER (IP)", style='Success.TButton',
                  command=self._add_printer_ip).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(header, text="➕ ADD PRINTER (SHARE)", style='Success.TButton',
                  command=self._add_printer_share).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(header, text="🗑️ REMOVE SELECTED", style='Danger.TButton',
                  command=self._remove_printer).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(header, text="🧹 CLEAR QUEUE", style='Warning.TButton',
                  command=self._clear_queue).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(header, text="🔄 RESTART SPOOLER", style='Dark.TButton',
                  command=self._restart_spooler).pack(side=tk.LEFT)
        
        # Printer list
        list_frame = ttk.LabelFrame(tab, text="🖨️ Installed Printers",
                                   padding="10", style='Dark.TLabelframe')
        list_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        columns = ("name", "port", "driver", "status", "default")
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings',
                                style='Dark.Treeview', height=10)
        
        self.tree.heading("name", text="Printer Name")
        self.tree.heading("port", text="Port/IP")
        self.tree.heading("driver", text="Driver")
        self.tree.heading("status", text="Status")
        self.tree.heading("default", text="Default")
        
        self.tree.column("name", width=200)
        self.tree.column("port", width=150)
        self.tree.column("driver", width=200)
        self.tree.column("status", width=100)
        self.tree.column("default", width=60)
        
        tree_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.grid(row=0, column=0, sticky='nsew')
        tree_scroll.grid(row=0, column=1, sticky='ns')
        
        # Actions for selected printer
        action_frame = ttk.LabelFrame(tab, text="Printer Actions",
                                     padding="10", style='Dark.TLabelframe')
        action_frame.grid(row=2, column=0, sticky='ew', padx=5, pady=5)
        
        ttk.Button(action_frame, text="⭐ SET AS DEFAULT", style='Dark.TButton',
                  command=self._set_default).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(action_frame, text="🖨️ TEST PRINT", style='Dark.TButton',
                  command=self._test_print).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(action_frame, text="⚙️ PROPERTIES", style='Dark.TButton',
                  command=self._open_properties).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(action_frame, text="📂 OPEN QUEUE", style='Dark.TButton',
                  command=self._open_queue).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(action_frame, text="🔄 REINSTALL DRIVER", style='Warning.TButton',
                  command=self._reinstall_driver).pack(side=tk.LEFT)
        
        # Status
        self.status_label = ttk.Label(tab, text="", style='DarkFrame.TLabel')
        self.status_label.grid(row=3, column=0, sticky='ew', padx=10, pady=5)
    
    def _refresh_printers(self):
        """Refresh the printer list."""
        threading.Thread(target=self._do_refresh, daemon=True).start()
    
    def _do_refresh(self):
        """Background refresh of printer list."""
        try:
            script = """
            Get-Printer | ForEach-Object {
                $port = (Get-PrinterPort -Name $_.PortName -ErrorAction SilentlyContinue).PrinterHostAddress
                if (-not $port) { $port = $_.PortName }
                $default = if ($_.Name -eq (Get-CimInstance -ClassName Win32_Printer | Where-Object { $_.Default -eq $true }).Name) { "Yes" } else { "No" }
                "$($_.Name)|$port|$($_.DriverName)|$($_.PrinterStatus)|$default"
            }
            """
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", script],
                capture_output=True, text=True, timeout=15
            )
            
            self.printers = []
            if result.returncode == 0 and result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    parts = line.strip().split('|')
                    if len(parts) >= 5:
                        self.printers.append({
                            'name': parts[0],
                            'port': parts[1],
                            'driver': parts[2],
                            'status': parts[3],
                            'default': parts[4],
                        })
            
            self.parent.after(0, self._update_tree)
        except Exception as e:
            self.parent.after(0, lambda: self.status_label.config(text=f"Error: {str(e)[:50]}"))
    
    def _update_tree(self):
        """Update treeview."""
        self.tree.delete(*self.tree.get_children())
        for p in self.printers:
            self.tree.insert('', tk.END, values=(
                p['name'], p['port'], p['driver'], p['status'], p['default']
            ))
        self.status_label.config(text=f"Found {len(self.printers)} printer(s)")
    
    def _get_selected_printer(self):
        """Get the selected printer name."""
        selection = self.tree.selection()
        if not selection:
            self.app.log_warning("Select a printer first")
            return None
        return self.tree.item(selection[0], 'values')[0]
    
    def _add_printer_ip(self):
        """Add a network printer by IP address."""
        ip = simpledialog.askstring("Add Printer", "Enter printer IP address:",
                                   parent=self.app.root)
        if not ip:
            return
        
        driver = simpledialog.askstring("Add Printer", 
                                       "Driver name (e.g., 'HP Universal Printing PCL 6'):",
                                       parent=self.app.root)
        if not driver:
            driver = "HP Universal Printing PCL 6"
        
        name = simpledialog.askstring("Add Printer",
                                     f"Printer display name:",
                                     initialvalue=f"Printer-{ip}",
                                     parent=self.app.root)
        if not name:
            name = f"Printer-{ip}"
        
        script = f"""
        $portName = "IP_{ip.replace('.', '_')}"
        Add-PrinterPort -Name $portName -PrinterHostAddress "{ip}" -ErrorAction SilentlyContinue
        Add-Printer -Name "{name}" -DriverName "{driver}" -PortName $portName
        """
        
        def run():
            try:
                result = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", script],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    self.parent.after(0, lambda: self.app.log_success(f"Printer '{name}' added at {ip}"))
                    self.parent.after(0, self._refresh_printers)
                else:
                    self.parent.after(0, lambda: self.app.log_error(f"Failed: {result.stderr.strip()[:100]}"))
            except Exception as e:
                self.parent.after(0, lambda: self.app.log_error(f"Error: {str(e)}"))
        
        threading.Thread(target=run, daemon=True).start()
    
    def _add_printer_share(self):
        """Add a shared printer by UNC path."""
        share = simpledialog.askstring("Add Shared Printer",
                                      "Enter share path (e.g., \\\\server\\PrinterName):",
                                      parent=self.app.root)
        if not share:
            return
        
        def run():
            try:
                result = subprocess.run(
                    ["powershell", "-NoProfile", "-Command",
                     f"Add-Printer -ConnectionName '{share}'"],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    self.parent.after(0, lambda: self.app.log_success(f"Shared printer added: {share}"))
                    self.parent.after(0, self._refresh_printers)
                else:
                    self.parent.after(0, lambda: self.app.log_error(f"Failed: {result.stderr.strip()[:100]}"))
            except Exception as e:
                self.parent.after(0, lambda: self.app.log_error(f"Error: {str(e)}"))
        
        threading.Thread(target=run, daemon=True).start()
    
    def _remove_printer(self):
        """Remove selected printer."""
        name = self._get_selected_printer()
        if not name:
            return
        
        confirm = messagebox.askyesno("Remove Printer", f"Remove '{name}'?", parent=self.app.root)
        if confirm:
            def run():
                try:
                    subprocess.run(
                        ["powershell", "-NoProfile", "-Command", f"Remove-Printer -Name '{name}'"],
                        capture_output=True, text=True, timeout=15
                    )
                    self.parent.after(0, lambda: self.app.log_success(f"Removed: {name}"))
                    self.parent.after(0, self._refresh_printers)
                except Exception as e:
                    self.parent.after(0, lambda: self.app.log_error(str(e)))
            threading.Thread(target=run, daemon=True).start()
    
    def _set_default(self):
        """Set selected printer as default."""
        name = self._get_selected_printer()
        if name:
            subprocess.Popen(["powershell", "-NoProfile", "-Command",
                            f"Set-DefaultPrinter -Name '{name}'"])
            self.app.log_success(f"Default printer: {name}")
            self._refresh_printers()
    
    def _test_print(self):
        """Send a test page to selected printer."""
        name = self._get_selected_printer()
        if name:
            script = f"""
            $printer = Get-CimInstance -ClassName Win32_Printer | Where-Object {{ $_.Name -eq '{name}' }}
            $printer | Invoke-CimMethod -MethodName PrintTestPage
            """
            subprocess.Popen(["powershell", "-NoProfile", "-Command", script])
            self.app.log(f"Test page sent to: {name}")
    
    def _clear_queue(self):
        """Clear all print jobs."""
        name = self._get_selected_printer()
        if name:
            script = f"Get-PrintJob -PrinterName '{name}' | Remove-PrintJob"
            subprocess.Popen(["powershell", "-NoProfile", "-Command", script])
            self.app.log_success(f"Print queue cleared: {name}")
    
    def _restart_spooler(self):
        """Restart the Print Spooler service."""
        def run():
            try:
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command",
                     "Restart-Service Spooler -Force"],
                    capture_output=True, text=True, timeout=15
                )
                self.parent.after(0, lambda: self.app.log_success("Print Spooler restarted"))
                self.parent.after(500, self._refresh_printers)
            except Exception as e:
                self.parent.after(0, lambda: self.app.log_error(str(e)))
        threading.Thread(target=run, daemon=True).start()
    
    def _open_properties(self):
        """Open printer properties dialog."""
        name = self._get_selected_printer()
        if name:
            subprocess.Popen(["rundll32", "printui.dll,PrintUIEntry", "/p", "/n", name])
    
    def _open_queue(self):
        """Open printer queue window."""
        name = self._get_selected_printer()
        if name:
            subprocess.Popen(["rundll32", "printui.dll,PrintUIEntry", "/o", "/n", name])
    
    def _reinstall_driver(self):
        """Remove and re-add the printer driver."""
        name = self._get_selected_printer()
        if not name:
            return
        
        confirm = messagebox.askyesno("Reinstall Driver",
                                     f"This will remove and re-add the driver for '{name}'.\nContinue?",
                                     parent=self.app.root)
        if confirm:
            self.app.log("Reinstalling driver... (check Printer Properties after)")
            subprocess.Popen(["rundll32", "printui.dll,PrintUIEntry", "/p", "/n", name])
