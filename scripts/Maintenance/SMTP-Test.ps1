# NAME: 📧 SMTP Test send
# DESCRIPTION: This test sending SMTP emails
# STYLE: Warning.TButton
# INTERACTIVE: true


$msolcred = Get-Credential -Message "Enter your SMTP credentials (e.g., Office 365 username/password)"
$SentFrom = Read-Host "Enter sender email (From)"
$SendTo = Read-Host "Enter recipient email (To)"
$SMTPserver_Input = Read-Host "Enter SMTP server (default smtp.office365.com)"
$SMTPserver = if ([string]::IsNullOrWhiteSpace($SMTPserver_Input)) { "smtp.office365.com" } else { $SMTPserver_Input }
$SMTP_PortInput = Read-Host "Enter SMTP port (default 587)"
$SMTP_Port = if ([string]::IsNullOrWhiteSpace($SMTP_PortInput)) { 587 } else { [int]$SMTP_PortInput }

# Create dynamic subject with current date (format: yyyy-MM-dd)
$Subject = "Test_$(Get-Date -Format 'yyyy-MM-dd')"

# Send the test email
Send-MailMessage -From $SentFrom -To $SendTo -Subject $Subject -Body $Subject -SmtpServer $SMTPserver -Credential $msolcred -UseSsl -Port $SMTP_Port

Write-Output "Test email '$Subject' sent successfully!"
