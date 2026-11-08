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
# Fixtures **versionadas** (no en `data_cache/`, que esta gitignored): permiten
# que un checkout limpio o sin red ejecute las 9 features. Ver `fixtures/README.md`.
FIXTURES = BENCHMARKS_ROOT / "fixtures"

OMNIDOCBENCH_REPO = "opendatalab/OmniDocBench"
# Revision **fijada** del dataset: sin `revision=`, cada maquina/fecha baja la
# revision vigente y dos runs miden sobre datos distintos sin que nadie lo note.
# Debe coincidir con la snapshot ya cacheada en `benchmarks/data_cache`.
OMNIDOCBENCH_REVISION = "aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec"
# Manifiesto de checksums **versionado** (fuera de `data_cache/`, que esta
# gitignored): pinnea el sha256 de los ficheros que definen el GT, para que dos
# maquinas con la misma revision verifiquen los MISMOS bytes. Ver `datasets_manifest.json`.
DATASETS_MANIFEST = BENCHMARKS_ROOT / "datasets_manifest.json"


class DatasetUnavailable(RuntimeError):
    """El dataset no se puede cargar en este entorno (falta una dependencia/cache)."""


class DatasetOffline(DatasetUnavailable):
    """No hay red y el cache no esta poblado: fallo **unico y accionable**.

    Distinto de `DatasetUnavailable` (que cubre fichero corrupto, categoria que
    falta, etc.): aqui el remedio es siempre el mismo — poblar el cache con
    `--fetch` — y el mensaje lo dice, en vez de dejar N muestras en `skipped`.
    """


def load_manifest(path: Path | None = None) -> dict:
    """Lee el manifiesto de checksums versionado (`datasets_manifest.json`)."""
    path = path or DATASETS_MANIFEST
    if not path.is_file():
        raise DatasetUnavailable(f"falta el manifiesto de checksums {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def verify_file(path: Path, expected_sha256: str, *, label: str = "") -> str:
    """Verifica el sha256 de `path`; devuelve el hash real. Falla claro si no cuadra.

    Es la comprobacion de integridad del criterio "mismo hash en dos maquinas":
    la revision fija de que revision se baja, el checksum garantiza que los bytes
    son los mismos.
    """
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    actual = digest.hexdigest()
    if actual != expected_sha256:
        raise DatasetUnavailable(
            f"checksum NO coincide para {label or path.name}: "
            f"esperado {expected_sha256[:12]}..., obtenido {actual[:12]}... "
            f"(el cache esta corrupto o es de otra revision; purga {path} y re-ejecuta --fetch)"
        )
    return actual

# Origen del ultimo dataset cargado: `dataset` (muestra real) o `fixture`
# (fallback minimo versionado). El runner lo propaga al `summary.json` para que
# el informe declare cuando los numeros vienen de la fixture y no de la muestra
# completa (regla de provenance del banco). El fallback es SILENCIOSO en consola
# a proposito: el silencio no se permite en el INFORME, no en el log.
PROVENANCE_DATASET = "dataset"
PROVENANCE_FIXTURE = "fixture"
_LAST_PROVENANCE: dict = {"source": PROVENANCE_DATASET, "detail": None, "revision": None}


def _set_provenance(source: str, detail: str | None = None,
                    revision: str | None = None) -> None:
    _LAST_PROVENANCE["source"] = source
    _LAST_PROVENANCE["detail"] = detail
    # Revision HF fijada (None si el origen es la fixture o un set sintetico).
    _LAST_PROVENANCE["revision"] = revision


def fixture_provenance() -> dict:
    """Origen del ultimo dataset cargado (`dataset` o `fixture`), para el informe."""
    return dict(_LAST_PROVENANCE)


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
    # **Estrato** de la página (`data_source × layout`) cuando el dataset anota
    # `page_attribute`: viaja con la muestra para que el informe pueda desglosar
    # la métrica *por estrato* sin volver a leer la anotación.
    stratum: str | None = None
    # GT de **orden de lectura / títulos** (`full_page`): bloques de contenido en
    # su `order` anotado, como `(caja, kind, texto)`. `kind` usa el vocabulario
    # que emite el pipeline (`ODB_CATEGORY_TO_KIND`); `texto` va vacío en tablas
    # y fórmulas (su contenido es HTML/LaTeX, ya presente en `gt_markdown`). De
    # aquí salen la secuencia de bloques (Kendall tau) y la detección de títulos.
    gt_ordered_blocks: tuple[tuple[tuple[float, float, float, float], str, str], ...] | None = None


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
    """Carga FUNSD desde Hugging Face, cacheado en `benchmarks/data_cache`.

    Sin red (o sin el cache), cae a la fixture versionada `fixtures/funsd_mini/`
    y lo declara en el provenance (`fixture_provenance()`).
    """
    try:
        from datasets import load_dataset
    except ImportError as exc:  # pragma: no cover - entorno sin `datasets`
        return _load_funsd_fixture(limit, f"datasets no instalado ({exc.__class__.__name__})")

    cache = DATA_CACHE
    cache.mkdir(parents=True, exist_ok=True)
    marker = cache / f"funsd_{split}.ok"

    try:
        ds = load_dataset("nielsr/funsd", split=split, cache_dir=str(cache))
    except Exception as exc:  # noqa: BLE001 - sin red / cache vacio: cae a la fixture
        return _load_funsd_fixture(limit, f"{exc.__class__.__name__}: {exc}")
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
    _set_provenance(PROVENANCE_DATASET, "nielsr/funsd (HF)")
    return samples


def _load_funsd_fixture(limit: int | None, reason: str) -> list[Sample]:
    """Carga FUNSD desde la fixture versionada (`fixtures/funsd_mini/`)."""
    manifest = FIXTURES / "funsd_mini" / "manifest.json"
    if not manifest.is_file():
        raise DatasetUnavailable(
            f"FUNSD no disponible ({reason}) y falta la fixture {manifest}")
    rows = json.loads(manifest.read_text(encoding="utf-8"))
    if limit is not None:
        rows = rows[:limit]
    samples: list[Sample] = []
    for row in rows:
        words, bboxes = [str(w) for w in row["words"]], row["bboxes"]
        ordered = sorted(
            zip(words, bboxes),
            key=lambda wb: ((wb[1][1] + wb[1][3]) / 2.0, (wb[1][0] + wb[1][2]) / 2.0),
        )
        samples.append(Sample(
            image_id=str(row["id"]),
            image=Image.open(manifest.parent / "images" / row["image"]).convert("RGB"),
            gt_text=" ".join(w for w, _ in ordered),
            gt_boxes=tuple(tuple(float(v) for v in box) for box in bboxes),
        ))
    _set_provenance(PROVENANCE_FIXTURE, f"funsd_mini ({reason})")
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


def _odb_page_attribute(page: dict) -> dict:
    """`page_info.page_attribute` de una página (atributos anotados del dataset)."""
    return (page.get("page_info") or {}).get("page_attribute") or {}


def _odb_stratum(page: dict, keys: Sequence[str] = ("data_source", "layout")) -> str:
    """Estrato de una página: valores de `keys` (p. ej. `data_source × layout`)."""
    attribute = _odb_page_attribute(page)
    return " × ".join(str(attribute.get(key) or "?") for key in keys)


def _odb_stratified(pages: list, limit: int | None = None,
                    keys: Sequence[str] = ("data_source", "layout")) -> list:
    """Orden determinista **estratificado** por `keys` (round-robin balanceado).

    Agrupa las páginas por estrato (`data_source × layout`) y las reparte por
    rondas: primero una de cada estrato, luego la segunda, etc. Así la muestra
    cubre todos los estratos posibles con el mismo peso y **ningún estrato
    domina** — con `n`=40 y 39 estratos el mayor pesa ~5%, muy lejos del sesgo
    de `_odb_rich_first`, que arranca con las páginas ricas en tabla/fórmula
    (20/20 `equation_hard` en la muestra de `layout`). El orden es
    **determinista** (estratos ordenados por clave, páginas en orden de
    anotación): dos ejecuciones dan la misma muestra.
    """
    groups: dict[str, list] = {}
    for page in pages:
        groups.setdefault(_odb_stratum(page, keys), []).append(page)
    picked: list = []
    round_index = 0
    while True:
        added = False
        for key in sorted(groups):
            stratum_pages = groups[key]
            if round_index < len(stratum_pages):
                picked.append(stratum_pages[round_index])
                added = True
                if limit is not None and len(picked) >= limit:
                    return picked
        if not added:
            return picked
        round_index += 1


def _odb_det_groups(pages: list, category: str, need: str, cap: int | None) -> list[tuple]:
    """Grupos `(name, page, dets)` por pagina con anotaciones de `category` y `need`.

    Solo las detecciones no `ignore` que traen el campo `need` (`latex` para
    formulas, `html` para tablas). Se recorren en el orden recibido (ya
    estratificado) y se cortan a `cap` grupos: cada pagina aporta como mucho una
    deteccion por ronda en `_spread_dets_per_page`, asi que `cap` paginas bastan
    para producir `limit` muestras.
    """
    groups: list[tuple] = []
    for page in pages:
        dets = [d for d in page["layout_dets"]
                if d["category_type"] == category and not d.get("ignore") and d.get(need)]
        if not dets:
            continue
        groups.append((str(page["page_info"]["image_path"]), page, dets))
        if cap is not None and len(groups) >= cap:
            break
    return groups


def _spread_dets_per_page(page_dets: list[tuple], limit: int | None) -> list[tuple]:
    """Intercala **una** deteccion por pagina y ronda (round-robin).

    Evita que la muestra se concentre en la primera pagina rica —el sesgo que
    `_odb_rich_first` producia en `formula` (14 de 20 recortes de una sola pagina
    `equation_hard`)— y le hace heredar la variedad de estratos del selector de
    paginas. Devuelve `(name, page, det)` en el orden de extraccion.
    """
    picked: list[tuple] = []
    round_index = 0
    while True:
        added = False
        for name, page, dets in page_dets:
            if round_index < len(dets):
                picked.append((name, page, dets[round_index]))
                added = True
                if limit is not None and len(picked) >= limit:
                    return picked
        if not added:
            return picked
        round_index += 1


def load_omnidocbench(limit: int | None = None, cache_dir: Path | None = None) -> list[Sample]:
    """Carga OmniDocBench (dataset documental con GT) desde Hugging Face.

    Descarga y cachea la anotacion y solo las imagenes de las paginas elegidas
    en `benchmarks/data_cache` (gitignored). La seleccion es **estratificada**
    por `page_attribute` (igual que `layout`: ver `_odb_stratified`), para que la
    muestra represente la composicion real del dataset en vez de sesgarse hacia
    las paginas ricas en tabla/formula.
    """
    pages = _odb_stratified(_load_omnidocbench_pages(cache_dir))
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


def _fixture_omnidocbench() -> Path:
    """Directorio de la fixture versionada de OmniDocBench."""
    return FIXTURES / "omnidocbench_mini"


def _load_omnidocbench_pages(cache_dir: Path | None) -> list:
    try:
        from huggingface_hub import hf_hub_download
    except ImportError as exc:  # pragma: no cover - entorno sin huggingface_hub
        return _load_omnidocbench_fixture(
            f"huggingface_hub no instalado ({exc.__class__.__name__})")
    cache = cache_dir or DATA_CACHE
    cache.mkdir(parents=True, exist_ok=True)
    try:
        ann = hf_hub_download(OMNIDOCBENCH_REPO, "OmniDocBench.json",
                              repo_type="dataset", revision=OMNIDOCBENCH_REVISION,
                              cache_dir=str(cache))
        pages = json.loads(Path(ann).read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - sin red / cache vacio: cae a la fixture
        return _load_omnidocbench_fixture(f"{exc.__class__.__name__}: {exc}")
    _verify_manifest_file(Path(ann), "OmniDocBench.json")
    _set_provenance(PROVENANCE_DATASET, _omnidocbench_source_detail(),
                    revision=OMNIDOCBENCH_REVISION)
    return pages


def _omnidocbench_source_detail() -> str:
    """Origen del dataset real **con la revision fijada** (provenance del informe)."""
    return f"{OMNIDOCBENCH_REPO}@{OMNIDOCBENCH_REVISION} (HF)"


def _verify_manifest_file(path: Path, repo_path: str) -> None:
    """Verifica el sha256 del fichero contra el manifiesto versionado.

    Si el manifiesto no lista el fichero (p. ej. una imagen que el banco descarga
    a demanda), no se verifica: la **revision** immutable ya garantiza sus bytes.
    """
    entry = (load_manifest().get("files") or {}).get(repo_path)
    if entry and entry.get("sha256"):
        verify_file(path, entry["sha256"], label=repo_path)


def _load_omnidocbench_fixture(reason: str) -> list:
    """Carga la anotacion de la fixture versionada y declara el origen."""
    ann = _fixture_omnidocbench() / "OmniDocBench.json"
    if not ann.is_file():
        raise DatasetUnavailable(
            f"dataset real no disponible ({reason}) y falta la fixture {ann}")
    _set_provenance(PROVENANCE_FIXTURE, f"omnidocbench_mini ({reason})")
    return json.loads(ann.read_text(encoding="utf-8"))


def _odb_image(name: str, cache: Path) -> Image.Image:
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:  # pragma: no cover - ya se aviso en las paginas
        return _odb_fixture_image(name)
    try:
        path = hf_hub_download(OMNIDOCBENCH_REPO, f"images/{name}",
                               repo_type="dataset", revision=OMNIDOCBENCH_REVISION,
                               cache_dir=str(cache))
        return Image.open(path).convert("RGB")
    except Exception:  # noqa: BLE001 - sin red: la fixture cubre las paginas que sirve
        return _odb_fixture_image(name)


def _odb_fixture_image(name: str) -> Image.Image:
    """Imagen de la fixture versionada (mismo `images/<name>` que la release)."""
    path = _fixture_omnidocbench() / "images" / name
    if not path.is_file():
        raise DatasetUnavailable(
            f"imagen {name} no esta ni en la cache HF ni en la fixture {path}")
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
    """Una muestra por formula: recorte de la imagen + su LaTeX anotado como GT.

    Las paginas se recorren en orden **estratificado** (`_odb_stratified`) y los
    recortes se **reparten entre paginas** (`_spread_dets_per_page`): sin el
    reparto la muestra se concentraba en la primera pagina rica y salia 20/20
    `equation_hard`, aunque el orden de paginas ya fuera estratificado.
    """
    pages = _odb_stratified(_load_omnidocbench_pages(cache_dir))
    cache = cache_dir or DATA_CACHE
    groups = _odb_det_groups(pages, "equation_isolated", "latex",
                             None if limit is None else limit)

    images: dict[str, Image.Image] = {}
    samples: list[Sample] = []
    for name, page, det in _spread_dets_per_page(groups, limit):
        if name not in images:
            images[name] = _odb_image(name, cache)
        # GT sin delimitadores `$`: el motor de formulas emite LaTeX "desnudo".
        gt = " ".join(str(det["latex"]).replace("$", "").split())
        samples.append(Sample(
            image_id=f"{Path(name).stem}::{det.get('anno_id', 'eq')}",
            image=_crop_poly(images[name], det["poly"]),
            gt_text=gt,
            stratum=_odb_stratum(page),
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

# Vocabulario del **pipeline completo** (`pp_structurev3`, oar-ocr
# `LayoutElementType::as_str`) -> categorias anotadas de OmniDocBench. Es el
# mapa que necesita `full_page` para puntuar el layout de las cajas que emite el
# propio pipeline: su vocabulario no es el de `pp_doclayoutv3` (dice `formula`,
# no `display_formula`; anade `list`, `abstract`, `region`...), asi que reusar
# `LAYOUT_MODEL_TO_GT` dejaria `formula` sin puntuar. Solo se evaluan las
# categorias destino de este mapa; el resto de etiquetas del pipeline se ignoran.
STRUCTURE_KIND_TO_GT = {
    "text": "text_block",
    "doc_title": "title",
    "paragraph_title": "title",
    "formula": "equation_isolated",
    "table": "table",
    "image": "figure",
    "figure_title": "figure_caption",
    "table_title": "figure_caption",
    "chart_title": "figure_caption",
    "figure_table_chart_title": "figure_caption",
    "header": "header",
    "footer": "footer",
    "number": "page_number",
    "footnote": "page_footnote",
    "reference": "reference",
    "reference_content": "reference",
    "list": "list_group",
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


def _odb_ordered_blocks(page: dict) -> tuple[tuple[tuple[float, float, float, float], str, str], ...]:
    """Bloques de contenido en su `order` anotado: `(caja, kind, texto)`.

    Es el GT de **orden de lectura** y de **títulos** de `full_page`. El `kind`
    (vocabulario del pipeline) permite aislar los títulos (`paragraph_title`); el
    texto solo se rellena para bloques de prosa (tablas/fórmulas lo llevan en
    `gt_markdown`). Un bloque anotado cuya categoría no tiene equivalencia en el
    vocabulario del pipeline se **omite** (no se inventa un `kind`).
    """
    out: list[tuple[tuple[float, float, float, float], str, str]] = []
    for det in _odb_content_blocks(page):
        kind = ODB_CATEGORY_TO_KIND.get(det["category_type"])
        if kind is None or not det.get("poly"):
            continue
        out.append((_odb_poly_bbox(det["poly"]), kind, str(det.get("text") or "")))
    return tuple(out)


def _odb_page_tables(page: dict) -> str:
    """HTML anotado de **todas** las tablas de la pagina, en orden de lectura.

    `full_page` recibe el pipeline completo, que emite el HTML de cada tabla
    dentro de su Markdown; para puntuar *estructura de tabla* a nivel de pagina
    se concatenan los `html` anotados y se comparan contra los que aparecen en la
    salida. Vacio (`""`) si la pagina no anota ninguna tabla -> la metrica no se
    evalua, nunca un `0.0`.
    """
    blocks = [d for d in _odb_content_blocks(page) if d["category_type"] == "table" and d.get("html")]
    return "\n".join(str(d["html"]) for d in blocks)


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
    """Paginas con GT de **layout** (cajas anotadas por clase de bloque).

    Muestreo **estratificado** por `page_attribute` (`data_source × layout`,
    round-robin balanceado -> ver `_odb_stratified`): cubre la heterogeneidad
    real de los documentos en vez de sesgar la muestra hacia páginas ricas en
    tabla/fórmula. El estrato viaja en `Sample.stratum` para el informe
    "por estrato".
    """
    cache = cache_dir or DATA_CACHE
    pages = _odb_stratified(_load_omnidocbench_pages(cache_dir))
    samples: list[Sample] = []
    for page in pages:
        layout = _odb_page_layout(page)
        if not layout:
            continue
        name = str(page["page_info"]["image_path"])
        samples.append(Sample(image_id=name, image=_odb_image(name, cache),
                              gt_text="", gt_layout=layout,
                              stratum=_odb_stratum(page)))
        if limit is not None and len(samples) >= limit:
            break
    return samples


def load_omnidocbench_tables(limit: int | None = None, cache_dir: Path | None = None) -> list[Sample]:
    """Una muestra por tabla anotada: recorte del `poly` + su `html` como GT.

    Orden **estratificado** de paginas (`_odb_stratified`) y recortes **repartidos
    entre paginas** (`_spread_dets_per_page`), igual que `formula`: sin el reparto
    las tablas se agolpaban en las primeras paginas ricas.
    """
    cache = cache_dir or DATA_CACHE
    pages = _odb_stratified(_load_omnidocbench_pages(cache_dir))
    groups = _odb_det_groups(pages, "table", "html", None if limit is None else limit)

    images: dict[str, Image.Image] = {}
    samples: list[Sample] = []
    for name, page, det in _spread_dets_per_page(groups, limit):
        if name not in images:
            images[name] = _odb_image(name, cache)
        samples.append(Sample(
            image_id=f"{Path(name).stem}::{det.get('anno_id', 'tbl')}",
            image=_crop_poly(images[name], det["poly"]),
            gt_text="", gt_html=str(det["html"]),
            stratum=_odb_stratum(page),
        ))
    return samples


def load_omnidocbench_full_page(limit: int | None = None, cache_dir: Path | None = None) -> list[Sample]:
    """Paginas con GT de **documento** completo (Markdown + bloques en orden).

    Orden **estratificado** (`_odb_stratified`), igual que `layout`: la muestra
    cubre la composicion del dataset en vez de sesgarse a `equation_hard`.
    """
    cache = cache_dir or DATA_CACHE
    pages = _odb_stratified(_load_omnidocbench_pages(cache_dir))
    samples: list[Sample] = []
    for page in pages:
        markdown = _odb_page_markdown(page)
        if not markdown:
            continue
        name = str(page["page_info"]["image_path"])
        # Ademas del documento (markdown/bloques), la **misma** pagina lleva su
        # GT desgranado para que `full_page` puntue layout (mAP de las cajas),
        # estructura de tabla (TEDS del HTML) y formula (similitud LaTeX) en la
        # misma pasada: son las mismas anotaciones que usan los bancos de
        # `layout`/`table`/`formula`, no un GT nuevo.
        tables_html = _odb_page_tables(page)
        formulas = _odb_page_formulas(page)
        samples.append(Sample(
            image_id=name, image=_odb_image(name, cache),
            gt_text=_odb_page_text(page), gt_markdown=markdown,
            gt_blocks=_odb_page_blocks(page),
            gt_layout=_odb_page_layout(page),
            gt_html=tables_html or None,
            gt_by_task={"formula": formulas} if formulas else None,
            stratum=_odb_stratum(page),
            gt_ordered_blocks=_odb_ordered_blocks(page),
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
# conocida y el GT es esa operacion. La pagina base es la de OmniDocBench **si
# esta en `benchmarks/data_cache`** (comportamiento historico) y, si no
# (checkout limpio o sin red), una pagina sintetica determinista dibujada con PIL
# (mismo enfoque que `_draw_seal_stamp`), de modo que estas features **no dependen
# de la red**.

ORIENTATION_ANGLES = (0, 90, 180, 270)
TEXT_LINE_ANGLES = (0, 180)
# Esquinas del destino deformado (fracciones del ancho/alto) de la homografia.
PERSPECTIVE_OFFSETS = ((0.06, 0.03), (0.96, 0.08), (0.93, 0.96), (0.08, 0.94))


def _cached_page_images(cache_dir: Path | None = None) -> list[Path]:
    """Paginas de OmniDocBench presentes en la cache local o en la fixture (sin red)."""
    root = (cache_dir or DATA_CACHE) / "datasets--opendatalab--OmniDocBench"
    paths = sorted(root.glob("snapshots/*/images/*.png"))
    if paths:
        return paths
    # Sin cache: la fixture versionada (mismo esquema `images/<name>`).
    fixture = FIXTURES / "omnidocbench_mini" / "images"
    paths = sorted(p for p in fixture.glob("*") if p.suffix.lower() in {".png", ".jpg", ".jpeg"})
    if paths:
        _set_provenance(PROVENANCE_FIXTURE, "omnidocbench_mini (paginas de la fixture)")
    return paths


def _cached_page_annotation(cache_dir: Path | None = None) -> list:
    """Anotacion de OmniDocBench de la cache local o de la fixture (sin red)."""
    root = (cache_dir or DATA_CACHE) / "datasets--opendatalab--OmniDocBench"
    files = sorted(root.glob("snapshots/*/OmniDocBench.json"))
    if not files:
        files = sorted((FIXTURES / "omnidocbench_mini").glob("OmniDocBench.json"))
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


# Fallback offline: sin cache de OmniDocBench, las features sinteticas generan su
# propia pagina fuente con PIL (determinista), en vez de depender de la red.
SYNTHETIC_PAGE_COUNT = 40
SYNTHETIC_PAGE_SIZE = (1000, 1400)


def _synthetic_page(index: int) -> Image.Image:
    """Pagina sintetica determinista (texto dibujado con PIL, misma idea que el sello)."""
    from PIL import ImageDraw

    width, height = SYNTHETIC_PAGE_SIZE
    page = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(page)
    draw.text((70, 70), f"Documento sintetico {index + 1}", fill=(0, 0, 0),
              font=_seal_font(34))
    font = _seal_font(22)
    y = 150
    for line in range(index % 7 + 6):
        text = f"Linea {line + 1} de relleno determinista numero {(index + 1) * (line + 3)}"
        draw.text((70, y), text, fill=(0, 0, 0), font=font)
        y += 42
    return page


def _page_sources(cache_dir: Path | None, count: int | None) -> list[tuple[str, Image.Image]]:
    """Fuentes `(name, image)` del GT sintetico: paginas cacheadas o sinteticas.

    Con la cache de OmniDocBench presente usa esas paginas (comportamiento previo);
    sin ella genera paginas sinteticas deterministas, asi que ninguna de las tres
    features necesita red.
    """
    paths = _cached_page_images(cache_dir)
    if paths:
        paths = paths if count is None else paths[:count]
        return [(path.stem, Image.open(path).convert("RGB")) for path in paths]
    total = SYNTHETIC_PAGE_COUNT if count is None else count
    return [(f"synthetic_{i:03d}", _synthetic_page(i)) for i in range(total)]


def _synthetic_text_lines(count: int) -> list[tuple[str, Image.Image]]:
    """Lineas de texto recortadas de paginas sinteticas (fallback de `_cached_text_lines`)."""
    lines: list[tuple[str, Image.Image]] = []
    for i in range(count):
        page = _synthetic_page(i)
        y = 150 + (i % 5) * 42
        lines.append((f"synthetic_{i:03d}::line", page.crop((60, y - 4, 760, y + 34))))
    return lines


def load_synthetic_orientation(limit: int | None = None, cache_dir: Path | None = None) -> list[Sample]:
    """Paginas rotadas 0/90/180/270; GT = la etiqueta de **correccion** esperada.

    El clasificador de `pyocrust` (`document_orientation`, PP-LCNet) devuelve la
    rotacion que hay que **aplicar** para enderezar la pagina, no la que se le
    aplico: sobre una pagina rotada `a` grados emite `(360 - a) mod 360`
    (comprobado con las cuatro clases en una pagina real antes de escribir el
    banco). El GT sintetico es exactamente esa etiqueta.
    """
    sources = _page_sources(cache_dir, limit)
    samples: list[Sample] = []
    for i, (name, image) in enumerate(sources):
        angle = ORIENTATION_ANGLES[i % len(ORIENTATION_ANGLES)]
        samples.append(Sample(
            image_id=f"{name}::rot{angle}",
            image=image.rotate(angle, expand=True) if angle else image,
            gt_text="", gt_label=str((360 - angle) % 360),
        ))
    return samples


def _text_line_sources(cache_dir: Path | None, count: int | None) -> list[tuple[str, Image.Image]]:
    """Lineas de texto de la cache si las hay; si no, recortes de paginas sinteticas."""
    lines = _cached_text_lines(cache_dir)
    if lines:
        return lines
    # Sin cache (o cache sin bloques de texto): lineas de paginas sinteticas.
    # ponytail: recorta una linea por pagina sintetica; subir si hacen falta mas.
    return _synthetic_text_lines(SYNTHETIC_PAGE_COUNT if count is None else count)


def load_synthetic_text_line(limit: int | None = None, cache_dir: Path | None = None) -> list[Sample]:
    """Lineas de texto giradas 0/180; GT = la etiqueta de orientacion aplicada."""
    lines = _text_line_sources(cache_dir, limit)
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
    sources = _page_sources(cache_dir, limit)
    samples: list[Sample] = []
    for name, image in sources:
        clean = _resize_max(image, 1000)
        samples.append(Sample(image_id=f"{name}::persp",
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
# Paso explicito de preparacion (`--fetch`): poblar el cache UNA vez, con un
# unico error claro si no hay red y el cache no esta.
# ---------------------------------------------------------------------------
# Sin esto, sin red las N muestras caen una a una al fallback de fixture y el
# log queda lleno de `skipped` silenciosos. Aqui se comprueba **de golpe**: si la
# anotacion no esta en cache y no se puede descargar, se lanza UN `DatasetOffline`
# con la instruccion exacta para poblarlo.

FETCH_HELP = (
    "pobla benchmarks/data_cache una vez (~545 MB, solo la anotacion + imagenes "
    "usadas). Requiere red la primera vez."
)

# Fichero que SIEMPRE se usa y define el GT: si su descarga falla, no hay dataset.
_FETCH_ANNOTATION = "OmniDocBench.json"


def prepare_datasets(cache_dir: Path | None = None) -> dict:
    """Descarga + verifica la anotacion de OmniDocBench. Falla rapido y claro.

    Devuelve `{"annotation": <ruta>, "sha256": ..., "revision": ...}`. Si no hay
    red y el cache no esta poblado, lanza **un solo** `DatasetOffline` con la
    instruccion de como poblarlo (nada de N `skipped`).
    """
    try:
        from huggingface_hub import hf_hub_download
    except ImportError as exc:
        raise DatasetUnavailable(
            "pip install huggingface_hub para descargar OmniDocBench "
            "(o usa la fixture versionada: benchmarks/fixtures/)"
        ) from exc

    cache = cache_dir or DATA_CACHE
    cache.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    revision = manifest.get("revision") or OMNIDOCBENCH_REVISION
    try:
        ann = hf_hub_download(OMNIDOCBENCH_REPO, _FETCH_ANNOTATION,
                              repo_type="dataset", revision=revision,
                              cache_dir=str(cache))
    except Exception as exc:  # noqa: BLE001 - se traduce a UN error accionable
        raise DatasetOffline(
            f"no se pudo preparar el dataset {OMNIDOCBENCH_REPO}@{revision[:12]} "
            f"({exc.__class__.__name__}: {exc}).\n"
            f"  -> Sin red y con el cache vacio no hay dataset real. Opciones:\n"
            f"     1) con red:   python benchmarks/prepare_datasets.py --fetch\n"
            f"     2) sin red:   usa la fixture versionada (benchmarks/fixtures/), "
            f"el banco la sirve sola con HF_HUB_OFFLINE=1\n"
            f"  (cache esperada en: {cache})"
        ) from exc

    entry = (manifest.get("files") or {}).get(_FETCH_ANNOTATION, {})
    if entry.get("sha256"):
        verify_file(Path(ann), entry["sha256"], label=_FETCH_ANNOTATION)

    import hashlib

    digest = hashlib.sha256(Path(ann).read_bytes()).hexdigest()
    return {"annotation": str(ann), "sha256": digest, "revision": revision}


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
    # Orden de lectura / titulos: bloques de contenido en su `order`, con `kind`
    # del pipeline y texto (vacio en tabla/formula); el `header` ignorado y la
    # mascara quedan fuera.
    assert _odb_ordered_blocks(annotated) == (
        ((0.0, 0.0, 10.0, 5.0), "text", "hola"),
        ((0.0, 5.0, 10.0, 9.0), "table", ""),
        ((0.0, 9.0, 10.0, 12.0), "formula", ""),
    )
    titled = {
        "layout_dets": [
            {"category_type": "title", "ignore": False, "order": 1,
             "poly": [0, 0, 10, 0, 10, 3, 0, 3], "text": "Introduccion"},
            {"category_type": "text_block", "ignore": False, "order": 2,
             "poly": [0, 3, 10, 3, 10, 8, 0, 8], "text": "cuerpo"},
        ],
        "page_info": {"image_path": "t.png"},
    }
    assert _odb_ordered_blocks(titled) == (
        ((0.0, 0.0, 10.0, 3.0), "paragraph_title", "Introduccion"),
        ((0.0, 3.0, 10.0, 8.0), "text", "cuerpo"),
    )
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
    # Selector estratificado: cubre ≥6 estratos (`data_source × layout`), ninguno
    # domina (>40%) y el orden es determinista (misma muestra en dos llamadas).
    def _attr_page(data_source, layout, eq=False, path="p"):
        return {"layout_dets": [], "page_info": {
            "image_path": path,
            "page_attribute": {"data_source": data_source, "layout": layout,
                               "subset": "equation_hard" if eq else "v1.5"},
        }}

    strat_pages = (
        [_attr_page("book", "single_column")] * 5
        + [_attr_page("book", "double_column")] * 4
        + [_attr_page("newspaper", "other_layout")] * 3
        + [_attr_page("exam_paper", "single_column")] * 2
        + [_attr_page("note", "single_column")] * 2
        + [_attr_page("magazine", "three_column")] * 1
        + [_attr_page("PPT2PDF", "1andmore_column")] * 1
    )
    picked = _odb_stratified(strat_pages, limit=12)
    assert len(picked) == 12
    strata_counts: dict[str, int] = {}
    for page in picked:
        key = _odb_stratum(page)
        strata_counts[key] = strata_counts.get(key, 0) + 1
    assert len(strata_counts) == 7, strata_counts          # ≥6 estratos cubiertos
    assert max(strata_counts.values()) <= 12 * 0.4, strata_counts  # ninguno >40%
    assert _odb_stratified(strat_pages, limit=12) == picked        # determinista
    assert _odb_stratum(_attr_page("book", "single_column")) == "book × single_column"
    print("common.datasets self-check OK")


if __name__ == "__main__":
    _self_check()
