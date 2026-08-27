# Setup guide

This installs a small background tool that records the *timing* of your
typing and mouse movement (never which keys you press, never screen
content) for a friend's machine-learning research project. **Read
[CONSENT.md](CONSENT.md) first** — it explains exactly what is and isn't
collected, and where it goes. Don't continue past step 2 until you've
read it and are OK with it.

Everything below is macOS. If you're on Windows, the same steps apply but
use `install_windows.ps1` / `setup_sync_windows.ps1` and PowerShell
instead of Terminal — ask the project owner if you get stuck translating
a step.

**Before you start**: three things you'll need from the project owner —
a GitHub repo URL, their GitHub username, and an access token (a string
starting with `github_pat_...`). That token can *only* write to one
specific data repo — it is not their password and can't access anything
else in their account.

## 1. Check you have Python

Open Terminal (Spotlight → type "Terminal" → Enter) and run:

```bash
python3 --version
```

If you see something like `Python 3.11.x` / `3.12.x` / `3.13.x`, you're
set. If it says "command not found," install Python from
[python.org/downloads](https://www.python.org/downloads/) first, then
come back and re-run the check.

## 2. Get the code and read the consent doc

In Terminal, run these one at a time — paste each line as a whole line,
don't let your terminal split it across lines (if a command visibly
wraps or you see a `>` prompt on its own line after pasting, something
got cut off — retype it instead of continuing):

```bash
git clone https://github.com/jacknero2/keystroke-biometrics-agent.git
```
```bash
cd keystroke-biometrics-agent
```
```bash
open CONSENT.md
```

Read `CONSENT.md` fully before continuing to step 3.

## 3. Run the installer

Executable permissions are already set from the repo, but this is
harmless to run again just in case:

```bash
chmod +x install_macos.sh uninstall_macos.sh setup_sync_macos.sh uninstall_sync_macos.sh
```
```bash
./install_macos.sh
```

It will ask you to:
1. Confirm you've read `CONSENT.md` — type `y`.
2. Enter a short label (e.g. your first name) — this is how your data
   gets tagged as yours, no further prompts needed after this.
3. **Set up weekly GitHub sync now?** — type `y`, then when prompted enter
   the **repo URL**, **username**, and **token** the project owner gave
   you (see "Before you start" above).

## 4. Grant the permission macOS asks for

macOS will pop up its own system dialog asking for **Input Monitoring**
and/or **Accessibility** permission — this is required for it to record
typing/mouse *timing*, and it's macOS's own security prompt, not
something this script controls. Click **Open System Settings** and
toggle it on when asked.

**If you miss the popup or need to add it manually:** find the exact
path first —

```bash
cd ~/keystroke-biometrics-agent && source .venv/bin/activate && python -c "import sys, os; print(os.path.realpath(sys.executable))"
```

Then in **System Settings → Privacy & Security → Accessibility** (and
again under **Input Monitoring**), click **+**, press `Cmd+Shift+G`,
paste that exact path, select it, and toggle it on.

## 5. If it still doesn't seem to work: reboot

This is the single most important troubleshooting step, based on hitting
it ourselves: **sometimes macOS shows the permission as granted (toggled
on in Settings) but doesn't actually honor it until you restart your
Mac.** If you've granted the permission and still don't see a small `●`
character in your menu bar, or a terminal test still says "This process
is not trusted," **restart your Mac** and check again afterward — this
resolved it every time for us, even after everything else looked
correctly configured.

## 6. Confirm it's actually working

```bash
cd ~/keystroke-biometrics-agent && source .venv/bin/activate && python inspect_data.py --summary
```

You should see real category counts (`alnum`, `correction`, `modifier`,
etc.) building up as you use your computer normally. If sync was set up,
test it immediately rather than waiting a week:

```bash
python sync_data.py
```

You should see `Synced ... to https://github.com/.../keystroke-biometrics-data.git`.
If it instead prints an authentication error, double check the repo URL/
username/token you entered in step 3 (re-run `./setup_sync_macos.sh` to
redo that part only).

## Troubleshooting reference

| Symptom | What it means | Fix |
|---|---|---|
| No menu bar `●` icon, no error | Permission not yet granted/active | Grant it (step 4), then **reboot** (step 5) |
| Terminal prints "This process is not trusted!" repeatedly | Same as above | Reboot after granting — this is the fix, not re-granting again |
| `Bus error: 10` crash | A very new Python version (3.14+) with incomplete GUI-library support | Shouldn't happen — the installer deliberately picks Python 3.12/3.11/3.13 over anything newer. If it still happens, tell the project owner rather than troubleshooting further |
| A pasted multi-line command errors oddly (e.g. "No such file or directory" on a path that looks right) | Terminal likely split the paste across lines and dropped a character | Retype the command as one line instead of pasting |
| `sync_data.py` says an auth/permission error | Wrong repo URL, username, or token | Re-run `./setup_sync_macos.sh` with the correct values |
| You want to pause without uninstalling | — | Click the `●` in the menu bar → **Pause / Resume** |
| You want to stop entirely | — | Run `./uninstall_macos.sh` (and `./uninstall_sync_macos.sh` if sync was set up) — both offer to delete your local data too |

## Your rights, any time

- Inspect exactly what's been recorded: `python inspect_data.py --recent 20`
- Ask the project owner to see, export, or delete your data
- Pause or fully uninstall with no explanation needed, per `CONSENT.md`
