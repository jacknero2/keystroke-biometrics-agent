# Keystroke Biometrics: weekly data sync setup (Windows)
#   powershell -ExecutionPolicy Bypass -File setup_sync_windows.ps1

$ErrorActionPreference = "Stop"
$AppDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = Join-Path $AppDir ".venv"
$AppDataDir = Join-Path $env:APPDATA "KeystrokeBiometrics"
$CloneDir = Join-Path $AppDataDir "sync-repo"
$TaskName = "KeystrokeBiometricsSync"

Write-Host "== Keystroke Biometrics: weekly data sync setup (Windows) =="
Write-Host ""
Write-Host "This schedules a weekly job that safely snapshots the local data.sqlite"
Write-Host "and pushes it to a private GitHub repo you control, so you don't have to"
Write-Host "retrieve it from this machine by hand."
Write-Host ""
Write-Host "You'll need a GitHub personal access token (fine-grained, scoped to ONLY"
Write-Host "the one data repo, Contents: Read and write) -- create one at"
Write-Host "https://github.com/settings/personal-access-tokens/new"
Write-Host ""

if (-not (Test-Path $VenvDir)) {
    Write-Host "Run install_windows.ps1 first (this needs the same Python environment)."
    exit 1
}

$RepoUrl = Read-Host "GitHub repo URL (e.g. https://github.com/OWNER/keystroke-biometrics-data.git)"
$GhUsername = Read-Host "GitHub username to authenticate as"
$GhTokenSecure = Read-Host "GitHub personal access token" -AsSecureString
$GhToken = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($GhTokenSecure))

New-Item -ItemType Directory -Force -Path $AppDataDir | Out-Null

# Git for Windows ships with git-credential-manager, which stores credentials
# in Windows Credential Manager (not a plaintext file).
$helper = git config --global credential.helper
if ([string]::IsNullOrWhiteSpace($helper)) {
    git config --global credential.helper manager
    Write-Host "Set git's global credential helper to manager (was unset)."
} else {
    Write-Host "Note: git's global credential.helper is already '$helper' -- leaving it as-is."
}

$credInput = "protocol=https`nhost=github.com`nusername=$GhUsername`npassword=$GhToken`n"
$credInput | git credential approve
Write-Host "Token stored via git's credential helper (Windows Credential Manager), not a plaintext file."

Write-Host "Cloning data repo..."
if (Test-Path $CloneDir) { Remove-Item -Recurse -Force $CloneDir }
git clone $RepoUrl $CloneDir

$syncConfig = @{ repo_url = $RepoUrl; local_clone_path = $CloneDir } | ConvertTo-Json
Set-Content -Path (Join-Path $AppDataDir "sync_config.json") -Value $syncConfig

# Randomize hour/minute per machine (instead of every install firing at the
# same instant) so concurrent syncs -- and the git push race that comes with
# them -- are rare in the first place. sync_data.py's push_with_retry() is
# the real safety net regardless, but this cuts how often it's even needed.
$SyncHour = Get-Random -Minimum 1 -Maximum 6   # 1am-5am
$SyncMinute = Get-Random -Minimum 0 -Maximum 60
$SyncTime = Get-Date -Hour $SyncHour -Minute $SyncMinute -Second 0

$PythonwPath = Join-Path $VenvDir "Scripts\pythonw.exe"
$Action = New-ScheduledTaskAction -Execute $PythonwPath -Argument "`"$AppDir\sync_data.py`""
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At $SyncTime

Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger | Out-Null

Write-Host ""
Write-Host ("Scheduled: every Sunday at {0:D2}:{1:D2} AM." -f $SyncHour, $SyncMinute)
Write-Host "Test it right now (does not wait for the schedule):"
Write-Host "  $VenvDir\Scripts\python.exe $AppDir\sync_data.py"
Write-Host "To remove this schedule later, run uninstall_sync_windows.ps1"
