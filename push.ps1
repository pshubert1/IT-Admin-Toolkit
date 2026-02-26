# NAME: Commit changes to GetHub Repo
# DESCRIPTION: Backs up and pushes changes to GitHub

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  IT Admin Toolkit - Push Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# === RUN BACKUP FIRST ===
if (Test-Path ".\Backup_App.ps1") {
    Write-Host "💾 Running backup..." -ForegroundColor Magenta
    & .\Backup_App.ps1
    Write-Host ""
}
#Push to Github
git add .
$commitMsg = Read-Host "Enter commit message"
git commit -m $commitMsg
git push
Write-Host "✅ Pushed to GitHub!" -ForegroundColor Green
