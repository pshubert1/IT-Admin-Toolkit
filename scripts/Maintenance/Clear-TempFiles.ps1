# NAME: 🗑️ Clear Temp Files
# DESCRIPTION: Clears temporary files from system
# STYLE: Warning.TButton

# === Script starts below ===
Write-Host "Clearing temporary files..." -ForegroundColor Yellow

$TempFolders = @($env:TEMP, 'C:\Windows\Temp')
$TotalCleared = 0

foreach($folder in $TempFolders) {
    Write-Host "  Cleaning $folder..." -ForegroundColor Gray
    $files = Get-ChildItem -Path $folder -Recurse -Force -ErrorAction SilentlyContinue
    $TotalCleared += $files.Count
    $files | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "✅ Cleared $TotalCleared items!" -ForegroundColor Green