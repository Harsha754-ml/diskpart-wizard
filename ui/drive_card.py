# ui/drive_card.py
# A single disk card - shows disk number, model, size, filesystem, drive letter.
# System disk (index 0) rendered with danger styling and blocked from selection.
# Selected disk gets accent border.

import customtkinter as ctk
from typing import Callable

from core.disk_info import DiskInfo
from ui.theme import COLORS, FONT


class DriveCard(ctk.CTkFrame):
    def __init__(self, parent, disk: DiskInfo, on_select: Callable[[DiskInfo], None]):
        bg = COLORS["bg_secondary"]
        super().__init__(
            parent,
            fg_color=bg,
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
        )

        self.disk = disk
        self.on_select = on_select
        self.selected = False

        self._build()
        if not disk.is_system_disk:
            self.bind("<Button-1>", self._handle_click)
            for child in self.winfo_children():
                child.bind("<Button-1>", self._handle_click)

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(8, 2))

        disk_label = ctk.CTkLabel(
            header,
            text=f"DISK {self.disk.index}",
            font=FONT(12, "bold"),
            text_color=COLORS["text_primary"],
        )
        disk_label.pack(side="left")

        badge_text = "USB" if self.disk.is_removable else "FIXED"
        badge_color = COLORS["accent"]
        if self.disk.is_system_disk:
            badge_text = "SYSTEM"
            badge_color = COLORS["danger"]

        badge = ctk.CTkLabel(
            header,
            text=badge_text,
            font=FONT(9, "bold"),
            text_color=badge_color,
        )
        badge.pack(side="right")

        model = ctk.CTkLabel(
            self,
            text=self.disk.model,
            font=FONT(11),
            text_color=COLORS["text_secondary"],
        )
        model.pack(anchor="w", padx=10)

        bar_row = ctk.CTkFrame(self, fg_color="transparent")
        bar_row.pack(fill="x", padx=10, pady=(6, 4))

        self.progress = ctk.CTkProgressBar(
            bar_row,
            fg_color=COLORS["bg_primary"],
            progress_color=COLORS["accent"],
            height=10,
        )
        self.progress.pack(side="left", fill="x", expand=True)
        self.progress.set(1.0)

        size_label = ctk.CTkLabel(
            bar_row,
            text=f"{self.disk.size_gb:.0f} GB",
            font=FONT(10),
            text_color=COLORS["text_secondary"],
        )
        size_label.pack(side="right", padx=(8, 0))

        fs = self.disk.filesystem or "Unformatted"
        letter = self.disk.drive_letter or "--"
        type_label = "Removable" if self.disk.is_removable else "Fixed"
        if self.disk.is_system_disk:
            type_label = "System"

        meta = ctk.CTkLabel(
            self,
            text=f"{fs} | {letter} | {type_label}",
            font=FONT(10),
            text_color=COLORS["text_secondary" if self.disk.filesystem else "text_muted"],
        )
        meta.pack(anchor="w", padx=10, pady=(0, 8))

    def set_selected(self, selected: bool):
        self.selected = selected
        border = COLORS["accent"] if selected else COLORS["border"]
        bg = COLORS["bg_tertiary"] if selected else COLORS["bg_secondary"]
        self.configure(border_color=border, border_width=2 if selected else 1)
        self.configure(fg_color=bg)

    def _handle_click(self, _event):
        if not self.disk.is_system_disk:
            self.on_select(self.disk)
