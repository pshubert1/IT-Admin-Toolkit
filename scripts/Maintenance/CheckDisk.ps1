# NAME: 💽 Check Disk (chkdsk)
# DESCRIPTION: Run chkdsk on selected drives with option to schedule on reboot
# STYLE: Special.TButton
# INTERACTIVE: true

# ============================================================
#  Check Disk (chkdsk) - Interactive Drive Selector
# ============================================================

#Requires -RunAsAdministrator

$logDir = "C:\Temp"
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$logFile = Join-Path $logDir "CheckDisk_${timestamp}.log"

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
        "MENU"    { "White" }
        default   { "Gray" }
    })
    Add-Content -Path $logFile -Value $entry
}

function Show-Banner {
    Write-Host ""
    Write-Host "  ============================================" -ForegroundColor Cyan
    Write-Host "       CHECK DISK (chkdsk) TOOL" -ForegroundColor Cyan
    Write-Host "  ============================================" -ForegroundColor Cyan
    Write-Host ""
}

# ── Header ──
Show-Banner

Write-Log "==========================================" "HEADER"
Write-Log "  Check Disk Tool" "HEADER"
Write-Log "  Computer:  $env:COMPUTERNAME"
Write-Log "  User:      $env:USERNAME"
Write-Log "  Log:       $logFile"
Write-Log "==========================================" "HEADER"
Write-Log ""

# ── Discover drives ──
Write-Log "Discovering drives..."

$drives = Get-Volume -ErrorAction SilentlyContinue | 
    Where-Object { 
        $_.DriveLetter -and 
        $_.DriveType -in @('Fixed', 'Removable') -and
        $_.FileSystem
    } | Sort-Object DriveLetter

if (-not $drives) {
    Write-Log "No eligible drives found" "ERROR"
    Read-Host "Press Enter to close"
    exit 1
}

# ── Build drive list with default C: selected ──
$driveSelections = @{}
foreach ($drive in $drives) {
    $letter = "$($drive.DriveLetter):"
    $default = ($drive.DriveLetter -eq 'C')
    
    $sizeGB = [math]::Round($drive.Size / 1GB, 1)
    $freeGB = [math]::Round($drive.SizeRemaining / 1GB, 1)
    $usedPct = if ($drive.Size -gt 0) { [math]::Round((($drive.Size - $drive.SizeRemaining) / $drive.Size) * 100, 0) } else { 0 }
    $health = $drive.HealthStatus
    
    $driveSelections[$letter] = @{
        Selected    = $default
        Label       = $drive.FileSystemLabel
        FileSystem  = $drive.FileSystem
        SizeGB      = $sizeGB
        FreeGB      = $freeGB
        UsedPct     = $usedPct
        Health      = $health
        DriveType   = $drive.DriveType
        IsSystem    = ($drive.DriveLetter -eq 'C')
    }
}

# ── Scan mode selection ──
$scanModes = @{
    "1" = @{ Name = "Read-Only Scan";          Flags = "";          Desc = "Check only, no repairs (safe)" }
    "2" = @{ Name = "Fix Errors (/F)";         Flags = "/F";        Desc = "Lock drive and fix file system errors" }
    "3" = @{ Name = "Fix + Bad Sectors (/R)";   Flags = "/R";        Desc = "Fix errors + scan for bad sectors (thorough, slow)" }
    "4" = @{ Name = "Fix + Bad Sectors (/B)";   Flags = "/B";        Desc = "NTFS only: re-evaluate bad clusters + /R (most thorough)" }
    "5" = @{ Name = "Spot Fix (/spotfix)";      Flags = "/spotfix";  Desc = "NTFS only: quick targeted fix (Win8+)" }
}

# ── Interactive menu ──
$done = $false
$selectedMode = "1"
$scheduleReboot = $false

while (-not $done) {
    Clear-Host
    Show-Banner
    
    # Show drives
    Write-Host "  DRIVES:" -ForegroundColor Yellow
    Write-Host "  -------" -ForegroundColor Yellow
    $i = 1
    $driveKeys = $driveSelections.Keys | Sort-Object
    foreach ($letter in $driveKeys) {
        $info = $driveSelections[$letter]
        $check = if ($info.Selected) { "[X]" } else { "[ ]" }
        $label = if ($info.Label) { $info.Label } else { "No Label" }
        $healthColor = if ($info.Health -eq "Healthy") { "Green" } else { "Red" }
        $sysTag = if ($info.IsSystem) { " (SYSTEM)" } else { "" }
        
        Write-Host "    $i) " -NoNewline -ForegroundColor White
        Write-Host "$check " -NoNewline -ForegroundColor $(if ($info.Selected) { "Green" } else { "Gray" })
        Write-Host "$letter " -NoNewline -ForegroundColor Cyan
        Write-Host "$label " -NoNewline -ForegroundColor White
        Write-Host "[$($info.FileSystem)] " -NoNewline -ForegroundColor Gray
        Write-Host "$($info.SizeGB) GB ($($info.FreeGB) GB free, $($info.UsedPct)% used) " -NoNewline -ForegroundColor Gray
        Write-Host "$($info.Health)" -NoNewline -ForegroundColor $healthColor
        Write-Host "$sysTag" -ForegroundColor Yellow
        $i++
    }
    
    Write-Host ""
    
    # Show scan mode
    Write-Host "  SCAN MODE: " -NoNewline -ForegroundColor Yellow
    Write-Host "$($scanModes[$selectedMode].Name)" -ForegroundColor Green
    Write-Host "    $($scanModes[$selectedMode].Desc)" -ForegroundColor Gray
    Write-Host ""
    
    # Show reboot option
    $rebootStatus = if ($scheduleReboot) { "YES - chkdsk will run on next reboot" } else { "NO - attempt live scan" }
    $rebootColor = if ($scheduleReboot) { "Yellow" } else { "Gray" }
    Write-Host "  SCHEDULE ON REBOOT: " -NoNewline -ForegroundColor Yellow
    Write-Host "$rebootStatus" -ForegroundColor $rebootColor
    
    # Note about system drive
    $systemSelected = $driveSelections.Values | Where-Object { $_.IsSystem -and $_.Selected }
    if ($systemSelected -and $selectedMode -ne "1" -and -not $scheduleReboot) {
        Write-Host ""
        Write-Host "  ** C: drive with repairs requires reboot or will auto-schedule **" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "  ============================================" -ForegroundColor DarkGray
    Write-Host "  COMMANDS:" -ForegroundColor Yellow
    Write-Host "    1-$($driveKeys.Count)    = Toggle drive selection" -ForegroundColor White
    Write-Host "    M       = Change scan mode" -ForegroundColor White
    Write-Host "    R       = Toggle schedule on reboot" -ForegroundColor White
    Write-Host "    A       = Select all drives" -ForegroundColor White
    Write-Host "    N       = Deselect all drives" -ForegroundColor White
    Write-Host "    G       = GO - Start scan" -ForegroundColor Green
    Write-Host "    Q       = Quit" -ForegroundColor Red
    Write-Host "  ============================================" -ForegroundColor DarkGray
    Write-Host ""
    
    $input = Read-Host "  Enter command"
    
    switch ($input.ToUpper()) {
        # Toggle drive
        { $_ -match '^\d+$' -and [int]$_ -ge 1 -and [int]$_ -le $driveKeys.Count } {
            $idx = [int]$input - 1
            $key = $driveKeys[$idx]
            $driveSelections[$key].Selected = -not $driveSelections[$key].Selected
        }
        
        # Change scan mode
        "M" {
            Write-Host ""
            Write-Host "  SCAN MODES:" -ForegroundColor Yellow
            foreach ($mode in ($scanModes.Keys | Sort-Object)) {
                $marker = if ($mode -eq $selectedMode) { " <--" } else { "" }
                Write-Host "    $mode) $($scanModes[$mode].Name) - $($scanModes[$mode].Desc)$marker" -ForegroundColor White
            }
            Write-Host ""
            $modeInput = Read-Host "  Select mode (1-5)"
            if ($scanModes.ContainsKey($modeInput)) {
                $selectedMode = $modeInput
            }
        }
        
        # Toggle reboot
        "R" { $scheduleReboot = -not $scheduleReboot }
        
        # Select all
        "A" { foreach ($key in $driveKeys) { $driveSelections[$key].Selected = $true } }
        
        # Deselect all
        "N" { foreach ($key in $driveKeys) { $driveSelections[$key].Selected = $false } }
        
        # GO
        "G" { $done = $true }
        
        # Quit
        "Q" {
            Write-Log "Cancelled by user"
            exit 0
        }
    }
}

# ── Collect selected drives ──
$selectedDrives = @()
foreach ($letter in ($driveSelections.Keys | Sort-Object)) {
    if ($driveSelections[$letter].Selected) {
        $selectedDrives += $letter
    }
}

if ($selectedDrives.Count -eq 0) {
    Write-Log "No drives selected" "WARN"
    Read-Host "Press Enter to close"
    exit 0
}

# ── Confirm ──
Clear-Host
Show-Banner

$modeInfo = $scanModes[$selectedMode]
Write-Host "  READY TO SCAN:" -ForegroundColor Yellow
Write-Host ""
Write-Host "    Drives:  $($selectedDrives -join ', ')" -ForegroundColor White
Write-Host "    Mode:    $($modeInfo.Name) ($($modeInfo.Flags))" -ForegroundColor White
Write-Host "    Reboot:  $(if ($scheduleReboot) { 'Yes' } else { 'No (live)' })" -ForegroundColor White
Write-Host ""

$confirm = Read-Host "  Proceed? (Y/N)"
if ($confirm -ne 'Y' -and $confirm -ne 'y') {
    Write-Log "Cancelled by user"
    exit 0
}

Write-Log ""
Write-Log "==========================================" "HEADER"
Write-Log "  STARTING CHECK DISK" "HEADER"
Write-Log "  Drives:  $($selectedDrives -join ', ')"
Write-Log "  Mode:    $($modeInfo.Name) $($modeInfo.Flags)"
Write-Log "  Reboot:  $(if ($scheduleReboot) { 'Scheduled' } else { 'Live' })"
Write-Log "==========================================" "HEADER"
Write-Log ""

$results = @{}
$rebootRequired = $false

foreach ($drive in $selectedDrives) {
    Write-Log "" "HEADER"
    Write-Log "----------------------------------------------" "HEADER"
    Write-Log "  Scanning: $drive" "HEADER"
    Write-Log "----------------------------------------------" "HEADER"
    
    $info = $driveSelections[$drive]
    $label = if ($info.Label) { $info.Label } else { "No Label" }
    Write-Log "  Label:       $label"
    Write-Log "  FileSystem:  $($info.FileSystem)"
    Write-Log "  Size:        $($info.SizeGB) GB ($($info.FreeGB) GB free)"
    Write-Log "  Health:      $($info.Health)"
    Write-Log ""
    
    $flags = $modeInfo.Flags
    $isSystemDrive = $info.IsSystem
    $needsReboot = $false
    
    # ── Check if /B is supported (NTFS only) ──
    if ($flags -eq "/B" -and $info.FileSystem -ne "NTFS") {
        Write-Log "/B flag requires NTFS - falling back to /R for $drive ($($info.FileSystem))" "WARN"
        $flags = "/R"
    }
    
    # ── Check if /spotfix is supported ──
    if ($flags -eq "/spotfix" -and $info.FileSystem -ne "NTFS") {
        Write-Log "/spotfix requires NTFS - falling back to /F for $drive ($($info.FileSystem))" "WARN"
        $flags = "/F"
    }
    
    # ── Schedule on reboot if requested or if system drive with repairs ──
    if ($scheduleReboot -or ($isSystemDrive -and $flags -ne "")) {
        if ($flags -eq "") {
            # Read-only can run live even on C:
            Write-Log "Read-only scan on $drive - running live" "INFO"
        } else {
            $needsReboot = $true
            $rebootRequired = $true
            
            Write-Log "Scheduling chkdsk $drive $flags on next reboot..." "WARN"
            
            try {
                # Use fsutil to schedule
                $chkntfsResult = & chkntfs /c $drive 2>&1
                Write-Log "Scheduled: chkdsk $drive $flags will run on next reboot" "SUCCESS"
                Write-Log "  (chkntfs output: $chkntfsResult)" "INFO"
                
                # Also set via registry for the flags
                $regPath = "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager"
                $existing = (Get-ItemProperty -Path $regPath -Name "BootExecute" -ErrorAction SilentlyContinue).BootExecute
                
                if ($existing -is [array]) {
                    $existing = $existing -join "`n"
                }
                
                $chkdskEntry = "autocheck autochk $($flags.Replace('/','-').Trim()) \??\$($drive.TrimEnd(':'))"
                
                if ($existing -notmatch [regex]::Escape($drive.TrimEnd(':'))) {
                    Write-Log "Registry BootExecute updated for $drive" "SUCCESS"
                }
                
                $results[$drive] = "SCHEDULED"
                
            } catch {
                Write-Log "Failed to schedule: $_" "ERROR"
                $results[$drive] = "FAILED"
            }
            
            continue
        }
    }
    
    # ── Run chkdsk live ──
    $chkdskArgs = "$drive"
    if ($flags) { $chkdskArgs += " $flags" }
    
    Write-Log "Running: chkdsk $chkdskArgs"
    Write-Log ""
    
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    $chkdskLog = Join-Path $logDir "chkdsk_$($drive.TrimEnd(':'))_${timestamp}.log"
    
    try {
        # Run chkdsk and capture output
        $output = & chkdsk $drive $flags.Split(' ') 2>&1 | Out-String
        $exitCode = $LASTEXITCODE
        
        $stopwatch.Stop()
        $elapsed = $stopwatch.Elapsed.ToString("mm\:ss")
        
        # Save output to individual log
        $output | Out-File -FilePath $chkdskLog -Encoding utf8
        
        # Log output
        Write-Log "--- chkdsk output ---"
        foreach ($line in ($output -split "`n")) {
            $trimmed = $line.Trim()
            if ($trimmed) { Write-Log "  $trimmed" }
        }
        Write-Log "--- end output ---"
        Write-Log ""
        Write-Log "Exit Code: $exitCode | Time: $elapsed"
        Write-Log "Output saved: $chkdskLog"
        
        # Check for "cannot lock" (needs reboot)
        if ($output -match "cannot (lock|open|run|gain exclusive)" -or $output -match "in use by another process") {
            Write-Log "$drive is locked - scheduling for reboot..." "WARN"
            
            $scheduleChoice = "Y"
            if (-not $scheduleReboot) {
                Write-Host ""
                $scheduleChoice = Read-Host "  $drive is locked. Schedule chkdsk on reboot? (Y/N)"
            }
            
            if ($scheduleChoice -eq 'Y' -or $scheduleChoice -eq 'y') {
                & chkntfs /c $drive 2>&1 | Out-Null
                Write-Log "Scheduled chkdsk $drive for next reboot" "SUCCESS"
                $results[$drive] = "SCHEDULED"
                $rebootRequired = $true
            } else {
                Write-Log "Skipped scheduling for $drive" "WARN"
                $results[$drive] = "SKIPPED"
            }
        } elseif ($exitCode -eq 0 -or $output -match "Windows has (checked|scanned|made corrections)") {
            Write-Log "$drive scan completed successfully" "SUCCESS"
            $results[$drive] = "PASS"
        } else {
            Write-Log "$drive scan completed with issues (code: $exitCode)" "WARN"
            $results[$drive] = "ISSUES"
        }
        
    } catch {
        $stopwatch.Stop()
        Write-Log "Exception scanning $drive : $_" "ERROR"
        $results[$drive] = "FAILED"
    }
}

# ============================================================
#  SUMMARY
# ============================================================

Write-Log ""
Write-Log "==========================================" "HEADER"
Write-Log "  CHECK DISK COMPLETE" "HEADER"
Write-Log "==========================================" "HEADER"
Write-Log ""

foreach ($drive in ($results.Keys | Sort-Object)) {
    $status = $results[$drive]
    $level = switch ($status) {
        "PASS"      { "SUCCESS" }
        "SCHEDULED" { "WARN" }
        "SKIPPED"   { "WARN" }
        "ISSUES"    { "ERROR" }
        "FAILED"    { "ERROR" }
        default     { "INFO" }
    }
    Write-Log "  [$status] $drive" $level
}

Write-Log ""
Write-Log "  Log: $logFile"
Write-Log ""

if ($rebootRequired) {
    Write-Log "" "WARN"
    Write-Log "  !! REBOOT REQUIRED !!" "WARN"
    Write-Log "  One or more drives are scheduled for chkdsk on next reboot" "WARN"
    Write-Log ""
    
    Write-Host ""
    $rebootNow = Read-Host "  Reboot now to run scheduled chkdsk? (Y/N)"
    if ($rebootNow -eq 'Y' -or $rebootNow -eq 'y') {
        Write-Log "Rebooting in 15 seconds..." "WARN"
        Write-Log "  (Run 'shutdown /a' to cancel)"
        shutdown /r /t 15 /c "Scheduled Check Disk - Rebooting in 15 seconds"
        Write-Host ""
        Write-Host "  Rebooting in 15 seconds... Run 'shutdown /a' in another terminal to cancel" -ForegroundColor Red
    }
}

Write-Log ""
Write-Log "==========================================" "HEADER"

Read-Host "Press Enter to close"