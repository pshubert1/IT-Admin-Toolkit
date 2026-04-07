"""
RMM Agent Installer Tool
Downloads and installs MSI from a configurable URL.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import json


CONFIG_FILE = os.path.join(os.environ.get('APPDATA', ''), 'ITAdminToolkit', 'rmm_config.json')


def _load_saved_urls():
    """Load saved URLs from config."""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                return data.get('urls', []), data.get('last_url', '')
    except:
        pass
    return [], ''


def _save_url(url):
    """Save URL to config for next time."""
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        urls, _ = _load_saved_urls()
        
        # Add to history (no duplicates, max 10)
        if url in urls:
            urls.remove(url)
        urls.insert(0, url)
        urls = urls[:10]
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump({'urls': urls, 'last_url': url}, f, indent=2)
    except:
        pass


class RMMInstallerWindow:
    def __init__(self, parent, app=None):
        self.app = app
        self.window = tk.Toplevel(parent)
        self.window.title("RMM Agent Installer")
        self.window.geometry("600x400")
        self.window.minsize(500, 350)
        self.window.grab_set()
        
        # Theme
        if app and hasattr(app, 'colors'):
            bg = app.colors['bg']
            fg = app.colors['fg']
        else:
            bg = '#1e1e2e'
            fg = '#ffffff'
        
        self.window.configure(bg=bg)
        self._bg = bg
        self._fg = fg
        
        # Load saved URLs
        saved_urls, last_url = _load_saved_urls()
        
        # ── Header ──
        header = tk.Label(self.window, text="📥 RMM Agent MSI Installer",
                         bg=bg, fg=fg, font=('Segoe UI', 12, 'bold'), anchor='w')
        header.pack(fill='x', padx=15, pady=(15, 5))
        
        desc = tk.Label(self.window, text="Enter the CW RMM / agent download URL, then click Install.",
                       bg=bg, fg='#888888', font=('Segoe UI', 9), anchor='w')
        desc.pack(fill='x', padx=15, pady=(0, 10))
        
        # ── URL Entry ──
        url_frame = tk.Frame(self.window, bg=bg)
        url_frame.pack(fill='x', padx=15, pady=(0, 5))
        
        tk.Label(url_frame, text="URL:", bg=bg, fg=fg, 
                font=('Segoe UI', 10, 'bold')).pack(side='left', padx=(0, 10))
        
        self.url_entry = tk.Entry(url_frame, bg='#2a2a3e', fg=fg, 
                                 font=('Consolas', 10), insertbackground='white')
        self.url_entry.pack(side='left', fill='x', expand=True)
        
        if last_url:
            self.url_entry.insert(0, last_url)
        
        # ── Saved URLs dropdown ──
        if saved_urls:
            history_frame = tk.Frame(self.window, bg=bg)
            history_frame.pack(fill='x', padx=15, pady=(0, 10))
            
            tk.Label(history_frame, text="Recent:", bg=bg, fg='#888888',
                    font=('Segoe UI', 9)).pack(side='left', padx=(0, 10))
            
            self.url_combo = ttk.Combobox(history_frame, values=saved_urls,
                                         font=('Consolas', 9), state='readonly')
            self.url_combo.pack(side='left', fill='x', expand=True)
            self.url_combo.bind('<<ComboboxSelected>>', self._on_url_selected)
        
        # ── Options ──
        opts_frame = tk.LabelFrame(self.window, text="Options", bg=bg, fg=fg,
                                  font=('Segoe UI', 9, 'bold'), padx=10, pady=5)
        opts_frame.pack(fill='x', padx=15, pady=(0, 10))
        
        self.silent_var = tk.BooleanVar(value=True)
        tk.Checkbutton(opts_frame, text="Silent install (/qn)", variable=self.silent_var,
                      bg=bg, fg=fg, selectcolor='#333355', activebackground=bg,
                      activeforeground=fg, font=('Segoe UI', 9)).pack(anchor='w')
        
        self.log_var = tk.BooleanVar(value=True)
        tk.Checkbutton(opts_frame, text="Enable MSI logging (C:\\Temp\\CW_RMM_Install.log)",
                      variable=self.log_var, bg=bg, fg=fg, selectcolor='#333355',
                      activebackground=bg, activeforeground=fg,
                      font=('Segoe UI', 9)).pack(anchor='w')
        
        self.cleanup_var = tk.BooleanVar(value=False)
        tk.Checkbutton(opts_frame, text="Delete MSI after install",
                      variable=self.cleanup_var, bg=bg, fg=fg, selectcolor='#333355',
                      activebackground=bg, activeforeground=fg,
                      font=('Segoe UI', 9)).pack(anchor='w')
        
        # ── Buttons ──
        btn_frame = tk.Frame(self.window, bg=bg)
        btn_frame.pack(fill='x', padx=15, pady=(5, 10))
        
        tk.Button(btn_frame, text="⚡ DOWNLOAD & INSTALL", command=self._run_install,
                 bg='#2d7d46', fg='white', relief='flat', padx=20, pady=8,
                 font=('Segoe UI', 10, 'bold'), cursor='hand2').pack(side='left', padx=(0, 10))
        
        tk.Button(btn_frame, text="📥 DOWNLOAD ONLY", command=self._run_download_only,
                 bg='#333355', fg=fg, relief='flat', padx=15, pady=8,
                 font=('Segoe UI', 9)).pack(side='left', padx=(0, 10))
        
        tk.Button(btn_frame, text="🗑️ CLEAR HISTORY", command=self._clear_history,
                 bg='#333355', fg=fg, relief='flat', padx=10, pady=8,
                 font=('Segoe UI', 9)).pack(side='right')
        
        # ── Status ──
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(self.window, textvariable=self.status_var, bg=bg, fg='#888888',
                font=('Consolas', 9), anchor='w').pack(fill='x', padx=15, pady=(0, 10))
    
    def _on_url_selected(self, event):
        """Fill entry from dropdown selection."""
        selected = self.url_combo.get()
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, selected)
    
    def _get_url(self):
        """Validate and return the URL."""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("No URL", "Enter a download URL.", parent=self.window)
            return None
        if not url.startswith('http'):
            messagebox.showwarning("Invalid URL", "URL must start with http:// or https://",
                                  parent=self.window)
            return None
        return url
    
    def _build_script(self, url, download_only=False):
        """Build the PowerShell script with the given URL."""
        silent_flag = '/qn' if self.silent_var.get() else '/qb'
        log_flag = '/l*v \\"$msiLog\\"' if self.log_var.get() else ''
        cleanup = '$true' if self.cleanup_var.get() else '$false'
        install_block = '$true' if not download_only else '$false'
        
        script = f'''
$ErrorActionPreference = "Stop"
$url = "{url}"
$doInstall = {install_block}
$doCleanup = {cleanup}

$logDir   = "C:\\Temp"
$msiLog   = Join-Path $logDir "CW_RMM_Install.log"
$scriptLog = Join-Path $logDir "CW_RMM_Install-Script.log"
$tempDir  = "C:\\Temp"

if (!(Test-Path $tempDir)) {{ New-Item -ItemType Directory -Path $tempDir -Force | Out-Null }}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RMM Agent MSI Installer" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "URL: $url" -ForegroundColor Gray
Write-Host ""

# ── Download ──
Write-Host "📥 Downloading..." -ForegroundColor Yellow
$uri = [System.Uri]$url
$path = $uri.AbsolutePath

if ($path -match '/32/([^/]+)/MSI') {{
    $encodedClientName = $matches[1]
    $clientName = [System.Uri]::UnescapeDataString($encodedClientName)
    $filename = "$clientName.msi"
}} elseif ($path -match '([^/]+\\.msi)') {{
    $filename = $matches[1]
}} else {{
    $filename = "RMM_Agent_Setup.msi"
    Write-Host "⚠️ Could not parse filename from URL, using default" -ForegroundColor Yellow
}}

$tempFile = "$tempDir\\setup.temp"
$msiPath  = "$tempDir\\$filename"

try {{
    Invoke-WebRequest -Uri $url -OutFile $tempFile -UseBasicParsing
    if (Test-Path $msiPath) {{ Remove-Item $msiPath -Force }}
    Rename-Item $tempFile $filename -Force
    Write-Host "✅ Downloaded: $msiPath" -ForegroundColor Green
    Write-Host "   Size: $([math]::Round((Get-Item $msiPath).Length / 1MB, 1)) MB" -ForegroundColor Gray
}} catch {{
    Write-Host "❌ Download failed: $_" -ForegroundColor Red
    exit 1
}}

if (-not $doInstall) {{
    Write-Host ""
    Write-Host "📁 Download complete (install skipped)" -ForegroundColor Cyan
    Write-Host "   File: $msiPath" -ForegroundColor Gray
    exit 0
}}

# ── Install ──
Write-Host ""
Write-Host "⚡ Installing..." -ForegroundColor Yellow
Start-Transcript -Path $scriptLog -Append | Out-Null

try {{
    $msiArgs = "/i `"$msiPath`" {silent_flag} /norestart"
    if ("{log_flag}") {{ $msiArgs += " {log_flag}" }}
    
    $proc = Start-Process msiexec.exe -ArgumentList $msiArgs -Wait -PassThru -NoNewWindow
    $exitCode = $proc.ExitCode

    Write-Host ""
    if ($exitCode -eq 0) {{
        Write-Host "✅ Installed successfully! (ExitCode: 0)" -ForegroundColor Green
    }} elseif ($exitCode -eq 3010) {{
        Write-Host "✅ Installed successfully! (Reboot required, ExitCode: 3010)" -ForegroundColor Yellow
    }} else {{
        Write-Host "❌ Install failed (ExitCode: $exitCode)" -ForegroundColor Red
        if (Test-Path $msiLog) {{
            Write-Host "   Check log: $msiLog" -ForegroundColor Gray
        }}
    }}
}} catch {{
    Write-Host "❌ Install error: $_" -ForegroundColor Red
}} finally {{
    Stop-Transcript | Out-Null
}}

# ── Cleanup ──
if ($doCleanup -and (Test-Path $msiPath)) {{
    Remove-Item $msiPath -Force
    Write-Host "🧹 Cleaned up: $msiPath" -ForegroundColor Gray
}}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
if (Test-Path $msiLog) {{ Write-Host "MSI Log: $msiLog" -ForegroundColor Gray }}
Write-Host "Script Log: $scriptLog" -ForegroundColor Gray
'''
        return script
    
    def _run_install(self):
        """Download and install."""
        url = self._get_url()
        if not url:
            return
        
        _save_url(url)
        script = self._build_script(url, download_only=False)
        
        if self.app:
            self.app.log(f"📥 RMM Install: {url}")
            self.app.powershell.run(script, "RMM Agent Install", interactive=True)
        
        self.status_var.set(f"Installing from: {url[:60]}...")
    
    def _run_download_only(self):
        """Download only, no install."""
        url = self._get_url()
        if not url:
            return
        
        _save_url(url)
        script = self._build_script(url, download_only=True)
        
        if self.app:
            self.app.log(f"📥 RMM Download: {url}")
            self.app.powershell.run(script, "RMM Agent Download", interactive=True)
        
        self.status_var.set(f"Downloading from: {url[:60]}...")
    
    def _clear_history(self):
        """Clear saved URL history."""
        try:
            if os.path.exists(CONFIG_FILE):
                os.remove(CONFIG_FILE)
            if hasattr(self, 'url_combo'):
                self.url_combo['values'] = []
            self.status_var.set("History cleared")
        except:
            pass


def open_rmm_installer(parent_root, app=None):
    """Launch the RMM installer as a popup window."""
    RMMInstallerWindow(parent_root, app)