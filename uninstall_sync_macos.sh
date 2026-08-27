#!/usr/bin/env bash
set -euo pipefail

PLIST_PATH="$HOME/Library/LaunchAgents/com.keystrokebiometrics.sync.plist"
APP_DATA_DIR="$HOME/Library/Application Support/KeystrokeBiometrics"

if [[ -f "$PLIST_PATH" ]]; then
  launchctl unload "$PLIST_PATH" 2>/dev/null || true
  rm -f "$PLIST_PATH"
  echo "Weekly sync schedule removed."
else
  echo "No sync schedule found (nothing to remove)."
fi

read -p "Also delete the local sync config and repo clone (the GitHub repo itself is untouched)? [y/N] " purge
if [[ "$purge" == "y" || "$purge" == "Y" ]]; then
  rm -f "$APP_DATA_DIR/sync_config.json"
  rm -rf "$APP_DATA_DIR/sync-repo"
  echo "Local sync files removed. Data already pushed to GitHub is unaffected."
fi
