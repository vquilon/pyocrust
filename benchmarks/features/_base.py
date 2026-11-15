"""Utilidades comunes a los bancos por feature (`benchmarks/features/`).

Cada feature tiene su carpeta con:

* `README.md` — qué mide, su tarea en `pyocrust`, sus **alternativas Python
  reales**, su métrica y su **provenance** (`medido`; las referencias externas no
  entran en ningún informe, ver `REFERENCES.md` de cada feature).
* `bank.py`   — el banco. Expone `SPEC` (un `FeatureSpec`) y `main(argv)`.

Los bancos ya implementados (`text`, `formula`, `layout`, `table`, `full_page`,
`orientation`, `text_line`, `rectification`, `seal`) cargan un dataset con GT —o
generan uno sintético determinista— y ejecutan `common.runner.run_backends` con la
métrica de su feature. `run_skeleton` sigue disponible para cualquier feature sin
dataset GT que se documente en el futuro, pero hoy no queda ninguna: `seal` pasó a
medido con un set **sintético** (sello pegado en posición conocida).
"""

from __future__ import annotations

import argparse
import json
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
    def factory(device: str = "cpu"):
        if not module_available(module):
            raise ProviderUnavailable(f"pip install {install_hint}")
        raise NotImplementedError(note or f"adaptador {module} pendiente de integrar")

    return factory


def orientation_accuracy(sample, output) -> dict:
    """`ori_acc` = 1.0/0.0: la etiqueta de orientación emitida es la esperada.

    Compartida por los bancos de `orientation` (4 clases) y `text_line` (2): en
    ambos el GT es la etiqueta anotada/aplicada y la salida del clasificador es su
    `label` de mayor score. Sin etiqueta GT o sin salida queda **no evaluada**
    (""), nunca un 0.0 espurio.
    """
    label = output.extra.get("label")
    if sample.gt_label is None or label is None:
        return {"ori_acc": ""}
    return {"ori_acc": float(str(label) == str(sample.gt_label))}


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
    parser.add_argument("--variant", default=None,
                        help="subcarpeta de variante bajo la feature (p. ej. `vl` -> "
                             "results/<feature>/vl/<run>/), sin tocar la serie normal")
    parser.add_argument("--resume", action="store_true",
                        help="reanuda la corrida incompleta mas reciente de esta feature "
                             "(misma firma dataset/muestra/device) en vez de empezar de cero")
    return parser


def feature_out_dir(base: Path, spec: FeatureSpec, variant: str | None = None) -> Path:
    """Subcarpeta de resultados por feature: `results/<feature>[/<variant>]/`.

    La variante (`vl`) va **bajo** la feature, no al lado: así `latest_run` de la
    serie normal (`results/<feature>/*/`) no la confunde con una corrida propia.
    """
    root = base / spec.feature
    return root / variant if variant else root


def feature_run_dir(
    base: Path, spec: FeatureSpec, timestamp: str, variant: str | None = None,
    *, resume: bool = False, signature: dict | None = None,
) -> tuple[Path, str, bool]:
    """Resuelve `(run_dir, timestamp, resume_efectivo)` del banco.

    Sin `resume` (o sin corrida incompleta que case): `results/<feature>[/<variant>]/<timestamp>/`.
    Con `resume`: reusa la corrida **más reciente** cuyo `summary.json` tenga la misma
    `run_signature` (dataset/muestra/device) y le falte algún backend de su propio
    `backends_requested`, y devuelve su timestamp; el banco continúa ESA corrida en vez
    de empezar de cero.

    `ponytail:` casa por firma la corrida incompleta más reciente, no fusiona corridas
    ni elige a mano; para reanudar una concreta pásale su `--output-dir` directo.
    """
    root = feature_out_dir(base, spec, variant)
    root.mkdir(parents=True, exist_ok=True)
    if resume and signature is not None:
        for run in sorted((d for d in root.iterdir() if d.is_dir()), reverse=True):
            summary_path = run / "summary.json"
            if not summary_path.exists():
                continue
            try:
                data = json.loads(summary_path.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                continue
            if data.get("run_signature") != signature:
                continue
            done = {b for b, m in (data.get("backends") or {}).items()
                    if isinstance(m, dict) and m.get("status") == "ok"}
            if set(data.get("backends_requested") or ()) - done:
                return run, str(data.get("timestamp") or run.name), True
    return root / timestamp, timestamp, False


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
IMPLEMENTED_FEATURES = (
    "text", "formula", "layout", "table", "full_page", "orientation",
    "text_line", "rectification", "seal",
)
# Ninguna feature sigue siendo esqueleto: `seal` pasa a medido con un set
# **sintetico** determinista (no hay anotacion humana de sellos local).
SKELETON_FEATURES = ()


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
