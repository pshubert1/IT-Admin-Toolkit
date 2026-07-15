"""
Collapsible Frame widget for the IT Admin Toolkit.
Click the header to toggle collapse/expand.
"""

import tkinter as tk
from tkinter import ttk


class CollapsibleFrame(ttk.Frame):
    """A frame with a clickable header that collapses/expands its content."""

    def __init__(self, parent, title="", collapsed=False, style_colors=None, **kwargs):
        super().__init__(parent, style='DarkBg.TFrame', **kwargs)

        self._is_collapsed = collapsed
        self._colors = style_colors or {
            'bg': '#1e1e2e',
            'fg': '#cdd6f4',
            'frame_bg': '#313244',
            'accent': '#0d8bd9',
        }

        # === Header bar (clickable) ===
        self.header = tk.Frame(self, bg=self._colors['frame_bg'], cursor='hand2')
        self.header.pack(fill=tk.X)

        # Arrow indicator
        self._arrow_var = tk.StringVar(value="▼ " if not collapsed else "▶ ")
        self.arrow_label = tk.Label(
            self.header, textvariable=self._arrow_var,
            bg=self._colors['frame_bg'], fg=self._colors['accent'],
            font=('Segoe UI', 10, 'bold'), padx=5
        )
        self.arrow_label.pack(side=tk.LEFT)

        # Title text
        self.title_label = tk.Label(
            self.header, text=title,
            bg=self._colors['frame_bg'], fg=self._colors['fg'],
            font=('Segoe UI', 10, 'bold'), anchor='w'
        )
        self.title_label.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=4)

        # Bind click on all header widgets
        for w in (self.header, self.arrow_label, self.title_label):
            w.bind("<Button-1>", self._toggle)

        # === Content frame ===
        self.content = ttk.Frame(self, style='Dark.TFrame', padding="10")
        if not collapsed:
            self.content.pack(fill=tk.BOTH, expand=True)

    def _toggle(self, event=None):
        if self._is_collapsed:
            self.expand()
        else:
            self.collapse()

    def collapse(self):
        self.content.pack_forget()
        self._is_collapsed = True
        self._arrow_var.set("▶ ")

    def expand(self):
        self.content.pack(fill=tk.BOTH, expand=True)
        self._is_collapsed = False
        self._arrow_var.set("▼ ")

    @property
    def is_collapsed(self):
        return self._is_collapsed