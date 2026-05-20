# ui/sidebar.py
# Left navigation sidebar.
# Shows DiskWizard logo/name at top.
# Navigation items: Disks, Format, Partition, Boot USB, History, Settings.
# Active page highlighted with accent left-border.
# Admin badge at bottom.

import customtkinter as ctk
from typing import Callable, Dict, Tuple

from ui.theme import COLORS, FONT

NAV_ITEMS = [
    ("disks", "DISKS"),
    ("format", "FORMAT"),
    ("partition", "PARTITION"),
    ("boot", "BOOT USB"),
    ("history", "HISTORY"),
    ("settings", "SETTINGS"),
]


class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, on_navigate: Callable[[str], None]):
        super().__init__(parent, fg_color=COLORS["bg_secondary"], width=160, corner_radius=0)
        self.pack_propagate(False)
        self.on_navigate = on_navigate
        self.active_page = "disks"
        self.nav_rows: Dict[str, Tuple[ctk.CTkFrame, ctk.CTkFrame]] = {}
        self._build()

    def _build(self):
        logo = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"])
        logo.pack(fill="x", padx=12, pady=(16, 20))

        monogram = ctk.CTkLabel(
            logo,
            text="DW",
            font=FONT(14, "bold"),
            text_color=COLORS["accent"],
        )
        monogram.pack(anchor="w")

        title = ctk.CTkLabel(
            logo,
            text="DiskWizard",
            font=FONT(12, "bold"),
            text_color=COLORS["text_primary"],
        )
        title.pack(anchor="w")

        for key, label in NAV_ITEMS:
            row = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"])
            row.pack(fill="x", padx=8, pady=2)

            indicator = ctk.CTkFrame(
                row,
                fg_color=COLORS["accent"] if key == self.active_page else COLORS["bg_secondary"],
                width=4,
                corner_radius=2,
            )
            indicator.pack(side="left", fill="y")

            btn = ctk.CTkButton(
                row,
                text=label,
                fg_color=COLORS["bg_secondary"],
                hover_color=COLORS["bg_tertiary"],
                text_color=COLORS["text_primary"],
                anchor="w",
                font=FONT(11, "bold"),
                command=lambda k=key: self._navigate(k),
            )
            btn.pack(side="left", fill="x", expand=True, padx=(6, 0))

            self.nav_rows[key] = (row, indicator)

        spacer = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"])
        spacer.pack(fill="both", expand=True)

        admin = ctk.CTkLabel(
            self,
            text="ADMIN",
            font=FONT(10, "bold"),
            text_color=COLORS["success"],
        )
        admin.pack(pady=(0, 14))

    def _navigate(self, page: str):
        self.active_page = page
        for key, (_row, indicator) in self.nav_rows.items():
            indicator.configure(
                fg_color=COLORS["accent"] if key == page else COLORS["bg_secondary"]
            )
        self.on_navigate(page)
