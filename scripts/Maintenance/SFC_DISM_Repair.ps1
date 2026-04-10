# NAME: 🔧 SFC & DISM Full Repair
# DESCRIPTION: Runs all SFC and DISM repair/cleanup commands with logging to C:\Temp
# STYLE: Warning.TButton
# INTERACTIVE: true

# ============================================================
#  SFC & DISM Full System Repair Suite
#  Runs all repair + cleanup variants with full logging
# ============================================================

#Requires -RunAsAdministrator

$logDir = "C:\Temp"
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$logFile = Join-Path $logDir "SFC_DISM_Repair_${timestamp}.log"
$cbsLog = "$env:WinDir\Logs\CBS\CBS.log"
$dismLog = Join-Path $logDir "DISM_${timestamp}.log"

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
        "HEADER"  { "Cyan" }
        default   { "White" }
    })
    Add-Content -Path $logFile -Value $entry
}

function Run-Step {
    param(
        [string]$StepName,
        [string]$Command,
        [string[]]$Arguments,
        [int]$TimeoutMinutes = 60
    )
    
    Write-Log "" "INFO"
    Write-Log "==========================================" "HEADER"
    Write-Log "  STEP: $StepName" "HEADER"
    Write-Log "==========================================" "HEADER"
    Write-Log "Command: $Command $($Arguments -join ' ')"
    Write-Log "Timeout: $TimeoutMinutes minutes"
    Write-Log ""
    
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    
    try {
        $proc = Start-Process -FilePath $Command -ArgumentList $Arguments `
            -Wait -PassThru -NoNewWindow -RedirectStandardOutput "$logDir\temp_stdout.txt" `
            -RedirectStandardError "$logDir\temp_stderr.txt"
        
        $stopwatch.Stop()
        $elapsed = $stopwatch.Elapsed.ToString("mm\:ss")
        
        # Read output
        $stdout = ""
        $stderr = ""
        if (Test-Path "$logDir\temp_stdout.txt") {
            $stdout = Get-Content "$logDir\temp_stdout.txt" -Raw -ErrorAction SilentlyContinue
            Remove-Item "$logDir\temp_stdout.txt" -Force -ErrorAction SilentlyContinue
        }
        if (Test-Path "$logDir\temp_stderr.txt") {
            $stderr = Get-Content "$logDir\temp_stderr.txt" -Raw -ErrorAction SilentlyContinue
            Remove-Item "$logDir\temp_stderr.txt" -Force -ErrorAction SilentlyContinue
        }
        
        # Show output
        if ($stdout) {
            Write-Log "--- Output ---"
            foreach ($line in ($stdout -split "`n")) {
                $trimmed = $line.Trim()
                if ($trimmed) { Write-Log "  $trimmed" }
            }
            Write-Log "--- End Output ---"
        }
        
        $exitCode = $proc.ExitCode
        Write-Log ""
        Write-Log "Exit Code: $exitCode | Time: $elapsed"
        
        switch ($exitCode) {
            0 {
                Write-Log "$StepName completed successfully" "SUCCESS"
                return $true
            }
            1 {
                Write-Log "$StepName found issues but could not fix all of them" "WARN"
                return $false
            }
            2 {
                Write-Log "$StepName was cancelled or could not complete" "WARN"
                return $false
            }
            87 {
                Write-Log "$StepName - invalid parameter (check Windows version)" "ERROR"
                return $false
            }
            default {
                Write-Log "$StepName finished with code $exitCode" "WARN"
                if ($stderr) { Write-Log "Errors: $stderr" "ERROR" }
                return ($exitCode -eq 0)
            }
        }
        
    } catch {
        $stopwatch.Stop()
        Write-Log "Exception running $StepName : $_" "ERROR"
        return $false
    }
}

# ── Header ──
Write-Log "==========================================" "HEADER"
Write-Log "  SFC & DISM FULL REPAIR SUITE" "HEADER"
Write-Log "==========================================" "HEADER"
Write-Log "  Computer:  $env:COMPUTERNAME"
Write-Log "  User:      $env:USERNAME"
Write-Log "  OS:        $((Get-CimInstance Win32_OperatingSystem).Caption)"
Write-Log "  Build:     $((Get-CimInstance Win32_OperatingSystem).BuildNumber)"
Write-Log "  Log:       $logFile"
Write-Log "  DISM Log:  $dismLog"
Write-Log "==========================================" "HEADER"
Write-Log ""

$overallStart = [System.Diagnostics.Stopwatch]::StartNew()
$results = @{}

# ============================================================
#  PHASE 1: DISM HEALTH CHECKS
# ============================================================

Write-Log "" "HEADER"
Write-Log "############################################" "HEADER"
Write-Log "  PHASE 1: DISM HEALTH CHECKS" "HEADER"
Write-Log "############################################" "HEADER"

# ── 1a: DISM CheckHealth (quick check) ──
$results["DISM CheckHealth"] = Run-Step `
    -StepName "DISM CheckHealth (Quick)" `
    -Command "DISM.exe" `
    -Arguments "/Online", "/Cleanup-Image", "/CheckHealth", "/LogPath:$dismLog" `
    -TimeoutMinutes 5

# ── 1b: DISM ScanHealth (deeper scan) ──
$results["DISM ScanHealth"] = Run-Step `
    -StepName "DISM ScanHealth (Deep Scan)" `
    -Command "DISM.exe" `
    -Arguments "/Online", "/Cleanup-Image", "/ScanHealth", "/LogPath:$dismLog" `
    -TimeoutMinutes 30

# ============================================================
#  PHASE 2: DISM REPAIRS
# ============================================================

Write-Log "" "HEADER"
Write-Log "############################################" "HEADER"
Write-Log "  PHASE 2: DISM REPAIRS" "HEADER"
Write-Log "############################################" "HEADER"

# ── 2a: DISM RestoreHealth (standard - uses Windows Update) ──
$results["DISM RestoreHealth"] = Run-Step `
    -StepName "DISM RestoreHealth (Windows Update Source)" `
    -Command "DISM.exe" `
    -Arguments "/Online", "/Cleanup-Image", "/RestoreHealth", "/LogPath:$dismLog" `
    -TimeoutMinutes 60

# ── 2b: DISM RestoreHealth with limited source (fallback if WU blocked) ──
if (-not $results["DISM RestoreHealth"]) {
    Write-Log ""
    Write-Log "Standard RestoreHealth had issues, trying with /Source:WIM fallback..." "WARN"
    
    # Check if install.wim exists (mounted ISO or recovery)
    $wimPaths = @(
        "D:\sources\install.wim",
        "E:\sources\install.wim",
        "$env:SystemDrive\sources\install.wim"
    )
    
    $wimPath = $null
    foreach ($path in $wimPaths) {
        if (Test-Path $path) {
            $wimPath = $path
            break
        }
    }
    
    if ($wimPath) {
        Write-Log "Found install.wim at: $wimPath" "INFO"
        $results["DISM RestoreHealth WIM"] = Run-Step `
            -StepName "DISM RestoreHealth (WIM Source)" `
            -Command "DISM.exe" `
            -Arguments "/Online", "/Cleanup-Image", "/RestoreHealth", "/Source:WIM:${wimPath}:1", "/LimitAccess", "/LogPath:$dismLog" `
            -TimeoutMinutes 60
    } else {
        Write-Log "No install.wim found - skipping WIM fallback" "INFO"
        Write-Log "  (Mount a Windows ISO to D: or E: if needed)" "INFO"
    }
}

# ============================================================
#  PHASE 3: SFC SCAN (first pass)
# ============================================================

Write-Log "" "HEADER"
Write-Log "############################################" "HEADER"
Write-Log "  PHASE 3: SFC SCAN (First Pass)" "HEADER"
Write-Log "############################################" "HEADER"

$results["SFC Pass 1"] = Run-Step `
    -StepName "SFC /scannow (Pass 1)" `
    -Command "sfc.exe" `
    -Arguments "/scannow" `
    -TimeoutMinutes 30

# ============================================================
#  PHASE 4: SFC SECOND PASS (if first found issues)
# ============================================================

if (-not $results["SFC Pass 1"]) {
    Write-Log "" "HEADER"
    Write-Log "############################################" "HEADER"
    Write-Log "  PHASE 4: SFC SCAN (Second Pass)" "HEADER"
    Write-Log "############################################" "HEADER"
    Write-Log "First SFC pass found issues - running again..." "WARN"
    
    $results["SFC Pass 2"] = Run-Step `
        -StepName "SFC /scannow (Pass 2)" `
        -Command "sfc.exe" `
        -Arguments "/scannow" `
        -TimeoutMinutes 30
} else {
    Write-Log ""
    Write-Log "SFC Pass 1 clean - skipping second pass" "SUCCESS"
}

# ============================================================
#  PHASE 5: DISM CLEANUP & OPTIMIZATION
# ============================================================

Write-Log "" "HEADER"
Write-Log "############################################" "HEADER"
Write-Log "  PHASE 5: DISM CLEANUP & OPTIMIZATION" "HEADER"
Write-Log "############################################" "HEADER"

# ── 5a: Analyze Component Store ──
$results["DISM AnalyzeStore"] = Run-Step `
    -StepName "DISM AnalyzeComponentStore" `
    -Command "DISM.exe" `
    -Arguments "/Online", "/Cleanup-Image", "/AnalyzeComponentStore", "/LogPath:$dismLog" `
    -TimeoutMinutes 10

# ── 5b: StartComponentCleanup (remove superseded updates) ──
$results["DISM ComponentCleanup"] = Run-Step `
    -StepName "DISM StartComponentCleanup" `
    -Command "DISM.exe" `
    -Arguments "/Online", "/Cleanup-Image", "/StartComponentCleanup", "/LogPath:$dismLog" `
    -TimeoutMinutes 30

# ── 5c: StartComponentCleanup with ResetBase (reclaim max space) ──
$results["DISM ResetBase"] = Run-Step `
    -StepName "DISM StartComponentCleanup /ResetBase" `
    -Command "DISM.exe" `
    -Arguments "/Online", "/Cleanup-Image", "/StartComponentCleanup", "/ResetBase", "/LogPath:$dismLog" `
    -TimeoutMinutes 30

# ── 5d: SPSuperseded (remove service pack backup) ──
$results["DISM SPSuperseded"] = Run-Step `
    -StepName "DISM SPSuperseded" `
    -Command "DISM.exe" `
    -Arguments "/Online", "/Cleanup-Image", "/SPSuperseded", "/LogPath:$dismLog" `
    -TimeoutMinutes 15

# ============================================================
#  PHASE 6: FINAL VERIFICATION
# ============================================================

Write-Log "" "HEADER"
Write-Log "############################################" "HEADER"
Write-Log "  PHASE 6: FINAL VERIFICATION" "HEADER"
Write-Log "############################################" "HEADER"

# ── Final DISM health check ──
$results["Final CheckHealth"] = Run-Step `
    -StepName "DISM Final CheckHealth" `
    -Command "DISM.exe" `
    -Arguments "/Online", "/Cleanup-Image", "/CheckHealth", "/LogPath:$dismLog" `
    -TimeoutMinutes 5

# ── Copy CBS log for review ──
Write-Log ""
Write-Log "Saving CBS log snapshot..."
if (Test-Path $cbsLog) {
    $cbsCopy = Join-Path $logDir "CBS_${timestamp}.log"
    try {
        Copy-Item -Path $cbsLog -Destination $cbsCopy -Force
        Write-Log "CBS log saved: $cbsCopy" "SUCCESS"
    } catch {
        Write-Log "Could not copy CBS log: $_" "WARN"
    }
} else {
    Write-Log "CBS log not found at $cbsLog" "WARN"
}

# ============================================================
#  SUMMARY
# ============================================================

$overallStart.Stop()
$totalTime = $overallStart.Elapsed.ToString("hh\:mm\:ss")

Write-Log ""
Write-Log "==========================================" "HEADER"
Write-Log "  REPAIR SUITE COMPLETE" "HEADER"
Write-Log "==========================================" "HEADER"
Write-Log "  Total Time: $totalTime"
Write-Log ""

$passCount = 0
$failCount = 0
$skipCount = 0

foreach ($step in $results.GetEnumerator() | Sort-Object Name) {
    if ($step.Value -eq $true) {
        Write-Log "  [PASS] $($step.Key)" "SUCCESS"
        $passCount++
    } elseif ($step.Value -eq $false) {
        Write-Log "  [FAIL] $($step.Key)" "ERROR"
        $failCount++
    } else {
        Write-Log "  [SKIP] $($step.Key)" "WARN"
        $skipCount++
    }
}

Write-Log ""
Write-Log "  Pass: $passCount | Fail: $failCount | Skip: $skipCount"
Write-Log ""
Write-Log "  Logs:" "INFO"
Write-Log "    Script:  $logFile"
Write-Log "    DISM:    $dismLog"
if (Test-Path (Join-Path $logDir "CBS_${timestamp}.log")) {
    Write-Log "    CBS:     $(Join-Path $logDir "CBS_${timestamp}.log")"
}
Write-Log ""

if ($failCount -gt 0) {
    Write-Log "  !! Some steps had issues - review logs above !!" "WARN"
    Write-Log "  A reboot may resolve remaining issues" "WARN"
} else {
    Write-Log "  All checks passed - system looks healthy!" "SUCCESS"
}

Write-Log ""
Write-Log "==========================================" "HEADER"

Read-Host "Press Enter to close"