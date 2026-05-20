# ui/operation_panel.py
# Guided 3-stage task flow for disk operations.

import threading
import tkinter as tk
from tkinter import filedialog

import customtkinter as ctk

from core.disk_info import DiskInfo
from core.safety import validate_operation
from ui.theme import COLORS, FONT
from ui import dialogs


TASK_DEFS = {
    "format": {
        "icon": "◈",
        "title": "Format Drive",
        "description": "Wipe and reformat\nwith a new filesystem",
    },
    "partition": {
        "icon": "▤",
        "title": "Create Partition",
        "description": "Set up a new partition\non a clean disk",
    },
    "boot": {
        "icon": "⌁",
        "title": "Make Bootable USB",
        "description": "Flash an ISO to\nthis USB drive",
    },
    "convert": {
        "icon": "↔",
        "title": "Convert Disk Style",
        "description": "Switch between MBR\nand GPT formats",
    },
    "assign": {
        "icon": "◎",
        "title": "Assign Drive Letter",
        "description": "Change or assign the\ndrive letter for this drive",
    },
}


class _TaskCard(ctk.CTkFrame):
    def __init__(self, parent, task_key: str, on_click):
        super().__init__(
            parent,
            fg_color=COLORS["bg_secondary"],
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
        )
        self.task_key = task_key
        self.on_click = on_click
        self.selected = False
        self.disabled = False
        self.default_fg = COLORS["bg_secondary"]
        self.hover_fg = COLORS["bg_tertiary"]
        self.default_border = COLORS["border"]
        self.active_border = COLORS["accent"]
        self._build()
        self._bind_recursive(self)

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 4))
        top.grid_columnconfigure(1, weight=1)

        meta = TASK_DEFS[self.task_key]
        self.icon_label = ctk.CTkLabel(
            top,
            text=meta["icon"],
            font=FONT(18, "bold"),
            text_color=COLORS["accent"],
        )
        self.icon_label.grid(row=0, column=0, sticky="w")

        title_row = ctk.CTkFrame(top, fg_color="transparent")
        title_row.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        title_row.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            title_row,
            text=meta["title"],
            font=FONT(13, "bold"),
            text_color=COLORS["text_primary"],
            anchor="w",
        )
        self.title_label.grid(row=0, column=0, sticky="w")

        self.running_label = ctk.CTkLabel(
            title_row,
            text="",
            font=FONT(10, "bold"),
            text_color=COLORS["accent"],
        )
        self.running_label.grid(row=0, column=1, sticky="e")

        self.desc_label = ctk.CTkLabel(
            self,
            text=meta["description"],
            font=FONT(11),
            text_color=COLORS["text_secondary"],
            justify="left",
            anchor="w",
        )
        self.desc_label.grid(row=1, column=0, sticky="w", padx=14, pady=(4, 12))

    def _bind_recursive(self, widget):
        widget.bind("<Enter>", self._on_enter)
        widget.bind("<Leave>", self._on_leave)
        widget.bind("<Button-1>", self._on_click)
        for child in widget.winfo_children():
            self._bind_recursive(child)

    def _on_enter(self, _event):
        if self.disabled or self.selected:
            return
        self.configure(fg_color=self.hover_fg, border_color=self.active_border)

    def _on_leave(self, _event):
        if self.disabled:
            return
        self._apply_style()

    def _on_click(self, _event):
        if not self.disabled:
            self.on_click(self.task_key)

    def set_selected(self, selected: bool):
        self.selected = selected
        self._apply_style()

    def set_disabled(self, disabled: bool):
        self.disabled = disabled
        state_color = COLORS["text_muted"] if disabled else COLORS["text_primary"]
        desc_color = COLORS["text_muted"] if disabled else COLORS["text_secondary"]
        self.title_label.configure(text_color=state_color)
        self.desc_label.configure(text_color=desc_color)
        self.icon_label.configure(
            text_color=COLORS["text_muted"] if disabled else COLORS["accent"]
        )
        self._apply_style()

    def set_running(self, running: bool, phase: int = 0):
        if not running:
            self.running_label.configure(text="")
            return
        dots = "." * ((phase % 3) + 1)
        self.running_label.configure(text=f"RUNNING{dots}")

    def update_copy(self, title: str, description: str):
        self.title_label.configure(text=title)
        self.desc_label.configure(text=description)

    def _apply_style(self):
        if self.disabled:
            self.configure(fg_color=self.default_fg, border_color=COLORS["border"])
        elif self.selected:
            self.configure(fg_color=self.hover_fg, border_color=self.active_border)
        else:
            self.configure(fg_color=self.default_fg, border_color=self.default_border)


class OperationPanel(ctk.CTkFrame):
    def __init__(self, parent, engine, get_selected_disk, on_change_drive, on_refresh_drives):
        super().__init__(parent, fg_color=COLORS["bg_secondary"], corner_radius=8)
        self.engine = engine
        self.get_selected_disk = get_selected_disk
        self.on_change_drive = on_change_drive
        self.on_refresh_drives = on_refresh_drives
        self.current_task: str | None = None
        self.running = False
        self.running_phase = 0
        self.iso_path = ""
        self.result_state: str | None = None
        self.result_frame_for = None
        self.task_cards: dict[str, _TaskCard] = {}
        self.task_positions = {
            "format": (0, 0),
            "partition": (0, 1),
            "boot": (1, 0),
            "convert": (1, 1),
            "assign": (2, 0),
        }
        self._build()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"])
        header.pack(fill="x", padx=14, pady=(12, 8))

        self.disk_banner = ctk.CTkLabel(
            header,
            text="OPERATING ON: NO DISK SELECTED",
            font=FONT(12, "bold"),
            text_color=COLORS["accent"],
        )
        self.disk_banner.pack(side="left")

        self.change_drive_btn = ctk.CTkButton(
            header,
            text="Change Drive",
            width=110,
            fg_color=COLORS["bg_tertiary"],
            hover_color=COLORS["bg_primary"],
            text_color=COLORS["text_primary"],
            border_width=1,
            border_color=COLORS["border"],
            command=self._change_drive,
        )
        self.change_drive_btn.pack(side="right")

        self.task_picker = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"])
        self.task_picker.pack(fill="x", padx=14, pady=(0, 10))
        self.task_picker.grid_columnconfigure(0, weight=1)
        self.task_picker.grid_columnconfigure(1, weight=1)

        for task_key in TASK_DEFS:
            card = _TaskCard(self.task_picker, task_key, self._select_task)
            row, column = self.task_positions[task_key]
            card.grid(row=row, column=column, sticky="nsew", padx=6, pady=6)
            self.task_cards[task_key] = card

        self.config_panel = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_primary"],
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
        )

        self.result_frame = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_primary"],
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
        )

        self.refresh_for_disk(None)

    def refresh_for_disk(self, disk: DiskInfo | None):
        if disk:
            self.disk_banner.configure(text=f"OPERATING ON: DISK {disk.index} — {disk.model}")
            self.change_drive_btn.configure(state="normal")
        else:
            self.disk_banner.configure(text="OPERATING ON: NO DISK SELECTED")
            self.change_drive_btn.configure(state="disabled")
            self.current_task = None
            self.iso_path = ""
            self.result_state = None
            self._hide_config_and_result()
        self._refresh_task_cards()

    def _refresh_task_cards(self):
        disk = self.get_selected_disk()
        visible_tasks = self._visible_tasks(disk)
        for task, card in self.task_cards.items():
            if task in visible_tasks and disk is not None:
                row, column = self.task_positions[task]
                card.grid(row=row, column=column, sticky="nsew", padx=6, pady=6)
                card.update_copy(*self._task_copy(task, disk))
            else:
                card.grid_remove()
            card.set_selected(task == self.current_task and task in visible_tasks)
            card.set_disabled(self.running or disk is None)
        if self.current_task not in visible_tasks:
            self.current_task = None
            self._hide_config_and_result()
        elif self.current_task:
            self._show_config()

    def _visible_tasks(self, disk: DiskInfo | None) -> list[str]:
        if disk is None:
            return []
        tasks = ["format", "partition", "convert"]
        if disk.is_removable:
            tasks.append("boot")
        if disk.drive_letter:
            tasks.append("assign")
        return tasks

    def _task_copy(self, task: str, disk: DiskInfo):
        if task == "convert":
            if (disk.partition_style or "").upper() == "MBR":
                return ("Convert to GPT", "Switch this disk\nto GPT format")
            return ("Convert to MBR", "Switch this disk\nto MBR format")
        if task == "assign":
            letter = disk.drive_letter or "this drive"
            return ("Assign Drive Letter", f"Change or assign the\ndrive letter for {letter}")
        meta = TASK_DEFS[task]
        return (meta["title"], meta["description"])

    def _select_task(self, task_key: str):
        if self.running:
            return
        self.current_task = task_key
        self.result_state = None
        self.result_frame.pack_forget()
        self._refresh_task_cards()
        self._show_config()

    def _hide_config_and_result(self):
        self.config_panel.pack_forget()
        self.result_frame.pack_forget()

    def _show_config(self):
        if not self.current_task:
            self.config_panel.pack_forget()
            return
        self.result_frame.pack_forget()
        for child in self.config_panel.winfo_children():
            child.destroy()
        self.config_panel.pack(fill="x", padx=14, pady=(0, 12))
        builder = getattr(self, f"_build_{self.current_task}_config")
        builder()

    def _section_title(self, parent, text: str):
        label = ctk.CTkLabel(
            parent,
            text=text,
            font=FONT(12, "bold"),
            text_color=COLORS["text_primary"],
        )
        label.pack(anchor="w", padx=14, pady=(14, 8))
        return label

    def _info_text(self, parent, text: str):
        label = ctk.CTkLabel(
            parent,
            text=text,
            font=FONT(11),
            text_color=COLORS["text_secondary"],
            justify="left",
            anchor="w",
        )
        label.pack(anchor="w", padx=14, pady=(0, 10))
        return label

    def _warning_banner(self, parent, text: str):
        banner = ctk.CTkFrame(parent, fg_color=COLORS["warning"], corner_radius=8)
        banner.pack(fill="x", padx=14, pady=(0, 12))
        label = ctk.CTkLabel(
            banner,
            text=text,
            font=FONT(11, "bold"),
            text_color=COLORS["bg_primary"],
            anchor="w",
        )
        label.pack(anchor="w", padx=12, pady=8)
        return banner

    def _button_row(self, parent, primary_text: str, primary_command):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=(0, 14))

        self.back_btn = ctk.CTkButton(
            row,
            text="← Back",
            width=110,
            fg_color=COLORS["bg_tertiary"],
            hover_color=COLORS["bg_primary"],
            text_color=COLORS["text_primary"],
            border_width=1,
            border_color=COLORS["border"],
            command=self._back_to_picker,
        )
        self.back_btn.pack(side="left")

        self.primary_btn = ctk.CTkButton(
            row,
            text=primary_text,
            width=170,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_dim"],
            text_color=COLORS["bg_primary"],
            command=primary_command,
        )
        self.primary_btn.pack(side="right")
        self._set_buttons_enabled(not self.running)

    def _set_buttons_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        if hasattr(self, "back_btn"):
            self.back_btn.configure(state=state)
        if hasattr(self, "primary_btn"):
            self.primary_btn.configure(state=state)

    def _build_format_config(self):
        disk = self.get_selected_disk()
        self._section_title(self.config_panel, "FORMAT DRIVE")

        form = ctk.CTkFrame(self.config_panel, fg_color="transparent")
        form.pack(fill="x", padx=14, pady=(0, 12))
        form.grid_columnconfigure(0, weight=1)
        form.grid_columnconfigure(1, weight=1)

        self.fs_choice = ctk.CTkOptionMenu(
            form,
            values=["NTFS", "FAT32", "exFAT"],
            fg_color=COLORS["bg_tertiary"],
            button_color=COLORS["bg_primary"],
            button_hover_color=COLORS["bg_secondary"],
        )
        self.fs_choice.set("NTFS")
        self.fs_choice.grid(row=0, column=0, sticky="ew", padx=(0, 8), pady=(0, 8))

        self.label_entry = ctk.CTkEntry(
            form,
            placeholder_text="Drive label (optional)",
            fg_color=COLORS["bg_tertiary"],
        )
        self.label_entry.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=(0, 8))

        self.clean_var = tk.BooleanVar(value=True)
        self.clean_check = ctk.CTkCheckBox(
            form,
            text="Also clean disk before formatting (recommended)",
            variable=self.clean_var,
            state="disabled",
            text_color=COLORS["text_primary"],
        )
        self.clean_check.grid(row=1, column=0, columnspan=2, sticky="w")

        self._warning_banner(
            self.config_panel,
            f"⚠  This will permanently erase all data on DISK {disk.index}",
        )
        self._button_row(self.config_panel, "Format Drive →", self._submit_format)

    def _build_partition_config(self):
        self._section_title(self.config_panel, "CREATE PARTITION")
        self._info_text(
            self.config_panel,
            "Creates a single primary NTFS partition\nusing all available space.",
        )
        self.partition_quick_var = tk.BooleanVar(value=True)
        self.partition_quick_check = ctk.CTkCheckBox(
            self.config_panel,
            text="Quick format after creating partition",
            variable=self.partition_quick_var,
            state="disabled",
            text_color=COLORS["text_primary"],
        )
        self.partition_quick_check.pack(anchor="w", padx=14, pady=(0, 12))
        self._button_row(self.config_panel, "Create Partition →", self._submit_partition)

    def _build_boot_config(self):
        disk = self.get_selected_disk()
        self._section_title(self.config_panel, "MAKE BOOTABLE USB")

        choose_btn = ctk.CTkButton(
            self.config_panel,
            text="Choose ISO File...",
            width=180,
            fg_color=COLORS["bg_tertiary"],
            hover_color=COLORS["bg_primary"],
            text_color=COLORS["text_primary"],
            border_width=1,
            border_color=COLORS["border"],
            command=self._choose_iso,
        )
        choose_btn.pack(anchor="w", padx=14, pady=(0, 8))
        self.iso_btn = choose_btn

        self.iso_label = ctk.CTkLabel(
            self.config_panel,
            text=self._truncate_path(self.iso_path) if self.iso_path else "No ISO selected",
            font=FONT(10),
            text_color=COLORS["text_secondary" if self.iso_path else "text_muted"],
            justify="left",
            anchor="w",
        )
        self.iso_label.pack(anchor="w", padx=14, pady=(0, 10))

        self._info_text(
            self.config_panel,
            "Drive will be formatted FAT32 and made bootable",
        )
        self._warning_banner(
            self.config_panel,
            f"⚠  All data on DISK {disk.index} will be erased",
        )
        self._button_row(self.config_panel, "Flash USB →", self._submit_boot)

    def _build_convert_config(self):
        disk = self.get_selected_disk()
        self._section_title(self.config_panel, "CONVERT DISK STYLE")
        current_style = (disk.partition_style or "Unknown").upper()
        target_style = "GPT" if current_style == "MBR" else "MBR"

        flow = ctk.CTkFrame(self.config_panel, fg_color="transparent")
        flow.pack(fill="x", padx=14, pady=(0, 12))

        current_badge = ctk.CTkLabel(
            flow,
            text=f"Currently: {current_style}",
            font=FONT(11, "bold"),
            text_color=COLORS["text_primary"],
            fg_color=COLORS["bg_tertiary"],
            corner_radius=6,
            padx=10,
            pady=6,
        )
        current_badge.pack(side="left")

        arrow = ctk.CTkLabel(
            flow,
            text="→",
            font=FONT(14, "bold"),
            text_color=COLORS["accent"],
        )
        arrow.pack(side="left", padx=10)

        target_badge = ctk.CTkLabel(
            flow,
            text=f"Will become: {target_style}",
            font=FONT(11, "bold"),
            text_color=COLORS["text_primary"],
            fg_color=COLORS["bg_tertiary"],
            corner_radius=6,
            padx=10,
            pady=6,
        )
        target_badge.pack(side="left")

        self._warning_banner(
            self.config_panel,
            "⚠  All data will be erased during conversion",
        )
        self._button_row(self.config_panel, "Convert →", self._submit_convert)

    def _build_assign_config(self):
        disk = self.get_selected_disk()
        self._section_title(self.config_panel, "ASSIGN LETTER")

        self.letter_entry = ctk.CTkEntry(
            self.config_panel,
            placeholder_text=(disk.drive_letter or "E:")[0],
            fg_color=COLORS["bg_tertiary"],
            width=120,
        )
        self.letter_entry.pack(anchor="w", padx=14, pady=(0, 8))

        info_text = (
            f"Current letter: {disk.drive_letter}\\"
            if disk.drive_letter
            else "No letter assigned"
        )
        self._info_text(self.config_panel, info_text)
        self._button_row(self.config_panel, "Assign →", self._submit_assign)

    def _back_to_picker(self):
        if self.running:
            return
        self.current_task = None
        self.result_state = None
        self._hide_config_and_result()
        self._refresh_task_cards()

    def _change_drive(self):
        if self.running:
            return
        self.current_task = None
        self.result_state = None
        self.iso_path = ""
        self._hide_config_and_result()
        self.on_change_drive()

    def _choose_iso(self):
        if self.running:
            return
        path = filedialog.askopenfilename(
            title="Select ISO",
            filetypes=[("ISO Files", "*.iso")],
        )
        if not path:
            return
        self.iso_path = path
        self.iso_label.configure(
            text=self._truncate_path(path),
            text_color=COLORS["text_secondary"],
        )

    def _truncate_path(self, path: str) -> str:
        if len(path) <= 54:
            return path
        return f"{path[:24]}...{path[-24:]}"

    def _validate(self, op: str, disk: DiskInfo) -> bool:
        allowed, reason = validate_operation(op, disk)
        if not allowed:
            dialogs.show_blocked(self, reason)
            return False
        if reason:
            self.engine.output_callback(reason, "warning")
        return True

    def _run_operation(self, runner, success_message: str, refresh_on_success: bool):
        self._set_running(True)

        def _work():
            ok = False
            try:
                ok = runner()
            finally:
                self.after(
                    0,
                    lambda: self._finish_operation(
                        ok,
                        success_message,
                        refresh_on_success,
                    ),
                )

        threading.Thread(target=_work, daemon=True).start()

    def _finish_operation(self, success: bool, success_message: str, refresh_on_success: bool):
        self._set_running(False)
        if success:
            self._show_result("success", success_message)
            if refresh_on_success:
                self.after(1500, self.on_refresh_drives)
        else:
            self._show_result(
                "error",
                "✗  Operation failed — see terminal output for details",
            )

    def _show_result(self, kind: str, message: str):
        for child in self.result_frame.winfo_children():
            child.destroy()
        self.result_frame.pack(fill="x", padx=14, pady=(0, 12))
        border = COLORS["success"] if kind == "success" else COLORS["danger"]
        text_color = COLORS["success"] if kind == "success" else COLORS["danger"]
        self.result_frame.configure(border_color=border)

        label = ctk.CTkLabel(
            self.result_frame,
            text=message,
            font=FONT(11, "bold"),
            text_color=text_color,
            anchor="w",
            justify="left",
        )
        label.pack(side="left", padx=14, pady=10)

        button_text = "← Do another operation" if kind == "success" else "← Try again"
        button_cmd = self._back_to_picker if kind == "success" else self._show_config
        btn = ctk.CTkButton(
            self.result_frame,
            text=button_text,
            width=170,
            fg_color=COLORS["bg_tertiary"],
            hover_color=COLORS["bg_primary"],
            text_color=COLORS["text_primary"],
            border_width=1,
            border_color=COLORS["border"],
            command=button_cmd,
        )
        btn.pack(side="right", padx=14, pady=10)

    def _set_running(self, running: bool):
        self.running = running
        self._refresh_task_cards()
        self._set_buttons_enabled(not running)
        if hasattr(self, "iso_btn"):
            self.iso_btn.configure(state="disabled" if running else "normal")
        if running:
            self._tick_running()
        else:
            for card in self.task_cards.values():
                card.set_running(False)

    def _tick_running(self):
        if not self.running or not self.current_task:
            return
        self.running_phase += 1
        for key, card in self.task_cards.items():
            card.set_running(key == self.current_task, self.running_phase)
        self.after(400, self._tick_running)

    def _submit_format(self):
        disk = self.get_selected_disk()
        if not disk or not self._validate("format", disk):
            return
        if not dialogs.confirm_destructive(self, disk, "Format Drive"):
            return
        fs = self.fs_choice.get().lower()
        label = self.label_entry.get().strip()
        drive = disk.drive_letter or "(pending)"
        size = f"{disk.size_gb:.0f} GB" if disk.size_gb else "--"
        message = f"✓  Format complete — Drive is now {drive} {fs.upper()} {size}"
        self._run_operation(
            lambda: self.engine.quick_format(disk, fs=fs, label=label),
            message,
            refresh_on_success=True,
        )

    def _submit_partition(self):
        disk = self.get_selected_disk()
        if not disk or not self._validate("create_partition", disk):
            return
        self._run_operation(
            lambda: self.engine.create_partition(disk),
            "✓  Partition complete — A new primary NTFS partition is ready",
            refresh_on_success=True,
        )

    def _submit_boot(self):
        disk = self.get_selected_disk()
        if not disk or not self._validate("format", disk):
            return
        if not self.iso_path:
            dialogs.show_error(self, "ISO Required", "Choose an ISO file before flashing.")
            return
        if not dialogs.confirm_destructive(self, disk, "Make Bootable USB"):
            return
        self._run_operation(
            lambda: self.engine.make_bootable(disk, self.iso_path),
            "✓  Bootable USB complete — Media is ready to use",
            refresh_on_success=True,
        )

    def _submit_convert(self):
        disk = self.get_selected_disk()
        if not disk or not self._validate("convert", disk):
            return
        target = "GPT" if (disk.partition_style or "").upper() == "MBR" else "MBR"
        if not dialogs.confirm_destructive(self, disk, f"Convert to {target}"):
            return
        runner = self.engine.convert_gpt if target == "GPT" else self.engine.convert_mbr
        self._run_operation(
            lambda: runner(disk),
            f"✓  Conversion complete — Disk style is now {target}",
            refresh_on_success=True,
        )

    def _submit_assign(self):
        disk = self.get_selected_disk()
        if not disk or not self._validate("assign", disk):
            return
        letter = self.letter_entry.get().strip().upper()
        if len(letter) != 1 or not letter.isalpha():
            dialogs.show_error(self, "Invalid Letter", "Enter a single letter A-Z.")
            return
        self._run_operation(
            lambda: self.engine.assign_letter(disk, letter),
            f"✓  Letter assigned — Drive is now {letter}:\\",
            refresh_on_success=True,
        )
