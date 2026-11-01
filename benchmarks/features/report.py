#!/usr/bin/env python
"""Reporte **por feature** a partir de las runs de `benchmarks/results/<feature>/`.

Lee la run más reciente (o `--run`) de una feature y escribe
`benchmarks/features/<feature>/REPORT.md` con:

* **provenance** explícita (comando reproducible, dataset, `n`, `warmup`,
  `repeats`, dispositivo, fecha) — todo `medido`;
* la **comparativa** por motor (media de las métricas de la feature);
* los **`skipped`** con su motivo, explicados (nunca contados como ejecutados).

Uso:
    .venv/Scripts/python.exe benchmarks/features/report.py --feature text
    .venv/Scripts/python.exe benchmarks/features/report.py --all
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Sequence

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import BENCHMARKS_ROOT, module_available

RESULTS_DIR = BENCHMARKS_ROOT / "results"
FEATURES_DIR = Path(__file__).resolve().parent

# Columnas del reporte por feature: (clave, etiqueta, formato, ¿más es mejor?)
FEATURE_COLUMNS: dict[str, list[tuple[str, str, str, bool | None]]] = {
    "text": [
        ("n", "n", "{}", None),
        ("word_f1", "F1 palabra ↑", "{:.3f}", True),
        ("wer_ord", "WER ord. ↓", "{:.3f}", False),
        ("cer", "CER ↓", "{:.3f}", False),
        ("wer", "WER ↓", "{:.3f}", False),
        ("box_recall", "box recall ↑", "{:.3f}", True),
        ("box_iou_mean", "IoU medio ↑", "{:.3f}", True),
        ("mean_ms", "ms/img ↓", "{:.0f}", False),
    ],
    "formula": [
        ("n", "n", "{}", None),
        ("latex_exact", "LaTeX exacto ↑", "{:.3f}", True),
        ("latex_sim", "Similitud ↑", "{:.3f}", True),
        ("latex_token_f1", "F1 tokens ↑", "{:.3f}", True),
        ("latex_any", "Salidas con LaTeX ↑", "{:.0%}", True),
        ("mean_ms", "ms/fórmula ↓", "{:.0f}", False),
    ],
}


def latest_run(feature: str) -> Path | None:
    base = RESULTS_DIR / feature
    runs = sorted((p for p in base.glob("*/") if any(p.glob("*.csv"))), reverse=True) if base.is_dir() else []
    return runs[0] if runs else None


def load_run(run: Path) -> tuple[list[dict], dict]:
    rows: list[dict] = []
    for csv_path in sorted(run.glob("*.csv")):
        with csv_path.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                if row.get("status") != "ok":
                    continue
                for key in ("cer", "wer", "cer_ord", "wer_ord", "word_f1", "exact_match",
                            "elapsed_ms", "markdown_f1", "block_f1",
                            "latex_exact", "latex_sim", "latex_token_f1",
                            "box_recall", "box_iou_mean"):
                    try:
                        row[key] = float(row[key])
                    except (TypeError, ValueError):
                        row[key] = None
                rows.append(row)
    summary_path = run / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
    return rows, summary


def latex_coverage(run: Path) -> dict[str, float]:
    """Fracción de salidas con algún comando LaTeX (sobre `<backend>.outputs.json`)."""
    coverage: dict[str, float] = {}
    for path in run.glob("*.outputs.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        texts = [o.get("text", "") for o in payload.get("outputs", [])]
        if texts:
            import re
            rx = re.compile(r"\\[A-Za-z]+")
            coverage[payload["backend"]] = sum(bool(rx.search(t)) for t in texts) / len(texts)
    return coverage


def summarize(rows: Sequence[dict]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        variant = row.get("model_variant") or "default"
        grouped[f"{row['backend']} ({variant})"].append(row)
    report: dict[str, dict[str, Any]] = {}
    for name, group in grouped.items():
        times = sorted(r["elapsed_ms"] for r in group if r["elapsed_ms"] is not None)
        entry: dict[str, Any] = {"n": len(group),
                                 "mean_ms": statistics.fmean(times) if times else None}
        for key in ("word_f1", "wer_ord", "cer", "wer", "box_recall", "box_iou_mean",
                    "latex_exact", "latex_sim", "latex_token_f1"):
            values = [r[key] for r in group if r.get(key) is not None]
            entry[key] = statistics.fmean(values) if values else None
        report[name] = entry
    return report


def build(feature: str, run: Path) -> str:
    rows, summary = load_run(run)
    if not rows:
        raise SystemExit(f"{run} no tiene filas `ok` para la feature {feature}")
    report = summarize(rows)
    if feature == "formula":
        for name, value in latex_coverage(run).items():
            for key in report:
                if key.split(" (")[0] == name:
                    report[key]["latex_any"] = value

    columns = FEATURE_COLUMNS[feature]
    ranked = [c for c in columns if c[3] is not None]
    best: dict[str, str] = {}
    for key, _label, _fmt, higher in ranked:
        values = [(d.get(key), name) for name, d in report.items() if d.get(key) is not None]
        if len(values) > 1 and len({v for v, _ in values}) > 1:
            best[key] = (max if higher else min)(values)[1]

    cmd = summary.get("command")
    if isinstance(cmd, list):
        command = " ".join(str(part) for part in cmd)
    else:
        command = (f"python benchmarks/features/{feature}/bank.py "
                   f"--dataset {summary.get('dataset', '?')} --limit {summary.get('n_samples', '?')} "
                   f"--warmup {summary.get('warmup', '?')} --repeats {summary.get('repeats', '?')} "
                   f"--device {summary.get('device_requested', '?')}")
    skipped = {b: m.get("reason", "") for b, m in (summary.get("backends") or {}).items()
               if m.get("status") == "skipped"}

    labels = [label for _k, label, _f, _h in columns]
    lines = [
        f"# Reporte por feature: `{feature}`",
        "",
        "> **Origen: `medido`** — ejecutado por nosotros en este repo. No hay filas de "
        "`referencia` (externas) en esta tabla.",
        "",
        "## Provenance",
        "",
        f"- **comando**: `{command}`",
        f"- **dataset**: `{summary.get('dataset', '?')}` · **n** (por motor): "
        f"`{summary.get('n_samples', '?')}` · **warmup**: `{summary.get('warmup', '?')}` · "
        f"**repeats**: `{summary.get('repeats', '?')}` · **device**: `{summary.get('device_requested', '?')}`",
        f"- **seed**: no aplica (banco determinista, sin aleatoriedad)",
        f"- **run**: `benchmarks/results/{feature}/{run.name}` · **fecha**: `{summary.get('timestamp', run.name)}`",
        f"- **runtime**: {summary.get('runtime', {})}",
        "",
        "## Comparativa (media por motor)",
        "",
        "| Motor (variante) | " + " | ".join(labels) + " |",
        "| :--- | " + " | ".join("---:" for _ in labels) + " |",
    ]
    for name, data in sorted(report.items()):
        cells = []
        for key, _label, fmt, _higher in columns:
            value = data.get(key)
            text = "N/A" if value is None else fmt.format(value)
            if best.get(key) == name:
                text = f"**{text}**"
            cells.append(text)
        lines.append(f"| {name} | " + " | ".join(cells) + " |")
    lines += [
        "",
        f"> En negrita, el mejor de cada métrica entre los motores **medidos** de `{feature}`. "
        "`N/A` = no evaluada (sin GT de esa columna), nunca un `0.0` inventado.",
        "",
        "## Saltados (`skipped`) — no cuentan como ejecutados",
        "",
    ]
    lines += [f"- `{b}` — {reason}" for b, reason in sorted(skipped.items())] or ["- (ninguno)"]
    lines += [
        "",
        "## Nota de honestidad",
        "",
        "- Ningún motor ausente se registra como `ok`: queda `skipped` con su `pip install`.",
        "- Las columnas sin GT no se rellenan con ceros: aparecen como `N/A` (no evaluada).",
        "",
    ]
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reporte por feature")
    parser.add_argument("--feature", choices=sorted(FEATURE_COLUMNS))
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--run", type=Path, default=None, help="carpeta de la run")
    args = parser.parse_args(argv)
    features = sorted(FEATURE_COLUMNS) if args.all or not args.feature else [args.feature]
    rc = 0
    for feature in features:
        run = args.run or latest_run(feature)
        if run is None:
            print(f"[report] {feature}: sin runs en results/{feature}/ (nada que reportar)")
            rc = 1
            continue
        md = build(feature, run)
        out = FEATURES_DIR / feature / "REPORT.md"
        out.write_text(md + "\n", encoding="utf-8")
        print(md)
        print(f"\n[report] {feature} -> {out}\n")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
