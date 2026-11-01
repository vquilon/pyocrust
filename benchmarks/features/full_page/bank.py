#!/usr/bin/env python
"""Banco de la feature **full_page** — esqueleto documentado.

Pipeline completo de página → Markdown/bloques (texto + tablas + fórmulas juntos).

Estado: **esqueleto**. Ya se mide el pipeline (`task_type=full_page` con Indra /
`pp_structurev3`) contra GT textual, pero la calidad Markdown/bloques queda **no
evaluada**: la release de OmniDocBench NO publica un Markdown de página
renderizado. Sin GT de esa modalidad no se inventa un `0.0`; el banco declara su
métrica para cuando haya GT propio.

Provenance: este esqueleto **no publica valores numéricos** — no hay nada
ejecutado que respalde una cifra.

Uso:
    .venv/Scripts/python.exe benchmarks/features/full_page/bank.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

# Ejecutable como script (`python benchmarks/features/full_page/bank.py`).
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from features._base import FeatureSpec, run_skeleton

SPEC = FeatureSpec(
    feature="full_page",
    summary="Pipeline completo de página → Markdown/bloques (texto + tablas + fórmulas juntos).",
    pyocrust_task="pp_structurev3 / Indra (VeloceOCR, pipeline completo)",
    metric="markdown_f1 / block_f1 (equivalencia de documento, no solo OCR de texto)",
    dataset="OmniDocBench (texto + LaTeX por bloque). La release NO publica Markdown de página renderizado: `markdown_f1`/`block_f1` quedan **no evaluadas** sin GT de esa modalidad.",
    alternatives={
        "docling": ("docling", "docling"),
        "unstructured": ("unstructured", "unstructured"),
        "paddleocr PP-StructureV3": ("paddleocr", "paddleocr paddlepaddle"),
        "marker-pdf": ("marker", "marker-pdf"),
    },
    status="skeleton",
    note="Ya se mide el pipeline (task_type=full_page) contra GT textual; la calidad Markdown/bloques queda no evaluada sin GT propio.",
    provenance="esqueleto: sin valores numéricos (no hay GT de página renderizada; nada ejecutado)",
)


def main(argv: Sequence[str] | None = None) -> int:
    return run_skeleton(SPEC, argv)


if __name__ == "__main__":
    raise SystemExit(main())
