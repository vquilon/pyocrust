"""Habilitar en runtime el execution provider CUDA de ``pyocrust``.

``onnxruntime_providers_cuda.dll`` (el provider que ONNX Runtime carga aparte)
importa ``cublas64_13.dll`` y ``cublasLt64_13.dll``. Esas DLL **están** en el
entorno (las trae ``nvidia-cublas-cu13`` o ``torch``), pero en directorios que el
proceso no mira: desde Python 3.8 ``LoadLibrary`` **ignora ``PATH``** en Windows.

``enable_cuda()`` añade esos directorios al *search path* (``os.add_dll_directory``)
de forma *best-effort* e idempotente, sin descargar ni instalar nada, y devuelve
los EPs que registran. En Linux/macOS el cargador respeta ``RPATH``/``LD_LIBRARY_PATH``,
así que allí es un no-op.

Uso (antes de construir el motor, ver ``GPU.md``)::

    import pyocrust
    pyocrust.enable_cuda()                       # -> ['cuda', 'directml'] p.ej.
    ocr = pyocrust.VeloceOCR("pp_ocrv6", device="cuda")
"""
from __future__ import annotations

import os
import site
from pathlib import Path

_HERE = Path(__file__).resolve().parent  # el provider puede viajar junto al .pyd


def _candidate_dirs() -> list[Path]:
    """Directorios donde puede vivir el runtime CUDA, en orden de preferencia."""
    dirs: list[Path] = [_HERE]
    for key in ("CUDA_PATH", "CUDA_HOME"):
        if (venv := os.environ.get(key)):
            dirs += [Path(venv) / "bin", Path(venv) / "bin" / "x86_64"]
    bases = {*site.getsitepackages(), site.getusersitepackages()}
    for base in bases:
        b = Path(base)
        dirs += sorted(b.glob("nvidia/*/bin*"))  # nvidia-cublas-cu13, nvidia-cudnn-cu13…
        dirs.append(b / "torch" / "lib")         # torch trae cublas/cudnn/cudart
    return [d for d in dirs if d.is_dir()]


def enable_cuda() -> list[str]:
    """Añade al search path las DLL del runtime CUDA presentes en el entorno.

    Best-effort e idempotente: un directorio que no exista o no se deje abrir se
    ignora. Devuelve ``available_providers()`` tras intentarlo, para que el
    llamante compruebe si ``'cuda'`` quedó registrado.
    """
    if hasattr(os, "add_dll_directory"):  # solo Windows
        for d in _candidate_dirs():
            try:
                os.add_dll_directory(str(d))
            except OSError:
                pass  # ponytail: se ignora el fallo; el diagnóstico lo da available_providers()
    from pyocrust import available_providers

    return available_providers()
