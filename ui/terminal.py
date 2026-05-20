# ui/terminal.py
# Live scrolling log of DiskPart output.
# Color-coded: green=success, red=error, yellow=warning, white=info.
# Uses CTkTextbox with tag_config for colors.
# Auto-scrolls to bottom on new output.
# Has "Clear" and "Export Log" buttons in header.

import customtkinter as ctk
from tkinter import filedialog

from ui.theme import COLORS, FONT

LEVEL_COLORS = {
    "info": COLORS["text_primary"],
    "success": COLORS["success"],
    "error": COLORS["danger"],
    "warning": COLORS["warning"],
    "cmd": COLORS["accent"],
}


class TerminalPanel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS["bg_secondary"], corner_radius=8)
        self._build()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"])
        header.pack(fill="x", padx=12, pady=(10, 6))

        title = ctk.CTkLabel(
            header,
            text="OUTPUT",
            text_color=COLORS["text_secondary"],
            font=FONT(12, "bold"),
        )
        title.pack(side="left")

        clear_btn = ctk.CTkButton(
            header,
            text="Clear",
            width=80,
            fg_color=COLORS["bg_tertiary"],
            hover_color=COLORS["bg_primary"],
            command=self.clear,
        )
        clear_btn.pack(side="right", padx=(8, 0))

        export_btn = ctk.CTkButton(
            header,
            text="Export Log",
            width=120,
            fg_color=COLORS["bg_tertiary"],
            hover_color=COLORS["bg_primary"],
            command=self.export,
        )
        export_btn.pack(side="right")

        self.textbox = ctk.CTkTextbox(
            self,
            fg_color=COLORS["bg_tertiary"],
            text_color=COLORS["text_primary"],
            border_color=COLORS["border"],
            font=FONT(11),
            wrap="word",
        )
        self.textbox.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        for level, color in LEVEL_COLORS.items():
            self.textbox.tag_config(level, foreground=color)

    def log(self, line: str, level: str = "info"):
        """Called by DiskPartEngine for each output line. Thread-safe via after()."""

        def _append():
            safe_level = level if level in LEVEL_COLORS else "info"
            self.textbox.insert("end", line + "\n", safe_level)
            self.textbox.see("end")

        self.after(0, _append)

    def clear(self):
        self.textbox.delete("1.0", "end")

    def export(self):
        path = filedialog.asksaveasfilename(
            title="Export Log",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
        )
        if not path:
            return
        content = self.textbox.get("1.0", "end").strip()
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
