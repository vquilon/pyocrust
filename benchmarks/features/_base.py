"""Utilidades comunes a los bancos por feature (`benchmarks/features/`).

Cada feature tiene su carpeta con:

* `README.md` — qué mide, su tarea en `pyocrust`, sus **alternativas Python
  reales**, su métrica y su **provenance** (`medido` vs `referencia`).
* `bank.py`   — el banco. Expone `SPEC` (un `FeatureSpec`) y `main(argv)`.

Los bancos ya implementados (`text`, `formula`) cargan un dataset con GT y
ejecutan `common.runner.run_backends`. Los que son **esqueleto documentado**
(sin dataset GT público local) exponen su `SPEC` y `run_skeleton` imprime el plan
y qué alternativas están disponibles, sin inventar números.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Sequence

# Ejecutable como script (`python benchmarks/features/_base.py`) y como módulo.
if __package__ in (None, ""):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import BENCHMARKS_ROOT, OcrOutput, ProviderUnavailable, module_available


@dataclass(frozen=True)
class FeatureSpec:
    """Descripción declarativa de un banco de feature.

    `alternatives` mapea nombre -> `(módulo_python, cómo_instalarlo)`: alimenta el
    reporte de disponibilidad y el `skipped` con motivo, sin inventar ejecución.
    """

    feature: str
    summary: str
    pyocrust_task: str | None
    metric: str
    dataset: str
    alternatives: dict[str, tuple[str, str]] = field(default_factory=dict)
    status: str = "skeleton"        # "implemented" | "skeleton"
    note: str = ""
    provenance: str = "sin valores numéricos medidos; esqueleto documentado"


def unavailable_factory(module: str, install_hint: str, note: str = "") -> Callable[[], Callable]:
    """Factoría honesta para una alternativa aún no integrada.

    Instalada o no, el backend queda **`skipped`** (nunca se cuenta como
    ejecutado): con `ProviderUnavailable` si falta el módulo, con
    `NotImplementedError` si está pero el adaptador no está escrito todavía.
    """
    def factory():
        if not module_available(module):
            raise ProviderUnavailable(f"pip install {install_hint}")
        raise NotImplementedError(note or f"adaptador {module} pendiente de integrar")

    return factory


def common_argparser(feature: str, description: str) -> argparse.ArgumentParser:
    """CLI uniforme de los bancos: dataset, límite, warmup, repeats, device, salida."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--dataset", default=None, help="dataset con GT (por defecto, el del banco)")
    parser.add_argument("--split", default="train")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--backends", default=None, help="separados por comas; los no disponibles se marcan skipped")
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--device", choices=["cpu", "gpu"], default="cpu")
    parser.add_argument("--output-dir", type=Path, default=BENCHMARKS_ROOT / "results")
    parser.add_argument("--dump-outputs", action="store_true")
    parser.add_argument("--feature", default=feature)
    return parser


def feature_out_dir(base: Path, spec: FeatureSpec) -> Path:
    """Subcarpeta de resultados por feature (`results/<feature>/`)."""
    return base / spec.feature


def run_skeleton(spec: FeatureSpec, argv: Sequence[str] | None = None) -> int:
    """Imprime el plan del esqueleto y el estado real de cada alternativa."""
    common_argparser(spec.feature, spec.summary).parse_args(argv)
    print(f"# banco de feature: {spec.feature}  (estado: {spec.status})")
    print(f"\n{spec.summary}\n")
    print(f"- tarea pyocrust   : {spec.pyocrust_task or '—'}")
    print(f"- métrica          : {spec.metric}")
    print(f"- dataset/GT        : {spec.dataset}")
    print(f"- provenance       : {spec.provenance}")
    if spec.note:
        print(f"- nota             : {spec.note}")
    print("\n## alternativas Python (disponibilidad real en este intérprete)")
    for name, (module, hint) in spec.alternatives.items():
        state = "instalado" if module_available(module) else f"skipped (pip install {hint})"
        print(f"- {name:24s} {state}")
    print("\n(esqueleto: no se ejecutan motores ni se inventan números)")
    return 0


# ---------------------------------------------------------------------------
# Estructura real de cada banco (para el README índice y los tests)
# ---------------------------------------------------------------------------

FEATURES_DIR = Path(__file__).resolve().parent
IMPLEMENTED_FEATURES = ("text", "formula")
SKELETON_FEATURES = (
    "layout", "orientation", "rectification", "text_line", "seal", "table", "full_page",
)


def all_feature_dirs() -> list[str]:
    return list(IMPLEMENTED_FEATURES) + list(SKELETON_FEATURES)


def _self_check() -> None:
    assert len(set(all_feature_dirs())) == len(all_feature_dirs()) == 9
    for name in all_feature_dirs():
        assert (FEATURES_DIR / name / "bank.py").is_file(), f"falta features/{name}/bank.py"
        assert (FEATURES_DIR / name / "README.md").is_file(), f"falta features/{name}/README.md"
    factory = unavailable_factory("__no_existe__", "x")
    try:
        factory()
    except ProviderUnavailable as exc:
        assert "pip install" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("unavailable_factory debía marcar skipped")
    print("features._base self-check OK")


if __name__ == "__main__":  # pragma: no cover - ejecución manual
    _self_check()
