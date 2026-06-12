#!/usr/bin/env python3
"""
IT Admin Toolkit - Main Entry Point
Run this file to start the application.
"""
import ctypes
import sys
import tkinter as tk
from app import AppInstaller
import sys
import os

# Set Windows taskbar icon identity (must be before Tk root)
if sys.platform == 'win32':
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('PShubert.ITAdminToolkit.1')

def main():
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            'ITAdminToolkit.App.1'
        )
    except Exception:
        pass
    
    root = tk.Tk()
    app = AppInstaller(root)
    root.mainloop()


if __name__ == "__main__":
    main()