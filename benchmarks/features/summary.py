#!/usr/bin/env python
"""Gráfica/final resumen: métrica titular por feature, `pyocrust` vs alternativas.

Lee las tablas de `benchmarks/features/<feature>/REPORT.md` (valores ya agregados,
`medido`) y escribe `benchmarks/SUMMARY.png` + `SUMMARY.svg` + `SUMMARY.md`.

Uso:
    .venv/Scripts/python.exe benchmarks/features/summary.py
"""
from __future__ import annotations

import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent

# feature -> (métrica titular ↑, título del panel, n)
FEATURES = [
    ("text", "F1 palabra", "text — FUNSD (detección + reconocimiento)", "word F1 ↑"),
    ("formula", "Similitud", "formula — OmniDocBench (fórmula → LaTeX)", "LaTeX similarity ↑"),
]


def _clean(cell: str) -> str:
    return cell.strip().replace("**", "").replace("`", "")


def parse_report(feature: str) -> tuple[list[str], dict[str, dict[str, str]]]:
    """Devuelve (cabeceras, {motor: {columna: valor}}) de la tabla *medido*.

    Lee **solo** la sección `## Comparativa (media por motor)`. Las tablas de
    `## Referencias externas` son valores de papers: mezclarlas rompería la regla
    de provenance (`medido` vs `referencia`).
    """
    text = (BENCH / "features" / feature / "REPORT.md").read_text(encoding="utf-8")
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines)
                  if ln.strip().lower().startswith("## comparativa")), None)
    if start is None:
        return [], {}

    rows: list[list[str]] = []
    for line in lines[start + 1:]:
        s = line.strip()
        if s.startswith("#"):
            break
        if s.startswith("|"):
            rows.append([_clean(c) for c in s.strip("|").split("|")])
        elif rows:
            break

    header = None
    data: dict[str, dict[str, str]] = {}
    for cells in rows:
        if header is None:
            header = cells
            continue
        if set("".join(cells)) <= set(":-"):  # línea separadora
            continue
        if len(cells) < 3:
            continue
        data[cells[0]] = dict(zip(header, cells))
    return header or [], data


def main() -> int:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    panels = []
    for feature, titular, title, xlabel in FEATURES:
        _, data = parse_report(feature)
        if not data:
            continue
        cols0 = next(iter(data.values()))
        key = next((k for k in cols0 if k.startswith(titular)), None)
        if key is None:
            continue
        pairs = []
        for motor, cols in data.items():
            raw = cols.get(key, "")
            try:
                pairs.append((motor, float(raw)))
            except ValueError:
                continue
        pairs.sort(key=lambda p: p[1])
        panels.append((title, xlabel, pairs))

    if not panels:
        raise SystemExit("No hay tablas con la métrica titular; ejecuta antes report.py")

    fig, axes = plt.subplots(1, len(panels), figsize=(13, 0.7 + 0.55 * max(len(p[2]) for p in panels)))
    if len(panels) == 1:
        axes = [axes]

    for ax, (title, xlabel, pairs) in zip(axes, panels):
        names = [p[0] for p in pairs]
        vals = [p[1] for p in pairs]
        # destaca pyocrust (verde) frente a alternativas (gris)
        colors = ["#2e7d32" if "pyocrust" in n else "#9e9e9e" for n in names]
        bars = ax.barh(names, vals, color=colors)
        best = max(vals) if vals else 0
        for bar, val in zip(bars, vals):
            ax.text(bar.get_width() + best * 0.01, bar.get_y() + bar.get_height() / 2,
                    f"{val:.3f}", va="center", fontsize=9)
        ax.set_title(title, fontsize=11)
        ax.set_xlabel(xlabel)
        ax.set_xlim(0, best * 1.18 if best else 1)
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(axis="y", labelsize=9)

    fig.suptitle("pyocrust — resumen de benchmarks por feature (medido, CPU)", fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    for ext in ("png", "svg"):
        fig.savefig(BENCH / f"SUMMARY.{ext}", dpi=160, bbox_inches="tight", facecolor="white")
    print("[summary] ->", BENCH / "SUMMARY.png")

    # tabla markdown consolidada
    lines = ["# Resumen de benchmarks (métrica titular por feature)", "",
             "> Generado por `features/summary.py` desde los `REPORT.md`. Todo `medido` (CPU).", ""]
    for title, xlabel, pairs in panels:
        lines += [f"## {title}", "", f"| Motor | {xlabel} |", "| :--- | ---: |"]
        for name, val in sorted(pairs, key=lambda p: -p[1]):
            mark = "**" if "pyocrust" in name else ""
            lines.append(f"| {mark}{name}{mark} | {val:.3f} |")
        lines.append("")
    (BENCH / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    print("[summary] ->", BENCH / "SUMMARY.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
