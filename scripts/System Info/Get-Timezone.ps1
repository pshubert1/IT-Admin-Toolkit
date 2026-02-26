# Detect REAL timezone based on IP (not Windows config)
# Works behind proxies, no external tools needed

# Force TLS 1.2+ (fixes SSL errors)
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls13

# Get local Windows time zone (what is configured)
$localTz = (Get-TimeZone).Id
$localOffset = [math]::Round((Get-Date).ToUniversalTime().Subtract((Get-Date)).TotalHours, 1)

# IP-based timezone detection with multiple fallbacks
$realTzIana = $null
$realTzWindows = $null

$apis = @(
    "https://worldtimeapi.org/api/ip",
    "https://ipapi.co/json/",
    "http://ip-api.com/json/?fields=timezone"
)

foreach ($api in $apis) {
    try {
        Write-Host "Trying API: $api" -ForegroundColor Cyan
        $resp = Invoke-RestMethod -Uri $api -TimeoutSec 8 -ErrorAction Stop
        if ($api -eq "https://worldtimeapi.org/api/ip") {
            $realTzIana = $resp.timezone
        } elseif ($api -eq "https://ipapi.co/json/") {
            $realTzIana = $resp.timezone
        } else {
            $realTzIana = $resp.timezone
        }
        Write-Host "✓ Success with $api" -ForegroundColor Green
        break
    } catch {
        Write-Host "✗ $api failed" -ForegroundColor Yellow
        continue
    }
}

# IANA to Windows timezone mapping (common US zones)
$ianaToWindows = @{
    "America/New_York"      = "Eastern Standard Time"
    "America/Chicago"       = "Central Standard Time" 
    "America/Denver"        = "Mountain Standard Time"
    "America/Los_Angeles"   = "Pacific Standard Time"
    "America/Phoenix"       = "US Mountain Standard Time"
    "America/Anchorage"     = "Alaskan Standard Time"
    "America/Adak"          = "Hawaiian Standard Time"
    "Pacific/Honolulu"      = "Hawaiian Standard Time"
    "Etc/UTC"               = "UTC"
}

if ($realTzIana -and $ianaToWindows.ContainsKey($realTzIana)) {
    $realTzWindows = $ianaToWindows[$realTzIana]
}

# Results table
[PSCustomObject]@{
    "PublicIP_Timezone_IANA"     = $realTzIana
    "Detected_Windows_TZ"        = $realTzWindows
    "Local_Windows_TZ_Config"    = $localTz
    "Local_TZ_Offset_(hrs)"      = $localOffset
    "Timezone_Match"             = if ($realTzWindows -eq $localTz) { "✓ YES" } else { "✗ NO" }
    "Remediation_Needed"         = if ($realTzWindows -and $realTzWindows -ne $localTz) { "Set-TimeZone '$realTzWindows'" } else { "N/A" }
} | Format-Table -AutoSize

# Auto-fix option (uncomment if desired)
<#
if ($realTzWindows -and $realTzWindows -ne $localTz) {
    $confirm = Read-Host "Update timezone to '$realTzWindows'? (Y/N)"
    if ($confirm -eq 'Y') {
        Set-TimeZone -Id $realTzWindows
        Write-Host "Timezone updated!" -ForegroundColor Green
    }
}
#>
