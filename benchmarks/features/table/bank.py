#!/usr/bin/env python
"""Banco de la feature **table** — esqueleto documentado.

Tablas: clasificación (hay/no hay), estructura (filas/columnas) y detección de
celdas.

Estado: **esqueleto**. TEDS necesita el HTML de la tabla GT; OmniDocBench lo
anota por bloque, falta el adaptador. Sin GT de estructura, la calidad se reporta
**no evaluada** (nunca un `0.0` espurio).

Provenance: este esqueleto **no publica valores numéricos** — no hay nada
ejecutado que respalde una cifra.

Uso:
    .venv/Scripts/python.exe benchmarks/features/table/bank.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

# Ejecutable como script (`python benchmarks/features/table/bank.py`).
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from features._base import FeatureSpec, run_skeleton

SPEC = FeatureSpec(
    feature="table",
    summary="Tablas: clasificación (hay/no hay), estructura (filas/columnas) y detección de celdas.",
    pyocrust_task="table_classification / table_structure_recognition / table_cell_detection (TaskPredictor)",
    metric="TEDS / estructura (edit distance de la estructura reconstruida) y IoU de celdas",
    dataset="OmniDocBench anota tablas (`html`/`latex`); PubTabNet es el estándar de TEDS.",
    alternatives={
        "table-transformer (TATR)": ("transformers", "transformers + table-transformer"),
        "docling": ("docling", "docling"),
        "paddleocr PP-Structure": ("paddleocr", "paddleocr paddlepaddle"),
    },
    status="skeleton",
    note="TEDS necesita el HTML de la tabla GT; OmniDocBench lo anota por bloque, falta el adaptador.",
    provenance="esqueleto: sin valores numéricos (no hay GT adaptado; nada ejecutado)",
)


def main(argv: Sequence[str] | None = None) -> int:
    return run_skeleton(SPEC, argv)


if __name__ == "__main__":
    raise SystemExit(main())
