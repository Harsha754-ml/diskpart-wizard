# main.py - DiskWizard entry point
# Always checks for admin before launching.
# Re-launches with elevation via UAC if needed.

import sys

from utils.admin import is_admin, request_elevation
from ui.app import DiskWizardApp


def main():
    if not is_admin():
        request_elevation()  # triggers UAC, exits current process
        sys.exit(0)
    app = DiskWizardApp()
    app.mainloop()


if __name__ == "__main__":
    main()
