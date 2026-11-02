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
    # GT de **layout**: clase -> cajas `(x1, y1, x2, y2)`. OmniDocBench anota
    # `category_type` + `poly` por bloque; permite mAP@IoU por clase.
    gt_layout: dict[str, tuple[tuple[float, float, float, float], ...]] | None = None
    # GT de **estructura de tabla**: el `html` anotado del bloque `table`.
    gt_html: str | None = None
    # GT de **clasificación** (orientación de página/línea): la etiqueta anotada.
    gt_label: str | None = None
    # GT de **rectificación**: la imagen limpia de la que se partió.
    gt_image: Image.Image | None = None


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


def _odb_rich_first(pages: list) -> list:
    """Orden determinista: páginas con tabla o fórmula primero, luego el resto.

    El dataset arranca con páginas ricas porque son las que cubren las
    casuísticas de `pyocrust` (estructura, tablas, fórmulas) sin dejar de lado
    las de texto; el orden es estable entre ejecuciones (no hay aleatoriedad).
    """
    rich_idx = [i for i, p in enumerate(pages) if _odb_kinds(p) & {"table", "equation_isolated"}]
    rich = set(rich_idx)
    return [pages[i] for i in rich_idx + [i for i in range(len(pages)) if i not in rich]]


def _odb_kinds(page: dict) -> set[str]:
    """Categorías anotadas (no ignoradas) de la página."""
    return {d["category_type"] for d in page["layout_dets"] if not d.get("ignore")}


def load_omnidocbench(limit: int | None = None, cache_dir: Path | None = None) -> list[Sample]:
    """Carga OmniDocBench (dataset documental con GT) desde Hugging Face.

    Descarga y cachea la anotacion y solo las imagenes de las paginas elegidas
    en `benchmarks/data_cache` (gitignored). La seleccion prioriza paginas con
    tabla o formula para cubrir las casuisticas de `pyocrust` (estructura,
    formulas) sin dejar de lado las de texto.
    """
    pages = _odb_rich_first(_load_omnidocbench_pages(cache_dir))
    if limit is not None:
        pages = pages[:limit]

    cache = cache_dir or DATA_CACHE
    samples: list[Sample] = []
    for page in pages:
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
# Adaptadores de GT de OmniDocBench por feature
# ---------------------------------------------------------------------------
#
# El dataset anota cada bloque con su `category_type` + `poly`, y ademas lleva
# `latex` (formulas) y `html` (tablas). Los adaptadores de aqui traducen esa
# anotacion a la GT que cada banco necesita, **sin inventar nada**: lo que el
# dataset no anota se queda a `None` y la metrica correspondiente sale `N/A`.

# Vocabulario del detector de layout de `pyocrust` (`pp_doclayoutv3`, 25 clases;
# oar-ocr-core `layout_detection_adapter.rs`) -> categorias de OmniDocBench. Solo
# se evaluan las categorias que aparecen como destino de este mapa; el resto de
# etiquetas del modelo se ignoran (y se documenta asi en el README del banco).
LAYOUT_MODEL_TO_GT = {
    "text": "text_block",
    "doc_title": "title",
    "paragraph_title": "title",
    "display_formula": "equation_isolated",
    "table": "table",
    "image": "figure",
    "figure_title": "figure_caption",
    "header": "header",
    "footer": "footer",
    "number": "page_number",
    "footnote": "page_footnote",
    "reference": "reference",
    "reference_content": "reference",
}

# Vocabulario de las alternativas con pesos del tipo DocLayNet (RT-DETR
# `docling-layout-heron-101`, Deformable-DETR y los tres YOLO documentales):
# etiqueta del modelo -> categoria anotada de OmniDocBench. Es la **composicion**
# de `runner.LAYOUT_DOCLAYNET_LABEL_TO_MODEL` con `LAYOUT_MODEL_TO_GT` de arriba,
# cacheada aqui para no encadenar dos diccionarios al puntuar; el por que de cada
# par, con su fuente, esta en `features/layout/class_map.md`.
#
# DocLayNet (11 clases) **no tiene** clase para `page_number` ni `reference`: esas
# categorias anotadas no son emitibles por estos modelos y por tanto se **ignoran**
# al puntuarlos (ver `layout_gt_classes`), en vez de contarse como fallo.
LAYOUT_DOCLAYNET_LABEL_TO_GT = {
    "text": "text_block",
    "title": "title",
    "section-header": "title",
    "formula": "equation_isolated",
    "table": "table",
    "picture": "figure",
    "caption": "figure_caption",
    "page-header": "header",
    "page-footer": "footer",
    "footnote": "page_footnote",
}

# Categorias anotadas que puede emitir cada familia de modelo (proyeccion de su
# vocabulario al de OmniDocBench). La metrica macro promedia solo sobre la
# **interseccion** GT-cap emitibles: una categoria que el modelo no puede emitir
# se cuenta como **ignorada** (ni acierto ni fallo silencioso).
_LAYOUT_PP_GT_CLASSES = frozenset(LAYOUT_MODEL_TO_GT.values())
_LAYOUT_DOCLAYNET_GT_CLASSES = frozenset(LAYOUT_DOCLAYNET_LABEL_TO_GT.values())

# `extra["engine"]` de los adaptadores cuyo vocabulario es DocLayNet.
LAYOUT_DOCLAYNET_ENGINES = frozenset({"transformers", "ultralytics"})


def layout_gt_classes(engine: str | None) -> frozenset[str]:
    """Categorias anotadas que puede emitir un motor de layout por su `engine`.

    Sin `engine` (o uno desconocido) se devuelve el conjunto **completo** de
    `LAYOUT_MODEL_TO_GT` — el vocabulario mas amplio, el de `pp_doclayoutv3`
    (detector propio): asi un motor nuevo no pierde categorias por defecto. Solo
    los vocabularios **mas estrechos** (DocLayNet) recortan la interseccion.
    """
    if str(engine or "").strip().lower() in LAYOUT_DOCLAYNET_ENGINES:
        return _LAYOUT_DOCLAYNET_GT_CLASSES
    return _LAYOUT_PP_GT_CLASSES


# Categorias de OmniDocBench -> vocabulario de `kind` que emite el pipeline
# completo (`pp_structurev3`), para que `block_f1` compare la misma taxonomia en
# ambos lados en vez de restar dos vocabularios distintos.
ODB_CATEGORY_TO_KIND = {
    "text_block": "text",
    "title": "paragraph_title",
    "header": "header",
    "footer": "footer",
    "page_number": "number",
    "list_group": "list",
    "reference": "reference",
    "page_footnote": "footnote",
    "table_footnote": "footnote",
    "figure_footnote": "footnote",
    "figure_caption": "figure_title",
    "table_caption": "figure_title",
    "equation_caption": "figure_title",
    "code_txt_caption": "figure_title",
    "code_txt": "text",
    "equation_explanation": "text",
    "equation_isolated": "formula",
    "equation_semantic": "formula",
    "table": "table",
    "figure": "image",
}

# Categorias que NO aportan contenido legible (mascaras de region).
_NON_CONTENT_SUFFIX = "_mask"


def _odb_poly_bbox(poly: Sequence[float]) -> tuple[float, float, float, float]:
    """Caja envolvente `(x1, y1, x2, y2)` del poligono anotado."""
    xs, ys = list(poly)[0::2], list(poly)[1::2]
    return (float(min(xs)), float(min(ys)), float(max(xs)), float(max(ys)))


def _odb_content_blocks(page: dict) -> list[dict]:
    """Bloques de contenido de la pagina, en orden de lectura.

    Se excluyen los `ignore` y las mascaras (`*_mask`, `abandon`), que no son
    contenido del documento.
    """
    blocks = [d for d in page["layout_dets"]
              if not d.get("ignore")
              and d["category_type"] != "abandon"
              and not d["category_type"].endswith(_NON_CONTENT_SUFFIX)]
    blocks.sort(key=lambda d: d.get("order") or (1 << 30))
    return blocks


def _odb_block_body(det: dict) -> str:
    """Contenido anotado de un bloque: su texto, su LaTeX o su HTML de tabla."""
    return str(det.get("text") or det.get("latex") or det.get("html") or "")


def _odb_page_markdown(page: dict) -> str:
    """Markdown GT reconstruido de los bloques anotados en orden de lectura.

    La release de OmniDocBench no publica un Markdown de pagina renderizado, pero
    **si** anota el contenido de cada bloque (`text`/`latex`/`html`) y su `order`:
    el Markdown de referencia es la concatenacion de esos contenidos en ese
    orden. No se inventa contenido; solo se serializa lo que ya esta anotado.
    """
    return "\n\n".join(filter(None, (_odb_block_body(d) for d in _odb_content_blocks(page))))


def _odb_page_blocks(page: dict) -> tuple[str, ...]:
    """Tipos de bloque (vocabulario `kind`) de los bloques con contenido."""
    kinds = (ODB_CATEGORY_TO_KIND.get(d["category_type"]) for d in _odb_content_blocks(page))
    return tuple(kind for kind in kinds if kind)


def _odb_page_layout(page: dict) -> dict[str, tuple[tuple[float, float, float, float], ...]]:
    """GT de layout: categoria de bloque -> cajas, solo categorias mapeadas."""
    mapped = set(LAYOUT_MODEL_TO_GT.values())
    boxes: dict[str, list] = {}
    for det in page["layout_dets"]:
        category = det["category_type"]
        if det.get("ignore") or category not in mapped:
            continue
        boxes.setdefault(category, []).append(_odb_poly_bbox(det["poly"]))
    return {category: tuple(values) for category, values in boxes.items()}


def load_omnidocbench_layout(limit: int | None = None, cache_dir: Path | None = None) -> list[Sample]:
    """Paginas con GT de **layout** (cajas anotadas por clase de bloque)."""
    cache = cache_dir or DATA_CACHE
    pages = _odb_rich_first(_load_omnidocbench_pages(cache_dir))
    samples: list[Sample] = []
    for page in pages:
        layout = _odb_page_layout(page)
        if not layout:
            continue
        name = str(page["page_info"]["image_path"])
        samples.append(Sample(image_id=name, image=_odb_image(name, cache),
                              gt_text="", gt_layout=layout))
        if limit is not None and len(samples) >= limit:
            break
    return samples


def load_omnidocbench_tables(limit: int | None = None, cache_dir: Path | None = None) -> list[Sample]:
    """Una muestra por tabla anotada: recorte del `poly` + su `html` como GT."""
    cache = cache_dir or DATA_CACHE
    pages = _odb_rich_first(_load_omnidocbench_pages(cache_dir))
    samples: list[Sample] = []
    for page in pages:
        dets = [d for d in page["layout_dets"]
                if d["category_type"] == "table" and not d.get("ignore") and d.get("html")]
        if not dets:
            continue
        name = str(page["page_info"]["image_path"])
        image = _odb_image(name, cache)
        for det in dets:
            samples.append(Sample(
                image_id=f"{Path(name).stem}::{det.get('anno_id', 'tbl')}",
                image=_crop_poly(image, det["poly"]),
                gt_text="", gt_html=str(det["html"]),
            ))
            if limit is not None and len(samples) >= limit:
                return samples
    return samples


def load_omnidocbench_full_page(limit: int | None = None, cache_dir: Path | None = None) -> list[Sample]:
    """Paginas con GT de **documento** completo (Markdown + bloques en orden)."""
    cache = cache_dir or DATA_CACHE
    pages = _odb_rich_first(_load_omnidocbench_pages(cache_dir))
    samples: list[Sample] = []
    for page in pages:
        markdown = _odb_page_markdown(page)
        if not markdown:
            continue
        name = str(page["page_info"]["image_path"])
        samples.append(Sample(
            image_id=name, image=_odb_image(name, cache),
            gt_text=_odb_page_text(page), gt_markdown=markdown,
            gt_blocks=_odb_page_blocks(page),
        ))
        if limit is not None and len(samples) >= limit:
            break
    return samples


# ---------------------------------------------------------------------------
# GT sintetico determinista (orientacion / linea de texto / rectificacion)
# ---------------------------------------------------------------------------
#
# Estas tres features no tienen un dataset con GT publico, pero su GT es **barato
# de generar y determinista**: se transforma una imagen limpia con una operacion
# conocida y el GT es esa operacion. Las imagenes base son las paginas de
# OmniDocBench **ya presentes en `benchmarks/data_cache`**, asi que no se
# descarga nada al ejecutar el banco.

ORIENTATION_ANGLES = (0, 90, 180, 270)
TEXT_LINE_ANGLES = (0, 180)
# Esquinas del destino deformado (fracciones del ancho/alto) de la homografia.
PERSPECTIVE_OFFSETS = ((0.06, 0.03), (0.96, 0.08), (0.93, 0.96), (0.08, 0.94))


def _cached_page_images(cache_dir: Path | None = None) -> list[Path]:
    """Paginas de OmniDocBench ya presentes en la cache local (sin red)."""
    root = (cache_dir or DATA_CACHE) / "datasets--opendatalab--OmniDocBench"
    return sorted(root.glob("snapshots/*/images/*.png"))


def _cached_page_annotation(cache_dir: Path | None = None) -> list:
    """Anotacion de OmniDocBench ya descargada (lista vacia si no esta)."""
    root = (cache_dir or DATA_CACHE) / "datasets--opendatalab--OmniDocBench"
    files = sorted(root.glob("snapshots/*/OmniDocBench.json"))
    return json.loads(files[0].read_text(encoding="utf-8")) if files else []


def _cached_text_lines(cache_dir: Path | None = None) -> list[tuple[str, Image.Image]]:
    """Recortes de bloques de texto de las paginas cacheadas (para `text_line`)."""
    pages = {str(p["page_info"]["image_path"]): p for p in _cached_page_annotation(cache_dir)}
    lines: list[tuple[str, Image.Image]] = []
    for path in _cached_page_images(cache_dir):
        page = pages.get(path.name)
        if page is None:
            continue
        image = Image.open(path).convert("RGB")
        for det in page["layout_dets"]:
            if det["category_type"] != "text_block" or det.get("ignore"):
                continue
            x1, y1, x2, y2 = _odb_poly_bbox(det["poly"])
            crop = image.crop((int(x1), int(y1), int(x2), int(y2)))
            if crop.width > 40 and 8 < crop.height < 120:
                lines.append((f"{path.stem}::{det.get('anno_id', 'line')}", crop))
    return lines


def load_synthetic_orientation(limit: int | None = None, cache_dir: Path | None = None) -> list[Sample]:
    """Paginas rotadas 0/90/180/270; GT = la etiqueta de **correccion** esperada.

    El clasificador de `pyocrust` (`document_orientation`, PP-LCNet) devuelve la
    rotacion que hay que **aplicar** para enderezar la pagina, no la que se le
    aplico: sobre una pagina rotada `a` grados emite `(360 - a) mod 360`
    (comprobado con las cuatro clases en una pagina real antes de escribir el
    banco). El GT sintetico es exactamente esa etiqueta.
    """
    paths = _cached_page_images(cache_dir)
    if not paths:
        raise DatasetUnavailable(
            "no hay paginas de OmniDocBench en benchmarks/data_cache para el GT sintetico"
        )
    samples: list[Sample] = []
    for i, path in enumerate(paths if limit is None else paths[:limit]):
        angle = ORIENTATION_ANGLES[i % len(ORIENTATION_ANGLES)]
        image = Image.open(path).convert("RGB")
        samples.append(Sample(
            image_id=f"{path.stem}::rot{angle}",
            image=image.rotate(angle, expand=True) if angle else image,
            gt_text="", gt_label=str((360 - angle) % 360),
        ))
    return samples


def load_synthetic_text_line(limit: int | None = None, cache_dir: Path | None = None) -> list[Sample]:
    """Lineas de texto giradas 0/180; GT = la etiqueta de orientacion aplicada."""
    lines = _cached_text_lines(cache_dir)
    if not lines:
        raise DatasetUnavailable(
            "no hay paginas de OmniDocBench en benchmarks/data_cache para cortar lineas"
        )
    samples: list[Sample] = []
    for i, (name, image) in enumerate(lines if limit is None else lines[:limit]):
        angle = TEXT_LINE_ANGLES[i % len(TEXT_LINE_ANGLES)]
        samples.append(Sample(image_id=f"{name}::rot{angle}",
                              image=image.rotate(180) if angle else image,
                              gt_text="", gt_label=str(angle)))
    return samples


def load_synthetic_rectification(limit: int | None = None, cache_dir: Path | None = None) -> list[Sample]:
    """Paginas deformadas con una homografia conocida; GT = la **imagen limpia**.

    La deformacion es determinista (cuatro esquinas fijas), asi que el par
    (deformada, limpia) es reproducible sin descargar ningun dataset: el motor
    debe devolver una imagen rectificada que se compara con la original.
    """
    paths = _cached_page_images(cache_dir)
    if not paths:
        raise DatasetUnavailable(
            "no hay paginas de OmniDocBench en benchmarks/data_cache para el GT sintetico"
        )
    samples: list[Sample] = []
    for path in (paths if limit is None else paths[:limit]):
        clean = _resize_max(Image.open(path).convert("RGB"), 1000)
        samples.append(Sample(image_id=f"{path.stem}::persp",
                              image=_perspective_warp(clean),
                              gt_text="", gt_image=clean))
    return samples


def _resize_max(image: Image.Image, max_side: int) -> Image.Image:
    """Escala la imagen para que su lado mayor mida `max_side` (sin deformar)."""
    scale = max_side / max(image.size)
    if scale >= 1.0:
        return image
    return image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))))


def _perspective_warp(image: Image.Image) -> Image.Image:
    """Aplica a la imagen una homografia fija (deformacion de perspectiva)."""
    try:
        import cv2
        import numpy as np
    except ImportError as exc:  # pragma: no cover - entorno sin opencv
        raise DatasetUnavailable(
            "pip install opencv-python-headless para el GT sintetico de rectificacion"
        ) from exc
    width, height = image.size
    source = np.float32([[0, 0], [width, 0], [width, height], [0, height]])
    destination = np.float32([[x * width, y * height] for x, y in PERSPECTIVE_OFFSETS])
    matrix = cv2.getPerspectiveTransform(source, destination)
    warped = cv2.warpPerspective(
        np.asarray(image), matrix, (width, height), borderValue=(255, 255, 255)
    )
    return Image.fromarray(warped)


# ---------------------------------------------------------------------------
# GT sintetico determinista para `seal` (sello pegado sobre documento blanco)
# ---------------------------------------------------------------------------
# No hay set publico local con sellos anotados (OmniDocBench v1.6 no anota
# `category_type=seal`; verificado sobre la anotacion cacheada). El GT de `seal`
# es **barato y determinista**: se pega un sello (tampon) en una posicion conocida
# de un documento blanco y la caja GT es el rectangulo del sello pegado. Es un set
# **SINTETICO** y asi se declara en el provenance del banco — no es anotacion
# humana de sellos reales.

SEAL_DOC_SIZE = (1000, 960)
SEAL_STAMP_SIZE = (420, 160)
SEAL_TEXTS = ("SELLO OFICIAL", "AYUNTAMIENTO", "REGISTRO CIVIL", "NOTARIA",
              "MINISTERIO", "CERTIFICADO", "COLEGIO OFICIAL", "SECRETARIA")
# Posiciones deterministas (esquina superior izquierda del sello) dentro del doc.
SEAL_POSITIONS = ((120, 140), (500, 260), (180, 640), (520, 720),
                  (300, 380), (140, 300), (560, 120), (260, 760))


def _seal_font(size: int):
    """Fuente determinista para el texto del sello (truetype del sistema si hay)."""
    from PIL import ImageFont

    for name in ("arial.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _draw_seal_stamp(text: str) -> Image.Image:
    """Tampon sintetico: doble borde rojo redondeado + texto centrado en rojo.

    El dibujo es determinista (mismas medidas, misma fuente); la caja GT del banco
    es el rectangulo del sello pegado, **independiente** de la fuente.
    """
    from PIL import ImageDraw

    width, height = SEAL_STAMP_SIZE
    stamp = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(stamp)
    draw.rounded_rectangle((3, 3, width - 4, height - 4), radius=16,
                           outline=(200, 30, 30), width=7)
    draw.rounded_rectangle((15, 15, width - 16, height - 16), radius=12,
                           outline=(200, 30, 30), width=2)
    font = _seal_font(52)
    try:
        draw.text((width / 2, height / 2), text, font=font, fill=(200, 30, 30), anchor="mm")
    except ValueError:  # pragma: no cover - fuente bitmap sin `anchor`
        draw.text((width / 4, height / 2 - 26), text, font=font, fill=(200, 30, 30))
    return stamp


def load_synthetic_seal(limit: int | None = None, cache_dir: Path | None = None) -> list[Sample]:
    """Sellos **sinteticos** pegados en posicion conocida; GT = caja del sello.

    Set determinista y declarado **sintetico** (no hay anotacion humana de sellos
    local). La caja GT es el rectangulo del tampon pegado, que es lo que el detector
    de sellos (`seal_text_detection`) debe localizar.
    """
    count = limit if limit is not None else len(SEAL_TEXTS)
    samples: list[Sample] = []
    for i in range(count):
        text = SEAL_TEXTS[i % len(SEAL_TEXTS)]
        x, y = SEAL_POSITIONS[i % len(SEAL_POSITIONS)]
        document = Image.new("RGB", SEAL_DOC_SIZE, "white")
        stamp = _draw_seal_stamp(text)
        document.paste(stamp, (x, y))
        width, height = SEAL_STAMP_SIZE
        samples.append(Sample(
            image_id=f"synthetic_seal::{i:02d}::{x},{y}",
            image=document, gt_text="",
            gt_boxes=((float(x), float(y), float(x + width), float(y + height)),),
        ))
    return samples


# ---------------------------------------------------------------------------
# Registro de datasets por nombre (cada feature declara el suyo)
# ---------------------------------------------------------------------------

DATASETS = {
    "funsd": lambda limit, split, cache: load_funsd(split=split, limit=limit),
    "omnidocbench": lambda limit, split, cache: load_omnidocbench(limit=limit, cache_dir=cache),
    "omnidocbench_formula": lambda limit, split, cache: load_omnidocbench_formulas(limit=limit, cache_dir=cache),
    # Adaptadores de GT por feature (OmniDocBench anota layout, tablas y bloques).
    "omnidocbench_layout": lambda limit, split, cache: load_omnidocbench_layout(limit=limit, cache_dir=cache),
    "omnidocbench_table": lambda limit, split, cache: load_omnidocbench_tables(limit=limit, cache_dir=cache),
    "omnidocbench_full_page": lambda limit, split, cache: load_omnidocbench_full_page(limit=limit, cache_dir=cache),
    # GT sintetico determinista, calculado desde las paginas ya cacheadas.
    "synthetic_orientation": lambda limit, split, cache: load_synthetic_orientation(limit=limit, cache_dir=cache),
    "synthetic_text_line": lambda limit, split, cache: load_synthetic_text_line(limit=limit, cache_dir=cache),
    "synthetic_rectification": lambda limit, split, cache: load_synthetic_rectification(limit=limit, cache_dir=cache),
    # Sello sintetico determinista (tampon pegado en documento blanco; GT = caja).
    "synthetic_seal": lambda limit, split, cache: load_synthetic_seal(limit=limit, cache_dir=cache),
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
    # Adaptadores de GT por feature sobre una pagina anotada (layout/tabla/documento).
    annotated = {
        "layout_dets": [
            {"category_type": "text_block", "ignore": False, "order": 1,
             "poly": [0, 0, 10, 0, 10, 5, 0, 5], "text": "hola"},
            {"category_type": "table", "ignore": False, "order": 2,
             "poly": [0, 5, 10, 5, 10, 9, 0, 9], "html": "<table><tr><td>x</td></tr></table>"},
            {"category_type": "equation_isolated", "ignore": False, "order": 3,
             "poly": [0, 9, 10, 9, 10, 12, 0, 12], "latex": "$$x$$"},
            {"category_type": "text_mask", "ignore": False, "order": 4, "text": "no"},
            {"category_type": "header", "ignore": True, "order": 0, "text": "ignorado"},
        ],
        "page_info": {"image_path": "p.png"},
    }
    assert _odb_page_markdown(annotated) == "hola\n\n<table><tr><td>x</td></tr></table>\n\n$$x$$"
    # `text_mask` (mascara) y el bloque `ignore` no son contenido ni bloques.
    assert _odb_page_blocks(annotated) == ("text", "table", "formula")
    # Solo las categorias con equivalencia en el vocabulario del modelo cuentan.
    assert _odb_page_layout(annotated) == {
        "text_block": ((0.0, 0.0, 10.0, 5.0),),
        "table": ((0.0, 5.0, 10.0, 9.0),),
        "equation_isolated": ((0.0, 9.0, 10.0, 12.0),),
    }
    assert set(LAYOUT_MODEL_TO_GT.values()) <= (
        {"text_block", "title", "equation_isolated", "table", "figure", "figure_caption",
         "header", "footer", "page_number", "page_footnote", "reference"}
    )
    # El mapa DocLayNet es la composicion runner.LAYOUT_DOCLAYNET_LABEL_TO_MODEL
    # (vocabulario pp_doclayoutv3) con LAYOUT_MODEL_TO_GT, y es mas estrecho: no
    # tiene `page_number` ni `reference`, que por tanto se ignoran al puntuar.
    assert LAYOUT_DOCLAYNET_LABEL_TO_GT == {
        "text": "text_block", "title": "title", "section-header": "title",
        "formula": "equation_isolated", "table": "table", "picture": "figure",
        "caption": "figure_caption", "page-header": "header",
        "page-footer": "footer", "footnote": "page_footnote",
    }
    assert layout_gt_classes(None) == frozenset(LAYOUT_MODEL_TO_GT.values())
    assert layout_gt_classes("PyOcrust") == frozenset(LAYOUT_MODEL_TO_GT.values())
    doclaynet = layout_gt_classes("transformers")
    assert doclaynet == layout_gt_classes("ultralytics")
    assert {"page_number", "reference"}.isdisjoint(doclaynet)
    assert doclaynet < layout_gt_classes(None)
    expected_datasets = {
        "funsd", "omnidocbench", "omnidocbench_formula", "omnidocbench_layout",
        "omnidocbench_table", "omnidocbench_full_page", "synthetic_orientation",
        "synthetic_text_line", "synthetic_rectification", "synthetic_seal",
    }
    assert expected_datasets <= set(DATASETS), sorted(expected_datasets - set(DATASETS))
    # Sello sintetico: la caja GT es el rectangulo del sello pegado (determinista).
    seals = load_synthetic_seal(limit=2)
    assert [s.gt_boxes for s in seals] == [
        ((120.0, 140.0, 540.0, 300.0),),
        ((500.0, 260.0, 920.0, 420.0),),
    ], [s.gt_boxes for s in seals]
    assert seals[0].image.size == SEAL_DOC_SIZE
    print("common.datasets self-check OK")


if __name__ == "__main__":
    _self_check()
