#!/usr/bin/env python
"""Banco de la feature **layout** (detección de bloques por clase).

Igual que el componente de layout de `oar-ocr`: un detector asigna a cada bloque
de la página su clase y su caja. Mide **mAP@IoU 0.5** y **recall@IoU 0.5** por
clase de bloque (macro), emparejando cajas GT y predichas 1-a-1.

Dataset por defecto: `omnidocbench_layout` — las páginas de OmniDocBench anotan
cada bloque con su `category_type` y su `poly`, así que **hay GT de layout real**
(no se inventa nada). Solo entran las clases con equivalencia declarada entre el
vocabulario del modelo y las categorías anotadas (`common.datasets.
LAYOUT_MODEL_TO_GT`); las que no la tienen (p. ej. `inline_formula`,
`formula_number`, `seal`) quedan fuera de la métrica y se documentan en la README.
El mapa completo (DocLayNet ↔ OmniDocBench ↔ PP-DocLayout, con fuente por par) y
la regla de clases ignoradas viven en `features/layout/class_map.md`.

Provenance: todo número que salga de aquí es **`medido`** (ejecutado por nosotros);
el `summary.json` de la run guarda comando, dataset, `n`, `warmup`, `repeats`,
dispositivo y fecha.

Uso:
    .venv/Scripts/python.exe benchmarks/features/layout/bank.py --limit 8
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

# Ejecutable como script (`python benchmarks/features/layout/bank.py`).
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from datetime import datetime

from common import OcrOutput, Sample, load_dataset, run_backends
from common.datasets import LAYOUT_MODEL_TO_GT, STRUCTURE_KIND_TO_GT, layout_gt_classes
from common.metrics import detection_map
from common.runner import YOLO_LAYOUT_MODELS
from features._base import FeatureSpec, common_argparser, feature_out_dir

# Vocabulario -> categoría OmniDocBench para puntuar las cajas de **cualquier**
# motor de este banco. Union de los dos vocabularios reales:
#   * `pp_doclayoutv3` (detector especializado, `pyocrust_layout`): dice
#     `display_formula`;
#   * pipeline completo (`pyocrust_structure`, `pp_structurev3`): dice `formula`,
#     y ademas `list`, `chart_title`... (ver `STRUCTURE_KIND_TO_GT`).
# Las claves en comun mapean al MISMO destino (comprobado), asi que la union no
# reasigna nada: solo evita que las cajas de formula del pipeline se caigan en
# silencio (su `formula` no esta en `LAYOUT_MODEL_TO_GT`).
_LAYOUT_KIND_TO_GT = {**STRUCTURE_KIND_TO_GT, **LAYOUT_MODEL_TO_GT}

SPEC = FeatureSpec(
    feature="layout",
    summary="Detección de layout de página: cada bloque (título, párrafo, tabla, figura, fórmula, encabezado...) con su clase y su caja.",
    pyocrust_task="layout_detection (TaskPredictor, pp_doclayoutv3)",
    metric="mAP@IoU 0.5 y recall@IoU 0.5 macro por clase de bloque (emparejado 1-a-1)",
    dataset="omnidocbench_layout: OmniDocBench anota `category_type` + `poly` por bloque (GT real, no inventado); muestra estratificada por `data_source × layout`",
    alternatives={
        "layoutparser": ("layoutparser", "layoutparser"),
        "docling": ("docling", "docling"),
        "unstructured": ("unstructured", "unstructured"),
        "paddleocr": ("paddleocr", "paddleocr paddlepaddle"),
        "TATR (transformers)": ("transformers", "transformers + table-transformer"),
    },
    status="implemented",
    note="Métrica acotada a las clases con equivalencia declarada modelo<->anotación; el resto se ignora y se documenta.",
    provenance="valores MEDIDOS por este banco (mAP/recall@IoU sobre las cajas anotadas de OmniDocBench)",
)

# Orden: detector propio de `pyocrust`, la alternativa real, y — cerrando la
# lista — el **pipeline completo** (`pyocrust_structure`, `pp_structurev3`), cuyas
# cajas de layout salen de `extra["elements"]`: la compara cruzada del pipeline
# contra el detector especializado con el MISMO GT de layout. Las que no tengan
# pesos en caché quedan `skipped` con su motivo — nunca `ok`.
DEFAULT_BACKENDS = ",".join(
    ["pyocrust_layout", "docling_heron_101", "deformable_detr", *sorted(YOLO_LAYOUT_MODELS),
     "pyocrust_structure"]
)


def _model_bbox(element: dict) -> tuple[float, float, float, float] | None:
    """Caja envolvente `(x1, y1, x2, y2)` de los 4 puntos que emite el detector."""
    points = element.get("bbox") or []
    if not points:
        return None
    xs = [float(p[0]) for p in points]
    ys = [float(p[1]) for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def score_layout(sample: Sample, output: OcrOutput) -> dict:
    """mAP/recall@IoU 0.5 por clase: cajas anotadas vs. bloques detectados.

    Dos filtros, ambos por la regla del banco (una clase sin equivalencia se
    **ignora**, nunca cuenta como acierto ni como fallo silencioso):

    * una clase del modelo sin equivalencia en `LAYOUT_MODEL_TO_GT` no entra en
      la predicción;
    * una categoría anotada que el vocabulario del motor **no puede emitir**
      (p. ej. `page_number`/`reference` en los detectores DocLayNet) se excluye
      de la media en vez de restar como un `0.0` espurio ([ref: class_map.md]).

    El mapa de equivalencias, con su fuente por par, vive en
    `features/layout/class_map.md` (código: `common.datasets`).

    ponytail: el AP se promedia **por pagina y clase** (macro), no agrupando las
    cajas de todo el dataset. Con `n=8` paginas una clase con 1 caja GT pesa lo
    mismo que una con 30, asi que el numero es mas ruidoso y algo mas bajo que un
    mAP agrupado; el ranking entre motores no cambia. Agrupar exige acumular las
    cajas de todas las paginas en `run_backends` antes de puntuar.
    """
    predicted: dict[str, list[tuple[float, tuple[float, float, float, float]]]] = {}
    for element in output.extra.get("elements") or []:
        category = _LAYOUT_KIND_TO_GT.get(str(element.get("element_type")))
        box = _model_bbox(element)
        if category is None or box is None:
            continue
        predicted.setdefault(category, []).append((float(element.get("score", 0.0) or 0.0), box))
    # GT acotado a las categorías que este motor puede emitir.
    emittable = layout_gt_classes(output.extra.get("engine"))
    gt = {cls: boxes for cls, boxes in (sample.gt_layout or {}).items() if cls in emittable}
    mean_ap, recall = detection_map(gt, predicted)
    # Sin cajas GT evaluables la métrica queda **no evaluada** (""), nunca un 0.0.
    return {
        "layout_map": "" if mean_ap is None else round(mean_ap, 4),
        "layout_recall": "" if recall is None else round(recall, 4),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = common_argparser(SPEC.feature, SPEC.summary)
    # Muestra **estratificada** por `data_source × layout` (n ≤ 40): cubre la
    # heterogeneidad real y evita el sesgo de `_odb_rich_first` (ricas en
    # tabla/fórmula -> casi todo `equation_hard`). Ver `common.datasets._odb_stratified`.
    parser.set_defaults(limit=40)
    args = parser.parse_args(argv)
    dataset = args.dataset or "omnidocbench_layout"
    samples = load_dataset(dataset, limit=args.limit, split=args.split)
    strata = sorted({s.stratum for s in samples if s.stratum})
    print(f"[layout] dataset={dataset} muestras={len(samples)} estratos={len(strata)}")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_dir = feature_out_dir(args.output_dir, SPEC) / timestamp
    run_backends(
        samples,
        [b.strip() for b in (args.backends or DEFAULT_BACKENDS).split(",") if b.strip()],
        dataset, out_dir, timestamp,
        warmup=args.warmup, repeats=args.repeats, device=args.device,
        feature=SPEC.feature, scorer=score_layout,
    )
    print(f"\n[layout] resultados en {out_dir}")
    return 0


def _self_check() -> None:
    """Comprobación mínima de la métrica: acierto perfecto, clase sin mapa y sin GT."""
    from PIL import Image

    sample = Sample("p", Image.new("RGB", (10, 10)), "",
                    gt_layout={"text_block": ((0.0, 0.0, 10.0, 5.0),)})
    hit = OcrOutput("", extra={"elements": [
        {"element_type": "text", "score": 0.9, "bbox": [[0, 0], [10, 0], [10, 5], [0, 5]]},
    ]})
    assert score_layout(sample, hit) == {"layout_map": 1.0, "layout_recall": 1.0}
    # Una clase del modelo sin equivalencia declarada no cuenta (ni a favor ni en contra).
    other = OcrOutput("", extra={"elements": [
        {"element_type": "seal", "score": 0.9, "bbox": [[0, 0], [10, 0], [10, 5], [0, 5]]},
    ]})
    assert score_layout(sample, other) == {"layout_map": 0.0, "layout_recall": 0.0}
    empty = Sample("q", Image.new("RGB", (10, 10)), "", gt_layout=None)
    assert score_layout(empty, hit) == {"layout_map": "", "layout_recall": ""}
    # Una categoria que el motor NO puede emitir se ignora: `page_number` no
    # existe en el vocabulario DocLayNet, asi que su GT no entra en la media.
    page = Sample("r", Image.new("RGB", (10, 10)), "",
                  gt_layout={"page_number": ((0.0, 0.0, 5.0, 5.0),)})
    yolo = OcrOutput("", extra={"engine": "ultralytics", "elements": [
        {"element_type": "number", "score": 0.9, "bbox": [[0, 0], [5, 0], [5, 5], [0, 5]]},
    ]})
    assert score_layout(page, yolo) == {"layout_map": "", "layout_recall": ""}
    # …pero el mismo GT SI se evalua para el detector propio, que si lo emite.
    assert score_layout(page, hit) == {"layout_map": 0.0, "layout_recall": 0.0}
    # El **pipeline completo** dice `formula` (no `display_formula`): con la union
    # de vocabularios su caja SI puntua contra el GT `equation_isolated`.
    eq = Sample("e", Image.new("RGB", (10, 10)), "",
                gt_layout={"equation_isolated": ((0.0, 0.0, 10.0, 5.0),)})
    struct = OcrOutput("", extra={"elements": [
        {"element_type": "formula", "score": 0.9, "bbox": [[0, 0], [10, 0], [10, 5], [0, 5]]},
    ]})
    assert score_layout(eq, struct) == {"layout_map": 1.0, "layout_recall": 1.0}
    print("features.layout self-check OK")


if __name__ == "__main__":  # pragma: no cover - ejecución manual
    if "--self-check" in sys.argv:
        _self_check()
    else:
        raise SystemExit(main())
