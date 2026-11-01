#!/usr/bin/env python
"""Banco de la feature **text_line** — esqueleto documentado.

Orientación de cada línea de texto (0/180°) antes de reconocerla.

Estado: **esqueleto**. No hay dataset local con GT de orientación de línea; el GT
es barato de generar (voltear líneas recortadas) pero no está incluido aún. Sin
GT, la calidad se reporta **no evaluada** (nunca un `0.0` espurio).

Provenance: este esqueleto **no publica valores numéricos** — no hay nada
ejecutado que respalde una cifra.

Uso:
    .venv/Scripts/python.exe benchmarks/features/text_line/bank.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

# Ejecutable como script (`python benchmarks/features/text_line/bank.py`).
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from features._base import FeatureSpec, run_skeleton

SPEC = FeatureSpec(
    feature="text_line",
    summary="Orientación de cada línea de texto (0/180°) antes de reconocerla.",
    pyocrust_task="text_line_orientation (TaskPredictor)",
    metric="accuracy 0/180 por línea",
    dataset="No hay dataset local con GT de orientación de línea.",
    alternatives={
        "paddleocr": ("paddleocr", "paddleocr paddlepaddle"),
        "surya": ("surya", "surya-ocr (requiere torch)"),
    },
    status="skeleton",
    note="GT barato de generar (voltear líneas recortadas) pero no incluido aún.",
    provenance="esqueleto: sin valores numéricos (no hay GT local; nada ejecutado)",
)


def main(argv: Sequence[str] | None = None) -> int:
    return run_skeleton(SPEC, argv)


if __name__ == "__main__":
    raise SystemExit(main())
