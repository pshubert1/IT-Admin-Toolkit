# NAME: Domain Controller Cleanup Script
# DESCRIPTION: Fully Removes old DC from domain
# STYLE: Dark.TButton
# INTERACTIVE: true


# EDIT THESE FOR EACH SERVER
$ServerName     = Read-Host "Enter old server-name"
$ZoneName       = Read-Host "Enter Domain (e.g., domain.local)"
$DomainDN       = Read-Host "Enter the DN (e.g., DC=domain,DC=com)"
$TargetDC       = Read-Host "Enter New DC server name (e.g., DC-02)"

Write-Host "=== DC CLEANUP v2 for $ServerName ===" -ForegroundColor Yellow

Import-Module ActiveDirectory
Import-Module DnsServer

## 1. FORCE REPLICATION SYNC FIRST
Write-Host "`n1. Syncing replication..." -ForegroundColor Green
repadmin /syncall $TargetDC /AdeP
Start-Sleep 5

## 2. REMOVE COMPUTER OBJECT (RECURSIVE)
Write-Host "`n2. Removing AD Computer..." -ForegroundColor Green
$computer = Get-ADComputer $ServerName -Server $TargetDC -ErrorAction SilentlyContinue
if ($computer) {
    Remove-ADObject $computer.DistinguishedName -Recursive -Confirm:$false -Server $TargetDC
    Write-Host "  ✓ Computer removed" -ForegroundColor Green
}

## 3. REMOVE ALL SITES & SERVICES OBJECTS (CRITICAL FOR REPLICATION)
Write-Host "`n3. Cleaning Sites & Services..." -ForegroundColor Green

# Server container
$serverPath = "CN=$ServerName,CN=Servers,CN=Default-First-Site-Name,CN=Sites,CN=Configuration,$DomainDN"
Get-ADObject $serverPath -Server $TargetDC -ErrorAction SilentlyContinue | 
    Remove-ADObject -Recursive -Confirm:$false -Server $TargetDC

# NTDS Settings (replication endpoint)
$ntdsPath = "CN=NTDS Settings,CN=$ServerName,CN=Servers,CN=Default-First-Site-Name,CN=Sites,CN=Configuration,$DomainDN"
Get-ADObject $ntdsPath -Server $TargetDC -ErrorAction SilentlyContinue | 
    Remove-ADObject -Recursive -Confirm:$false -Server $TargetDC

Write-Host "  ✓ Sites & Services cleaned" -ForegroundColor Green

## 4. REMOVE CONNECTION OBJECTS (REPLICATION PARTNERS)
Write-Host "`n4. Removing connection objects..." -ForegroundColor Green
$connections = Get-ADObject -Filter "objectClass -eq 'ntdsConnection'" -Server $TargetDC -SearchBase "CN=Sites,CN=Configuration,$DomainDN" |
    Where-Object { $_.Name -like "*$ServerName*" }
$connections | Remove-ADObject -Confirm:$false -Server $TargetDC
Write-Host "  ✓ $($connections.Count) connections removed" -ForegroundColor Green

## 5. DNS CLEANUP
Write-Host "`n5. DNS Cleanup..." -ForegroundColor Green
Get-DnsServerResourceRecord -ZoneName $ZoneName -ErrorAction SilentlyContinue |
    Where-Object { $_.HostName -eq $ServerName -or $_.RecordData.ToString() -like "*$ServerName*" } |
    Remove-DnsServerResourceRecord -ZoneName $ZoneName -Force -Confirm:$false

## 6. FINAL VERIFICATION
Write-Host "`n6. CHECK RESULTS:" -ForegroundColor Cyan
repadmin /replsummary
Write-Host "`nSites & Services should now be clean!" -ForegroundColor Green

Write-Host "`n✅ CLEANUP COMPLETE. Run 'repadmin /replsummary' to confirm no $ServerName errors." -ForegroundColor Green