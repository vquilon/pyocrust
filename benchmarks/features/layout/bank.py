#!/usr/bin/env python
"""Banco de la feature **layout** — esqueleto documentado.

Detección de layout de página: cada bloque (título, párrafo, tabla, figura,
fórmula, encabezado...) con su clase y su caja.

Estado: **esqueleto**. El dataset documental ya trae GT de layout (OmniDocBench
anota `category_type` + `poly` por bloque); falta escribir el emparejador
caja↔bloque y la métrica por clase. Sin GT adaptado, la calidad se reporta **no
evaluada** (nunca un `0.0` espurio).

Provenance: este esqueleto **no publica valores numéricos** — no hay nada
ejecutado que respalde una cifra.

Uso:
    .venv/Scripts/python.exe benchmarks/features/layout/bank.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

# Ejecutable como script (`python benchmarks/features/layout/bank.py`).
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from features._base import FeatureSpec, run_skeleton

SPEC = FeatureSpec(
    feature="layout",
    summary="Detección de layout de página: cada bloque (título, párrafo, tabla, figura, fórmula, encabezado...) con su clase y su caja.",
    pyocrust_task="layout_detection (TaskPredictor, pp_doclayoutv3)",
    metric="mAP / IoU por clase vs GT (precisión@IoU y recall por clase de bloque)",
    dataset="OmniDocBench anota `category_type` + `poly` por bloque (GT de layout disponible); falta el adaptador que empareja cajas predichas con GT.",
    alternatives={
        "layoutparser": ("layoutparser", "layoutparser"),
        "docling": ("docling", "docling"),
        "unstructured": ("unstructured", "unstructured"),
        "paddleocr": ("paddleocr", "paddleocr paddlepaddle"),
        "TATR (transformers)": ("transformers", "transformers + table-transformer"),
    },
    status="skeleton",
    note="El dataset documental ya trae GT de layout; falta el emparejador caja↔bloque y la métrica por clase.",
    provenance="esqueleto: sin valores numéricos (no hay GT adaptado; nada ejecutado)",
)


def main(argv: Sequence[str] | None = None) -> int:
    return run_skeleton(SPEC, argv)


if __name__ == "__main__":
    raise SystemExit(main())
