"""
╔══════════════════════════════════════════════════════════════════╗
║                    POWERSHELL SCRIPTS                            ║
║                                                                  ║
║  This file contains built-in scripts.                           ║
║  You can also add .ps1 files to the 'scripts' folder!           ║
╚══════════════════════════════════════════════════════════════════╝
"""

from config.script_loader import get_all_script_sections

# ============================================================
#  🔧 BUILT-IN SYSTEM INFO SCRIPTS
# ============================================================

SYSTEM_INFO_SCRIPTS = [
    (
        "📊 System Information",
        "Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion, OsHardwareAbstractionLayer, CsName, CsProcessors, CsTotalPhysicalMemory | Format-List",
        "Displays basic system information",
        "Dark.TButton"
    ),
    (
        "🌐 IP Configuration",
        "Get-NetIPConfiguration | Where-Object {$_.IPv4Address} | Select-Object InterfaceAlias, IPv4Address, IPv4DefaultGateway, DNSServer | Format-List",
        "Displays network configuration",
        "Dark.TButton"
    ),
]

# ============================================================
#  🛡️ BUILT-IN SECURITY SCRIPTS
# ============================================================

SECURITY_SCRIPTS = [
    (
        "🛡️ Windows Defender Status",
        "Get-MpComputerStatus | Select-Object AntivirusEnabled, RealTimeProtectionEnabled, AntivirusSignatureLastUpdated | Format-List",
        "Shows Windows Defender protection status",
        "Dark.TButton"
    ),
]

# ============================================================
#  🧹 BUILT-IN MAINTENANCE SCRIPTS
# ============================================================

MAINTENANCE_SCRIPTS = [
    (
        "🧹 Flush DNS Cache",
        "Clear-DnsClientCache; Write-Host '✅ DNS Cache cleared!' -ForegroundColor Green",
        "Clears the DNS resolver cache",
        "Dark.TButton"
    ),
]


# ============================================================
#  COMBINE ALL SCRIPTS
# ============================================================

def get_script_sections():
    """
    Returns all script sections including:
    1. Built-in scripts (defined above)
    2. Loaded .ps1 files from the scripts folder
    """
    
    # Built-in sections
    sections = [
        ("🔧 SYSTEM INFO", SYSTEM_INFO_SCRIPTS),
        ("🛡️ SECURITY", SECURITY_SCRIPTS),
        ("🧹 MAINTENANCE", MAINTENANCE_SCRIPTS),
    ]
    
    # Add loaded scripts from the scripts folder
    loaded_sections = get_all_script_sections()
    sections.extend(loaded_sections)
    
    return sections