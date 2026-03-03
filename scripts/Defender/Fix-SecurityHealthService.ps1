# NAME: 🛡️ Fix Security Health Service
# DESCRIPTION: Fixes stopped SecurityHealthService and missing MSASCuiL.exe
# STYLE: Danger.TButton
# INTERACTIVE: true

try {

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  🛡️ Fix Security Health Service" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "❌ Must run as Administrator!" -ForegroundColor Red
    Read-Host "Press Enter to close"
    return
}

# ==========================================
# Step 1: Find the current Defender platform
# ==========================================
Write-Host "🔧 Step 1: Locating Defender platform..." -ForegroundColor Yellow
$platformBase = "$env:ProgramData\Microsoft\Windows Defender\Platform"
$latestPlatform = Get-ChildItem $platformBase -Directory -ErrorAction SilentlyContinue | 
    Sort-Object Name -Descending | Select-Object -First 1

if ($latestPlatform) {
    Write-Host "  ✅ Latest platform: $($latestPlatform.Name)" -ForegroundColor Green
    Write-Host "     Path: $($latestPlatform.FullName)" -ForegroundColor Gray
    
    # Check for MSASCuiL.exe in platform folder
    $platformMSASCuiL = Join-Path $latestPlatform.FullName "MSASCuiL.exe"
    if (Test-Path $platformMSASCuiL) {
        Write-Host "  ✅ MSASCuiL.exe found in platform folder" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️ MSASCuiL.exe not in platform folder either" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ❌ No platform folder found" -ForegroundColor Red
}
Write-Host ""

# ==========================================
# Step 2: Fix MSASCuiL.exe
# ==========================================
Write-Host "🔧 Step 2: Fixing MSASCuiL.exe..." -ForegroundColor Yellow
$defenderPath = "$env:ProgramFiles\Windows Defender"
$targetMSASCuiL = Join-Path $defenderPath "MSASCuiL.exe"

if (-not (Test-Path $targetMSASCuiL)) {
    # Try to copy from platform folder
    if ($latestPlatform) {
        $sourceMSASCuiL = Join-Path $latestPlatform.FullName "MSASCuiL.exe"
        if (Test-Path $sourceMSASCuiL) {
            try {
                Copy-Item $sourceMSASCuiL $targetMSASCuiL -Force
                Write-Host "  ✅ Copied MSASCuiL.exe from platform folder" -ForegroundColor Green
            } catch {
                Write-Host "  ⚠️ Could not copy: $_" -ForegroundColor Gray
            }
        }
    }
    
    # If still missing, try SFC to restore it
    if (-not (Test-Path $targetMSASCuiL)) {
        Write-Host "  🔄 Running SFC to restore missing file..." -ForegroundColor Yellow
        sfc /scannow 2>&1 | Out-Null
        if (Test-Path $targetMSASCuiL) {
            Write-Host "  ✅ MSASCuiL.exe restored by SFC" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️ SFC could not restore MSASCuiL.exe" -ForegroundColor Yellow
            Write-Host "  ⚠️ This is OK on newer Win 11 builds - UI uses SecurityHealthHost instead" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "  ✅ MSASCuiL.exe already exists" -ForegroundColor Green
}
Write-Host ""

# ==========================================
# Step 3: Fix SecurityHealthService
# ==========================================
Write-Host "🔧 Step 3: Fixing SecurityHealthService..." -ForegroundColor Yellow

# Fix service registry configuration
try {
    $svcRegPath = "HKLM:\SYSTEM\CurrentControlSet\Services\SecurityHealthService"
    if (Test-Path $svcRegPath) {
        # Ensure service is set to Auto start
        Set-ItemProperty -Path $svcRegPath -Name "Start" -Value 2 -Force
        Write-Host "  ✅ Service set to Automatic start" -ForegroundColor Green
        
        # Check and fix ImagePath
        $imagePath = (Get-ItemProperty -Path $svcRegPath -Name "ImagePath" -ErrorAction SilentlyContinue).ImagePath
        Write-Host "  📌 Current ImagePath: $imagePath" -ForegroundColor Gray
        
        # Verify the executable exists
        $cleanPath = $imagePath -replace '"', ''
        if ($cleanPath -and (Test-Path $cleanPath)) {
            Write-Host "  ✅ Service executable exists" -ForegroundColor Green
        } else {
            Write-Host "  ❌ Service executable NOT FOUND at: $cleanPath" -ForegroundColor Red
            
            # Try to find it
            $possiblePaths = @(
                "$env:ProgramFiles\Windows Defender\MSASCuiL.exe",
                "$env:ProgramFiles\Windows Defender Advanced Threat Protection\SenseCncProxy.exe",
                "$env:SystemRoot\system32\SecurityHealthService.exe",
                "$($latestPlatform.FullName)\SecurityHealthService.exe"
            )
            foreach ($path in $possiblePaths) {
                if (Test-Path $path) {
                    Write-Host "  ✅ Found alternative: $path" -ForegroundColor Green
                    Set-ItemProperty -Path $svcRegPath -Name "ImagePath" -Value "`"$path`"" -Force
                    Write-Host "  ✅ Updated ImagePath" -ForegroundColor Green
                    break
                }
            }
        }
        
        # Remove any failure flags
        Remove-ItemProperty -Path $svcRegPath -Name "FailureActions" -Force -ErrorAction SilentlyContinue
        
    } else {
        Write-Host "  ❌ Service registry key not found" -ForegroundColor Red
    }
} catch {
    Write-Host "  ⚠️ Registry fix error: $_" -ForegroundColor Gray
}
Write-Host ""

# ==========================================
# Step 4: Fix SecurityHealthSystray startup
# ==========================================
Write-Host "🔧 Step 4: Fixing Security Health startup entry..." -ForegroundColor Yellow
try {
    $runPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
    
    # Find the correct executable for systray
    $systrayExe = $null
    $systrayOptions = @(
        "$env:ProgramFiles\Windows Defender\MSASCuiL.exe",
        "$($latestPlatform.FullName)\MSASCuiL.exe",
        "$env:SystemRoot\system32\SecurityHealthSystray.exe",
        "$($latestPlatform.FullName)\SecurityHealthSystray.exe"
    )
    foreach ($opt in $systrayOptions) {
        if (Test-Path $opt) {
            $systrayExe = $opt
            break
        }
    }
    
    if ($systrayExe) {
        Set-ItemProperty -Path $runPath -Name "SecurityHealth" -Value "`"$systrayExe`"" -Force
        Write-Host "  ✅ Startup entry set to: $systrayExe" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️ No systray executable found" -ForegroundColor Yellow
        Write-Host "  ⚠️ Checking platform folder for alternatives..." -ForegroundColor Gray
        if ($latestPlatform) {
            Get-ChildItem $latestPlatform.FullName -Filter "*.exe" | ForEach-Object {
                Write-Host "     Found: $($_.Name)" -ForegroundColor Gray
            }
        }
    }
    
    # Make sure it's not blocked in StartupApproved
    $approvedPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"
    if (Test-Path $approvedPath) {
        Remove-ItemProperty -Path $approvedPath -Name "SecurityHealth" -Force -ErrorAction SilentlyContinue
        Write-Host "  ✅ Removed any startup block" -ForegroundColor Green
    }
} catch {
    Write-Host "  ⚠️ Startup fix error: $_" -ForegroundColor Gray
}
Write-Host ""

# ==========================================
# Step 5: Re-register Windows Security app
# ==========================================
Write-Host "🔧 Step 5: Re-registering Windows Security app..." -ForegroundColor Yellow

# Get the app's actual install location from AppX
$secApp = Get-AppxPackage -Name "Microsoft.SecHealthUI" -AllUsers -ErrorAction SilentlyContinue
if ($secApp -and $secApp.InstallLocation) {
    $manifest = Join-Path $secApp.InstallLocation "AppXManifest.xml"
    if (Test-Path $manifest) {
        try {
            Add-AppxPackage -DisableDevelopmentMode -Register $manifest -ForceApplicationShutdown -ErrorAction Stop
            Write-Host "  ✅ App re-registered from: $($secApp.InstallLocation)" -ForegroundColor Green
        } catch {
            Write-Host "  ⚠️ Re-register failed: $_" -ForegroundColor Gray
        }
    }
}

# Also try the WindowsApps path directly
$windowsAppsPath = "C:\Program Files\WindowsApps"
$secHealthDirs = Get-ChildItem $windowsAppsPath -Directory -Filter "*SecHealthUI*" -ErrorAction SilentlyContinue
if ($secHealthDirs) {
    $latest = $secHealthDirs | Sort-Object Name -Descending | Select-Object -First 1
    $manifest = Join-Path $latest.FullName "AppXManifest.xml"
    if (Test-Path $manifest) {
        try {
            Add-AppxPackage -DisableDevelopmentMode -Register $manifest -ForceApplicationShutdown -ErrorAction Stop
            Write-Host "  ✅ App re-registered from WindowsApps" -ForegroundColor Green
        } catch {
            Write-Host "  ⚠️ Already registered or error: $_" -ForegroundColor Gray
        }
    }
}
Write-Host ""

# ==========================================
# Step 6: Start SecurityHealthService
# ==========================================
Write-Host "🔧 Step 6: Starting SecurityHealthService..." -ForegroundColor Yellow
try {
    # First try normal start
    Start-Service -Name "SecurityHealthService" -ErrorAction Stop
    Write-Host "  ✅ SecurityHealthService started!" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️ Normal start failed: $_" -ForegroundColor Gray
    Write-Host "  🔄 Trying alternative method..." -ForegroundColor Yellow
    
    try {
        # Try via sc.exe
        $scResult = sc.exe start SecurityHealthService 2>&1
        Write-Host "  sc.exe result: $scResult" -ForegroundColor Gray
    } catch {
        Write-Host "  ⚠️ sc.exe also failed" -ForegroundColor Gray
    }
    
    try {
        # Try via WMI
        $svc = Get-WmiObject -Class Win32_Service -Filter "Name='SecurityHealthService'" -ErrorAction Stop
        $svc.StartService() | Out-Null
        Write-Host "  ✅ Started via WMI" -ForegroundColor Green
    } catch {
        Write-Host "  ❌ All start methods failed" -ForegroundColor Red
        Write-Host "  ⚠️ The service executable may be corrupt" -ForegroundColor Yellow
    }
}

# Verify it's running
Start-Sleep -Seconds 2
$svcStatus = Get-Service -Name "SecurityHealthService" -ErrorAction SilentlyContinue
Write-Host "  📌 Service status: $($svcStatus.Status)" -ForegroundColor $(if($svcStatus.Status -eq 'Running'){'Green'}else{'Red'})
Write-Host ""

# ==========================================
# Step 7: Start the systray icon
# ==========================================
Write-Host "🔧 Step 7: Launching Security Health systray..." -ForegroundColor Yellow
if ($systrayExe -and (Test-Path $systrayExe)) {
    try {
        Start-Process $systrayExe -ErrorAction SilentlyContinue
        Write-Host "  ✅ Systray launched" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠️ Could not launch systray" -ForegroundColor Gray
    }
} else {
    Write-Host "  ⚠️ No systray executable to launch" -ForegroundColor Yellow
}
Write-Host ""

# ==========================================
# Step 8: Test opening Windows Security
# ==========================================
Write-Host "🔧 Step 8: Testing Windows Security app..." -ForegroundColor Yellow
try {
    Start-Process "windowsdefender:" -ErrorAction Stop
    Write-Host "  ✅ Windows Security app launched via protocol" -ForegroundColor Green
    Write-Host "  👀 Check if it loads properly..." -ForegroundColor Yellow
} catch {
    Write-Host "  ⚠️ Protocol launch failed, trying direct..." -ForegroundColor Gray
    try {
        Start-Process "ms-settings:windowsdefender" -ErrorAction Stop
        Write-Host "  ✅ Opened via Settings" -ForegroundColor Green
    } catch {
        Write-Host "  ❌ Could not open Windows Security" -ForegroundColor Red
    }
}
Write-Host ""

# ==========================================
# Final Status
# ==========================================
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host "       📋 FINAL STATUS" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$svcFinal = Get-Service -Name "SecurityHealthService" -ErrorAction SilentlyContinue
if ($svcFinal.Status -eq 'Running') {
    Write-Host "  ✅ SecurityHealthService: Running" -ForegroundColor Green
} else {
    Write-Host "  ❌ SecurityHealthService: $($svcFinal.Status)" -ForegroundColor Red
}

$appFinal = Get-AppxPackage -Name "Microsoft.SecHealthUI" -ErrorAction SilentlyContinue
if ($appFinal) {
    Write-Host "  ✅ Security App: Installed v$($appFinal.Version)" -ForegroundColor Green
} else {
    Write-Host "  ❌ Security App: Not installed" -ForegroundColor Red
}

try {
    $mpStatus = Get-MpComputerStatus -ErrorAction Stop
    Write-Host "  ✅ Defender Engine: Running" -ForegroundColor Green
    Write-Host "  ✅ Real-Time Protection: $($mpStatus.RealTimeProtectionEnabled)" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Cannot query Defender status" -ForegroundColor Red
}

Write-Host ""
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

if ($svcFinal.Status -ne 'Running') {
    Write-Host "  ⚠️ Service still not running. Next steps:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  1. Reboot and check if service starts" -ForegroundColor White
    Write-Host ""
    Write-Host "  2. If still broken, run in admin PowerShell:" -ForegroundColor White
    Write-Host "     DISM /Online /Cleanup-Image /RestoreHealth" -ForegroundColor Gray
    Write-Host "     sfc /scannow" -ForegroundColor Gray
    Write-Host "     Reboot" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  3. In-Place Upgrade Repair:" -ForegroundColor White
    Write-Host "     Download Win 11 ISO > Mount > setup.exe" -ForegroundColor Gray
    Write-Host "     Choose 'Keep files and apps'" -ForegroundColor Gray
    Write-Host "     This replaces ALL system files" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  4. Check if this is an Insider/Dev build:" -ForegroundColor White
    Write-Host "     Build 26200 is a Dev channel build" -ForegroundColor Gray
    Write-Host "     Known issues with Security app on Insider builds" -ForegroundColor Gray
    Write-Host "     May need to wait for a newer build to fix it" -ForegroundColor Gray
}

} catch {
    Write-Host ""
    Write-Host "❌ Error: $_" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor Gray
} finally {
    Write-Host ""
    Write-Host "Press Enter to close..." -ForegroundColor Gray
    Read-Host
}