#!/usr/bin/env python3
"""
IT Admin Toolkit - Main Entry Point
Run this file to start the application.
"""

import tkinter as tk
from app import AppInstaller

def enable_mousewheel_scroll(canvas, inner_frame):
    """Enable mouse wheel scrolling for a canvas and all widgets inside it."""
    
    def on_scroll(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def on_scroll_linux_up(event):
        canvas.yview_scroll(-1, "units")
    
    def on_scroll_linux_down(event):
        canvas.yview_scroll(1, "units")
    
    def bind_wheel(widget):
        widget.bind("<MouseWheel>", on_scroll)           # Windows/Mac
        widget.bind("<Button-4>", on_scroll_linux_up)    # Linux scroll up
        widget.bind("<Button-5>", on_scroll_linux_down)  # Linux scroll down
        for child in widget.winfo_children():
            bind_wheel(child)
    
    bind_wheel(canvas)
    bind_wheel(inner_frame)

def main():
    root = tk.Tk()
    app = AppInstaller(root)
    root.mainloop()

if __name__ == "__main__":
    main()