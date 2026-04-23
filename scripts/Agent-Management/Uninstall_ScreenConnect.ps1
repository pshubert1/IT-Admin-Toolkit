# NAME: 🗑️ Uninstall ScreenConnect
# DESCRIPTION: Uninstall ConnectWise ScreenConnect/Control with full logging to C:\Temp
# STYLE: Danger.TButton
# INTERACTIVE: true

# ============================================================
#  Uninstall ScreenConnect (ConnectWise Control) with Logging
# ============================================================

$searchTerms = @("ScreenConnect", "ConnectWise Control")
$logDir = "C:\Temp"
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$logFile = Join-Path $logDir "Uninstall_ScreenConnect_${timestamp}.log"

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
Write-Log "  Uninstall: ScreenConnect / CW Control"
Write-Log "  Computer:  $env:COMPUTERNAME"
Write-Log "  User:      $env:USERNAME"
Write-Log "  Log:       $logFile"
Write-Log "=========================================="
Write-Log ""

# ── Find matching apps in registry ──
Write-Log "Searching registry..."

$regPaths = @(
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
    "HKLM:\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
)

$found = @()
foreach ($regPath in $regPaths) {
    try {
        $entries = Get-ChildItem -Path $regPath -ErrorAction SilentlyContinue |
            Get-ItemProperty -ErrorAction SilentlyContinue |
            Where-Object { 
                $dn = $_.DisplayName
                $pub = $_.Publisher
                if (!$dn) { return $false }
                foreach ($term in $searchTerms) {
                    if ($dn -match $term -or ($pub -and $pub -match $term)) { return $true }
                }
                return $false
            }
        
        foreach ($entry in $entries) {
            # Skip duplicates by checking UninstallString
            $isDupe = $found | Where-Object { $_.UninstallString -eq $entry.UninstallString -and $_.DisplayName -eq $entry.DisplayName }
            if ($isDupe) { continue }
            
            $found += [PSCustomObject]@{
                DisplayName     = $entry.DisplayName
                Version         = $entry.DisplayVersion
                Publisher       = $entry.Publisher
                UninstallString = $entry.UninstallString
                QuietUninstall  = $entry.QuietUninstallString
                InstallDate     = $entry.InstallDate
                InstallLocation = $entry.InstallLocation
                RegPath         = $entry.PSPath
                GUID            = if ($entry.PSChildName -match '^\{') { $entry.PSChildName } else { $null }
            }
        }
    } catch {
        Write-Log "Error reading $regPath : $_" "WARN"
    }
}

if ($found.Count -eq 0) {
    Write-Log "ScreenConnect / ConnectWise Control not found in registry" "WARN"
    Write-Log ""
    Write-Log "Checking for leftover services and folders anyway..."
} else {
    Write-Log "Found $($found.Count) matching installation(s):"
    Write-Log ""
    
    foreach ($app in $found) {
        Write-Log "  Name:      $($app.DisplayName)"
        Write-Log "  Version:   $($app.Version)"
        Write-Log "  Publisher: $($app.Publisher)"
        Write-Log "  GUID:      $($app.GUID)"
        Write-Log "  Location:  $($app.InstallLocation)"
        Write-Log "  Uninstall: $($app.UninstallString)"
        Write-Log ""
    }
}

# ── Stop ScreenConnect services first ──
Write-Log "----------------------------------------------"
Write-Log "Stopping ScreenConnect services..."

$scServices = Get-Service -ErrorAction SilentlyContinue | 
    Where-Object { $_.Name -match 'ScreenConnect' -or $_.DisplayName -match 'ScreenConnect' -or
                   $_.Name -match 'ConnectWise Control' -or $_.DisplayName -match 'ConnectWise Control' }

foreach ($svc in $scServices) {
    Write-Log "  Stopping: $($svc.Name) ($($svc.DisplayName)) - Status: $($svc.Status)"
    try {
        if ($svc.Status -ne 'Stopped') {
            Stop-Service -Name $svc.Name -Force -ErrorAction Stop
            Start-Sleep -Seconds 2
        }
        Write-Log "  Stopped: $($svc.Name)" "SUCCESS"
    } catch {
        Write-Log "  Could not stop $($svc.Name): $_" "ERROR"
        # Try killing the process directly
        try {
            $scProcs = Get-Process -ErrorAction SilentlyContinue | 
                Where-Object { $_.Name -match 'ScreenConnect' }
            foreach ($proc in $scProcs) {
                Write-Log "  Force killing process: $($proc.Name) (PID: $($proc.Id))" "WARN"
                Stop-Process -Id $proc.Id -Force
            }
        } catch {
            Write-Log "  Could not kill process: $_" "ERROR"
        }
    }
}
if (-not $scServices) { Write-Log "  No ScreenConnect services found" "INFO" }

# ── Kill any remaining ScreenConnect processes ──
Write-Log ""
Write-Log "Checking for running processes..."
$scProcs = Get-Process -ErrorAction SilentlyContinue | 
    Where-Object { $_.Name -match 'ScreenConnect' -or $_.Name -match 'ConnectWiseControl' }

foreach ($proc in $scProcs) {
    Write-Log "  Killing: $($proc.Name) (PID: $($proc.Id))" "WARN"
    try {
        Stop-Process -Id $proc.Id -Force
        Write-Log "  Killed: $($proc.Name)" "SUCCESS"
    } catch {
        Write-Log "  Could not kill $($proc.Name): $_" "ERROR"
    }
}
if (-not $scProcs) { Write-Log "  No running processes found" "INFO" }

# ── Uninstall each found entry ──
$successCount = 0
$failCount = 0

foreach ($app in $found) {
    Write-Log ""
    Write-Log "----------------------------------------------"
    Write-Log "Uninstalling: $($app.DisplayName) $($app.Version)"
    
    if (-not $app.UninstallString) {
        Write-Log "No uninstall string found, skipping" "WARN"
        $failCount++
        continue
    }
    
    $uninst = $app.UninstallString
    $msiLogFile = Join-Path $logDir "MSI_Uninstall_ScreenConnect_${timestamp}.log"
    
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
            
            if (Test-Path $exePath) {
                $proc = Start-Process -FilePath $exePath -ArgumentList $exeArgs -Wait -PassThru -NoNewWindow
                $exitCode = $proc.ExitCode
            } else {
                Write-Log "Uninstaller not found at: $exePath" "ERROR"
                $failCount++
                continue
            }
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
                Write-Log "Uninstalled - reboot initiated (ExitCode: 1641)" "SUCCESS"
                $successCount++ 
            }
            default { 
                Write-Log "Uninstall may have failed (ExitCode: $exitCode)" "ERROR"
                if (Test-Path $msiLogFile) {
                    Write-Log "MSI log: $msiLogFile" "INFO"
                }
                $failCount++ 
            }
        }
        
    } catch {
        Write-Log "Exception during uninstall: $_" "ERROR"
        $failCount++
    }
}

# ── Clean up leftover folders ──
Write-Log ""
Write-Log "----------------------------------------------"
Write-Log "Cleaning up leftover files..."

$cleanupPaths = @(
    "$env:ProgramFiles\ScreenConnect Client*",
    "$env:ProgramFiles(x86)\ScreenConnect Client*",
    "$env:ProgramFiles\ConnectWise Control*",
    "$env:ProgramFiles(x86)\ConnectWise Control*",
    "$env:ProgramData\ScreenConnect Client*",
    "$env:ProgramData\ConnectWise Control*"
)

foreach ($pattern in $cleanupPaths) {
    $matches2 = Get-Item -Path $pattern -ErrorAction SilentlyContinue
    foreach ($folder in $matches2) {
        try {
            Remove-Item -Path $folder.FullName -Recurse -Force -ErrorAction Stop
            Write-Log "  Removed: $($folder.FullName)" "SUCCESS"
        } catch {
            Write-Log "  Could not remove $($folder.FullName): $_" "WARN"
        }
    }
}

# ── Remove leftover services ──
Write-Log ""
Write-Log "Checking for leftover service registrations..."
$leftoverSvcs = Get-Service -ErrorAction SilentlyContinue | 
    Where-Object { $_.Name -match 'ScreenConnect' -or $_.DisplayName -match 'ScreenConnect' -or
                   $_.Name -match 'ConnectWise Control' -or $_.DisplayName -match 'ConnectWise Control' }

foreach ($svc in $leftoverSvcs) {
    Write-Log "  Removing service: $($svc.Name)" "WARN"
    try {
        sc.exe delete $svc.Name | Out-Null
        Write-Log "  Removed: $($svc.Name)" "SUCCESS"
    } catch {
        Write-Log "  Could not remove $($svc.Name): $_" "ERROR"
    }
}
if (-not $leftoverSvcs) { Write-Log "  No leftover services" "SUCCESS" }

# ── Verify removal ──
Write-Log ""
Write-Log "----------------------------------------------"
Write-Log "Verifying removal..."
Start-Sleep -Seconds 3

$remaining = @()
foreach ($regPath in $regPaths) {
    $remaining += Get-ChildItem -Path $regPath -ErrorAction SilentlyContinue |
        Get-ItemProperty -ErrorAction SilentlyContinue |
        Where-Object { 
            $dn = $_.DisplayName
            if (!$dn) { return $false }
            foreach ($term in $searchTerms) { if ($dn -match $term) { return $true } }
            return $false
        }
}

if ($remaining.Count -eq 0) {
    Write-Log "Verified: ScreenConnect no longer found in registry" "SUCCESS"
} else {
    Write-Log "$($remaining.Count) entries still in registry:" "WARN"
    foreach ($r in $remaining) {
        Write-Log "  - $($r.DisplayName) ($($r.DisplayVersion))" "WARN"
    }
}

# ── Summary ──
Write-Log ""
Write-Log "=========================================="
Write-Log "  SCREENCONNECT UNINSTALL COMPLETE"
Write-Log "  Success: $successCount  |  Failed: $failCount"
Write-Log "  Log: $logFile"
if (Test-Path $msiLogFile) { Write-Log "  MSI Log: $msiLogFile" }
Write-Log "=========================================="
Write-Log ""

Read-Host "Press Enter to close"