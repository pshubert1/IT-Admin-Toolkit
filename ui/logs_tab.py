"""
Log Analysis Tab UI
"""

import tkinter as tk
from tkinter import ttk, filedialog
import os
from datetime import datetime, timedelta
import threading
from utils.logs import ESXiLogAnalyzer, GenericLogAnalyzer
from utils.logs import ESXiLogAnalyzer


class LogsTab:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.colors = app.colors
        
        self.create_tab()
    # =========================================================================
    # GENERIC LOG ANALYZER UI
    # =========================================================================
    def _show_generic_analyzer(self):
        """Show the generic log analyzer interface."""
        self._clear_content()
        
        # === INPUT FRAME ===
        input_frame = ttk.LabelFrame(self.content_frame, text="📄 Generic Log Viewer",
                                    padding="15", style='Dark.TLabelframe')
        input_frame.grid(row=0, column=0, sticky='ew', padx=10, pady=10)
        input_frame.columnconfigure(1, weight=1)
        
        # Log file selection
        ttk.Label(input_frame, text="Log File:", 
                 style='DarkFrame.TLabel').grid(row=0, column=0, sticky='w', pady=5)
        
        file_frame = ttk.Frame(input_frame, style='Dark.TFrame')
        file_frame.grid(row=0, column=1, sticky='ew', pady=5, padx=(10, 0))
        file_frame.columnconfigure(0, weight=1)
        
        self.generic_file_entry = ttk.Entry(file_frame, font=('Segoe UI', 10))
        self.generic_file_entry.grid(row=0, column=0, sticky='ew', padx=(0, 10))
        
        ttk.Button(file_frame, text="📂 Browse", style='Dark.TButton',
                  command=self._generic_browse_file).grid(row=0, column=1)
        
        # File info label
        self.generic_file_info = ttk.Label(input_frame, text="", style='DarkFrame.TLabel')
        self.generic_file_info.grid(row=1, column=1, sticky='w', padx=(10, 0))
        
        # Date filters
        ttk.Separator(input_frame, orient='horizontal').grid(row=2, column=0, columnspan=2, sticky='ew', pady=10)
        
        ttk.Label(input_frame, text="Start Date:", 
                 style='DarkFrame.TLabel').grid(row=3, column=0, sticky='w', pady=5)
        
        start_frame = ttk.Frame(input_frame, style='Dark.TFrame')
        start_frame.grid(row=3, column=1, sticky='w', pady=5, padx=(10, 0))
        
        self.generic_start_entry = ttk.Entry(start_frame, font=('Segoe UI', 10), width=22)
        self.generic_start_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.generic_start_entry.insert(0, "(optional)")
        self.generic_start_entry.bind('<FocusIn>', 
            lambda e: self._clear_placeholder(self.generic_start_entry, "(optional)"))
        
        ttk.Button(start_frame, text="📅", style='Dark.TButton', width=3,
                  command=lambda: self._set_date(self.generic_start_entry, "start")).pack(side=tk.LEFT)
        
        ttk.Label(input_frame, text="End Date:", 
                 style='DarkFrame.TLabel').grid(row=4, column=0, sticky='w', pady=5)
        
        end_frame = ttk.Frame(input_frame, style='Dark.TFrame')
        end_frame.grid(row=4, column=1, sticky='w', pady=5, padx=(10, 0))
        
        self.generic_end_entry = ttk.Entry(end_frame, font=('Segoe UI', 10), width=22)
        self.generic_end_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.generic_end_entry.insert(0, "(optional)")
        self.generic_end_entry.bind('<FocusIn>', 
            lambda e: self._clear_placeholder(self.generic_end_entry, "(optional)"))
        
        ttk.Button(end_frame, text="📅", style='Dark.TButton', width=3,
                  command=lambda: self._set_date(self.generic_end_entry, "end")).pack(side=tk.LEFT)
        
        # Quick range buttons
        quick_frame = ttk.Frame(input_frame, style='Dark.TFrame')
        quick_frame.grid(row=5, column=1, sticky='w', pady=5, padx=(10, 0))
        
        ttk.Label(quick_frame, text="Quick:", style='DarkFrame.TLabel').pack(side=tk.LEFT, padx=(0, 10))
        for label, days in [("24h", 1), ("7d", 7), ("30d", 30)]:
            ttk.Button(quick_frame, text=label, style='Dark.TButton', width=5,
                      command=lambda d=days: self._generic_set_quick_range(d)).pack(side=tk.LEFT, padx=(0, 5))
        
        # Keyword/Regex filters
        ttk.Separator(input_frame, orient='horizontal').grid(row=6, column=0, columnspan=2, sticky='ew', pady=10)
        
        ttk.Label(input_frame, text="Keywords:", 
                 style='DarkFrame.TLabel').grid(row=7, column=0, sticky='w', pady=5)
        
        keyword_frame = ttk.Frame(input_frame, style='Dark.TFrame')
        keyword_frame.grid(row=7, column=1, sticky='ew', pady=5, padx=(10, 0))
        keyword_frame.columnconfigure(0, weight=1)
        
        self.generic_keyword_entry = ttk.Entry(keyword_frame, font=('Segoe UI', 10))
        self.generic_keyword_entry.grid(row=0, column=0, sticky='ew')
        
        ttk.Label(keyword_frame, text="(comma separated)", style='DarkFrame.TLabel',
                 font=('Segoe UI', 8)).grid(row=0, column=1, padx=(10, 0))
        
        ttk.Label(input_frame, text="Regex:", 
                 style='DarkFrame.TLabel').grid(row=8, column=0, sticky='w', pady=5)
        
        regex_frame = ttk.Frame(input_frame, style='Dark.TFrame')
        regex_frame.grid(row=8, column=1, sticky='ew', pady=5, padx=(10, 0))
        regex_frame.columnconfigure(0, weight=1)
        
        self.generic_regex_entry = ttk.Entry(regex_frame, font=('Segoe UI', 10))
        self.generic_regex_entry.grid(row=0, column=0, sticky='ew')
        
        ttk.Label(regex_frame, text="(optional pattern)", style='DarkFrame.TLabel',
                 font=('Segoe UI', 8)).grid(row=0, column=1, padx=(10, 0))
        
        # Options
        options_frame = ttk.Frame(input_frame, style='Dark.TFrame')
        options_frame.grid(row=9, column=1, sticky='w', pady=10, padx=(10, 0))
        
        self.generic_case_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Case Sensitive", variable=self.generic_case_var,
                       style='DarkFrame.TCheckbutton').pack(side=tk.LEFT, padx=(0, 20))
        
        self.generic_save_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Save Results to File", variable=self.generic_save_var,
                       style='DarkFrame.TCheckbutton').pack(side=tk.LEFT)
        
        # Action buttons
        btn_frame = ttk.Frame(input_frame, style='Dark.TFrame')
        btn_frame.grid(row=10, column=0, columnspan=2, pady=15)
        
        ttk.Button(btn_frame, text="🔍 SEARCH / FILTER", style='Success.TButton',
                  command=self._generic_start_analysis).pack(side=tk.LEFT, padx=(0, 10), ipadx=15)
        
        ttk.Button(btn_frame, text="📋 LOAD ALL", style='Dark.TButton',
                  command=self._generic_load_all).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(btn_frame, text="🗑️ Clear", style='Dark.TButton',
                  command=self._generic_clear_form).pack(side=tk.LEFT)
        
        # === RESULTS FRAME ===
        results_frame = ttk.LabelFrame(self.content_frame, text="📋 Log Contents",
                                      padding="10", style='Dark.TLabelframe')
        results_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=(0, 10))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Results text with line numbers
        text_frame = ttk.Frame(results_frame, style='Dark.TFrame')
        text_frame.grid(row=0, column=0, sticky='nsew')
        text_frame.columnconfigure(1, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        self.generic_results_text = tk.Text(text_frame, bg='#0a0a0a', fg='#00ff00',
                                           font=('Consolas', 9), wrap=tk.NONE)
        
        results_scrolly = ttk.Scrollbar(text_frame, orient=tk.VERTICAL,
                                       command=self.generic_results_text.yview)
        results_scrollx = ttk.Scrollbar(text_frame, orient=tk.HORIZONTAL,
                                       command=self.generic_results_text.xview)
        
        self.generic_results_text.config(yscrollcommand=results_scrolly.set,
                                        xscrollcommand=results_scrollx.set)
        
        self.generic_results_text.grid(row=0, column=0, sticky='nsew')
        results_scrolly.grid(row=0, column=1, sticky='ns')
        results_scrollx.grid(row=1, column=0, sticky='ew')
        
        # Results stats
        self.generic_stats_label = ttk.Label(results_frame, text="", style='DarkFrame.TLabel')
        self.generic_stats_label.grid(row=2, column=0, sticky='w', pady=(5, 0))
        
        self.generic_results_text.insert('1.0', "Select a log file and click 'Load All' or apply filters...")
    
    # === Generic Log Helper Methods ===
    
    def _generic_browse_file(self):
        """Browse for log file."""
        filepath = filedialog.askopenfilename(
            title="Select Log File",
            filetypes=[
                ("Log files", "*.log *.txt"),
                ("All files", "*.*")
            ]
        )
        if filepath:
            self.generic_file_entry.delete(0, tk.END)
            self.generic_file_entry.insert(0, filepath)
            
            # Get file info
            analyzer = GenericLogAnalyzer(app=self.app)
            stats = analyzer.get_log_stats(filepath)
            
            size_kb = stats['file_size'] / 1024
            size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB"
            
            info = f"📊 {stats['total_lines']:,} lines | {size_str}"
            if stats['first_timestamp'] and stats['last_timestamp']:
                info += f" | {stats['first_timestamp'].strftime('%Y-%m-%d')} to {stats['last_timestamp'].strftime('%Y-%m-%d')}"
            
            self.generic_file_info.config(text=info)
    
    def _generic_set_quick_range(self, days):
        """Set quick date range for generic analyzer."""
        end = datetime.now()
        start = end - timedelta(days=days)
        
        self.generic_start_entry.delete(0, tk.END)
        self.generic_start_entry.insert(0, start.strftime("%Y-%m-%d 00:00:00"))
        
        self.generic_end_entry.delete(0, tk.END)
        self.generic_end_entry.insert(0, end.strftime("%Y-%m-%d 23:59:59"))
    
    def _generic_clear_form(self):
        """Clear generic log form."""
        self.generic_file_entry.delete(0, tk.END)
        self.generic_file_info.config(text="")
        self.generic_start_entry.delete(0, tk.END)
        self.generic_start_entry.insert(0, "(optional)")
        self.generic_end_entry.delete(0, tk.END)
        self.generic_end_entry.insert(0, "(optional)")
        self.generic_keyword_entry.delete(0, tk.END)
        self.generic_regex_entry.delete(0, tk.END)
        self.generic_results_text.delete('1.0', tk.END)
        self.generic_stats_label.config(text="")
    
    def _generic_load_all(self):
        """Load entire log file without filters."""
        log_file = self.generic_file_entry.get()
        
        if not log_file or not os.path.exists(log_file):
            self.app.log_warning("Please select a valid log file")
            return
        
        def load():
            self.app.root.after(0, self.progress.start)
            self.app.root.after(0, lambda: self.app.log(f"📄 Loading: {os.path.basename(log_file)}"))
            
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    line_count = content.count('\n')
                
                # Update UI
                self.app.root.after(0, lambda: self._generic_display_results(content, line_count, line_count))
                self.app.root.after(0, lambda: self.app.log_success(f"Loaded {line_count:,} lines"))
                
            except Exception as e:
                self.app.root.after(0, lambda:self.app.log_error(f"Error: {str(e)}"))
            finally:
                self.app.root.after(0, self.progress.stop)
        
        threading.Thread(target=load, daemon=True).start()
    
    def _generic_start_analysis(self):
        """Start generic log analysis with filters."""
        log_file = self.generic_file_entry.get()
        
        if not log_file or not os.path.exists(log_file):
            self.app.log_warning("Please select a valid log file")
            return
        
        # Parse dates
        start_time, end_time = None, None
        start_str = self.generic_start_entry.get()
        end_str = self.generic_end_entry.get()
        
        try:
            if start_str and start_str != "(optional)":
                start_time = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
            if end_str and end_str != "(optional)":
                end_time = datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            self.app.log_warning(f"Invalid date format (use YYYY-MM-DD HH:MM:SS): {e}")
            return
        
        # Parse keywords
        keywords = None
        keyword_str = self.generic_keyword_entry.get().strip()
        if keyword_str:
            keywords = [k.strip() for k in keyword_str.split(',') if k.strip()]
        
        # Get regex
        regex_pattern = self.generic_regex_entry.get().strip() or None
        
        # Output file
        output_path = None
        if self.generic_save_var.get():
            base = os.path.splitext(log_file)[0]
            output_path = f"{base}_filtered.txt"
        
        def analyze():
            self.app.root.after(0, self.progress.start)
            
            analyzer = GenericLogAnalyzer(app=self.app)
            results = analyzer.analyze(
                log_file, output_path,
                start_time, end_time,
                keywords, regex_pattern,
                self.generic_case_var.get()
            )
            
            # Display results
            content = ''.join(results['matched_lines'])
            self.app.root.after(0, lambda: self._generic_display_results(
                content, results['filtered_lines'], results['total_lines']))
            
            self.app.root.after(0, self.progress.stop)
        
        threading.Thread(target=analyze, daemon=True).start()
    
    def _generic_display_results(self, content, matched, total):
        """Display results in text widget."""
        self.generic_results_text.delete('1.0', tk.END)
        self.generic_results_text.insert('1.0', content)
        self.generic_stats_label.config(text=f"Showing {matched:,} of {total:,} lines")
    
    def create_tab(self):
        """Create the Logs tab content."""
        tab = self.parent
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)
        
        # === LOG TOOLS BUTTONS ===
        tools_frame = ttk.LabelFrame(tab, text="📊 Log Analysis Tools", 
                                    padding="10", style='Dark.TLabelframe')
        tools_frame.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
        
        ttk.Button(tools_frame, text="🖥️ ESXi Logs", style='Dark.TButton',
                  command=self._show_esxi_analyzer).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(tools_frame, text="📄 Generic Log Viewer", style='Dark.TButton',
                  command=self._show_generic_analyzer).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(tools_frame, text="🪟 Windows Events", style='Dark.TButton',
                   command=self._show_windows_analyzer).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(tools_frame, text="🐧 Syslog", style='Dark.TButton',
                   command=self._show_syslog_analyzer).pack(side=tk.LEFT, padx=(0, 10))
        
        # === CONTENT FRAME ===
        self.content_frame = ttk.Frame(tab, style='DarkBg.TFrame')
        self.content_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.rowconfigure(0, weight=1)
        
        # Default message
        ttk.Label(self.content_frame, 
                 text="👆 Select a log analysis tool above to get started",
                 style='DarkFrame.TLabel', font=('Segoe UI', 12)).grid(row=0, column=0, pady=50)
        
        # Progress bar
        self.progress = ttk.Progressbar(tab, mode='indeterminate')
        self.progress.grid(row=2, column=0, sticky='ew', padx=5, pady=5)
    
    def _clear_content(self):
        """Clear the content frame."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        self.content_frame.rowconfigure(0, weight=0)
        self.content_frame.rowconfigure(1, weight=1)
    
    # =========================================================================
    # ESXi LOG ANALYZER UI
    # =========================================================================
    def _show_esxi_analyzer(self):
        """Show the ESXi log analyzer interface."""
        self._clear_content()
        
        # === INPUT FRAME ===
        input_frame = ttk.LabelFrame(self.content_frame, text="🖥️ ESXi Log Analyzer",
                                    padding="15", style='Dark.TLabelframe')
        input_frame.grid(row=0, column=0, sticky='ew', padx=10, pady=10)
        input_frame.columnconfigure(1, weight=1)
        
        # Archive file
        ttk.Label(input_frame, text="Log Archive:", 
                 style='DarkFrame.TLabel').grid(row=0, column=0, sticky='w', pady=5)
        
        file_frame = ttk.Frame(input_frame, style='Dark.TFrame')
        file_frame.grid(row=0, column=1, sticky='ew', pady=5, padx=(10, 0))
        file_frame.columnconfigure(0, weight=1)
        
        self.esxi_archive_entry = ttk.Entry(file_frame, font=('Segoe UI', 10))
        self.esxi_archive_entry.grid(row=0, column=0, sticky='ew', padx=(0, 10))
        
        ttk.Button(file_frame, text="📂 Browse", style='Dark.TButton',
                  command=self._esxi_browse_archive).grid(row=0, column=1)
        
        # Start date
        ttk.Label(input_frame, text="Start Date:", 
                 style='DarkFrame.TLabel').grid(row=1, column=0, sticky='w', pady=5)
        
        start_frame = ttk.Frame(input_frame, style='Dark.TFrame')
        start_frame.grid(row=1, column=1, sticky='w', pady=5, padx=(10, 0))
        
        self.esxi_start_entry = ttk.Entry(start_frame, font=('Segoe UI', 10), width=22)
        self.esxi_start_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.esxi_start_entry.insert(0, "YYYY-MM-DD HH:MM:SS")
        self.esxi_start_entry.bind('<FocusIn>', 
            lambda e: self._clear_placeholder(self.esxi_start_entry, "YYYY-MM-DD HH:MM:SS"))
        
        ttk.Button(start_frame, text="📅 Today", style='Dark.TButton',
                  command=lambda: self._set_date(self.esxi_start_entry, "start")).pack(side=tk.LEFT)
        
        # End date
        ttk.Label(input_frame, text="End Date:", 
                 style='DarkFrame.TLabel').grid(row=2, column=0, sticky='w', pady=5)
        
        end_frame = ttk.Frame(input_frame, style='Dark.TFrame')
        end_frame.grid(row=2, column=1, sticky='w', pady=5, padx=(10, 0))
        
        self.esxi_end_entry = ttk.Entry(end_frame, font=('Segoe UI', 10), width=22)
        self.esxi_end_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.esxi_end_entry.insert(0, "YYYY-MM-DD HH:MM:SS")
        self.esxi_end_entry.bind('<FocusIn>', 
            lambda e: self._clear_placeholder(self.esxi_end_entry, "YYYY-MM-DD HH:MM:SS"))
        
        ttk.Button(end_frame, text="📅 Today", style='Dark.TButton',
                  command=lambda: self._set_date(self.esxi_end_entry, "end")).pack(side=tk.LEFT)
        
        # Quick range buttons
        quick_frame = ttk.Frame(input_frame, style='Dark.TFrame')
        quick_frame.grid(row=3, column=1, sticky='w', pady=10, padx=(10, 0))
        
        ttk.Label(quick_frame, text="Quick:", style='DarkFrame.TLabel').pack(side=tk.LEFT, padx=(0, 10))
        for label, days in [("24h", 1), ("7 days", 7), ("30 days", 30)]:
            ttk.Button(quick_frame, text=label, style='Dark.TButton', width=8,
                      command=lambda d=days: self._set_quick_range(d)).pack(side=tk.LEFT, padx=(0, 5))
        
        # Output file
        ttk.Separator(input_frame, orient='horizontal').grid(row=4, column=0, columnspan=2, sticky='ew', pady=15)
        
        ttk.Label(input_frame, text="Output File:", 
                 style='DarkFrame.TLabel').grid(row=5, column=0, sticky='w', pady=5)
        
        output_frame = ttk.Frame(input_frame, style='Dark.TFrame')
        output_frame.grid(row=5, column=1, sticky='ew', pady=5, padx=(10, 0))
        output_frame.columnconfigure(0, weight=1)
        
        self.esxi_output_entry = ttk.Entry(output_frame, font=('Segoe UI', 10))
        self.esxi_output_entry.grid(row=0, column=0, sticky='ew', padx=(0, 10))
        
        ttk.Button(output_frame, text="💾 Save As", style='Dark.TButton',
                  command=self._esxi_browse_output).grid(row=0, column=1)
        
        # Action buttons
        btn_frame = ttk.Frame(input_frame, style='Dark.TFrame')
        btn_frame.grid(row=6, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="🚀 START ANALYSIS", style='Success.TButton',
                  command=self._esxi_start_analysis).pack(side=tk.LEFT, padx=(0, 10), ipadx=20)
        
        ttk.Button(btn_frame, text="🗑️ Clear", style='Dark.TButton',
                  command=self._esxi_clear_form).pack(side=tk.LEFT)
        
        # === RESULTS FRAME ===
        results_frame = ttk.LabelFrame(self.content_frame, text="📋 Results Preview",
                                      padding="10", style='Dark.TLabelframe')
        results_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=(0, 10))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        self.esxi_results_text = tk.Text(results_frame, height=15, bg='#0a0a0a', fg='#00ff00',
                                        font=('Consolas', 9))
        results_scroll = ttk.Scrollbar(results_frame, orient=tk.VERTICAL,
                                      command=self.esxi_results_text.yview)
        self.esxi_results_text.config(yscrollcommand=results_scroll.set)
        self.esxi_results_text.grid(row=0, column=0, sticky='nsew')
        results_scroll.grid(row=0, column=1, sticky='ns')
        
        self.esxi_results_text.insert('1.0', "Results will appear here after analysis...")
    
    # === ESXi Helper Methods ===
    
    def _clear_placeholder(self, entry, placeholder):
        """Clear placeholder text on focus."""
        if entry.get() == placeholder:
            entry.delete(0, tk.END)
    
    def _set_date(self, entry, date_type):
        """Set today's date."""
        entry.delete(0, tk.END)
        if date_type == "start":
            entry.insert(0, datetime.now().strftime("%Y-%m-%d 00:00:00"))
        else:
            entry.insert(0, datetime.now().strftime("%Y-%m-%d 23:59:59"))
    
    def _set_quick_range(self, days):
        """Set quick date range."""
        end = datetime.now()
        start = end - timedelta(days=days)
        
        self.esxi_start_entry.delete(0, tk.END)
        self.esxi_start_entry.insert(0, start.strftime("%Y-%m-%d 00:00:00"))
        
        self.esxi_end_entry.delete(0, tk.END)
        self.esxi_end_entry.insert(0, end.strftime("%Y-%m-%d 23:59:59"))
    
    def _esxi_browse_archive(self):
        """Browse for archive file."""
        filepath = filedialog.askopenfilename(
            title="Select ESXi Log Archive",
            filetypes=[("TAR/TGZ files", "*.tar *.tgz *.tar.gz"), ("All files", "*.*")]
        )
        if filepath:
            self.esxi_archive_entry.delete(0, tk.END)
            self.esxi_archive_entry.insert(0, filepath)
            
            # Auto-set output filename
            base = os.path.splitext(os.path.basename(filepath))[0]
            if base.endswith('.tar'):
                base = os.path.splitext(base)[0]
            output_path = os.path.join(os.path.dirname(filepath), f"{base}_filtered.txt")
            self.esxi_output_entry.delete(0, tk.END)
            self.esxi_output_entry.insert(0, output_path)
    
    def _esxi_browse_output(self):
        """Browse for output file."""
        filepath = filedialog.asksaveasfilename(
            title="Save Filtered Logs As",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filepath:
            self.esxi_output_entry.delete(0, tk.END)
            self.esxi_output_entry.insert(0, filepath)
    
    def _esxi_clear_form(self):
        """Clear all form fields."""
        self.esxi_archive_entry.delete(0, tk.END)
        self.esxi_start_entry.delete(0, tk.END)
        self.esxi_start_entry.insert(0, "YYYY-MM-DD HH:MM:SS")
        self.esxi_end_entry.delete(0, tk.END)
        self.esxi_end_entry.insert(0, "YYYY-MM-DD HH:MM:SS")
        self.esxi_output_entry.delete(0, tk.END)
        self.esxi_results_text.delete('1.0', tk.END)
        self.esxi_results_text.insert('1.0', "Results will appear here after analysis...")
    
    def _esxi_start_analysis(self):
        """Start the ESXi log analysis."""
        archive_file = self.esxi_archive_entry.get()
        output_file = self.esxi_output_entry.get()
        
        if not archive_file or not os.path.exists(archive_file):
            self.app.log_warning("Please select a valid archive file")
            return
        
        if not output_file:
            self.app.log_warning("Please specify an output file")
            return
        
        # Parse dates
        start_time, end_time = None, None
        start_str = self.esxi_start_entry.get()
        end_str = self.esxi_end_entry.get()
        
        try:
            if start_str and start_str != "YYYY-MM-DD HH:MM:SS":
                start_time = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
            if end_str and end_str != "YYYY-MM-DD HH:MM:SS":
                end_time = datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            self.app.log_warning(f"Invalid date format: {e}")
            return
        
        # Run in background
        def analyze():
            self.app.root.after(0, self.progress.start)
            
            analyzer = ESXiLogAnalyzer(app=self.app)
            results = analyzer.analyze(archive_file, output_file, start_time, end_time)
            
            # Show preview
            self.app.root.after(0, lambda: self._esxi_show_preview(output_file, results))
            self.app.root.after(0, self.progress.stop)
        
        threading.Thread(target=analyze, daemon=True).start()
    
    def _esxi_show_preview(self, output_file, results):
        """Show preview of filtered logs."""
        self.esxi_results_text.delete('1.0', tk.END)
        
        # Stats header
        self.esxi_results_text.insert('1.0', "═══ ANALYSIS RESULTS ═══\n\n")
        self.esxi_results_text.insert(tk.END, f"📁 Files processed: {results['total_files']}\n")
        self.esxi_results_text.insert(tk.END, f"📊 Total lines scanned: {results['total_lines']}\n")
        self.esxi_results_text.insert(tk.END, f"📋 Lines matching filter: {results['filtered_lines']}\n")
        
        if results['errors']:
            self.esxi_results_text.insert(tk.END, f"\n⚠️ Errors: {len(results['errors'])}\n")
        
        self.esxi_results_text.insert(tk.END, "\n═══ PREVIEW (first 200 lines) ═══\n\n")
        
        # Load preview
        try:
            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[:200]
                self.esxi_results_text.insert(tk.END, ''.join(lines))
                
                if len(lines) >= 200:
                    self.esxi_results_text.insert(tk.END, "\n\n... (truncated, see full file)")
            else:
                self.esxi_results_text.insert(tk.END, "No output file created (no matching lines)")
        except Exception as e:
            self.esxi_results_text.insert(tk.END, f"Error loading preview: {e}")
    
# =========================================================================
    # WINDOWS EVENT LOG ANALYZER UI
    # =========================================================================
    def _show_windows_analyzer(self):
        """Show the Windows Event Log analyzer interface."""
        self._clear_content()
        
        from utils.logs import WindowsEventLogAnalyzer
        
        # === INPUT FRAME ===
        input_frame = ttk.LabelFrame(self.content_frame, text="🪟 Windows Event Log Analyzer",
                                    padding="15", style='Dark.TLabelframe')
        input_frame.grid(row=0, column=0, sticky='ew', padx=10, pady=10)
        input_frame.columnconfigure(1, weight=1)
        
        # Log selection
        ttk.Label(input_frame, text="Event Log:", 
                 style='DarkFrame.TLabel').grid(row=0, column=0, sticky='w', pady=5)
        
        log_frame = ttk.Frame(input_frame, style='Dark.TFrame')
        log_frame.grid(row=0, column=1, sticky='w', pady=5, padx=(10, 0))
        
        self.win_log_var = tk.StringVar(value="System")
        
        # Get available logs
        analyzer = WindowsEventLogAnalyzer(app=self.app)
        available_logs = analyzer.get_available_logs()
        
        self.win_log_combo = ttk.Combobox(log_frame, textvariable=self.win_log_var,
                                         values=available_logs, state='readonly', width=40)
        self.win_log_combo.pack(side=tk.LEFT)
        
        # Common log buttons
        common_frame = ttk.Frame(input_frame, style='Dark.TFrame')
        common_frame.grid(row=1, column=1, sticky='w', pady=5, padx=(10, 0))
        
        for name in ["System", "Application", "Security"]:
            ttk.Button(common_frame, text=name, style='Dark.TButton', width=12,
                      command=lambda n=name: self.win_log_var.set(n)).pack(side=tk.LEFT, padx=(0, 5))
        
        # Time range
        ttk.Label(input_frame, text="Time Range:", 
                 style='DarkFrame.TLabel').grid(row=2, column=0, sticky='w', pady=5)
        
        time_frame = ttk.Frame(input_frame, style='Dark.TFrame')
        time_frame.grid(row=2, column=1, sticky='w', pady=5, padx=(10, 0))
        
        self.win_hours_var = tk.StringVar(value="24")
        ttk.Entry(time_frame, textvariable=self.win_hours_var, width=8, 
                 font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(time_frame, text="hours", style='DarkFrame.TLabel').pack(side=tk.LEFT, padx=(0, 20))
        
        for label, hours in [("1h", 1), ("24h", 24), ("7d", 168), ("30d", 720)]:
            ttk.Button(time_frame, text=label, style='Dark.TButton', width=5,
                      command=lambda h=hours: self.win_hours_var.set(str(h))).pack(side=tk.LEFT, padx=(0, 5))
        
        # Event level filter
        ttk.Label(input_frame, text="Level:", 
                 style='DarkFrame.TLabel').grid(row=3, column=0, sticky='w', pady=5)
        
        level_frame = ttk.Frame(input_frame, style='Dark.TFrame')
        level_frame.grid(row=3, column=1, sticky='w', pady=5, padx=(10, 0))
        
        self.win_level_var = tk.StringVar(value="All")
        levels = ["All", "Critical (1)", "Error (2)", "Warning (3)", "Information (4)"]
        ttk.Combobox(level_frame, textvariable=self.win_level_var, values=levels,
                    state='readonly', width=20).pack(side=tk.LEFT)
        
        # Event IDs
        ttk.Label(input_frame, text="Event IDs:", 
                 style='DarkFrame.TLabel').grid(row=4, column=0, sticky='w', pady=5)
        
        id_frame = ttk.Frame(input_frame, style='Dark.TFrame')
        id_frame.grid(row=4, column=1, sticky='ew', pady=5, padx=(10, 0))
        id_frame.columnconfigure(0, weight=1)
        
        self.win_ids_entry = ttk.Entry(id_frame, font=('Segoe UI', 10))
        self.win_ids_entry.grid(row=0, column=0, sticky='ew')
        ttk.Label(id_frame, text="(comma separated, optional)", style='DarkFrame.TLabel',
                 font=('Segoe UI', 8)).grid(row=0, column=1, padx=(10, 0))
        
        # Keywords
        ttk.Label(input_frame, text="Keywords:", 
                 style='DarkFrame.TLabel').grid(row=5, column=0, sticky='w', pady=5)
        
        kw_frame = ttk.Frame(input_frame, style='Dark.TFrame')
        kw_frame.grid(row=5, column=1, sticky='ew', pady=5, padx=(10, 0))
        kw_frame.columnconfigure(0, weight=1)
        
        self.win_keywords_entry = ttk.Entry(kw_frame, font=('Segoe UI', 10))
        self.win_keywords_entry.grid(row=0, column=0, sticky='ew')
        ttk.Label(kw_frame, text="(comma separated, optional)", style='DarkFrame.TLabel',
                 font=('Segoe UI', 8)).grid(row=0, column=1, padx=(10, 0))
        
        # Action buttons
        btn_frame = ttk.Frame(input_frame, style='Dark.TFrame')
        btn_frame.grid(row=6, column=0, columnspan=2, pady=15)
        
        ttk.Button(btn_frame, text="🔍 SEARCH EVENTS", style='Success.TButton',
                  command=self._win_start_search).pack(side=tk.LEFT, padx=(0, 10), ipadx=15)
        
        ttk.Button(btn_frame, text="💾 Export Results", style='Dark.TButton',
                  command=self._win_export).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(btn_frame, text="🗑️ Clear", style='Dark.TButton',
                  command=self._win_clear).pack(side=tk.LEFT)
        
        # === RESULTS FRAME ===
        results_frame = ttk.LabelFrame(self.content_frame, text="📋 Event Results",
                                      padding="10", style='Dark.TLabelframe')
        results_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=(0, 10))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Results treeview
        columns = ('time', 'id', 'level', 'message')
        self.win_tree = ttk.Treeview(results_frame, columns=columns, show='headings',
                                    style='Dark.Treeview')
        
        self.win_tree.heading('time', text='Time')
        self.win_tree.heading('id', text='Event ID')
        self.win_tree.heading('level', text='Level')
        self.win_tree.heading('message', text='Message')
        
        self.win_tree.column('time', width=150, minwidth=120)
        self.win_tree.column('id', width=80, minwidth=60)
        self.win_tree.column('level', width=100, minwidth=80)
        self.win_tree.column('message', width=500, minwidth=200)
        
        tree_scrolly = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.win_tree.yview)
        tree_scrollx = ttk.Scrollbar(results_frame, orient=tk.HORIZONTAL, command=self.win_tree.xview)
        self.win_tree.configure(yscrollcommand=tree_scrolly.set, xscrollcommand=tree_scrollx.set)
        
        self.win_tree.grid(row=0, column=0, sticky='nsew')
        tree_scrolly.grid(row=0, column=1, sticky='ns')
        tree_scrollx.grid(row=1, column=0, sticky='ew')
        
        # Color tags for levels
        self.win_tree.tag_configure('Critical', foreground='#ff4444')
        self.win_tree.tag_configure('Error', foreground='#ff8888')
        self.win_tree.tag_configure('Warning', foreground='#ffff44')
        self.win_tree.tag_configure('Information', foreground='#88ff88')
        
        self.win_stats_label = ttk.Label(results_frame, text="", style='DarkFrame.TLabel')
        self.win_stats_label.grid(row=2, column=0, sticky='w', pady=(5, 0))
        
        # Store results for export
        self.win_results = None
    
    def _win_start_search(self):
        """Search Windows Event Logs."""
        from utils.logs import WindowsEventLogAnalyzer
        
        log_name = self.win_log_var.get()
        
        try:
            hours = int(self.win_hours_var.get())
        except ValueError:
            self.app.log_warning("Invalid hours value")
            return
        
        # Parse level
        level = None
        level_str = self.win_level_var.get()
        if level_str != "All":
            level = int(level_str.split('(')[1].split(')')[0])
        
        # Parse event IDs
        event_ids = None
        ids_str = self.win_ids_entry.get().strip()
        if ids_str:
            try:
                event_ids = [int(id.strip()) for id in ids_str.split(',') if id.strip()]
            except ValueError:
                self.app.log_warning("Invalid event ID format")
                return
        
        # Parse keywords
        keywords = None
        kw_str = self.win_keywords_entry.get().strip()
        if kw_str:
            keywords = [k.strip() for k in kw_str.split(',') if k.strip()]
        
        def search():
            self.app.root.after(0, self.progress.start)
            
            analyzer = WindowsEventLogAnalyzer(app=self.app)
            results = analyzer.analyze(log_name, hours, level, event_ids, keywords)
            
            self.win_results = results
            self.app.root.after(0, lambda: self._win_display_results(results))
            self.app.root.after(0, self.progress.stop)
        
        threading.Thread(target=search, daemon=True).start()
    
    def _win_display_results(self, results):
        """Display Windows Event results."""
        # Clear tree
        for item in self.win_tree.get_children():
            self.win_tree.delete(item)
        
        # Add events
        for event in results['events']:
            tag = event['level'] if event['level'] in ['Critical', 'Error', 'Warning', 'Information'] else ''
            self.win_tree.insert('', 'end', values=(
                event['time'], event['id'], event['level'], event['message']
            ), tags=(tag,))
        
        self.win_stats_label.config(text=f"Found {results['total_events']} events")
    
    def _win_export(self):
        """Export Windows Event results."""
        if not self.win_results or not self.win_results['events']:
            self.app.log_warning("No results to export")
            return
        
        filepath = filedialog.asksaveasfilename(
            title="Export Events",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv")]
        )
        
        if filepath:
            from utils.logs import WindowsEventLogAnalyzer
            analyzer = WindowsEventLogAnalyzer(self.app.log)
            analyzer.results = self.win_results
            analyzer.export(filepath)
    
    def _win_clear(self):
        """Clear Windows Event form."""
        self.win_log_var.set("System")
        self.win_hours_var.set("24")
        self.win_level_var.set("All")
        self.win_ids_entry.delete(0, tk.END)
        self.win_keywords_entry.delete(0, tk.END)
        for item in self.win_tree.get_children():
            self.win_tree.delete(item)
        self.win_stats_label.config(text="")
        self.win_results = None
    
    # =========================================================================
    # SYSLOG ANALYZER UI
    # =========================================================================
    def _show_syslog_analyzer(self):
        """Show the Syslog analyzer interface."""
        self._clear_content()
        
        # For syslog, we can reuse the generic analyzer with syslog-specific options
        # or create a dedicated UI. Here's a simple approach:
        
        ttk.Label(self.content_frame, 
                 text="💡 Tip: Use the Generic Log Viewer for syslog files.\n"
                      "It automatically detects syslog timestamp format (Mon DD HH:MM:SS).",
                 style='DarkFrame.TLabel', font=('Segoe UI', 11),
                 justify='center').grid(row=0, column=0, pady=30)
        
        ttk.Button(self.content_frame, text="📄 Open Generic Log Viewer", 
                  style='Success.TButton',
                  command=self._show_generic_analyzer).grid(row=1, column=0)