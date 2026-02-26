# NAME: 🔒 Bitlocker Keys
# DESCRIPTION: Shows you the Bitlocker keys for this computer
# STYLE: Dark.TButton


Get-BitLockerVolume | Select-Object MountPoint, VolumeStatus, ProtectionStatus, 
    @{Name='RecoveryPasswords'; Expression={ ($_.KeyProtector | Where-Object KeyProtectorType -eq 'RecoveryPassword').RecoveryPassword }} |
    Format-Table -AutoSize
