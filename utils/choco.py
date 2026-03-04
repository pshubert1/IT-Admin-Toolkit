"""
Chocolatey operations utility.
"""

import subprocess
import threading
import os


class ChocoManager:
    def __init__(self, app):
        self.app = app
        self.choco_exe = self._find_choco()
    
    def _find_choco(self):
        """Find choco.exe path."""
        default_path = r"C:\ProgramData\chocolatey\bin\choco.exe"
        if os.path.exists(default_path):
            return default_path
        
        import shutil
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
                subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-Command", cmd],
                              capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                self.choco_exe = self._find_choco()
                self.app.log_success("Chocolatey installed")
            except Exception as e:
                self.app.log_error(f"Chocolatey install failed: {e}",
                    hint="Run the app as Administrator and try again")
            if callback:
                self.app.root.after(0, callback)
        threading.Thread(target=run, daemon=True).start()
    
    def install_app(self, name, pkg, callback=None):
        def run():
            self.app.log(f"📥 Installing {name}...")
            try:
                self._run_choco(["install", pkg, "-y"], capture_output=True,
                               creationflags=subprocess.CREATE_NO_WINDOW)
                self.app.log_success(f"{name} installed")
            except FileNotFoundError:
                self.app.log_error(f"Cannot install {name}",
                    hint="Chocolatey not installed. Click 'INSTALL CHOCO' first")
            except Exception as e:
                self.app.log_error(f"{name} install failed: {e}")
            if callback:
                self.app.root.after(0, callback)
        threading.Thread(target=run, daemon=True).start()
    
    def install_apps(self, apps_dict, btn, progress):
        selected = [(n, p) for n, (v, p) in apps_dict.items() if v.get()]
        if not selected:
            self.app.log_warning("Select at least one app")
            return
        
        def run():
            btn.config(state="disabled")
            progress.start()
            for name, pkg in selected:
                self.app.log(f"📥 Installing {name}...")
                try:
                    self._run_choco(["install", pkg, "-y"], capture_output=True,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
                    self.app.log_success(f"{name} installed")
                except FileNotFoundError:
                    self.app.log_error("Chocolatey not installed",
                        hint="Click 'INSTALL CHOCO' first")
                    break
                except Exception as e:
                    self.app.log_error(f"{name} failed: {e}")
            self.app.log("🎉 All installations complete!")
            self.app.root.after(0, progress.stop)
            self.app.root.after(0, lambda: btn.config(state="normal"))
        threading.Thread(target=run, daemon=True).start()
    
    def search(self, query, listbox):
        if len(query) < 2:
            return
        
        def run():
            listbox.delete(0, "end")
            try:
                result = self._run_choco(["search", query, "--limit-output"],
                                        capture_output=True, text=True,
                                        creationflags=subprocess.CREATE_NO_WINDOW)
                for line in result.stdout.strip().split("\n")[:15]:
                    if "|" in line:
                        listbox.insert("end", line.split("|")[0])
            except FileNotFoundError:
                self.app.log_error("Chocolatey not installed",
                    hint="Click 'INSTALL CHOCO' first")
            except:
                pass
        threading.Thread(target=run, daemon=True).start()