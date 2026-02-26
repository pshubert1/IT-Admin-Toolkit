# NAME: 🖨️ Restart Print Spooler
# DESCRIPTION: Restarts the Windows Print Spooler service
# STYLE: Warning.TButton

Write-Host "Restarting Print Spooler..." -ForegroundColor Yellow

# Stop the service
Stop-Service -Name Spooler -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Clear print queue (optional)
Remove-Item -Path "$env:SystemRoot\System32\spool\PRINTERS\*" -Force -ErrorAction SilentlyContinue

# Start the service
Start-Service -Name Spooler

# Check status
$service = Get-Service -Name Spooler
Write-Host ""
Write-Host "Print Spooler Status: $($service.Status)" -ForegroundColor Green