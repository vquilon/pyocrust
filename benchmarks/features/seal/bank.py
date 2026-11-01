#!/usr/bin/env python
"""Banco de la feature **seal** — esqueleto documentado.

Detección de texto dentro de sellos (tampones) superpuestos al documento.

Estado: **esqueleto**. No hay dataset local con GT de sellos; sin anotación la
calidad se reporta **no evaluada** (nunca un `0.0` espurio).

Provenance: este esqueleto **no publica valores numéricos** — no hay nada
ejecutado que respalde una cifra.

Uso:
    .venv/Scripts/python.exe benchmarks/features/seal/bank.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

# Ejecutable como script (`python benchmarks/features/seal/bank.py`).
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from features._base import FeatureSpec, run_skeleton

SPEC = FeatureSpec(
    feature="seal",
    summary="Detección de texto dentro de sellos (tampones) superpuestos al documento.",
    pyocrust_task="seal_text_detection (TaskPredictor)",
    metric="IoU / detección (precision@IoU de las cajas de sello)",
    dataset="No hay dataset local con GT de sellos.",
    alternatives={
        "paddleocr (seal)": ("paddleocr", "paddleocr paddlepaddle"),
        "doctrl": ("doctrl", "doctrl"),
    },
    status="skeleton",
    note="Requiere un set con sellos anotados; no se inventa GT.",
    provenance="esqueleto: sin valores numéricos (no hay GT local; nada ejecutado)",
)


def main(argv: Sequence[str] | None = None) -> int:
    return run_skeleton(SPEC, argv)


if __name__ == "__main__":
    raise SystemExit(main())
