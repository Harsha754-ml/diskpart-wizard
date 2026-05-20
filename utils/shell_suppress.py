import ctypes


def suppress_autoplay_for_drive(letter: str):
    """
    Temporarily suppress Windows Shell disk notifications for a drive.
    Uses SHChangeNotify to tell the shell the drive is gone.
    """
    SHCNE_DRIVEREMOVED = 0x00000080
    SHCNF_PATH = 0x0005
    path = f"{letter.rstrip('\\')}\\"
    ctypes.windll.shell32.SHChangeNotify(
        SHCNE_DRIVEREMOVED,
        SHCNF_PATH,
        path,
        None,
    )


def restore_shell_notification(letter: str):
    """
    Tell Windows Shell to re-scan after diskpart completes.
    Triggers drive re-detection so the app refresh sees the latest state.
    """
    SHCNE_DRIVEADD = 0x00000100
    SHCNF_PATH = 0x0005
    path = f"{letter.rstrip('\\')}\\"
    ctypes.windll.shell32.SHChangeNotify(
        SHCNE_DRIVEADD,
        SHCNF_PATH,
        path,
        None,
    )
