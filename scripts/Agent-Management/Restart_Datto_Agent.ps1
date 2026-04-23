# NAME: 🔄 Restart Datto Backup Agent
# DESCRIPTION: Restart the DattoBackupAgentService with status logging
# STYLE: Warning.TButton
# INTERACTIVE: true

# ============================================================
#  Restart Datto Backup Agent Service
# ============================================================

#Requires -RunAsAdministrator

$serviceName = "DattoBackupAgentService"
$logDir = "C:\Temp"
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$logFile = Join-Path $logDir "Restart_Datto_${timestamp}.log"

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
Write-Log "  RESTART DATTO BACKUP AGENT" "HEADER"
Write-Log "  Computer:  $env:COMPUTERNAME"
Write-Log "  User:      $env:USERNAME"
Write-Log "  Log:       $logFile"
Write-Log "==========================================" "HEADER"
Write-Log ""

# ── Check if service exists ──
$svc = Get-Service -Name $serviceName -ErrorAction SilentlyContinue

if (-not $svc) {
    Write-Log "Service '$serviceName' not found on this computer" "ERROR"
    Write-Log ""
    
    # Check for similar services
    Write-Log "Searching for Datto-related services..." "INFO"
    $dattoServices = Get-Service -ErrorAction SilentlyContinue | 
        Where-Object { $_.Name -match 'Datto' -or $_.DisplayName -match 'Datto' }
    
    if ($dattoServices) {
        Write-Log "Found these Datto services:" "WARN"
        foreach ($ds in $dattoServices) {
            Write-Log "  - $($ds.Name) ($($ds.DisplayName)) [$($ds.Status)]" "INFO"
        }
    } else {
        Write-Log "No Datto services found - agent may not be installed" "ERROR"
    }
    
    Write-Log ""
    Read-Host "Press Enter to close"
    exit 1
}

# ── Show current status ──
Write-Log "Service Found:" "SUCCESS"
Write-Log "  Name:         $($svc.Name)"
Write-Log "  Display Name: $($svc.DisplayName)"
Write-Log "  Status:       $($svc.Status)"
Write-Log "  Start Type:   $($svc.StartType)"
Write-Log ""

# ── Also find dependent/related Datto services ──
$allDattoServices = Get-Service -ErrorAction SilentlyContinue | 
    Where-Object { $_.Name -match 'Datto' -or $_.DisplayName -match 'Datto' }

if ($allDattoServices.Count -gt 1) {
    Write-Log "All Datto services on this machine:" "HEADER"
    foreach ($ds in $allDattoServices) {
        Write-Log "  $($ds.Name) ($($ds.DisplayName)) - $($ds.Status)" "INFO"
    }
    Write-Log ""
    
    $restartAll = Read-Host "  Restart ALL Datto services? (Y = all, N = just $serviceName)"
    
    if ($restartAll -eq 'Y' -or $restartAll -eq 'y') {
        $servicesToRestart = $allDattoServices
    } else {
        $servicesToRestart = @($svc)
    }
} else {
    $servicesToRestart = @($svc)
}

# ── Restart ──
foreach ($service in $servicesToRestart) {
    Write-Log "----------------------------------------------" "HEADER"
    Write-Log "Restarting: $($service.Name) ($($service.DisplayName))..." "WARN"
    
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    
    try {
        # Stop
        if ($service.Status -ne 'Stopped') {
            Write-Log "  Stopping..." "WARN"
            Stop-Service -Name $service.Name -Force -ErrorAction Stop
            $service.WaitForStatus('Stopped', '00:00:30')
            Write-Log "  Stopped" "SUCCESS"
        } else {
            Write-Log "  Already stopped" "INFO"
        }
        
        # Small delay
        Start-Sleep -Seconds 2
        
        # Start
        Write-Log "  Starting..." "WARN"
        Start-Service -Name $service.Name -ErrorAction Stop
        $service.WaitForStatus('Running', '00:00:30')
        
        $stopwatch.Stop()
        $elapsed = $stopwatch.Elapsed.ToString("mm\:ss")
        
        # Verify
        $check = Get-Service -Name $service.Name
        if ($check.Status -eq 'Running') {
            Write-Log "  Running! (took $elapsed)" "SUCCESS"
        } else {
            Write-Log "  Status: $($check.Status) (expected Running)" "WARN"
        }
        
    } catch {
        $stopwatch.Stop()
        Write-Log "  Failed: $_" "ERROR"
        
        # Try net stop/start as fallback
        Write-Log "  Trying fallback (net stop/start)..." "WARN"
        try {
            net stop $service.Name 2>&1 | Out-Null
            Start-Sleep -Seconds 3
            net start $service.Name 2>&1 | Out-Null
            
            $recheck = Get-Service -Name $service.Name
            if ($recheck.Status -eq 'Running') {
                Write-Log "  Fallback succeeded - Running" "SUCCESS"
            } else {
                Write-Log "  Fallback result: $($recheck.Status)" "ERROR"
            }
        } catch {
            Write-Log "  Fallback also failed: $_" "ERROR"
        }
    }
    
    Write-Log ""
}

# ── Final status ──
Write-Log "==========================================" "HEADER"
Write-Log "  FINAL STATUS" "HEADER"
Write-Log "==========================================" "HEADER"

$finalServices = Get-Service -ErrorAction SilentlyContinue | 
    Where-Object { $_.Name -match 'Datto' -or $_.DisplayName -match 'Datto' }

foreach ($fs in $finalServices) {
    $level = if ($fs.Status -eq 'Running') { "SUCCESS" } else { "ERROR" }
    Write-Log "  $($fs.Name): $($fs.Status)" $level
}

Write-Log ""
Write-Log "  Log: $logFile"
Write-Log "==========================================" "HEADER"
Write-Log ""

Read-Host "Press Enter to close"