# NAME: 🛡️ Repair Windows Security App
# DESCRIPTION: Fixes Windows Security app when it won't load (blank shield/spinning)
# STYLE: Danger.TButton
# INTERACTIVE: true

try {

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  🛡️ Windows Security App Repair" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check for admin
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "❌ This script must be run as Administrator!" -ForegroundColor Red
    Read-Host "Press Enter to close"
    return
}

# ==========================================
# Step 1: Kill all Security related processes
# ==========================================
Write-Host "🔧 Step 1: Killing Security processes..." -ForegroundColor Yellow
$processes = @('SecurityHealthSystray', 'SecurityHealthService', 'SecurityHealthHost', 'MSASCuiL')
foreach ($proc in $processes) {
    try {
        Get-Process -Name $proc -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
        Write-Host "  ⏹️ Killed $proc" -ForegroundColor Gray
    } catch {
        Write-Host "  ⚠️ $proc not running" -ForegroundColor Gray
    }
}
Write-Host ""

# ==========================================
# Step 2: Stop Security Center service
# ==========================================
Write-Host "🔧 Step 2: Stopping Security Center service..." -ForegroundColor Yellow
try {
    Stop-Service -Name "wscsvc" -Force -ErrorAction SilentlyContinue
    Stop-Service -Name "SecurityHealthService" -Force -ErrorAction SilentlyContinue
    Write-Host "  ✅ Services stopped" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️ Could not stop some services (protected)" -ForegroundColor Gray
}
Write-Host ""

# ==========================================
# Step 3: Clear Windows Security app cache
# ==========================================
Write-Host "🔧 Step 3: Clearing app cache..." -ForegroundColor Yellow
$cachePaths = @(
    "$env:LOCALAPPDATA\Packages\Microsoft.SecHealthUI_8wekyb3d8bbwe\AC",
    "$env:LOCALAPPDATA\Packages\Microsoft.SecHealthUI_8wekyb3d8bbwe\LocalCache",
    "$env:LOCALAPPDATA\Packages\Microsoft.SecHealthUI_8wekyb3d8bbwe\LocalState",
    "$env:LOCALAPPDATA\Packages\Microsoft.SecHealthUI_8wekyb3d8bbwe\TempState"
)
foreach ($path in $cachePaths) {
    if (Test-Path $path) {
        try {
            Remove-Item -Path "$path\*" -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host "  ✅ Cleared $([System.IO.Path]::GetFileName($path))" -ForegroundColor Green
        } catch {
            Write-Host "  ⚠️ Could not fully clear $([System.IO.Path]::GetFileName($path))" -ForegroundColor Gray
        }
    } else {
        Write-Host "  ⚠️ $([System.IO.Path]::GetFileName($path)) not found" -ForegroundColor Gray
    }
}
Write-Host ""

# ==========================================
# Step 4: Uninstall Windows Security app
# ==========================================
Write-Host "🔧 Step 4: Removing Windows Security app..." -ForegroundColor Yellow
try {
    Get-AppxPackage -Name "Microsoft.SecHealthUI" -AllUsers -ErrorAction SilentlyContinue | Remove-AppxPackage -AllUsers -ErrorAction SilentlyContinue
    Write-Host "  ✅ App removed" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️ Standard removal failed, trying forced..." -ForegroundColor Gray
    try {
        Get-AppxPackage -Name "Microsoft.SecHealthUI" -ErrorAction SilentlyContinue | Remove-AppxPackage -ErrorAction SilentlyContinue
        Write-Host "  ✅ App removed (current user)" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠️ Could not remove app: $_" -ForegroundColor Gray
    }
}
Write-Host ""

# ==========================================
# Step 5: Clean up leftover registration
# ==========================================
Write-Host "🔧 Step 5: Cleaning up app registration..." -ForegroundColor Yellow
try {
    Get-AppxProvisionedPackage -Online -ErrorAction SilentlyContinue | 
        Where-Object { $_.PackageName -like "*SecHealthUI*" } | 
        Remove-AppxProvisionedPackage -Online -ErrorAction SilentlyContinue
    Write-Host "  ✅ Provisioned package cleaned" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️ No provisioned package to clean" -ForegroundColor Gray
}
Write-Host ""

# ==========================================
# Step 6: Re-register Windows Security app
# ==========================================
Write-Host "🔧 Step 6: Re-registering Windows Security app..." -ForegroundColor Yellow

# Method 1: Register from SystemApps
$appPath = "C:\Windows\SystemApps\Microsoft.Windows.SecHealthUI_cw5n1h2txyewy\AppXManifest.xml"
if (Test-Path $appPath) {
    try {
        Add-AppxPackage -DisableDevelopmentMode -Register $appPath -ErrorAction Stop
        Write-Host "  ✅ App re-registered from SystemApps" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠️ Method 1 failed: $_" -ForegroundColor Gray
    }
} else {
    Write-Host "  ⚠️ SystemApps path not found, trying alternative..." -ForegroundColor Gray
}

# Method 2: Register from WindowsApps
$altPaths = Get-ChildItem "C:\Windows\SystemApps" -Directory -Filter "*SecHealth*" -ErrorAction SilentlyContinue
if ($altPaths) {
    foreach ($dir in $altPaths) {
        $manifest = Join-Path $dir.FullName "AppXManifest.xml"
        if (Test-Path $manifest) {
            try {
                Add-AppxPackage -DisableDevelopmentMode -Register $manifest -ErrorAction Stop
                Write-Host "  ✅ App re-registered from $($dir.Name)" -ForegroundColor Green
            } catch {
                Write-Host "  ⚠️ Could not register from $($dir.Name)" -ForegroundColor Gray
            }
        }
    }
}

# Method 3: PowerShell re-register all built-in apps (nuclear option)
Write-Host "  🔄 Running full re-register of all system apps..." -ForegroundColor Gray
try {
    Get-AppxPackage -AllUsers -ErrorAction SilentlyContinue | 
        Where-Object { $_.Name -like "*SecHealthUI*" } |
        ForEach-Object { 
            Add-AppxPackage -DisableDevelopmentMode -Register "$($_.InstallLocation)\AppXManifest.xml" -ErrorAction SilentlyContinue 
        }
    Write-Host "  ✅ Full re-register complete" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️ Full re-register had issues" -ForegroundColor Gray
}
Write-Host ""

# ==========================================
# Step 7: Reset Defender platform via MpCmdRun
# ==========================================
Write-Host "🔧 Step 7: Resetting Defender platform..." -ForegroundColor Yellow
$mpCmdRun = "$env:ProgramFiles\Windows Defender\MpCmdRun.exe"
if (Test-Path $mpCmdRun) {
    try {
        & $mpCmdRun -ResetPlatform 2>$null
        Write-Host "  ✅ Platform reset" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠️ Platform reset not supported on this version" -ForegroundColor Gray
    }
    try {
        & $mpCmdRun -SignatureUpdate 2>$null
        Write-Host "  ✅ Signatures updated" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠️ Could not update signatures" -ForegroundColor Gray
    }
} else {
    Write-Host "  ⚠️ MpCmdRun.exe not found" -ForegroundColor Gray
}
Write-Host ""

# ==========================================
# Step 8: Fix Security Center registry
# ==========================================
Write-Host "🔧 Step 8: Repairing Security Center registry..." -ForegroundColor Yellow
try {
    # Ensure Security Center service starts automatically
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\wscsvc" -Name "Start" -Value 2 -Force -ErrorAction SilentlyContinue
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\SecurityHealthService" -Name "Start" -Value 2 -Force -ErrorAction SilentlyContinue
    
    # Remove any disable flags
    Remove-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender" -Name "DisableAntiSpyware" -Force -ErrorAction SilentlyContinue
    Remove-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender Security Center" -Name "*" -Force -ErrorAction SilentlyContinue
    Remove-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run" -Name "SecurityHealth" -Force -ErrorAction SilentlyContinue
    
    # Ensure SecurityHealth startup entry exists
    $startupPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
    $secHealthPath = "$env:ProgramFiles\Windows Defender\MSASCuiL.exe"
    if (Test-Path $secHealthPath) {
        Set-ItemProperty -Path $startupPath -Name "SecurityHealth" -Value "`"$secHealthPath`"" -Force -ErrorAction SilentlyContinue
    }
    
    Write-Host "  ✅ Registry repaired" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️ Some registry repairs failed" -ForegroundColor Gray
}
Write-Host ""

# ==========================================
# Step 9: DISM repair for Defender component
# ==========================================
Write-Host "🔧 Step 9: Repairing Defender component store..." -ForegroundColor Yellow
try {
    DISM /Online /Cleanup-Image /RestoreHealth 2>&1 | ForEach-Object { 
        if ($_ -match "\d+\.\d+%") { Write-Host "  $($_.Trim())" -ForegroundColor Gray -NoNewline; Write-Host "`r" -NoNewline }
    }
    Write-Host ""
    Write-Host "  ✅ DISM repair complete" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️ DISM had issues" -ForegroundColor Gray
}
Write-Host ""

# ==========================================
# Step 10: Restart all services
# ==========================================
Write-Host "🔧 Step 10: Restarting services..." -ForegroundColor Yellow
$services = @('wscsvc', 'WinDefend', 'WdNisSvc', 'SecurityHealthService')
foreach ($svc in $services) {
    try {
        Start-Service -Name $svc -ErrorAction SilentlyContinue
        $status = (Get-Service -Name $svc -ErrorAction SilentlyContinue).Status
        if ($status -eq 'Running') {
            Write-Host "  ✅ $svc running" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️ $svc status: $status" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ⚠️ Could not start $svc" -ForegroundColor Gray
    }
}
Write-Host ""

# ==========================================
# Step 11: Enable all protection features
# ==========================================
Write-Host "🔧 Step 11: Enabling all protection features..." -ForegroundColor Yellow
try {
    Set-MpPreference -DisableRealtimeMonitoring $false -ErrorAction SilentlyContinue
    Set-MpPreference -DisableBehaviorMonitoring $false -ErrorAction SilentlyContinue
    Set-MpPreference -DisableIOAVProtection $false -ErrorAction SilentlyContinue
    Set-MpPreference -DisableScriptScanning $false -ErrorAction SilentlyContinue
    Set-MpPreference -UILockdown $false -ErrorAction SilentlyContinue
    Write-Host "  ✅ All protection features enabled" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️ Some features could not be enabled" -ForegroundColor Gray
}
Write-Host ""

# ==========================================
# Step 12: Verify final status
# ==========================================
Write-Host "🔧 Step 12: Verifying status..." -ForegroundColor Yellow
Write-Host ""
try {
    $mpStatus = Get-MpComputerStatus -ErrorAction Stop
    
    Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "       🛡️ DEFENDER STATUS REPORT" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
    
    $checks = @(
        @{ Name = "Antivirus Enabled";       Value = $mpStatus.AntivirusEnabled },
        @{ Name = "Real-Time Protection";    Value = $mpStatus.RealTimeProtectionEnabled },
        @{ Name = "Behavior Monitor";        Value = $mpStatus.BehaviorMonitorEnabled },
        @{ Name = "Access Protection";       Value = $mpStatus.OnAccessProtectionEnabled },
        @{ Name = "Antispyware Enabled";     Value = $mpStatus.AntispywareEnabled }
    )
    
    $allGood = $true
    foreach ($check in $checks) {
        if ($check.Value) {
            Write-Host "  ✅ $($check.Name)" -ForegroundColor Green
        } else {
            Write-Host "  ❌ $($check.Name)" -ForegroundColor Red
            $allGood = $false
        }
    }
    
    Write-Host ""
    Write-Host "  📅 Definitions: $($mpStatus.AntivirusSignatureVersion)" -ForegroundColor Gray
    Write-Host "  📅 Last Updated: $($mpStatus.AntivirusSignatureLastUpdated)" -ForegroundColor Gray
    Write-Host "  📅 Engine:       $($mpStatus.AMEngineVersion)" -ForegroundColor Gray
    Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
    
    # Check if Windows Security app works
    Write-Host ""
    $secApp = Get-AppxPackage -Name "Microsoft.SecHealthUI" -ErrorAction SilentlyContinue
    if ($secApp) {
        Write-Host "  ✅ Windows Security app is registered" -ForegroundColor Green
        Write-Host "  📦 Version: $($secApp.Version)" -ForegroundColor Gray
    } else {
        Write-Host "  ❌ Windows Security app NOT registered" -ForegroundColor Red
        $allGood = $false
    }
    
} catch {
    Write-Host "  ❌ Could not get Defender status: $_" -ForegroundColor Red
    $allGood = $false
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  🛡️ Repair Complete!" -ForegroundColor Green
if ($allGood) {
    Write-Host "  ✅ All checks passed" -ForegroundColor Green
} else {
    Write-Host "  ⚠️ Some issues remain" -ForegroundColor Yellow
    Write-Host "  ⚠️ A REBOOT IS REQUIRED" -ForegroundColor Yellow
    Write-Host "" 
    Write-Host "  If still broken after reboot:" -ForegroundColor Gray
    Write-Host "  1. Run this script again" -ForegroundColor Gray
    Write-Host "  2. Check Windows Update" -ForegroundColor Gray
    Write-Host "  3. Try: sfc /scannow" -ForegroundColor Gray
    Write-Host "  4. Last resort: DISM /Online /Cleanup-Image /StartComponentCleanup" -ForegroundColor Gray
}
Write-Host "========================================" -ForegroundColor Green

} catch {
    Write-Host ""
    Write-Host "❌ An error occurred: $_" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor Gray
    Write-Host ""
} finally {
    Write-Host ""
    Write-Host "Press Enter to close..." -ForegroundColor Gray
    Read-Host
}