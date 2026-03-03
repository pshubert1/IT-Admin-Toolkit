# NAME: 🔍 Diagnose Defender Issues
# DESCRIPTION: Finds the root cause when Windows Security won't load
# STYLE: Dark.TButton
# INTERACTIVE: true

try {

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  🔍 Windows Defender Diagnostics" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ==========================================
# Check 1: Third-Party Antivirus
# ==========================================
Write-Host "🔍 Check 1: Third-Party Antivirus..." -ForegroundColor Yellow
$avProducts = Get-CimInstance -Namespace "root\SecurityCenter2" -ClassName "AntivirusProduct" -ErrorAction SilentlyContinue
$thirdPartyAV = $false
if ($avProducts) {
    foreach ($av in $avProducts) {
        if ($av.displayName -notlike "*Windows Defender*" -and $av.displayName -notlike "*Microsoft Defender*") {
            Write-Host "  ⚠️ FOUND: $($av.displayName)" -ForegroundColor Red
            Write-Host "     State: $($av.productState)" -ForegroundColor Gray
            $thirdPartyAV = $true
        } else {
            Write-Host "  ✅ $($av.displayName)" -ForegroundColor Green
        }
    }
    if ($thirdPartyAV) {
        Write-Host ""
        Write-Host "  ❗ THIRD-PARTY AV DETECTED - This is likely the cause!" -ForegroundColor Red
        Write-Host "  ❗ Uninstall it completely, reboot, then try again" -ForegroundColor Red
    }
} else {
    Write-Host "  ⚠️ Could not query SecurityCenter2" -ForegroundColor Gray
}
Write-Host ""

# ==========================================
# Check 2: Defender Services
# ==========================================
Write-Host "🔍 Check 2: Defender Services..." -ForegroundColor Yellow
$services = @(
    @{ Name = "WinDefend";             Display = "Windows Defender Service" },
    @{ Name = "WdNisSvc";              Display = "Defender Network Inspection" },
    @{ Name = "SecurityHealthService"; Display = "Security Health Service" },
    @{ Name = "wscsvc";                Display = "Security Center" },
    @{ Name = "SgrmBroker";            Display = "System Guard Runtime Monitor" },
    @{ Name = "mpssvc";                Display = "Windows Firewall" }
)
foreach ($svc in $services) {
    $service = Get-Service -Name $svc.Name -ErrorAction SilentlyContinue
    if ($service) {
        $startType = (Get-CimInstance -ClassName Win32_Service -Filter "Name='$($svc.Name)'" -ErrorAction SilentlyContinue).StartMode
        if ($service.Status -eq 'Running') {
            Write-Host "  ✅ $($svc.Display): Running ($startType)" -ForegroundColor Green
        } else {
            Write-Host "  ❌ $($svc.Display): $($service.Status) ($startType)" -ForegroundColor Red
        }
    } else {
        Write-Host "  ❌ $($svc.Display): NOT FOUND" -ForegroundColor Red
    }
}
Write-Host ""

# ==========================================
# Check 3: Defender Registry Policies
# ==========================================
Write-Host "🔍 Check 3: Registry Policies (GPO/MDM that disable Defender)..." -ForegroundColor Yellow
$disabledByPolicy = $false

$regChecks = @(
    @{ Path = "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender"; Name = "DisableAntiSpyware" },
    @{ Path = "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender"; Name = "DisableAntiVirus" },
    @{ Path = "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection"; Name = "DisableRealtimeMonitoring" },
    @{ Path = "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection"; Name = "DisableBehaviorMonitoring" },
    @{ Path = "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender Security Center"; Name = "DisableVirusUI" },
    @{ Path = "HKLM:\SOFTWARE\Microsoft\Windows Defender"; Name = "DisableAntiSpyware" },
    @{ Path = "HKLM:\SOFTWARE\Microsoft\Windows Defender"; Name = "DisableAntiVirus" }
)

foreach ($reg in $regChecks) {
    try {
        $val = Get-ItemProperty -Path $reg.Path -Name $reg.Name -ErrorAction SilentlyContinue
        if ($val -and $val.$($reg.Name) -eq 1) {
            Write-Host "  ❌ DISABLED: $($reg.Path)\$($reg.Name) = 1" -ForegroundColor Red
            $disabledByPolicy = $true
        }
    } catch {}
}

if (-not $disabledByPolicy) {
    Write-Host "  ✅ No disabling policies found" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "  ❗ DEFENDER IS DISABLED BY POLICY!" -ForegroundColor Red
    Write-Host "  ❗ This may be from GPO, Intune, or malware" -ForegroundColor Red
}
Write-Host ""

# ==========================================
# Check 4: Windows Security App Package
# ==========================================
Write-Host "🔍 Check 4: Windows Security App Package..." -ForegroundColor Yellow
$secApp = Get-AppxPackage -Name "Microsoft.SecHealthUI" -AllUsers -ErrorAction SilentlyContinue
if ($secApp) {
    Write-Host "  ✅ App installed: $($secApp.Version)" -ForegroundColor Green
    Write-Host "     Location: $($secApp.InstallLocation)" -ForegroundColor Gray
    Write-Host "     Status: $($secApp.Status)" -ForegroundColor Gray
    
    if (Test-Path $secApp.InstallLocation) {
        Write-Host "  ✅ Install location exists" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Install location MISSING" -ForegroundColor Red
    }
} else {
    Write-Host "  ❌ Windows Security app NOT INSTALLED" -ForegroundColor Red
}

# Check SystemApps folder
$sysAppPaths = Get-ChildItem "C:\Windows\SystemApps" -Directory -Filter "*SecHealth*" -ErrorAction SilentlyContinue
if ($sysAppPaths) {
    foreach ($p in $sysAppPaths) {
        Write-Host "  📁 Found: $($p.FullName)" -ForegroundColor Gray
        $manifest = Join-Path $p.FullName "AppXManifest.xml"
        if (Test-Path $manifest) {
            Write-Host "  ✅ Manifest exists" -ForegroundColor Green
        } else {
            Write-Host "  ❌ Manifest MISSING" -ForegroundColor Red
        }
    }
} else {
    Write-Host "  ❌ No SecHealth folder in SystemApps" -ForegroundColor Red
}
Write-Host ""

# ==========================================
# Check 5: Component Store Health
# ==========================================
Write-Host "🔍 Check 5: Component Store Health..." -ForegroundColor Yellow
try {
    $dismCheck = DISM /Online /Cleanup-Image /CheckHealth 2>&1
    $dismOutput = $dismCheck -join " "
    if ($dismOutput -match "repairable|corrupted") {
        Write-Host "  ❌ Component store is CORRUPTED" -ForegroundColor Red
    } elseif ($dismOutput -match "healthy|No component store corruption") {
        Write-Host "  ✅ Component store is healthy" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️ Could not determine: $dismOutput" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠️ DISM check failed" -ForegroundColor Gray
}
Write-Host ""

# ==========================================
# Check 6: Windows Version
# ==========================================
Write-Host "🔍 Check 6: Windows Version..." -ForegroundColor Yellow
$os = Get-CimInstance -ClassName Win32_OperatingSystem
$build = [System.Environment]::OSVersion.Version.Build
Write-Host "  📌 OS: $($os.Caption)" -ForegroundColor Gray
Write-Host "  📌 Version: $($os.Version)" -ForegroundColor Gray
Write-Host "  📌 Build: $build" -ForegroundColor Gray
if ($build -lt 19041) {
    Write-Host "  ⚠️ Build is old - consider updating Windows" -ForegroundColor Yellow
}
Write-Host ""

# ==========================================
# Check 7: Defender Platform Files
# ==========================================
Write-Host "🔍 Check 7: Defender Platform Files..." -ForegroundColor Yellow
$criticalFiles = @(
    "$env:ProgramFiles\Windows Defender\MsMpEng.exe",
    "$env:ProgramFiles\Windows Defender\MpCmdRun.exe",
    "$env:ProgramFiles\Windows Defender\MSASCuiL.exe",
    "$env:ProgramData\Microsoft\Windows Defender\Platform"
)
foreach ($file in $criticalFiles) {
    if (Test-Path $file) {
        Write-Host "  ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ MISSING: $file" -ForegroundColor Red
    }
}

# Check platform versions
$platformPath = "$env:ProgramData\Microsoft\Windows Defender\Platform"
if (Test-Path $platformPath) {
    $platforms = Get-ChildItem $platformPath -Directory | Sort-Object Name -Descending
    Write-Host "  📌 Platform versions:" -ForegroundColor Gray
    foreach ($p in $platforms | Select-Object -First 3) {
        Write-Host "     $($p.Name)" -ForegroundColor Gray
    }
}
Write-Host ""

# ==========================================
# Check 8: Defender Preferences
# ==========================================
Write-Host "🔍 Check 8: Defender Preferences..." -ForegroundColor Yellow
try {
    $prefs = Get-MpPreference -ErrorAction Stop
    Write-Host "  Real-Time Monitoring Disabled:  $($prefs.DisableRealtimeMonitoring)" -ForegroundColor $(if($prefs.DisableRealtimeMonitoring){'Red'}else{'Green'})
    Write-Host "  Behavior Monitoring Disabled:   $($prefs.DisableBehaviorMonitoring)" -ForegroundColor $(if($prefs.DisableBehaviorMonitoring){'Red'}else{'Green'})
    Write-Host "  IOAV Protection Disabled:       $($prefs.DisableIOAVProtection)" -ForegroundColor $(if($prefs.DisableIOAVProtection){'Red'}else{'Green'})
    Write-Host "  Tamper Protection Source:        $($prefs.TamperProtectionSource)" -ForegroundColor Gray
    Write-Host "  UI Lockdown:                     $($prefs.UILockdown)" -ForegroundColor $(if($prefs.UILockdown){'Red'}else{'Green'})
} catch {
    Write-Host "  ❌ Cannot read preferences: $_" -ForegroundColor Red
}
Write-Host ""

# ==========================================
# Check 9: Event Log Errors
# ==========================================
Write-Host "🔍 Check 9: Recent Defender Errors (last 24h)..." -ForegroundColor Yellow
try {
    $errors = Get-WinEvent -LogName "Microsoft-Windows-Windows Defender/Operational" -MaxEvents 50 -ErrorAction SilentlyContinue | 
        Where-Object { $_.Level -le 2 -and $_.TimeCreated -gt (Get-Date).AddHours(-24) }
    if ($errors) {
        Write-Host "  ⚠️ Found $($errors.Count) errors/warnings:" -ForegroundColor Yellow
        foreach ($err in $errors | Select-Object -First 5) {
            Write-Host "     [$($err.TimeCreated.ToString('HH:mm:ss'))] ID:$($err.Id) - $($err.Message.Substring(0, [Math]::Min(100, $err.Message.Length)))..." -ForegroundColor Gray
        }
    } else {
        Write-Host "  ✅ No recent errors" -ForegroundColor Green
    }
} catch {
    Write-Host "  ⚠️ Could not read event log" -ForegroundColor Gray
}
Write-Host ""

# ==========================================
# Summary & Recommendations
# ==========================================
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host "       📋 DIAGNOSIS SUMMARY" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

if ($thirdPartyAV) {
    Write-Host "  🔴 ROOT CAUSE: Third-party antivirus is installed" -ForegroundColor Red
    Write-Host "     FIX: Fully uninstall the third-party AV, reboot, then" -ForegroundColor Yellow
    Write-Host "          run the Defender repair script" -ForegroundColor Yellow
    Write-Host ""
}

if ($disabledByPolicy) {
    Write-Host "  🔴 ROOT CAUSE: Defender is disabled by Group Policy or MDM" -ForegroundColor Red
    Write-Host "     FIX: Remove the policy or check Intune compliance settings" -ForegroundColor Yellow
    Write-Host "     Run: gpedit.msc > Computer Config > Admin Templates >" -ForegroundColor Gray
    Write-Host "          Windows Components > Microsoft Defender Antivirus" -ForegroundColor Gray
    Write-Host "          Set 'Turn off Microsoft Defender Antivirus' to Not Configured" -ForegroundColor Gray
    Write-Host ""
}

if (-not $thirdPartyAV -and -not $disabledByPolicy) {
    Write-Host "  🟡 No obvious policy or AV conflict found" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Recommended fixes (try in order):" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  1. Re-register ALL system apps (run in admin PowerShell):" -ForegroundColor White
    Write-Host "     Get-AppxPackage -AllUsers | foreach {" -ForegroundColor Gray
    Write-Host "       Add-AppxPackage -DisableDevelopmentMode -Register" -ForegroundColor Gray
    Write-Host '       "$($_.InstallLocation)\AppXManifest.xml" -EA SilentlyContinue}' -ForegroundColor Gray
    Write-Host ""
    Write-Host "  2. Create a new Windows user profile and test there" -ForegroundColor White
    Write-Host "     (If it works = your profile is corrupted)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  3. In-Place Upgrade Repair:" -ForegroundColor White
    Write-Host "     - Download Windows ISO from microsoft.com" -ForegroundColor Gray
    Write-Host "     - Mount ISO, run setup.exe" -ForegroundColor Gray
    Write-Host "     - Choose 'Keep files and apps'" -ForegroundColor Gray
    Write-Host "     - This repairs all system components" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  4. Reset Windows (last resort):" -ForegroundColor White
    Write-Host "     Settings > System > Recovery > Reset this PC" -ForegroundColor Gray
}

Write-Host ""
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan

} catch {
    Write-Host ""
    Write-Host "❌ Diagnostic error: $_" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor Gray
} finally {
    Write-Host ""
    Write-Host "Press Enter to close..." -ForegroundColor Gray
    Read-Host
}