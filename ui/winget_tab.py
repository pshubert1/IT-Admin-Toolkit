"""
Application Installer Tab UI
"""

import tkinter as tk
from tkinter import ttk
from config.winget import get_app_sections


class WingetTab:
    def __init__(self, parent, app):
        """
        Initialize the installer tab.
        
        Args:
            parent: The parent notebook tab frame
            app: Reference to main AppInstaller instance
        """
        self.parent = parent
        self.app = app
        self.colors = app.colors
        self.checkboxes = {}
        self.custom_result = None
        
        self.create_tab()
    
    def create_tab(self):
        """Create the Application Installer tab content."""
        tab = self.parent
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)
        
        # === SEARCH SECTION ===
        self._create_search_section(tab)
        
        # === PRESET APPS with SCROLLABLE CANVAS ===
        self._create_apps_section(tab)
        
        # === BUTTONS ===
        self._create_buttons(tab)
        
        # Progress bar
        self.progress = ttk.Progressbar(tab, mode='indeterminate')
        self.progress.grid(row=3, column=0, sticky='ew', padx=5, pady=5)
        
        # === BIND MOUSEWHEEL TO ALL CHILDREN ===
        self._bind_mousewheel_to_all(self.scrollable_frame)
    
    def _create_search_section(self, tab):
        """Create the winget search section."""
        search_frame = ttk.LabelFrame(tab, text="🔍 Search Winget Repository", 
                                      padding="10", style='Dark.TLabelframe')
        search_frame.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
        
        search_row = ttk.Frame(search_frame, style='Dark.TFrame')
        search_row.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_row, text="Search:", style='DarkFrame.TLabel').pack(side=tk.LEFT)
        self.search_entry = ttk.Entry(search_row, font=('Segoe UI', 11))
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 10))
        self.search_entry.bind('<Return>', lambda e: self.app.winget.search(self.search_entry.get()))
        
        ttk.Button(search_row, text="🔍 SEARCH", style='Dark.TButton', 
                  command=lambda: self.app.winget.search(self.search_entry.get())).pack(side=tk.LEFT)
        
        self.results_listbox = tk.Listbox(search_frame, height=4, bg=self.colors['bg'], 
                                        fg=self.colors['fg'], font=('Consolas', 10),
                                        selectbackground=self.colors['accent'])
        self.results_listbox.pack(fill=tk.X, pady=(0, 10))
        self.results_listbox.bind('<<ListboxSelect>>', self._on_result_select)
        
        ttk.Button(search_frame, text="⚡ INSTALL SELECTED", style='Dark.TButton', 
                  command=self._install_custom).pack()
    
    def _create_apps_section(self, tab):
        """Create the scrollable preset apps section."""
        apps_outer_frame = ttk.LabelFrame(tab, text="📦 Preset Applications", 
                                         padding="5", style='Dark.TLabelframe')
        apps_outer_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        apps_outer_frame.columnconfigure(0, weight=1)
        apps_outer_frame.rowconfigure(0, weight=1)
        
        # Create canvas with scrollbar
        self.apps_canvas = tk.Canvas(apps_outer_frame, bg=self.colors['frame_bg'], 
                                     highlightthickness=0)
        apps_scrollbar = ttk.Scrollbar(apps_outer_frame, orient=tk.VERTICAL, 
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
        
        # Mouse wheel scrolling on canvas
        self.apps_canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.apps_canvas.bind("<Button-4>", self._on_mousewheel)
        self.apps_canvas.bind("<Button-5>", self._on_mousewheel)
        
        self.apps_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        apps_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create 2-column layout
        left_frame = ttk.Frame(self.scrollable_frame, style='Dark.TFrame', padding="5")
        right_frame = ttk.Frame(self.scrollable_frame, style='Dark.TFrame', padding="5")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Get apps from config
        sections = get_app_sections()
        
        for section_title, apps_list, column in sections:
            parent_frame = left_frame if column == "left" else right_frame
            
            section_frame = ttk.LabelFrame(parent_frame, text=section_title, 
                                          padding="8", style='Dark.TLabelframe')
            section_frame.pack(fill=tk.X, pady=(0, 8))
            
            for name, winget_id in apps_list:
                var = tk.BooleanVar()
                cb = ttk.Checkbutton(section_frame, text=f"☐ {name}", variable=var, 
                                    style='DarkFrame.TCheckbutton')
                cb.pack(anchor='w', pady=2)
                self.checkboxes[name] = (var, winget_id)
    
    def _create_buttons(self, tab):
        """Create the action buttons."""
        btn_frame = ttk.Frame(tab, style='DarkBg.TFrame')
        btn_frame.grid(row=2, column=0, sticky='ew', padx=5, pady=5)
        
        self.install_btn = ttk.Button(btn_frame, text="⚡ INSTALL ALL SELECTED", 
                                      style='Dark.TButton', command=self._start_install)
        self.install_btn.pack(side=tk.LEFT, padx=(0, 10), ipadx=20)
        
        ttk.Button(btn_frame, text="🔍 CHECK WINGET", style='Dark.TButton', 
                  command=self.app.winget.check).pack(side=tk.LEFT)
    
    def _on_canvas_configure(self, event):
        self.apps_canvas.itemconfig(self.canvas_window, width=event.width)
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        if event.num == 5 or event.delta < 0:
            self.apps_canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0:
            self.apps_canvas.yview_scroll(-1, "units")
    
    def _bind_mousewheel_to_all(self, widget):
        """Recursively bind mousewheel to widget and all its children."""
        widget.bind("<MouseWheel>", self._on_mousewheel)
        widget.bind("<Button-4>", self._on_mousewheel)
        widget.bind("<Button-5>", self._on_mousewheel)
        
        for child in widget.winfo_children():
            self._bind_mousewheel_to_all(child)
    
    def _on_result_select(self, event):
        selection = self.results_listbox.curselection()
        if selection:
            item = self.results_listbox.get(selection[0])
            parts = item.split()
            if len(parts) >= 2:
                for part in parts:
                    if '.' in part and not part.startswith('v') and not part[0].isdigit():
                        self.custom_result = part
                        self.app.log(f"📦 Selected: {self.custom_result}")
                        return
                self.custom_result = parts[1]
                self.app.log(f"📦 Selected: {self.custom_result}")
    
    def _install_custom(self):
        if not self.custom_result:
            self.app.log_warning("Select a search result first")
            return
        
        self.app.log(f"🚀 Adding custom app: {self.custom_result}")
        var = tk.BooleanVar(value=True)
        self.checkboxes["Custom: " + self.custom_result.split('.')[0]] = (var, self.custom_result)
        self._start_install()
    
    def _start_install(self):
        selected = [name for name, (var, _) in self.checkboxes.items() if var.get()]
        if not selected:
            self.app.log_warning("Select at least one app")
            return
        
        self.app.winget.install_apps(selected, self.checkboxes, self.install_btn, self.progress)