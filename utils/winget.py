"""
Winget operations utilities.
"""

import subprocess
import threading

class WingetManager:
    def __init__(self, app):
        """
        Initialize the Winget manager.
        
        Args:
            app: Reference to main AppInstaller instance
        """
        self.app = app
    
    def check(self):
        """Check if winget is available."""
        try:
            result = subprocess.run(["winget", "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.app.log(f"✅ winget {result.stdout.strip()}")
            else:
                self.app.log("❌ winget not responding")
        except Exception:
            self.app.log("❌ winget not found")
    
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
            self.app.log(f"🔍 Searching winget for '{query}'...")
            result = subprocess.run(["winget", "search", query], 
                                  capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                data_lines = []
                for i, line in enumerate(lines):
                    if '---' in line:
                        data_lines = lines[i+1:]
                        break
                self.app.root.after(0, self._populate_results, data_lines)
            else:
                self.app.root.after(0, self.app.log, "❌ Search failed")
        except Exception as e:
            self.app.root.after(0, self.app.log, f"💥 Search error: {str(e)}")
    
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
        install_btn.config(state='disabled')
        progress.start()
        self.app.log(f"🚀 Starting {len(selected)} installs...")
        
        for app_name in selected:
            _, winget_id = checkboxes[app_name]
            self.app.log(f"📥 Installing {app_name}...")
            
            cmd = ["winget", "install", "-e", "--id", winget_id, "--silent",
                  "--accept-package-agreements", "--accept-source-agreements"]
            
            self.app.debug_log(f"CMD: {' '.join(cmd)}")
            
            try:
                if self.app.debug_mode.get():
                    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                             universal_newlines=True, bufsize=1)
                    for line in process.stdout:
                        self.app.debug_log(f"  {line.strip()}")
                    process.wait(timeout=300)
                    exit_code = process.returncode
                else:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                    exit_code = result.returncode
                
                if exit_code in [0, 3010]:
                    self.app.log(f"✅ {app_name} OK")
                else:
                    self.app.log(f"❌ {app_name} failed (code {exit_code})")
                    
            except subprocess.TimeoutExpired:
                self.app.log(f"⏰ {app_name} timeout")
            except Exception as e:
                self.app.log(f"💥 {app_name} error")
                self.app.debug_log(f"ERROR: {str(e)}")
        
        self.app.log("🎉 All installations complete!")
        progress.stop()
        install_btn.config(state='normal')