# NAME: 🔋 Set Power Settings (No Sleep)
# DESCRIPTION: Never sleep on AC power, display off after 15 min
# STYLE: Warning.TButton

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Power Settings Configuration" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get current power scheme
$currentScheme = powercfg /getactivescheme
Write-Host "Current Power Scheme:" -ForegroundColor Yellow
Write-Host "  $currentScheme" -ForegroundColor Gray
Write-Host ""

# === AC POWER (Plugged In) Settings ===
Write-Host "Configuring AC Power (Plugged In) settings..." -ForegroundColor Yellow

# Display timeout: 15 minutes (900 seconds) on AC
Write-Host "  Setting display timeout to 15 minutes..." -ForegroundColor Gray
powercfg /change monitor-timeout-ac 15

# Sleep timeout: Never (0 = never) on AC
Write-Host "  Setting sleep to NEVER..." -ForegroundColor Gray
powercfg /change standby-timeout-ac 0

# Hibernate timeout: Never on AC
Write-Host "  Setting hibernate to NEVER..." -ForegroundColor Gray
powercfg /change hibernate-timeout-ac 0

Write-Host ""

# === DC POWER (Battery) Settings - Optional ===
Write-Host "Configuring DC Power (Battery) settings..." -ForegroundColor Yellow

# Display timeout: 10 minutes on battery
Write-Host "  Setting display timeout to 10 minutes..." -ForegroundColor Gray
powercfg /change monitor-timeout-dc 10

# Sleep timeout: 30 minutes on battery
Write-Host "  Setting sleep to 30 minutes..." -ForegroundColor Gray
powercfg /change standby-timeout-dc 30

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✅ Power Settings Applied!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "AC Power (Plugged In):" -ForegroundColor Cyan
Write-Host "  • Display off: 15 minutes" -ForegroundColor White
Write-Host "  • Sleep: Never" -ForegroundColor White
Write-Host "  • Hibernate: Never" -ForegroundColor White
Write-Host ""
Write-Host "DC Power (Battery):" -ForegroundColor Cyan
Write-Host "  • Display off: 10 minutes" -ForegroundColor White
Write-Host "  • Sleep: 30 minutes" -ForegroundColor White
Write-Host ""