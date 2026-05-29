<#
.SYNOPSIS
    Build IT Admin Toolkit EXE and create a GitHub Release.

.DESCRIPTION
    - Reads current version from version.py
    - Bumps version (auto-patch, or manual major/minor/explicit)
    - Builds EXE with PyInstaller
    - Creates Git tag + GitHub Release with EXE attached
    - Optionally backs up source code

.PARAMETER Bump
    Version bump type: "patch" (default), "minor", "major"

.PARAMETER Version
    Explicit version override (e.g., "1.0.0", "2.1.0")

.PARAMETER SkipRelease
    Build EXE only, don't push to GitHub

.PARAMETER Draft
    Create GitHub release as draft (not published)

.PARAMETER Notes
    Release notes / changelog text

.EXAMPLE
    .\Build-Release.ps1                          # Auto-increment patch: 0.0.1 → 0.0.2
    .\Build-Release.ps1 -Bump minor              # Bump minor: 0.0.2 → 0.1.0
    .\Build-Release.ps1 -Bump major              # Bump major: 0.1.0 → 1.0.0
    .\Build-Release.ps1 -Version "1.0.0"         # Set explicit version
    .\Build-Release.ps1 -SkipRelease             # Build only, no GitHub push
    .\Build-Release.ps1 -Notes "Fixed winget"    # Custom release notes
    .\Build-Release.ps1 -Draft                   # Create as draft release
#>

param(
    [ValidateSet("patch", "minor", "major")]
    [string]$Bump = "patch",
    
    [string]$Version = "",
    
    [switch]$SkipRelease,
    
    [switch]$Draft,
    
    [string]$Notes = ""
)

$ErrorActionPreference = "Stop"

# ============================================================
#  CONFIGURATION
# ============================================================
$ProjectDir = $PSScriptRoot
$VersionFile = Join-Path $ProjectDir "version.py"
$DistDir = Join-Path $ProjectDir "dist"
$ExeName = "IT-Admin-Toolkit.exe"
$ExePath = Join-Path $DistDir $ExeName
$ReleaseDir = Join-Path $ProjectDir "release"

# GitHub repos
$PrivateRepo = "pshubert1/Install_Apps"          # Code pushes here
$PublicRepo  = "pshubert1/IT-Admin-Toolkit"       # EXE releases go here

$BackupScript = Join-Path $ProjectDir "Backup_App.ps1"

# ============================================================
#  FUNCTIONS
# ============================================================

function Get-CurrentVersion {
    if (-not (Test-Path $VersionFile)) {
        Write-Host "⚠️ version.py not found, creating with v0.0.0" -ForegroundColor Yellow
        Set-Content -Path $VersionFile -Value 'VERSION = "0.0.0"' -Encoding UTF8
        return "0.0.0"
    }
    
    $content = Get-Content $VersionFile -Raw
    if ($content -match 'VERSION\s*=\s*"(\d+\.\d+\.\d+)"') {
        return $Matches[1]
    }
    
    Write-Host "⚠️ Could not parse version, defaulting to 0.0.0" -ForegroundColor Yellow
    return "0.0.0"
}

function Get-NextVersion {
    param([string]$Current, [string]$BumpType)
    
    $parts = $Current.Split('.')
    $major = [int]$parts[0]
    $minor = [int]$parts[1]
    $patch = [int]$parts[2]
    
    switch ($BumpType) {
        "major" { $major++; $minor = 0; $patch = 0 }
        "minor" { $minor++; $patch = 0 }
        "patch" { $patch++ }
    }
    
    return "$major.$minor.$patch"
}

function Set-VersionFile {
    param([string]$NewVersion)
    
    $content = @"
"""
App version - auto-updated by Build-Release.ps1
"""
VERSION = "$NewVersion"
"@
    Set-Content -Path $VersionFile -Value $content -Encoding UTF8
}

function Test-GitHubCLI {
    try {
        $null = gh --version 2>$null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Install-GitHubCLI {
    Write-Host "📥 GitHub CLI (gh) not found. Installing..." -ForegroundColor Yellow
    
    # Try winget first
    try {
        winget install --id GitHub.cli --accept-source-agreements --accept-package-agreements
        if ($LASTEXITCODE -eq 0) {
            # Refresh PATH
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
            Write-Host "✅ GitHub CLI installed" -ForegroundColor Green
            return $true
        }
    } catch {}
    
    # Try choco
    try {
        choco install gh -y 2>$null
        if ($LASTEXITCODE -eq 0) {
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
            Write-Host "✅ GitHub CLI installed via Chocolatey" -ForegroundColor Green
            return $true
        }
    } catch {}
    
    Write-Host "❌ Could not auto-install GitHub CLI" -ForegroundColor Red
    Write-Host "   Install manually: https://cli.github.com/" -ForegroundColor Gray
    return $false
}

# ============================================================
#  MAIN BUILD PROCESS
# ============================================================

Write-Host ""
Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     🏗️  IT Admin Toolkit - Build & Release    ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Navigate to project directory
Set-Location $ProjectDir

# ── Step 1: Version ──────────────────────────────────────
Write-Host "📋 Step 1: Version" -ForegroundColor Yellow
$currentVersion = Get-CurrentVersion
Write-Host "   Current version: v$currentVersion" -ForegroundColor Gray

if ($Version -ne "") {
    # Explicit version override
    if ($Version -notmatch '^\d+\.\d+\.\d+$') {
        Write-Host "❌ Invalid version format. Use: X.Y.Z (e.g., 1.0.0)" -ForegroundColor Red
        exit 1
    }
    $newVersion = $Version
    Write-Host "   Manual override: v$newVersion" -ForegroundColor Cyan
} else {
    $newVersion = Get-NextVersion -Current $currentVersion -BumpType $Bump
    Write-Host "   Bump type: $Bump" -ForegroundColor Gray
}

Write-Host "   New version: v$newVersion" -ForegroundColor Green
Write-Host ""

# Confirm
$confirm = Read-Host "   Proceed with v$newVersion? (Y/n)"
if ($confirm -eq 'n' -or $confirm -eq 'N') {
    Write-Host "❌ Cancelled" -ForegroundColor Red
    exit 0
}

# Update version file
Set-VersionFile -NewVersion $newVersion
Write-Host "   ✅ version.py updated" -ForegroundColor Green
Write-Host ""

# ── Step 2: Backup ───────────────────────────────────────
Write-Host "💾 Step 2: Backup" -ForegroundColor Yellow
if (Test-Path $BackupScript) {
    Write-Host "   Running backup..." -ForegroundColor Gray
    & $BackupScript
    Write-Host "   ✅ Backup complete" -ForegroundColor Green
} else {
    Write-Host "   ⚠️ Backup script not found, skipping" -ForegroundColor Yellow
}
Write-Host ""

# ── Step 3: Build EXE ────────────────────────────────────
Write-Host "🔨 Step 3: Building EXE" -ForegroundColor Yellow

# Activate venv if it exists
$venvActivate = Join-Path $ProjectDir ".venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    Write-Host "   Activating virtual environment..." -ForegroundColor Gray
    & $venvActivate
}

# Clean old build
if (Test-Path (Join-Path $ProjectDir "build")) { 
    Remove-Item -Recurse -Force (Join-Path $ProjectDir "build") 
}
if (Test-Path $DistDir) { 
    Remove-Item -Recurse -Force $DistDir 
}
# Generate version info file for EXE metadata
Write-Host "   Generating version info..." -ForegroundColor Gray
$versionParts = $newVersion.Split('.')
$major = $versionParts[0]
$minor = $versionParts[1]
$patch = $versionParts[2]
$year = (Get-Date).Year

$versionInfoTemplate = Join-Path $ProjectDir "version_info_template.py"
$versionInfoFile = Join-Path $ProjectDir "version_info.txt"

if (Test-Path $versionInfoTemplate) {
    $content = Get-Content $versionInfoTemplate -Raw
    $content = $content -replace '\{MAJOR\}', $major
    $content = $content -replace '\{MINOR\}', $minor
    $content = $content -replace '\{PATCH\}', $patch
    $content = $content -replace '\{VERSION\}', $newVersion
    $content = $content -replace '\{COMPANY\}', 'IT Admin Toolkit'
    $content = $content -replace '\{DESCRIPTION\}', 'IT Admin Toolkit - System Administration Tool'
    $content = $content -replace '\{INTERNAL_NAME\}', 'IT-Admin-Toolkit'
    $content = $content -replace '\{COPYRIGHT\}', "Copyright (c) $year Patrick Shubert"
    $content = $content -replace '\{FILENAME\}', 'IT-Admin-Toolkit.exe'
    $content = $content -replace '\{PRODUCT_NAME\}', 'IT Admin Toolkit'
    Set-Content -Path $versionInfoFile -Value $content -Encoding UTF8
    Write-Host "   ✅ Version info: v$newVersion" -ForegroundColor Green
} else {
    Write-Host "   ⚠️ version_info_template.py not found, skipping EXE metadata" -ForegroundColor Yellow
}

# Build
Write-Host "   Running PyInstaller..." -ForegroundColor Gray
$pyinstallerArgs = @(
    "--onefile"
    "--windowed"
    "--name", "IT-Admin-Toolkit"
    "--icon=icon.ico"
    "--add-data", "icon.ico;."
    "--add-data", "scripts;scripts"
    "--add-data", "version.py;."
    "--uac-admin"
    "--clean"
    # Hidden imports for Update tab services
    "--hidden-import", "services"
    "--hidden-import", "services.update_service"
    "--hidden-import", "services.install_service"
    "--hidden-import", "services.feature_update_service"
    "--hidden-import", "services.reboot_service"
    "--hidden-import", "models"
    "--hidden-import", "models.update_info"
    # pywin32 modules (needed by update services)
    "--hidden-import", "win32com"
    "--hidden-import", "win32com.client"
    "--hidden-import", "pythoncom"
    "--hidden-import", "pywintypes"
    "--hidden-import", "win32api"
    "main.py"
)

# Add version info if generated
if (Test-Path $versionInfoFile) {
    $pyinstallerArgs += "--version-file", $versionInfoFile
}

# Add manifest if it exists
if (Test-Path (Join-Path $ProjectDir "admin.manifest")) {
    $pyinstallerArgs += "--manifest", "admin.manifest"
}

pyinstaller @pyinstallerArgs 2>&1 | ForEach-Object {
    if ($_ -match "error|ERROR|Error") {
        Write-Host "   $_" -ForegroundColor Red
    } elseif ($_ -match "Building|Appending|Copying") {
        Write-Host "   $_" -ForegroundColor Gray
    }
}

if (-not (Test-Path $ExePath)) {
    Write-Host "❌ Build failed! EXE not found at: $ExePath" -ForegroundColor Red
    exit 1
}

$exeSize = (Get-Item $ExePath).Length / 1MB
Write-Host "   ✅ Build successful! ($([math]::Round($exeSize, 1)) MB)" -ForegroundColor Green
Write-Host "   📁 $ExePath" -ForegroundColor Gray
Write-Host ""

# ── Step 3b: Copy to Release Folder ──────────────────────
Write-Host "📦 Step 3b: Copying to Release folder" -ForegroundColor Yellow

$ReleaseDir = Join-Path $ProjectDir "release"
if (-not (Test-Path $ReleaseDir)) {
    New-Item -ItemType Directory -Path $ReleaseDir -Force | Out-Null
}

# Copy with version in filename
$versionedExe = "IT-Admin-Toolkit-v$newVersion.exe"
$releasePath = Join-Path $ReleaseDir $versionedExe
Copy-Item -Path $ExePath -Destination $releasePath -Force

# Also keep a "latest" copy for easy access
$latestPath = Join-Path $ReleaseDir "IT-Admin-Toolkit-latest.exe"
Copy-Item -Path $ExePath -Destination $latestPath -Force

Write-Host "   ✅ Copied to: release\$versionedExe" -ForegroundColor Green
Write-Host "   ✅ Updated:   release\IT-Admin-Toolkit-latest.exe" -ForegroundColor Green
Write-Host ""


# ── Step 4: Clean Build Artifacts ─────────────────────────
Write-Host "🧹 Step 4: Cleanup" -ForegroundColor Yellow
$specFile = Join-Path $ProjectDir "IT-Admin-Toolkit.spec"
if (Test-Path $specFile) { Remove-Item $specFile -Force }
if (Test-Path (Join-Path $ProjectDir "build")) { Remove-Item -Recurse -Force (Join-Path $ProjectDir "build") }
if (Test-Path $versionInfoFile) { Remove-Item $versionInfoFile -Force }
Write-Host "   ✅ Cleaned build artifacts" -ForegroundColor Green

# ── Step 5: Git Commit + Tag ─────────────────────────────
Write-Host "📝 Step 5: Git Commit & Tag" -ForegroundColor Yellow

# Check for existing tag
$existingTag = git tag -l "v$newVersion" 2>$null
if ($existingTag) {
    Write-Host "   ⚠️ Tag v$newVersion already exists, deleting..." -ForegroundColor Yellow
    git tag -d "v$newVersion" 2>$null
    git push origin --delete "v$newVersion" 2>$null
}

# Stage and commit
git add -A
$commitMsg = "Release v$newVersion"
if ($Notes -ne "") {
    $commitMsg = "Release v$newVersion - $Notes"
}
git commit -m $commitMsg 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "   ⚠️ Nothing to commit (already up to date)" -ForegroundColor Yellow
}

# Create tag
git tag -a "v$newVersion" -m "Release v$newVersion"
Write-Host "   ✅ Tagged: v$newVersion" -ForegroundColor Green

# Push
Write-Host "   Pushing to GitHub..." -ForegroundColor Gray
git push origin main 2>$null
git push origin "v$newVersion" 2>$null
Write-Host "   ✅ Pushed to GitHub" -ForegroundColor Green
Write-Host ""

# ── Step 6: GitHub Release ────────────────────────────────
if ($SkipRelease) {
    Write-Host "⏭️ Step 6: Skipping GitHub Release (-SkipRelease)" -ForegroundColor Yellow
} else {
    Write-Host "🚀 Step 6: Creating GitHub Release" -ForegroundColor Yellow
    
    # Check for GitHub CLI
    if (-not (Test-GitHubCLI)) {
        Write-Host "   GitHub CLI (gh) not found" -ForegroundColor Yellow
        $installChoice = Read-Host "   Install GitHub CLI? (Y/n)"
        if ($installChoice -ne 'n' -and $installChoice -ne 'N') {
            $installed = Install-GitHubCLI
            if (-not $installed) {
                Write-Host "   ⚠️ Skipping GitHub Release (no gh CLI)" -ForegroundColor Yellow
                Write-Host "   📋 Tag v$newVersion was still pushed" -ForegroundColor Gray
                Write-Host ""
                Write-Host "   Create release manually at:" -ForegroundColor Gray
                Write-Host "  https://github.com/$PublicRepo/releases/new?tag=v$newVersion" -ForegroundColor Cyan
                
                # Skip to summary
                $SkipRelease = $true
            }
        } else {
            $SkipRelease = $true
            Write-Host "   ⚠️ Skipping GitHub Release" -ForegroundColor Yellow
            Write-Host "   📋 Tag v$newVersion was still pushed" -ForegroundColor Gray
        }
    }
    
    if (-not $SkipRelease) {
        # Check if authenticated
        $null = gh auth status 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "   ⚠️ Not authenticated. Running 'gh auth login'..." -ForegroundColor Yellow
            gh auth login
        }
        
        # Build release notes
        if ($Notes -eq "") {
            $Notes = "## IT Admin Toolkit v$newVersion`n`n"
            $Notes += "### Changes`n"
            
            # Auto-generate from recent commits
            $recentCommits = git log --oneline -10 "v$currentVersion..HEAD" 2>$null
            if ($recentCommits) {
                foreach ($commit in $recentCommits) {
                    $Notes += "- $commit`n"
                }
            } else {
                $Notes += "- Release v$newVersion`n"
            }
            
            $Notes += "`n### Download`n"
            $Notes += "Download ``$ExeName`` below and run as Administrator.`n"
        }
        
        # Create release
        $releaseArgs = @(
            "release", "create", "v$newVersion"
            $releasePath
            "--repo", $PublicRepo
            "--title", "v$newVersion"
            "--notes", $Notes
        )
        
        if ($Draft) {
            $releaseArgs += "--draft"
        }
        
        Write-Host "   Creating release with EXE attachment..." -ForegroundColor Gray
        gh @releaseArgs
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ GitHub Release created!" -ForegroundColor Green
            Write-Host "   🔗 https://github.com/$PublicRepo/releases/new?tag=v$newVersion" -ForegroundColor Cyan
        } else {
            Write-Host "   ❌ Release creation failed" -ForegroundColor Red
            Write-Host "   Create manually at:" -ForegroundColor Gray
            Write-Host "   https://github.com/$PublicRepo/releases/new?tag=v$newVersion" -ForegroundColor Cyan
        }
    }
}

Write-Host ""

# ── Summary ───────────────────────────────────────────────
Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║            ✅ BUILD COMPLETE                  ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "   Version:  v$newVersion" -ForegroundColor White
Write-Host "   EXE:      $ExePath" -ForegroundColor White
Write-Host "   Size:     $([math]::Round($exeSize, 1)) MB" -ForegroundColor White
Write-Host "   Tag:      v$newVersion" -ForegroundColor White
if (-not $SkipRelease) {
    Write-Host "   Release:  🔗 https://github.com/$PublicRepo/releases/tag/v$newVersion" -ForegroundColor Cyan
}
Write-Host ""

# ── Version History ───────────────────────────────────────
$historyFile = Join-Path $ProjectDir "CHANGELOG.md"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
$changelogEntry = "## v$newVersion ($timestamp)`n"

if ($Notes -ne "" -and $Notes -notmatch "^## IT Admin") {
    $changelogEntry += "$Notes`n"
}

$changelogEntry += "`n"

if (Test-Path $historyFile) {
    $existing = Get-Content $historyFile -Raw
    $changelogEntry + $existing | Set-Content $historyFile -Encoding UTF8
} else {
    "# Changelog`n`n" + $changelogEntry | Set-Content $historyFile -Encoding UTF8
}

Write-Host "   📜 CHANGELOG.md updated" -ForegroundColor Gray
Write-Host ""
Write-Host "   EXE:      release\$versionedExe" -ForegroundColor White