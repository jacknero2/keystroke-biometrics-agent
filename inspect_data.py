"""
Transparency tool: lets anyone running this agent (you or your friend)
see exactly what has been recorded, in plain human-readable form. Run
this any time you want to verify nothing beyond timing/category data is
being stored.

    python inspect_data.py --recent 20
    python inspect_data.py --summary
"""

import argparse
import sqlite3
import time
from datetime import datetime

import config


def _connect():
    path = config.db_path()
    if not path.exists():
        raise FileNotFoundError(f"No data recorded yet at {path}")
    return sqlite3.connect(str(path))


def recent(n=20):
    conn = _connect()
    cur = conn.execute(
        "SELECT ts, event_type, category, user_label FROM key_events "
        "ORDER BY ts DESC LIMIT ?",
        (n,),
    )
    rows = cur.fetchall()
    print(f"Most recent {len(rows)} key events (category only -- no key content is ever stored):")
    for ts, event_type, category, user_label in reversed(rows):
        when = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        print(f"  {when}  {user_label:<12} {event_type:<5} {category}")


def summary(hours=24):
    conn = _connect()
    since = time.time() - hours * 3600
    print(f"Summary of the last {hours}h:\n")

    print("Key event categories:")
    for user_label, category, count in conn.execute(
        "SELECT user_label, category, COUNT(*) AS cnt FROM key_events WHERE ts >= ? "
        "GROUP BY user_label, category ORDER BY user_label, cnt DESC",
        (since,),
    ):
        print(f"  {user_label:<12} {category:<12} {count}")

    print("\nMouse event types:")
    for user_label, event_type, count in conn.execute(
        "SELECT user_label, event_type, COUNT(*) AS cnt FROM mouse_events WHERE ts >= ? "
        "GROUP BY user_label, event_type ORDER BY user_label, cnt DESC",
        (since,),
    ):
        print(f"  {user_label:<12} {event_type:<8} {count}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recent", type=int, metavar="N", help="Show the N most recent key events")
    parser.add_argument("--summary", action="store_true", help="Show category counts over --hours")
    parser.add_argument("--hours", type=float, default=24.0, help="Window for --summary (default 24h)")
    args = parser.parse_args()

    if args.recent:
        recent(args.recent)
    elif args.summary:
        summary(args.hours)
    else:
        summary(24)
