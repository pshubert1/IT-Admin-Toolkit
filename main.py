#!/usr/bin/env python3
"""
IT Admin Toolkit - Main Entry Point
Run this file to start the application.
"""

import tkinter as tk
from app import AppInstaller


def main():
    root = tk.Tk()
    app = AppInstaller(root)
    root.mainloop()


if __name__ == "__main__":
    main()