#!/usr/bin/env python
"""Reporte **por feature** a partir de las runs de `benchmarks/results/<feature>/`.

Lee la run más reciente (o `--run`) de una feature y escribe
`benchmarks/reports/<feature>/REPORT.md` (y, para features con datos,
`benchmarks/figures/<feature>/REPORT.png`/`.svg` con la comparativa por motor) con:

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

from common import (BENCHMARKS_ROOT, applicable_rows, module_available,
                    not_evaluable_metrics, select_device_rows)
from features._localization import english_markdown

RESULTS_DIR = BENCHMARKS_ROOT / "results"
REPORTS_DIR = BENCHMARKS_ROOT / "reports"
FIGURES_DIR = BENCHMARKS_ROOT / "figures"
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
        # Contenido (lo que ya se publicaba: comparable con las series previas).
        ("markdown_f1", "Markdown F1 ↑", "{:.3f}", True),
        ("block_f1", "F1 bloques ↑", "{:.3f}", True),
        # Estructura/posición (desgranado: una tabla mal estructurada con texto
        # correcto baja estas, no solo markdown_f1).
        ("layout_map", "layout mAP ↑", "{:.3f}", True),
        ("table_teds", "TEDS tabla ↑", "{:.3f}", True),
        ("latex_sim", "LaTeX sim ↑", "{:.3f}", True),
        # Títulos/índice (detección + texto) y **orden de lectura** como secuencia
        # (Kendall tau): lo que el LCS de tokens de `markdown_f1` no separa.
        ("title_recall", "títulos recall ↑", "{:.3f}", True),
        ("title_precision", "títulos prec. ↑", "{:.3f}", True),
        ("title_text_f1", "F1 texto títulos ↑", "{:.3f}", True),
        ("title_seq_tau", "secuencia títulos τ ↑", "{:.3f}", True),
        ("read_order_tau", "orden lectura τ ↑", "{:.3f}", True),
        # Figuras (detección + asociación figura↔caption): lo que `markdown_f1`
        # sólo cuenta como texto y `block_f1` como tipo sin posición.
        ("figure_recall", "figuras recall ↑", "{:.3f}", True),
        ("figure_precision", "figuras prec. ↑", "{:.3f}", True),
        ("figure_caption_recall", "captions recall ↑", "{:.3f}", True),
        ("figure_caption_precision", "captions prec. ↑", "{:.3f}", True),
        ("figure_caption_pair_f1", "asoc. fig↔caption ↑", "{:.3f}", True),
        ("figure_caption_text_f1", "F1 texto captions ↑", "{:.3f}", True),
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

# Claves de las métricas **propias de figuras** de `full_page` (detección de
# `figure`, detección de sus captions y asociación figura↔caption). Se agregan
# como el resto: media por motor, `None` = no evaluada (nunca `0.0`).
_FIGURE_KEYS = ("figure_recall", "figure_precision",
                "figure_caption_recall", "figure_caption_precision",
                "figure_caption_pair_f1", "figure_caption_text_f1")

# Métrica **titular** de cada feature (la que encabeza su REPORT.md): clave,
# etiqueta y si "más es mejor". Solo entran features con banco implementado y
# con datos; el resto no tiene gráfica (un esqueleto no publica cifras).
TITULAR_METRIC: dict[str, tuple[str, str, bool]] = {
    "text": ("word_f1", "Word F1 ↑", True),
    "formula": ("latex_sim", "LaTeX similarity ↑", True),
    "layout": ("layout_map", "mAP@IoU 0.5 ↑", True),
    "table": ("table_teds", "Structural TEDS ↑", True),
    "full_page": ("markdown_f1", "Markdown F1 ↑", True),
    "orientation": ("ori_acc", "accuracy ↑", True),
    "text_line": ("ori_acc", "accuracy ↑", True),
    "rectification": ("rect_sim", "SSIM ↑", True),
    "seal": ("box_recall", "recall@IoU 0.5 ↑", True),
}


def run_csv(run: Path) -> Path | None:
    """CSV propio de una run: exactamente **uno**, sin adivinar entre varios.

    Un dir de run puede haberse contaminado con el CSV de otra corrida (copia
    manual); leerlos todos sumaba filas y publicaba `n` mezclados (p. ej.
    `pp-doclayoutv3` con `n=40+20=60`). Se acepta el CSV que casa con
    `summary.json['timestamp']`, o `<dir>.csv`, o el unico que haya. Si hay varios
    y ninguno casa se devuelve `None` (esa run no se publica) en vez de inventar.
    """
    summary_path = run / "summary.json"
    try:
        stamp = (json.loads(summary_path.read_text(encoding="utf-8")).get("timestamp")
                 if summary_path.exists() else None)
    except (OSError, json.JSONDecodeError):
        stamp = None
    candidates = ([run / f"{stamp}.csv"] if stamp else []) + [run / f"{run.name}.csv"]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    csvs = sorted(run.glob("*.csv"))
    return csvs[0] if len(csvs) == 1 else None


def latest_run(feature: str, root: Path = RESULTS_DIR, device: str = "cpu") -> Path | None:
    """Run de referencia para `device`: más muestras por motor, luego más motores.

    El filtro de device evita que una corrida GPU más reciente oculte la
    comparativa CPU de referencia. Los empates se resuelven por nombre de run.
    """
    base = root / feature
    runs = sorted((p for p in base.glob("*") if any(p.glob("*.csv"))), reverse=True) if base.is_dir() else []
    if not runs:
        return None

    def stats_of(run: Path) -> tuple[int, int]:
        csv_path = run_csv(run)
        if csv_path is None:
            return (0, 0)
        summary_path = run / "summary.json"
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
        except (OSError, json.JSONDecodeError):
            summary = {}
        run_device = summary.get("device_requested")
        per_backend: dict[str, int] = defaultdict(int)
        for row in csv.DictReader(csv_path.read_text(encoding="utf-8").splitlines()):
            row_device = row.get("device_requested") or run_device
            if row.get("status") == "ok" and row_device == device:
                per_backend[row["backend"]] += 1
        return (max(per_backend.values(), default=0), len(per_backend))

    eligible = [run for run in runs if stats_of(run) != (0, 0)]
    return max(eligible, key=lambda p: (*stats_of(p), p.name)) if eligible else None


def _backend_for(summary: dict, name: str) -> str:
    """Backend canónico de un nombre de motor (`model_name (variante)`).

    Los informes etiquetan por `model_name`, pero el `summary.json` indexa por
    `backend`. Sin este puente `_provider_of` no encuentra la entrada y reporta
    `n/a` para motores que corrieron en un acelerador real.
    """
    backends = summary.get("backends") or {}
    # El `model_name` de algunos motores ya lleva un sufijo entre paréntesis
    # (`yolo26m (doc-layout)`), así que la variante del informe es lo que va
    # después del **segundo** paréntesis; sin él no hay forma de distinguir
    # `yolo26m (doc-layout) (21.8M)` de `yolo26m (doc-layout)`.
    parts = name.split(" (")
    model = parts[0]
    name_variant = parts[-1].rstrip(")") if len(parts) > 1 else ""
    for backend, meta in backends.items():
        meta = meta or {}
        declared_model = meta.get("model_name") or ""
        declared_variant = meta.get("model_variant") or ""
        # Algunos YOLO declaran `model_name` ya con sufijo de dataset
        # (`yolo26m (doc-layout)`), así que el nombre del informe es el prefijo.
        same_model = declared_model == model or declared_model.startswith(f"{model} (")
        if same_model and declared_variant == name_variant:
            return backend
    return ""


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
    gpu_rep = (gpu_rep or {}) if same_dataset else {}
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
            backend = _backend_for(gpu_sum or {}, name)
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


def _short_stratum(stratum: str) -> str:
    """`book × single_column` -> etiqueta compacta para la cabecera del pivote."""
    return stratum.replace(" × ", "×")


def strata_summary(rows: Sequence[dict]) -> dict[tuple[str, str], dict[str, Any]]:
    """`(motor, estrato) -> {layout_map, layout_recall, n}` desde las filas de layout.

    El `stratum` (columna aditiva del CSV, `data_source × layout`) viaja con cada
    fila; los motores y estratos se etiquetan como en la comparativa
    (`model_name (variant)`) para que el pivote cuadre con la tabla global.
    """
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        stratum = str(row.get("stratum") or "").strip()
        if not stratum:
            continue
        motor = row.get("model_name") or row["backend"]
        variant = row.get("model_variant")
        name = f"{motor} ({variant})" if variant else motor
        entry = grouped.setdefault(
            (name, stratum), {"layout_map": [], "layout_recall": [], "n": 0})
        for key in ("layout_map", "layout_recall"):
            value = row.get(key)
            if isinstance(value, float):
                entry[key].append(value)
        entry["n"] += 1
    return grouped


def _strata_pivot(motors: Sequence[str], strata: Sequence[str],
                  grouped: dict[tuple[str, str], dict[str, Any]], key: str) -> list[str]:
    """Pivote motor × estrato de una métrica (`key`); `—` = sin medición."""
    lines = [
        "| Motor (variante) | " + " | ".join(_short_stratum(s) for s in strata) + " |",
        "| :--- | " + " | ".join("---:" for _ in strata) + " |",
    ]
    for motor in motors:
        cells = []
        for stratum in strata:
            values = (grouped.get((motor, stratum)) or {}).get(key) or []
            cells.append(f"{statistics.fmean(values):.3f}" if values else "—")
        lines.append(f"| {motor} | " + " | ".join(cells) + " |")
    return lines


def render_strata(feature: str, rows: Sequence[dict]) -> list[str]:
    """Sección "Por estrato": mAP/recall@IoU 0.5 por motor y estrato anotado.

    Desglosa la media global por el estrato (`data_source × layout`) de cada
    página para medir la **heterogeneidad real** de los motores: un mismo motor
    puede rendir muy distinto en `book × single_column` y en
    `newspaper × other_layout`. Sin `stratum` en las filas (features cuyo dataset
    no anota `page_attribute`) no se emite sección.
    """
    if feature != "layout":
        return []
    grouped = strata_summary(rows)
    if not grouped:
        return []
    strata = sorted({stratum for _motor, stratum in grouped})
    motors = sorted({motor for motor, _stratum in grouped})
    counts = {stratum: (grouped.get((motors[0], stratum)) or {}).get("n", 0) for stratum in strata}
    lines = [
        "## Por estrato (`data_source × layout`)",
        "",
        f"> mAP/recall@IoU 0.5 **por motor y estrato** de la página (muestra estratificada, "
        f"`page_info.page_attribute`). Motores medidos: {len(motors)} · estratos cubiertos: "
        f"{len(strata)}. `—` = ese motor no tiene medición en ese estrato.",
        "",
        "> **Estratos (n de páginas en la muestra)**: "
        + ", ".join(f"`{_short_stratum(s)}` ({counts[s]})" for s in strata) + ".",
        "",
        "### mAP@IoU 0.5 por estrato",
        "",
    ]
    lines += _strata_pivot(motors, strata, grouped, "layout_map")
    lines += ["", "### recall@IoU 0.5 por estrato", ""]
    lines += _strata_pivot(motors, strata, grouped, "layout_recall")
    lines.append("")
    return lines


def render_content_vs_structure(feature: str) -> list[str]:
    """Sección que separa **contenido** de **estructura/posición** (solo `full_page`).

    Explica por qué las columnas del informe no son redundantes: `markdown_f1` mide
    el **contenido** (tokens en orden de lectura, conservando el LaTeX) y
    `block_f1` el multiconjunto de **tipos** de bloque; ninguno ve la **estructura
    interna** de una tabla ni la **posición** de los bloques. `layout mAP`, `TEDS
    tabla` y `LaTeX sim` sí. Una tabla con las celdas correctas pero mal
    estructurada (filas/columnas fusionadas o repartidas) mantiene alto
    `markdown_f1` y baja `TEDS tabla`: sin esta columna el fallo quedaría tapado.
    """
    if feature != "full_page":
        return []
    return [
        "## Contenido vs estructura/posición",
        "",
        "> Las columnas del informe **no son redundantes**: miden fallos distintos y "
        "por eso se publican juntas.",
        "",
        "> **Contenido** (lo que ya se publicaba, comparable con las series previas): "
        "`Markdown F1` = LCS de tokens en orden de lectura (conserva el LaTeX); "
        "`F1 bloques` = multiconjunto de **tipos** de bloque (ignora posición y "
        "contenido); `CER` = reconocimiento sobre texto plano. Un `Markdown F1` alto "
        "**no** garantiza que la tabla esté bien armada: si el texto de las celdas es "
        "correcto, el LCS lo da por bueno aunque la estructura esté mal.",
        "",
        "> **Estructura/posición** (desgranado nuevo): `layout mAP` = posición de las "
        "cajas contra el `poly` anotado; `TEDS tabla` = estructura HTML de tabla "
        "(filas/columnas/fusiones, **sin** el texto de celda); `LaTeX sim` = similitud "
        "del LaTeX de fórmula. Una tabla **mal estructurada con el texto correcto** "
        "baja `TEDS tabla` y **no** `Markdown F1`: por eso se distinguen.",
        "",
        "> **Figuras** (desgranado propio): `figuras recall/prec.` = detección de las "
        "cajas `figure` (IoU@0.5, como `layout`); `captions recall/prec.` = detección "
        "de las cajas de caption; `asoc. fig↔caption` = fracción de figuras "
        "detectadas cuya caption compañera también se localizó; `F1 texto captions` = "
        "F1 del texto de la caption. `Markdown F1`/`F1 bloques` sólo ven el **texto** "
        "y el **tipo** de la figura, nunca su posición ni si la caption quedó ligada: "
        "una página con las figuras detectadas pero **sin** sus captions baja "
        "`asoc. fig↔caption` sin que `Markdown F1` lo note.",
        "",
        "> `N/A` = la página/el motor no aporta GT o no emite esa modalidad (p. ej. un "
        "motor sin fórmulas separadas), nunca un `0.0`.",
        "",
    ]


def render_title_coverage(feature: str, rows: Sequence[dict]) -> list[str]:
    """Cobertura de títulos y aviso de jerarquía NO medible (solo `full_page`).

    Declara **sobre cuántas páginas** se midió la métrica de títulos (las que
    anotan `title`), sin disolverlo en la media global, y deja constancia de que
    la **jerarquía** (h1/h2/h3) **no es medible**: OmniDocBench deja `attribute`
    siempre vacío, así que no se emite `0.0` por profundidad ni se finge un índice
    anidado. Solo se miden presencia, posición, texto y secuencia.
    """
    if feature != "full_page":
        return []
    # Presencia de GT de títulos = propiedad de la PÁGINA (del dataset), no del
    # motor: una pagina tiene GT de titulos si CUALQUIER motor capaz de emitirlos la
    # puntuo. Contarlo por la metrica de un solo motor marcaria `0%` para un motor
    # que no emite titulos (docling), mintiendo sobre la cobertura del dataset.
    titled_ids = {r["image_id"] for r in rows if r.get("title_recall") is not None}
    if not titled_ids:
        return []
    by_engine: dict[str, list[int]] = {}
    for row in rows:
        motor = row.get("model_name") or row["backend"]
        variant = row.get("model_variant")
        name = f"{motor} ({variant})" if variant else motor
        total, titled = by_engine.setdefault(name, [0, 0])
        by_engine[name] = [total + 1, titled + (1 if row.get("image_id") in titled_ids else 0)]
    lines = [
        "## Cobertura de títulos y jerarquía (no medible)",
        "",
        "> La métrica de **títulos/índice** solo se evalúa en las páginas que la "
        "anotación marca con `category_type=title`; en el resto queda `N/A` y **no** "
        "entra en la media (no se diluye en un promedio global). El dataset "
        "`OmniDocBench` (v1.6, 1651 páginas) anota `title` en **1179** páginas "
        "(el **71.4 %**); el resto no tiene GT de títulos.",
        "",
        "> **La jerarquía de títulos (h1/h2/h3) NO es medible con esta anotación**: "
        "el campo `attribute` está **siempre vacío** en OmniDocBench, no hay nivel "
        "jerárquico anotado. Por eso esta tarjeta mide **presencia, posición, texto y "
        "secuencia**, y **no** emite un `0.0` por profundidad ni finge un índice "
        "anidado: donde el dataset no anota, el informe lo dice.",
        "",
        "| Motor (variante) | páginas medidas | páginas con GT de títulos | "
        "cobertura títulos |",
        "| :--- | ---: | ---: | ---: |",
    ]
    for name in sorted(by_engine):
        total, titled = by_engine[name]
        lines.append(f"| {name} | {total} | {titled} | {titled / total:.0%} |")
    lines.append("")
    return lines


def render_figure_coverage(feature: str, rows: Sequence[dict]) -> list[str]:
    """Cobertura de **figuras** y nota de lo **no emitible** (solo `full_page`).

    Declara **sobre cuántas páginas** se midió la métrica de figuras/captions
    (las que anotan `figure`), sin disolver ese subconjunto en la media global, y
    deja constancia de que las **máscaras** (`*_mask`, `chart_mask`, `table_mask`,
    `algorithm_mask`, `organic_chemical_formula_mask`, `text_mask`, `need_mask`,
    `abandon`, `unknown_mask`) **no son emitibles por el pipeline**: se ignoran al
    puntuar y **nunca** cuentan como `0.0` por no emitirlas, igual que
    `page_number`/`reference` en `layout`.
    """
    if feature != "full_page":
        return []
    # Presencia de GT de figuras = propiedad de la PÁGINA, no del motor (ver
    # `render_title_coverage`): un motor que no emite cajas (docling) no debe
    # rebajar a `0%` la cobertura de figuras del dataset.
    figure_ids = {r["image_id"] for r in rows if r.get("figure_recall") is not None}
    if not figure_ids:
        return []
    by_engine: dict[str, list[int]] = {}
    for row in rows:
        motor = row.get("model_name") or row["backend"]
        variant = row.get("model_variant")
        name = f"{motor} ({variant})" if variant else motor
        total, with_fig = by_engine.setdefault(name, [0, 0])
        by_engine[name] = [total + 1, with_fig + (1 if row.get("image_id") in figure_ids else 0)]
    lines = [
        "## Cobertura de figuras y lo no emitible (máscaras)",
        "",
        "> La métrica de **figuras/captions** solo se evalúa en las páginas que la "
        "anotación marca con `category_type=figure`; en el resto queda `N/A` y **no** "
        "entra en la media (no se diluye en un promedio global). El dataset "
        "`OmniDocBench` (v1.6, 1651 páginas) anota `figure` en **613** páginas "
        "(el **37.1 %**; 1385 instancias de `figure` en total); el resto no tiene GT "
        "de figuras.",
        "",
        "> **Las máscaras (`*_mask`) NO son emitibles por el pipeline** y por eso "
        "**no se puntúan**: `chart_mask`, `table_mask`, `algorithm_mask`, "
        "`organic_chemical_formula_mask`, `text_mask`, `need_mask`, `abandon`, "
        "`unknown_mask` se **ignoran** al puntuar (quedan fuera del GT de bloques, "
        "ver `_odb_content_blocks`); **nunca** cuentan como `0.0` por no emitirlas, "
        "igual que `page_number`/`reference` en `layout`. Un motor que no las emite "
        "no se penaliza.",
        "",
        "> La **asociación figura↔caption** (`asoc. fig↔caption`) exige que, además "
        "de detectar la figura, se localice su caption compañera: una página con las "
        "figuras detectadas pero **sin** sus captions baja esa columna aunque su "
        "`figuras recall` sea `1.0`, así que no puede puntuar igual que una completa.",
        "",
        "| Motor (variante) | páginas medidas | páginas con GT de figuras | "
        "cobertura figuras |",
        "| :--- | ---: | ---: | ---: |",
    ]
    for name in sorted(by_engine):
        total, with_fig = by_engine[name]
        lines.append(f"| {name} | {total} | {with_fig} | {with_fig / total:.0%} |")
    lines.append("")
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
                            "layout_map", "layout_recall", "table_teds", "ori_acc", "rect_sim",
                            "title_recall", "title_precision", "title_text_f1",
                            "title_seq_tau", "read_order_tau", *_FIGURE_KEYS):
                    try:
                        row[key] = float(row[key])
                    except (KeyError, TypeError, ValueError):
                        # CSV antiguo sin esa columna, o celda vacia: N/A (nunca 0).
                        row[key] = None
                # Un motor que no emite una estructura (docling solo Markdown; indra
                # sin el vocabulario del banco) NO la mide: la celda guardada como
                # `0.0` es en realidad **no evaluada** -> `None` (se pinta `N/A` y no
                # entra en la media). La senal la declara el adaptador
                # (`common.runner.STRUCTURE_CHANNELS`); el propio runner ya escribe
                # `""` en runs nuevas, esto interpreta tambien las runs previas.
                # El mapa `FULL_PAGE_METRIC_CHANNEL` es **especifico de `full_page`**:
                # no se aplica a otras features. En `formula`, `latex_sim`/
                # `latex_token_f1` se calculan desde el **texto** del motor
                # (`formula/bank.py::_formula_latex`), no desde un canal `formulas`,
                # asi que ahi SI estan evaluadas y no se enmascaran.
                if row.get("feature") == "full_page":
                    for key in not_evaluable_metrics(row.get("backend", "")):
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
        model = row.get("model_name") or row["backend"]
        variant = row.get("model_variant")
        grouped[f"{model} ({variant})" if variant else model].append(row)
    report: dict[str, dict[str, Any]] = {}
    for name, group in grouped.items():
        times = sorted(r["elapsed_ms"] for r in group if r["elapsed_ms"] is not None)
        entry: dict[str, Any] = {"n": len(group),
                                 "mean_ms": statistics.fmean(times) if times else None}
        for key in ("word_f1", "wer_ord", "cer", "wer", "markdown_f1", "block_f1",
                    "box_recall", "box_iou_mean",
                    "latex_exact", "latex_sim", "latex_token_f1",
                    "layout_map", "layout_recall", "table_teds", "ori_acc", "rect_sim",
                    "title_recall", "title_precision", "title_text_f1",
                    "title_seq_tau", "read_order_tau", *_FIGURE_KEYS):
            values = [r[key] for r in group if r.get(key) is not None]
            entry[key] = statistics.fmean(values) if values else None
        report[name] = entry
    return report


def analyze(feature: str, run: Path) -> tuple[dict[str, dict[str, Any]], dict]:
    """Carga la run y agrega el reporte por motor (+ cobertura LaTeX en `formula`)."""
    rows, summary = load_run(run)
    rows = applicable_rows(feature, rows)
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


def _provenance_notes(feature: str, report: dict[str, dict[str, Any]]) -> list[str]:
    """Declara si cada motor medido es un modelo INDEPENDIENTE o el mismo peso.

    Evita presentar como "modelo alternativo" lo que solo cambia de runtime: el
    `pyocrust` propio es la referencia; para cada alternativa se dice si es
    `independiente` (otro modelo) o `mismo_peso_otra_via` (el MISMO `.onnx` de
    PaddleOCR por otro runtime).
    """
    from common import MODEL_NAMES, alternative_provenance

    # El informe etiqueta por `model_name (variante)`. Se resuelve backend por
    # (model_name, variante) para no confundir el motor de referencia con su
    # alternativa homonima (`pyocrust_orientation` y `lcnet_doc_ori` comparten
    # modelo pero distinta variante: `6.8M` vs `onnxruntime`).
    by_label = {f"{model} ({variant})": backend
                for backend, (model, variant) in MODEL_NAMES.items()}
    labels = {
        "independiente": "modelo **independiente** (otro proyecto/checkpoint)",
        "mismo_peso_otra_via": "**mismo peso, distinta vía** (el MISMO `.onnx` de PaddleOCR por otro runtime — NO es un modelo distinto)",
        "mismo_tronco_otro_checkpoint": "mismo tronco PP-LCNet, **checkpoint distinto**",
        "baseline_clasico": "**línea base clásica** sin pesos (no es un modelo aprendido ni un SOTA: suelo de comparación)",
    }
    lines: list[str] = []
    for name in sorted(report):
        backend = by_label.get(name, "")
        if not backend or backend.startswith("pyocrust"):
            continue  # el motor de referencia no es una "alternativa"
        line = f"- `{name}` — {labels.get(alternative_provenance(backend), 'modelo **independiente**')}"
        lines.append(line)
    if not lines:
        return []
    return lines + [
        "",
        "> El motor de referencia (`pyocrust`) no se lista: es el que define el resultado "
        "base. Una alternativa con **mismo peso, distinta vía** mide el mismo modelo con "
        "otro runtime; **no** aporta un competidor independiente y así queda declarado.",
    ]


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
    # Origen del dataset: si los numeros vienen de la fixture versionada (sin red)
    # y NO de la muestra completa, se declara de forma visible (regla de provenance).
    ds_info = summary.get("dataset_source") or {}
    ds_source = ds_info.get("source", "dataset")
    # Revision HF fijada (criterio de la tarjeta): aparece SIEMPRE en el informe
    # cuando los numeros vienen del dataset real, para poder reproducir la muestra.
    ds_revision = ds_info.get("revision")

    labels = [label for _k, label, _f, _h in columns]
    lines = [
        f"# Reporte por feature: `{feature}`",
        "",
        "> **Origen: `medido`** — ejecutado por nosotros en este repo. No hay filas de "
        "`referencia` (externas) en esta tabla.",
        "",
    ]
    if ds_source == "fixture":
        detail = (summary.get("dataset_source") or {}).get("detail", "")
        lines += [
            f"> **AVISO — muestra: `fixture` (NO la muestra completa).** Los numeros de "
            "esta tabla se midieron sobre la **fixture minima versionada** porque el "
            f"dataset real no estaba disponible (`{detail}`). **No son comparables** con "
            "los del set completo.",
            "",
        ]
    lines += [
        "## Provenance",
        "",
        f"- **comando**: `{command}`",
        f"- **dataset**: `{summary.get('dataset', '?')}` · **n** (por motor): "
        f"`{summary.get('n_samples', '?')}` · **warmup**: `{summary.get('warmup', '?')}` · "
        f"**repeats**: `{summary.get('repeats', '?')}` · **device**: `{summary.get('device_requested', '?')}`",
    ]
    if ds_source != "fixture" and ds_revision:
        lines.append(
            f"- **revision HF (fijada)**: `{ds_revision}` — misma revision en cualquier "
            "maquina; los bytes se verifican contra `benchmarks/datasets_manifest.json`")
    lines += [
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
        "`N/A` = no evaluada (sin GT de esa columna **o** el motor no emite esa estructura), nunca un `0.0` inventado.",
        "",
        "## Saltados (`skipped`) — no cuentan como ejecutados",
        "",
    ]
    lines += [f"- `{b}` — {reason}" for b, reason in sorted(skipped.items())] or ["- (ninguno)"]
    # Procedencia de cada alternativa: declara cuando un motor es el MISMO peso que
    # `pyocrust` por otra via, en vez de presentarlo como modelo independiente.
    prov_lines = _provenance_notes(feature, report)
    if prov_lines:
        lines += ["", "## Procedencia de las alternativas", ""] + prov_lines
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
    # Desglose contenido vs estructura/posición (solo `full_page`).
    lines += render_content_vs_structure(feature)
    # Desglose por estrato al final (fuera del bloque `## Comparativa`/`## CPU vs
    # GPU`, para no alterar el orden que esperan los informes consolidados).
    rows, _ = load_run(run)
    lines += render_strata(feature, rows)
    # Cobertura de títulos + aviso de jerarquía no medible (solo `full_page`).
    lines += render_title_coverage(feature, rows)
    # Cobertura de figuras + nota de máscaras no emitibles (solo `full_page`).
    lines += render_figure_coverage(feature, rows)
    return "\n".join(lines)


def build(feature: str, run: Path) -> str:
    """Markdown del reporte por feature (compatibilidad; = `render_md(analyze(...))`)."""
    return render_md(feature, *analyze(feature, run), run)


# Columnas de la tabla publicable: las mismas del REPORT.md (fuente única) + la
# licencia informativa. La tabla se genera desde el MISMO `report` agregado que el
# REPORT, así las celdas MD/TeX/REPORT no pueden divergir.
_TABLE_TEX_ESCAPES = (("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"),
                      ("$", r"\$"), ("#", r"\#"), ("_", r"\_"), ("{", r"\{"), ("}", r"\}"),
                      ("↑", r"$\uparrow$"), ("↓", r"$\downarrow$"))


def _tex_escape(text: str) -> str:
    for source, target in _TABLE_TEX_ESCAPES:
        text = text.replace(source, target)
    return text


def render_table(feature: str, report: dict[str, dict[str, Any]], summary: dict) -> tuple[str, str]:
    """`(markdown_es, latex_en)` de `benchmark_table.{md,tex}` de una feature.

    Reutiliza `FEATURE_COLUMNS[feature]` (las mismas columnas y etiquetas del
    `REPORT.md`) sobre el agregado `report` que ya calculó `analyze`: la tabla
    publicable y el informe salen de un único origen, así no hay celda que
    diverja. Las cifras son las del `report` (media por motor del device pedido);
    `N/A` = no evaluada, nunca un `0.0`.
    """
    from features.summary import _license_for  # import perezoso (evita matplotlib)

    columns = FEATURE_COLUMNS[feature]
    labels = [label for _k, label, _f, _h in columns] + ["license"]
    # Mejor/segundo por métrica (mismo criterio que `render_md`).
    best: dict[str, tuple[str, str]] = {}
    for key, _label, _fmt, higher in columns:
        if higher is None:
            continue
        values = [(d.get(key), name) for name, d in report.items() if d.get(key) is not None]
        if len(values) > 1 and len({v for v, _ in values}) > 1:
            ordered = sorted(values, key=lambda p: p[0], reverse=higher)
            best[key] = (ordered[0][1], ordered[1][1] if len(ordered) > 1 else "")

    md_rows, tex_rows = [], []
    keys = [key for key, _l, _f, _h in columns]
    for name in sorted(report):
        data = report[name]
        cells = [("N/A" if data.get(key) is None else fmt.format(data[key]))
                 for key, _label, fmt, _higher in columns]
        # La licencia es la 6ª celda, fuera de las columnas de métrica (el `zip`
        # se detenía en 5 y la descartaba: columna `license` siempre vacía).
        cells.append(_license_for(name))
        md_cells = []
        for idx, text in enumerate(cells):
            if idx < len(keys):
                if best.get(keys[idx], ("", ""))[0] == name:
                    text = f"**{text}**"
                elif best.get(keys[idx], ("", ""))[1] == name:
                    text = f"<u>{text}</u>"
            md_cells.append(text)
        md_rows.append("| " + " | ".join([name, *md_cells]) + " |")
        tex_cells = []
        for idx, text in enumerate(cells):
            esc = _tex_escape(text)
            if idx < len(keys):
                if best.get(keys[idx], ("", ""))[0] == name:
                    esc = rf"\textbf{{{esc}}}"
                elif best.get(keys[idx], ("", ""))[1] == name:
                    esc = rf"\underline{{{esc}}}"
            tex_cells.append(esc)
        tex_rows.append(_tex_escape(name) + " & " + " & ".join(tex_cells) + r" \\")

    run_name = summary.get("timestamp", "?")
    device = summary.get("device_requested", "?")
    n_total = summary.get("n_samples", "?")
    note = ("> Nota: `N/A` = **no evaluada** — sin GT de esa columna, o el motor no "
            "emite esa estructura (p. ej. `docling`, que solo emite Markdown); "
            "`0.000` = **evaluada** y el motor no acertó, nunca un `0.0` sin medir. "
            f"Cifras y n reproducen `REPORT.md` (run `{run_name}`, device `{device}`, "
            f"n ≤ {n_total}); licencias informativas según `../QUALITY_VS_TIME.md`.")
    md = "\n".join([
        f"# Benchmark: {feature}",
        "",
        "| Motor (variante/tamaño) | " + " | ".join(labels) + " |",
        "| :--- | " + " | ".join("---:" for _ in labels) + " |",
        *md_rows,
        "",
        note,
    ]) + "\n"

    tex_labels = [lbl.replace("(variante/tamaño)", "(variant/size)") for lbl in labels]
    tex = "\n".join([
        r"\documentclass[border=2pt]{standalone}",
        r"\usepackage{booktabs}",
        r"\begin{document}",
        r"\begin{tabular}{l" + "r" * len(labels) + "}",
        r"\toprule",
        "Engine (variant/size) & " + " & ".join(_tex_escape(l) for l in tex_labels) + r" \\",
        r"\midrule",
        *tex_rows,
        r"\bottomrule",
        r"\end{tabular}",
        r"\par\smallskip{\footnotesize " + _tex_escape(
            "Note: N/A = not evaluated (no ground truth for that column, or the "
            "engine does not emit that structure, e.g. docling emits Markdown "
            "only); 0.000 = evaluated and the engine got it wrong, never an "
            f"unmeasured 0.0. Values and n match REPORT.md (run {run_name}, "
            f"device {device}, n <= {n_total}).") + "}",
        r"\end{document}",
    ]) + "\n"
    return md, tex


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
    axq.set_title(f"Quality — {label}", fontsize=12, weight="bold")

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
    axt.set_ylabel("ms/unit ↓")
    axt.set_title("Runtime — ms/unit (CPU vs. GPU)", fontsize=12, weight="bold")

    for ax in (axq, axt):
        ax.set_xticks(x)
        ax.set_xticklabels(names)
        ax.xaxis.set_major_formatter(FixedFormatter([_wrap_engine(n) for n in names]))
        # 45° con anclaje a la derecha: con muchos motores (layout tiene 41) las
        # etiquetas horizontales se pisan y no se pueden leer.
        for tick in ax.get_xticklabels():
            tick.set_rotation(45)
            tick.set_ha("right")
            tick.set_rotation_mode("anchor")
            tick.set_fontsize(8)

    origen = "measured" if summary.get("origen") in (None, "medido") else "reference"
    skipped = sum(1 for m in (summary.get("backends") or {}).values()
                  if m.get("status") == "skipped")
    dataset = summary.get("dataset", "?")
    run_id = summary.get("timestamp", "?")
    fig.suptitle(f"pyocrust · {feature} — engine comparison (source: {origen})",
                 fontsize=13, weight="bold")
    fig.legend(
        handles=[
            Patch(color="#1f6f5c", label=f"Quality: {label} (source: {origen})"),
            Patch(color="#3b6fb0", label=f"Runtime: ms/unit ↓ (source: {origen})"),
        ],
        loc="lower center", ncol=2, frameon=False, fontsize=9, bbox_to_anchor=(0.5, -0.03),
    )
    fig.text(0.5, -0.075,
             f"dataset: {dataset} · n per engine: {sorted({c for c in counts if c}) or '?'} · "
             f"run: {run_id} · skipped engines: {skipped}",
             ha="center", fontsize=8.5, color="#444444")
    # rect con mas aire arriba: con `ms` altos (p. ej. layout >2 s) el ultimo tick
    # del eje de tiempo asoma por encima del area y chocaba con el suptitulo.
    fig.tight_layout(rect=(0, 0.04, 1, 0.90))
    fig.savefig(out.with_suffix(".png"), dpi=160, bbox_inches="tight", facecolor="white")
    fig.savefig(out.with_suffix(".svg"), bbox_inches="tight", facecolor="white")
    plt.close(fig)


GPU_PROVIDERS = frozenset({"cuda", "directml", "tensorrt", "coreml", "openvino", "webgpu", "rocm", "mps"})


def load_gpu(feature: str, n_samples: int | None = None) -> tuple[dict, dict] | None:
    """Agrega la última run GPU real de cada motor, no una sola run global.

    Escanea la jerarquía designada (`results/_gpu/<feature>/`) y también la ruta
    CPU (`results/<feature>/`): hay runs GPU escritas sin `--output-dir`.

    Con `n_samples` solo se consideran runs GPU del **mismo tamaño de muestra**
    que la run CPU de referencia: al cambiar la muestra (p. ej. la estratificada
    de `layout`, n=40) las runs GPU viejas (n=20) miden otro conjunto de páginas
    y su calidad no sería comparable — mezclarlas rompería el «misma calidad CPU
    vs GPU» de la tabla consolidada.
    """
    roots = (GPU_RESULTS_DIR / feature, RESULTS_DIR / feature)
    runs = sorted({p for root in roots if root.is_dir() for p in root.iterdir()
                   if p.is_dir() and any(p.glob("*.csv"))},
                  key=lambda p: (p.name, p.as_posix()), reverse=True)
    if not runs:
        return None
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
        if n_samples is not None and summary.get("n_samples") != n_samples:
            continue
        rows, _ = load_run(run)
        rows = applicable_rows(feature, rows)
        grouped: dict[str, list[dict]] = defaultdict(list)
        for row in rows:
            backend = row.get("backend", "")
            provider = str(row.get("provider_effective", "")).lower()
            if provider not in GPU_PROVIDERS:
                continue
            grouped[backend].append(row)
        for backend, backend_rows in grouped.items():
            if backend in selected:
                continue
            selected[backend] = backend_rows
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
        gpu = load_gpu(feature, cpu_sum.get("n_samples"))
        gpu_rep, gpu_sum = gpu if gpu else ({}, {})
        if gpu and cpu_sum.get("dataset") != gpu_sum.get("dataset"):
            gpu_rep = {}
        key = TITULAR_METRIC[feature][0]
        for name in sorted(set(cpu_rep) | set(gpu_rep)):
            c, g = cpu_rep.get(name) or {}, gpu_rep.get(name) or {}
            backend = _backend_for(gpu_sum or {}, name)
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
        gpu = None if args.no_gpu else load_gpu(feature, summary.get("n_samples"))
        md = render_md(feature, report, summary, run, gpu=gpu)
        print(md)
        if not args.no_md:
            out = REPORTS_DIR / feature / "REPORT.md"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(md + "\n", encoding="utf-8")
            (REPORTS_DIR / feature / "REPORT.en.md").write_text(
                english_markdown(md) + "\n", encoding="utf-8"
            )
            # Tabla publicable MD/TeX desde el MISMO agregado que el REPORT: una
            # única fuente, así las celdas de las tres no divergen. `layout` tiene
            # su propio generador estratificado (`features.layout.table`), que
            # manda: no se pisa desde aquí.
            if feature != "layout":
                table_md, table_tex = render_table(feature, report, summary)
                (REPORTS_DIR / feature / "benchmark_table.md").write_text(table_md, encoding="utf-8")
                (REPORTS_DIR / feature / "benchmark_table.en.md").write_text(
                    english_markdown(table_md), encoding="utf-8"
                )
                (REPORTS_DIR / feature / "benchmark_table.tex").write_text(table_tex, encoding="utf-8")
            print(f"\n[report] {feature} -> {out} (+ .en.md)")
        if feature in TITULAR_METRIC:
            out = FIGURES_DIR / feature / "REPORT"
            out.parent.mkdir(parents=True, exist_ok=True)
            plot_feature(feature, report, summary, out, gpu_report=(gpu[0] if gpu else None))
            print(f"[report] {feature} -> {out}.png (+ .svg)")
        print()
    if features == sorted(FEATURE_COLUMNS):
        consolidated = REPORTS_DIR / "CPU_VS_GPU.md"
        table = consolidated_table(features)
        consolidated.parent.mkdir(parents=True, exist_ok=True)
        consolidated.write_text(table, encoding="utf-8")
        (REPORTS_DIR / "CPU_VS_GPU.en.md").write_text(
            english_markdown(table), encoding="utf-8"
        )
        print(f"[report] tabla consolidada -> {consolidated} (+ .en.md)")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
