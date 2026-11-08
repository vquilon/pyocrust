"""Muestra estratificada de `layout` (criterio de aceptación de la tarjeta).

Sobre la anotación **real** de OmniDocBench ya cacheada (sin red; si no está, se
omite), comprueba que el muestreo estratificado por `data_source × layout`
cumple: ≥6 estratos cubiertos, ningún estrato >40% de la muestra, ninguna página
`equation_hard` >50%, y orden determinista. Además, el `stratum` viaja al CSV y
la sección "Por estrato" solo se emite para `layout` y cuando hay estratos.
"""

from __future__ import annotations

import pytest
from PIL import Image

from common import CSV_FIELDS, OcrOutput, Sample, run_benchmark
from common.datasets import (
    _cached_page_annotation,
    _odb_page_attribute,
    _odb_stratified,
    _odb_stratum,
)
from features import report


def _cached_pages():
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
    grouped = report.strata_summary(rows)
    assert grouped[("pp-doclayoutv3 (130M)", "book × single_column")]["layout_map"] == [0.5]
    # Otras features (sin `stratum`) y filas vacías no emiten sección.
    assert report.render_strata("text", rows) == []
    assert report.render_strata("layout", []) == []
