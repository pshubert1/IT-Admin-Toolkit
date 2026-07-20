"""
=== INTEGRATION GUIDE ===
How to add the new tabs to your IT Admin Toolkit

Place all new .py files in your ui/ folder:
  ui/bsod_tab.py
  ui/health_dashboard_tab.py
  ui/eventlog_tab.py
  ui/setup_checklist_tab.py
  ui/bloatware_tab.py
  ui/printer_tab.py
  ui/bitlocker_tab.py
"""

# ============================================================
# In your app.py, add these imports at the top:
# ============================================================

from ui.health_dashboard_tab import HealthDashboardTab
from ui.bsod_tab import BSODTab
from ui.eventlog_tab import EventLogTab
from ui.setup_checklist_tab import SetupChecklistTab
from ui.bloatware_tab import BloatwareTab
from ui.printer_tab import PrinterTab
from ui.bitlocker_tab import BitLockerTab


# ============================================================
# In your app.py, where you create tabs (likely in create_tabs
# or similar method), add these new tabs:
# ============================================================

def create_tabs(self):
    """Create all application tabs."""
    
    # Your existing tabs...
    # self.scripts_tab_frame = ttk.Frame(self.notebook, style='DarkBg.TFrame')
    # self.winget_tab_frame = ttk.Frame(self.notebook, style='DarkBg.TFrame')
    # etc.
    
    # === NEW TABS ===
    
    # Health Dashboard (make this the FIRST tab - shows overview on open)
    self.health_tab_frame = ttk.Frame(self.notebook, style='DarkBg.TFrame')
    self.notebook.insert(0, self.health_tab_frame, text="  📊 Dashboard  ")
    self.health_tab = HealthDashboardTab(self.health_tab_frame, self)
    
    # Setup Checklist
    self.setup_tab_frame = ttk.Frame(self.notebook, style='DarkBg.TFrame')
    self.notebook.add(self.setup_tab_frame, text="  📋 Setup  ")
    self.setup_tab = SetupChecklistTab(self.setup_tab_frame, self)
    
    # Bloatware Remover
    self.bloatware_tab_frame = ttk.Frame(self.notebook, style='DarkBg.TFrame')
    self.notebook.add(self.bloatware_tab_frame, text="  🗑️ Bloatware  ")
    self.bloatware_tab = BloatwareTab(self.bloatware_tab_frame, self)
    
    # Printer Manager
    self.printer_tab_frame = ttk.Frame(self.notebook, style='DarkBg.TFrame')
    self.notebook.add(self.printer_tab_frame, text="  🖨️ Printers  ")
    self.printer_tab = PrinterTab(self.printer_tab_frame, self)
    
    # Event Log Summary
    self.eventlog_tab_frame = ttk.Frame(self.notebook, style='DarkBg.TFrame')
    self.notebook.add(self.eventlog_tab_frame, text="  📜 Events  ")
    self.eventlog_tab = EventLogTab(self.eventlog_tab_frame, self)
    
    # BSOD Analyzer
    self.bsod_tab_frame = ttk.Frame(self.notebook, style='DarkBg.TFrame')
    self.notebook.add(self.bsod_tab_frame, text="  💀 Crashes  ")
    self.bsod_tab = BSODTab(self.bsod_tab_frame, self)
    
    # BitLocker Manager
    self.bitlocker_tab_frame = ttk.Frame(self.notebook, style='DarkBg.TFrame')
    self.notebook.add(self.bitlocker_tab_frame, text="  🔐 BitLocker  ")
    self.bitlocker_tab = BitLockerTab(self.bitlocker_tab_frame, self)


# ============================================================
# SUGGESTED TAB ORDER (after adding all new tabs):
# ============================================================
#
#  1. 📊 Dashboard        (health_dashboard_tab.py) - System overview at a glance
#  2. 📋 Setup            (setup_checklist_tab.py)  - New PC setup wizard
#  3. 🖥️ Scripts          (scripts_tab.py)          - EXISTING
#  4. 📦 Winget           (winget_tab.py)           - EXISTING
#  5. 🍫 Chocolatey       (choco_tab.py)            - EXISTING
#  6. 🗑️ Bloatware        (bloatware_tab.py)        - Remove crapware
#  7. 🖨️ Printers         (printer_tab.py)          - Printer management
#  8. 🔄 Updates          (updates_tab.py)          - EXISTING
#  9. 📜 Events           (eventlog_tab.py)         - Event log summary
# 10. 💀 Crashes          (bsod_tab.py)             - BSOD/crash analyzer
# 11. 🔐 BitLocker        (bitlocker_tab.py)        - Encryption management
# 12. 📝 Logs             (logs_tab.py)             - EXISTING
#
# ============================================================


# ============================================================
# UPDATE YOUR __init__.py in ui/ folder:
# ============================================================
#
# Add these lines:
#
# from ui.bsod_tab import BSODTab
# from ui.health_dashboard_tab import HealthDashboardTab
# from ui.eventlog_tab import EventLogTab
# from ui.setup_checklist_tab import SetupChecklistTab
# from ui.bloatware_tab import BloatwareTab
# from ui.printer_tab import PrinterTab
# from ui.bitlocker_tab import BitLockerTab


# ============================================================
# UPDATE Build-Release.ps1 hidden imports:
# ============================================================
#
# Add these to your --hidden-import list:
#
#     "--hidden-import", "ui.bsod_tab"
#     "--hidden-import", "ui.health_dashboard_tab"
#     "--hidden-import", "ui.eventlog_tab"
#     "--hidden-import", "ui.setup_checklist_tab"
#     "--hidden-import", "ui.bloatware_tab"
#     "--hidden-import", "ui.printer_tab"
#     "--hidden-import", "ui.bitlocker_tab"


# ============================================================
# DEPENDENCIES: None beyond what you already have!
# ============================================================
#
# All 7 new tabs use only:
#   - tkinter (included with Python)
#   - subprocess (stdlib)
#   - threading (stdlib)
#   - os, struct, platform, datetime (stdlib)
#   - urllib.request (stdlib) - for external IP check
#
# No new pip packages needed!
#
# The only requirement is that ui/collapsible_frame.py exists
# (health_dashboard_tab.py and setup_checklist_tab.py use it
# for their collapsible sections).
