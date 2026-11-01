"""Stubs de tipos de pyocrust.

Refleja el contrato PyO3 real: ``VeloceOCR.recognize`` devuelve ``OcrResult``
en los presets de texto (``pp_ocrv6*``) y ``StructureResult`` en
``pp_structurev3`` (ADR-003) e ``indra`` (S2.2 parcial): tres familias de presets.

S3 re-exports (immutable dataclasses, defined in hardware/resolver):
GpuInfo(name: str | None=None, vram_bytes: int | None=None).
HardwareProfile(cpu_count: int, ram_bytes: int | None, gpu: GpuInfo | None=None).
CPU is a positive int; RAM/VRAM are positive ints or None (not bool).
Invalid numeric values raise ValueError; invalid gpu type raises TypeError.
detect_hardware() returns physical inventory, not wheel CUDA capability;
unknown RAM/VRAM remain None. CUDA_VISIBLE_DEVICES filters NVIDIA inventory.

TaskSpec(document_kind='digital', ocr_only=True, formulas='none', tables=False,
quality='speed', output_format='text'). Allowed enums: scanned/digital/mixed;
none/with_text/only; speed/balanced/accuracy; text/markdown/html/json.
Invalid enums raise ValueError; ocr_only/tables must be bool (TypeError).
PipelineChoice has preset: str, size: str | None, tasks: tuple[str, ...],
models_dir: str, offline: bool; id is pp_ocrv6_{size} or the structure preset.
resolve_pipeline(task: TaskSpec, hardware: HardwareProfile | None=None):
formulas/tables/Markdown/HTML/not ocr_only take precedence -> pp_structurev3,
size=None. Otherwise speed/unknown RAM/<4 GiB -> tiny; balanced/<8 GiB ->
small; otherwise medium. Scanned/mixed adds orientation/rectification;
accuracy with >=8 GiB physical VRAM adds Indra as an alternative, not execution.
Explicit hardware bypasses discovery; incorrect argument types raise TypeError.
No models/download/preflight; native models_dir resolution can normalize and
re-export relative OAR_HOME. PYOCRUST_OFFLINE is false for unset/empty/0/false/no
(case-insensitive, no whitespace trimming). Tasks are recommendations only;
output_format selects a preset, not a conversion. No GPU/availability guarantee.
"""

from __future__ import annotations

from os import PathLike
from typing import Sequence
from .hardware import GpuInfo as GpuInfo, HardwareProfile as HardwareProfile, detect_hardware as detect_hardware
from .resolver import TaskSpec as TaskSpec, PipelineChoice as PipelineChoice, resolve_pipeline as resolve_pipeline

def model_catalog() -> dict[str, dict]:
    """Metadata by artifact name, without filesystem scan, network or inference.

    Rows: name/task/description: str, params: int | None, size_bytes: int | None,
    env_vars: list[str]. params is always None; upstream sizes use find(name),
    Indra sizes remain None. Includes dictionaries/tokenizers, not only models.
    env_vars: OAR_HOME, OCR_MODELS_CACHE_DIR, PYOCRUST_OFFLINE,
    CUDA_LAUNCH_BLOCKING, RUST_LOG; no OAR_VL_* controls for Indra ONNX.
    """
    ...
def pipeline_profiles() -> dict[str, dict]:
    """Registered presets/tasks by ID, without disk scan, network or inference.

    Rows: id/family/quality/output_format/description: str, artifacts: list[str],
    disk_bytes: int | None, ram_bytes: int | None. Five presets plus eleven tasks;
    exact artifacts come from registry. disk_bytes sums upstream sizes, None if
    any entry is missing or sum overflows (Indra: None); ram_bytes always None.
    File size is not parameters, measured RAM or proof of local availability.
    """
    ...

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
    """Eleven standalone tasks; schemas list every returned key (S2.4).

    ``text_detection`` and ``seal_text_detection``: ``{detections: list[dict]}``,
    items ``{bbox: list[list[float]], score: float}`` (four [x, y] points).
    ``text_recognition``: ``{text: str, score: float}``.
    ``layout_detection``: ``{elements: list[dict], is_reading_order_sorted: bool}``,
    items ``{bbox: list[list[float]], element_type: str, score: float}``.
    ``table_classification``: ``{classifications: list[dict]}``, items
    ``{class_id: int, label: str, score: float}``.
    ``table_structure_recognition``: ``{structures: list[str], bboxes: list[list[float]]}``;
    structure tokens and geometry, NOT reconstructed HTML.
    ``table_cell_detection``: ``{cells: list[dict]}``, items
    ``{bbox: list[list[float]], label: str, score: float}``.
    Layout/cell boxes also contain four [x, y] points.
    ``document_orientation`` and ``text_line_orientation``: ``{orientations: list[dict]}``,
    items ``{class_id: int, label: str, score: float}``.
    ``document_rectification``: ``{image: bytes, width: int, height: int}`` (PNG).
    ``formula_recognition``: ``{formula: str, score: float | None}``;
    unavailable score is None; fixed model ``PP-FormulaNet-S``.

    Exact option whitelist/defaults:
    text_detection: score_threshold=0.3, box_threshold=0.6, unclip_ratio=1.5,
        max_candidates=1000.
    text_recognition: score_threshold=0.0, dict_path (priority below).
    layout_detection: score_threshold=0.5, model_name='pp_doclayoutv3'.
    table_classification: score_threshold=0.5, topk=2, input_shape=(224, 224).
    table_structure_recognition: dict_path, model_name, input_shape; omitted
        model_name/shape leave upstream path/ONNX detection (wired fallback).
        Local (512, 512) fallback is NOT forwarded when shape is omitted.
    table_cell_detection: score_threshold=0.3, model_name detected from path,
        fallback 'rt-detr-l_wired_table_cell_det'.
    document_orientation: score_threshold=0.5, topk=4.
    text_line_orientation: score_threshold=0.5, topk=2, input_shape=(80, 160).
    seal_text_detection: score_threshold=0.5 only.
    document_rectification/formula_recognition: no options.
    input_shape is (H, W), positive u32 integers. Unknown task/option or zero
    shape raises PyOcrValueError; whitelist is checked before model resolution.

    models=None ensures registered artifacts. Explicit str is a model file,
    not a directory; dict requires 'model', with optional 'dict'/'tokenizer'.
    Explicit paths bypass downloads. Text/table dictionary priority:
    options['dict_path'] > models['dict'] > lazy canonical-model sibling
    (ppocrv6_tiny_dict.txt / table_structure_dict_ch.txt).
    Formula tokenizer: models['tokenizer'] > pp-formulanet-tokenizer.json sibling.
    All selected model/dict/tokenizer assets must be existing local files and
    are canonicalized before upstream; invalid overrides never fall back.
    Missing/directory/canonicalization failures raise PyOcrRuntimeError with
    path/cause, without implicit upstream downloads. Registered model filenames
    are documented in DESIGN.md section 3.1.2, sourced from storage/registry.rs.

    predict_batch preserves input order and returns [] for empty input.
    Inference releases the GIL; decoding and Python mapping retain it.
    Approval covers code/contracts, not eleven real inferences or GPU validation.
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
    "model_catalog",
    "pipeline_profiles",
    "GpuInfo",
    "HardwareProfile",
    "detect_hardware",
    "TaskSpec",
    "PipelineChoice",
    "resolve_pipeline",
]
