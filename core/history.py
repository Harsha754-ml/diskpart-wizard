# core/history.py
# Append-only JSON log of all operations attempted (success or failure).
# Stored at %APPDATA%\DiskWizard\history.json
# Max 500 entries - oldest pruned on overflow.

import json
import os
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List

HISTORY_FILE = os.path.join(os.getenv("APPDATA", "."), "DiskWizard", "history.json")
MAX_ENTRIES = 500


@dataclass
class HistoryEntry:
    timestamp: str
    operation: str
    disk_index: int
    disk_model: str
    status: str  # "success" | "failed" | "cancelled"
    script: str
    error_msg: str = ""


def _ensure_dir():
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)


def load_all() -> List[HistoryEntry]:
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return [HistoryEntry(**item) for item in raw]
    except Exception:
        return []


def append(entry: HistoryEntry):
    _ensure_dir()
    entries = load_all()
    entries.append(entry)
    if len(entries) > MAX_ENTRIES:
        entries = entries[-MAX_ENTRIES:]

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump([asdict(e) for e in entries], f, indent=2)


def export_to_txt(path: str):
    entries = load_all()
    lines = []
    for e in entries:
        lines.append(
            f"[{e.timestamp}] {e.operation} | Disk {e.disk_index} | {e.disk_model} | {e.status}"
        )
        if e.error_msg:
            lines.append(f"  Error: {e.error_msg}")
        lines.append("  Script:")
        for line in e.script.splitlines():
            lines.append(f"    {line}")
        lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
