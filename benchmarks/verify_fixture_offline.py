"""Verifica el criterio: con red cortada y `data_cache/` vacio, las 9 features
producen filas `ok` (>=2 muestras) usando la fixture versionada.

Se ejecuta con el harness del bench (`common.datasets.load_dataset`) en un
entorno SIN red (HF_HUB_OFFLINE/TRANSFORMERS_OFFLINE) y con `DATA_CACHE`
apuntando a un directorio temporal vacio.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))

# Sin red y sin cache: fuerza el camino de la fixture.
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import common.datasets as datasets  # noqa: E402

# Cada una de las 9 features con el dataset que declara su banco.
FEATURES = {
    "text": "funsd",
    "formula": "omnidocbench_formula",
    "layout": "omnidocbench_layout",
    "table": "omnidocbench_table",
    "full_page": "omnidocbench_full_page",
    "orientation": "synthetic_orientation",
    "text_line": "synthetic_text_line",
    "rectification": "synthetic_rectification",
    "seal": "synthetic_seal",
}


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="empty_cache_"))
    datasets.DATA_CACHE = tmp  # cache vacia: solo queda la fixture
    failures = []
    for feature, dataset in FEATURES.items():
        datasets._set_provenance("dataset", None)
        samples = datasets.load_dataset(dataset, limit=10)
        prov = datasets.fixture_provenance()
        ok = len(samples) >= 2
        print(f"{feature:14s} dataset={dataset:24s} n={len(samples):2d} "
              f"source={prov['source']:7s} {'OK' if ok else 'FAIL'}")
        if not ok:
            failures.append(f"{feature}: {len(samples)} muestras")
    if failures:
        print("\nFALLOS:", failures)
        return 1
    print("\nTODAS las 9 features cargan >=2 muestras sin red.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
