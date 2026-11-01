#!/usr/bin/env python
"""Reporte de la comparativa de OCR de **formulas** (`task_type=formula`).

Lee una run de `benchmarks/results/` con filas `task_type=formula` —generadas por
`run_benchmarks.py --dataset omnidocbench_formula`— y escribe
`benchmarks/FORMULA_REPORT.md`.

Metricas (por fila, media por motor):

* **LaTeX exacto** (`exact_match`): 1.0 si el LaTeX normalizado coincide caracter a
  caracter (minusculas, espacios colapsados).
* **Levenshtein normalizado** = distancia / `max(|GT|, |pred|)`: 0.0 identico, 1.0
  todo distinto. Se normaliza por el maximo y no por `|GT|` porque el motor de
  formulas emite LaTeX **mas largo** que la referencia (`array`->`matrix`, llaves de
  agrupacion); dividir por `|GT|` daria > 1 y una "similitud" negativa.
* **Similitud** = `1 - Levenshtein normalizado`.
* **Salidas con LaTeX** (`latex_any`): fraccion de salidas que contienen algun comando
  LaTeX (`\\palabra`), medida sobre `<backend>.outputs.json` de `--dump-outputs`.
* **ms/formula** y **p95**.

Uso:
    .venv/Scripts/python.exe benchmarks/report_formula.py [--run <ts>]
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Sequence

from report_benchmarks import RESULTS_DIR, load_rows

OUT = Path(__file__).resolve().parent / "FORMULA_REPORT.md"
COLS = [
    ("n", "n", "{}"),
    ("exact_match", "LaTeX exacto ↑", "{:.3f}"),
    ("similarity", "Similitud ↑", "{:.3f}"),
    ("lev_norm", "Levenshtein norm. ↓", "{:.3f}"),
    ("latex_any", "Salidas con LaTeX ↑", "{:.0%}"),
    ("mean_ms", "ms/fórmula ↓", "{:.0f}"),
    ("p95_ms", "p95 ms ↓", "{:.0f}"),
]
HIGHER_BETTER = {"exact_match", "similarity", "latex_any"}
LATEX_CMD = re.compile(r"\\[A-Za-z]+")
LATEX_BLOCK = re.compile(r"\\begin\{")


def latex_coverage(run: Path) -> dict[str, dict]:
    """Por backend: fraccion de salidas con >=1 comando LaTeX y con `\\begin{`.

    La salida cruda no cabe en el CSV de contrato fijo, asi que la escribe
    `run_benchmarks.py --dump-outputs` en `<backend>.outputs.json`.
    """
    coverage: dict[str, dict] = {}
    for path in run.glob("*.outputs.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        texts = [o.get("text", "") for o in payload.get("outputs", [])]
        if texts:
            coverage[payload["backend"]] = {
                "latex_any": sum(bool(LATEX_CMD.search(t)) for t in texts) / len(texts),
                "latex_block": sum(bool(LATEX_BLOCK.search(t)) for t in texts) / len(texts),
                "empty": sum(not t.strip() for t in texts) / len(texts),
            }
    return coverage


def summarize(rows: Sequence[dict]) -> dict[str, dict]:
    """Media por motor de las filas `task_type=formula` con `status=ok`."""
    group: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        if row.get("task_type") == "formula" and row.get("status") == "ok":
            variant = row.get("model_variant") or "default"
            group[f"{row['backend']} ({variant}; formula)"].append(row)

    summary: dict[str, dict] = {}
    for backend, rs in group.items():
        lev_norm, sims = [], []
        for row in rs:
            gt, pred = row.get("n_chars_gt") or 0.0, row.get("n_chars_pred") or 0.0
            # cer = levenshtein / |GT| -> se recupera la distancia entera.
            lev = round((row.get("cer") or 0.0) * gt)
            denom = max(gt, pred)
            norm = lev / denom if denom else 0.0
            lev_norm.append(norm)
            sims.append(1.0 - norm)
        times = sorted(row["elapsed_ms"] for row in rs)
        summary[backend] = {
            "n": len(rs),
            "exact_match": statistics.fmean(row["exact_match"] for row in rs),
            "lev_norm": statistics.fmean(lev_norm),
            "similarity": statistics.fmean(sims),
            "mean_ms": statistics.fmean(times),
            "p95_ms": times[min(len(times) - 1, math.ceil(0.95 * len(times)) - 1)],
        }
    return summary


def latest_run_with_formula() -> Path:
    """Run mas reciente que tenga al menos una fila `task_type=formula` medida."""
    for run_dir in sorted(RESULTS_DIR.glob("*/"), reverse=True):
        for csv_path in run_dir.glob("*.csv"):
            with csv_path.open(encoding="utf-8", newline="") as fh:
                if any(r.get("task_type") == "formula" and r.get("status") == "ok"
                       for r in csv.DictReader(fh)):
                    return run_dir
    raise SystemExit("no hay ninguna run con filas task_type=formula medidas")


def build(run: Path) -> str:
    report = summarize(load_rows(run))
    if not report:
        raise SystemExit(f"{run} no tiene filas task_type=formula medidas")

    coverage = latex_coverage(run)
    for backend, data in report.items():
        data.update(coverage.get(backend.split(" ", 1)[0],
                                 {"latex_any": 0.0, "latex_block": 0.0, "empty": 0.0}))

    skipped: dict[str, str] = {}
    summary_path = run / "summary.json"
    if summary_path.exists():
        backends = json.loads(summary_path.read_text(encoding="utf-8")).get("backends", {})
        skipped = {b: m.get("reason", "") for b, m in backends.items() if m.get("status") == "skipped"}

    # marca de mejor por metrica (solo entre motores medidos y sin empates)
    best = {}
    for key, _label, _fmt in COLS:
        if key == "n":
            continue
        values = [(d[key], b) for b, d in report.items()]
        if len(values) > 1 and len({v for v, _ in values}) > 1:
            best[key] = (max if key in HIGHER_BETTER else min)(values)[1]

    labels = [label for _k, label, _f in COLS]
    lines = [
        "# Comparativa de OCR de fórmulas — `pyocrust` (pp-formulanet-s) vs otros motores",
        "",
        f"Run `benchmarks/results/{run.name}`. Dataset **`omnidocbench_formula`**: "
        "`opendatalab/OmniDocBench` v1.6, **una muestra por fórmula** (bloque "
        "`equation_isolated`): el adaptador recibe el **recorte** de la fórmula y el GT es "
        "el **LaTeX anotado** de ese bloque (sin los `$` de delimitador). Entrada idéntica "
        "(mismo recorte PNG) para todos los motores; un motor a la vez, CPU, `warmup=1`, "
        "`repeats=1`.",
        "",
        "| Motor (variante; tarea) | " + " | ".join(labels) + " |",
        "| :--- | " + " | ".join("---:" for _ in labels) + " |",
    ]
    for backend, data in sorted(report.items()):
        cells = []
        for key, _label, fmt in COLS:
            value = data.get(key)
            text = fmt.format(value) if value is not None else "N/A"
            if best.get(key) == backend:
                text = f"**{text}**"
            cells.append(text)
        lines.append(f"| {backend} | " + " | ".join(cells) + " |")
    lines += [
        "",
        "> `LaTeX exacto` exige coincidencia carácter a carácter del LaTeX normalizado "
        "(0 en todos: la notación del dataset —`\\begin{array}`, `\\left\\lbrack`— no coincide "
        "con la del modelo). `Similitud = 1 - Levenshtein/max(|GT|,|pred|)`. `Salidas con LaTeX` "
        "es la fracción de salidas (medida sobre `<backend>.outputs.json`) que contienen algún "
        "comando LaTeX (`\\palabra`): separa un motor que **emite LaTeX** de uno que solo repite "
        "los símbolos como texto.",
    ]

    def by_prefix(prefix: str) -> dict | None:
        for backend, data in report.items():
            if backend.startswith(prefix + " "):
                return data
        return None

    emit = {b.split(" ", 1)[0]: (d.get("latex_any") or 0.0) for b, d in report.items()}
    order = sorted(emit, key=lambda key: -emit[key])
    n_formulas = max(d["n"] for d in report.values())
    lines += ["", "## Lectura honesta", ""]
    if all(d["exact_match"] == 0 for d in report.values()):
        lines.append(
            f"* **Ningún motor reproduce el LaTeX anotado exactamente**: `LaTeX exacto = 0.000` "
            f"sobre {n_formulas} fórmulas en los {len(report)} motores."
        )
    lines.append(
        "* **Solo los motores de fórmulas de `pyocrust` producen LaTeX**: `Salidas con LaTeX` = "
        + ", ".join(f"`{k}` {emit[k]:.0%}" for k in order if emit[k] > 0)
        + ", frente a "
        + ", ".join(f"`{k}` {emit[k]:.0%}" for k in order if emit[k] == 0)
        + " de los OCR de texto, que devuelven los símbolos sueltos y no LaTeX."
    )
    fn, pf = by_prefix("pyocrust_formulanet"), by_prefix("pyocrust_formula")
    indra = by_prefix("pyocrust_indra")
    if indra and indra.get("latex_any"):
        lines.append(
            f"* **`pyocrust_indra` matiza**: su {indra['latex_any']:.0%} de salidas con LaTeX son "
            f"**símbolos inline** (`$x_{{2}}$`) dentro de tablas HTML; no emite entornos de bloque "
            f"(`\\begin{{}}` = {indra['latex_block']:.0%}), así que no produce LaTeX de fórmula."
        )
    if fn and pf:
        lines.append(
            "* **El cuello de botella es el detector de layout, no el modelo**: "
            f"`pyocrust_formula` (pp_structurev3 completo sobre el recorte) devuelve **salida vacía "
            f"en {round(pf['empty'] * pf['n'])}/{pf['n']}** recortes ({pf['empty']:.0%}); "
            f"`pyocrust_formulanet` (PP-FormulaNet-S directo, sin layout) no deja ninguna vacía "
            f"({round(fn['empty'] * fn['n'])}/{fn['n']}) y reconoce mejor "
            f"(Similitud {fn['similarity']:.3f} vs {pf['similarity']:.3f})."
        )
    block_emit = {b.split(" ", 1)[0]: (d.get("latex_block") or 0.0) for b, d in report.items()}
    latex_motors = [b for b in report if block_emit.get(b.split(" ", 1)[0], 0.0) > 0]
    if latex_motors:
        fastest = min((report[b]["mean_ms"], b.split(" ", 1)[0]) for b in latex_motors)
        slowest = max((report[b]["mean_ms"], b.split(" ", 1)[0]) for b in latex_motors)
        lines.append(
            f"* **Velocidad**: entre los motores que emiten LaTeX de fórmula, `{fastest[1]}` es el "
            f"más rápido ({fastest[0]:.0f} ms/fórmula), ~{slowest[0] / fastest[0]:.1f}× que "
            f"`{slowest[1]}` ({slowest[0]:.0f} ms, el pipeline completo). Un modelo a la vez, CPU."
        )
    lines.append(
        "* **La `Similitud` de caracteres no mide corrección matemática**: el motor de fórmulas "
        "emite LaTeX verboso (`\\begin{matrix}` frente a `\\begin{array}`, llaves de agrupación) y "
        "comparte con el GT la estructura, no los comandos exactos. Se reporta como se pidió; "
        "`Salidas con LaTeX` es la columna que sí separa quién produce LaTeX de quién no."
    )
    lines += [
        "",
        "## Limitaciones",
        "",
        "* La unidad es el **recorte** del bloque `equation_isolated` (`poly` anotado, +4 px de "
        "margen). No mide el pipeline a nivel de página ni la detección de la fórmula en la página.",
        "* El GT es el **LaTeX anotado** del bloque. Su notación (`array`, `\\left\\lbrack`) no "
        "coincide con la del modelo, así que `LaTeX exacto = 0` no significa «no reconoce».",
        "* Una sola run, `repeats=1`, **CPU**: los ms no llevan intervalo de confianza y "
        "`provider_effective = unverified` (no se instrumenta el provider real).",
        "* No hay métrica **semántica** (equivalencia matemática), solo superficial sobre el texto; "
        "un LaTeX distinto pero equivalente puntúa como error.",
    ]
    if skipped:
        lines += ["", "**Skipped** (modelo/entorno ausente, no un OCR malo):"]
        lines += [f"* `{b}` — {reason}" for b, reason in sorted(skipped.items())]
    lines.append("")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reporte de la comparativa de formulas")
    parser.add_argument("--run", type=Path, default=None, help="subcarpeta de results/")
    args = parser.parse_args(argv)
    run = args.run or latest_run_with_formula()
    md = build(run)
    OUT.write_text(md + "\n", encoding="utf-8")
    print(md)
    print(f"\n[report] escrito en {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
