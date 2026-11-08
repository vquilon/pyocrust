#!/usr/bin/env python
"""Banco de la feature **text_line** (orientación de línea de texto).

Orientación de cada línea de texto (0/180°) antes de reconocerla. Mide la
**accuracy** de las 2 clases.

Dataset por defecto: `synthetic_text_line` — **GT sintético determinista**. Se
recortan los bloques de texto anotados de las páginas de OmniDocBench si están en
`benchmarks/data_cache` y, si no (checkout limpio o sin red), líneas de páginas
sintéticas generadas con PIL; en ambos casos se giran 0/180 y el GT es la
etiqueta de orientación aplicada.

Provenance: todo número que salga de aquí es **`medido`**; el `summary.json` de la
run guarda comando, dataset, `n`, `warmup`, `repeats`, dispositivo y fecha.

Uso:
    .venv/Scripts/python.exe benchmarks/features/text_line/bank.py --limit 8
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

# Ejecutable como script (`python benchmarks/features/text_line/bank.py`).
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from datetime import datetime

from common import load_dataset, run_backends
from features._base import FeatureSpec, common_argparser, feature_out_dir, orientation_accuracy

SPEC = FeatureSpec(
    feature="text_line",
    summary="Orientación de cada línea de texto (0/180°) antes de reconocerla.",
    pyocrust_task="text_line_orientation (TaskPredictor; PP-LCNet)",
    metric="accuracy 0/180 por línea",
    dataset="synthetic_text_line: recortes de línea (OmniDocBench o sintéticos sin caché), girados 0/180; GT = orientación aplicada",
    alternatives={
        "paddleocr (mismo peso, otra via)": ("paddleocr", "paddleocr paddlepaddle"),
        "rapidocr_mobile_cls (independiente)": ("rapidocr", "rapidocr (ch_ppocr_mobile_v2.0_cls)"),
        "surya": ("surya", "surya-ocr (requiere torch)"),
    },
    status="implemented",
    note="GT sintético determinista; la entrada es un recorte de línea (la tarea espera una línea, no una página).",
    provenance="valores MEDIDOS por este banco (accuracy sobre GT sintético determinista, sin descargar nada)",
)

# `rapidocr_mobile_cls` es un tercero INDEPENDIENTE (red mobile cls de PP-OCRv2 del
# proyecto RapidAI, no el PP-LCNet del banco); `lcnet_textline_ori` es el MISMO peso
# del banco por otro runtime (`onnxruntime`).
DEFAULT_BACKENDS = "pyocrust_textline,lcnet_textline_ori,rapidocr_mobile_cls"


def main(argv: Sequence[str] | None = None) -> int:
    args = common_argparser(SPEC.feature, SPEC.summary).parse_args(argv)
    dataset = args.dataset or "synthetic_text_line"
    samples = load_dataset(dataset, limit=args.limit, split=args.split)
    print(f"[text_line] dataset={dataset} muestras={len(samples)}")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_dir = feature_out_dir(args.output_dir, SPEC) / timestamp
    run_backends(
        samples,
        [b.strip() for b in (args.backends or DEFAULT_BACKENDS).split(",") if b.strip()],
        dataset, out_dir, timestamp,
        warmup=args.warmup, repeats=args.repeats, device=args.device,
        feature=SPEC.feature, scorer=orientation_accuracy,
    )
    print(f"\n[text_line] resultados en {out_dir}")
    return 0


def _self_check() -> None:
    """Los dos ángulos del GT sintético se corresponden con su etiqueta."""
    from common.datasets import TEXT_LINE_ANGLES

    assert TEXT_LINE_ANGLES == (0, 180)
    assert [str(a) for a in TEXT_LINE_ANGLES] == ["0", "180"]
    print("features.text_line self-check OK")


if __name__ == "__main__":  # pragma: no cover - ejecución manual
    if "--self-check" in sys.argv:
        _self_check()
    else:
        raise SystemExit(main())
