"""
Admin privilege utilities.
"""

import ctypes
import sys
import os


def is_admin():
    """Check if the current process has admin privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False


def run_as_admin(executable=None, parameters=None):
    """
    Relaunch the current script/exe with admin privileges.
    
    Returns True if relaunch was initiated, False if failed or cancelled.
    """
    if executable is None:
        executable = sys.executable
        
        # If running as PyInstaller exe, use the exe path
        if getattr(sys, 'frozen', False):
            executable = sys.executable
        else:
            # Running as script, need to run python with the script
            executable = sys.executable
            if parameters is None:
                parameters = ' '.join(sys.argv)
    
    if parameters is None:
        parameters = ''
    
    try:
        # ShellExecute with 'runas' verb to request elevation
        ret = ctypes.windll.shell32.ShellExecuteW(
            None,           # hwnd
            "runas",        # operation - 'runas' triggers UAC
            executable,     # file
            parameters,     # parameters
            None,           # directory
            1               # show command (SW_SHOWNORMAL)
        )
        
        # ShellExecute returns > 32 on success
        return ret > 32
        
    except Exception as e:
        print(f"Failed to elevate: {e}")
        return False


def restart_as_admin():
    """Restart the current application with admin privileges and exit."""
    if is_admin():
        return False  # Already admin
    
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        executable = sys.executable
        parameters = ''
    else:
        # Running as script
        executable = sys.executable
        parameters = '"' + '" "'.join(sys.argv) + '"'
    
    if run_as_admin(executable, parameters):
        sys.exit(0)  # Exit current instance
        return True
    
    return False