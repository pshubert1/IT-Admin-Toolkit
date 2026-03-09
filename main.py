#!/usr/bin/env python3
"""
IT Admin Toolkit - Main Entry Point
Run this file to start the application.
"""

import tkinter as tk
from app import AppInstaller
import sys
import os

# Set Windows taskbar icon identity (must be before Tk root)
if sys.platform == 'win32':
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('PShubert.ITAdminToolkit.1')

def main():
    root = tk.Tk()
    app = AppInstaller(root)
    root.mainloop()


if __name__ == "__main__":
    main()