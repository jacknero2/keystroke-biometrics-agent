#!/usr/bin/env bash
set -euo pipefail

PLIST_PATH="$HOME/Library/LaunchAgents/com.keystrokebiometrics.agent.plist"

if [[ -f "$PLIST_PATH" ]]; then
  launchctl unload "$PLIST_PATH" 2>/dev/null || true
  rm -f "$PLIST_PATH"
  echo "Agent stopped and will no longer start at login."
else
  echo "No installed agent found (nothing to unload)."
fi

read -p "Also delete all locally collected data? [y/N] " purge
if [[ "$purge" == "y" || "$purge" == "Y" ]]; then
  rm -rf "$HOME/Library/Application Support/KeystrokeBiometrics"
  echo "Local data deleted."
else
  echo "Data kept at: $HOME/Library/Application Support/KeystrokeBiometrics"
fi
