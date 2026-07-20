"""
New PC Setup Checklist Tab UI
Guided workflow for setting up new machines with one-click actions.
"""

import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import threading
import subprocess
import os


# Default checklist items with their PowerShell commands
SETUP_TASKS = [
    {
        "category": "System Configuration",
        "tasks": [
            ("Rename Computer", "rename_computer", "Rename this PC to a standard naming convention"),
            ("Set Timezone", "set_timezone", "Set timezone to Eastern (or select)"),
            ("Set Power Plan - High Performance", "set_power_plan", "Disable sleep on AC, set High Performance"),
            ("Disable Fast Startup", "disable_fast_startup", "Prevents wake issues and update problems"),
            ("Enable Remote Desktop", "enable_rdp", "Allow RDP connections to this machine"),
            ("Enable WinRM", "enable_winrm", "Enable PowerShell remoting"),
            ("Disable Hibernation", "disable_hibernate", "Saves disk space, prevents issues"),
        ]
    },
    {
        "category": "Network & Domain",
        "tasks": [
            ("Check Domain Status", "check_domain", "Show current domain/workgroup membership"),
            ("Set DNS Servers", "set_dns", "Set DNS to your standard servers"),
            ("Disable IPv6", "disable_ipv6", "Disable IPv6 on all adapters (if policy requires)"),
            ("Map Network Drives", "map_drives", "Run your Map-Drives script"),
        ]
    },
    {
        "category": "Security & Updates",
        "tasks": [
            ("Check Windows Activation", "check_activation", "Verify Windows is activated"),
            ("Enable BitLocker", "enable_bitlocker", "Enable BitLocker on C: drive"),
            ("Run Windows Update", "run_updates", "Check and install pending updates"),
            ("Set UAC to Default", "set_uac", "Ensure UAC is at recommended level"),
            ("Disable NetBIOS", "disable_netbios", "Security hardening - disable NetBIOS over TCP/IP"),
        ]
    },
    {
        "category": "Cleanup & Optimization",
        "tasks": [
            ("Remove Bloatware", "remove_bloatware", "Remove pre-installed crapware (see Bloatware tab)"),
            ("Disable Cortana", "disable_cortana", "Disable Cortana search assistant"),
            ("Disable Telemetry", "disable_telemetry", "Minimize Windows telemetry/data collection"),
            ("Clear Start Menu Pins", "clear_start", "Remove default pinned apps from Start"),
            ("Disable Tips & Suggestions", "disable_tips", "Turn off Windows tips, tricks, suggestions"),
        ]
    },
    {
        "category": "Applications",
        "tasks": [
            ("Install Standard Apps (Winget)", "install_winget_apps", "Switch to Winget tab to install apps"),
            ("Install Standard Apps (Choco)", "install_choco_apps", "Switch to Chocolatey tab to install apps"),
            ("Set Default Browser", "set_browser", "Open default apps settings"),
            ("Install Printers", "install_printers", "Switch to Printer tab or run printer script"),
        ]
    },
    {
        "category": "Final Checks",
        "tasks": [
            ("Run Disk Cleanup", "disk_cleanup", "Clean temp files, Windows update cache"),
            ("Check Device Manager", "check_devices", "Look for missing/problem drivers"),
            ("Create Restore Point", "create_restore", "Create a system restore point"),
            ("Verify All Settings", "verify_all", "Run a quick audit of all above settings"),
        ]
    },
]


class SetupChecklistTab:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.colors = app.colors
        self.task_vars = {}  # {task_id: BooleanVar}
        self.task_labels = {}
        
        self.create_tab()
    
    def create_tab(self):
        """Create the Setup Checklist tab."""
        tab = self.parent
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)
        
        # Header
        header = ttk.Frame(tab, style='DarkBg.TFrame')
        header.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
        
        ttk.Button(header, text="✅ MARK ALL COMPLETE", style='Success.TButton',
                  command=self._mark_all_complete).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(header, text="🔄 RESET ALL", style='Warning.TButton',
                  command=self._reset_all).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(header, text="📋 EXPORT CHECKLIST", style='Dark.TButton',
                  command=self._export_checklist).pack(side=tk.LEFT, padx=(0, 10))
        
        self.progress_label = ttk.Label(header, text="0/0 complete", 
                                       style='DarkFrame.TLabel', font=('Segoe UI', 10, 'bold'))
        self.progress_label.pack(side=tk.RIGHT, padx=10)
        
        # Progress bar
        self.progress = ttk.Progressbar(tab, mode='determinate', maximum=100)
        self.progress.grid(row=1, column=0, sticky='ew', padx=10, pady=(0, 5))
        
        # Scrollable checklist
        outer = ttk.Frame(tab, style='DarkBg.TFrame')
        outer.grid(row=2, column=0, sticky='nsew', padx=5, pady=5)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(0, weight=1)
        tab.rowconfigure(2, weight=1)
        
        canvas = tk.Canvas(outer, bg=self.colors['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient=tk.VERTICAL, command=canvas.yview)
        self.scrollable = ttk.Frame(canvas, style='DarkBg.TFrame')
        
        self.scrollable.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        self.canvas_window = canvas.create_window((0, 0), window=self.scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(self.canvas_window, width=e.width))
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Build checklist
        self._build_checklist()
        self._update_progress()
    
    def _build_checklist(self):
        """Build the checklist UI."""
        from ui.collapsible_frame import CollapsibleFrame
        
        for section in SETUP_TASKS:
            category = section['category']
            
            section_frame = CollapsibleFrame(self.scrollable, title=f"📋 {category}",
                                           style_colors=self.colors)
            section_frame.pack(fill=tk.X, padx=10, pady=(0, 8))
            
            for task_name, task_id, description in section['tasks']:
                row = ttk.Frame(section_frame.content, style='Dark.TFrame')
                row.pack(fill=tk.X, pady=3)
                
                # Checkbox
                var = tk.BooleanVar(value=False)
                self.task_vars[task_id] = var
                
                cb = ttk.Checkbutton(row, text="", variable=var, 
                                    style='Dark.TCheckbutton',
                                    command=self._update_progress)
                cb.pack(side=tk.LEFT, padx=(0, 5))
                
                # Run button
                btn = ttk.Button(row, text="▶", style='Dark.TButton', width=3,
                               command=lambda tid=task_id: self._run_task(tid))
                btn.pack(side=tk.LEFT, padx=(0, 8))
                
                # Task name and description
                name_label = ttk.Label(row, text=task_name, style='DarkFrame.TLabel',
                                      font=('Segoe UI', 9, 'bold'))
                name_label.pack(side=tk.LEFT, padx=(0, 10))
                
                desc_label = ttk.Label(row, text=description, style='DarkFrame.TLabel',
                                      font=('Segoe UI', 8))
                desc_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
                
                self.task_labels[task_id] = name_label
    
    def _update_progress(self, *args):
        """Update progress bar and label."""
        total = len(self.task_vars)
        completed = sum(1 for v in self.task_vars.values() if v.get())
        
        percent = (completed / total * 100) if total > 0 else 0
        self.progress['value'] = percent
        self.progress_label.config(text=f"{completed}/{total} complete ({percent:.0f}%)")
    
    def _run_task(self, task_id):
        """Execute a setup task."""
        commands = {
            'rename_computer': self._task_rename_computer,
            'set_timezone': self._task_set_timezone,
            'set_power_plan': lambda: self._run_ps("powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c; powercfg /change standby-timeout-ac 0; powercfg /change monitor-timeout-ac 30", "Power plan set to High Performance, sleep disabled"),
            'disable_fast_startup': lambda: self._run_ps("Set-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Power' -Name HiberbootEnabled -Value 0", "Fast Startup disabled"),
            'enable_rdp': lambda: self._run_ps("Set-ItemProperty -Path 'HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server' -Name fDenyTSConnections -Value 0; Enable-NetFirewallRule -DisplayGroup 'Remote Desktop'", "Remote Desktop enabled"),
            'enable_winrm': lambda: self._run_ps("Enable-PSRemoting -Force -SkipNetworkProfileCheck", "WinRM enabled"),
            'disable_hibernate': lambda: self._run_ps("powercfg /hibernate off", "Hibernation disabled"),
            'check_domain': lambda: self._run_ps("(Get-CimInstance Win32_ComputerSystem).Domain", "Domain check"),
            'set_dns': self._task_set_dns,
            'disable_ipv6': lambda: self._run_ps("Get-NetAdapterBinding -ComponentId ms_tcpip6 | Disable-NetAdapterBinding -ComponentId ms_tcpip6", "IPv6 disabled on all adapters"),
            'map_drives': lambda: self.app.powershell.run("& '.\\scripts\\Map-Drives.ps1'", "Map Drives", False),
            'check_activation': lambda: self._run_ps("(Get-CimInstance -Query 'select * from SoftwareLicensingProduct where PartialProductKey is not null').LicenseStatus", "Activation status (1=Activated)"),
            'enable_bitlocker': lambda: self._run_ps("Enable-BitLocker -MountPoint 'C:' -EncryptionMethod XtsAes256 -UsedSpaceOnly -RecoveryPasswordProtector", "BitLocker enabling..."),
            'run_updates': lambda: self.app.log("Switch to the Updates tab to run Windows Update"),
            'set_uac': lambda: self._run_ps("Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System' -Name EnableLUA -Value 1; Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System' -Name ConsentPromptBehaviorAdmin -Value 5", "UAC set to default"),
            'disable_netbios': lambda: self._run_ps("Get-WmiObject Win32_NetworkAdapterConfiguration | Where-Object {$_.TcpipNetbiosOptions -ne $null} | ForEach-Object { $_.SetTcpipNetbios(2) }", "NetBIOS disabled"),
            'remove_bloatware': lambda: self.app.log("Use the Bloatware Remover tab"),
            'disable_cortana': lambda: self._run_ps("New-ItemProperty -Path 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search' -Name AllowCortana -Value 0 -PropertyType DWORD -Force", "Cortana disabled"),
            'disable_telemetry': lambda: self._run_ps("Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection' -Name AllowTelemetry -Value 0 -Force", "Telemetry minimized"),
            'clear_start': lambda: self._run_ps("Remove-Item 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\CloudStore\\Store\\Cache\\DefaultAccount' -Recurse -Force -ErrorAction SilentlyContinue", "Start menu cleared (restart Explorer to see)"),
            'disable_tips': lambda: self._run_ps("Set-ItemProperty -Path 'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager' -Name SubscribedContent-338389Enabled -Value 0; Set-ItemProperty -Path 'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager' -Name SoftLandingEnabled -Value 0", "Tips disabled"),
            'install_winget_apps': lambda: self.app.log("Switch to the Winget tab to install applications"),
            'install_choco_apps': lambda: self.app.log("Switch to the Chocolatey tab to install applications"),
            'set_browser': lambda: self._run_ps("Start-Process 'ms-settings:defaultapps'", "Opened Default Apps settings"),
            'install_printers': lambda: self.app.log("Use the Printer tab or run Add-Printer script"),
            'disk_cleanup': lambda: self._run_ps("cleanmgr /sagerun:1", "Disk Cleanup launched"),
            'check_devices': lambda: self._run_ps("Start-Process devmgmt.msc", "Device Manager opened"),
            'create_restore': lambda: self._run_ps("Checkpoint-Computer -Description 'IT Admin Toolkit Setup' -RestorePointType MODIFY_SETTINGS", "Restore point created"),
            'verify_all': self._task_verify_all,
        }
        
        action = commands.get(task_id)
        if action:
            action()
            # Mark as complete
            if task_id in self.task_vars:
                self.task_vars[task_id].set(True)
                self._update_progress()
        else:
            self.app.log_warning(f"No action defined for: {task_id}")
    
    def _run_ps(self, script, success_msg):
        """Run a PowerShell command in background."""
        def run():
            try:
                result = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", script],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    output = result.stdout.strip()
                    self.app.log_success(f"{success_msg}" + (f"\n{output}" if output else ""))
                else:
                    self.app.log_error(f"Failed: {result.stderr.strip()[:100]}")
            except Exception as e:
                self.app.log_error(f"Error: {str(e)}")
        
        threading.Thread(target=run, daemon=True).start()
    
    def _task_rename_computer(self):
        """Prompt for new computer name and rename."""
        current = os.environ.get('COMPUTERNAME', '')
        new_name = simpledialog.askstring("Rename Computer", 
                                         f"Current: {current}\nEnter new name:",
                                         parent=self.app.root)
        if new_name:
            self._run_ps(f"Rename-Computer -NewName '{new_name}' -Force", 
                        f"Computer renamed to {new_name} (reboot required)")
    
    def _task_set_timezone(self):
        """Set timezone."""
        self._run_ps("Set-TimeZone -Id 'Eastern Standard Time'", "Timezone set to Eastern")
    
    def _task_set_dns(self):
        """Set DNS servers."""
        dns_primary = simpledialog.askstring("Set DNS", "Primary DNS (e.g., 8.8.8.8):",
                                           parent=self.app.root)
        if dns_primary:
            dns_secondary = simpledialog.askstring("Set DNS", "Secondary DNS (e.g., 8.8.4.4):",
                                                  parent=self.app.root)
            if dns_secondary:
                script = f"""
                $adapters = Get-NetAdapter | Where-Object {{$_.Status -eq 'Up'}}
                foreach ($a in $adapters) {{
                    Set-DnsClientServerAddress -InterfaceIndex $a.ifIndex -ServerAddresses ('{dns_primary}', '{dns_secondary}')
                }}
                """
                self._run_ps(script, f"DNS set to {dns_primary}, {dns_secondary}")
    
    def _task_verify_all(self):
        """Run a quick verification of common settings."""
        script = """
        $results = @()
        $results += "Computer: $env:COMPUTERNAME"
        $results += "Domain: $(Get-CimInstance Win32_ComputerSystem).Domain"
        $results += "Timezone: $(Get-TimeZone).Id"
        $results += "RDP: $((Get-ItemProperty 'HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server').fDenyTSConnections -eq 0)"
        $results += "Fast Startup: $((Get-ItemProperty 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Power' -ErrorAction SilentlyContinue).HiberbootEnabled)"
        $results += "Power Plan: $(powercfg /getactivescheme)"
        $results -join "`n"
        """
        self._run_ps(script, "Verification complete")
    
    def _mark_all_complete(self):
        """Mark all tasks as complete."""
        for var in self.task_vars.values():
            var.set(True)
        self._update_progress()
    
    def _reset_all(self):
        """Reset all tasks."""
        for var in self.task_vars.values():
            var.set(False)
        self._update_progress()
    
    def _export_checklist(self):
        """Export checklist status."""
        from tkinter import filedialog
        from datetime import datetime
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile=f"SetupChecklist_{os.environ.get('COMPUTERNAME', '')}_{datetime.now().strftime('%Y%m%d')}.txt"
        )
        
        if filepath:
            with open(filepath, 'w') as f:
                f.write(f"PC Setup Checklist - {os.environ.get('COMPUTERNAME', '')}\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
                f.write("=" * 50 + "\n\n")
                
                for section in SETUP_TASKS:
                    f.write(f"\n{section['category']}\n")
                    f.write("-" * 40 + "\n")
                    for task_name, task_id, description in section['tasks']:
                        done = "✅" if self.task_vars.get(task_id, tk.BooleanVar()).get() else "☐"
                        f.write(f"  {done} {task_name} - {description}\n")
            
            self.app.log_success(f"Checklist saved: {filepath}")
