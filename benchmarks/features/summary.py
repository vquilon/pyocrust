#!/usr/bin/env python
"""Resumen de benchmarks de las 9 features (solo motores `medido`).

Genera `benchmarks/figures/SUMMARY.png` + `SUMMARY.svg` + `benchmarks/reports/SUMMARY.md`.

Un panel por feature, con **una sola clase de dato**:

* **`medido`** — números ejecutados en este repo (`reports/<feature>/REPORT.md`,
  sección `## Comparativa`). Barra sólida; `pyocrust` en verde.

No se publican **referencias externas** (valores de papers sobre otro dataset/GT):
una calidad medida sobre otro ground truth no es comparable y no entra en ninguna
tabla ni gráfica. Las features sin datos medidos salen como **`pendiente`** (sin
barras): nunca se inventan cifras.

Uso:
    .venv/Scripts/python.exe benchmarks/features/summary.py
"""
from __future__ import annotations

import math
import os
import re
import sys
import csv
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent
RESULTS = BENCH / "results"
REPORTS = BENCH / "reports"
FIGURES = BENCH / "figures"

# El registro del runner es la fuente única de nombres canónicos y licencias YOLO.
if str(BENCH) not in sys.path:
    sys.path.insert(0, str(BENCH))
from common.runner import (  # noqa: E402
    FORMULA_BACKENDS_EXCLUDED, LICENSES, MODEL_NAMES, YOLO_LAYOUT_MODELS,
)
from features._localization import english_markdown  # noqa: E402

# (feature, prefijo de la métrica titular ↑ o None). El título del panel NO se
# escribe a mano: sale de `feature_title()`, que lee el `dataset` REAL del
# `REPORT.md` de la feature (fuente única -> imposible que el título mienta).
FEATURES = [
    ("text", "F1 palabra"),
    ("formula", "Similitud"),
    ("layout", "mAP@IoU 0.5"),
    ("orientation", "accuracy"),
    ("rectification", "SSIM"),
    ("text_line", "accuracy"),
    ("seal", "recall@IoU 0.5"),
    ("table", "TEDS"),
    ("full_page", "Markdown F1"),
]

# token `dataset` del REPORT.md -> nombre legible para el título del panel.
# Solo es una etiqueta: el dato (qué dataset se midió) SIEMPRE sale del REPORT.
DATASET_TITLES = {
    "funsd": "FUNSD",
    "omnidocbench_formula": "OmniDocBench",
    "omnidocbench_layout": "OmniDocBench",
    "omnidocbench_table": "OmniDocBench",
    "omnidocbench_full_page": "OmniDocBench",
    "synthetic_orientation": "sintético",
    "synthetic_rectification": "sintético",
    "synthetic_text_line": "sintético",
    "synthetic_seal": "sintético",
}

# Solo la métrica titular por feature y el dataset real del REPORT (sin refs externas).
DATASET_RE = re.compile(r"\*\*dataset\*\*:\s*`([^`]+)`")

# Licencia de los motores de **comparación**, verificada en HuggingFace
# (`cardData.license`). Es **informativa**: sirve para señalar en el informe los
# que usan una licencia no permisiva (p. ej. AGPL-3.0). La **puerta** (los flags
# `license_commercial_use` / `license_acknowledge`) solo aplica a los modelos que
# usa `pyocrust`, que salen de `pyocrust.model_catalog()`.
EXTERNAL_LICENSE = {
    "rapidocr (default)": "Apache-2.0",
    "easyocr (default)": "Apache-2.0",
    "lcnet_doc_ori (onnxruntime)": "Apache-2.0",
    "lcnet_textline_ori (onnxruntime)": "Apache-2.0",
    "uvdoc (onnxruntime)": "Apache-2.0",
    "onnx_seal_det (onnxruntime)": "Apache-2.0",
    "docling_heron_101 (default)": "Apache-2.0",
    "docling_heron_101": "Apache-2.0",
    "tatr (default)": "MIT",
    "tatr": "MIT",
    # El motor se etiqueta por su `model_name` (no por el id del backend).
    "table-transformer-structure-recognition (default)": "MIT",
    "table-transformer-structure-recognition": "MIT",
    # Otras alternativas de `table`: SLANet (PaddleOCR) y TableFormer (docling).
    "paddleocr_slanet (paddleocr)": "Apache-2.0",
    "paddleocr_slanet": "Apache-2.0",
    "SLANet_plus (paddleocr)": "Apache-2.0",
    "docling_tableformer (docling)": "MIT",
    "docling_tableformer": "MIT",
    "tableformer (docling)": "MIT",
    "pix2tex (default)": "MIT",
    "paddle_latex_ocr (PP-FormulaNet_plus-M)": "Apache-2.0",
    "paddle_latex_ocr (PP-FormulaNet-S)": "Apache-2.0",
    "paddle_latex_ocr": "Apache-2.0",
    # YOLO documentales: omoured = AGPL-3.0 (copyleft, no permisiva), Armaggheddon = MIT.
    "yolo26m (21.8M)": "MIT",
    "yolo26m": "MIT",
    "yolov10x (31.7M)": "AGPL-3.0",
    "yolov10b (20.5M)": "AGPL-3.0",
    "yolov10x": "AGPL-3.0",
    "yolov10b": "AGPL-3.0",
    "YOLOv10-x": "AGPL-3.0",
    "YOLOv10-b": "AGPL-3.0",
    "YOLOv10-l": "AGPL-3.0",
    "YOLOv10-m": "AGPL-3.0",
    "YOLOv10-s": "AGPL-3.0",
    "YOLOv10-n": "AGPL-3.0",
}


def _license_for(motor: str) -> str:
    """Licencia de un motor: del catálogo si es de `pyocrust`, verificada en HF
    si es de comparación (vacía si no se pudo verificar: nunca se inventa)."""
    if motor in LICENSES:
        return LICENSES[motor]
    for backend, license_name in LICENSES.items():
        model_name = MODEL_NAMES[backend][0]
        if motor == model_name or motor.startswith(f"{model_name} ("):
            return license_name
    if "indra" in motor:
        return "OpenRAIL-M-Mod"
    # Los modelos de pyocrust se etiquetan por `model_name` (p. ej.
    # `pp-doclayoutv3 (130M)`), no por el id del backend: Todos son Apache-2.0.
    for backend, (model_name, _variant) in MODEL_NAMES.items():
        if backend.startswith("pyocrust") and (motor == model_name or motor.startswith(f"{model_name} (")):
            return "Apache-2.0"
    if motor.startswith("pyocrust"):
        return "Apache-2.0"
    base = motor.split(" (")[0]
    for key in (motor, base, f"{base} (default)"):
        if key in EXTERNAL_LICENSE:
            return EXTERNAL_LICENSE[key]
    return ""


def _collect_rows() -> dict[tuple[str, str, str], list[dict]]:
    """{(feature, device, backend): filas} de **una sola** corrida de referencia por device.

    Usa `report.latest_run(feature, root, device)` como fuente unica — **no** "el run
    mas reciente de cada motor". Elegir por motor mezclaba corridas con distinto
    numero de filas (p. ej. `pp-doclayoutv3` cpu `n=60` junto a docling `n=40` y
    `pp_structurev3` `n=20`): una comparativa con distinto `n` **no es comparable**.
    Los motores que no esten en la corrida de referencia no entran en la tabla, en
    vez de colarse desde otra corrida.
    """
    from features.report import latest_run, run_csv  # perezoso: evita ciclo de import

    out: dict[tuple[str, str, str], list[dict]] = {}
    for feature, _titular in FEATURES:
        for device, root in (("cpu", RESULTS), ("gpu", RESULTS / "_gpu")):
            run = latest_run(feature, root=root, device=device)
            csv_path = run_csv(run) if run else None
            if csv_path is None:
                continue
            by_key: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
            for r in csv.DictReader(csv_path.read_text(encoding="utf-8").splitlines()):
                if r.get("status") != "ok" or (r.get("device_requested") or device) != device:
                    continue
                # `formula` no compara OCR de texto: no emiten LaTeX.
                if feature == "formula" and r["backend"] in FORMULA_BACKENDS_EXCLUDED:
                    continue
                by_key[(feature, device, r["backend"])].append(r)
            out.update(by_key)
    return out


_YOLO_VERSION = re.compile(r"_(?:v|y)(8|10|11|12|26)[a-z]$")
# Older generic aliases are not part of the verified 39-model DocLayNet inventory.
_LEGACY_YOLO_LAYOUT_BACKENDS = {"yolov10x", "yolov10b", "yolo26m"}


def _yolo_scores(rows: dict[tuple[str, str, str], list[dict]] | None = None
                 ) -> dict[str, dict[str, dict[str, list[float]]]]:
    """mAP@0.5 de los YOLO verificados, por versión → backend → device.

    CPU manda sobre GPU: la medida en GPU es un respaldo, así un modelo con run
    duplicada no puede sesgar su propia puntuación.
    """
    rows = _collect_rows() if rows is None else rows
    scores: dict[str, dict[str, dict[str, list[float]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )
    for (feature, device, backend), measurements in rows.items():
        match = _YOLO_VERSION.search(backend)
        if feature != "layout" or backend not in YOLO_LAYOUT_MODELS or not match:
            continue
        for row in measurements:
            if row.get("dataset") != "omnidocbench_layout":
                continue
            quality = _num(row.get("layout_map", ""))
            if quality is not None:
                scores[match.group(1)][backend][device].append(quality)
    return scores


def _yolo_mean(by_device: dict[str, list[float]]) -> float | None:
    values = by_device.get("cpu") or [v for device in by_device.values() for v in device]
    return sum(values) / len(values) if values else None


def _checkpoint_bytes(path: str | None) -> int | None:
    try:
        return Path(path).stat().st_size if path else None
    except OSError:
        return None


def size_matched_yolo_layout_backend(rows: dict[tuple[str, str, str], list[dict]] | None = None
                                    ) -> str | None:
    """El YOLO cuyo checkpoint más se acerca en bytes al de `pyocrust_layout`.

    Es el único punto del panel resumen que compara modelos de **tamaño parecido**
    (~130 MB): el resto de YOLO son bastante más pequeños y su tiempo no sería
    una comparación equiparable contra `pp-doclayoutv3`.
    """
    target = _checkpoint_bytes(os.environ.get("OAR_HOME", str(Path.home() / ".oar"))
                               + "/pp-doclayoutv3.onnx")
    if target is None:
        return None
    best, best_delta = None, None
    for backend, path in YOLO_LAYOUT_MODELS.items():
        size = _checkpoint_bytes(path)
        if size is None:
            continue
        delta = abs(size - target)
        if best_delta is None or delta < best_delta:
            best, best_delta = backend, delta
    return best


def summary_yolo_layout_backends(rows: dict[tuple[str, str, str], list[dict]] | None = None
                                 ) -> set[str]:
    """YOLO que sobreviven en los paneles resumen (`SUMMARY`, `SCOREBOARD`, `QUALITY_VS_TIME`).

    Dos cortes, en orden:

    1. **Uno por versión, cruzando autores.** De todas las variantes medidas de una
       versión (v8/v10/v11/v12/y26), gana la de mejor mAP@0.5 **sin mirar el
       autor**: si tres autores tienen un yolo10, en el resumen queda solo el
       yolo10 del que mejor puntúa. No se arrastra un proveedor entero por su
       mejor modelo, ni se exige que un autor cubra todas las versiones.
    2. **El de tamaño similar a `pyocrust`.** Se añade aunque repita versión.

    Los informes **por feature** no pasan por aquí: `REPORT.md`,
    `benchmark_table.*` y `LAYOUT_ALL_MODELS` conservan los 39 modelos medidos.
    """
    scores = _yolo_scores(rows)
    means: dict[str, float] = {}
    for models in scores.values():
        for backend, by_device in models.items():
            mean = _yolo_mean(by_device)
            if mean is not None:
                means[backend] = mean
    if not means:
        return set()
    # Un ganador por versión, elegido entre **todos** los autores (desempate por
    # nombre para que el resultado sea determinista).
    winners: set[str] = set()
    for models in scores.values():
        pool = {backend: means[backend] for backend in models if backend in means}
        if pool:
            winners.add(max(pool, key=lambda backend: (pool[backend], backend)))
    size_matched = size_matched_yolo_layout_backend(rows)
    if size_matched and size_matched in means:
        winners.add(size_matched)
    return winners


def collect_rows() -> dict[tuple[str, str, str], list[dict]]:
    """Latest rows shared by SUMMARY/SCOREBOARD, with the summary YOLO subset."""
    rows = _collect_rows()
    winners = summary_yolo_layout_backends(rows)
    return {
        key: measurements for key, measurements in rows.items()
        if key[0] != "layout" or (
            key[2] not in _LEGACY_YOLO_LAYOUT_BACKENDS
            and (key[2] not in YOLO_LAYOUT_MODELS or key[2] in winners)
        )
    }


# Columna de calidad por feature en los CSV de resultados (la del REPORT puede
# diferir en la etiqueta: «mAP@IoU 0.5» -> `layout_map`).
QUALITY_COL = {
    "text": "word_f1",
    "formula": "latex_sim",
    "layout": "layout_map",
    "orientation": "ori_acc",
    "rectification": "rect_sim",
    "text_line": "ori_acc",
    "seal": "box_recall",
    "table": "table_teds",
    "full_page": "markdown_f1",
}


def _motor_label(backend: str, variant: str, model_name: str = "") -> str:
    """Nomenclatura unica del banco: el **modelo real** (`model_name`) con la
    variante entre parentesis; `backend` solo como respaldo si no hay
    `model_name`. Iguala a `report.py` (`row.get("model_name") or row["backend"]`),
    de modo que `REPORT`, `SUMMARY`, `SCOREBOARD` y `QUALITY_VS_TIME` etiquetan
    el mismo motor con la misma cadena."""
    motor = model_name or backend
    return f"{motor} ({variant})" if variant and variant != "default" else motor


def _is_pyocrust(motor: str, backend: str = "") -> bool:
    """True si la fila es un modelo de `pyocrust` (catalogo Apache-2.0).

    Con la nomenclatura unica la etiqueta es el `model_name` (p. ej.
    `pp-lcnet_x1_0_doc_ori (6.8M)`), no el id del backend, asi que el criterio
    de "fila propia de pyocrust" no puede ser `"pyocrust" in motor`. Cuando se
    conoce el `backend` manda ese; el chequeo por nombre es solo el respaldo
    para los informes que parsean texto (p. ej. `QUALITY_VS_TIME`).
    """
    if backend:
        return backend.startswith("pyocrust")
    base = motor.split(" (")[0]
    return any(b.startswith("pyocrust") and m == base for b, (m, _v) in MODEL_NAMES.items())


def measured_from_rows(feature: str) -> dict[tuple[str, str], tuple[float, int, str]]:
    """Motores medidos por device: `(motor, device) -> (calidad, n, backend)`.

    Misma fuente que el SCOREBOARD (`collect_rows`), asi los dos informes no
    pueden divergir. El `n` es obligatorio y se muestra por fila/device: una
    corrida de 5 muestras no se confunde con una de 20 ni con otro device. El
    `backend` viaja con la fila para distinguir "modelo propio" aunque el
    `model_name` coincida con el de un motor externo (p. ej. `lcnet_doc_ori`
    y `pyocrust_orientation` comparten `pp-lcnet_x1_0_doc_ori`).
    """
    col = QUALITY_COL[feature]
    out: dict[tuple[str, str], tuple[float, int]] = {}
    for (f, device, backend), rws in collect_rows().items():
        if f != feature:
            continue
        vals = [r for r in rws if _num(r.get(col, "")) is not None]
        if not vals:
            continue
        label = _motor_label(
            backend, vals[0].get("model_variant", ""), vals[0].get("model_name", "")
        )
        key = (label, device)
        quality = sum(_num(r[col]) for r in vals) / len(vals)
        out[key] = (quality, len(rws), backend)
    return out


def parse_dataset(feature: str) -> str:
    """Token del `dataset`/GT realmente medido (`**dataset**: \\`x\\`` del REPORT)."""
    p = REPORTS / feature / "REPORT.md"
    if not p.exists():
        return ""
    m = DATASET_RE.search(p.read_text(encoding="utf-8"))
    return m.group(1) if m else ""


def feature_title(feature: str) -> str:
    """`<feature> — <dataset medido>`; el dataset viene del REPORT (fuente única)."""
    ds = parse_dataset(feature)
    if not ds:
        return feature
    return f"{feature} — {DATASET_TITLES.get(ds, ds)}"


# La calidad solo se publica sobre el dataset/GT propio de cada feature. No se
# comparan cifras entre datasets distintos: no hay mapa de notas de referencia.


def _clean(cell: str) -> str:
    return cell.strip().replace("**", "").replace("`", "")


def _num(cell: str) -> float | None:
    """Número de una celda; tolera el sufijo `%` (100.0% -> 1.0)."""
    raw = cell.strip()
    pct = "%" in raw
    try:
        v = float(raw.replace("%", "").strip())
    except ValueError:
        return None
    return v / 100.0 if pct else v


def _rows_from(lines, start_idx):
    header, rows = None, []
    for line in lines[start_idx:]:
        s = line.strip()
        if s.startswith("#") and rows:
            break
        if not s.startswith("|"):
            continue
        cells = [_clean(c) for c in s.strip("|").split("|")]
        if set("".join(cells)) <= set(":-"):
            continue
        if header is None:
            header = cells
        else:
            rows.append(cells)
    return header, rows


def parse_measured(feature: str, titular: str | None) -> dict[str, float]:
    if titular is None:
        return {}
    p = REPORTS / feature / "REPORT.md"
    if not p.exists():
        return {}
    lines = p.read_text(encoding="utf-8").splitlines()
    start = next((i for i, ln in enumerate(lines)
                  if ln.strip().lower().startswith("## comparativa")), None)
    if start is None:
        return {}
    header, rows = _rows_from(lines, start + 1)
    if not header:
        return {}
    key = next((k for k in header if k.startswith(titular)), None)
    if key is None:
        return {}
    idx = header.index(key)
    out: dict[str, float] = {}
    for cells in rows:
        if idx < len(cells):
            v = _num(cells[idx])
            if v is not None:
                out[cells[0]] = v
    return out


def _one_row_per_motor(measured: dict[tuple[str, str], tuple[float, int, str]]
                       ) -> dict[tuple[str, str], tuple[float, int, str]]:
    """Una **sola** fila por motor (CPU manda; GPU solo si no hay medida de CPU).

    El SUMMARY es **solo calidad**: repetir el mismo modelo sobre el mismo dataset
    dos veces (cpu y gpu) no aporta — el device se publica donde sí importa, en los
    informes con tiempos (`CPU_VS_GPU`, `QUALITY_VS_TIME`).
    """
    chosen: dict[str, tuple[tuple[str, str], tuple[float, int, str]]] = {}
    for key, value in measured.items():
        motor, device = key
        if motor not in chosen or device == "cpu":
            chosen[motor] = (key, value)
    return dict(chosen.values())


def _panel(ax, measured, title):
    entries = []  # (nombre, valor, origen, n, backend)
    entries += [(name, v, "medido", cnt, backend)
                for (name, _device), (v, cnt, backend) in measured.items()]
    if not entries:
        ax.axis("off")
        ax.set_title(f"{title}\n(pending: no measured data)", fontsize=9, color="#888")
        return
    entries.sort(key=lambda e: e[1])
    names = [e[0] for e in entries]
    vals = [e[1] for e in entries]
    counts = [e[3] for e in entries]
    colors = ["#2e7d32" if _is_pyocrust(n, backend) else "#607d8b"
              for n, _v, _origin, _cnt, backend in entries]
    bars = ax.barh(range(len(vals)), vals)
    for bar, c in zip(bars, colors):
        bar.set_color(c)
    for i, (v, cnt) in enumerate(zip(vals, counts)):
        label = f"{v:.3f} · n={cnt}" if cnt else f"{v:.3f}"
        ax.text(v + (max(vals) or 1) * 0.01, i, label, va="center", fontsize=7)
    ax.set_yticks(range(len(vals)))
    ax.set_yticklabels(names, fontsize=7)
    ax.set_xlim(0, (max(vals) or 1) * 1.22)
    ax.set_title(title, fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="x", labelsize=7)


def main() -> int:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    n = len(FEATURES)
    cols = 3
    rows = math.ceil(n / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(16, 4.0 * rows))
    axes = axes.ravel()

    md = ["# Resumen de benchmarks — 9 features (solo `medido`)", "",
          "> `medido` = ejecutado en este repo · `pendiente` = aún sin datos.",
          "> **No se publican referencias externas**: una calidad medida sobre otro",
          "> dataset/GT no es comparable, así que no entra en ninguna tabla ni gráfica.",
          "> Una fila por motor sobre **su mismo dataset** (el device solo se publica en los informes con tiempos). El `n` se declara por fila.",
          "> `license` es **informativa** (señala las no permisivas, p. ej. AGPL-3.0); la puerta solo aplica a los modelos de `pyocrust`.", ""]

    for k, (feature, titular) in enumerate(FEATURES):
        measured = _one_row_per_motor(measured_from_rows(feature))
        ds = parse_dataset(feature)
        title = feature_title(feature)
        plot_title = title.replace("sintético", "Synthetic")
        _panel(axes[k], measured, plot_title)
        status = "medido" if measured else "pendiente"
        src = f" · **dataset medido**: `{ds}`" if ds else ""
        md += [f"## {title} — `{status}`{src}", ""]
        if measured:
            md += ["| Motor | Valor | n | Origen | license |",
                   "| :--- | ---: | ---: | :--- | :--- |"]
            for (nm, _device), (v, cnt, backend) in sorted(measured.items(), key=lambda p: -p[1][0]):
                mark = "**" if _is_pyocrust(nm, backend) else ""
                md.append(f"| {mark}{nm}{mark} | {v:.3f} | {cnt} | medido | {_license_for(nm)} |")
        else:
            md.append("_Sin datos medidos todavía._")
        md.append("")

    for ax in axes[n:]:
        ax.axis("off")

    fig.legend(handles=[
        Patch(facecolor="#2e7d32", label="pyocrust (measured)"),
        Patch(facecolor="#607d8b", label="alternative (measured)"),
    ], loc="lower center", bbox_to_anchor=(0.5, 0.035), ncol=2, frameon=False, fontsize=10)
    fig.suptitle("pyocrust — benchmark results by feature (measured only)", fontsize=14)
    fig.text(0.5, 0.006,
             "Every bar is a MEASUREMENT on the panel's own dataset/ground truth. "
             "No external reference is published: quality is never compared across datasets.",
             ha="center", fontsize=8, color="#555555")
    fig.tight_layout(rect=(0, 0.075, 1, 0.96))
    FIGURES.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "svg"):
        fig.savefig(FIGURES / f"SUMMARY.{ext}", dpi=150, bbox_inches="tight", facecolor="white")
    summary_md = "\n".join(md)
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "SUMMARY.md").write_text(summary_md, encoding="utf-8")
    (REPORTS / "SUMMARY.en.md").write_text(english_markdown(summary_md), encoding="utf-8")
    print("[summary] ->", FIGURES / "SUMMARY.png")
    print("[summary] ->", REPORTS / "SUMMARY.md (+ SUMMARY.en.md)")
    return 0


def _self_check() -> None:
    """El título de cada panel lleva el dataset REAL del REPORT (nada a mano)."""
    for feature, _titular in FEATURES:
        token = parse_dataset(feature)
        assert token, f"{feature}: REPORT.md sin `**dataset**`"
        assert token in DATASET_TITLES, f"{feature}: dataset {token!r} sin etiqueta legible"
        title = feature_title(feature)
        assert title.startswith(f"{feature} — "), title
        assert DATASET_TITLES[token] in title, title
    print("features.summary self-check OK")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        _self_check()
    else:
        raise SystemExit(main())
