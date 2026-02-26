"""
PowerShell execution utilities.
"""

import subprocess
import sys
import threading
import os
import tempfile

class PowerShellRunner:
    def __init__(self, app):
        self.app = app
        self.ps_executable = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
        
        if not os.path.exists(self.ps_executable):
            self.ps_executable = "powershell"
    
    def run(self, script, name="Script", interactive=False):
        """Run a PowerShell script."""
        self.app.log(f"⚡ Running: {name}")
        
        if interactive:
            # Run in visible window for user interaction
            self._run_interactive(script, name)
        else:
            # Run in background thread
            thread = threading.Thread(target=self._execute, args=(script, name), daemon=True)
            thread.start()
    
    def _run_interactive(self, script, name):
        """Run script in a visible PowerShell window for user input."""
        try:
            # Create a temporary script file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False, encoding='utf-8') as f:
                # Add a pause at the end so user can see results
                full_script = script + '\n\nWrite-Host ""\nWrite-Host "Press any key to close..." -ForegroundColor Cyan\n$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")'
                f.write(full_script)
                temp_path = f.name
            
            # Run in visible window
            cmd = [
                self.ps_executable,
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-File", temp_path
            ]
            
            # Start process with visible window
            subprocess.Popen(
                cmd,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
            self.app.log(f"📺 Opened {name} in new window")
            
            # Clean up temp file after a delay (in background)
            def cleanup():
                import time
                time.sleep(60)  # Wait 60 seconds before cleanup
                try:
                    os.remove(temp_path)
                except:
                    pass
            
            threading.Thread(target=cleanup, daemon=True).start()
            
        except Exception as e:
            self.app.log(f"💥 Error: {str(e)}")
    
    def _execute(self, script, name):
        """Execute PowerShell script in background and capture output."""
        scripts_tab = self.app.scripts_tab
        scripts_tab.script_progress.start()
        
        self.app.root.after(0, lambda: scripts_tab.script_output.delete('1.0', 'end'))
        self.app.root.after(0, lambda: scripts_tab.script_output.insert('end', f">>> Running: {name}\n{'='*50}\n\n"))
        
        try:
            cmd = [
                self.ps_executable, 
                "-NoProfile", 
                "-ExecutionPolicy", "Bypass", 
                "-Command", script
            ]
            
            if self.app.debug_mode.get():
                self.app.debug_log(f"CMD: {self.ps_executable} -Command \"{script[:100]}...\"")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            for line in process.stdout:
                self.app.root.after(0, lambda l=line: self._append_output(l))
                
                stripped = line.strip()
                if stripped and self.app.log_script_output.get():
                    self.app.root.after(0, lambda l=stripped: self.app.log(f"📤 {l}"))
                
                if self.app.debug_mode.get():
                    self.app.debug_log(f"  {line.strip()}")
            
            process.wait(timeout=600)
            exit_code = process.returncode
            
            self.app.root.after(0, lambda: self._append_output(f"\n{'='*50}\n✅ Completed (exit code: {exit_code})"))
            self.app.root.after(0, lambda: self.app.log(f"✅ {name} completed (exit code: {exit_code})"))
            
        except subprocess.TimeoutExpired:
            self.app.root.after(0, lambda: self._append_output("\n⏰ TIMEOUT: Script took too long"))
            self.app.root.after(0, lambda: self.app.log(f"⏰ {name} timed out"))
        except Exception as e:
            self.app.root.after(0, lambda: self._append_output(f"\n💥 ERROR: {str(e)}"))
            self.app.root.after(0, lambda: self.app.log(f"💥 {name} error: {str(e)}"))
        finally:
            self.app.root.after(0, scripts_tab.script_progress.stop)
    
    def _append_output(self, text):
        self.app.scripts_tab.script_output.insert('end', text)
        self.app.scripts_tab.script_output.see('end')