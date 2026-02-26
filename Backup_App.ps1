# NAME: 💾 Backup Project
# DESCRIPTION: Creates clean backup using 7-Zip (keeps last 10)

$7z = "C:\Program Files\7-Zip\7z.exe"

# Check for 7-Zip
if (-not (Test-Path $7z)) {
    $7z = "C:\Program Files (x86)\7-Zip\7z.exe"
    if (-not (Test-Path $7z)) {
        Write-Host "7-Zip not found!" -ForegroundColor Red
        exit 1
    }
}

# Configuration
$source = "$env:USERPROFILE\Install_Apps"
$backupFolder = "$env:USERPROFILE\Install_Apps\Backups"
$backup = "$backupFolder\$(Get-Date -Format 'yy-MM-dd_HHmm').7z"
$keepCount = 10  # Number of backups to keep

# Create backup folder if it doesn't exist
if (-not (Test-Path $backupFolder)) {
    New-Item -ItemType Directory -Path $backupFolder -Force | Out-Null
}

# Exclusions
$exclude = @(
    "-xr!__pycache__",
    "-xr!build",
    "-xr!dist",
    "-xr!venv",
    "-xr!.venv",
    "-xr!env",
    "-xr!.git",
    "-xr!.idea",
    "-xr!.vscode",
    "-xr!.mypy_cache",
    "-xr!.pytest_cache",
    "-xr!*.pyc",
    "-xr!*.pyo",
    "-xr!*.log",
    "-xr!*.bak",
    "-xr!Backups",
    "-xr!*.tmp"
)

Write-Host "Creating backup..." -ForegroundColor Cyan
Write-Host "Source: $source" -ForegroundColor Gray
Write-Host "Output: $backup" -ForegroundColor Gray
Write-Host ""

# Create archive
& $7z a $backup $source $exclude

Write-Host ""
Write-Host "✅ Backup complete: $backup" -ForegroundColor Green

# Show size
$size = (Get-Item $backup).Length / 1MB
Write-Host "📦 Size: $([math]::Round($size, 2)) MB" -ForegroundColor Cyan

# === CLEANUP OLD BACKUPS ===
Write-Host ""
Write-Host "🧹 Checking for old backups..." -ForegroundColor Yellow

$backups = Get-ChildItem -Path $backupFolder -Filter "*.7z" | Sort-Object CreationTime -Descending

if ($backups.Count -gt $keepCount) {
    $toDelete = $backups | Select-Object -Skip $keepCount
    
    Write-Host "   Keeping last $keepCount backups, removing $($toDelete.Count) old backup(s):" -ForegroundColor Gray
    
    foreach ($file in $toDelete) {
        Write-Host "   🗑️ Deleting: $($file.Name)" -ForegroundColor DarkGray
        Remove-Item $file.FullName -Force
    }
    
    Write-Host "   ✅ Cleanup complete" -ForegroundColor Green
} else {
    Write-Host "   ✅ No cleanup needed ($($backups.Count) of $keepCount max)" -ForegroundColor Green
}

# === LIST CURRENT BACKUPS ===
Write-Host ""
Write-Host "📁 Current backups:" -ForegroundColor Cyan
Get-ChildItem -Path $backupFolder -Filter "*.7z" | Sort-Object CreationTime -Descending | ForEach-Object {
    $s = [math]::Round($_.Length / 1MB, 2)
    $d = $_.CreationTime.ToString("yyyy-MM-dd HH:mm")
    Write-Host "   $($_.Name) ($s MB) - $d" -ForegroundColor Gray
}