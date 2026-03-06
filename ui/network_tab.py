"""
Network Debug Tab UI
"""

import tkinter as tk
from tkinter import ttk
import threading
import subprocess
import os
from datetime import datetime, timedelta

from utils.network_debug import NetworkDebugger


class NetworkTab:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.colors = app.colors
        self.debugger = NetworkDebugger(app=app)
        
        self.create_tab()
    
    def create_tab(self):
        """Create the Network Debug tab content."""
        tab = self.parent
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(2, weight=1)
        
        # === ROW 0: TARGET INPUT ===
        controls_frame = ttk.LabelFrame(tab, text="🎯 Target", 
                                       padding="10", style='Dark.TLabelframe')
        controls_frame.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
        controls_frame.columnconfigure(1, weight=1)
        
        # Target input
        ttk.Label(controls_frame, text="IP / Hostname:", 
                 style='DarkFrame.TLabel').grid(row=0, column=0, sticky='w', padx=(0, 10))
        
        self.target_entry = ttk.Entry(controls_frame, font=('Consolas', 11))
        self.target_entry.grid(row=0, column=1, sticky='ew', padx=(0, 10))
        self.target_entry.insert(0, "8.8.8.8")
        self.target_entry.bind('<Return>', lambda e: self._ping())
        
        # Quick targets
        quick_frame = ttk.Frame(controls_frame, style='Dark.TFrame')
        quick_frame.grid(row=0, column=2, sticky='e')
        
        for target in ["8.8.8.8", "1.1.1.1", "google.com"]:
            ttk.Button(quick_frame, text=target, style='Dark.TButton',
                      command=lambda t=target: self._set_target(t)).pack(side=tk.LEFT, padx=2)
        
        # Port input
        ttk.Label(controls_frame, text="Port:", 
                 style='DarkFrame.TLabel').grid(row=1, column=0, sticky='w', padx=(0, 10), pady=(10, 0))
        
        port_frame = ttk.Frame(controls_frame, style='Dark.TFrame')
        port_frame.grid(row=1, column=1, columnspan=2, sticky='w', pady=(10, 0))
        
        self.port_entry = ttk.Entry(port_frame, font=('Consolas', 11), width=8)
        self.port_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.port_entry.insert(0, "80")
        
        ttk.Label(port_frame, text="Common:", style='DarkFrame.TLabel').pack(side=tk.LEFT, padx=(10, 5))
        for port, name in [(80, "HTTP"), (443, "HTTPS"), (22, "SSH"), (3389, "RDP")]:
            ttk.Button(port_frame, text=name, style='Dark.TButton',
                      command=lambda p=port: self._set_port(p)).pack(side=tk.LEFT, padx=2)
        
        # === ROW 1: TOOL BUTTONS ===
        tools_frame = ttk.LabelFrame(tab, text="🔧 Tools", 
                                    padding="10", style='Dark.TLabelframe')
        tools_frame.grid(row=1, column=0, sticky='ew', padx=5, pady=5)
        
        # Row 1 - Target-based tools
        row1 = ttk.Frame(tools_frame, style='Dark.TFrame')
        row1.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(row1, text="🏓 Ping", style='Success.TButton',
                  command=self._ping).pack(side=tk.LEFT, padx=(0, 5))
        
        self.cping_start_btn = ttk.Button(row1, text="📡 CONTINUOUS PING", 
                                         style='Dark.TButton',
                                         command=self._start_continuous_ping)
        self.cping_start_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.cping_stop_btn = ttk.Button(row1, text="⏹ STOP PING", 
                                        style='Danger.TButton',
                                        command=self._stop_continuous_ping, 
                                        state='disabled')
        self.cping_stop_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        
        ttk.Button(row1, text="🔍 Traceroute", style='Dark.TButton',
                  command=self._traceroute).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(row1, text="🔎 NSLookup", style='Dark.TButton',
                  command=self._nslookup).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(row1, text="🔌 Port Check", style='Dark.TButton',
                  command=self._port_check).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(row1, text="📡 Port Scan", style='Warning.TButton',
                  command=self._port_scan).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(row1, text="🌐 Whois", style='Dark.TButton',
                  command=self._whois).pack(side=tk.LEFT, padx=(0, 5))
        
        # Row 2 - System tools
        row2 = ttk.Frame(tools_frame, style='Dark.TFrame')
        row2.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(row2, text="🌐 Internet Test", style='Success.TButton',
                  command=self._test_internet).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(row2, text="📋 IPConfig", style='Dark.TButton',
                  command=self._ipconfig).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(row2, text="🧹 Flush DNS", style='Warning.TButton',
                  command=self._flush_dns).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(row2, text="🔄 Renew IP", style='Warning.TButton',
                  command=self._renew_ip).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(row2, text="📊 Netstat", style='Dark.TButton',
                  command=self._netstat).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(row2, text="🗺️ Routes", style='Dark.TButton',
                  command=self._route_table).pack(side=tk.LEFT, padx=(0, 5))
        
        # Row 3 - More tools
        row3 = ttk.Frame(tools_frame, style='Dark.TFrame')
        row3.pack(fill=tk.X)
        
        ttk.Button(row3, text="📋 ARP", style='Dark.TButton',
                  command=self._arp_table).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(row3, text="📶 WiFi Info", style='Dark.TButton',
                  command=self._wifi_info).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(row3, text="📡 WiFi Scan", style='Dark.TButton',
                  command=self._wifi_networks).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(row3, text="🗑️ Clear", style='Dark.TButton',
                  command=self._clear_output).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(row3, text="💾 Save", style='Dark.TButton',
                  command=self._save_output).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(row3, text="🔍 Device Join Status", style='Dark.TButton',
                  command=self._check_join_status).pack(side=tk.LEFT, padx=(0, 5))
        
        # === ROW 2: OUTPUT AREA ===
        output_frame = ttk.LabelFrame(tab, text="📤 Output", 
                                     padding="10", style='Dark.TLabelframe')
        output_frame.grid(row=2, column=0, sticky='nsew', padx=5, pady=5)
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        
        self.output_text = tk.Text(output_frame, bg='#0a0a0a', fg='#00ff00',
                                  font=('Consolas', 10), wrap=tk.NONE)
        
        scrolly = ttk.Scrollbar(output_frame, orient=tk.VERTICAL, command=self.output_text.yview)
        scrollx = ttk.Scrollbar(output_frame, orient=tk.HORIZONTAL, command=self.output_text.xview)
        self.output_text.config(yscrollcommand=scrolly.set, xscrollcommand=scrollx.set)
        
        self.output_text.grid(row=0, column=0, sticky='nsew')
        scrolly.grid(row=0, column=1, sticky='ns')
        scrollx.grid(row=1, column=0, sticky='ew')
        
        # Progress bar
        self.progress = ttk.Progressbar(tab, mode='indeterminate')
        self.progress.grid(row=3, column=0, sticky='ew', padx=5, pady=5)
        
        # Initial message
        self.output_text.insert('1.0', "Enter a target IP or hostname above and select a tool.\n")

    def _check_join_status(self):
        """Check domain, Azure AD, Hybrid join, and Intune enrollment status."""
        self.app.log("🔍 Checking device join status...")
        
        def check():
            try:
                result = subprocess.run(['dsregcmd', '/status'],
                                    capture_output=True, text=True, timeout=30,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
                
                if result.returncode != 0:
                    self.app.root.after(0, lambda: self.app.log_error("Failed to run dsregcmd", hint="Run as Administrator"))
                    return
                
                output = result.stdout
                
                # Parse key fields
                checks = {
                    'Domain Joined': self._parse_dsreg(output, 'AzureAdJoined') == 'NO' and self._parse_dsreg(output, 'DomainJoined') == 'YES',
                    'Azure AD Joined': self._parse_dsreg(output, 'AzureAdJoined') == 'YES' and self._parse_dsreg(output, 'DomainJoined') == 'NO',
                    'Hybrid Joined': self._parse_dsreg(output, 'AzureAdJoined') == 'YES' and self._parse_dsreg(output, 'DomainJoined') == 'YES',
                    'Intune Enrolled': self._parse_dsreg(output, 'MdmUrl') != 'NONE',
                }
                
                details = {
                    'Domain Name': self._parse_dsreg(output, 'DomainName'),
                    'Tenant Name': self._parse_dsreg(output, 'TenantName'),
                    'Device ID': self._parse_dsreg(output, 'DeviceId'),
                    'MDM URL': self._parse_dsreg(output, 'MdmUrl'),
                }
                
                # Log results
                self.app.root.after(0, lambda: self.app.log(""))
                self.app.root.after(0, lambda: self.app.log("═══════════════════════════════════"))
                self.app.root.after(0, lambda: self.app.log("       📋 DEVICE JOIN STATUS"))
                self.app.root.after(0, lambda: self.app.log("═══════════════════════════════════"))
                
                for name, status in checks.items():
                    icon = "✅" if status else "❌"
                    self.app.root.after(0, lambda n=name, i=icon: self.app.log(f"  {i} {n}"))
                
                self.app.root.after(0, lambda: self.app.log("───────────────────────────────────"))
                
                for name, value in details.items():
                    val = value if value != "NONE" else "N/A"
                    self.app.root.after(0, lambda n=name, v=val: self.app.log(f"  📌 {n}: {v}"))
                
                self.app.root.after(0, lambda: self.app.log("═══════════════════════════════════"))
                self.app.root.after(0, lambda: self.app.log(""))
                
            except Exception as e:
                self.app.root.after(0, lambda: self.app.log_error(str(e)))
        
        threading.Thread(target=check, daemon=True).start()

    def _parse_dsreg(self, output, key):
        """Parse a value from dsregcmd /status output."""
        for line in output.splitlines():
            line = line.strip()
            if line.startswith(f"{key}"):
                parts = line.split(":", 1)
                if len(parts) > 1:
                    value = parts[1].strip()
                    if value:
                        return value
        return "NONE"

    def _set_port(self, port):
        """Set port in entry."""
        self.port_entry.delete(0, tk.END)
        self.port_entry.insert(0, str(port))
    
    def _set_target(self, target):
        """Set target in entry."""
        self.target_entry.delete(0, tk.END)
        self.target_entry.insert(0, target)
    
    def _get_target(self):
        """Get target from entry."""
        return self.target_entry.get().strip()
    
    def _get_port(self):
        """Get port from entry."""
        try:
            return int(self.port_entry.get().strip())
        except ValueError:
            return 80
    
    def _append_output(self, text):
        """Append text to output."""
        self.output_text.insert(tk.END, text + "\n")
        self.output_text.see(tk.END)
    
    def _set_output(self, text):
        """Set output text."""
        self.output_text.delete('1.0', tk.END)
        self.output_text.insert('1.0', text)
    
    def _run_async(self, func):
        """Run function in background thread."""
        def wrapper():
            self.app.root.after(0, self.progress.start)
            try:
                func()
            finally:
                self.app.root.after(0, self.progress.stop)
        
        threading.Thread(target=wrapper, daemon=True).start()
    
    
    
    # === TOOL COMMANDS ===
    
    def _ping(self):
        """Run ping."""
        target = self._get_target()
        if not target:
            self.app.log_warning("Enter a target first")
            return
        
        def run():
            output, _ = self.debugger.ping(target, count=4)
            self.app.root.after(0, lambda: self._set_output(output))
        
        self._run_async(run)
    
    def _traceroute(self):
        """Run traceroute."""
        target = self._get_target()
        if not target:
            self.app.log_warning("Enter a target first")
            return
        
        def run():
            self.app.root.after(0, lambda: self._set_output("Running traceroute... (this may take a while)\n"))
            output, _ = self.debugger.traceroute(target)
            self.app.root.after(0, lambda: self._set_output(output))
        
        self._run_async(run)
    
    def _nslookup(self):
        """Run nslookup."""
        target = self._get_target()
        if not target:
            self.app.log_warning("Enter a target first")
            return
        
        def run():
            output, _ = self.debugger.nslookup(target)
            self.app.root.after(0, lambda: self._set_output(output))
        
        self._run_async(run)
    
    def _port_check(self):
        """Check single port."""
        target = self._get_target()
        port = self._get_port()
        if not target:
            self.app.log_warning("Enter a target first")
            return
        
        def run():
            output, _ = self.debugger.port_check(target, port)
            self.app.root.after(0, lambda: self._set_output(output))
        
        self._run_async(run)
    
    def _port_scan(self):
        """Scan common ports."""
        target = self._get_target()
        if not target:
            self.app.log_warning("Enter a target first")
            return
        
        def run():
            self.app.root.after(0, lambda: self._set_output("Scanning ports... please wait\n"))
            output, _ = self.debugger.port_scan(target)
            self.app.root.after(0, lambda: self._set_output(output))
        
        self._run_async(run)
    
    def _whois(self):
        """Get whois info."""
        target = self._get_target()
        if not target:
            self.app.log_warning("Enter a target first")
            return
        
        def run():
            output, _ = self.debugger.whois(target)
            self.app.root.after(0, lambda: self._set_output(output))
        
        self._run_async(run)
    
    def _test_internet(self):
        """Test internet connectivity."""
        def run():
            output, _ = self.debugger.test_internet()
            self.app.root.after(0, lambda: self._set_output(output))
        
        self._run_async(run)
    
    def _ipconfig(self):
        """Show IP config."""
        def run():
            output, _ = self.debugger.get_ip_config()
            self.app.root.after(0, lambda: self._set_output(output))
        
        self._run_async(run)
    
    def _flush_dns(self):
        """Flush DNS cache."""
        def run():
            output, _ = self.debugger.flush_dns()
            self.app.root.after(0, lambda: self._set_output(output))
        
        self._run_async(run)
    
    def _renew_ip(self):
        """Release and renew IP."""
        def run():
            self.app.root.after(0, lambda: self._set_output("Releasing and renewing IP... please wait\n"))
            output, _ = self.debugger.release_renew_ip()
            self.app.root.after(0, lambda: self._set_output(output))
        
        self._run_async(run)
    
    def _arp_table(self):
        """Show ARP table."""
        def run():
            output, _ = self.debugger.get_arp_table()
            self.app.root.after(0, lambda: self._set_output(output))
        
        self._run_async(run)
    
    def _netstat(self):
        """Show network connections."""
        def run():
            output, _ = self.debugger.get_netstat()
            self.app.root.after(0, lambda: self._set_output(output))
        
        self._run_async(run)
    
    def _route_table(self):
        """Show routing table."""
        def run():
            output, _ = self.debugger.get_route_table()
            self.app.root.after(0, lambda: self._set_output(output))
        
        self._run_async(run)
    
    def _wifi_info(self):
        """Show WiFi info."""
        def run():
            output, _ = self.debugger.get_wifi_info()
            self.app.root.after(0, lambda: self._set_output(output))
        
        self._run_async(run)
    
    def _wifi_networks(self):
        """Show available WiFi networks."""
        def run():
            output, _ = self.debugger.get_wifi_networks()
            self.app.root.after(0, lambda: self._set_output(output))
        
        self._run_async(run)
    
    def _clear_output(self):
        """Clear output text."""
        self.output_text.delete('1.0', tk.END)
    
    def _save_output(self):
        """Save output to file."""
        from tkinter import filedialog
        from datetime import datetime
        
        content = self.output_text.get('1.0', tk.END)
        if not content.strip():
            sself.app.log_warning("No output to save")
            return
        
        filepath = filedialog.asksaveasfilename(
            title="Save Output",
            defaultextension=".txt",
            initialfile=f"network_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.app.log_success(f"Saved to: {filepath}")
            except Exception as e:
                 self.app.log_error(f"Save failed: {e}")
                 
    def _start_continuous_ping(self):
        """Start continuous ping using the IP/hostname entry."""
        target = self.target_entry.get().strip()
        if not target:
            self.app.log_warning("Enter an IP or hostname first")
            return
        
        if hasattr(self, '_cping_running') and self._cping_running:
            self.app.log_warning("Ping monitor already running")
            return
        
        self._cping_running = True
        self._cping_sent = 0
        self._cping_fail = 0
        
        # Setup log file
        log_dir = os.path.join(os.environ.get('TEMP', r'C:\Temp'), 'ping_monitor')
        os.makedirs(log_dir, exist_ok=True)
        safe_target = target.replace(':', '-').replace('/', '-')
        self._cping_log = os.path.join(log_dir, f"ping_{safe_target}.log")
        
        # Update buttons
        self.cping_start_btn.config(state='disabled')
        self.cping_stop_btn.config(state='normal')
        
        self.app.log(f"📡 Continuous ping started: {target}")
        self.app.log(f"   Log: {self._cping_log}")
        
        self._cping_thread = threading.Thread(
            target=self._cping_loop, args=(target,), daemon=True
        )
        self._cping_thread.start()
    
    def _stop_continuous_ping(self):
        """Stop continuous ping."""
        self._cping_running = False
        self.cping_start_btn.config(state='normal')
        self.cping_stop_btn.config(state='disabled')
        
        if self._cping_sent > 0:
            loss = (self._cping_fail / self._cping_sent) * 100
            self.app.log(f"📡 Ping stopped — Sent: {self._cping_sent}, "
                        f"Failed: {self._cping_fail}, Loss: {loss:.1f}%")
            self.app.log(f"   Failures logged to: {self._cping_log}")
    
    def _cping_loop(self, target):
        """Background continuous ping loop."""
        import time
        
        while self._cping_running:
            try:
                result = subprocess.run(
                    ['ping', '-n', '1', '-w', '2000', target],
                    capture_output=True, text=True, timeout=5,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                output = result.stdout or ""
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self._cping_sent += 1
                
                if result.returncode == 0 and 'ttl=' in output.lower():
                    # Success
                    ms = ""
                    if 'time=' in output.lower():
                        try:
                            ms = output.lower().split('time=')[1].split('ms')[0].strip()
                            ms = f" ({ms}ms)"
                        except:
                            ms = ""
                    
                    self.app.root.after(0, lambda t=timestamp, m=ms: 
                        self.app.log(f"✅ {target} OK{m}"))
                else:
                    # Failure — log to file
                    self._cping_fail += 1
                    
                    reason = "TIMEOUT"
                    if 'unreachable' in output.lower():
                        reason = "UNREACHABLE"
                    elif 'could not find host' in output.lower():
                        reason = "DNS FAILED"
                    
                    self.app.root.after(0, lambda t=timestamp, r=reason:
                        self.app.log_error(f"{target} — {r}"))
                    
                    # Write failure to log file
                    try:
                        with open(self._cping_log, 'a') as f:
                            f.write(f"{timestamp} - {target} - {reason}\n")
                            f.write(f"  {output.strip()}\n\n")
                    except:
                        pass
                
                # Clean old logs every 100 pings
                if self._cping_sent % 100 == 0:
                    try:
                        cutoff = datetime.now() - timedelta(days=10)
                        log_dir = os.path.dirname(self._cping_log)
                        for f in os.listdir(log_dir):
                            fp = os.path.join(log_dir, f)
                            if os.path.isfile(fp) and datetime.fromtimestamp(os.path.getmtime(fp)) < cutoff:
                                os.remove(fp)
                    except:
                        pass
                        
            except Exception as e:
                self.app.root.after(0, lambda err=str(e):
                    self.app.log_error(f"Ping error: {err}"))
            
            time.sleep(1)