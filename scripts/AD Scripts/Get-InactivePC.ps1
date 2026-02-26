# NAME: Inactive Domain PCs
# DESCRIPTION: Show computer that have not been used in 90 days
# STYLE: Dark.TButton
# Import the Active Directory module
Import-Module ActiveDirectory

# Define the number of days for the inactive period
$inactiveDays = 90

# Get the current date
$currentDate = Get-Date

# Calculate the cutoff date
$cutoffDate = $currentDate.AddDays(-$inactiveDays)

# Search for inactive computers in AD
$inactiveComputers = Get-ADComputer -Filter {
    LastLogonDate -lt $cutoffDate -and
    Enabled -eq $true
} -Properties LastLogonDate

# Select the desired properties for the CSV
$csvData = $inactiveComputers | Select-Object Name, LastLogonDate

# Export the data to a CSV file
$csvData | Export-Csv -Path "devices.csv" -NoTypeInformation