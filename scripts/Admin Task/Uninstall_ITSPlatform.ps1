# NAME: 🗑️ Uninstall ITSPlatform
# DESCRIPTION: Uninstall CW RMM Agent with full logging to C:\Temp
# STYLE: Danger.TButton
# INTERACTIVE: true


# ============================================================
#  Uninstall ITSPlatform (CW RMM Agent) with Full Logging
# ============================================================

$apps = "ITSPlatform"
$logDir = "C:\Temp"
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$logFile = Join-Path $logDir "Uninstall_${apps}_${timestamp}.log"

# Ensure log directory exists
if (!(Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $entry = "[$ts] [$Level] $Message"
    Write-Host $entry -ForegroundColor $(switch ($Level) {
        "ERROR"   { "Red" }
        "WARN"    { "Yellow" }
        "SUCCESS" { "Green" }
        default   { "White" }
    })
    Add-Content -Path $logFile -Value $entry
}

Write-Log "=========================================="
Write-Log "  Uninstall: $apps"
Write-Log "  Computer:  $env:COMPUTERNAME"
Write-Log "  User:      $env:USERNAME"
Write-Log "  Log:       $logFile"
Write-Log "=========================================="
Write-Log ""

# ── Find matching apps in registry ──
Write-Log "Searching registry for '$apps'..."

$regPaths = @(
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
    "HKLM:\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
)

$found = @()
foreach ($regPath in $regPaths) {
    try {
        $entries = Get-ChildItem -Path $regPath -ErrorAction SilentlyContinue |
            Get-ItemProperty -ErrorAction SilentlyContinue |
            Where-Object { $_.DisplayName -match $apps }
        
        foreach ($entry in $entries) {
            $found += [PSCustomObject]@{
                DisplayName     = $entry.DisplayName
                Version         = $entry.DisplayVersion
                Publisher       = $entry.Publisher
                UninstallString = $entry.UninstallString
                QuietUninstall  = $entry.QuietUninstallString
                InstallDate     = $entry.InstallDate
                RegPath         = $entry.PSPath
                GUID            = if ($entry.PSChildName -match '^\{') { $entry.PSChildName } else { $null }
            }
        }
    } catch {
        Write-Log "Error reading $regPath : $_" "WARN"
    }
}

if ($found.Count -eq 0) {
    Write-Log "'$apps' not found in registry - nothing to uninstall" "WARN"
    Write-Log ""
    Write-Log "Done."
    Read-Host "Press Enter to close"
    exit 0
}

Write-Log "Found $($found.Count) matching installation(s):"
Write-Log ""

foreach ($app in $found) {
    Write-Log "  Name:      $($app.DisplayName)"
    Write-Log "  Version:   $($app.Version)"
    Write-Log "  Publisher: $($app.Publisher)"
    Write-Log "  GUID:      $($app.GUID)"
    Write-Log "  Uninstall: $($app.UninstallString)"
    Write-Log ""
}

# ── Uninstall each ──
$successCount = 0
$failCount = 0

foreach ($app in $found) {
    Write-Log "----------------------------------------------"
    Write-Log "Uninstalling: $($app.DisplayName) $($app.Version)"
    
    if (-not $app.UninstallString) {
        Write-Log "No uninstall string found, skipping" "WARN"
        $failCount++
        continue
    }
    
    $uninst = $app.UninstallString
    $msiLogFile = Join-Path $logDir "MSI_Uninstall_${apps}_${timestamp}.log"
    
    try {
        if ($uninst -match 'msiexec' -or $app.GUID) {
            # ── MSI uninstall ──
            if ($app.GUID) {
                $msiArgs = "/x `"$($app.GUID)`" /qn /norestart /l*v `"$msiLogFile`""
            } else {
                $cleanCmd = $uninst -replace '(?i)msiexec\.exe\s*', '' -replace '/I', '/x'
                $msiArgs = "$cleanCmd /qn /norestart /l*v `"$msiLogFile`""
            }
            
            Write-Log "Running: msiexec.exe $msiArgs"
            $proc = Start-Process msiexec.exe -ArgumentList $msiArgs -Wait -PassThru -NoNewWindow
            $exitCode = $proc.ExitCode
            
        } else {
            # ── EXE uninstall ──
            if ($uninst -match '^"(.+?)"\s*(.*)$') {
                $exePath = $matches[1]
                $exeArgs = "$($matches[2]) /S /silent /quiet /norestart".Trim()
            } elseif ($uninst -match '^(\S+)\s*(.*)$') {
                $exePath = $matches[1]
                $exeArgs = "$($matches[2]) /S /silent /quiet /norestart".Trim()
            } else {
                $exePath = $uninst
                $exeArgs = "/S /silent /quiet /norestart"
            }
            
            Write-Log "Running: `"$exePath`" $exeArgs"
            $proc = Start-Process -FilePath $exePath -ArgumentList $exeArgs -Wait -PassThru -NoNewWindow
            $exitCode = $proc.ExitCode
        }
        
        # ── Check result ──
        switch ($exitCode) {
            0    { 
                Write-Log "Uninstalled successfully (ExitCode: 0)" "SUCCESS"
                $successCount++ 
            }
            3010 { 
                Write-Log "Uninstalled successfully - REBOOT REQUIRED (ExitCode: 3010)" "SUCCESS"
                $successCount++ 
            }
            1605 { 
                Write-Log "Product not found / already removed (ExitCode: 1605)" "WARN"
                $successCount++ 
            }
            1641 { 
                Write-Log "Uninstalled - reboot initiated by installer (ExitCode: 1641)" "SUCCESS"
                $successCount++ 
            }
            default { 
                Write-Log "Uninstall may have failed (ExitCode: $exitCode)" "ERROR"
                if (Test-Path $msiLogFile) {
                    Write-Log "MSI log saved: $msiLogFile" "INFO"
                }
                $failCount++ 
            }
        }
        
    } catch {
        Write-Log "Exception during uninstall: $_" "ERROR"
        $failCount++
    }
    
    Write-Log ""
}

# ── Verify removal ──
Write-Log "----------------------------------------------"
Write-Log "Verifying removal..."
Start-Sleep -Seconds 3

$remaining = @()
foreach ($regPath in $regPaths) {
    $remaining += Get-ChildItem -Path $regPath -ErrorAction SilentlyContinue |
        Get-ItemProperty -ErrorAction SilentlyContinue |
        Where-Object { $_.DisplayName -match $apps }
}

if ($remaining.Count -eq 0) {
    Write-Log "Verified: '$apps' no longer found in registry" "SUCCESS"
} else {
    Write-Log "$($remaining.Count) entries still found in registry:" "WARN"
    foreach ($r in $remaining) {
        Write-Log "  - $($r.DisplayName) ($($r.DisplayVersion))" "WARN"
    }
}

# ── Stop services if still running ──
Write-Log ""
Write-Log "Checking for leftover services..."
$services = Get-Service -ErrorAction SilentlyContinue | 
    Where-Object { $_.DisplayName -match $apps -or $_.Name -match 'ITSPlatform' }

foreach ($svc in $services) {
    Write-Log "Stopping service: $($svc.Name) ($($svc.Status))" "WARN"
    try {
        Stop-Service -Name $svc.Name -Force -ErrorAction Stop
        Write-Log "  Stopped: $($svc.Name)" "SUCCESS"
    } catch {
        Write-Log "  Could not stop: $_" "ERROR"
    }
}
if (-not $services) { Write-Log "No leftover services found" "SUCCESS" }

# ── Summary ──
Write-Log ""
Write-Log "=========================================="
Write-Log "  UNINSTALL COMPLETE"
Write-Log "  Success: $successCount  |  Failed: $failCount"
Write-Log "  Log: $logFile"
if (Test-Path $msiLogFile) { Write-Log "  MSI Log: $msiLogFile" }
Write-Log "=========================================="
Write-Log ""

Read-Host "Press Enter to close"