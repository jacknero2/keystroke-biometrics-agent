# Keystroke Biometrics Research Agent: Windows uninstall
#   powershell -ExecutionPolicy Bypass -File uninstall_windows.ps1

$TaskName = "KeystrokeBiometricsAgent"
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($existing) {
    Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Agent stopped and will no longer start at login."
} else {
    Write-Host "No installed agent found (nothing to remove)."
}

$purge = Read-Host "Also delete all locally collected data? [y/N]"
if ($purge -match '^[Yy]$') {
    Remove-Item -Recurse -Force "$env:APPDATA\KeystrokeBiometrics" -ErrorAction SilentlyContinue
    Write-Host "Local data deleted."
} else {
    Write-Host "Data kept at: $env:APPDATA\KeystrokeBiometrics"
}
