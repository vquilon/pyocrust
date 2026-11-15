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

import re
import sys
from pathlib import Path
from typing import Sequence

# Ejecutable como script (`python benchmarks/features/table/bank.py`).
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from datetime import datetime

from common import OcrOutput, Sample, load_dataset, run_backends
from common.metrics import table_teds
from features._base import FeatureSpec, common_argparser, feature_run_dir, feature_out_dir

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
DEFAULT_BACKENDS = ("pyocrust_table,pyocrust_table_slanet,paddleocr_slanext_wired,"
                    "paddleocr_slanet,tatr,docling_tableformer,pyocrust_structure")


_PIPE_SEP_CELL = re.compile(r"^:?-{2,}:?$")


def _pipe_cells(line: str) -> list[str] | None:
    """Celdas de una fila de tabla-pipe de Markdown (`a | b` o `| a | b |`).

    `None` si la línea no es una fila de tabla (sin `|`, una sola celda vacía) ni
    una fila separadora (`|---|---|`), que no aporta estructura.
    """
    if "|" not in line:
        return None
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    if len(cells) < 2 or not any(cells):
        return None
    if all(_PIPE_SEP_CELL.match(cell) for cell in cells):
        return None
    return cells


def _pipe_rows_to_html(lines: Sequence[str]) -> str:
    """Filas-pipe de Markdown -> gramática `<tr>/<td>` (lo que mide el TEDS-S)."""
    rows = [cells for line in lines if (cells := _pipe_cells(line))]
    if not rows:
        return ""
    return "<table>" + "".join(
        "<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>" for cells in rows
    ) + "</table>"


def _table_html(text: str) -> str:
    """HTML de tabla que emite un motor: HTML embebido o **tabla-pipe de Markdown**.

    El reconocedor de tabla especializado (`pyocrust_table`, TATR, SLANet) emite
    **solo** la gramática (`<tr>/<td>`) sin envoltorio `<table>`, así que su `text`
    ya es la tabla. El **pipeline completo** (`pyocrust_structure`) y **docling
    TableFormer** devuelven HTML con la tabla envuelta (`<table …>…</table>`,
    TableFormer incluso con `<html><body>`); se extrae el bloque `<table>`.

    Los **VLM documentales** solo emiten Markdown, y su tabla llega en dos formas:
    LightOnOCR la envuelve en `<table>` y PaddleOCR-VL la emite como **tabla-pipe**
    (`a | b`, sin `<table>`); LightOnOCR-3 0.8B incluso mete filas-pipe *dentro* del
    `<table>`. Ambas se convierten a la gramática `<tr>/<td>` que mide el TEDS-S
    (filas/columnas/fusiones), de modo que el VLM se puntúa por su estructura real
    y no por la ausencia de etiquetas. Glm-OCR emite celdas separadas por espacios
    (sin `|` ni `<table>`): no hay tabla que reconstruir -> `N/A`, nunca `0.0`.

    Normaliza `<th>` -> `<td>`: TableFormer etiqueta la cabecera como `<th>` y
    OmniDocBench/el resto usa `<td>`; para el TEDS-S son la MISMA celda.
    """
    text = text.replace("<th", "<td").replace("</th>", "</td>")
    if "<table" in text:
        parts, start = [], text.find("<table")
        while start != -1:
            end = text.find("</table>", start)
            if end == -1:
                break
            block = text[start:end + len("</table>")]
            # Un `<table>` sin `<tr>` (cuerpo en filas-pipe, LightOnOCR-3 0.8B) se
            # convierte a gramática; si no tiene pipes se deja tal cual.
            parts.append(block if "<tr" in block else (_pipe_rows_to_html(block.splitlines()) or block))
            start = text.find("<table", end)
        if parts:
            return "\n".join(parts)
    # Sin `<table>`: tabla-pipe suelta (PaddleOCR-VL). Se exige >=2 filas para no
    # tomar una línea con un `|` suelto por una tabla.
    pipe = _pipe_rows_to_html(text.splitlines())
    if pipe.count("<tr>") >= 2:
        return pipe
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
    out_dir, timestamp, resume = feature_run_dir(
        args.output_dir, SPEC, timestamp, args.variant, resume=args.resume,
        signature={"dataset": dataset, "n_samples": len(samples), "warmup": args.warmup,
                   "repeats": args.repeats, "device_requested": args.device},
    )
    run_backends(
        samples,
        [b.strip() for b in (args.backends or DEFAULT_BACKENDS).split(",") if b.strip()],
        dataset, out_dir, timestamp,
        warmup=args.warmup, repeats=args.repeats, device=args.device,
        variant=args.variant, resume=resume,
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
    # VLM solo-Markdown: tabla-pipe suelta (PaddleOCR-VL), sin `<table>`.
    gt2 = Sample("t2", Image.new("RGB", (4, 4)), "",
                 gt_html="<table><tr><td>a</td><td>b</td></tr><tr><td>c</td><td>d</td></tr></table>")
    assert score_table(gt2, OcrOutput("a | b\nc | d")) == {"table_teds": 1.0}
    # …y filas-pipe DENTRO de un `<table>` sin gramática (LightOnOCR-3 0.8B).
    inner = OcrOutput("<table>\n### Table - x\n| a | b |\n| --- | --- |\n| c | d |\n</table>")
    assert score_table(gt2, inner) == {"table_teds": 1.0}
    # Glm-OCR: celdas separadas por espacios (ni `|` ni `<table>`) -> N/A, nunca 0.0.
    assert score_table(gt2, OcrOutput("a b\nc d")) == {"table_teds": ""}
    # Una sola línea con un `|` suelto NO es una tabla -> N/A.
    assert score_table(gt2, OcrOutput("a | b")) == {"table_teds": ""}
    print("features.table self-check OK")


if __name__ == "__main__":  # pragma: no cover - ejecución manual
    if "--self-check" in sys.argv:
        _self_check()
    else:
        raise SystemExit(main())
