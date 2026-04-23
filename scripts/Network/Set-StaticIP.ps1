# NAME: 🌐 Set Static IP
# DESCRIPTION: Configures a static IP address on a network adapter
# STYLE: Special.TButton
# INTERACTIVE: true

Write-Host "================================" -ForegroundColor Cyan
Write-Host "  Set Static IP Address" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# List network adapters
Write-Host "Available Network Adapters:" -ForegroundColor Yellow
$adapters = Get-NetAdapter | Where-Object { $_.Status -eq 'Up' }
$adapters | Format-Table -Property Name, InterfaceDescription, Status -AutoSize

Write-Host ""
$AdapterName = Read-Host "Enter adapter name (e.g., Ethernet)"

$adapter = Get-NetAdapter -Name $AdapterName -ErrorAction SilentlyContinue
if (-not $adapter) {
    Write-Host "❌ Adapter not found!" -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "Current IP Configuration for $AdapterName`:" -ForegroundColor Yellow
Get-NetIPAddress -InterfaceAlias $AdapterName -AddressFamily IPv4 | 
    Select-Object IPAddress, PrefixLength | Format-Table -AutoSize

Write-Host ""
$IPAddress = Read-Host "Enter new IP address (e.g., 192.168.1.100)"
$SubnetPrefix = Read-Host "Enter subnet prefix length (e.g., 24 for 255.255.255.0)"
$Gateway = Read-Host "Enter default gateway (e.g., 192.168.1.1)"
$DNS = Read-Host "Enter DNS server (e.g., 8.8.8.8)"

Write-Host ""
$Confirm = Read-Host "Apply these settings? (yes/no)"

if ($Confirm -eq 'yes') {
    Write-Host ""
    Write-Host "Applying configuration..." -ForegroundColor Yellow
    
    # Remove existing IP configuration
    Remove-NetIPAddress -InterfaceAlias $AdapterName -AddressFamily IPv4 -Confirm:$false -ErrorAction SilentlyContinue
    Remove-NetRoute -InterfaceAlias $AdapterName -AddressFamily IPv4 -Confirm:$false -ErrorAction SilentlyContinue
    
    # Set new IP
    New-NetIPAddress -InterfaceAlias $AdapterName -IPAddress $IPAddress -PrefixLength $SubnetPrefix -DefaultGateway $Gateway
    
    # Set DNS
    Set-DnsClientServerAddress -InterfaceAlias $AdapterName -ServerAddresses $DNS
    
    Write-Host ""
    Write-Host "✅ Static IP configured!" -ForegroundColor Green
    Write-Host ""
    
    # Show new configuration
    Get-NetIPAddress -InterfaceAlias $AdapterName -AddressFamily IPv4 | 
        Select-Object IPAddress, PrefixLength | Format-Table -AutoSize
} else {
    Write-Host "Cancelled." -ForegroundColor Yellow
}