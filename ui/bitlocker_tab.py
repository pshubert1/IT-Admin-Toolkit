"""
BitLocker Manager Tab UI
View status, manage encryption, backup keys for all drives.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import subprocess
import os
from datetime import datetime


class BitLockerTab:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.colors = app.colors
        self.drives = []
        
        self.create_tab()
        self._refresh_status()
    
    def create_tab(self):
        """Create the BitLocker Manager tab."""
        tab = self.parent
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)
        
        # Header
        header = ttk.Frame(tab, style='DarkBg.TFrame')
        header.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
        
        ttk.Button(header, text="🔄 REFRESH STATUS", style='Dark.TButton',
                  command=self._refresh_status).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(header, text="🔑 BACKUP KEY (C:)", style='Success.TButton',
                  command=self._backup_key).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(header, text="⏸️ SUSPEND (C:)", style='Warning.TButton',
                  command=self._suspend_bitlocker).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(header, text="▶️ RESUME (C:)", style='Dark.TButton',
                  command=self._resume_bitlocker).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(header, text="🔒 ENABLE (C:)", style='Success.TButton',
                  command=self._enable_bitlocker).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(header, text="🔓 DISABLE (C:)", style='Danger.TButton',
                  command=self._disable_bitlocker).pack(side=tk.LEFT)
        
        # Drive status list
        status_frame = ttk.LabelFrame(tab, text="🔐 BitLocker Drive Status",
                                     padding="10", style='Dark.TLabelframe')
        status_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        status_frame.columnconfigure(0, weight=1)
        status_frame.rowconfigure(0, weight=1)
        
        columns = ("drive", "status", "protection", "encryption", "method", "key_protectors")
        self.tree = ttk.Treeview(status_frame, columns=columns, show='headings',
                                style='Dark.Treeview', height=6)
        
        self.tree.heading("drive", text="Drive")
        self.tree.heading("status", text="Volume Status")
        self.tree.heading("protection", text="Protection")
        self.tree.heading("encryption", text="Encryption %")
        self.tree.heading("method", text="Method")
        self.tree.heading("key_protectors", text="Key Protectors")
        
        self.tree.column("drive", width=60)
        self.tree.column("status", width=150)
        self.tree.column("protection", width=100)
        self.tree.column("encryption", width=100)
        self.tree.column("method", width=120)
        self.tree.column("key_protectors", width=250)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        
        # Recovery key display
        key_frame = ttk.LabelFrame(tab, text="🔑 Recovery Key",
                                  padding="10", style='Dark.TLabelframe')
        key_frame.grid(row=2, column=0, sticky='ew', padx=5, pady=5)
        
        key_btn_frame = ttk.Frame(key_frame, style='Dark.TFrame')
        key_btn_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(key_btn_frame, text="👁️ SHOW KEY", style='Dark.TButton',
                  command=self._show_key).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(key_btn_frame, text="📋 COPY KEY", style='Dark.TButton',
                  command=self._copy_key).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(key_btn_frame, text="💾 SAVE TO FILE", style='Dark.TButton',
                  command=self._save_key_to_file).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(key_btn_frame, text="☁️ BACKUP TO AD", style='Dark.TButton',
                  command=self._backup_to_ad).pack(side=tk.LEFT)
        
        self.key_text = tk.Text(key_frame, height=3, bg='#0a0a0a', fg='#00ff00',
                               font=('Consolas', 11), state=tk.DISABLED)
        self.key_text.pack(fill=tk.X)
        
        # Status bar
        self.status_label = ttk.Label(tab, text="", style='DarkFrame.TLabel')
        self.status_label.grid(row=3, column=0, sticky='ew', padx=10, pady=5)
    
    def _refresh_status(self):
        """Refresh BitLocker status for all drives."""
        threading.Thread(target=self._do_refresh, daemon=True).start()
    
    def _do_refresh(self):
        """Background refresh."""
        try:
            script = """
            try {
                Get-BitLockerVolume | ForEach-Object {
                    $protectors = ($_.KeyProtector | ForEach-Object { $_.KeyProtectorType }) -join ', '
                    "$($_.MountPoint)|$($_.VolumeStatus)|$($_.ProtectionStatus)|$($_.EncryptionPercentage)|$($_.EncryptionMethod)|$protectors"
                }
            } catch {
                "ERROR|$($_.Exception.Message)"
            }
            """
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", script],
                capture_output=True, text=True, timeout=15
            )
            
            self.drives = []
            if result.returncode == 0 and result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    parts = line.strip().split('|')
                    if parts[0] == 'ERROR':
                        self.parent.after(0, lambda m=parts[1]: self.status_label.config(
                            text=f"⚠️ {m} (Run as Administrator)"))
                        return
                    if len(parts) >= 6:
                        self.drives.append({
                            'drive': parts[0],
                            'status': parts[1],
                            'protection': parts[2],
                            'encryption': parts[3],
                            'method': parts[4],
                            'protectors': parts[5],
                        })
            
            self.parent.after(0, self._update_tree)
        except Exception as e:
            self.parent.after(0, lambda: self.status_label.config(text=f"Error: {str(e)[:50]}"))
    
    def _update_tree(self):
        """Update the treeview."""
        self.tree.delete(*self.tree.get_children())
        for d in self.drives:
            self.tree.insert('', tk.END, values=(
                d['drive'], d['status'], d['protection'],
                f"{d['encryption']}%", d['method'], d['protectors']
            ))
        
        if self.drives:
            c_drive = next((d for d in self.drives if 'C:' in d['drive']), None)
            if c_drive:
                status_icon = "🔒" if c_drive['protection'] == 'On' else "🔓"
                self.status_label.config(text=f"{status_icon} C: Drive - {c_drive['status']} ({c_drive['protection']})")
        else:
            self.status_label.config(text="No BitLocker volumes found (run as Admin)")
    
    def _show_key(self):
        """Show the recovery key."""
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "(Get-BitLockerVolume -MountPoint 'C:').KeyProtector | Where-Object { $_.KeyProtectorType -eq 'RecoveryPassword' } | Select-Object -ExpandProperty RecoveryPassword"],
                capture_output=True, text=True, timeout=10
            )
            
            key = result.stdout.strip() if result.returncode == 0 else "Could not retrieve key (run as Admin)"
            
            self.key_text.config(state=tk.NORMAL)
            self.key_text.delete('1.0', tk.END)
            self.key_text.insert('1.0', key if key else "No recovery password found")
            self.key_text.config(state=tk.DISABLED)
        except Exception as e:
            self.app.log_error(f"Error: {str(e)}")
    
    def _copy_key(self):
        """Copy recovery key to clipboard."""
        key = self.key_text.get('1.0', tk.END).strip()
        if key and key != "No recovery password found":
            self.app.root.clipboard_clear()
            self.app.root.clipboard_append(key)
            self.app.log_success("Recovery key copied to clipboard")
        else:
            self._show_key()
    
    def _save_key_to_file(self):
        """Save recovery key to a file."""
        self._show_key()
        key = self.key_text.get('1.0', tk.END).strip()
        
        if not key or "Could not" in key or "No recovery" in key:
            self.app.log_warning("No key to save")
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile=f"BitLocker_Key_{os.environ.get('COMPUTERNAME', 'PC')}_{datetime.now().strftime('%Y%m%d')}.txt"
        )
        
        if filepath:
            with open(filepath, 'w') as f:
                f.write(f"BitLocker Recovery Key\n")
                f.write(f"Computer: {os.environ.get('COMPUTERNAME', '')}\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
                f.write(f"Drive: C:\n")
                f.write(f"\nRecovery Key: {key}\n")
            self.app.log_success(f"Key saved to: {filepath}")
    
    def _backup_key(self):
        """Backup recovery key to multiple locations."""
        script = """
        $vol = Get-BitLockerVolume -MountPoint 'C:'
        $rp = $vol.KeyProtector | Where-Object { $_.KeyProtectorType -eq 'RecoveryPassword' }
        if ($rp) {
            # Backup to AD if domain-joined
            try { Backup-BitLockerKeyProtector -MountPoint 'C:' -KeyProtectorId $rp.KeyProtectorId -ErrorAction SilentlyContinue } catch {}
            $rp.RecoveryPassword
        } else {
            "No recovery password protector found"
        }
        """
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", script],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                self.app.log_success(f"Key backed up. Key: {result.stdout.strip()[:20]}...")
            else:
                self.app.log_error("Backup failed (run as Admin)")
        except Exception as e:
            self.app.log_error(str(e))
    
    def _backup_to_ad(self):
        """Backup BitLocker key to Active Directory."""
        script = """
        $vol = Get-BitLockerVolume -MountPoint 'C:'
        $rp = $vol.KeyProtector | Where-Object { $_.KeyProtectorType -eq 'RecoveryPassword' }
        if ($rp) {
            Backup-BitLockerKeyProtector -MountPoint 'C:' -KeyProtectorId $rp.KeyProtectorId
            "Success"
        } else {
            "No recovery password found"
        }
        """
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", script],
                capture_output=True, text=True, timeout=10
            )
            if "Success" in result.stdout:
                self.app.log_success("BitLocker key backed up to Active Directory")
            else:
                self.app.log_warning(result.stdout.strip() or "Failed - machine may not be domain-joined")
        except Exception as e:
            self.app.log_error(str(e))
    
    def _suspend_bitlocker(self):
        """Suspend BitLocker (for BIOS updates, etc.)."""
        confirm = messagebox.askyesno("Suspend BitLocker",
                                     "Suspend BitLocker on C:?\n\nProtection will resume after next reboot.\n"
                                     "Use this before BIOS/firmware updates.",
                                     parent=self.app.root)
        if confirm:
            try:
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command",
                     "Suspend-BitLocker -MountPoint 'C:' -RebootCount 1"],
                    capture_output=True, text=True, timeout=10
                )
                self.app.log_success("BitLocker suspended for 1 reboot")
                self._refresh_status()
            except Exception as e:
                self.app.log_error(str(e))
    
    def _resume_bitlocker(self):
        """Resume BitLocker protection."""
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "Resume-BitLocker -MountPoint 'C:'"],
                capture_output=True, text=True, timeout=10
            )
            self.app.log_success("BitLocker resumed")
            self._refresh_status()
        except Exception as e:
            self.app.log_error(str(e))
    
    def _enable_bitlocker(self):
        """Enable BitLocker on C: drive."""
        confirm = messagebox.askyesno("Enable BitLocker",
                                     "Enable BitLocker encryption on C:?\n\n"
                                     "This will:\n"
                                     "- Use XTS-AES 256 encryption\n"
                                     "- Encrypt used space only\n"
                                     "- Create a recovery password\n\n"
                                     "Make sure TPM is available.",
                                     parent=self.app.root)
        if confirm:
            def run():
                try:
                    result = subprocess.run(
                        ["powershell", "-NoProfile", "-Command",
                         "Enable-BitLocker -MountPoint 'C:' -EncryptionMethod XtsAes256 -UsedSpaceOnly -RecoveryPasswordProtector"],
                        capture_output=True, text=True, timeout=30
                    )
                    if result.returncode == 0:
                        self.parent.after(0, lambda: self.app.log_success("BitLocker enabled! Save your recovery key."))
                        self.parent.after(0, self._show_key)
                    else:
                        self.parent.after(0, lambda: self.app.log_error(f"Failed: {result.stderr.strip()[:100]}"))
                    self.parent.after(0, self._refresh_status)
                except Exception as e:
                    self.parent.after(0, lambda: self.app.log_error(str(e)))
            threading.Thread(target=run, daemon=True).start()
    
    def _disable_bitlocker(self):
        """Disable BitLocker (decrypt drive)."""
        confirm = messagebox.askyesno("Disable BitLocker",
                                     "⚠️ DECRYPT C: drive?\n\n"
                                     "This will fully decrypt the drive.\n"
                                     "This process takes time and cannot be interrupted.",
                                     parent=self.app.root)
        if confirm:
            try:
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command",
                     "Disable-BitLocker -MountPoint 'C:'"],
                    capture_output=True, text=True, timeout=15
                )
                self.app.log_warning("BitLocker decryption started (will take time)")
                self._refresh_status()
            except Exception as e:
                self.app.log_error(str(e))
