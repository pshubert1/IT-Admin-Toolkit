<#
.SYNOPSIS
    Downloads and runs the latest IT Admin Toolkit from GitHub.
.DESCRIPTION
    Fetches the latest release EXE from GitHub and optionally runs it as Administrator.
.EXAMPLE
    # Run directly from the internet:
    irm https://raw.githubusercontent.com/pshubert1/IT-Admin-Toolkit/main/Install.ps1 | iex
    
    # Or download and run manually:
    .\Install.ps1
#>

$repo = "pshubert1/IT-Admin-Toolkit"
$outputDir = "$env:USERPROFILE\Desktop"
$exeName = "IT-Admin-Toolkit.exe"
$outputPath = Join-Path $outputDir $exeName

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   IT Admin Toolkit - Download & Install" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Checking latest release..." -ForegroundColor Gray
try {
    $release = Invoke-RestMethod "https://api.github.com/repos/$repo/releases/latest"
    $version = $release.tag_name
    $asset = $release.assets | Where-Object { $_.name -like "*.exe" } | Select-Object -First 1
    
    if (-not $asset) {
        Write-Host "No EXE found in latest release" -ForegroundColor Red
        exit 1
    }
    
    $downloadUrl = $asset.browser_download_url
    $size = [math]::Round($asset.size / 1MB, 1)
    
    Write-Host "Version:  $version" -ForegroundColor Green
    Write-Host "Size:     $size MB" -ForegroundColor Green
    Write-Host "Save to:  $outputPath" -ForegroundColor Green
    Write-Host ""
    
    # Check if already exists
    if (Test-Path $outputPath) {
        Write-Host "Existing file found on Desktop - will be replaced" -ForegroundColor Yellow
    }
    
    Write-Host "Downloading..." -ForegroundColor Yellow
    
    $ProgressPreference = 'SilentlyContinue'
    Invoke-WebRequest -Uri $downloadUrl -OutFile $outputPath -UseBasicParsing
    $ProgressPreference = 'Continue'
    
    if (Test-Path $outputPath) {
        $actualSize = [math]::Round((Get-Item $outputPath).Length / 1MB, 1)
        Write-Host "Downloaded! ($actualSize MB)" -ForegroundColor Green
        Write-Host ""
        
        $run = Read-Host "Run now as Administrator? (Y/n)"
        if ($run -ne 'n' -and $run -ne 'N') {
            Write-Host "Launching as Administrator..." -ForegroundColor Cyan
            Start-Process $outputPath -Verb RunAs
        } else {
            Write-Host "Saved to Desktop: $exeName" -ForegroundColor Green
        }
    } else {
        Write-Host "Download failed - file not found" -ForegroundColor Red
    }
    
} catch {
    Write-Host "Failed: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Manual download:" -ForegroundColor Yellow
    Write-Host "https://github.com/$repo/releases/latest" -ForegroundColor Cyan
}

Write-Host ""
