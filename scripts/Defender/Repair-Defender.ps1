# NAME: 🛡️ Repair Windows Defender
# DESCRIPTION: Fully repairs Windows Defender - resets services, policies, definitions, and registration
# STYLE: Warning.TButton
# INTERACTIVE: true

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  🛡️ Windows Defender Full Repair" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check for admin
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "❌ This script must be run as Administrator!" -ForegroundColor Red
    Pause
    exit 1
}

# ==========================================
# Step 1: Stop Defender Services
# ==========================================
Write-Host "🔧 Step 1: Stopping Defender services..." -ForegroundColor Yellow
$services = @('WinDefend', 'WdNisSvc', 'SecurityHealthService', 'wscsvc')
foreach ($svc in $services) {
    try {
        $service = Get-Service -Name $svc -ErrorAction SilentlyContinue
        if ($service -and $service.Status -eq 'Running') {
            Stop-Service -Name $svc -Force -ErrorAction SilentlyContinue
            Write-Host "  ⏹️ Stopped $svc" -ForegroundColor Gray
        } else {
            Write-Host "  ⚠️ $svc not running or not found" -ForegroundColor Gray
        }
    } catch {
        Write-Host "  ⚠️ Could not stop $svc (may be protected)" -ForegroundColor Gray
    }
}
Write-Host ""

# ==========================================
# Step 2: Re-register Defender DLLs
# ==========================================
Write-Host "🔧 Step 2: Re-registering Defender components..." -ForegroundColor Yellow
$dlls = @(
    "$env:ProgramFiles\Windows Defender\MpClient.dll",
    "$env:ProgramFiles\Windows Defender\MpCmdRun.exe",
    "$env:ProgramFiles\Windows Defender\MsMpEng.exe"
)
foreach ($dll in $dlls) {
    if (Test-Path $dll) {
        try {
            regsvr32.exe /s $dll 2>$null
            Write-Host "  ✅ Registered $([System.IO.Path]::GetFileName($dll))" -ForegroundColor Gray
        } catch {
            Write-Host "  ⚠️ Could not register $([System.IO.Path]::GetFileName($dll))" -ForegroundColor Gray
        }
    }
}
Write-Host ""

# ==========================================
# Step 3: Reset Defender Registry Settings
# ==========================================
Write-Host "🔧 Step 3: Resetting Defender registry settings..." -ForegroundColor Yellow

# Remove policies that may have disabled Defender
$policyPaths = @(
    "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender",
    "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection",
    "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender\Spynet",
    "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender\MpEngine"
)

foreach ($path in $policyPaths) {
    if (Test-Path $path) {
        try {
            # Remove DisableAntiSpyware
            Remove-ItemProperty -Path $path -Name "DisableAntiSpyware" -Force -ErrorAction SilentlyContinue
            Remove-ItemProperty -Path $path -Name "DisableAntiVirus" -Force -ErrorAction SilentlyContinue
            Remove-ItemProperty -Path $path -Name "DisableRealtimeMonitoring" -Force -ErrorAction SilentlyContinue
            Remove-ItemProperty -Path $path -Name "DisableBehaviorMonitoring" -Force -ErrorAction SilentlyContinue
            Remove-ItemProperty -Path $path -Name "DisableOnAccessProtection" -Force -ErrorAction SilentlyContinue
            Remove-ItemProperty -Path $path -Name "DisableScanOnRealtimeEnable" -Force -ErrorAction SilentlyContinue
            Remove-ItemProperty -Path $path -Name "DisableIOAVProtection" -Force -ErrorAction SilentlyContinue
            Write-Host "  ✅ Cleaned $path" -ForegroundColor Gray
        } catch {
            Write-Host "  ⚠️ Could not clean $path" -ForegroundColor Gray
        }
    }
}
Write-Host ""

# ==========================================
# Step 4: Reset Windows Security App
# ==========================================
Write-Host "🔧 Step 4: Resetting Windows Security app..." -ForegroundColor Yellow
try {
    Get-AppxPackage -Name "Microsoft.SecHealthUI" -ErrorAction SilentlyContinue | Reset-AppxPackage -ErrorAction SilentlyContinue
    Write-Host "  ✅ Windows Security app reset" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️ Reset-AppxPackage not available, trying re-register..." -ForegroundColor Gray
    try {
        Get-AppxPackage -Name "Microsoft.SecHealthUI" -ErrorAction SilentlyContinue | 
            ForEach-Object { Add-AppxPackage -DisableDevelopmentMode -Register "$($_.InstallLocation)\AppXManifest.xml" -ErrorAction SilentlyContinue }
        Write-Host "  ✅ Windows Security app re-registered" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠️ Could not re-register Windows Security app" -ForegroundColor Gray
    }
}
Write-Host ""

# ==========================================
# Step 5: Repair WMI Repository
# ==========================================
Write-Host "🔧 Step 5: Repairing WMI repository..." -ForegroundColor Yellow
try {
    winmgmt /verifyrepository | Out-Null
    $verify = winmgmt /verifyrepository 2>&1
    if ($verify -match "not consistent|inconsistent") {
        Write-Host "  ⚠️ WMI repository inconsistent - rebuilding..." -ForegroundColor Yellow
        winmgmt /salvagerepository | Out-Null
        Write-Host "  ✅ WMI repository rebuilt" -ForegroundColor Green
    } else {
        Write-Host "  ✅ WMI repository is consistent" -ForegroundColor Green
    }
} catch {
    Write-Host "  ⚠️ Could not verify WMI repository" -ForegroundColor Gray
}
Write-Host ""

# ==========================================
# Step 6: Run SFC and DISM Repairs
# ==========================================
Write-Host "🔧 Step 6: Running system file repairs (this may take a few minutes)..." -ForegroundColor Yellow
Write-Host "  🔄 Running DISM health restore..." -ForegroundColor Gray
try {
    $dism = DISM /Online /Cleanup-Image /RestoreHealth 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ DISM repair completed" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️ DISM completed with warnings" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠️ DISM failed: $_" -ForegroundColor Gray
}

Write-Host "  🔄 Running SFC scan..." -ForegroundColor Gray
try {
    $sfc = sfc /scannow 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ SFC scan completed" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️ SFC completed with issues" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠️ SFC failed: $_" -ForegroundColor Gray
}
Write-Host ""

# ==========================================
# Step 7: Remove and Update Definitions
# ==========================================
Write-Host "🔧 Step 7: Updating virus definitions..." -ForegroundColor Yellow
$mpCmdRun = "$env:ProgramFiles\Windows Defender\MpCmdRun.exe"
if (Test-Path $mpCmdRun) {
    try {
        Write-Host "  🗑️ Removing old definitions..." -ForegroundColor Gray
        & $mpCmdRun -RemoveDefinitions -All 2>$null
        Write-Host "  📥 Downloading latest definitions..." -ForegroundColor Gray
        & $mpCmdRun -SignatureUpdate 2>$null
        Write-Host "  ✅ Definitions updated" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠️ Could not update definitions" -ForegroundColor Gray
    }
} else {
    Write-Host "  ⚠️ MpCmdRun.exe not found" -ForegroundColor Gray
}
Write-Host ""

# ==========================================
# Step 8: Restart Defender Services
# ==========================================
Write-Host "🔧 Step 8: Starting Defender services..." -ForegroundColor Yellow
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
# Step 9: Enable Real-Time Protection
# ==========================================
Write-Host "🔧 Step 9: Enabling Real-Time Protection..." -ForegroundColor Yellow
try {
    Set-MpPreference -DisableRealtimeMonitoring $false -ErrorAction Stop
    Set-MpPreference -DisableBehaviorMonitoring $false -ErrorAction Stop
    Set-MpPreference -DisableIOAVProtection $false -ErrorAction Stop
    Set-MpPreference -DisableScriptScanning $false -ErrorAction Stop
    Write-Host "  ✅ Real-Time Protection enabled" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️ Could not enable some features: $_" -ForegroundColor Gray
}
Write-Host ""

# ==========================================
# Step 10: Verify Defender Status
# ==========================================
Write-Host "🔧 Step 10: Verifying Defender status..." -ForegroundColor Yellow
try {
    $mpStatus = Get-MpComputerStatus -ErrorAction Stop
    
    Write-Host ""
    Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "       🛡️ DEFENDER STATUS REPORT" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
    
    $checks = @(
        @{ Name = "Antivirus Enabled";       Value = $mpStatus.AntivirusEnabled },
        @{ Name = "Real-Time Protection";    Value = $mpStatus.RealTimeProtectionEnabled },
        @{ Name = "Behavior Monitor";        Value = $mpStatus.BehaviorMonitorEnabled },
        @{ Name = "Access Protection";       Value = $mpStatus.OnAccessProtectionEnabled },
        @{ Name = "Antispyware Enabled";     Value = $mpStatus.AntispywareEnabled },
        @{ Name = "NIS Enabled";             Value = $mpStatus.NISEnabled }
    )
    
    foreach ($check in $checks) {
        if ($check.Value) {
            Write-Host "  ✅ $($check.Name)" -ForegroundColor Green
        } else {
            Write-Host "  ❌ $($check.Name)" -ForegroundColor Red
        }
    }
    
    Write-Host ""
    Write-Host "  📅 Definitions Version:  $($mpStatus.AntivirusSignatureVersion)" -ForegroundColor Gray
    Write-Host "  📅 Definitions Updated:  $($mpStatus.AntivirusSignatureLastUpdated)" -ForegroundColor Gray
    Write-Host "  📅 Engine Version:       $($mpStatus.AMEngineVersion)" -ForegroundColor Gray
    Write-Host "  📅 Product Version:      $($mpStatus.AMProductVersion)" -ForegroundColor Gray
    Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
    
} catch {
    Write-Host "  ❌ Could not get Defender status: $_" -ForegroundColor Red
    Write-Host "  ⚠️ A reboot may be required" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  🛡️ Defender Repair Complete!" -ForegroundColor Green
Write-Host "  ⚠️ A restart is recommended" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Pause