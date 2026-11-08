#!/usr/bin/env python
"""Banco de la feature **orientation** (orientación de página completa).

Orientación de la página completa (0/90/180/270°) antes de OCR. Mide la
**accuracy** de las 4 clases.

Dataset por defecto: `synthetic_orientation` — **GT sintético determinista**. Se
toman las páginas de OmniDocBench si están en `benchmarks/data_cache` y, si no
(checkout limpio o sin red), páginas sintéticas deterministas generadas con PIL;
en ambos casos se rotan 0/90/180/270 y el GT es la etiqueta de corrección que el
clasificador debe emitir para esa rotación, `(360 - a) mod 360`, comprobada sobre
las cuatro clases en una página real antes de escribir el banco.

Provenance: todo número que salga de aquí es **`medido`**; el `summary.json` de la
run guarda comando, dataset, `n`, `warmup`, `repeats`, dispositivo y fecha.

Uso:
    .venv/Scripts/python.exe benchmarks/features/orientation/bank.py --limit 8
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

# Ejecutable como script (`python benchmarks/features/orientation/bank.py`).
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from datetime import datetime

from common import load_dataset, run_backends
from features._base import FeatureSpec, common_argparser, feature_out_dir, orientation_accuracy

SPEC = FeatureSpec(
    feature="orientation",
    summary="Orientación de la página completa (0/90/180/270°) antes de OCR.",
    pyocrust_task="document_orientation (TaskPredictor; PP-LCNet)",
    metric="accuracy de la rotación (4 clases)",
    dataset="synthetic_orientation: páginas de OmniDocBench (o sintéticas sin caché) rotadas 0/90/180/270; GT = etiqueta de corrección ((360-a) mod 360)",
    alternatives={
        "paddleocr (mismo peso, otra via)": ("paddleocr", "paddleocr paddlepaddle"),
        "easyocr_rotation (independiente)": ("easyocr", "easyocr"),
        "docling": ("docling", "docling (sin modelo de orientacion dedicado)"),
        "surya": ("surya", "surya-ocr (requiere torch)"),
    },
    status="implemented",
    note="GT sintético determinista y reproducible: la rotación aplicada es conocida y su etiqueta esperada también.",
    provenance="valores MEDIDOS por este banco (accuracy sobre GT sintético determinista, sin descargar nada)",
)

# `easyocr_rotation` es un tercero INDEPENDIENTE (no pesos PaddleOCR): el
# recognizer de EasyOCR elige la rotación de mayor confianza, no un PP-LCNet.
# `lcnet_doc_ori` se mantiene pero es el MISMO peso del banco por otro runtime.
DEFAULT_BACKENDS = "pyocrust_orientation,lcnet_doc_ori,easyocr_rotation"


def main(argv: Sequence[str] | None = None) -> int:
    args = common_argparser(SPEC.feature, SPEC.summary).parse_args(argv)
    dataset = args.dataset or "synthetic_orientation"
    samples = load_dataset(dataset, limit=args.limit, split=args.split)
    print(f"[orientation] dataset={dataset} muestras={len(samples)}")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_dir = feature_out_dir(args.output_dir, SPEC) / timestamp
    run_backends(
        samples,
        [b.strip() for b in (args.backends or DEFAULT_BACKENDS).split(",") if b.strip()],
        dataset, out_dir, timestamp,
        warmup=args.warmup, repeats=args.repeats, device=args.device,
        feature=SPEC.feature, scorer=orientation_accuracy,
    )
    print(f"\n[orientation] resultados en {out_dir}")
    return 0


def _self_check() -> None:
    """La etiqueta de corrección del GT sintético es la esperada para cada rotación."""
    from common.datasets import ORIENTATION_ANGLES

    assert ORIENTATION_ANGLES == (0, 90, 180, 270)
    assert [str((360 - a) % 360) for a in ORIENTATION_ANGLES] == ["0", "270", "180", "90"]
    print("features.orientation self-check OK")


if __name__ == "__main__":  # pragma: no cover - ejecución manual
    if "--self-check" in sys.argv:
        _self_check()
    else:
        raise SystemExit(main())
