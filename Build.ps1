# NAME: 🔨 Build IT Admin Toolkit
# DESCRIPTION: Backs up and builds exe with all resources

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  IT Admin Toolkit - Build Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# === RUN BACKUP FIRST ===
if (Test-Path ".\Backup_App.ps1") {
    Write-Host "💾 Running backup..." -ForegroundColor Magenta
    & .\Backup_App.ps1
    Write-Host ""
}

# === BUILD CONFIGURATION ===
$ExeName = "IT-Admin-Toolkit.exe"
$DistFolder = "dist"
$ExePath = "$DistFolder\$ExeName"

# Create dist folder if it doesn't exist
if (-not (Test-Path $DistFolder)) {
    New-Item -ItemType Directory -Path $DistFolder | Out-Null
}

# Check if old exe exists and rename it with creation date
if (Test-Path $ExePath) {
    $file = Get-Item $ExePath
    $createdDate = $file.CreationTime.ToString("yyyy-MM-dd_HHmmss")
    $newName = "IT-Admin-Toolkit_$createdDate.exe"
    
    Write-Host "📦 Archiving existing build" -ForegroundColor Yellow
    Write-Host "   $ExeName → $newName" -ForegroundColor Gray
    
    if (Test-Path "$DistFolder\$newName") {
        Remove-Item "$DistFolder\$newName" -Force
    }
    
    Rename-Item -Path $ExePath -NewName $newName
    Write-Host "   ✅ Archived" -ForegroundColor Green
    Write-Host ""
}

# Clean build folder
if (Test-Path "build") {
    Write-Host "🧹 Cleaning build folder..." -ForegroundColor Gray
    Remove-Item "build" -Recurse -Force
}

# Show what will be included
Write-Host "📦 Including resources:" -ForegroundColor Cyan
Write-Host "   - icon.ico" -ForegroundColor Gray
if (Test-Path "scripts") {
    $scriptCount = (Get-ChildItem "scripts" -Recurse -Filter "*.ps1").Count
    Write-Host "   - scripts/ ($scriptCount .ps1 files)" -ForegroundColor Gray
}
if (Test-Path "config") {
    Write-Host "   - config/" -ForegroundColor Gray
}
Write-Host ""

# Run PyInstaller with all resources
Write-Host "🔨 Building..." -ForegroundColor Cyan
Write-Host ""

pyinstaller --onefile --noconsole --icon=icon.ico `
    --add-data "icon.ico;." `
    --add-data "scripts;scripts" `
    --name "IT-Admin-Toolkit" main.py

# Check if build succeeded
if (Test-Path $ExePath) {
    $size = [math]::Round((Get-Item $ExePath).Length / 1MB, 2)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  ✅ BUILD SUCCESSFUL!" -ForegroundColor Green  
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Output: $ExePath" -ForegroundColor White
    Write-Host "  Size:   $size MB" -ForegroundColor White
    Write-Host ""
    
    # List all versions
    Write-Host "📁 All versions:" -ForegroundColor Cyan
    Get-ChildItem "$DistFolder\IT-Admin-Toolkit*.exe" | Sort-Object CreationTime -Descending | ForEach-Object {
        $s = [math]::Round($_.Length / 1MB, 2)
        $d = $_.CreationTime.ToString("yyyy-MM-dd HH:mm")
        if ($_.Name -eq $ExeName) {
            Write-Host "   ★ $($_.Name) ($s MB) - $d" -ForegroundColor Green
        } else {
            Write-Host "     $($_.Name) ($s MB) - $d" -ForegroundColor Gray
        }
    }
} else {
    Write-Host ""
    Write-Host "❌ BUILD FAILED!" -ForegroundColor Red
}                                                                              