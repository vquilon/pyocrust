"""Stubs de tipos de pyocrust.

Refleja el contrato PyO3 real: ``VeloceOCR.recognize`` devuelve ``OcrResult``
en los presets de texto (``pp_ocrv6*``) y ``StructureResult`` en
``pp_structurev3`` (ADR-003).
"""

from __future__ import annotations

from os import PathLike
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

class LayoutRegion:
    """Elemento de layout de PP-StructureV3; en ``formula``, ``text`` es LaTeX."""

    kind: str
    text: str
    confidence: float
    box: BoundingBox
    def __init__(
        self, kind: str, text: str, confidence: float, box: BoundingBox
    ) -> None: ...

class StructureResult:
    """Salida de PP-StructureV3: estructura documental sin aplanar (ADR-003)."""

    elements: Sequence[LayoutRegion]
    regions: Sequence[TextRegion]
    def to_markdown(self) -> str: ...
    def __len__(self) -> int: ...

class PyOcrError(Exception): ...
class PyOcrValueError(PyOcrError): ...
class PyOcrRuntimeError(PyOcrError): ...

def resolve_models_dir(custom_path: str | None = None) -> str: ...

def models_status(
    custom_path: str | None = None,
) -> dict[str, object]:
    """Estado de los modelos en disco: `models_dir`, `offline`, `presets`, `indra`."""

class VeloceOCR:
    def __init__(self, preset: str = "pp_ocrv6", custom_path: str | None = None) -> None: ...
    @property
    def models_dir(self) -> str: ...
    def recognize(
        self, image: str | bytes | PathLike[str]
    ) -> OcrResult | StructureResult: ...

__all__: list[str] = [
    "__version__",
    "BoundingBox",
    "LayoutRegion",
    "OcrResult",
    "PyOcrError",
    "PyOcrRuntimeError",
    "PyOcrValueError",
    "StructureResult",
    "TextRegion",
    "VeloceOCR",
    "resolve_models_dir",
    "models_status",
]
