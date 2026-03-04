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
            self._run_interactive(script, name)
        else:
            thread = threading.Thread(target=self._execute, args=(script, name), daemon=True)
            thread.start()
    
    def _run_interactive(self, script, name):
        """Run script in a visible PowerShell window for user input."""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False, encoding='utf-8') as f:
                full_script = (
                    'try {\n'
                    f'{script}\n'
                    '} catch {\n'
                    '    Write-Host ""\n'
                    '    Write-Host "ERROR: $_" -ForegroundColor Red\n'
                    '    Write-Host $_.ScriptStackTrace -ForegroundColor Gray\n'
                    '} finally {\n'
                    '    Write-Host ""\n'
                    '    Write-Host "Press any key to close..." -ForegroundColor Cyan\n'
                    '    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")\n'
                    '}\n'
                )
                f.write(full_script)
                temp_path = f.name
            
            cmd = [
                self.ps_executable,
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-File", temp_path
            ]
            
            subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
            self.app.log_success(f"Opened {name} in new window")
            
            def cleanup():
                import time
                time.sleep(120)
                try:
                    os.remove(temp_path)
                except:
                    pass
            
            threading.Thread(target=cleanup, daemon=True).start()
            
        except FileNotFoundError:
            self.app.log_error(f"PowerShell not found",
                hint="Verify PowerShell is installed at C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\")
        except PermissionError:
            self.app.log_error(f"Permission denied launching {name}",
                hint="Try running the app as Administrator")
        except Exception as e:
            self.app.log_error(f"Failed to launch {name}: {str(e)}")
    
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
            
            if exit_code == 0:
                self.app.root.after(0, lambda: self._append_output(f"\n{'='*50}\n✅ Completed successfully"))
                self.app.root.after(0, lambda: self.app.log_success(f"{name} completed"))
            else:
                self.app.root.after(0, lambda: self._append_output(f"\n{'='*50}\n⚠️ Completed with exit code: {exit_code}"))
                self.app.root.after(0, lambda: self.app.log_warning(f"{name} completed with exit code: {exit_code}",
                    hint="Check script output for details"))
            
        except subprocess.TimeoutExpired:
            self.app.root.after(0, lambda: self._append_output("\n⏰ TIMEOUT: Script took too long"))
            self.app.root.after(0, lambda: self.app.log_error(f"{name} timed out after 600s",
                hint="The script may still be running in the background"))
        except FileNotFoundError:
            self.app.root.after(0, lambda: self.app.log_error("PowerShell not found",
                hint="Verify PowerShell is installed"))
        except Exception as e:
            self.app.root.after(0, lambda: self._append_output(f"\n💥 ERROR: {str(e)}"))
            self.app.root.after(0, lambda: self.app.log_error(f"{name} error: {str(e)}"))
        finally:
            self.app.root.after(0, scripts_tab.script_progress.stop)
    
    def _append_output(self, text):
        self.app.scripts_tab.script_output.insert('end', text)
        self.app.scripts_tab.script_output.see('end')