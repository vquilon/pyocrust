#!/usr/bin/env python
"""Calidad vs tiempo por feature: **una gráfica multigráfica** (Y = índice de
calidad, X = ms por página/unidad).

Complementa a `summary.py` (que solo compara calidad). Reutiliza su parser de las
tablas `## Comparativa` de `features/<feature>/REPORT.md` y produce
`SUMMARY_QUALITY_VS_TIME.{png,svg}` + `QUALITY_VS_TIME.md`.

* Un **panel por feature** (9).
* Cada **punto** es un motor **medido** en `features/<feature>/REPORT*.md`:
  - eje X → su columna `ms/<unidad>` (ms/página, ms/imagen, ms/fórmula, ms/línea…);
    se prefiere ms frente a páginas/s porque así se lee calidad vs tiempo.
  - eje Y → su columna titular de calidad (`↑`).
* El **device** (cpu/gpu) se lee de la línea `**device**` del provenance del
  reporte y se anota en el punto; sin él queda `?`. Nunca se inventa un device.

Un panel con un solo motor es válido (queda un punto): es el estado real mientras
no se midan alternativas, y por eso los huecos **no** se rellenan. Para que un
motor entre, hay que medirlo con su banco (`features/<feature>/bank.py`) y
regenerar su `REPORT.md`.

Uso:
    .venv/Scripts/python.exe benchmarks/features/quality_vs_time.py
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

# Reutiliza el parser de tablas y la lista de features de `summary.py`: una sola
# fuente de verdad para "qué features hay y cuál es su métrica titular".
from summary import FEATURES, _clean, _num, _rows_from, feature_title  # noqa: E402

# Nombre corto para que la anotación del punto no se solape ni ocupe el panel.
_SHORT = {
    "pyocrust_formulanet (direct)": "pyocrust_formulanet",
    "pyocrust_formula (pp-formulanet-s)": "pyocrust_formula",
    "pyocrust_structure (default)": "pyocrust_structure",
    "pyocrust_layout (default)": "pyocrust_layout",
    "pyocrust_table (default)": "pyocrust_table",
    "pyocrust_orientation (default)": "pyocrust_orientation",
    "pyocrust_textline (default)": "pyocrust_textline",
    "pyocrust_rectify (default)": "pyocrust_rectify",
    "pyocrust (tiny)": "pyocrust (tiny)",
}


def _short(name: str) -> str:
    return _SHORT.get(name, name)


def _device(lines: list[str]) -> str:
    """Device declarado en la línea `**device**: \\`cpu\\`` del provenance."""
    for line in lines:
        if "**device**" in line:
            for token in line.split("`"):
                tok = token.strip()
                if tok in ("cpu", "gpu"):
                    return tok
    return "?"


def parse_quality_time(feature: str, titular: str | None) -> tuple[list[tuple[str, float, float]], str, str]:
    """(puntos, device, unidad) leyendo la tabla `## Comparativa`.

    Cada punto es `(motor, ms, calidad)`; `unidad` es la etiqueta real de la
    columna de tiempo (p. ej. `ms/img`). Fila sin `ms/` o sin calidad legible se
    omite (no se rellena con cero). `titular=None` (seal) devuelve vacío.
    """
    p = BENCH / "features" / feature / "REPORT.md"
    if titular is None or not p.exists():
        return [], "?", ""
    lines = p.read_text(encoding="utf-8").splitlines()
    device = _device(lines)
    start = next((i for i, ln in enumerate(lines)
                  if ln.strip().lower().startswith("## comparativa")), None)
    if start is None:
        return [], device, ""
    header, rows = _rows_from(lines, start + 1)
    if not header:
        return [], device, ""
    qkey = next((k for k in header if k.startswith(titular)), None)
    mkey = next((k for k in header if k.lower().startswith("ms/")), None)
    if qkey is None or mkey is None:
        return [], device, ""
    qi, mi = header.index(qkey), header.index(mkey)
    points: list[tuple[str, float, float]] = []
    for cells in rows:
        if qi >= len(cells) or mi >= len(cells):
            continue
        ms, quality = _num(cells[mi]), _num(cells[qi])
        if ms is None or quality is None:
            continue
        points.append((_short(_clean(cells[0])), ms, quality))
    return points, device, mkey


def _ms_ticks(ax) -> None:
    """Eje X en milisegundos legibles: entero con separador de miles.

    Evita el `1e4` que matplotlib pone por defecto (offset/notacion cientifica)
    y deja ticks redondos que no se solapan. En ejes log el `MaxNLocator`
    reparte en escala LINEAL y amontona los ticks (p. ej. 250/500/750/1 000 en
    `orientation`): ahí se usa el localizador logarítmico, con tramos iguales en
    log y sin solape.
    """
    from matplotlib.ticker import FuncFormatter, LogLocator, MaxNLocator, NullFormatter

    fmt = FuncFormatter(lambda v, _pos: f"{v:,.0f}")
    ax.xaxis.set_major_formatter(fmt)
    ax.xaxis.set_minor_formatter(NullFormatter())
    if ax.get_xscale() == "log":
        ax.xaxis.set_major_locator(LogLocator(base=10.0, numticks=6))
    else:
        ax.xaxis.set_major_locator(MaxNLocator(nbins=4, integer=True))


def _panel(ax, points, title, device) -> None:
    if not points:
        ax.axis("off")
        ax.set_title(f"{title}\n(pendiente: sin tiempo medido)", fontsize=9, color="#888")
        return
    xs = [p[1] for p in points]
    ys = [p[2] for p in points]
    for name, ms, q in points:
        py = "pyocrust" in name
        ax.scatter(ms, q, s=70, zorder=3,
                   color="#2e7d32" if py else "#3b6fb0",
                   marker="o" if device != "gpu" else "*",
                   edgecolor="white", linewidth=0.8)
        ax.annotate(name, (ms, q), textcoords="offset points", xytext=(7, 5),
                    fontsize=6.5, color="#333333")
    # Escala: log sólo cuando el rango abarca >1 década (ahí el log aporta y deja
    # ticks de década repartidos); si no, lineal, que con `MaxNLocator` da ticks
    # redondos sin amontonar (un log sobre un rango estrecho los apila).
    if min(xs) > 0 and len(points) > 1 and max(xs) / min(xs) > 10:
        ax.set_xscale("log")
        lo = 10 ** math.floor(math.log10(min(xs)))
        hi = 10 ** math.ceil(math.log10(max(xs)))
        ax.set_xlim(lo, hi)
    elif len(points) == 1 and min(xs) > 0:
        # un solo punto: no hay rango que autoscale, se deja aire alrededor
        ax.set_xlim(min(xs) * 0.6, min(xs) * 1.5)
    _ms_ticks(ax)
    ax.set_yscale("linear")
    lo, hi = min(ys), max(ys)
    pad = (hi - lo) * 0.25 or 0.05
    ax.set_ylim(max(0.0, lo - pad), hi + pad)
    ax.set_xlabel("ms por unidad ↓ (izquierda = mejor)", fontsize=7)
    ax.set_ylabel("índice de calidad ↑", fontsize=7)
    ax.grid(True, which="major", alpha=0.18)
    ax.set_title(f"{title}  ·  device: {device}\n{len(points)} motor(es) MEDIDO(s) · mismo GT", fontsize=9)
    ax.tick_params(labelsize=7)
    ax.spines[["top", "right"]].set_visible(False)


def main() -> int:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    n = len(FEATURES)
    cols = 3
    rows = math.ceil(n / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(16, 4.0 * rows))
    axes = axes.ravel()

    md = ["# Calidad vs tiempo por feature — un panel por feature", "",
          "> Cada punto es un motor **medido** (`features/<feature>/REPORT.md`).",
          "> X = `ms` por unidad (izquierda = mejor) · Y = índice de calidad (arriba = mejor).",
          "> Un panel con un solo punto significa: **no hay alternativas medidas** para esa",
          "> feature todavía; el hueco se ve, no se rellena.",
          ">",
          "> **Solo motores medidos** (mismo banco/GT por panel): aquí **no** hay referencias",
          "> externas. Por eso puede contradecir [`SUMMARY.md`](SUMMARY.md), que sí añade",
          "> referencias de **otro dataset/métrica** (p. ej. los YOLO sobre DocLayNet en `layout`).", "",
          "## Mismas condiciones para todos los motores", "",
          "- **Mismo host y mismo intérprete**: el `.venv` del repo (la versión de Python y el",
          "  resto del runtime quedan en el `provenance` de cada `REPORT.md`). El *device* se",
          "  anota en el título de cada panel.",
          "- **Mismo banco y mismo GT**: todas las filas de un panel salen del mismo",
          "  `bank.py`, el mismo dataset anotado y el mismo `--limit`/`warmup`.",
          "- Un **modelo a la vez** (nunca dos motores cargados en paralelo).",
          "- El tiempo es **inferencia + post-proceso**: excluye carga de modelo y descarga.",
          "  `ultralytics` cronometra además su preprocesado interno (nota en el README).",
          "- El **nombre del motor lleva el tamaño del modelo** (p. ej. `yolov10x (DocLayNet) (31.7M)`).",
          ""]

    for k, (feature, titular) in enumerate(FEATURES):
        points, device, unit = parse_quality_time(feature, titular)
        title = feature_title(feature)
        _panel(axes[k], points, title, device)
        md += [f"## {title} — device `{device}` · SOLO motores medidos", ""]
        if points:
            md += [f"| Motor | {unit} | calidad ↑ |", "| :--- | ---: | ---: |"]
            for name, ms, q in sorted(points, key=lambda p: p[1]):
                mark = "**" if "pyocrust" in name else ""
                md.append(f"| {mark}{name}{mark} | {ms:.0f} | {q:.3f} |")
        else:
            md.append("_Sin tiempo medido todavía._")
        md.append("")

    for ax in axes[n:]:
        ax.axis("off")

    from matplotlib.lines import Line2D

    fig.legend(handles=[
        Line2D([], [], marker="o", linestyle="", color="#2e7d32", label="pyocrust (medido)"),
        Line2D([], [], marker="o", linestyle="", color="#3b6fb0", label="alternativa (medida)"),
    ], loc="lower center", bbox_to_anchor=(0.5, 0.045), ncol=2, frameon=False, fontsize=10)
    fig.suptitle("pyocrust — calidad vs tiempo por feature · SOLO motores medidos (mismo GT por panel)",
                 fontsize=14)
    fig.text(0.5, 0.022,
             "Cada punto es un motor medido con el mismo banco/GT del panel: aquí NO hay referencias externas. "
             "Puede contradecir SUMMARY.png, que sí añade referencias de OTRO dataset/métrica "
             "(p. ej. los YOLO sobre DocLayNet en layout).",
             ha="center", fontsize=8, color="#555555")
    fig.text(0.5, 0.004,
             "Mismo host/.venv y un modelo a la vez · ms = inferencia+post-proceso (sin carga ni descarga) · el nombre lleva el tamaño del modelo.",
             ha="center", fontsize=7.5, color="#777777")
    fig.tight_layout(rect=(0, 0.10, 1, 0.96))
    for ext in ("png", "svg"):
        fig.savefig(BENCH / f"SUMMARY_QUALITY_VS_TIME.{ext}", dpi=150,
                    bbox_inches="tight", facecolor="white")
    plt.close(fig)
    (BENCH / "QUALITY_VS_TIME.md").write_text("\n".join(md), encoding="utf-8")
    print("[quality_vs_time] ->", BENCH / "SUMMARY_QUALITY_VS_TIME.png")
    print("[quality_vs_time] ->", BENCH / "QUALITY_VS_TIME.md")
    return 0


def _self_check() -> None:
    """El parser debe sacar >=2 motores con ms y calidad para `text` (tabla real)."""
    points, device, unit = parse_quality_time("text", "F1 palabra")
    assert len(points) >= 2, points
    assert all(ms > 0 and 0 <= q <= 1 for _n, ms, q in points), points
    assert unit.startswith("ms/"), unit
    assert device == "cpu", device
    # Una feature esqueleto (sin tabla) no inventa puntos.
    assert parse_quality_time("seal", None) == ([], "?", "")
    print("features.quality_vs_time self-check OK")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        _self_check()
    else:
        raise SystemExit(main())
