"""
py2app build script: packages tray_macos.py into a real .app bundle.

Recent macOS versions have been unreliable about granting Accessibility /
Input Monitoring trust to a bare, unsigned command-line python3.12 binary
(manually toggling it on in System Settings did not actually take effect,
even after a tccutil reset). A proper .app bundle -- with its own stable
bundle identifier -- is what rumps's own docs recommend for exactly this
reason. Build with:

    python setup.py py2app
"""

from setuptools import setup

setup(
    app=["tray_macos.py"],
    setup_requires=["py2app"],
    options={
        "py2app": {
            "packages": ["rumps", "pynput"],
            "includes": [
                "config",
                "db",
                "categorize",
                "capture_agent",
                "tray_common",
                "inspect_data",
            ],
            "plist": {
                "CFBundleName": "KeystrokeBiometricsAgent",
                "CFBundleIdentifier": "com.keystrokebiometrics.agent",
                "CFBundleShortVersionString": "1.0.0",
                "LSUIElement": True,
            },
        }
    },
)
