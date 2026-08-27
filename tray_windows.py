"""
Windows system tray UI using pystray. (macOS uses rumps instead -- see
tray_macos.py -- to avoid a real Apple Silicon PNG/NSImage decoding bug
in pystray's Darwin backend; that bug doesn't exist on Windows.)
"""

import threading

import pystray
from PIL import Image, ImageDraw

import config
import tray_common
from capture_agent import CaptureAgent

_RECORDING_COLOR = (220, 50, 47)
_PAUSED_COLOR = (150, 150, 150)


def _make_icon(color):
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((8, 8, 56, 56), fill=color)
    return img


def main():
    agent = CaptureAgent()
    agent.start()

    def on_toggle_pause(icon, item):
        paused = agent.toggle_pause()
        icon.icon = _make_icon(_PAUSED_COLOR if paused else _RECORDING_COLOR)
        icon.title = "Keystroke Biometrics Agent (paused)" if paused else "Keystroke Biometrics Agent (recording)"

    def on_open_folder(icon, item):
        tray_common.open_path(config.app_data_dir())

    def on_view_activity(icon, item):
        def run():
            path = tray_common.write_summary_file()
            try:
                icon.notify("Activity summary written -- opening it now.", "Keystroke Biometrics Agent")
            except Exception:
                pass
            tray_common.open_path(path)

        threading.Thread(target=run, daemon=True).start()

    def on_quit(icon, item):
        agent.stop()
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem("Pause / Resume", on_toggle_pause),
        pystray.MenuItem("View last 24h activity", on_view_activity),
        pystray.MenuItem("Open data folder", on_open_folder),
        pystray.MenuItem("Quit", on_quit),
    )

    icon = pystray.Icon(
        "keystroke-biometrics",
        icon=_make_icon(_RECORDING_COLOR),
        title="Keystroke Biometrics Agent (recording)",
        menu=menu,
    )
    icon.run()


if __name__ == "__main__":
    main()
