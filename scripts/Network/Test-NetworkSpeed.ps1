# NAME: 🌐 Network Speed Test
# DESCRIPTION: Tests download speed from Microsoft
# STYLE: Dark.TButton

Write-Host "Network Speed Test" -ForegroundColor Cyan
Write-Host "==================" -ForegroundColor Cyan
Write-Host ""

$url = "http://speed.hetzner.de/1MB.bin"
$output = "$env:TEMP\speedtest.tmp"

Write-Host "Downloading test file..." -ForegroundColor Yellow
$start = Get-Date
Invoke-WebRequest -Uri $url -OutFile $output -UseBasicParsing
$end = Get-Date

$duration = ($end - $start).TotalSeconds
$filesize = (Get-Item $output).Length / 1MB
$speed = $filesize / $duration

Write-Host ""
Write-Host "Results:" -ForegroundColor Green
Write-Host "  File Size: $([math]::Round($filesize, 2)) MB"
Write-Host "  Duration:  $([math]::Round($duration, 2)) seconds"
Write-Host "  Speed:     $([math]::Round($speed, 2)) MB/s ($([math]::Round($speed * 8, 2)) Mbps)"

Remove-Item $output -ErrorAction SilentlyContinue