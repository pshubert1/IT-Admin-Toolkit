# NAME: AD Replication Health Check
# DESCRIPTION: Checks for AD replication issues
# STYLE: Dark.TButton

# 
    AD Replication Health Check
    - Run on any DC with RSAT/AD module
    - Auto-detects domain and DCs
#>

Import-Module ActiveDirectory

Write-Host "=== AD Replication Health Check ===" -ForegroundColor Cyan
$domain = (Get-ADDomain).DNSRoot
Write-Host "Domain: $domain" -ForegroundColor Cyan
Write-Host ""

# 1. Summary of failures per DC
Write-Host "== Replication Failures ==" -ForegroundColor Yellow

$failures = Get-ADDomainController -Filter * | ForEach-Object {
    Get-ADReplicationFailure -Target $_.Hostname -Scope Server -ErrorAction SilentlyContinue
}

if (-not $failures) {
    Write-Host "No replication failures reported on any DC." -ForegroundColor Green
} else {
    $failures |
        Select-Object Server, Partner, FailureCount, FirstFailureTime, LastError |
        Sort-Object Server |
        Format-Table -Auto
}

Write-Host ""
# 2. Last replication success per partner
Write-Host "== Last Replication Success By Partner ==" -ForegroundColor Yellow

$partnerMeta = Get-ADDomainController -Filter * | ForEach-Object {
    Get-ADReplicationPartnerMetadata -Target $_.Hostname -Partition * -ErrorAction SilentlyContinue
}

$staleThresholdHours = 4  # adjust as desired

$partnerMeta |
    Select-Object Server,
                  Partner,
                  LastReplicationSuccess,
                  LastResult,
                  @{Name='HoursSinceLastSuccess'; Expression = {
                        if ($_.LastReplicationSuccess) {
                            [math]::Round((New-TimeSpan -Start $_.LastReplicationSuccess -End (Get-Date)).TotalHours,2)
                        } else { $null }
                  }} |
    Sort-Object HoursSinceLastSuccess -Descending |
    Format-Table -Auto

Write-Host ""
Write-Host "== Stale Replication (>${staleThresholdHours}h since success) ==" -ForegroundColor Yellow

$stale = $partnerMeta | Where-Object {
    $_.LastReplicationSuccess -and
    ((New-TimeSpan -Start $_.LastReplicationSuccess -End (Get-Date)).TotalHours -gt $staleThresholdHours)
}

if (-not $stale) {
    Write-Host "No partners older than $staleThresholdHours hours since last successful replication." -ForegroundColor Green
} else {
    $stale |
        Select-Object Server, Partner, LastReplicationSuccess, LastResult |
        Sort-Object LastReplicationSuccess |
        Format-Table -Auto
}

Write-Host ""
Write-Host "== repadmin summary (optional) ==" -ForegroundColor Yellow
# Requires repadmin (on DCs by default)
repadmin /replsummary