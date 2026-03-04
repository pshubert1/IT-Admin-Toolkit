"""
Winget operations utilities.
"""

import subprocess
import sys
import threading
import shutil


class WingetManager:
    def __init__(self, app):
        self.app = app
        self.winget_exe = self._find_winget()
    
    def _find_winget(self):
        """Find the winget executable."""
        found = shutil.which("winget")
        if found:
            return found
        
        import os
        import glob
        common_paths = [
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WindowsApps\winget.exe"),
            r"C:\Program Files\WindowsApps\Microsoft.DesktopAppInstaller_*\winget.exe",
        ]
        for path in common_paths:
            matches = glob.glob(path)
            if matches:
                return matches[0]
        
        return "winget"
    
    def check(self):
        """Check if winget is available."""
        def _check():
            try:
                result = subprocess.run(
                    [self.winget_exe, "--version"], 
                    capture_output=True, text=True, timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )
                if result.returncode == 0:
                    version = result.stdout.strip()
                    self.app.root.after(0, lambda: self.app.log(f"✅ winget {version}"))
                else:
                    self.app.root.after(0, lambda: self.app.log("❌ winget not responding"))
            except FileNotFoundError:
                self.app.root.after(0, lambda: self.app.log("❌ winget not found - Install 'App Installer' from Microsoft Store"))
            except Exception as e:
                self.app.root.after(0, lambda: self.app.log(f"❌ winget error: {str(e)}"))
        
        threading.Thread(target=_check, daemon=True).start()
    
    def search(self, query):
        """Search winget repository."""
        if not query or not query.strip():
            self.app.log("⚠️ Enter search term first")
            return
        
        self.app.installer_tab.results_listbox.delete(0, 'end')
        threading.Thread(target=self._do_search, args=(query.strip(),), daemon=True).start()
    
    def _do_search(self, query):
        """Perform the actual search (runs in thread)."""
        try:
            self.app.root.after(0, lambda: self.app.log(f"🔍 Searching winget for '{query}'..."))
            result = subprocess.run(
                [self.winget_exe, "search", query, 
                 "--accept-source-agreements"], 
                capture_output=True, text=True, timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                data_lines = []
                for i, line in enumerate(lines):
                    if '---' in line:
                        data_lines = lines[i+1:]
                        break
                self.app.root.after(0, lambda: self._populate_results(data_lines))
            else:
                error = result.stderr.strip() or result.stdout.strip() or "Unknown error"
                self.app.root.after(0, lambda: self.app.log(f"❌ Search failed: {error[:200]}"))
        except subprocess.TimeoutExpired:
            self.app.root.after(0, lambda: self.app.log("⏰ Search timed out"))
        except FileNotFoundError:
            self.app.root.after(0, lambda: self.app.log("❌ winget not found - Install 'App Installer' from Microsoft Store"))
        except Exception as e:
            self.app.root.after(0, lambda: self.app.log(f"💥 Search error: {str(e)}"))
    
    def _populate_results(self, lines):
        """Populate the results listbox."""
        listbox = self.app.installer_tab.results_listbox
        listbox.delete(0, 'end')
        for line in lines:
            if line.strip():
                listbox.insert('end', line.strip())
        count = listbox.size()
        self.app.log(f"✅ Found {count} results")
    
    def install_apps(self, selected, checkboxes, install_btn, progress):
        """Install selected apps."""
        thread = threading.Thread(
            target=self._do_install, 
            args=(selected, checkboxes, install_btn, progress), 
            daemon=True
        )
        thread.start()
    
    def _do_install(self, selected, checkboxes, install_btn, progress):
        """Perform the actual installation (runs in thread)."""
        self.app.root.after(0, lambda: install_btn.config(state='disabled'))
        self.app.root.after(0, progress.start)
        self.app.root.after(0, lambda: self.app.log(f"🚀 Starting {len(selected)} installs..."))
        
        for app_name in selected:
            _, winget_id = checkboxes[app_name]
            self.app.root.after(0, lambda n=app_name: self.app.log(f"📥 Installing {n}..."))
            
            # Try silent first, then fallback
            attempts = [
                {
                    "label": "silent",
                    "cmd": [
                        self.winget_exe, "install", "-e", "--id", winget_id,
                        "--silent", "--accept-package-agreements", 
                        "--accept-source-agreements", "--disable-interactivity"
                    ]
                },
                {
                    "label": "interactive",
                    "cmd": [
                        self.winget_exe, "install", "-e", "--id", winget_id,
                        "--accept-package-agreements", "--accept-source-agreements"
                    ]
                }
            ]
            
            installed = False
            
            for attempt in attempts:
                cmd = attempt["cmd"]
                label = attempt["label"]
                
                if self.app.debug_mode.get():
                    self.app.root.after(0, lambda c=cmd: self.app.debug_log(f"CMD: {' '.join(c)}"))
                
                try:
                    process = subprocess.Popen(
                        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        universal_newlines=True, bufsize=1,
                        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                    )
                    
                    output_lines = []
                    for line in process.stdout:
                        stripped = line.strip()
                        if stripped:
                            output_lines.append(stripped)
                            if self.app.debug_mode.get():
                                self.app.root.after(0, lambda l=stripped: self.app.debug_log(f"  {l}"))
                    
                    process.wait(timeout=300)
                    exit_code = process.returncode
                    
                    # Log output on failure
                    if exit_code not in [0, 3010, -1978335189, 2316632107]:
                        output_text = '\n'.join(output_lines[-10:])
                        self.app.root.after(0, lambda o=output_text, l=label: 
                            self.app.debug_log(f"[{l}] OUTPUT:\n{o}"))
                    
                    # Success
                    if exit_code in [0, 3010]:
                        reboot = " (reboot needed)" if exit_code == 3010 else ""
                        self.app.root.after(0, lambda n=app_name, r=reboot: 
                            self.app.log(f"✅ {n} OK{r}"))
                        installed = True
                        break
                    
                    # Already installed
                    elif exit_code in [-1978335189, 2316632107]:
                        self.app.root.after(0, lambda n=app_name: 
                            self.app.log(f"✅ {n} already installed"))
                        installed = True
                        break
                    
                    # Not found
                    elif exit_code in [-1978335215, 2316632081]:
                        self.app.root.after(0, lambda n=app_name, wid=winget_id: 
                            self.app.log(f"❌ {n} - not found (ID: {wid})"))
                        installed = True
                        break
                    
                    # No applicable installer
                    elif exit_code in [-1978335212, 2316632084]:
                        if label == "silent":
                            self.app.root.after(0, lambda n=app_name: 
                                self.app.log(f"⚠️ {n} - silent failed, trying interactive..."))
                            continue
                        else:
                            self.app.root.after(0, lambda n=app_name, wid=winget_id: 
                                self.app.log(f"❌ {n} - no installer for this system (ID: {wid})"))
                            installed = True
                            break
                    
                    # Update available
                    elif exit_code in [-1978335188, 2316632108]:
                        self.app.root.after(0, lambda n=app_name: 
                            self.app.log(f"⬆️ {n} - already installed, newer version available"))
                        installed = True
                        break
                    
                    # Download failed
                    elif exit_code in [-1978335192, 2316632104]:
                        self.app.root.after(0, lambda n=app_name: 
                            self.app.log(f"❌ {n} - download failed"))
                        installed = True
                        break
                    
                    else:
                        if label == "silent":
                            self.app.root.after(0, lambda n=app_name, c=exit_code: 
                                self.app.log(f"⚠️ {n} - silent failed (code {c}), retrying..."))
                            continue
                        else:
                            self.app.root.after(0, lambda n=app_name, c=exit_code: 
                                self.app.log(f"❌ {n} failed (code {c})"))
                            installed = True
                            break
                    
                except subprocess.TimeoutExpired:
                    self.app.root.after(0, lambda n=app_name: 
                        self.app.log(f"⏰ {n} timeout (300s)"))
                    installed = True
                    break
                except FileNotFoundError:
                    self.app.root.after(0, lambda: 
                        self.app.log("❌ winget not found"))
                    installed = True
                    break
                except Exception as e:
                    self.app.root.after(0, lambda n=app_name, err=str(e): 
                        self.app.log(f"💥 {n} error: {err}"))
                    installed = True
                    break
            
            if not installed:
                self.app.root.after(0, lambda n=app_name: 
                    self.app.log(f"❌ {n} - all install methods failed"))
        
        self.app.root.after(0, lambda: self.app.log("🎉 All installations complete!"))
        self.app.root.after(0, progress.stop)
        self.app.root.after(0, lambda: install_btn.config(state='normal'))