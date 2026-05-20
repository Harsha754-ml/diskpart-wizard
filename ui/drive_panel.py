# ui/drive_panel.py
# Drive list + refresh.
# Horizontal scroll area of DriveCard widgets.

import tkinter as tk
import customtkinter as ctk

from typing import Callable, List

from core.disk_info import DiskInfo, get_all_disks
from ui.drive_card import DriveCard
from ui.theme import COLORS, FONT


class DrivePanel(ctk.CTkFrame):
    def __init__(self, parent, on_disk_selected: Callable[[DiskInfo], None]):
        super().__init__(parent, fg_color=COLORS["bg_primary"])
        self.on_disk_selected = on_disk_selected
        self.cards: List[DriveCard] = []
        self.selected_disk: DiskInfo | None = None
        self._build()
        self.refresh()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_primary"])
        header.pack(fill="x", pady=(0, 8))

        title = ctk.CTkLabel(
            header,
            text="DRIVES",
            font=FONT(12, "bold"),
            text_color=COLORS["text_secondary"],
        )
        title.pack(side="left")

        refresh_btn = ctk.CTkButton(
            header,
            text="Refresh",
            width=90,
            fg_color=COLORS["bg_tertiary"],
            hover_color=COLORS["bg_secondary"],
            command=self.refresh,
        )
        refresh_btn.pack(side="right")

        self.canvas = tk.Canvas(
            self,
            bg=COLORS["bg_primary"],
            highlightthickness=0,
            height=140,
        )
        self.canvas.pack(fill="x", expand=False)

        self.scrollbar = ctk.CTkScrollbar(
            self, orientation="horizontal", command=self.canvas.xview
        )
        self.scrollbar.pack(fill="x", pady=(4, 0))
        self.canvas.configure(xscrollcommand=self.scrollbar.set)

        self.inner = ctk.CTkFrame(self.canvas, fg_color=COLORS["bg_primary"])
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.inner, anchor="nw"
        )

        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _on_inner_configure(self, _event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, height=event.height)

    def refresh(self):
        for child in self.inner.winfo_children():
            child.destroy()
        self.cards = []

        disks = get_all_disks()
        for disk in disks:
            card = DriveCard(self.inner, disk, on_select=self._handle_select)
            card.pack(side="left", padx=6)
            self.cards.append(card)

    def _handle_select(self, disk: DiskInfo):
        self.selected_disk = disk
        for card in self.cards:
            card.set_selected(card.disk.index == disk.index)
        self.on_disk_selected(disk)
