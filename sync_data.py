"""
Periodic sync: safely snapshots the local data.sqlite and pushes it to a
private GitHub repo you control. Runs on a schedule (weekly by default)
via setup_sync_macos.sh / setup_sync_windows.ps1 -- not meant to be run
continuously, just invoked periodically.

Safety notes:
  - Uses sqlite3's own backup API (not a plain file copy) so a snapshot
    taken while the capture agent is actively writing (WAL mode) is
    always structurally consistent, never a half-written/corrupt copy.
  - The GitHub token lives in the macOS Keychain (via git's
    credential-osxkeychain helper), never in a plaintext file in this
    repo or the synced one.
  - Only ever writes to the one dedicated data repo configured in
    sync_config.json -- never touches the code repo.
"""

import json
import random
import shutil
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import config

MAX_PUSH_ATTEMPTS = 5


def sync_config_path() -> Path:
    return config.app_data_dir() / "sync_config.json"


def load_sync_config() -> dict:
    path = sync_config_path()
    if not path.exists():
        raise FileNotFoundError(
            f"No sync config at {path}. Run setup_sync_macos.sh (or setup_sync_windows.ps1) first."
        )
    return json.loads(path.read_text())


def safe_backup(src_db: Path, dest_db: Path):
    """Consistent snapshot of a live (possibly WAL-mode) SQLite db."""
    src_conn = sqlite3.connect(str(src_db))
    dest_conn = sqlite3.connect(str(dest_db))
    with dest_conn:
        src_conn.backup(dest_conn)
    src_conn.close()
    dest_conn.close()


def run(cmd, cwd=None, check=True):
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{result.stdout}\n{result.stderr}")
    return result


def current_branch(repo_path) -> str:
    return run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_path).stdout.strip()


def push_with_retry(repo_path):
    """Every device writes its own uniquely-named file (see file_slug in
    main()), so two devices syncing at once never touch the same content
    -- but they can still race at the git level (both trying to push a
    new commit onto the same branch tip). Retry with a rebase + backoff
    rather than failing outright; the rebase is always conflict-free here
    since concurrent syncs never modify the same file."""
    for attempt in range(1, MAX_PUSH_ATTEMPTS + 1):
        result = run(["git", "push"], cwd=repo_path, check=False)
        if result.returncode == 0:
            return
        if attempt == MAX_PUSH_ATTEMPTS:
            raise RuntimeError(f"git push failed after {MAX_PUSH_ATTEMPTS} attempts:\n{result.stderr}")
        print(f"Push rejected (attempt {attempt}/{MAX_PUSH_ATTEMPTS}), likely a concurrent sync from "
              f"another device -- rebasing and retrying...")
        time.sleep(random.uniform(2, 10) * attempt)
        run(["git", "fetch", "origin"], cwd=repo_path)
        run(["git", "rebase", f"origin/{current_branch(repo_path)}"], cwd=repo_path)


def main():
    sync_cfg = load_sync_config()
    cfg = config.load_config()
    repo_path = Path(sync_cfg["local_clone_path"])
    file_slug = f"{cfg['user_label']}-{cfg['device_id'][:8]}"

    if not repo_path.exists():
        run(["git", "clone", sync_cfg["repo_url"], str(repo_path)])
    else:
        # A brand-new remote repo (no commits pushed yet by anyone) has no
        # branch to pull -- that's expected on the very first sync, not an
        # error condition.
        has_commits = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"], cwd=repo_path, capture_output=True
        ).returncode == 0
        if has_commits:
            run(["git", "pull", "--rebase"], cwd=repo_path)

    data_dir = repo_path / "data"
    data_dir.mkdir(exist_ok=True)
    dest_db = data_dir / f"{file_slug}.sqlite"

    tmp_db = dest_db.with_suffix(".sqlite.tmp")
    safe_backup(config.db_path(), tmp_db)
    shutil.move(str(tmp_db), str(dest_db))

    run(["git", "add", f"data/{file_slug}.sqlite"], cwd=repo_path)

    status = run(["git", "status", "--porcelain"], cwd=repo_path).stdout
    if not status.strip():
        print("No changes since last sync -- nothing to push.")
        return

    when = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    run(["git", "commit", "-m", f"Sync {file_slug} ({when})"], cwd=repo_path)
    push_with_retry(repo_path)
    print(f"Synced {dest_db.name} to {sync_cfg['repo_url']} at {when}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Sync failed: {exc}", file=sys.stderr)
        sys.exit(1)
