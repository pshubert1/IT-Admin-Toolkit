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
    """Relaunch the current script/exe with admin privileges."""
    if executable is None:
        executable = sys.executable
        if parameters is None:
            parameters = ' '.join(sys.argv)
    
    if parameters is None:
        parameters = ''
    
    try:
        ret = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", executable, parameters, None, 1
        )
        return ret > 32
    except Exception:
        return False


def restart_as_admin():
    """Restart the current application with admin privileges and exit."""
    if is_admin():
        return False
    
    if getattr(sys, 'frozen', False):
        executable = sys.executable
        parameters = ''
    else:
        executable = sys.executable
        parameters = '"' + '" "'.join(sys.argv) + '"'
    
    if run_as_admin(executable, parameters):
        sys.exit(0)
        return True
    
    return False