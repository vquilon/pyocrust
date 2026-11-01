#!/usr/bin/env python
"""Banco de la feature **formula** (fórmula → LaTeX).

Igual que el componente `formula` de `oar-ocr`. La crítica del usuario es
explícita: **easyocr/rapidocr no tienen modelo de fórmulas→LaTeX**, así que este
banco compara contra motores que **sí** emiten LaTeX. La unidad es cada fórmula
anotada (bloque `equation_isolated` de OmniDocBench, recorte por `poly` + GT de
su `latex`), la misma entrada PNG para todos.

Métrica (sobre la **forma canónica** de LaTeX, `latex_metrics.py`):
`latex_exact` (coincidencia normalizada), `latex_sim` (similitud) y
`latex_token_f1` (multiconjunto de comandos/símbolos). Más `ms/fórmula` y la
fracción de salidas con LaTeX, que separa quien **emite LaTeX** de quien solo
repite símbolos como texto.

Provenance: números **`medidos`** por este banco. Las alternativas comparadas son
reales; la disponibilidad es real (las ausentes quedan `skipped` con su
`pip install`). Los motores de OCR de texto (`easyocr`, `rapidocr`, `tesseract`)
se incluyen como **control** (no emiten LaTeX), no como alternativas del ranking.

Uso:
    .venv/Scripts/python.exe benchmarks/features/formula/bank.py --limit 10
"""

from __future__ import annotations

import io
import sys
import time
from pathlib import Path
from typing import Callable, Sequence

# Ejecutable como script (`python benchmarks/features/formula/bank.py`).
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from datetime import datetime

from PIL import Image

from common import OcrOutput, ProviderUnavailable, load_dataset, run_backends
from common.runner import _image_bytes
from features._base import FeatureSpec, common_argparser, feature_out_dir, unavailable_factory

SPEC = FeatureSpec(
    feature="formula",
    summary="Fórmula de imagen → LaTeX, comparada contra motores que SÍ producen LaTeX.",
    pyocrust_task="formula_recognition (TaskPredictor, PP-FormulaNet) + pipeline pp_structurev3 e Indra",
    metric="latex_exact / latex_sim / latex_token_f1 (forma canónica) + ms/fórmula y cobertura LaTeX",
    dataset="omnidocbench_formula (recorte por bloque `equation_isolated` + GT LaTeX)",
    alternatives={
        "pix2tex (LaTeX-OCR)": ("pix2tex", "pix2tex"),
        "texify (surya_latex_ocr)": ("texify", "texify"),
        "nougat": ("nougat", "nougat-ocr"),
        "UniMERNet": ("unimernet", "unimernet (github.com/opendatalab/UniMERNet)"),
        "Pix2Text": ("pix2text", "pix2text"),
        "TexTeller": ("texteller", "texteller"),
        "img2latex": ("img2latex", "img2latex"),
    },
    status="implemented",
    provenance="valores MEDIDOS por este banco; los motores ausentes se reportan `skipped` (no se citan como referencia)",
)

# --- adaptadores de las alternativas LaTeX -----------------------------------

def _pix2tex_backend() -> Callable[[Image.Image], OcrOutput]:
    """`pix2tex` (`LaTeX-OCR`): API pública `from pix2tex.cli import LatexOCR`."""
    try:
        from pix2tex.cli import LatexOCR
    except ImportError as exc:
        raise ProviderUnavailable("pip install pix2tex") from exc

    model = LatexOCR()

    def run(image: Image.Image) -> OcrOutput:
        data = Image.open(io.BytesIO(_image_bytes(image)))
        start = time.perf_counter()
        text = model(data)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return OcrOutput(text=str(text or ""), elapsed_ms=elapsed_ms, extra={"engine": "pix2tex"})

    return run


# Motores LaTeX aún no integrados: `skipped` con motivo honesto (nunca `ok`).
EXTRA_FACTORIES = {
    "pix2tex": _pix2tex_backend,
    "texify": unavailable_factory("texify", "texify"),
    "nougat": unavailable_factory("nougat", "nougat-ocr"),
    "unimernet": unavailable_factory("unimernet", "unimernet (github.com/opendatalab/UniMERNet)"),
    "pix2text": unavailable_factory("pix2text", "pix2text"),
    "texteller": unavailable_factory("texteller", "texteller"),
    "img2latex": unavailable_factory("img2latex", "img2latex"),
}
EXTRA_MODELS = {name: (name, "default") for name in EXTRA_FACTORIES}

# Orden por defecto: motores LaTeX de pyocrust, luego alternativas LaTeX reales,
# y al final los controles de OCR de texto (etiquetados como tales).
DEFAULT_BACKENDS = (
    "pyocrust_formulanet,pyocrust_formula,pyocrust_indra,"
    "pix2tex,texify,nougat,unimernet,pix2text,texteller,img2latex,"
    "easyocr,rapidocr"
)


def main(argv: Sequence[str] | None = None) -> int:
    args = common_argparser(SPEC.feature, SPEC.summary).parse_args(argv)
    dataset = args.dataset or "omnidocbench_formula"
    samples = load_dataset(dataset, limit=args.limit, split=args.split)
    print(f"[formula] dataset={dataset} muestras={len(samples)}")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_dir = feature_out_dir(args.output_dir, SPEC) / timestamp
    run_backends(
        samples,
        [b.strip() for b in (args.backends or DEFAULT_BACKENDS).split(",") if b.strip()],
        dataset, out_dir, timestamp,
        warmup=args.warmup, repeats=args.repeats, device=args.device,
        task_override="formula", feature=SPEC.feature,
        factories=EXTRA_FACTORIES, models=EXTRA_MODELS, dump_outputs=args.dump_outputs,
    )
    print(f"\n[formula] resultados en {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
