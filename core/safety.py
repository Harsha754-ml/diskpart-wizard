# core/safety.py
# The single source of truth for all safety decisions.
# All destructive operations MUST call validate_operation() first.
# This module never executes anything - it only validates.

from typing import Tuple
from core.disk_info import DiskInfo


class SafetyError(Exception):
    """Raised when an operation is blocked for safety reasons."""


DESTRUCTIVE_OPS = {"clean", "format", "convert", "create_partition"}


def validate_operation(op: str, disk: DiskInfo) -> Tuple[bool, str]:
    """
    Returns (allowed: bool, reason: str).

    Rules (in order, first match wins):
    1. disk.index == 0  -> BLOCKED. "Disk 0 is your system drive. This operation is permanently blocked."
    2. disk.is_system_disk -> BLOCKED (same message)
    3. op in DESTRUCTIVE_OPS and not disk.is_removable -> WARN. Return (True, warning_message)
    4. disk.status != "Online" -> BLOCKED. "Disk is not online."
    5. All other cases -> (True, "")
    """
    normalized = op.strip().lower()
    if disk.index == 0:
        return (
            False,
            "Disk 0 is your system drive. This operation is permanently blocked.",
        )
    if disk.is_system_disk:
        return (
            False,
            "Disk 0 is your system drive. This operation is permanently blocked.",
        )
    if normalized in DESTRUCTIVE_OPS and not disk.is_removable:
        return (
            True,
            "Warning: This disk is not marked as removable. Proceed only if you are sure.",
        )
    if disk.status != "Online":
        return (False, "Disk is not online.")
    return (True, "")


def require_double_confirmation(disk: DiskInfo, op: str) -> bool:
    """
    Returns True if this operation requires the "I understand this will erase all data"
    checkbox confirmation dialog before proceeding.
    Always True for: clean, format, convert.
    False for: assign, create_partition (non-destructive).
    """
    normalized = op.strip().lower()
    if normalized in {"clean", "format", "convert"}:
        return True
    if normalized in {"assign", "create_partition"}:
        return False
    return normalized in {"clean_disk", "quick_format", "convert_mbr", "convert_gpt"}
