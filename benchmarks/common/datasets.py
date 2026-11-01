"""Carga de datasets con ground truth para los bancos por feature.

Movido desde `benchmarks/run_benchmarks.py` en la reorganización por feature.
Cada banco declara **su** dataset y aquí viven los cargadores compartidos:

* `funsd` — formularios escaneados en inglés (`nielsr/funsd`): GT de texto por
  orden de lectura por caja y, además, las **cajas** anotadas (`gt_boxes`), que
  el banco de `text` usa para medir detección además de reconocimiento.
* `omnidocbench` — páginas documentales reales (`opendatalab/OmniDocBench` v1.6):
  GT de texto por orden de lectura y LaTeX por fórmula (`gt_by_task`).
* `omnidocbench_formula` — una muestra por bloque `equation_isolated`: recorte de
  la fórmula (`poly` + margen) y su LaTeX anotado como GT.
* `--manifest` — JSON local con `image` + `text`/`markdown`/`blocks` de GT.

Regla: **no se inventa GT**. Lo que el dataset no anota queda a `None` y la
métrica correspondiente se reporta como *no evaluada*, nunca como un `0.0`
espurio.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from PIL import Image

BENCHMARKS_ROOT = Path(__file__).resolve().parent.parent
DATA_CACHE = BENCHMARKS_ROOT / "data_cache"

OMNIDOCBENCH_REPO = "opendatalab/OmniDocBench"


@dataclass(frozen=True)
class Sample:
    image_id: str
    image: Image.Image
    gt_text: str
    gt_markdown: str | None = None
    gt_blocks: tuple[str, ...] | None = None
    # Cajas GT `(x1, y1, x2, y2)` cuando el dataset las anota (p. ej. FUNSD):
    # permiten medir detección (recall@IoU) además de reconocimiento.
    gt_boxes: tuple[tuple[float, float, float, float], ...] | None = None
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


# ---------------------------------------------------------------------------
# FUNSD (formularios escaneados, 149 train + 50 test)
# ---------------------------------------------------------------------------


def load_funsd(split: str = "train", limit: int | None = None) -> list[Sample]:
    """Carga FUNSD desde Hugging Face, cacheado en `benchmarks/data_cache`."""
    try:
        from datasets import load_dataset
    except ImportError as exc:  # pragma: no cover - entorno sin `datasets`
        raise DatasetUnavailable(
            "pip install datasets (y pyarrow) para descargar FUNSD"
        ) from exc

    cache = DATA_CACHE
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
                # Cajas GT anotadas (misma fuente que el texto): detección.
                gt_boxes=tuple(tuple(float(v) for v in box) for box in bboxes),
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
# **no evaluada** (regla del banco: no inventar GT). Lo que si da el dataset
# es el **LaTeX de cada formula** (`equation_isolated`), que se usa como GT de la
# tarea `formula` via `gt_by_task`.


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
    pages = _load_omnidocbench_pages(cache_dir)

    def kinds(page: dict) -> set[str]:
        return {d["category_type"] for d in page["layout_dets"] if not d.get("ignore")}

    # Deterministic: rich pages (tabla o formula) primero, luego el resto.
    rich_idx = [i for i, p in enumerate(pages) if kinds(p) & {"table", "equation_isolated"}]
    rest_idx = [i for i in range(len(pages)) if i not in set(rich_idx)]
    ordered = [pages[i] for i in (rich_idx + rest_idx)]
    if limit is not None:
        ordered = ordered[:limit]

    cache = cache_dir or DATA_CACHE
    samples: list[Sample] = []
    for page in ordered:
        name = str(page["page_info"]["image_path"])
        image = _odb_image(name, cache)
        formulas = _odb_page_formulas(page)
        samples.append(Sample(
            image_id=name,
            image=image,
            gt_text=_odb_page_text(page),
            gt_markdown=None,
            gt_blocks=None,
            gt_by_task={"formula": formulas} if formulas else None,
        ))
    (cache / "omnidocbench.ok").write_text(f"{len(samples)} samples\n", encoding="utf-8")
    return samples


def _load_omnidocbench_pages(cache_dir: Path | None) -> list:
    try:
        from huggingface_hub import hf_hub_download
    except ImportError as exc:  # pragma: no cover - entorno sin huggingface_hub
        raise DatasetUnavailable(
            "pip install huggingface_hub para descargar OmniDocBench"
        ) from exc
    cache = cache_dir or DATA_CACHE
    cache.mkdir(parents=True, exist_ok=True)
    ann = hf_hub_download(OMNIDOCBENCH_REPO, "OmniDocBench.json",
                          repo_type="dataset", cache_dir=str(cache))
    return json.loads(Path(ann).read_text(encoding="utf-8"))


def _odb_image(name: str, cache: Path) -> Image.Image:
    from huggingface_hub import hf_hub_download

    path = hf_hub_download(OMNIDOCBENCH_REPO, f"images/{name}",
                           repo_type="dataset", cache_dir=str(cache))
    return Image.open(path).convert("RGB")


# ---------------------------------------------------------------------------
# Dataset de formulas: un recorte por bloque `equation_isolated`
# ---------------------------------------------------------------------------
#
# La tarea `formula` de `load_omnidocbench` puntúa el **LaTeX de todas las
# formulas de la pagina** contra lo que emite el motor para la pagina entera:
# mide, sobre todo, diferencia de formato y de granularidad. Para medir
# reconocimiento de formulas de verdad —y de forma comparable entre motores— la
# unidad aqui es cada formula anotada: se recorta su region (`poly`) y el GT es
# su `latex`.


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
    pages = _load_omnidocbench_pages(cache_dir)
    cache = cache_dir or DATA_CACHE

    samples: list[Sample] = []
    for name, _page, dets in _odb_formula_pages(pages, limit):
        image = _odb_image(name, cache)
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
# Registro de datasets por nombre (cada feature declara el suyo)
# ---------------------------------------------------------------------------

DATASETS = {
    "funsd": lambda limit, split, cache: load_funsd(split=split, limit=limit),
    "omnidocbench": lambda limit, split, cache: load_omnidocbench(limit=limit, cache_dir=cache),
    "omnidocbench_formula": lambda limit, split, cache: load_omnidocbench_formulas(limit=limit, cache_dir=cache),
}


class DatasetUnavailable(RuntimeError):
    """El dataset no se puede cargar en este entorno (falta una dependencia/cache)."""


def load_dataset(name: str, limit: int | None = None, split: str = "train",
                 cache_dir: Path | None = None) -> list[Sample]:
    """Carga un dataset registrado por nombre (interfaz común a los bancos)."""
    if name not in DATASETS:
        raise DatasetUnavailable(f"dataset desconocido: {name} (usa {sorted(DATASETS)})")
    return DATASETS[name](limit, split, cache_dir)


def _self_check() -> None:
    page = {
        "layout_dets": [
            {"category_type": "text_block", "ignore": False, "order": 2, "text": "second"},
            {"category_type": "equation_isolated", "ignore": False, "order": 1, "latex": "$$E=mc^2$$"},
            {"category_type": "title", "ignore": False, "order": None, "text": "first"},
            {"category_type": "header", "ignore": True, "order": 0, "text": "ignored"},
        ],
        "page_info": {"image_path": "p.png"},
    }
    assert _odb_page_text(page) == "second first"
    assert _odb_page_formulas(page) == "$$E=mc^2$$"
    assert _odb_formula_pages([page], 1)[0][2][0]["latex"] == "$$E=mc^2$$"
    assert _crop_poly(Image.new("RGB", (20, 20)), [2, 3, 8, 3, 8, 9, 2, 9], pad=0).size == (6, 6)
    assert "funsd" in DATASETS and "omnidocbench_formula" in DATASETS
    print("common.datasets self-check OK")


if __name__ == "__main__":
    _self_check()
