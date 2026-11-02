#!/usr/bin/env python
"""Banco de la feature **rectification** (enderezado de documentos deformados).

Corrección de la deformación de perspectiva antes de OCR. Mide la **similitud
estructural (SSIM)** entre la imagen rectificada por el motor y la imagen limpia
de la que se partió.

Dataset por defecto: `synthetic_rectification` — **GT sintético determinista**. Se
toman las páginas de OmniDocBench ya presentes en `benchmarks/data_cache` (sin
descargar nada), se reescalan a un tamaño fijo y se les aplica una homografía
conocida; el GT es la imagen limpia original. El par (deformada, limpia) es
reproducible entre ejecuciones.

Provenance: todo número que salga de aquí es **`medido`**; el `summary.json` de la
run guarda comando, dataset, `n`, `warmup`, `repeats`, dispositivo y fecha.

Uso:
    .venv/Scripts/python.exe benchmarks/features/rectification/bank.py --limit 6
"""

from __future__ import annotations

import io
import sys
from pathlib import Path
from typing import Sequence

# Ejecutable como script (`python benchmarks/features/rectification/bank.py`).
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from datetime import datetime

from PIL import Image

from common import OcrOutput, Sample, load_dataset, run_backends
from common.metrics import image_ssim
from features._base import FeatureSpec, common_argparser, feature_out_dir

SPEC = FeatureSpec(
    feature="rectification",
    summary="Rectificación de documentos deformados (páginas curvadas/inclinadas) antes de OCR.",
    pyocrust_task="document_rectification (TaskPredictor; UVDoc, devuelve el PNG rectificado)",
    metric="similitud estructural (SSIM) con la imagen limpia de referencia",
    dataset="synthetic_rectification: páginas cacheadas con una homografía conocida; GT = la imagen limpia",
    alternatives={
        "paddleocr": ("paddleocr", "paddleocr paddlepaddle"),
        "docling": ("docling", "docling"),
    },
    status="implemented",
    note="El GT es la imagen limpia original (par reproducible deformada/limpia); SSIM se mide en gris y acotado a [0,1].",
    provenance="valores MEDIDOS por este banco (SSIM contra la referencia limpia, GT sintético determinista)",
)


def score_rectification(sample: Sample, output: OcrOutput) -> dict:
    """SSIM entre el PNG rectificado por el motor y la imagen limpia de referencia."""
    data = output.extra.get("image") or b""
    if not data or sample.gt_image is None:
        # Sin imagen de referencia o sin salida rectificada: no evaluada ("").
        return {"rect_sim": ""}
    rectified = Image.open(io.BytesIO(data)).convert("RGB")
    value = image_ssim(sample.gt_image, rectified)
    # `image_ssim` devuelve None si falta scikit-image: métrica no evaluada.
    return {"rect_sim": "" if value is None else round(value, 4)}


def main(argv: Sequence[str] | None = None) -> int:
    args = common_argparser(SPEC.feature, SPEC.summary).parse_args(argv)
    dataset = args.dataset or "synthetic_rectification"
    samples = load_dataset(dataset, limit=args.limit, split=args.split)
    print(f"[rectification] dataset={dataset} muestras={len(samples)}")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_dir = feature_out_dir(args.output_dir, SPEC) / timestamp
    run_backends(
        samples,
        [b.strip() for b in (args.backends or "pyocrust_rectify").split(",") if b.strip()],
        dataset, out_dir, timestamp,
        warmup=args.warmup, repeats=args.repeats, device=args.device,
        feature=SPEC.feature, scorer=score_rectification,
    )
    print(f"\n[rectification] resultados en {out_dir}")
    return 0


def _self_check() -> None:
    """SSIM: 1.0 contra la misma imagen, y "no evaluada" sin salida o sin GT."""
    clean = Image.new("RGB", (24, 16), "white")
    buffer = io.BytesIO()
    clean.save(buffer, format="PNG")
    hit = OcrOutput("", extra={"image": buffer.getvalue()})
    sample = Sample("r", clean, "", gt_image=clean)
    assert score_rectification(sample, hit)["rect_sim"] == 1.0
    assert score_rectification(Sample("r", clean, ""), hit) == {"rect_sim": ""}
    assert score_rectification(sample, OcrOutput("", extra={"image": b""})) == {"rect_sim": ""}
    print("features.rectification self-check OK")


if __name__ == "__main__":  # pragma: no cover - ejecución manual
    if "--self-check" in sys.argv:
        _self_check()
    else:
        raise SystemExit(main())
