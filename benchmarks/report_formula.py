#!/usr/bin/env python
"""Reporte de la comparativa de OCR de **formulas** (`task_type=formula`).

Lee una run de `benchmarks/results/` con filas `task_type=formula` —generadas por
`run_benchmarks.py --dataset omnidocbench_formula`— y escribe
`benchmarks/FORMULA_REPORT.md`.

Dos familias de metrica, para separar el artefacto de notacion de la correccion real:

* **Cruda** (texto tal cual): `LaTeX exacto` (`exact_match`), `Similitud`
  (`1 - Levenshtein/max(|GT|,|pred|)`), `Levenshtein norm.`.
* **Normalizada** (forma canonica de LaTeX, `latex_metrics.py`): `LaTeX exacto norm.`
  (`latex_exact`), `Similitud norm.` (`latex_sim`), `F1 tokens LaTeX` (`latex_token_f1`).
  La forma canonica unifica espaciado, `\\left`/`\\right`, el entorno `array` frente a
  `matrix`, delimitadores (`\\lbrack` vs `[`) y alias de comandos (`\\le` vs `\\leq`).

No es equivalencia matematica (no hay CAS): normalizacion canonica + comparacion
superficial endurecida. Se documenta como tal.

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

OUT = Path(__file__).resolve().parent / "reports" / "formula" / "FORMULA_REPORT.md"
COLS = [
    ("n", "n", "{}"),
    ("exact_match", "LaTeX exacto ↑", "{:.3f}"),
    ("latex_exact", "LaTeX exacto norm. ↑", "{:.3f}"),
    ("similarity", "Similitud ↑", "{:.3f}"),
    ("latex_sim", "Similitud norm. ↑", "{:.3f}"),
    ("latex_token_f1", "F1 tokens LaTeX ↑", "{:.3f}"),
    ("lev_norm", "Levenshtein norm. ↓", "{:.3f}"),
    ("latex_any", "Salidas con LaTeX ↑", "{:.0%}"),
    ("mean_ms", "ms/fórmula ↓", "{:.0f}"),
    ("p95_ms", "p95 ms ↓", "{:.0f}"),
]
HIGHER_BETTER = {"exact_match", "latex_exact", "similarity", "latex_sim",
                 "latex_token_f1", "latex_any"}
LATEX_CMD = re.compile(r"\\[A-Za-z]+")
LATEX_BLOCK = re.compile(r"\\begin\{")
FORMULANET_PREFIX = "pyocrust_formulanet"


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


def _num(value) -> float | None:
    """Coacciona a float; `None`/`''`/texto no numerico -> `None` (no se inventa 0)."""
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _mean(rows: Sequence[dict], key: str) -> float | None:
    """Media de `key` sobre las filas que la traen medida (si no hay, `None`)."""
    values = [v for v in (_num(row.get(key)) for row in rows) if v is not None]
    return statistics.fmean(values) if values else None


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
            # Metricas normalizadas: `None` si la run es anterior a `latex_metrics`
            # o si el motor no las trae; el reporte imprime `N/A`.
            "latex_exact": _mean(rs, "latex_exact"),
            "latex_sim": _mean(rs, "latex_sim"),
            "latex_token_f1": _mean(rs, "latex_token_f1"),
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


def _fmt(value, fmt: str) -> str:
    return fmt.format(value) if value is not None else "N/A"


def _variant_table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> list[str]:
    return ["| " + " | ".join(headers) + " |",
            "| " + " | ".join("---:" for _ in headers) + " |"] + \
           ["| " + " | ".join(cells) + " |" for cells in rows]


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
    for key, _label, _fmt_ in COLS:
        if key == "n":
            continue
        values = [(d[key], b) for b, d in report.items() if d.get(key) is not None]
        if len(values) > 1 and len({v for v, _ in values}) > 1:
            best[key] = (max if key in HIGHER_BETTER else min)(values)[1]

    labels = [label for _k, label, _f in COLS]
    lines = [
        "# Comparativa de OCR de fórmulas — `pyocrust` vs otros motores (métrica normalizada)",
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
            text = _fmt(data.get(key), fmt)
            if best.get(key) == backend:
                text = f"**{text}**"
            cells.append(text)
        lines.append(f"| {backend} | " + " | ".join(cells) + " |")
    lines += [
        "",
        "> **Dos familias de métrica.** Las columnas *sin* `norm.` puntúan el texto LaTeX tal "
        "cual; las `norm.` puntúan la **forma canónica** (`latex_metrics.py`: espaciado, "
        "`\\left`/`\\right`, `array`→`matrix`, `\\lbrack`→`[`, alias de comandos). `LaTeX "
        "exacto` exige coincidencia carácter a carácter del LaTeX normalizado (0 en todos). "
        "`Similitud = 1 - Levenshtein/max(|GT|,|pred|)`. `Salidas con LaTeX` es la fracción de "
        "salidas (`<backend>.outputs.json`) que contienen algún comando LaTeX (`\\palabra`).",
    ]

    def by_prefix(prefix: str) -> dict | None:
        for backend, data in report.items():
            if backend.startswith(prefix + " "):
                return data
        return None

    emit = {b.split(" ", 1)[0]: (d.get("latex_any") or 0.0) for b, d in report.items()}
    order = sorted(emit, key=lambda key: -emit[key])
    n_formulas = max(d["n"] for d in report.values())
    fn, pf = by_prefix(FORMULANET_PREFIX), by_prefix("pyocrust_formula")
    indra = by_prefix("pyocrust_indra")

    lines += ["", "## Lectura honesta", ""]
    if all(d["exact_match"] == 0 for d in report.values()):
        lines.append(
            f"* **Ningún motor reproduce el LaTeX anotado exactamente**: `LaTeX exacto = 0.000` "
            f"sobre {n_formulas} fórmulas en los {len(report)} motores."
        )
    if fn and fn.get("latex_exact") is not None:
        lines.append(
            "* **La normalización sube la similitud pero NO cierra el `exacto`**: en "
            f"`pyocrust_formulanet` la `Similitud` pasa de {fn['similarity']:.3f} (cruda) a "
            f"{fn['latex_sim']:.3f} (norm.) y el `F1 tokens` es {fn['latex_token_f1']:.3f}, pero "
            f"`LaTeX exacto norm.` sigue en {fn['latex_exact']:.3f}. La brecha que queda es real, "
            "no solo de espaciado: el modelo emite comandos de **fuente** (`\\mathcal`, `\\mathbf`), "
            "**agrupa** con llaves de más (`{a}_{11}`) y a veces añade **columnas vacías** de más "
            "en el `matrix`. La métrica normalizada mide eso, no lo esconde."
        )
    lines.append(
        "* **Solo los motores de fórmulas de `pyocrust` producen LaTeX**: `Salidas con LaTeX` = "
        + ", ".join(f"`{k}` {emit[k]:.0%}" for k in order if emit[k] > 0)
        + ", frente a "
        + ", ".join(f"`{k}` {emit[k]:.0%}" for k in order if emit[k] == 0)
        + " de los OCR de texto, que devuelven los símbolos sueltos y no LaTeX."
    )
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
            f"(F1 tokens {_fmt(fn.get('latex_token_f1'), '{:.3f}')} vs "
            f"{_fmt(pf.get('latex_token_f1'), '{:.3f}')})."
        )
    block_emit = {b.split(" ", 1)[0]: (d.get("latex_block") or 0.0) for b, d in report.items()}
    latex_motors = [b for b in report if block_emit.get(b.split(" ", 1)[0], 0.0) > 0]
    if latex_motors:
        fastest = min((report[b]["mean_ms"], b.split(" ", 1)[0]) for b in latex_motors)
        slowest = max((report[b]["mean_ms"], b.split(" ", 1)[0]) for b in latex_motors)
        lines.append(
            f"* **Velocidad**: entre los motores que emiten LaTeX de fórmula, `{fastest[1]}` es el "
            f"más rápido ({fastest[0]:.0f} ms/fórmula), ~{slowest[0] / fastest[0]:.1f}× que "
            f"`{slowest[1]}` ({slowest[0]:.0f} ms). Un modelo a la vez, CPU."
        )

    # --- Comparativa de variantes PP-FormulaNet (mismo adaptador, distinto .onnx) ---
    variants = sorted(b for b in report if b.split(" ", 1)[0].startswith(FORMULANET_PREFIX))
    if variants:
        lines += [
            "",
            "## Comparativa de variantes PP-FormulaNet",
            "",
            "Todas comparten `FormulaModelKind::PPFormulaNet` en oar-ocr: el adaptador de "
            "`formula_recognition` es el mismo y solo cambia el `.onnx` (registro ModelScope "
            "`greatv/oar-ocr`). Aísla el tamaño/entrenamiento del modelo, no el pipeline. "
            "Calidad sobre la **forma canónica**:",
            "",
        ]
        headers = ["Variante (`.onnx`)", "n", "LaTeX exacto norm. ↑", "Similitud norm. ↑",
                   "F1 tokens LaTeX ↑", "Salidas con LaTeX ↑", "ms/fórmula ↓"]
        rows_cells = []
        for backend in variants:
            d = report[backend]
            rows_cells.append([
                f"`{backend.split(' (', 1)[0]}`", str(d["n"]),
                _fmt(d.get("latex_exact"), "{:.3f}"), _fmt(d.get("latex_sim"), "{:.3f}"),
                _fmt(d.get("latex_token_f1"), "{:.3f}"), _fmt(d.get("latex_any"), "{:.0%}"),
                _fmt(d.get("mean_ms"), "{:.0f}"),
            ])
        lines += _variant_table(headers, rows_cells)
        scored = [(report[b].get("latex_token_f1"), b.split(" ", 1)[0]) for b in variants
                  if report[b].get("latex_token_f1") is not None]
        timed = [(report[b].get("mean_ms"), b.split(" ", 1)[0]) for b in variants
                 if report[b].get("mean_ms") is not None]
        extra = []
        if len(scored) > 1 and len({v for v, _ in scored}) > 1:
            bestf1 = max(scored)
            extra.append(f"mejor `F1 tokens` = `{bestf1[1]}` ({bestf1[0]:.3f})")
        if len(timed) > 1 and len({v for v, _ in timed}) > 1:
            fastest = min(timed)
            extra.append(f"más rápida = `{fastest[1]}` ({fastest[0]:.0f} ms/fórmula)")
        if extra:
            lines.append("")
            lines.append("* **Variantes**: " + "; ".join(extra) + ". Un modelo a la vez, CPU.")
        missing = [b for b in ("l", "pluss", "plusm", "plusl")
                   if f"{FORMULANET_PREFIX}_{b}" in skipped]
        if missing:
            lines.append("")
            lines.append(
                "* Variantes de `pyocrust_formulanet` **no medidas** (fichero `.onnx` no "
                "descargado; no se inventan números): "
                + ", ".join(f"`pyocrust_formulanet_{m}`" for m in missing) + "."
            )

    # --- Referencia externa: oar-ocr solo mide tiempos ---
    lines += [
        "",
        "## Referencia externa: el benchmark de `oar-ocr` solo mide **tiempos**",
        "",
        "El repo original `GreatV/oar-ocr` trae `oar-bench` (crate no publicado "
        "`oar-ocr-bench`, doc. en `docs/benchmarking.md`). Mide el pipeline completo por "
        "página — `load_ms`, `latency_ms` (media/p50/p95), `pages_per_second`, "
        "`output_chars_per_second` (solo VL), `host_peak_bytes` y picos de GPU con NVML — y "
        "**compara dos runs** con un umbral de regresión en latencia/throughput.",
        "",
        "**No calcula ninguna métrica de calidad.** El propio `docs/benchmarking.md` delega la "
        "precisión en herramientas **externas**: `run --save-outputs predictions` y luego el "
        "scorer oficial de **OmniDocBench** (`pdf_validation.py`) o de **olmOCR** "
        "(`olmocr.bench`). Es decir, `oar-ocr` —y con él el backend de `pyocrust`— **no "
        "publica** comparativa de calidad de fórmulas: las columnas `LaTeX exacto norm.`, "
        "`Similitud norm.` y `F1 tokens LaTeX` de este reporte son métrica **nuestra**, medida "
        "sobre el GT de OmniDocBench.",
    ]

    lines += [
        "",
        "## Limitaciones",
        "",
        "* La unidad es el **recorte** del bloque `equation_isolated` (`poly` anotado, +4 px de "
        "margen). No mide el pipeline a nivel de página ni la detección de la fórmula en la página.",
        "* El GT es el **LaTeX anotado** del bloque. Su notación (`array`, `\\left\\lbrack`) no "
        "coincide con la del modelo, así que `LaTeX exacto = 0` no significa «no reconoce».",
        "* La métrica **normalizada NO es equivalencia matemática**: unifica notación (espaciado, "
        "`array`/`matrix`, `\\left[`/`[`, alias) y compara tokens, pero no evalúa la expresión con "
        "un CAS. Las diferencias de **fuente** (`\\mathcal`, `\\mathbf`) y de **agrupación de "
        "llaves** se conservan a propósito (cambian el significado); por eso `LaTeX exacto norm.` "
        "queda por debajo de `Similitud norm.`.",
        "* Una sola run, `repeats=1`; el eje de proveedor se registra por fila "
        "(`device_requested` / `provider_effective`). `--device gpu` se mide con "
        "`pyocrust device=auto` (DirectML en este host) y sólo cuenta como GPU si el motor "
        "CONFIRMA el acelerador; un fallback CPU queda `skipped`, nunca etiquetado como GPU.",
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
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(md + "\n", encoding="utf-8")
    print(md)
    print(f"\n[report] escrito en {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
