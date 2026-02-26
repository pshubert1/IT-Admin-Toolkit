"""
TTK Style configuration for the application.
"""

from tkinter import ttk

def setup_styles(colors):
    """Configure all TTK styles for the application."""
    style = ttk.Style()
    style.theme_use('clam')
    
    # Frame styles
    style.configure('Dark.TFrame', background=colors['frame_bg'])
    style.configure('DarkBg.TFrame', background=colors['bg'])
    
    # Label styles
    style.configure('Dark.TLabel', background=colors['bg'], foreground=colors['fg'])
    style.configure('DarkFrame.TLabel', background=colors['frame_bg'], foreground=colors['fg'])
    
    # Checkbutton styles
    style.configure('Dark.TCheckbutton', background=colors['bg'], foreground=colors['fg'])
    style.configure('DarkFrame.TCheckbutton', background=colors['frame_bg'], foreground=colors['fg'])
    
    # Button styles
    style.configure('Dark.TButton', background=colors['accent'], foreground='white')
    style.map('Dark.TButton', background=[('active', '#1177bb')])
    
    style.configure('Success.TButton', background=colors['success'], foreground='white')
    style.map('Success.TButton', background=[('active', '#3da63a')])
    
    style.configure('Warning.TButton', background=colors['warning'], foreground='black')
    style.map('Warning.TButton', background=[('active', '#d9973d')])
    
    style.configure('Danger.TButton', background=colors['error'], foreground='white')
    style.map('Danger.TButton', background=[('active', '#c7352b')])
    
    # Title style
    style.configure('Dark.Title.TLabel', font=('Segoe UI', 18, 'bold'), 
                   foreground=colors['accent'], background=colors['bg'])
    
    # Labelframe styles
    style.configure('Dark.TLabelframe', background=colors['frame_bg'])
    style.configure('Dark.TLabelframe.Label', background=colors['frame_bg'], 
                   foreground=colors['fg'])
    
    # Notebook (tab) styles
    style.configure('Dark.TNotebook', background=colors['bg'])
    style.configure('Dark.TNotebook.Tab', background=colors['frame_bg'], 
                   foreground=colors['fg'], padding=[15, 8])
    style.map('Dark.TNotebook.Tab', 
             background=[('selected', colors['accent'])],
             foreground=[('selected', 'white')])
    
    return style