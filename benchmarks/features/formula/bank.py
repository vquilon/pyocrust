#!/usr/bin/env python
"""Banco de la feature **formula** (fórmula → LaTeX).

Igual que el componente `formula` de `oar-ocr`. Los motores de OCR de texto
(`easyocr`, `rapidocr`, `tesseract`) **no** entran: no tienen módulo de
fórmulas→LaTeX y no son equiparables contra un GT LaTeX. Este banco compara
únicamente motores que **sí** emiten LaTeX. La unidad es cada fórmula anotada
(bloque `equation_isolated` de OmniDocBench, recorte por `poly` + GT de su
`latex`), la misma entrada PNG para todos.

Métrica (sobre la **forma canónica** de LaTeX, `latex_metrics.py`):
`latex_exact` (coincidencia normalizada), `latex_sim` (similitud) y
`latex_token_f1` (multiconjunto de comandos/símbolos). Más `ms/fórmula` y la
fracción de salidas con LaTeX, que separa quien **emite LaTeX** de quien solo
repite símbolos como texto.

Provenance: números **`medidos`** por este banco. Las alternativas comparadas son
reales; la disponibilidad es real (las ausentes quedan `skipped` con su
`pip install`). Los OCR de texto quedan fuera por diseño: ver
`FORMULA_BACKENDS_EXCLUDED` en `common/runner.py`.

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

from common import OcrOutput, ProviderUnavailable, Sample, load_dataset, run_backends
from common.metrics import latex_exact, latex_similarity, latex_token_f1
from common.runner import _image_bytes, _paddle_latex_ocr_backend
from features._base import FeatureSpec, common_argparser, feature_out_dir, unavailable_factory

SPEC = FeatureSpec(
    feature="formula",
    summary="Fórmula de imagen → LaTeX, comparada contra motores que SÍ producen LaTeX.",
    pyocrust_task="formula_recognition (TaskPredictor, PP-FormulaNet) + pipeline pp_structurev3 e Indra",
    metric="latex_exact / latex_sim / latex_token_f1 (forma canónica) + ms/fórmula y cobertura LaTeX",
    dataset="omnidocbench_formula (recorte por bloque `equation_isolated` + GT LaTeX)",
    alternatives={
        "pix2tex (LaTeX-OCR)": ("pix2tex", "pix2tex"),
        "UniMERNet": ("unimernet", "unimernet (github.com/opendatalab/UniMERNet)"),
        "texify (surya_latex_ocr)": ("texify", "texify"),
        "nougat": ("nougat", "nougat-ocr"),
        "Pix2Text": ("pix2text", "pix2text"),
        "TexTeller": ("texteller", "texteller"),
        "img2latex": ("img2latex", "img2latex"),
    },
    status="implemented",
    provenance="valores MEDIDOS por este banco; los motores ausentes se reportan `skipped` (no se citan como referencia)",
)

# --- adaptadores de las alternativas LaTeX -----------------------------------

def _pix2tex_backend(device: str = "cpu") -> Callable[[Image.Image], OcrOutput]:
    """`pix2tex` (`LaTeX-OCR`): API pública `from pix2tex.cli import LatexOCR`.

    Proveedor **efectivo CPU**: `LatexOCR()` trae `no_cuda=True` por defecto, así
    que resuelve `self.args.device='cpu'` aunque hubiera GPU. La fila se mide en
    CPU (device_requested=cpu == provider real); nunca se etiqueta como GPU.
    """
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
        return OcrOutput(text=str(text or ""), elapsed_ms=elapsed_ms,
                         extra={"engine": "pix2tex", "provider_effective": "cpu"})

    return run


# Motores LaTeX aún no integrados: `skipped` con motivo honesto (nunca `ok`).
# NO entran en `DEFAULT_BACKENDS`: sin adaptador no producen filas y anunciarlas en
# el default dejaba el informe con motores que nunca aparecen (criterio de la tarjeta).
# `unimernet` SÍ se integró (venv aislado + subproceso) y ya no vive aquí: va en
# `PROVIDERS` del runner y sí produce filas.
EXTRA_FACTORIES = {
    "pix2tex": _pix2tex_backend,
    "paddle_latex_ocr": _paddle_latex_ocr_backend,
    "texify": unavailable_factory("texify", "texify"),
    "nougat": unavailable_factory("nougat", "nougat-ocr"),
    # P2T no se fuerza a propósito: `pip install pix2text` degrada `transformers`
    # y `huggingface_hub` y cambia `opencv-python-headless` por `opencv-python`
    # en el venv donde ya corren easyocr/rapidocr/datasets. La fila queda
    # `skipped` con el motivo, nunca medida a medias.
    "pix2text": unavailable_factory(
        "pix2text",
        "pix2text (no forzado: degrada transformers/huggingface_hub y "
        "cambia opencv-python-headless→opencv-python)",
    ),
    "texteller": unavailable_factory("texteller", "texteller"),
    # `img2latex` NO existe en PyPI (verificado con `pip index versions`): es un
    # nombre fantasma, no una alternativa instalable. Queda `skipped` con el motivo.
    "img2latex": unavailable_factory("img2latex", "img2latex (no publicado en PyPI)"),
}
EXTRA_MODELS = {name: (name, "default") for name in EXTRA_FACTORIES}

# --- puntuación: LaTeX **aislado** del motor, contra el GT anotado -----------

def _formula_latex(output: OcrOutput) -> str:
    """LaTeX **aislado** que emite un motor de fórmulas (no el Markdown de página).

    El banco recibe un recorte de fórmula por muestra, pero el **pipeline
    completo** (`pyocrust_structure`) devuelve el Markdown de la "página" entera:
    su LaTeX va en `extra["formulas"]` (y en el `text` de cada elemento
    `formula`). Se prioriza esa salida por sub-tarea; si el motor no expone
    fórmulas separadas, se usa `text` tal cual —los motores LaTeX puros (pix2tex,
    PP-FormulaNet) solo emiten el LaTeX en `text`—. Sin LaTeX -> `""`: la métrica
    queda **no evaluada** con motivo honesto, no un `0.0` espurio.
    """
    formulas = [str(f) for f in (output.extra.get("formulas") or []) if str(f).strip()]
    if formulas:
        return "\n".join(formulas)
    text = str(output.text or "").strip()
    # Markdown de página (con tabla o cabeceras) sin fórmulas aisladas: no es LaTeX.
    if "<table" in text or "##" in text or "<div" in text:
        return ""
    return text


def score_formula(sample: Sample, output: OcrOutput) -> dict:
    """`latex_*` sobre el LaTeX **aislado** del motor, contra el GT anotado.

    Sustituye la puntuación por defecto del runner (que mide `output.text` crudo,
    el Markdown de página en el pipeline completo). Así todos los motores se
    comparan por su salida de fórmula. Sin GT LaTeX o sin LaTeX emitido la
    métrica queda **no evaluada** (`""`), nunca un `0.0` espurio.
    """
    gt = str((sample.gt_by_task or {}).get("formula", sample.gt_text) or "")
    pred = _formula_latex(output)
    if not gt.strip() or not pred:
        return {"latex_exact": "", "latex_sim": "", "latex_token_f1": ""}
    return {
        "latex_exact": latex_exact(gt, pred),
        "latex_sim": round(latex_similarity(gt, pred), 4),
        "latex_token_f1": round(latex_token_f1(gt, pred), 4),
    }


# Orden por defecto: solo motores con adaptador real que producen filas. Las
# alternativas anunciadas sin adaptador ni pesos (texify/nougat/pix2text/texteller/
# img2latex) se piden de forma explícita y salen como `skipped` con su motivo
# —anunciarlas en el default dejaba el informe con motores que nunca aparecen—.
# `pyocrust_structure` cierra la lista: el **pipeline completo** medido en la
# tarea de fórmula (compara cruzada; su LaTeX aislado sale de `extra["formulas"]`).
DEFAULT_BACKENDS = (
    "pyocrust_formulanet,pyocrust_formula,pyocrust_indra,"
    "paddle_latex_ocr,pix2tex,unimernet,"
    "pyocrust_structure"
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
        scorer=score_formula,
    )
    print(f"\n[formula] resultados en {out_dir}")
    return 0


def _self_check() -> None:
    """Motor LaTeX puro y pipeline completo se puntúan por su LaTeX aislado."""
    from PIL import Image

    image = Image.new("RGB", (4, 4))
    sample = Sample("f", image, "", gt_by_task={"formula": r"x^2"})
    # Motor LaTeX puro: el LaTeX va en `text`.
    pure = OcrOutput(r"x^2")
    assert score_formula(sample, pure)["latex_exact"] == 1.0
    assert score_formula(sample, pure)["latex_sim"] == 1.0
    # Pipeline completo: su `text` es Markdown de página; el LaTeX aislado sale de
    # `extra["formulas"]` (prioritario). Se puntúa por esa salida, no por el Markdown.
    pipeline = OcrOutput("## titulo\n<div>algo</div>", extra={"formulas": [r"x^2"]})
    assert score_formula(sample, pipeline)["latex_exact"] == 1.0
    # Sin fórmulas aisladas y con Markdown de página -> no evaluada (""), no 0.0.
    no_formula = OcrOutput("## titulo\n<div>algo</div>")
    assert score_formula(sample, no_formula) == {
        "latex_exact": "", "latex_sim": "", "latex_token_f1": ""}
    # Sin GT LaTeX la métrica queda no evaluada, nunca un 0.0.
    bare = Sample("g", image, "")
    assert score_formula(bare, pure)["latex_sim"] == ""
    print("features.formula self-check OK")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        _self_check()
    else:
        raise SystemExit(main())
