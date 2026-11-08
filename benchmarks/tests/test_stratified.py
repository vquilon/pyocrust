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
    grouped = report.strata_summary(rows)
    assert grouped[("pp-doclayoutv3 (130M)", "book × single_column")]["layout_map"] == [0.5]
    # Otras features (sin `stratum`) y filas vacías no emiten sección.
    assert report.render_strata("text", rows) == []
    assert report.render_strata("layout", []) == []


def _fake_image(_name, _cache):
    return Image.new("RGB", (4, 4))


def test_los_loaders_de_omnidocbench_usan_el_orden_estratificado(monkeypatch):
    """Regresión: ninguna feature vuelve al orden crudo ni a `_odb_rich_first`.

    `_odb_image` se parchea para no tocar la red: lo que se comprueba es el
    **orden** en que cada loader visita las páginas, no su contenido.
    """
    pages = _cached_pages()
    # El pool de páginas y la imagen se sustituyen para no tocar red ni disco:
    # solo importa el ORDEN en que cada loader visita las páginas, y ambos lados
    # (loader y referencia) deben estratificar el MISMO pool.
    monkeypatch.setattr(datasets, "_load_omnidocbench_pages",
                        lambda cache_dir=None: pages)
    monkeypatch.setattr(datasets, "_odb_image", _fake_image)
    # El recorte real depende del tamaño de la página anotada; el contenido de
    # los recortes no se comprueba aquí, así que se neutraliza (`_crop_poly`
    # es un global del módulo).
    monkeypatch.setattr(datasets, "_crop_poly", lambda image, poly, pad=4: image)
    image_paths = [p["page_info"]["image_path"] for p in pages]
    strat_names = [p["page_info"]["image_path"] for p in _odb_stratified(pages)]
    by_name = {p["page_info"]["image_path"]: p for p in pages}
    # `tables`/`formulas` recortan el `image_id` a `Path(...).stem`, y la
    # extensión de la imagen varía por página (`.jpg`/`.png`): se resuelve el
    # nombre completo por stem en vez de adivinar la extensión.
    name_by_stem = {Path(image_path).stem: image_path for image_path in image_paths}

    for loader in (datasets.load_omnidocbench_full_page,
                   datasets.load_omnidocbench_tables,
                   datasets.load_omnidocbench_formulas):
        seen: list[str] = []
        for sample in loader(limit=20):
            stem = sample.image_id.split("::")[0]
            name = name_by_stem.get(stem, stem)
            if name not in seen:
                seen.append(name)
        assert seen, loader.__name__
        indexes = [strat_names.index(n) for n in seen]
        # Orden creciente = las páginas siguen el muestreo estratificado.
        assert indexes == sorted(indexes), loader.__name__
        assert len({_odb_stratum(by_name[n]) for n in seen}) >= 3, loader.__name__


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
