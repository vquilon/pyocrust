"""Muestra estratificada de `layout` (criterio de aceptación de la tarjeta).

Sobre la anotación **real** de OmniDocBench ya cacheada (sin red; si no está, se
omite), comprueba que el muestreo estratificado por `data_source × layout`
cumple: ≥6 estratos cubiertos, ningún estrato >40% de la muestra, ninguna página
`equation_hard` >50%, y orden determinista. Además, el `stratum` viaja al CSV y
la sección "Por estrato" solo se emite para `layout` y cuando hay estratos.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest
from PIL import Image

from common import CSV_FIELDS, OcrOutput, Sample, run_benchmark
from common import datasets
from common.datasets import (
    _cached_page_annotation,
    _odb_page_attribute,
    _odb_stratified,
    _odb_stratum,
)
from features import report


def _cached_pages():
    """Anotación **real** de OmniDocBench (la del cache, no la fixture mínima).

    Criterio sobre la muestra completa: con el cache ausente, `_cached_page_annotation`
    cae a la fixture (10 páginas) y no puede cumplir `limit=40`/≥6 estratos, así que
    aquí se omite explícitamente si la anotación real no está cacheada.
    """
    if not sorted((datasets.DATA_CACHE / "datasets--opendatalab--OmniDocBench")
                  .glob("snapshots/*/OmniDocBench.json")):
        pytest.skip("anotación real de OmniDocBench no está en benchmarks/data_cache")
    pages = _cached_page_annotation()
    if not pages:
        pytest.skip("anotación OmniDocBench no está en benchmarks/data_cache")
    return pages


@pytest.mark.parametrize("limit", [20, 40])
def test_muestra_estratificada_cumple_el_criterio(limit):
    sample = _odb_stratified(_cached_pages(), limit=limit)
    assert len(sample) == limit
    counts: dict[str, int] = {}
    for page in sample:
        key = _odb_stratum(page)
        counts[key] = counts.get(key, 0) + 1
    assert len(counts) >= 6, counts                                   # ≥6 estratos
    assert max(counts.values()) <= limit * 0.4, counts                # ninguno >40%
    equation = sum(1 for p in sample
                   if _odb_page_attribute(p).get("subset") == "equation_hard")
    assert equation <= limit * 0.5, equation                          # ≤50% equation_hard


def test_muestra_estratificada_es_determinista():
    pages = _cached_pages()
    first = [_odb_stratum(p) for p in _odb_stratified(pages, limit=40)]
    second = [_odb_stratum(p) for p in _odb_stratified(pages, limit=40)]
    assert first == second


def test_stratum_viaja_al_csv():
    sample = Sample("p", Image.new("RGB", (4, 4)), "", stratum="book × single_column")
    rows, meta = run_benchmark(
        [sample], "pyocrust_layout", "omnidocbench_layout", warmup=0,
        backend_factory=lambda: lambda image: OcrOutput(""),
    )
    assert meta["status"] == "ok"
    assert "stratum" in CSV_FIELDS
    assert rows[0]["stratum"] == "book × single_column"
    # Sin estrato anotado la celda queda vacía (nunca inventada).
    rows, _ = run_benchmark(
        [Sample("q", Image.new("RGB", (4, 4)), "")], "pyocrust_layout",
        "omnidocbench_layout", warmup=0,
        backend_factory=lambda: lambda image: OcrOutput(""),
    )
    assert rows[0]["stratum"] == ""


def test_seccion_por_estrato():
    rows = [{"backend": "pyocrust_layout", "model_name": "pp-doclayoutv3",
             "model_variant": "130M", "stratum": "book × single_column",
             "layout_map": 0.5, "layout_recall": 0.6},
            {"backend": "pyocrust_layout", "model_name": "pp-doclayoutv3",
             "model_variant": "130M", "stratum": "newspaper × other_layout",
             "layout_map": 0.2, "layout_recall": 0.3}]
    section = report.render_strata("layout", rows)
    assert section[0] == "## Por estrato (`data_source × layout`)"
    assert "0.500" in "\n".join(section) and "0.200" in "\n".join(section)
    # `(motor, estrato) -> métricas` se agrupa como en la comparativa.
    grouped = report.strata_summary(rows, ["layout_map", "layout_recall"])
    assert grouped[("pp-doclayoutv3 (130M)", "book × single_column")]["layout_map"] == [0.5]
    # La sección es genérica: cada feature publica su métrica primaria.
    formula_rows = [{"backend": "pyocrust_formula", "model_name": "latex_ocr",
                     "stratum": "book × single_column", "latex_sim": 0.7}]
    formula_section = report.render_strata("formula", formula_rows)
    assert "### LaTeX sim por estrato" in formula_section
    assert "0.700" in "\n".join(formula_section)
    # Features sin `stratum` (p. ej. `text`) y filas vacías no emiten sección.
    assert report.render_strata("text", rows) == []
    assert report.render_strata("layout", []) == []
    assert report.render_strata("formula", []) == []


def _fake_image(_name, _cache):
    return Image.new("RGB", (4, 4))


def test_ninguna_feature_omnidocbench_muestrea_en_un_solo_estrato(monkeypatch):
    """Criterio de la tarjeta sobre la muestra **real** de cada feature.

    Ninguna feature OmniDocBench puede muestrear en un solo estrato: la muestra
    derivada de sus loaders cubre >=3 estratos (`data_source × layout`) y ninguna
    página `equation_hard` supera el 50%. Se comprueba sobre los loaders reales
    (no sobre `_odb_stratified` a secas): el sesgo que se cuela por el **pool**
    de páginas elegibles —313 de 1651 en `formula`— no lo ve el selector de
    páginas, así que el criterio tiene que asertarse sobre la muestra final.
    """
    pages = _cached_pages()
    monkeypatch.setattr(datasets, "_load_omnidocbench_pages",
                        lambda cache_dir=None: pages)
    monkeypatch.setattr(datasets, "_odb_image", _fake_image)
    monkeypatch.setattr(datasets, "_crop_poly", lambda image, poly, pad=4: image)
    by_path = {str(p["page_info"]["image_path"]): p for p in pages}
    by_stem = {Path(p["page_info"]["image_path"]).stem: p for p in pages}

    def page_of(sample):
        image_id = sample.image_id
        if "::" in image_id:
            return by_stem[image_id.split("::")[0]]
        return by_path.get(image_id) or by_stem.get(Path(image_id).stem)

    # (loader, sus dos tamaños de muestra: default del banco y n=20)
    cases = [
        (datasets.load_omnidocbench_formulas, (10, 20)),
        (datasets.load_omnidocbench_tables, (10, 20)),
        (datasets.load_omnidocbench_full_page, (6, 20)),
        (datasets.load_omnidocbench_layout, (20, 40)),
    ]
    for loader, limits in cases:
        for limit in limits:
            samples = loader(limit=limit)
            assert len(samples) == limit, (loader.__name__, limit, len(samples))
            strata = {_odb_stratum(page_of(s)) for s in samples}
            assert len(strata) >= 3, (loader.__name__, limit, strata)
            equation = sum(1 for s in samples
                           if _odb_page_attribute(page_of(s)).get("subset") == "equation_hard")
            assert equation <= limit * 0.5, (loader.__name__, limit, equation)


def test_los_recortes_se_reparten_entre_paginas(monkeypatch):
    """`formula`/`table` reparten sus recortes entre páginas, no los agolpan.

    Regresión del sesgo que dejaba `formula` en ~17-20/20 `equation_hard`: el
    round-robin (`_spread_dets_per_page`) hace que ninguna página aporte más de la
    mitad de la muestra y que salgan >=3 estratos.
    """
    pages = _cached_pages()
    monkeypatch.setattr(datasets, "_load_omnidocbench_pages",
                        lambda cache_dir=None: pages)
    monkeypatch.setattr(datasets, "_odb_image", _fake_image)
    monkeypatch.setattr(datasets, "_crop_poly", lambda image, poly, pad=4: image)
    by_stem = {Path(p["page_info"]["image_path"]).stem: p for p in pages}

    for loader in (datasets.load_omnidocbench_formulas,
                   datasets.load_omnidocbench_tables):
        samples = loader(limit=20)
        assert len(samples) >= 10, loader.__name__
        per_page = Counter(s.image_id.split("::")[0] for s in samples)
        assert max(per_page.values()) <= len(samples) / 2, (loader.__name__, per_page)
        strata = {_odb_stratum(by_stem[stem]) for stem in per_page if stem in by_stem}
        assert len(strata) >= 3, (loader.__name__, strata)
