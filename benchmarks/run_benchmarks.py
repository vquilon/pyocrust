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
Esquema de columnas (contrato con `report_benchmarks.py`, 25 columnas):
    run_timestamp,backend,dataset,image_id,cer,wer,cer_ord,wer_ord,word_f1,
    exact_match,elapsed_ms,n_regions,mean_confidence,n_chars_gt,n_chars_pred,
    status,error,task_type,model_name,model_variant,markdown_f1,block_f1,
    latex_exact,latex_sim,latex_token_f1

Las tres últimas (`latex_*`) solo se rellenan en `task_type=formula` (vacías en el
resto): miden la fórmula contra su GT sobre la **forma canónica** de LaTeX
(`latex_metrics.py`) y no sobre el texto crudo.

Eje `task_type`: `text` (pp_ocrv6 tiny), `structure` (pp_structurev3 → Markdown),
`formula` (pp_structurev3 + pp-formulanet-s → LaTeX), `full_page` (indra con math
→ Markdown + LaTeX). `markdown_f1`/`block_f1` van vacíos (`""`) en `text`.

Dataset `--dataset omnidocbench_formula` (analisis de formulas, no de pagina): toma
cada bloque `equation_isolated` de OmniDocBench como **una muestra** —recorte de la
imagen + su **LaTeX anotado** como GT— y fuerza `task_type=formula` en **todos** los
adaptadores, para que motores que no emiten LaTeX (`rapidocr`, `easyocr`, `pyocrust`
tiny, `tesseract`) compitan sobre la **misma entrada** y quede medido, no supuesto,
qué reproduce cada uno el LaTeX. El recorte usa el `poly` anotado con 4 px de margen;
el GT se normaliza quitando los `$` de delimitador (`$$...$$` → `...`).

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

from latex_metrics import latex_exact, latex_similarity, latex_token_f1

# Origen único del mapeo backend -> banco por feature (columna aditiva `feature`).
from common.runner import (
    FEATURE_TYPES,
    GPU_NOT_CONFIRMED,
    GPU_PROVIDERS,
    available_providers,
    device_outcome,
    pyocrust_device_arg,
)

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
    "latex_exact", "latex_sim", "latex_token_f1",
    "feature",
    "box_recall", "box_iou_mean",
    # Honestidad de proveedor: dispositivo pedido vs. el que de verdad corrió.
    "device_requested", "provider_effective",
    # Métricas de las features de layout/tabla/orientación/rectificado: este CLI
    # no las produce (no tiene sus datasets ni su scorer), así que van vacías.
    "layout_map", "layout_recall", "table_teds", "ori_acc", "rect_sim",
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
    # Per-task GT override for `gt_text`: some datasets carry modality-specific
    # references (e.g. OmniDocBench annotates each display formula's LaTeX), so
    # the formula task can be scored against formula GT instead of page prose.
    gt_by_task: dict[str, str] | None = None


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
# Dataset documental: OmniDocBench (paginas de documentos reales con GT)
# ---------------------------------------------------------------------------
#
# `opendatalab/OmniDocBench` (v1.6, 1651 paginas) anota cada bloque de la
# pagina (parrafos, titulos, tablas, formulas, ...) con su `text` o su `latex`
# y da el **orden de lectura** (`order`). El GT de texto de una pagina es, por
# tanto, su contenido anotado en ese orden: no se inventa nada.
#
# La release (HF) **no** publica un Markdown de pagina ya renderizado —su
# `answer`/anotacion es el mismo JSON de bloques—, asi que `gt_markdown` y
# `gt_blocks` quedan a `None` y la calidad Markdown/bloques se reporta como
# **no evaluada** (regla de la tarjeta: no inventar GT). Lo que si da el dataset
# es el **LaTeX de cada formula** (`equation_isolated`), que se usa como GT de la
# tarea `formula` via `gt_by_task`.

OMNIDOCBENCH_REPO = "opendatalab/OmniDocBench"
# Revision **fijada** (misma que `common/datasets.OMNIDOCBENCH_REVISION`): este
# driver historico no puede bajar la revision vigente de cada fecha, o dos runs
# medirian sobre datos distintos sin que nadie lo note.
OMNIDOCBENCH_REVISION = "aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec"


def _odb_block_content(det: dict) -> str:
    """Texto anotado de un bloque de prosa (parrafo, titulo, pie, ...).

    Las formulas y tablas anotadas solo traen `latex`/`html`; se dejan fuera del
    GT de texto para no mezclar modalidades: su referencia viaja aparte en
    `gt_by_task["formula"]`.
    """
    return str(det.get("text") or "")


def _odb_page_text(page: dict) -> str:
    """GT de texto de la pagina: bloques no ignorados, en orden de lectura."""
    blocks = [d for d in page["layout_dets"] if not d.get("ignore")]
    blocks.sort(key=lambda d: d.get("order") or (1 << 30))
    return " ".join(filter(None, (_odb_block_content(d) for d in blocks)))


def _odb_page_formulas(page: dict) -> str:
    """GT LaTeX de las formulas mostradas (`equation_isolated`) de la pagina."""
    blocks = [d for d in page["layout_dets"]
              if not d.get("ignore") and d["category_type"] == "equation_isolated"]
    blocks.sort(key=lambda d: d.get("order") or (1 << 30))
    return "\n".join(filter(None, (d.get("latex") for d in blocks)))


def load_omnidocbench(limit: int | None = None, cache_dir: Path | None = None) -> list[Sample]:
    """Carga OmniDocBench (dataset documental con GT) desde Hugging Face.

    Descarga y cachea la anotacion y solo las imagenes de las paginas elegidas
    en `benchmarks/data_cache` (gitignored). La seleccion prioriza paginas con
    tabla o formula para cubrir las casuisticas de `pyocrust` (estructura,
    formulas) sin dejar de lado las de texto.
    """
    try:
        from huggingface_hub import hf_hub_download
    except ImportError as exc:  # pragma: no cover - entorno sin huggingface_hub
        raise ProviderUnavailable(
            "pip install huggingface_hub para descargar OmniDocBench"
        ) from exc

    cache = cache_dir or (HERE / "data_cache")
    cache.mkdir(parents=True, exist_ok=True)
    ann = hf_hub_download(OMNIDOCBENCH_REPO, "OmniDocBench.json",
                          repo_type="dataset", revision=OMNIDOCBENCH_REVISION,
                          cache_dir=str(cache))
    pages = json.loads(Path(ann).read_text(encoding="utf-8"))

    def kinds(page: dict) -> set[str]:
        return {d["category_type"] for d in page["layout_dets"] if not d.get("ignore")}

    # Deterministic: rich pages (tabla o formula) primero, luego el resto.
    rich_idx = [i for i, p in enumerate(pages) if kinds(p) & {"table", "equation_isolated"}]
    rest_idx = [i for i in range(len(pages)) if i not in set(rich_idx)]
    ordered = [pages[i] for i in (rich_idx + rest_idx)]
    if limit is not None:
        ordered = ordered[:limit]

    samples: list[Sample] = []
    for page in ordered:
        name = str(page["page_info"]["image_path"])
        path = hf_hub_download(OMNIDOCBENCH_REPO, f"images/{name}",
                               repo_type="dataset", revision=OMNIDOCBENCH_REVISION,
                               cache_dir=str(cache))
        formulas = _odb_page_formulas(page)
        samples.append(Sample(
            image_id=name,
            image=Image.open(path).convert("RGB"),
            gt_text=_odb_page_text(page),
            gt_markdown=None,
            gt_blocks=None,
            gt_by_task={"formula": formulas} if formulas else None,
        ))
    (cache / "omnidocbench.ok").write_text(f"{len(samples)} samples\n", encoding="utf-8")
    return samples


# ---------------------------------------------------------------------------
# Dataset de formulas: un recorte por bloque `equation_isolated`
# ---------------------------------------------------------------------------
#
# La tarea `formula` de `load_omnidocbench` puntúa el **LaTeX de todas las formulas
# de la pagina** contra lo que emite el motor para la pagina entera: mide, sobre
# todo, diferencia de formato y de granularidad. Para medir reconocimiento de
# formulas de verdad —y de forma comparable entre motores— la unidad aqui es cada
# formula anotada: se recorta su region (`poly`) y el GT es su `latex`.

def _odb_formula_pages(pages: list, limit: int | None) -> list[tuple]:
    """Paginas con formulas (en orden de anotacion), recortadas a `limit` bloques."""
    selected: list[tuple] = []
    total = 0
    for page in pages:
        dets = [d for d in page["layout_dets"]
                if not d.get("ignore") and d["category_type"] == "equation_isolated" and d.get("latex")]
        if not dets:
            continue
        if limit is not None:
            dets = dets[: max(0, limit - total)]
            if not dets:
                break
        total += len(dets)
        selected.append((str(page["page_info"]["image_path"]), page, dets))
        if limit is not None and total >= limit:
            break
    return selected


def _crop_poly(image: Image.Image, poly: Sequence[float], pad: int = 4) -> Image.Image:
    """Recorte del poligono anotado (caja envolvente) con `pad` px de margen."""
    xs, ys = poly[0::2], poly[1::2]
    x1, y1 = max(0, int(min(xs)) - pad), max(0, int(min(ys)) - pad)
    x2, y2 = min(image.width, int(max(xs)) + pad), min(image.height, int(max(ys)) + pad)
    return image.crop((x1, y1, x2, y2))


def load_omnidocbench_formulas(limit: int | None = None, cache_dir: Path | None = None) -> list[Sample]:
    """Una muestra por formula: recorte de la imagen + su LaTeX anotado como GT."""
    try:
        from huggingface_hub import hf_hub_download
    except ImportError as exc:  # pragma: no cover - entorno sin huggingface_hub
        raise ProviderUnavailable(
            "pip install huggingface_hub para descargar OmniDocBench"
        ) from exc

    cache = cache_dir or (HERE / "data_cache")
    cache.mkdir(parents=True, exist_ok=True)
    ann = hf_hub_download(OMNIDOCBENCH_REPO, "OmniDocBench.json",
                          repo_type="dataset", revision=OMNIDOCBENCH_REVISION,
                          cache_dir=str(cache))
    pages = json.loads(Path(ann).read_text(encoding="utf-8"))

    samples: list[Sample] = []
    for name, _page, dets in _odb_formula_pages(pages, limit):
        path = hf_hub_download(OMNIDOCBENCH_REPO, f"images/{name}",
                               repo_type="dataset", revision=OMNIDOCBENCH_REVISION,
                               cache_dir=str(cache))
        image = Image.open(path).convert("RGB")
        for det in dets:
            # GT sin delimitadores `$`: el motor de formulas emite LaTeX "desnudo".
            gt = " ".join(str(det["latex"]).replace("$", "").split())
            samples.append(Sample(
                image_id=f"{Path(name).stem}::{det.get('anno_id', 'eq')}",
                image=_crop_poly(image, det["poly"]),
                gt_text=gt,
            ))
    (cache / "omnidocbench_formulas.ok").write_text(f"{len(samples)} samples\n", encoding="utf-8")
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


def _pyocrust_backend(preset: str, formula_only: bool = False, device: str = "cpu") -> Callable[[Image.Image], OcrOutput]:
    import pyocrust  # noqa: PLC0415 - import tardío para no penalizar el arranque

    engine = pyocrust.VeloceOCR(preset=preset, device=device)

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

    run.provider_effective = getattr(engine, "provider_effective", None)
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
        "available_providers": available_providers(),
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
) -> tuple[list[dict], dict]:
    """Ejecuta un backend sobre todas las muestras y devuelve (filas, metadatos).

    `task_override` fuerza el `task_type` de las filas (p. ej. `formula` sobre el
    dataset de recortes de formula) aunque el backend sea de otra familia; el GT
    sigue siendo el de la muestra. Si `dump` no es None, se rellena con
    `{image_id, text}` de cada muestra medida: la salida cruda no cabe en el CSV de
    contrato fijo y hace falta para medir, p. ej., quien emite LaTeX de verdad.
    """
    task_type = task_override or TASK_TYPES.get(backend, "text")
    model_name, model_variant = MODEL_NAMES.get(backend, (backend, "default"))
    provider_effective, skip_reason = device_outcome(backend, device)
    provenance = {"task_type": task_type, "model_name": model_name, "model_variant": model_variant,
                  "device_requested": device,
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
        # Los backends `pyocrust` reciben el `device` resuelto (`cpu`/`auto`); el
        # resto —y las factorías inyectadas (p. ej. en tests)— no lo aceptan.
        runner = (factory(pyocrust_device_arg(device))
                  if backend_factory is None and backend.startswith("pyocrust")
                  else factory())
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
                    "feature": FEATURE_TYPES.get(backend, "text"),
                    "box_recall": "", "box_iou_mean": "",
                    "device_requested": device, "provider_effective": provider_effective,
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
                # Aditivas del banco por feature: banco que produjo la fila + cajas.
                # Sin cajas GT en este driver, la detección queda "no evaluada" (""),
                # nunca un 0.0 espurio.
                "feature": FEATURE_TYPES.get(backend, "text"),
                "box_recall": "", "box_iou_mean": "",
                "device_requested": device, "provider_effective": provider_effective,
                # Métricas por feature: este CLI no las calcula -> no evaluadas ("").
                "layout_map": "", "layout_recall": "", "table_teds": "",
                "ori_acc": "", "rect_sim": "",
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
    parser.add_argument("--dataset", default=DEFAULT_DATASET, choices=["funsd", "omnidocbench", "omnidocbench_formula"])
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
    elif args.dataset == "omnidocbench":
        samples = load_omnidocbench(limit=args.limit)
    elif args.dataset == "omnidocbench_formula":
        samples = load_omnidocbench_formulas(limit=args.limit)
    else:
        samples = load_funsd(split=args.split, limit=args.limit)
    # Los recortes de formula se evaluan con `task_type=formula` en TODOS los
    # adaptadores: la entrada ya es una formula, no una pagina que haya que tipar.
    force_task = "formula" if args.dataset == "omnidocbench_formula" else None
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
        if (force_task or TASK_TYPES.get(backend, "text")) not in tasks:
            summary[backend] = {"status": "skipped", "reason": "task type excluded"}
            continue
        print(f"\n[run] {backend} ...")
        dump: list[dict] | None = [] if args.dump_outputs else None
        rows, meta = run_benchmark(samples, backend, args.dataset, warmup=args.warmup, repeats=args.repeats, device=args.device, task_override=force_task, dump=dump)
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
