"""
Local device identity and paths. No network code anywhere in this module --
everything this agent collects stays on the machine it runs on.
"""

import json
import platform
import sys
import uuid
from pathlib import Path


def app_data_dir() -> Path:
    system = platform.system()
    if system == "Darwin":
        base = Path.home() / "Library" / "Application Support" / "KeystrokeBiometrics"
    elif system == "Windows":
        import os
        base = Path(os.environ.get("APPDATA", Path.home())) / "KeystrokeBiometrics"
    else:
        base = Path.home() / ".keystroke-biometrics"
    base.mkdir(parents=True, exist_ok=True)
    return base


def config_path() -> Path:
    return app_data_dir() / "config.json"


def db_path() -> Path:
    return app_data_dir() / "data.sqlite"


def log_dir() -> Path:
    d = app_data_dir() / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_config() -> dict:
    path = config_path()
    if not path.exists():
        raise FileNotFoundError(
            f"No config at {path}. Run: python config.py init --user-label <name>"
        )
    return json.loads(path.read_text())


def init_config(user_label: str) -> dict:
    """Idempotent: keeps the existing device_id if config already exists,
    so re-running install doesn't fragment one device's history across ids."""
    path = config_path()
    if path.exists():
        cfg = json.loads(path.read_text())
        cfg["user_label"] = user_label
    else:
        cfg = {
            "user_label": user_label,
            "device_id": str(uuid.uuid4()),
        }
    path.write_text(json.dumps(cfg, indent=2))
    return cfg


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Manage local agent config")
    sub = parser.add_subparsers(dest="command", required=True)
    init_p = sub.add_parser("init", help="Create or update the local config")
    init_p.add_argument("--user-label", required=True, help="Label for whoever uses this device")
    args = parser.parse_args()

    if args.command == "init":
        cfg = init_config(args.user_label)
        print(f"Config written to {config_path()}")
        print(json.dumps(cfg, indent=2))
        sys.exit(0)
