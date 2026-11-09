#!/usr/bin/env python
"""Tabla publicable de la feature `layout` (`.md` ES + `.tex` EN) con "Por estrato".

Genera `reports/layout/benchmark_table.md` (castellano) desde la run CPU de
referencia de `layout` (`features.report.latest_run`) y su `benchmark_table.tex`
(inglés, artefacto de publicación). `features.report` deriva después el `.en.md`
desde el `.md` (con `english_markdown`, fuente única de traducción).

Incluye la sección **Por estrato** (mAP/recall@IoU 0.5 por motor y estrato
`data_source × layout`): es la razón de este generador — resume la muestra
estratificada de `layout` y expone la heterogeneidad real que la media global
esconde. La nomenclatura de motor es la misma que `REPORT.md`/`SUMMARY`
(`model_name (variant)`), para que las tablas no diverjan.

Uso:
    .venv/Scripts/python.exe -m features.layout.table
"""

from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from common import BENCHMARKS_ROOT, select_device_rows
from features import report as report_mod

FEATURE = "layout"
OUT_DIR = BENCHMARKS_ROOT / "reports" / FEATURE

# Celdas: (clave de la métrica, etiqueta castellana, formato, ¿↑?). Se copian
# las de `report.FEATURE_COLUMNS["layout"]` + `license` (columna informativa).
_COLUMNS = [
    ("n", "n", "{}"),
    ("layout_map", "mAP@IoU 0.5 ↑", "{:.3f}"),
    ("layout_recall", "recall@IoU 0.5 ↑", "{:.3f}"),
    ("mean_ms", "ms/imagen ↓", "{:.0f}"),
]


def _tex_escape(text: str) -> str:
    """Escapa los caracteres especiales de LaTeX de una celda."""
    for source, target in (("\\", r"\textbackslash{}"), ("_", r"\_"), ("&", r"\&"),
                           ("%", r"\%"), ("#", r"\#"), ("↑", r"$\uparrow$"),
                           ("↓", r"$\downarrow$")):
        text = text.replace(source, target)
    return text


def _license_for(motor: str) -> str:
    from features.summary import _license_for  # import perezoso (evita cargar matplotlib)

    return _license_for(motor)


def _engine_rows(report: dict, summary: dict) -> tuple[list[str], list[str]]:
    """(filas_md, filas_tex) de la tabla por motor, más una nota de `skipped`."""
    md_rows, tex_rows = [], []
    backends = summary.get("backends") or {}
    for name in sorted(report):
        data = report[name]
        cells = [fmt.format(data[key]) if data.get(key) is not None else "N/A"
                 for key, _label, fmt in _COLUMNS]
        cells.append(_license_for(name))
        md_rows.append("| " + " | ".join([name, *cells]) + " |")
        tex_rows.append(" & ".join(_tex_escape(c) for c in [name, *cells]) + r" \\")
    # Motores `skipped` (sin filas) salen como `N/A`, nunca como ausencia ni `0.0`.
    for backend, meta in sorted(backends.items()):
        if (meta or {}).get("status") != "skipped":
            continue
        detail = f"{meta.get('model_name') or backend} ({meta.get('model_variant') or 'default'})"
        label = f"{detail} — skipped"
        md_rows.append(f"| {label} | " + " | ".join(["N/A"] * (len(_COLUMNS) + 1)) + " |")
        tex_rows.append(" & ".join(_tex_escape(c) for c in
                                   [label, *(["N/A"] * (len(_COLUMNS) + 1))]) + r" \\")
    return md_rows, tex_rows


def build() -> tuple[str, str]:
    """(markdown_es, latex_en) de `benchmark_table.{md,tex}` para `layout`."""
    run = report_mod.latest_run(FEATURE)
    if run is None:
        raise SystemExit(f"{FEATURE}: sin runs en results/{FEATURE}/ (nada que tabular)")
    report, summary = report_mod.analyze(FEATURE, run)
    all_rows, _ = report_mod.load_run(run)
    device_rows = select_device_rows(
        report_mod.applicable_rows(FEATURE, all_rows),
        summary.get("device_requested", "cpu"),
    )

    labels = [label for _k, label, _f in _COLUMNS] + ["license"]
    n_total = summary.get("n_samples", "?")
    strata = sorted({r["stratum"] for r in device_rows if r.get("stratum")})
    provenance = (f"Métricas **estratificadas** por `data_source × layout` de la run "
                  f"`{run.name}` (device `{summary.get('device_requested', '?')}`, "
                  f"n total ≤ {n_total}, {len(strata)} estratos). `N/A` = no medido "
                  "(`skipped`), nunca `0.0`. Licencias informativas.")

    md_rows, tex_rows = _engine_rows(report, summary)
    md = "\n".join([
        "# Benchmark: layout",
        "",
        "Muestra **estratificada** por `data_source × layout` (heterogeneidad real",
        "de documentos frente al sesgo previo hacia páginas ricas en tabla/fórmula).",
        "",
        "| Motor (variante/tamaño) | " + " | ".join(labels) + " |",
        "| :--- | " + " | ".join("---:" for _ in labels) + " |",
        *md_rows,
        "",
        f"> {provenance}",
        "",
        *report_mod.render_strata(FEATURE, device_rows),
    ]) + "\n"

    tex = "\n".join([
        r"\documentclass[border=2pt]{standalone}",
        r"\usepackage{booktabs}",
        r"\begin{document}",
        r"\begin{tabular}{l" + "r" * len(labels) + "}",
        r"\toprule",
        "Engine (variant/size) & " + " & ".join(
            _tex_escape(lbl) for lbl in labels) + r" \\",
        r"\midrule",
        *tex_rows,
        r"\bottomrule",
        r"\end{tabular}",
        r"\par\smallskip{\footnotesize " + _tex_escape(
            f"Stratified sample (data_source x layout), run {run.name}, "
            f"device {summary.get('device_requested', '?')}, n <= {n_total}, "
            f"{len(strata)} strata.") + "}",
        "",
        r"\par\textbf{Per stratum (\texttt{data\_source} $\times$ "
        r"\texttt{layout})}",
        r"\par\smallskip mAP@IoU 0.5 per stratum",
        "",
        *_strata_table_tex(report_mod.strata_summary(device_rows, ["layout_map", "layout_recall"]), strata, "layout_map"),
        "",
        r"\par\smallskip recall@IoU 0.5 per stratum",
        "",
        *_strata_table_tex(report_mod.strata_summary(device_rows, ["layout_map", "layout_recall"]), strata, "layout_recall"),
        r"\end{document}",
    ]) + "\n"
    return md, tex


def _strata_table_tex(grouped: dict, strata: list[str], key: str) -> list[str]:
    """Tabla LaTeX (motor × estrato) del pivote de una métrica (`key`)."""
    return [
        r"\begin{tabular}{l" + "r" * len(strata) + "}",
        r"\toprule",
        "Engine (variant) & " + " & ".join(_tex_escape(s.replace(" × ", "x"))
                                            for s in strata) + r" \\",
        r"\midrule",
        *_strata_tex_rows(grouped, strata, key),
        r"\bottomrule",
        r"\end{tabular}",
    ]


def _strata_tex_rows(grouped: dict, strata: list[str], key: str) -> list[str]:
    """Filas LaTeX del pivote por estrato (motor × estrato) de una métrica (`key`)."""
    rows = []
    for motor in sorted({m for m, _s in grouped}):
        cells = []
        for stratum in strata:
            values = (grouped.get((motor, stratum)) or {}).get(key) or []
            cells.append(f"{sum(values) / len(values):.3f}" if values else "---")
        rows.append(_tex_escape(motor) + " & " + " & ".join(cells) + r" \\")
    return rows


def main() -> int:
    md, tex = build()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "benchmark_table.md").write_text(md, encoding="utf-8")
    (OUT_DIR / "benchmark_table.tex").write_text(tex, encoding="utf-8")
    print(f"[layout.table] -> {OUT_DIR / 'benchmark_table.md'}")
    print(f"[layout.table] -> {OUT_DIR / 'benchmark_table.tex'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
