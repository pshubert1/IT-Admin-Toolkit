"""
System Health Dashboard Tab UI
Shows at-a-glance system information when the app opens.
"""

import tkinter as tk
from tkinter import ttk
import threading
import subprocess
import os
import platform
from datetime import datetime


class HealthDashboardTab:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.colors = app.colors
        self.info_labels = {}
        
        self.create_tab()
        # Auto-refresh on load
        self._refresh_all()
    
    def create_tab(self):
        """Create the System Health Dashboard tab."""
        tab = self.parent
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(0, weight=1)
        
        # Scrollable frame
        outer = ttk.Frame(tab, style='DarkBg.TFrame')
        outer.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(0, weight=1)
        
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
        
        # Refresh button
        btn_frame = ttk.Frame(self.scrollable, style='DarkBg.TFrame')
        btn_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        ttk.Button(btn_frame, text="🔄 REFRESH ALL", style='Success.TButton',
                  command=self._refresh_all).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(btn_frame, text="📋 COPY TO CLIPBOARD", style='Dark.TButton',
                  command=self._copy_to_clipboard).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(btn_frame, text="💾 EXPORT REPORT", style='Dark.TButton',
                  command=self._export_report).pack(side=tk.LEFT)
        
        self.refresh_label = ttk.Label(btn_frame, text="", style='DarkFrame.TLabel')
        self.refresh_label.pack(side=tk.RIGHT, padx=10)
        
        # === System Overview ===
        self._create_section("🖥️ System Overview", [
            ("Computer Name", "computer_name"),
            ("Domain / Workgroup", "domain"),
            ("Windows Version", "os_version"),
            ("OS Build", "os_build"),
            ("Install Date", "install_date"),
            ("Architecture", "arch"),
            ("Serial Number", "serial"),
            ("Manufacturer / Model", "model"),
        ])
        
        # === Performance ===
        self._create_section("📊 Performance", [
            ("CPU", "cpu_name"),
            ("CPU Usage", "cpu_usage"),
            ("RAM", "ram_total"),
            ("RAM Usage", "ram_usage"),
            ("System Drive (C:)", "disk_c"),
            ("Uptime", "uptime"),
            ("Last Boot", "last_boot"),
            ("Boot Type", "boot_type"),
        ])
        
        # === Network ===
        self._create_section("🌐 Network", [
            ("IP Address (Local)", "ip_local"),
            ("IP Address (External)", "ip_external"),
            ("Default Gateway", "gateway"),
            ("DNS Servers", "dns"),
            ("MAC Address", "mac"),
            ("Connection Type", "connection_type"),
        ])
        
        # === Security ===
        self._create_section("🛡️ Security", [
            ("Antivirus", "av_status"),
            ("Firewall", "firewall"),
            ("Windows Defender", "defender"),
            ("BitLocker (C:)", "bitlocker"),
            ("UAC Level", "uac"),
            ("Secure Boot", "secure_boot"),
            ("TPM", "tpm"),
        ])
        
        # === Updates & Maintenance ===
        self._create_section("🔄 Updates & Maintenance", [
            ("Last Windows Update", "last_update"),
            ("Pending Updates", "pending_updates"),
            ("Pending Reboot", "reboot_needed"),
            (".NET Versions", "dotnet"),
            ("PowerShell Version", "ps_version"),
        ])
    
    def _create_section(self, title, fields):
        """Create a dashboard section with label/value pairs."""
        from ui.collapsible_frame import CollapsibleFrame
        
        section = CollapsibleFrame(self.scrollable, title=title, style_colors=self.colors)
        section.pack(fill=tk.X, padx=10, pady=(0, 8))
        
        for label_text, key in fields:
            row = ttk.Frame(section.content, style='Dark.TFrame')
            row.pack(fill=tk.X, pady=2)
            
            ttk.Label(row, text=f"{label_text}:", style='DarkFrame.TLabel',
                     font=('Segoe UI', 9, 'bold'), width=22, anchor='w'
                     ).pack(side=tk.LEFT, padx=(5, 10))
            
            value_label = ttk.Label(row, text="Loading...", style='DarkFrame.TLabel',
                                   font=('Consolas', 9))
            value_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            self.info_labels[key] = value_label
    
    def _refresh_all(self):
        """Refresh all system information."""
        self.refresh_label.config(text="Refreshing...")
        threading.Thread(target=self._collect_all_info, daemon=True).start()
    
    def _collect_all_info(self):
        """Collect all system info in background."""
        info = {}
        
        # System Overview
        info['computer_name'] = os.environ.get('COMPUTERNAME', 'Unknown')
        info['domain'] = os.environ.get('USERDOMAIN', 'WORKGROUP')
        info['arch'] = platform.machine()
        info['os_version'] = platform.platform()
        
        try:
            # Detailed system info via PowerShell
            ps_script = """
            $os = Get-CimInstance Win32_OperatingSystem
            $cs = Get-CimInstance Win32_ComputerSystem
            $bios = Get-CimInstance Win32_BIOS
            $cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
            $disk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
            
            # Network
            $adapter = Get-CimInstance Win32_NetworkAdapterConfiguration | Where-Object { $_.IPEnabled -eq $true } | Select-Object -First 1
            
            # Output
            "OS_VER|$($os.Caption) $($os.Version)"
            "OS_BUILD|$($os.BuildNumber)"
            "INSTALL|$($os.InstallDate.ToString('yyyy-MM-dd'))"
            "SERIAL|$($bios.SerialNumber)"
            "MODEL|$($cs.Manufacturer) $($cs.Model)"
            "CPU|$($cpu.Name)"
            "CPU_USAGE|$($cpu.LoadPercentage)%"
            "RAM_TOTAL|$([math]::Round($cs.TotalPhysicalMemory/1GB, 1)) GB"
            "RAM_FREE|$([math]::Round($os.FreePhysicalMemory/1MB, 1)) GB free"
            "DISK_C|$([math]::Round($disk.Size/1GB, 0)) GB total, $([math]::Round($disk.FreeSpace/1GB, 1)) GB free ($([math]::Round(($disk.FreeSpace/$disk.Size)*100, 0))%)"
            "UPTIME|$((Get-Date) - $os.LastBootUpTime | ForEach-Object { '{0}d {1}h {2}m' -f $_.Days, $_.Hours, $_.Minutes })"
            "LAST_BOOT|$($os.LastBootUpTime.ToString('yyyy-MM-dd HH:mm'))"
            "IP|$($adapter.IPAddress[0])"
            "GW|$($adapter.DefaultIPGateway -join ', ')"
            "DNS|$($adapter.DNSServerSearchOrder -join ', ')"
            "MAC|$($adapter.MACAddress)"
            """
            
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True, text=True, timeout=20
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if '|' in line:
                        key, value = line.strip().split('|', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        if key == 'OS_VER': info['os_version'] = value
                        elif key == 'OS_BUILD': info['os_build'] = value
                        elif key == 'INSTALL': info['install_date'] = value
                        elif key == 'SERIAL': info['serial'] = value
                        elif key == 'MODEL': info['model'] = value
                        elif key == 'CPU': info['cpu_name'] = value
                        elif key == 'CPU_USAGE': info['cpu_usage'] = value
                        elif key == 'RAM_TOTAL': info['ram_total'] = value
                        elif key == 'RAM_FREE': info['ram_usage'] = value
                        elif key == 'DISK_C': info['disk_c'] = value
                        elif key == 'UPTIME': info['uptime'] = value
                        elif key == 'LAST_BOOT': info['last_boot'] = value
                        elif key == 'IP': info['ip_local'] = value
                        elif key == 'GW': info['gateway'] = value
                        elif key == 'DNS': info['dns'] = value
                        elif key == 'MAC': info['mac'] = value
        except Exception as e:
            info['os_version'] = f"Error: {str(e)[:40]}"
        
        # Security checks
        try:
            sec_script = """
            # Antivirus
            $av = Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct -ErrorAction SilentlyContinue
            $avName = if ($av) { ($av | Select-Object -First 1).displayName } else { "None detected" }
            
            # Firewall
            $fw = (Get-NetFirewallProfile | Where-Object { $_.Enabled -eq $true }).Name -join ', '
            if (-not $fw) { $fw = "Disabled" }
            
            # Defender
            try {
                $def = Get-MpComputerStatus -ErrorAction SilentlyContinue
                $defStatus = if ($def.RealTimeProtectionEnabled) { "Enabled (Defs: $($def.AntivirusSignatureLastUpdated.ToString('yyyy-MM-dd')))" } else { "Disabled" }
            } catch { $defStatus = "N/A" }
            
            # BitLocker
            try {
                $bl = Get-BitLockerVolume -MountPoint C: -ErrorAction SilentlyContinue
                $blStatus = if ($bl) { $bl.ProtectionStatus.ToString() } else { "Not available" }
            } catch { $blStatus = "N/A (requires admin)" }
            
            # Secure Boot
            try {
                $sb = Confirm-SecureBootUEFI -ErrorAction SilentlyContinue
                $sbStatus = if ($sb) { "Enabled" } else { "Disabled" }
            } catch { $sbStatus = "N/A" }
            
            # TPM
            try {
                $tpm = Get-Tpm -ErrorAction SilentlyContinue
                $tpmStatus = if ($tpm.TpmPresent) { "Present (v$($tpm.ManufacturerVersion))" } else { "Not present" }
            } catch { $tpmStatus = "N/A" }
            
            # Pending reboot
            $reboot = Test-Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Component Based Servicing\\RebootPending"
            
            "AV|$avName"
            "FW|$fw"
            "DEF|$defStatus"
            "BL|$blStatus"
            "SB|$sbStatus"
            "TPM|$tpmStatus"
            "REBOOT|$reboot"
            """
            
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", sec_script],
                capture_output=True, text=True, timeout=15
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if '|' in line:
                        key, value = line.strip().split('|', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        if key == 'AV': info['av_status'] = value
                        elif key == 'FW': info['firewall'] = value
                        elif key == 'DEF': info['defender'] = value
                        elif key == 'BL': info['bitlocker'] = value
                        elif key == 'SB': info['secure_boot'] = value
                        elif key == 'TPM': info['tpm'] = value
                        elif key == 'REBOOT': info['reboot_needed'] = "⚠️ Yes" if value == "True" else "✅ No"
        except Exception:
            pass
        
        # External IP
        try:
            import urllib.request
            info['ip_external'] = urllib.request.urlopen('https://api.ipify.org', timeout=5).read().decode()
        except Exception:
            info['ip_external'] = "Could not determine"
        
        # Additional info
        info.setdefault('boot_type', 'UEFI' if os.path.exists(r'C:\\Windows\\Panther\setupact.log') else 'Unknown')
        info.setdefault('uac', "Check manually")
        info.setdefault('pending_updates', "Use Updates tab")
        info.setdefault('last_update', "Check Windows Update")
        info.setdefault('connection_type', "Ethernet/WiFi")
        
        # PowerShell version
        try:
            result = subprocess.run(["powershell", "-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"],
                                   capture_output=True, text=True, timeout=5)
            info['ps_version'] = result.stdout.strip() if result.returncode == 0 else "Unknown"
        except Exception:
            info['ps_version'] = "Unknown"
        
        # .NET versions
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "(Get-ChildItem 'HKLM:\\SOFTWARE\\Microsoft\\NET Framework Setup\\NDP\\v4\\Full' -ErrorAction SilentlyContinue).GetValue('Release')"],
                capture_output=True, text=True, timeout=5
            )
            release = int(result.stdout.strip()) if result.returncode == 0 and result.stdout.strip() else 0
            if release >= 533320: info['dotnet'] = "4.8.1+"
            elif release >= 528040: info['dotnet'] = "4.8"
            elif release >= 461808: info['dotnet'] = "4.7.2"
            else: info['dotnet'] = f"Release {release}"
        except Exception:
            info['dotnet'] = "Unknown"
        
        # Update UI
        self.parent.after(0, lambda: self._update_labels(info))
    
    def _update_labels(self, info):
        """Update all labels with collected info."""
        for key, label in self.info_labels.items():
            value = info.get(key, "N/A")
            label.config(text=value)
        
        self.refresh_label.config(text=f"Last refresh: {datetime.now().strftime('%H:%M:%S')}")
    
    def _copy_to_clipboard(self):
        """Copy all info to clipboard."""
        lines = []
        for key, label in self.info_labels.items():
            lines.append(f"{key}: {label.cget('text')}")
        
        text = "\n".join(lines)
        self.app.root.clipboard_clear()
        self.app.root.clipboard_append(text)
        self.app.log_success("System info copied to clipboard")
    
    def _export_report(self):
        """Export system info to file."""
        from tkinter import filedialog
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile=f"SystemHealth_{os.environ.get('COMPUTERNAME', 'PC')}_{datetime.now().strftime('%Y%m%d')}.txt"
        )
        
        if filepath:
            with open(filepath, 'w') as f:
                f.write(f"System Health Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
                f.write(f"Computer: {os.environ.get('COMPUTERNAME', '')}\n")
                f.write("=" * 60 + "\n\n")
                
                for key, label in self.info_labels.items():
                    f.write(f"{key:25s}: {label.cget('text')}\n")
            
            self.app.log_success(f"Report saved: {filepath}")
