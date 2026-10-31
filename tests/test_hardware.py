"""Detección de hardware (S3.1) contrastada con el host real.

Tarjeta `S3.2`. `detect_hardware()` no puede inventar: `cpu_count` debe ser el
del host y `ram_bytes` una memoria física real; además `HardwareProfile` debe
aceptar un override explícito que manda sobre la detección.

Ejecución: `python -m pytest tests/ -q`
"""

from __future__ import annotations

import inspect
import os
import sys

import pytest

import pyocrust

GIB = 1024**3


def _ram_total_host() -> int | None:
    """Memoria física total del host, por la vía nativa de cada plataforma."""
    if sys.platform.startswith("win"):
        import ctypes
        from ctypes import wintypes

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", wintypes.DWORD),
                ("dwMemoryLoad", wintypes.DWORD),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        estado = MEMORYSTATUSEX()
        estado.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(estado)):
            return int(estado.ullTotalPhys)
        return None
    try:
        return os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE")
    except (ValueError, OSError, AttributeError):
        return None


def test_detect_hardware_devuelve_el_perfil_del_host():
    perfil = pyocrust.detect_hardware()
    assert isinstance(perfil, pyocrust.HardwareProfile), (
        f"detect_hardware() devolvió {type(perfil).__name__}, no un HardwareProfile"
    )
    assert isinstance(perfil.cpu_count, int) and perfil.cpu_count >= 1, (
        f"cpu_count debe ser int >= 1, es {perfil.cpu_count!r}"
    )
    host_cpus = os.cpu_count()
    if host_cpus is not None:
        assert perfil.cpu_count == host_cpus, (
            f"cpu_count={perfil.cpu_count} no coincide con os.cpu_count()={host_cpus}"
        )
    assert isinstance(perfil.ram_bytes, int) and perfil.ram_bytes > 0, (
        f"ram_bytes debe ser int > 0, es {perfil.ram_bytes!r}"
    )
    total = _ram_total_host()
    if total:
        assert total // 4 <= perfil.ram_bytes <= total + total // 20, (
            f"ram_bytes={perfil.ram_bytes} no es coherente con la RAM del host ({total})"
        )


def test_hardware_profile_acepta_override_explicito():
    """El override se escribe tal cual, sin que la detección lo pise."""
    perfil = pyocrust.HardwareProfile(cpu_count=3, ram_bytes=8 * GIB)
    assert perfil.cpu_count == 3, f"cpu_count={perfil.cpu_count}, se pidió 3"
    assert perfil.ram_bytes == 8 * GIB, f"ram_bytes={perfil.ram_bytes}, se pidió {8 * GIB}"


def test_detect_hardware_acepta_override_si_lo_expone():
    """Si `detect_hardware` acepta overrides, también deben mandar sobre la detección."""
    parametros = set(inspect.signature(pyocrust.detect_hardware).parameters)
    soportados = {"cpu_count", "ram_bytes"} & parametros
    if not soportados:
        pytest.skip(
            "detect_hardware() no expone overrides; el override explícito se hace por "
            "HardwareProfile(...), cubierto por test_hardware_profile_acepta_override_explicito"
        )
    perfil = pyocrust.detect_hardware(cpu_count=3, ram_bytes=8 * GIB)
    assert perfil.cpu_count == 3, f"el override de cpu_count no se aplicó: {perfil.cpu_count}"
    assert perfil.ram_bytes == 8 * GIB, f"el override de ram_bytes no se aplicó: {perfil.ram_bytes}"


def test_ram_desconocida_se_conserva(monkeypatch):
    import pyocrust.hardware as modulo

    monkeypatch.setattr(modulo, "_ram_bytes", lambda: None)
    monkeypatch.setattr(modulo, "_gpu", lambda: None)
    assert pyocrust.detect_hardware().ram_bytes is None


@pytest.mark.parametrize("mascara", ["", "-1", "1", "GPU-b", ",", "GPU-", "9,0", "GPU-a"])
def test_mascara_gpu_filtra_inventario(monkeypatch, mascara):
    import pyocrust.hardware as modulo
    from types import SimpleNamespace

    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", mascara)
    monkeypatch.setattr(modulo.shutil, "which", lambda _: "nvidia-smi")

    def inventario(*args, **kwargs):
        assert mascara not in ("", "-1"), "una máscara deshabilitada no debe consultar GPUs"
        return SimpleNamespace(stdout="0, GPU-aa, primera, 4096\n1, GPU-b, segunda, 8192\n2, GPU-ab, tercera, 4096\n")

    monkeypatch.setattr(modulo.subprocess, "run", inventario)
    gpu = modulo._gpu()
    if mascara in ("1", "GPU-b"):
        assert gpu == pyocrust.GpuInfo(name="segunda", vram_bytes=8 * GIB)
    else:
        assert gpu is None


@pytest.mark.parametrize("pages,page_size", [(-1, 4096), (1, -1), (-1, -1)])
def test_ram_sysconf_negativo_es_desconocida(monkeypatch, pages, page_size):
    import pyocrust.hardware as modulo

    monkeypatch.setattr(modulo.sys, "platform", "linux")
    valores = {"SC_PHYS_PAGES": pages, "SC_PAGE_SIZE": page_size}
    monkeypatch.setattr(modulo.os, "sysconf", valores.__getitem__, raising=False)
    assert modulo._ram_bytes() is None


def test_gpu_memoria_cero_conserva_nombre(monkeypatch):
    import pyocrust.hardware as modulo
    from types import SimpleNamespace

    monkeypatch.delenv("CUDA_VISIBLE_DEVICES", raising=False)
    monkeypatch.setattr(modulo.shutil, "which", lambda _: "nvidia-smi")
    monkeypatch.setattr(modulo.subprocess, "run", lambda *a, **kw: SimpleNamespace(stdout="0, GPU-a, primera, 0\n"))
    assert modulo._gpu() == pyocrust.GpuInfo(name="primera", vram_bytes=None)
