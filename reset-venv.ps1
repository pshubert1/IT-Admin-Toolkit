# reset-venv.ps1
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Resetting Virtual Environment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Deactivate if active
if ($env:VIRTUAL_ENV) {
    Write-Host "🔄 Deactivating current venv..." -ForegroundColor Yellow
    deactivate
}

# Step 2: Remove old venv
if (Test-Path ".venv") {
    Write-Host "🧹 Removing old .venv..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force ".venv"
    Write-Host "✅ Old .venv removed" -ForegroundColor Green
} else {
    Write-Host "✅ No existing .venv found" -ForegroundColor Green
}

# Step 3: Create new venv
Write-Host "📦 Creating new .venv..." -ForegroundColor Yellow
python -m venv .venv

# Step 4: Activate
Write-Host "⚡ Activating .venv..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Step 5: Upgrade pip
Write-Host "🔄 Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Step 6: Install dependencies
if (Test-Path "requirements.txt") {
    Write-Host "📥 Installing dependencies from requirements.txt..." -ForegroundColor Yellow
    pip install -r requirements.txt
    Write-Host "✅ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "⚠️ No requirements.txt found - skipping dependency install" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Done! venv is ready" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Run 'python main.py' to start the app" -ForegroundColor Cyan