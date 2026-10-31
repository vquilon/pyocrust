#!/usr/bin/env python
"""Genera tablas y graficos listos para publicar (LinkedIn, paper, README).

Lee los CSV de `benchmarks/results/` producidos por `run_benchmarks.py` y
escribe en `benchmarks/output_examples/`:

* `benchmark_table.md`      — tabla markdown (para README / LinkedIn texto)
* `benchmark_table.tex`     — tabla LaTeX standalone
* `benchmark_table.png|svg` — la misma tabla renderizada
* `benchmark_quality.png`   — CER y F1 de palabra por backend
* `benchmark_speed.png`     — ms/pagina y paginas/s por backend
* `benchmark_quality_vs_speed.png` — calidad vs velocidad (grafico principal)

Uso:
    python benchmarks/report_benchmarks.py                 # todas las runs
    python benchmarks/report_benchmarks.py --run <tsv>     # una run concreta
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Sequence

HERE = Path(__file__).resolve().parent
RESULTS_DIR = HERE / "results"
OUT_DIR = HERE / "output_examples"

# metricas donde mas alto es mejor / mas bajo es mejor
HIGHER_BETTER = {"word_f1", "markdown_f1", "block_f1", "exact_match", "pages_per_s", "mean_confidence"}
LOWER_BETTER = {"cer", "wer", "mean_ms", "median_ms", "p95_ms"}


# ---------------------------------------------------------------------------
# Carga y agregado
# ---------------------------------------------------------------------------

def load_rows(run: Path | None = None, all_runs: bool = False) -> list[dict]:
    """Lee filas `ok`. Por defecto solo la run más reciente (comparaciones limpias)."""
    if run is not None:
        runs = [run]
    elif all_runs:
        runs = sorted(RESULTS_DIR.glob("*/"))
    else:
        runs = sorted(RESULTS_DIR.glob("*/"))[-1:]
    rows: list[dict] = []
    for run_dir in runs:
        for csv_path in sorted(run_dir.glob("*.csv")):
            with csv_path.open(encoding="utf-8", newline="") as fh:
                for row in csv.DictReader(fh):
                    if row.get("status") != "ok":
                        continue
                    # Legacy cer_ord was word-level and duplicated wer_ord.
                    # Do not relabel it as the current character-level metric.
                    if "task_type" not in row:
                        row["cer_ord"] = None
                    for key in (
                        "cer",
                        "wer",
                        "cer_ord",
                        "wer_ord",
                        "word_f1",
                        "exact_match",
                        "elapsed_ms",
                        "mean_confidence",
                        "n_regions",
                        "n_chars_gt",
                        "n_chars_pred",
                    ):
                        try:
                            row[key] = float(row.get(key))
                        except (TypeError, ValueError):
                            row[key] = None
                    for key in ("markdown_f1", "block_f1"):
                        try:
                            row[key] = float(row.get(key))
                        except (TypeError, ValueError):
                            row[key] = None
                    row["_csv"] = str(csv_path)
                    rows.append(row)
    return rows


def aggregate(rows: Sequence[dict]) -> dict[str, dict[str, Any]]:
    """Media por backend, con dispersion. Solo filas `status == ok`."""
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        if row.get("status", "ok") != "ok":
            continue
        task = row.get("task_type", "text")
        variant = row.get("model_variant", "legacy")
        grouped[f"{row['backend']} ({variant}; {task})"].append(row)

    report: dict[str, dict[str, Any]] = {}
    for backend, group in grouped.items():
        cers = [r["cer"] for r in group if r["cer"] is not None]
        wers = [r["wer"] for r in group if r["wer"] is not None]
        cer_ords = [r["cer_ord"] for r in group if r.get("cer_ord") is not None]
        wer_ords = [r["wer_ord"] for r in group if r.get("wer_ord") is not None]
        f1s = [r["word_f1"] for r in group if r["word_f1"] is not None]
        exact = [r["exact_match"] for r in group if r["exact_match"] is not None]
        times = sorted(r["elapsed_ms"] for r in group if r["elapsed_ms"] is not None)
        confs = [r["mean_confidence"] for r in group if r["mean_confidence"] is not None]
        mean_ms = statistics.fmean(times) if times else 0.0
        report[backend] = {
            "n": len(group),
            "cer": statistics.fmean(cers) if cers else 0.0,
            "wer": statistics.fmean(wers) if wers else 0.0,
            "cer_ord": statistics.fmean(cer_ords) if cer_ords else None,
            "wer_ord": statistics.fmean(wer_ords) if wer_ords else None,
            "markdown_f1": statistics.fmean(r["markdown_f1"] for r in group if r.get("markdown_f1") is not None) if any(r.get("markdown_f1") is not None for r in group) else None,
            "block_f1": statistics.fmean(r["block_f1"] for r in group if r.get("block_f1") is not None) if any(r.get("block_f1") is not None for r in group) else None,
            "word_f1": statistics.fmean(f1s) if f1s else 0.0,
            "exact_match": statistics.fmean(exact) if exact else 0.0,
            "mean_ms": mean_ms,
            "median_ms": statistics.median(times) if times else 0.0,
            # percentil 95 por el método del rango más cercano (n pequeño)
            "p95_ms": times[min(len(times) - 1, math.ceil(0.95 * len(times)) - 1)] if times else 0.0,
            "pages_per_s": 1000.0 / mean_ms if mean_ms else 0.0,
            "mean_confidence": statistics.fmean(confs) if confs else 0.0,
            "cer_std": statistics.pstdev(cers) if len(cers) > 1 else 0.0,
        }
    return report


# ---------------------------------------------------------------------------
# Tablas
# ---------------------------------------------------------------------------

METRIC_COLUMNS = [
    ("markdown_f1", "F1 Markdown ↑", "{:.3f}"),
    ("block_f1", "F1 bloques ↑", "{:.3f}"),
    # `word_f1` y los `*_ord` encabezan: miden reconocimiento, no disposición.
    # `cer`/`wer` crudos miden también el orden de lectura y quedan al final, sin marca.
    ("word_f1", "F1 palabra ↑", "{:.3f}"),
    ("wer_ord", "WER ord. ↓", "{:.3f}"),
    ("cer", "CER ↓", "{:.3f}"),
    ("wer", "WER ↓", "{:.3f}"),
    ("mean_ms", "ms/pág.", "{:.0f}"),
    ("pages_per_s", "págs/s", "{:.2f}"),
]

# Solo estas métricas deciden la marca de "mejor": el resto se publica como
# información (B4/D1: el CER/WER crudos se invierten al neutralizar el orden).
RANKED_METRICS = {"markdown_f1", "word_f1", "wer_ord", "mean_ms", "pages_per_s"}


def _ranks(report: dict[str, dict[str, Any]]) -> dict[str, dict[str, str]]:
    """Mejor (best) y segundo mejor (second) por métrica."""
    backends = list(report.keys())
    marks: dict[str, dict[str, str]] = {}
    for key, _label, _fmt in METRIC_COLUMNS:
        if key not in RANKED_METRICS:
            continue
        marks[key] = {}
        # Compare only the same task; text quality cannot rank page Markdown.
        tasks = {b.rsplit("; ", 1)[-1].rstrip(")") for b in backends}
        for task in tasks:
            if key in {"word_f1", "wer_ord"} and task != "text":
                continue
            if key == "markdown_f1" and task == "text":
                continue
            ordered = sorted([b for b in backends if b.endswith(f"; {task})") and report[b].get(key) is not None],
                             key=lambda b: report[b][key], reverse=key in HIGHER_BETTER)
            if len(ordered) > 1:
                marks[key][ordered[0]] = "best"
                marks[key][ordered[1]] = "second"
    return marks


def render_markdown(report: dict[str, dict[str, Any]]) -> str:
    marks = _ranks(report)
    labels = [label for _key, label, _fmt in METRIC_COLUMNS]
    header = "| Backend | n | " + " | ".join(labels) + " |"
    sep = "|---|---|" + "---|" * len(labels)
    lines = [header, sep]
    for backend, data in sorted(report.items()):
        cells = [backend, str(data["n"])]
        for key, _label, fmt in METRIC_COLUMNS:
            value = fmt.format(data[key]) if data.get(key) is not None else "N/A"
            if marks.get(key, {}).get(backend) == "best":
                value = f"**{value}**"
            elif marks.get(key, {}).get(backend) == "second":
                value = f"_{value}_"
            cells.append(value)
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    lines.append(
        "> `F1 palabra` y `CER/WER ord.` neutralizan el orden de lectura: miden "
        "reconocimiento. `CER`/`WER` crudos miden también la disposición de la "
        "página y llevan la marca solo informativa."
    )
    return "\n".join(lines)


def render_latex(report: dict[str, dict[str, Any]]) -> str:
    marks = _ranks(report)

    def esc(value: str) -> str:
        for old, new in (
            ("\\", r"\textbackslash{}"),
            ("&", r"\&"),
            ("%", r"\%"),
            ("$", r"\$"),
            ("#", r"\#"),
            ("_", r"\_"),
            ("{", r"\{"),
            ("}", r"\}"),
        ):
            value = value.replace(old, new)
        return value

    def cell(key: str, backend: str, value: float, fmt: str) -> str:
        text = fmt.format(value) if value is not None else "N/A"
        if marks.get(key, {}).get(backend) == "best":
            return rf"\textbf{{{text}}}"
        if marks.get(key, {}).get(backend) == "second":
            return rf"\underline{{{text}}}"
        return text

    labels = [label for _key, label, _fmt in METRIC_COLUMNS]
    header = (
        r"\begin{tabular}{ll" + "r" * len(labels) + "}" + "\n"
        r"\toprule" + "\n"
        r"Backend & n & " + " & ".join(labels) + r" \\" + "\n"
        r"\midrule" + "\n"
    )
    body = []
    for backend, data in sorted(report.items()):
        cells = [esc(backend), str(data["n"])]
        for key, _label, fmt in METRIC_COLUMNS:
            cells.append(cell(key, backend, data[key], fmt))
        body.append(" & ".join(cells) + r" \\")
    footer = (
        r"\bottomrule" + "\n"
        r"\end{tabular}" + "\n"
    )
    return (
        r"\documentclass[varwidth,border=2pt]{standalone}" + "\n"
        r"\usepackage{booktabs}" + "\n"
        r"\begin{document}" + "\n"
        + header + "\n".join(body) + "\n" + footer
        + r"\end{document}" + "\n"
    )


# ---------------------------------------------------------------------------
# Graficos (matplotlib, backend Agg)
# ---------------------------------------------------------------------------

def _pyplot():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "font.size": 11,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.grid": True,
            "grid.alpha": 0.25,
            "grid.linestyle": "--",
        }
    )
    return plt


def plot_table(report: dict[str, dict[str, Any]], out: Path) -> None:
    plt = _pyplot()
    marks = _ranks(report)
    backends = sorted(report.keys())
    labels = [b for b, _l, _f in METRIC_COLUMNS]
    fig, ax = plt.subplots(figsize=(12, 1.1 + 0.55 * len(backends)))
    ax.axis("off")

    cell_text = []
    for backend in backends:
        data = report[backend]
        row = [backend, str(data["n"])]
        for key, _label, fmt in METRIC_COLUMNS:
            value = fmt.format(data[key]) if data.get(key) is not None else "N/A"
            if marks.get(key, {}).get(backend) == "best":
                value = f"★ {value}"
            row.append(value)
        cell_text.append(row)

    table = ax.table(
        cellText=cell_text,
        colLabels=["Backend", "n"] + labels,
        cellLoc="center",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10.5)
    table.scale(1.0, 1.6)
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_text_props(weight="bold")
    fig.suptitle(
        "pyocrust vs. OCR en Python/Rust — dataset real FUNSD "
        f"({max((d['n'] for d in report.values()), default=0)} imágenes evaluadas)",
        fontsize=13,
        weight="bold",
    )
    fig.tight_layout()
    fig.savefig(out.with_suffix(".png"), dpi=160, bbox_inches="tight", facecolor="white")
    fig.savefig(out.with_suffix(".svg"), bbox_inches="tight", facecolor="white")
    plt.close(fig)


def plot_quality(report: dict[str, dict[str, Any]], out: Path) -> None:
    plt = _pyplot()
    backends = sorted(b for b in report if b.endswith("; text)"))
    x = range(len(backends))
    width = 0.38

    fig, ax = plt.subplots(figsize=(8, 4.6))
    cer = [report[b]["cer_ord"] if report[b]["cer_ord"] is not None else float("nan") for b in backends]
    f1 = [report[b]["word_f1"] for b in backends]
    bars1 = ax.bar([i - width / 2 for i in x], cer, width,
                   label="CER ord. ↓ (reconocimiento)", color="#c0504d")
    bars2 = ax.bar([i + width / 2 for i in x], f1, width, label="F1 palabra ↑",
                   color="#1f6f5c")
    for bars in (bars1, bars2):
        for bar in bars:
            ax.annotate(f"{bar.get_height():.3f}",
                        (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                        ha="center", va="bottom", fontsize=8.5)
    ax.set_xticks(list(x))
    ax.set_xticklabels(backends)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Error / acierto")
    ax.set_title("Calidad de OCR sobre FUNSD", fontsize=12, weight="bold")
    ax.legend(loc="upper right", frameon=False)
    fig.tight_layout()
    fig.savefig(out, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def plot_speed(report: dict[str, dict[str, Any]], out: Path) -> None:
    plt = _pyplot()
    backends = sorted(report.keys())
    x = range(len(backends))
    width = 0.38
    ms = [report[b]["mean_ms"] for b in backends]
    pps = [report[b]["pages_per_s"] for b in backends]

    fig, ax = plt.subplots(figsize=(8, 4.6))
    bars = ax.bar([i - width / 2 for i in x], ms, width, label="ms/página ↓",
                  color="#3b6fb0")
    for bar in bars:
        ax.annotate(f"{bar.get_height():.0f}", (bar.get_x() + bar.get_width() / 2,
                                                bar.get_height()),
                    ha="center", va="bottom", fontsize=8.5)
    ax2 = ax.twinx()
    bars2 = ax2.bar([i + width / 2 for i in x], pps, width, label="págs/s ↑",
                    color="#e08a2e")
    ax2.grid(False)
    ax2.spines["right"].set_visible(True)
    for bar in bars2:
        ax2.annotate(f"{bar.get_height():.2f}", (bar.get_x() + bar.get_width() / 2,
                                                 bar.get_height()),
                     ha="center", va="bottom", fontsize=8.5)
    ax.set_xticks(list(x))
    ax.set_xticklabels(backends)
    ax.set_ylabel("ms por página")
    ax2.set_ylabel("páginas por segundo")
    ax.set_title("Velocidad de OCR (provider efectivo no instrumentado)", fontsize=12, weight="bold")
    handles = [bars, bars2]
    ax.legend(handles=[h for h in handles], labels=[h.get_label() for h in handles],
              loc="upper right", frameon=False)
    fig.tight_layout()
    fig.savefig(out, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def plot_quality_vs_speed(report: dict[str, dict[str, Any]], out: Path) -> None:
    plt = _pyplot()
    fig, ax = plt.subplots(figsize=(8, 5.2))
    for backend, data in sorted(report.items()):
        if not backend.endswith("; text)"):
            continue
        ax.scatter(data["pages_per_s"], data["word_f1"], s=140, label=backend, zorder=3)
        ax.annotate(backend, (data["pages_per_s"], data["word_f1"]),
                    textcoords="offset points", xytext=(8, 4), fontsize=9.5)
    ax.set_xlabel("páginas por segundo ↑")
    ax.set_ylabel("F1 de palabra ↑")
    ax.set_title("Calidad vs. velocidad — dataset real FUNSD", fontsize=12, weight="bold")
    ax.set_xlim(left=0)
    ax.set_ylim(0, 1.0)
    fig.tight_layout()
    fig.savefig(out, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ---------------------------------------------------------------------------

def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Tablas y graficos del benchmark")
    parser.add_argument("--run", type=Path, default=None, help="subcarpeta de results/")
    parser.add_argument(
        "--all",
        action="store_true",
        help="agregar todas las runs (por defecto solo la mas reciente)",
    )
    args = parser.parse_args(argv)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = load_rows(args.run, all_runs=args.all)
    if not rows:
        print("[report] no hay filas 'ok' en los CSV; ejecuta run_benchmarks.py antes.")
        return 1

    report = aggregate(rows)
    md = render_markdown(report)
    (OUT_DIR / "benchmark_table.md").write_text(md + "\n", encoding="utf-8")
    (OUT_DIR / "benchmark_table.tex").write_text(render_latex(report), encoding="utf-8")
    (OUT_DIR / "benchmark_summary.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    plot_table(report, OUT_DIR / "benchmark_table")
    plot_quality(report, OUT_DIR / "benchmark_quality.png")
    plot_speed(report, OUT_DIR / "benchmark_speed.png")
    plot_quality_vs_speed(report, OUT_DIR / "benchmark_quality_vs_speed.png")

    print(md)
    print(f"\n[report] escritos en {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
