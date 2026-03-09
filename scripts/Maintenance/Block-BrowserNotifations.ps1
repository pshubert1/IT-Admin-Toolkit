# NAME: Block Browser Notifations
# DESCRIPTION: Blocks all Browser Notifications
# STYLE: Warning.TButton


# SYSTEM-WIDE: Block ALL browser notifications
# Chrome, Edge, Firefox - Safe for missing browsers

# Chrome
$ChromePath = "HKLM:\SOFTWARE\Policies\Google\Chrome"; if (-not (Test-Path $ChromePath)) { New-Item $ChromePath -Force | Out-Null }; New-ItemProperty -Path $ChromePath -Name "DefaultNotificationsSetting" -Value 2 -PropertyType DWORD -Force

# Edge  
$EdgePath = "HKLM:\SOFTWARE\Policies\Microsoft\Edge"; if (-not (Test-Path $EdgePath)) { New-Item $EdgePath -Force | Out-Null }; New-ItemProperty -Path $EdgePath -Name "DefaultNotificationsSetting" -Value 3 -PropertyType DWORD -Force

# Firefox (ignored if not installed)
$FirefoxPath = "HKLM:\SOFTWARE\Policies\Mozilla\Firefox"; if (-not (Test-Path $FirefoxPath)) { New-Item $FirefoxPath -Force | Out-Null }; New-ItemProperty -Path $FirefoxPath -Name "DefaultNotificationsSetting" -Value 2 -PropertyType DWORD -Force

# Restart browsers
Stop-Process -Name "chrome","msedge","firefox" -Force -ErrorAction SilentlyContinue

Write-Output "Chrome/Edge/Firefox notifications BLOCKED system-wide"