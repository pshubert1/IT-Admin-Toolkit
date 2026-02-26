# NAME: 🌐 Map Network Drive
# DESCRIPTION: Maps a network drive with credentials
# STYLE: Dark.TButton
# INTERACTIVE: true

Write-Host "================================" -ForegroundColor Cyan
Write-Host "  Map Network Drive" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Show current mapped drives
Write-Host "Current mapped drives:" -ForegroundColor Yellow
Get-PSDrive -PSProvider FileSystem | Where-Object { $_.DisplayRoot } | 
    Select-Object Name, DisplayRoot | Format-Table -AutoSize

Write-Host ""
$DriveLetter = Read-Host "Enter drive letter (e.g., Z)"
$Path = Read-Host "Enter network path (e.g., \\server\share)"
$UseCredentials = Read-Host "Use different credentials? (yes/no)"

$DriveLetter = $DriveLetter.TrimEnd(':') + ':'

try {
    if ($UseCredentials -eq 'yes') {
        $Cred = Get-Credential -Message "Enter credentials for $Path"
        New-PSDrive -Name $DriveLetter.TrimEnd(':') -PSProvider FileSystem -Root $Path -Credential $Cred -Persist -Scope Global
    } else {
        New-PSDrive -Name $DriveLetter.TrimEnd(':') -PSProvider FileSystem -Root $Path -Persist -Scope Global
    }
    
    Write-Host ""
    Write-Host "✅ Drive $DriveLetter mapped to $Path" -ForegroundColor Green
    
} catch {
    Write-Host ""
    Write-Host "❌ Error: $_" -ForegroundColor Red
}