# NAME: 👤 Create Local User
# DESCRIPTION: Creates a new local user account
# STYLE: Warning.TButton
# INTERACTIVE: true

Write-Host "================================" -ForegroundColor Cyan
Write-Host "  Create Local User" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

$Username = Read-Host "Enter username"
$FullName = Read-Host "Enter full name"
$Password = Read-Host "Enter password" -AsSecureString
$IsAdmin = Read-Host "Make administrator? (yes/no)"

Write-Host ""
Write-Host "Creating user '$Username'..." -ForegroundColor Yellow

try {
    New-LocalUser -Name $Username -Password $Password -FullName $FullName -Description "Created by IT Admin Toolkit" -ErrorAction Stop
    Write-Host "✅ User created" -ForegroundColor Green
    
    if ($IsAdmin -eq 'yes') {
        Add-LocalGroupMember -Group "Administrators" -Member $Username
        Write-Host "✅ Added to Administrators group" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "User '$Username' created successfully!" -ForegroundColor Green
    
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
}