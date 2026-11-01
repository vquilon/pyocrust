#!/usr/bin/env python
"""Banco de la feature **orientation** — esqueleto documentado.

Orientación de la página completa (0/90/180/270°) antes de OCR.

Estado: **esqueleto**. No hay dataset local con GT de orientación de página;
requiere rotar un set con orientación conocida y GT legible. Sin GT, la calidad
se reporta **no evaluada** (nunca un `0.0` espurio).

Provenance: este esqueleto **no publica valores numéricos** — no hay nada
ejecutado que respalde una cifra.

Uso:
    .venv/Scripts/python.exe benchmarks/features/orientation/bank.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

# Ejecutable como script (`python benchmarks/features/orientation/bank.py`).
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from features._base import FeatureSpec, run_skeleton

SPEC = FeatureSpec(
    feature="orientation",
    summary="Orientación de la página completa (0/90/180/270°) antes de OCR.",
    pyocrust_task="document_orientation (TaskPredictor)",
    metric="accuracy de la rotación (4 clases)",
    dataset="No hay dataset local con GT de orientación de página; requiere rotar un set con orientación conocida y GT legible.",
    alternatives={
        "paddleocr": ("paddleocr", "paddleocr paddlepaddle"),
        "docling": ("docling", "docling"),
        "surya": ("surya", "surya-ocr (requiere torch)"),
    },
    status="skeleton",
    note="Se puede construir GT rotando páginas de OmniDocBench y comprobando OCR; documentado, no medido todavía.",
    provenance="esqueleto: sin valores numéricos (no hay GT local; nada ejecutado)",
)


def main(argv: Sequence[str] | None = None) -> int:
    return run_skeleton(SPEC, argv)


if __name__ == "__main__":
    raise SystemExit(main())
