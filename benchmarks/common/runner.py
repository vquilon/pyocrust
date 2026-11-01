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

Columnas del CSV (contrato con `report_benchmarks.py`, **28 columnas**):
    run_timestamp, backend, dataset, image_id, cer, wer, cer_ord, wer_ord,
    word_f1, exact_match, elapsed_ms, n_regions, mean_confidence, n_chars_gt,
    n_chars_pred, status, error, task_type, model_name, model_variant,
    markdown_f1, block_f1,
    latex_exact, latex_sim, latex_token_f1,     (solo `task_type=formula`)
    feature,                                    (banco por feature que produjo la fila)
    box_recall, box_iou_mean                    (solo si el dataset anota cajas GT)

Las 22 columnas históricas se mantienen en su orden; las nuevas son aditivas.

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
import sys
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
]


class ProviderUnavailable(RuntimeError):
    """El backend no se puede ejecutar en este entorno (no como un OCR malo)."""


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


def _pyocrust_backend(preset: str, formula_only: bool = False) -> Callable[[Image.Image], OcrOutput]:
    import pyocrust  # noqa: PLC0415 - import tardío para no penalizar el arranque

    engine = pyocrust.VeloceOCR(preset=preset)

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
        return OcrOutput(
            text=text,
            n_regions=len(regions),
            mean_confidence=float(confidence),
            elapsed_ms=elapsed_ms,
            extra={"kind": type(result).__name__,
                   "blocks": [e.kind for e in getattr(result, "elements", [])],
                   "boxes": boxes},
        )

    return run


def _rapidocr_backend() -> Callable[[Image.Image], OcrOutput]:
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError as exc:
        raise ProviderUnavailable("pip install rapidocr-onnxruntime") from exc

    engine = RapidOCR()

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

    return run


def _easyocr_backend(languages: Sequence[str] = ("en",)) -> Callable[[Image.Image], OcrOutput]:
    try:
        import easyocr
    except ImportError as exc:
        raise ProviderUnavailable("pip install easyocr (requiere torch)") from exc

    reader = easyocr.Reader(list(languages), gpu=False, verbose=False)

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

    return run


def _pyocrust_formula_variant_backend(model_file: str) -> Callable[[Image.Image], OcrOutput]:
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

    return run


def _tesseract_backend() -> Callable[[Image.Image], OcrOutput]:
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


# nombre -> factoría (el preset por defecto es el de `pp_ocrv6` = Tiny)
PROVIDERS: dict[str, Callable[[], Callable[[Image.Image], OcrOutput]]] = {
    "pyocrust": lambda: _pyocrust_backend("pp_ocrv6"),
    "pyocrust_structure": lambda: _pyocrust_backend("pp_structurev3"),
    "pyocrust_formula": lambda: _pyocrust_backend("pp_structurev3", formula_only=True),
    "pyocrust_formulanet": lambda: _pyocrust_formula_variant_backend("pp-formulanet-s.onnx"),
    # Variantes PP-FormulaNet del registro ModelScope `greatv/oar-ocr` (oar-ocr-core
    # registry.rs): mismo adaptador, distinto `.onnx`. Se saltan si falta el fichero.
    "pyocrust_formulanet_l": lambda: _pyocrust_formula_variant_backend("pp-formulanet-l.onnx"),
    "pyocrust_formulanet_pluss": lambda: _pyocrust_formula_variant_backend("pp-formulanet_plus-s.onnx"),
    "pyocrust_formulanet_plusm": lambda: _pyocrust_formula_variant_backend("pp-formulanet_plus-m.onnx"),
    "pyocrust_formulanet_plusl": lambda: _pyocrust_formula_variant_backend("pp-formulanet_plus-l.onnx"),
    "pyocrust_indra": lambda: _pyocrust_backend("indra"),
    "rapidocr": _rapidocr_backend,
    "easyocr": _easyocr_backend,
    "tesseract": _tesseract_backend,
}


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
    }


TASK_TYPES = {"pyocrust_structure": "structure", "pyocrust_formula": "formula", "pyocrust_formulanet": "formula",
              "pyocrust_formulanet_l": "formula", "pyocrust_formulanet_pluss": "formula",
              "pyocrust_formulanet_plusm": "formula", "pyocrust_formulanet_plusl": "formula",
              "pyocrust_indra": "full_page"}
MODEL_NAMES = {"pyocrust": ("pp_ocrv6", "tiny"), "pyocrust_structure": ("pp_structurev3", "default"),
               "pyocrust_formula": ("pp_structurev3", "pp-formulanet-s"), "pyocrust_formulanet": ("pp-formulanet-s", "direct"),
               "pyocrust_formulanet_l": ("pp-formulanet-l", "direct"),
               "pyocrust_formulanet_pluss": ("pp-formulanet_plus-s", "direct"),
               "pyocrust_formulanet_plusm": ("pp-formulanet_plus-m", "direct"),
               "pyocrust_formulanet_plusl": ("pp-formulanet_plus-l", "direct"),
               "pyocrust_indra": ("indra", "math")}
# Banco de feature al que pertenece cada backend conocido (columna `feature`).
FEATURE_TYPES = {"pyocrust_structure": "full_page", "pyocrust_indra": "full_page",
                 "pyocrust_formula": "formula", "pyocrust_formulanet": "formula",
                 "pyocrust_formulanet_l": "formula", "pyocrust_formulanet_pluss": "formula",
                 "pyocrust_formulanet_plusm": "formula", "pyocrust_formulanet_plusl": "formula"}


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
) -> tuple[list[dict], dict]:
    """Ejecuta un backend sobre todas las muestras y devuelve (filas, metadatos).

    `task_override` fuerza el `task_type` de las filas (p. ej. `formula` sobre el
    dataset de recortes de formula) aunque el backend sea de otra familia; el GT
    sigue siendo el de la muestra. `feature` etiqueta el banco por feature que
    produjo la fila (columna aditiva). `model` fija `(model_name, model_variant)`
    para backends fuera del registro (`PROVIDERS`). Si `dump` no es None, se
    rellena con `{image_id, text}` de cada muestra medida: la salida cruda no cabe
    en el CSV de contrato fijo y hace falta para medir, p. ej., quién emite LaTeX.
    """
    task_type = task_override or TASK_TYPES.get(backend, "text")
    model_name, model_variant = model or MODEL_NAMES.get(backend, (backend, "default"))
    feature = feature or FEATURE_TYPES.get(backend, "text")
    provenance = {"task_type": task_type, "model_name": model_name, "model_variant": model_variant,
                  "feature": feature, "device_requested": device, "provider_effective": "unverified",
                  "repeats": repeats}
    if repeats < 1 or warmup < 0:
        raise ValueError("repeats must be positive and warmup nonnegative")
    if device != "cpu":
        return [], {"backend": backend, "status": "skipped", "reason": "GPU selection not exposed; refusing CPU fallback", **provenance}
    factory = backend_factory or PROVIDERS[backend]
    load_start = time.perf_counter()
    try:
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
                }
            )
            continue

        # Tareas con GT propio (p. ej. `formula` -> LaTeX anotado) se puntuan
        # contra su referencia; el resto usa el GT de texto de la pagina.
        gt = sample.gt_by_task.get(task_type, sample.gt_text) if sample.gt_by_task else sample.gt_text
        if dump is not None:
            dump.append({"image_id": sample.image_id, "text": output.text})
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
        rows.append(
            {
                "backend": backend,
                "dataset": dataset,
                "image_id": sample.image_id,
                "cer": cer(gt, output.text),
                "wer": wer(gt, output.text),
                "cer_ord": cer_ord(gt, output.text),
                "wer_ord": wer_ord(gt, output.text),
                "word_f1": word_f1(gt, output.text),
                "exact_match": float(normalize(gt) == normalize(output.text)),
                "elapsed_ms": round(output.elapsed_ms, 3),
                "n_regions": output.n_regions,
                "mean_confidence": round(output.mean_confidence, 4),
                "n_chars_gt": len(normalize(gt)),
                "n_chars_pred": len(normalize(output.text)),
                "status": "ok",
                "error": "",
                "task_type": task_type, "model_name": model_name, "model_variant": model_variant,
                "markdown_f1": markdown_f1(sample.gt_markdown, output.text) if task_type != "text" and sample.gt_markdown is not None else "",
                "block_f1": block_f1(sample.gt_blocks, output.extra.get("blocks", [])) if task_type != "text" and sample.gt_blocks is not None else "",
                "latex_exact": latex_exact_v, "latex_sim": latex_sim_v, "latex_token_f1": latex_f1_v,
                "feature": feature,
                "box_recall": box_recall_v, "box_iou_mean": box_iou_v,
            }
        )

    ok = [r for r in rows if r["status"] == "ok"]
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
            statistics.fmean(r["cer"] for r in ok) if ok else None
        ),
        "mean_word_f1": (
            statistics.fmean(r["word_f1"] for r in ok) if ok else None
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
) -> tuple[list[dict], dict[str, dict]]:
    """Ejecuta una lista de backends y escribe CSV + metadatos. Interfaz de los bancos.

    Los bancos por feature llaman aquí: un backend/modelo a la vez, `skipped` con
    motivo para lo no disponible, y `summary.json` con el origen de cada número.
    """
    all_rows: list[dict] = []
    summary: dict[str, dict] = {}
    out_dir.mkdir(parents=True, exist_ok=True)
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
            print(
                f"  {meta['n_ok']}/{meta['n_images']} ok, "
                f"n_error={meta['n_error']}, "
                f"CER medio={meta['mean_cer']:.4f}, "
                f"F1 palabra={meta['mean_word_f1']:.4f}, "
                f"{meta['mean_ms']:.1f} ms/imagen"
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
    args = parser.parse_args(argv)
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
