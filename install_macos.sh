#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$APP_DIR/.venv"
PLIST_LABEL="com.keystrokebiometrics.agent"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_LABEL}.plist"

echo "== Keystroke Biometrics Research Agent: macOS setup =="
echo
echo "This installs a background agent that records the TIMING of your"
echo "keystrokes and mouse movements (never which keys/characters, never"
echo "screen/window content) for a behavioral-biometrics research project."
echo "Please read CONSENT.md in this folder before continuing."
echo
read -p "Have you read CONSENT.md and agree to proceed? [y/N] " ack
if [[ "$ack" != "y" && "$ack" != "Y" ]]; then
  echo "Stopping. Read CONSENT.md first: $APP_DIR/CONSENT.md"
  exit 1
fi

read -p "Enter a short label for who uses this device (e.g. your first name): " USER_LABEL
if [[ -z "$USER_LABEL" ]]; then
  echo "A label is required."
  exit 1
fi

PYTHON_BIN=""
for candidate in python3.12 python3.13 python3.11 python3.10 python3; do
  if command -v "$candidate" >/dev/null 2>&1; then
    PYTHON_BIN="$candidate"
    break
  fi
done
if [[ -z "$PYTHON_BIN" ]]; then
  echo "No Python 3 interpreter found on PATH."
  exit 1
fi
echo "Using $(command -v "$PYTHON_BIN") ($($PYTHON_BIN --version))"
# Deliberately avoid defaulting to the newest installed Python (e.g. a brand-new
# major version like 3.14): native GUI deps (pyobjc, used for the menu bar icon)
# often lag behind on wheel support for a very new interpreter, which can crash
# the tray app with a native Bus error instead of a clean Python exception.

echo "Setting up Python environment..."
"$PYTHON_BIN" -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install -q --upgrade pip
pip install -q -r "$APP_DIR/requirements.txt"

"$VENV_DIR/bin/python3" "$APP_DIR/config.py" init --user-label "$USER_LABEL"

LOG_DIR="$HOME/Library/Application Support/KeystrokeBiometrics/logs"
mkdir -p "$LOG_DIR"

cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>${PLIST_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>${VENV_DIR}/bin/python3</string>
        <string>${APP_DIR}/tray_app.py</string>
    </array>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key><false/>
    </dict>
    <key>StandardOutPath</key><string>${LOG_DIR}/agent.out.log</string>
    <key>StandardErrorPath</key><string>${LOG_DIR}/agent.err.log</string>
</dict>
</plist>
EOF

launchctl unload "$PLIST_PATH" 2>/dev/null || true
launchctl load "$PLIST_PATH"

echo
echo "Installed and started. A status icon should appear in your menu bar within a few seconds."
echo "macOS will show its own system prompt asking to grant 'Input Monitoring' and/or"
echo "'Accessibility' permission the first time -- this is required and is macOS's own"
echo "permission gate, not something this script controls. Approve it in System Settings."
echo
echo "IMPORTANT: if you approve the permission but still don't see the menu bar icon"
echo "(or a terminal run of tray_app.py still prints 'This process is not trusted!'),"
echo "the fix that works is a full RESTART of your Mac -- not just re-running anything."
echo "This is a known macOS quirk, not something wrong with your setup; see"
echo "FRIEND_SETUP.md's troubleshooting section if you hit it."
echo
echo "Data is stored locally at:"
echo "  $HOME/Library/Application Support/KeystrokeBiometrics/data.sqlite"
echo "Inspect what's been recorded any time with:"
echo "  $VENV_DIR/bin/python3 $APP_DIR/inspect_data.py --summary"
echo "To uninstall at any time, run:"
echo "  $APP_DIR/uninstall_macos.sh"
echo

read -p "Set up weekly automatic sync to GitHub now? [Y/n] " SETUP_SYNC
if [[ "$SETUP_SYNC" != "n" && "$SETUP_SYNC" != "N" ]]; then
  echo
  "$APP_DIR/setup_sync_macos.sh"
else
  echo "Skipping sync setup. Run ./setup_sync_macos.sh any time later to enable it."
fi
