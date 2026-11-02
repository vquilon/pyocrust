#!/usr/bin/env python
"""Resumen de benchmarks de las 9 features: `medido` + `referencia` (separados).

Genera `benchmarks/SUMMARY.png` + `SUMMARY.svg` + `SUMMARY.md`.

Un panel por feature. En cada panel conviven dos orígenes, **siempre distinguidos**:

* **`medido`** — números ejecutados en este repo (`features/<feature>/REPORT.md`,
  sección `## Comparativa`). Barra sólida; `pyocrust` en verde.
* **`referencia`** — valores publicados en papers (`features/<feature>/REFERENCES.md`,
  o la sección `## Referencias externas` del REPORT). Barra gris rayada.

Las features sin ningún dato salen como **`pendiente`** (sin barras): nunca se
inventan cifras. Las métricas externas pueden diferir de las nuestras, por eso cada
panel declara su métrica y las referencias van marcadas (no equivalencia 1:1).

Uso:
    .venv/Scripts/python.exe benchmarks/features/summary.py
"""
from __future__ import annotations

import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent

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

REF_URL = re.compile(r"\[ref:\s*(https?://[^\]]+)\]")
DATASET_RE = re.compile(r"\*\*dataset\*\*:\s*`([^`]+)`")


def parse_dataset(feature: str) -> str:
    """Token del `dataset`/GT realmente medido (`**dataset**: \\`x\\`` del REPORT)."""
    p = BENCH / "features" / feature / "REPORT.md"
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


# Features cuya tabla mezcla `medido` (nuestro GT) con `referencia` externa: el
# panel lo avisa para que NUNCA se lea como una comparación 1:1. La referencia
# usa otro dataset y/o otra métrica; se dice cuál. La nota entra en el título del
# panel, así que se mantiene CORTA (<= ~45 car.) para no invadir el panel vecino.
REF_NOTE = {
    "rectification": "ref: UVDoc CER↓ (otra métrica y dataset)",
    "layout": "ref: DocLayNet mAP (otro dataset/GT)",
    "table": "ref: PubTabNet/ICDAR (otro dataset/GT)",
    "orientation": "ref: PP-LCNet (otro conjunto de eval.)",
    "text_line": "ref: PP-LCNet (otro conjunto de eval.)",
    "full_page": "ref: OmniDocBench Overall (otra escala 0-100)",
}


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
    p = BENCH / "features" / feature / "REPORT.md"
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


def parse_references(feature: str) -> tuple[dict[str, float], str, str]:
    """(valores, métrica, url). Prioriza `REFERENCES.md`; si no, la sección del REPORT."""
    refs_md = BENCH / "features" / feature / "REFERENCES.md"
    if refs_md.exists():
        lines = refs_md.read_text(encoding="utf-8").splitlines()
        header, rows = _rows_from(lines, 0)
        url_m = REF_URL.search(refs_md.read_text(encoding="utf-8"))
        url = url_m.group(1) if url_m else ""
        if header and rows:
            mi = next((i for i, h in enumerate(header) if h.lower().startswith("métrica")), None)
            vi = next((i for i, h in enumerate(header) if h.lower().startswith("valor")), None)
            if vi is None:  # tablas que nombran la métrica en la cabecera (p. ej. "Overall ↑")
                vi = next((i for i, h in enumerate(header) if "↑" in h), None)
            if vi is not None:
                metric = header[mi] if mi is not None else header[vi]
                ui = next((i for i, h in enumerate(header) if h.lower().startswith("fuente")), None)
                out: dict[str, float] = {}
                urls: dict[str, str] = {}
                for cells in rows:
                    if vi < len(cells):
                        v = _num(cells[vi])
                        if v is not None:
                            out[cells[0]] = v
                            if ui is not None and ui < len(cells):
                                m2 = REF_URL.search(cells[ui])
                                urls[cells[0]] = m2.group(1) if m2 else url
                if out:
                    return out, metric, urls

    # fallback: sección de referencias dentro del REPORT.md
    rep = BENCH / "features" / feature / "REPORT.md"
    if not rep.exists():
        return {}, "", {}
    text = rep.read_text(encoding="utf-8")
    m = REF_URL.search(text)
    url = m.group(1) if m else ""
    lines = text.splitlines()
    i = next((i for i, ln in enumerate(lines)
              if ln.strip().lower().startswith("## referencias externas")), None)
    if i is None:
        return {}, "", {}
    header, rows = _rows_from(lines, i + 1)
    if not header or not rows:
        return {}, "", {}
    col = next((k for k in header if "↑" in k), None)
    if col is None:
        return {}, "", {}
    idx = header.index(col)
    out = {}
    for cells in rows:
        if idx < len(cells):
            v = _num(cells[idx])
            if v is not None:
                out[cells[0]] = v
    return out, col, {n: url for n in out}


def _panel(ax, measured, refs, title):
    entries = []  # (nombre, valor, origen)
    entries += [(n, v, "medido") for n, v in measured.items()]
    entries += [(n, v, "referencia") for n, v in refs.items()]
    if not entries:
        ax.axis("off")
        ax.set_title(f"{title}\n(pendiente: sin datos ni referencia)", fontsize=9, color="#888")
        return
    entries.sort(key=lambda e: e[1])
    names = [e[0] for e in entries]
    vals = [e[1] for e in entries]
    colors, hatches = [], []
    for n, _v, origin in entries:
        if origin == "referencia":
            colors.append("#b0bec5")
            hatches.append("//")
        else:
            colors.append("#2e7d32" if "pyocrust" in n else "#607d8b")
            hatches.append(None)
    bars = ax.barh(range(len(vals)), vals)
    for bar, c, h in zip(bars, colors, hatches):
        bar.set_color(c)
        if h:
            bar.set_hatch(h)
            bar.set_edgecolor("#78909c")
    for i, v in enumerate(vals):
        ax.text(v + (max(vals) or 1) * 0.01, i, f"{v:.3f}", va="center", fontsize=7)
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

    md = ["# Resumen de benchmarks — 9 features (`medido` + `referencia`)", "",
          "> `medido` = ejecutado en este repo · `referencia` = publicado en un paper (con URL),",
          "> **no comparable 1:1** · `pendiente` = aún sin datos. Una barra rayada es referencia.", ""]

    for k, (feature, titular) in enumerate(FEATURES):
        measured = parse_measured(feature, titular)
        refs, metric, ref_urls = parse_references(feature)
        ds = parse_dataset(feature)
        title = feature_title(feature)
        nota = REF_NOTE.get(feature)
        _panel(axes[k], measured, refs, f"{title}\n({nota})" if nota else title)
        status = "medido" if measured else ("referencia" if refs else "pendiente")
        src = f" · **dataset medido**: `{ds}`" if ds else ""
        md += [f"## {title} — `{status}`{src}", ""]
        if nota:
            md += [f"> ⚠️ **{nota}**", ""]
        if measured or refs:
            md += ["| Motor | Valor | Origen |", "| :--- | ---: | :--- |"]
            for nm, v in sorted(measured.items(), key=lambda p: -p[1]):
                mark = "**" if "pyocrust" in nm else ""
                md.append(f"| {mark}{nm}{mark} | {v:.3f} | medido |")
            for nm, v in sorted(refs.items(), key=lambda p: -p[1]):
                src = ref_urls.get(nm, "") or "ver REFERENCES.md"
                md.append(f"| {nm} | {v:.3f} | referencia [ref: {src}] |")
        else:
            md.append("_Sin datos ni referencia todavía._")
        md.append("")

    for ax in axes[n:]:
        ax.axis("off")

    fig.legend(handles=[
        Patch(facecolor="#2e7d32", label="pyocrust (medido)"),
        Patch(facecolor="#607d8b", label="alternativa (medida)"),
        Patch(facecolor="#b0bec5", hatch="//", edgecolor="#78909c", label="referencia (externo)"),
    ], loc="lower center", bbox_to_anchor=(0.5, 0.035), ncol=3, frameon=False, fontsize=10)
    fig.suptitle("pyocrust — benchmarks por feature: medido vs referencia externa", fontsize=14)
    fig.text(0.5, 0.006,
             "Barra sólida = MEDIDO (dataset del título del panel) · barra rayada = REFERENCIA "
             "externa de OTRO dataset/métrica (ver nota del panel). No comparables 1:1.",
             ha="center", fontsize=8, color="#555555")
    fig.tight_layout(rect=(0, 0.075, 1, 0.96))
    for ext in ("png", "svg"):
        fig.savefig(BENCH / f"SUMMARY.{ext}", dpi=150, bbox_inches="tight", facecolor="white")
    (BENCH / "SUMMARY.md").write_text("\n".join(md), encoding="utf-8")
    print("[summary] ->", BENCH / "SUMMARY.png")
    print("[summary] ->", BENCH / "SUMMARY.md")
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
    # Toda feature con referencias externas avisa de que son otro dataset/métrica.
    for feature in ("layout", "table", "rectification", "orientation", "text_line", "full_page"):
        assert feature in REF_NOTE, f"falta REF_NOTE para {feature}"
    print("features.summary self-check OK")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        _self_check()
    else:
        raise SystemExit(main())
