#!/usr/bin/env python
"""Banco de la feature **seal** (detección de regiones de sello/tampón).

Detección de regiones de sello superpuestas al documento. Mide **recall@IoU 0.5**
y el **IoU medio** de las cajas de sello (las métricas de cajas compartidas
`box_recall`/`box_iou_mean`, que el runner ya calcula cuando la muestra anota
`gt_boxes`).

Dataset por defecto: `synthetic_seal` — **GT SINTÉTICO determinista**. No hay set
público local con sellos anotados (OmniDocBench v1.6 no anota `category_type=seal`;
verificado sobre la anotación cacheada), así que el banco **genera** documentos
blancos con un tampón pegado en una posición conocida; la caja GT es el rectángulo
del sello. El set se declara **sintético** aquí y en su provenance: no es anotación
humana de sellos reales.

Provenance: todo número que salga de aquí es **`medido`**; el `summary.json` de la
run guarda comando, dataset, `n`, `warmup`, `repeats`, dispositivo y fecha, y el
`dataset` (`synthetic_seal`) deja explícito que el GT es sintético.

Uso:
    .venv/Scripts/python.exe benchmarks/features/seal/bank.py --limit 8 --backends pyocrust_seal
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

# Ejecutable como script (`python benchmarks/features/seal/bank.py`).
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from datetime import datetime

from common import load_dataset, run_backends
from features._base import FeatureSpec, common_argparser, feature_out_dir, unavailable_factory

SPEC = FeatureSpec(
    feature="seal",
    summary="Detección de regiones de sello (tampones) superpuestas al documento.",
    pyocrust_task="seal_text_detection (TaskPredictor; PP-OCRv4 mobile seal det)",
    metric="recall@IoU 0.5 / IoU medio de las cajas de sello (box_recall, box_iou_mean)",
    dataset="synthetic_seal: tampón sintético pegado en documento blanco, posición/caja conocidas (GT SINTÉTICO determinista)",
    alternatives={
        "paddleocr (seal)": ("paddleocr", "paddleocr paddlepaddle"),
        "doctrl": ("doctrl", "doctrl"),
    },
    status="implemented",
    note=(
        "GT SINTÉTICO determinista: no hay set público local con sellos anotados; "
        "el banco pega un tampón en posición conocida y la caja GT es el rectángulo del sello."
    ),
    provenance=(
        "valores MEDIDOS por este banco sobre un dataset SINTÉTICO determinista "
        "(sello pegado en documento blanco); no es anotación humana de sellos reales"
    ),
)

# Alternativas aún no integradas: quedan `skipped` con motivo honesto (nunca `ok`).
EXTRA_FACTORIES = {
    "paddleocr": unavailable_factory("paddleocr", "paddleocr paddlepaddle"),
    "doctrl": unavailable_factory("doctrl", "doctrl"),
}
EXTRA_MODELS = {name: (name, "default") for name in EXTRA_FACTORIES}


def main(argv: Sequence[str] | None = None) -> int:
    args = common_argparser(SPEC.feature, SPEC.summary).parse_args(argv)
    dataset = args.dataset or "synthetic_seal"
    samples = load_dataset(dataset, limit=args.limit, split=args.split)
    print(f"[seal] dataset={dataset} muestras={len(samples)}")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_dir = feature_out_dir(args.output_dir, SPEC) / timestamp
    # La métrica de sello es la de cajas (recall@IoU / IoU medio): el runner la
    # calcula solo cuando la muestra trae `gt_boxes`; no hace falta scorer propio.
    run_backends(
        samples,
        [b.strip() for b in (args.backends or "pyocrust_seal").split(",") if b.strip()],
        dataset, out_dir, timestamp,
        warmup=args.warmup, repeats=args.repeats, device=args.device,
        feature=SPEC.feature, factories=EXTRA_FACTORIES, models=EXTRA_MODELS,
    )
    print(f"\n[seal] resultados en {out_dir}")
    return 0


def _self_check() -> None:
    """El GT sintético de sello es determinista y su caja es la del tampón pegado."""
    from common.datasets import SEAL_STAMP_SIZE, load_synthetic_seal

    samples = load_synthetic_seal(limit=3)
    assert len(samples) == 3
    width, height = SEAL_STAMP_SIZE
    for sample, (x, y) in zip(samples, ((120, 140), (500, 260), (180, 640))):
        assert sample.gt_boxes == ((float(x), float(y), float(x + width), float(y + height)),)
    print("features.seal self-check OK")


if __name__ == "__main__":  # pragma: no cover - ejecución manual
    if "--self-check" in sys.argv:
        _self_check()
    else:
        raise SystemExit(main())
