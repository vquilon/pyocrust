"""Fixture minima versionada: ninguna feature se queda sin dataset sin red.

Verifica el criterio de la tarjeta `[bench][datasets] Fixture minima versionada`:

* la fixture esta en `benchmarks/fixtures/` (NO en `data_cache/`), pesa < 20 MB y
  **no** la ignora git;
* con la red cortada y `data_cache/` vacio, **cada una de las 9 features**
  produce >= 2 muestras usando la fixture;
* el provenance declara que el origen es la `fixture` (no la muestra completa).

No descarga nada: `load_dataset` se ejecuta con los loaders apuntando a una cache
vacia y a la fixture versionada (el unico camino que queda sin red).
"""

from __future__ import annotations

from pathlib import Path

import pytest

import common.datasets as datasets

BENCHMARKS = Path(__file__).resolve().parents[1]
FIXTURES = BENCHMARKS / "fixtures"

# Cada una de las 9 features con el dataset que declara su banco. `True` = el
# dataset se lee de una fuente externa (HF/cache -> fixture); `False` = set
# **sintetico** propio (seal), que no depende de ningun dataset.
FEATURE_DATASETS = {
    "text": ("funsd", True),
    "formula": ("omnidocbench_formula", True),
    "layout": ("omnidocbench_layout", True),
    "table": ("omnidocbench_table", True),
    "full_page": ("omnidocbench_full_page", True),
    "orientation": ("synthetic_orientation", True),
    "text_line": ("synthetic_text_line", True),
    "rectification": ("synthetic_rectification", True),
    "seal": ("synthetic_seal", False),
}

FIXTURE_DIRS = ("omnidocbench_mini", "funsd_mini")


def _fixture_size() -> int:
    return sum(f.stat().st_size for d in FIXTURE_DIRS
               for f in (FIXTURES / d).rglob("*") if f.is_file())


def _gitignored(rel: str) -> bool:
    """¿Ignora `.gitignore` la ruta relativa `rel` (desde `benchmarks/`)?

    Implementa el subconjunto de patrones que usa el repo (rutas ancladas con
    `/`, globs `*`/`**`): evita invocar `git` (bloqueado en este sandbox) y no
    depende de librerias.
    """
    import fnmatch

    gitignore = BENCHMARKS.parent / ".gitignore"
    for line in gitignore.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        pattern = line.rstrip("/")
        if pattern.startswith("/"):
            pattern = pattern[1:]  # anclado a la raiz del repo
            target = f"benchmarks/{rel}"
        else:
            target = rel
        if fnmatch.fnmatch(target, pattern) or target.startswith(pattern + "/"):
            return True
    return False


def test_fixture_existe_pesa_menos_de_20mb_y_no_esta_ignorada():
    for name in FIXTURE_DIRS:
        assert (FIXTURES / name).is_dir(), f"falta la fixture {name}"
    assert _fixture_size() < 20 * 1024 * 1024, "la fixture debe pesar < 20 MB"
    # Commiteada: `.gitignore` NO debe ignorar la fixture (a diferencia de
    # `data_cache/`, que si esta en el `.gitignore`).
    for name in FIXTURE_DIRS:
        assert not _gitignored(f"fixtures/{name}"), f"{name} esta ignorada por .gitignore"
    # Control de la propia comprobacion: `data_cache` SI esta ignorada.
    assert _gitignored("data_cache")


@pytest.mark.parametrize("feature,dataset,external", 
                         [(f, d, e) for f, (d, e) in sorted(FEATURE_DATASETS.items())])
def test_feature_carga_desde_la_fixture_sin_red(feature, dataset, external, tmp_path, monkeypatch):
    # Sin red y sin cache: fuerza el camino de la fixture.
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    monkeypatch.setenv("HF_DATASETS_OFFLINE", "1")
    monkeypatch.setenv("TRANSFORMERS_OFFLINE", "1")
    monkeypatch.setattr(datasets, "DATA_CACHE", tmp_path)  # cache vacia
    datasets._set_provenance(datasets.PROVENANCE_DATASET, None)

    samples = datasets.load_dataset(dataset, limit=10)
    assert len(samples) >= 2, f"{feature}: {len(samples)} muestras"
    if external:
        assert datasets.fixture_provenance()["source"] == datasets.PROVENANCE_FIXTURE, \
            f"{feature}: el provenance debe declarar el origen fixture"


def test_fixture_omnidocbench_cubre_las_categorias_que_necesitan_las_features():
    """La fixture anota las categorias de las que dependen los GT por feature."""
    import json

    pages = json.loads((FIXTURES / "omnidocbench_mini" / "OmniDocBench.json")
                       .read_text(encoding="utf-8"))
    cats = {d["category_type"] for p in pages for d in p["layout_dets"] if not d.get("ignore")}
    # Sin estas no habria GT de layout/tabla/formula/full_page.
    for required in ("text_block", "title", "equation_isolated", "table", "figure"):
        assert required in cats, f"la fixture no anota {required}"
    # Y debe haber al menos una tabla con `html` y una formula con `latex`.
    assert any(d["category_type"] == "table" and d.get("html")
               for p in pages for d in p["layout_dets"])
    assert any(d["category_type"] == "equation_isolated" and d.get("latex")
               for p in pages for d in p["layout_dets"])


@pytest.mark.parametrize("feature,dataset,external",
                         [(f, d, e) for f, (d, e) in sorted(FEATURE_DATASETS.items())])
def test_el_harness_produce_filas_ok_sobre_la_fixture(feature, dataset, external,
                                                      tmp_path, monkeypatch):
    """`run_benchmark` produce filas `ok` sobre las muestras de la fixture.

    No carga ningun modelo: usa un backend de identidad (devuelve el GT) para
    comprobar que el pipeline del harness cierra sobre las muestras de la
    fixture (criterio: cada feature produce filas `ok` >= 2).
    """
    from common import OcrOutput, run_benchmark

    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    monkeypatch.setenv("HF_DATASETS_OFFLINE", "1")
    monkeypatch.setattr(datasets, "DATA_CACHE", tmp_path)
    samples = datasets.load_dataset(dataset, limit=4)

    def identity(image, sample=samples[0]):
        return OcrOutput(text=sample.gt_text or "", extra={"kind": "test"})

    rows, meta = run_benchmark(samples, "pyocrust", dataset, warmup=0,
                               backend_factory=lambda: identity)
    ok = [r for r in rows if r["status"] == "ok"]
    assert len(ok) >= 2, f"{feature}: {len(ok)} filas ok (meta={meta.get('status')})"
