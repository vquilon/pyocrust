"""Hardware discovery using only stdlib; unknown memory stays None.

A detected GPU is physical inventory, not proof that the native wheel supports
CUDA. CUDA_VISIBLE_DEVICES filters inventory; it never fabricates a GPU.
"""
from __future__ import annotations

import csv
import ctypes
from dataclasses import dataclass
import os
import shutil
import subprocess
import sys


@dataclass(frozen=True)
class GpuInfo:
    name: str | None = None
    vram_bytes: int | None = None

    def __post_init__(self):
        if self.vram_bytes is not None and (type(self.vram_bytes) is not int or self.vram_bytes <= 0):
            raise ValueError("vram_bytes must be a positive integer or None")


@dataclass(frozen=True)
class HardwareProfile:
    cpu_count: int
    ram_bytes: int | None
    gpu: GpuInfo | None = None

    def __post_init__(self):
        if type(self.cpu_count) is not int or self.cpu_count < 1:
            raise ValueError("cpu_count must be a positive integer")
        if self.ram_bytes is not None and (type(self.ram_bytes) is not int or self.ram_bytes <= 0):
            raise ValueError("ram_bytes must be a positive integer or None")
        if self.gpu is not None and not isinstance(self.gpu, GpuInfo):
            raise TypeError("gpu must be GpuInfo or None")


def _ram_bytes() -> int | None:
    try:
        if sys.platform.startswith("win"):
            from ctypes import wintypes

            class MemoryStatus(ctypes.Structure):
                _fields_ = [("length", wintypes.DWORD), ("load", wintypes.DWORD)] + [
                    (name, ctypes.c_ulonglong) for name in (
                        "total_phys", "avail_phys", "total_page_file", "avail_page_file",
                        "total_virtual", "avail_virtual", "avail_extended_virtual",
                    )
                ]

            status = MemoryStatus()
            status.length = ctypes.sizeof(status)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                return int(status.total_phys) or None
        elif sys.platform == "darwin":
            result = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, timeout=2, check=True)
            total = int(result.stdout.strip())
            return total if total > 0 else None
        else:
            pages, page_size = os.sysconf("SC_PHYS_PAGES"), os.sysconf("SC_PAGE_SIZE")
            return int(pages * page_size) if pages > 0 and page_size > 0 else None
    except (AttributeError, ValueError, OSError, subprocess.SubprocessError):
        pass
    return None


def _gpu() -> GpuInfo | None:
    visible = os.environ.get("CUDA_VISIBLE_DEVICES")
    if visible is not None and visible.strip() in ("", "-1"):
        return None
    executable = shutil.which("nvidia-smi")
    if not executable:
        return None
    try:
        result = subprocess.run(
            [executable, "--query-gpu=index,uuid,name,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=2, check=True,
        )
        rows = [row for row in csv.reader(result.stdout.splitlines(), skipinitialspace=True) if len(row) == 4]
        if visible is not None:
            selected = []
            for device in visible.split(","):
                device = device.strip()
                if device.isascii() and device.isdigit():
                    matches = [row for row in rows if row[0].strip() == device]
                elif device.startswith("GPU-") and len(device) > 4:
                    matches = [row for row in rows if row[1].strip().startswith(device)]
                else:
                    break
                # CUDA stops at an invalid/ambiguous or repeated identifier.
                if len(matches) != 1 or matches[0] in selected:
                    break
                selected.append(matches[0])
            rows = selected
        for row in rows:
            if len(row) == 4:
                try:
                    memory = int(row[3].strip()) * 1024**2
                    if memory <= 0:
                        memory = None
                except ValueError:
                    memory = None
                return GpuInfo(name=row[2].strip(), vram_bytes=memory)
    except (ValueError, OSError, subprocess.SubprocessError):
        pass
    return None


def detect_hardware() -> HardwareProfile:
    """Return host inventory without importing inference libraries or loading models.

    Use HardwareProfile directly for overrides; resolve_pipeline never detects
    hardware when an explicit profile is supplied.
    """
    return HardwareProfile(cpu_count=os.cpu_count() or 1, ram_bytes=_ram_bytes(), gpu=_gpu())
