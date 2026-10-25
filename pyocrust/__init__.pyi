"""Stubs de tipos de pyocrust (tarjeta `I1`).

El módulo nativo ``pyocrust._pyocrust_core`` se declara entero: el contrato
PyO3 (clases ``OcrResult``, ``TextRegion``, ``VeloceOCR``...) llega con las
tarjetas ``I2``-``I4`` y se documenta aquí cuando exista.
"""

from __future__ import annotations

from typing import Sequence

__version__: str

class BoundingBox:
    x1: float
    y1: float
    x2: float
    y2: float
    def __init__(self, x1: float, y1: float, x2: float, y2: float) -> None: ...
    @property
    def width(self) -> float: ...
    @property
    def height(self) -> float: ...

class TextRegion:
    text: str
    confidence: float
    box: BoundingBox
    def __init__(self, text: str, confidence: float, box: BoundingBox) -> None: ...

class OcrResult:
    regions: Sequence[TextRegion]
    def __init__(self, regions: Sequence[TextRegion]) -> None: ...
    @property
    def text(self) -> str: ...
    @property
    def confidence(self) -> float: ...
    def __len__(self) -> int: ...

class PyOcrError(Exception): ...
class PyOcrValueError(ValueError, PyOcrError): ...
class PyOcrRuntimeError(RuntimeError, PyOcrError): ...

def resolve_models_dir(custom_path: str | None = None) -> str: ...

class VeloceOCR:
    def __init__(self, preset: str = "pp_ocrv6", custom_path: str | None = None) -> None: ...
    @property
    def models_dir(self) -> str: ...
    def recognize(self, image: str | bytes) -> OcrResult: ...

__all__: list[str] = [
    "__version__",
    "BoundingBox",
    "OcrResult",
    "PyOcrError",
    "PyOcrRuntimeError",
    "PyOcrValueError",
    "TextRegion",
    "VeloceOCR",
    "resolve_models_dir",
]
