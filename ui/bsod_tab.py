"""
BSOD / Crash Analyzer Tab UI
Reads Windows minidump files and displays crash information in plain English.
"""

import tkinter as tk
from tkinter import ttk
import os
import struct
import threading
from datetime import datetime, timedelta


# Common BSOD stop codes and their meanings
STOP_CODES = {
    0x0000000A: ("IRQL_NOT_LESS_OR_EQUAL", "A driver tried to access invalid memory. Usually a faulty driver or RAM issue."),
    0x0000001E: ("KMODE_EXCEPTION_NOT_HANDLED", "A kernel-mode program generated an exception the error handler didn't catch."),
    0x00000024: ("NTFS_FILE_SYSTEM", "NTFS file system issue. Could be disk corruption or failing drive."),
    0x0000002E: ("DATA_BUS_ERROR", "Hardware memory failure. Check RAM with memtest."),
    0x0000003B: ("SYSTEM_SERVICE_EXCEPTION", "A system thread generated an exception. Often caused by GPU drivers or antivirus."),
    0x0000003F: ("NO_MORE_SYSTEM_PTES", "System ran out of page table entries. Too many I/O operations or driver leak."),
    0x00000050: ("PAGE_FAULT_IN_NONPAGED_AREA", "Invalid memory access. Bad RAM, corrupt driver, or failing disk."),
    0x0000007A: ("KERNEL_DATA_INPAGE_ERROR", "Page of kernel data could not be read. Disk failure or bad sectors."),
    0x0000007E: ("SYSTEM_THREAD_EXCEPTION_NOT_HANDLED", "A system thread generated an unhandled exception. Check the faulting driver."),
    0x0000007F: ("UNEXPECTED_KERNEL_MODE_TRAP", "CPU generated a trap the kernel didn't expect. Overheating, bad RAM, or driver."),
    0x0000009C: ("MACHINE_CHECK_EXCEPTION", "Hardware failure detected by CPU. Check cooling, RAM, and motherboard."),
    0x0000009F: ("DRIVER_POWER_STATE_FAILURE", "Driver in inconsistent power state during sleep/wake. Update affected driver."),
    0x000000BE: ("ATTEMPTED_WRITE_TO_READONLY_MEMORY", "Driver tried to write to read-only memory. Update or reinstall the driver."),
    0x000000C2: ("BAD_POOL_CALLER", "Current thread is making a bad pool request. Faulty driver."),
    0x000000D1: ("DRIVER_IRQL_NOT_LESS_OR_EQUAL", "Driver tried to access pageable memory at too high IRQL. Faulty driver."),
    0x000000EF: ("CRITICAL_PROCESS_DIED", "A critical system process terminated. Corrupt system files or malware."),
    0x000000F4: ("CRITICAL_OBJECT_TERMINATION", "A critical system object unexpectedly terminated."),
    0x00000116: ("VIDEO_TDR_FAILURE", "Display driver failed to respond. Update GPU drivers."),
    0x00000124: ("WHEA_UNCORRECTABLE_ERROR", "Hardware error (CPU, RAM, or disk). Check temperatures and run diagnostics."),
    0x00000133: ("DPC_WATCHDOG_VIOLATION", "DPC routine took too long. Often SSD/storage driver or firmware issue."),
    0x00000139: ("KERNEL_SECURITY_CHECK_FAILURE", "Kernel detected corruption. Could be driver or hardware."),
    0x0000013A: ("KERNEL_MODE_HEAP_CORRUPTION", "Kernel-mode heap corruption detected. Usually a driver bug."),
    0x00000154: ("UNEXPECTED_STORE_EXCEPTION", "Store component caught an unexpected exception. Often SSD or antivirus related."),
    0x00000019: ("BAD_POOL_HEADER", "Pool header is corrupt. Faulty driver, bad RAM, or overclocking."),
    0x000001CA: ("SYNTHETIC_WATCHDOG_TIMEOUT", "System became unresponsive. Could be storage, driver, or firmware hang."),
}


class BSODTab:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.colors = app.colors
        self.crashes = []
        
        self.create_tab()
    
    def create_tab(self):
        """Create the BSOD Analyzer tab."""
        tab = self.parent
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)
        
        # Header / Actions
        header = ttk.Frame(tab, style='DarkBg.TFrame')
        header.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
        
        ttk.Button(header, text="🔍 SCAN FOR CRASHES", style='Success.TButton',
                  command=self._scan_crashes).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(header, text="📋 EXPORT REPORT", style='Dark.TButton',
                  command=self._export_report).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(header, text="🗑️ CLEAR", style='Dark.TButton',
                  command=self._clear_results).pack(side=tk.LEFT)
        
        self.status_label = ttk.Label(header, text="Click Scan to check for crash dumps",
                                     style='DarkFrame.TLabel')
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        # Results area
        results_frame = ttk.LabelFrame(tab, text="💀 Crash History",
                                      padding="10", style='Dark.TLabelframe')
        results_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Treeview for crash list
        columns = ("date", "stop_code", "name", "cause", "driver")
        self.tree = ttk.Treeview(results_frame, columns=columns, show='headings',
                                style='Dark.Treeview', height=8)
        
        self.tree.heading("date", text="Date/Time")
        self.tree.heading("stop_code", text="Stop Code")
        self.tree.heading("name", text="Error Name")
        self.tree.heading("cause", text="Probable Cause")
        self.tree.heading("driver", text="Faulting Module")
        
        self.tree.column("date", width=140)
        self.tree.column("stop_code", width=100)
        self.tree.column("name", width=200)
        self.tree.column("cause", width=350)
        self.tree.column("driver", width=150)
        
        tree_scroll = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.grid(row=0, column=0, sticky='nsew')
        tree_scroll.grid(row=0, column=1, sticky='ns')
        
        # Detail panel
        detail_frame = ttk.LabelFrame(tab, text="📝 Details & Recommendations",
                                     padding="10", style='Dark.TLabelframe')
        detail_frame.grid(row=2, column=0, sticky='ew', padx=5, pady=5)
        
        self.detail_text = tk.Text(detail_frame, height=6, bg='#0a0a0a', fg='#00ff00',
                                  font=('Consolas', 9), state=tk.DISABLED, wrap=tk.WORD)
        self.detail_text.pack(fill=tk.BOTH, expand=True)
        
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
    
    def _scan_crashes(self):
        """Scan for crash dumps in background."""
        self.status_label.config(text="Scanning...")
        threading.Thread(target=self._do_scan, daemon=True).start()
    
    def _do_scan(self):
        """Background scan for minidump files."""
        self.crashes = []
        
        # Check minidump directory
        minidump_dir = r"C:\Windows\Minidump"
        memory_dmp = r"C:\Windows\MEMORY.DMP"
        
        dumps_found = []
        
        if os.path.exists(minidump_dir):
            for f in os.listdir(minidump_dir):
                if f.lower().endswith('.dmp'):
                    dumps_found.append(os.path.join(minidump_dir, f))
        
        if os.path.exists(memory_dmp):
            dumps_found.append(memory_dmp)
        
        # Also check Event Log for BugCheck events
        crashes_from_events = self._get_bugcheck_events()
        
        # Parse dump files (basic header parsing)
        for dump_path in dumps_found:
            try:
                crash_info = self._parse_minidump(dump_path)
                if crash_info:
                    self.crashes.append(crash_info)
            except Exception as e:
                self.crashes.append({
                    'date': datetime.fromtimestamp(os.path.getmtime(dump_path)).strftime("%Y-%m-%d %H:%M"),
                    'stop_code': "Unknown",
                    'name': "Parse Error",
                    'cause': f"Could not parse: {str(e)[:50]}",
                    'driver': os.path.basename(dump_path),
                    'file': dump_path,
                    'recommendation': "Use WinDbg for detailed analysis."
                })
        
        # Add event log crashes
        for event_crash in crashes_from_events:
            # Don't duplicate if we already have a dump for this time
            self.crashes.append(event_crash)
        
        # Sort by date (newest first)
        self.crashes.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        # Update UI from main thread
        self.parent.after(0, self._update_tree)
    
    def _parse_minidump(self, filepath):
        """Parse basic info from a minidump file header."""
        with open(filepath, 'rb') as f:
            # MINIDUMP_HEADER signature
            sig = f.read(4)
            if sig != b'MDMP':
                return None
            
            # Skip version
            f.read(4)
            
            # Number of streams
            num_streams = struct.unpack('<I', f.read(4))[0]
            
            # Stream directory RVA
            stream_dir_rva = struct.unpack('<I', f.read(4))[0]
            
            # Checksum
            f.read(4)
            
            # TimeDateStamp
            timestamp = struct.unpack('<I', f.read(4))[0]
            crash_time = datetime(1970, 1, 1) + timedelta(seconds=timestamp)
        
        # Get file modification time as fallback
        mod_time = datetime.fromtimestamp(os.path.getmtime(filepath))
        
        # Use file mod time (more reliable for display)
        display_time = mod_time.strftime("%Y-%m-%d %H:%M")
        
        # Try to get stop code from filename or basic parsing
        filename = os.path.basename(filepath)
        
        return {
            'date': display_time,
            'stop_code': "See Event Log",
            'name': "Minidump Found",
            'cause': "Analyze with WinDbg or check Event Log for details",
            'driver': filename,
            'file': filepath,
            'recommendation': f"Dump file: {filepath}\nUse 'WinDbg Preview' from Microsoft Store for full analysis.\nOr run: !analyze -v in WinDbg."
        }
    
    def _get_bugcheck_events(self):
        """Get BugCheck events from Windows Event Log."""
        crashes = []
        
        try:
            import subprocess
            # Query System event log for BugCheck (Event ID 1001 from BugCheck)
            cmd = [
                "powershell", "-NoProfile", "-Command",
                """
                Get-WinEvent -FilterHashtable @{LogName='System'; ProviderName='Microsoft-Windows-WER-SystemErrorReporting'; Id=1001} -MaxEvents 20 -ErrorAction SilentlyContinue |
                ForEach-Object {
                    $props = $_.Properties
                    $bugcheck = if ($props.Count -ge 1) { $props[0].Value } else { 'Unknown' }
                    $p1 = if ($props.Count -ge 2) { $props[1].Value } else { '' }
                    $p2 = if ($props.Count -ge 3) { $props[2].Value } else { '' }
                    $p3 = if ($props.Count -ge 4) { $props[3].Value } else { '' }
                    $p4 = if ($props.Count -ge 5) { $props[4].Value } else { '' }
                    "$($_.TimeCreated.ToString('yyyy-MM-dd HH:mm'))|$bugcheck|$p1|$p2|$p3|$p4"
                }
                """
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0 and result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    parts = line.strip().split('|')
                    if len(parts) >= 2:
                        date_str = parts[0]
                        bugcheck_str = parts[1].strip()
                        
                        # Parse stop code
                        try:
                            stop_code = int(bugcheck_str, 16) if bugcheck_str.startswith('0x') else int(bugcheck_str)
                        except (ValueError, TypeError):
                            stop_code = 0
                        
                        name, cause = STOP_CODES.get(stop_code, ("UNKNOWN", f"Stop code: {bugcheck_str}"))
                        
                        faulting = ""
                        if len(parts) >= 6 and parts[5]:
                            faulting = parts[5]
                        
                        crashes.append({
                            'date': date_str,
                            'stop_code': f"0x{stop_code:08X}" if stop_code else bugcheck_str,
                            'name': name,
                            'cause': cause[:80],
                            'driver': faulting or "Unknown",
                            'file': "Event Log",
                            'recommendation': f"Stop Code: 0x{stop_code:08X}\nName: {name}\n\nDescription: {cause}\n\nParameters: {'|'.join(parts[2:6]) if len(parts) >= 6 else 'N/A'}"
                        })
        except Exception:
            pass
        
        return crashes
    
    def _update_tree(self):
        """Update the treeview with crash data."""
        self.tree.delete(*self.tree.get_children())
        
        for crash in self.crashes:
            self.tree.insert('', tk.END, values=(
                crash['date'],
                crash['stop_code'],
                crash['name'],
                crash['cause'][:60],
                crash['driver']
            ))
        
        count = len(self.crashes)
        if count == 0:
            self.status_label.config(text="✅ No crashes found! System looks healthy.")
        else:
            self.status_label.config(text=f"⚠️ Found {count} crash event(s)")
    
    def _on_select(self, event):
        """Show details for selected crash."""
        selection = self.tree.selection()
        if not selection:
            return
        
        idx = self.tree.index(selection[0])
        if idx < len(self.crashes):
            crash = self.crashes[idx]
            
            self.detail_text.config(state=tk.NORMAL)
            self.detail_text.delete('1.0', tk.END)
            
            detail = f"Date: {crash['date']}\n"
            detail += f"Stop Code: {crash['stop_code']}\n"
            detail += f"Error: {crash['name']}\n"
            detail += f"Cause: {crash['cause']}\n"
            detail += f"\n{crash.get('recommendation', '')}\n"
            
            self.detail_text.insert('1.0', detail)
            self.detail_text.config(state=tk.DISABLED)
    
    def _export_report(self):
        """Export crash report to file."""
        if not self.crashes:
            self.app.log_warning("No crash data to export. Run scan first.")
            return
        
        from tkinter import filedialog
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile=f"CrashReport_{datetime.now().strftime('%Y%m%d')}.txt"
        )
        
        if filepath:
            with open(filepath, 'w') as f:
                f.write(f"BSOD/Crash Report - Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
                f.write("=" * 70 + "\n\n")
                
                for crash in self.crashes:
                    f.write(f"Date: {crash['date']}\n")
                    f.write(f"Stop Code: {crash['stop_code']}\n")
                    f.write(f"Error: {crash['name']}\n")
                    f.write(f"Cause: {crash['cause']}\n")
                    f.write(f"Module: {crash['driver']}\n")
                    f.write(f"{crash.get('recommendation', '')}\n")
                    f.write("-" * 70 + "\n\n")
            
            self.app.log_success(f"Report saved: {filepath}")
    
    def _clear_results(self):
        """Clear all results."""
        self.tree.delete(*self.tree.get_children())
        self.crashes = []
        self.detail_text.config(state=tk.NORMAL)
        self.detail_text.delete('1.0', tk.END)
        self.detail_text.config(state=tk.DISABLED)
        self.status_label.config(text="Cleared")
