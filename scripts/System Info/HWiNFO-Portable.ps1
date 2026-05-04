# NAME: HWiNFO Portable
# DESCRIPTION: Downloads HWiNFO portable and runs it
# STYLE: Special.TButton

# --- Configuration ---
$DestFolder  = "C:\temp"
$ZipFile     = "$DestFolder\hwi_846.zip"
$ExtractPath = "$DestFolder\HWiNFO"

# --- Try these URLs in order until one works ---
$DownloadURLs = @(
    "https://www.sac.sk/download/utildiag/hwi_846.zip",   # Slovakia mirror (no Cloudflare)
    "https://www.hwinfo.com/files/hwi_846.zip"            # Official (Cloudflare protected)
)

# --- Create C:\temp if it doesn't exist ---
If (-Not (Test-Path -Path $DestFolder)) {
    New-Item -ItemType Directory -Path $DestFolder -Force | Out-Null
    Write-Host "Created folder: $DestFolder" -ForegroundColor Green
} Else {
    Write-Host "Folder already exists: $DestFolder" -ForegroundColor Yellow
}

# --- Download using curl.exe (built into Windows 10/11) with fallback URLs ---
$Downloaded = $false
foreach ($URL in $DownloadURLs) {
    Write-Host "Trying: $URL" -ForegroundColor Cyan
    curl.exe -L -o $ZipFile $URL --max-time 60
    
    # Verify it's actually a ZIP (PK header) and not an HTML error page
    If ((Test-Path $ZipFile) -and (Get-Item $ZipFile).Length -gt 100000) {
        $Header = [System.IO.File]::ReadAllBytes($ZipFile)[0..1]
        If ($Header[0] -eq 80 -and $Header[1] -eq 75) {  # "PK" = valid ZIP
            Write-Host "Download successful from: $URL" -ForegroundColor Green
            $Downloaded = $true
            Break
        }
    }
    Write-Host "That URL failed or returned an invalid file, trying next..." -ForegroundColor Yellow
    Remove-Item -Path $ZipFile -Force -ErrorAction SilentlyContinue
}

If (-Not $Downloaded) {
    Write-Host "All download sources failed. Please download manually from https://www.hwinfo.com/download/" -ForegroundColor Red
    Exit
}

# --- Extract the ZIP ---
Write-Host "Extracting..." -ForegroundColor Cyan
Expand-Archive -Path $ZipFile -DestinationPath $ExtractPath -Force
Write-Host "Extracted to: $ExtractPath" -ForegroundColor Green

# --- Detect Architecture and map to correct EXE name ---
$Arch = (Get-CimInstance -ClassName Win32_Processor).Architecture

Switch ($Arch) {
    12      { $ArchLabel = "ARM64"; $ExeName = "HWiNFO_ARM64.exe" }
    9       { $ArchLabel = "x64";   $ExeName = "HWiNFO64.exe"     }
    0       { $ArchLabel = "x86";   $ExeName = "HWiNFO32.exe"     }
    Default { $ArchLabel = "x64";   $ExeName = "HWiNFO64.exe"     }
}

Write-Host "Detected architecture: $ArchLabel" -ForegroundColor Cyan

# --- Build full path and verify it exists ---
$ExeFile = Join-Path -Path $ExtractPath -ChildPath $ExeName

If (Test-Path -Path $ExeFile) {
    Write-Host "Launching: $ExeFile" -ForegroundColor Green
    Start-Process -FilePath $ExeFile
} Else {
    Write-Host "Could not find expected EXE: $ExeName" -ForegroundColor Red
    Write-Host "Available EXEs in $ExtractPath :" -ForegroundColor Yellow
    Get-ChildItem -Path $ExtractPath -Filter "*.exe" -Recurse | ForEach-Object {
        Write-Host "  $($_.Name)" -ForegroundColor White
    }
}