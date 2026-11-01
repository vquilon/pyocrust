#!/usr/bin/env python
"""pyocrust OCR benchmark runner sobre un dataset real (FUNSD por defecto).

Mide **calidad** (CER, WER, exact-match) y **tiempo** (ms/pagina, paginas/s) de
`pyocrust` contra otros OCR disponibles (rapidocr, easyocr, tesseract) sobre las
mismas imagenes, y vuelca el resultado en CSV para `report_benchmarks.py`.

Uso:
    python benchmarks/run_benchmarks.py --limit 20 --backends pyocrust,rapidocr

Los backends que no esten instalados (o cuyos modelos falten) se registrarán con
`status=skipped` y un motivo; nunca como si hubieran corrido.

Salida: `benchmarks/results/<timestamp>/<timestamp>.csv`
Esquema de columnas (contrato con `report_benchmarks.py`, 22 columnas):
    run_timestamp,backend,dataset,image_id,cer,wer,cer_ord,wer_ord,word_f1,
    exact_match,elapsed_ms,n_regions,mean_confidence,n_chars_gt,n_chars_pred,
    status,error,task_type,model_name,model_variant,markdown_f1,block_f1

Eje `task_type`: `text` (pp_ocrv6 tiny), `structure` (pp_structurev3 → Markdown),
`formula` (pp_structurev3 + pp-formulanet-s → LaTeX), `full_page` (indra con math
→ Markdown + LaTeX). `markdown_f1`/`block_f1` van vacíos (`""`) en `text`.

Fairness (representación elegida): **todos los adaptadores reciben la MISMA entrada,
los mismos bytes PNG re-codificados** (`_image_bytes`). `pyocrust.recognize` solo
admite ruta/`bytes`/PathLike, así que el denominador común es `bytes`; cada adaptador
entrega esos bytes a su motor y es el motor quien los decodifica (tesseract vía
`io.BytesIO`). Sin reescalado ni preproceso por backend. La conversión de la entrada
queda fuera del cronómetro: `elapsed_ms` mide solo la inferencia, sin carga de modelo
ni descarga. El *warmup* es idéntico para todos los backends.
"""

from __future__ import annotations

import argparse
import csv
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

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

HERE = Path(__file__).resolve().parent
DEFAULT_RESULTS_DIR = HERE / "results"
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
]


class ProviderUnavailable(RuntimeError):
    """El backend no se puede ejecutar en este entorno (no como un OCR malo)."""


# ---------------------------------------------------------------------------
# Métricas de calidad (Levenshtein propio: sin dependencias extra)
# ---------------------------------------------------------------------------

def normalize(text: str) -> str:
    """Normalización de fairness: minusculas y espacios colapsados."""
    return " ".join(text.lower().split())


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current = [i]
        for j, cb in enumerate(b, start=1):
            current.append(
                min(
                    previous[j] + 1,          # borrado
                    current[j - 1] + 1,       # inserción
                    previous[j - 1] + (ca != cb),  # sustitución
                )
            )
        previous = current
    return previous[-1]


def cer(gt: str, pred: str) -> float:
    """Character Error Rate sobre texto normalizado."""
    gt_n, pred_n = normalize(gt), normalize(pred)
    if not gt_n:
        return 0.0 if not pred_n else 1.0
    return levenshtein(gt_n, pred_n) / len(gt_n)


def wer(gt: str, pred: str) -> float:
    """Word Error Rate sobre texto normalizado."""
    gt_w, pred_w = normalize(gt).split(), normalize(pred).split()
    if not gt_w:
        return 0.0 if not pred_w else 1.0
    return levenshtein(gt_w, pred_w) / len(gt_w)


def word_f1(gt: str, pred: str) -> float:
    """F1 a nivel de palabra, independiente del orden de lectura (multi-columna).

    Un formulario con varias columnas hace que el orden lineal del OCR y el del
    ground truth difieran sin que ninguno de los dos esté mal; este F1 compara
    el multiconjunto de palabras y no castiga ese desorden.
    """
    from collections import Counter

    gt_w = Counter(normalize(gt).split())
    pred_w = Counter(normalize(pred).split())
    if not gt_w and not pred_w:
        return 1.0
    if not gt_w or not pred_w:
        return 0.0
    overlap = sum((gt_w & pred_w).values())
    if overlap == 0:
        return 0.0
    precision = overlap / sum(pred_w.values())
    recall = overlap / sum(gt_w.values())
    return 2 * precision * recall / (precision + recall)


def _ordered(text: str) -> list[str]:
    """Palabras del texto ordenadas: neutraliza el orden de lectura."""
    return sorted(normalize(text).split())


def cer_ord(gt: str, pred: str) -> float:
    """CER con orden de lectura neutralizado (B4/D1).

    El CER crudo castiga la diferencia de recorrido entre el OCR lineal y el
    ground truth ordenado por caja; este CER compara el **multiconjunto** de
    palabras y mide reconocimiento, no disposición.
    """
    gt_o, pred_o = " ".join(_ordered(gt)), " ".join(_ordered(pred))
    if not gt_o:
        return 0.0 if not pred_o else 1.0
    return levenshtein(gt_o, pred_o) / len(gt_o)


def wer_ord(gt: str, pred: str) -> float:
    """WER con orden de lectura neutralizado (B4/D1)."""
    gt_o, pred_o = _ordered(gt), _ordered(pred)
    if not gt_o:
        return 0.0 if not pred_o else 1.0
    return levenshtein(gt_o, pred_o) / len(gt_o)


# ---------------------------------------------------------------------------
# Dataset real: FUNSD (formularios escaneados, 149 train + 50 test)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Sample:
    image_id: str
    image: Image.Image
    gt_text: str
    gt_markdown: str | None = None
    gt_blocks: tuple[str, ...] | None = None


def load_local(manifest: Path, limit: int | None = None) -> list[Sample]:
    """JSON array: image and optional text/markdown/blocks reference fields."""
    rows = json.loads(manifest.read_text(encoding="utf-8"))
    return [Sample(str(row.get("id", row["image"])),
                   Image.open(manifest.parent / row["image"]).convert("RGB"),
                   row.get("text", ""), row.get("markdown"),
                   tuple(row["blocks"]) if "blocks" in row else None)
            for row in rows[:limit]]


def markdown_f1(gt: str, pred: str) -> float:
    """Order-sensitive token LCS F1; preserve LaTeX case."""
    import re
    def tokens(text):
        parts = re.split(r"(\$\$.*?\$\$|\$[^$]*\$)", text, flags=re.DOTALL)
        return [token for part in parts for token in (part if part.startswith("$") else part.lower()).split()]
    a, b = tokens(gt), tokens(pred)
    if not a and not b:
        return 1.0
    previous = [0] * (len(b) + 1)
    for token in a:
        current = [0]
        for j, other in enumerate(b, 1):
            current.append(previous[j - 1] + 1 if token == other else max(previous[j], current[-1]))
        previous = current
    return 2 * previous[-1] / (len(a) + len(b))


def block_f1(gt: Sequence[str], pred: Sequence[str]) -> float:
    from collections import Counter
    a, b = Counter(gt), Counter(pred)
    return 2 * sum((a & b).values()) / (sum(a.values()) + sum(b.values())) if a or b else 1.0


def load_funsd(split: str = "train", limit: int | None = None) -> list[Sample]:
    """Carga FUNSD desde Hugging Face, cacheado en `benchmarks/data_cache`."""
    try:
        from datasets import load_dataset
    except ImportError as exc:  # pragma: no cover - entorno sin `datasets`
        raise ProviderUnavailable(
            "pip install datasets (y pyarrow) para descargar FUNSD"
        ) from exc

    cache = HERE / "data_cache"
    cache.mkdir(parents=True, exist_ok=True)
    marker = cache / f"funsd_{split}.ok"

    ds = load_dataset("nielsr/funsd", split=split, cache_dir=str(cache))
    if limit is not None:
        ds = ds.select(range(min(limit, len(ds))))

    samples: list[Sample] = []
    for row in ds:
        words = [str(w) for w in row["words"]]
        bboxes = row["bboxes"]
        # Orden de lectura por caja (fila, luego columna): el OCR lineal y el
        # ground truth deben recorrer la pagina en el mismo sentido.
        ordered = sorted(
            zip(words, bboxes),
            key=lambda wb: (
                (wb[1][1] + wb[1][3]) / 2.0,  # centro Y
                (wb[1][0] + wb[1][2]) / 2.0,  # centro X
            ),
        )
        gt_text = " ".join(w for w, _ in ordered)
        samples.append(
            Sample(
                image_id=str(row["id"]),
                image=row["image"].convert("RGB"),
                gt_text=gt_text,
            )
        )
    marker.write_text(f"{len(samples)} samples\n", encoding="utf-8")
    return samples


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
        return OcrOutput(
            text=text,
            n_regions=len(regions),
            mean_confidence=float(confidence),
            elapsed_ms=elapsed_ms,
            extra={"kind": type(result).__name__, "blocks": [e.kind for e in getattr(result, "elements", [])]},
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
        return OcrOutput(
            text="\n".join(texts),
            n_regions=len(texts),
            mean_confidence=sum(scores) / len(scores) if scores else 0.0,
            elapsed_ms=elapsed_ms,
            extra={"engine": "rapidocr_onnxruntime"},
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
        return OcrOutput(
            text="\n".join(texts),
            n_regions=len(texts),
            mean_confidence=sum(scores) / len(scores),
            elapsed_ms=elapsed_ms,
            extra={"engine": "easyocr"},
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


TASK_TYPES = {"pyocrust_structure": "structure", "pyocrust_formula": "formula", "pyocrust_indra": "full_page"}
MODEL_NAMES = {"pyocrust": ("pp_ocrv6", "tiny"), "pyocrust_structure": ("pp_structurev3", "default"),
               "pyocrust_formula": ("pp_structurev3", "pp-formulanet-s"), "pyocrust_indra": ("indra", "math")}


def run_benchmark(
    samples: Iterable[Sample],
    backend: str,
    dataset: str,
    warmup: int = 1,
    backend_factory: Callable[[], Callable[[Image.Image], OcrOutput]] | None = None,
    repeats: int = 1,
    device: str = "cpu",
) -> tuple[list[dict], dict]:
    """Ejecuta un backend sobre todas las muestras y devuelve (filas, metadatos)."""
    task_type = TASK_TYPES.get(backend, "text")
    model_name, model_variant = MODEL_NAMES.get(backend, (backend, "default"))
    provenance = {"task_type": task_type, "model_name": model_name, "model_variant": model_variant,
                  "device_requested": device, "provider_effective": "unverified", "repeats": repeats}
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
                }
            )
            continue

        rows.append(
            {
                "backend": backend,
                "dataset": dataset,
                "image_id": sample.image_id,
                "cer": cer(sample.gt_text, output.text),
                "wer": wer(sample.gt_text, output.text),
                "cer_ord": cer_ord(sample.gt_text, output.text),
                "wer_ord": wer_ord(sample.gt_text, output.text),
                "word_f1": word_f1(sample.gt_text, output.text),
                "exact_match": float(normalize(sample.gt_text) == normalize(output.text)),
                "elapsed_ms": round(output.elapsed_ms, 3),
                "n_regions": output.n_regions,
                "mean_confidence": round(output.mean_confidence, 4),
                "n_chars_gt": len(normalize(sample.gt_text)),
                "n_chars_pred": len(normalize(output.text)),
                "status": "ok",
                "error": "",
                "task_type": task_type, "model_name": model_name, "model_variant": model_variant,
                "markdown_f1": markdown_f1(sample.gt_markdown, output.text) if task_type != "text" and sample.gt_markdown is not None else "",
                "block_f1": block_f1(sample.gt_blocks, output.extra.get("blocks", [])) if task_type != "text" and sample.gt_blocks is not None else "",
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


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Benchmark de OCR sobre FUNSD")
    parser.add_argument("--dataset", default=DEFAULT_DATASET, choices=["funsd"])
    parser.add_argument("--split", default="train")
    parser.add_argument("--limit", type=int, default=20, help="imagenes a evaluar")
    parser.add_argument(
        "--backends",
        default="pyocrust,rapidocr",
        help="separados por comas; los no disponibles se marcan skipped",
    )
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--task-types", default="text,structure,formula,full_page")
    parser.add_argument("--manifest", type=Path, help="JSON local images with supplied text/markdown/blocks GT")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--device", choices=["cpu", "gpu"], default="cpu")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    args = parser.parse_args(argv)
    tasks = set(args.task_types.split(","))
    if not tasks <= {"text", "structure", "formula", "full_page"} or args.limit < 0 or args.warmup < 0 or args.repeats < 1:
        parser.error("invalid task types or limits")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_dir = args.output_dir / timestamp
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[dataset] {args.dataset} split={args.split} limit={args.limit}")
    samples = load_local(args.manifest, args.limit) if args.manifest else load_funsd(split=args.split, limit=args.limit)
    if args.manifest:
        args.dataset = str(args.manifest.resolve())
    print(f"[dataset] {len(samples)} muestras cargadas")

    all_rows: list[dict] = []
    summary: dict[str, dict] = {}
    for backend in [b.strip() for b in args.backends.split(",") if b.strip()]:
        if backend not in PROVIDERS:
            print(f"[skip] backend desconocido: {backend}")
            summary[backend] = {"status": "skipped", "reason": "no registrado"}
            continue
        if TASK_TYPES.get(backend, "text") not in tasks:
            summary[backend] = {"status": "skipped", "reason": "task type excluded"}
            continue
        print(f"\n[run] {backend} ...")
        rows, meta = run_benchmark(samples, backend, args.dataset, warmup=args.warmup, repeats=args.repeats, device=args.device)
        all_rows.extend(rows)
        summary[backend] = meta
        if meta.get("status") == "skipped":
            print(f"  skipped: {meta['reason']}")
        elif not meta.get("n_ok"):
            # B4/D8: sin muestras medidas no hay nada que agregar (p.ej. --limit 1)
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
            {"timestamp": timestamp, "runtime": _describe_runtime(), "backends": summary},
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
