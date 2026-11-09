#!/usr/bin/env python
"""Runner compartido de los bancos por feature (`benchmarks/common/`).

Reorganización por feature (oar-ocr components): este módulo es el **runner
común** que orquestan `benchmarks/features/<feature>/bank.py`. Se derivó del
antiguo `benchmarks/run_benchmarks.py`; ambos siguen en pie y **comparten el
contrato del CSV** (`CSV_FIELDS`): el driver histórico `run_benchmarks.py` se
mantiene como CLI de compatibilidad (y como banco de fórmulas de las variantes
PP-FormulaNet), y este runner es el que usan los bancos por feature.

Mide **calidad** (CER, WER, F1, Markdown/bloques, LaTeX) y **tiempo**
(ms/imagen) de `pyocrust` contra alternativas Python reales sobre las mismas
imágenes, con warmup y `--repeats`, y vuelca una fila por `(backend, imagen)`.

Los backends que no estén instalados (o cuyos modelos falten) se registran con
`status=skipped` y un motivo; **nunca** como si hubieran corrido.

Salida: `<output-dir>/<timestamp>/<timestamp>.csv` (+ `<backend>.meta.json` y
`summary.json`).

Columnas del CSV (contrato con `report_benchmarks.py`, **30 columnas**):
    run_timestamp, backend, dataset, image_id, cer, wer, cer_ord, wer_ord,
    word_f1, exact_match, elapsed_ms, n_regions, mean_confidence, n_chars_gt,
    n_chars_pred, status, error, task_type, model_name, model_variant,
    markdown_f1, block_f1,
    latex_exact, latex_sim, latex_token_f1,     (solo `task_type=formula`)
    feature,                                    (banco por feature que produjo la fila)
    box_recall, box_iou_mean,                   (solo si el dataset anota cajas GT)
    device_requested, provider_effective        (honestidad de proveedor, ver abajo)

Las 22 columnas históricas se mantienen en su orden; las nuevas son aditivas.

**Honestidad de proveedor (regla dura).** `device_requested` es el eje pedido
(`cpu`/`gpu`) y `provider_effective` es el provider que **de verdad** corrió
(`cpu`/`cuda`/`directml`/…). `--device gpu` se mapea al `device="auto"` de
`pyocrust` (`VeloceOCR`/`TaskPredictor`, tarjeta `t_13a1b2b7`), que **prueba**
los EPs compilados y confirma el que registra de verdad; el provider real se lee
de `engine.provider_effective` tras construir el motor. Un fallback CPU **nunca**
se etiqueta como GPU: si no se confirma un acelerador (o el recurso/build no
está), la fila/backend queda `skipped` con motivo, no `ok`.

**Provenance (regla del usuario).** Todo valor numérico publicado desde este
banco es **`medido`** (ejecutado por nosotros en este repo): el `summary.json` y
los metadatos por backend guardan el comando, dataset, `n`, `warmup`, `repeats`,
dispositivo y fecha que lo respaldan. Los valores **`referencia`** (externos) no
los produce este runner y solo se citan en los markdown con su URL.

Uso genérico:
    python benchmarks/run_benchmarks.py --limit 20 --backends pyocrust,rapidocr
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import io
import json
import platform
import statistics
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable, Sequence

from PIL import Image

# Ejecutable también como script (`python benchmarks/common/runner.py`).
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common.datasets import (
    DatasetUnavailable,
    Sample,
    fixture_provenance,
    load_dataset,
    load_funsd,
    load_local,
    load_omnidocbench,
    load_omnidocbench_formulas,
)
from common.metrics import (
    block_f1,
    box_metrics,
    cer,
    cer_ord,
    latex_exact,
    latex_similarity,
    latex_token_f1,
    markdown_f1,
    normalize,
    wer,
    wer_ord,
    word_f1,
)

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

HERE = Path(__file__).resolve().parent
BENCHMARKS_ROOT = HERE.parent
DEFAULT_RESULTS_DIR = BENCHMARKS_ROOT / "results"
DEFAULT_DATASET = "funsd"

CSV_FIELDS = [
    "run_timestamp",
    "backend",
    "dataset",
    "image_id",
    "cer",
    "wer",
    "cer_ord",
    "wer_ord",
    "word_f1",
    "exact_match",
    "elapsed_ms",
    "n_regions",
    "mean_confidence",
    "n_chars_gt",
    "n_chars_pred",
    "status",
    "error",
    "task_type", "model_name", "model_variant", "markdown_f1", "block_f1",
    # Additive: métrica LaTeX normalizada (fórmulas), banco por feature y cajas.
    "latex_exact", "latex_sim", "latex_token_f1",
    "feature",
    "box_recall", "box_iou_mean",
    # Honestidad de proveedor: dispositivo pedido vs. el que de verdad corrió.
    "device_requested", "provider_effective",
    # Additive: métricas de las features de layout/tabla/orientación/rectificado
    # (vacías — no evaluadas — en los bancos que no las producen).
    "layout_map", "layout_recall", "table_teds", "ori_acc", "rect_sim",
    # Additive: estrato de la página (`data_source × layout`) cuando el dataset
    # lo anota (`Sample.stratum`); vacío en el resto. Permite el informe "por
    # estrato" sin releer la anotación del dataset.
    "stratum",
    # Additive: métricas **propias** de `full_page` que `markdown_f1` no separa —
    # detección/texto de títulos y **orden de lectura** como secuencia (Kendall
    # tau). Vacías en el resto de bancos y en páginas sin GT de la modalidad
    # (`""` = no evaluada). La cobertura se cuenta en el informe sobre las filas
    # con `title_recall` evaluado (no se diluye en una media global).
    "title_recall", "title_precision", "title_text_f1", "title_seq_tau",
    "read_order_tau",
    # Additive: métricas **propias de figuras** de `full_page` — detección de
    # `figure`, detección de sus captions y **asociación figura↔caption**.
    # Vacías en el resto de bancos y en páginas sin GT de figuras (`""` = no
    # evaluada, nunca `0.0`; lo no emitible — las `*_mask` — no entra).
    "figure_recall", "figure_precision",
    "figure_caption_recall", "figure_caption_precision",
    "figure_caption_pair_f1", "figure_caption_text_f1",
]


# ---------------------------------------------------------------------------
# Canales de estructura que un motor declara emitir (senal del ADAPTADOR)
# ---------------------------------------------------------------------------
# Un motor **solo-texto** (p. ej. `docling`, que devuelve Markdown y nada mas)
# NO emite las estructuras que miden las columnas de `full_page`: sin ellas la
# metrica queda **no evaluada** (`N/A`), nunca un `0.0` inventado — 0.0 y N/A no
# son lo mismo. La senal la declara cada adaptador en `run.emits`; un motor sin
# declaracion se asume completo (compatibilidad con runs e informes previos).
#
# Canales = lo que la metrica necesita para poder evaluarse:
#   * "layout"   -> elementos de layout en el vocabulario del banco (kind + caja):
#                   `block_f1`, `layout mAP/recall`, titulos y figuras.
#   * "boxes"    -> cajas con posicion, aunque el vocabulario no sea el del banco:
#                   `orden lectura tau`.
#   * "tables"   -> HTML `<table>` embebido en el Markdown: `TEDS tabla`.
#   * "formulas" -> registros de formula/LaTeX separados: `LaTeX sim`.
ALL_STRUCTURE_CHANNELS = frozenset({"layout", "boxes", "tables", "formulas"})

# Motores que NO emiten todos los canales (los ausentes se asumen completos).
#   * `docling`           — solo Markdown, y sus tablas son **pipe tables**, no
#     HTML `<table>` (verificado sobre las paginas con GT de tabla): ninguno.
#   * `pp_structurev3_api` — PaddleOCR PP-StructureV3 en Python: devuelve solo el
#     Markdown (que si embebe `<table>`), sin cajas, bloques ni formulas aparte.
#   * `pyocrust_indra` — emite cajas y tablas HTML, pero su vocabulario de bloques
#     no es el del banco (sin `layout`) y no expone formulas separadas.
STRUCTURE_CHANNELS: dict[str, frozenset[str]] = {
    "docling": frozenset(),
    "pp_structurev3_api": frozenset({"tables"}),
    "pyocrust_indra": frozenset({"boxes", "tables"}),
}


def emitted_channels(backend: str) -> frozenset[str]:
    """Canales de estructura que `backend` declara emitir (por defecto, todos)."""
    return STRUCTURE_CHANNELS.get(backend, ALL_STRUCTURE_CHANNELS)


# Metrica de `full_page` -> canal de estructura que necesita para evaluarse.
# Lo comparten el `scorer` (gatea de origen: la celda sale `""` = N/A) y el
# generador de informes (no pinta como `0.0` lo que un motor no podia emitir).
FULL_PAGE_METRIC_CHANNEL: dict[str, str] = {
    "block_f1": "layout",
    "layout_map": "layout", "layout_recall": "layout",
    "title_recall": "layout", "title_precision": "layout",
    "title_text_f1": "layout", "title_seq_tau": "layout",
    "figure_recall": "layout", "figure_precision": "layout",
    "figure_caption_recall": "layout", "figure_caption_precision": "layout",
    "figure_caption_pair_f1": "layout", "figure_caption_text_f1": "layout",
    "read_order_tau": "boxes",
    "table_teds": "tables",
    "latex_sim": "formulas", "latex_token_f1": "formulas",
}


def not_evaluable_metrics(backend: str) -> frozenset[str]:
    """Metricas de estructura que `backend` **no puede** emitir -> `N/A`.

    El conjunto son claves de columna del banco (`block_f1`, `layout_map`, …):
    lo que el motor no emite no se mide ni se pinta como `0.0`.
    """
    emits = emitted_channels(backend)
    return frozenset(metric for metric, channel in FULL_PAGE_METRIC_CHANNEL.items()
                     if channel not in emits)


class ProviderUnavailable(RuntimeError):
    """El backend no se puede ejecutar en este entorno (no como un OCR malo)."""


# `--device gpu` -> `device="auto"` en pyocrust: prueba los EPs aceleradores
# compilados (cuda, directml, ...) y elige el que REGISTRA de verdad; `cpu` es
# explícito y no sondea ninguna GPU.
PYOCRUST_DEVICE = {"cpu": "cpu", "gpu": "auto"}

# Motivo honesto cuando se pide GPU pero el motor acaba sin acelerador confirmado:
# nunca se cuenta un fallback CPU como GPU (regla dura del card).
GPU_NOT_CONFIRMED = (
    "device=gpu pedido pero el motor corre en '{engine}' (sin acelerador confirmado; "
    "available_providers()={available}); se niega a etiquetar CPU como GPU"
)


def available_providers() -> list[str]:
    """EPs aceleradores que **registran de verdad** (delega en `pyocrust`)."""
    try:
        import pyocrust  # noqa: PLC0415

        return list(pyocrust.available_providers())
    except Exception:  # pragma: no cover - pyocrust no importable/compilado
        return []


def pyocrust_device_arg(device: str) -> str:
    """Eje del banco (`cpu`/`gpu`) -> `device` de `pyocrust` (`cpu`/`auto`)."""
    return PYOCRUST_DEVICE.get(device, "cpu")


# Backends cuya factoría acepta `device` y puede correr en GPU de verdad.
GPU_CAPABLE_BACKENDS = frozenset({
    "paddle_latex_ocr",
    "hantian_v8n", "hantian_v8s", "hantian_v8m", "hantian_v8l", "hantian_v8x",
    "hantian_v10n", "hantian_v10s", "hantian_v10m", "hantian_v10l", "hantian_v10b",
    "hantian_v11n", "hantian_v11s", "hantian_v11m", "hantian_v11l",
    "hantian_v12n", "hantian_v12s", "hantian_v12m", "hantian_v12l",
    "hantian_y26n", "hantian_y26s", "hantian_y26m", "hantian_y26l",
    "omoured_v10n", "omoured_v10s", "omoured_v10m", "omoured_v10l", "omoured_v10b", "omoured_v10x",
    "omoured_v11n", "omoured_v11s", "omoured_v11m", "omoured_v11l", "omoured_v11x",
    "armaggheddon_y11n", "armaggheddon_y11s", "armaggheddon_y11m",
    "armaggheddon_y26n", "armaggheddon_y26s", "armaggheddon_y26m",
    "rapidocr", "easyocr",
})


def device_outcome(backend: str, device: str) -> tuple[str | None, str | None]:
    """Resuelve `(provider_effective, motivo_skip)` **antes** de construir el motor.

    Honestidad de proveedor: devuelve el provider que **de verdad** corre y, si la
    GPU no es confirmable, un motivo de `skipped` (nunca un `ok` CPU disfrazado).

    - `cpu`  -> `("cpu", None)`: EP de CPU explícito en `pyocrust`.
    - `gpu` + backend `pyocrust` -> `(None, None)`: el provider real **no se puede
      adivinar** aquí; se CONFIRMA al construir el motor, leyendo
      `engine.provider_effective` (`pyocrust` resuelve y prueba el EP).
    - `gpu` + backend no-`pyocrust` -> `("n/a", motivo)`: esos adaptadores son
      CPU-only en este banco.
    """
    if device == "cpu":
        return "cpu", None
    if backend.startswith("pyocrust") or backend in GPU_CAPABLE_BACKENDS:
        return None, None
    return "n/a", f"{backend} no expone ejecucion GPU en este banco (solo CPU; device={device})"


# Providers que cuentan como acelerador REAL (nunca `cpu` ni `n/a`).
GPU_PROVIDERS = frozenset({"cuda", "directml", "tensorrt", "coreml", "openvino", "webgpu", "rocm", "mps"})


def select_device_rows(rows: Iterable[dict], device: str) -> list[dict]:
    """Filas que **de verdad** corrieron en `device` (honestidad de proveedor).

    El ranking GPU sólo cuenta filas con un `provider_effective` de acelerador
    real: una fila que pidió `gpu` pero corrió en CPU (`provider_effective=cpu`,
    p. ej. un fallback) queda fuera, nunca se cuenta como GPU. Para `cpu`, cuenta
    las filas cuyo provider efectivo es `cpu` (el valor por defecto si falta).
    """
    if device == "cpu":
        return [r for r in rows if (r.get("provider_effective") or "cpu") == "cpu"]
    return [r for r in rows if str(r.get("provider_effective", "")).lower() in GPU_PROVIDERS]


def preload_gpu_runtime() -> None:
    """Carga el runtime CUDA de `torch` **antes** que el provider CUDA de ORT.

    Windows: el provider CUDA de ORT (`onnxruntime_providers_cuda.dll`) resuelve
    `cudnn64_9.dll` desde `torch/lib` pero `cudnn_ops64_9.dll`/`cublas64_13.dll`
    del **CUDA Toolkit del PATH** (build distinto). Si eso ocurre primero, el
    `import torch` posterior revienta con `WinError 127` en `cudnn_cnn64_9.dll` y
    los motores torch (`easyocr`, `paddle_latex_ocr`, YOLO de `layout`) quedan
    `skipped` aunque la GPU funcione (medido 2026-11-09). Importando `torch`
    primero, sus DLL (cudnn/cublas) quedan cargadas y ORT reutiliza ESE cudnn
    consistente. Idempotente y best-effort: sin torch no hace nada, y un fallo
    aquí nunca debe abortar el banco.
    """
    try:
        import torch  # noqa: PLC0415

        torch.cuda.is_available()
    except Exception:  # noqa: BLE001 - best-effort
        pass


def module_available(name: str) -> bool:
    """¿Está instalado `name` en este intérprete? (para decidir `skipped`)."""
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):  # pragma: no cover - nombre no importable
        return False


# ---------------------------------------------------------------------------
# Proveedores (adaptadores de backends OCR)
# ---------------------------------------------------------------------------

@dataclass
class OcrOutput:
    text: str
    n_regions: int = 0
    mean_confidence: float = 0.0
    elapsed_ms: float = 0.0
    extra: dict = field(default_factory=dict)


def _image_bytes(image: Image.Image) -> bytes:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def _quad_to_bbox(points: Sequence[Sequence[float]]) -> list[float]:
    """Caja envolvente `[x1, y1, x2, y2]` de 4 puntos `[[x, y], ...]`."""
    xs = [float(p[0]) for p in points]
    ys = [float(p[1]) for p in points]
    return [min(xs), min(ys), max(xs), max(ys)]


def _bbox_quad(box: object) -> list[list[float]]:
    """`BoundingBox` de pyocrust -> 4 puntos `[[x1,y1],[x2,y1],[x2,y2],[x1,y2]]`.

    Es la forma de `bbox` que consumen los scorers de layout (`score_layout`):
    caja envolvente del poligono. Vacio si la caja no expone sus esquinas.
    """
    try:
        x1, y1, x2, y2 = float(box.x1), float(box.y1), float(box.x2), float(box.y2)
    except (AttributeError, TypeError, ValueError):
        return []
    return [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]


def _pyocrust_backend(preset: str, formula_only: bool = False, device: str = "cpu") -> Callable[[Image.Image], OcrOutput]:
    import pyocrust  # noqa: PLC0415 - import tardío para no penalizar el arranque

    # El banco es un contexto **no comercial** y la atribución va documentada:
    # Indra (OpenRAIL-M-Mod) exige declarar ambas cosas (son acumulativas).
    kwargs: dict = {}
    if preset == "indra":
        kwargs = {"license_commercial_use": False, "license_acknowledge": True}
    engine = pyocrust.VeloceOCR(preset=preset, device=device, **kwargs)

    def run(image: Image.Image) -> OcrOutput:
        # La preparación de la entrada va **fuera** del cronómetro: lo medido es
        # solo la inferencia, simétrico con los demás backends (B4/D12).
        data = _image_bytes(image)
        start = time.perf_counter()
        result = engine.recognize(data)
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        if formula_only:
            text = "\n".join(result.formulas)
        elif hasattr(result, "to_markdown"):  # StructureResult (ADR-003)
            text = result.to_markdown()
        else:
            text = result.text
        regions = getattr(result, "regions", []) or []
        confidence = getattr(result, "confidence", 0.0) or 0.0
        boxes = [
            [r.box.x1, r.box.y1, r.box.x2, r.box.y2]
            for r in regions
            if getattr(r, "box", None) is not None
        ]
        # Elementos de layout (kind + caja + score) en el **mismo vocabulario**
        # que consume `score_layout` (`element_type`/`score`/`bbox`): el pipeline
        # ya los trae y antes se tiraban. `full_page` los usa para el mAP de
        # layout; las formulas llevan su LaTeX en `text`.
        elements = [
            {
                "element_type": str(getattr(element, "kind", "")),
                "score": float(getattr(element, "confidence", 0.0) or 0.0),
                "bbox": _bbox_quad(getattr(element, "box", None)),
                "text": str(getattr(element, "text", "") or ""),
            }
            for element in (getattr(result, "elements", []) or [])
            if getattr(element, "box", None) is not None
        ]
        return OcrOutput(
            text=text,
            n_regions=len(regions),
            mean_confidence=float(confidence),
            elapsed_ms=elapsed_ms,
            extra={"kind": type(result).__name__,
                   "blocks": [e.kind for e in getattr(result, "elements", [])],
                   "boxes": boxes,
                   "elements": elements,
                   "formulas": [str(f) for f in (getattr(result, "formulas", []) or [])]},
        )

    # EP real confirmado por pyocrust (honestidad de proveedor): el banco no lo supone.
    run.provider_effective = getattr(engine, "provider_effective", None)
    # Declaracion de estructura: Indra emite cajas y tablas HTML pero su vocabulario
    # de bloques no es el del banco (sin `layout`) y no expone formulas separadas;
    # `pp_structurev3` emite todos los canales. Sin esta senal, un motor que no
    # emite una estructura publicaria `0.0` en vez de `N/A` (ver `STRUCTURE_CHANNELS`).
    run.emits = (emitted_channels("pyocrust_indra") if preset == "indra"
                 else ALL_STRUCTURE_CHANNELS)
    return run


def _rapidocr_backend(device: str = "cpu") -> Callable[[Image.Image], OcrOutput]:
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError as exc:
        raise ProviderUnavailable("pip install rapidocr-onnxruntime") from exc

    engine = RapidOCR(use_cuda=device != "cpu")

    def run(image: Image.Image) -> OcrOutput:
        # Fairness (B6): los MISMOS bytes PNG que el resto de adaptadores; rapidocr
        # los decodifica dentro de su propia llamada. Codificar queda fuera del cronómetro.
        data = _image_bytes(image)
        start = time.perf_counter()
        # rapidocr 1.2.x devuelve (result, elapse): result = [[box, texto, score]]
        result, _elapse = engine(data)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        if not result:
            return OcrOutput(text="", elapsed_ms=elapsed_ms)
        texts = [str(item[1]) for item in result]
        scores = [float(item[2]) for item in result]
        boxes = [_quad_to_bbox(item[0]) for item in result]
        return OcrOutput(
            text="\n".join(texts),
            n_regions=len(texts),
            mean_confidence=sum(scores) / len(scores) if scores else 0.0,
            elapsed_ms=elapsed_ms,
            extra={"engine": "rapidocr_onnxruntime", "boxes": boxes},
        )

    run.provider_effective = "cpu" if device == "cpu" else "cuda"
    return run


def _easyocr_backend(languages: Sequence[str] = ("en",),
                     device: str = "cpu") -> Callable[[Image.Image], OcrOutput]:
    try:
        import easyocr
    except ImportError as exc:
        raise ProviderUnavailable("pip install easyocr (requiere torch)") from exc

    reader = easyocr.Reader(list(languages), gpu=device != "cpu", verbose=False)

    def run(image: Image.Image) -> OcrOutput:
        # Fairness (B6): los MISMOS bytes PNG que el resto de adaptadores; easyocr
        # acepta `bytes` y los decodifica dentro de su propia llamada.
        data = _image_bytes(image)
        start = time.perf_counter()
        result = reader.readtext(data)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        if not result:
            return OcrOutput(text="", elapsed_ms=elapsed_ms)
        texts = [str(item[1]) for item in result]
        scores = [float(item[2]) for item in result]
        boxes = [_quad_to_bbox(item[0]) for item in result]
        return OcrOutput(
            text="\n".join(texts),
            n_regions=len(texts),
            mean_confidence=sum(scores) / len(scores),
            elapsed_ms=elapsed_ms,
            extra={"engine": "easyocr", "boxes": boxes},
        )

    run.provider_effective = "cpu" if device == "cpu" else "cuda"
    return run


def _pyocrust_formula_variant_backend(model_file: str, device: str = "cpu") -> Callable[[Image.Image], OcrOutput]:
    """PP-FormulaNet **directo** de una variante concreta (`formula_recognition`).

    Sin layout propio: recibe el recorte de la formula tal cual. Aisla el modelo de
    formulas del pipeline de pagina, que sobre un recorte puede no detectar bloque.
    Todas las variantes comparten `FormulaModelKind::PPFormulaNet` en oar-ocr: el
    adaptador es el mismo y solo cambia el `.onnx`, asi que elegir el fichero aisla
    el tamano del modelo, no el pipeline. Si el `.onnx` no esta descargado, el
    backend queda `skipped` (no se mide a medias).
    """
    import pyocrust  # noqa: PLC0415

    models_dir = Path(pyocrust.resolve_models_dir())
    model_path = models_dir / model_file
    tokenizer = models_dir / "pp-formulanet-tokenizer.json"
    if not model_path.is_file():
        raise ProviderUnavailable(f"falta {model_file} en {models_dir} (no descargado)")
    predictor = pyocrust.TaskPredictor(
        task="formula_recognition",
        models={"model": str(model_path), "tokenizer": str(tokenizer)},
        device=device,
    )

    def run(image: Image.Image) -> OcrOutput:
        data = _image_bytes(image)
        start = time.perf_counter()
        result = predictor.predict(data)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return OcrOutput(
            text=str(result.get("formula", "") or ""),
            elapsed_ms=elapsed_ms,
            extra={"kind": "formula_recognition", "model_file": model_file},
        )

    run.provider_effective = getattr(predictor, "provider_effective", None)
    return run


def _tesseract_backend(device: str = "cpu") -> Callable[[Image.Image], OcrOutput]:
    try:
        import pytesseract
    except ImportError as exc:
        raise ProviderUnavailable("pip install pytesseract + binario Tesseract") from exc

    def run(image: Image.Image) -> OcrOutput:
        # Fairness (B6): los MISMOS bytes PNG que el resto de adaptadores; el
        # decodificado a PIL (lo que consume pytesseract) queda fuera del cronómetro.
        data = Image.open(io.BytesIO(_image_bytes(image)))
        start = time.perf_counter()
        text = pytesseract.image_to_string(data)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return OcrOutput(text=text, elapsed_ms=elapsed_ms, extra={"engine": "tesseract"})

    return run


# TATR (`table-transformer-structure-recognition`) es la alternativa REAL al
# `table_structure_recognition` de `pyocrust` en el banco de `table`. Su `config`
# es `model_type=table-transformer`, así que la clase es `TableTransformer...` y
# no `DetrForObjectDetection` (aunque comparte arquitectura DETR).
TATR_MODEL_ID = "microsoft/table-transformer-structure-recognition"


def _patch_legacy_timm_feature_index() -> None:
    """Rellena `index` en `FeatureInfo.get_dicts()` de timm 0.5.4.

    `transformers>=5` exige la clave `index` al envolver un backbone timm
    (`TimmBackbone.__init__`), pero timm 0.5.4 no la añade (llegó en timm 0.9).
    Este intérprete tiene timm 0.5.4 **fijado por `pix2tex`**, que importa
    `timm.models.resnetv2` (eliminado en timm 1.x): subir timm rompería la
    alternativa de fórmulas. El parche da al dict la posición real del módulo en
    `feature_info.info`, que es justo lo que hace el timm moderno. Idempotente.
    """
    try:
        from timm.models.features import FeatureInfo  # noqa: PLC0415
    except ImportError:  # pragma: no cover - entorno sin timm
        return
    if getattr(FeatureInfo.get_dicts, "_pyocrust_index_patch", False):
        return
    original = FeatureInfo.get_dicts

    def get_dicts(self, keys=None, idx=None):
        infos = original(self, None, idx)
        if idx is None:
            positions = self.out_indices
        elif isinstance(idx, (tuple, list)):
            positions = idx
        else:
            positions = [idx]
        for position, info in zip(positions, infos):
            info.setdefault("index", position)
        return infos if keys is None else [{k: d[k] for k in keys} for d in infos]

    get_dicts._pyocrust_index_patch = True  # type: ignore[attr-defined]
    FeatureInfo.get_dicts = get_dicts


def _tatr_grid_html(n_rows: int, n_cols: int) -> str:
    """Gramática HTML de una rejilla `n_rows`×`n_cols` (lo que consume `table_teds`).

    El modelo de estructura no emite texto de celda; `table_teds` compara la
    secuencia de etiquetas, así que basta `<tr>`/`<td>` por celda.
    """
    return "<table>" + "".join(
        "<tr>" + "<td></td>" * n_cols + "</tr>" for _ in range(n_rows)
    ) + "</table>"


def _tatr_backend(device: str = "cpu") -> Callable[[Image.Image], OcrOutput]:
    """TATR (`microsoft/table-transformer-structure-recognition`) vía `transformers`.

    Reconstruye la **estructura** de la tabla como una rejilla HTML: las cajas
    `table row` / `table column header` son filas y las `table column` /
    `table projected row header` son columnas (mismo reparto que el
    `objects_to_structures` oficial). Emite la gramática que consume
    `table_teds` (`<tr>`/`<td>`), sin texto de celda — igual que `pyocrust_table`.

    ponytail: rejilla filas×columnas, sin `rowspan`/`colspan`; `table_teds` compara
    la SECUENCIA de etiquetas e ignora atributos y texto, así que el span de TATR
    no cambiaría el TEDS-S. Si algún día se puntúa el TEDS de árbol completo, aquí
    entra el `objects_to_structures` + `structure_to_cells` oficiales.
    """
    try:
        import torch  # noqa: PLC0415 - import tardío (carga pesada)
        from transformers import AutoImageProcessor, TableTransformerForObjectDetection  # noqa: PLC0415
    except ImportError as exc:
        raise ProviderUnavailable("pip install transformers torch (TATR)") from exc

    image_processor = AutoImageProcessor.from_pretrained(TATR_MODEL_ID)
    _patch_legacy_timm_feature_index()
    model = TableTransformerForObjectDetection.from_pretrained(TATR_MODEL_ID)
    model.eval()
    id2label = {int(key): str(value) for key, value in model.config.id2label.items()}
    row_labels = frozenset({"table row", "table column header"})
    col_labels = frozenset({"table column", "table projected row header"})

    def run(image: Image.Image) -> OcrOutput:
        # El preprocesado (resize/normalize) va **fuera** del cronómetro, igual que
        # el re-encode PNG del resto de adaptadores (fairness, B4/D12).
        inputs = image_processor(images=image, return_tensors="pt")
        start = time.perf_counter()
        with torch.no_grad():
            outputs = model(**inputs)
        # El post-proceso es parte de la salida del motor (como el decode interno
        # de rapidocr/easyocr): también dentro del cronómetro.
        results = image_processor.post_process_object_detection(
            outputs, threshold=0.5, target_sizes=torch.tensor([image.size[::-1]])
        )[0]
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        labels = [id2label[int(label)] for label in results["labels"]]
        n_rows = sum(label in row_labels for label in labels)
        n_cols = sum(label in col_labels for label in labels)
        html = _tatr_grid_html(n_rows, n_cols)
        scores = [float(score) for score in results["scores"]]
        return OcrOutput(
            text=html,
            n_regions=len(labels),
            mean_confidence=(sum(scores) / len(scores)) if scores else 0.0,
            elapsed_ms=elapsed_ms,
            extra={
                "engine": "table-transformer",
                "model": TATR_MODEL_ID,
                "labels": labels,
                "boxes": [[float(v) for v in box] for box in results["boxes"]],
            },
        )

    return run


# ---------------------------------------------------------------------------
# Alternativas reales de `layout` (`transformers`): RT-DETR / Deformable-DETR
# ---------------------------------------------------------------------------
# Detectores de layout de documentos publicados en HF: `docling-layout-heron-101`
# (RT-DETR v2) y `deformable-detr-DocLayNet` (Deformable-DETR). Comparten el
# vocabulario DocLayNet (`Caption/Footnote/Formula/List-item/Page-footer/`
# `Page-header/Picture/Section-header/Table/Text/Title`); heron-101 anade 6 mas.
# El vocabulario de `pyocrust` (`common.datasets.LAYOUT_MODEL_TO_GT`) solo tiene
# equivalencia para una parte: las clases sin equivalencia (List-item, Code,
# Form, Checkbox-*, Document Index, Key-Value Region) **no se emiten**, asi que
# no entran ni a favor ni en contra (regla del banco).
LAYOUT_DOCLAYNET_LABEL_TO_MODEL = {
    "text": "text",
    "title": "doc_title",
    "section-header": "paragraph_title",
    "formula": "display_formula",
    "table": "table",
    "picture": "image",
    "caption": "figure_title",
    "page-header": "header",
    "page-footer": "footer",
    "footnote": "footnote",
}
DOCLAYNET_CLASSES = frozenset({
    "caption", "footnote", "formula", "list-item", "page-footer", "page-header",
    "picture", "section-header", "table", "text", "title",
})

# Backend -> `model_id` de HF (pesos en la cache HF local; ruta **offline**).
LAYOUT_HF_MODELS = {
    "docling_heron_101": "docling-project/docling-layout-heron-101",
    "deformable_detr": "Aryn/deformable-detr-DocLayNet",
}


# Umbral de **recolección** de cajas para el banco de `layout`, no de reporte.
#
# Un AP se calcula sobre la curva precision-recall completa: si los adaptadores
# emiten solo las cajas con `score>=0.5`, el AP se mide sobre un unico punto de
# operacion y sale artificialmente bajo (una caja GT cuyo mejor acierto puntua
# 0.4 es un fallo permanente). Medido en este host, bajar el umbral de 0.5 a 0.05
# sube el mAP de 0.236->0.303 (yolo26m) y 0.658->0.821 (docling heron-101).
# Se emiten por tanto las detecciones crudas y el barrido lo hace `_class_ap`.
# Efecto colateral asumido: `n_regions` cuenta cajas sobre el suelo, no a 0.5.
LAYOUT_AP_SCORE_FLOOR = 0.05


def _hf_layout_backend(model_id: str, threshold: float = LAYOUT_AP_SCORE_FLOOR) -> Callable[[Image.Image], OcrOutput]:
    """Detector de layout de `transformers` (RT-DETR / Deformable-DETR) -> `elements`.

    Carga **offline** (`local_files_only=True`): si los pesos no estan en la cache
    HF (`HF_HOME`) el backend queda `skipped` con motivo honesto, en vez de
    descargar en mitad del banco. Emite `extra["elements"]` en el vocabulario que
    consume `score_layout` (`element_type`, `score`, `bbox` = 4 puntos).

    ponytail: `AutoImageProcessor` + `AutoModelForObjectDetection` cubren las
    arquitecturas del card; otro detector entra como una linea mas en
    `LAYOUT_HF_MODELS`, sin duplicar el adaptador.
    """
    try:
        import torch  # noqa: PLC0415 - import tardio (carga pesada)
        from transformers import AutoImageProcessor, AutoModelForObjectDetection  # noqa: PLC0415
    except ImportError as exc:
        raise ProviderUnavailable("pip install transformers torch (detectores de layout)") from exc

    try:
        image_processor = AutoImageProcessor.from_pretrained(model_id, local_files_only=True)
        model = AutoModelForObjectDetection.from_pretrained(model_id, local_files_only=True)
    except Exception as exc:  # noqa: BLE001 - pesos no cacheados: es un `skipped`, no un OCR malo
        raise ProviderUnavailable(
            f"pesos de {model_id} no estan en la cache HF local ({type(exc).__name__}: {exc})"
        ) from exc
    model.eval()
    id2label = {int(key): str(value) for key, value in model.config.id2label.items()}

    def run(image: Image.Image) -> OcrOutput:
        # El preprocesado va **fuera** del cronometro, simetrico con TATR (B4/D12).
        inputs = image_processor(images=image, return_tensors="pt")
        start = time.perf_counter()
        with torch.no_grad():
            outputs = model(**inputs)
        # El post-proceso es parte de la salida del motor (como el decode de
        # rapidocr/easyocr): tambien dentro del cronometro.
        results = image_processor.post_process_object_detection(
            outputs, threshold=threshold, target_sizes=torch.tensor([image.size[::-1]])
        )[0]
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        elements: list[dict] = []
        boxes: list[list[float]] = []
        for label, score, box in zip(results["labels"], results["scores"], results["boxes"]):
            element_type = LAYOUT_DOCLAYNET_LABEL_TO_MODEL.get(id2label[int(label)].strip().lower())
            if element_type is None:
                continue  # clase sin equivalencia declarada: fuera de la metrica
            x1, y1, x2, y2 = (float(v) for v in box)
            elements.append({
                "element_type": element_type,
                "score": float(score),
                "bbox": [[x1, y1], [x2, y1], [x2, y2], [x1, y2]],
            })
            boxes.append([x1, y1, x2, y2])
        return OcrOutput(
            text="", n_regions=len(elements), elapsed_ms=elapsed_ms,
            extra={"engine": "transformers", "model": model_id, "elements": elements, "boxes": boxes},
        )

    return run


# ---------------------------------------------------------------------------
# Alternativa real de `layout` con YOLO (`ultralytics`, pesos `.pt` en cache)
# ---------------------------------------------------------------------------
# Los tres YOLO documentales comparten el vocabulario DocLayNet de arriba, asi
# que reutilizan `LAYOUT_DOCLAYNET_LABEL_TO_MODEL` tal cual. `DocLayout-YOLO`
# usa su propio vocabulario y lleva su mapa aparte. El tamano del modelo va en
# el nombre visible (`MODEL_NAMES`) para que la tabla diga que se comparo.
YOLO_LAYOUT_MODELS = {
    "hantian_v8n": "D:/Environments/cache/models/layout/hantian/yolo8/yolov8n-doclaynet.pt",
    "hantian_v8s": "D:/Environments/cache/models/layout/hantian/yolo8/yolov8s-doclaynet.pt",
    "hantian_v8m": "D:/Environments/cache/models/layout/hantian/yolo8/yolov8m-doclaynet.pt",
    "hantian_v8l": "D:/Environments/cache/models/layout/hantian/yolo8/yolov8l-doclaynet.pt",
    "hantian_v8x": "D:/Environments/cache/models/layout/hantian/yolo8/yolov8x-doclaynet.pt",
    "hantian_v10b": "D:/Environments/cache/models/layout/hantian/yolo10/yolov10b-doclaynet.pt",
    "hantian_v10l": "D:/Environments/cache/models/layout/hantian/yolo10/yolov10l-doclaynet.pt",
    "hantian_v10m": "D:/Environments/cache/models/layout/hantian/yolo10/yolov10m-doclaynet.pt",
    "hantian_v10n": "D:/Environments/cache/models/layout/hantian/yolo10/yolov10n-doclaynet.pt",
    "hantian_v10s": "D:/Environments/cache/models/layout/hantian/yolo10/yolov10s-doclaynet.pt",
    "hantian_v11l": "D:/Environments/cache/models/layout/hantian/yolo11/yolov11l-doclaynet.pt",
    "hantian_v11m": "D:/Environments/cache/models/layout/hantian/yolo11/yolov11m-doclaynet.pt",
    "hantian_v11n": "D:/Environments/cache/models/layout/hantian/yolo11/yolov11n-doclaynet.pt",
    "hantian_v11s": "D:/Environments/cache/models/layout/hantian/yolo11/yolov11s-doclaynet.pt",
    "hantian_v12l": "D:/Environments/cache/models/layout/hantian/yolo12/yolov12l-doclaynet.pt",
    "hantian_v12m": "D:/Environments/cache/models/layout/hantian/yolo12/yolov12m-doclaynet.pt",
    "hantian_v12n": "D:/Environments/cache/models/layout/hantian/yolo12/yolov12n-doclaynet.pt",
    "hantian_v12s": "D:/Environments/cache/models/layout/hantian/yolo12/yolov12s-doclaynet.pt",
    "hantian_y26l": "D:/Environments/cache/models/layout/hantian/yolo26/yolo26l-doclaynet.pt",
    "hantian_y26m": "D:/Environments/cache/models/layout/hantian/yolo26/yolo26m-doclaynet.pt",
    "hantian_y26n": "D:/Environments/cache/models/layout/hantian/yolo26/yolo26n-doclaynet.pt",
    "hantian_y26s": "D:/Environments/cache/models/layout/hantian/yolo26/yolo26s-doclaynet.pt",
    "omoured_v10b": "D:/Environments/cache/models/layout/omoured/yolo10/yolov10b_best.pt",
    "omoured_v10l": "D:/Environments/cache/models/layout/omoured/yolo10/yolov10l_best.pt",
    "omoured_v10m": "D:/Environments/cache/models/layout/omoured/yolo10/yolov10m_best.pt",
    "omoured_v10n": "D:/Environments/cache/models/layout/omoured/yolo10/yolov10n_best.pt",
    "omoured_v10s": "D:/Environments/cache/models/layout/omoured/yolo10/yolov10s_best.pt",
    "omoured_v10x": "D:/Environments/cache/models/layout/omoured/yolo10/yolov10x_best.pt",
    "omoured_v11l": "D:/Environments/cache/models/layout/omoured/yolo11/yolov11l_best.pt",
    "omoured_v11m": "D:/Environments/cache/models/layout/omoured/yolo11/yolov11m_best.pt",
    "omoured_v11n": "D:/Environments/cache/models/layout/omoured/yolo11/yolov11n_best.pt",
    "omoured_v11s": "D:/Environments/cache/models/layout/omoured/yolo11/yolov11s_best.pt",
    "omoured_v11x": "D:/Environments/cache/models/layout/omoured/yolo11/yolov11x_best.pt",
    "armaggheddon_y11n": "D:/Environments/cache/models/layout/Armaggheddon/yolo11/yolo11n_doc_layout.pt",
    "armaggheddon_y11s": "D:/Environments/cache/models/layout/Armaggheddon/yolo11/yolo11s_doc_layout.pt",
    "armaggheddon_y11m": "D:/Environments/cache/models/layout/Armaggheddon/yolo11/yolo11m_doc_layout.pt",
    "armaggheddon_y26n": "D:/Environments/cache/models/layout/Armaggheddon/yolo26/yolo26n_doc_layout.pt",
    "armaggheddon_y26s": "D:/Environments/cache/models/layout/Armaggheddon/yolo26/yolo26s_doc_layout.pt",
    "armaggheddon_y26m": "D:/Environments/cache/models/layout/Armaggheddon/yolo26/yolo26m_doc_layout.pt",
}

# Licencias verificadas en las tarjetas de los tres autores; todos sus checkpoints
# quedan cubiertos individualmente para que la tabla pueda resolver por backend.
LICENSES = {
    **{name: "AGPL-3.0" for name in YOLO_LAYOUT_MODELS if name.startswith(("hantian_", "omoured_"))},
    **{name: "MIT" for name in YOLO_LAYOUT_MODELS if name.startswith("armaggheddon_")},
    # Pipelines documentales completos del banco `full_page`.
    "pp_structurev3_api": "Apache-2.0",
    "docling": "MIT",
    # Alternativas externas del banco `table` (además de TATR, MIT).
    "paddleocr_slanet": "Apache-2.0",
    "docling_tableformer": "MIT",
    # Alternativas independientes de `orientation`/`text_line` (proyecto distinto).
    "rapidocr_mobile_cls": "Apache-2.0",
    "easyocr_rotation": "Apache-2.0",
    # Baseline geometrica clasica de `rectification` (OpenCV: Apache-2.0; sin pesos).
    "opencv_perspective": "Apache-2.0",
    # Alternativa externa del banco `formula` (UniMERNet, Apache-2.0).
    "unimernet": "Apache-2.0",
}

# ---------------------------------------------------------------------------
# Procedencia de cada alternativa: ¿es un modelo INDEPENDIENTE o el MISMO peso
# por otra via? El informe lo declara explicitamente para no presentar como
# "modelo distinto" lo que solo cambia de runtime.
# ---------------------------------------------------------------------------
#   "independiente"      -> otro modelo (otro proveedor o checkpoint distinto).
#   "mismo_peso_otra_via"-> MISMO `.onnx` de PaddleOCR cargado por otro runtime.
#   "mismo_tronco_otro_checkpoint" -> PP-LCNet de PaddleOCR pero OTRO entrenamiento.
ALTERNATIVE_PROVENANCE: dict[str, str] = {
    "lcnet_doc_ori": "mismo_peso_otra_via",
    "lcnet_textline_ori": "mismo_peso_otra_via",
    "uvdoc": "mismo_peso_otra_via",
    "onnx_seal_det": "mismo_peso_otra_via",
    "rapidocr_mobile_cls": "independiente",
    "easyocr_rotation": "independiente",
    "opencv_perspective": "baseline_clasico",
    "tatr": "independiente",
    "paddleocr_slanet": "independiente",
    "docling_tableformer": "independiente",
    "docling_heron_101": "independiente",
    "deformable_detr": "independiente",
    "pp_structurev3_api": "independiente",
    "docling": "independiente",
    "rapidocr": "independiente",
    "easyocr": "independiente",
    "tesseract": "independiente",
    "paddle_latex_ocr": "independiente",
    "unimernet": "independiente",
}


def alternative_provenance(backend: str) -> str:
    """Como se relaciona `backend` con el motor de `pyocrust` (para el informe)."""
    return ALTERNATIVE_PROVENANCE.get(backend, "independiente")


# --- pipelines documentales completos (`full_page`) ---------------------------
# Dos alternativas externas REALES al pipeline propio. Las dos emiten el Markdown
# del documento, que es lo que consume `markdown_f1`; ninguna inventa contenido.

# docling vive en un venv APARTE (`benchmarks/.venv_docling`): su `[standard]`
# arrastra torch/torchvision y comparte `transformers`/`huggingface_hub` con el
# venv del banco. Instalarlo en el venv principal degradaria los backends de
# `layout`/`table`. Se invoca por **subproceso**, un modelo a la vez.
DOCLING_VENV_PYTHON = BENCHMARKS_ROOT / ".venv_docling" / "Scripts" / "python.exe"
_DOCLING_RUNNER = r'''
import sys, warnings
warnings.filterwarnings("ignore")
from docling.document_converter import DocumentConverter, ImageFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

pipe = PdfPipelineOptions()
# La entrada del banco es una imagen raster: sin OCR no hay texto que emitir.
pipe.do_ocr = True
pipe.do_table_structure = True
conv = DocumentConverter(format_options={InputFormat.IMAGE: ImageFormatOption(pipeline_options=pipe)})
print(conv.convert(sys.argv[1]).document.export_to_markdown())
'''

# Variante tabla-solo del runner de docling: el recorte ya es una tabla, así que
# se emite su HTML (`export_to_html`), que es lo que consume el TEDS-S del banco
# de `table`. `do_ocr=True` para que TableFormer haga cell-matching y la tabla
# salga estructurada; sin OCR la tabla queda vacía. Sin `do_table_structure` no
# habría estructura: se pide explícitamente.
_DOCLING_TABLE_RUNNER = r'''
import sys, warnings
warnings.filterwarnings("ignore")
from docling.document_converter import DocumentConverter, ImageFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

pipe = PdfPipelineOptions()
pipe.do_ocr = True
pipe.do_table_structure = True
conv = DocumentConverter(format_options={InputFormat.IMAGE: ImageFormatOption(pipeline_options=pipe)})
doc = conv.convert(sys.argv[1]).document
for table in doc.tables:
    sys.stdout.write(table.export_to_html(doc))
'''


def _docling_backend(device: str = "cpu") -> Callable[[Image.Image], OcrOutput]:
    """Pipeline documental completo de **docling** (MIT) -> Markdown de página.

    Corre en el venv aislado `benchmarks/.venv_docling` por subproceso: sus
    dependencias (torch/torchvision/transformers) no coexisten con el venv del
    banco. Si ese venv no existe, el backend queda `skipped` con el `pip install`
    exacto en vez de fallar a medias.
    """
    if not DOCLING_VENV_PYTHON.is_file():
        raise ProviderUnavailable(
            f"falta el venv de docling; crear con: uv venv {DOCLING_VENV_PYTHON.parents[1]} "
            f"&& uv pip install --python {DOCLING_VENV_PYTHON} docling")

    def run(image: Image.Image) -> OcrOutput:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "page.png"
            image.convert("RGB").save(path, format="PNG")
            start = time.perf_counter()
            proc = subprocess.run(
                [str(DOCLING_VENV_PYTHON), "-c", _DOCLING_RUNNER, str(path)],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900,
            )
            elapsed_ms = (time.perf_counter() - start) * 1000.0
        if proc.returncode != 0:
            raise RuntimeError(f"docling: {(proc.stderr or '').strip().splitlines()[-1:]}")
        return OcrOutput(text=proc.stdout, elapsed_ms=elapsed_ms,
                         extra={"engine": "docling", "model": "docling-default"})

    run.provider_effective = "cpu" if device == "cpu" else "cuda"
    # docling solo devuelve Markdown (sin cajas, bloques ni formulas; sus tablas
    # son `pipe tables`, no el HTML que mide `TEDS`): declara 0 canales de
    # estructura -> esas columnas salen `N/A`, nunca `0.0`.
    run.emits = emitted_channels("docling")
    return run


# PP-StructureV3 vive en el venv **del banco** (`paddleocr`/`paddlepaddle` ya
# instalados), pero su pipeline **segfaultea (exit 139) o cuelga** en proceso sobre
# páginas reales (medido 2026-11-09: muere en una imagen `11112x7925` tras cargar
# sus 16 submodelos; en sonda 1/5 páginas cuelga con CPU idle). Por eso se ejecuta
# por **subproceso con timeout**, igual que `docling`/`unimernet`: un segfault o un
# cuelgue mata solo a ese hijo y la fila sale `error`/`skipped` con motivo — nunca
# aborta el banco entero. Ojo: el `ms` medido incluye spawn + carga de los 16
# submodelos + inferencia (como el de docling), no solo la inferencia.
_PP_STRUCTUREV3_RUNNER = r'''
import sys, warnings
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
from PIL import Image
from paddleocr import PPStructureV3

image_path, device = sys.argv[1], sys.argv[2]
# `enable_mkldnn=False`: este paddle (3.3.1) revienta al ejecutar un modelo por el
# motor oneDNN/PIR ("ConvertPirAttribute2RuntimeAttribute not support
# [pir::ArrayAttribute<pir::DoubleAttribute>]"); el EP de CPU nativo si corre.
pipeline = PPStructureV3(device=device, enable_mkldnn=False)
results = pipeline.predict(np.asarray(Image.open(image_path).convert("RGB")))
if not results:
    sys.exit(0)
payload = results[0].markdown
# PP-StructureV3 devuelve el Markdown como dict (`markdown_texts`) o como str.
markdown = (str(payload.get("markdown_texts", "") or "") if isinstance(payload, dict)
            else str(payload or ""))
sys.stdout.write(markdown)
'''


def _pp_structurev3_api_backend(device: str = "cpu") -> Callable[[Image.Image], OcrOutput]:
    """Pipeline completo de página de **PaddleOCR PP-StructureV3** (Apache-2.0) -> Markdown.

    Alternativa externa al `pp_structurev3` de `pyocrust`: el **mismo** pipeline
    publicado por PaddleOCR (layout + OCR + tablas + fórmulas). Corre en
    **subproceso con timeout** (mismo patrón que `docling`/`unimernet`, ver arriba):
    el pipeline en proceso segfaultea o cuelga en páginas reales, así que aislarlo
    evita que aborte el banco. El intérprete es el del propio banco
    (`sys.executable`), donde ya viven `paddleocr`/`paddlepaddle`.
    """
    # Chequeo barato en el PADRE: no se importa `paddle` aquí (importar el motor en
    # proceso es justo lo que colgaba/segfaulteaba). Si falta el paquete -> `skipped`.
    if importlib.util.find_spec("paddleocr") is None:  # pragma: no cover - entorno sin paddleocr
        raise ProviderUnavailable("pip install paddleocr paddlex[ocr]")
    paddle_device = "gpu" if device != "cpu" else "cpu"

    def run(image: Image.Image) -> OcrOutput:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "page.png"
            image.convert("RGB").save(path, format="PNG")
            start = time.perf_counter()
            proc = subprocess.run(
                [sys.executable, "-c", _PP_STRUCTUREV3_RUNNER, str(path), paddle_device],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900,
            )
            elapsed_ms = (time.perf_counter() - start) * 1000.0
        if proc.returncode != 0:
            tail = (proc.stderr or "").strip().splitlines()[-1:]
            detail = f"exit {proc.returncode}" + (f": {tail[-1]}" if tail else
                                                  " (sin stderr: probable segfault/cuelgue del pipeline)")
            raise RuntimeError(f"pp_structurev3_api: {detail}")
        return OcrOutput(text=proc.stdout, elapsed_ms=elapsed_ms,
                         extra={"engine": "paddleocr", "model": "PP-StructureV3"})

    run.provider_effective = "cpu" if device == "cpu" else "cuda"
    # Devuelve solo Markdown (con tablas HTML embebidas): emite `tables` pero no
    # cajas/bloques/formulas aparte -> esas columnas quedan `N/A`, no `0.0`.
    run.emits = emitted_channels("pp_structurev3_api")
    return run


# Segunda y tercera alternativa REAL al `table_structure_recognition` de
# `pyocrust` en el banco de `table`, además de TATR. Ambas off-line y CPU-only.
# - `paddleocr_slanet`: SLANet_plus de PaddleOCR por su API oficial
#   (`TableStructureRecognition`), Apache-2.0. Emite el HTML de la tabla (solo
#   gramática, sin texto de celda), el mismo GT que `pyocrust_table`.
# - `docling_tableformer`: TableFormer (docling, MIT) en su venv aislado; emite
#   HTML con texto de celda, así que se puntúa con el MISMO TEDS-S que el resto
#   (la secuencia de etiquetas), no el TEDS de árbol.
PADDLEOCR_TABLE_MODELS = frozenset({"SLANet_plus", "SLANeXt_wired"})


def _paddleocr_slanet_backend(model_name: str = "SLANet_plus",
                              device: str = "cpu") -> Callable[[Image.Image], OcrOutput]:
    """SLANet de **PaddleOCR** (`TableStructureRecognition`) -> HTML de estructura.

    El motor propio de `pyocrust` implementa el mismo SLANeXt en Rust/ONNX; aquí
    se mide la implementación **oficial** de PaddleOCR sobre el mismo recorte y el
    mismo GT. `enable_mkldnn=False` por el mismo choque del motor oneDNN/PIR que
    en `_pp_structurev3_api_backend`. Solo CPU.
    """
    try:
        import numpy as np  # noqa: PLC0415
        from paddleocr import TableStructureRecognition  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover - entorno sin paddleocr
        raise ProviderUnavailable("pip install paddleocr paddlepaddle") from exc

    if model_name not in PADDLEOCR_TABLE_MODELS:  # pragma: no cover - guardia
        raise ProviderUnavailable(f"modelo SLANet desconocido: {model_name!r}")
    model = TableStructureRecognition(model_name=model_name, enable_mkldnn=False)

    def run(image: Image.Image) -> OcrOutput:
        arr = np.asarray(image.convert("RGB"))
        start = time.perf_counter()
        results = model.predict(arr)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        html, scores = "", []
        if results:
            res = results[0].json.get("res", {})
            structure = res.get("structure")
            html = "".join(structure) if isinstance(structure, list) else (structure or "")
            if res.get("structure_score") is not None:
                scores.append(float(res["structure_score"]))
        return OcrOutput(
            text=html,
            mean_confidence=(sum(scores) / len(scores)) if scores else 0.0,
            elapsed_ms=elapsed_ms,
            extra={"engine": "paddleocr", "model": model_name},
        )

    run.provider_effective = "cpu" if device == "cpu" else "cuda"
    return run


def _docling_tableformer_backend(device: str = "cpu") -> Callable[[Image.Image], OcrOutput]:
    """Estructura de tabla de **docling TableFormer** (MIT) -> HTML de la tabla.

    Corre en el venv aislado `benchmarks/.venv_docling` por subproceso (mismo
    motivo que el backend `docling` de `full_page`: sus deps no coexisten con el
    venv del banco). El modelo ve un recorte de tabla: `DocumentConverter` detecta
    la tabla y `export_to_html` da su estructura **con** texto de celda; el banco
    la puntúa con TEDS-S (secuencia de etiquetas), comparable a TATR/SLANet.
    """
    if not DOCLING_VENV_PYTHON.is_file():
        raise ProviderUnavailable(
            f"falta el venv de docling; crear con: uv venv {DOCLING_VENV_PYTHON.parents[1]} "
            f"&& uv pip install --python {DOCLING_VENV_PYTHON} docling")

    def run(image: Image.Image) -> OcrOutput:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "table.png"
            image.convert("RGB").save(path, format="PNG")
            start = time.perf_counter()
            proc = subprocess.run(
                [str(DOCLING_VENV_PYTHON), "-c", _DOCLING_TABLE_RUNNER, str(path)],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900,
            )
            elapsed_ms = (time.perf_counter() - start) * 1000.0
        if proc.returncode != 0:
            raise RuntimeError(f"docling tableformer: {(proc.stderr or '').strip().splitlines()[-1:]}")
        return OcrOutput(text=proc.stdout, elapsed_ms=elapsed_ms,
                         extra={"engine": "docling", "model": "tableformer"})

    run.provider_effective = "cpu" if device == "cpu" else "cuda"
    return run


def _paddle_latex_ocr_backend(model_name: str = "PP-FormulaNet_plus-M",
                               device: str = "cpu") -> Callable[[Image.Image], OcrOutput]:
    try:
        from paddleocr import FormulaRecognition  # noqa: PLC0415
        import numpy as np  # noqa: PLC0415
    except ImportError as exc:
        raise ProviderUnavailable("pip install paddleocr (requiere paddle)") from exc

    model = FormulaRecognition(model_name=model_name, device=device)

    def run(image: Image.Image) -> OcrOutput:
        data = _image_bytes(image)
        img = Image.open(io.BytesIO(data))
        arr = np.asarray(img.convert("RGB"))
        start = time.perf_counter()
        res = model.predict(input=arr)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        if isinstance(res, (list, tuple)) and res:
            res = res[0]
        if isinstance(res, dict):
            text = str(res.get("rec_formula", "") or "")
        else:
            text = str(res or "")
        return OcrOutput(text=text, elapsed_ms=elapsed_ms, extra={"engine": "paddleocr", "model": model_name})

    # Honestidad de proveedor: el runner confirma el EP leyendo este atributo.
    run.provider_effective = "cpu" if device == "cpu" else "cuda"
    return run


# --- UniMERNet (formula) -----------------------------------------------------
# `unimernet` fija `transformers==4.42.4` (numpy<2) y arrastra `evaluate`/`datasets`;
# instalarlo en el venv del banco degradaria transformers 5.x, que usan paddleocr,
# docling y los detectores de layout. Vive en su propio venv
# (`benchmarks/.venv_unimernet`) y se invoca por **subproceso**, un modelo a la vez
# — mismo patrón que `docling`. Sus pesos (`unimernet_tiny`, 441 MB) se cargan del
# cache local (`~/.cache/models/MFR/unimernet_tiny`); si faltan, es `skipped`.
UNIMERNET_VENV_PYTHON = BENCHMARKS_ROOT / ".venv_unimernet" / "Scripts" / "python.exe"
UNIMERNET_MODEL_DIR = Path("D:/Environments/cache/models/MFR/unimernet_tiny")
_UNIMERNET_RUNNER = r'''
import sys, json, warnings
warnings.filterwarnings("ignore")
from omegaconf import OmegaConf
from PIL import Image
from unimernet.models.unimernet.unimernet import UniMERModel
from unimernet.processors.formula_processor import FormulaImageEvalProcessor

model_dir, image_path = sys.argv[1], sys.argv[2]
cfg = OmegaConf.load(model_dir + "/unimernet_tiny.yaml").model
cfg.model_config.model_name = model_dir
cfg.tokenizer_config.path = model_dir
cfg.pretrained = model_dir + "/pytorch_model.pth"
model = UniMERModel.from_config(cfg).eval()
proc = FormulaImageEvalProcessor.from_config(OmegaConf.create({"image_size": [192, 672]}))
img = Image.open(image_path).convert("RGB")
tensor = proc(img).unsqueeze(0)
out = model.generate({"image": tensor})
pred = out["pred_str"]
sys.stdout.write(pred[0] if isinstance(pred, list) else str(pred))
'''


def _unimernet_backend(device: str = "cpu") -> Callable[[Image.Image], OcrOutput]:
    """**UniMERNet** (`unimernet`, Apache-2.0) -> LaTeX, en venv aislado + subproceso.

    Alternativa externa real de `formula` (referencia SOTA en fórmulas
    manuscritas). Corre en `benchmarks/.venv_unimernet` porque su pin
    `transformers==4.42.4`/`numpy<2` choca con el venv del banco. Solo CPU: su
    `generate` no expone ruta GPU aquí (si se pide GPU, el runner ya lo marca
    `skipped` por `GPU_CAPABLE_BACKENDS`). Sin venv o sin pesos -> `skipped`.
    """
    if not UNIMERNET_VENV_PYTHON.is_file():
        raise ProviderUnavailable(
            f"falta el venv de unimernet; crear con: uv venv {UNIMERNET_VENV_PYTHON.parents[1]} "
            f"&& uv pip install --python {UNIMERNET_VENV_PYTHON} unimernet "
            f"&& uv pip install --python {UNIMERNET_VENV_PYTHON} 'numpy<2' 'pyarrow<16' 'datasets==2.21.0'")
    if not (UNIMERNET_MODEL_DIR / "pytorch_model.pth").is_file():
        raise ProviderUnavailable(f"faltan los pesos de unimernet en {UNIMERNET_MODEL_DIR}")

    def run(image: Image.Image) -> OcrOutput:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "formula.png"
            image.convert("RGB").save(path, format="PNG")
            start = time.perf_counter()
            proc = subprocess.run(
                [str(UNIMERNET_VENV_PYTHON), "-c", _UNIMERNET_RUNNER,
                 str(UNIMERNET_MODEL_DIR), str(path)],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900,
            )
            elapsed_ms = (time.perf_counter() - start) * 1000.0
        if proc.returncode != 0:
            raise RuntimeError(f"unimernet: {(proc.stderr or '').strip().splitlines()[-1:]}")
        return OcrOutput(text=proc.stdout, elapsed_ms=elapsed_ms,
                         extra={"engine": "unimernet", "model": "unimernet_tiny"})

    run.provider_effective = "cpu" if device == "cpu" else "cuda"
    return run


def _patch_pathlib_local_for_doclaynet() -> None:
    """Compatibilidad de checkpoints DocLayNet guardados en Python 3.14.

    Un peso de hantian referencia `pathlib._local.PosixPath`; en Windows/Python
    anterior a 3.14 esa ruta no existe y `PosixPath` tampoco se puede instanciar.
    El alias a `PurePosixPath` conserva la lectura del checkpoint sin tocar disco.
    """
    if sys.platform != "win32" or sys.version_info >= (3, 14) or "pathlib._local" in sys.modules:
        return
    import pathlib  # noqa: PLC0415
    import types  # noqa: PLC0415

    compat = types.ModuleType("pathlib._local")
    compat.Path = compat.PurePath = pathlib.PurePath
    compat.PurePosixPath = pathlib.PurePosixPath
    compat.PureWindowsPath = pathlib.PureWindowsPath
    compat.PosixPath = pathlib.PurePosixPath
    compat.WindowsPath = pathlib.PureWindowsPath
    sys.modules["pathlib._local"] = compat
    pathlib._local = compat


def _yolo_layout_backend(name: str, imgsz: int = 1024, device: str = "cpu") -> Callable[[Image.Image], OcrOutput]:
    """Detector YOLO documental (`ultralytics`) -> `extra["elements"]`.

    Mismo contrato que `_hf_layout_backend`: emite `element_type`, `score` y
    `bbox` de 4 puntos en el vocabulario de `score_layout`, y deja fuera las
    clases sin equivalencia declarada.

    ponytail: se cronometra `model.predict(...)` entero, que incluye el
    preprocesado interno de ultralytics; los adaptadores de `transformers`
    cronometran solo forward+post-proceso. La nota va en el README para no
    comparar peras con manzanas. Separarlo exige reimplementar el letterbox.
    """
    _patch_pathlib_local_for_doclaynet()
    try:
        from ultralytics import YOLO  # noqa: PLC0415 - import tardio (carga pesada)
    except ImportError as exc:
        raise ProviderUnavailable("pip install ultralytics (YOLO documental)") from exc

    weights = YOLO_LAYOUT_MODELS[name]
    try:
        model = YOLO(weights)
    except Exception as exc:  # noqa: BLE001 - pesos ausentes: es un `skipped`
        raise ProviderUnavailable(f"pesos YOLO no disponibles ({weights}): {exc}") from exc
    label_map = LAYOUT_DOCLAYNET_LABEL_TO_MODEL
    model_names = model.names
    class_names = tuple(str(model_names[key]) for key in sorted(model_names))
    if {name.strip().casefold() for name in class_names} != DOCLAYNET_CLASSES:
        raise ProviderUnavailable(
            f"{name}: clases {class_names!r} no coinciden con las 11 clases DocLayNet"
        )
    params_m = round(sum(p.numel() for p in model.model.parameters()) / 1e6, 1)

    def run(image: Image.Image) -> OcrOutput:
        # Ultralytics quiere `device=0` (o `"cpu"`), no `"gpu"`.
        ultralytics_device = "cpu" if device == "cpu" else "0"
        start = time.perf_counter()
        results = model.predict(image, imgsz=imgsz, conf=LAYOUT_AP_SCORE_FLOOR,
                                device=ultralytics_device, verbose=False)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        elements: list[dict] = []
        boxes: list[list[float]] = []
        names = results[0].names if results else {}
        for box, cls, conf in zip(
            results[0].boxes.xyxy.tolist(), results[0].boxes.cls.tolist(), results[0].boxes.conf.tolist()
        ):
            element_type = label_map.get(str(names.get(int(cls), "")).strip().lower())
            if element_type is None:
                continue  # clase sin equivalencia declarada: fuera de la metrica
            x1, y1, x2, y2 = (float(v) for v in box)
            elements.append({
                "element_type": element_type,
                "score": float(conf),
                "bbox": [[x1, y1], [x2, y1], [x2, y2], [x1, y2]],
            })
            boxes.append([x1, y1, x2, y2])
        return OcrOutput(
            text="", n_regions=len(elements), elapsed_ms=elapsed_ms,
            extra={"engine": "ultralytics", "model": weights, "params_m": params_m,
                   "classes": class_names,
                   "imgsz": imgsz, "elements": elements, "boxes": boxes},
        )

    run.provider_effective = "cpu" if device == "cpu" else "cuda"
    return run


# ---------------------------------------------------------------------------
# Alternativas reales de `orientation` / `text_line` / `rectification`
# (`onnxruntime` sobre los pesos canonicos de PaddleOCR)
# ---------------------------------------------------------------------------
# `pyocrust` corre estas tres tareas por el runtime Rust de `oar-ocr`; aqui el
# **mismo** `.onnx` se ejecuta con `onnxruntime` en Python, reproduciendo el
# preprocesado/postprocesado documentado por PaddleOCR. Es la alternativa del
# motor de referencia: mismos pesos, distinto runtime (Rust vs onnxruntime).
#
# `.onnx` de cada alternativa dentro del directorio de modelos de `pyocrust`
# (`~/.oar` por defecto). Si falta el fichero, el backend queda `skipped`.
ONNX_MODEL_FILES = {
    "lcnet_doc_ori": "pp-lcnet_x1_0_doc_ori.onnx",
    "lcnet_textline_ori": "pp-lcnet_x1_0_textline_ori.onnx",
    "uvdoc": "uvdoc.onnx",
    # Mismo `.onnx` que `pyocrust_seal` (deteccion de sellos sobre `onnxruntime`).
    "seal_det": "pp-ocrv4_mobile_seal_det.onnx",
}

# Pesos del clasificador de orientacion de linea de **RapidOCR** (proyecto RapidAI),
# un modelo distinto del PP-LCNet del banco. Vive dentro del paquete instalado
# (venv del repo, un nivel por encima de `benchmarks/`).
RAPIDOCR_MOBILE_CLS_ONNX = (
    BENCHMARKS_ROOT.parent / ".venv" / "Lib" / "site-packages"
    / "rapidocr" / "models" / "ch_ppocr_mobile_v2.0_cls_mobile.onnx"
)

# ImageNet en orden **RGB** (el que documenta PP-LCNet; `oar-ocr` lo confirma).
_LCNET_MEAN = (0.485, 0.456, 0.406)
_LCNET_STD = (0.229, 0.224, 0.225)

# Postproceso DB del detector de sellos (defaults de PaddleOCR que reproduce
# `oar-ocr`). `LIMIT` es el lado mayor al que se reescala la pagina.
_SEAL_DET_LIMIT = 960
_SEAL_DET_THRESH = 0.3
_SEAL_DET_BOX_THRESH = 0.5
_SEAL_DET_UNCLIP = 1.0
_SEAL_DET_MIN_AREA = 64.0


def _onnx_model_path(name: str) -> Path:
    """Ruta del `.onnx` de una alternativa dentro del models dir de `pyocrust`."""
    import pyocrust  # noqa: PLC0415

    return Path(pyocrust.resolve_models_dir()) / ONNX_MODEL_FILES[name]


def _load_onnx_session(name: str):
    """`InferenceSession` de CPU del `.onnx` de la alternativa (o `ProviderUnavailable`)."""
    try:
        import onnxruntime as ort  # noqa: PLC0415 - import tardio (carga pesada)
    except ImportError as exc:
        raise ProviderUnavailable("pip install onnxruntime") from exc
    path = _onnx_model_path(name)
    if not path.is_file():
        raise ProviderUnavailable(f"falta {ONNX_MODEL_FILES[name]} en {path.parent} (modelo no descargado)")
    return ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])


def _cv2_resize(image: Image.Image, size_wh: tuple[int, int], interpolation: int):
    """Resize con OpenCV devolviendo RGB (mismo motor que PaddleOCR/`oar-ocr`).

    PIL y `cv2` no coinciden pixel a pixel; el runtime Rust de `oar-ocr` usa un
    filtro con antialias que, medido sobre el GT sintetico, reproduce `INTER_AREA`
    (los clasificadores aciertan 8/8 igual que `pyocrust`; `PIL.BILINEAR` falla 1).
    """
    import cv2  # noqa: PLC0415
    import numpy as np  # noqa: PLC0415

    bgr = np.asarray(image.convert("RGB"))[:, :, ::-1]
    resized = cv2.resize(bgr, size_wh, interpolation=interpolation)
    return np.ascontiguousarray(resized[:, :, ::-1])


def _lcnet_tensor(image: Image.Image, input_hw: tuple[int, int], resize_short: int | None):
    """Tensor CHW normalizado (ImageNet RGB) que consume un clasificador PP-LCNet.

    Reproduce el preprocesado de PaddleOCR que confirma `oar-ocr`:

    * `resize_short` no nulo -> reescala el lado corto a `resize_short` (ratio
      conservado) y recorta al centro `input_hw` (doc/table orientation, 224x224).
    * `resize_short` nulo -> reescala directo a `input_hw` (H, W) sin recorte
      (text line orientation, 80x160).

    Se mantiene fuera del cronometro, simetrico con los demas adaptadores
    no-`pyocrust` (B4/D12).
    """
    import cv2  # noqa: PLC0415
    import numpy as np  # noqa: PLC0415

    out_h, out_w = input_hw
    w, h = image.size
    if resize_short is not None:
        scale = resize_short / min(w, h)
        new_w = max(round(w * scale), out_w)
        new_h = max(round(h * scale), out_h)
        resized = _cv2_resize(image, (new_w, new_h), cv2.INTER_AREA)
        x1 = (new_w - out_w) // 2
        y1 = (new_h - out_h) // 2
        resized = resized[y1:y1 + out_h, x1:x1 + out_w]
    else:
        resized = _cv2_resize(image, (out_w, out_h), cv2.INTER_AREA)
    arr = resized.astype(np.float32) / 255.0
    arr = (arr - np.asarray(_LCNET_MEAN, dtype=np.float32)) / np.asarray(_LCNET_STD, dtype=np.float32)
    return np.ascontiguousarray(arr.transpose(2, 0, 1)[None], dtype=np.float32)


def _lcnet_classify_backend(model_name: str, labels: Sequence[str],
                            input_hw: tuple[int, int], resize_short: int | None) -> Callable[[Image.Image], OcrOutput]:
    """Clasificador PP-LCNet (orientacion de pagina/linea) via `onnxruntime`.

    Emite el mismo contrato que `pyocrust`: `text`/`extra["label"]` = etiqueta
    ganadora y `extra["orientations"]` = lista `{class_id, label, score}`.
    """
    import numpy as np  # noqa: PLC0415

    session = _load_onnx_session(model_name)
    input_name = session.get_inputs()[0].name

    def run(image: Image.Image) -> OcrOutput:
        tensor = _lcnet_tensor(image, input_hw, resize_short)
        start = time.perf_counter()
        logits = np.asarray(session.run(None, {input_name: tensor})[0][0], dtype=np.float64)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        probs = np.exp(logits - logits.max())
        probs /= probs.sum()
        order = np.argsort(probs)[::-1]
        orientations = [
            {"class_id": int(i), "label": labels[i], "score": float(probs[i])} for i in order
        ]
        top = int(order[0])
        return OcrOutput(
            text=labels[top], mean_confidence=float(probs[top]), elapsed_ms=elapsed_ms,
            extra={"engine": "onnxruntime", "model": model_name,
                   "label": labels[top], "score": float(probs[top]),
                   "orientations": orientations},
        )

    return run


def _uvdoc_backend(device: str = "cpu") -> Callable[[Image.Image], OcrOutput]:
    """UVDoc (rectificado de perspectiva) via `onnxruntime`.

    Preprocesado: resize bilineal (`cv2.INTER_LINEAR`, el de PaddleOCR) a 512x512,
    escala a [0, 1] y canales en **BGR** (lo que documenta `oar-ocr` para UVDoc).
    La salida `[3, H, W]` es una imagen rectificada en BGR: se reescala a [0, 255],
    se reordena a RGB y se devuelve al tamano original. Emite el PNG en
    `extra["image"]` (lo que consume `score_rectification`).
    """
    import cv2  # noqa: PLC0415
    import numpy as np  # noqa: PLC0415

    session = _load_onnx_session("uvdoc")
    input_name = session.get_inputs()[0].name
    target = 512

    def run(image: Image.Image) -> OcrOutput:
        orig_w, orig_h = image.size
        resized = _cv2_resize(image, (target, target), cv2.INTER_LINEAR)
        bgr = np.ascontiguousarray(resized[:, :, ::-1].astype(np.float32).transpose(2, 0, 1)[None] / 255.0)
        start = time.perf_counter()
        out = np.asarray(session.run(None, {input_name: bgr})[0][0], dtype=np.float32)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        channels = np.clip(out * 255.0, 0.0, 255.0)
        # Salida en BGR -> RGB: canal 0 = B, canal 2 = R.
        rectified = np.ascontiguousarray(channels[::-1].transpose(1, 2, 0)).astype(np.uint8)
        if (orig_w, orig_h) != (rectified.shape[1], rectified.shape[0]):
            rectified = _cv2_resize(Image.fromarray(rectified, "RGB"), (orig_w, orig_h), cv2.INTER_LINEAR).astype(np.uint8)
        buffer = io.BytesIO()
        Image.fromarray(rectified, "RGB").save(buffer, format="PNG")
        return OcrOutput(
            text="", elapsed_ms=elapsed_ms,
            extra={"engine": "onnxruntime", "model": "uvdoc", "image": buffer.getvalue()},
        )

    return run


def _rapidocr_mobile_cls_backend(device: str = "cpu") -> Callable[[Image.Image], OcrOutput]:
    """Clasificador de orientacion de linea 0/180 de **RapidOCR** (`ch_ppocr_mobile_v2.0_cls`).

    Modelo **distinto** del banco: no es el PP-LCNet de PaddleOCR, es la red mobile
    `cls` de PP-OCRv2 distribuida por el proyecto **RapidAI** (Apache-2.0), ya en el
    venv de RapidOCR. Aporta un tercero realmente independiente a `text_line`.

    Preprocesado copiado de RapidOCR: resize a `[3, 48, 192]` (W = 192), escala a
    [0, 1] y normalizacion ImageNet RGB. Salida `[N, 2]`: `label_list = ["0","180"]`.
    """
    import numpy as np  # noqa: PLC0415

    try:  # onnxruntime + pesos no conllevan carga de pyocrust
        import onnxruntime as ort  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover - entorno sin onnxruntime
        raise ProviderUnavailable("pip install onnxruntime") from exc
    path = RAPIDOCR_MOBILE_CLS_ONNX
    if not path.is_file():
        raise ProviderUnavailable(f"falta {path.name} (RapidOCR no instalado)")
    session = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
    input_name = session.get_inputs()[0].name
    labels = ("0", "180")

    def run(image: Image.Image) -> OcrOutput:
        tensor = _lcnet_tensor(image, (48, 192), None)
        start = time.perf_counter()
        logits = np.asarray(session.run(None, {input_name: tensor})[0][0], dtype=np.float64)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        probs = np.exp(logits - logits.max())
        probs /= probs.sum()
        order = np.argsort(probs)[::-1]
        top = int(order[0])
        return OcrOutput(
            text=labels[top], mean_confidence=float(probs[top]), elapsed_ms=elapsed_ms,
            extra={"engine": "rapidocr", "model": "ch_ppocr_mobile_v2.0_cls",
                   "label": labels[top], "score": float(probs[top]),
                   "orientations": [{"class_id": int(i), "label": labels[i], "score": float(probs[i])}
                                    for i in order]},
        )

    run.provider_effective = "cpu"
    return run


def _easyocr_rotation_backend(device: str = "cpu") -> Callable[[Image.Image], OcrOutput]:
    """Orientacion de pagina por **EasyOCR** (proyecto distinto, no PaddleOCR).

    No es un clasificador dedicado: reconoce el texto de la pagina en las cuatro
    rotaciones 0/90/180/270 con el recognizer propio de EasyOCR y elige la rotacion
    que **aplicada** deja el texto legible (mayor confianza media). Es la heuristica
    que un pipeline OCR real usa cuando no tiene clasificador dedicado; se declara
    como tal en el informe (`.venv` con los pesos CRAFT+latin ya en cache).

    Emite `label` = la rotacion de **correccion** en grados (la que hay que aplicar),
    la misma convencion que el GT del banco de `orientation`.
    """
    import numpy as np  # noqa: PLC0415

    try:
        import easyocr  # noqa: PLC0415 - import tardio (carga torch)
    except ImportError as exc:
        raise ProviderUnavailable("pip install easyocr") from exc
    if device != "cpu":
        raise ProviderUnavailable("easyocr_rotation corre solo en CPU en este banco")
    # `gpu=False`: solo CPU (regla de honestidad del banco). Los pesos deben estar
    # en cache; `download_enabled=False` evita bajadas silenciosas en el run.
    try:
        reader = easyocr.Reader(["en"], gpu=False, download_enabled=False, verbose=False)
    except Exception as exc:  # noqa: BLE001 - pesos ausentes: es un `skipped`
        raise ProviderUnavailable(f"easyocr: pesos no disponibles en cache ({exc})") from exc
    angles = (0, 90, 180, 270)

    def run(image: Image.Image) -> OcrOutput:
        start = time.perf_counter()
        # Convencion del banco: la etiqueta es la rotacion a APLICAR para enderezar.
        # Si la pagina esta girada `a`, aplicarle `(360-a)%360` la endereza.
        corrections = {angle: (360 - angle) % 360 for angle in angles}
        scores = {}
        for angle in angles:
            upright = image.rotate(angle, expand=True) if angle else image
            arr = np.asarray(upright.convert("RGB"))
            try:
                detections = reader.readtext(arr, detail=1, paragraph=False)
            except Exception:  # noqa: BLE001
                detections = []
            vals = [float(d[2]) for d in detections if len(d) > 2]
            scores[angle] = float(sum(vals) / len(vals)) if vals else 0.0
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        best_angle = max(scores, key=scores.get)
        label = str(corrections[best_angle])
        return OcrOutput(
            text=label, mean_confidence=scores[best_angle], elapsed_ms=elapsed_ms,
            extra={"engine": "easyocr", "model": "craft_mlt_25k+latin_g2 (recognizer)",
                   "label": label, "score": scores[best_angle],
                   "rotations": {str(a): corrections[a] for a in angles},
                   "scores": {str(a): scores[a] for a in angles},
                   "note": "no es clasificador dedicado: elige la rotacion de mayor confianza OCR"},
        )

    run.provider_effective = "cpu"
    return run


def _opencv_perspective_backend(device: str = "cpu") -> Callable[[Image.Image], OcrOutput]:
    """Rectificacion geometrica CLASICA con OpenCV (linea base, NO una red).

    Competidor **independiente** de UVDoc/PaddleOCR en el sentido estricto del
    termino: no usa pesos PaddleOCR (no usa pesos de ningun tipo). Detecta el
    contorno del documento (Canny -> contorno mayor -> `approxPolyDP`) y aplica la
    homografia de 4 esquinas a la pagina A4.

    Se declara como **linea base clasica**, no un SOTA: sobre una homografia de
    perspectiva severa recupera poco (SSIM bajo); sirve de suelo de comparacion,
    no de techo. Emite el PNG rectificado en `extra["image"]`, igual que `uvdoc`.
    """
    import cv2  # noqa: PLC0415
    import numpy as np  # noqa: PLC0415

    def _order(points: "np.ndarray") -> "np.ndarray":
        pts = points.reshape(4, 2).astype(np.float32)
        s = pts.sum(axis=1)
        d = np.diff(pts, axis=1).ravel()
        return np.array([pts[np.argmin(s)], pts[np.argmin(d)],
                         pts[np.argmax(s)], pts[np.argmax(d)]], dtype=np.float32)

    def run(image: Image.Image) -> OcrOutput:
        arr = np.asarray(image.convert("RGB"))[:, :, ::-1]  # RGB -> BGR
        start = time.perf_counter()
        gray = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
        edges = cv2.dilate(cv2.Canny(cv2.GaussianBlur(gray, (5, 5), 0), 50, 150),
                           np.ones((3, 3), np.uint8))
        cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        h, w = arr.shape[:2]
        if cnts:
            c = max(cnts, key=cv2.contourArea)
            approx = cv2.approxPolyDP(cv2.convexHull(c), 0.02 * cv2.arcLength(c, True), True)
            if len(approx) != 4:
                approx = cv2.boxPoints(cv2.minAreaRect(c)).reshape(-1, 1, 2)
            src = _order(approx.reshape(-1, 2))
            dst = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], np.float32)
            rectified = cv2.warpPerspective(arr, cv2.getPerspectiveTransform(src, dst), (w, h))
        else:  # sin contorno: se devuelve la entrada sin tocar (rectificacion nula)
            rectified = arr
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        buffer = io.BytesIO()
        Image.fromarray(rectified[:, :, ::-1], "RGB").save(buffer, format="PNG")
        return OcrOutput(
            text="", elapsed_ms=elapsed_ms,
            extra={"engine": "opencv", "model": "perspective-4corner (baseline)",
                   "image": buffer.getvalue()},
        )

    run.provider_effective = "cpu"
    return run


def _paddle_det_boxes(prob, ratio: float, thresh: float, box_thresh: float,
                      unclip: float, min_area: float) -> list[list[float]]:
    """Postproceso DB de PaddleOCR: mapa de probabilidad -> cajas.

    `prob` es el mapa `(H, W)` ya en [0, 1]; `ratio` deshace el resize al tamaño
    original. Reproduce el pipeline documentado por PaddleOCR: binariza por
    `thresh`, extrae contornos, puntúa cada caja con la media del mapa **sobre los
    píxeles del contorno** (no el rectángulo relleno: el sello es un anillo), y
    `unclip` expande el `minAreaRect` sobre su centro.
    """
    import cv2  # noqa: PLC0415
    import numpy as np  # noqa: PLC0415

    mask = (prob > thresh).astype(np.uint8)
    contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    height, width = prob.shape
    boxes: list[list[float]] = []
    for contour in contours:
        rect = cv2.minAreaRect(contour)
        if rect[1][0] * rect[1][1] < min_area:
            continue
        points = contour.reshape(-1, 2)
        inside = prob[points[:, 1].clip(0, height - 1), points[:, 0].clip(0, width - 1)]
        if float(inside.mean()) < box_thresh:
            continue
        quad = cv2.boxPoints(rect)
        center = quad.mean(0)
        quad = (center + (quad - center) * unclip) / ratio
        boxes.append([float(quad[:, 0].min()), float(quad[:, 1].min()),
                      float(quad[:, 0].max()), float(quad[:, 1].max())])
    return boxes


def _onnx_seal_det_backend(device: str = "cpu") -> Callable[[Image.Image], OcrOutput]:
    """Detección de sellos: **mismos pesos** que `pyocrust_seal`, vía `onnxruntime`.

    Alternativa del motor de referencia (Rust `oar-ocr` vs `onnxruntime`): el
    mismo `.onnx` (`pp-ocrv4_mobile_seal_det.onnx`, Apache-2.0) con el preprocesado
    y postproceso DB de PaddleOCR. A diferencia de los clasificadores PP-LCNet, la
    entrada va en **BGR y sin normalizar** (0..255), que es lo que documenta la
    config de inferencia de este detector.
    """
    import cv2  # noqa: PLC0415
    import numpy as np  # noqa: PLC0415

    session = _load_onnx_session("seal_det")
    input_name = session.get_inputs()[0].name

    def run(image: Image.Image) -> OcrOutput:
        rgb = np.asarray(image.convert("RGB"))
        height, width = rgb.shape[:2]
        ratio = _SEAL_DET_LIMIT / max(height, width)
        new_h = max(32, int(round(height * ratio / 32)) * 32)
        new_w = max(32, int(round(width * ratio / 32)) * 32)
        bgr = cv2.resize(rgb[:, :, ::-1].astype(np.float32), (new_w, new_h))
        tensor = np.ascontiguousarray(bgr.transpose(2, 0, 1)[None])
        start = time.perf_counter()
        prob = np.asarray(session.run(None, {input_name: tensor})[0][0, 0], dtype=np.float32)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        boxes = _paddle_det_boxes(prob, ratio, _SEAL_DET_THRESH, _SEAL_DET_BOX_THRESH,
                                  _SEAL_DET_UNCLIP, _SEAL_DET_MIN_AREA)
        return OcrOutput(
            text="", n_regions=len(boxes), elapsed_ms=elapsed_ms,
            extra={"engine": "onnxruntime", "model": "pp-ocrv4_mobile_seal_det",
                   "boxes": boxes},
        )

    run.provider_effective = "cpu" if device == "cpu" else "cuda"
    return run


def _predictor_output(task: str, result: dict, elapsed_ms: float) -> OcrOutput:
    """`dict` devuelto por una tarea de `TaskPredictor` -> `OcrOutput` común.

    `text` lleva lo que la tarea emite como texto (LaTeX, etiqueta de orientación,
    gramática de tabla) y `extra` sus estructuras nativas (cajas, elementos,
    imagen rectificada), que es lo que consumen las métricas por feature.
    """
    extra: dict = {"task": task}
    if task == "layout_detection":
        elements = list(result.get("elements") or [])
        extra["elements"] = elements
        extra["boxes"] = [list(_quad_to_bbox(e["bbox"])) for e in elements if e.get("bbox")]
        return OcrOutput(text="", n_regions=len(elements), elapsed_ms=elapsed_ms, extra=extra)
    if task == "table_structure_recognition":
        structures = [str(token) for token in (result.get("structures") or [])]
        extra["structures"] = structures
        extra["bboxes"] = list(result.get("bboxes") or [])
        return OcrOutput(text="".join(structures), elapsed_ms=elapsed_ms, extra=extra)
    if task in ("document_orientation", "text_line_orientation"):
        orientations = list(result.get("orientations") or [])
        top = orientations[0] if orientations else {}
        label = str(top.get("label", ""))
        score = float(top.get("score", 0.0) or 0.0)
        extra.update({"label": label, "score": score, "orientations": orientations})
        return OcrOutput(text=label, mean_confidence=score, elapsed_ms=elapsed_ms, extra=extra)
    if task == "document_rectification":
        extra["image"] = result.get("image") or b""
        return OcrOutput(text="", elapsed_ms=elapsed_ms, extra=extra)
    if task in ("text_detection", "seal_text_detection"):
        detections = list(result.get("detections") or [])
        extra["boxes"] = [list(_quad_to_bbox(d["bbox"])) for d in detections if d.get("bbox")]
        return OcrOutput(text="", n_regions=len(detections), elapsed_ms=elapsed_ms, extra=extra)
    if task == "formula_recognition":
        return OcrOutput(text=str(result.get("formula", "") or ""), elapsed_ms=elapsed_ms, extra=extra)
    return OcrOutput(text="", elapsed_ms=elapsed_ms, extra=extra)


def _task_predictor_backend(task: str, device: str = "cpu", **options: object) -> Callable[[Image.Image], OcrOutput]:
    """Adaptador a **una tarea suelta** de `pyocrust` (`TaskPredictor`, S2.4).

    Sin pipeline de página: el modelo recibe la imagen tal cual (página, recorte
    de tabla, línea, fórmula). Si el modelo registrado de la tarea no está en
    disco, `TaskPredictor` falla y el backend queda `skipped` con su motivo.
    """
    import pyocrust  # noqa: PLC0415

    predictor = pyocrust.TaskPredictor(task=task, device=device, **options)

    def run(image: Image.Image) -> OcrOutput:
        data = _image_bytes(image)
        start = time.perf_counter()
        result = predictor.predict(data)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return _predictor_output(task, result, elapsed_ms)

    run.provider_effective = getattr(predictor, "provider_effective", None)
    return run


# nombre -> factoría (el preset por defecto es el de `pp_ocrv6` = Tiny). Las de
# `pyocrust` reciben el `device` resuelto (`cpu`/`auto`); el resto lo ignoran.
PROVIDERS: dict[str, Callable[..., Callable[[Image.Image], OcrOutput]]] = {
    "pyocrust": lambda device="cpu": _pyocrust_backend("pp_ocrv6", device=device),
    "pyocrust_structure": lambda device="cpu": _pyocrust_backend("pp_structurev3", device=device),
    "pyocrust_formula": lambda device="cpu": _pyocrust_backend("pp_structurev3", formula_only=True, device=device),
    "pyocrust_formulanet": lambda device="cpu": _pyocrust_formula_variant_backend("pp-formulanet-s.onnx", device=device),
    # Variantes PP-FormulaNet del registro ModelScope `greatv/oar-ocr` (oar-ocr-core
    # registry.rs): mismo adaptador, distinto `.onnx`. Se saltan si falta el fichero.
    "pyocrust_formulanet_l": lambda device="cpu": _pyocrust_formula_variant_backend("pp-formulanet-l.onnx", device=device),
    "pyocrust_formulanet_pluss": lambda device="cpu": _pyocrust_formula_variant_backend("pp-formulanet_plus-s.onnx", device=device),
    "pyocrust_formulanet_plusm": lambda device="cpu": _pyocrust_formula_variant_backend("pp-formulanet_plus-m.onnx", device=device),
    "pyocrust_formulanet_plusl": lambda device="cpu": _pyocrust_formula_variant_backend("pp-formulanet_plus-l.onnx", device=device),
    "pyocrust_indra": lambda device="cpu": _pyocrust_backend("indra", device=device),
    # Tareas sueltas de `TaskPredictor`: cada banco de feature aporta su GT.
    "pyocrust_layout": lambda device="cpu": _task_predictor_backend("layout_detection", device=device, score_threshold=LAYOUT_AP_SCORE_FLOOR),
    "pyocrust_table": lambda device="cpu": _task_predictor_backend("table_structure_recognition", device=device),
    "pyocrust_orientation": lambda device="cpu": _task_predictor_backend("document_orientation", device=device),
    "pyocrust_textline": lambda device="cpu": _task_predictor_backend("text_line_orientation", device=device),
    "pyocrust_rectify": lambda device="cpu": _task_predictor_backend("document_rectification", device=device),
    "pyocrust_seal": lambda device="cpu": _task_predictor_backend("seal_text_detection", device=device),
    # Alternativas reales de orientation/text_line/rectification (`onnxruntime`
    # sobre los MISMO pesos de PaddleOCR que usa `pyocrust`; solo CPU).
    "lcnet_doc_ori": lambda device="cpu": _lcnet_classify_backend("lcnet_doc_ori", ["0", "90", "180", "270"], (224, 224), 256),
    "lcnet_textline_ori": lambda device="cpu": _lcnet_classify_backend("lcnet_textline_ori", ["0", "180"], (80, 160), None),
    "uvdoc": lambda device="cpu": _uvdoc_backend(),
    # Alternativas realmente INDEPENDIENTES (no pesos PaddleOCR):
    #   * `rapidocr_mobile_cls` — red mobile cls de PP-OCRv2 del proyecto RapidAI
    #      -> `text_line` (0/180). Modelo distinto, no el PP-LCNet del banco.
    #   * `easyocr_rotation` — orientacion de pagina por reconocimiento en 4
    #      rotaciones con el recognizer de EasyOCR -> `orientation`. No es un
    #      clasificador dedicado; el informe lo declara como heuristica.
    "rapidocr_mobile_cls": lambda device="cpu": _rapidocr_mobile_cls_backend(device=device),
    "easyocr_rotation": lambda device="cpu": _easyocr_rotation_backend(device=device),
    # Alternativa a `rectification` SIN pesos PaddleOCR y sin red: linea base
    # geometrica clasica (OpenCV). El informe la declara como baseline, no SOTA.
    "opencv_perspective": lambda device="cpu": _opencv_perspective_backend(device=device),
    # Alternativa real de `seal`: mismos pesos que `pyocrust_seal` (PP-OCRv4 seal
    # det), otro runtime (`onnxruntime`). Deteccion de cajas -> `extra["boxes"]`.
    "onnx_seal_det": lambda device="cpu": _onnx_seal_det_backend(device=device),
    # Alternativas reales de `layout` (`transformers`, offline desde la cache HF):
    # RT-DETR (docling heron-101) y Deformable-DETR (DocLayNet). Solo CPU.
    "docling_heron_101": lambda device="cpu": _hf_layout_backend(LAYOUT_HF_MODELS["docling_heron_101"]),
    "deformable_detr": lambda device="cpu": _hf_layout_backend(LAYOUT_HF_MODELS["deformable_detr"]),
    "paddle_latex_ocr": _paddle_latex_ocr_backend,
    # Alternativa real de `formula`: UniMERNet (Apache-2.0) en su venv aislado,
    # por subproceso (solo CPU). Pesos `unimernet_tiny` del cache local.
    "unimernet": _unimernet_backend,
    "rapidocr": _rapidocr_backend,
    "easyocr": _easyocr_backend,
    "tesseract": _tesseract_backend,
    # Alternativa real al `table_structure_recognition` de `pyocrust` en el banco
    # de `table`: TATR vía `transformers` (solo CPU; `--device gpu` -> `skipped`).
    "tatr": _tatr_backend,
    # Pipelines documentales completos para `full_page` (emiten Markdown de pagina).
    # `pp_structurev3_api`: PaddleOCR PP-StructureV3 en Python (Apache-2.0).
    # `docling`: docling (MIT) en su venv aislado, por subproceso (solo CPU).
    "pp_structurev3_api": lambda device="cpu": _pp_structurev3_api_backend(device=device),
    "docling": lambda device="cpu": _docling_backend(device=device),
    # Alternativas externas al `table_structure_recognition` de `pyocrust` (además
    # de TATR): SLANet oficial de PaddleOCR y TableFormer de docling. Solo CPU.
    "paddleocr_slanet": lambda device="cpu": _paddleocr_slanet_backend(device=device),
    "docling_tableformer": lambda device="cpu": _docling_tableformer_backend(device=device),
}

# Una factoría por checkpoint; captura cada nombre para no cerrar sobre el último.
PROVIDERS.update({
    name: (lambda name=name, device="cpu": _yolo_layout_backend(name, device=device))
    for name in YOLO_LAYOUT_MODELS
})
# Alias de nomenclatura: los bancos históricos usan PROVIDERS.
BACKENDS = PROVIDERS


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def _describe_runtime() -> dict:
    import pyocrust  # noqa: PLC0415

    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "pyocrust": pyocrust.__version__,
        "available_providers": available_providers(),
    }


TASK_TYPES = {"pyocrust_structure": "structure", "pyocrust_formula": "formula", "pyocrust_formulanet": "formula",
              "pyocrust_formulanet_l": "formula", "pyocrust_formulanet_pluss": "formula",
              "pyocrust_formulanet_plusm": "formula", "pyocrust_formulanet_plusl": "formula",
              "pyocrust_indra": "full_page",
              # Tareas sueltas: su `task_type` es el nombre de su banco de feature.
              "pyocrust_layout": "layout", "pyocrust_table": "table",
              # Alternativas reales de `layout` (transformers): mismo task_type.
              "docling_heron_101": "layout", "deformable_detr": "layout",
              "pyocrust_orientation": "orientation", "pyocrust_textline": "text_line",
              "pyocrust_rectify": "rectification", "pyocrust_seal": "seal",
              # Alternativas reales de esas tareas (`onnxruntime`): mismo task_type.
              "lcnet_doc_ori": "orientation", "lcnet_textline_ori": "text_line",
              "uvdoc": "rectification", "onnx_seal_det": "seal",
              # Alternativas independientes (no pesos PaddleOCR) de esas tareas.
              "rapidocr_mobile_cls": "text_line", "easyocr_rotation": "orientation",
              "opencv_perspective": "rectification",
              # Alternativa real de `table` (TATR): estructura de tabla, mismo GT.
              "tatr": "table",
              # Alternativa real de `formula`: UniMERNet (LaTeX, mismo GT anotado).
              "unimernet": "formula",
              # Otras alternativas reales de `table`: SLANet (PaddleOCR) y
              # TableFormer (docling), misma GT que el especialista.
              "paddleocr_slanet": "table", "docling_tableformer": "table",
              # Pipelines documentales completos: mismo task_type que el banco.
              "pp_structurev3_api": "full_page", "docling": "full_page"}
MODEL_NAMES = {"pyocrust": ("pp_ocrv6", "tiny"), "pyocrust_structure": ("pp_structurev3", "default"),
               "pyocrust_formula": ("pp_structurev3", "pp-formulanet-s"), "pyocrust_formulanet": ("pp-formulanet-s", "direct"),
               "pyocrust_formulanet_l": ("pp-formulanet-l", "direct"),
               "pyocrust_formulanet_pluss": ("pp-formulanet_plus-s", "direct"),
               "pyocrust_formulanet_plusm": ("pp-formulanet_plus-m", "direct"),
               "pyocrust_formulanet_plusl": ("pp-formulanet_plus-l", "direct"),
               "pyocrust_indra": ("indra", "math"),
               "pyocrust_layout": ("pp-doclayoutv3", "130M"),
               # Alternativas reales de `layout` (transformers, DocLayNet/RT-DETR).
               "docling_heron_101": ("docling-layout-heron-101", "default"),
               "deformable_detr": ("deformable-detr-DocLayNet", "default"),
               "pyocrust_table": ("slanet_plus", "default"),
               "pyocrust_orientation": ("pp-lcnet_x1_0_doc_ori", "6.8M"),
               "pyocrust_textline": ("pp-lcnet_x1_0_textline_ori", "6.8M"),
               "pyocrust_rectify": ("uvdoc", "31.7M"),
               "pyocrust_seal": ("pp-ocrv4_mobile_seal_det", "4.8M"),
               # Alternativas reales (PaddleOCR via onnxruntime): mismo peso, otro runtime.
               "lcnet_doc_ori": ("pp-lcnet_x1_0_doc_ori", "onnxruntime"),
               "lcnet_textline_ori": ("pp-lcnet_x1_0_textline_ori", "onnxruntime"),
               "uvdoc": ("uvdoc", "onnxruntime"),
               "onnx_seal_det": ("pp-ocrv4_mobile_seal_det", "onnxruntime"),
               # Alternativas independientes (modelo de otro proyecto, no PaddleOCR).
               "rapidocr_mobile_cls": ("ch_ppocr_mobile_v2.0_cls", "rapidocr"),
               "easyocr_rotation": ("craft_mlt_25k+latin_g2", "easyocr"),
               "opencv_perspective": ("perspective-4corner", "baseline (OpenCV, sin pesos)"),
               # Alternativa real de `table` (TATR, `transformers`).
               "tatr": ("table-transformer-structure-recognition", "default"),
               # Alternativa real de `formula`: UniMERNet (`unimernet`), pesos tiny.
               "unimernet": ("unimernet", "tiny"),
               # Otras alternativas de `table`: SLANet (PaddleOCR, Apache-2.0) y
               # TableFormer (docling, MIT).
               "paddleocr_slanet": ("SLANet_plus", "paddleocr"),
               "docling_tableformer": ("tableformer", "docling"),
               "pp_structurev3_api": ("PP-StructureV3", "paddleocr"),
               "docling": ("docling-default", "pipeline")}

# `params_m` conocido por mediciones previas, el smoke limitado y los ejemplos
# explícitos del criterio; para los demás se deja desconocido hasta medir el
# checkpoint, en vez de asumir el tamaño nominal de un YOLO base.
_YOLO_PARAMS_M = {
    "omoured_v10x": 31.7,
    "omoured_v10b": 20.5,
    "hantian_v11m": 21.8,
    "hantian_v11n": 2.6,
    "armaggheddon_y26n": 2.6,
    "armaggheddon_y26m": 21.8,
}
MODEL_NAMES.update({
    backend: (
        f"{backend.rsplit('_', 1)[0]}/{backend.rsplit('_', 1)[1][:-1]}-"
        f"{backend.rsplit('_', 1)[1][-1]}",
        f"{_YOLO_PARAMS_M[backend]:.1f}M" if backend in _YOLO_PARAMS_M else None,
    )
    for backend in YOLO_LAYOUT_MODELS
})
TASK_TYPES.update({backend: "layout" for backend in YOLO_LAYOUT_MODELS})
# Banco de feature al que pertenece cada backend conocido (columna `feature`).
FEATURE_TYPES = {"pyocrust_structure": "full_page", "pyocrust_indra": "full_page",
                 "pyocrust_formula": "formula", "pyocrust_formulanet": "formula",
                 "pyocrust_formulanet_l": "formula", "pyocrust_formulanet_pluss": "formula",
                 "pyocrust_formulanet_plusm": "formula", "pyocrust_formulanet_plusl": "formula",
                 "pyocrust_layout": "layout", "pyocrust_table": "table",
                 # Alternativas reales de `layout` (transformers): mismo banco.
                 "docling_heron_101": "layout", "deformable_detr": "layout",
              "pyocrust_orientation": "orientation", "pyocrust_textline": "text_line",
                 "pyocrust_rectify": "rectification", "pyocrust_seal": "seal",
                 # Alternativas reales de esas tareas (`onnxruntime`): mismo banco.
                 "lcnet_doc_ori": "orientation", "lcnet_textline_ori": "text_line",
                 "uvdoc": "rectification", "onnx_seal_det": "seal",
                 # Alternativas independientes (no pesos PaddleOCR) de esas tareas.
                 "rapidocr_mobile_cls": "text_line", "easyocr_rotation": "orientation",
                 "opencv_perspective": "rectification",
                 # Alternativa real del banco `table` (TATR, `transformers`).
                 "tatr": "table",
                 # Alternativa real del banco `formula` (UniMERNet).
                 "unimernet": "formula",
                 # Otras alternativas reales de `table` (SLANet / TableFormer).
                 "paddleocr_slanet": "table", "docling_tableformer": "table",
                 # Pipelines documentales completos: mismo banco.
                 "pp_structurev3_api": "full_page", "docling": "full_page"}
FEATURE_TYPES.update({backend: "layout" for backend in YOLO_LAYOUT_MODELS})

# `formula` compara motores que **emiten LaTeX**. Los OCR de texto no tienen
# módulo de fórmulas y no son equiparables (su `latex_sim` mide texto plano
# contra GT LaTeX), así que no entran en los informes de esa feature. Ver el
# docstring de `features/formula/bank.py`.
FORMULA_BACKENDS_EXCLUDED = frozenset({"rapidocr", "easyocr", "tesseract"})


def applicable_rows(feature: str, rows: Iterable[dict]) -> list[dict]:
    """Filas de una feature sin los backends que no son equiparables en ella."""
    rows = list(rows)
    if feature != "formula":
        return rows
    return [row for row in rows if row.get("backend") not in FORMULA_BACKENDS_EXCLUDED]


def run_benchmark(
    samples: Iterable[Sample],
    backend: str,
    dataset: str,
    warmup: int = 1,
    backend_factory: Callable[[], Callable[[Image.Image], OcrOutput]] | None = None,
    repeats: int = 1,
    device: str = "cpu",
    task_override: str | None = None,
    dump: list[dict] | None = None,
    feature: str | None = None,
    model: tuple[str, str] | None = None,
    scorer: Callable[[Sample, OcrOutput], dict] | None = None,
) -> tuple[list[dict], dict]:
    """Ejecuta un backend sobre todas las muestras y devuelve (filas, metadatos).

    `task_override` fuerza el `task_type` de las filas (p. ej. `formula` sobre el
    dataset de recortes de formula) aunque el backend sea de otra familia; el GT
    sigue siendo el de la muestra. `feature` etiqueta el banco por feature que
    produjo la fila (columna aditiva). `model` fija `(model_name, model_variant)`
    para backends fuera del registro (`PROVIDERS`). Si `dump` no es None, se
    rellena con `{image_id, text}` de cada muestra medida: la salida cruda no cabe
    en el CSV de contrato fijo y hace falta para medir, p. ej., quién emite LaTeX.

    `scorer` es la métrica **propia de una feature** (layout, tabla, orientación,
    rectificado): recibe la muestra y la salida del motor y devuelve las columnas
    a añadir a su fila. Un banco sin scorer deja esas columnas vacías.
    """
    task_type = task_override or TASK_TYPES.get(backend, "text")
    model_name, model_variant = model or MODEL_NAMES.get(backend, (backend, "default"))
    feature = feature or FEATURE_TYPES.get(backend, "text")
    provider_effective, skip_reason = device_outcome(backend, device)
    provenance = {"task_type": task_type, "model_name": model_name, "model_variant": model_variant,
                  "feature": feature, "device_requested": device,
                  "provider_effective": provider_effective or "n/a", "repeats": repeats}
    if repeats < 1 or warmup < 0:
        raise ValueError("repeats must be positive and warmup nonnegative")
    if skip_reason:
        # Backend CPU-only con `--device gpu`: se rechaza ANTES de cargar el motor,
        # para no medir un fallback CPU bajo la etiqueta de GPU.
        return [], {"backend": backend, "status": "skipped", "reason": skip_reason, **provenance}
    factory = backend_factory or PROVIDERS[backend]
    load_start = time.perf_counter()
    try:
        # Todas las factorías reciben el `device` resuelto: las que no lo usan
        # (rapidocr, easyocr, tesseract…) lo aceptan y lo ignoran. Va **por
        # nombre** porque no todos lo declaran como primer parámetro; si la
        # factoría no lo acepta (p. ej. las de los tests), se llama sin él.
        dev = pyocrust_device_arg(device) if backend.startswith("pyocrust") else device
        try:
            runner = factory(device=dev)
        except TypeError:
            runner = factory()
    except ProviderUnavailable as exc:
        return [], {
            "backend": backend,
            "dataset": dataset,
            "status": "skipped",
            "reason": str(exc),
            **provenance,
        }
    except Exception as exc:  # noqa: BLE001 - p.ej. modelos ausentes: no es un OCR malo
        return [], {
            "backend": backend,
            "dataset": dataset,
            "status": "skipped",
            "reason": f"{type(exc).__name__}: {exc}",
            **provenance,
        }

    # Confirmación honesta del EP: pedir GPU NO cuenta como GPU. El provider real
    # solo se conoce al construir el motor (`engine.provider_effective`); si no es
    # un acelerador, la fila/backend queda `skipped` — nunca CPU etiquetado GPU.
    if provider_effective is None:
        engine_provider = getattr(runner, "provider_effective", None) or "desconocido"
        if engine_provider not in GPU_PROVIDERS:
            return [], {
                "backend": backend, "dataset": dataset, "status": "skipped",
                "reason": GPU_NOT_CONFIRMED.format(engine=engine_provider, available=available_providers()),
                **provenance,
            }
        provider_effective = engine_provider
        provenance["provider_effective"] = provider_effective

    # Canales de estructura que declara el ADAPTADOR (atributo `run.emits`); si no
    # declara nada (adaptadores de test, runs previas) se asume motor completo.
    emits = getattr(runner, "emits", emitted_channels(backend))

    load_ms = (time.perf_counter() - load_start) * 1000
    rows: list[dict] = []
    errors: list[str] = []
    timings: list[float] = []
    samples = list(samples)

    # Calentamiento fuera de la medición y **sin consumir muestras evaluadas**:
    # la primera pasada paga el costo de caché del runtime de ONNX y penalizaría
    # al primero en ejecutarse. Se repite la primera imagen en vez de descartarla.
    try:
        for _ in range(warmup if samples else 0):
            runner(samples[0].image.copy())
    except Exception as exc:
        return [], {"backend": backend, "status": "error", "reason": f"warmup: {type(exc).__name__}: {exc}", "load_ms": load_ms, **provenance}

    for sample in samples:
        try:
            outputs = [runner(sample.image.copy()) for _ in range(repeats)]
            timings.extend(item.elapsed_ms for item in outputs)
            output = outputs[-1]
            output.elapsed_ms = statistics.fmean(item.elapsed_ms for item in outputs)
        except Exception as exc:  # noqa: BLE001 - un OCR roto no tira el benchmark
            errors.append(f"{sample.image_id}: {type(exc).__name__}: {exc}")
            rows.append(
                {
                    "backend": backend,
                    "dataset": dataset,
                    "image_id": sample.image_id,
                    "status": "error",
                    "error": str(exc),
                    "task_type": task_type, "model_name": model_name, "model_variant": model_variant,
                    "feature": feature,
                    "device_requested": device, "provider_effective": provider_effective,
                }
            )
            continue

        # Tareas con GT propio (p. ej. `formula` -> LaTeX anotado) se puntuan
        # contra su referencia; el resto usa el GT de texto de la pagina.
        gt = sample.gt_by_task.get(task_type, sample.gt_text) if sample.gt_by_task else sample.gt_text
        if dump is not None:
            dump.append({"image_id": sample.image_id, "text": output.text})
        # Sin GT de texto (features de orientacion/rectificado/layout, cuya
        # referencia es una etiqueta, una imagen o unas cajas) la calidad textual
        # queda **no evaluada** ("") en vez de un 0.0 espurio.
        has_text_gt = bool((gt or "").strip())
        # Metricas LaTeX normalizadas: solo tienen sentido en formulas (en el
        # resto van vacias, como `markdown_f1`/`block_f1` en texto).
        if task_type == "formula":
            latex_exact_v = latex_exact(gt, output.text)
            latex_sim_v = round(latex_similarity(gt, output.text), 4)
            latex_f1_v = round(latex_token_f1(gt, output.text), 4)
        else:
            latex_exact_v = latex_sim_v = latex_f1_v = ""
        # Deteccion (recall@IoU): solo cuando el dataset anota cajas GT. Sin GT de
        # cajas la métrica queda vacía (no evaluada), nunca un 0.0 espurio.
        if sample.gt_boxes:
            box_recall_v, box_iou_v = box_metrics(sample.gt_boxes, output.extra.get("boxes") or [])
            box_recall_v, box_iou_v = round(box_recall_v, 4), round(box_iou_v, 4)
        else:
            box_recall_v = box_iou_v = ""
        row = {
            "backend": backend,
            "dataset": dataset,
            "image_id": sample.image_id,
            "cer": cer(gt, output.text) if has_text_gt else "",
            "wer": wer(gt, output.text) if has_text_gt else "",
            "cer_ord": cer_ord(gt, output.text) if has_text_gt else "",
            "wer_ord": wer_ord(gt, output.text) if has_text_gt else "",
            "word_f1": word_f1(gt, output.text) if has_text_gt else "",
            "exact_match": float(normalize(gt) == normalize(output.text)) if has_text_gt else "",
            "elapsed_ms": round(output.elapsed_ms, 3),
            "n_regions": output.n_regions,
            "mean_confidence": round(output.mean_confidence, 4),
            "n_chars_gt": len(normalize(gt)) if has_text_gt else "",
            "n_chars_pred": len(normalize(output.text)),
            "status": "ok",
            "error": "",
            "task_type": task_type, "model_name": model_name, "model_variant": model_variant,
            "markdown_f1": markdown_f1(sample.gt_markdown, output.text) if task_type != "text" and sample.gt_markdown is not None else "",
            # `block_f1` compara TIPOS de bloque del vocabulario del banco: un motor
            # que no los emite (docling, indra) queda no evaluado, no `0.0`.
            "block_f1": block_f1(sample.gt_blocks, output.extra.get("blocks", [])) if "layout" in emits and task_type != "text" and sample.gt_blocks is not None else "",
            "latex_exact": latex_exact_v, "latex_sim": latex_sim_v, "latex_token_f1": latex_f1_v,
            "feature": feature,
            "box_recall": box_recall_v, "box_iou_mean": box_iou_v,
            "device_requested": device, "provider_effective": provider_effective,
            # Métricas por feature: "" = no evaluada; el `scorer` las sobreescribe.
            "layout_map": "", "layout_recall": "", "table_teds": "", "ori_acc": "", "rect_sim": "",
            # Métricas propias de `full_page` (títulos + orden de lectura): el
            # `scorer` de esa feature las rellena; "" = no evaluada.
            "title_recall": "", "title_precision": "", "title_text_f1": "",
            "title_seq_tau": "", "read_order_tau": "",
            # Estrato de la página (`data_source × layout`) cuando el dataset lo anota.
            "stratum": sample.stratum or "",
        }
        # Métrica propia de la feature (layout/tabla/orientación/rectificado).
        # El adaptador declara sus canales de estructura en `extra["emits"]`; un
        # `scorer` (p. ej. `score_full_page`) los consulta para no puntuar como
        # `0.0` lo que el motor no emite.
        output.extra.setdefault("emits", emits)
        if scorer is not None:
            row.update(scorer(sample, output))
        rows.append(row)

    ok = [r for r in rows if r["status"] == "ok"]
    cers = [r["cer"] for r in ok if isinstance(r["cer"], float)]
    word_f1s = [r["word_f1"] for r in ok if isinstance(r["word_f1"], float)]
    meta = {
        "backend": backend,
        "dataset": dataset,
        "status": "ok" if ok else "error" if errors else "empty",
        **provenance,
        "load_ms": load_ms,
        "warmup": warmup,
        "input": "identical re-encoded PNG bytes for every adapter; no per-backend resize or preprocess; conversion excluded from timing",
        "image_sizes": {s.image_id: list(s.image.size) for s in samples},
        "inference_ms": timings,
        "p95_ms": sorted(timings)[min(len(timings) - 1, int(0.95 * len(timings)))] if timings else None,
        "markdown_quality": "evaluated" if any(r.get("markdown_f1") != "" for r in ok) else "not_evaluated",
        "n_images": len(rows),
        "n_ok": sum(1 for r in rows if r["status"] == "ok"),
        "n_error": len(errors),
        "errors": errors,
        "mean_cer": (
            statistics.fmean(cers) if cers else None
        ),
        "mean_word_f1": (
            statistics.fmean(word_f1s) if word_f1s else None
        ),
        "mean_ms": (
            statistics.fmean(r["elapsed_ms"] for r in ok) if ok else None
        ),
    }
    return rows, meta


def write_csv(rows: Sequence[dict], out_dir: Path, timestamp: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{timestamp}.csv"
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({"run_timestamp": timestamp, **row})
    meta_path = out_dir / f"{timestamp}.meta.json"
    meta_path.write_text(
        json.dumps({"run_timestamp": timestamp, "rows": len(rows)}, indent=2),
        encoding="utf-8",
    )
    return path


def run_backends(
    samples: Sequence[Sample],
    backends: Sequence[str],
    dataset: str,
    out_dir: Path,
    timestamp: str,
    warmup: int = 1,
    repeats: int = 1,
    device: str = "cpu",
    task_override: str | None = None,
    feature: str | None = None,
    factories: dict[str, Callable[[], Callable[[Image.Image], OcrOutput]]] | None = None,
    models: dict[str, tuple[str, str]] | None = None,
    dump_outputs: bool = False,
    task_types: set[str] | None = None,
    scorer: Callable[[Sample, OcrOutput], dict] | None = None,
) -> tuple[list[dict], dict[str, dict]]:
    """Ejecuta una lista de backends y escribe CSV + metadatos. Interfaz de los bancos.

    Los bancos por feature llaman aquí: un backend/modelo a la vez, `skipped` con
    motivo para lo no disponible, y `summary.json` con el origen de cada número.
    `scorer` es la métrica propia de la feature (ver `run_benchmark`).
    """
    all_rows: list[dict] = []
    summary: dict[str, dict] = {}
    out_dir.mkdir(parents=True, exist_ok=True)
    if device != "cpu":
        # Antes de construir NINGÚN motor: deja cargado el cudnn/cublas de torch
        # para que el provider CUDA de ORT los reutilice (ver preload_gpu_runtime).
        preload_gpu_runtime()
    for backend in backends:
        factories = factories or {}
        if backend not in PROVIDERS and backend not in factories:
            print(f"[skip] backend desconocido: {backend}")
            summary[backend] = {"status": "skipped", "reason": "no registrado"}
            continue
        if task_types is not None and (task_override or TASK_TYPES.get(backend, "text")) not in task_types:
            summary[backend] = {"status": "skipped", "reason": "task type excluded"}
            continue
        print(f"\n[run] {backend} ...")
        dump: list[dict] | None = [] if dump_outputs else None
        rows, meta = run_benchmark(
            samples, backend, dataset, warmup=warmup, repeats=repeats, device=device,
            task_override=task_override, dump=dump, feature=feature,
            backend_factory=(factories or {}).get(backend),
            model=(models or {}).get(backend),
            scorer=scorer,
        )
        all_rows.extend(rows)
        summary[backend] = meta
        if dump:
            (out_dir / f"{backend}.outputs.json").write_text(
                json.dumps({"backend": backend, "outputs": dump}, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        if meta.get("status") == "skipped":
            print(f"  skipped: {meta['reason']}")
        elif not meta.get("n_ok"):
            print(f"  [aviso] 0 muestras medidas: {meta.get('reason') or 'limit/warmup sin margen'}")
        else:
            def _fmt(value, spec, suffix=""):
                return "N/A" if value is None else f"{value:{spec}}{suffix}"

            print(
                f"  {meta['n_ok']}/{meta['n_images']} ok, "
                f"n_error={meta['n_error']}, "
                f"CER medio={_fmt(meta['mean_cer'], '.4f')}, "
                f"F1 palabra={_fmt(meta['mean_word_f1'], '.4f')}, "
                f"{_fmt(meta['mean_ms'], '.1f', ' ms/imagen')}"
            )
        (out_dir / f"{backend}.meta.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    csv_path = write_csv(all_rows, out_dir, timestamp)
    print(f"\n[csv] {csv_path}")
    print(f"[json] {out_dir / 'summary.json'}")
    (out_dir / "summary.json").write_text(
        json.dumps(
            {
                "timestamp": timestamp,
                "runtime": _describe_runtime(),
                "origen": "medido",
                # Provenance del DATASET: `dataset` (muestra real) o `fixture`
                # (fallback minimo versionado, sin red). El informe lo declara.
                "dataset_source": fixture_provenance(),
                # Provenance: comando exacto + parámetros de la corrida.
                "command": [sys.executable, *sys.argv],
                "dataset": dataset,
                "backends_requested": list(backends),
                "n_samples": len(samples),
                "warmup": warmup,
                "repeats": repeats,
                "device_requested": device,
                "backends": summary,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return all_rows, summary


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Benchmark de OCR (runner común por feature)")
    parser.add_argument("--dataset", default=DEFAULT_DATASET,
                        choices=["funsd", "omnidocbench", "omnidocbench_formula"])
    parser.add_argument("--split", default="train")
    parser.add_argument("--limit", type=int, default=20, help="imagenes a evaluar")
    parser.add_argument(
        "--backends",
        default="pyocrust,rapidocr",
        help="separados por comas; los no disponibles se marcan skipped",
    )
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--task-types", default="text,structure,formula,full_page")
    parser.add_argument("--feature", default=None, help="etiqueta de banco por feature (columna aditiva)")
    parser.add_argument("--manifest", type=Path, help="JSON local images with supplied text/markdown/blocks GT")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--device", choices=["cpu", "gpu"], default="cpu")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--dump-outputs", action="store_true",
                        help="escribe <backend>.outputs.json con la salida cruda de cada muestra")
    parser.add_argument("--fetch", action="store_true",
                        help="prepara (puebla) el cache del dataset y sale: falla claro sin red")
    args = parser.parse_args(argv)
    if args.fetch:
        # Paso explicito de preparacion: UN error claro si no hay red y no hay
        # cache, en vez de dejar cada muestra en `skipped`.
        from common.datasets import FETCH_HELP, DatasetOffline, prepare_datasets

        try:
            info = prepare_datasets()
        except DatasetOffline as exc:
            print(f"[error] {exc}", file=sys.stderr)
            return 2
        print(f"[ok] dataset preparado: revision={info['revision']} "
              f"sha256={info['sha256'][:12]}... ({FETCH_HELP})")
        return 0
    tasks = set(args.task_types.split(","))
    if not tasks <= {"text", "structure", "formula", "full_page"} or args.limit < 0 or args.warmup < 0 or args.repeats < 1:
        parser.error("invalid task types or limits")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_dir = args.output_dir / timestamp
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[dataset] {args.dataset} split={args.split} limit={args.limit}")
    if args.manifest:
        samples = load_local(args.manifest, args.limit)
        dataset = str(args.manifest.resolve())
    else:
        samples = load_dataset(args.dataset, limit=args.limit, split=args.split)
        dataset = args.dataset
    # Los recortes de formula se evaluan con `task_type=formula` en TODOS los
    # adaptadores: la entrada ya es una formula, no una pagina que haya que tipar.
    force_task = "formula" if args.dataset == "omnidocbench_formula" else None
    print(f"[dataset] {len(samples)} muestras cargadas")

    selected = [b.strip() for b in args.backends.split(",") if b.strip()]
    run_backends(samples, selected, dataset, out_dir, timestamp, warmup=args.warmup,
                 repeats=args.repeats, device=args.device, task_override=force_task,
                 feature=args.feature, dump_outputs=args.dump_outputs, task_types=tasks)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
