# main.py - DiskWizard entry point
# Always checks for admin before launching.
# Re-launches with elevation via UAC if needed.

import sys
import tkinter.messagebox as messagebox

from utils.admin import is_admin, request_elevation
from utils.logger import get_logger


def main():
    logger = get_logger("diskwizard")
    logger.info("DiskWizard starting. admin=%s", is_admin())

    if not is_admin():
        logger.info("Requesting UAC elevation.")
        request_elevation()  # triggers UAC, exits current process
        sys.exit(0)

    try:
        from ui.app import DiskWizardApp

        app = DiskWizardApp()
        logger.info("UI initialized.")
        app.mainloop()
    except Exception as exc:
        logger.exception("Fatal error during startup.")
        try:
            messagebox.showerror(
                "DiskWizard failed to start",
                "See %APPDATA%\\DiskWizard\\diskwizard.log for details.\n\n"
                f"Error: {exc}",
            )
        except Exception:
            pass


if __name__ == "__main__":
    main()
