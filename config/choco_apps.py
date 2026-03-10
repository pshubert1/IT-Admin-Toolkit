"""
Chocolatey Application Definitions
"""


def get_choco_sections():
    """
    Returns sections of Chocolatey apps.
    Format: [(section_title, [(app_name, choco_id), ...]), ...]
    """
    return [
        ("🤖 AI Tools", [
            ("GitHub Copilot CLI", "github-copilot-cli"), 
        ]),
        ("🌐 Browsers", [
            ("Google Chrome", "googlechrome"),
            ("Firefox", "firefox"),
            ("Brave", "brave"),
            ("Microsoft Edge", "microsoft-edge"),
        ]),
        
        ("💬 Communication", [
            ("Zoom", "zoom"),
            ("Microsoft Teams", "microsoft-teams"),
            ("Slack", "slack"),
            ("Discord", "discord"),
        ]),
        
        ("🔧 Utilities", [
            ("7-Zip", "7zip"),
            ("Notepad++", "notepadplusplus"),
            ("PuTTY", "putty"),
            ("WinSCP", "winscp"),
            ("Everything Search", "everything"),
            ("PowerToys", "powertoys"),
            ("Dell Command Updates", "dellcommandupdate"),
            ("Lenovo System Update", "lenovo-thinkvantage-system-update"),
            
        ]),
        
        ("👨‍💻 Development", [
            ("VS Code", "vscode"),
            ("Git", "git"),
            ("Python 3", "python3"),
            ("Node.js LTS", "nodejs-lts"),
            ("Windows Terminal", "microsoft-windows-terminal"),
        ]),
        
        ("🎬 Media", [
            ("VLC", "vlc"),
            ("Spotify", "spotify"),
            ("ShareX", "sharex"),
        ]),
        
        ("📄 Office", [
            ("Adobe Reader", "adobereader"),
            ("LibreOffice", "libreoffice-fresh"),
            ("SumatraPDF", "sumatrapdf"),
            ("Office365-Apps", "office365business"),
        ]),
        
        ("🔒 Security", [
            ("Malwarebytes", "malwarebytes"),
            ("Bitwarden", "bitwarden"),
        ]),
        
        ("🖥️ Remote Access", [
            ("AnyDesk", "anydesk"),
            ("TeamViewer", "teamviewer"),
            ("RustDesk", "rustdesk"),
        ]),
        
        ("🛠️ System Tools", [
            ("CPU-Z", "cpu-z"),
            ("HWiNFO", "hwinfo"),
            ("CrystalDiskInfo", "crystaldiskinfo"),
            ("Sysinternals Suite", "sysinternals"),
        ]),
    ]