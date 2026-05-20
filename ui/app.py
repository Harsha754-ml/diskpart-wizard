# ui/app.py
# Root application window.
# Manages layout, navigation state, and shared application state.
# Child components communicate via callbacks passed at construction time.

from typing import Optional
import subprocess
import tkinter as tk
import customtkinter as ctk

from ui.theme import apply_theme, COLORS, FONT
from ui.sidebar import DiskInfoPanel
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

        # Terminal widget created first - engine needs its callback
        self.terminal = TerminalPanel(self)
        self.engine = DiskPartEngine(output_callback=self.terminal.log)

        self._build_layout()

    def _build_layout(self):
        # Left sidebar - selected disk info and quick actions
        self.sidebar = DiskInfoPanel(
            self,
            on_refresh_drives=self._refresh_drives,
            on_open_disk_mgmt=self._open_disk_mgmt,
        )
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

        self.empty_state = ctk.CTkFrame(
            self.main_frame,
            fg_color=COLORS["bg_secondary"],
            corner_radius=8,
        )
        self.empty_state.pack(fill="both", expand=True, pady=(0, 12))
        self._build_empty_state()

        # Guided operations flow
        self.op_panel = OperationPanel(
            self.main_frame,
            engine=self.engine,
            get_selected_disk=lambda: self.selected_disk,
            on_change_drive=self._change_drive,
            on_refresh_drives=self._refresh_drives,
        )

        # Terminal output
        self.terminal.pack(fill="x", side="bottom")
        self.terminal.pack_propagate(False)
        self.terminal.configure(height=200)

    def _build_empty_state(self):
        canvas = tk.Canvas(
            self.empty_state,
            width=72,
            height=72,
            bg=COLORS["bg_secondary"],
            highlightthickness=0,
            bd=0,
        )
        canvas.pack(pady=(36, 14))
        canvas.create_oval(12, 8, 60, 56, outline=COLORS["text_muted"], width=2)
        canvas.create_line(36, 24, 36, 48, fill=COLORS["text_muted"], width=2)
        canvas.create_line(30, 42, 36, 48, fill=COLORS["text_muted"], width=2)
        canvas.create_line(42, 42, 36, 48, fill=COLORS["text_muted"], width=2)

        title = ctk.CTkLabel(
            self.empty_state,
            text="Select a drive above to begin",
            font=FONT(14, "bold"),
            text_color=COLORS["text_muted"],
        )
        title.pack()

        subtext = ctk.CTkLabel(
            self.empty_state,
            text="System drives are locked for your safety",
            font=FONT(14),
            text_color=COLORS["text_muted"],
        )
        subtext.pack(pady=(6, 0))

    def _on_disk_selected(self, disk: Optional[DiskInfo]):
        self.selected_disk = disk
        if hasattr(self, "sidebar"):
            self.sidebar.update_disk_info(disk)
        if not hasattr(self, "op_panel"):
            return
        if disk and not disk.is_system_disk:
            if self.empty_state.winfo_ismapped():
                self.empty_state.pack_forget()
            if not self.op_panel.winfo_ismapped():
                self.op_panel.pack(fill="x", pady=(0, 12))
            self.op_panel.refresh_for_disk(disk)
        else:
            if self.op_panel.winfo_ismapped():
                self.op_panel.pack_forget()
            if not self.empty_state.winfo_ismapped():
                self.empty_state.pack(fill="both", expand=True, pady=(0, 12))
            self.op_panel.refresh_for_disk(None)

    def _refresh_drives(self):
        self.drive_panel.refresh()
        self.sidebar.update_disk_info(self.selected_disk)

    def _open_disk_mgmt(self):
        try:
            subprocess.Popen("diskmgmt.msc", shell=True)
        except Exception as exc:
            self.terminal.log(f"Failed to open Disk Management: {exc}", "error")

    def _change_drive(self):
        self.selected_disk = None
        self.drive_panel.clear_selection()
        self.sidebar.update_disk_info(None)
        if self.op_panel.winfo_ismapped():
            self.op_panel.pack_forget()
        if not self.empty_state.winfo_ismapped():
            self.empty_state.pack(fill="both", expand=True, pady=(0, 12))
