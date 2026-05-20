# ui/operation_panel.py
# Operation buttons and form inputs.
# Dangerous ops require confirmation and are run in background threads.

import os
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog

import customtkinter as ctk

from core.disk_info import DiskInfo
from core.safety import validate_operation
from ui.theme import COLORS, FONT
from ui import dialogs


class _Tooltip:
    def __init__(self, widget, text: str):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, _event):
        if self.tip or not self.text:
            return
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.configure(bg=COLORS["bg_tertiary"])
        label = tk.Label(
            self.tip,
            text=self.text,
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            font=FONT(9),
            padx=6,
            pady=4,
        )
        label.pack()
        x = self.widget.winfo_rootx() + 10
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.tip.wm_geometry(f"+{x}+{y}")

    def _hide(self, _event):
        if self.tip:
            self.tip.destroy()
            self.tip = None


class OperationPanel(ctk.CTkFrame):
    def __init__(self, parent, engine, get_selected_disk):
        super().__init__(parent, fg_color=COLORS["bg_secondary"], corner_radius=8)
        self.engine = engine
        self.get_selected_disk = get_selected_disk
        self.buttons = []
        self._build()

    def _build(self):
        header = ctk.CTkLabel(
            self,
            text="OPERATIONS",
            font=FONT(12, "bold"),
            text_color=COLORS["text_secondary"],
        )
        header.pack(anchor="w", padx=12, pady=(10, 8))

        grid = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"])
        grid.pack(fill="x", padx=12, pady=(0, 12))
        grid.grid_columnconfigure((0, 1, 2), weight=1)

        self.fs_choice = ctk.CTkOptionMenu(
            grid,
            values=["ntfs", "fat32", "exfat"],
            fg_color=COLORS["bg_tertiary"],
            button_color=COLORS["bg_primary"],
            button_hover_color=COLORS["bg_secondary"],
        )
        self.fs_choice.set("ntfs")
        self.fs_choice.grid(row=0, column=0, padx=6, pady=6, sticky="ew")

        self.label_entry = ctk.CTkEntry(
            grid,
            placeholder_text="Label (optional)",
            fg_color=COLORS["bg_tertiary"],
        )
        self.label_entry.grid(row=0, column=1, padx=6, pady=6, sticky="ew")

        self.letter_entry = ctk.CTkEntry(
            grid,
            placeholder_text="Letter (A-Z)",
            fg_color=COLORS["bg_tertiary"],
        )
        self.letter_entry.grid(row=0, column=2, padx=6, pady=6, sticky="ew")

        self.clean_btn = self._button(
            grid,
            text="Clean Disk",
            row=1,
            column=0,
            color=COLORS["danger"],
            cmd=self._clean_disk,
            tooltip="Wipes ALL data. Partition table is destroyed. Unrecoverable.",
        )
        self.format_btn = self._button(
            grid,
            text="Quick Format",
            row=1,
            column=1,
            color=COLORS["danger"],
            cmd=self._quick_format,
            tooltip="Formats with chosen filesystem. Select NTFS, FAT32, or exFAT.",
        )
        self.create_btn = self._button(
            grid,
            text="Create Partition",
            row=1,
            column=2,
            color=COLORS["bg_tertiary"],
            cmd=self._create_partition,
            tooltip="Creates a single primary partition and formats NTFS.",
        )

        self.assign_btn = self._button(
            grid,
            text="Assign Letter",
            row=2,
            column=0,
            color=COLORS["bg_tertiary"],
            cmd=self._assign_letter,
            tooltip="Assigns or changes the drive letter.",
        )
        self.mbr_btn = self._button(
            grid,
            text="Convert to MBR",
            row=2,
            column=1,
            color=COLORS["danger"],
            cmd=self._convert_mbr,
            tooltip="Converts partition style. Destroys all data.",
        )
        self.gpt_btn = self._button(
            grid,
            text="Convert to GPT",
            row=2,
            column=2,
            color=COLORS["danger"],
            cmd=self._convert_gpt,
            tooltip="Converts partition style. Destroys all data.",
        )

        self.boot_btn = self._button(
            grid,
            text="Make Bootable USB",
            row=3,
            column=0,
            color=COLORS["bg_tertiary"],
            cmd=self._make_bootable,
            tooltip="Formats and copies ISO contents. Requires ISO file selection.",
        )
        self.diskmgmt_btn = self._button(
            grid,
            text="Open Disk Management",
            row=3,
            column=1,
            color=COLORS["bg_tertiary"],
            cmd=self._open_disk_mgmt,
            tooltip="Launches Windows Disk Management (diskmgmt.msc).",
        )

        self.refresh_for_disk(None)

    def _button(self, parent, text, row, column, color, cmd, tooltip):
        btn = ctk.CTkButton(
            parent,
            text=text,
            fg_color=color,
            hover_color=COLORS["bg_primary"],
            command=cmd,
        )
        btn.grid(row=row, column=column, padx=6, pady=6, sticky="ew")
        _Tooltip(btn, tooltip)
        self.buttons.append(btn)
        return btn

    def refresh_for_disk(self, disk: DiskInfo | None):
        enabled = bool(disk) and not disk.is_system_disk
        for btn in self.buttons:
            btn.configure(state="normal" if enabled else "disabled")

    def _validate(self, op: str, disk: DiskInfo) -> bool:
        allowed, reason = validate_operation(op, disk)
        if not allowed:
            dialogs.show_blocked(self, reason)
            return False
        if reason:
            self.engine.output_callback(reason, "warning")
        return True

    def _run_threaded(self, fn):
        threading.Thread(target=fn, daemon=True).start()

    def _clean_disk(self):
        disk = self.get_selected_disk()
        if not disk or not self._validate("clean", disk):
            return
        if not dialogs.confirm_destructive(self, disk, "Clean Disk"):
            return
        self._run_threaded(lambda: self.engine.clean_disk(disk))

    def _quick_format(self):
        disk = self.get_selected_disk()
        if not disk or not self._validate("format", disk):
            return
        if not dialogs.confirm_destructive(self, disk, "Quick Format"):
            return
        fs = self.fs_choice.get().lower()
        label = self.label_entry.get().strip()
        self._run_threaded(lambda: self.engine.quick_format(disk, fs=fs, label=label))

    def _create_partition(self):
        disk = self.get_selected_disk()
        if not disk or not self._validate("create_partition", disk):
            return
        self._run_threaded(lambda: self.engine.create_partition(disk))

    def _assign_letter(self):
        disk = self.get_selected_disk()
        if not disk or not self._validate("assign", disk):
            return
        letter = self.letter_entry.get().strip().upper()
        if len(letter) != 1 or not letter.isalpha():
            dialogs.show_error(self, "Invalid Letter", "Enter a single letter A-Z.")
            return
        self._run_threaded(lambda: self.engine.assign_letter(disk, letter))

    def _convert_mbr(self):
        disk = self.get_selected_disk()
        if not disk or not self._validate("convert", disk):
            return
        if not dialogs.confirm_destructive(self, disk, "Convert to MBR"):
            return
        self._run_threaded(lambda: self.engine.convert_mbr(disk))

    def _convert_gpt(self):
        disk = self.get_selected_disk()
        if not disk or not self._validate("convert", disk):
            return
        if not dialogs.confirm_destructive(self, disk, "Convert to GPT"):
            return
        self._run_threaded(lambda: self.engine.convert_gpt(disk))

    def _make_bootable(self):
        disk = self.get_selected_disk()
        if not disk or not self._validate("format", disk):
            return
        iso_path = filedialog.askopenfilename(
            title="Select ISO",
            filetypes=[("ISO Files", "*.iso")],
        )
        if not iso_path:
            return
        if not dialogs.confirm_destructive(self, disk, "Make Bootable USB"):
            return
        self._run_threaded(lambda: self.engine.make_bootable(disk, iso_path))

    def _open_disk_mgmt(self):
        try:
            subprocess.Popen("diskmgmt.msc", shell=True)
        except Exception as exc:
            dialogs.show_error(self, "Launch Failed", str(exc))
