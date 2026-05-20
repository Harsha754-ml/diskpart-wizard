# core/diskpart.py
# Builds and executes DiskPart scripts.
# NEVER runs diskpart directly with inline commands - always via script file.
# This gives us an audit trail and prevents injection.

import os
import subprocess
import tempfile
import time
from datetime import datetime
from typing import Callable, Optional

from core.disk_info import DiskInfo, get_all_disks
from core.safety import validate_operation, SafetyError
from core.history import HistoryEntry, append
from utils.shell_suppress import (
    restore_shell_notification,
    suppress_autoplay_for_drive,
)


class DiskPartEngine:
    """
    Builds DiskPart .txt scripts, validates them, and executes them.
    Streams output line-by-line via a callback for live terminal display.
    """

    def __init__(
        self,
        output_callback: Callable[[str, str], None],
        on_complete_callback: Optional[Callable[[bool], None]] = None,
    ):
        """
        output_callback(line: str, level: str) - called for each output line.
        level: "info" | "success" | "error" | "warning" | "cmd"
        """
        self.output_callback = output_callback
        self.on_complete_callback = on_complete_callback
        self._current_script_path: Optional[str] = None

    def build_script(self, disk_index: int, operations: list[str]) -> str:
        """
        Builds a DiskPart script string.
        Always starts with `select disk N`.
        operations: list of raw DiskPart command strings.
        """
        normalized_ops: list[str] = []
        partition_selected = False
        pending_partition_select = False
        for op in operations:
            clean_op = op.strip()
            lowered = clean_op.lower()
            if lowered == "create partition primary":
                normalized_ops.append(clean_op)
                partition_selected = False
                pending_partition_select = True
                continue
            if lowered.startswith("select partition"):
                partition_selected = True
                pending_partition_select = False
            if (
                pending_partition_select
                and not partition_selected
                and (lowered.startswith("format") or lowered.startswith("assign"))
            ):
                normalized_ops.append("select partition 1")
                partition_selected = True
                pending_partition_select = False
            normalized_ops.append(clean_op)

        lines = [f"select disk {disk_index}"] + normalized_ops + ["exit"]
        return "\n".join(lines)

    def execute(self, script: str, disk: DiskInfo, op_name: str) -> bool:
        """
        1. Validates via safety.validate_operation().
        2. Writes script to a named temp file.
        3. Runs `diskpart /s <tempfile>` via subprocess.
        4. Streams stdout line-by-line to output_callback.
        5. Deletes temp file on completion.
        6. Returns True on success, False on failure.
        """
        allowed, reason = validate_operation(op_name, disk)
        status = "failed"
        error_msg = ""
        if not allowed:
            self.output_callback(reason, "error")
            status = "cancelled"
            error_msg = reason
            append(
                HistoryEntry(
                    timestamp=datetime.utcnow().isoformat(),
                    operation=op_name,
                    disk_index=disk.index,
                    disk_model=disk.model,
                    status=status,
                    script=script,
                    error_msg=error_msg,
                )
            )
            raise SafetyError(reason)
        if reason:
            self.output_callback(reason, "warning")

        expected = f"select disk {int(disk.index)}"
        script_lines = [l.strip() for l in script.splitlines() if l.strip()]
        if not script_lines or script_lines[0].lower() != expected.lower():
            msg = "Safety check failed: script disk index mismatch."
            self.output_callback(msg, "error")
            raise SafetyError(msg)

        tmp_path = None
        original_letter = disk.drive_letter.rstrip("\\") if disk.drive_letter else None
        try:
            if original_letter:
                self.output_callback(
                    f"> dismounting {original_letter}\\ before operation...", "cmd"
                )
                suppress_autoplay_for_drive(original_letter)
                subprocess.run(
                    ["mountvol", f"{original_letter}\\", "/p"],
                    capture_output=True,
                    shell=False,
                )
                time.sleep(0.8)

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False, encoding="utf-8"
            ) as tmp:
                tmp.write(script)
                tmp_path = tmp.name
                self._current_script_path = tmp_path

            for line in script_lines:
                self.output_callback(f"> {line}", "cmd")

            proc = subprocess.Popen(
                ["diskpart", "/s", tmp_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            self._stream_output(proc)
            exit_code = proc.wait()
            if exit_code == 0:
                self.output_callback("DiskPart completed successfully.", "success")
                status = "success"
                append(
                    HistoryEntry(
                        timestamp=datetime.utcnow().isoformat(),
                        operation=op_name,
                        disk_index=disk.index,
                        disk_model=disk.model,
                        status=status,
                        script=script,
                        error_msg=error_msg,
                    )
                )
                self._notify_complete(True)
                return True

            self.output_callback(
                f"DiskPart exited with code {exit_code}.", "error"
            )
            error_msg = f"DiskPart exited with code {exit_code}."
            append(
                HistoryEntry(
                    timestamp=datetime.utcnow().isoformat(),
                    operation=op_name,
                    disk_index=disk.index,
                    disk_model=disk.model,
                    status=status,
                    script=script,
                    error_msg=error_msg,
                )
            )
            self._notify_complete(False)
            return False
        except SafetyError:
            return False
        except Exception as exc:
            self.output_callback(f"DiskPart failed: {exc}", "error")
            error_msg = str(exc)
            append(
                HistoryEntry(
                    timestamp=datetime.utcnow().isoformat(),
                    operation=op_name,
                    disk_index=disk.index,
                    disk_model=disk.model,
                    status=status,
                    script=script,
                    error_msg=error_msg,
                )
            )
            self._notify_complete(False)
            return False
        finally:
            restore_letter = self._resolve_restore_letter(disk, original_letter)
            if restore_letter:
                try:
                    restore_shell_notification(restore_letter)
                except Exception:
                    pass
            self._current_script_path = None
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

    def _resolve_restore_letter(
        self, disk: DiskInfo, original_letter: Optional[str]
    ) -> Optional[str]:
        try:
            for refreshed_disk in get_all_disks():
                if refreshed_disk.index == disk.index and refreshed_disk.drive_letter:
                    return refreshed_disk.drive_letter.rstrip("\\")
        except Exception:
            pass
        return original_letter

    def _notify_complete(self, success: bool):
        if self.on_complete_callback is None:
            return
        try:
            self.on_complete_callback(success)
        except Exception:
            pass

    def _stream_output(self, proc: subprocess.Popen):
        """Reads stdout in real time and calls output_callback per line."""
        if not proc.stdout:
            return
        for line in proc.stdout:
            clean = line.rstrip()
            level = self._infer_level(clean)
            if clean:
                self.output_callback(clean, level)

    def _infer_level(self, line: str) -> str:
        lowered = line.lower()
        if "error" in lowered or "failed" in lowered:
            return "error"
        if "warning" in lowered:
            return "warning"
        if "success" in lowered or "completed" in lowered:
            return "success"
        return "info"

    # --- Pre-built operation factories ---

    def clean_disk(self, disk: DiskInfo) -> bool:
        script = self.build_script(disk.index, ["clean"])
        return self.execute(script, disk, "clean")

    def quick_format(self, disk: DiskInfo, fs: str = "ntfs", label: str = "") -> bool:
        label_cmd = f'label="{label}"' if label else ""
        script = self.build_script(
            disk.index,
            [
                "clean",
                "create partition primary",
                f"format fs={fs} quick {label_cmd}".strip(),
                "assign",
            ],
        )
        return self.execute(script, disk, "format")

    def create_partition(self, disk: DiskInfo) -> bool:
        script = self.build_script(
            disk.index, ["create partition primary", "format fs=ntfs quick", "assign"]
        )
        return self.execute(script, disk, "create_partition")

    def assign_letter(self, disk: DiskInfo, letter: str) -> bool:
        script = self.build_script(
            disk.index, ["select partition 1", f"assign letter={letter}"]
        )
        return self.execute(script, disk, "assign")

    def convert_mbr(self, disk: DiskInfo) -> bool:
        script = self.build_script(disk.index, ["clean", "convert mbr"])
        return self.execute(script, disk, "convert")

    def convert_gpt(self, disk: DiskInfo) -> bool:
        script = self.build_script(disk.index, ["clean", "convert gpt"])
        return self.execute(script, disk, "convert")

    def make_bootable(self, disk: DiskInfo, iso_path: str) -> bool:
        """
        1. Clean + format FAT32 + active partition via DiskPart.
        2. Mount ISO via PowerShell Mount-DiskImage.
        3. xcopy ISO contents to drive letter.
        4. Unmount ISO.
        """
        if not os.path.exists(iso_path):
            self.output_callback("ISO path not found.", "error")
            return False

        operations = ["clean"]
        if (disk.partition_style or "").upper() != "MBR":
            operations.append("convert mbr")
        operations.extend(
            [
                "create partition primary",
                "format fs=fat32 quick",
                "active",
                "assign",
            ]
        )
        script = self.build_script(disk.index, operations)
        if not self.execute(script, disk, "format"):
            return False

        target_letter = None
        for d in get_all_disks():
            if d.index == disk.index and d.drive_letter:
                target_letter = d.drive_letter
                break

        if not target_letter:
            self.output_callback("Failed to resolve target drive letter.", "error")
            return False

        mount_cmd = (
            "Mount-DiskImage -ImagePath "
            f'"{iso_path}" -PassThru | '
            "Get-Volume | Select-Object -ExpandProperty DriveLetter"
        )
        self.output_callback(f"> powershell {mount_cmd}", "cmd")
        try:
            mount = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command", mount_cmd],
                text=True,
                stderr=subprocess.STDOUT,
            )
            iso_letter = mount.strip().splitlines()[-1].strip()
            if not iso_letter:
                raise RuntimeError("ISO mount returned no drive letter.")
        except Exception as exc:
            self.output_callback(f"ISO mount failed: {exc}", "error")
            return False

        xcopy_cmd = [
            "xcopy",
            f"{iso_letter}:\\*",
            f"{target_letter}\\",
            "/E",
            "/F",
            "/H",
            "/Y",
        ]
        self.output_callback(f"> {' '.join(xcopy_cmd)}", "cmd")
        try:
            proc = subprocess.Popen(
                xcopy_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            self._stream_output(proc)
            code = proc.wait()
            if code != 0:
                self.output_callback(f"xcopy exited with code {code}.", "error")
                return False
        except Exception as exc:
            self.output_callback(f"xcopy failed: {exc}", "error")
            return False
        finally:
            dismount_cmd = (
                f'Dismount-DiskImage -ImagePath "{iso_path}"'
            )
            self.output_callback(f"> powershell {dismount_cmd}", "cmd")
            try:
                subprocess.check_output(
                    ["powershell", "-NoProfile", "-Command", dismount_cmd],
                    text=True,
                    stderr=subprocess.STDOUT,
                )
            except Exception:
                pass

        self.output_callback("Bootable USB creation completed.", "success")
        return True
