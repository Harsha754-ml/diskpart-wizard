# ui/app.py
# Root application window.
# Manages layout, navigation state, and shared application state.
# Child components communicate via callbacks passed at construction time.

from typing import Optional
import customtkinter as ctk

from ui.theme import apply_theme, COLORS
from ui.sidebar import Sidebar
from ui.drive_panel import DrivePanel
from ui.operation_panel import OperationPanel
from ui.terminal import TerminalPanel
from core.diskpart import DiskPartEngine
from core.disk_info import DiskInfo


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

        # Terminal widget created first - engine needs its callback
        self.terminal = TerminalPanel(self)
        self.engine = DiskPartEngine(output_callback=self.terminal.log)

        self._build_layout()

    def _build_layout(self):
        # Left sidebar - fixed 160px
        self.sidebar = Sidebar(self, on_navigate=self._navigate)
        self.sidebar.pack(side="left", fill="y")

        # Right main area
        self.main_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_primary"])
        self.main_frame.pack(side="left", fill="both", expand=True, padx=16, pady=16)

        # Drive cards row
        self.drive_panel = DrivePanel(
            self.main_frame,
            on_disk_selected=self._on_disk_selected,
        )
        self.drive_panel.pack(fill="x", pady=(0, 12))

        # Operation buttons
        self.op_panel = OperationPanel(
            self.main_frame,
            engine=self.engine,
            get_selected_disk=lambda: self.selected_disk,
        )
        self.op_panel.pack(fill="x", pady=(0, 12))

        # Terminal output
        self.terminal.pack(fill="both", expand=True)

    def _on_disk_selected(self, disk: DiskInfo):
        self.selected_disk = disk
        self.op_panel.refresh_for_disk(disk)

    def _navigate(self, page: str):
        self.current_page = page
        show_ops = page in {"disks", "format", "partition", "boot"}
        if show_ops:
            if not self.drive_panel.winfo_ismapped():
                self.drive_panel.pack(fill="x", pady=(0, 12))
            if not self.op_panel.winfo_ismapped():
                self.op_panel.pack(fill="x", pady=(0, 12))
        else:
            if self.drive_panel.winfo_ismapped():
                self.drive_panel.pack_forget()
            if self.op_panel.winfo_ismapped():
                self.op_panel.pack_forget()
