"""
Windows Profile Remover Tool
Launches as a Toplevel window from the main app.
"""

import os
import shutil
import tkinter as tk
from tkinter import messagebox
import winreg

USERS_DIR = r"C:\Users"


class ProfileRemoverWindow:
    def __init__(self, parent, app=None):
        self.app = app
        self.window = tk.Toplevel(parent)
        self.window.title("Windows Profile Remover")
        self.window.geometry("450x500")
        self.window.minsize(350, 300)
        self.window.grab_set()  # Modal window
        
        # Match parent theme if available
        if app and hasattr(app, 'colors'):
            bg = app.colors['bg']
            fg = app.colors['fg']
            self.window.configure(bg=bg)
        else:
            bg = '#1e1e2e'
            fg = '#ffffff'
        
        # Try to inherit icon from parent
        try:
            self.window.iconbitmap(parent.iconbitmap())
        except:
            pass
        
        self.profile_info = {}
        
        # Header
        header = tk.Label(self.window, text="Select profiles to remove:", 
                         bg=bg, fg=fg, font=('Segoe UI', 10, 'bold'), anchor='w')
        header.pack(fill='x', padx=10, pady=(10, 5))
        
        # Warning
        warn = tk.Label(self.window, text="⚠️ This permanently deletes profile folders!", 
                       bg=bg, fg='#ffaa00', font=('Segoe UI', 9), anchor='w')
        warn.pack(fill='x', padx=10, pady=(0, 5))
        
        # Scrollable frame for checkboxes
        canvas_frame = tk.Frame(self.window, bg=bg)
        canvas_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.canvas = tk.Canvas(canvas_frame, bg=bg, highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient='vertical', command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas, bg=bg)
        
        self.scroll_frame.bind("<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Buttons
        btn_frame = tk.Frame(self.window, bg=bg)
        btn_frame.pack(fill='x', padx=10, pady=(5, 10))
        
        tk.Button(btn_frame, text="🔄 Refresh", command=self.refresh,
                 bg='#333355', fg=fg, relief='flat', padx=10, pady=5
                 ).pack(side='left', padx=(0, 5))
        
        tk.Button(btn_frame, text="☑ Select All", command=self._select_all,
                 bg='#333355', fg=fg, relief='flat', padx=10, pady=5
                 ).pack(side='left', padx=(0, 5))
        
        tk.Button(btn_frame, text="☐ Deselect All", command=self._deselect_all,
                 bg='#333355', fg=fg, relief='flat', padx=10, pady=5
                 ).pack(side='left')
        
        tk.Button(btn_frame, text="🗑️ Remove Selected", command=self.remove_selected,
                 bg='#cc3333', fg='white', relief='flat', padx=15, pady=5,
                 font=('Segoe UI', 9, 'bold')
                 ).pack(side='right')
        
        # Status bar
        self.status_var = tk.StringVar(value="Loading profiles...")
        status = tk.Label(self.window, textvariable=self.status_var, bg=bg, 
                         fg='#888888', font=('Consolas', 8), anchor='w')
        status.pack(fill='x', padx=10, pady=(0, 5))
        
        # Store colors for refresh
        self._bg = bg
        self._fg = fg
        
        # Load profiles
        self.check_vars = {}
        self.populate_profiles()
        self.refresh_display()
    
    def _log(self, msg):
        """Log to parent app if available."""
        if self.app and hasattr(self.app, 'log'):
            self.app.log(msg)
    
    def sid_to_account(self, sid):
        """Convert SID to username via registry."""
        try:
            reg_path = rf"SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\{sid}"
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
            profile_path, _ = winreg.QueryValueEx(key, "ProfileImagePath")
            winreg.CloseKey(key)
            
            username = os.path.basename(profile_path)
            computer = os.environ.get('COMPUTERNAME', 'PC')
            return f"{computer}\\{username}"
        except:
            return None

    def get_profile_info(self):
        """Get user profiles from registry."""
        profiles = {}
        current_user = os.environ.get('USERNAME', '').lower()
        
        # Folders to always skip
        exclude = {"All Users", "Default", "Default User", "Public", 
                   "DefaultAppPool", "defaultuser0"}
        
        try:
            reg_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList"
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
            
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    i += 1
                    
                    profile_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                               rf"{reg_path}\{subkey_name}")
                    try:
                        profile_path, _ = winreg.QueryValueEx(profile_key, "ProfileImagePath")
                        if profile_path and os.path.exists(profile_path):
                            folder = os.path.basename(profile_path)
                            
                            if folder in exclude:
                                continue
                            
                            display = self.sid_to_account(subkey_name) or folder
                            is_current = folder.lower() == current_user
                            
                            profiles[folder] = {
                                'path': profile_path,
                                'display': display,
                                'sid': subkey_name,
                                'is_current': is_current
                            }
                    finally:
                        winreg.CloseKey(profile_key)
                        
                except OSError:
                    break
                    
            winreg.CloseKey(key)
            
        except Exception:
            # Fallback: scan C:\Users
            for entry in sorted(os.listdir(USERS_DIR)):
                full_path = os.path.join(USERS_DIR, entry)
                if os.path.isdir(full_path) and entry not in exclude:
                    is_current = entry.lower() == current_user
                    profiles[entry] = {
                        'path': full_path,
                        'display': f"{os.environ.get('COMPUTERNAME', 'PC')}\\{entry}",
                        'sid': None,
                        'is_current': is_current
                    }
        
        return profiles

    def populate_profiles(self):
        self.profile_info = self.get_profile_info()

    def refresh_display(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.check_vars = {}

        if not self.profile_info:
            tk.Label(self.scroll_frame, text="No user profiles found.", 
                    bg=self._bg, fg=self._fg).pack(anchor="w")
            self.status_var.set("No profiles found")
            return

        for folder, info in sorted(self.profile_info.items(), key=lambda x: x[1]['display']):
            var = tk.BooleanVar()
            
            # Build display text
            display = info['display']
            if info.get('is_current'):
                display += "  ← CURRENT USER"
            
            # Get folder size
            try:
                size = sum(
                    os.path.getsize(os.path.join(dp, f))
                    for dp, _, fns in os.walk(info['path'])
                    for f in fns
                ) / (1024 * 1024 * 1024)  # GB
                display += f"  ({size:.1f} GB)"
            except:
                pass
            
            cb = tk.Checkbutton(self.scroll_frame, text=display, variable=var,
                               bg=self._bg, fg=self._fg, selectcolor='#333355',
                               activebackground=self._bg, activeforeground=self._fg,
                               font=('Consolas', 9))
            
            # Disable current user checkbox
            if info.get('is_current'):
                cb.configure(state='disabled', fg='#666666')
            
            cb.pack(anchor="w", pady=1)
            self.check_vars[folder] = var

        count = len(self.profile_info)
        self.status_var.set(f"{count} profiles found")

    def refresh(self):
        self.status_var.set("Refreshing...")
        self.window.update()
        self.populate_profiles()
        self.refresh_display()
    
    def _select_all(self):
        for folder, var in self.check_vars.items():
            info = self.profile_info.get(folder, {})
            if not info.get('is_current'):
                var.set(True)
    
    def _deselect_all(self):
        for var in self.check_vars.values():
            var.set(False)

    def remove_selected(self):
        selected = [f for f, v in self.check_vars.items() if v.get()]
        if not selected:
            messagebox.showinfo("No selection", "No profiles selected.", parent=self.window)
            return
        
        # Safety check — prevent removing current user
        current_user = os.environ.get('USERNAME', '').lower()
        for folder in selected:
            if folder.lower() == current_user:
                messagebox.showerror("Error", 
                    "Cannot remove the currently logged-in user profile!",
                    parent=self.window)
                return

        display_list = []
        for folder in selected:
            info = self.profile_info[folder]
            display_list.append(f"  • {info['display']}")
        
        confirm = messagebox.askyesno(
            "⚠️ Confirm Delete",
            f"Permanently delete {len(selected)} profile(s)?\n\n" + 
            "\n".join(display_list) +
            "\n\nThis cannot be undone!",
            parent=self.window
        )
        if not confirm:
            return

        errors = []
        removed = []
        
        for folder in selected:
            info = self.profile_info.get(folder)
            path = info['path'] if info else os.path.join(USERS_DIR, folder)
            display = info['display'] if info else folder
            
            self.status_var.set(f"Removing {display}...")
            self.window.update()
            
            try:
                shutil.rmtree(path)
                removed.append(display)
                self._log(f"🗑️ Removed profile: {display}")
                
                # Also try to remove registry entry
                if info and info.get('sid'):
                    try:
                        reg_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList"
                        winreg.DeleteKey(winreg.HKEY_LOCAL_MACHINE, 
                                        rf"{reg_path}\{info['sid']}")
                        self._log(f"   Cleaned registry for {display}")
                    except:
                        pass
                        
            except PermissionError:
                errors.append(f"{display}: Access denied (profile may be in use)")
            except Exception as e:
                errors.append(f"{display}: {str(e)}")

        if removed:
            self._log(f"✅ Removed {len(removed)} profile(s)")
        
        if errors:
            self._log(f"❌ {len(errors)} profile(s) failed to remove")
            messagebox.showerror("Errors", "\n".join(errors), parent=self.window)
        elif removed:
            messagebox.showinfo("Success", 
                f"Removed {len(removed)} profile(s).", parent=self.window)
        
        self.refresh()


def open_profile_remover(parent_root, app=None):
    """Launch the profile remover as a popup window."""
    ProfileRemoverWindow(parent_root, app)