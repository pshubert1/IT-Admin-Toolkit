# IT Admin Toolkit v2.0 - COMPLETE DEPLOYMENT & MAINTENANCE GUIDE

## 🚀 QUICK START

Run: `.\Build.ps1`
```plaintext
↳ Auto-backups source code + builds optimized EXE
   ↳ Keeps only last 10 backups
   ↳ Everything you need in ONE COMMAND
````
## 📁 FOLDER STRUCTURE

```plaintext
IT-Admin-Toolkit/
├── 📁 Backups/                 # Versioned backups (*.7z) - max 10 kept
├── 📁 config/
│   ├── 📄 __init__.py
│   ├── 📄 winget.py            # Winget application definitions
│   ├── 📄 choco_apps.py        # Chocolatey application definitions
│   ├── 📄 script_loader.py     # Auto-loads .ps1 scripts from scripts folder
│   ├── 📄 scripts.py           # Built-in scripts + folder merge rules
│   └── 📄 colors.py            # Theme colors
├── 📁 ui/
│   ├── 📄 __init__.py
│   ├── 📄 styles.py            # TTK widget styles
│   ├── 📄 winget_tab.py        # Winget installer tab
│   ├── 📄 choco_tab.py         # Chocolatey installer tab
│   ├── 📄 scripts_tab.py       # PowerShell scripts tab
│   ├── 📄 uninstall_tab.py     # Uninstall & cleanup tab
│   ├── 📄 logs_tab.py          # Log analysis tab
│   ├── 📄 network_tab.py       # Network debugging tab
│   └── 📄 updates_tab.py       # Windows Updates tab
├── 📁 utils/
│   ├── 📄 __init__.py
│   ├── 📄 admin.py             # Admin privilege detection/elevation
│   ├── 📄 powershell.py        # PowerShell execution handler
│   ├── 📄 winget.py            # Winget manager class
│   ├── 📄 choco.py             # Chocolatey manager class
│   ├── 📄 logs.py              # Log analysis utilities
│   ├── 📄 network.py           # Network diagnostics
│   └── 📄 network_debug.py     # Network debugging tools
├── 📁 scripts/                 # PowerShell scripts (auto-detected + merged)
│   ├── 📁 AD Scripts/
│   ├── 📁 Admin Task/
│   ├── 📁 Defender/
│   ├── 📁 Maintenance/
│   ├── 📁 Network/
│   └── 📁 System Info/
├── 📁 build/                   # PyInstaller temp (excluded from Git)
├── 📁 dist/                    # EXE output (excluded from Git)
│   └── IT-Admin-Toolkit.exe
├── 📄 main.py                  # Entry point
├── 📄 app.py                   # Main application class
├── 📄 icon.ico                 # App icon
├── 📄 Build.ps1               # 🏗️ Build + Backup (RECOMMENDED)
├── 📄 Backup.ps1              # Source backup only (keeps last 10)
├── 📄 push.ps1                # 🚀 One-command Git push workflow
├── 📄 .gitignore              # List of things to exclude from GitHub
├── 📄 requirements.py         # To find all add-ons that are needed
├── 📄 requirements.txt        # List add-ons that are needed
├── 📄 Setup_dev_environment.ps1   # Installs what is needed for this project
├── 📄 reset-venv.ps1          # Reset virtual env and creates the new .venv files
└── 📄 README.md
```

## 🖥️ APPLICATION TABS

### 📦 WINGET TAB

```plaintext
• Install applications via Windows Package Manager
• Search Winget repository
• Bulk install selected apps
• Silent install with automatic fallback to interactive
• Handles common exit codes with helpful messages
```

### 🍫 CHOCOLATEY TAB

```plaintext
• Install applications via Chocolatey
• Search Choco repository
• Install Chocolatey if not present
• Update all Choco packages
• Auto-detects choco.exe path
```

### ⚡ POWERSHELL SCRIPTS TAB

```plaintext
• Run preset PowerShell scripts
• Auto-loads scripts from scripts/ folder
• Built-in scripts merged with matching folder scripts
• Custom script input with interactive mode
• Network diagnostics button
• Load .ps1 files from disk
```

### 🗑️ UNINSTALL & CLEANUP TAB

```plaintext
• Scan installed apps (Registry, Winget, Chocolatey)
• Uninstall selected applications
• Clean up leftover files, registry, AppData
• Update selected or all apps
• Export installed apps list
```

### 📊 LOG ANALYZER TAB

```plaintext
• ESXi Log Analyzer - Extract and filter VMware logs
• Generic Log Viewer - View any log file with filters
• Windows Event Logs - Query System/Application/Security logs
• Syslog Analyzer - Parse Linux syslog format
• Date range filtering with quick presets
• Keyword and regex search
• Export filtered results
```

### 🌐 NETWORK DEBUG TAB

```plaintext
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
• Device Join Status (Azure AD / Hybrid / Intune)
```

### 🔄 WINDOWS UPDATES TAB

```plaintext
• Scan for available updates via PSWindowsUpdate
• Display update details (KB, size, type)
• Selective installation with checkboxes
• Module auto-install if missing
```

---

## ➕ ADD NEW CONTENT

### ➕ NEW APPLICATIONS (Winget)

1. Open: `config/winget.py`
2. Add to category:

```python
("🌐 Browsers", [
    ("Google Chrome", "Google.Chrome"),
    ("Firefox", "Mozilla.Firefox"),  # ← ADD HERE
]),
```

3. Save & restart app

### ➕ NEW APPLICATIONS (Chocolatey)

1. Open: `config/choco_apps.py`
2. Add to category:

```python
("🔧 Utilities", [
    ("7-Zip", "7zip"),
    ("Notepad++", "notepadplusplus"),  # ← ADD HERE
]),
```

3. Save & restart app

### ➕ NEW POWERSHELL SCRIPTS (Auto-detected from folder)

1. Create `.ps1` file in: `scripts/` or `scripts/Category/`
2. Add metadata header:

```powershell
# NAME: 🚀 My Script Name
# DESCRIPTION: What this does
# STYLE: Dark.TButton
# INTERACTIVE: false

# Your PowerShell code here...
```

3. Restart app — script auto-appears in the matching category

#### Script Metadata Reference

|Field|Required|Values|Default|
|---|---|---|---|
|`NAME`|No|Any text|Filename|
|`DESCRIPTION`|No|Any text|"No description"|
|`STYLE`|No|`Dark.TButton`, `Warning.TButton`, `Danger.TButton`, `Success.TButton`|`Dark.TButton`|
|`INTERACTIVE`|No|`true` / `false`|Auto-detects if script contains `Read-Host`|

#### Interactive Scripts

Scripts with `INTERACTIVE: true` (or containing `Read-Host`) open in a **visible PowerShell window** so the user can interact. All other scripts run in the background with output captured in the app.

### ➕ NEW POWERSHELL SCRIPTS (Hardcoded / Built-in)

1. Open: `config/scripts.py`
2. Add entry to a section's `"scripts"` list:

```python
(
    "🛡️ Button Name",
    "Get-Command | Format-List",      # PowerShell command
    "Description shown next to button",
    "Dark.TButton",                    # Button style
    False                              # Interactive (True/False)
),
```

3. Restart app

---

## 🔀 SCRIPT CATEGORY MERGE RULES

The Scripts tab **automatically merges** built-in (hardcoded) scripts with scripts loaded from the `scripts/` folder. If a folder name matches a built-in category, they appear together in one unified section.

### How Merging Works

```plaintext
Built-in Category              scripts/ Folder              UI Result
──────────────────             ─────────────────           ──────────────────
"🔧 System Info"          +   scripts/System Info/*.ps1   → One "🔧 System Info" section
"🛡️ Security / Defender"  +   scripts/Defender/*.ps1      → One "🛡️ Security / Defender" section
"🧹 Maintenance"          +   scripts/Maintenance/*.ps1   → One "🧹 Maintenance" section
"🌐 Network"              +   scripts/Network/*.ps1       → One "🌐 Network" section
"👤 AD Scripts"            +   scripts/AD Scripts/*.ps1    → One "👤 AD Scripts" section
"⚙️ Admin Tasks"           +   scripts/Admin Task/*.ps1    → One "⚙️ Admin Tasks" section

(no match)                     scripts/NewFolder/*.ps1     → New "📁 NewFolder" section
```

**Built-in scripts appear first**, followed by folder scripts in the same section.

### Current Merge Map

Defined in `config/scripts.py` → `BUILTIN_SECTIONS`:

|Built-in Section|Matches These Folders|Built-in Scripts|
|---|---|---|
|🔧 System Info|`System Info`|System Information, IP Configuration|
|🛡️ Security / Defender|`Defender`, `Security`|Defender Status|
|🧹 Maintenance|`Maintenance`|Flush DNS, Axcient Backup|
|🌐 Network|`Network`|_(none — folder scripts only)_|
|👤 AD Scripts|`AD Scripts`|_(none — folder scripts only)_|
|⚙️ Admin Tasks|`Admin Task`, `Admin Tasks`|_(none — folder scripts only)_|

### ➕ Add a New Merge Rule

1. Open: `config/scripts.py`
2. Add to `BUILTIN_SECTIONS`:

```python
{
    "name": "🔥 My New Category",        # Display name in the UI
    "match_folders": ["My Folder"],       # Folder names to merge (can list multiple)
    "scripts": [
        # Optional built-in scripts (or leave empty [])
        (
            "📊 My Built-in Script",
            "Get-Process | Select-Object -First 10",
            "Shows top 10 processes",
            "Dark.TButton",
            False
        ),
    ]
},
```

3. Create matching folder: `scripts/My Folder/`
4. Add `.ps1` files to that folder
5. Restart app — built-in + folder scripts appear together

### ➕ Add a Folder-Only Category (No Built-in Scripts)

1. Just create the folder: `scripts/My New Category/`
2. Add `.ps1` files with metadata headers
3. Restart app — appears as "📁 My New Category"

_No changes to any Python files needed!_

### ➕ Add a Built-in-Only Category (No Folder)

1. Open: `config/scripts.py`
2. Add to `BUILTIN_SECTIONS`:

```python
{
    "name": "⚡ Quick Commands",
    "match_folders": [],                  # No folder matching
    "scripts": [
        ("📋 List Services", "Get-Service | Where-Object {$_.Status -eq 'Running'}", "List running services", "Dark.TButton", False),
        ("💾 Disk Space", "Get-PSDrive -PSProvider FileSystem | Format-Table", "Show disk usage", "Dark.TButton", False),
    ]
},
```

3. Restart app

---

## 📋 CENTRALIZED LOGGING

All error, warning, and success messages use centralized methods in `app.py` for consistent formatting.

### Log Methods

|Method|Format|Use For|
|---|---|---|
|`self.app.log("message")`|`[HH:MM:SS] message`|Neutral info, status updates|
|`self.app.log_success("message")`|`[HH:MM:SS] ✅ message`|Successful operations|
|`self.app.log_warning("message", hint)`|`[HH:MM:SS] ⚠️ message` + optional hint|Non-fatal issues|
|`self.app.log_error("message", hint)`|`[HH:MM:SS] ❌ message` + hint + debug reminder|Failures|

### Error Format Example

```plaintext
[14:53:15] ❌ Process Explorer - no installer for this system
[14:53:15]    💡 ID 'Microsoft.Sysinternals.ProcessExplorer' may not support this OS/architecture
[14:53:15]    🔧 Enable Debug Mode for more details
```

### Usage in Code

**From UI tabs** (where `self.app` is available):

```python
self.app.log("📥 Installing Chrome...")
self.app.log_success("Chrome installed")
self.app.log_warning("Silent install failed, retrying...")
self.app.log_error("Chrome failed to install", hint="Try Chocolatey instead")
```

**From utility classes** (where `self.app` is passed in):

```python
# In __init__:
def __init__(self, app=None, log_callback=None):
    self.app = app

# Then use:
self.app.log_error("DNS lookup failed", hint="Check DNS settings")
```

### 🧪 Testing Logs

1. Enable **Debug Mode** (checkbox in header)
2. Click **🧪 TEST LOGS** button (appears in Activity Log toolbar)
3. All error/warning/success formats are displayed for verification

---

## 🎨 CUSTOM COLORS

1. Edit: `config/colors.py`
2. Modify `COLORS` dictionary

## 🏗️ BUILD EXECUTABLE

**✅ RECOMMENDED:**

```plaintext
.\Build.ps1
↳ Backup + Optimized EXE + Cleanup + Keep last 10 backups
```

## 💾 BACKUP PROCESS

**✅ BACKED UP:**

```plaintext
main.py, app.py, config/, ui/, utils/, scripts/
icon.ico, admin.manifest, Build.ps1, Backup.ps1, README.md
```

**✅ VERSIONING:**

```plaintext
Format: "YY-MM-DD_HHMM.7z"
Example: "25-02-26_1430.7z"
Keeps: Last 10 backups only (older auto-deleted)
```

**❌ EXCLUDED:**

```plaintext
__pycache__/  build/  dist/  venv/  .venv/  .git/
*.pyc  *.exe  *.log  *.spec  *.tmp  Backups/
```

## 🔄 UPDATE WORKFLOW

```plaintext
1. Make changes (winget.py, choco_apps.py, scripts/, colors.py, etc.)
2. Test: python main.py
3. Build: .\Build.ps1
4. Deploy: dist/IT-Admin-Toolkit.exe → users
✅ DONE
```

## 🛡️ ADMIN PRIVILEGES

```plaintext
The app requests admin on launch (via manifest).
If not running as admin:
   • Yellow "Run as Admin" button appears
   • Click to relaunch with elevation
   • Some features limited without admin:
     - Flush DNS
     - Renew IP
     - Some uninstall operations
     - Windows Event Log queries
     - Chocolatey install
     - Windows Update install
```

## 📊 LOG ANALYZER FEATURES

### 🖥️ ESXi Log Analyzer

```plaintext
• Extracts .tar/.tgz log bundles
• Filters by date range
• Outputs filtered results to text file
• Preview in app
```

### 📄 Generic Log Viewer

```plaintext
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
```

### 🪟 Windows Event Logs

```plaintext
• Query any Windows event log
• Filter by time range (hours)
• Filter by level (Critical, Error, Warning, Info)
• Filter by Event IDs
• Keyword search
• Color-coded results
• Export to file
```

## 🌐 NETWORK DEBUG FEATURES

**Target-based tools** (uses IP/Hostname field):

```plaintext
🏓 Ping          - ICMP ping with statistics
🔍 Traceroute    - Trace route to target
🔎 NSLookup      - DNS resolution
🔌 Port Check    - Test single port
📡 Port Scan     - Scan common ports (21,22,80,443,etc)
🌐 Whois         - Domain/IP information
```

**System tools:**

```plaintext
🌐 Internet Test - Quick connectivity check
📋 IPConfig      - Full network configuration
🧹 Flush DNS     - Clear DNS resolver cache
🔄 Renew IP      - Release and renew DHCP
📊 Netstat       - Active network connections
🗺️ Routes        - IP routing table
📋 ARP           - ARP cache table
📶 WiFi Info     - Current WiFi connection details
📡 WiFi Scan     - Available wireless networks
🖥️ Device Join   - Azure AD / Hybrid Join / Intune status
```

**Output options:**

```plaintext
🗑️ Clear         - Clear output window
💾 Save          - Save output to file
```

## 🐛 TROUBLESHOOTING

```plaintext
❓ New scripts not showing?
      → Restart app (scripts load at startup)
      → Check .ps1 file is in scripts/ or scripts/SubFolder/

❓ Scripts showing in wrong category?
      → Check folder name matches a match_folders entry in config/scripts.py
      → Or create a new BUILTIN_SECTIONS entry with the folder name

❓ PyInstaller fails?
      → Delete build/, dist/ folders
      → Run: .\Build.ps1

❓ App won't run as admin?
      → Right-click EXE → Run as administrator
      → Check admin.manifest exists

❓ Uninstall scan empty?
      → Click "SCAN INSTALLED APPS" button
      → Requires admin for full results

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

❓ Winget install fails?
      → Enable Debug Mode for detailed output
      → Check winget ID with: winget search "app name"
      → Try Chocolatey tab as alternative

❓ Chocolatey not found?
      → Click "INSTALL CHOCO" button (requires admin)
      → Restart app after installing

❓ Execution Policy errors?
      → Run once as admin: Set-ExecutionPolicy RemoteSigned -Scope LocalMachine -Force
```


### What Was Added/Updated

| Section | Change |
|---------|--------|
| Folder Structure | Added `updates_tab.py`, `choco.py`, updated `scripts.py` description |
| Scripts Tab | Updated description mentioning merge behavior |
| Network Tab | Added Device Join Status |
| Updates Tab | New section |
| Script Metadata Reference | New table with all fields |
| Interactive Scripts | New explanation |
| **🔀 Script Category Merge Rules** | **New entire section** with merge map, examples, all 3 add scenarios |
| **📋 Centralized Logging** | **New entire section** with methods, format, code examples, testing |
| Troubleshooting | Added entries for scripts, winget, choco, execution policy |