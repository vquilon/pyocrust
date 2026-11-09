#!/usr/bin/env python
"""Banco de la feature **full_page** (documento completo → Markdown y bloques).

Pipeline completo de página: layout + OCR + tablas + fórmulas en una sola salida
Markdown. Mide **`markdown_f1`** (LCS de tokens sobre el Markdown, sensible al
orden y conservando el LaTeX) y **`block_f1`** (multiconjunto de tipos de bloque),
además del CER/WER de texto que ya calcula el runner.

Dataset por defecto: `omnidocbench_full_page` — el Markdown de referencia se
**reconstruye** de la anotación de OmniDocBench: sus bloques (`text`/`latex`/
`html`) concatenados en su `order` de lectura, y sus tipos de bloque traducidos al
vocabulario que emite el pipeline (`kind`). No se inventa contenido: solo se
serializa lo que el dataset ya anota.

Provenance: todo número que salga de aquí es **`medido`**; el `summary.json` de la
run guarda comando, dataset, `n`, `warmup`, `repeats`, dispositivo y fecha.

Uso:
    .venv/Scripts/python.exe benchmarks/features/full_page/bank.py --limit 6
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

# Ejecutable como script (`python benchmarks/features/full_page/bank.py`).
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from datetime import datetime

from common import OcrOutput, Sample, load_dataset, run_backends
from common.datasets import STRUCTURE_KIND_TO_GT
from common.metrics import (
    detection_map,
    kendall_tau,
    latex_similarity,
    latex_token_f1,
    match_boxes,
    table_teds,
    word_f1,
)
from features._base import FeatureSpec, common_argparser, feature_out_dir, unavailable_factory

SPEC = FeatureSpec(
    feature="full_page",
    summary="Pipeline completo de página → Markdown/bloques (texto + tablas + fórmulas juntos).",
    pyocrust_task="pp_structurev3 (VeloceOCR) e Indra (pipeline completo de página)",
    metric=("contenido: markdown_f1 / block_f1 + CER/WER · estructura/posición: "
            "layout mAP@IoU 0.5 + TEDS de tabla + similitud LaTeX de fórmula + "
            "figuras (detección) y asociación figura↔caption"),
    dataset="omnidocbench_full_page: Markdown GT reconstruido de los bloques anotados en orden de lectura",
    alternatives={
        "docling": ("docling", "docling"),
        "unstructured": ("unstructured", "unstructured"),
        "paddleocr PP-StructureV3": ("paddleocr", "paddleocr paddlepaddle"),
        "marker-pdf": ("marker", "marker-pdf"),
    },
    status="implemented",
    note="El GT de documento se serializa de la anotación (texto + LaTeX + HTML de tabla en orden de lectura); no se inventa contenido.",
    provenance="valores MEDIDOS por este banco (markdown_f1/block_f1 contra la GT reconstruida de OmniDocBench)",
)

# --- alternativas de pipeline documental -------------------------------------
# Pipelines **externos reales** que emiten el Markdown del documento que consume
# `markdown_f1`/`block_f1`:
#   * `docling`            — docling (MIT), en su venv aislado por subproceso.
# `pp_structurev3_api` (PaddleOCR PP-StructureV3, Apache-2.0) queda FUERA del
# default: el pipeline en proceso **cuelga o segfaultea** (exit 139) en páginas
# reales de la muestra (medido 2026-11-09: muere procesando una imagen grande,
# 11112x7925, tras cargar sus 16 submodelos), así que no puede producir filas de
# forma fiable en CPU. Sigue registrado en `PROVIDERS` (pedido explícito -> la
# fila sale `error`/`skipped` con motivo, nunca cuelga el banco).
# `pdf_extract_kit` sigue `skipped` con motivo honesto: sus pesos son un
# **detector de layout**, no un pipeline de documento (ver ALTERNATIVES.md §7).
EXTRA_FACTORIES = {
    "pdf_extract_kit": unavailable_factory(
        "pdf_extract_kit",
        "pdf-extract-kit (opendatalab/PDF-Extract-Kit-1.0; pesos en cache HF, adaptador pendiente)",
        note="pdf_extract_kit solo publica un detector de layout, no un pipeline de documento",
    ),
    "pp_structurev3_api": unavailable_factory(
        "pp_structurev3_api",
        "PaddleOCR PP-StructureV3 (cuelga/segfaultea en CPU sobre páginas reales; adaptador en proceso)",
        note="el pipeline en proceso aborta el banco en páginas grandes; falta envolverlo en subproceso con timeout",
    ),
}
EXTRA_MODELS = {name: (name, "default") for name in EXTRA_FACTORIES}

# `pyocrust_indra` se salta solo si sus 9 artefactos no están en disco (motivo en el informe).
DEFAULT_BACKENDS = "pyocrust_structure,pyocrust_indra,docling,pdf_extract_kit"


def _emits(output: OcrOutput, channel: str) -> bool:
    """¿El adaptador declara emitir `channel`? (`None` = sin declaración -> sí).

    Los canales los declara el motor en `output.extra["emits"]` (ver
    `common.runner.STRUCTURE_CHANNELS`). Un `OcrOutput` sin esa señal —adaptadores
    de test o runs previas— se trata como motor completo, para no cambiar el
    significado de lo ya medido.
    """
    declares = output.extra.get("emits")
    return declares is None or channel in declares


def score_full_page(sample: Sample, output: OcrOutput) -> dict:
    """Métricas **desgranadas** del pipeline completo, en la misma pasada.

    Separa **contenido** de **estructura/posición** para que una tabla mal
    estructurada con texto correcto no tape el fallo en `markdown_f1`:

    * `layout_map`/`layout_recall` — mAP@IoU 0.5 de las cajas que emite el
      pipeline contra el `poly` anotado (misma métrica que el banco `layout`,
      con el vocabulario de `pp_structurev3`, ``STRUCTURE_KIND_TO_GT``).
    * `table_teds` — TEDS de estructura del HTML de tabla que aparece en el
      Markdown del pipeline contra el `html` anotado (misma métrica que `table`).
    * `latex_sim`/`latex_token_f1` — similitud del LaTeX de las fórmulas frente a
      su `latex` anotado (misma métrica que `formula`).

    Regla del banco: sin GT de la modalidad, la métrica queda **no evaluada**
    (`""`), nunca un `0.0`. Y si el **motor no emite** la estructura que mide la
    columna (lo declara el adaptador en `output.extra["emits"]`, ver
    `STRUCTURE_CHANNELS`) también queda `""`: no se penaliza lo ausente ni se
    publica `0.0` donde en realidad no se midió nada.
    """
    # --- layout: mAP de las cajas del pipeline contra los `poly` anotados ----
    if _emits(output, "layout"):
        predicted: dict[str, list[tuple[float, tuple[float, float, float, float]]]] = {}
        for element in output.extra.get("elements") or []:
            category = STRUCTURE_KIND_TO_GT.get(str(element.get("element_type")))
            box = _element_bbox(element)
            if category is None or box is None:
                continue
            predicted.setdefault(category, []).append((float(element.get("score", 0.0) or 0.0), box))
        gt = {cls: boxes for cls, boxes in (sample.gt_layout or {}).items() if cls in STRUCTURE_KIND_TO_GT.values()}
        mean_ap, recall = detection_map(gt, predicted)
    else:
        mean_ap = recall = None

    # --- tabla: TEDS de estructura del HTML emitido contra el anotado --------
    if sample.gt_html and _emits(output, "tables"):
        teds = round(table_teds(sample.gt_html, _markdown_tables(output.text)), 4)
    else:
        teds = ""

    # --- fórmula: similitud LaTeX contra el `latex` anotado ------------------
    gt_latex = (sample.gt_by_task or {}).get("formula")
    pred_latex = "\n".join(str(f) for f in (output.extra.get("formulas") or [])) or \
        "\n".join(str(e.get("text") or "") for e in (output.extra.get("elements") or [])
                  if STRUCTURE_KIND_TO_GT.get(str(e.get("element_type"))) == "equation_isolated")
    if gt_latex and pred_latex.strip() and _emits(output, "formulas"):
        latex_sim = round(latex_similarity(gt_latex, pred_latex), 4)
        latex_f1 = round(latex_token_f1(gt_latex, pred_latex), 4)
    else:
        latex_sim = latex_f1 = ""

    # --- títulos / índice y orden de lectura ---------------------------------
    # El pipeline emite `elements` **en orden de lectura** (el orden de la lista ES
    # el orden); el GT anota cada bloque con su `order`. Se miden por separado:
    #   * títulos: detección (recall/precision@IoU 0.5) + F1 del **texto**;
    #   * secuencia de títulos: tau de Kendall entre el orden emitido y el anotado;
    #   * orden de lectura: tau sobre TODOS los bloques emparejados.
    # `markdown_f1` (LCS de tokens) NO captura el orden: dos bloques idénticos
    # intercambiados dan el mismo LCS, pero aquí la tau baja. La **jerarquía**
    # (h1/h2/h3) NO se mide: `attribute` está siempre vacío en OmniDocBench.
    title_metrics = _title_and_order_metrics(sample, output)

    # --- figuras: detección + asociación figura↔caption ----------------------
    figure_metrics = _figure_metrics(sample, output)

    return {
        "layout_map": "" if mean_ap is None else round(mean_ap, 4),
        "layout_recall": "" if recall is None else round(recall, 4),
        "table_teds": teds,
        "latex_sim": latex_sim,
        "latex_token_f1": latex_f1,
        **title_metrics,
        **figure_metrics,
    }


# Kinds del pipeline que la anotación marca como `title` (para aislar títulos).
_TITLE_GT_CATEGORY = "title"


def _pred_title(element: dict) -> bool:
    """¿El elemento emitido es un título (`doc_title`/`paragraph_title`)?"""
    return STRUCTURE_KIND_TO_GT.get(str(element.get("element_type"))) == _TITLE_GT_CATEGORY


def _title_and_order_metrics(sample: Sample, output: OcrOutput) -> dict:
    """Títulos (detección + texto + secuencia) y orden de lectura como secuencia.

    El GT (`Sample.gt_ordered_blocks`) son los bloques de contenido en su `order`
    anotado, `(caja, kind, texto)`. Los títulos son los de `kind ==
    paragraph_title` (el vocabulario que emite el pipeline para `title`).

    `title_recall`/`title_precision`: emparejamiento 1-a-1 por IoU@0.5 (mismo
    criterio que layout); `title_text_f1`: F1 de palabra del texto de los títulos
    emparejados; `title_seq_tau`/`read_order_tau`: tau de Kendall entre el orden
    emitido y el `order` anotado. Sin GT de títulos, las métricas de títulos
    quedan **no evaluadas** (`""`), nunca `0.0`; con <2 bloques emparejados, la
    tau no se evalúa (no hay secuencia que comparar).
    """
    gt_blocks = sample.gt_ordered_blocks or ()
    elements = list(output.extra.get("elements") or [])

    metrics: dict = {
        "title_recall": "", "title_precision": "", "title_text_f1": "",
        "title_seq_tau": "", "read_order_tau": "",
    }

    # Orden de lectura: empareja TODOS los bloques por caja (no por vocabulario),
    # así que basta con que el motor emita cajas (`boxes`).
    if _emits(output, "boxes"):
        read_tau = _sequence_tau(gt_blocks, elements)
        if read_tau is not None:
            metrics["read_order_tau"] = round(read_tau, 4)

    # Títulos: solo si la página los anota (`attribute` no los jerarquiza, pero
    # `category_type == "title"` sí los localiza) y el motor emite layout del
    # vocabulario del banco (`layout`); si no, quedan no evaluadas.
    gt_titles = [(i, box, text) for i, (box, kind, text) in enumerate(gt_blocks)
                 if kind == "paragraph_title"]
    if not gt_titles or not _emits(output, "layout"):
        return metrics
    pred_titles = [(i, _element_bbox(e), str(e.get("text") or ""))
                   for i, e in enumerate(elements) if _pred_title(e)]
    pred_titles = [(i, b, t) for i, b, t in pred_titles if b is not None]

    pairs = match_boxes([b for _i, b, _t in gt_titles], [b for _i, b, _t in pred_titles])
    metrics["title_recall"] = round(len(pairs) / len(gt_titles), 4)
    metrics["title_precision"] = round(len(pairs) / len(pred_titles), 4) if pred_titles else 0.0

    # F1 del texto de los títulos emparejados (media; "" si ninguno trae texto).
    texts = [gt_titles[gi][2] for gi, pi in pairs if gt_titles[gi][2] and pred_titles[pi][2]]
    if texts:
        metrics["title_text_f1"] = round(
            sum(word_f1(gt_titles[gi][2], pred_titles[pi][2]) for gi, pi in pairs
                if gt_titles[gi][2] and pred_titles[pi][2]) / len(texts), 4)

    # Secuencia de títulos: orden emitido (índice del elemento) vs `order` anotado
    # (índice del bloque GT). Con <2 títulos emparejados no hay secuencia.
    if len(pairs) >= 2:
        metrics["title_seq_tau"] = round(kendall_tau(
            [pred_titles[pi][0] for _gi, pi in pairs],
            [gt_titles[gi][0] for gi, _pi in pairs],
        ), 4)
    return metrics


# --- figuras e imágenes: detección y asociación figura↔caption ----------------
# Los bloques GT de `gt_ordered_blocks` usan el **vocabulario del pipeline**
# (`ODB_CATEGORY_TO_KIND`): una figura anotada llega como kind `image` y su
# caption como `figure_title` (OmniDocBench mapea `figure_caption` ahí; otros
# corpora usan `table_title`/`chart_title`/`figure_table_chart_title`). Al puntuar
# los **elementos emitidos** se usa `STRUCTURE_KIND_TO_GT` (element_type -> GT).
_GT_FIGURE_KIND = "image"
_GT_CAPTION_KINDS = frozenset({
    "figure_title", "table_title", "chart_title", "figure_table_chart_title",
    "figure_caption",
})


def _figure_metrics(sample: Sample, output: OcrOutput) -> dict:
    """Figuras (`figure`) y sus captions como métricas **propias** de `full_page`.

    Separa tres cosas que `markdown_f1`/`block_f1` mezclan o ignoran:

    * `figure_recall`/`figure_precision` — **detección** de las cajas `figure`
      por IoU@0.5, mismo criterio 1-a-1 que `layout`. Una figura anotada que el
      pipeline no localiza baja el recall.
    * `figure_caption_recall`/`figure_caption_precision` — **detección** de las
      cajas de caption anotadas (`figure_caption`) contra los elementos que el
      pipeline emite como título de figura/tabla.
    * `figure_caption_pair_f1` — **asociación figura↔caption**: fracción de
      figuras GT emparejadas cuya **caption anotada compañera** (la más próxima
      en el orden de lectura anotado) también fue localizada y emparejada a un
      elemento emitido. Es la métrica clave del criterio: una página con las
      figuras detectadas pero **sin** sus captions puntúa bajo aquí aunque su
      `figure_recall` sea 1.0, así que no puede igualar a una completa.
    * `figure_caption_text_f1` — F1 de palabra del **texto** de la caption, sobre
      las captions emparejadas (media; `""` si ninguna trae texto).

    Regla del banco: sin GT de figuras en la página, todo queda **no evaluado**
    (`""`), nunca `0.0`; lo mismo con la precisión cuando el motor no emite
    ninguna caja de esa clase (no hay denominador, no se inventa un cero). Las
    **máscaras** (`*_mask`, `chart_mask`, `table_mask`, …) **no** entran: no son
    emitibles por el pipeline y ya quedan fuera de `gt_ordered_blocks` (ver
    `_odb_content_blocks`); nunca se puntúan como fallo.
    """
    metrics: dict = {
        "figure_recall": "", "figure_precision": "",
        "figure_caption_recall": "", "figure_caption_precision": "",
        "figure_caption_pair_f1": "", "figure_caption_text_f1": "",
    }
    # Sin layout del vocabulario del banco no hay detección que comparar (docling,
    # indra): todo no evaluado, nunca un `0.0` por figuras que el motor no emite.
    if not _emits(output, "layout"):
        return metrics
    gt_blocks = sample.gt_ordered_blocks or ()
    elements = list(output.extra.get("elements") or [])

    # GT: figuras y captions anotados con su caja, en el orden de lectura anotado.
    gt_figures = [(i, box) for i, (box, kind, _t) in enumerate(gt_blocks)
                  if kind == _GT_FIGURE_KIND]
    gt_captions = [(i, box, text) for i, (box, kind, text) in enumerate(gt_blocks)
                   if kind in _GT_CAPTION_KINDS]
    if not gt_figures:
        return metrics

    # Predicho: elementos con caja válida, separando figuras de captions.
    pred_figures = [(i, b) for i, e in enumerate(elements)
                    if STRUCTURE_KIND_TO_GT.get(str(e.get("element_type"))) == "figure"
                    and (b := _element_bbox(e)) is not None]
    pred_captions = [(i, b, str(e.get("text") or "")) for i, e in enumerate(elements)
                     if _pred_is_caption(e) and (b := _element_bbox(e)) is not None]

    fig_pairs = match_boxes([b for _i, b in gt_figures], [b for _i, b in pred_figures])
    metrics["figure_recall"] = round(len(fig_pairs) / len(gt_figures), 4)
    metrics["figure_precision"] = (
        round(len(fig_pairs) / len(pred_figures), 4) if pred_figures else 0.0)

    if gt_captions:
        cap_pairs = match_boxes([b for _i, b, _t in gt_captions], [b for _i, b, _t in pred_captions])
        metrics["figure_caption_recall"] = round(len(cap_pairs) / len(gt_captions), 4)
        metrics["figure_caption_precision"] = (
            round(len(cap_pairs) / len(pred_captions), 4) if pred_captions else 0.0)
        # Texto de las captions emparejadas (media; "" si ninguna trae texto).
        texts = [(gt_captions[gi][2], pred_captions[pi][2]) for gi, pi in cap_pairs
                 if gt_captions[gi][2] and pred_captions[pi][2]]
        if texts:
            metrics["figure_caption_text_f1"] = round(
                sum(word_f1(g, p) for g, p in texts) / len(texts), 4)
        # Asociación figura↔caption: para cada figura GT emparejada, ¿su caption
        # compañera (la anotada más próxima) también fue emparejada a un elemento?
        matched_caption_gt = {gi for gi, _pi in cap_pairs}
        companion = _companion_captions(gt_figures, gt_captions)
        paired = [gi for gi, _pi in fig_pairs if companion.get(gi) in matched_caption_gt]
        metrics["figure_caption_pair_f1"] = (
            round(len(paired) / len(fig_pairs), 4) if fig_pairs else 0.0)

    return metrics


def _pred_is_caption(element: dict) -> bool:
    """¿El elemento emitido es cualquier clase de caption/título de figura?"""
    return STRUCTURE_KIND_TO_GT.get(str(element.get("element_type"))) == "figure_caption"


def _companion_captions(gt_figures, gt_captions) -> dict[int, int | None]:
    """`figura_gt_idx -> caption_gt_idx` compañera (la caption más cercana).

    Los índices son **posiciones en las listas** `gt_figures`/`gt_captions` (los
    mismos que devuelven `match_boxes`), no índices de bloque. La anotación de
    OmniDocBench no liga explícitamente cada figura con su caption por id; se
    asume la **adyacencia**: la caption anotada cuyo bloque en el orden de lectura
    está más próximo a la figura. Es la heurística razonable de documentos y es
    determinista; con empates gana la anterior (las captions suelen ir bajo la
    figura). Sin captions anotadas, el mapa va vacío.
    """
    if not gt_captions:
        return {}
    out: dict[int, int | None] = {}
    for fi, (fig_block, _fbox) in enumerate(gt_figures):
        best, best_dist = None, None
        for ci, (cap_block, _cbox, _ctext) in enumerate(gt_captions):
            dist = abs(cap_block - fig_block)
            if best_dist is None or dist < best_dist:
                best, best_dist = ci, dist
        out[fi] = best
    return out


def _sequence_tau(gt_blocks, elements) -> float | None:
    """Tau de Kendall del orden de lectura: bloques emitidos vs `order` anotado.

    Empareja cada bloque GT con su elemento emitido por IoU@0.5 (1-a-1) y compara
    la **posición** de cada par en ambos órdenes. `None` con <2 pares (no hay
    secuencia medible) -> la métrica queda no evaluada.
    """
    pairs = match_boxes([box for box, _k, _t in gt_blocks],
                        [b for e in elements if (b := _element_bbox(e)) is not None])
    if len(pairs) < 2:
        return None
    # `match_boxes` empareja contra la lista de cajas **ya filtrada** (solo
    # elementos con caja válida), en el mismo orden que `elements`: el índice de
    # predicción de cada par es su posición en esa lista filtrada, que es también
    # su posición relativa en el orden de lectura emitido.
    filtered = [i for i, e in enumerate(elements) if _element_bbox(e) is not None]
    return kendall_tau(
        [filtered[pi] for _gi, pi in pairs],
        [gi for gi, _pi in pairs],
    )


def _element_bbox(element: dict) -> tuple[float, float, float, float] | None:
    """Caja envolvente `(x1, y1, x2, y2)` de los 4 puntos del elemento."""
    points = element.get("bbox") or []
    if not points:
        return None
    xs = [float(p[0]) for p in points]
    ys = [float(p[1]) for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def _markdown_tables(markdown: str) -> str:
    """Concatenación del HTML de las tablas presente en el Markdown del pipeline.

    `pp_structurev3` inyecta cada tabla como `<table ...>…</table>` en su
    Markdown; se extraen esos bloques para compararlos con el `html` anotado. Si
    no hay tablas en la salida, `""` (TEDS no evaluable, no `0.0`).
    """
    if "<table" not in markdown:
        return ""
    parts, start = [], markdown.find("<table")
    while start != -1:
        end = markdown.find("</table>", start)
        if end == -1:
            break
        parts.append(markdown[start:end + len("</table>")])
        start = markdown.find("<table", end)
    return "\n".join(parts)


def main(argv: Sequence[str] | None = None) -> int:
    args = common_argparser(SPEC.feature, SPEC.summary).parse_args(argv)
    dataset = args.dataset or "omnidocbench_full_page"
    samples = load_dataset(dataset, limit=args.limit, split=args.split)
    print(f"[full_page] dataset={dataset} muestras={len(samples)}")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_dir = feature_out_dir(args.output_dir, SPEC) / timestamp
    run_backends(
        samples,
        [b.strip() for b in (args.backends or DEFAULT_BACKENDS).split(",") if b.strip()],
        dataset, out_dir, timestamp,
        warmup=args.warmup, repeats=args.repeats, device=args.device,
        feature=SPEC.feature, factories=EXTRA_FACTORIES, models=EXTRA_MODELS,
        scorer=score_full_page,
    )
    print(f"\n[full_page] resultados en {out_dir}")
    return 0


def _self_check() -> None:
    """La GT de documento sale de la anotación: bloques con contenido, en orden."""
    from PIL import Image

    from common.datasets import _odb_page_blocks, _odb_page_markdown

    page = {
        "layout_dets": [
            {"category_type": "text_block", "ignore": False, "order": 1, "text": "hola"},
            {"category_type": "equation_isolated", "ignore": False, "order": 2, "latex": "$$x$$"},
            {"category_type": "text_mask", "ignore": False, "order": 3, "text": "no"},
        ],
        "page_info": {"image_path": "p.png"},
    }
    assert _odb_page_markdown(page) == "hola\n\n$$x$$"
    assert _odb_page_blocks(page) == ("text", "formula")
    assert Image.new("RGB", (2, 2)).size == (2, 2)  # PIL disponible (entrada del banco)

    # Métricas desgranadas: contenido (markdown) vs estructura/posición.
    image = Image.new("RGB", (10, 10))
    sample = Sample(
        "p", image, "", gt_markdown="hola", gt_blocks=("text",),
        gt_layout={"text_block": ((0.0, 0.0, 10.0, 5.0),), "table": ((0.0, 5.0, 10.0, 9.0),)},
        gt_html="<table><tr><td>x</td></tr></table>",
        gt_by_task={"formula": "$$x$$"},
    )
    hit = OcrOutput(
        "hola\n<table border=\"1\"><tr><td>x</td></tr></table>\n$$x$$",
        extra={
            "elements": [
                {"element_type": "text", "score": 0.9, "bbox": [[0, 0], [10, 0], [10, 5], [0, 5]]},
                {"element_type": "table", "score": 0.9, "bbox": [[0, 5], [10, 5], [10, 9], [0, 9]]},
            ],
            "formulas": ["$$x$$"],
        },
    )
    scored = score_full_page(sample, hit)
    assert scored["layout_map"] == 1.0 and scored["layout_recall"] == 1.0
    assert scored["table_teds"] == 1.0
    assert scored["latex_sim"] == 1.0
    # Tabla con el MISMO texto de celda pero estructura MAL (una fila en vez de
    # dos): `markdown_f1` no lo ve, `table_teds` si. Es el fallo que esta tarjeta
    # se propone destapar.
    from common.metrics import markdown_f1
    gt_tbl = "<table><tr><td>a</td></tr><tr><td>b</td></tr></table>"
    bad = OcrOutput("<table><tr><td>a</td><td>b</td></tr></table>",
                    extra={"elements": hit.extra["elements"], "formulas": ["$$x$$"]})
    bad_sample = Sample("t", image, "", gt_markdown="a b", gt_blocks=("table",), gt_html=gt_tbl)
    assert markdown_f1(bad_sample.gt_markdown, "a b") == 1.0   # contenido intacto
    assert score_full_page(bad_sample, bad)["table_teds"] < 1.0  # estructura penalizada
    # Sin GT de la modalidad, la métrica queda no evaluada (""), nunca 0.0.
    bare = Sample("q", image, "", gt_markdown="hola", gt_blocks=("text",))
    bare_scored = score_full_page(bare, hit)
    for key in ("layout_map", "layout_recall", "table_teds", "latex_sim", "latex_token_f1"):
        assert bare_scored[key] == "", key

    # --- títulos / índice y orden de lectura ---------------------------------
    # Página con dos títulos y un párrafo, en orden anotado 1-2-3.
    gt_ordered = (
        ((0.0, 0.0, 10.0, 3.0), "paragraph_title", "Introduccion"),
        ((0.0, 3.0, 10.0, 8.0), "text", "cuerpo"),
        ((0.0, 8.0, 10.0, 11.0), "paragraph_title", "Conclusion"),
    )
    page_gt = Sample("t", image, "", gt_markdown="x", gt_blocks=("text",),
                     gt_ordered_blocks=gt_ordered)
    # El motor emite TODO bien: mismos títulos, mismo orden.
    good = OcrOutput("", extra={"elements": [
        {"element_type": "paragraph_title", "score": 0.9, "text": "Introduccion",
         "bbox": [[0, 0], [10, 0], [10, 3], [0, 3]]},
        {"element_type": "text", "score": 0.9, "text": "cuerpo",
         "bbox": [[0, 3], [10, 3], [10, 8], [0, 8]]},
        {"element_type": "paragraph_title", "score": 0.9, "text": "Conclusion",
         "bbox": [[0, 8], [10, 8], [10, 11], [0, 11]]},
    ]})
    good_m = score_full_page(page_gt, good)
    assert good_m["title_recall"] == 1.0 and good_m["title_precision"] == 1.0
    assert good_m["title_text_f1"] == 1.0
    assert good_m["title_seq_tau"] == 1.0 and good_m["read_order_tau"] == 1.0
    # Bloques correctos pero DESORDENADOS: los títulos van invertidos. El
    # `markdown_f1` no lo ve (mismo multiconjunto de tokens); el orden de lectura
    # como secuencia SÍ baja. Es exactamente el hueco que esta tarjeta cubre.
    swapped = OcrOutput("", extra={"elements": [
        {"element_type": "paragraph_title", "score": 0.9, "text": "Conclusion",
         "bbox": [[0, 8], [10, 8], [10, 11], [0, 11]]},
        {"element_type": "text", "score": 0.9, "text": "cuerpo",
         "bbox": [[0, 3], [10, 3], [10, 8], [0, 8]]},
        {"element_type": "paragraph_title", "score": 0.9, "text": "Introduccion",
         "bbox": [[0, 0], [10, 0], [10, 3], [0, 3]]},
    ]})
    swapped_m = score_full_page(page_gt, swapped)
    assert swapped_m["title_recall"] == 1.0              # los encuentra todos...
    assert swapped_m["read_order_tau"] < good_m["read_order_tau"]  # ...pero desordenados
    assert swapped_m["title_seq_tau"] == -1.0            # títulos invertidos
    # El LCS de tokens solo ve el orden **relativo** de tokens compartidos: mover
    # un bloque rodeado de vocabulario repetido apenas mueve `markdown_f1`, pero
    # la tau de orden lo castiga. Es el hueco que la tarjeta señala: una métrica
    # de secuencia no es el solape de tokens.
    from common.metrics import markdown_f1 as _md
    ordered_text = "a b c d e f g h"
    reordered = "e f g h a b c d"      # dos mitades intercambiadas, mismos tokens
    assert _md(ordered_text, reordered) == 0.5   # el LCS tampoco es ciego: baja
    # ...pero con vocabulario repetido el LCS aguanta alto mientras el orden real
    # cambia: por eso hace falta una métrica de secuencia, no solo de tokens.
    assert _md("x x x y y y", "y y y x x x") > 0.4
    # Página SIN títulos anotados: métricas de títulos no evaluadas, orden sí.
    no_title = Sample("n", image, "", gt_markdown="x", gt_blocks=("text",),
                      gt_ordered_blocks=(((0.0, 3.0, 10.0, 8.0), "text", "cuerpo"),))
    nt = score_full_page(no_title, good)
    assert nt["title_recall"] == "" and nt["title_precision"] == "" and nt["title_seq_tau"] == ""

    # --- figuras y captions --------------------------------------------------
    # Página con una figura y su caption anotadas (kind del pipeline: la figura
    # llega como `image`, la caption como `figure_title`).
    fig_blocks = (
        ((0.0, 0.0, 10.0, 6.0), "image", ""),
        ((0.0, 6.0, 10.0, 8.0), "figure_title", "Fig 1: diagrama"),
    )
    fig_gt = Sample("f", image, "", gt_markdown="x", gt_blocks=("figure",),
                    gt_ordered_blocks=fig_blocks)
    # (a) Completa: figura + caption, ambos bien localizados.
    full = OcrOutput("", extra={"elements": [
        {"element_type": "image", "score": 0.9, "bbox": [[0, 0], [10, 0], [10, 6], [0, 6]]},
        {"element_type": "figure_title", "score": 0.9, "text": "Fig 1: diagrama",
         "bbox": [[0, 6], [10, 6], [10, 8], [0, 8]]},
    ]})
    m_full = score_full_page(fig_gt, full)
    assert m_full["figure_recall"] == 1.0 and m_full["figure_precision"] == 1.0
    assert m_full["figure_caption_recall"] == 1.0
    assert m_full["figure_caption_pair_f1"] == 1.0
    assert m_full["figure_caption_text_f1"] == 1.0
    # (b) Figuras detectadas pero SIN caption: la asociación figura↔caption debe
    # caer aunque la detección de la figura sea perfecta -> no puntúa igual que
    # una página completa. Es el criterio central de esta tarjeta.
    nocap = OcrOutput("", extra={"elements": [
        {"element_type": "image", "score": 0.9, "bbox": [[0, 0], [10, 0], [10, 6], [0, 6]]},
    ]})
    m_nocap = score_full_page(fig_gt, nocap)
    assert m_nocap["figure_recall"] == 1.0            # la figura sí se detecta...
    assert m_nocap["figure_caption_pair_f1"] == 0.0   # ...pero sin caption, la asociación cae
    assert m_nocap["figure_caption_pair_f1"] < m_full["figure_caption_pair_f1"]
    # Página sin GT de figuras: métricas no evaluadas, nunca 0.0.
    nofig = Sample("g", image, "", gt_markdown="x", gt_blocks=("text",),
                   gt_ordered_blocks=(((0.0, 3.0, 10.0, 8.0), "text", "cuerpo"),))
    nf = score_full_page(nofig, full)
    for key in ("figure_recall", "figure_precision", "figure_caption_recall",
                "figure_caption_precision", "figure_caption_pair_f1",
                "figure_caption_text_f1"):
        assert nf[key] == "", key
    print("features.full_page self-check OK")


if __name__ == "__main__":  # pragma: no cover - ejecución manual
    if "--self-check" in sys.argv:
        _self_check()
    else:
        raise SystemExit(main())
