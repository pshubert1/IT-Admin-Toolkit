# NAME: Restart Axcient Services
# DESCRIPTION: Get all services that start with "Replibit"
# STYLE: Warning.TButton

$services = Get-Service | Where-Object { $_.Name -like "Replibit*" }
foreach ($service in $services) {
    try {
        Write-Host "Restarting service: $($service.Name)"
        Restart-Service -Name $service.Name -Force -ErrorAction Stop
        Write-Host "$($service.Name) restarted successfully.`n"
    } catch {
        Write-Host "Failed to restart $($service.Name): $_"
    }
}