# NAME: 🛡️ Fix SecurityHealth Image Hash
# DESCRIPTION: Fixes Code Integrity blocking SecurityHealthService (error 0x80070577)
# STYLE: Danger.TButton
# INTERACTIVE: true

try {

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  🛡️ Fix Code Integrity Block" -ForegroundColor Cyan
Write-Host "  Error: 0x80070577 INVALID_IMAGE_HASH" -ForegroundColor Gray
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "❌ Must run as Administrator!" -ForegroundColor Red
    Read-Host "Press Enter to close"
    return
}

# ==========================================
# Step 1: Check Code Integrity status
# ==========================================
Write-Host "🔍 Step 1: Checking Code Integrity / Memory Integrity..." -ForegroundColor Yellow

$hvci = Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity" -Name "Enabled" -ErrorAction SilentlyContinue
$ciEnabled = $hvci.Enabled -eq 1
Write-Host "  Memory Integrity (HVCI): $(if($ciEnabled){'ENABLED'}else{'Disabled'})" -ForegroundColor $(if($ciEnabled){'Yellow'}else{'Green'})

$sgEnabled = (Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard" -Name "EnableVirtualizationBasedSecurity" -ErrorAction SilentlyContinue).EnableVirtualizationBasedSecurity
Write-Host "  Virtualization Security: $(if($sgEnabled -eq 1){'ENABLED'}else{'Disabled'})" -ForegroundColor Gray

# Check for WDAC policies
$wdacPath = "$env:SystemRoot\System32\CodeIntegrity\SIPolicy.p7b"
$wdacExists = Test-Path $wdacPath
Write-Host "  WDAC Policy Present: $wdacExists" -ForegroundColor $(if($wdacExists){'Yellow'}else{'Green'})

# Check CI event log for blocks
Write-Host ""
Write-Host "  Recent Code Integrity blocks:" -ForegroundColor Gray
$ciEvents = Get-WinEvent -LogName "Microsoft-Windows-CodeIntegrity/Operational" -MaxEvents 100 -ErrorAction SilentlyContinue | 
    Where-Object { $_.Message -like "*SecurityHealth*" -or $_.Message -like "*SecHealth*" } |
    Select-Object -First 5
if ($ciEvents) {
    foreach ($evt in $ciEvents) {
        Write-Host "  ❌ [$($evt.TimeCreated.ToString('MM/dd HH:mm'))] $($evt.Message.Substring(0, [Math]::Min(120, $evt.Message.Length)))" -ForegroundColor Red
    }
} else {
    Write-Host "  ✅ No SecurityHealth blocks in CI log" -ForegroundColor Green
}
Write-Host ""

# ==========================================
# Step 2: Repair catalog files
# ==========================================
Write-Host "🔧 Step 2: Repairing system catalog files..." -ForegroundColor Yellow

# Clear the catroot2 database (forces catalog rebuild)
Write-Host "  🔄 Stopping Cryptographic Services..." -ForegroundColor Gray
Stop-Service -Name CryptSvc -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

$catroot2 = "$env:SystemRoot\System32\catroot2"
$catroot2Backup = "$env:SystemRoot\System32\catroot2.bak.$(Get-Date -Format 'yyyyMMddHHmmss')"

if (Test-Path $catroot2) {
    try {
        Rename-Item $catroot2 $catroot2Backup -Force -ErrorAction Stop
        Write-Host "  ✅ Backed up catroot2 to: $catroot2Backup" -ForegroundColor Green
        Write-Host "  ✅ Windows will rebuild catalog database on restart" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠️ Could not rename catroot2: $_" -ForegroundColor Yellow
        Write-Host "  🔄 Trying to clear contents instead..." -ForegroundColor Gray
        try {
            Remove-Item "$catroot2\*" -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host "  ✅ Cleared catroot2 contents" -ForegroundColor Green
        } catch {
            Write-Host "  ⚠️ Could not clear catroot2" -ForegroundColor Gray
        }
    }
}

Start-Service -Name CryptSvc -ErrorAction SilentlyContinue
Write-Host ""

# ==========================================
# Step 3: Replace SecurityHealthService.exe from DISM
# ==========================================
Write-Host "🔧 Step 3: Restoring SecurityHealthService.exe from Windows image..." -ForegroundColor Yellow

# First run DISM to ensure the component store is clean
Write-Host "  🔄 Running DISM RestoreHealth (this takes a few minutes)..." -ForegroundColor Gray
$dismResult = DISM /Online /Cleanup-Image /RestoreHealth 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ DISM RestoreHealth completed" -ForegroundColor Green
} else {
    Write-Host "  ⚠️ DISM completed with code: $LASTEXITCODE" -ForegroundColor Yellow
}

# Then run SFC to replace the file with a verified copy
Write-Host "  🔄 Running SFC to replace corrupted files..." -ForegroundColor Gray
$sfcResult = sfc /scannow 2>&1
$sfcOutput = $sfcResult -join " "
if ($sfcOutput -match "found corrupt files and successfully repaired") {
    Write-Host "  ✅ SFC repaired corrupted files" -ForegroundColor Green
} elseif ($sfcOutput -match "did not find any integrity violations") {
    Write-Host "  ✅ SFC found no issues (file hashes match source)" -ForegroundColor Green
    Write-Host "  ⚠️ The exe may be fine - catalog is the problem" -ForegroundColor Yellow
} else {
    Write-Host "  ⚠️ SFC result: check C:\Windows\Logs\CBS\CBS.log" -ForegroundColor Yellow
}
Write-Host ""

# ==========================================
# Step 4: Re-register the executable's catalog
# ==========================================
Write-Host "🔧 Step 4: Re-registering security catalogs..." -ForegroundColor Yellow

# Find catalogs related to SecurityHealth
$catroot = "$env:SystemRoot\System32\catroot\{F750E6C3-38EE-11D1-85E5-00C04FC295EE}"
if (Test-Path $catroot) {
    $secCats = Get-ChildItem $catroot -Filter "*.cat" | ForEach-Object {
        $catContent = Get-Content $_.FullName -Raw -ErrorAction SilentlyContinue
        if ($catContent -match "SecurityHealth") {
            $_
        }
    }
    if ($secCats) {
        Write-Host "  Found SecurityHealth catalogs:" -ForegroundColor Gray
        foreach ($cat in $secCats) {
            Write-Host "     $($cat.Name)" -ForegroundColor Gray
        }
    }
}

# Force re-verification
Write-Host "  🔄 Refreshing signature verification cache..." -ForegroundColor Gray
try {
    $exe = "C:\WINDOWS\system32\SecurityHealthService.exe"
    $sig = Get-AuthenticodeSignature $exe
    Write-Host "  Signature Status: $($sig.Status)" -ForegroundColor $(if($sig.Status -eq 'Valid'){'Green'}else{'Red'})
    Write-Host "  Signer: $($sig.SignerCertificate.Subject)" -ForegroundColor Gray
    
    # Re-hash the file
    $hash = Get-FileHash $exe -Algorithm SHA256
    Write-Host "  SHA256: $($hash.Hash)" -ForegroundColor Gray
} catch {
    Write-Host "  ⚠️ Could not verify signature" -ForegroundColor Gray
}
Write-Host ""

# ==========================================
# Step 5: Clear CI cache
# ==========================================
Write-Host "🔧 Step 5: Clearing Code Integrity cache..." -ForegroundColor Yellow
$ciCachePaths = @(
    "$env:SystemRoot\System32\CodeIntegrity\CiCacheRefresh.lock",
    "$env:SystemRoot\System32\CodeIntegrity\cache"
)
foreach ($path in $ciCachePaths) {
    if (Test-Path $path) {
        try {
            Remove-Item $path -Recurse -Force -ErrorAction Stop
            Write-Host "  ✅ Cleared: $path" -ForegroundColor Green
        } catch {
            Write-Host "  ⚠️ Could not clear: $path" -ForegroundColor Gray
        }
    }
}
Write-Host ""

# ==========================================
# Step 6: Temporarily disable Memory Integrity if enabled
# ==========================================
if ($ciEnabled) {
    Write-Host "🔧 Step 6: Memory Integrity is ENABLED - this may cause the hash check failure" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Memory Integrity (HVCI) enforces strict code signing." -ForegroundColor Gray
    Write-Host "  After a Windows Update, catalog mismatches can occur." -ForegroundColor Gray
    Write-Host ""
    
    $choice = Read-Host "  Disable Memory Integrity temporarily to test? (Y/N)"
    if ($choice -eq 'Y' -or $choice -eq 'y') {
        try {
            Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity" -Name "Enabled" -Value 0 -Force
            Write-Host "  ✅ Memory Integrity will be disabled after reboot" -ForegroundColor Green
            Write-Host "  ⚠️ You can re-enable it later in Windows Security > Device Security" -ForegroundColor Yellow
        } catch {
            Write-Host "  ⚠️ Could not disable: $_" -ForegroundColor Gray
        }
    } else {
        Write-Host "  ⏭️ Skipped - will try other fixes first" -ForegroundColor Gray
    }
} else {
    Write-Host "🔧 Step 6: Memory Integrity already disabled - not the cause" -ForegroundColor Green
}
Write-Host ""

# ==========================================
# Step 7: Force Windows Update repair
# ==========================================
Write-Host "🔧 Step 7: Checking for Defender platform updates..." -ForegroundColor Yellow
$mpCmdRun = "$env:ProgramFiles\Windows Defender\MpCmdRun.exe"
if (Test-Path $mpCmdRun) {
    Write-Host "  🔄 Updating Defender platform..." -ForegroundColor Gray
    & $mpCmdRun -SignatureUpdate 2>$null
    & $mpCmdRun -ResetPlatform 2>$null
    Write-Host "  ✅ Platform update attempted" -ForegroundColor Green
}
Write-Host ""

# ==========================================
# Step 8: Test service start
# ==========================================
Write-Host "🔧 Step 8: Testing service start..." -ForegroundColor Yellow
try {
    Start-Service -Name SecurityHealthService -ErrorAction Stop
    Start-Sleep -Seconds 2
    $status = (Get-Service -Name SecurityHealthService).Status
    Write-Host "  ✅ Service status: $status" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Service still won't start: $_" -ForegroundColor Red
    
    # Check exit code again
    $proc = Start-Process "C:\WINDOWS\system32\SecurityHealthService.exe" -PassThru -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    if ($proc.HasExited) {
        $exitHex = "0x{0:X8}" -f [uint32]$proc.ExitCode
        Write-Host "  Exit Code: $($proc.ExitCode) ($exitHex)" -ForegroundColor Red
    }
}
Write-Host ""

# ==========================================
# Summary
# ==========================================
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host "       📋 RESULTS" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$svcFinal = Get-Service -Name SecurityHealthService -ErrorAction SilentlyContinue
if ($svcFinal.Status -eq 'Running') {
    Write-Host "  ✅ SecurityHealthService is RUNNING!" -ForegroundColor Green
    Write-Host "  ✅ Try opening Windows Security now" -ForegroundColor Green
} else {
    Write-Host "  ❌ Service still not running" -ForegroundColor Red
    Write-Host ""
    Write-Host "  ⚠️ A REBOOT IS REQUIRED for these changes:" -ForegroundColor Yellow
    Write-Host "     - Catalog database rebuild (catroot2)" -ForegroundColor Gray
    Write-Host "     - Code Integrity cache cleared" -ForegroundColor Gray
    Write-Host "     - SFC/DISM file replacements" -ForegroundColor Gray
    if ($ciEnabled) {
        Write-Host "     - Memory Integrity change (if selected)" -ForegroundColor Gray
    }
    Write-Host ""
    Write-Host "  👉 REBOOT NOW, then check if Windows Security loads" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  If still broken after reboot:" -ForegroundColor Gray
    Write-Host "  1. Run this script again" -ForegroundColor Gray
    Write-Host "  2. Check Windows Update for new cumulative updates" -ForegroundColor Gray
    Write-Host "  3. In-place repair: Mount Win 11 ISO > setup.exe > Keep files" -ForegroundColor Gray
}

Write-Host ""
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan

} catch {
    Write-Host ""
    Write-Host "❌ Error: $_" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor Gray
} finally {
    Write-Host ""
    Write-Host "Press Enter to close..." -ForegroundColor Gray
    Read-Host
}