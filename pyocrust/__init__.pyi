"""Stubs de tipos de pyocrust.

Refleja el contrato PyO3 real: ``VeloceOCR.recognize`` devuelve ``OcrResult``
en los presets de texto (``pp_ocrv6*``) y ``StructureResult`` en
``pp_structurev3`` (ADR-003) e ``indra`` (S2.2 parcial): tres familias de presets.
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
    """Elemento de PP-StructureV3 o Indra; en ``formula``, ``text`` es LaTeX.

    En bloques Indra, ``confidence=0.0`` indica score no disponible.
    """

    kind: str
    text: str
    confidence: float
    box: BoundingBox
    def __init__(
        self, kind: str, text: str, confidence: float, box: BoundingBox
    ) -> None: ...

class StructureResult:
    """Salida de PP-StructureV3 o Indra, sin aplanar (ADR-003).

    Indra conserva LaTeX inline en Markdown/regiones; ``formulas=[]`` indica
    ausencia de registros separados, no ausencia de matemáticas.
    """

    elements: Sequence[LayoutRegion]
    regions: Sequence[TextRegion]
    def to_markdown(self) -> str: ...
    formulas: Sequence[str]
    def __len__(self) -> int: ...

class PyOcrError(Exception): ...
class PyOcrValueError(PyOcrError): ...
class PyOcrRuntimeError(PyOcrError): ...

class TaskPredictor:
    """One ``oar-ocr`` task predictor; each schema lists all returned keys.

    ``document_orientation`` returns ``{"orientations": list[dict]}``, where
    each item has ``class_id: int``, ``label: str`` and ``score: float``.
    ``text_line_orientation`` returns the same schema.

    ``document_rectification`` returns ``{"image": bytes, "width": int,
    "height": int}``; ``image`` contains PNG-encoded image data.

    ``seal_text_detection`` returns ``{"detections": list[dict]}``, where
    each item has ``bbox: list[list[float]]`` (four [x, y] points) and
    ``score: float``.

    ``formula_recognition`` returns ``{"formula": str, "score": float | None}``.
    The score is ``None`` when the underlying result has no score.
    """
    def __init__(self, task: str, models: str | dict[str, str] | None = None, **options: object) -> None: ...
    def predict(self, image: str | bytes | PathLike[str]) -> dict[str, object]: ...
    def predict_batch(self, images: Sequence[str | bytes | PathLike[str]]) -> list[dict[str, object]]: ...

def resolve_models_dir(custom_path: str | None = None) -> str: ...

def models_status(
    custom_path: str | None = None,
) -> dict[str, object]:
    """Estado en disco: ``models_dir``, ``offline``, ``presets``, ``indra``.

    ``['indra']`` es el catálogo (``required=false``); ``['presets']['indra']``
    son los nueve requisitos efectivos (``required=true``) en ``models_dir/indra``.
    """

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
    "TaskPredictor",
    "TextRegion",
    "VeloceOCR",
    "resolve_models_dir",
    "models_status",
]
