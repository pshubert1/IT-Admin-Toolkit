# NAME: 💻 Rename Computer
# DESCRIPTION: Changes the computer name (requires restart)
# STYLE: Danger.TButton
# INTERACTIVE: true

Write-Host "================================" -ForegroundColor Cyan
Write-Host "  Rename Computer" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Current computer name: $env:COMPUTERNAME" -ForegroundColor Yellow
Write-Host ""

$NewName = Read-Host "Enter new computer name"

if ($NewName -and $NewName -ne $env:COMPUTERNAME) {
    $Confirm = Read-Host "Rename to '$NewName'? (yes/no)"
    
    if ($Confirm -eq 'yes') {
        Write-Host ""
        Write-Host "Renaming computer..." -ForegroundColor Yellow
        Rename-Computer -NewName $NewName -Force
        Write-Host ""
        Write-Host "✅ Computer will be renamed to '$NewName' after restart" -ForegroundColor Green
        
        $Restart = Read-Host "Restart now? (yes/no)"
        if ($Restart -eq 'yes') {
            Restart-Computer -Force
        }
    } else {
        Write-Host "Cancelled." -ForegroundColor Yellow
    }
} else {
    Write-Host "Invalid name or same as current." -ForegroundColor Red
}