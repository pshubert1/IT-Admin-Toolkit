"""
Winget operations utility.
"""

import subprocess
import threading
import sys
import os
import shutil


class WingetManager:
    def __init__(self, app):
        self.app = app
        self.winget_exe = self._find_winget()
    
    def _find_winget(self):
        """Find winget executable path."""
        # Check common paths first
        common_paths = [
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 
                        'Microsoft', 'WindowsApps', 'winget.exe'),
            os.path.join(os.environ.get('PROGRAMFILES', ''), 
                        'WindowsApps', 'winget.exe'),
        ]
        
        for path in common_paths:
            if path and os.path.exists(path):
                return path
        
        # Try shutil.which
        found = shutil.which('winget')
        if found:
            return found
        
        # Try running it directly
        try:
            result = subprocess.run(
                ['where', 'winget'], 
                capture_output=True, text=True, timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split('\n')[0].strip()
        except:
            pass
        
        return None
    
    def _ensure_winget(self):
        """Verify winget is available, return True/False."""
        if self.winget_exe and os.path.exists(self.winget_exe):
            return True
        
        # Try finding it again
        self.winget_exe = self._find_winget()
        if self.winget_exe:
            return True
        
        self.app.root.after(0, lambda: self.app.log_error(
            "winget not found",
            hint="Install 'App Installer' from the Microsoft Store"
        ))
        return False
    def check(self):
        """Check if winget is available and log the result."""
        def _do_check():
            if not self._ensure_winget():
                return
            
            try:
                result = subprocess.run(
                    [self.winget_exe, "--version"],
                    capture_output=True, text=True, timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                if result.returncode == 0:
                    version = result.stdout.strip()
                    self.app.root.after(0, lambda: self.app.log_success(f"Winget {version} is available"))
                else:
                    self.app.root.after(0, lambda: self.app.log_error(
                        "Winget check failed",
                        hint="Try reinstalling 'App Installer' from the Microsoft Store"
                    ))
                    
            except subprocess.TimeoutExpired:
                self.app.root.after(0, lambda: self.app.log_error("Winget check timed out"))
            except Exception as e:
                self.app.root.after(0, lambda: self.app.log_error(f"Winget check failed: {e}"))
        
        threading.Thread(target=_do_check, daemon=True).start()
    
    def search(self, query, callback=None):
        """Search winget repository."""
        def _do_search():
            if not self._ensure_winget():
                return
            
            self.app.root.after(0, lambda: self.app.log(f"🔍 Searching winget for '{query}'..."))
            
            try:
                result = subprocess.run(
                    [self.winget_exe, "search", query,
                     "--source", "winget",
                     "--accept-source-agreements"],
                    capture_output=True, text=True, timeout=30,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                output = result.stdout or ""
                lines = output.strip().split('\n')
                
                # Parse results - find the header line with dashes
                results = []
                data_started = False
                
                for line in lines:
                    if '---' in line:
                        data_started = True
                        continue
                    if data_started and line.strip():
                        results.append(line.strip())
                
                if results:
                    self.app.root.after(0, lambda: self.app.log_success(f"Found {len(results)} results"))
                else:
                    self.app.root.after(0, lambda: self.app.log_warning(f"No results for '{query}'"))
                
                if callback:
                    self.app.root.after(0, lambda: callback(results))
                    
            except subprocess.TimeoutExpired:
                self.app.root.after(0, lambda: self.app.log_error(
                    "Search timed out",
                    hint="Try a more specific search term"
                ))
            except Exception as e:
                self.app.root.after(0, lambda: self.app.log_error(f"Search error: {str(e)}"))
        
        threading.Thread(target=_do_search, daemon=True).start()
    
    def install_apps(self, apps_list, progress_callback=None, complete_callback=None):
        """Install a list of apps via winget."""
        def _do_installs():
            total = len(apps_list)
            self.app.root.after(0, lambda: self.app.log(f"🚀 Starting {total} installs..."))
            
            if not self._ensure_winget():
                if complete_callback:
                    self.app.root.after(0, complete_callback)
                return
            
            for i, (name, winget_id) in enumerate(apps_list):
                self.app.root.after(0, lambda n=name: self.app.log(f"📥 Installing {n}..."))
                
                if progress_callback:
                    self.app.root.after(0, lambda idx=i, t=total: progress_callback(idx, t))
                
                success = self._do_install(name, winget_id)
                
                if not success:
                    self.app.root.after(0, lambda n=name: self.app.debug_log(f"Failed: {n}"))
            
            self.app.root.after(0, lambda: self.app.log("🎉 All installations complete!"))
            
            if complete_callback:
                self.app.root.after(0, complete_callback)
        
        threading.Thread(target=_do_installs, daemon=True).start()
    
    def _do_install(self, name, winget_id):
        """Install a single app. Returns True on success."""
        
        attempts = [
            {
                "label": "silent",
                "cmd": [
                    self.winget_exe, "install", "-e", "--id", winget_id,
                    "--source", "winget",
                    "--silent", "--accept-package-agreements", 
                    "--accept-source-agreements", "--disable-interactivity"
                ]
            },
            {
                "label": "interactive",
                "cmd": [
                    self.winget_exe, "install", "-e", "--id", winget_id,
                    "--source", "winget",
                    "--accept-package-agreements", "--accept-source-agreements"
                ]
            }
        ]
        
        for attempt in attempts:
            label = attempt["label"]
            cmd = attempt["cmd"]
            
            # Debug log the command
            self.app.root.after(0, lambda c=' '.join(cmd): self.app.debug_log(f"CMD: {c}"))
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True, text=True, timeout=300,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                output = (result.stdout or "") + (result.stderr or "")
                code = result.returncode
                
                # Debug log output
                self.app.root.after(0, lambda o=output, l=label: self.app.debug_log(
                    f"[{l}] OUTPUT:\n{o[-500:]}" if len(o) > 500 else f"[{l}] OUTPUT:\n{o}"
                ))
                
                # Success
                if code == 0:
                    self.app.root.after(0, lambda n=name: self.app.log_success(f"{n} installed"))
                    return True
                
                # Already installed
                if code == -1978335189:  # 0x8A150019
                    self.app.root.after(0, lambda n=name: self.app.log_success(f"{n} already installed"))
                    return True
                
                # Reboot required but installed
                if code == 3010:
                    self.app.root.after(0, lambda n=name: self.app.log_success(f"{n} installed (reboot needed)"))
                    return True
                
                # Upgrade available (already installed)
                if code == -1978335175:  # 0x8A150029
                    self.app.root.after(0, lambda n=name: self.app.log(f"⬆️ {n} - already installed, newer version available"))
                    return True
                
                # Not found in repo
                if code == -1978335212:  # 0x8A150004
                    self.app.root.after(0, lambda n=name, w=winget_id: self.app.log_error(
                        f"{n} - not found in repository",
                        hint=f"Verify winget ID: {w}"
                    ))
                    return False
                
                # No applicable installer
                if code == -1978335196:  # 0x8A150014
                    self.app.root.after(0, lambda n=name, w=winget_id: self.app.log_error(
                        f"{n} - no installer for this system",
                        hint=f"ID '{w}' may not support this OS/architecture"
                    ))
                    return False
                
                # Download failed
                if code == -1978335164:  # 0x8A150034
                    self.app.root.after(0, lambda n=name: self.app.log_error(
                        f"{n} - download failed",
                        hint="Check internet connection"
                    ))
                    return False
                
                # Source agreement / certificate error
                if code == -1978335138 or code == 2316632158:  # 0x8A15005E
                    if label == "silent":
                        self.app.root.after(0, lambda n=name: self.app.log_warning(
                            f"{n} - msstore certificate error on silent, retrying with --source winget..."
                        ))
                        continue
                    else:
                        self.app.root.after(0, lambda n=name: self.app.log_error(
                            f"{n} - certificate/source error",
                            hint="Try: winget source reset --force (as admin)"
                        ))
                        return False
                
                # Silent install failed with code 1 — retry interactive
                if label == "silent" and code == 1:
                    self.app.root.after(0, lambda n=name: self.app.log_warning(
                        f"{n} - silent failed (code 1), retrying interactive..."
                    ))
                    continue
                
                # Silent failed with other code — retry interactive
                if label == "silent":
                    self.app.root.after(0, lambda n=name, c=code: self.app.log_warning(
                        f"{n} - silent failed (code {c}), retrying interactive..."
                    ))
                    continue
                
                # Interactive also failed
                self.app.root.after(0, lambda n=name, c=code: self.app.log_error(
                    f"{n} failed (code {c})",
                    hint="Try installing with Chocolatey instead"
                ))
                return False
                
            except subprocess.TimeoutExpired:
                self.app.root.after(0, lambda n=name: self.app.log_error(
                    f"{n} timed out after 300s",
                    hint="Try installing manually or check internet speed"
                ))
                return False
            except Exception as e:
                self.app.root.after(0, lambda n=name, err=str(e): self.app.log_error(
                    f"{n} error: {err}"
                ))
                return False
        
        # All attempts exhausted
        self.app.root.after(0, lambda n=name: self.app.log_error(
            f"{n} - all install methods failed",
            hint="Try installing with Chocolatey instead"
        ))
        return False