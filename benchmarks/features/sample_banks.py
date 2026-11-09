#!/usr/bin/env python
"""Regenera y verifica el **banco de muestras** OmniDocBench de las 4 features.

Criterio (tarjeta `t_4d2155d3`): la muestra de cada feature cubre **>=3 estratos**
(`data_source × layout`) y **ningún estrato de página supera el 50%** de la
muestra. Los bancos se cargan con los **loaders reales** —el mismo camino que
`features/<feat>/bank.py` (`load_dataset`)— sobre la anotación cacheada; la
selección es determinista (mismo resultado en dos ejecuciones).

Escribe un manifiesto JSON (por defecto `results/sample_banks.json`) con la
composición de cada banco. Con `--check` devuelve rc=1 si alguna feature incumple
el criterio, para poder encadenarlo.

Uso:
    .venv/Scripts/python.exe benchmarks/features/sample_banks.py
    .venv/Scripts/python.exe benchmarks/features/sample_banks.py --check
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Sequence

# Ejecutable como script (`python benchmarks/features/sample_banks.py`).
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import BENCHMARKS_ROOT, load_dataset
from common.datasets import _cached_page_annotation, _odb_page_attribute, _odb_stratum

# (feature, dataset del banco, límite) — límites de la tarjeta t_4d2155d3.
BANKS = (
    ("formula", "omnidocbench_formula", 10),
    ("table", "omnidocbench_table", 8),
    ("full_page", "omnidocbench_full_page", 6),
    ("layout", "omnidocbench_layout", 40),
)
MIN_STRATA = 3
MAX_STRATUM_SHARE = 0.50


def _verdict(strata: Counter, n: int) -> tuple[bool, float]:
    """`(cumple, cuota_del_estrato_mayor)`: >=3 estratos y ninguno >50%."""
    if n == 0:
        return False, 0.0
    top = max(strata.values()) / n
    return (len(strata) >= MIN_STRATA and top <= MAX_STRATUM_SHARE), top


def _page_lookup(pages: list):
    """`image_id` -> página anotada (para leer el `subset` de cada muestra)."""
    by_path = {str(p["page_info"]["image_path"]): p for p in pages}
    by_stem = {Path(p["page_info"]["image_path"]).stem: p for p in pages}

    def page_of(image_id: str) -> dict | None:
        if "::" in image_id:                       # recorte de fórmula/tabla
            return by_stem.get(image_id.split("::")[0])
        return by_path.get(image_id) or by_stem.get(Path(image_id).stem)

    return page_of


def bank_composition(feature: str, dataset: str, limit: int, page_of) -> dict:
    """Carga el banco real y resume su composición (estratos + `equation_hard`)."""
    samples = load_dataset(dataset, limit=limit)
    strata: Counter = Counter()
    pages_seen: set[str] = set()
    eq_hard = 0
    for sample in samples:
        strata[sample.stratum or _odb_stratum(page_of(sample.image_id) or {})] += 1
        page = page_of(sample.image_id)
        if page is not None:
            pages_seen.add(str(page["page_info"]["image_path"]))
            if _odb_page_attribute(page).get("subset") == "equation_hard":
                eq_hard += 1
    n = len(samples)
    ok, top = _verdict(strata, n)
    eq_share = eq_hard / n if n else 0.0
    return {
        "feature": feature,
        "dataset": dataset,
        "limit": limit,
        "n": n,
        "pages": len(pages_seen),
        "strata": dict(sorted(strata.items())),
        "n_strata": len(strata),
        "max_stratum_share": round(top, 4),
        "equation_hard": eq_hard,
        "equation_hard_share": round(eq_share, 4),
        "ok": ok and eq_share <= MAX_STRATUM_SHARE,
        "samples": [[s.image_id, s.stratum or ""] for s in samples],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=BENCHMARKS_ROOT / "results" / "sample_banks.json")
    parser.add_argument("--check", action="store_true",
                        help="rc=1 si alguna feature incumple el criterio")
    args = parser.parse_args(argv)

    pages = _cached_page_annotation()
    page_of = _page_lookup(pages)
    print(f"[sample_banks] anotacion OmniDocBench: {len(pages)} paginas")

    banks = [bank_composition(f, d, n, page_of) for f, d, n in BANKS]

    print(f"\n{'feature':10s} {'n':>3s} {'pag':>4s} {'estratos':>8s} "
          f"{'max_estrato':>11s} {'eq_hard':>8s}  criterio")
    for b in banks:
        verdict = "OK" if b["ok"] else "FALLA"
        print(f"{b['feature']:10s} {b['n']:>3d} {b['pages']:>4d} {b['n_strata']:>8d} "
              f"{b['max_stratum_share'] * 100:>10.1f}% {b['equation_hard_share'] * 100:>7.1f}%  {verdict}")
        for name, count in sorted(b["strata"].items(), key=lambda kv: -kv[1]):
            print(f"    {name:40s} {count:>3d}  ({count / b['n'] * 100:.0f}%)")

    manifest = {
        "criterion": {"min_strata": MIN_STRATA, "max_stratum_share": MAX_STRATUM_SHARE},
        "features": {b["feature"]: b for b in banks},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[sample_banks] manifiesto en {args.output}")

    failed = [b["feature"] for b in banks if not b["ok"]]
    if failed:
        print(f"[sample_banks] INCUMPLEN el criterio: {', '.join(failed)}")
    return 1 if (args.check and failed) else 0


def _self_check() -> None:
    """La veredicta: >=3 estratos y ningún estrato >50%."""
    ok, top = _verdict(Counter({"a": 1, "b": 1, "c": 1}), 3)
    assert ok and top == 1 / 3
    ok, top = _verdict(Counter({"a": 2, "b": 1}), 3)       # solo 2 estratos
    assert not ok
    ok, _ = _verdict(Counter({"a": 3, "b": 1, "c": 1}), 5)  # 60% > 50%
    assert not ok
    ok, _ = _verdict(Counter({"a": 2, "b": 2, "c": 1}), 5)  # 40% <= 50%
    assert ok
    print("features.sample_banks self-check OK")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        _self_check()
    else:
        raise SystemExit(main())
