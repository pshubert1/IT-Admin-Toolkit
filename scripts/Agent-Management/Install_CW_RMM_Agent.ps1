# NAME: 📥 Install CW RMM Agent
# DESCRIPTION: Download & install ConnectWise RMM agent from URL (prompts for URL)
# STYLE: Warning.TButton
# INTERACTIVE: true

# ============================================================
#  ConnectWise RMM Agent MSI Installer
# ============================================================

#Requires -RunAsAdministrator

$logDir = "C:\Temp"
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$logFile = Join-Path $logDir "CW_RMM_Install_${timestamp}.log"
$msiLog = Join-Path $logDir "CW_RMM_Install_MSI_${timestamp}.log"
$scriptLog = Join-Path $logDir "CW_RMM_Install_Transcript_${timestamp}.log"

if (!(Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $entry = "[$ts] [$Level] $Message"
    Write-Host $entry -ForegroundColor $(switch ($Level) {
        "ERROR"   { "Red" }
        "WARN"    { "Yellow" }
        "SUCCESS" { "Green" }
        "HEADER"  { "Cyan" }
        default   { "White" }
    })
    Add-Content -Path $logFile -Value $entry
}

Write-Log "==========================================" "HEADER"
Write-Log "  CW RMM AGENT INSTALLER" "HEADER"
Write-Log "==========================================" "HEADER"
Write-Log "  Computer:  $env:COMPUTERNAME"
Write-Log "  User:      $env:USERNAME"
Write-Log "  Log:       $logFile"
Write-Log "==========================================" "HEADER"
Write-Log ""

# ── Prompt for URL ──
Write-Host ""
Write-Host "  Paste the CW RMM agent download URL below." -ForegroundColor Cyan
Write-Host "  Example: https://prod.setup.itsupport247.net/Client/..." -ForegroundColor Gray
Write-Host ""

$url = Read-Host "  URL"

if ([string]::IsNullOrWhiteSpace($url)) {
    Write-Log "No URL entered - exiting" "ERROR"
    Read-Host "Press Enter to close"
    exit 1
}

if ($url -notmatch '^https?://') {
    Write-Log "Invalid URL (must start with http:// or https://)" "ERROR"
    Read-Host "Press Enter to close"
    exit 1
}

Write-Log "URL: $url"
Write-Log ""

# ── Parse filename from URL ──
Write-Log "Parsing download URL..." "INFO"

$uri = [System.Uri]$url
$path = $uri.AbsolutePath

if ($path -match '/32/([^/]+)/MSI') {
    $encodedClientName = $matches[1]
    $clientName = [System.Uri]::UnescapeDataString($encodedClientName)
    $filename = "$clientName.msi"
    Write-Log "Client name: $clientName" "SUCCESS"
} elseif ($path -match '([^/]+\.msi)') {
    $filename = $matches[1]
    Write-Log "Filename from URL: $filename" "SUCCESS"
} else {
    $filename = "CW_RMM_Agent_Setup.msi"
    Write-Log "Could not parse filename - using default: $filename" "WARN"
}

$tempFile = Join-Path $logDir "setup.temp"
$msiPath = Join-Path $logDir $filename

Write-Log "MSI will save to: $msiPath"
Write-Log ""

# ── Download ──
Write-Log "Downloading agent..." "WARN"

try {
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    Invoke-WebRequest -Uri $url -OutFile $tempFile -UseBasicParsing -ErrorAction Stop
    $stopwatch.Stop()
    
    if (Test-Path $msiPath) { Remove-Item $msiPath -Force }
    Rename-Item $tempFile $filename -Force
    
    $fileSize = [math]::Round((Get-Item $msiPath).Length / 1MB, 1)
    $elapsed = $stopwatch.Elapsed.ToString("mm\:ss")
    
    Write-Log "Downloaded: $msiPath ($fileSize MB in $elapsed)" "SUCCESS"
} catch {
    Write-Log "Download failed: $_" "ERROR"
    
    # Clean up temp file
    if (Test-Path $tempFile) { Remove-Item $tempFile -Force -ErrorAction SilentlyContinue }
    
    Write-Log ""
    Read-Host "Press Enter to close"
    exit 1
}

# ── Confirm install ──
Write-Host ""
$confirm = Read-Host "  Proceed with install? (Y/N)"
if ($confirm -ne 'Y' -and $confirm -ne 'y') {
    Write-Log "Install cancelled by user" "WARN"
    Write-Log "MSI saved at: $msiPath"
    Read-Host "Press Enter to close"
    exit 0
}

# ── Install ──
Write-Log "" "HEADER"
Write-Log "Installing agent..." "WARN"
Write-Log "  MSI:     $msiPath"
Write-Log "  MSI Log: $msiLog"
Write-Log ""

Start-Transcript -Path $scriptLog -Append | Out-Null

try {
    $msiArgs = "/i `"$msiPath`" /qn /norestart /l*v `"$msiLog`""
    Write-Log "Running: msiexec.exe $msiArgs"
    
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    $proc = Start-Process msiexec.exe -ArgumentList $msiArgs -Wait -PassThru -NoNewWindow
    $stopwatch.Stop()
    
    $exitCode = $proc.ExitCode
    $elapsed = $stopwatch.Elapsed.ToString("mm\:ss")
    
    Write-Log ""
    switch ($exitCode) {
        0 {
            Write-Log "Installed successfully (ExitCode: 0, Time: $elapsed)" "SUCCESS"
        }
        3010 {
            Write-Log "Installed successfully - REBOOT REQUIRED (ExitCode: 3010, Time: $elapsed)" "SUCCESS"
        }
        1602 {
            Write-Log "Install was cancelled (ExitCode: 1602)" "WARN"
        }
        1603 {
            Write-Log "Fatal error during install (ExitCode: 1603)" "ERROR"
            Write-Log "Check MSI log: $msiLog" "ERROR"
        }
        1618 {
            Write-Log "Another install is in progress (ExitCode: 1618)" "ERROR"
            Write-Log "Wait for other installs to finish, then retry" "WARN"
        }
        default {
            Write-Log "Install finished with ExitCode: $exitCode (Time: $elapsed)" "ERROR"
            Write-Log "Check MSI log: $msiLog" "ERROR"
        }
    }
} catch {
    Write-Log "Install exception: $_" "ERROR"
} finally {
    Stop-Transcript | Out-Null
}

# ── Verify ──
Write-Log ""
Write-Log "Verifying installation..." "INFO"
Start-Sleep -Seconds 5

$installed = Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*",
    "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*" -ErrorAction SilentlyContinue |
    Where-Object { $_.DisplayName -match "ITSPlatform|ConnectWise|CW RMM|SAAZOD" }

if ($installed) {
    foreach ($app in $installed) {
        Write-Log "  Found: $($app.DisplayName) v$($app.DisplayVersion)" "SUCCESS"
    }
} else {
    Write-Log "  Agent not yet visible in registry (may need a moment or reboot)" "WARN"
}

$svc = Get-Service -Name "ITSPlatform" -ErrorAction SilentlyContinue
if ($svc) {
    Write-Log "  Service: $($svc.Name) - $($svc.Status)" "SUCCESS"
} else {
    Write-Log "  Service not found yet (may take a minute to register)" "WARN"
}

# ── Summary ──
Write-Log ""
Write-Log "==========================================" "HEADER"
Write-Log "  COMPLETE" "HEADER"
Write-Log "==========================================" "HEADER"
Write-Log "  Script Log:     $logFile"
Write-Log "  MSI Log:        $msiLog"
Write-Log "  Transcript:     $scriptLog"
Write-Log "  MSI Location:   $msiPath"
Write-Log "==========================================" "HEADER"
Write-Log ""

Read-Host "Press Enter to close"