# ui/drive_card.py
# A single disk card - shows disk number, model, size, filesystem, drive letter.
# System disk (index 0) rendered with danger styling and blocked from selection.
# Selected disk gets accent border.

import customtkinter as ctk
import tkinter as tk
from typing import Callable
import psutil

from core.disk_info import DiskInfo
from ui.theme import COLORS, FONT


class CTkToolTip:
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


class DriveCard(ctk.CTkFrame):
    def __init__(self, parent, disk: DiskInfo, on_select: Callable[[DiskInfo], None]):
        bg = COLORS["bg_secondary"]
        try:
            super().__init__(
                parent,
                fg_color=bg,
                corner_radius=8,
                border_width=1,
                border_color=COLORS["border"],
            )
        except Exception:
            super().__init__(
                parent,
                fg_color=bg,
                corner_radius=8,
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
            text=self._truncate_model(self.disk.model),
            font=FONT(11),
            text_color=COLORS["text_secondary"],
        )
        model.pack(anchor="w", padx=10)
        CTkToolTip(model, self.disk.model)

        bar_row = ctk.CTkFrame(self, fg_color="transparent")
        bar_row.pack(fill="x", padx=10, pady=(6, 4))

        self.progress = ctk.CTkProgressBar(
            bar_row,
            fg_color=COLORS["bg_primary"],
            progress_color=COLORS["accent"],
            height=10,
        )
        self.progress.pack(side="left", fill="x", expand=True)

        ratio, usage_text = self._usage_display()
        self.progress.set(ratio)

        size_label = ctk.CTkLabel(
            bar_row,
            text=usage_text,
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
        try:
            self.configure(border_color=border, border_width=2 if selected else 1)
        except Exception:
            self.configure(border_color=border)
        self.configure(fg_color=bg)

    def _handle_click(self, _event):
        if not self.disk.is_system_disk:
            self.on_select(self.disk)

    def _truncate_model(self, model: str) -> str:
        if len(model) <= 28:
            return model
        return f"{model[:28]}..."

    def _usage_display(self) -> tuple[float, str]:
        if not self.disk.drive_letter:
            return 0.0, "No data"
        try:
            usage = psutil.disk_usage(f"{self.disk.drive_letter}\\")
        except Exception:
            return 0.0, "No data"
        if usage.total <= 0:
            return 0.0, "No data"
        ratio = max(0.0, min(1.0, usage.used / usage.total))
        used_gb = usage.used / (1024**3)
        total_gb = usage.total / (1024**3)
        return ratio, f"{used_gb:.0f}/{total_gb:.0f} GB"
