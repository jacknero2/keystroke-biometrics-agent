"""
Local-only SQLite storage. Buffers events in memory and flushes in
batches on a background thread so the input-hook callbacks (which must
stay fast to avoid lagging real typing/clicking) never block on disk I/O.
"""

import queue
import sqlite3
import threading
import time

_SCHEMA = """
CREATE TABLE IF NOT EXISTS key_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    event_type TEXT NOT NULL,
    category TEXT NOT NULL,
    user_label TEXT NOT NULL,
    device_id TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS mouse_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    event_type TEXT NOT NULL,
    x REAL,
    y REAL,
    button TEXT,
    pressed INTEGER,
    dx REAL,
    dy REAL,
    user_label TEXT NOT NULL,
    device_id TEXT NOT NULL
);
"""

_FLUSH_INTERVAL_SEC = 2.0
_FLUSH_BATCH_SIZE = 200


class EventStore:
    def __init__(self, path):
        self.path = str(path)
        self._queue = queue.Queue()
        self._stop = threading.Event()
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.executescript(_SCHEMA)
        self._conn.commit()
        self._thread = threading.Thread(target=self._writer_loop, daemon=True)
        self._thread.start()

    def put_key_event(self, ts, event_type, category, user_label, device_id):
        self._queue.put(("key", (ts, event_type, category, user_label, device_id)))

    def put_mouse_event(self, ts, event_type, x, y, button, pressed, dx, dy, user_label, device_id):
        self._queue.put(("mouse", (ts, event_type, x, y, button, pressed, dx, dy, user_label, device_id)))

    def _writer_loop(self):
        key_buf, mouse_buf = [], []
        last_flush = time.monotonic()
        while not self._stop.is_set() or not self._queue.empty():
            try:
                kind, row = self._queue.get(timeout=0.5)
                (key_buf if kind == "key" else mouse_buf).append(row)
            except queue.Empty:
                pass

            due = time.monotonic() - last_flush >= _FLUSH_INTERVAL_SEC
            full = len(key_buf) + len(mouse_buf) >= _FLUSH_BATCH_SIZE
            if (due or full) and (key_buf or mouse_buf):
                self._flush(key_buf, mouse_buf)
                key_buf, mouse_buf = [], []
                last_flush = time.monotonic()

        if key_buf or mouse_buf:
            self._flush(key_buf, mouse_buf)

    def _flush(self, key_buf, mouse_buf):
        if key_buf:
            self._conn.executemany(
                "INSERT INTO key_events (ts, event_type, category, user_label, device_id) VALUES (?,?,?,?,?)",
                key_buf,
            )
        if mouse_buf:
            self._conn.executemany(
                "INSERT INTO mouse_events (ts, event_type, x, y, button, pressed, dx, dy, user_label, device_id) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                mouse_buf,
            )
        self._conn.commit()

    def close(self):
        self._stop.set()
        self._thread.join(timeout=5)
        self._conn.close()
