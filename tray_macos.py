"""
macOS menu bar UI using rumps instead of pystray.

pystray's macOS backend converts its icon to an NSImage via a PNG-byte
round trip (PIL -> bytes -> NSData -> NSImage.initWithData_), which hits
a real Apple Silicon alignment bug (SIGBUS / EXC_ARM_DA_ALIGN) inside
macOS's own PNGReadPlugin on this machine.

That same crash also fires from plain COLOR EMOJI title text (e.g. the
red-circle emoji): color emoji glyphs are internally backed by embedded
PNG bitmaps, decoded through the identical buggy ImageIO path -- this is
a machine-level PNG-decoder bug, not something specific to pystray. So
the title here deliberately uses plain monochrome Unicode symbols
(no emoji presentation, no color glyph, no PNG decoding at all) rather
than an emoji, to avoid the crash entirely.
"""

import threading

import rumps

import config
import tray_common
from capture_agent import CaptureAgent

_RECORDING_TITLE = "●"  # BLACK CIRCLE (plain glyph, not emoji)
_PAUSED_TITLE = "○"  # WHITE CIRCLE (plain glyph, not emoji)


class TrayApp(rumps.App):
    def __init__(self, agent):
        super().__init__(name="KeystrokeBiometricsAgent", title=_RECORDING_TITLE, quit_button=None)
        self.agent = agent
        self.menu = [
            rumps.MenuItem("Pause / Resume", callback=self.on_toggle_pause),
            rumps.MenuItem("View last 24h activity", callback=self.on_view_activity),
            rumps.MenuItem("Open data folder", callback=self.on_open_folder),
            rumps.MenuItem("Quit", callback=self.on_quit),
        ]

    def on_toggle_pause(self, _sender):
        paused = self.agent.toggle_pause()
        self.title = _PAUSED_TITLE if paused else _RECORDING_TITLE

    def on_open_folder(self, _sender):
        tray_common.open_path(config.app_data_dir())

    def on_view_activity(self, _sender):
        def run():
            path = tray_common.write_summary_file()
            tray_common.open_path(path)

        threading.Thread(target=run, daemon=True).start()

    def on_quit(self, _sender):
        self.agent.stop()
        rumps.quit_application()


def main():
    agent = CaptureAgent()
    agent.start()
    app = TrayApp(agent)
    app.run()


if __name__ == "__main__":
    main()
