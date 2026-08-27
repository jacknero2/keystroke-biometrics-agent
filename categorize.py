"""
Maps raw input events to coarse categories only. This is the privacy
boundary of the whole agent: literal key characters are inspected in
memory just long enough to classify them (letter/digit vs punctuation)
and are never written to a variable that outlives this function, logged,
or persisted anywhere. Only the category string ever reaches the database.
"""

from pynput import keyboard

_CORRECTION_KEYS = {keyboard.Key.backspace, keyboard.Key.delete}
_MODIFIER_KEYS = {
    keyboard.Key.shift, keyboard.Key.shift_r,
    keyboard.Key.ctrl, keyboard.Key.ctrl_r,
    keyboard.Key.alt, keyboard.Key.alt_r,
    keyboard.Key.cmd, keyboard.Key.cmd_r,
}
_NAV_KEYS = {
    keyboard.Key.up, keyboard.Key.down, keyboard.Key.left, keyboard.Key.right,
    keyboard.Key.home, keyboard.Key.end, keyboard.Key.page_up, keyboard.Key.page_down,
}
_CONTROL_KEYS = {
    keyboard.Key.enter, keyboard.Key.tab, keyboard.Key.esc, keyboard.Key.caps_lock,
}


def categorize_key(key) -> str:
    if key in _CORRECTION_KEYS:
        return "correction"
    if key == keyboard.Key.space:
        return "space"
    if key in _MODIFIER_KEYS:
        return "modifier"
    if key in _NAV_KEYS:
        return "navigation"
    if key in _CONTROL_KEYS:
        return "control"
    if isinstance(key, keyboard.KeyCode):
        char = key.char  # inspected locally only, never stored or returned
        if char is None:
            return "other"
        return "alnum" if char.isalnum() else "punctuation"
    return "other"
