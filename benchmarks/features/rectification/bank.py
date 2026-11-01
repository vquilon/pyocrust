#!/usr/bin/env python
"""Banco de la feature **rectification** — esqueleto documentado.

Rectificación de documentos deformados (páginas curvadas/inclinadas) antes de OCR.

Estado: **esqueleto**. No hay GT público local de imagen rectificada de
referencia; sin par (deformada, enderezada) la calidad queda **no evaluada**
(nunca un `0.0` espurio).

Provenance: este esqueleto **no publica valores numéricos** — no hay nada
ejecutado que respalde una cifra.

Uso:
    .venv/Scripts/python.exe benchmarks/features/rectification/bank.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

# Ejecutable como script (`python benchmarks/features/rectification/bank.py`).
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from features._base import FeatureSpec, run_skeleton

SPEC = FeatureSpec(
    feature="rectification",
    summary="Rectificación de documentos deformados (páginas curvadas/inclinadas) antes de OCR.",
    pyocrust_task="document_rectification (TaskPredictor; devuelve PNG rectificado)",
    metric="calidad de enderezado (rectitud de líneas / similitud con la referencia enderezada)",
    dataset="No hay GT público local de imagen rectificada de referencia.",
    alternatives={
        "paddleocr": ("paddleocr", "paddleocr paddlepaddle"),
        "docling": ("docling", "docling"),
    },
    status="skeleton",
    note="Necesita un par (deformada, enderezada) de referencia; sin él, calidad no evaluada.",
    provenance="esqueleto: sin valores numéricos (no hay GT local; nada ejecutado)",
)


def main(argv: Sequence[str] | None = None) -> int:
    return run_skeleton(SPEC, argv)


if __name__ == "__main__":
    raise SystemExit(main())
