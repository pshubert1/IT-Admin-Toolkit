import subprocess
import threading

class ChocoManager:
    def __init__(self, app):
        self.app = app
    
    def is_installed(self):
        try:
            result = subprocess.run(["choco", "--version"], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            return result.returncode == 0
        except:
            return False
    
    def get_version(self):
        try:
            result = subprocess.run(["choco", "--version"], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            return result.stdout.strip() if result.returncode == 0 else None
        except:
            return None
    
    def install_choco(self, callback=None):
        def run():
            self.app.log("Installing Chocolatey...")
            cmd = "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
            try:
                subprocess.run(["powershell", "-Command", cmd], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                self.app.log("Chocolatey installed!")
            except Exception as e:
                self.app.log(f"Error: {e}")
            if callback:
                self.app.root.after(0, callback)
        threading.Thread(target=run, daemon=True).start()
    
    def install_app(self, name, pkg, callback=None):
        def run():
            self.app.log(f"Installing {name}...")
            try:
                subprocess.run(["choco", "install", pkg, "-y"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                self.app.log(f"{name} installed!")
            except Exception as e:
                self.app.log(f"Error: {e}")
            if callback:
                self.app.root.after(0, callback)
        threading.Thread(target=run, daemon=True).start()
    
    def install_apps(self, apps_dict, btn, progress):
        selected = [(n, p) for n, (v, p) in apps_dict.items() if v.get()]
        if not selected:
            self.app.log("Select at least one app!")
            return
        def run():
            btn.config(state="disabled")
            progress.start()
            for name, pkg in selected:
                self.app.log(f"Installing {name}...")
                try:
                    subprocess.run(["choco", "install", pkg, "-y"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    self.app.log(f"{name} done!")
                except:
                    self.app.log(f"{name} failed!")
            self.app.log("Complete!")
            self.app.root.after(0, progress.stop)
            self.app.root.after(0, lambda: btn.config(state="normal"))
        threading.Thread(target=run, daemon=True).start()
    
    def search(self, query, listbox):
        if len(query) < 2:
            return
        def run():
            listbox.delete(0, "end")
            try:
                result = subprocess.run(["choco", "search", query, "--limit-output"], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                for line in result.stdout.strip().split("\n")[:15]:
                    if "|" in line:
                        listbox.insert("end", line.split("|")[0])
            except:
                pass
        threading.Thread(target=run, daemon=True).start()
