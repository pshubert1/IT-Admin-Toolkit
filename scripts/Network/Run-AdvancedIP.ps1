# NAME: 🌐 Advanced IP Scanner
# DESCRIPTION: Downloads and runs Advanced IP Scanner - no prompts
# STYLE: Dark.TButton

Write-Host "Advanced IP Scanner (Portable)" -ForegroundColor Cyan
Write-Host ""

$TempDir = "$env:TEMP\AdvancedIPScanner"
$exe = "$TempDir\Advanced_IP_Scanner.exe"
$settingsFile = "$TempDir\advanced_ip_scanner_settings.xml"
$url = "https://download.advanced-ip-scanner.com/download/files/Advanced_IP_Scanner_2.5.4594.1.exe"

# Create folder
if (-not (Test-Path $TempDir)) {
    New-Item -ItemType Directory -Path $TempDir -Force | Out-Null
}

# Download if needed
if (-not (Test-Path $exe)) {
    Write-Host "Downloading..." -ForegroundColor Yellow
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $url -OutFile $exe -UseBasicParsing
    Write-Host "Downloaded!" -ForegroundColor Green
}

# Pre-create settings file to skip language dialog
if (-not (Test-Path $settingsFile)) {
    Write-Host "Creating settings..." -ForegroundColor Gray
    $settings = @"
<?xml version="1.0" encoding="utf-8"?>
<Settings>
  <Language>English</Language>
  <LanguageId>1033</LanguageId>
  <ShowWelcome>false</ShowWelcome>
  <FirstRun>false</FirstRun>
  <LicenseAccepted>true</LicenseAccepted>
</Settings>
"@
    $settings | Out-File -FilePath $settingsFile -Encoding UTF8
}

Write-Host "Launching..." -ForegroundColor Cyan

# Run with portable flag from the temp directory
Start-Process $exe -ArgumentList "/portable" -WorkingDirectory $TempDir

Write-Host "Done!" -ForegroundColor Green