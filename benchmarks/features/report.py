#!/usr/bin/env python
"""Reporte **por feature** a partir de las runs de `benchmarks/results/<feature>/`.

Lee la run más reciente (o `--run`) de una feature y escribe
`benchmarks/features/<feature>/REPORT.md` (y, para features con datos,
`REPORT.png`/`.svg` con la comparativa por motor) con:

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

from common import BENCHMARKS_ROOT, module_available, select_device_rows

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
    "layout": [
        ("n", "n", "{}", None),
        ("layout_map", "mAP@IoU 0.5 ↑", "{:.3f}", True),
        ("layout_recall", "recall@IoU 0.5 ↑", "{:.3f}", True),
        ("mean_ms", "ms/imagen ↓", "{:.0f}", False),
    ],
    "table": [
        ("n", "n", "{}", None),
        ("table_teds", "TEDS estrut. ↑", "{:.3f}", True),
        ("mean_ms", "ms/tabla ↓", "{:.0f}", False),
    ],
    "full_page": [
        ("n", "n", "{}", None),
        ("markdown_f1", "Markdown F1 ↑", "{:.3f}", True),
        ("block_f1", "F1 bloques ↑", "{:.3f}", True),
        ("cer", "CER ↓", "{:.3f}", False),
        ("mean_ms", "ms/página ↓", "{:.0f}", False),
    ],
    "orientation": [
        ("n", "n", "{}", None),
        ("ori_acc", "accuracy ↑", "{:.1%}", True),
        ("mean_ms", "ms/página ↓", "{:.0f}", False),
    ],
    "text_line": [
        ("n", "n", "{}", None),
        ("ori_acc", "accuracy ↑", "{:.1%}", True),
        ("mean_ms", "ms/línea ↓", "{:.0f}", False),
    ],
    "rectification": [
        ("n", "n", "{}", None),
        ("rect_sim", "SSIM ↑", "{:.3f}", True),
        ("mean_ms", "ms/página ↓", "{:.0f}", False),
    ],
    "seal": [
        ("n", "n", "{}", None),
        ("box_recall", "recall@IoU 0.5 ↑", "{:.3f}", True),
        ("box_iou_mean", "IoU medio ↑", "{:.3f}", True),
        ("mean_ms", "ms/imagen ↓", "{:.0f}", False),
    ],
}

# Métrica **titular** de cada feature (la que encabeza su REPORT.md): clave,
# etiqueta y si "más es mejor". Solo entran features con banco implementado y
# con datos; el resto no tiene gráfica (un esqueleto no publica cifras).
TITULAR_METRIC: dict[str, tuple[str, str, bool]] = {
    "text": ("word_f1", "F1 palabra ↑", True),
    "formula": ("latex_sim", "Similitud LaTeX ↑", True),
    "layout": ("layout_map", "mAP@IoU 0.5 ↑", True),
    "table": ("table_teds", "TEDS de estructura ↑", True),
    "full_page": ("markdown_f1", "Markdown F1 ↑", True),
    "orientation": ("ori_acc", "accuracy ↑", True),
    "text_line": ("ori_acc", "accuracy ↑", True),
    "rectification": ("rect_sim", "SSIM ↑", True),
    "seal": ("box_recall", "recall@IoU 0.5 ↑", True),
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
                            "box_recall", "box_iou_mean",
                            "layout_map", "layout_recall", "table_teds", "ori_acc", "rect_sim"):
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
        for key in ("word_f1", "wer_ord", "cer", "wer", "markdown_f1", "block_f1",
                    "box_recall", "box_iou_mean",
                    "latex_exact", "latex_sim", "latex_token_f1",
                    "layout_map", "layout_recall", "table_teds", "ori_acc", "rect_sim"):
            values = [r[key] for r in group if r.get(key) is not None]
            entry[key] = statistics.fmean(values) if values else None
        report[name] = entry
    return report


def analyze(feature: str, run: Path) -> tuple[dict[str, dict[str, Any]], dict]:
    """Carga la run y agrega el reporte por motor (+ cobertura LaTeX en `formula`)."""
    rows, summary = load_run(run)
    if not rows:
        raise SystemExit(f"{run} no tiene filas `ok` para la feature {feature}")
    # Honestidad de proveedor: sólo cuentan las filas que de verdad corrieron en el
    # device pedido; una fila que pidió GPU pero cayó a CPU no entra en el ranking GPU.
    device = summary.get("device_requested", "cpu")
    device_rows = select_device_rows(rows, device)
    if not device_rows:
        raise SystemExit(
            f"{run}: ninguna fila corrio de verdad en device={device} "
            "(provider_effective honesto: un fallback CPU no cuenta como GPU)"
        )
    report = summarize(device_rows)
    if feature == "formula":
        for name, value in latex_coverage(run).items():
            for key in report:
                if key.split(" (")[0] == name:
                    report[key]["latex_any"] = value

    return report, summary


def render_md(feature: str, report: dict[str, dict[str, Any]], summary: dict, run: Path) -> str:
    """Markdown del reporte por feature (provenance + comparativa + skipped)."""
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
        f"- Honestidad de proveedor: el ranking sólo cuenta filas que de verdad corrieron en "
        f"`device={summary.get('device_requested', 'cpu')}`. `pyocrust` confirma el EP real en "
        "`provider_effective`; si no hay acelerador, `--device gpu` queda `skipped` — un fallback "
        "CPU nunca se cuenta como GPU.",
        "",
    ]
    return "\n".join(lines)


def build(feature: str, run: Path) -> str:
    """Markdown del reporte por feature (compatibilidad; = `render_md(analyze(...))`)."""
    return render_md(feature, *analyze(feature, run), run)


def _wrap_engine(label: str) -> str:
    """Parte `nombre_variante (detalle)` en varias líneas: rompe en `_` y en `(`.

    Nombres como `pyocrust_formulanet` son largos; partir en cada `_` evita que
    dos etiquetas vecinas se pisen en el eje X (medido, no a ojo).
    """
    head, sep, tail = label.partition("(")
    head = head.strip().replace("_", "_\n") if head.strip() else label
    if sep and label.endswith(")") and head:
        return f"{head}\n({tail}"
    return head


def _ordered_names(report: dict, key: str, higher: bool) -> list[str]:
    """Motores ordenados por la métrica titular (mejor primero; `None` al final)."""
    def rank(name: str):
        value = report[name].get(key)
        return (value is None, -(value or 0.0) if higher else (value or 0.0))

    return sorted(report, key=rank)


def plot_feature(feature: str, report: dict, summary: dict, out: Path) -> None:
    """Resumen de una feature: **calidad** (métrica titular) + **tiempo**, por motor.

    Cada barra lleva su valor y su `n`; el `origen` (`medido`/`referencia`) del run
    va rotulado en título y leyenda. Nombres partidos en dos líneas y leyenda fuera
    del área de dibujo: mismo criterio anti-solapamiento que `report_benchmarks.py`.
    """
    from matplotlib.patches import Patch
    from matplotlib.ticker import FixedFormatter

    from report_benchmarks import _pyplot

    key, label, higher = TITULAR_METRIC[feature]
    names = _ordered_names(report, key, higher)
    quality = [report[n].get(key) for n in names]
    times = [report[n].get("mean_ms") for n in names]
    counts = [report[n].get("n") for n in names]
    x = list(range(len(names)))

    plt = _pyplot()
    fig, (axq, axt) = plt.subplots(1, 2, figsize=(max(10.5, 1.55 * len(names) + 4.5), 5.8))

    def bars(ax, values, color, fmt):
        heights = [v if v is not None else float("nan") for v in values]
        drawn = ax.bar(x, heights, 0.62, color=color)
        for bar, value, n in zip(drawn, values, counts):
            if value is None:
                continue
            ax.annotate(f"{fmt.format(value)}\nn={n}",
                        (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                        ha="center", va="bottom", fontsize=8.5)

    present_q = [v for v in quality if v is not None]
    bars(axq, quality, "#1f6f5c", "{:.3f}")
    axq.set_ylim(0, (max(present_q) if present_q else 1.0) * 1.28)
    axq.set_ylabel(label)
    axq.set_title(f"Calidad — {label}", fontsize=12, weight="bold")

    present_t = [v for v in times if v is not None]
    bars(axt, times, "#3b6fb0", "{:.0f}")
    axt.set_ylim(0, (max(present_t) if present_t else 1.0) * 1.28)
    axt.set_ylabel("ms/imagen ↓")
    axt.set_title("Tiempo — ms/imagen", fontsize=12, weight="bold")

    for ax in (axq, axt):
        ax.set_xticks(x)
        ax.set_xticklabels(names)
        ax.xaxis.set_major_formatter(FixedFormatter([_wrap_engine(n) for n in names]))

    origen = summary.get("origen") or "medido"
    skipped = sum(1 for m in (summary.get("backends") or {}).values()
                  if m.get("status") == "skipped")
    dataset = summary.get("dataset", "?")
    run_id = summary.get("timestamp", "?")
    fig.suptitle(f"pyocrust · feature «{feature}» — comparativa por motor (origen: {origen})",
                 fontsize=13, weight="bold")
    fig.legend(
        handles=[
            Patch(color="#1f6f5c", label=f"Calidad: {label} (origen: {origen})"),
            Patch(color="#3b6fb0", label=f"Tiempo: ms/imagen ↓ (origen: {origen})"),
        ],
        loc="lower center", ncol=2, frameon=False, fontsize=9, bbox_to_anchor=(0.5, -0.03),
    )
    fig.text(0.5, -0.075,
             f"dataset: {dataset} · n por motor: {sorted({c for c in counts if c}) or '?'} · "
             f"run: {run_id} · motores saltados (skipped): {skipped}",
             ha="center", fontsize=8.5, color="#444444")
    fig.tight_layout(rect=(0, 0.04, 1, 0.95))
    fig.savefig(out.with_suffix(".png"), dpi=160, bbox_inches="tight", facecolor="white")
    fig.savefig(out.with_suffix(".svg"), bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reporte por feature")
    parser.add_argument("--feature", choices=sorted(FEATURE_COLUMNS))
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--run", type=Path, default=None, help="carpeta de la run")
    parser.add_argument("--no-md", action="store_true",
                        help="no reescribir REPORT.md (solo la gráfica REPORT.png/.svg)")
    args = parser.parse_args(argv)
    features = sorted(FEATURE_COLUMNS) if args.all or not args.feature else [args.feature]
    rc = 0
    for feature in features:
        run = args.run or latest_run(feature)
        if run is None:
            print(f"[report] {feature}: sin runs en results/{feature}/ (nada que reportar)")
            rc = 1
            continue
        report, summary = analyze(feature, run)
        md = render_md(feature, report, summary, run)
        print(md)
        if not args.no_md:
            out = FEATURES_DIR / feature / "REPORT.md"
            out.write_text(md + "\n", encoding="utf-8")
            print(f"\n[report] {feature} -> {out}")
        if feature in TITULAR_METRIC:
            out = FEATURES_DIR / feature / "REPORT"
            plot_feature(feature, report, summary, out)
            print(f"[report] {feature} -> {out}.png (+ .svg)")
        print()
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
