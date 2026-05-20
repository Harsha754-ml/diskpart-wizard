# core/disk_info.py
# Detects all connected disks using Windows WMI.
# Falls back to wmic output or psutil disk_partitions() if WMI unavailable.
# Returns List[DiskInfo] - one entry per physical disk where possible.

from dataclasses import dataclass
from typing import Optional, List, Dict
import subprocess


@dataclass
class DiskInfo:
    index: int
    size_gb: float
    model: str
    is_removable: bool
    is_system_disk: bool
    filesystem: Optional[str]
    drive_letter: Optional[str]
    partition_style: Optional[str]
    status: str


def get_all_disks() -> List[DiskInfo]:
    """
    Primary: query WMI Win32_DiskDrive + Win32_LogicalDisk.
    Fallback: parse `wmic diskdrive list full /format:list` subprocess output.
    If both fail, return a best-effort list from psutil disk_partitions().
    Always marks index=0 as is_system_disk=True regardless of any other signal.
    """
    try:
        import wmi

        c = wmi.WMI()
        disks = c.Win32_DiskDrive()

        msft_disks: Dict[int, object] = {}
        try:
            storage = wmi.WMI(namespace="root\\Microsoft\\Windows\\Storage")
            msft_disks = {int(d.Number): d for d in storage.MSFT_Disk()}
        except Exception:
            msft_disks = {}

        results: List[DiskInfo] = []
        for d in disks:
            index = int(d.Index)
            size_gb = round(int(d.Size) / (1024**3), 2) if d.Size else 0.0
            model = (d.Model or d.Caption or "Unknown").strip()

            is_removable = False
            if d.MediaType and "Removable" in d.MediaType:
                is_removable = True
            if d.InterfaceType and d.InterfaceType.upper() == "USB":
                is_removable = True

            filesystem = None
            drive_letter = None
            try:
                for partition in d.associators("Win32_DiskDriveToDiskPartition"):
                    for logical in partition.associators("Win32_LogicalDiskToPartition"):
                        drive_letter = logical.DeviceID
                        filesystem = logical.FileSystem
                        if drive_letter:
                            break
                    if drive_letter:
                        break
            except Exception:
                pass

            partition_style = None
            status = d.Status or "Unknown"
            if index in msft_disks:
                msft = msft_disks[index]
                try:
                    style = int(msft.PartitionStyle)
                    partition_style = {1: "MBR", 2: "GPT", 3: "RAW"}.get(style)
                except Exception:
                    pass
                try:
                    status = "Offline" if bool(msft.IsOffline) else "Online"
                except Exception:
                    pass

            results.append(
                DiskInfo(
                    index=index,
                    size_gb=size_gb,
                    model=model,
                    is_removable=is_removable,
                    is_system_disk=index == 0,
                    filesystem=filesystem,
                    drive_letter=drive_letter,
                    partition_style=partition_style,
                    status=status,
                )
            )

        return results
    except Exception:
        pass

    try:
        raw = subprocess.check_output(
            ["wmic", "diskdrive", "list", "full", "/format:list"],
            text=True,
            stderr=subprocess.STDOUT,
        )
        parsed = _parse_wmic_output(raw)
        if parsed:
            return parsed
    except Exception:
        pass

    return _fallback_psutil()


def _fallback_psutil() -> List[DiskInfo]:
    import psutil

    results: List[DiskInfo] = []
    index = 0
    for part in psutil.disk_partitions(all=False):
        size_gb = 0.0
        try:
            usage = psutil.disk_usage(part.mountpoint)
            size_gb = round(usage.total / (1024**3), 2)
        except Exception:
            pass

        drive_letter = None
        if part.device:
            drive_letter = part.device.split("\\")[0]

        results.append(
            DiskInfo(
                index=index,
                size_gb=size_gb,
                model=part.device or "Unknown",
                is_removable=False,
                is_system_disk=index == 0,
                filesystem=part.fstype or None,
                drive_letter=drive_letter,
                partition_style=None,
                status="Online",
            )
        )
        index += 1

    return results


def _parse_wmic_output(raw: str) -> List[DiskInfo]:
    """Parse wmic diskdrive list full /format:list output into DiskInfo objects."""
    blocks = [b for b in raw.replace("\r", "").split("\n\n") if b.strip()]
    results: List[DiskInfo] = []

    for block in blocks:
        data: Dict[str, str] = {}
        for line in block.split("\n"):
            if "=" in line:
                key, value = line.split("=", 1)
                data[key.strip()] = value.strip()

        if "Index" not in data:
            continue

        try:
            index = int(data.get("Index", "-1"))
        except ValueError:
            continue

        model = data.get("Model") or data.get("Caption") or "Unknown"
        size_gb = 0.0
        if data.get("Size"):
            try:
                size_gb = round(int(data["Size"]) / (1024**3), 2)
            except Exception:
                size_gb = 0.0

        media_type = data.get("MediaType", "")
        interface_type = data.get("InterfaceType", "")
        is_removable = ("Removable" in media_type) or (interface_type.upper() == "USB")

        results.append(
            DiskInfo(
                index=index,
                size_gb=size_gb,
                model=model.strip(),
                is_removable=is_removable,
                is_system_disk=index == 0,
                filesystem=None,
                drive_letter=None,
                partition_style=None,
                status=data.get("Status", "Unknown"),
            )
        )

    return results
