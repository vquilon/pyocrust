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

try:
    from .summary import EXCLUDED_MOTORS
except ImportError:  # ejecutado directamente como script
    from summary import EXCLUDED_MOTORS

RESULTS_DIR = BENCHMARKS_ROOT / "results"
# Runs GPU en su propia jerarquía (`--output-dir benchmarks/results/_gpu`), para
# que `latest_run` CPU (glob `results/<feature>/*/`) no se confunda con ellas.
GPU_RESULTS_DIR = RESULTS_DIR / "_gpu"
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


def latest_run(feature: str, root: Path = RESULTS_DIR, device: str = "cpu") -> Path | None:
    """Run de referencia para `device`: más muestras por motor, luego más motores.

    El filtro de device evita que una corrida GPU más reciente oculte la
    comparativa CPU de referencia. Los empates se resuelven por nombre de run.
    """
    base = root / feature
    runs = sorted((p for p in base.glob("*/") if any(p.glob("*.csv"))), reverse=True) if base.is_dir() else []
    if not runs:
        return None

    def stats_of(run: Path) -> tuple[int, int]:
        summary_path = run / "summary.json"
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
        except (OSError, json.JSONDecodeError):
            summary = {}
        run_device = summary.get("device_requested")
        per_backend: dict[str, int] = defaultdict(int)
        for csv_path in run.glob("*.csv"):
            for row in csv.DictReader(csv_path.read_text(encoding="utf-8").splitlines()):
                row_device = row.get("device_requested") or run_device
                if row.get("status") == "ok" and row_device == device:
                    per_backend[row["backend"]] += 1
        return (max(per_backend.values(), default=0), len(per_backend))

    eligible = [run for run in runs if stats_of(run) != (0, 0)]
    return max(eligible, key=lambda p: (*stats_of(p), p.name)) if eligible else None


def _provider_of(summary: dict, backend: str) -> str:
    """`provider_effective` real del backend en el `summary.json` de una run."""
    meta = (summary.get("backends") or {}).get(backend) or {}
    return meta.get("provider_effective") or "n/a"


def render_cpu_gpu(feature: str, cpu_rep: dict, cpu_sum: dict, gpu_rep: dict | None,
                   gpu_sum: dict | None) -> list[str]:
    """Sección `## CPU vs GPU`: misma calidad (mismo GT), distinto tiempo por device.

    Solo muestra motores no excluidos y GPU reales; si el dataset difiere, no
    presenta las cifras como una comparación equiparable.
    """
    key, label, _higher = TITULAR_METRIC[feature]
    same_dataset = not gpu_sum or cpu_sum.get("dataset") == gpu_sum.get("dataset")
    if not same_dataset:
        gpu_rep = {}
    else:
        gpu_rep = {name: values for name, values in (gpu_rep or {}).items()
                   if name.split(" (")[0] not in EXCLUDED_MOTORS}
    cpu_rep = {name: values for name, values in cpu_rep.items()
               if name.split(" (")[0] not in EXCLUDED_MOTORS}
    lines = [
        "## CPU vs GPU (`device_requested` vs `provider_effective`)",
        "",
        "> Mismo banco, mismo dataset y mismo GT en ambas columnas: la **calidad** debe "
        "coincidir; lo que cambia es el **tiempo**. La columna GPU solo lista motores que "
        "de verdad corrieron en un acelerador (`provider_effective` ∈ cuda/directml/…); "
        "un fallback CPU nunca se cuenta como GPU. `N/A` = ese motor **no** corre en GPU "
        "en este banco (queda `skipped` con motivo), no un valor de CPU repetido.",
        "",
        f"| Motor (variante) | {label} (CPU) | {label} (GPU) | ms CPU | ms GPU | provider GPU |",
        "| :--- | ---: | ---: | ---: | ---: | :--- |",
    ]
    if not same_dataset:
        lines.append("| _(dataset GPU distinto; comparación no equiparable)_ | | | | | |")
    elif not gpu_rep:
        lines.append("| _(sin run GPU)_ | | | | | |")
    else:
        for name in sorted(set(cpu_rep) | set(gpu_rep)):
            c = cpu_rep.get(name) or {}
            g = gpu_rep.get(name) or {}
            gq = g.get(key)
            gms = g.get("mean_ms")
            backend = name.split(" (")[0]
            lines.append(
                f"| {name} | "
                f"{'N/A' if cpu_rep.get(name, {}).get(key) is None else format(cpu_rep[name][key], '.3f')} | "
                f"{'N/A' if gq is None else format(gq, '.3f')} | "
                f"{'N/A' if c.get('mean_ms') is None else format(c['mean_ms'], '.0f')} | "
                f"{'N/A' if gms is None else format(gms, '.0f')} | "
                f"{(_provider_of(gpu_sum or {}, backend)) if name in gpu_rep else 'n/a (no corre en GPU)'} |"
            )
    lines += [
        "",
        "> El `provider GPU` sale del `provider_effective` real del `summary.json` GPU "
        "(`n/a` = el motor no expone ejecución GPU en este banco). No hay filas GPU "
        "inventadas: lo que no corrió en acelerador se ve como `N/A`.",
        "",
    ]
    return lines


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
                    except (KeyError, TypeError, ValueError):
                        # CSV antiguo sin esa columna, o celda vacia: N/A (nunca 0).
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
    report = {name: values for name, values in report.items()
              if name.split(" (")[0] not in EXCLUDED_MOTORS}
    if feature == "formula":
        for name, value in latex_coverage(run).items():
            for key in report:
                if key.split(" (")[0] == name:
                    report[key]["latex_any"] = value

    return report, summary


def render_md(feature: str, report: dict[str, dict[str, Any]], summary: dict, run: Path,
              gpu: tuple[dict, dict] | None = None) -> str:
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
    if gpu is not None:
        gpu_rep, gpu_sum = gpu
        lines += render_cpu_gpu(feature, report, summary, gpu_rep, gpu_sum)
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


def plot_feature(feature: str, report: dict, summary: dict, out: Path,
                 gpu_report: dict | None = None) -> None:
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
    # Series GPU (solo motores que corrieron en acelerador real): misma calidad,
    # distinto tiempo. Sin datos GPU, la barra GPU simplemente no aparece.
    gpu_times = [((gpu_report or {}).get(n) or {}).get("mean_ms") for n in names]
    has_gpu = any(v is not None for v in gpu_times)
    if has_gpu:
        w = 0.38
        offsets_c = [xi - w / 2 for xi in x]
        offsets_g = [xi + w / 2 for xi in x]
        bc = axt.bar(offsets_c, [v if v is not None else float("nan") for v in times],
                     w, color="#3b6fb0", label="CPU")
        bg = axt.bar(offsets_g, [v if v is not None else float("nan") for v in gpu_times],
                     w, color="#c0693b", label="GPU (acelerador real)")
        for bars_, values in ((bc, times), (bg, gpu_times)):
            for bar, value in zip(bars_, values):
                if value is None:
                    continue
                axt.annotate(f"{value:.0f}",
                             (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                             ha="center", va="bottom", fontsize=7.5)
        axt.legend(loc="upper right", fontsize=8, frameon=False)
        present_t = present_t + [v for v in gpu_times if v is not None]
    else:
        bars(axt, times, "#3b6fb0", "{:.0f}")
    axt.set_ylim(0, (max(present_t) if present_t else 1.0) * 1.28)
    axt.set_ylabel("ms/imagen ↓")
    axt.set_title("Tiempo — ms/imagen (CPU vs GPU)", fontsize=12, weight="bold")

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
    # rect con mas aire arriba: con `ms` altos (p. ej. layout >2 s) el ultimo tick
    # del eje de tiempo asoma por encima del area y chocaba con el suptitulo.
    fig.tight_layout(rect=(0, 0.04, 1, 0.90))
    fig.savefig(out.with_suffix(".png"), dpi=160, bbox_inches="tight", facecolor="white")
    fig.savefig(out.with_suffix(".svg"), bbox_inches="tight", facecolor="white")
    plt.close(fig)


GPU_PROVIDERS = frozenset({"cuda", "directml", "tensorrt", "coreml", "openvino", "webgpu", "rocm", "mps"})


def load_gpu(feature: str) -> tuple[dict, dict] | None:
    """Agrega la última run GPU real de cada motor, no una sola run global."""
    base = RESULTS_DIR / feature
    if not base.is_dir():
        return None
    runs = sorted((p for p in base.iterdir() if p.is_dir() and any(p.glob("*.csv"))),
                  reverse=True)
    selected: dict[str, list[dict]] = {}
    gpu_summary: dict[str, Any] = {"device_requested": "gpu", "backends": {}}
    for run in runs:
        summary_path = run / "summary.json"
        if not summary_path.exists():
            continue
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if summary.get("device_requested") != "gpu":
            continue
        rows, _ = load_run(run)
        grouped: dict[str, list[dict]] = defaultdict(list)
        for row in rows:
            backend = row.get("backend", "")
            provider = str(row.get("provider_effective", "")).lower()
            if backend in EXCLUDED_MOTORS or provider not in GPU_PROVIDERS:
                continue
            variant = row.get("model_variant") or "default"
            name = f"{backend} ({variant})"
            grouped[name].append(row)
        for name, backend_rows in grouped.items():
            if name in selected:
                continue
            selected[name] = backend_rows
            backend = name.split(" (")[0]
            meta = dict((summary.get("backends") or {}).get(backend) or {})
            meta["provider_effective"] = backend_rows[0].get("provider_effective") or "n/a"
            gpu_summary["backends"][backend] = meta
        if selected and "dataset" not in gpu_summary:
            gpu_summary["dataset"] = summary.get("dataset")
    if not selected:
        return None
    gpu_report = summarize([row for rows in selected.values() for row in rows])
    return gpu_report, gpu_summary


def consolidated_table(features: Sequence[str]) -> str:
    """Tabla única CPU vs GPU (para el README): calidad igual, tiempo distinto."""
    lines = [
        "# CPU vs GPU por feature — misma calidad, distinto tiempo",
        "",
        "> Runs **CPU**: `benchmarks/results/<feature>/` · runs **GPU**: "
        "`benchmarks/results/_gpu/<feature>/` — mismo banco, mismo dataset y mismo GT "
        "en ambas. La columna GPU solo lista motores que corrieron en un acelerador "
        "real (`provider_effective`); el resto queda `N/A` (no corre en GPU / `skipped`). "
        "`N/A` = no ejecutado, jamás un `0`. En este host el acelerador real de pyocrust "
        "es **DirectML** (`--device gpu` → `device=auto` → `provider_effective=directml`).",
        "",
        "| Feature | Motor (variante) | Calidad (titular) | ms CPU | ms GPU | provider GPU |",
        "| :--- | :--- | ---: | ---: | ---: | :--- |",
    ]
    for feature in features:
        run = latest_run(feature)
        if run is None:
            continue
        cpu_rep, cpu_sum = analyze(feature, run)
        gpu = load_gpu(feature)
        gpu_rep, gpu_sum = gpu if gpu else ({}, {})
        if gpu and cpu_sum.get("dataset") != gpu_sum.get("dataset"):
            gpu_rep = {}
        key = TITULAR_METRIC[feature][0]
        for name in sorted(set(cpu_rep) | set(gpu_rep)):
            c, g = cpu_rep.get(name) or {}, gpu_rep.get(name) or {}
            backend = name.split(" (")[0]
            q = c.get(key) if c.get(key) is not None else g.get(key)
            lines.append(
                f"| `{feature}` | {name} | "
                f"{'N/A' if q is None else format(q, '.3f')} | "
                f"{'N/A' if c.get('mean_ms') is None else format(c['mean_ms'], '.0f')} | "
                f"{'N/A' if g.get('mean_ms') is None else format(g['mean_ms'], '.0f')} | "
                f"{(_provider_of(gpu_sum, backend)) if name in gpu_rep else 'n/a (no corre en GPU)'} |"
            )
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reporte por feature")
    parser.add_argument("--feature", choices=sorted(FEATURE_COLUMNS))
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--run", type=Path, default=None, help="carpeta de la run")
    parser.add_argument("--no-md", action="store_true",
                        help="no reescribir REPORT.md (solo la gráfica REPORT.png/.svg)")
    parser.add_argument("--no-gpu", action="store_true",
                        help="no anexar la sección CPU vs GPU (ignora results/_gpu/)")
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
        gpu = None if args.no_gpu else load_gpu(feature)
        md = render_md(feature, report, summary, run, gpu=gpu)
        print(md)
        if not args.no_md:
            out = FEATURES_DIR / feature / "REPORT.md"
            out.write_text(md + "\n", encoding="utf-8")
            print(f"\n[report] {feature} -> {out}")
        if feature in TITULAR_METRIC:
            out = FEATURES_DIR / feature / "REPORT"
            plot_feature(feature, report, summary, out, gpu_report=(gpu[0] if gpu else None))
            print(f"[report] {feature} -> {out}.png (+ .svg)")
        print()
    if features == sorted(FEATURE_COLUMNS):
        consolidated = BENCHMARKS_ROOT / "CPU_VS_GPU.md"
        consolidated.write_text(consolidated_table(features), encoding="utf-8")
        print(f"[report] tabla consolidada -> {consolidated}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
