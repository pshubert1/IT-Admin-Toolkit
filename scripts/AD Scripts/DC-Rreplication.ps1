# NAME: DC Replication 
# DESCRIPTION: Forcing replication for all DCs in the Domain
# STYLE: Dark.TButton

Import-Module ActiveDirectory

$domain = (Get-ADDomain).DNSRoot
Write-Host "Forcing replication for all DCs in $domain ..." -ForegroundColor Cyan

Get-ADDomainController -Filter * | ForEach-Object {
    $dc = $_.HostName
    Write-Host "Syncing $dc ..." -ForegroundColor Yellow
    repadmin /syncall $dc /AeD
}
