# NAME: 🌍 Auto-Detect & Set Timezone
# DESCRIPTION: Detects timezone from IP location and sets it automatically
# STYLE: Warning.TButton

Write-Host "=== AUTO TIMEZONE DETECTOR ===" -ForegroundColor Cyan
Write-Host ""

# Force TLS 1.2+
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# Get current timezone
$beforeTz = (Get-TimeZone).Id
Write-Host "Current Timezone: $beforeTz" -ForegroundColor Yellow
Write-Host ""

# IP-based timezone detection with fallbacks
$realTzIana = $null
$apis = @(
    @{Url="https://worldtimeapi.org/api/ip"; Field="timezone"},
    @{Url="https://ipapi.co/json/"; Field="timezone"},
    @{Url="http://ip-api.com/json/?fields=timezone"; Field="timezone"}
)

Write-Host "Detecting timezone from IP..." -ForegroundColor Cyan

foreach ($api in $apis) {
    try {
        Write-Host "  Trying $($api.Url)... " -NoNewline
        $resp = Invoke-RestMethod -Uri $api.Url -TimeoutSec 8 -ErrorAction Stop
        $realTzIana = $resp.($api.Field)
        Write-Host "OK - $realTzIana" -ForegroundColor Green
        break
    } catch {
        Write-Host "FAILED" -ForegroundColor Red
    }
}

if (-not $realTzIana) {
    Write-Host ""
    Write-Host "All APIs failed. Cannot determine location." -ForegroundColor Red
    exit 1
}

# IANA to Windows timezone mapping
$ianaToWindows = @{
    "America/New_York"      = "Eastern Standard Time"
    "America/Detroit"       = "Eastern Standard Time"
    "America/Indiana/Indianapolis" = "US Eastern Standard Time"
    "America/Chicago"       = "Central Standard Time"
    "America/Denver"        = "Mountain Standard Time"
    "America/Los_Angeles"   = "Pacific Standard Time"
    "America/Phoenix"       = "US Mountain Standard Time"
    "America/Anchorage"     = "Alaskan Standard Time"
    "America/Adak"          = "Hawaiian Standard Time"
    "Pacific/Honolulu"      = "Hawaiian Standard Time"
    "America/Puerto_Rico"   = "Atlantic Standard Time"
    "Etc/UTC"               = "UTC"
    "Europe/London"         = "GMT Standard Time"
    "Europe/Paris"          = "W. Europe Standard Time"
    "Europe/Berlin"         = "W. Europe Standard Time"
    "Europe/Amsterdam"      = "W. Europe Standard Time"
    "Europe/Rome"           = "W. Europe Standard Time"
    "Europe/Madrid"         = "Romance Standard Time"
    "Asia/Tokyo"            = "Tokyo Standard Time"
    "Asia/Shanghai"         = "China Standard Time"
    "Asia/Singapore"        = "Singapore Standard Time"
    "Australia/Sydney"      = "AUS Eastern Standard Time"
    "Australia/Melbourne"   = "AUS Eastern Standard Time"
}

$targetTz = $ianaToWindows[$realTzIana]

if (-not $targetTz) {
    Write-Host ""
    Write-Host "IANA timezone '$realTzIana' not in mapping." -ForegroundColor Yellow
    Write-Host "Attempting to find Windows equivalent..." -ForegroundColor Yellow
    
    # Try to find a matching Windows timezone
    $allTz = Get-TimeZone -ListAvailable
    $match = $allTz | Where-Object { $_.Id -like "*$($realTzIana.Split('/')[-1])*" } | Select-Object -First 1
    if ($match) {
        $targetTz = $match.Id
        Write-Host "Found match: $targetTz" -ForegroundColor Green
    } else {
        Write-Host "Could not find Windows timezone for '$realTzIana'" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Detected Location: $realTzIana" -ForegroundColor Cyan
Write-Host "Target Timezone:   $targetTz" -ForegroundColor Cyan
Write-Host ""

# Apply if different
if ($targetTz -ne $beforeTz) {
    Write-Host "UPDATING: $beforeTz -> $targetTz" -ForegroundColor Green
    
    try {
        Set-TimeZone -Id $targetTz -ErrorAction Stop
        
        $afterTz = (Get-TimeZone).Id
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "  TIMEZONE UPDATED SUCCESSFULLY!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "  Was: $beforeTz" -ForegroundColor White
        Write-Host "  Now: $afterTz" -ForegroundColor White
        Write-Host ""
    } catch {
        Write-Host "Failed to set timezone: $_" -ForegroundColor Red
    }
} else {
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  TIMEZONE ALREADY CORRECT!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Current: $beforeTz" -ForegroundColor White
    Write-Host ""
}