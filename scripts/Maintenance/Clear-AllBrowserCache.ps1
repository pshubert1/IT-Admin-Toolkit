# NAME: 🧹 Clear All Browser Caches
# DESCRIPTION: Clears cache for Chrome, Edge, and Firefox
# STYLE: Danger.TButton

Write-Host "Clearing Browser Caches" -ForegroundColor Cyan
Write-Host "=======================" -ForegroundColor Cyan
Write-Host ""

# Close browsers first
Write-Host "Closing browsers..." -ForegroundColor Yellow
Stop-Process -Name "chrome","msedge","firefox" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Chrome
$ChromeCache = "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Cache"
if (Test-Path $ChromeCache) {
    Remove-Item "$ChromeCache\*" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "✅ Chrome cache cleared" -ForegroundColor Green
}

# Edge
$EdgeCache = "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Cache"
if (Test-Path $EdgeCache) {
    Remove-Item "$EdgeCache\*" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "✅ Edge cache cleared" -ForegroundColor Green
}

# Firefox
$FirefoxProfiles = "$env:APPDATA\Mozilla\Firefox\Profiles"
if (Test-Path $FirefoxProfiles) {
    Get-ChildItem $FirefoxProfiles -Directory | ForEach-Object {
        $cache = "$($_.FullName)\cache2"
        if (Test-Path $cache) {
            Remove-Item "$cache\*" -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
    Write-Host "✅ Firefox cache cleared" -ForegroundColor Green
}

Write-Host ""
Write-Host "✅ All browser caches cleared!" -ForegroundColor Cyan