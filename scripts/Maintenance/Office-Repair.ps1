# NAME: Office Apps Online Repair (Enhanced)
# DESCRIPTION: Triggers Full Online Repair for Click-to-Run Office installations with dynamic culture and logging
# STYLE: Warning.TButton

$ErrorActionPreference = "Stop"

# Start logging
$logPath = Join-Path -Path $PSScriptRoot -ChildPath "OfficeRepairLog.txt"
Start-Transcript -Path $logPath -Append
Write-Host "Logging started: $logPath" -ForegroundColor Cyan

try {
    # Quick admin check (warn if not elevated, even if expected)
    if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        Write-Warning "Script is not running as Administrator. Repairs may fail. Relaunch as admin."
    }

    # Detect Office architecture (x64/x86) and path
    $paths = @(
        "${env:ProgramFiles}\Common Files\Microsoft Shared\ClickToRun\OfficeClickToRun.exe",
        "${env:ProgramFiles(x86)}\Common Files\Microsoft Shared\ClickToRun\OfficeClickToRun.exe",
        "${env:ProgramFiles}\Microsoft Office\root\Office16\OfficeClickToRun.exe",
        "${env:ProgramFiles(x86)}\Microsoft Office\root\Office16\OfficeClickToRun.exe",
        "${env:ProgramFiles}\Microsoft Office 15\root\Office15\OfficeClickToRun.exe",  # For older installs
        "${env:ProgramFiles(x86)}\Microsoft Office 15\root\Office15\OfficeClickToRun.exe"
    )

    $officeExe = $null
    $platform = $null
    foreach ($path in $paths) {
        if (Test-Path $path) {
            $officeExe = $path
            $platform = if ($path -like "*x86*" -or [Environment]::Is64BitOperatingSystem -eq $false) { "x86" } else { "x64" }
            Write-Host "Found Office C2R at: $path (Platform: $platform)" -ForegroundColor Green
            break
        }
    }

    if (-not $officeExe) {
        throw "Office Click-to-Run executable not found. Ensure Office is installed via Click-to-Run."
    }

    # Detect installed culture dynamically (from registry or system fallback)
    $culture = "en-us"  # Default fallback
    try {
        $officeRegKey = "HKLM:\SOFTWARE\Microsoft\Office\ClickToRun\Configuration"
        if (Test-Path $officeRegKey) {
            $installedCulture = (Get-ItemProperty -Path $officeRegKey -Name "ClientCulture").ClientCulture
            if ($installedCulture) { $culture = $installedCulture }
        } else {
            $culture = (Get-Culture).Name  # System culture as fallback
        }
        Write-Host "Detected Office culture: $culture" -ForegroundColor Green
    } catch {
        Write-Warning "Could not detect Office culture; using fallback: $culture"
    }

    # User confirmation
    $confirm = Read-Host "This will close all Office apps and start a full online repair. Continue? (Y/N)"
    if ($confirm -ne "Y" -and $confirm -ne "y") {
        Write-Host "Repair cancelled by user." -ForegroundColor Yellow
        exit 0
    }

    # Kill all Office processes with verification
    $officeProcesses = @("WINWORD", "EXCEL", "POWERPNT", "OUTLOOK", "ONENOTE", "MSACCESS", "MSPUB", "LYNC", "VISIO")
    Write-Host "Closing Office applications..." -ForegroundColor Yellow
    Get-Process | Where-Object { $officeProcesses -contains $_.ProcessName } | Stop-Process -Force -ErrorAction SilentlyContinue
    
    # Wait and verify processes are closed (up to 30 seconds)
    $timeout = 30
    while ($timeout -gt 0 -and (Get-Process | Where-Object { $officeProcesses -contains $_.ProcessName })) {
        Start-Sleep -Seconds 1
        $timeout--
    }
    if ($timeout -le 0) {
        Write-Warning "Some Office processes may not have closed. Repair might fail."
    }

    # Online Repair command (FullRepair = Online Repair)
    $arguments = @(
        "scenario=Repair",
        "platform=$platform",
        "culture=$culture",
        "RepairType=FullRepair",
        "forceappshutdown=True",
        "DisplayLevel=False"
    )

    Write-Host "Starting Office Online Repair (FullRepair)..." -ForegroundColor Cyan
    Write-Host "Command: $officeExe $($arguments -join ' ')" -ForegroundColor Gray

    # Start the repair process
    $process = Start-Process -FilePath $officeExe -ArgumentList $arguments -PassThru -WindowStyle Hidden -Wait

    # Handle exit codes
    switch ($process.ExitCode) {
        0 { Write-Host "Office Online Repair completed successfully!" -ForegroundColor Green }
        3010 { Write-Host "Repair completed but requires a reboot to take effect." -ForegroundColor Green }
        default { Write-Warning "Repair process exited with code: $($process.ExitCode). Check logs or Microsoft docs for details." }
    }

    Write-Host "Reboot recommended after Online Repair. Verify by opening an Office app (e.g., Word) and checking File > Account > About." -ForegroundColor Yellow

} catch {
    Write-Error "Error during repair: $_"
    exit 1
} finally {
    Stop-Transcript
    Write-Host "Logging stopped. Check $logPath for details." -ForegroundColor Cyan
}