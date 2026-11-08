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
        "PaddleOCR SLANet": ("paddleocr", "paddleocr paddlepaddle"),
        "docling TableFormer": ("docling", "docling (venv aislado)"),
        "paddleocr PP-Structure": ("paddleocr", "paddleocr paddlepaddle"),
    },
    status="implemented",
    note="El modelo emite estructura sin texto de celda: se puntúa la gramática (TEDS-S), no el contenido.",
    provenance="valores MEDIDOS por este banco (TEDS de estructura sobre el HTML anotado de OmniDocBench)",
)

# Orden: reconocedor especializado de `pyocrust`, las alternativas externas
# reales (TATR, SLANet de PaddleOCR, TableFormer de docling) y, como fila
# adicional, el **pipeline completo** (`pyocrust_structure`, `pp_structurev3`),
# cuya tabla va embebida en su Markdown — la compara cruzada contra el
# especialista con el MISMO GT de tabla. Ver `t_8b618f13`.
DEFAULT_BACKENDS = "pyocrust_table,tatr,paddleocr_slanet,docling_tableformer,pyocrust_structure"


def _table_html(text: str) -> str:
    """HTML de tabla que emite un motor: el `<table>` embebido o el texto tal cual.

    El reconocedor de tabla especializado (`pyocrust_table`, TATR, SLANet) emite
    **solo** la gramática (`<tr>/<td>`) sin envoltorio `<table>`, así que su `text`
    ya es la tabla. El **pipeline completo** (`pyocrust_structure`) y **docling
    TableFormer** devuelven HTML con la tabla envuelta (`<table …>…</table>`,
    TableFormer incluso con `<html><body>`); se extrae el bloque `<table>`. Sin
    tabla alguna (ni `<table>` ni `<tr>`) devuelve vacío: TEDS no evaluable, no un
    0.0 espurio.

    Normaliza `<th>` -> `<td>`: TableFormer etiqueta la fila de cabecera como
    `<th>` mientras el GT de OmniDocBench y los demás motores usan `<td>`. Para el
    TEDS-S (filas/columnas/fusiones) `th` y `td` son la MISMA celda; sin
    normalizar se penalizaría a TableFormer por nombrar mejor la cabecera.
    """
    text = text.replace("<th", "<td").replace("</th>", "</td>")
    if "<table" in text:
        parts, start = [], text.find("<table")
        while start != -1:
            end = text.find("</table>", start)
            if end == -1:
                break
            parts.append(text[start:end + len("</table>")])
            start = text.find("<table", end)
        if parts:
            return "\n".join(parts)
    # Gramática suelta del modelo especializado (`<tr>` sin envoltorio).
    return text if "<tr" in text else ""


def score_table(sample: Sample, output: OcrOutput) -> dict:
    """TEDS de estructura entre el `html` anotado y el que reconstruye el motor.

    Valen tanto el reconocedor especializado (gramática directa) como el pipeline
    completo (tabla embebida en su Markdown). Si el motor no emite tabla alguna,
    la métrica queda **no evaluada** (`""`), no un `0.0` espurio.
    """
    if not sample.gt_html:
        # Sin GT de tabla la métrica queda **no evaluada** (""), nunca un 0.0.
        return {"table_teds": ""}
    html = _table_html(output.text)
    if not html:
        return {"table_teds": ""}
    return {"table_teds": round(table_teds(sample.gt_html, html), 4)}


def main(argv: Sequence[str] | None = None) -> int:
    args = common_argparser(SPEC.feature, SPEC.summary).parse_args(argv)
    dataset = args.dataset or "omnidocbench_table"
    samples = load_dataset(dataset, limit=args.limit, split=args.split)
    print(f"[table] dataset={dataset} muestras={len(samples)}")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_dir = feature_out_dir(args.output_dir, SPEC) / timestamp
    run_backends(
        samples,
        [b.strip() for b in (args.backends or DEFAULT_BACKENDS).split(",") if b.strip()],
        dataset, out_dir, timestamp,
        warmup=args.warmup, repeats=args.repeats, device=args.device,
        task_override="table", feature=SPEC.feature, scorer=score_table,
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
    # Pipeline completo: su `text` es Markdown de página con la tabla embebida;
    # `score_table` extrae el `<table>…</table>` y puntúa contra el mismo GT.
    pipeline = OcrOutput("hola\n<div><table border=\"1\"><tr><td>a</td><td>b</td></tr></table></div>\nfin")
    assert score_table(sample, pipeline) == {"table_teds": 1.0}
    # Motor que no emite tabla alguna -> no evaluada (""), nunca un 0.0 espurio.
    assert score_table(sample, OcrOutput("sin tabla")) == {"table_teds": ""}
    # `<th>` (cabecera de docling TableFormer) se normaliza a `<td>`: misma celda
    # en el TEDS-S, así que no penaliza la etiqueta de cabecera.
    th = OcrOutput("<html><body><table><tr><th>a</th><th>b</th></tr></table></body></html>")
    assert score_table(sample, th) == {"table_teds": 1.0}
    print("features.table self-check OK")


if __name__ == "__main__":  # pragma: no cover - ejecución manual
    if "--self-check" in sys.argv:
        _self_check()
    else:
        raise SystemExit(main())
