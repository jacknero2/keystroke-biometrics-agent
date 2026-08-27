#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$APP_DIR/.venv"
APP_DATA_DIR="$HOME/Library/Application Support/KeystrokeBiometrics"
CLONE_DIR="$APP_DATA_DIR/sync-repo"
LABEL="com.keystrokebiometrics.sync"
PLIST_PATH="$HOME/Library/LaunchAgents/${LABEL}.plist"

echo "== Keystroke Biometrics: weekly data sync setup (macOS) =="
echo
echo "This schedules a weekly job that safely snapshots the local data.sqlite"
echo "and pushes it to a private GitHub repo you control, so you don't have to"
echo "retrieve it from this machine by hand."
echo
echo "You'll need a GitHub personal access token (fine-grained, scoped to ONLY"
echo "the one data repo, Contents: Read and write) -- create one at"
echo "https://github.com/settings/personal-access-tokens/new"
echo

if [[ ! -d "$APP_DIR/.venv" ]]; then
  echo "Run install_macos.sh first (this needs the same Python environment)."
  exit 1
fi

read -p "GitHub repo URL (e.g. https://github.com/OWNER/keystroke-biometrics-data.git): " REPO_URL
read -p "GitHub username to authenticate as: " GH_USERNAME
read -s -p "GitHub personal access token: " GH_TOKEN
echo
echo

mkdir -p "$APP_DATA_DIR"

EXISTING_HELPER="$(git config --global credential.helper || true)"
if [[ -z "$EXISTING_HELPER" ]]; then
  git config --global credential.helper osxkeychain
  echo "Set git's global credential helper to osxkeychain (was unset)."
elif [[ "$EXISTING_HELPER" != "osxkeychain" ]]; then
  echo "Note: git's global credential.helper is already '$EXISTING_HELPER' -- leaving it as-is."
fi

printf 'protocol=https\nhost=github.com\nusername=%s\npassword=%s\n' "$GH_USERNAME" "$GH_TOKEN" | git credential approve
echo "Token stored via git's credential helper (Keychain), not in a plaintext file."

echo "Cloning data repo..."
rm -rf "$CLONE_DIR"
git clone "$REPO_URL" "$CLONE_DIR"

cat > "$APP_DATA_DIR/sync_config.json" <<EOF
{
  "repo_url": "$REPO_URL",
  "local_clone_path": "$CLONE_DIR"
}
EOF

LOG_DIR="$APP_DATA_DIR/logs"
mkdir -p "$LOG_DIR"

# Randomize hour/minute per machine (instead of every install firing at the
# same instant) so concurrent syncs -- and the git push race that comes with
# them -- are rare in the first place. sync_data.py's push_with_retry() is
# the real safety net regardless, but this cuts how often it's even needed.
SYNC_HOUR=$(( (RANDOM % 5) + 1 ))   # 1am-5am
SYNC_MINUTE=$(( RANDOM % 60 ))

cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>${LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>${VENV_DIR}/bin/python3</string>
        <string>${APP_DIR}/sync_data.py</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key><integer>0</integer>
        <key>Hour</key><integer>${SYNC_HOUR}</integer>
        <key>Minute</key><integer>${SYNC_MINUTE}</integer>
    </dict>
    <key>StandardOutPath</key><string>${LOG_DIR}/sync.out.log</string>
    <key>StandardErrorPath</key><string>${LOG_DIR}/sync.err.log</string>
</dict>
</plist>
EOF

launchctl unload "$PLIST_PATH" 2>/dev/null || true
launchctl load "$PLIST_PATH"

echo
printf "Scheduled: every Sunday at %02d:%02d AM.\n" "$SYNC_HOUR" "$SYNC_MINUTE"
echo "Test it right now (does not wait for the schedule):"
echo "  $VENV_DIR/bin/python3 $APP_DIR/sync_data.py"
echo "To remove this schedule later, run uninstall_sync_macos.sh"
