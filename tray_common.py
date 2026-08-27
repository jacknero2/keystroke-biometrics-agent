"""Shared helpers used by both platform-specific tray implementations."""

import io
import os
import platform
import subprocess
from contextlib import redirect_stdout

import config


def open_path(path):
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.run(["open", str(path)])
        elif system == "Windows":
            os.startfile(str(path))  # opens folder in Explorer, or file in its default app
        else:
            subprocess.run(["xdg-open", str(path)])
    except Exception as exc:
        print(f"Could not open {path}: {exc}")


def write_summary_file():
    """Writes the last-24h activity summary to a text file and returns its path."""
    import inspect_data as insp

    try:
        buf = io.StringIO()
        with redirect_stdout(buf):
            insp.summary(24)
        text = buf.getvalue()
    except FileNotFoundError as exc:
        text = str(exc)

    summary_path = config.log_dir() / "last_summary.txt"
    summary_path.write_text(text)
    return summary_path
