# Keystroke Biometrics: remove weekly data sync (Windows)
#   powershell -ExecutionPolicy Bypass -File uninstall_sync_windows.ps1

$TaskName = "KeystrokeBiometricsSync"
$AppDataDir = Join-Path $env:APPDATA "KeystrokeBiometrics"

$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Weekly sync schedule removed."
} else {
    Write-Host "No sync schedule found (nothing to remove)."
}

$purge = Read-Host "Also delete the local sync config and repo clone (the GitHub repo itself is untouched)? [y/N]"
if ($purge -match '^[Yy]$') {
    Remove-Item -Force (Join-Path $AppDataDir "sync_config.json") -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force (Join-Path $AppDataDir "sync-repo") -ErrorAction SilentlyContinue
    Write-Host "Local sync files removed. Data already pushed to GitHub is unaffected."
}
