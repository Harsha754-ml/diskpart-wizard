# DiskWizard — Master Cursor Prompt
> Production-grade Windows GUI utility for DiskPart operations
> Stack: Python + CustomTkinter | Target: Windows 10/11 | Aesthetic: Surgical Industrial

---

## ROLE

You are a senior Windows systems engineer and Python desktop application architect.
Your job is to build **DiskWizard** — a safe, beginner-friendly, production-grade
Windows GUI utility that wraps DiskPart operations in a modern interface.

This is NOT a prototype. This is a shippable application.
Write code like it will be maintained by someone else. Comment every non-obvious decision.

---

## AESTHETIC DIRECTION (NON-NEGOTIABLE)

**Design language: Surgical Industrial**

Think: a precision instrument panel. Not a toy. Not a hacker terminal.
Something a professional would trust with their data.

### Color System

```python
# Define in constants.py
COLORS = {
    "bg_primary":     "#0D0D0D",   # near-black canvas
    "bg_secondary":   "#141414",   # card/panel bg
    "bg_tertiary":    "#1C1C1C",   # input/hover bg
    "border":         "#2A2A2A",   # subtle separators
    "accent":         "#00E5FF",   # electric cyan — single accent color
    "accent_dim":     "#007A8A",   # muted accent for secondary states
    "danger":         "#FF3B3B",   # destructive actions only
    "warning":        "#FFB300",   # warnings
    "success":        "#00C853",   # success states
    "text_primary":   "#F0F0F0",   # main text
    "text_secondary": "#8A8A8A",   # labels, metadata
    "text_muted":     "#444444",   # disabled, placeholders
}
```

### Typography

Use **JetBrains Mono** (via Google Fonts or bundled TTF) for ALL text.
- Headers: JetBrains Mono Bold, 13–15px
- Body/labels: JetBrains Mono Regular, 11–12px
- Terminal output: JetBrains Mono Regular, 11px
- Tag/badge text: JetBrains Mono Bold, 9px uppercase with letter-spacing

This is a system tool. Monospace everywhere is correct and intentional.
It reads like a precision instrument, not a consumer app.

### Layout Rules

```
┌─────────────────────────────────────────────────────────────┐
│  [●] DiskWizard          v1.0.0           [ADMIN ✓]        │  <- title bar
├──────────────┬──────────────────────────────────────────────┤
│              │                                              │
│   SIDEBAR    │              MAIN PANEL                     │
│   160px      │              flex-fill                      │
│   fixed      │                                             │
│              │  ┌─────────────────────────────────────┐   │
│  [Disks]     │  │  DRIVE CARDS (horizontal scroll)    │   │
│  [Format]    │  └─────────────────────────────────────┘   │
│  [Partition] │                                             │
│  [Boot]      │  ┌─────────────────────────────────────┐   │
│  [History]   │  │  OPERATION PANEL                    │   │
│  [Settings]  │  └─────────────────────────────────────┘   │
│              │                                             │
│              │  ┌─────────────────────────────────────┐   │
│              │  │  LIVE TERMINAL (200px min-height)   │   │
│              │  └─────────────────────────────────────┘   │
└──────────────┴──────────────────────────────────────────────┘
```

**Drive cards** look like this:

```
┌──────────────────────────────┐
│  DISK 1                [USB] │
│  SanDisk Ultra              │
│  ████████░░  32 GB          │
│  NTFS  •  E:\  •  Removable │
└──────────────────────────────┘
```

- Selected card: `accent` border (2px), `bg_tertiary` background
- System disk (Disk 0): always rendered with `danger` tag, non-clickable
- Unknown/unformatted: `text_muted` italic label

---

## PROJECT STRUCTURE

```
DiskWizard/
├── main.py                  # Entry point — admin check, launch app
├── requirements.txt
├── DiskWizard.spec          # PyInstaller spec
├── assets/
│   └── fonts/
│       └── JetBrainsMono-Regular.ttf
│       └── JetBrainsMono-Bold.ttf
├── core/
│   ├── __init__.py
│   ├── diskpart.py          # DiskPart script builder + executor
│   ├── disk_info.py         # Drive detection via wmic/psutil/WMI
│   ├── safety.py            # Validation, guards, confirmation logic
│   └── history.py           # Operation log — JSON append-only
├── ui/
│   ├── __init__.py
│   ├── app.py               # Root CTk window, layout orchestration
│   ├── sidebar.py           # Navigation sidebar component
│   ├── drive_card.py        # Individual disk card widget
│   ├── drive_panel.py       # Drive list + refresh
│   ├── operation_panel.py   # Action buttons + form inputs
│   ├── terminal.py          # Live output log widget
│   ├── dialogs.py           # Confirmation modals, warnings
│   └── theme.py             # CTk theme + COLORS + font loader
└── utils/
    ├── __init__.py
    ├── admin.py             # UAC elevation check
    └── logger.py            # File logger (diskwizard.log)
```

---

## FILE-BY-FILE SPECIFICATION

Build each file completely. No placeholders. No `# TODO`. No `pass`.

---

### `requirements.txt`

```
customtkinter>=5.2.2
psutil>=5.9.8
pywin32>=306
wmi>=1.5.1
Pillow>=10.3.0
pyinstaller>=6.6.0
```

---

### `main.py`

**Purpose:** Entry point. Check admin rights. If not elevated, re-launch with UAC prompt using `ShellExecuteW`. If elevated, launch the CTk app.

```python
# main.py — DiskWizard entry point
# Always checks for admin before launching.
# Re-launches with elevation via UAC if needed.

import sys
import ctypes
from utils.admin import is_admin, request_elevation
from ui.app import DiskWizardApp

def main():
    if not is_admin():
        request_elevation()   # triggers UAC, exits current process
        sys.exit(0)
    app = DiskWizardApp()
    app.mainloop()

if __name__ == "__main__":
    main()
```

---

### `utils/admin.py`

```python
# utils/admin.py
# Checks Windows UAC admin status.
# Re-launches the script with ShellExecuteW("runas") if not elevated.
# This is the standard Windows UAC elevation pattern.

import ctypes, sys, os

def is_admin() -> bool:
    """Returns True if the process has administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def request_elevation():
    """
    Re-launch the current script with UAC elevation.
    Uses ShellExecuteW with 'runas' verb — standard Windows UAC pattern.
    The current process should exit after calling this.
    """
    ctypes.windll.shell32.ShellExecuteW(
        None,                          # hwnd
        "runas",                       # verb — triggers UAC
        sys.executable,                # python.exe or .exe (when compiled)
        " ".join(f'"{a}"' for a in sys.argv),  # args
        None,                          # working dir (None = current)
        1                              # SW_SHOWNORMAL
    )
```

---

### `ui/theme.py`

**Purpose:** Single source of truth for all visual tokens. Import `COLORS`, `FONTS`, `apply_theme()` from here everywhere.

Implement:
- `COLORS` dict (full set from Aesthetic Direction above)
- `FONT` helper that returns `(family, size, weight)` tuples
- `apply_theme()` that sets `customtkinter.set_appearance_mode("dark")` and applies a custom CTk color theme via `customtkinter.set_default_color_theme()`
- Custom CTk theme JSON generated at runtime from `COLORS` to avoid shipping a separate file
- Font loading: use `tkinter.font.Font` with the bundled JetBrains Mono TTF via `pyglet` or `tkinter`'s `font.families()` fallback

```python
# ui/theme.py — Design system tokens and CTk theme setup
# All colors, fonts, and spacing defined here.
# Import from here everywhere. Never hardcode colors elsewhere.

import customtkinter as ctk

COLORS = { ... }  # Full COLORS dict from Aesthetic Direction

def FONT(size: int = 12, weight: str = "normal") -> tuple:
    """Returns font tuple for CTk widgets. Falls back to Courier if JetBrains not loaded."""
    family = "JetBrains Mono" if _jetbrains_loaded else "Courier New"
    return (family, size, weight)

def apply_theme():
    ctk.set_appearance_mode("dark")
    # Set bg colors by patching ctk internals for full control
    ...
```

---

### `core/disk_info.py`

**Purpose:** Returns a list of `DiskInfo` dataclass objects. Use **WMI** as primary source, **psutil** as fallback.

```python
# core/disk_info.py
# Detects all connected disks using Windows WMI.
# Falls back to psutil disk_partitions() if WMI unavailable.
# Returns List[DiskInfo] — one entry per physical disk.

from dataclasses import dataclass
from typing import Optional, List
import subprocess, json

@dataclass
class DiskInfo:
    index: int              # DiskPart disk number (0, 1, 2...)
    size_gb: float          # Total size in GB
    model: str              # Drive model string from WMI
    is_removable: bool      # True for USB drives
    is_system_disk: bool    # True if index == 0 (NEVER touch)
    filesystem: Optional[str]  # "NTFS", "FAT32", "exFAT", None
    drive_letter: Optional[str]  # "E:", "F:", None
    partition_style: Optional[str]  # "MBR", "GPT", "RAW"
    status: str             # "Online", "Offline", "No Media"

def get_all_disks() -> List[DiskInfo]:
    """
    Primary: query WMI Win32_DiskDrive + Win32_LogicalDisk.
    Fallback: parse `wmic diskdrive list brief` subprocess output.
    Always marks index=0 as is_system_disk=True regardless of any other signal.
    """
    ...

def _parse_wmic_output(raw: str) -> List[DiskInfo]:
    """Parse wmic diskdrive list full /format:list output into DiskInfo objects."""
    ...
```

---

### `core/safety.py`

**Purpose:** Every destructive action must pass through a safety gate here. This is the only place where "is this allowed?" decisions are made.

```python
# core/safety.py
# The single source of truth for all safety decisions.
# All destructive operations MUST call validate_operation() first.
# This module never executes anything — it only validates.

from core.disk_info import DiskInfo
from typing import Tuple

class SafetyError(Exception):
    """Raised when an operation is blocked for safety reasons."""
    pass

DESTRUCTIVE_OPS = {"clean", "format", "convert", "create_partition"}

def validate_operation(op: str, disk: DiskInfo) -> Tuple[bool, str]:
    """
    Returns (allowed: bool, reason: str).
    
    Rules (in order, first match wins):
    1. disk.index == 0  → BLOCKED. "Disk 0 is your system drive. This operation is permanently blocked."
    2. disk.is_system_disk → BLOCKED (same message)
    3. op in DESTRUCTIVE_OPS and not disk.is_removable → WARN. Return (True, warning_message)
    4. disk.status != "Online" → BLOCKED. "Disk is not online."
    5. All other cases → (True, "")
    """
    ...

def require_double_confirmation(disk: DiskInfo, op: str) -> bool:
    """
    Returns True if this operation requires the "I understand this will erase all data"
    checkbox confirmation dialog before proceeding.
    Always True for: clean, format, convert.
    False for: assign, create_partition (non-destructive).
    """
    ...
```

---

### `core/diskpart.py`

**Purpose:** Builds DiskPart scripts as strings, writes them to temp files, executes with `diskpart /s`, streams stdout/stderr in real time.

```python
# core/diskpart.py
# Builds and executes DiskPart scripts.
# NEVER runs diskpart directly with inline commands — always via script file.
# This gives us an audit trail and prevents injection.

import subprocess, tempfile, os, threading
from typing import Callable, Optional
from core.safety import validate_operation, SafetyError
from core.disk_info import DiskInfo

class DiskPartEngine:
    """
    Builds DiskPart .txt scripts, validates them, and executes them.
    Streams output line-by-line via a callback for live terminal display.
    """

    def __init__(self, output_callback: Callable[[str, str], None]):
        """
        output_callback(line: str, level: str) — called for each output line.
        level: "info" | "success" | "error" | "warning"
        """
        self.output_callback = output_callback
        self._current_script_path: Optional[str] = None

    def build_script(self, disk_index: int, operations: list[str]) -> str:
        """
        Builds a DiskPart script string.
        Always starts with `select disk N`.
        operations: list of raw DiskPart command strings.

        Example output:
            select disk 2
            clean
            create partition primary
            format fs=ntfs quick
            assign
            exit
        """
        lines = [f"select disk {disk_index}"] + operations + ["exit"]
        return "\n".join(lines)

    def execute(self, script: str, disk: DiskInfo, op_name: str) -> bool:
        """
        1. Validates via safety.validate_operation().
        2. Writes script to a named temp file.
        3. Runs `diskpart /s <tempfile>` via subprocess.
        4. Streams stdout line-by-line to output_callback.
        5. Deletes temp file on completion.
        6. Returns True on success, False on failure.
        """
        ...

    def _stream_output(self, proc: subprocess.Popen):
        """Reads stdout in real time and calls output_callback per line."""
        ...

    # --- Pre-built operation factories ---

    def clean_disk(self, disk: DiskInfo) -> bool:
        script = self.build_script(disk.index, ["clean"])
        return self.execute(script, disk, "clean")

    def quick_format(self, disk: DiskInfo, fs: str = "ntfs", label: str = "") -> bool:
        label_cmd = f'label="{label}"' if label else ""
        script = self.build_script(disk.index, [
            "clean",
            "create partition primary",
            f"format fs={fs} quick {label_cmd}".strip(),
            "assign"
        ])
        return self.execute(script, disk, "format")

    def create_partition(self, disk: DiskInfo) -> bool:
        script = self.build_script(disk.index, [
            "create partition primary",
            "format fs=ntfs quick",
            "assign"
        ])
        return self.execute(script, disk, "create_partition")

    def assign_letter(self, disk: DiskInfo, letter: str) -> bool:
        script = self.build_script(disk.index, [
            "select partition 1",
            f"assign letter={letter}"
        ])
        return self.execute(script, disk, "assign")

    def convert_mbr(self, disk: DiskInfo) -> bool:
        script = self.build_script(disk.index, ["clean", "convert mbr"])
        return self.execute(script, disk, "convert")

    def convert_gpt(self, disk: DiskInfo) -> bool:
        script = self.build_script(disk.index, ["clean", "convert gpt"])
        return self.execute(script, disk, "convert")

    def make_bootable(self, disk: DiskInfo, iso_path: str) -> bool:
        """
        1. Clean + format FAT32 + active partition via DiskPart.
        2. Mount ISO via PowerShell Mount-DiskImage.
        3. xcopy ISO contents to drive letter.
        4. Unmount ISO.
        Full implementation — no placeholders.
        """
        ...
```

---

### `core/history.py`

```python
# core/history.py
# Append-only JSON log of all operations attempted (success or failure).
# Stored at %APPDATA%\DiskWizard\history.json
# Max 500 entries — oldest pruned on overflow.

import json, os
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List

HISTORY_FILE = os.path.join(os.getenv("APPDATA", "."), "DiskWizard", "history.json")

@dataclass
class HistoryEntry:
    timestamp: str
    operation: str
    disk_index: int
    disk_model: str
    status: str          # "success" | "failed" | "cancelled"
    script: str          # The exact DiskPart script that was run
    error_msg: str = ""

def append(entry: HistoryEntry): ...
def load_all() -> List[HistoryEntry]: ...
def export_to_txt(path: str): ...
```

---

### `ui/app.py`

**Purpose:** Root `CTk` window. Sets up 2-column layout (sidebar + main). Manages page switching. Passes shared state (selected disk, diskpart engine, disk list) down to child components.

```python
# ui/app.py
# Root application window. 
# Manages layout, navigation state, and shared application state.
# Child components communicate via callbacks passed at construction time.

import customtkinter as ctk
from ui.theme import apply_theme, COLORS, FONT
from ui.sidebar import Sidebar
from ui.drive_panel import DrivePanel
from ui.operation_panel import OperationPanel
from ui.terminal import TerminalPanel
from core.diskpart import DiskPartEngine
from core.disk_info import DiskInfo
from typing import Optional

class DiskWizardApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        apply_theme()
        self.title("DiskWizard")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.configure(fg_color=COLORS["bg_primary"])

        self.selected_disk: Optional[DiskInfo] = None
        self.current_page = "disks"

        # Terminal widget created first — engine needs its callback
        self.terminal = TerminalPanel(self)
        self.engine = DiskPartEngine(output_callback=self.terminal.log)

        self._build_layout()

    def _build_layout(self):
        # Left sidebar — fixed 160px
        self.sidebar = Sidebar(self, on_navigate=self._navigate)
        self.sidebar.pack(side="left", fill="y")

        # Right main area
        self.main_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_primary"])
        self.main_frame.pack(side="left", fill="both", expand=True, padx=16, pady=16)

        # Drive cards row
        self.drive_panel = DrivePanel(
            self.main_frame,
            on_disk_selected=self._on_disk_selected
        )
        self.drive_panel.pack(fill="x", pady=(0, 12))

        # Operation buttons
        self.op_panel = OperationPanel(
            self.main_frame,
            engine=self.engine,
            get_selected_disk=lambda: self.selected_disk
        )
        self.op_panel.pack(fill="x", pady=(0, 12))

        # Terminal output
        self.terminal.pack(fill="both", expand=True)

    def _on_disk_selected(self, disk: DiskInfo):
        self.selected_disk = disk
        self.op_panel.refresh_for_disk(disk)

    def _navigate(self, page: str):
        self.current_page = page
        # Show/hide panels based on page
        ...
```

---

### `ui/drive_card.py`

**Purpose:** Single disk card widget. Renders disk metadata. Highlights on selection. Blocks click on system disk.

```python
# ui/drive_card.py
# A single disk card — shows disk number, model, size, filesystem, drive letter.
# System disk (index 0) rendered with danger styling and blocked from selection.
# Selected disk gets accent border.

import customtkinter as ctk
from core.disk_info import DiskInfo
from ui.theme import COLORS, FONT
from typing import Callable

class DriveCard(ctk.CTkFrame):
    def __init__(self, parent, disk: DiskInfo, on_select: Callable[[DiskInfo], None]):
        bg = COLORS["bg_secondary"]
        super().__init__(parent, fg_color=bg, corner_radius=8, border_width=1,
                         border_color=COLORS["border"])

        self.disk = disk
        self.on_select = on_select
        self.selected = False

        self._build()
        if not disk.is_system_disk:
            self.bind("<Button-1>", self._handle_click)
            for child in self.winfo_children():
                child.bind("<Button-1>", self._handle_click)

    def _build(self):
        # Disk number + type badge row
        # Model name
        # Size bar (CTkProgressBar)
        # Filesystem + drive letter + removable tag
        ...

    def set_selected(self, selected: bool):
        self.selected = selected
        border = COLORS["accent"] if selected else COLORS["border"]
        self.configure(border_color=border, border_width=2 if selected else 1)

    def _handle_click(self, _event):
        if not self.disk.is_system_disk:
            self.on_select(self.disk)
```

---

### `ui/operation_panel.py`

**Purpose:** Buttons for each operation. Disabled when no disk selected. Danger buttons (Clean, Format, Convert) styled with `danger` color. Always calls `safety.validate_operation()` before doing anything. Shows confirmation dialog via `dialogs.py`.

Operations to implement as buttons (with tooltips):
- **Clean Disk** — "Wipes ALL data. Partition table is destroyed. Unrecoverable."
- **Quick Format** — "Formats with chosen filesystem. Select NTFS, FAT32, or exFAT."
- **Create Partition** — "Creates a single primary partition and formats NTFS."
- **Assign Letter** — "Assigns or changes the drive letter."
- **Convert → MBR** — "Converts partition style. Destroys all data."
- **Convert → GPT** — "Converts partition style. Destroys all data."
- **Make Bootable USB** — "Formats and copies ISO contents. Requires ISO file selection."
- **Open Disk Management** — "Launches Windows Disk Management (diskmgmt.msc)."

Each button:
1. Is disabled (`state="disabled"`) until a non-system disk is selected
2. Dangerous ops (clean, format, convert) show confirmation dialog first
3. On confirmation, calls the corresponding `DiskPartEngine` method in a `threading.Thread`
4. Never blocks the UI thread

---

### `ui/terminal.py`

```python
# ui/terminal.py
# Live scrolling log of DiskPart output.
# Color-coded: green=success, red=error, yellow=warning, white=info.
# Uses CTkTextbox with tag_config for colors.
# Auto-scrolls to bottom on new output.
# Has "Clear" and "Export Log" buttons in header.

import customtkinter as ctk
from ui.theme import COLORS, FONT
from datetime import datetime

LEVEL_COLORS = {
    "info":    COLORS["text_primary"],
    "success": COLORS["success"],
    "error":   COLORS["danger"],
    "warning": COLORS["warning"],
    "cmd":     COLORS["accent"],      # the diskpart commands themselves
}

class TerminalPanel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS["bg_secondary"], corner_radius=8)
        self._build()

    def _build(self):
        # Header row: "OUTPUT" label + Clear button + Export button
        # CTkTextbox below
        ...

    def log(self, line: str, level: str = "info"):
        """Called by DiskPartEngine for each output line. Thread-safe via after()."""
        ...

    def clear(self): ...
    def export(self): ...
```

---

### `ui/dialogs.py`

```python
# ui/dialogs.py
# Confirmation dialogs for destructive operations.
# Returns True/False based on user choice.
# Always modal — blocks parent window.

import customtkinter as ctk
from ui.theme import COLORS, FONT
from core.disk_info import DiskInfo

def confirm_destructive(parent, disk: DiskInfo, operation: str) -> bool:
    """
    Shows a modal dialog with:
    - Operation name + disk details
    - Red warning banner: "THIS WILL PERMANENTLY ERASE ALL DATA"
    - Checkbox: "I understand this will erase all data on DISK N (model)"
    - Confirm button (disabled until checkbox checked)
    - Cancel button
    Returns True only if user checked the box AND clicked Confirm.
    """
    ...

def show_blocked(parent, reason: str):
    """Shows a non-destructive info dialog for blocked operations (e.g., system disk)."""
    ...

def show_error(parent, title: str, message: str):
    """Generic error dialog."""
    ...
```

---

### `ui/sidebar.py`

```python
# ui/sidebar.py
# Left navigation sidebar.
# Shows DiskWizard logo/name at top.
# Navigation items: Disks, Format, Partition, Boot USB, History, Settings.
# Active page highlighted with accent left-border.
# Admin badge at bottom.

import customtkinter as ctk
from ui.theme import COLORS, FONT
from typing import Callable

NAV_ITEMS = [
    ("disks",     "⬡  DISKS"),
    ("format",    "◈  FORMAT"),
    ("partition", "▤  PARTITION"),
    ("boot",      "⌁  BOOT USB"),
    ("history",   "≡  HISTORY"),
    ("settings",  "◎  SETTINGS"),
]

class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, on_navigate: Callable[[str], None]):
        super().__init__(parent, fg_color=COLORS["bg_secondary"], width=160, corner_radius=0)
        self.pack_propagate(False)
        self.on_navigate = on_navigate
        self.active_page = "disks"
        self._build()

    def _build(self):
        # Logo area: "DW" monogram + "DiskWizard" text
        # Nav buttons
        # Bottom: ADMIN badge in green
        ...
```

---

## SAFETY PROTECTIONS — IMPLEMENTATION CHECKLIST

Implement ALL of these. None are optional.

| Protection | Where | Implementation |
|---|---|---|
| Disk 0 never touchable | `safety.py` + `drive_card.py` | `validate_operation` returns blocked + card click disabled |
| Confirmation checkbox | `dialogs.py` | Confirm button disabled until checkbox state == True |
| Double disk index validation | `diskpart.py` `execute()` | Re-read disk index from DiskInfo right before writing script |
| No auto-execute | `operation_panel.py` | All destructive ops require dialog confirmation first |
| Script audit trail | `history.py` | Store exact script content in every HistoryEntry |
| Thread safety | `terminal.py` | Use `self.after()` for all UI updates from background threads |
| Temp file cleanup | `diskpart.py` | `finally:` block deletes temp file regardless of success/failure |
| Admin check | `main.py` + `admin.py` | App refuses to start without elevation |
| Readable errors | All UI callbacks | Catch subprocess exceptions, display in terminal as level="error" |

---

## PACKAGING

### `DiskWizard.spec` (PyInstaller)

```python
# DiskWizard.spec
block_cipher = None
a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('assets/fonts/*.ttf', 'assets/fonts'),
    ],
    hiddenimports=['customtkinter', 'wmi', 'psutil', 'win32api', 'win32con'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz, a.scripts, a.binaries, a.zipfiles, a.datas,
    name='DiskWizard',
    debug=False,
    strip=False,
    upx=True,
    console=False,              # No console window — GUI only
    uac_admin=True,             # Embed UAC manifest — Windows prompts for admin on launch
    icon='assets/icon.ico',
)
```

**Build command:**
```bash
pip install pyinstaller
pyinstaller DiskWizard.spec
# Output: dist/DiskWizard.exe
```

`uac_admin=True` in the spec embeds a UAC manifest into the exe — Windows will automatically prompt for admin when the user double-clicks it. This is cleaner than manual re-launch via ShellExecuteW for the compiled executable.

---

## COMMON MISTAKES TO AVOID

1. **Never call `diskpart` without `/s`** — inline diskpart commands are not scriptable and can't be tested.
2. **Never update CTk widgets from a background thread directly** — always use `widget.after(0, callback)`.
3. **Never assume Disk 1 is safe** — only `is_removable=True` disks should have destructive ops enabled.
4. **Never skip the temp file `finally` block** — leaked temp files in `%TEMP%` accumulate and confuse users.
5. **Never hardcode drive letters** — drive letters change between plugin events.
6. **Never use `subprocess.run()` for long operations** — use `Popen` + streaming to avoid UI freeze.
7. **Never disable the cancel button during execution** — user must always be able to cancel.

---

## EXECUTION ORDER

Build in this order (each step depends on the previous):

1. `utils/admin.py` → `main.py` — run, confirm UAC works
2. `ui/theme.py` — run, confirm window opens with correct colors/fonts
3. `core/disk_info.py` — run standalone, print disk list to console
4. `core/safety.py` — unit test validate_operation() for disk 0, disk 1
5. `core/diskpart.py` — test build_script() output before ever running diskpart
6. `ui/terminal.py` → `ui/drive_card.py` → `ui/drive_panel.py`
7. `ui/sidebar.py` → `ui/app.py` — wire layout
8. `ui/dialogs.py` → `ui/operation_panel.py`
9. `core/history.py` → wire into engine
10. `DiskWizard.spec` → PyInstaller build

---

## DELIVERABLE CHECKLIST

- [ ] App launches, requests UAC, shows window
- [ ] All connected disks detected and shown as cards
- [ ] Disk 0 card has danger styling and is unclickable
- [ ] Selecting a USB card enables operation buttons
- [ ] Clean Disk shows confirmation dialog with checkbox
- [ ] Checkbox required before Confirm button enables
- [ ] DiskPart output streams live in terminal panel
- [ ] Success lines green, error lines red, commands cyan
- [ ] History saved to %APPDATA%\DiskWizard\history.json
- [ ] Export log button writes terminal output to .txt
- [ ] Open Disk Management launches diskmgmt.msc
- [ ] PyInstaller exe runs without Python installed
- [ ] Exe triggers UAC on launch (uac_admin=True)
- [ ] No crash on USB unplug mid-operation
- [ ] Refresh button re-detects drives correctly
