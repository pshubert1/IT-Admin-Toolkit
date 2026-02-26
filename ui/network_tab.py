"""
Network Debug Tab UI
"""

import tkinter as tk
from tkinter import ttk
import threading

from utils.network_debug import NetworkDebugger


class NetworkTab:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.colors = app.colors
        self.debugger = NetworkDebugger(app.log)
        
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
            self.app.log("⚠️ Enter a target first")
            return
        
        def run():
            output, _ = self.debugger.ping(target, count=4)
            self.app.root.after(0, lambda: self._set_output(output))
        
        self._run_async(run)
    
    def _traceroute(self):
        """Run traceroute."""
        target = self._get_target()
        if not target:
            self.app.log("⚠️ Enter a target first")
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
            self.app.log("⚠️ Enter a target first")
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
            self.app.log("⚠️ Enter a target first")
            return
        
        def run():
            output, _ = self.debugger.port_check(target, port)
            self.app.root.after(0, lambda: self._set_output(output))
        
        self._run_async(run)
    
    def _port_scan(self):
        """Scan common ports."""
        target = self._get_target()
        if not target:
            self.app.log("⚠️ Enter a target first")
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
            self.app.log("⚠️ Enter a target first")
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
            self.app.log("⚠️ No output to save")
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
                self.app.log(f"💾 Saved to: {filepath}")
            except Exception as e:
                self.app.log(f"❌ Save failed: {e}")