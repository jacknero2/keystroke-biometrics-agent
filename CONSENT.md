# What this agent does — read this before installing

This is a research data-collection tool for a personal machine-learning
project: training a model to recognize *who* is using a laptop from the
*rhythm* of their typing and mouse movement, not from *what* they type.

## What it records

- **Keyboard**: for every key press/release, the timestamp and a coarse
  *category* only — `alnum` (letter/digit), `correction` (backspace/delete),
  `space`, `modifier` (shift/ctrl/alt/cmd), `navigation` (arrow keys),
  `control` (enter/tab/esc), or `punctuation`. **It never records which
  specific key or character was pressed.** It cannot reconstruct what you
  typed, and it cannot capture passwords, messages, or any text content.
- **Mouse**: timestamp, event type (move/click/scroll), and position as a
  fraction of your screen size (e.g. "68% across, 40% down") — not tied to
  window content or which application was focused.

## What it does NOT do

- It does not log which keys/characters you pressed.
- It does not take screenshots or read window/application content.
- It does not hide itself: a status icon (menu bar on macOS, system tray
  on Windows) is visible the entire time it's running, showing whether
  it's actively recording or paused, with one-click Pause and Quit.

## Network activity (only if weekly sync is set up)

By default, everything stays in a local file on this computer
(`data.sqlite` in the app's data folder) until someone with physical
access manually copies it off. **If the person running this project has
additionally set up `setup_sync_macos.sh` / `setup_sync_windows.ps1` on
this machine**, a scheduled job also runs about once a week that:

- Takes a safe snapshot of `data.sqlite` (same category/timing-only data
  described above — nothing new is collected for this).
- Pushes that snapshot to **one specific private GitHub repository** the
  project owner controls. Nothing else on this computer is touched or
  transmitted, and no other destination is ever contacted.

Run this to check whether that schedule is active on this machine:

    # macOS
    launchctl list | grep keystrokebiometrics
    # Windows (PowerShell)
    Get-ScheduledTask | Where-Object TaskName -like "KeystrokeBiometrics*"

If you see `com.keystrokebiometrics.sync` (macOS) or
`KeystrokeBiometricsSync` (Windows) in that list, weekly sync is enabled
on this machine.

## How to check what's been collected

Run this any time (paths shown by the installer):

    python inspect_data.py --recent 20
    python inspect_data.py --summary

This prints exactly what's in the database in plain, human-readable form.

## How to stop it

- Menu bar / tray icon → **Pause** stops recording immediately without
  uninstalling.
- Run `uninstall_macos.sh` (or `uninstall_windows.ps1`) to remove the
  background service entirely, with the option to also delete all
  collected data.

## Your data

The collected data leaves this machine either manually (copied off by
the person running this project) or, if weekly sync is enabled per
above, automatically to their one private GitHub repo. You can ask to
see, export, or delete your data at any point, ask whether sync is
enabled on your machine, and uninstall at any time (including the sync
schedule specifically, via `uninstall_sync_macos.sh` /
`uninstall_sync_windows.ps1`) with no obligation to keep participating.

**By running the installer, you're confirming you've read this and agree
to participate on these terms.**
