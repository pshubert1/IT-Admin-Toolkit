"""
PowerShell Scripts Tab UI
"""

import tkinter as tk
from tkinter import ttk, filedialog
import os
from config.scripts import get_script_sections
from utils.network import NetworkDiagnostics
from utils.profile_remover import open_profile_remover
from utils.rmm_installer import open_rmm_installer


class ScriptsTab:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.colors = app.colors
        
        self.create_tab()
    
    def create_tab(self):
        """Create the PowerShell Scripts tab content."""
        tab = self.parent
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(0, weight=1)
        
        scripts_outer = ttk.Frame(tab, style='DarkBg.TFrame')
        scripts_outer.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        scripts_outer.columnconfigure(0, weight=1)
        scripts_outer.rowconfigure(0, weight=1)
        
        self.scripts_canvas = tk.Canvas(scripts_outer, bg=self.colors['bg'], highlightthickness=0)
        scripts_scrollbar = ttk.Scrollbar(scripts_outer, orient=tk.VERTICAL, 
                                         command=self.scripts_canvas.yview)
        self.scripts_scrollable = ttk.Frame(self.scripts_canvas, style='DarkBg.TFrame')
        
        self.scripts_scrollable.bind(
            "<Configure>",
            lambda e: self.scripts_canvas.configure(scrollregion=self.scripts_canvas.bbox("all"))
        )
        
        self.scripts_canvas_window = self.scripts_canvas.create_window((0, 0), 
                                                                       window=self.scripts_scrollable, 
                                                                       anchor="nw")
        self.scripts_canvas.configure(yscrollcommand=scripts_scrollbar.set)
        self.scripts_canvas.bind('<Configure>', self._on_canvas_configure)
        
        self.scripts_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scripts_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Build script sections
        self._create_script_buttons()
        
        # Custom script section
        self._create_custom_section()
        
        # Script output section
        self._create_output_section()
        
        # Progress bar
        self.script_progress = ttk.Progressbar(tab, mode='indeterminate')
        self.script_progress.grid(row=1, column=0, sticky='ew', padx=5, pady=5)
    
    def _create_script_buttons(self):
        """Create all the script section buttons - merged built-in + folder scripts."""
        script_sections = get_script_sections()
        
        for section_title, scripts in script_sections:
            section_frame = ttk.LabelFrame(self.scripts_scrollable, text=section_title, 
                                          padding="10", style='Dark.TLabelframe')
            section_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
            
            for script_data in scripts:
                # Handle both 4-item and 5-item tuples
                if len(script_data) == 5:
                    script_name, script_content, description, btn_style, interactive = script_data
                else:
                    script_name, script_content, description, btn_style = script_data
                    interactive = False
                
                script_row = ttk.Frame(section_frame, style='Dark.TFrame')
                script_row.pack(fill=tk.X, pady=4)
                
                display_name = f"📺 {script_name}" if interactive else script_name
                
                btn = ttk.Button(
                    script_row, 
                    text=display_name, 
                    style=btn_style, 
                    width=35,
                    command=lambda s=script_content, n=script_name, i=interactive: self.app.powershell.run(s, n, i)
                )
                btn.pack(side=tk.LEFT, padx=(0, 10))
                
                desc_text = f"{description} (opens in new window)" if interactive else description
                desc_label = ttk.Label(script_row, text=desc_text, style='DarkFrame.TLabel',
                                      font=('Segoe UI', 9))
                desc_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # ── Add Profile Remover to Admin Tasks section ──
            if "Admin Task" in section_title:
                tool_row = ttk.Frame(section_frame, style='Dark.TFrame')
                tool_row.pack(fill=tk.X, pady=4)
                
                ttk.Button(
                    tool_row, text="👤 Profile Remover",
                    style='Dark.TButton', width=35,
                    command=lambda: open_profile_remover(self.app.root, self.app)
                ).pack(side=tk.LEFT, padx=(0, 10))
                
                ttk.Label(tool_row, text="Remove Windows user profiles",
                         style='DarkFrame.TLabel', font=('Segoe UI', 9)
                ).pack(side=tk.LEFT, fill=tk.X, expand=True)
                if "Admin Task" in section_title:
                # Profile Remover
                    tool_row = ttk.Frame(section_frame, style='Dark.TFrame')
                    tool_row.pack(fill=tk.X, pady=4)
                
                ttk.Button(
                    tool_row, text="👤 Profile Remover",
                    style='Dark.TButton', width=35,
                    command=lambda: open_profile_remover(self.app.root, self.app)
                ).pack(side=tk.LEFT, padx=(0, 10))
                
                ttk.Label(tool_row, text="Remove Windows user profiles",
                         style='DarkFrame.TLabel', font=('Segoe UI', 9)
                ).pack(side=tk.LEFT, fill=tk.X, expand=True)
                
                # RMM Installer
                rmm_row = ttk.Frame(section_frame, style='Dark.TFrame')
                rmm_row.pack(fill=tk.X, pady=4)
                
                ttk.Button(
                    rmm_row, text="📥 RMM Agent Installer",
                    style='Dark.TButton', width=35,
                    command=lambda: open_rmm_installer(self.app.root, self.app)
                ).pack(side=tk.LEFT, padx=(0, 10))
                
                ttk.Label(rmm_row, text="Download & install RMM agent from URL",
                         style='DarkFrame.TLabel', font=('Segoe UI', 9)
                ).pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    
                if "Admin Task" in section_title:
                # Profile Remover
                    tool_row = ttk.Frame(section_frame, style='Dark.TFrame')
                    tool_row.pack(fill=tk.X, pady=4)
                
                ttk.Button(
                    tool_row, text="👤 Profile Remover",
                    style='Dark.TButton', width=35,
                    command=lambda: open_profile_remover(self.app.root, self.app)
                ).pack(side=tk.LEFT, padx=(0, 10))
                
                ttk.Label(tool_row, text="Remove Windows user profiles",
                         style='DarkFrame.TLabel', font=('Segoe UI', 9)
                ).pack(side=tk.LEFT, fill=tk.X, expand=True)
                
                # RMM Installer
                rmm_row = ttk.Frame(section_frame, style='Dark.TFrame')
                rmm_row.pack(fill=tk.X, pady=4)
                
                ttk.Button(
                    rmm_row, text="📥 RMM Agent Installer",
                    style='Dark.TButton', width=35,
                    command=lambda: open_rmm_installer(self.app.root, self.app)
                ).pack(side=tk.LEFT, padx=(0, 10))
                
                ttk.Label(rmm_row, text="Download & install RMM agent from URL",
                         style='DarkFrame.TLabel', font=('Segoe UI', 9)
                ).pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    
    def _create_custom_section(self):
        """Create the custom script input section."""
        custom_frame = ttk.LabelFrame(self.scripts_scrollable, text="📝 Custom Script", 
                                     padding="10", style='Dark.TLabelframe')
        custom_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.custom_script_text = tk.Text(custom_frame, height=5, bg=self.colors['bg'], 
                                         fg='#00ff00', font=('Consolas', 10),
                                         insertbackground='white')
        self.custom_script_text.pack(fill=tk.X, pady=(0, 10))
        self.custom_script_text.insert('1.0', '# Enter your PowerShell script here\nGet-Date')
        
        custom_btn_frame = ttk.Frame(custom_frame, style='Dark.TFrame')
        custom_btn_frame.pack(fill=tk.X)
        
        ttk.Button(custom_btn_frame, text="▶️ RUN SCRIPT", style='Success.TButton',
                  command=self._run_custom_script).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(custom_btn_frame, text="📺 RUN INTERACTIVE", style='Warning.TButton',
                  command=self._run_custom_interactive).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(custom_btn_frame, text="📂 LOAD FILE", style='Dark.TButton',
                  command=self._load_script_from_file).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(custom_btn_frame, text="🗑️ CLEAR", style='Dark.TButton',
                  command=lambda: self.custom_script_text.delete('1.0', tk.END)).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(custom_btn_frame, text="🌐 Network Diag", style='Dark.TButton',
                  command=self._run_network_diagnostic).pack(side=tk.LEFT)
    
    def _create_output_section(self):
        """Create the script output display section."""
        output_frame = ttk.LabelFrame(self.scripts_scrollable, text="📤 Script Output", 
                                     padding="10", style='Dark.TLabelframe')
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.script_output = tk.Text(output_frame, height=10, bg='#0a0a0a', fg='#00ff00', 
                                    font=('Consolas', 9), state=tk.NORMAL)
        output_scroll = ttk.Scrollbar(output_frame, orient=tk.VERTICAL, 
                                     command=self.script_output.yview)
        self.script_output.config(yscrollcommand=output_scroll.set)
        self.script_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        output_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _on_canvas_configure(self, event):
        self.scripts_canvas.itemconfig(self.scripts_canvas_window, width=event.width)
    
    def _run_custom_script(self):
        """Run the custom script from the text area (background mode)."""
        script = self.custom_script_text.get('1.0', tk.END).strip()
        if not script or script == '# Enter your PowerShell script here':
            self.app.log_warning("Enter a script first")
            return
        self.app.powershell.run(script, "Custom Script", interactive=False)
    
    def _run_custom_interactive(self):
        """Run the custom script in interactive mode (visible window)."""
        script = self.custom_script_text.get('1.0', tk.END).strip()
        if not script or script == '# Enter your PowerShell script here':
            self.app.log_warning("Enter a script first")
            return
        self.app.powershell.run(script, "Custom Script", interactive=True)
    
    def _load_script_from_file(self):
        """Load a PowerShell script from a file."""
        filetypes = [
            ("PowerShell Scripts", "*.ps1"),
            ("All Files", "*.*")
        ]
        filepath = filedialog.askopenfilename(title="Select PowerShell Script", filetypes=filetypes)
        
        if filepath:
            try:
                content = None
                for encoding in ['utf-8-sig', 'utf-8', 'utf-16', 'latin-1']:
                    try:
                        with open(filepath, 'r', encoding=encoding) as f:
                            content = f.read()
                        break
                    except (UnicodeDecodeError, UnicodeError):
                        continue
                
                if content:
                    self.custom_script_text.delete('1.0', tk.END)
                    self.custom_script_text.insert('1.0', content)
                    self.app.log_success(f"Loaded: {os.path.basename(filepath)}")
                else:
                    self.app.log_error("Could not read file",
                        hint="The file encoding is not supported")
                    
            except Exception as e:
                self.app.log_error(f"Failed to load file: {str(e)}")
    
    def _run_network_diagnostic(self):
        """Run network diagnostics in background."""
        import threading
        
        def run():
            diag = NetworkDiagnostics(app=self.app)
            diag.run_all(save_report=True)
        
        threading.Thread(target=run, daemon=True).start()