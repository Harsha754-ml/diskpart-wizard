# utils/admin.py
# Checks Windows UAC admin status.
# Re-launches the script with ShellExecuteW("runas") if not elevated.
# This is the standard Windows UAC elevation pattern.

import ctypes
import sys


def is_admin() -> bool:
    """Returns True if the process has administrator privileges."""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def request_elevation():
    """
    Re-launch the current script with UAC elevation.
    Uses ShellExecuteW with 'runas' verb - standard Windows UAC pattern.
    The current process should exit after calling this.
    """
    ctypes.windll.shell32.ShellExecuteW(
        None,  # hwnd
        "runas",  # verb - triggers UAC
        sys.executable,  # python.exe or .exe (when compiled)
        " ".join(f'"{a}"' for a in sys.argv),  # args
        None,  # working dir (None = current)
        1,  # SW_SHOWNORMAL
    )
