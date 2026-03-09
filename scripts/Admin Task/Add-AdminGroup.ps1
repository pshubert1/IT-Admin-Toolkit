# NAME: 👤 Local Admin Group
# DESCRIPTION: Adds user to local Admin Group
# STYLE: Warning.TButton
# INTERACTIVE: true


$User = Read-Host "Enter username (e.g., Domain\username, AzureAD\username, or Username if local account)"   # AzureAD\user@company.com or AzureAD\name, depending on how it appears locally
Add-LocalGroupMember -Group 'Administrators' -Member $User
#List the members administrators group 
$group = [ADSI]"WinNT://$env:COMPUTERNAME/Administrators,group"

$members = @()
foreach ($m in $group.psbase.Invoke('Members')) {
    $name = $m.GetType().InvokeMember('Name','GetProperty',$null,$m,$null)
    $adsPath = $m.GetType().InvokeMember('ADsPath','GetProperty',$null,$m,$null)

    $members += [pscustomobject]@{
        Name    = $name
        AdsPath = $adsPath
    }
}
$members | Sort-Object Name