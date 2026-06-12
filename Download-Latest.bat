@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

:: ============================================================
::  Download & Run Latest IT Admin Toolkit Release from GitHub
:: ============================================================

title IT Admin Toolkit - Updater
echo.
echo ================================================
echo    IT Admin Toolkit - Download Latest Release
echo ================================================
echo.

set "REPO=pshubert1/IT-Admin-Toolkit"
set "API_URL=https://api.github.com/repos/%REPO%/releases/latest"
set "DOWNLOAD_DIR=C:\temp\"
set "EXE_NAME=IT-Admin-Toolkit.exe"
set "TEMP_JSON=%TEMP%\github_release.json"
set "TEMP_DOWNLOAD=%TEMP%\toolkit_download.tmp"

:: Create C:\temp if it doesn't exist
if not exist "%DOWNLOAD_DIR%" (
    echo [*] Creating %DOWNLOAD_DIR%...
    mkdir "%DOWNLOAD_DIR%"
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create %DOWNLOAD_DIR%
        echo         Try running as Administrator.
        pause
        exit /b 1
    )
)

:: Check for curl
where curl >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] curl not found. Requires Windows 10 or later.
    pause
    exit /b 1
)

:: Check for PowerShell
where powershell >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] PowerShell not found.
    pause
    exit /b 1
)

echo [*] Checking latest release from GitHub...
echo     Repo: %REPO%
echo.

:: Get latest release info
curl -s -L "%API_URL%" -o "%TEMP_JSON%" 2>nul

if not exist "%TEMP_JSON%" (
    echo [ERROR] Failed to fetch release info from GitHub.
    echo         Check your internet connection.
    pause
    exit /b 1
)

:: Parse the tag name (version)
for /f "usebackq delims=" %%A in (`powershell -NoProfile -Command "(Get-Content '%TEMP_JSON%' | ConvertFrom-Json).tag_name"`) do set "VERSION=%%A"

if "%VERSION%"=="" (
    echo [ERROR] Could not determine latest version.
    echo         The repository may have no releases yet.
    del "%TEMP_JSON%" >nul 2>&1
    pause
    exit /b 1
)

echo [OK] Latest version: %VERSION%
echo.

:: Parse the download URL for the .exe asset
for /f "usebackq delims=" %%A in (`powershell -NoProfile -Command "$json = Get-Content '%TEMP_JSON%' | ConvertFrom-Json; ($json.assets | Where-Object { $_.name -like '*.exe' } | Select-Object -First 1).browser_download_url"`) do set "DOWNLOAD_URL=%%A"

if "%DOWNLOAD_URL%"=="" (
    echo [ERROR] No .exe asset found in the latest release.
    del "%TEMP_JSON%" >nul 2>&1
    pause
    exit /b 1
)

:: Parse the filename
for /f "usebackq delims=" %%A in (`powershell -NoProfile -Command "$json = Get-Content '%TEMP_JSON%' | ConvertFrom-Json; ($json.assets | Where-Object { $_.name -like '*.exe' } | Select-Object -First 1).name"`) do set "ASSET_NAME=%%A"

:: Parse file size
for /f "usebackq delims=" %%A in (`powershell -NoProfile -Command "$json = Get-Content '%TEMP_JSON%' | ConvertFrom-Json; [math]::Round(($json.assets | Where-Object { $_.name -like '*.exe' } | Select-Object -First 1).size / 1MB, 1)"`) do set "FILE_SIZE=%%A"

echo     File: %ASSET_NAME%
echo     Size: %FILE_SIZE% MB
echo     Dest: %DOWNLOAD_DIR%%EXE_NAME%
echo.
echo [*] Downloading...
echo.

:: Delete old temp file if it exists
if exist "%TEMP_DOWNLOAD%" del "%TEMP_DOWNLOAD%" >nul 2>&1

:: Download to temp location first (avoids AV blocking .exe writes)
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%DOWNLOAD_URL%' -OutFile '%TEMP_DOWNLOAD%' -UseBasicParsing"

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Download failed via PowerShell.
    echo         Trying curl as fallback...
    echo.
    curl -L -o "%TEMP_DOWNLOAD%" "%DOWNLOAD_URL%"
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] Download failed.
        echo         Check internet connection or try manually:
        echo         %DOWNLOAD_URL%
        del "%TEMP_JSON%" >nul 2>&1
        pause
        exit /b 1
    )
)

:: Verify the download isn't empty
for %%F in ("%TEMP_DOWNLOAD%") do set "DL_SIZE=%%~zF"
if "%DL_SIZE%"=="0" (
    echo [ERROR] Downloaded file is empty.
    del "%TEMP_DOWNLOAD%" >nul 2>&1
    del "%TEMP_JSON%" >nul 2>&1
    pause
    exit /b 1
)

:: Move to final location
if exist "%DOWNLOAD_DIR%%EXE_NAME%" del "%DOWNLOAD_DIR%%EXE_NAME%" >nul 2>&1
move /y "%TEMP_DOWNLOAD%" "%DOWNLOAD_DIR%%EXE_NAME%" >nul 2>&1

if %errorlevel% neq 0 (
    :: Move failed, try copy
    copy /y "%TEMP_DOWNLOAD%" "%DOWNLOAD_DIR%%EXE_NAME%" >nul 2>&1
    del "%TEMP_DOWNLOAD%" >nul 2>&1
)

if not exist "%DOWNLOAD_DIR%%EXE_NAME%" (
    echo [ERROR] Failed to save file to %DOWNLOAD_DIR%%EXE_NAME%
    del "%TEMP_JSON%" >nul 2>&1
    pause
    exit /b 1
)

echo.
echo [OK] Download complete!
echo      Saved to: %DOWNLOAD_DIR%%EXE_NAME%
echo.

:: Cleanup
del "%TEMP_JSON%" >nul 2>&1

:: Launch the app
echo [*] Launching IT Admin Toolkit %VERSION%...
start "" "%DOWNLOAD_DIR%%EXE_NAME%"

timeout /t 2 >nul
exit /b 0
