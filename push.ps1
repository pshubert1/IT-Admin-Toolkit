# NAME: 🚀 Push to GitHub
# DESCRIPTION: Backs up and pushes changes to GitHub

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  IT Admin Toolkit - Git Push Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# === CHECK IF GIT REPO ===
if (-not (Test-Path ".git")) {
    Write-Host "❌ Not a Git repository!" -ForegroundColor Red
    exit 1
}

# === RUN BACKUP FIRST ===
if (Test-Path ".\Backup_App.ps1") {
    Write-Host "💾 Running backup..." -ForegroundColor Magenta
    & .\Backup_App.ps1
    Write-Host ""
}

# === SHOW CURRENT BRANCH ===
$branch = git branch --show-current
Write-Host "📌 Current branch: $branch" -ForegroundColor Yellow
Write-Host ""

# === CHECK FOR CHANGES ===
$status = git status --porcelain
if (-not $status) {
    Write-Host "✅ No changes to commit!" -ForegroundColor Green
    exit 0
}

# === SHOW CHANGES ===
Write-Host "📝 Changes to commit:" -ForegroundColor Cyan
git status --short
Write-Host ""

# === STAGE ALL CHANGES ===
git add .

# === GET COMMIT MESSAGE ===
$commitMsg = Read-Host "Enter commit message (or 'q' to cancel)"

if ($commitMsg -eq 'q' -or $commitMsg -eq '') {
    Write-Host "❌ Cancelled - no commit made" -ForegroundColor Yellow
    git reset HEAD  # Unstage changes
    exit 0
}

# === COMMIT ===
Write-Host ""
Write-Host "📦 Committing..." -ForegroundColor Cyan
git commit -m $commitMsg

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Commit failed!" -ForegroundColor Red
    exit 1
}

# === PUSH ===
Write-Host ""
Write-Host "🚀 Pushing to origin/$branch..." -ForegroundColor Cyan
git push origin $branch

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  ✅ Successfully pushed to GitHub!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ Push failed! Try 'git pull' first?" -ForegroundColor Red
    exit 1
}