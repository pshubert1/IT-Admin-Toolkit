# NAME: 💾 Disk Space Report
# DESCRIPTION: Shows disk usage for all drives
# STYLE: Info.TButton

# === Script starts below ===
Write-Host "Disk Space Report" -ForegroundColor Cyan
Write-Host "=================" -ForegroundColor Cyan

Get-PSDrive -PSProvider FileSystem | Select-Object Name, 
    @{N='Used(GB)';E={[math]::Round($_.Used/1GB,2)}}, 
    @{N='Free(GB)';E={[math]::Round($_.Free/1GB,2)}}, 
    @{N='Total(GB)';E={[math]::Round(($_.Used+$_.Free)/1GB,2)}} | 
    Format-Table -AutoSize

Write-Host ""
Write-Host "✅ Done!" -ForegroundColor Green