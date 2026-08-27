# Keystroke Biometrics Research Agent: Windows setup
# Run this from a normal (non-admin) PowerShell prompt in this folder:
#   powershell -ExecutionPolicy Bypass -File install_windows.ps1

$ErrorActionPreference = "Stop"
$AppDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "== Keystroke Biometrics Research Agent: Windows setup =="
Write-Host ""
Write-Host "This installs a background agent that records the TIMING of your"
Write-Host "keystrokes and mouse movements (never which keys/characters, never"
Write-Host "screen/window content) for a behavioral-biometrics research project."
Write-Host "Please read CONSENT.md in this folder before continuing."
Write-Host ""
$ack = Read-Host "Have you read CONSENT.md and agree to proceed? [y/N]"
if ($ack -notmatch '^[Yy]$') {
    Write-Host "Stopping. Read CONSENT.md first: $AppDir\CONSENT.md"
    exit 1
}

$UserLabel = Read-Host "Enter a short label for who uses this device (e.g. your first name)"
if ([string]::IsNullOrWhiteSpace($UserLabel)) {
    Write-Host "A label is required."
    exit 1
}

Write-Host "Setting up Python environment..."
$VenvDir = Join-Path $AppDir ".venv"
python -m venv $VenvDir
& "$VenvDir\Scripts\pip.exe" install -q --upgrade pip
& "$VenvDir\Scripts\pip.exe" install -q -r "$AppDir\requirements.txt"

& "$VenvDir\Scripts\python.exe" "$AppDir\config.py" init --user-label "$UserLabel"

$PythonwPath = Join-Path $VenvDir "Scripts\pythonw.exe"
$TaskName = "KeystrokeBiometricsAgent"

$Action = New-ScheduledTaskAction -Execute $PythonwPath -Argument "`"$AppDir\tray_app.py`""
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings | Out-Null
Start-ScheduledTask -TaskName $TaskName

Write-Host ""
Write-Host "Installed and started. A status icon should appear in your system tray"
Write-Host "(it may be under the small up-arrow 'show hidden icons' overflow area)."
Write-Host ""
Write-Host "Data is stored locally at:"
Write-Host "  $env:APPDATA\KeystrokeBiometrics\data.sqlite"
Write-Host "Inspect what's been recorded any time with:"
Write-Host "  $VenvDir\Scripts\python.exe $AppDir\inspect_data.py --summary"
Write-Host "To uninstall at any time, run:"
Write-Host "  powershell -ExecutionPolicy Bypass -File $AppDir\uninstall_windows.ps1"
Write-Host ""

$SetupSync = Read-Host "Set up weekly automatic sync to GitHub now? [Y/n]"
if ($SetupSync -notmatch '^[Nn]$') {
    Write-Host ""
    & powershell -ExecutionPolicy Bypass -File "$AppDir\setup_sync_windows.ps1"
} else {
    Write-Host "Skipping sync setup. Run setup_sync_windows.ps1 any time later to enable it."
}
