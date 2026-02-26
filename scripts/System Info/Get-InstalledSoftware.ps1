# NAME: 📦 List Installed Software
# DESCRIPTION: Lists all installed programs from registry
# STYLE: Dark.TButton

Write-Host "Installed Software" -ForegroundColor Cyan
Write-Host "==================" -ForegroundColor Cyan
Write-Host ""

Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* | 
    Where-Object {$_.DisplayName} | 
    Select-Object DisplayName, DisplayVersion, Publisher | 
    Sort-Object DisplayName | 
    Format-Table -AutoSize

Write-Host ""
Write-Host "✅ Done!" -ForegroundColor Green