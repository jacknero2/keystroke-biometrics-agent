# Keystroke Biometrics Capture Agent

Background data-collection agent for the behavioral-biometrics research
project (see the parent folder's `results/` for the modeling validation
that motivated building this). Records keystroke/mouse **timing and
category** only, never content. Read [CONSENT.md](CONSENT.md) first —
send it to anyone before they install this on their own machine.

**Setting this up on someone else's machine?** Send them
[FRIEND_SETUP.md](FRIEND_SETUP.md) instead of this file — it's a
step-by-step walkthrough written for them directly, including the exact
troubleshooting steps for the permission/crash quirks we hit while
building this (a stuck macOS permission that needs a reboot to actually
take effect, in particular). This README is the reference/dev-facing
version.

## Requirements

- Python 3.9+ available on PATH (`python3` on macOS, `python` on Windows).
- macOS: no admin rights needed, but macOS will prompt for **Input
  Monitoring** / **Accessibility** permission on first run — this is the
  OS's own permission gate; approve it in System Settings when asked.
- Windows: no admin rights needed for a per-user scheduled task.

## Install

**macOS:**
```bash
cd agent
chmod +x install_macos.sh uninstall_macos.sh
./install_macos.sh
```

**Windows (PowerShell):**
```powershell
cd agent
powershell -ExecutionPolicy Bypass -File install_windows.ps1
```

Each installer will ask you to confirm you've read `CONSENT.md`, then ask
for a short label (e.g. a first name) identifying whoever uses that
device — this is how collected data gets auto-labeled with identity,
with no interruptive "who is this?" prompts during use. At the end, it
also offers to set up weekly GitHub sync right then (see below) —
defaults to yes, so a normal run of the installer sets up both the
capture agent and the sync schedule in one pass.

A status icon appears in the menu bar (macOS) or system tray (Windows)
the whole time the agent runs, showing recording/paused state, with
Pause/Resume, "View last 24h activity", "Open data folder", and Quit.

## Checking what's been collected

```bash
python inspect_data.py --summary          # category counts, last 24h
python inspect_data.py --recent 20        # last 20 raw key events
```

## Uninstall

**macOS:** `./uninstall_macos.sh`
**Windows:** `powershell -ExecutionPolicy Bypass -File uninstall_windows.ps1`

Both offer to delete all locally collected data as part of uninstalling.

## Retrieving data for training

**Manual**: copy each machine's `data.sqlite` (path printed by the
installer / `config.py`) back by hand — AirDrop, USB, or a shared drive
folder all work fine given how small these files stay (categories +
timestamps only, no raw content). Each row already carries `user_label`
and `device_id`, so files from different machines merge without any
relabeling step.

**Automatic weekly sync (optional)**: pushes a safe snapshot of
`data.sqlite` to a private GitHub repo you own, on a weekly schedule, so
you don't have to physically retrieve it from each machine.

```bash
# macOS
./setup_sync_macos.sh

# Windows (PowerShell)
powershell -ExecutionPolicy Bypass -File setup_sync_windows.ps1
```

You'll need a GitHub [fine-grained personal access
token](https://github.com/settings/personal-access-tokens/new) scoped to
**only** the one data repo (Contents: Read and write) — not a broader
token, and not your own login. The token is stored via git's own
credential helper (macOS Keychain / Windows Credential Manager), never in
a plaintext file. Test it immediately without waiting for the schedule:

```bash
python sync_data.py
```

Remove the schedule with `./uninstall_sync_macos.sh` (or the Windows
equivalent) — this only stops future syncs; data already pushed to GitHub
stays there until you delete it yourself.

**How collisions between people's data are avoided**: every device writes
to its own uniquely-named file (`data/<user_label>-<device_id prefix>.sqlite`),
so two machines can never overwrite each other's data even if they sync
at the same moment. Each install also picks a random hour/minute (1–5 AM)
for its weekly sync rather than a fixed time, so simultaneous syncs are
rare in the first place; if two do land at the same instant, `sync_data.py`
detects the resulting git push conflict, rebases, and retries automatically
(tested by literally simulating two concurrent devices pushing at once —
see the design notes below).

From there, the window/feature extraction step (same schema validated in
`../src/evaluate.py`) turns the raw event tables into the fixed-length
per-window feature vectors used for training.

## Design notes / safeguards carried over from the project design

- Key **category**, never key content (`categorize.py`) — see prior
  discussion on why this preserves nearly all the accuracy-relevant
  signal (backspace rate, digraph-adjacent timing) without being able to
  reconstruct typed text.
- Mouse position normalized to screen fraction, not raw pixels, to reduce
  (not eliminate) hardware/resolution fingerprinting, per the earlier
  point about the model potentially learning device identity instead of
  behavior — full mitigation still requires "swap session" data (each
  person also using someone else's physical machine for a bit) captured
  the same way with this agent, which is on you to arrange.
- The capture agent itself (`capture_agent.py`/`tray_app.py`) has no
  network code at all. The **optional** sync job (`sync_data.py`) is a
  separate, explicitly-opted-into script — it only ever talks to the one
  private GitHub repo configured in `sync_config.json`, and only pushes
  the local snapshot, never any other data on the machine.
- Visible status icon at all times; no hidden/disguised process, no
  silent auto-start without the install script's explicit consent step.
