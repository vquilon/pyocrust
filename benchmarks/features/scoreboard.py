#!/usr/bin/env python
"""Resumen global de RESULTADOS: features × modelo × licencia × device × tiempo × calidad.

Genera `benchmarks/reports/SCOREBOARD.md` + `benchmarks/figures/SCOREBOARD.png` + `SCOREBOARD.svg`.

Una fila por (feature, motor, device) con la **última** corrida medida. La licencia
sale de `summary._license_for` (catálogo de `pyocrust` para `pyocrust*`, tabla de
externos para el resto); una licencia no verificada queda **vacía** (nunca se
inventa). No debe confundirse con `overview.py`, que es la matriz de cobertura
feature × capacidad.

Uso:
    .venv/Scripts/python.exe benchmarks/features/scoreboard.py
"""
from __future__ import annotations

import csv
import math
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent
REPORTS = BENCH / "reports"
FIGURES = BENCH / "figures"
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from summary import EXTERNAL_LICENSE, FEATURES, _license_for, _motor_label, _num, collect_rows  # noqa: E402
from features._localization import english_markdown  # noqa: E402

RESULTS = BENCH / "results"

# Columna de calidad por feature (el resto quedan vacías en el CSV).
QUALITY_COL = {
    "text": ("word_f1", "Word F1"),
    "formula": ("latex_sim", "Similarity"),
    "layout": ("layout_map", "mAP@0.5"),
    "orientation": ("ori_acc", "accuracy"),
    "rectification": ("rect_sim", "SSIM"),
    "text_line": ("ori_acc", "accuracy"),
    "seal": ("box_recall", "recall@0.5"),
    "table": ("table_teds", "TEDS"),
    "full_page": ("markdown_f1", "Markdown F1"),
}

# Color por licencia: permisivas verdes/azules, copyleft naranja/rojo.
LICENSE_COLOR = {
    "Apache-2.0": "#2e7d32",
    "MIT": "#1565c0",
    "OpenRAIL-M-Mod": "#ef6c00",
    "AGPL-3.0": "#c62828",
}


def _motor(backend: str, variant: str) -> str:
    return f"{backend} ({variant})" if variant and variant != "default" else backend


def latest_run(feature: str) -> Path | None:
    d = RESULTS / feature
    if not d.is_dir():
        return None
    runs = sorted((p for p in d.iterdir() if p.is_dir() and any(p.glob("*.csv"))), reverse=True)
    return runs[0] if runs else None


def collect() -> dict[tuple[str, str, str], list[dict]]:
    """{(feature, device, motor): filas} de la última corrida que midió ese motor.

    Sin esto, una corrida tardía de un solo backend (p. ej. la de GPU de Paddle)
    haría desaparecer del resumen las filas de CPU de los demás motores.
    """
    out: dict[tuple[str, str, str], list[dict]] = {}
    for feature, _titular in FEATURES:
        d = RESULTS / feature
        if not d.is_dir():
            continue
        runs = sorted((p for p in d.iterdir() if p.is_dir() and any(p.glob("*.csv"))), reverse=True)
        seen: set[tuple[str, str, str]] = set()
        for run in runs:
            by_key: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
            for csv_path in sorted(run.glob("*.csv")):
                for r in csv.DictReader(csv_path.read_text(encoding="utf-8").splitlines()):
                    if r.get("status") != "ok" or not r.get("device_requested"):
                        continue
                    key = (feature, r.get("device_requested", "?"),
                           r["backend"])  # por backend, no por etiqueta de variante
                    by_key[key].append(r)
            for key, rows in by_key.items():
                if key not in seen:
                    seen.add(key)
                    out[key] = rows
    return out


def aggregate(rows: list[dict], quality: str) -> dict:
    vals = [r for r in rows if _num(r.get(quality, "")) is not None]
    ms = [float(r["elapsed_ms"]) for r in rows if r.get("elapsed_ms")]
    return {
        "n": len(rows),
        "quality": (sum(float(r[quality]) for r in vals) / len(vals)) if vals else None,
        "ms": (sum(ms) / len(ms)) if ms else None,
        "provider": rows[0].get("provider_effective", "?"),
        "dataset": rows[0].get("dataset", "?"),
        "task": rows[0].get("task_type", "?"),
        "model_name": rows[0].get("model_name", ""),
        "variant": rows[0].get("model_variant", ""),
    }


def _panel(ax, entries, title) -> None:
    if not entries:
        ax.axis("off")
        ax.set_title(f"{title}\n(pending: no data)", fontsize=9, color="#888")
        return
    entries.sort(key=lambda e: e["quality"] if e["quality"] is not None else -1)
    vals = [e["quality"] if e["quality"] is not None else 0.0 for e in entries]
    colors = [LICENSE_COLOR.get(e["license"], "#90a4ae") for e in entries]
    bars = ax.barh(range(len(vals)), vals, color=colors)
    top = max(vals) or 1
    for bar, e in zip(bars, entries):
        ms = f"{e['ms']:.0f} ms" if e["ms"] is not None else "?"
        lic = e["license"] or "unverified"
        ax.text(bar.get_width() + top * 0.01, bar.get_y() + bar.get_height() / 2,
                f"{e['quality']:.3f} · {ms} · {lic}", va="center", fontsize=6.5)
    ax.set_yticks(range(len(vals)))
    ax.set_yticklabels([e["motor"] for e in entries], fontsize=7)
    ax.set_xlim(0, top * 1.65)
    ax.set_title(title, fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="x", labelsize=7)


def main() -> int:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    data = collect_rows()
    n = len(FEATURES)
    cols = 3
    rows_n = math.ceil(n / cols)
    fig, axes = plt.subplots(rows_n, cols, figsize=(18, 3.6 * rows_n))
    axes = axes.ravel()

    md = [
        "# Resumen global — features × modelo × licencia × device × tiempo × calidad",
        "",
        "> Una fila por (feature, motor, device) con la **última** corrida medida.",
        "> `license` es **informativa** (señala las no permisivas); la puerta solo aplica a los modelos de `pyocrust`.",
        "",
        "| Feature | Motor | Licencia | Task | Device | n | Calidad | ms | Proveedor | Dataset |",
        "| :--- | :--- | :--- | :--- | :--- | ---: | ---: | ---: | :--- | :--- |",
    ]

    for k, (feature, _titular) in enumerate(FEATURES):
        quality_col, quality_label = QUALITY_COL[feature]
        entries = []
        for (f, device, motor), rws in sorted(data.items()):
            if f != feature:
                continue
            agg = aggregate(rws, quality_col)
            label = _motor_label(motor, agg["variant"], agg["model_name"])
            entries.append({
                "motor": label, "device": device,
                "license": _license_for(label),
                "task": agg["task"], "n": agg["n"], "quality": agg["quality"],
                "ms": agg["ms"], "provider": agg["provider"], "dataset": agg["dataset"],
            })
        _panel(axes[k], entries, f"{feature} — {quality_label} ↑")
        for e in entries:
            q = f"{e['quality']:.3f}" if e["quality"] is not None else "N/A"
            ms = f"{e['ms']:.0f}" if e["ms"] is not None else "N/A"
            md.append(
                f"| {feature} | {e['motor']} | {e['license']} | {e['task']} | {e['device']} "
                f"| {e['n']} | {q} | {ms} | {e['provider']} | {e['dataset']} |"
            )
        if not entries:
            md.append(f"| {feature} | — | — | — | — | 0 | N/A | N/A | — | — |")

    for ax in axes[n:]:
        ax.axis("off")

    fig.legend(handles=[
        Patch(facecolor=LICENSE_COLOR["Apache-2.0"], label="Apache-2.0"),
        Patch(facecolor=LICENSE_COLOR["MIT"], label="MIT"),
        Patch(facecolor=LICENSE_COLOR["OpenRAIL-M-Mod"], label="OpenRAIL-M-Mod (Indra)"),
        Patch(facecolor=LICENSE_COLOR["AGPL-3.0"], label="AGPL-3.0 (copyleft)"),
        Patch(facecolor="#90a4ae", label="unverified / outside catalog"),
    ], loc="lower center", bbox_to_anchor=(0.5, 0.02), ncol=5, frameon=False, fontsize=9)
    fig.suptitle("pyocrust — all features: quality, runtime, license, and device", fontsize=14)
    fig.tight_layout(rect=(0, 0.06, 1, 0.97))
    FIGURES.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "svg"):
        fig.savefig(FIGURES / f"SCOREBOARD.{ext}", dpi=150, bbox_inches="tight", facecolor="white")
    scoreboard_md = "\n".join(md)
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "SCOREBOARD.md").write_text(scoreboard_md, encoding="utf-8")
    (REPORTS / "SCOREBOARD.en.md").write_text(english_markdown(scoreboard_md), encoding="utf-8")
    print("[scoreboard] ->", FIGURES / "SCOREBOARD.png")
    print("[scoreboard] ->", REPORTS / "SCOREBOARD.md (+ SCOREBOARD.en.md)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
