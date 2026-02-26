IT Admin Toolkit v2.0 - COMPLETE DEPLOYMENT & MAINTENANCE GUIDE
===================================================================

🚀 QUICK START
------------
Run: .\Build.ps1
   ↳ Auto-backups source code + builds optimized EXE
   ↳ Keeps only last 10 backups
   ↳ Everything you need in ONE COMMAND

## 📁 FOLDER STRUCTURE

```plaintext
IT-Admin-Toolkit/
├── 📁 Backups/                 # Versioned backups (*.7z) - max 10 kept
├── 📁 config/
│   ├── 📄 __init__.py
│   ├── 📄 winget.py            # Winget application definitions
│   ├── 📄 choco_apps.py        # Chocolatey application definitions
│   ├── 📄 script_loader.py     # Auto-loads .ps1 scripts from scripts folder
│   ├── 📄 scripts.py           # Hardcoded PowerShell script buttons
│   └── 📄 colors.py            # Theme colors
├── 📁 ui/
│   ├── 📄 __init__.py
│   ├── 📄 styles.py            # TTK widget styles
│   ├── 📄 winget_tab.py        # Winget installer tab
│   ├── 📄 choco_tab.py         # Chocolatey installer tab
│   ├── 📄 scripts_tab.py       # PowerShell scripts tab
│   ├── 📄 uninstall_tab.py     # Uninstall & cleanup tab
│   ├── 📄 logs_tab.py          # Log analysis tab
│   └── 📄 network_tab.py       # Network debugging tab
├── 📁 utils/
│   ├── 📄 __init__.py
│   ├── 📄 admin.py             # Admin privilege detection/elevation
│   ├── 📄 powershell.py        # PowerShell execution handler
│   ├── 📄 winget.py            # Winget manager class
│   ├── 📄 logs.py              # Log analysis utilities
│   ├── 📄 network.py           # Network diagnostics
│   └── 📄 network_debug.py     # Network debugging tools
├── 📁 scripts/                 # PowerShell scripts (auto-detected)
│   ├── 📁 Admin Task/
│   ├── 📁 Maintenance/
│   ├── 📁 Network/
│   ├── 📁 System Info/
│   └── 📁 AD Scripts/
├── 📁 build/                   # PyInstaller temp (excluded from Git)
├── 📁 dist/                    # EXE output (excluded from Git)
│   └── IT-Admin-Toolkit.exe
├── 📄 main.py                  # Entry point
├── 📄 app.py                   # Main application class
├── 📄 icon.ico                 # App icon
├── 📄 admin.manifest           # UAC admin elevation manifest
├── 📄 IT-Admin-Toolkit.spec    # PyInstaller build config
├── 📄 Build.ps1               # 🏗️ Build + Backup (RECOMMENDED)
├── 📄 Backup.ps1              # Source backup only (keeps last 10)
├── 📄 push.ps1                # 🚀 One-command Git push workflow
└── 📄 README.md
```

--------------------------------------------------------------------------------
🖥️ APPLICATION TABS
--------------------------------------------------------------------------------

📦 WINGET TAB
   • Install applications via Windows Package Manager
   • Search Winget repository
   • Bulk install selected apps

🍫 CHOCOLATEY TAB
   • Install applications via Chocolatey
   • Search Choco repository
   • Install Chocolatey if not present
   • Update all Choco packages

⚡ POWERSHELL SCRIPTS TAB
   • Run preset PowerShell scripts
   • Auto-loads scripts from scripts/ folder
   • Custom script input with interactive mode
   • Network diagnostics button

🗑️ UNINSTALL & CLEANUP TAB
   • Scan installed apps (Registry, Winget, Chocolatey)
   • Uninstall selected applications
   • Clean up leftover files, registry, AppData
   • Update selected or all apps
   • Export installed apps list

📊 LOG ANALYZER TAB
   • ESXi Log Analyzer - Extract and filter VMware logs
   • Generic Log Viewer - View any log file with filters
   • Windows Event Logs - Query System/Application/Security logs
   • Syslog Analyzer - Parse Linux syslog format
   • Date range filtering with quick presets
   • Keyword and regex search
   • Export filtered results

🌐 NETWORK DEBUG TAB
   • Ping - Test host reachability
   • Traceroute - Trace network path
   • NSLookup - DNS resolution
   • Port Check - Test specific port
   • Port Scan - Scan common ports
   • Whois - Get domain/IP info
   • Internet Test - Quick connectivity check
   • IPConfig - View network configuration
   • Flush DNS - Clear DNS cache
   • Renew IP - Release/renew DHCP
   • Netstat - View active connections
   • Routes - View routing table
   • ARP - View ARP cache
   • WiFi Info - Current WiFi details
   • WiFi Scan - Available networks

--------------------------------------------------------------------------------
➕ ADD NEW CONTENT
--------------------------------------------------------------------------------

➕ NEW APPLICATIONS (Winget)
   1. Open: config/winget.py
   2. Add to category:
      ("🌐 Browsers", [
          ("Google Chrome", "Google.Chrome"),
          ("Firefox", "Mozilla.Firefox"),  ← ADD HERE
      ]),
   3. Save & restart app

➕ NEW APPLICATIONS (Chocolatey)
   1. Open: config/choco_apps.py
   2. Add to category:
      ("🔧 Utilities", [
          ("7-Zip", "7zip"),
          ("Notepad++", "notepadplusplus"),  ← ADD HERE
      ]),
   3. Save & restart app

➕ NEW POWERSHELL SCRIPTS (Auto-detected)
   1. Create .ps1 file in: scripts/ or scripts/[Category]/
   2. Add header:
      # NAME: 🚀 My Script Name
      # DESCRIPTION: What this does
      # STYLE: Dark.TButton
      # INTERACTIVE: false
      
      # Your PowerShell code here...
   3. Restart app - script auto-appears

➕ NEW POWERSHELL SCRIPTS (Hardcoded)
   1. Open: config/scripts.py
   2. Add entry:
      (
          "🛡️ Button Name",
          "Get-Command | Format-List",  # PowerShell command
          "Description shown on hover",
          "Dark.TButton"  # or Warning.TButton, Danger.TButton
      ),
   3. Restart app

🎨 CUSTOM COLORS
   1. Edit: config/colors.py
   2. Modify COLORS dictionary

--------------------------------------------------------------------------------
🏗️ BUILD EXECUTABLE
--------------------------------------------------------------------------------

✅ RECOMMENDED:
   .\Build.ps1
   ↳ Backup + Optimized EXE + Cleanup + Keep last 10 backups

📦 BUILD OPTIMIZATIONS (automatic):
   • UPX compression (if upx.exe present)
   • Excluded unused modules
   • Admin manifest embedded
   • Strip debug symbols

⬇️ OPTIONAL - Download UPX for smaller builds:
   https://github.com/upx/upx/releases
   Extract upx.exe to project folder

📊 TYPICAL SIZES:
   • Without UPX: ~25-35 MB
   • With UPX:    ~10-15 MB

--------------------------------------------------------------------------------
💾 BACKUP PROCESS
--------------------------------------------------------------------------------

✅ BACKED UP:
   main.py, app.py, config/, ui/, utils/, scripts/
   icon.ico, admin.manifest, Build.ps1, Backup.ps1, README.md

✅ VERSIONING:
   Format: "YY-MM-DD_HHMM.7z"
   Example: "25-02-26_1430.7z"
   Keeps: Last 10 backups only (older auto-deleted)

❌ EXCLUDED:
   __pycache__/  build/  dist/  venv/  .venv/  .git/
   *.pyc  *.exe  *.log  *.spec  *.tmp  Backups/

--------------------------------------------------------------------------------
🔄 UPDATE WORKFLOW
--------------------------------------------------------------------------------
1. Make changes (winget.py, choco_apps.py, scripts/, colors.py, etc.)
2. Test: python main.py
3. Build: .\Build.ps1
4. Deploy: dist/IT-Admin-Toolkit.exe → users
5. ✅ DONE

--------------------------------------------------------------------------------
🛡️ ADMIN PRIVILEGES
--------------------------------------------------------------------------------

The app requests admin on launch (via manifest).

If not running as admin:
   • Yellow "Run as Admin" button appears
   • Click to relaunch with elevation
   • Some features limited without admin:
     - Flush DNS
     - Renew IP
     - Some uninstall operations
     - Windows Event Log queries

--------------------------------------------------------------------------------
📊 LOG ANALYZER FEATURES
--------------------------------------------------------------------------------

🖥️ ESXi Log Analyzer
   • Extracts .tar/.tgz log bundles
   • Filters by date range
   • Outputs filtered results to text file
   • Preview in app

📄 Generic Log Viewer
   • Opens any .log or .txt file
   • Auto-detects common timestamp formats:
     - 2025-02-26 14:30:00
     - 2025-02-26T14:30:00
     - 02/26/2025 14:30:00
     - Feb 26 14:30:00 (syslog)
   • Filter by date range
   • Search by keywords (comma-separated)
   • Regex pattern matching
   • Case sensitive option
   • Save filtered results

🪟 Windows Event Logs
   • Query any Windows event log
   • Filter by time range (hours)
   • Filter by level (Critical, Error, Warning, Info)
   • Filter by Event IDs
   • Keyword search
   • Color-coded results
   • Export to file

--------------------------------------------------------------------------------
🌐 NETWORK DEBUG FEATURES
--------------------------------------------------------------------------------

Target-based tools (uses IP/Hostname field):
   🏓 Ping          - ICMP ping with statistics
   🔍 Traceroute    - Trace route to target
   🔎 NSLookup      - DNS resolution
   🔌 Port Check    - Test single port
   📡 Port Scan     - Scan common ports (21,22,80,443,etc)
   🌐 Whois         - Domain/IP information

System tools:
   🌐 Internet Test - Quick connectivity check
   📋 IPConfig      - Full network configuration
   🧹 Flush DNS     - Clear DNS resolver cache
   🔄 Renew IP      - Release and renew DHCP
   📊 Netstat       - Active network connections
   🗺️ Routes        - IP routing table
   📋 ARP           - ARP cache table
   📶 WiFi Info     - Current WiFi connection details
   📡 WiFi Scan     - Available wireless networks

Output options:
   🗑️ Clear         - Clear output window
   💾 Save          - Save output to file

--------------------------------------------------------------------------------
🐛 TROUBLESHOOTING
--------------------------------------------------------------------------------

❓ New scripts not showing?
   → Restart app (scripts load at startup)

❓ PyInstaller fails?
   → Delete build/, dist/ folders
   → Run: .\Build.ps1

❓ App won't run as admin?
   → Right-click EXE → Run as administrator
   → Check admin.manifest exists

❓ Uninstall scan empty?
   → Click "SCAN INSTALLED APPS" button
   → Requires admin for full results

❓ Build too large?
   → Download upx.exe to project folder
   → Rebuild with .\Build.ps1

❓ Python update issues?
   → pip install --upgrade pyinstaller
   → Delete build/, dist/, *.spec
   → Rebuild

❓ Network tools not working?
   → Run app as administrator
   → Check Windows Firewall settings

❓ Log analyzer can't read file?
   → Check file encoding (UTF-8 recommended)
   → Try Generic Log Viewer for unknown formats

❓ Windows Events query slow?
   → Reduce time range (hours)
   → Add Event ID filter
   → Limit to specific log (System vs All)