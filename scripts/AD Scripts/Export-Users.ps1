# NAME: User Export to CSV
# DESCRIPTION: Export a list of users for given OU to CSV
# STYLE: Dark.TButton

$OU = Read-Host "Enter the OU path (e.g., OU=Users,DC=domain,DC=com)"
$ExportPath = "C:\ExportedUsers.csv"
$Users = Get-ADUser -SearchBase $OU -Filter {Enabled -eq $true -and ObjectClass -eq "user"} -Property * |
    Select-Object Name, SamAccountName, UserPrincipalName, GivenName, Surname, Mail, Enabled
$Users | Export-Csv -Path $ExportPath -NoTypeInformation
Write-Output "Export completed. File saved at: $ExportPath"
