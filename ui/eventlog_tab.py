"""
Event Log Summary Tab UI
Curated view of important Windows events for troubleshooting.
"""

import tkinter as tk
from tkinter import ttk
import threading
import subprocess
from datetime import datetime


class EventLogTab:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.colors = app.colors
        self.events = []
        
        self.create_tab()
    
    def create_tab(self):
        """Create the Event Log Summary tab."""
        tab = self.parent
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)
        
        # Header / Filters
        header = ttk.Frame(tab, style='DarkBg.TFrame')
        header.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
        
        ttk.Button(header, text="🔍 SCAN EVENTS", style='Success.TButton',
                  command=self._scan_events).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(header, text="📋 EXPORT", style='Dark.TButton',
                  command=self._export_report).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(header, text="Filter:", style='DarkFrame.TLabel').pack(side=tk.LEFT, padx=(20, 5))
        
        self.filter_var = tk.StringVar(value="All")
        filters = ["All", "Critical", "Errors", "Crashes", "Disk", "Login Failures", "Shutdowns"]
        filter_menu = ttk.OptionMenu(header, self.filter_var, "All", *filters,
                                    command=self._apply_filter)
        filter_menu.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(header, text="Days:", style='DarkFrame.TLabel').pack(side=tk.LEFT, padx=(10, 5))
        self.days_var = tk.StringVar(value="7")
        days_entry = ttk.Entry(header, textvariable=self.days_var, width=5)
        days_entry.pack(side=tk.LEFT)
        
        self.status_label = ttk.Label(header, text="Click Scan to check events",
                                     style='DarkFrame.TLabel')
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        # Results Treeview
        results_frame = ttk.Frame(tab, style='DarkBg.TFrame')
        results_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        columns = ("time", "level", "source", "id", "message")
        self.tree = ttk.Treeview(results_frame, columns=columns, show='headings',
                                style='Dark.Treeview', height=15)
        
        self.tree.heading("time", text="Time")
        self.tree.heading("level", text="Level")
        self.tree.heading("source", text="Source")
        self.tree.heading("id", text="Event ID")
        self.tree.heading("message", text="Message")
        
        self.tree.column("time", width=140)
        self.tree.column("level", width=70)
        self.tree.column("source", width=180)
        self.tree.column("id", width=70)
        self.tree.column("message", width=500)
        
        tree_scroll_y = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.tree.yview)
        tree_scroll_x = ttk.Scrollbar(results_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        tree_scroll_y.grid(row=0, column=1, sticky='ns')
        tree_scroll_x.grid(row=1, column=0, sticky='ew')
        
        # Detail panel
        detail_frame = ttk.LabelFrame(tab, text="Event Details",
                                     padding="5", style='Dark.TLabelframe')
        detail_frame.grid(row=2, column=0, sticky='ew', padx=5, pady=5)
        
        self.detail_text = tk.Text(detail_frame, height=5, bg='#0a0a0a', fg='#00ff00',
                                  font=('Consolas', 9), state=tk.DISABLED, wrap=tk.WORD)
        self.detail_text.pack(fill=tk.BOTH, expand=True)
        
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        
        # Summary bar
        self.summary_frame = ttk.Frame(tab, style='DarkBg.TFrame')
        self.summary_frame.grid(row=3, column=0, sticky='ew', padx=5, pady=5)
        
        self.summary_labels = {}
        for cat in ["Critical", "Error", "Warning", "Crashes", "Disk Issues"]:
            lbl = ttk.Label(self.summary_frame, text=f"{cat}: 0", style='DarkFrame.TLabel',
                           font=('Segoe UI', 9, 'bold'))
            lbl.pack(side=tk.LEFT, padx=10)
            self.summary_labels[cat] = lbl
    
    def _scan_events(self):
        """Scan Windows Event Logs."""
        self.status_label.config(text="Scanning...")
        self.tree.delete(*self.tree.get_children())
        threading.Thread(target=self._do_scan, daemon=True).start()
    
    def _do_scan(self):
        """Background scan of event logs."""
        self.events = []
        days = int(self.days_var.get()) if self.days_var.get().isdigit() else 7
        
        queries = [
            # Critical and Error events from System log
            {
                'name': 'System Critical/Error',
                'script': f"""
                    $start = (Get-Date).AddDays(-{days})
                    Get-WinEvent -FilterHashtable @{{LogName='System'; Level=1,2; StartTime=$start}} -MaxEvents 50 -ErrorAction SilentlyContinue |
                    ForEach-Object {{
                        $msg = $_.Message -replace '[\r\n]+', ' '
                        if ($msg.Length -gt 200) {{ $msg = $msg.Substring(0, 200) }}
                        "$($_.TimeCreated.ToString('yyyy-MM-dd HH:mm'))|$($_.LevelDisplayName)|$($_.ProviderName)|$($_.Id)|$msg"
                    }}
                """
            },
            # Application crashes (Event ID 1000)
            {
                'name': 'App Crashes',
                'script': f"""
                    $start = (Get-Date).AddDays(-{days})
                    Get-WinEvent -FilterHashtable @{{LogName='Application'; ProviderName='Application Error'; Id=1000; StartTime=$start}} -MaxEvents 20 -ErrorAction SilentlyContinue |
                    ForEach-Object {{
                        $msg = $_.Message -replace '[\r\n]+', ' '
                        if ($msg.Length -gt 200) {{ $msg = $msg.Substring(0, 200) }}
                        "$($_.TimeCreated.ToString('yyyy-MM-dd HH:mm'))|Crash|Application Error|1000|$msg"
                    }}
                """
            },
            # Unexpected shutdowns (Event ID 6008)
            {
                'name': 'Unexpected Shutdowns',
                'script': f"""
                    $start = (Get-Date).AddDays(-{days})
                    Get-WinEvent -FilterHashtable @{{LogName='System'; ProviderName='EventLog'; Id=6008; StartTime=$start}} -MaxEvents 10 -ErrorAction SilentlyContinue |
                    ForEach-Object {{
                        $msg = $_.Message -replace '[\r\n]+', ' '
                        if ($msg.Length -gt 200) {{ $msg = $msg.Substring(0, 200) }}
                        "$($_.TimeCreated.ToString('yyyy-MM-dd HH:mm'))|Critical|EventLog|6008|Unexpected shutdown: $msg"
                    }}
                """
            },
            # Disk errors (Event ID 7, 11, 51, 52)
            {
                'name': 'Disk Errors',
                'script': f"""
                    $start = (Get-Date).AddDays(-{days})
                    Get-WinEvent -FilterHashtable @{{LogName='System'; Id=7,11,51,52; StartTime=$start}} -MaxEvents 20 -ErrorAction SilentlyContinue |
                    ForEach-Object {{
                        $msg = $_.Message -replace '[\r\n]+', ' '
                        if ($msg.Length -gt 200) {{ $msg = $msg.Substring(0, 200) }}
                        "$($_.TimeCreated.ToString('yyyy-MM-dd HH:mm'))|Disk|$($_.ProviderName)|$($_.Id)|$msg"
                    }}
                """
            },
            # Login failures (Event ID 4625)
            {
                'name': 'Login Failures',
                'script': f"""
                    $start = (Get-Date).AddDays(-{days})
                    Get-WinEvent -FilterHashtable @{{LogName='Security'; Id=4625; StartTime=$start}} -MaxEvents 20 -ErrorAction SilentlyContinue |
                    ForEach-Object {{
                        $msg = $_.Message -replace '[\r\n]+', ' '
                        if ($msg.Length -gt 200) {{ $msg = $msg.Substring(0, 200) }}
                        "$($_.TimeCreated.ToString('yyyy-MM-dd HH:mm'))|Warning|Security|4625|Login failure: $msg"
                    }}
                """
            },
        ]
        
        for query in queries:
            try:
                result = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", query['script']],
                    capture_output=True, text=True, timeout=20
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    for line in result.stdout.strip().split('\n'):
                        parts = line.strip().split('|', 4)
                        if len(parts) >= 5:
                            self.events.append({
                                'time': parts[0],
                                'level': parts[1],
                                'source': parts[2],
                                'id': parts[3],
                                'message': parts[4],
                                'category': query['name']
                            })
            except Exception:
                pass
        
        # Sort by time (newest first)
        self.events.sort(key=lambda x: x['time'], reverse=True)
        
        self.parent.after(0, self._update_tree)
    
    def _update_tree(self):
        """Update treeview with events."""
        self.tree.delete(*self.tree.get_children())
        
        # Count categories
        counts = {'Critical': 0, 'Error': 0, 'Warning': 0, 'Crashes': 0, 'Disk Issues': 0}
        
        for event in self.events:
            level = event['level']
            if 'Critical' in level: counts['Critical'] += 1
            elif 'Error' in level: counts['Error'] += 1
            elif 'Warning' in level: counts['Warning'] += 1
            if 'Crash' in level: counts['Crashes'] += 1
            if 'Disk' in level or 'disk' in event['source'].lower(): counts['Disk Issues'] += 1
            
            self.tree.insert('', tk.END, values=(
                event['time'], event['level'], event['source'],
                event['id'], event['message'][:100]
            ))
        
        # Update summary
        for cat, label in self.summary_labels.items():
            count = counts.get(cat, 0)
            color = '#ff5555' if count > 0 and cat in ('Critical', 'Error', 'Crashes') else self.colors['fg']
            label.config(text=f"{cat}: {count}", foreground=color)
        
        total = len(self.events)
        self.status_label.config(text=f"Found {total} event(s)")
    
    def _apply_filter(self, *args):
        """Filter the displayed events."""
        filter_val = self.filter_var.get()
        self.tree.delete(*self.tree.get_children())
        
        for event in self.events:
            show = False
            if filter_val == "All":
                show = True
            elif filter_val == "Critical" and 'Critical' in event['level']:
                show = True
            elif filter_val == "Errors" and 'Error' in event['level']:
                show = True
            elif filter_val == "Crashes" and ('Crash' in event['level'] or event['id'] == '1000'):
                show = True
            elif filter_val == "Disk" and ('Disk' in event['level'] or 'disk' in event['source'].lower()):
                show = True
            elif filter_val == "Login Failures" and event['id'] == '4625':
                show = True
            elif filter_val == "Shutdowns" and event['id'] == '6008':
                show = True
            
            if show:
                self.tree.insert('', tk.END, values=(
                    event['time'], event['level'], event['source'],
                    event['id'], event['message'][:100]
                ))
    
    def _on_select(self, event):
        """Show full event details."""
        selection = self.tree.selection()
        if not selection:
            return
        
        values = self.tree.item(selection[0], 'values')
        if values:
            # Find matching event
            for evt in self.events:
                if evt['time'] == values[0] and evt['id'] == values[3]:
                    self.detail_text.config(state=tk.NORMAL)
                    self.detail_text.delete('1.0', tk.END)
                    detail = f"Time: {evt['time']}\nLevel: {evt['level']}\nSource: {evt['source']}\nEvent ID: {evt['id']}\n\n{evt['message']}"
                    self.detail_text.insert('1.0', detail)
                    self.detail_text.config(state=tk.DISABLED)
                    break
    
    def _export_report(self):
        """Export event log summary."""
        if not self.events:
            self.app.log_warning("No events to export. Run scan first.")
            return
        
        from tkinter import filedialog
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("CSV", "*.csv")],
            initialfile=f"EventLog_{datetime.now().strftime('%Y%m%d')}.txt"
        )
        
        if filepath:
            with open(filepath, 'w') as f:
                f.write(f"Event Log Summary - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
                f.write("=" * 80 + "\n\n")
                
                for evt in self.events:
                    f.write(f"[{evt['time']}] [{evt['level']}] {evt['source']} (ID: {evt['id']})\n")
                    f.write(f"  {evt['message']}\n\n")
            
            self.app.log_success(f"Report saved: {filepath}")
