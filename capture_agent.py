"""
Core capture logic: global keyboard/mouse listeners -> categorize.py ->
db.py. No network code. No raw key characters ever touch the queue or
the database -- only categories (see categorize.py) and, for mouse,
screen-relative coordinates (never which application/window is focused).

Mouse movement is throttled: pynput's on_move fires extremely often
(potentially thousands of times/sec), which would both bloat the local
database over a multi-week collection run and burn CPU for no added
signal beyond a much coarser sampling rate.
"""

import threading
import time

from pynput import keyboard, mouse

import config
import db

_MOVE_THROTTLE_SEC = 0.05  # ~20 samples/sec cap on mouse movement


class CaptureAgent:
    def __init__(self):
        cfg = config.load_config()
        self.user_label = cfg["user_label"]
        self.device_id = cfg["device_id"]
        self.store = db.EventStore(config.db_path())
        self.paused = threading.Event()  # set() == paused

        self._screen_w, self._screen_h = self._get_screen_size()
        self._last_move_ts = 0.0

        self._kb_listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        self._mouse_listener = mouse.Listener(
            on_move=self._on_move, on_click=self._on_click, on_scroll=self._on_scroll
        )

    @staticmethod
    def _get_screen_size():
        try:
            import tkinter as tk

            root = tk.Tk()
            root.withdraw()
            w, h = root.winfo_screenwidth(), root.winfo_screenheight()
            root.destroy()
            return float(w), float(h)
        except Exception:
            return 1920.0, 1080.0

    def _norm(self, x, y):
        return x / self._screen_w, y / self._screen_h

    def start(self):
        self._kb_listener.start()
        self._mouse_listener.start()

    def stop(self):
        self._kb_listener.stop()
        self._mouse_listener.stop()
        self.store.close()

    def toggle_pause(self):
        if self.paused.is_set():
            self.paused.clear()
        else:
            self.paused.set()
        return self.paused.is_set()

    # --- keyboard callbacks ---

    def _on_press(self, key):
        if self.paused.is_set():
            return
        from categorize import categorize_key

        category = categorize_key(key)
        self.store.put_key_event(time.time(), "down", category, self.user_label, self.device_id)

    def _on_release(self, key):
        if self.paused.is_set():
            return
        from categorize import categorize_key

        category = categorize_key(key)
        self.store.put_key_event(time.time(), "up", category, self.user_label, self.device_id)

    # --- mouse callbacks ---

    def _on_move(self, x, y):
        if self.paused.is_set():
            return
        now = time.monotonic()
        if now - self._last_move_ts < _MOVE_THROTTLE_SEC:
            return
        self._last_move_ts = now
        nx, ny = self._norm(x, y)
        self.store.put_mouse_event(
            time.time(), "move", nx, ny, None, None, None, None, self.user_label, self.device_id
        )

    def _on_click(self, x, y, button, pressed):
        if self.paused.is_set():
            return
        nx, ny = self._norm(x, y)
        self.store.put_mouse_event(
            time.time(), "click", nx, ny, str(button), int(pressed), None, None,
            self.user_label, self.device_id,
        )

    def _on_scroll(self, x, y, dx, dy):
        if self.paused.is_set():
            return
        nx, ny = self._norm(x, y)
        self.store.put_mouse_event(
            time.time(), "scroll", nx, ny, None, None, float(dx), float(dy),
            self.user_label, self.device_id,
        )


if __name__ == "__main__":
    agent = CaptureAgent()
    agent.start()
    print(f"Capturing for user_label={agent.user_label!r} device_id={agent.device_id}")
    print(f"Writing to {config.db_path()}")
    print("Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        agent.stop()
