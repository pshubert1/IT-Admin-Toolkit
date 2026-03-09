# NAME: 🔧 Setup Dev Environment
# DESCRIPTION: Installs everything needed to develop the IT Admin Toolkit

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Dev Environment Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "Please run as Administrator!" -ForegroundColor Red
    exit 1
}

# Install software via winget
Write-Host "Installing core software..." -ForegroundColor Yellow

$apps = @(
    @{name="VS Code"; id="Microsoft.VisualStudioCode"},
    @{name="Python 3.12"; id="Python.Python.3.12"},
    @{name="7-Zip"; id="7zip.7zip"},
    @{name="Git"; id="Git.Git"}
)

foreach ($app in $apps) {
    Write-Host "  Installing $($app.name)..." -ForegroundColor Gray
    winget install --id $app.id --silent --accept-package-agreements --accept-source-agreements 2>$null
}

Write-Host ""
Write-Host "Installing VS Code extensions..." -ForegroundColor Yellow

$extensions = @(
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.debugpy",
    "ms-vscode.powershell"
)

# Refresh PATH to include code command
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

foreach ($ext in $extensions) {
    Write-Host "  Installing $ext..." -ForegroundColor Gray
    code --install-extension $ext 2>$null
}

Write-Host ""
Write-Host "Installing Python packages..." -ForegroundColor Yellow

# Refresh PATH for Python
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

python -m pip install --upgrade pip 2>$null
pip install pyinstaller 2>$null

Write-Host ""
Write-Host "🔄 Setting up Python virtual environment..." -ForegroundColor Cyan
& "$PSScriptRoot\reset-venv.ps1"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Installed:" -ForegroundColor Cyan
Write-Host "  - VS Code" -ForegroundColor Whiteabout:blank#blocked
Write-Host "  - Python 3.12" -ForegroundColor White
Write-Host "  - 7-Zip" -ForegroundColor White
Write-Host "  - Git" -ForegroundColor White
Write-Host "  - PyInstaller" -ForegroundColor White
Write-Host "  - VS Code Extensions (Python, PowerShell)" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Open VS Code" -ForegroundColor White
Write-Host "  2. Open your project folder" -ForegroundColor White
Write-Host "  3. Run: python main.py" -ForegroundColor White
Write-Host "  4. Build: .\build.ps1" -ForegroundColor White