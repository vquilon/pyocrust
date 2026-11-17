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
quality='speed', output_format='text', license_commercial_use=True,
license_acknowledge=False). Allowed enums: scanned/digital/mixed;
none/with_text/only; speed/balanced/accuracy; text/markdown/html/json.
Invalid enums raise ValueError; ocr_only/tables and both license flags must be
bool (TypeError). `license_commercial_use` and `license_acknowledge` are USER
declarations (commercial intent / acceptance of attribution), not the model's
terms: `license_commercial_use=True` keeps restricted models (Indra,
OpenRAIL-M-Mod) out of the recommendation, and a restricted model also
requires `license_acknowledge=True` (Indra §7).
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

Multi-feature: ``recognize(image, features=[...])`` runs one or more feature ids
from ``pipeline_profiles()`` (or an alias of ``FEATURE_ALIASES``) over the same
image. One feature returns today's object unwrapped (``OcrResult`` /
``StructureResult`` / the task dictionary); several return ``{label: output}``
keyed by the label the caller used, keeping each feature's schema (never
flattened). Unknown/duplicate/empty features, or a bare ``str`` instead of a
sequence, raise ``PyOcrValueError`` before any model loads. Sequential by
default (ADR-008); ``parallel=True`` runs the features in threads, overlapping
the native GIL-free inferences.

RAUTO (``DESIGN.md`` §12): ``route(declared=None, signals=None) -> RouteDecision``
is the pure structure router — R0 declared (delegate to resolve_pipeline / the
given features), R1 ``min(W,H) < GEOM_MIN_SIDE_PX``, R2/R2' probe signals
(``n_regions``/``ink_ratio``) and R3 default text. It decides only whether to
turn on ``pp_structurev3`` (never table/formula flags, which layout gates
upstream) and carries ``preset``, ``size``, ``features``, ``reason`` and
``artifacts`` — never times, never new keys in the OCR result.
``auto_recognize(image, *, declared=None, probe=False, ...) -> (output, RouteDecision)``
runs the optional detection probe, routes, and executes through
``recognize`` (the single executor); the output is exactly ``recognize``'s.
"""

from __future__ import annotations

from os import PathLike
from typing import Iterator, Literal, Mapping, Sequence
from .hardware import GpuInfo as GpuInfo, HardwareProfile as HardwareProfile, detect_hardware as detect_hardware
from .multifeature import FEATURE_ALIASES as FEATURE_ALIASES, auto_recognize as auto_recognize, recognize as recognize
from .resolver import (
    GEOM_MIN_SIDE_PX as GEOM_MIN_SIDE_PX,
    ROUTE_MIN_DENSITY as ROUTE_MIN_DENSITY,
    ROUTE_MIN_REGIONS as ROUTE_MIN_REGIONS,
    PipelineChoice as PipelineChoice,
    RouteDecision as RouteDecision,
    TaskSpec as TaskSpec,
    resolve_pipeline as resolve_pipeline,
    route as route,
)

def model_catalog() -> dict[str, dict]:
    """Metadata by artifact name, without filesystem scan, network or inference.

    Rows: name/task/description: str, params: int | None, size_bytes: int | None,
    env_vars: list[str], license: str, license_commercial_use: bool,
    license_acknowledge: bool, license_restricted: bool, license_notes: str,
    license_url: str | None. params is always None; upstream sizes use
    find(name), Indra sizes remain None. Includes dictionaries/tokenizers.
    license_commercial_use is False for Indra (OpenRAIL-M-Mod) and Unknown.
    env_vars: OAR_HOME, OCR_MODELS_CACHE_DIR, PYOCRUST_OFFLINE,
    CUDA_LAUNCH_BLOCKING, RUST_LOG; no OAR_VL_* controls for Indra ONNX.
    """
    ...
def pipeline_profiles() -> dict[str, dict]:
    """Registered presets/tasks by ID, without disk scan, network or inference.

    Rows: id/family/quality/output_format/description: str, artifacts: list[str],
    disk_bytes: int | None, ram_bytes: int | None, license: str,
    license_commercial_use: bool, license_acknowledge: bool,
    license_restricted: bool, license_notes: str, license_url: str | None.
    Five presets plus eleven tasks;
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

class PageInfo:
    """Metadatos de una página del API de documentos (DESIGN.md §13).

    ``text_regions`` reutiliza ``TextRegion``: ``box`` es el AABB del segmento en
    puntos PDF con origen arriba-izquierda e ``y`` hacia abajo, y ``confidence``
    es siempre ``1.0`` porque es extracción exacta del text-layer, no una
    puntuación de modelo. ``has_text_layer`` es ``page.text().len() >=
    text_min_chars`` y ``needs_ocr == not has_text_layer``.
    """

    index: int
    has_text_layer: bool
    needs_ocr: bool
    width_px: int
    height_px: int
    text_regions: Sequence[TextRegion]

class PyOcrError(Exception): ...
class PyOcrValueError(PyOcrError): ...
class PyOcrRuntimeError(PyOcrError): ...
class IncompatibleImageError(PyOcrValueError): ...
class IncompatiblePdfError(PyOcrValueError): ...
class ResolutionError(PyOcrRuntimeError): ...

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

    ``**options`` are accepted only when that task's oar-ocr builder really has
    them *and* this wrapper wires them; anything else raises PyOcrValueError
    (accepted-but-unwired would be silently ignored). Per task:
    ``text_detection`` score_threshold/box_threshold/unclip_ratio/max_candidates;
    ``text_recognition`` score_threshold/dict_path; ``layout_detection``
    score_threshold/model_name; ``table_classification``
    score_threshold/topk/input_shape; ``table_structure_recognition``
    score_threshold/dict_path/model_name/input_shape; ``table_cell_detection``
    score_threshold/model_name (RT-DETR variant); ``document_orientation``
    score_threshold/topk/input_shape; ``text_line_orientation``
    score_threshold/topk/input_shape; ``seal_text_detection`` score_threshold;
    ``formula_recognition`` score_threshold (checkpoint and tokenizer are
    pinned); ``document_rectification`` none.

    predict_batch preserves input order and returns [] for empty input.
    Inference releases the GIL; decoding and Python mapping retain it.

    ``device`` is opt-in (default ``"cpu"``) and selects the ONNX Runtime
    execution provider *before* the predictor is built, via
    ``core::device::resolve_device``. ``provider_effective`` reports what really
    runs. ``available_providers()`` lists the accelerators that actually register.
    Approval covers code/contracts, not eleven real inferences or GPU validation.
    """
    def __init__(self, task: str, models: str | dict[str, str] | None = None, device: str = "cpu", license_commercial_use: bool = True, license_acknowledge: bool = False, **options: object) -> None: ...
    @property
    def provider_effective(self) -> str: ...
    @property
    def license(self) -> dict[str, object]:
        """Resolved license for this task's registered artifacts; ``Unknown``
        when explicit ``models`` paths are used (provenance cannot be verified)."""
        ...
    def predict(self, image: str | bytes | PathLike[str]) -> dict[str, object]: ...
    def predict_batch(self, images: Sequence[str | bytes | PathLike[str]]) -> list[dict[str, object]]: ...

def available_providers() -> list[str]:
    """Accelerator execution providers that really register in this host, or ``[]``.

    Probes the compiled candidates (``cuda``/``directml``) through ONNX Runtime;
    a physical GPU (``detect_hardware``) is not proof that an EP exists here.
    """
    ...

def resolve_models_dir(custom_path: str | None = None) -> str: ...

def parse_document(
    path: str | PathLike[str],
    pages: Sequence[int] | None = None,
    dpi: int = 200,
    *,
    text_min_chars: int = 64,
) -> list[PageInfo]:
    """Metadatos por página: text-layer (texto + cajas) o marca de ``needs_ocr``.

    ``pages=None`` devuelve todas; si no, una secuencia de índices
    **1-indexados**. ``dpi`` sólo fija ``width_px``/``height_px``
    (``round(pt * dpi / 72)``): las cajas no cambian con el ``dpi``, así que
    re-renderizar a otro ``dpi`` no obliga a re-parsear. Una página con
    ``needs_ocr=True`` no trae regiones: se rasteriza con :func:`render_page` y
    entra al OCR como cualquier imagen.

    ``dpi < 1``, ``text_min_chars < 1``, o ``pages`` con índices no enteros,
    duplicados, fuera de rango o 0-based lanzan ``PyOcrValueError`` antes de abrir
    el documento. Requiere la librería nativa PDFium: se resuelve desde
    ``PYOCRUST_PDFIUM_LIB`` (fichero o directorio) o desde el directorio del
    módulo nativo; si no carga, ``PyOcrRuntimeError`` (nunca una lista vacía).
    """
    ...

def render_page(
    path: str | PathLike[str],
    index: int,
    dpi: int = 200,
) -> bytes:
    """Rasteriza UNA página (índice 1-indexado) a PNG, listo para ``recognize``.

    Las dimensiones son ``round(pt * dpi / 72)``, las mismas que ``PageInfo``.
    Índice fuera de rango o ``dpi < 1`` lanzan ``PyOcrValueError``.
    """
    ...

def models_status(
    custom_path: str | None = None,
) -> dict[str, object]:
    """Estado en disco: ``models_dir``, ``offline``, ``presets``, ``indra``.

    ``['indra']`` es el catálogo (``required=false``); ``['presets']['indra']``
    son los nueve requisitos efectivos (``required=true``) en ``models_dir/indra``.
    """

class VeloceOCR:
    """Clase de alto nivel: un preset, un pipeline residente.

    ``text_det_*`` ajustan el detector DB (solo los presets ``pp_ocrv6*``; los
    demás presets los ignoran). Sin ellos el comportamiento es el histórico: el
    adaptador de oar-ocr reescala a ``limit_side_len=960, limit_type="max"`` con
    tope ``max_side_len=4000``, y los umbrales son 0.2 / 0.45 (0.4 en tiny) /
    1.4 / 3000. En una página grande (7000x5000) con texto fino eso reescala a
    ~960 px de lado mayor y pierde texto; ``text_det_limit_type="min",
    text_det_limit_side_len=64`` desactiva el reescalado, pero el tope de 4000
    sigue recortando **incondicionalmente** el lado largo, así que a resolución
    nativa hay que subir también ``text_det_max_side_len`` (p. ej. 7000).

    Un valor inválido (``text_det_limit_type`` fuera de ``"min"``/``"max"``,
    umbral fuera de rango, lado <= 0) lanza ``PyOcrValueError`` en el
    constructor; nunca cae en silencio al default.

    ``use_doc_orientation``, ``use_doc_unwarping`` y ``use_textline_orientation``
    (los tres ``True`` por defecto, como en PaddleOCR) encienden los componentes
    de composición de ``oar-ocr`` que hasta ahora pyocrust no cableaba: una
    página girada 90/180/270 grados se endereza antes de detectar, una página
    curvada se rectifica (UVDoc) y un recorte de línea boca abajo se gira antes
    de reconocer. Cada uno exige sus pesos (``pp-lcnet_x1_0_doc_ori.onnx``,
    ``uvdoc.onnx``, ``pp-lcnet_x1_0_textline_ori.onnx``, ~45 MB en total), que se
    resuelven en el mismo directorio de modelos y se descargan si faltan
    (``PYOCRUST_OFFLINE=1`` los convierte en error tipado en vez de red).
    ``text_type`` ("general"|"table"|"seal") es el ``text_type`` del pipeline:
    cambia el preprocesado del detector y el tipo de caja (``"seal"`` = polígono,
    reescalado 736/min). Ojo: el ``text_det_*`` explícito que este wrapper fija
    con los umbrales oficiales de PP-OCRv6 gana sobre los presets de umbral de
    ``table``/``seal`` — lo que cambia con ``text_type`` es el preprocesado y el
    tipo de caja, no los umbrales; para estos pasa ``text_det_thresh`` /
    ``text_det_box_thresh`` / ``text_det_unclip_ratio`` explícitos.

    Los cuatro se ignoran en los presets que no son ``pp_ocrv6*``.

    Ejemplo (página grande / PDF vectorial a alta resolución; copiar y ejecutar)::

        from pyocrust import VeloceOCR, render_page

        # render_page necesita PDFium (DESIGN.md §13).
        png = render_page("plano.pdf", index=1, dpi=600)   # raster grande

        RECETA = dict(text_det_limit_type="min", text_det_limit_side_len=64,
                      text_det_max_side_len=7000)          # los TRES knobs
        engine = VeloceOCR("pp_ocrv6_medium", **RECETA)
        boxes = engine.detect_regions(png, **RECETA)       # list[BoundingBox]
        result = engine.recognize_regions(png, boxes)      # OcrResult, 1:1 por caja
    """

    def __init__(
        self,
        preset: str = "pp_ocrv6",
        custom_path: str | None = None,
        device: str = "cpu",
        license_commercial_use: bool = True,
        license_acknowledge: bool = False,
        text_det_limit_side_len: int | None = None,
        text_det_limit_type: str | None = None,
        text_det_max_side_len: int | None = None,
        text_det_thresh: float | None = None,
        text_det_box_thresh: float | None = None,
        text_det_unclip_ratio: float | None = None,
        text_det_max_candidates: int | None = None,
        use_doc_orientation: bool = True,
        use_doc_unwarping: bool = True,
        use_textline_orientation: bool = True,
        text_type: str = "general",
    ) -> None: ...
    @property
    def models_dir(self) -> str: ...
    @property
    def license(self) -> dict[str, object]:
        """Resolved license for this preset's artifacts (six fields)."""
        ...
    @property
    def provider_effective(self) -> str:
        """EP that really ran (``cpu``/``cuda``/``directml``/...); never faked.

        Requesting ``device="cuda"`` with no registered CUDA EP raises at
        construction instead of labelling CPU as GPU.
        """
        ...
    def recognize(
        self, image: str | bytes | PathLike[str]
    ) -> OcrResult | StructureResult: ...
    def detect_regions(
        self,
        image: str | bytes | PathLike[str],
        *,
        text_det_limit_side_len: int | None = None,
        text_det_limit_type: str | None = None,
        text_det_max_side_len: int | None = None,
        text_det_thresh: float | None = None,
        text_det_box_thresh: float | None = None,
        text_det_unclip_ratio: float | None = None,
        text_det_max_candidates: int | None = None,
    ) -> list[BoundingBox]:
        """Cajas AABB de las regiones de texto (`DESIGN.md` §11.2, `RDET`).

        Usa el modelo de detección **del preset** (no el `tiny` fijo de
        ``TaskPredictor("text_detection")``) a la resolución que fijen los
        ``text_det_*``: los del constructor se heredan y los de aquí los pisan
        (``None`` = heredado; con el constructor por defecto eso es 960/Max/4000
        más los umbrales de hoy). Para una página grande a resolución nativa
        hacen falta los **tres** (el tope del lado largo recorta
        incondicionalmente): ``text_det_limit_type="min"``,
        ``text_det_limit_side_len=64`` y ``text_det_max_side_len>=7000``.

        La caja es el AABB del cuadrilátero detectado: se pierde la rotación de
        líneas inclinadas (para texto rotado, ``recognize``). Presets sin par
        det+rec propio (``indra``, VLM) y valores fuera de rango lanzan
        ``PyOcrValueError`` antes de cargar modelos.
        """
        ...
    def recognize_regions(
        self,
        image: str | bytes | PathLike[str],
        boxes: Sequence[BoundingBox],
        *,
        rec_score_threshold: float | None = None,
        region_batch_size: int | None = None,
    ) -> OcrResult:
        """OCR de las cajas dadas, recortando la imagen nativa (§11.2).

        Una ``TextRegion`` por caja de entrada, en el mismo orden: ``box`` es la
        caja dada, ``text`` el texto reconocido o ``""`` y ``confidence`` su
        score o ``0.0``. Recorta con ``image::imageops::crop_imm`` sin reescalar
        la página y pasa los recortes al reconocedor del preset en lotes de
        ``region_batch_size`` (por defecto 16 en ``tiny`` y 4 en el resto); el
        nº de pasadas de rec es ``ceil(N / region_batch_size)``. Regiones sin
        área dentro de la página producen ``text=""``. ``rec_score_threshold``
        (``None`` = ``0.0``, sin filtro) fuera de ``[0, 1]`` o
        ``region_batch_size < 1`` lanzan ``PyOcrValueError``.
        """
        ...
    def recognize_tiled(
        self,
        image: str | bytes | PathLike[str],
        *,
        tile_size: int = 2048,
        tile_overlap: int = 256,
        text_det_limit_side_len: int | None = None,
        text_det_limit_type: Literal["min", "max"] | None = None,
        text_det_max_side_len: int | None = None,
        text_det_thresh: float | None = None,
        text_det_box_thresh: float | None = None,
        text_det_unclip_ratio: float | None = None,
        text_det_max_candidates: int | None = None,
    ) -> OcrResult: ...

ImageOutput = OcrResult | StructureResult
Resolution = Literal["default", "balanced", "native", "tiled"]

class PageRun:
    index: int
    source: Literal["text_layer", "ocr"]
    output: OcrResult | StructureResult
    route_decision: RouteDecision | None
    warnings: tuple[str, ...]

class DocumentResult:
    pages: tuple[PageRun, ...]

class Session:
    def __init__(
        self, *, device: str = "cpu", custom_path: str | None = None,
        resolution: Resolution = "balanced", tile_size: int | None = None,
        tile_overlap: int | None = None, text_det_limit_side_len: int | None = None,
        text_det_limit_type: Literal["min", "max"] | None = None,
        text_det_max_side_len: int | None = None, text_det_thresh: float | None = None,
        text_det_box_thresh: float | None = None, text_det_unclip_ratio: float | None = None,
        text_det_max_candidates: int | None = None,
        license_commercial_use: bool = True, license_acknowledge: bool = False,
    ) -> None: ...
    def __enter__(self) -> Session: ...
    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None: ...
    def recognize_image(self, image: str | bytes | PathLike[str], *,
                        task: TaskSpec | None = None) -> ImageOutput: ...
    def iter_document_pages(
        self, path: str | PathLike[str], pages: Sequence[int] | None = None, *,
        task: TaskSpec | None = None, page_tasks: Mapping[int, TaskSpec] | None = None,
        auto_route: bool = False, probe: bool = False, dpi: int = 600,
        text_min_chars: int = 64,
    ) -> Iterator[PageRun]: ...
    def purge(self) -> None: ...


def available_features(*, license_commercial_use: bool = True,
                       license_acknowledge: bool = False) -> list[str]: ...

def recognize_image(
    image: str | bytes | PathLike[str], *, task: TaskSpec | None = None,
    resolution: Literal["default", "balanced", "native", "tiled"] = "balanced",
    tile_size: int | None = None, tile_overlap: int | None = None,
    text_det_limit_side_len: int | None = None,
    text_det_limit_type: Literal["min", "max"] | None = None,
    text_det_max_side_len: int | None = None,
    text_det_thresh: float | None = None, text_det_box_thresh: float | None = None,
    text_det_unclip_ratio: float | None = None, text_det_max_candidates: int | None = None,
    device: str = "cpu", custom_path: str | None = None,
    license_commercial_use: bool | None = None,
    license_acknowledge: bool | None = None,
) -> OcrResult | StructureResult: ...

def recognize_document(
    path: str | PathLike[str], pages: Sequence[int] | None = None, *,
    task: TaskSpec | None = None, page_tasks: Mapping[int, TaskSpec] | None = None,
    auto_route: bool = False, probe: bool = False, dpi: int = 600,
    text_min_chars: int = 64,
    resolution: Literal["default", "balanced", "native", "tiled"] = "balanced",
    tile_size: int | None = None, tile_overlap: int | None = None,
    text_det_limit_side_len: int | None = None,
    text_det_limit_type: Literal["min", "max"] | None = None,
    text_det_max_side_len: int | None = None,
    text_det_thresh: float | None = None, text_det_box_thresh: float | None = None,
    text_det_unclip_ratio: float | None = None, text_det_max_candidates: int | None = None,
    device: str = "cpu", custom_path: str | None = None,
    license_commercial_use: bool | None = None,
    license_acknowledge: bool | None = None,
) -> DocumentResult: ...

__all__: list[str] = [
    "__version__",
    "BoundingBox",
    "LayoutRegion",
    "OcrResult",
    "PyOcrError",
    "PyOcrRuntimeError",
    "PyOcrValueError",
    "IncompatibleImageError",
    "IncompatiblePdfError",
    "ResolutionError",
    "StructureResult",
    "TaskPredictor",
    "TextRegion",
    "VeloceOCR",
    "PageInfo",
    "parse_document",
    "render_page",
    "resolve_models_dir",
    "models_status",
    "model_catalog",
    "pipeline_profiles",
    "available_providers",
    "GpuInfo",
    "HardwareProfile",
    "detect_hardware",
    "TaskSpec",
    "PipelineChoice",
    "resolve_pipeline",
    "RouteDecision",
    "route",
    "auto_recognize",
    "GEOM_MIN_SIDE_PX",
    "ROUTE_MIN_REGIONS",
    "ROUTE_MIN_DENSITY",
    "FEATURE_ALIASES",
    "recognize",
    "recognize_image",
    "recognize_document",
    "PageRun",
    "DocumentResult",
    "Session",
    "ImageOutput",
    "Resolution",
    "available_features",
]
