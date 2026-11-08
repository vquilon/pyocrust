#!/usr/bin/env python
"""Banco de la feature **text** (detección + reconocimiento de texto).

Igual que el componente `text` de `oar-ocr`: un motor resuelve detección y
reconocimiento juntos. Mide **CER/WER/F1** (reconocimiento, con `*_ord` para
neutralizar el orden de lectura) y, cuando el dataset anota cajas, **recall@IoU**
y **IoU medio** (detección) — dos caras del mismo motor.

Dataset por defecto: `funsd` (formularios con GT de texto y **cajas** anotadas).
Alternativas Python integradas (en el default): rapidocr, easyocr, tesseract.
`surya`/`paddleocr`/`python-doctr` están **anunciadas sin adaptador**: quedan fuera
del default y solo aparecen como `skipped` con motivo si se piden explícitamente.

Provenance: todo número que salga de aquí es **`medido`** (ejecutado por nosotros);
el `summary.json` de la run guarda comando, dataset, `n`, `warmup`, `repeats`,
dispositivo y fecha.

Uso:
    .venv/Scripts/python.exe benchmarks/features/text/bank.py --limit 5
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

# Ejecutable como script (`python benchmarks/features/text/bank.py`).
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from datetime import datetime

from common import load_dataset, run_backends
from features._base import FeatureSpec, common_argparser, feature_out_dir, unavailable_factory

SPEC = FeatureSpec(
    feature="text",
    summary="Detección + reconocimiento de texto sobre imágenes con GT (FUNSD / OmniDocBench).",
    pyocrust_task="text_detection + text_recognition (VeloceOCR pp_ocrv6)",
    metric="CER / WER / word_f1 (+ cer_ord/wer_ord) y box_recall / box_iou_mean (detección)",
    dataset="funsd (texto + cajas GT) u omnidocbench (texto por orden de lectura)",
    alternatives={
        "rapidocr": ("rapidocr_onnxruntime", "rapidocr-onnxruntime"),
        "easyocr": ("easyocr", "easyocr"),
        "tesseract": ("pytesseract", "pytesseract + binario Tesseract"),
        "surya": ("surya", "surya-ocr (requiere torch)"),
        "paddleocr": ("paddleocr", "paddleocr paddlepaddle"),
        "python-doctr": ("doctr", "python-doctr (mindee/doctr, Apache-2.0)"),
    },
    status="implemented",
    provenance="valores MEDIDOS por este banco (no hay referencias externas en el reporte por defecto)",
)

# Alternativas aún no integradas: quedan `skipped` con motivo honesto (nunca `ok`).
# NO entran en `DEFAULT_BACKENDS`: sin adaptador no producen filas y anunciarlas en
# el default dejaba el informe con motores que nunca aparecen (criterio de la tarjeta).
# El fantasma `doctrl` (nombre no publicado) se resolvió a su paquete real:
# `python-doctr` (mindee/doctr, Apache-2.0), importable como `doctr`.
EXTRA_FACTORIES = {
    "surya": unavailable_factory("surya", "surya-ocr (requiere torch)"),
    "paddleocr": unavailable_factory("paddleocr", "paddleocr paddlepaddle"),
    "python-doctr": unavailable_factory("doctr", "python-doctr (mindee/doctr)"),
}
EXTRA_MODELS = {name: (name, "default") for name in EXTRA_FACTORIES}

# Orden por defecto: solo motores con adaptador real que producen filas. Las
# alternativas anunciadas sin fabrica (surya/paddleocr/python-doctr) se piden de
# forma explicita y salen como `skipped` con su motivo, no en el default.
DEFAULT_BACKENDS = "pyocrust,rapidocr,easyocr,tesseract"


def main(argv: Sequence[str] | None = None) -> int:
    args = common_argparser(SPEC.feature, SPEC.summary).parse_args(argv)
    dataset = args.dataset or "funsd"
    samples = load_dataset(dataset, limit=args.limit, split=args.split)
    print(f"[text] dataset={dataset} muestras={len(samples)}")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_dir = feature_out_dir(args.output_dir, SPEC) / timestamp
    run_backends(
        samples,
        [b.strip() for b in (args.backends or DEFAULT_BACKENDS).split(",") if b.strip()],
        dataset, out_dir, timestamp,
        warmup=args.warmup, repeats=args.repeats, device=args.device,
        feature=SPEC.feature, factories=EXTRA_FACTORIES, models=EXTRA_MODELS,
        dump_outputs=args.dump_outputs,
    )
    print(f"\n[text] resultados en {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
