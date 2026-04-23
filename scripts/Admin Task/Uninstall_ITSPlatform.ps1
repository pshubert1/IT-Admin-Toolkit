# NAME: 🗑️ Remove ITSPlatform ULTIMATE
# DESCRIPTION: Full nuclear removal of CW RMM (ITSPlatform) - services, files, all registry keys
# STYLE: Danger.TButton
# INTERACTIVE: true

# ============================================================
#  Remove ITSPlatform - ULTIMATE (SYSTEM Context + Full Nuke)
# ============================================================

#Requires -RunAsAdministrator

$LogPath = "C:\Temp"
$LogFile = Join-Path $LogPath "Remove-ITSPlatform_ULTIMATE_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

if (!(Test-Path $LogPath)) { New-Item -ItemType Directory -Path $LogPath -Force | Out-Null }

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "[$Timestamp] [$Level] $Message"
    Add-Content -Path $LogFile -Value $LogMessage -Force
    $Color = switch ($Level) {
        "ERROR"   { "Red" }
        "WARNING" { "Yellow" }
        "SUCCESS" { "Green" }
        "HEADER"  { "Cyan" }
        default   { "White" }
    }
    Write-Host $LogMessage -ForegroundColor $Color
}

function Remove-RegKeyForced {
    param(
        [string]$KeyPath,
        [string]$RegExePath,
        [string]$PSExecPath
    )

    if (!(Get-Item -Path $KeyPath -ErrorAction SilentlyContinue)) { return }

    Write-Log "  REG DELETE: $KeyPath" "INFO"
    try {
        Remove-Item -Path $KeyPath -Recurse -Force -ErrorAction Stop
        Write-Log "    Removed via PowerShell" "SUCCESS"
    }
    catch {
        Write-Log "    PS failed ($($_.Exception.Message)) - retrying as SYSTEM" "WARNING"
        & $PSExecPath -s -nobanner -AcceptEula reg.exe delete "$RegExePath" /f 2>&1 |
            ForEach-Object { Write-Log "    SYSTEM REG> $_" }
        if (!(Get-Item -Path $KeyPath -ErrorAction SilentlyContinue)) {
            Write-Log "    Removed via SYSTEM reg.exe" "SUCCESS"
        } else {
            Write-Log "    STILL PRESENT: $KeyPath" "ERROR"
        }
    }
}

function Remove-RegValueForced {
    param(
        [string]$KeyPath,
        [string]$ValueName,
        [string]$RegExePath,
        [string]$PSExecPath
    )

    try {
        Remove-ItemProperty -Path $KeyPath -Name $ValueName -Force -ErrorAction Stop
        Write-Log "    Removed value: $ValueName" "SUCCESS"
    }
    catch {
        Write-Log "    PS failed - retrying as SYSTEM" "WARNING"
        & $PSExecPath -s -nobanner -AcceptEula reg.exe delete "$RegExePath" /v "$ValueName" /f 2>&1 |
            ForEach-Object { Write-Log "    SYSTEM REG> $_" }
    }
}

Write-Log "==========================================" "HEADER"
Write-Log "  ITSPLATFORM ULTIMATE REMOVAL" "HEADER"
Write-Log "  Computer:  $env:COMPUTERNAME"
Write-Log "  User:      $env:USERNAME"
Write-Log "  Log:       $LogFile"
Write-Log "==========================================" "HEADER"
Write-Log ""

# ===== PSEXEC DOWNLOAD =====
$PSExecPath  = Join-Path $env:TEMP "PsExec.exe"
$zipPath     = Join-Path $env:TEMP "PSTools.zip"
$extractPath = Join-Path $env:TEMP "PSTools"

if (!(Test-Path $PSExecPath)) {
    Write-Log "Downloading PsExec for SYSTEM context..." "INFO"
    Invoke-WebRequest -Uri "https://download.sysinternals.com/files/PSTools.zip" -OutFile $zipPath -UseBasicParsing
    New-Item -ItemType Directory -Path $extractPath -Force | Out-Null
    Expand-Archive -Path $zipPath -DestinationPath $extractPath -Force
    $src = Join-Path $extractPath "PsExec.exe"
    if (!(Test-Path $src)) { $src = Join-Path $extractPath "psexec.exe" }
    Copy-Item -Path $src -Destination $PSExecPath -Force
    Write-Log "PsExec ready" "SUCCESS"
}

# ===== PHASE 0: SYSTEM CONTEXT SERVICE TERMINATION =====
Write-Log "" "HEADER"
Write-Log "==========================================" "HEADER"
Write-Log "  PHASE 0: STOP & DELETE SERVICES" "HEADER"
Write-Log "==========================================" "HEADER"

$Services = @("ITSPlatform", "ITSPlatformManager", "SAAZOD", "SAAZODBKP")
foreach ($Service in $Services) {
    $svc = Get-Service -Name $Service -ErrorAction SilentlyContinue
    if ($svc) {
        Write-Log "Stopping: $Service ($($svc.Status))" "WARNING"
        & $PSExecPath -s -nobanner -AcceptEula sc.exe stop $Service 2>&1 |
            ForEach-Object { Write-Log "  SYSTEM> $_" }
        Start-Sleep 2
        Write-Log "Deleting: $Service" "WARNING"
        & $PSExecPath -s -nobanner -AcceptEula sc.exe delete $Service 2>&1 |
            ForEach-Object { Write-Log "  SYSTEM> $_" }
    } else {
        Write-Log "Service not found: $Service (OK)" "INFO"
    }
}

# ===== PHASE 1: KILL ALL PROCESSES =====
Write-Log "" "HEADER"
Write-Log "==========================================" "HEADER"
Write-Log "  PHASE 1: KILL PROCESSES" "HEADER"
Write-Log "==========================================" "HEADER"

$TargetPatterns = @("*ITSPlatform*", "*SAAZOD*", "*SAAZODBKP*", "*agentcore*", "*platform-agent*", "*CWRMMAgent*")
$killed = 0

Get-WmiObject Win32_Process | Where-Object {
    $proc = $_
    $TargetPatterns | Where-Object { $proc.Name -like $_ -or $proc.Path -like $_ }
} | ForEach-Object {
    Write-Log "KILL PID $($_.ProcessId): $($_.Name) [$($_.Path)]" "WARNING"
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    $killed++
}

if ($killed -eq 0) { Write-Log "No matching processes found" "INFO" }

Start-Sleep 3

# ===== PHASE 2: PERMISSION TAKEOVER + FOLDER DELETION =====
Write-Log "" "HEADER"
Write-Log "==========================================" "HEADER"
Write-Log "  PHASE 2: FILE & FOLDER REMOVAL" "HEADER"
Write-Log "==========================================" "HEADER"

$Folders = @(
    "C:\Program Files (x86)\ITSPlatform",
    "C:\Program Files (x86)\SAAZOD",
    "C:\Program Files (x86)\SAAZODBKP",
    "C:\Program Files\ITSPlatform",
    "C:\Program Files\SAAZOD",
    "C:\ProgramData\SAAZOD",
    "C:\ProgramData\ITSPlatform",
    "C:\ProgramData\CentraStage",
    "$env:TEMP\ITSPlatform",
    "$env:TEMP\SAAZOD"
)

foreach ($Folder in $Folders) {
    if (Test-Path $Folder) {
        Write-Log "Taking ownership: $Folder" "WARNING"
        takeown /F "$Folder" /R /D Y 2>&1 | Out-Null
        icacls "$Folder" /grant "SYSTEM:(OI)(CI)F" /T /C 2>&1 | Out-Null
        icacls "$Folder" /grant "Administrators:(OI)(CI)F" /T /C 2>&1 | Out-Null
        
        Write-Log "Deleting: $Folder" "WARNING"
        Remove-Item -Path $Folder -Recurse -Force -ErrorAction SilentlyContinue
        
        if (Test-Path $Folder) {
            Write-Log "  PS delete failed - trying SYSTEM context" "WARNING"
            & $PSExecPath -s -nobanner -AcceptEula cmd.exe /c "rmdir /s /q `"$Folder`"" 2>&1 |
                ForEach-Object { Write-Log "  SYSTEM> $_" }
        }
        
        if (Test-Path $Folder) {
            Write-Log "  STILL PRESENT: $Folder (may need reboot)" "ERROR"
        } else {
            Write-Log "  Removed: $Folder" "SUCCESS"
        }
    }
}

# ===== PHASE 3: SCHEDULED TASKS =====
Write-Log "" "HEADER"
Write-Log "==========================================" "HEADER"
Write-Log "  PHASE 3: SCHEDULED TASKS" "HEADER"
Write-Log "==========================================" "HEADER"

$TaskKeywords = @("ITSPlatform", "SAAZOD", "SAAZODBKP", "CentraStage", "ConnectWise RMM", "platform-agent", "CWRMMAgent")

try {
    $tasks = Get-ScheduledTask -ErrorAction SilentlyContinue | Where-Object {
        $tn = $_.TaskName
        $tp = $_.TaskPath
        $TaskKeywords | Where-Object { $tn -like "*$_*" -or $tp -like "*$_*" }
    }
    
    foreach ($task in $tasks) {
        Write-Log "Removing task: $($task.TaskPath)$($task.TaskName)" "WARNING"
        try {
            Unregister-ScheduledTask -TaskName $task.TaskName -TaskPath $task.TaskPath -Confirm:$false -ErrorAction Stop
            Write-Log "  Removed" "SUCCESS"
        } catch {
            Write-Log "  Failed: $_" "ERROR"
        }
    }
    
    if (-not $tasks) { Write-Log "No matching scheduled tasks found" "INFO" }
} catch {
    Write-Log "Scheduled task check failed: $_" "ERROR"
}

# Also check task folders
$TaskFolders = @(
    "C:\Windows\System32\Tasks\ITSPlatform",
    "C:\Windows\System32\Tasks\SAAZOD",
    "C:\Windows\System32\Tasks\CentraStage"
)
foreach ($tf in $TaskFolders) {
    if (Test-Path $tf) {
        Write-Log "Removing task folder: $tf" "WARNING"
        Remove-Item -Path $tf -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# ===== PHASE 4: REGISTRY NUKE =====
Write-Log "" "HEADER"
Write-Log "==========================================" "HEADER"
Write-Log "  PHASE 4: REGISTRY CLEANUP" "HEADER"
Write-Log "==========================================" "HEADER"

# ── 4a: Explicit known keys ──
Write-Log "  4a: Explicit known registry keys" "HEADER"

$ExplicitKeys = [ordered]@{
    # Services (CurrentControlSet)
    "HKLM:\SYSTEM\CurrentControlSet\Services\ITSPlatform"        = "HKLM\SYSTEM\CurrentControlSet\Services\ITSPlatform"
    "HKLM:\SYSTEM\CurrentControlSet\Services\ITSPlatformManager" = "HKLM\SYSTEM\CurrentControlSet\Services\ITSPlatformManager"
    "HKLM:\SYSTEM\CurrentControlSet\Services\SAAZOD"             = "HKLM\SYSTEM\CurrentControlSet\Services\SAAZOD"
    "HKLM:\SYSTEM\CurrentControlSet\Services\SAAZODBKP"          = "HKLM\SYSTEM\CurrentControlSet\Services\SAAZODBKP"

    # Software hive (64-bit)
    "HKLM:\SOFTWARE\ITSPlatform"                                  = "HKLM\SOFTWARE\ITSPlatform"
    "HKLM:\SOFTWARE\SAAZOD"                                       = "HKLM\SOFTWARE\SAAZOD"
    "HKLM:\SOFTWARE\SAAZODBKP"                                    = "HKLM\SOFTWARE\SAAZODBKP"
    "HKLM:\SOFTWARE\ConnectWise"                                  = "HKLM\SOFTWARE\ConnectWise"
    "HKLM:\SOFTWARE\CentraStage"                                  = "HKLM\SOFTWARE\CentraStage"

    # Software hive (WOW6432Node)
    "HKLM:\SOFTWARE\WOW6432Node\ITSPlatform"                     = "HKLM\SOFTWARE\WOW6432Node\ITSPlatform"
    "HKLM:\SOFTWARE\WOW6432Node\SAAZOD"                          = "HKLM\SOFTWARE\WOW6432Node\SAAZOD"
    "HKLM:\SOFTWARE\WOW6432Node\SAAZODBKP"                       = "HKLM\SOFTWARE\WOW6432Node\SAAZODBKP"
    "HKLM:\SOFTWARE\WOW6432Node\ConnectWise"                     = "HKLM\SOFTWARE\WOW6432Node\ConnectWise"
    "HKLM:\SOFTWARE\WOW6432Node\CentraStage"                     = "HKLM\SOFTWARE\WOW6432Node\CentraStage"

    # Event Log sources
    "HKLM:\SYSTEM\CurrentControlSet\Services\EventLog\Application\ITSPlatform"        = "HKLM\SYSTEM\CurrentControlSet\Services\EventLog\Application\ITSPlatform"
    "HKLM:\SYSTEM\CurrentControlSet\Services\EventLog\Application\ITSPlatformManager" = "HKLM\SYSTEM\CurrentControlSet\Services\EventLog\Application\ITSPlatformManager"
    "HKLM:\SYSTEM\CurrentControlSet\Services\EventLog\Application\SAAZOD"             = "HKLM\SYSTEM\CurrentControlSet\Services\EventLog\Application\SAAZOD"
    "HKLM:\SYSTEM\CurrentControlSet\Services\EventLog\Application\SAAZODBKP"          = "HKLM\SYSTEM\CurrentControlSet\Services\EventLog\Application\SAAZODBKP"
    "HKLM:\SYSTEM\CurrentControlSet\Services\EventLog\System\ITSPlatform"             = "HKLM\SYSTEM\CurrentControlSet\Services\EventLog\System\ITSPlatform"
    "HKLM:\SYSTEM\CurrentControlSet\Services\EventLog\System\ITSPlatformManager"      = "HKLM\SYSTEM\CurrentControlSet\Services\EventLog\System\ITSPlatformManager"
}

foreach ($entry in $ExplicitKeys.GetEnumerator()) {
    Remove-RegKeyForced -KeyPath $entry.Key -RegExePath $entry.Value -PSExecPath $PSExecPath
}

# ── 4b: ControlSet001 / ControlSet002 / ControlSet003 mirrors ──
Write-Log "" "INFO"
Write-Log "  4b: ControlSet mirror cleanup" "HEADER"

$ControlSets = @("ControlSet001", "ControlSet002", "ControlSet003")
$SvcKeywords = @("ITSPlatform", "ITSPlatformManager", "SAAZOD", "SAAZODBKP")

foreach ($cs in $ControlSets) {
    foreach ($svc in $SvcKeywords) {
        $psPath  = "HKLM:\SYSTEM\$cs\Services\$svc"
        $regPath = "HKLM\SYSTEM\$cs\Services\$svc"
        Remove-RegKeyForced -KeyPath $psPath -RegExePath $regPath -PSExecPath $PSExecPath
    }
    
    # Event logs in each ControlSet
    foreach ($svc in $SvcKeywords) {
        foreach ($logType in @("Application", "System")) {
            $psPath  = "HKLM:\SYSTEM\$cs\Services\EventLog\$logType\$svc"
            $regPath = "HKLM\SYSTEM\$cs\Services\EventLog\$logType\$svc"
            Remove-RegKeyForced -KeyPath $psPath -RegExePath $regPath -PSExecPath $PSExecPath
        }
    }
}

# ── 4c: Uninstall entries ──
Write-Log "" "INFO"
Write-Log "  4c: Uninstall key sweep" "HEADER"

$UninstallRoots = @(
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
    "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
)
$UninstallKeywords = @("ITSPlatform", "SAAZOD", "SAAZODBKP", "ConnectWise RMM", "CentraStage", "platform-agent", "CWRMMAgent", "Datto RMM")

foreach ($Root in $UninstallRoots) {
    Get-ChildItem -Path $Root -ErrorAction SilentlyContinue | ForEach-Object {
        $props = Get-ItemProperty -Path $_.PSPath -ErrorAction SilentlyContinue
        $DisplayName = $props.DisplayName
        $Publisher = $props.Publisher
        $ChildName = $_.PSChildName
        
        $matched = $UninstallKeywords | Where-Object { 
            $DisplayName -like "*$_*" -or $ChildName -like "*$_*" -or $Publisher -like "*$_*"
        }
        if ($matched) {
            Write-Log "  Uninstall entry: $ChildName [$DisplayName] by $Publisher" "WARNING"
            $nativePath = $_.PSPath -replace "Microsoft.PowerShell.Core\\Registry::", ""
            Remove-RegKeyForced -KeyPath $_.PSPath -RegExePath $nativePath -PSExecPath $PSExecPath
        }
    }
}

# ── 4d: Run / RunOnce startup entries ──
Write-Log "" "INFO"
Write-Log "  4d: Run/RunOnce startup entries" "HEADER"

$RunKeys = @(
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce",
    "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run",
    "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\RunOnce"
)
$RunKeywords = @("ITSPlatform", "SAAZOD", "SAAZODBKP", "platform-agent", "agentcore", "CentraStage", "CWRMMAgent")

foreach ($RunKey in $RunKeys) {
    if (!(Test-Path $RunKey)) { continue }
    $props = Get-ItemProperty -Path $RunKey -ErrorAction SilentlyContinue
    $nativeRunKey = $RunKey -replace "HKLM:\\", "HKLM\"
    
    $props.PSObject.Properties | Where-Object { $_.Name -notlike "PS*" } | ForEach-Object {
        $valName = $_.Name
        $valData = $_.Value
        $matched = $RunKeywords | Where-Object { $valName -like "*$_*" -or $valData -like "*$_*" }
        if ($matched) {
            Write-Log "  Run value: [$RunKey] $valName = $valData" "WARNING"
            Remove-RegValueForced -KeyPath $RunKey -ValueName $valName -RegExePath $nativeRunKey -PSExecPath $PSExecPath
        }
    }
}

# ── 4e: MSI Installer / Windows Installer product entries ──
Write-Log "" "INFO"
Write-Log "  4e: Windows Installer product entries" "HEADER"

$InstallerRoots = @(
    "HKLM:\SOFTWARE\Classes\Installer\Products",
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Installer\UserData"
)
$MsiKeywords = @("ITSPlatform", "SAAZOD", "SAAZODBKP", "ConnectWise", "CentraStage", "CWRMMAgent", "Datto RMM")

foreach ($Root in $InstallerRoots) {
    if (!(Test-Path $Root)) { continue }
    try {
        Get-ChildItem -Path $Root -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
            $props = Get-ItemProperty -Path $_.PSPath -ErrorAction SilentlyContinue
            $productName = $props.ProductName
            $displayName = $props.DisplayName
            $childName = $_.PSChildName
            
            $matched = $MsiKeywords | Where-Object {
                $productName -like "*$_*" -or $displayName -like "*$_*" -or $childName -like "*$_*"
            }
            if ($matched) {
                Write-Log "  MSI entry: $($_.PSPath) [$productName$displayName]" "WARNING"
                $nativePath = $_.PSPath -replace "Microsoft.PowerShell.Core\\Registry::", ""
                Remove-RegKeyForced -KeyPath $_.PSPath -RegExePath $nativePath -PSExecPath $PSExecPath
            }
        }
    } catch {
        Write-Log "  Error scanning $Root : $_" "ERROR"
    }
}

# ── 4f: CLSID / COM registrations ──
Write-Log "" "INFO"
Write-Log "  4f: COM / CLSID entries" "HEADER"

$CLSIDRoots = @(
    "HKLM:\SOFTWARE\Classes\CLSID",
    "HKLM:\SOFTWARE\WOW6432Node\Classes\CLSID",
    "HKLM:\SOFTWARE\Classes\TypeLib",
    "HKLM:\SOFTWARE\WOW6432Node\Classes\TypeLib",
    "HKLM:\SOFTWARE\Classes\AppID"
)
$COMKeywords = @("ITSPlatform", "SAAZOD", "SAAZODBKP", "CentraStage", "platform-agent")

foreach ($Root in $CLSIDRoots) {
    if (!(Test-Path $Root)) { continue }
    try {
        Get-ChildItem -Path $Root -ErrorAction SilentlyContinue | ForEach-Object {
            $props = Get-ItemProperty -Path $_.PSPath -ErrorAction SilentlyContinue
            $defaultVal = $props.'(Default)'
            $inproc = $null
            
            # Check InprocServer32 / LocalServer32 for paths
            $subKeys = @("InprocServer32", "LocalServer32")
            foreach ($sub in $subKeys) {
                $subPath = Join-Path $_.PSPath $sub
                if (Test-Path $subPath) {
                    $subProps = Get-ItemProperty -Path $subPath -ErrorAction SilentlyContinue
                    $inproc = $subProps.'(Default)'
                }
            }
            
            $matched = $COMKeywords | Where-Object {
                $defaultVal -like "*$_*" -or $inproc -like "*$_*"
            }
            if ($matched) {
                Write-Log "  COM entry: $($_.PSChildName) [$defaultVal] -> $inproc" "WARNING"
                $nativePath = $_.PSPath -replace "Microsoft.PowerShell.Core\\Registry::", ""
                Remove-RegKeyForced -KeyPath $_.PSPath -RegExePath $nativePath -PSExecPath $PSExecPath
            }
        }
    } catch {
        Write-Log "  Error scanning $Root : $_" "ERROR"
    }
}

# ── 4g: SharedDLLs references ──
Write-Log "" "INFO"
Write-Log "  4g: SharedDLLs cleanup" "HEADER"

$SharedDLLKey = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\SharedDLLs"
if (Test-Path $SharedDLLKey) {
    $props = Get-ItemProperty -Path $SharedDLLKey -ErrorAction SilentlyContinue
    $nativeSDK = "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\SharedDLLs"
    $SharedKeywords = @("ITSPlatform", "SAAZOD", "SAAZODBKP", "CentraStage")
    
    $props.PSObject.Properties | Where-Object { $_.Name -notlike "PS*" } | ForEach-Object {
        $valName = $_.Name
        $matched = $SharedKeywords | Where-Object { $valName -like "*$_*" }
        if ($matched) {
            Write-Log "  SharedDLL: $valName" "WARNING"
            Remove-RegValueForced -KeyPath $SharedDLLKey -ValueName $valName -RegExePath $nativeSDK -PSExecPath $PSExecPath
        }
    }
}

# ── 4h: Firewall rules ──
Write-Log "" "INFO"
Write-Log "  4h: Firewall rules" "HEADER"

$FWKeywords = @("ITSPlatform", "SAAZOD", "SAAZODBKP", "CentraStage", "platform-agent")
try {
    $fwRules = Get-NetFirewallRule -ErrorAction SilentlyContinue | Where-Object {
        $rn = $_.DisplayName
        $rd = $_.Description
        $FWKeywords | Where-Object { $rn -like "*$_*" -or $rd -like "*$_*" }
    }
    foreach ($rule in $fwRules) {
        Write-Log "  Removing firewall rule: $($rule.DisplayName)" "WARNING"
        Remove-NetFirewallRule -Name $rule.Name -ErrorAction SilentlyContinue
        Write-Log "    Removed" "SUCCESS"
    }
    if (-not $fwRules) { Write-Log "  No matching firewall rules" "INFO" }
} catch {
    Write-Log "  Firewall check failed: $_" "ERROR"
}

# ── 4i: Windows Defender exclusions ──
Write-Log "" "INFO"
Write-Log "  4i: Defender exclusions" "HEADER"

try {
    $prefs = Get-MpPreference -ErrorAction SilentlyContinue
    $DefKeywords = @("ITSPlatform", "SAAZOD", "SAAZODBKP", "CentraStage")
    
    if ($prefs.ExclusionPath) {
        foreach ($excl in $prefs.ExclusionPath) {
            $matched = $DefKeywords | Where-Object { $excl -like "*$_*" }
            if ($matched) {
                Write-Log "  Removing Defender path exclusion: $excl" "WARNING"
                Remove-MpPreference -ExclusionPath $excl -ErrorAction SilentlyContinue
            }
        }
    }
    if ($prefs.ExclusionProcess) {
        foreach ($excl in $prefs.ExclusionProcess) {
            $matched = $DefKeywords | Where-Object { $excl -like "*$_*" }
            if ($matched) {
                Write-Log "  Removing Defender process exclusion: $excl" "WARNING"
                Remove-MpPreference -ExclusionProcess $excl -ErrorAction SilentlyContinue
            }
        }
    }
} catch {
    Write-Log "  Defender exclusion check failed: $_" "WARNING"
}

# ── 4j: Per-user registry (all HKU profiles) ──
Write-Log "" "INFO"
Write-Log "  4j: Per-user registry (HKU hives)" "HEADER"

try {
    New-PSDrive -Name HKU -PSProvider Registry -Root HKEY_USERS -ErrorAction SilentlyContinue | Out-Null
    
    $userSIDs = Get-ChildItem -Path "HKU:\" -ErrorAction SilentlyContinue | 
        Where-Object { $_.PSChildName -match '^S-1-5-21' -and $_.PSChildName -notmatch '_Classes$' }
    
    $UserKeywords = @("ITSPlatform", "SAAZOD", "SAAZODBKP", "CentraStage")
    
    foreach ($sid in $userSIDs) {
        $sidPath = $sid.PSChildName
        
        # Run/RunOnce per user
        $userRunKeys = @(
            "HKU:\$sidPath\SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
            "HKU:\$sidPath\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"
        )
        
        foreach ($urk in $userRunKeys) {
            if (!(Test-Path $urk)) { continue }
            $props = Get-ItemProperty -Path $urk -ErrorAction SilentlyContinue
            $nativeUrk = $urk -replace "HKU:\\", "HKU\"
            
            $props.PSObject.Properties | Where-Object { $_.Name -notlike "PS*" } | ForEach-Object {
                $matched = $UserKeywords | Where-Object { $_.Value -like "*$_*" -or $_.Name -like "*$_*" }
                if ($matched) {
                    Write-Log "  User [$sidPath] Run: $($_.Name)" "WARNING"
                    Remove-RegValueForced -KeyPath $urk -ValueName $_.Name -RegExePath $nativeUrk -PSExecPath $PSExecPath
                }
            }
        }
        
        # Software keys per user
        foreach ($kw in $UserKeywords) {
            $userSwKey = "HKU:\$sidPath\SOFTWARE\$kw"
            if (Test-Path $userSwKey) {
                $nativePath = "HKU\$sidPath\SOFTWARE\$kw"
                Write-Log "  User [$sidPath] Software: $kw" "WARNING"
                Remove-RegKeyForced -KeyPath $userSwKey -RegExePath $nativePath -PSExecPath $PSExecPath
            }
        }
    }
} catch {
    Write-Log "  HKU scan error: $_" "ERROR"
}

# ── 4k: Deep scan - full HKLM\SOFTWARE + SYSTEM sweep ──
Write-Log "" "INFO"
Write-Log "  4k: Deep registry scan (may take a moment...)" "HEADER"

$DeepKeywords = @("ITSPlatform", "SAAZOD", "SAAZODBKP", "platform-agent", "CentraStage")
$DeepRoots = @(
    "HKLM:\SOFTWARE",
    "HKLM:\SOFTWARE\WOW6432Node",
    "HKLM:\SYSTEM\CurrentControlSet\Services"
)

foreach ($Root in $DeepRoots) {
    Write-Log "  Scanning: $Root" "INFO"
    try {
        Get-ChildItem -Path $Root -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
            $keyName = $_.PSChildName
            $matched = $DeepKeywords | Where-Object { $keyName -like "*$_*" }
            if ($matched) {
                # Don't re-process keys we already handled
                $alreadyHandled = $ExplicitKeys.Keys | Where-Object { $_.PSPath -like "$_*" }
                if (-not $alreadyHandled) {
                    Write-Log "  Deep hit: $($_.PSPath)" "WARNING"
                    $nativePath = $_.PSPath -replace "Microsoft.PowerShell.Core\\Registry::", ""
                    Remove-RegKeyForced -KeyPath $_.PSPath -RegExePath $nativePath -PSExecPath $PSExecPath
                }
            }
        }
    } catch {
        Write-Log "  Deep scan error on $Root : $($_.Exception.Message)" "WARNING"
    }
}

Write-Log "" "SUCCESS"
Write-Log "  PHASE 4 COMPLETE" "SUCCESS"

# ===== PHASE 5: WMI CLEANUP =====
Write-Log "" "HEADER"
Write-Log "==========================================" "HEADER"
Write-Log "  PHASE 5: WMI EVENT SUBSCRIPTIONS" "HEADER"
Write-Log "==========================================" "HEADER"

$WMIKeywords = @("ITSPlatform", "SAAZOD", "SAAZODBKP", "CentraStage")

try {
    $wmiClasses = @(
        "root\subscription:__EventFilter",
        "root\subscription:__EventConsumer",
        "root\subscription:__FilterToConsumerBinding"
    )
    
    foreach ($class in $wmiClasses) {
        $parts = $class -split ":"
        $ns = $parts[0]
        $cn = $parts[1]
        
        Get-WmiObject -Namespace $ns -Class $cn -ErrorAction SilentlyContinue | ForEach-Object {
            $name = $_.Name
            $matched = $WMIKeywords | Where-Object { $name -like "*$_*" }
            if ($matched) {
                Write-Log "  WMI $cn : $name" "WARNING"
                $_ | Remove-WmiObject -ErrorAction SilentlyContinue
                Write-Log "    Removed" "SUCCESS"
            }
        }
    }
} catch {
    Write-Log "  WMI cleanup error: $_" "WARNING"
}

# ===== PHASE 6: FINAL VERIFICATION =====
Write-Log "" "HEADER"
Write-Log "==========================================" "HEADER"
Write-Log "  PHASE 6: FINAL VERIFICATION" "HEADER"
Write-Log "==========================================" "HEADER"

$issues = 0

# Check folders
Write-Log "  Checking files..." "INFO"
foreach ($Folder in $Folders) {
    if (Test-Path $Folder) {
        Write-Log "  [REMAIN] $Folder" "ERROR"
        $issues++
    }
}

# Check services
Write-Log "  Checking services..." "INFO"
foreach ($svc in $Services) {
    $check = Get-Service -Name $svc -ErrorAction SilentlyContinue
    if ($check) {
        Write-Log "  [REMAIN] Service: $svc ($($check.Status))" "ERROR"
        $issues++
    }
}

# Check registry - comprehensive scan
Write-Log "  Checking registry..." "INFO"
$VerifyKeywords = @("ITSPlatform", "SAAZOD", "SAAZODBKP")
$VerifyRoots = @(
    "HKLM:\SOFTWARE",
    "HKLM:\SOFTWARE\WOW6432Node",
    "HKLM:\SYSTEM\CurrentControlSet\Services"
)

$remainingKeys = @()
foreach ($Root in $VerifyRoots) {
    try {
        Get-ChildItem -Path $Root -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
            $keyName = $_.PSChildName
            $matched = $VerifyKeywords | Where-Object { $keyName -like "*$_*" }
            if ($matched) {
                $remainingKeys += $_.PSPath
                Write-Log "  [REMAIN] $($_.PSPath)" "ERROR"
                $issues++
            }
        }
    } catch {}
}

# Also verify ControlSets
foreach ($cs in $ControlSets) {
    foreach ($svc in $SvcKeywords) {
        $checkPath = "HKLM:\SYSTEM\$cs\Services\$svc"
        if (Test-Path $checkPath) {
            Write-Log "  [REMAIN] $checkPath" "ERROR"
            $issues++
        }
    }
}

# Check processes
Write-Log "  Checking processes..." "INFO"
$remainProcs = Get-Process -ErrorAction SilentlyContinue | Where-Object {
    $TargetPatterns | Where-Object { $_.Name -like $_ }
}
foreach ($proc in $remainProcs) {
    Write-Log "  [REMAIN] Process: $($proc.Name) (PID: $($proc.Id))" "ERROR"
    $issues++
}

# ── Summary ──
Write-Log "" "HEADER"
Write-Log "==========================================" "HEADER"
Write-Log "  REMOVAL COMPLETE" "HEADER"
Write-Log "==========================================" "HEADER"

if ($issues -eq 0) {
    Write-Log "  TOTAL ANNIHILATION COMPLETE - NO REMNANTS FOUND!" "SUCCESS"
} else {
    Write-Log "  $issues remnant(s) found - REBOOT RECOMMENDED" "WARNING"
    
    if ($remainingKeys.Count -gt 0) {
        Write-Log "" "WARNING"
        Write-Log "  Attempting final SYSTEM-level cleanup of remaining keys..." "WARNING"
        foreach ($rk in $remainingKeys) {
            $nativePath = $rk -replace "Microsoft.PowerShell.Core\\Registry::", ""
            Write-Log "  Final attempt: $nativePath" "WARNING"
            & $PSExecPath -s -nobanner -AcceptEula reg.exe delete "$nativePath" /f 2>&1 |
                ForEach-Object { Write-Log "    SYSTEM> $_" }
        }
    }
}

Write-Log ""
Write-Log "  Log: $LogFile"
Write-Log "==========================================" "HEADER"
Write-Log ""

Read-Host "Press Enter to close"