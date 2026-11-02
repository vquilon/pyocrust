#!/usr/bin/env python
"""Banco de la feature **full_page** (documento completo → Markdown y bloques).

Pipeline completo de página: layout + OCR + tablas + fórmulas en una sola salida
Markdown. Mide **`markdown_f1`** (LCS de tokens sobre el Markdown, sensible al
orden y conservando el LaTeX) y **`block_f1`** (multiconjunto de tipos de bloque),
además del CER/WER de texto que ya calcula el runner.

Dataset por defecto: `omnidocbench_full_page` — el Markdown de referencia se
**reconstruye** de la anotación de OmniDocBench: sus bloques (`text`/`latex`/
`html`) concatenados en su `order` de lectura, y sus tipos de bloque traducidos al
vocabulario que emite el pipeline (`kind`). No se inventa contenido: solo se
serializa lo que el dataset ya anota.

Provenance: todo número que salga de aquí es **`medido`**; el `summary.json` de la
run guarda comando, dataset, `n`, `warmup`, `repeats`, dispositivo y fecha.

Uso:
    .venv/Scripts/python.exe benchmarks/features/full_page/bank.py --limit 6
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

# Ejecutable como script (`python benchmarks/features/full_page/bank.py`).
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from datetime import datetime

from common import load_dataset, run_backends
from features._base import FeatureSpec, common_argparser, feature_out_dir, unavailable_factory

SPEC = FeatureSpec(
    feature="full_page",
    summary="Pipeline completo de página → Markdown/bloques (texto + tablas + fórmulas juntos).",
    pyocrust_task="pp_structurev3 (VeloceOCR) e Indra (pipeline completo de página)",
    metric="markdown_f1 / block_f1 (equivalencia de documento, no solo OCR de texto) + CER/WER",
    dataset="omnidocbench_full_page: Markdown GT reconstruido de los bloques anotados en orden de lectura",
    alternatives={
        "docling": ("docling", "docling"),
        "unstructured": ("unstructured", "unstructured"),
        "paddleocr PP-StructureV3": ("paddleocr", "paddleocr paddlepaddle"),
        "marker-pdf": ("marker", "marker-pdf"),
    },
    status="implemented",
    note="El GT de documento se serializa de la anotación (texto + LaTeX + HTML de tabla en orden de lectura); no se inventa contenido.",
    provenance="valores MEDIDOS por este banco (markdown_f1/block_f1 contra la GT reconstruida de OmniDocBench)",
)

# --- alternativas de pipeline documental -------------------------------------
# `opendatalab/PDF-Extract-Kit-1.0` (pesos ya en cache HF) aún no tiene adaptador
# escrito: se registra como `skipped` con motivo honesto (nunca `ok`).
EXTRA_FACTORIES = {
    "pdf_extract_kit": unavailable_factory(
        "pdf_extract_kit",
        "pdf-extract-kit (opendatalab/PDF-Extract-Kit-1.0; pesos en cache HF, adaptador pendiente)",
    ),
}
EXTRA_MODELS = {name: (name, "default") for name in EXTRA_FACTORIES}

# `pyocrust_indra` se salta solo si sus 9 artefactos no están en disco (motivo en el informe).
# Orden: pipeline propio de pyocrust y, al final, la alternativa documental.
DEFAULT_BACKENDS = "pyocrust_structure,pyocrust_indra,pdf_extract_kit"


def main(argv: Sequence[str] | None = None) -> int:
    args = common_argparser(SPEC.feature, SPEC.summary).parse_args(argv)
    dataset = args.dataset or "omnidocbench_full_page"
    samples = load_dataset(dataset, limit=args.limit, split=args.split)
    print(f"[full_page] dataset={dataset} muestras={len(samples)}")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_dir = feature_out_dir(args.output_dir, SPEC) / timestamp
    run_backends(
        samples,
        [b.strip() for b in (args.backends or DEFAULT_BACKENDS).split(",") if b.strip()],
        dataset, out_dir, timestamp,
        warmup=args.warmup, repeats=args.repeats, device=args.device,
        feature=SPEC.feature, factories=EXTRA_FACTORIES, models=EXTRA_MODELS,
    )
    print(f"\n[full_page] resultados en {out_dir}")
    return 0


def _self_check() -> None:
    """La GT de documento sale de la anotación: bloques con contenido, en orden."""
    from PIL import Image

    from common.datasets import _odb_page_blocks, _odb_page_markdown

    page = {
        "layout_dets": [
            {"category_type": "text_block", "ignore": False, "order": 1, "text": "hola"},
            {"category_type": "equation_isolated", "ignore": False, "order": 2, "latex": "$$x$$"},
            {"category_type": "text_mask", "ignore": False, "order": 3, "text": "no"},
        ],
        "page_info": {"image_path": "p.png"},
    }
    assert _odb_page_markdown(page) == "hola\n\n$$x$$"
    assert _odb_page_blocks(page) == ("text", "formula")
    assert Image.new("RGB", (2, 2)).size == (2, 2)  # PIL disponible (entrada del banco)
    print("features.full_page self-check OK")


if __name__ == "__main__":  # pragma: no cover - ejecución manual
    if "--self-check" in sys.argv:
        _self_check()
    else:
        raise SystemExit(main())
