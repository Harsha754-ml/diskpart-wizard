# ui/dialogs.py
# Confirmation dialogs for destructive operations.
# Returns True/False based on user choice.
# Always modal - blocks parent window.

import customtkinter as ctk
from tkinter import BooleanVar

from ui.theme import COLORS, FONT
from core.disk_info import DiskInfo


def _center_window(win: ctk.CTkToplevel, parent: ctk.CTkBaseClass):
    win.update_idletasks()
    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (win.winfo_width() // 2)
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (win.winfo_height() // 2)
    win.geometry(f"+{x}+{y}")


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
    result = {"value": False}

    dialog = ctk.CTkToplevel(parent)
    dialog.title("Confirm Destructive Operation")
    dialog.geometry("520x260")
    dialog.configure(fg_color=COLORS["bg_secondary"])
    dialog.transient(parent)
    dialog.grab_set()

    title = ctk.CTkLabel(
        dialog,
        text=f"{operation.upper()} - DISK {disk.index}",
        font=FONT(13, "bold"),
        text_color=COLORS["text_primary"],
    )
    title.pack(anchor="w", padx=16, pady=(14, 6))

    detail = ctk.CTkLabel(
        dialog,
        text=disk.model,
        font=FONT(11),
        text_color=COLORS["text_secondary"],
    )
    detail.pack(anchor="w", padx=16)

    warning = ctk.CTkFrame(dialog, fg_color=COLORS["danger"], corner_radius=6)
    warning.pack(fill="x", padx=16, pady=(12, 10))
    warning_text = ctk.CTkLabel(
        warning,
        text="THIS WILL PERMANENTLY ERASE ALL DATA",
        font=FONT(11, "bold"),
        text_color=COLORS["bg_primary"],
    )
    warning_text.pack(padx=10, pady=6)

    confirm_var = BooleanVar(value=False)

    def _toggle():
        confirm_btn.configure(state="normal" if confirm_var.get() else "disabled")

    checkbox = ctk.CTkCheckBox(
        dialog,
        text=f"I understand this will erase all data on DISK {disk.index} ({disk.model})",
        variable=confirm_var,
        command=_toggle,
        text_color=COLORS["text_primary"],
    )
    checkbox.pack(anchor="w", padx=16, pady=(0, 16))

    button_row = ctk.CTkFrame(dialog, fg_color=COLORS["bg_secondary"])
    button_row.pack(fill="x", padx=16, pady=(0, 12))

    def _confirm():
        if confirm_var.get():
            result["value"] = True
            dialog.destroy()

    def _cancel():
        dialog.destroy()

    confirm_btn = ctk.CTkButton(
        button_row,
        text="Confirm",
        fg_color=COLORS["danger"],
        hover_color=COLORS["accent_dim"],
        state="disabled",
        command=_confirm,
    )
    confirm_btn.pack(side="right")

    cancel_btn = ctk.CTkButton(
        button_row,
        text="Cancel",
        fg_color=COLORS["bg_tertiary"],
        hover_color=COLORS["bg_primary"],
        command=_cancel,
    )
    cancel_btn.pack(side="right", padx=(0, 8))

    _center_window(dialog, parent)
    dialog.wait_window()
    return result["value"]


def show_blocked(parent, reason: str):
    """Shows a non-destructive info dialog for blocked operations (e.g., system disk)."""
    dialog = ctk.CTkToplevel(parent)
    dialog.title("Operation Blocked")
    dialog.geometry("420x180")
    dialog.configure(fg_color=COLORS["bg_secondary"])
    dialog.transient(parent)
    dialog.grab_set()

    title = ctk.CTkLabel(
        dialog,
        text="Operation Blocked",
        font=FONT(13, "bold"),
        text_color=COLORS["warning"],
    )
    title.pack(anchor="w", padx=16, pady=(14, 6))

    message = ctk.CTkLabel(
        dialog,
        text=reason,
        font=FONT(11),
        text_color=COLORS["text_primary"],
        wraplength=380,
        justify="left",
    )
    message.pack(anchor="w", padx=16, pady=(0, 16))

    ok_btn = ctk.CTkButton(
        dialog,
        text="OK",
        fg_color=COLORS["bg_tertiary"],
        hover_color=COLORS["bg_primary"],
        command=dialog.destroy,
    )
    ok_btn.pack(padx=16, pady=(0, 12), anchor="e")

    _center_window(dialog, parent)
    dialog.wait_window()


def show_error(parent, title: str, message: str):
    """Generic error dialog."""
    dialog = ctk.CTkToplevel(parent)
    dialog.title(title)
    dialog.geometry("420x200")
    dialog.configure(fg_color=COLORS["bg_secondary"])
    dialog.transient(parent)
    dialog.grab_set()

    title_label = ctk.CTkLabel(
        dialog,
        text=title,
        font=FONT(13, "bold"),
        text_color=COLORS["danger"],
    )
    title_label.pack(anchor="w", padx=16, pady=(14, 6))

    message_label = ctk.CTkLabel(
        dialog,
        text=message,
        font=FONT(11),
        text_color=COLORS["text_primary"],
        wraplength=380,
        justify="left",
    )
    message_label.pack(anchor="w", padx=16, pady=(0, 16))

    ok_btn = ctk.CTkButton(
        dialog,
        text="OK",
        fg_color=COLORS["bg_tertiary"],
        hover_color=COLORS["bg_primary"],
        command=dialog.destroy,
    )
    ok_btn.pack(padx=16, pady=(0, 12), anchor="e")

    _center_window(dialog, parent)
    dialog.wait_window()
