#!/usr/bin/env python
"""Resumen GLOBAL de cobertura: quién cubre qué y la autogestión de modelos.

Genera, en la raíz de `benchmarks/`:

* `FEATURES_OVERVIEW.png` / `.svg` — matriz **feature × capacidad**: qué
  componentes de `pyocrust` sirven a cada feature, coloreados por origen
  (`medido` = banco con números reales; `esqueleto` = documentado, sin cifras).
* `FEATURES_OVERVIEW.md` — la misma matriz en markdown + la **autogestión**:
  un único paquete, N capacidades, catálogo y descarga/caché de modelos
  integradas (`ensure_models`, `resolve_models_dir`, `models_status`, offline).

Regla de honestidad: nada de números inventados. El catálogo de modelos viene de
`pyocrust.model_catalog()` (real); una feature sin banco ejecutado se marca
`esqueleto` y **no publica** valores.

Uso:
    .venv/Scripts/python.exe benchmarks/features/overview.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Sequence

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import BENCHMARKS_ROOT

OVERVIEW_PNG = BENCHMARKS_ROOT / "FEATURES_OVERVIEW.png"
OVERVIEW_SVG = BENCHMARKS_ROOT / "FEATURES_OVERVIEW.svg"
OVERVIEW_MD = BENCHMARKS_ROOT / "FEATURES_OVERVIEW.md"
RESULTS_DIR = BENCHMARKS_ROOT / "results"
FEATURES_DIR = Path(__file__).resolve().parent

# Orden del resumen (el del enunciado de la tarjeta).
FEATURE_ORDER: tuple[str, ...] = (
    "text", "layout", "orientation", "rectification", "text_line",
    "seal", "formula", "table", "full_page",
)

# Eje de **capacidades** = tareas del catálogo de `pyocrust` (`model_catalog()`).
CAPABILITY_ORDER: tuple[str, ...] = (
    "text_detection", "text_recognition", "layout_detection",
    "table_classification", "table_structure_recognition", "table_cell_detection",
    "document_orientation", "text_line_orientation", "document_rectification",
    "seal_text_detection", "formula_recognition", "indra",
)

# Feature -> capacidades que la sirven. Derivadas de la `pyocrust_task` de cada
# banco (`features/<f>/bank.py`) y de los artefactos de los perfiles de pipeline
# (`pp_ocrv6` = text_detection+text_recognition; `pp_structurev3` =
# layout+ocr+tabla+fórmula; `indra`). Se auto-verifica contra el catálogo real.
FEATURE_CAPABILITIES: dict[str, tuple[str, ...]] = {
    "text": ("text_detection", "text_recognition"),
    "layout": ("layout_detection",),
    "orientation": ("document_orientation",),
    "rectification": ("document_rectification",),
    "text_line": ("text_line_orientation",),
    "seal": ("seal_text_detection",),
    "formula": ("formula_recognition",),
    "table": ("table_classification", "table_structure_recognition", "table_cell_detection"),
    "full_page": ("layout_detection", "text_detection", "text_recognition",
                  "table_classification", "table_structure_recognition",
                  "table_cell_detection", "formula_recognition", "indra"),
}

# Perfiles de pipeline listos para usar (todos descargan/cachean sus modelos solos).
PIPELINE_PROFILES = ("pp_ocrv6_tiny", "pp_ocrv6_small", "pp_ocrv6_medium",
                     "pp_structurev3", "indra")


def load_catalog() -> dict[str, dict[str, Any]]:
    """Catálogo real de modelos (`pyocrust.model_catalog()`), o `{}` si no está."""
    try:
        import pyocrust

        return pyocrust.model_catalog()
    except Exception as exc:  # pragma: no cover - entorno sin el paquete
        print(f"[overview] catálogo no disponible: {exc}")
        return {}


def feature_status(feature: str) -> dict[str, Any]:
    """Estado real de una feature: banco, runs `medido` y referencias externas."""
    import importlib

    try:
        spec = importlib.import_module(f"features.{feature}.bank").SPEC
        status = spec.status
    except Exception:  # pragma: no cover - banco ausente
        status = "skeleton"
    latest = None
    runs = sorted(p for p in (RESULTS_DIR / feature).glob("*")
                  if p.is_dir() and any(p.glob("*.csv"))) if (RESULTS_DIR / feature).is_dir() else []
    if runs:
        latest = runs[-1].name
    report_md = FEATURES_DIR / feature / "REPORT.md"
    references = report_md.is_file() and "Referencias externas" in report_md.read_text(encoding="utf-8")
    if latest:
        estado = "medido"
    elif status == "implemented":
        estado = "documentado"
    else:
        estado = "esqueleto"
    return {"status": status, "latest": latest, "references": references, "estado": estado}


def catalog_tasks(catalog: dict[str, dict[str, Any]]) -> list[str]:
    return sorted({v.get("task") for v in catalog.values() if v.get("task")})


def usable(catalog: dict[str, dict[str, Any]]) -> list[str]:
    """Capacidades presentes a la vez en el eje y en el catálogo (intersección)."""
    present = set(catalog_tasks(catalog))
    if not present:
        return list(CAPABILITY_ORDER)
    return [c for c in CAPABILITY_ORDER if c in present or c == "indra"]


def _fmt_bytes(size: int | None) -> str:
    if not isinstance(size, int):
        return "N/A"
    if size >= 1_000_000_000:
        return f"{size / 1_000_000_000:.2f} GB"
    if size >= 1_000_000:
        return f"{size / 1_000_000:.1f} MB"
    return f"{size / 1_000:.1f} KB"


def capability_stats(catalog: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Por capacidad: nº de modelos y tamaño conocido (nunca inventado)."""
    stats: dict[str, dict[str, Any]] = {}
    for task in CAPABILITY_ORDER:
        models = [v for v in catalog.values() if v.get("task") == task]
        known = [v["size_bytes"] for v in models if isinstance(v.get("size_bytes"), int)]
        stats[task] = {
            "models": len(models),
            "known": len(known),
            "bytes": sum(known) if known else None,
            "features": [f for f in FEATURE_ORDER if task in FEATURE_CAPABILITIES[f]],
        }
    return stats


def build_matrix(statuses: dict[str, dict[str, Any]], capabilities: Sequence[str]) -> list[list[float | None]]:
    """Valor por celda: 2.0 `medido`, 1.0 `esqueleto`, `None` no cubierto.

    `None` (nunca un 0) para lo que pyocrust no cubre: una celda sin dato se deja
    vacía, no se rellena con un cero espurio.
    """
    matrix: list[list[float | None]] = []
    for feature in FEATURE_ORDER:
        covered = FEATURE_CAPABILITIES[feature]
        value = 2.0 if statuses[feature]["estado"] == "medido" else 1.0
        matrix.append([value if cap in covered else None for cap in capabilities])
    return matrix


def render_markdown(statuses: dict[str, dict[str, Any]], catalog: dict[str, dict[str, Any]],
                    capabilities: Sequence[str]) -> str:
    stats = capability_stats(catalog)
    known = [v["size_bytes"] for v in catalog.values() if isinstance(v.get("size_bytes"), int)]
    unknown = len(catalog) - len(known)
    total = sum(known)
    n_measured = sum(1 for f in FEATURE_ORDER if statuses[f]["estado"] == "medido")
    n_skeleton = len(FEATURE_ORDER) - n_measured

    lines = [
        "# Cobertura de `pyocrust` — «todo en uno», autogestionado",
        "",
        f"> **Un solo paquete** cubre **{len(FEATURE_ORDER)} features** en "
        f"**{len(capabilities)} capacidades** y **descarga y cachea sus propios "
        "modelos** (`ensure_models`), sin servicios externos ni pesos versionados "
        "a mano. Lo `medido` se separa siempre de lo `referencia` y lo `esqueleto`.",
        "",
        "![Cobertura feature × capacidad](FEATURES_OVERVIEW.png)",
        "",
        "## Autogestión de modelos",
        "",
        "- **`ensure_models`** (Rust, `src/storage/models.rs`) hace *preflight*, "
        "descarga en paralelo (4 hilos) lo que falte y **re-verifica** con sidecar "
        "`<name>.sha256` (evita re-hashear en caliente).",
        "- La invocan **`VeloceOCR(...)`** y **`TaskPredictor(...)`** en su "
        "constructor: pedir un pipeline descarga lo que falte y arranca.",
        "- **Python**: `pyocrust.models_status()` (qué hay y qué falta) y "
        "`pyocrust.resolve_models_dir()`; `PYOCRUST_OFFLINE=1` falla con error "
        "tipado y el comando exacto si falta un artefacto.",
        f"- **Catálogo**: **{len(catalog)} modelos** en {len(capabilities)} "
        f"capacidades (**{_fmt_bytes(total)}** conocidos"
        + (f" + {unknown} sin tamaño publicado" if unknown else "") + ").",
        "- **Perfiles de pipeline listos**: " + ", ".join(f"`{p}`" for p in PIPELINE_PROFILES) + ".",
        "",
        "### Catálogo por capacidad",
        "",
        "| Capacidad | Modelos | Tamaño conocido | Features que la usan |",
        "| :--- | ---: | ---: | :--- |",
    ]
    for cap in CAPABILITY_ORDER:
        s = stats[cap]
        feats = ", ".join(s["features"]) or "—"
        lines.append(f"| `{cap}` | {s['models']} | {_fmt_bytes(s['bytes'])} | {feats} |")
    lines += [
        "",
        "## Matriz feature × capacidad — qué cubre `pyocrust`",
        "",
        "`estado`: **medido** = banco ejecutado con números reales; **esqueleto** = "
        "documentado, sin cifras (nunca un `0`). `✔` = capacidad que sirve a la feature.",
        "",
        "| Feature | estado | " + " | ".join(f"`{c}`" for c in capabilities) + " |",
        "| :--- | :--- | " + " | ".join(":-:" for _ in capabilities) + " |",
    ]
    for feature in FEATURE_ORDER:
        st = statuses[feature]
        check = " | ".join("✔" if cap in FEATURE_CAPABILITIES[feature] else "·"
                           for cap in capabilities)
        lines.append(f"| **{feature}** | {st['estado']} | {check} |")
    lines += [
        "",
        "## Provenance (sin mezclar orígenes)",
        "",
        f"- **`medido`** ({n_measured}): " + ", ".join(
            f"`{f}`" for f in FEATURE_ORDER if statuses[f]["estado"] == "medido") + ".",
        f"- **`esqueleto`** ({n_skeleton}): " + ", ".join(
            f"`{f}`" for f in FEATURE_ORDER if statuses[f]["estado"] != "medido")
        + " — banco y README documentados, sin cifras.",
        "- **`referencia`**: " + ", ".join(
            f"`{f}`" for f in FEATURE_ORDER if statuses[f]["references"])
        + " citan tablas externas **con URL** en su `REPORT.md` (no comparables 1:1).",
        "",
    ]
    return "\n".join(lines)


def plot_overview(statuses: dict[str, dict[str, Any]], catalog: dict[str, dict[str, Any]],
                  capabilities: Sequence[str], out: Path) -> None:
    """Matriz feature × capacidad como heatmap, con leyenda de estados y autogestión."""
    import numpy as np
    from matplotlib.colors import BoundaryNorm, ListedColormap
    from matplotlib.patches import Patch

    from report_benchmarks import _pyplot

    matrix = build_matrix(statuses, capabilities)
    data = np.array([[np.nan if v is None else v for v in row] for row in matrix], dtype=float)

    plt = _pyplot()
    fig, ax = plt.subplots(
        figsize=(max(11.5, 0.95 * len(capabilities) + 4.5), max(5.2, 0.6 * len(FEATURE_ORDER) + 3.2))
    )
    # 1 -> esqueleto (ámbar), 2 -> medido (verde); NaN (no cubierto) -> blanco.
    cmap = ListedColormap(["#f0b429", "#2e8b57"]).with_extremes(bad="#ffffff")
    ax.imshow(np.ma.masked_invalid(data), cmap=cmap,
              norm=BoundaryNorm([0.5, 1.5, 2.5], cmap.N), aspect="auto")

    for i, feature in enumerate(FEATURE_ORDER):
        for j, cap in enumerate(capabilities):
            if cap in FEATURE_CAPABILITIES[feature]:
                ax.text(j, i, "✔", ha="center", va="center", color="white", fontsize=11)

    ax.set_xticks(list(range(len(capabilities))))
    ax.set_xticklabels([c.replace("_", "\n") for c in capabilities], fontsize=9)
    ax.set_yticks(list(range(len(FEATURE_ORDER))))
    ax.set_yticklabels([f"{f}  ·  {statuses[f]['estado']}" for f in FEATURE_ORDER], fontsize=10)
    ax.set_xticks(np.arange(-0.5, len(capabilities), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(FEATURE_ORDER), 1), minor=True)
    ax.grid(which="major", visible=False)
    ax.grid(which="minor", color="white", linewidth=2.0)
    ax.tick_params(which="minor", length=0)

    ax.legend(
        handles=[
            Patch(facecolor="#2e8b57", label="medido (banco con números)"),
            Patch(facecolor="#f0b429", label="esqueleto (documentado, sin cifras)"),
            Patch(facecolor="white", edgecolor="#bbbbbb", label="no cubierto"),
        ],
        loc="upper left", bbox_to_anchor=(1.02, 1.0), borderaxespad=0.0, frameon=False, fontsize=9,
    )

    known = [v["size_bytes"] for v in catalog.values() if isinstance(v.get("size_bytes"), int)]
    unknown = len(catalog) - len(known)
    fig.suptitle("pyocrust — cobertura «todo en uno» (feature × capacidad)",
                 fontsize=13, weight="bold")
    fig.text(0.5, -0.04,
             f"1 paquete · {len(FEATURE_ORDER)} features · {len(capabilities)} capacidades · "
             f"{len(catalog)} modelos auto-descargados en catálogo ({_fmt_bytes(sum(known))}"
             + (f" + {unknown} sin tamaño" if unknown else "") + ") · descarga y caché integradas",
             ha="center", fontsize=9, color="#333333")
    fig.tight_layout(rect=(0, 0.02, 1, 0.95))
    fig.savefig(out.with_suffix(".png"), dpi=160, bbox_inches="tight", facecolor="white")
    fig.savefig(out.with_suffix(".svg"), bbox_inches="tight", facecolor="white")
    plt.close(fig)


def _self_check() -> None:
    catalog = load_catalog()
    tasks = set(catalog_tasks(catalog))
    # Nunca se inventa una capacidad: todas las del eje existen en el catálogo real.
    if tasks:
        for feature, caps in FEATURE_CAPABILITIES.items():
            for cap in caps:
                assert cap in tasks, f"{feature}: capacidad inexistente en el catálogo -> {cap}"
    assert set(FEATURE_CAPABILITIES) == set(FEATURE_ORDER) == set(
        ["text", "layout", "orientation", "rectification", "text_line",
         "seal", "formula", "table", "full_page"])
    statuses = {f: {"estado": "medido" if f in ("text", "formula") else "esqueleto",
                    "references": f in ("text", "formula")} for f in FEATURE_ORDER}
    matrix = build_matrix(statuses, CAPABILITY_ORDER)
    assert len(matrix) == len(FEATURE_ORDER)
    assert all(len(row) == len(CAPABILITY_ORDER) for row in matrix)
    # full_page es la fila «todo en uno»: cubre más capacidades que cualquier otra.
    covered = [sum(v is not None for v in row) for row in matrix]
    assert covered[FEATURE_ORDER.index("full_page")] == max(covered)
    print("overview self-check OK")


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    argparse.ArgumentParser(description="Resumen global de cobertura").parse_args(argv)
    statuses = {f: feature_status(f) for f in FEATURE_ORDER}
    catalog = load_catalog()
    capabilities = usable(catalog)
    OVERVIEW_MD.write_text(render_markdown(statuses, catalog, capabilities) + "\n", encoding="utf-8")
    plot_overview(statuses, catalog, capabilities, OVERVIEW_PNG)
    print(f"[overview] -> {OVERVIEW_MD}")
    print(f"[overview] -> {OVERVIEW_PNG} (+ {OVERVIEW_SVG.name})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
