"""
Winget Tab UI
"""

import tkinter as tk
from tkinter import ttk
from config.winget import get_app_sections


class WingetTab:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.colors = app.colors
        self.app_vars = {}       # {display_name: (BooleanVar, winget_id)}
        self.search_results = []
        self.custom_apps = []
        
        self.create_tab()
    
    def create_tab(self):
        """Create the Winget tab content."""
        tab = self.parent
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(0, weight=1)
        
        # Scrollable frame
        outer = ttk.Frame(tab, style='DarkBg.TFrame')
        outer.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(0, weight=1)
        
        self.canvas = tk.Canvas(outer, bg=self.colors['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable = ttk.Frame(self.canvas, style='DarkBg.TFrame')
        
        self.scrollable.bind("<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Build content
        self._create_app_checkboxes(self.scrollable)
        self._create_search_section(self.scrollable)
        self._create_buttons(tab)
        
        # Progress bar
        self.progress = ttk.Progressbar(tab, mode='indeterminate')
        self.progress.grid(row=2, column=0, sticky='ew', padx=5, pady=5)
    
    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)
    
    def _create_app_checkboxes(self, parent):
        """Create app category sections with checkboxes."""
        for category_name, apps, position in get_app_sections():
            frame = ttk.LabelFrame(parent, text=category_name, 
                                  padding="10", style='Dark.TLabelframe')
            frame.pack(fill=tk.X, padx=10, pady=(0, 10))
            
            # Select All / Deselect All for this category
            cat_btn_frame = ttk.Frame(frame, style='Dark.TFrame')
            cat_btn_frame.pack(fill=tk.X, pady=(0, 5))
            
            cat_vars = []  # Track vars in this category
            
            for display_name, winget_id in apps:
                var = tk.BooleanVar(value=False)
                self.app_vars[display_name] = (var, winget_id)
                cat_vars.append(var)
                
                ttk.Checkbutton(frame, text=f"{display_name}  ({winget_id})", 
                               variable=var, style='Dark.TCheckbutton').pack(
                               anchor=tk.W, pady=1)
            
            # Select all / deselect all buttons for category
            ttk.Button(cat_btn_frame, text="Select All", style='Dark.TButton',
                      command=lambda vs=cat_vars: [v.set(True) for v in vs]
                      ).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(cat_btn_frame, text="Deselect All", style='Dark.TButton',
                      command=lambda vs=cat_vars: [v.set(False) for v in vs]
                      ).pack(side=tk.LEFT)
    
    def _create_search_section(self, parent):
        """Create the winget search section."""
        search_frame = ttk.LabelFrame(parent, text="🔍 Search Winget Repository",
                                     padding="10", style='Dark.TLabelframe')
        search_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Search input row
        input_frame = ttk.Frame(search_frame, style='Dark.TFrame')
        input_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.search_entry = tk.Entry(input_frame, bg=self.colors['bg'], 
                                    fg=self.colors['fg'], font=('Consolas', 10),
                                    insertbackground='white')
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.search_entry.bind('<Return>', lambda e: self._do_search())
        
        ttk.Button(input_frame, text="🔍 SEARCH", style='Dark.TButton',
                  command=self._do_search).pack(side=tk.LEFT)
        
        # Results listbox
        self.search_listbox = tk.Listbox(search_frame, height=6, bg=self.colors['bg'],
                                        fg=self.colors['fg'], font=('Consolas', 9),
                                        selectmode=tk.SINGLE)
        self.search_listbox.pack(fill=tk.X, pady=(5, 5))
        
        # Add selected button
        ttk.Button(search_frame, text="➕ ADD SELECTED TO INSTALL", style='Success.TButton',
                  command=self._add_search_result).pack(fill=tk.X)
    
    def _create_buttons(self, parent):
        """Create the action buttons."""
        btn_frame = ttk.Frame(parent, style='DarkBg.TFrame')
        btn_frame.grid(row=1, column=0, sticky='ew', padx=5, pady=5)
        
        self.install_btn = ttk.Button(btn_frame, text="📦 INSTALL ALL SELECTED", 
                                     style='Success.TButton',
                                     command=self._install_selected)
        self.install_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(btn_frame, text="🔄 CHECK WINGET", style='Dark.TButton',
                  command=self.app.winget.check).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(btn_frame, text="☐ SELECT ALL", style='Dark.TButton',
                  command=self._select_all).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(btn_frame, text="☐ DESELECT ALL", style='Dark.TButton',
                  command=self._deselect_all).pack(side=tk.LEFT)
    
    def _do_search(self):
        """Search winget repository."""
        query = self.search_entry.get().strip()
        if not query:
            self.app.log_warning("Enter a search term")
            return
        
        self.search_listbox.delete(0, tk.END)
        
        def on_results(results):
            self.search_results = results
            for line in results:
                self.search_listbox.insert(tk.END, line)
        
        self.app.winget.search(query, callback=on_results)
    
    def _add_search_result(self):
        """Add selected search result to the install list."""
        selection = self.search_listbox.curselection()
        if not selection:
            self.app.log_warning("Select an app from search results first")
            return
        
        line = self.search_listbox.get(selection[0])
        
        # Parse the winget ID from the result line
        # Winget output format: "Name                    Id              Source"
        parts = line.split()
        winget_id = None
        
        # Find the part that looks like a winget ID (contains dots)
        for part in parts:
            if '.' in part and part[0].isupper():
                winget_id = part
        
        if not winget_id:
            # Try just using the second-to-last column
            if len(parts) >= 2:
                winget_id = parts[-2] if parts[-1] in ('winget', 'msstore') else parts[-1]
        
        if winget_id:
            display_name = f"Custom: {winget_id}"
            
            # Don't add duplicates
            if display_name in self.app_vars:
                self.app.log_warning(f"{winget_id} already in list")
                return
            
            var = tk.BooleanVar(value=True)  # Pre-checked
            self.app_vars[display_name] = (var, winget_id)
            self.custom_apps.append((display_name, winget_id))
            
            self.app.log(f"📦 Selected: {winget_id}")
            self.app.log(f"🚀 Added to install list (pre-checked)")
        else:
            self.app.log_warning("Could not parse winget ID from selection")
    
    def _install_selected(self):
        """Install all checked apps."""
        # Collect all checked apps
        selected = []
        for display_name, (var, winget_id) in self.app_vars.items():
            if var.get():
                selected.append((display_name, winget_id))
        
        if not selected:
            self.app.log_warning("Select at least one app to install")
            return
        
        # Disable button during install
        self.install_btn.config(state="disabled")
        self.progress.start()
        
        def on_complete():
            self.progress.stop()
            self.install_btn.config(state="normal")
        
        self.app.winget.install_apps(
            selected, 
            progress_callback=None,
            complete_callback=on_complete
        )
    
    def _select_all(self):
        """Check all app checkboxes."""
        for var, _ in self.app_vars.values():
            var.set(True)
    
    def _deselect_all(self):
        """Uncheck all app checkboxes."""
        for var, _ in self.app_vars.values():
            var.set(False)