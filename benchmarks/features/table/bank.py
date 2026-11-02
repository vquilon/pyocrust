#!/usr/bin/env python
"""Banco de la feature **table** (estructura de tabla).

Igual que los componentes de tabla de `oar-ocr`: clasificación (hay/no hay),
estructura (filas/columnas/fusiones) y detección de celdas. Este banco mide la
**estructura**: TEDS de estructura = `1 - editDist(etiquetas HTML) / max(len)`.

Dataset por defecto: `omnidocbench_table` — cada bloque `table` anotado se
recorta por su `poly` y su `html` anotado es el GT. El modelo de estructura emite
solo la gramática (`<tr>`, `<td>`, `</tr>`) y **no** el texto de las celdas, así
que la comparación honesta es sobre la secuencia de etiquetas (la variante
*TEDS-S* de la literatura): mide filas, columnas y fusiones, no el OCR de dentro.
El TEDS de árbol completo exigiría el texto de celda, que aquí no se predice.

Provenance: todo número que salga de aquí es **`medido`**; el `summary.json` de la
run guarda comando, dataset, `n`, `warmup`, `repeats`, dispositivo y fecha.

Uso:
    .venv/Scripts/python.exe benchmarks/features/table/bank.py --limit 8
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

# Ejecutable como script (`python benchmarks/features/table/bank.py`).
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from datetime import datetime

from common import OcrOutput, Sample, load_dataset, run_backends
from common.metrics import table_teds
from features._base import FeatureSpec, common_argparser, feature_out_dir

SPEC = FeatureSpec(
    feature="table",
    summary="Tablas: clasificación (hay/no hay), estructura (filas/columnas) y detección de celdas.",
    pyocrust_task="table_structure_recognition (TaskPredictor; SLANet/SLANeXt)",
    metric="TEDS de estructura: 1 - editDist(etiquetas HTML) / max(longitudes)",
    dataset="omnidocbench_table: recorte del bloque `table` anotado + su `html` como GT",
    alternatives={
        "table-transformer (TATR)": ("transformers", "transformers + table-transformer"),
        "docling": ("docling", "docling"),
        "paddleocr PP-Structure": ("paddleocr", "paddleocr paddlepaddle"),
    },
    status="implemented",
    note="El modelo emite estructura sin texto de celda: se puntúa la gramática (TEDS-S), no el contenido.",
    provenance="valores MEDIDOS por este banco (TEDS de estructura sobre el HTML anotado de OmniDocBench)",
)


def score_table(sample: Sample, output: OcrOutput) -> dict:
    """TEDS de estructura entre el `html` anotado y el que reconstruye el motor."""
    if not sample.gt_html:
        # Sin GT de tabla la métrica queda **no evaluada** (""), nunca un 0.0.
        return {"table_teds": ""}
    return {"table_teds": round(table_teds(sample.gt_html, output.text), 4)}


def main(argv: Sequence[str] | None = None) -> int:
    args = common_argparser(SPEC.feature, SPEC.summary).parse_args(argv)
    dataset = args.dataset or "omnidocbench_table"
    samples = load_dataset(dataset, limit=args.limit, split=args.split)
    print(f"[table] dataset={dataset} muestras={len(samples)}")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_dir = feature_out_dir(args.output_dir, SPEC) / timestamp
    run_backends(
        samples,
        [b.strip() for b in (args.backends or "pyocrust_table").split(",") if b.strip()],
        dataset, out_dir, timestamp,
        warmup=args.warmup, repeats=args.repeats, device=args.device,
        feature=SPEC.feature, scorer=score_table,
    )
    print(f"\n[table] resultados en {out_dir}")
    return 0


def _self_check() -> None:
    """La métrica ignora el texto de celda y los envoltorios, y respeta filas."""
    from PIL import Image

    sample = Sample("t", Image.new("RGB", (4, 4)), "",
                    gt_html="<table><tr><td>a</td><td>b</td></tr></table>")
    same = OcrOutput("<tr><td></td><td></td></tr>")
    assert score_table(sample, same) == {"table_teds": 1.0}
    fewer = OcrOutput("<tr><td></td></tr>")
    assert score_table(sample, fewer)["table_teds"] < 1.0
    no_gt = Sample("u", Image.new("RGB", (4, 4)), "", gt_html=None)
    assert score_table(no_gt, same) == {"table_teds": ""}
    print("features.table self-check OK")


if __name__ == "__main__":  # pragma: no cover - ejecución manual
    if "--self-check" in sys.argv:
        _self_check()
    else:
        raise SystemExit(main())
