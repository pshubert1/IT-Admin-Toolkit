<#
.SYNOPSIS
    Build IT Admin Toolkit EXE and create a GitHub Release.

.DESCRIPTION
    - Reads current version from version.py
    - Bumps version (auto-patch, or manual major/minor/explicit)
    - Builds EXE with PyInstaller
    - Auto-generates release notes from git commits
    - Creates Git tag + GitHub Release with EXE attached on BOTH repos
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
    Release notes / changelog text (overrides auto-generated notes)

.PARAMETER Category
    Release category tag: "bugfix", "feature", "security", "maintenance"

.EXAMPLE
    .\Build-Release.ps1                          # Auto-increment patch: 0.0.1 -> 0.0.2
    .\Build-Release.ps1 -Bump minor              # Bump minor: 0.0.2 -> 0.1.0
    .\Build-Release.ps1 -Bump major              # Bump major: 0.1.0 -> 1.0.0
    .\Build-Release.ps1 -Version "1.0.0"         # Set explicit version
    .\Build-Release.ps1 -SkipRelease             # Build only, no GitHub push
    .\Build-Release.ps1 -Notes "Fixed winget"    # Custom release notes
    .\Build-Release.ps1 -Draft                   # Create as draft release
    .\Build-Release.ps1 -Category bugfix         # Tag release as bugfix
#>

param(
    [ValidateSet("patch", "minor", "major")]
    [string]$Bump = "patch",
    
    [string]$Version = "",
    
    [switch]$SkipRelease,
    
    [switch]$Draft,
    
    [string]$Notes = "",
    
    [ValidateSet("bugfix", "feature", "security", "maintenance", "")]
    [string]$Category = ""
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
        Write-Host "  version.py not found, creating with v0.0.0" -ForegroundColor Yellow
        Set-Content -Path $VersionFile -Value 'VERSION = "0.0.0"' -Encoding UTF8
        return "0.0.0"
    }
    
    $content = Get-Content $VersionFile -Raw
    if ($content -match 'VERSION\s*=\s*"(\d+\.\d+\.\d+)"') {
        return $Matches[1]
    }
    
    Write-Host "  Could not parse version, defaulting to 0.0.0" -ForegroundColor Yellow
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
    Write-Host "  GitHub CLI (gh) not found. Installing..." -ForegroundColor Yellow
    
    try {
        winget install --id GitHub.cli --accept-source-agreements --accept-package-agreements
        if ($LASTEXITCODE -eq 0) {
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
            Write-Host "  GitHub CLI installed" -ForegroundColor Green
            return $true
        }
    } catch {}
    
    try {
        choco install gh -y 2>$null
        if ($LASTEXITCODE -eq 0) {
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
            Write-Host "  GitHub CLI installed via Chocolatey" -ForegroundColor Green
            return $true
        }
    } catch {}
    
    Write-Host "  Could not auto-install GitHub CLI" -ForegroundColor Red
    Write-Host "   Install manually: https://cli.github.com/" -ForegroundColor Gray
    return $false
}

# ============================================================
#  AUTO-GENERATE RELEASE NOTES FROM GIT HISTORY
# ============================================================

function Get-AutoReleaseNotes {
    param(
        [string]$CurrentVersion,
        [string]$NewVersion,
        [string]$CategoryTag
    )
    
    $notes = ""
    $timestamp = Get-Date -Format "yyyy-MM-dd"
    
    # Header
    $notes += "## IT Admin Toolkit v$NewVersion`n"
    $notes += "**Released:** $timestamp`n`n"
    
    # Category badge
    if ($CategoryTag -ne "") {
        $badge = switch ($CategoryTag) {
            "bugfix"      { "Bug Fix" }
            "feature"     { "New Feature" }
            "security"    { "Security Update" }
            "maintenance" { "Maintenance" }
        }
        $notes += "**Type:** $badge`n`n"
    }
    
    # Get commits since last tag
    $lastTag = git describe --tags --abbrev=0 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $lastTag) {
        # No previous tag, get all commits
        $commits = git log --oneline --no-merges -20 2>$null
    } else {
        $commits = git log --oneline --no-merges "$lastTag..HEAD" 2>$null
    }
    
    if (-not $commits) {
        $notes += "### Changes`n- Release v$NewVersion`n`n"
        return $notes
    }
    
    # Categorize commits by conventional commit prefixes
    $features = @()
    $fixes = @()
    $improvements = @()
    $docs = @()
    $other = @()
    
    foreach ($commit in $commits) {
        # Strip the short hash (first 7-8 chars + space)
        $msg = ($commit -replace '^\w+\s+', '').Trim()
        
        # Skip empty or merge commits
        if (-not $msg -or $msg -match '^Merge') { continue }
        
        # Categorize based on prefix keywords
        if ($msg -match '^(feat|add|new|feature)[:\s\(]' -or $msg -match 'added|new feature|implement') {
            $features += $msg
        }
        elseif ($msg -match '^(fix|bug|patch|hotfix)[:\s\(]' -or $msg -match 'fixed|bugfix|repair|resolve') {
            $fixes += $msg
        }
        elseif ($msg -match '^(doc|docs|readme)[:\s\(]' -or $msg -match 'documentation|readme') {
            $docs += $msg
        }
        elseif ($msg -match '^(refactor|improve|update|enhance|perf|style|clean)[:\s\(]' -or $msg -match 'improve|update|enhance|refactor|cleanup') {
            $improvements += $msg
        }
        else {
            $other += $msg
        }
    }
    
    # Build categorized notes
    if ($features.Count -gt 0) {
        $notes += "### New Features`n"
        foreach ($f in $features) { $notes += "- $f`n" }
        $notes += "`n"
    }
    
    if ($fixes.Count -gt 0) {
        $notes += "### Bug Fixes`n"
        foreach ($f in $fixes) { $notes += "- $f`n" }
        $notes += "`n"
    }
    
    if ($improvements.Count -gt 0) {
        $notes += "### Improvements`n"
        foreach ($f in $improvements) { $notes += "- $f`n" }
        $notes += "`n"
    }
    
    if ($docs.Count -gt 0) {
        $notes += "### Documentation`n"
        foreach ($f in $docs) { $notes += "- $f`n" }
        $notes += "`n"
    }
    
    if ($other.Count -gt 0) {
        $notes += "### Other Changes`n"
        foreach ($f in $other) { $notes += "- $f`n" }
        $notes += "`n"
    }
    
    # Footer
    $notes += "---`n"
    $notes += "### Download`n"
    $notes += "Download ``$ExeName`` below and run as Administrator.`n"
    
    return $notes
}

# ============================================================
#  MAIN BUILD PROCESS
# ============================================================

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "     IT Admin Toolkit - Build & Release         " -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to project directory
Set-Location $ProjectDir

# -- Step 1: Version --
Write-Host "[Step 1] Version" -ForegroundColor Yellow
$currentVersion = Get-CurrentVersion
Write-Host "   Current version: v$currentVersion" -ForegroundColor Gray

if ($Version -ne "") {
    if ($Version -notmatch '^\d+\.\d+\.\d+$') {
        Write-Host "   ERROR: Invalid version format. Use: X.Y.Z (e.g., 1.0.0)" -ForegroundColor Red
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
    Write-Host "   Cancelled" -ForegroundColor Red
    exit 0
}

# Update version file
Set-VersionFile -NewVersion $newVersion
Write-Host "   [OK] version.py updated" -ForegroundColor Green
Write-Host ""

# -- Step 2: Auto-Generate Release Notes --
Write-Host "[Step 2] Release Notes" -ForegroundColor Yellow

if ($Notes -eq "") {
    $autoNotes = Get-AutoReleaseNotes -CurrentVersion $currentVersion -NewVersion $newVersion -CategoryTag $Category
    Write-Host "   Auto-generated from git history:" -ForegroundColor Gray
    Write-Host ""
    Write-Host $autoNotes -ForegroundColor DarkGray
    Write-Host ""
    
    $editNotes = Read-Host "   Edit notes? (Y/n/skip)"
    if ($editNotes -eq 'Y' -or $editNotes -eq 'y') {
        # Save to temp file for editing
        $tempNotesFile = Join-Path $env:TEMP "release_notes_temp.md"
        Set-Content -Path $tempNotesFile -Value $autoNotes -Encoding UTF8
        
        # Open in VS Code or notepad
        $editor = "code"
        try {
            & $editor --wait $tempNotesFile 2>$null
            if ($LASTEXITCODE -ne 0) { throw "VS Code failed" }
        } catch {
            notepad $tempNotesFile | Out-Null
            Start-Sleep -Seconds 1
            Write-Host "   Press Enter after saving notes in Notepad..." -ForegroundColor Yellow
            Read-Host
        }
        
        $Notes = Get-Content $tempNotesFile -Raw
        Remove-Item $tempNotesFile -Force -ErrorAction SilentlyContinue
        Write-Host "   [OK] Notes edited" -ForegroundColor Green
    }
    elseif ($editNotes -eq 'skip') {
        $Notes = "Release v$newVersion"
        Write-Host "   [OK] Using minimal notes" -ForegroundColor Yellow
    }
    else {
        $Notes = $autoNotes
        Write-Host "   [OK] Using auto-generated notes" -ForegroundColor Green
    }
} else {
    # User provided -Notes parameter, wrap it in proper format
    $timestamp = Get-Date -Format "yyyy-MM-dd"
    $Notes = "## IT Admin Toolkit v$newVersion`n**Released:** $timestamp`n`n### Changes`n- $Notes`n`n---`n### Download`nDownload ``$ExeName`` below and run as Administrator.`n"
    Write-Host "   [OK] Using provided notes" -ForegroundColor Green
}
Write-Host ""

# -- Step 3: Backup --
Write-Host "[Step 3] Backup" -ForegroundColor Yellow
if (Test-Path $BackupScript) {
    Write-Host "   Running backup..." -ForegroundColor Gray
    & $BackupScript
    Write-Host "   [OK] Backup complete" -ForegroundColor Green
} else {
    Write-Host "   Backup script not found, skipping" -ForegroundColor Yellow
}
Write-Host ""

# -- Step 4: Build EXE --
Write-Host "[Step 4] Building EXE" -ForegroundColor Yellow

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
    Write-Host "   [OK] Version info: v$newVersion" -ForegroundColor Green
} else {
    Write-Host "   version_info_template.py not found, skipping EXE metadata" -ForegroundColor Yellow
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

    # === EXCLUDE UNUSED STDLIB (saves ~5-8 MB) ===
    "--exclude-module", "matplotlib"
    "--exclude-module", "numpy"
    "--exclude-module", "pandas"
    "--exclude-module", "scipy"
    "--exclude-module", "PIL"
    "--exclude-module", "setuptools"
    "--exclude-module", "pkg_resources"
    "--exclude-module", "unittest"
    "--exclude-module", "test"
    "--exclude-module", "xmlrpc"
    "--exclude-module", "pydoc"
    "--exclude-module", "doctest"
    "--exclude-module", "lib2to3"
    "--exclude-module", "distutils"
    "--exclude-module", "curses"
    "--exclude-module", "asyncio"
    "--exclude-module", "concurrent"
    "--exclude-module", "multiprocessing"
    "--exclude-module", "sqlite3"
    "--exclude-module", "email"
    "--exclude-module", "http.server"
    "--exclude-module", "ftplib"
    "--exclude-module", "imaplib"
    "--exclude-module", "smtplib"
    "--exclude-module", "decimal"
    "--exclude-module", "fractions"
    "--exclude-module", "statistics"
    "--exclude-module", "argparse"

    # === EXCLUDE UNUSED PYWIN32 (saves ~2-4 MB) ===
    "--exclude-module", "win32ui"
    "--exclude-module", "win32print"
    "--exclude-module", "win32clipboard"
    "--exclude-module", "win32pipe"
    "--exclude-module", "win32net"
    "--exclude-module", "win32wnet"
    "--exclude-module", "adodbapi"
    "--exclude-module", "isapi"
    "--exclude-module", "pythonwin"

    # === HIDDEN IMPORTS (keep - your app needs these) ===
    "--hidden-import", "services"
    "--hidden-import", "services.update_service"
    "--hidden-import", "services.install_service"
    "--hidden-import", "services.feature_update_service"
    "--hidden-import", "services.reboot_service"
    "--hidden-import", "models"
    "--hidden-import", "models.update_info"
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
    Write-Host "   ERROR: Build failed! EXE not found at: $ExePath" -ForegroundColor Red
    exit 1
}

$exeSize = (Get-Item $ExePath).Length / 1MB
Write-Host "   [OK] Build successful! ($([math]::Round($exeSize, 1)) MB)" -ForegroundColor Green
Write-Host "   Path: $ExePath" -ForegroundColor Gray

# Get SHA256 for SentinelOne/Cynet whitelisting
$exeHash = (Get-FileHash $ExePath -Algorithm SHA256).Hash
Write-Host "   SHA256: $exeHash" -ForegroundColor Gray
Write-Host ""

# -- Step 4b: Copy to Release Folder --
Write-Host "[Step 4b] Copying to Release folder" -ForegroundColor Yellow

if (-not (Test-Path $ReleaseDir)) {
    New-Item -ItemType Directory -Path $ReleaseDir -Force | Out-Null
}

$versionedExe = "IT-Admin-Toolkit-v$newVersion.exe"
$releasePath = Join-Path $ReleaseDir $versionedExe
Copy-Item -Path $ExePath -Destination $releasePath -Force

$latestPath = Join-Path $ReleaseDir "IT-Admin-Toolkit-latest.exe"
Copy-Item -Path $ExePath -Destination $latestPath -Force

Write-Host "   [OK] Copied to: release\$versionedExe" -ForegroundColor Green
Write-Host "   [OK] Updated:   release\IT-Admin-Toolkit-latest.exe" -ForegroundColor Green
Write-Host ""

# -- Step 5: Clean Build Artifacts --
Write-Host "[Step 5] Cleanup" -ForegroundColor Yellow
$specFile = Join-Path $ProjectDir "IT-Admin-Toolkit.spec"
if (Test-Path $specFile) { Remove-Item $specFile -Force }
if (Test-Path (Join-Path $ProjectDir "build")) { Remove-Item -Recurse -Force (Join-Path $ProjectDir "build") }
if (Test-Path $versionInfoFile) { Remove-Item $versionInfoFile -Force }
Write-Host "   [OK] Cleaned build artifacts" -ForegroundColor Green
Write-Host ""

# -- Step 6: Git Commit + Tag --
Write-Host "[Step 6] Git Commit & Tag" -ForegroundColor Yellow

# Check for existing tag
$existingTag = git tag -l "v$newVersion" 2>$null
if ($existingTag) {
    Write-Host "   Tag v$newVersion already exists, deleting..." -ForegroundColor Yellow
    git tag -d "v$newVersion" 2>$null
    git push origin --delete "v$newVersion" 2>$null
}

# Stage and commit
git add -A
$commitMsg = "Release v$newVersion"
if ($Category -ne "") {
    $commitMsg = "[$Category] Release v$newVersion"
}
git commit -m $commitMsg 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "   Nothing to commit (already up to date)" -ForegroundColor Yellow
}

# Create annotated tag with release notes summary
$tagMsg = "Release v$newVersion"
git tag -a "v$newVersion" -m $tagMsg
Write-Host "   [OK] Tagged: v$newVersion" -ForegroundColor Green

# Push to private repo
Write-Host "   Pushing to private repo ($PrivateRepo)..." -ForegroundColor Gray
git push origin main 2>$null
git push origin "v$newVersion" 2>$null
Write-Host "   [OK] Pushed to private repo" -ForegroundColor Green
Write-Host ""

# -- Step 7: GitHub Releases (Both Repos) --
if ($SkipRelease) {
    Write-Host "[Step 7] Skipping GitHub Release (-SkipRelease)" -ForegroundColor Yellow
} else {
    Write-Host "[Step 7] Creating GitHub Releases" -ForegroundColor Yellow
    
    # Check for GitHub CLI
    if (-not (Test-GitHubCLI)) {
        Write-Host "   GitHub CLI (gh) not found" -ForegroundColor Yellow
        $installChoice = Read-Host "   Install GitHub CLI? (Y/n)"
        if ($installChoice -ne 'n' -and $installChoice -ne 'N') {
            $installed = Install-GitHubCLI
            if (-not $installed) {
                Write-Host "   Skipping GitHub Release (no gh CLI)" -ForegroundColor Yellow
                $SkipRelease = $true
            }
        } else {
            $SkipRelease = $true
        }
    }
    
    if (-not $SkipRelease) {
        # Check if authenticated
        $null = gh auth status 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "   Not authenticated. Running 'gh auth login'..." -ForegroundColor Yellow
            gh auth login
        }
        
        # Save notes to temp file (avoids command line escaping issues)
        $notesFile = Join-Path $env:TEMP "release_notes.md"
        Set-Content -Path $notesFile -Value $Notes -Encoding UTF8
        
        # ── Release on PRIVATE repo (code + notes, no exe) ──
        Write-Host ""
        Write-Host "   [Private] Creating release on $PrivateRepo..." -ForegroundColor Gray
        
        $privateArgs = @(
            "release", "create", "v$newVersion"
            "--repo", $PrivateRepo
            "--title", "v$newVersion"
            "--notes-file", $notesFile
        )
        if ($Draft) { $privateArgs += "--draft" }
        
        gh @privateArgs 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   [OK] Private release created" -ForegroundColor Green
            Write-Host "   URL: https://github.com/$PrivateRepo/releases/tag/v$newVersion" -ForegroundColor Cyan
        } else {
            Write-Host "   WARNING: Private release failed (tag may already exist)" -ForegroundColor Yellow
        }
        
        # ── Release on PUBLIC repo (exe + notes) ──
        Write-Host ""
        Write-Host "   [Public] Creating release on $PublicRepo..." -ForegroundColor Gray
        
        # Push tag to public repo too
        git push "https://github.com/$PublicRepo.git" "v$newVersion" 2>$null
        
        $publicArgs = @(
            "release", "create", "v$newVersion"
            $releasePath
            "--repo", $PublicRepo
            "--title", "IT Admin Toolkit v$newVersion"
            "--notes-file", $notesFile
        )
        if ($Draft) { $publicArgs += "--draft" }
        
        gh @publicArgs 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   [OK] Public release created (with EXE)" -ForegroundColor Green
            Write-Host "   URL: https://github.com/$PublicRepo/releases/tag/v$newVersion" -ForegroundColor Cyan
        } else {
            Write-Host "   WARNING: Public release failed" -ForegroundColor Yellow
            Write-Host "   Create manually: https://github.com/$PublicRepo/releases/new?tag=v$newVersion" -ForegroundColor Gray
        }
        
        # Cleanup temp notes file
        Remove-Item $notesFile -Force -ErrorAction SilentlyContinue
    }
}

Write-Host ""

# -- Step 8: Update CHANGELOG.md --
Write-Host "[Step 8] Updating CHANGELOG.md" -ForegroundColor Yellow

$historyFile = Join-Path $ProjectDir "CHANGELOG.md"
$changelogEntry = $Notes + "`n`n"

if (Test-Path $historyFile) {
    $existing = Get-Content $historyFile -Raw
    $changelogEntry + $existing | Set-Content $historyFile -Encoding UTF8
} else {
    "# Changelog`n`n" + $changelogEntry | Set-Content $historyFile -Encoding UTF8
}

# Commit the changelog update
git add CHANGELOG.md
git commit -m "docs: update CHANGELOG.md for v$newVersion" 2>$null
git push origin main 2>$null

Write-Host "   [OK] CHANGELOG.md updated and pushed" -ForegroundColor Green
Write-Host ""

# -- Summary --
Write-Host "================================================" -ForegroundColor Green
Write-Host "            BUILD COMPLETE                      " -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "   Version:  v$newVersion" -ForegroundColor White
Write-Host "   EXE:      release\$versionedExe" -ForegroundColor White
Write-Host "   Size:     $([math]::Round($exeSize, 1)) MB" -ForegroundColor White
Write-Host "   SHA256:   $exeHash" -ForegroundColor White
Write-Host "   Tag:      v$newVersion" -ForegroundColor White
if ($Category -ne "") {
    Write-Host "   Category: $Category" -ForegroundColor White
}
if (-not $SkipRelease) {
    Write-Host ""
    Write-Host "   Private:  https://github.com/$PrivateRepo/releases/tag/v$newVersion" -ForegroundColor Cyan
    Write-Host "   Public:   https://github.com/$PublicRepo/releases/tag/v$newVersion" -ForegroundColor Cyan
}
Write-Host ""
