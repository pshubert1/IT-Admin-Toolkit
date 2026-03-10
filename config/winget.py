"""
╔══════════════════════════════════════════════════════════════════╗
║                    WINGET APPLICATION LIST                       ║
║                                                                  ║
║  Edit this file to add/remove applications from the installer.  ║
║                                                                  ║
║  Format: ("Display Name", "Winget.Package.ID")                  ║
╚══════════════════════════════════════════════════════════════════╝
"""

# ============================================================
#  LEFT COLUMN APPS
# ============================================================

CORE_PRODUCTIVITY = [
    ("Microsoft 365", "Microsoft.Office"),
    ("Teams", "Microsoft.Teams"),
]

BROWSERS = [
    ("Chrome", "Google.Chrome"),
    ("Edge", "Microsoft.Edge"),
    ("FireFox", "Mozilla.Firefox.ESR"),
    ("Brave", "Brave.Brave"),
   
]

MSP_ADMIN = [
    ("Windows Terminal", "Microsoft.WindowsTerminal"),
    ("PowerShell 7", "Microsoft.PowerShell"),
    ("PowerToys", "Microsoft.PowerToys"),
    ("Everything", "voidtools.Everything"),
    # ("Remote Desktop Manager", "Devolutions.RemoteDesktopManager"),
]

# ============================================================
#  RIGHT COLUMN APPS
# ============================================================

UTILITIES = [
    ("7-Zip", "7zip.7zip"),
    ("Advanced IP Scanner", "Famatech.AdvancedIPScanner"),
    ("TreeSize Free", "JAMSoftware.TreeSize.Free"),
    ("VLC", "VideoLAN.VLC"),
    ("Notepad++", "Notepad++.Notepad++"),
    ("WinSCP", "WinSCP.WinSCP"),
]

TROUBLESHOOTING = [
    ('Wireshark', 'WiresharkFoundation.Wireshark'),
    ("Sysinternals Suite", "Microsoft.SysinternalsSuite"),
    ("Process Explorer", "Microsoft.SysinternalsProcessExplorer"),
    ("HWiNFO", "REALiX.HWiNFO"),
    ("CPU-Z", "CPUID.CPU-Z"),
]

BUSINESS = [
    ("Adobe Reader", "Adobe.Acrobat.Reader.64-bit"),
    ("Zoom", "Zoom.Zoom"),
    ("Slack", "Slack.Slack"),
    ("Webex", "Cisco.Webex"),
    ("Microsoft Copilot", "Microsoft.Copilot"),  # Standalone Copilot app
]

EXTRAS = [
    ("ShareX", "ShareX.ShareX"),
    ("Obsidian", "Obsidian.Obsidian"),
    # ("VS Code", "Microsoft.VisualStudioCode"),
    # ("Git", "Git.Git"),
]


# ============================================================
#  DO NOT EDIT BELOW - This combines everything for the app
# ============================================================

def get_app_sections():
    """
    Returns the complete app sections configuration.
    The third item ('left' or 'right') determines which column.
    """
    return [
        ("🔴 CORE PRODUCTIVITY", CORE_PRODUCTIVITY, "left"),
        ("🟡 BROWSERS", BROWSERS, "left"),
        ("🔧 MSP/ADMIN", MSP_ADMIN, "left"),
        ("⚙️ UTILITIES", UTILITIES, "right"),
        ("🛠️ TROUBLESHOOTING", TROUBLESHOOTING, "right"),
        ("🏢 BUSINESS", BUSINESS, "right"),
        ("✨ EXTRAS", EXTRAS, "right"),
    ]