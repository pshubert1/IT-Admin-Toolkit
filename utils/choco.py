"""
Chocolatey operations utility.
"""

import subprocess
import threading
import os
import shutil


class ChocoManager:
    def __init__(self, app):
        self.app = app
        self.choco_exe = self._find_choco()
    
    def _find_choco(self):
        """Find choco.exe path."""
        default_path = r"C:\ProgramData\chocolatey\bin\choco.exe"
        if os.path.exists(default_path):
            return default_path
        
        found = shutil.which("choco")
        if found:
            return found
        
        return None
    
    def _run_choco(self, args, **kwargs):
        """Run a choco command with the correct path."""
        if not self.choco_exe:
            self.choco_exe = self._find_choco()
        if not self.choco_exe:
            raise FileNotFoundError("Chocolatey not installed")
        return subprocess.run([self.choco_exe] + args, **kwargs)
    
    def is_installed(self):
        try:
            result = self._run_choco(["--version"], capture_output=True, text=True,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
            return result.returncode == 0
        except:
            return False
    
    def get_version(self):
        try:
            result = self._run_choco(["--version"], capture_output=True, text=True,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
            return result.stdout.strip() if result.returncode == 0 else None
        except:
            return None
    
    def install_choco(self, callback=None):
        def run():
            self.app.log("📥 Installing Chocolatey...")
            cmd = ("Set-ExecutionPolicy Bypass -Scope Process -Force; "
                   "[System.Net.ServicePointManager]::SecurityProtocol = "
                   "[System.Net.ServicePointManager]::SecurityProtocol -bor 3072; "
                   "iex ((New-Object System.Net.WebClient).DownloadString("
                   "'https://community.chocolatey.org/install.ps1'))")
            try:
                result = subprocess.run(
                    ["powershell", "-ExecutionPolicy", "Bypass", "-Command", cmd],
                    capture_output=True, text=True, timeout=120,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                self.choco_exe = self._find_choco()
                if self.choco_exe:
                    self.app.root.after(0, lambda: self.app.log_success("Chocolatey installed"))
                else:
                    self.app.root.after(0, lambda: self.app.log_error(
                        "Chocolatey install may have failed",
                        hint="Restart the app and try again"
                    ))
            except Exception as e:
                self.app.root.after(0, lambda: self.app.log_error(
                    f"Chocolatey install failed: {e}",
                    hint="Run the app as Administrator and try again"
                ))
            if callback:
                self.app.root.after(0, callback)
        threading.Thread(target=run, daemon=True).start()
    
    def install_app(self, name, pkg, callback=None):
        def run():
            self.app.root.after(0, lambda: self.app.log(f"📥 Installing {name}..."))
            try:
                result = self._run_choco(
                    ["install", pkg, "-y", "--no-progress"],
                    capture_output=True, text=True, timeout=300,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                output = (result.stdout or "") + (result.stderr or "")
                
                # Debug log full output
                self.app.root.after(0, lambda o=output: self.app.debug_log(f"[choco] {o[-500:]}"))
                
                if result.returncode == 0:
                    self.app.root.after(0, lambda: self.app.log_success(f"{name} installed"))
                elif "already installed" in output.lower():
                    self.app.root.after(0, lambda: self.app.log_success(f"{name} already installed"))
                else:
                    # Extract just the error line, not the entire output
                    error_line = ""
                    for line in output.split('\n'):
                        if 'error' in line.lower() or 'fail' in line.lower():
                            error_line = line.strip()[:100]
                            break
                    
                    hint = error_line if error_line else "Check debug log for details"
                    self.app.root.after(0, lambda: self.app.log_error(
                        f"{name} install failed",
                        hint=hint
                    ))
                    
            except FileNotFoundError:
                self.app.root.after(0, lambda: self.app.log_error(
                    "Chocolatey not installed",
                    hint="Click 'INSTALL CHOCO' first"
                ))
            except subprocess.TimeoutExpired:
                self.app.root.after(0, lambda: self.app.log_error(
                    f"{name} timed out after 300s",
                    hint="Try installing manually: choco install " + pkg
                ))
            except Exception as e:
                self.app.root.after(0, lambda: self.app.log_error(f"{name} failed: {e}"))
            
            if callback:
                self.app.root.after(0, callback)
        threading.Thread(target=run, daemon=True).start()
    
    def install_apps(self, apps_dict, btn, progress):
        selected = [(n, p) for n, (v, p) in apps_dict.items() if v.get()]
        if not selected:
            self.app.log_warning("Select at least one app")
            return
        
        def run():
            self.app.root.after(0, lambda: btn.config(state="disabled"))
            self.app.root.after(0, lambda: progress.start())
            self.app.root.after(0, lambda: self.app.log(f"🚀 Installing {len(selected)} packages..."))
            
            for name, pkg in selected:
                self.app.root.after(0, lambda n=name: self.app.log(f"📥 Installing {n}..."))
                try:
                    result = self._run_choco(
                        ["install", pkg, "-y", "--no-progress"],
                        capture_output=True, text=True, timeout=300,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    
                    output = (result.stdout or "") + (result.stderr or "")
                    self.app.root.after(0, lambda o=output: self.app.debug_log(f"[choco] {o[-500:]}"))
                    
                    if result.returncode == 0 or "already installed" in output.lower():
                        self.app.root.after(0, lambda n=name: self.app.log_success(f"{n} installed"))
                    else:
                        error_line = ""
                        for line in output.split('\n'):
                            if 'error' in line.lower() or 'fail' in line.lower():
                                error_line = line.strip()[:100]
                                break
                        hint = error_line if error_line else "Check debug log for details"
                        self.app.root.after(0, lambda n=name, h=hint: self.app.log_error(
                            f"{n} install failed", hint=h
                        ))
                        
                except FileNotFoundError:
                    self.app.root.after(0, lambda: self.app.log_error(
                        "Chocolatey not installed",
                        hint="Click 'INSTALL CHOCO' first"
                    ))
                    break
                except subprocess.TimeoutExpired:
                    self.app.root.after(0, lambda n=name: self.app.log_error(f"{n} timed out"))
                except Exception as e:
                    self.app.root.after(0, lambda n=name, err=str(e): self.app.log_error(f"{n} failed: {err}"))
            
            self.app.root.after(0, lambda: self.app.log("🎉 All installations complete!"))
            self.app.root.after(0, lambda: progress.stop())
            self.app.root.after(0, lambda: btn.config(state="normal"))
        
        threading.Thread(target=run, daemon=True).start()
    
    def search(self, query, listbox):
        if len(query) < 2:
            return
        
        def run():
            self.app.root.after(0, lambda: listbox.delete(0, "end"))
            try:
                result = self._run_choco(
                    ["search", query, "--limit-output"],
                    capture_output=True, text=True, timeout=30,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                for line in result.stdout.strip().split("\n")[:15]:
                    if "|" in line:
                        pkg_name = line.split("|")[0]
                        self.app.root.after(0, lambda p=pkg_name: listbox.insert("end", p))
            except FileNotFoundError:
                self.app.root.after(0, lambda: self.app.log_error(
                    "Chocolatey not installed",
                    hint="Click 'INSTALL CHOCO' first"
                ))
            except:
                pass
        threading.Thread(target=run, daemon=True).start()