# NAME: Password Expiration
# DESCRIPTION: Show password expiration for user in a given OU
# STYLE: Dark.TButton
# INTERACTIVE: true
Import-Module ActiveDirectory
 
$ou = Read-Host "Enter the OU path (e.g., OU=Users,DC=domain,DC=com)"
$now = Get-Date
$users = Get-ADUser -SearchBase $ou -SearchScope Subtree `
   -Filter * `
   -Properties DisplayName,
               SamAccountName,
               Enabled,
               PasswordNeverExpires,
              msDS-UserPasswordExpiryTimeComputed |
   Select-Object DisplayName, SamAccountName, Enabled, PasswordNeverExpires,
       @{ Name = 'PasswordExpiry';
          Expression = {
              if ($_.PasswordNeverExpires) {
                  $null
              }
              else {
                 [DateTime]::FromFileTime($_.'msDS-UserPasswordExpiryTimeComputed')
              }
          }
       }
 

   # Color Legend
Write-Host "`nLegend:" -ForegroundColor Cyan
Write-Host "Red          = Expired" -ForegroundColor Red
Write-Host "DarkYellow   = Expires ≤10 days" -ForegroundColor DarkYellow
Write-Host "DarkRed     = Disabled" -ForegroundColor DarkRed
Write-Host "DarkGray     = Never Expires" -ForegroundColor DarkGray
Write-Host "White        = >10 days left`n" -ForegroundColor White

# Header
Write-Host ("{0,-30} {1,-20} {2,-10} {3,-20} {4,-25}" -f `
  "DisplayName","SamAccountName","Enabled","PwdNeverExpires","PasswordExpiry") -ForegroundColor Cyan
 
 
foreach ($u in $users) {
   $expiry = $u.PasswordExpiry
   $color  = 'White'
   $expText = $expiry
 
if (-not $u.Enabled) {
   # Disabled account – brown/orange
$color  = 'DarkRed'
   if ($u.PasswordNeverExpires) {
       $expText = 'Never Expires (Disabled)'
   }
   elseif ($expiry) {
       $expText = "$expiry (Disabled)"
   }
}
 
   elseif ($u.PasswordNeverExpires) {
       # Enabled + never expires
       $color  = 'DarkGray'
       $expText = 'Never Expires'
   }
   elseif ($expiry) {
       $daysLeft = ($expiry - $now).TotalDays
 
       if ($daysLeft -lt 0) {
           $color = 'Red'          # expired
       }
       elseif ($daysLeft -le 10) {
           $color = 'DarkYellow'   # 10 days or less
       }
       else {
           $color = 'White'        # more than 10 days
       }
   }
 
   Write-Host ("{0,-30} {1,-20} {2,-10} {3,-20} {4,-25}" -f ` $u.DisplayName, $u.SamAccountName, $u.Enabled, $u.PasswordNeverExpires, $expText) -ForegroundColor $color }
