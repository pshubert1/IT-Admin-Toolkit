# NAME: Move FMSO roles
# DESCRIPTION: Moves FSMO roles to another server
# STYLE: Dark.TButton
# INTERACTIVE: true


$server = Read-Host "Enter New DC server name (e.g., DC-02)"
$FSMO = @(
'PDCEmulator',
'RIDMaster',
'Infrastructuremaster',
'DomainNamingmaster',
'SchemaMaster'
)
Foreach ($FSMOr in $FSMO){
 write-host "Moved Role" $FSMOr
 Move-ADDirectoryServerOperationMasterRole -Identity $server $FSMOr
}