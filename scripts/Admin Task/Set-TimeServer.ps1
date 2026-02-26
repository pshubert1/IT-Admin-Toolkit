# NAME: 🕐 Set Time Server (NTP)
# DESCRIPTION: Configures Windows to sync time with a specified NTP server
# STYLE: Warning.TButton

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Windows Time Server Configuration" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# === CONFIGURE YOUR TIME SERVER HERE ===
$TimeServer = "time.windows.com"
# Other common options:
#   time.windows.com      (Microsoft - default)
#   time.nist.gov         (US NIST)
#   pool.ntp.org          (NTP Pool)
#   time.google.com       (Google)
#   time.cloudflare.com   (Cloudflare)

Write-Host "Time Server: $TimeServer" -ForegroundColor Yellow
Write-Host ""

# Step 1: Set the time server
Write-Host "Step 1: Setting NTP server..." -ForegroundColor Yellow
w32tm /config /manualpeerlist:$TimeServer /syncfromflags:manual /reliable:yes /update

# Step 2: Restart the Windows Time service
Write-Host "Step 2: Restarting Windows Time service..." -ForegroundColor Yellow
Restart-Service w32time -Force

# Step 3: Force an immediate sync
Write-Host "Step 3: Forcing time sync..." -ForegroundColor Yellow
w32tm /resync /force

# Step 4: Show current configuration
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Current Time Configuration" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

w32tm /query /status

Write-Host ""
Write-Host "✅ Time server configured successfully!" -ForegroundColor Green
Write-Host "   Server: $TimeServer" -ForegroundColor Cyan