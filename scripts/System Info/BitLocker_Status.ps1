# NAME: 🔒 BitLocker Status & Keys
# DESCRIPTION: Show BitLocker encryption status and recovery keys for all drives
# STYLE: Info.TButton
# INTERACTIVE: true

# ============================================================
#  BitLocker Status & Recovery Key Viewer
# ============================================================

#Requires -RunAsAdministrator

$logDir = "C:\Temp"
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$logFile = Join-Path $logDir "BitLocker_Status_${timestamp}.log"
$keyExportFile = Join-Path $logDir "BitLocker_Keys_${timestamp}.txt"

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
        "KEY"     { "Magenta" }
        default   { "White" }
    })
    Add-Content -Path $logFile -Value $entry
}

Write-Log "==========================================" "HEADER"
Write-Log "  BITLOCKER STATUS & RECOVERY KEYS" "HEADER"
Write-Log "==========================================" "HEADER"
Write-Log "  Computer:  $env:COMPUTERNAME"
Write-Log "  User:      $env:USERNAME"
Write-Log "  Domain:    $env:USERDOMAIN"
Write-Log "  OS:        $((Get-CimInstance Win32_OperatingSystem).Caption)"
Write-Log "  Date:      $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Log "  Log:       $logFile"
Write-Log "==========================================" "HEADER"
Write-Log ""

# ── Check if BitLocker module is available ──
$blModule = $false
try {
    Import-Module BitLocker -ErrorAction Stop
    $blModule = $true
    Write-Log "BitLocker PowerShell module loaded" "SUCCESS"
} catch {
    Write-Log "BitLocker PowerShell module not available - using manage-bde fallback" "WARN"
}

# ── Get all fixed drives ──
$allDrives = Get-Volume -ErrorAction SilentlyContinue | 
    Where-Object { $_.DriveLetter -and $_.DriveType -eq 'Fixed' } | 
    Sort-Object DriveLetter

if (-not $allDrives) {
    Write-Log "No fixed drives found" "ERROR"
    Read-Host "Press Enter to close"
    exit 1
}

Write-Log "Found $($allDrives.Count) fixed drive(s)"
Write-Log ""

# ── Initialize key export file ──
$keyExportContent = @()
$keyExportContent += "============================================"
$keyExportContent += "  BITLOCKER RECOVERY KEYS"
$keyExportContent += "  Computer: $env:COMPUTERNAME"
$keyExportContent += "  Date:     $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$keyExportContent += "============================================"
$keyExportContent += ""

$encryptedCount = 0
$totalKeys = 0

foreach ($drive in $allDrives) {
    $letter = "$($drive.DriveLetter):"
    $label = if ($drive.FileSystemLabel) { $drive.FileSystemLabel } else { "No Label" }
    $sizeGB = [math]::Round($drive.Size / 1GB, 1)
    $freeGB = [math]::Round($drive.SizeRemaining / 1GB, 1)
    
    Write-Log "==========================================" "HEADER"
    Write-Log "  DRIVE: $letter ($label)" "HEADER"
    Write-Log "==========================================" "HEADER"
    Write-Log "  Size:        $sizeGB GB ($freeGB GB free)"
    Write-Log "  FileSystem:  $($drive.FileSystem)"
    Write-Log "  Health:      $($drive.HealthStatus)"
    Write-Log ""
    
    # ── Get BitLocker status ──
    $blStatus = $null
    $protectionStatus = "Unknown"
    $encryptionStatus = "Unknown"
    $encryptionPct = "N/A"
    $encryptionMethod = "N/A"
    $lockStatus = "N/A"
    $keyProtectors = @()
    
    if ($blModule) {
        # ── Method 1: PowerShell BitLocker module ──
        try {
            $blStatus = Get-BitLockerVolume -MountPoint $letter -ErrorAction Stop
            
            $protectionStatus = $blStatus.ProtectionStatus
            $encryptionStatus = $blStatus.VolumeStatus
            $encryptionPct = "$($blStatus.EncryptionPercentage)%"
            $encryptionMethod = $blStatus.EncryptionMethod
            $lockStatus = $blStatus.LockStatus
            $keyProtectors = $blStatus.KeyProtector
            
        } catch {
            Write-Log "Could not query BitLocker via module: $_" "WARN"
        }
    }
    
    if (-not $blStatus) {
        # ── Method 2: manage-bde fallback ──
        try {
            $bdeOutput = manage-bde -status $letter 2>&1 | Out-String
            
            if ($bdeOutput -match "Protection Status:\s+(.+)") {
                $protectionStatus = $matches[1].Trim()
            }
            if ($bdeOutput -match "Conversion Status:\s+(.+)") {
                $encryptionStatus = $matches[1].Trim()
            }
            if ($bdeOutput -match "Percentage Encrypted:\s+(.+)") {
                $encryptionPct = $matches[1].Trim()
            }
            if ($bdeOutput -match "Encryption Method:\s+(.+)") {
                $encryptionMethod = $matches[1].Trim()
            }
            if ($bdeOutput -match "Lock Status:\s+(.+)") {
                $lockStatus = $matches[1].Trim()
            }
        } catch {
            Write-Log "manage-bde failed for $letter : $_" "ERROR"
        }
    }
    
    # ── Display status ──
    $isEncrypted = ($protectionStatus -match "On|Protection On" -or $encryptionStatus -match "Encrypted|FullyEncrypted")
    $statusLevel = if ($isEncrypted) { "SUCCESS" } else { "WARN" }
    
    Write-Log "  Protection:    $protectionStatus" $statusLevel
    Write-Log "  Encryption:    $encryptionStatus" $statusLevel
    Write-Log "  Percent:       $encryptionPct"
    Write-Log "  Method:        $encryptionMethod"
    Write-Log "  Lock Status:   $lockStatus"
    Write-Log ""
    
    if ($isEncrypted) { $encryptedCount++ }
    
    # ── Recovery Keys ──
    if ($keyProtectors -and $keyProtectors.Count -gt 0) {
        Write-Log "  KEY PROTECTORS:" "HEADER"
        Write-Log "  ---------------" "HEADER"
        
        $keyExportContent += "  DRIVE: $letter ($label)"
        $keyExportContent += "  ---------------"
        
        foreach ($kp in $keyProtectors) {
            Write-Log ""
            Write-Log "    Type:       $($kp.KeyProtectorType)" "INFO"
            Write-Log "    ID:         $($kp.KeyProtectorId)" "INFO"
            
            $keyExportContent += "    Type:    $($kp.KeyProtectorType)"
            $keyExportContent += "    ID:      $($kp.KeyProtectorId)"
            
            switch ($kp.KeyProtectorType) {
                "RecoveryPassword" {
                    $totalKeys++
                    Write-Log "" "KEY"
                    Write-Log "    ┌──────────────────────────────────────────────┐" "KEY"
                    Write-Log "    │  RECOVERY KEY:                               │" "KEY"
                    Write-Log "    │  $($kp.RecoveryPassword)  │" "KEY"
                    Write-Log "    └──────────────────────────────────────────────┘" "KEY"
                    Write-Log "" "KEY"
                    
                    $keyExportContent += ""
                    $keyExportContent += "    *** RECOVERY KEY: $($kp.RecoveryPassword) ***"
                    $keyExportContent += ""
                }
                "Tpm" {
                    Write-Log "    (TPM protector - no visible key)" "INFO"
                    $keyExportContent += "    (TPM protector)"
                }
                "TpmPin" {
                    Write-Log "    (TPM + PIN protector)" "INFO"
                    $keyExportContent += "    (TPM + PIN protector)"
                }
                "TpmStartupKey" {
                    Write-Log "    (TPM + Startup Key protector)" "INFO"
                    $keyExportContent += "    (TPM + Startup Key protector)"
                }
                "ExternalKey" {
                    Write-Log "    (External Key / USB protector)" "INFO"
                    Write-Log "    File: $($kp.KeyFileName)" "INFO"
                    $keyExportContent += "    (External Key: $($kp.KeyFileName))"
                }
                "Password" {
                    Write-Log "    (Password protector)" "INFO"
                    $keyExportContent += "    (Password protector)"
                }
                default {
                    Write-Log "    ($($kp.KeyProtectorType) protector)" "INFO"
                    $keyExportContent += "    ($($kp.KeyProtectorType) protector)"
                }
            }
        }
        
        $keyExportContent += ""
        
    } elseif ($isEncrypted) {
        # ── Fallback: manage-bde to get keys ──
        Write-Log "  KEY PROTECTORS (via manage-bde):" "HEADER"
        
        try {
            $bdeProtectors = manage-bde -protectors -get $letter 2>&1 | Out-String
            
            # Parse recovery passwords
            $keyMatches = [regex]::Matches($bdeProtectors, '(\d{6}-\d{6}-\d{6}-\d{6}-\d{6}-\d{6}-\d{6}-\d{6})')
            
            if ($keyMatches.Count -gt 0) {
                $keyExportContent += "  DRIVE: $letter ($label)"
                $keyExportContent += "  ---------------"
                
                foreach ($match in $keyMatches) {
                    $totalKeys++
                    $key = $match.Value
                    Write-Log "" "KEY"
                    Write-Log "    ┌──────────────────────────────────────────────┐" "KEY"
                    Write-Log "    │  RECOVERY KEY:                               │" "KEY"
                    Write-Log "    │  $key  │" "KEY"
                    Write-Log "    └──────────────────────────────────────────────┘" "KEY"
                    Write-Log "" "KEY"
                    
                    $keyExportContent += ""
                    $keyExportContent += "    *** RECOVERY KEY: $key ***"
                    $keyExportContent += ""
                }
            }
            
            # Parse IDs
            $idMatches = [regex]::Matches($bdeProtectors, '\{([0-9A-Fa-f-]+)\}')
            foreach ($idMatch in $idMatches) {
                Write-Log "    Protector ID: {$($idMatch.Groups[1].Value)}" "INFO"
            }
            
            # Show protector types
            if ($bdeProtectors -match "TPM") { Write-Log "    TPM protector present" "INFO" }
            if ($bdeProtectors -match "Numerical Password") { Write-Log "    Recovery Password protector present" "INFO" }
            if ($bdeProtectors -match "External Key") { Write-Log "    External Key protector present" "INFO" }
            
        } catch {
            Write-Log "Could not retrieve protectors: $_" "ERROR"
        }
        
        $keyExportContent += ""
        
    } else {
        Write-Log "  Not encrypted - no keys to display" "INFO"
    }
    
# ── Backup keys to AD and/or Azure AD / Entra ID ──
    if ($isEncrypted -and $blModule) {
        Write-Log ""
        Write-Log "  KEY BACKUP:" "HEADER"
        
        # Detect join type
        $dsregOutput = dsregcmd /status 2>&1 | Out-String
        $isAzureJoined = $dsregOutput -match "AzureAdJoined\s*:\s*YES"
        $isDomainJoined = $dsregOutput -match "DomainJoined\s*:\s*YES"
        
        Write-Log "    Domain Joined:   $isDomainJoined" $(if ($isDomainJoined) { "SUCCESS" } else { "INFO" })
        Write-Log "    Azure AD Joined: $isAzureJoined" $(if ($isAzureJoined) { "SUCCESS" } else { "INFO" })
        Write-Log ""
        
        foreach ($kp in $keyProtectors) {
            if ($kp.KeyProtectorType -eq "RecoveryPassword") {
                Write-Log "    Key ID: $($kp.KeyProtectorId)" "INFO"
                
                # ── On-prem AD backup ──
                if ($isDomainJoined) {
                    try {
                        Backup-BitLockerKeyProtector -MountPoint $letter -KeyProtectorId $kp.KeyProtectorId -ErrorAction Stop | Out-Null
                        Write-Log "    [AD] Backed up to Active Directory" "SUCCESS"
                    } catch {
                        Write-Log "    [AD] Backup failed: $_" "WARN"
                    }
                }
                
                # ── Azure AD / Entra ID backup ──
                if ($isAzureJoined) {
                    try {
                        BackupToAAD-BitLockerKeyProtector -MountPoint $letter -KeyProtectorId $kp.KeyProtectorId -ErrorAction Stop | Out-Null
                        Write-Log "    [Entra ID] Backed up to Azure AD / M365" "SUCCESS"
                    } catch {
                        if ($_ -match "not recognized|CommandNotFoundException") {
                            Write-Log "    [Entra ID] BackupToAAD cmdlet not available (requires Win10 1703+)" "WARN"
                            
                            # Fallback: trigger via MDM
                            try {
                                $bdeResult = manage-bde -protectors -aadbackup $letter -id $kp.KeyProtectorId 2>&1
                                if ($LASTEXITCODE -eq 0) {
                                    Write-Log "    [Entra ID] Backed up via manage-bde" "SUCCESS"
                                } else {
                                    Write-Log "    [Entra ID] manage-bde backup failed: $bdeResult" "WARN"
                                }
                            } catch {
                                Write-Log "    [Entra ID] Fallback also failed: $_" "WARN"
                            }
                        } else {
                            Write-Log "    [Entra ID] Backup failed: $_" "WARN"
                        }
                    }
                }
                
                # ── Neither joined ──
                if (-not $isDomainJoined -and -not $isAzureJoined) {
                    Write-Log "    Not domain or Azure AD joined - cloud backup not available" "WARN"
                    Write-Log "    Save keys manually using the export option below" "WARN"
                }
            }
        }
    }
    
    Write-Log ""
}

# ── TPM Status ──
Write-Log "==========================================" "HEADER"
Write-Log "  TPM STATUS" "HEADER"
Write-Log "==========================================" "HEADER"

try {
    $tpm = Get-Tpm -ErrorAction Stop
    
    Write-Log "  Present:       $($tpm.TpmPresent)" $(if ($tpm.TpmPresent) { "SUCCESS" } else { "ERROR" })
    Write-Log "  Ready:         $($tpm.TpmReady)" $(if ($tpm.TpmReady) { "SUCCESS" } else { "WARN" })
    Write-Log "  Enabled:       $($tpm.TpmEnabled)" $(if ($tpm.TpmEnabled) { "SUCCESS" } else { "WARN" })
    Write-Log "  Activated:     $($tpm.TpmActivated)" $(if ($tpm.TpmActivated) { "SUCCESS" } else { "WARN" })
    Write-Log "  Owned:         $($tpm.TpmOwned)" "INFO"
    Write-Log "  Lockout:       $($tpm.LockoutCount) / $($tpm.LockoutMax)" "INFO"
    
    # Get TPM version
    try {
        $tpmWmi = Get-CimInstance -Namespace "root\cimv2\security\microsofttpm" -ClassName Win32_Tpm -ErrorAction Stop
        $specVersion = $tpmWmi.SpecVersion
        if ($specVersion) {
            $majorVer = ($specVersion -split ',')[0].Trim()
            Write-Log "  Version:       $majorVer" "INFO"
            Write-Log "  Spec Version:  $specVersion" "INFO"
        }
        Write-Log "  Manufacturer:  $($tpmWmi.ManufacturerIdTxt)" "INFO"
    } catch {
        Write-Log "  Could not get TPM details: $_" "WARN"
    }
    
} catch {
    Write-Log "  TPM not available or access denied: $_" "WARN"
}

# ── Export keys to file ──
Write-Log ""
Write-Log "==========================================" "HEADER"

if ($totalKeys -gt 0) {
    Write-Host ""
    Write-Host "  ============================================" -ForegroundColor Yellow
    Write-Host "  Found $totalKeys recovery key(s)" -ForegroundColor Yellow
    Write-Host "  ============================================" -ForegroundColor Yellow
    Write-Host ""
    
    $exportChoice = Read-Host "  Save recovery keys to file? (Y/N)"
    
    if ($exportChoice -eq 'Y' -or $exportChoice -eq 'y') {
        $keyExportContent += "============================================"
        $keyExportContent += "  KEEP THIS FILE SECURE"
        $keyExportContent += "  Delete after storing keys safely"
        $keyExportContent += "============================================"
        
        $keyExportContent | Out-File -FilePath $keyExportFile -Encoding utf8
        Write-Log "Recovery keys saved to: $keyExportFile" "SUCCESS"
        Write-Log ""
        Write-Log "  !! SECURITY WARNING !!" "WARN"
        Write-Log "  Delete $keyExportFile after storing keys in a secure location" "WARN"
        Write-Log "  (password manager, AD, Azure AD, etc.)" "WARN"
    } else {
        Write-Log "Key export skipped" "INFO"
    }
} else {
    Write-Log "No recovery keys found to export" "INFO"
}

# ── Summary ──
Write-Log ""
Write-Log "==========================================" "HEADER"
Write-Log "  SUMMARY" "HEADER"
Write-Log "==========================================" "HEADER"
Write-Log "  Total Drives:     $($allDrives.Count)"
Write-Log "  Encrypted:        $encryptedCount" $(if ($encryptedCount -gt 0) { "SUCCESS" } else { "WARN" })
Write-Log "  Not Encrypted:    $($allDrives.Count - $encryptedCount)" $(if (($allDrives.Count - $encryptedCount) -gt 0) { "WARN" } else { "SUCCESS" })
Write-Log "  Recovery Keys:    $totalKeys"
Write-Log ""
Write-Log "  Log: $logFile"
if (Test-Path $keyExportFile) { Write-Log "  Keys: $keyExportFile" "WARN" }
Write-Log "==========================================" "HEADER"
Write-Log ""

Read-Host "Press Enter to close"