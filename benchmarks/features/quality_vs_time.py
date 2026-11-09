#!/usr/bin/env python
"""Calidad vs tiempo por feature: **una gráfica multigráfica** (Y = índice de
calidad, X = ms por página/unidad).

Complementa a `summary.py` (que solo compara calidad). Reutiliza su parser de las
tablas `## Comparativa` de `reports/<feature>/REPORT.md` y produce
`SUMMARY_QUALITY_VS_TIME_CPU.{png,svg}` + `SUMMARY_QUALITY_VS_TIME_GPU.{png,svg}` + `QUALITY_VS_TIME.md`.

* Un **panel por feature** (9).
* Cada **punto** es un motor **medido** en `reports/<feature>/REPORT*.md`:
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
REPORTS = BENCH / "reports"
FIGURES = BENCH / "figures"
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

# Reutiliza el parser de tablas y la lista de features de `summary.py`: una sola
# fuente de verdad para "qué features hay y cuál es su métrica titular".
from summary import (
    FEATURES, MODEL_NAMES, YOLO_LAYOUT_MODELS, _LEGACY_YOLO_LAYOUT_BACKENDS,
    _clean, _is_pyocrust, _license_for, _num, _rows_from, feature_title,
    summary_yolo_layout_backends,
)
from features._localization import english_markdown  # noqa: E402


def _device(lines: list[str]) -> str:
    """Device declarado en la línea `**device**: \\`cpu\\`` del provenance."""
    for line in lines:
        if "**device**" in line:
            for token in line.split("`"):
                tok = token.strip()
                if tok in ("cpu", "gpu"):
                    return tok
    return "?"


def parse_quality_time(feature: str, titular: str | None) -> tuple[list[tuple[str, float, float, str]], str, str]:
    """Puntos `(motor, ms, calidad, device)` desde Comparativa y CPU vs GPU.

    La tabla `Comparativa` aporta el device de provenance; `CPU vs GPU` añade
    solo las filas GPU cuyo provider fue un acelerador real. Nunca rellena celdas
    vacías.
    """
    p = REPORTS / feature / "REPORT.md"
    if titular is None or not p.exists():
        return [], "?", ""
    lines = p.read_text(encoding="utf-8").splitlines()
    default_device = _device(lines)
    start = next((i for i, ln in enumerate(lines)
                  if ln.strip().lower().startswith("## comparativa")), None)
    if start is None:
        return [], default_device, ""
    header, rows = _rows_from(lines, start + 1)
    if not header:
        return [], default_device, ""
    qkey = next((k for k in header if k.startswith(titular)), None)
    mkey = next((k for k in header if k.lower().startswith("ms/")), None)
    if qkey is None or mkey is None:
        return [], default_device, ""
    qi, mi = header.index(qkey), header.index(mkey)
    points: dict[tuple[str, str], tuple[str, float, float, str]] = {}
    for cells in rows:
        if qi >= len(cells) or mi >= len(cells):
            continue
        name = _clean(cells[0])
        ms, quality = _num(cells[mi]), _num(cells[qi])
        if ms is not None and quality is not None:
            points[(name, default_device)] = (name, ms, quality, default_device)

    # La tabla comparativa tiene los dos devices en columnas. No tratar N/A ni
    # un provider CPU como si fuesen un punto GPU.
    gpu_start = next((i for i, line in enumerate(lines)
                      if line.strip().lower().startswith("## cpu vs gpu")), None)
    if gpu_start is not None:
        gpu_header, gpu_rows = _rows_from(lines, gpu_start + 1)
        if gpu_header:
            # La cabecera es `<titular> ↑ (CPU)` y el titular de FEATURES es solo
            # el prefijo («Similitud» de «Similitud LaTeX ↑»): normalizando y
            # mirando prefijo+sufijo es el unico modo de casar sin tablas rotas.
            def _norm(text: str) -> str:
                return text.lower().replace("↑", "").replace("↓", "").replace(" ", "")

            def col_quality(device: str) -> int | None:
                d, t = _norm(f"({device})"), _norm(titular)
                # Columnas de CALIDAD de ese device: acaban en «(gpu)»/«(cpu)» y no
                # son tiempos. El titular de FEATURES es una pista, no un requisito:
                # se desfasa del encabezado real del informe («F1 palabra» vs
                # «Word F1», «Similitud LaTeX» vs «LaTeX similarity») y con el
                # `startswith` obligatorio se perdían enteras las filas GPU.
                cands = [i for i, key in enumerate(gpu_header)
                         if _norm(key).endswith(d) and "ms" not in _norm(key)]
                con_titular = [i for i in cands if _norm(gpu_header[i]).startswith(t)]
                if con_titular:
                    return con_titular[0]
                # Sin titular que case solo se acepta si hay UNA columna de calidad;
                # con varias, adivinar sería inventar la métrica.
                return cands[0] if len(cands) == 1 else None

            def col_suffix(suffix: str) -> int | None:
                s = _norm(suffix)
                return next((i for i, key in enumerate(gpu_header)
                             if _norm(key).endswith(s)), None)

            cpu_qi = col_quality("cpu")
            gpu_qi = col_quality("gpu")
            cpu_mi, gpu_mi = col_suffix("ms CPU"), col_suffix("ms GPU")
            provider_i = col_suffix("provider GPU")
            for cells in gpu_rows:
                if not cells:
                    continue
                name = _clean(cells[0])
                if cpu_qi is not None and cpu_mi is not None and max(cpu_qi, cpu_mi) < len(cells):
                    q, ms = _num(cells[cpu_qi]), _num(cells[cpu_mi])
                    if q is not None and ms is not None:
                        points[(name, "cpu")] = (name, ms, q, "cpu")
                if gpu_qi is not None and gpu_mi is not None and max(gpu_qi, gpu_mi) < len(cells):
                    provider = cells[provider_i].strip().lower() if provider_i is not None and provider_i < len(cells) else ""
                    q, ms = _num(cells[gpu_qi]), _num(cells[gpu_mi])
                    if provider in {"cuda", "directml", "tensorrt", "coreml", "openvino", "webgpu", "rocm", "mps"} and q is not None and ms is not None:
                        points[(name, "gpu")] = (name, ms, q, "gpu")
    if feature == "layout":
        selected = summary_yolo_layout_backends()
        all_labels, selected_labels = set(), set()
        for backend in YOLO_LAYOUT_MODELS:
            model, variant = MODEL_NAMES[backend]
            labels = {backend, model}
            if variant:
                labels.update({f"{backend} ({variant})", f"{model} ({variant})"})
            all_labels.update(labels)
            if backend in selected:
                selected_labels.update(labels)
        points = {key: point for key, point in points.items()
                  if point[0].split(" (")[0] not in _LEGACY_YOLO_LAYOUT_BACKENDS
                  and (point[0] not in all_labels or point[0] in selected_labels)}
    devices = {point[3] for point in points.values()}
    device = "+".join(d for d in ("cpu", "gpu") if d in devices) or default_device
    return list(points.values()), device, mkey


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


# Un color por FAMILIA (estilo Artificial Analysis: la leyenda agrupa por
# desarrollador, no por modelo). Se reutilizan los colores ya fijados en
# `features/layout/all_models.py` para que la misma familia tenga el mismo color
# en las dos figuras.
_COLORES_FAMILIA = {
    "PaddleOCR (PP-*)": "#238b57",
    "datalab (indra)": "#c44536",
    "hantian": "#2878b5",
    "omoured": "#d97706",
    "armaggheddon": "#7b61a8",
    "docling (IBM)": "#0f766e",
    "easyocr (JaidedAI)": "#a16207",
    "RapidAI": "#7c3aed",
    "Microsoft (TATR)": "#be123c",
    "pix2tex": "#0369a1",
    "UniMERNet": "#4d7c0f",
    "baseline (OpenCV)": "#6b7280",
}


def _familia(nombre: str) -> str:
    """Familia de un motor por su nombre visible (quién firma los pesos).

    El nombre lleva el runtime entre paréntesis (`pp-… (onnxruntime)`), así que
    los mismos pesos con otro runtime caen en la MISMA familia: el color agrupa
    por desarrollador y lo que distingue a pyocrust es la forma (★).
    """
    n = nombre.lower()
    if "indra" in n:
        return "datalab (indra)"
    if "paddle" in n or n.startswith(("pp-", "pp_", "slanet", "uvdoc")):
        return "PaddleOCR (PP-*)"
    if n.startswith("docling") or "tableformer" in n:
        return "docling (IBM)"
    for clave in ("hantian", "omoured", "armaggheddon"):
        if n.startswith(clave):
            return clave
    if "easyocr" in n:
        return "easyocr (JaidedAI)"
    if "rapidocr" in n:
        return "RapidAI"
    if "table-transformer" in n:
        return "Microsoft (TATR)"
    if "pix2tex" in n:
        return "pix2tex"
    if "unimernet" in n:
        return "UniMERNet"
    if "opencv" in n or "perspective" in n:
        return "baseline (OpenCV)"
    return "otros"


def _colores(feature_data) -> tuple[dict[str, str], dict[str, str]]:
    """(color por motor, color por familia) para la leyenda global."""
    nombres = sorted({n for _t, pts, _u in feature_data for n, _ms, _q, _d in pts})
    familia = {nombre: _familia(nombre) for nombre in nombres}
    por_familia = {f: _COLORES_FAMILIA.get(f, "#555555") for f in dict.fromkeys(familia.values())}
    return {nombre: por_familia[familia[nombre]] for nombre in nombres}, por_familia


def _frontera(points):
    """Motores que nadie domina: no existe otro con ≤ ms y ≥ calidad (mejor en uno).

    Es la envolvente que se dibuja punteada — un hecho del panel, no un ajuste.
    """
    return sorted((p for p in points if not any(
        o[1] <= p[1] and o[2] >= p[2] and (o[1] < p[1] or o[2] > p[2]) for o in points)),
        key=lambda p: p[1])


def _panel(ax, points, title, device, colores=None) -> None:
    colores = colores or {}
    points = [point for point in points if point[3] == device]
    if not points:
        ax.axis("off")
        ax.set_title(f"{title}\n(pending: no measured runtime)", fontsize=9, color="#888")
        return
    xs = [p[1] for p in points]
    ys = [p[2] for p in points]
    for name, ms, q, _point_device in points:
        py = _is_pyocrust(name)
        # La FORMA distingue pyocrust del resto (★ vs ●) y el COLOR identifica al
        # motor (leyenda global al pie). El device ya lo dice el título del panel.
        ax.scatter(ms, q, s=110 if py else 60, zorder=3,
                   color=colores.get(name, "#3b6fb0"),
                   marker="*" if py else "o",
                   edgecolor="white", linewidth=0.8)
        # Etiqueta SIEMPRE a la derecha del punto y pegada a él: desplazada en
        # puntos de pantalla (no en datos) y sin repartidores de colisiones — lo
        # que se separa del punto deja de leerse.
        ax.annotate(name, xy=(ms, q), xytext=(5, 0), textcoords="offset points",
                    ha="left", va="center", fontsize=6.5, color="#333333")
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
    pad = (hi - lo) * 0.18 or 0.05
    ax.set_ylim(max(0.0, lo - pad), hi + pad)
    # Cuadrante que interesa: MENOS tiempo (izquierda) y MÁS calidad (arriba).
    # El corte es la mediana del propio panel — un dato del panel, no un umbral
    # inventado— y va sombreado para que el «bueno» se vea de un vistazo.
    from matplotlib.patches import Rectangle

    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    xm, ym = sorted(xs)[len(xs) // 2], sorted(ys)[len(ys) // 2]
    if xm > x0 and y1 > ym:
        ax.add_patch(Rectangle((x0, ym), xm - x0, y1 - ym, zorder=0,
                               facecolor="#2e7d32", alpha=0.07, edgecolor="none"))
    # Frontera de Pareto (punteada): los motores que nadie domina — mismo lenguaje
    # visual que la referencia, pero como envolvente y no como recta ajustada: es
    # un hecho del panel, no un modelo inventado.
    frontera = _frontera(points)
    if len(frontera) > 1:
        ax.plot([p[1] for p in frontera], [p[2] for p in frontera], ":",
                color="#777777", lw=1.2, zorder=2)
    ax.set_xlabel("Runtime per unit (ms) ↓ (left = faster)", fontsize=7)
    ax.set_ylabel("Quality score ↑", fontsize=7)
    ax.grid(True, which="major", alpha=0.18)
    ax.set_title(f"{title}  ·  device: {device}\n{len(points)} measured engine(s)", fontsize=9)
    ax.tick_params(labelsize=7)
    ax.spines[["top", "right"]].set_visible(False)


def main() -> int:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    feature_data = []

    md = ["# Calidad vs tiempo por feature — tabla unificada CPU/GPU", "",
          "> Cada punto es un motor **medido** (`reports/<feature>/REPORT.md`).",
          "> X = `ms` por unidad (izquierda = mejor) · Y = índice de calidad (arriba = mejor).",
          "> Un panel con un solo punto significa: **no hay alternativas medidas** para esa",
          "> feature todavía; el hueco se ve, no se rellena.",
          ">",
          "> **Solo motores medidos** (mismo banco por panel): no hay referencias",
          "> externas, ni aquí ni en [`SUMMARY.md`](SUMMARY.md). Una calidad medida sobre",
          "> otro dataset/GT no es comparable y no se publica en ninguna tabla.", "",
          "## Mismas condiciones para todos los motores", "",
          "- **Mismo host y mismo intérprete**: el `.venv` del repo (la versión de Python y el",
          "  resto del runtime quedan en el `provenance` de cada `REPORT.md`). El *device* se",
          "  anota en el título de cada panel.",
          "- **Mismo banco**: todas las filas de un panel salen del mismo",
          "  `bank.py`, el mismo dataset anotado y el mismo `--limit`/`warmup`.",
          "- Un **modelo a la vez** (nunca dos motores cargados en paralelo).",
          "- El tiempo es **inferencia + post-proceso**: excluye carga de modelo y descarga.",
          "  `ultralytics` cronometra además su preprocesado interno (nota en el README).",
          "- El **nombre del motor lleva el tamaño del modelo** (p. ej. `yolov10x (DocLayNet) (31.7M)`).",
          ""]

    for k, (feature, titular) in enumerate(FEATURES):
        points, device, unit = parse_quality_time(feature, titular)
        title = feature_title(feature)
        feature_data.append((title, points, unit))
        md += [f"## {title} — device `{device}` · motores medidos", ""]
        if points:
            md += [f"| Motor | Device | {unit} | calidad ↑ | license |", "| :--- | :--- | ---: | ---: | :--- |"]
            for name, ms, q, point_device in sorted(points, key=lambda p: (p[3], p[1], p[0])):
                mark = "**" if _is_pyocrust(name) else ""
                md.append(f"| {mark}{name}{mark} | {point_device} | {ms:.0f} | {q:.3f} | {_license_for(name)} |")
        else:
            md.append("_Sin tiempo medido todavía._")
        md.append("")

    from matplotlib.lines import Line2D

    for device in ("cpu", "gpu"):
        n = len(feature_data)
        # DOS columnas, no tres: con 9 features a 3 por fila cada panel queda tan
        # estrecho que en pantalla no se lee y las etiquetas no caben. Es la causa
        # real de que el gráfico «se vea pequeño», no el tamaño del lienzo.
        cols = 2
        rows = math.ceil(n / cols)
        fig, axes = plt.subplots(rows, cols, figsize=(13, 3.6 * rows))
        axes = axes.ravel()
        colores, por_familia = _colores(feature_data)
        for k, (title, points, _unit) in enumerate(feature_data):
            _panel(axes[k], points, title.replace("sintético", "Synthetic"), device, colores)
        for ax in axes[n:]:
            ax.axis("off")

        # Leyenda global por FAMILIA (quién firma los pesos), no por motor: el
        # nombre va en la etiqueta de cada punto. Mismo título que la figura de
        # `layout/all_models.py` para que las dos se lean igual.
        fig.legend(handles=[
            Line2D([], [], marker="o", linestyle="", markersize=7, color=color, label=fam)
            for fam, color in sorted(por_familia.items())
        ], loc="lower center", bbox_to_anchor=(0.5, 0.032), ncol=6, frameon=False, fontsize=8,
            title="Color: model family", title_fontsize=8.5, handletextpad=0.3, columnspacing=1.4)
        fig.suptitle(f"pyocrust — quality vs. runtime by feature · {device.upper()}", fontsize=14)
        fig.text(0.5, 0.014,
                 f"★ pyocrust · ● alternativa · zona verde = menos tiempo y más calidad (mediana del panel) · "
                 f"línea punteada = frontera de Pareto (ningún motor la domina). "
                 f"Cada punto es una medición {device.upper()} del mismo banco; referencias externas excluidas.",
                 ha="center", fontsize=8, color="#555555")
        fig.tight_layout(rect=(0, 0.10, 1, 0.96))
        FIGURES.mkdir(parents=True, exist_ok=True)
        for ext in ("png", "svg"):
            fig.savefig(FIGURES / f"SUMMARY_QUALITY_VS_TIME_{device.upper()}.{ext}", dpi=150,
                        bbox_inches="tight", facecolor="white")
        plt.close(fig)
        print(f"[quality_vs_time] -> {FIGURES / f'SUMMARY_QUALITY_VS_TIME_{device.upper()}.png'}")
    quality_md = "\n".join(md)
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "QUALITY_VS_TIME.md").write_text(quality_md, encoding="utf-8")
    (REPORTS / "QUALITY_VS_TIME.en.md").write_text(english_markdown(quality_md), encoding="utf-8")
    print("[quality_vs_time] ->", REPORTS / "QUALITY_VS_TIME.md (+ .en.md)")
    return 0


def _self_check() -> None:
    """Etiquetas-dentro-del-panel (independiente de datos) + contrato del parser."""
    # Regresión vista de verdad: si las etiquetas se salen del panel,
    # `savefig(bbox_inches="tight")` hincha el lienzo y los paneles quedan
    # diminutos con el texto repartido por el blanco de al lado. Va PRIMERO: las
    # aserciones del parser dependen del estado de los informes.
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.text import Annotation

    puntos = [(f"motor-{i:02d}", 10.0 * (i + 1), 0.5 + 0.001 * i, "cpu") for i in range(9)]
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    _panel(ax, puntos, "layout", "cpu")
    fig.canvas.draw()
    etiquetas = [c for c in ax.get_children() if isinstance(c, Annotation)]
    plt.close(fig)
    assert len(etiquetas) == len(puntos), f"inspeccionadas {len(etiquetas)} etiquetas, esperadas {len(puntos)}"
    # Contrato: la etiqueta va PEGADA a su punto (desplazada a la derecha en
    # puntos de pantalla, no en datos). Si alguna se despegara del dato —que es
    # lo que dejaba la figura ilegible— su ancla dejaría de coincidir con el punto.
    anclas = {(round(t.xy[0], 6), round(t.xy[1], 6)) for t in etiquetas}
    esperado = {(round(ms, 6), round(q, 6)) for _n, ms, q, _d in puntos}
    assert esperado <= anclas, f"etiquetas despegadas de su punto: {sorted(esperado - anclas)}"
    # El mapa de familias: una regla mal escrita caería en «otros» y pintaría el
    # punto en gris de relleno sin avisar de que la agrupación está rota.
    conocidos = ("easyocr (default)", "pp_ocrv6 (tiny)", "rapidocr (default)",
                 "uvdoc (onnxruntime)", "docling-default (pipeline)", "hantian/v8-n",
                 "armaggheddon/y26-n (2.6M)", "table-transformer-structure-recognition (default)",
                 "pix2tex (default)", "unimernet (tiny)", "perspective-4corner (baseline)",
                 "indra (math)", "PP-StructureV3 (paddleocr)", "pp-formulanet-s (direct)")
    sin_familia = [n for n in conocidos if _familia(n) not in _COLORES_FAMILIA]
    assert not sin_familia, f"motores sin familia declarada: {sin_familia}"
    # Frontera de Pareto con datos conocidos: `a` y `c` los domina `d` (misma
    # calidad en menos ms) y `b` no lo domina nadie (nadie llega a su calidad).
    ejemplo = [("a", 10.0, 0.5, "cpu"), ("b", 20.0, 0.9, "cpu"),
               ("c", 30.0, 0.5, "cpu"), ("d", 5.0, 0.5, "cpu")]
    assert [p[0] for p in _frontera(ejemplo)] == ["d", "b"], _frontera(ejemplo)

    points, device, unit = parse_quality_time("text", "F1 palabra")
    assert len(points) >= 2, points
    assert all(ms > 0 and 0 <= q <= 1 for _name, ms, q, _device in points), points
    assert {point[3] for point in points} >= {"cpu", "gpu"}, points
    assert unit.startswith("ms/"), unit
    assert device == "cpu+gpu", device
    # Una feature esqueleto (sin tabla) no inventa puntos.
    assert parse_quality_time("seal", None) == ([], "?", "")
    print("features.quality_vs_time self-check OK")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        _self_check()
    else:
        raise SystemExit(main())
