"""
Bloatware Remover Tab UI
One-click removal of common Windows pre-installed apps and manufacturer crapware.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import subprocess


# Bloatware categories and their AppxPackage names
BLOATWARE = {
    "Microsoft Bloatware": [
        ("Clipchamp", "Clipchamp.Clipchamp"),
        ("Cortana", "Microsoft.549981C3F5F10"),
        ("Get Help", "Microsoft.GetHelp"),
        ("Microsoft News", "Microsoft.BingNews"),
        ("Microsoft Solitaire", "Microsoft.MicrosoftSolitaireCollection"),
        ("Microsoft Tips", "Microsoft.Getstarted"),
        ("Microsoft To-Do", "Microsoft.Todos"),
        ("Mixed Reality Portal", "Microsoft.MixedReality.Portal"),
        ("Movies & TV", "Microsoft.ZuneVideo"),
        ("MSN Weather", "Microsoft.BingWeather"),
        ("Office Hub", "Microsoft.MicrosoftOfficeHub"),
        ("OneNote (UWP)", "Microsoft.Office.OneNote"),
        ("Paint 3D", "Microsoft.MSPaint"),
        ("People", "Microsoft.People"),
        ("Power Automate", "Microsoft.PowerAutomateDesktop"),
        ("Skype", "Microsoft.SkypeApp"),
        ("Sticky Notes", "Microsoft.MicrosoftStickyNotes"),
        ("Voice Recorder", "Microsoft.WindowsSoundRecorder"),
        ("Widgets", "MicrosoftWindows.Client.WebExperience"),
        ("Xbox App", "Microsoft.GamingApp"),
        ("Xbox Game Bar", "Microsoft.XboxGamingOverlay"),
        ("Xbox Identity", "Microsoft.XboxIdentityProvider"),
        ("Xbox Speech-to-Text", "Microsoft.XboxSpeechToTextOverlay"),
        ("Your Phone", "Microsoft.YourPhone"),
    ],
    "Social / Entertainment": [
        ("TikTok", "BytedancePte.Ltd.TikTok"),
        ("Instagram", "Facebook.InstagramBeta"),
        ("Facebook", "Facebook.Facebook"),
        ("Spotify", "SpotifyAB.SpotifyMusic"),
        ("Disney+", "Disney.37853FC22B2CE"),
        ("Netflix", "4DF9E0F8.Netflix"),
        ("Amazon Prime Video", "AmazonVideo.PrimeVideo"),
        ("Hulu", "HuluLLC.HuluPlus"),
    ],
    "Games": [
        ("Candy Crush Saga", "king.com.CandyCrushSaga"),
        ("Candy Crush Friends", "king.com.CandyCrushFriends"),
        ("Farm Heroes Saga", "king.com.FarmHeroesSaga"),
        ("Bubble Witch 3", "king.com.BubbleWitch3Saga"),
        ("March of Empires", "A278AB0D.MarchofEmpires"),
        ("Minecraft (Trial)", "Microsoft.MinecraftUWP"),
    ],
    "Manufacturer Bloat": [
        ("Dell SupportAssist", "DellInc.DellSupportAssistforPCs"),
        ("Dell Digital Delivery", "DellInc.DellDigitalDelivery"),
        ("Dell Command Update", "DellInc.DellCommandUpdate"),
        ("HP Wolf Security", "AD2F1837.HPWolfSecurity"),
        ("HP Support Assistant", "AD2F1837.HPSupportAssistant"),
        ("HP Smart", "AD2F1837.HPSmart"),
        ("Lenovo Vantage", "E046963F.LenovoCompanion"),
        ("Lenovo Now", "4505Fortemedia.FMAPOControl"),
        ("McAfee Personal Security", "McAfeeInc.McAfeePersonalSecurity"),
        ("Norton 360", "NortonLifeLock.Norton360"),
        ("WildTangent Games", "WildTangentGames.*"),
    ],
    "Trials & Promotions": [
        ("Microsoft 365 Trial", "Microsoft.MicrosoftOfficeHub"),
        ("OneDrive (pre-installed)", "— Use script to remove —"),
        ("Dropbox Promo", "C27EB4BA.Dropbox"),
        ("ExpressVPN", "XP9KHVBFBR4X26.ExpressVPN"),
    ],
}


class BloatwareTab:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.colors = app.colors
        self.app_vars = {}  # {package_name: BooleanVar}
        
        self.create_tab()
    
    def create_tab(self):
        """Create the Bloatware Remover tab."""
        tab = self.parent
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)
        
        # Header
        header = ttk.Frame(tab, style='DarkBg.TFrame')
        header.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
        
        ttk.Button(header, text="🗑️ REMOVE SELECTED", style='Danger.TButton',
                  command=self._remove_selected).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(header, text="🔍 SCAN INSTALLED", style='Dark.TButton',
                  command=self._scan_installed).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(header, text="☑️ SELECT ALL", style='Dark.TButton',
                  command=self._select_all).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(header, text="☐ DESELECT ALL", style='Dark.TButton',
                  command=self._deselect_all).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(header, text="⚡ QUICK CLEAN", style='Warning.TButton',
                  command=self._quick_clean).pack(side=tk.LEFT)
        
        self.status_label = ttk.Label(header, text="", style='DarkFrame.TLabel')
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        # Scrollable content
        outer = ttk.Frame(tab, style='DarkBg.TFrame')
        outer.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
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
        
        # Build categories
        self._build_categories()
        
        # Progress
        self.progress = ttk.Progressbar(tab, mode='indeterminate')
        self.progress.grid(row=2, column=0, sticky='ew', padx=5, pady=5)
    
    def _build_categories(self):
        """Build bloatware category sections."""
        from ui.collapsible_frame import CollapsibleFrame
        
        for category_name, apps in BLOATWARE.items():
            section = CollapsibleFrame(self.scrollable, title=f"🗑️ {category_name}",
                                     style_colors=self.colors)
            section.pack(fill=tk.X, padx=10, pady=(0, 8))
            
            # Select All / Deselect All for category
            cat_btn_frame = ttk.Frame(section.content, style='Dark.TFrame')
            cat_btn_frame.pack(fill=tk.X, pady=(0, 5))
            
            cat_vars = []
            
            for display_name, package_id in apps:
                var = tk.BooleanVar(value=False)
                self.app_vars[package_id] = var
                cat_vars.append(var)
                
                cb = ttk.Checkbutton(section.content, 
                                    text=f"{display_name}  ({package_id})",
                                    variable=var, style='Dark.TCheckbutton')
                cb.pack(anchor=tk.W, pady=1)
            
            ttk.Button(cat_btn_frame, text="Select All", style='Dark.TButton',
                      command=lambda vs=cat_vars: [v.set(True) for v in vs]
                      ).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(cat_btn_frame, text="Deselect All", style='Dark.TButton',
                      command=lambda vs=cat_vars: [v.set(False) for v in vs]
                      ).pack(side=tk.LEFT)
    
    def _remove_selected(self):
        """Remove all selected bloatware."""
        selected = [pkg for pkg, var in self.app_vars.items() if var.get()]
        
        if not selected:
            self.app.log_warning("Select apps to remove first")
            return
        
        confirm = messagebox.askyesno("Confirm Removal",
                                     f"Remove {len(selected)} app(s)?\n\nThis cannot be undone.",
                                     parent=self.app.root)
        if not confirm:
            return
        
        self.progress.start()
        self.status_label.config(text=f"Removing {len(selected)} apps...")
        threading.Thread(target=self._do_remove, args=(selected,), daemon=True).start()
    
    def _do_remove(self, packages):
        """Background removal of apps."""
        removed = 0
        failed = 0
        
        for pkg in packages:
            if pkg.startswith("\u2014"):  # Skip placeholder entries
                continue
            
            try:
                # Remove for current user
                cmd = f"Get-AppxPackage -Name '{pkg}' -ErrorAction SilentlyContinue | Remove-AppxPackage -ErrorAction SilentlyContinue"
                result = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", cmd],
                    capture_output=True, text=True, timeout=30
                )
                
                # Also remove provisioned (prevents reinstall)
                cmd2 = f"Get-AppxProvisionedPackage -Online | Where-Object {{$_.PackageName -like '*{pkg}*'}} | Remove-AppxProvisionedPackage -Online -ErrorAction SilentlyContinue"
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command", cmd2],
                    capture_output=True, text=True, timeout=30
                )
                
                removed += 1
                self.parent.after(0, lambda p=pkg: self.app.log(f"Removed: {p}"))
            except Exception as e:
                failed += 1
                self.parent.after(0, lambda p=pkg, e=e: self.app.log_error(f"Failed: {p} - {str(e)[:50]}"))
        
        def finish():
            self.progress.stop()
            self.status_label.config(text=f"Done! Removed: {removed}, Failed: {failed}")
            self.app.log_success(f"Bloatware removal complete. Removed: {removed}, Failed: {failed}")
        
        self.parent.after(0, finish)
    
    def _scan_installed(self):
        """Scan which bloatware is currently installed."""
        self.status_label.config(text="Scanning...")
        threading.Thread(target=self._do_scan, daemon=True).start()
    
    def _do_scan(self):
        """Check which packages are installed."""
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", 
                 "Get-AppxPackage | Select-Object -ExpandProperty Name"],
                capture_output=True, text=True, timeout=20
            )
            
            installed = set(result.stdout.strip().split('\n')) if result.returncode == 0 else set()
            
            found = 0
            for pkg, var in self.app_vars.items():
                if any(pkg.lower() in inst.lower() for inst in installed):
                    var.set(True)
                    found += 1
                else:
                    var.set(False)
            
            self.parent.after(0, lambda: self.status_label.config(
                text=f"Found {found} installed bloatware apps"))
        except Exception as e:
            self.parent.after(0, lambda: self.status_label.config(text=f"Scan error: {str(e)[:40]}"))
    
    def _quick_clean(self):
        """Remove the most common/safe bloatware without confirmation per-item."""
        safe_removes = [
            "Clipchamp.Clipchamp", "king.com.CandyCrushSaga", "king.com.CandyCrushFriends",
            "king.com.FarmHeroesSaga", "BytedancePte.Ltd.TikTok", "Facebook.InstagramBeta",
            "Microsoft.BingNews", "Microsoft.BingWeather", "Microsoft.GetHelp",
            "Microsoft.Getstarted", "Microsoft.MixedReality.Portal",
            "Microsoft.People", "Microsoft.SkypeApp",
            "A278AB0D.MarchofEmpires", "Microsoft.549981C3F5F10",
        ]
        
        confirm = messagebox.askyesno("Quick Clean",
                                     f"Remove {len(safe_removes)} common bloatware apps?\n\n"
                                     "This includes: games, social media, Cortana, news, weather, etc.",
                                     parent=self.app.root)
        if confirm:
            self.progress.start()
            self.status_label.config(text="Quick cleaning...")
            threading.Thread(target=self._do_remove, args=(safe_removes,), daemon=True).start()
    
    def _select_all(self):
        for var in self.app_vars.values():
            var.set(True)
    
    def _deselect_all(self):
        for var in self.app_vars.values():
            var.set(False)
