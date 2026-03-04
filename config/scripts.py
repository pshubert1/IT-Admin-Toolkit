"""
╔══════════════════════════════════════════════════════════════════╗
║                    POWERSHELL SCRIPTS                            ║
║                                                                  ║
║  Built-in scripts are merged with matching folders from          ║
║  the scripts/ directory. If a folder name matches a built-in     ║
║  category, they appear together in one section.                  ║
╚══════════════════════════════════════════════════════════════════╝
"""

import re
from config.script_loader import get_all_script_sections

# ============================================================
#  BUILT-IN SCRIPTS
#  Each section has: (display_name, folder_matches, scripts_list)
#    - display_name: What shows in the UI
#    - folder_matches: List of folder names that merge into this section
#    - scripts_list: Built-in script definitions
# ============================================================

BUILTIN_SECTIONS = [
    {
        "name": "🔧 System Info",
        "match_folders": ["System Info"],
        "scripts": [
            (
                "📊 System Information",
                "Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion, "
                "OsHardwareAbstractionLayer, CsName, CsProcessors, CsTotalPhysicalMemory | Format-List",
                "Displays basic system information",
                "Dark.TButton",
                False
            ),
            (
                "🌐 IP Configuration",
                "Get-NetIPConfiguration | Where-Object {$_.IPv4Address} | "
                "Select-Object InterfaceAlias, IPv4Address, IPv4DefaultGateway, DNSServer | Format-List",
                "Displays network configuration",
                "Dark.TButton",
                False
            ),
        ]
    },
    {
        "name": "🛡️ Security / Defender",
        "match_folders": ["Defender", "Security"],
        "scripts": [
            (
                "🛡️ Windows Defender Status",
                "Get-MpComputerStatus | Select-Object AntivirusEnabled, "
                "RealTimeProtectionEnabled, AntivirusSignatureLastUpdated | Format-List",
                "Shows Windows Defender protection status",
                "Dark.TButton",
                False
            ),
        ]
    },
    {
        "name": "🧹 Maintenance",
        "match_folders": ["Maintenance"],
        "scripts": [
            (
                "🧹 Flush DNS Cache",
                "Clear-DnsClientCache; Write-Host '✅ DNS Cache cleared!' -ForegroundColor Green",
                "Clears the DNS resolver cache",
                "Dark.TButton",
                False
            ),
            (
                "💾 Axcient Full Backup",
                r'$agentPath = "${env:ProgramFiles(x86)}\Axcient\x360Recover Agent"; '
                r'& "$agentPath\x360recover-agent.exe" --full-backup',
                "Starts a full Axcient D2C backup",
                "Dark.TButton",
                False
            ),
        ]
    },
    {
        "name": "🌐 Network",
        "match_folders": ["Network"],
        "scripts": []
    },
    {
        "name": "👤 AD Scripts",
        "match_folders": ["AD Scripts"],
        "scripts": []
    },
    {
        "name": "⚙️ Admin Tasks",
        "match_folders": ["Admin Task", "Admin Tasks"],
        "scripts": []
    },
]


def _normalize(name):
    """Strip emojis and whitespace for comparison."""
    # Remove emoji and special chars, lowercase, strip
    cleaned = re.sub(r'[^\w\s]', '', name).strip().lower()
    # Remove common prefixes
    cleaned = re.sub(r'^(folder|scripts?)\s*', '', cleaned).strip()
    return cleaned


def get_script_sections():
    """
    Returns all script sections with built-in and folder scripts merged.
    
    Logic:
    1. Start with built-in sections (hardcoded scripts)
    2. Load all .ps1 scripts from scripts/ subfolders
    3. If a folder name matches a built-in section's match_folders, merge them
    4. Unmatched folders become their own new sections
    """
    
    # Load scripts from the scripts/ folder
    loaded_sections = get_all_script_sections()
    
    # Build a lookup: normalized folder name → list of scripts
    folder_lookup = {}
    for section_name, scripts in loaded_sections:
        # section_name comes as "📁 FolderName" from script_loader
        # Strip the "📁 " prefix to get the raw folder name
        raw_name = section_name.replace("📁 ", "").strip()
        folder_lookup[raw_name] = {
            "display_name": section_name,
            "scripts": scripts,
            "matched": False
        }
    
    # Build merged sections
    merged_sections = []
    
    for builtin in BUILTIN_SECTIONS:
        section_name = builtin["name"]
        section_scripts = list(builtin["scripts"])  # Copy so we don't modify original
        
        # Check each match_folders entry against loaded folders
        for match_name in builtin.get("match_folders", []):
            if match_name in folder_lookup:
                # Merge folder scripts into this section
                folder_data = folder_lookup[match_name]
                
                # Add a separator label between built-in and loaded scripts
                if section_scripts and folder_data["scripts"]:
                    # Add loaded scripts after built-in ones
                    section_scripts.extend(folder_data["scripts"])
                elif folder_data["scripts"]:
                    section_scripts = list(folder_data["scripts"])
                
                folder_data["matched"] = True
            else:
                # Try normalized matching as fallback
                for folder_name, folder_data in folder_lookup.items():
                    if (not folder_data["matched"] and 
                        _normalize(match_name) == _normalize(folder_name)):
                        section_scripts.extend(folder_data["scripts"])
                        folder_data["matched"] = True
                        break
        
        # Only add section if it has scripts
        if section_scripts:
            merged_sections.append((section_name, section_scripts))
    
    # Add any unmatched folders as their own sections
    for folder_name, folder_data in folder_lookup.items():
        if not folder_data["matched"] and folder_data["scripts"]:
            merged_sections.append((folder_data["display_name"], folder_data["scripts"]))
    
    return merged_sections