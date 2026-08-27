"""
Entry point: dispatches to the platform-specific tray implementation.
Both install scripts (install_macos.sh / install_windows.ps1) point at
this file, so it always exists at a stable path regardless of OS.
"""

import platform


def main():
    system = platform.system()
    if system == "Darwin":
        import tray_macos

        tray_macos.main()
    elif system == "Windows":
        import tray_windows

        tray_windows.main()
    else:
        raise SystemExit(f"Unsupported platform: {system}")


if __name__ == "__main__":
    main()
