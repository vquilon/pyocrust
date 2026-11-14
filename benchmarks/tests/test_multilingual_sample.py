"""Muestra **no china** (inglesa/latina) para la comparativa de parse.

Criterio de la tarjeta `[bench][datasets] Muestra multilingue no-china para la
comparativa de parse`: un loader de dataset con muestra no china **versionada**
(misma revision HF pinnada + checksum del manifiesto que el resto de OmniDocBench),
de composicion **declarada** (cruce `image_id` × `page_info.page_attribute`) y con
`n` suficiente para comparar motores, reproducible **offline**.

Sobre la anotacion **real** cacheada (sin red; se omite si no esta): la muestra es
de un solo idioma (`english`), cubre >=3 estratos y ningun estrato >40%, es
determinista, y el manifiesto declara la MISMA composicion que se recalcula del
cache — paginas concretas incluidas (los `image_ids`).
"""

from __future__ import annotations

from collections import Counter

import pytest
from PIL import Image

import common.datasets as datasets
from common import load_manifest
from common.datasets import (
    ODB_EN_LANGUAGES,
    ODB_EN_SAMPLE_N,
    OMNIDOCBENCH_REVISION,
    DatasetOffline,
    _odb_language,
    _odb_only_languages,
    _odb_page_attribute,
    _odb_stratum,
    odb_composition,
)


def _cached_pages():
    """Anotacion **real** de OmniDocBench (la del cache; si no esta, se omite)."""
    if not sorted((datasets.DATA_CACHE / "datasets--opendatalab--OmniDocBench")
                  .glob("snapshots/*/OmniDocBench.json")):
        pytest.skip("anotacion real de OmniDocBench no esta en benchmarks/data_cache")
    pages = datasets._cached_page_annotation()
    if not pages:
        pytest.skip("anotacion OmniDocBench no esta en benchmarks/data_cache")
    return pages


@pytest.fixture
def fake_omnidocbench(monkeypatch):
    """Loader sobre la anotacion real, sin descargar ninguna imagen."""
    pages = _cached_pages()
    monkeypatch.setattr(datasets, "_load_omnidocbench_pages", lambda cache_dir=None: pages)
    monkeypatch.setattr(datasets, "_odb_image", lambda name, cache: Image.new("RGB", (4, 4)))
    by_path = {str(p["page_info"]["image_path"]): p for p in pages}
    return lambda image_id: by_path[image_id]


def test_la_muestra_no_china_es_solo_el_idioma_latino_anotado(fake_omnidocbench):
    """El loader del registro sirve **solo** paginas `english` en `n` declarado."""
    page_of = fake_omnidocbench
    samples = datasets.load_dataset("omnidocbench_full_page_en", limit=ODB_EN_SAMPLE_N)
    assert len(samples) == ODB_EN_SAMPLE_N, len(samples)
    assert {_odb_language(page_of(s.image_id)) for s in samples} == {"english"}
    # `en_ch_mixed` lleva chino mezclado: existe en el dataset y queda FUERA.
    langs = {_odb_language(p) for p in _cached_pages()}
    assert {"simplified_chinese", "en_ch_mixed"} <= langs
    assert not langs - {"english"} & {_odb_language(page_of(s.image_id)) for s in samples}
    # Sin `language` el comportamiento previo no cambia (todas las paginas).
    every = datasets.load_omnidocbench_full_page(limit=12)
    assert any(_odb_language(page_of(s.image_id)) != "english" for s in every)


@pytest.mark.parametrize("limit", [ODB_EN_SAMPLE_N, 40])
def test_muestra_no_china_cumple_el_criterio_estratificado(fake_omnidocbench, limit):
    """>=3 estratos, ninguno >40%, <=50% `equation_hard` y orden determinista."""
    page_of = fake_omnidocbench
    samples = datasets.load_omnidocbench_full_page(limit=limit, language=ODB_EN_LANGUAGES)
    assert len(samples) == limit
    strata: Counter = Counter(_odb_stratum(page_of(s.image_id)) for s in samples)
    assert len(strata) >= 3, strata
    assert max(strata.values()) <= limit * 0.4, strata
    equation = sum(1 for s in samples
                   if _odb_page_attribute(page_of(s.image_id)).get("subset") == "equation_hard")
    assert equation <= limit * 0.5, equation
    again = datasets.load_omnidocbench_full_page(limit=limit, language=ODB_EN_LANGUAGES)
    assert [s.image_id for s in again] == [s.image_id for s in samples]


def test_pool_sin_el_idioma_pedido_falla_claro_offline():
    """Un pool sin el idioma pedido no da 0 muestras: falla con el remedio."""
    def page(language: str, path: str) -> dict:
        return {"layout_dets": [], "page_info": {
            "image_path": path, "page_attribute": {"language": language}}}

    assert _odb_language({}) == ""                        # sin anotar, no se inventa
    only_en = _odb_only_languages([page("english", "a.png"), page("en_ch_mixed", "b.png")],
                                  ODB_EN_LANGUAGES)
    assert [p["page_info"]["image_path"] for p in only_en] == ["a.png"]
    with pytest.raises(DatasetOffline) as exc:
        _odb_only_languages([page("simplified_chinese", "c.png")], ODB_EN_LANGUAGES)
    assert "--fetch" in str(exc.value)


def test_el_manifiesto_declara_la_composicion_de_la_muestra(fake_omnidocbench):
    """La composicion declarada cruza `image_id` × `page_attribute` y es la real.

    Recalculada offline del cache: si la muestra o el `n` cambian sin regenerar el
    manifiesto, este test cae (la declaracion no puede mentir).
    """
    page_of = fake_omnidocbench
    declared = load_manifest()["samples"]["omnidocbench_full_page_en"]
    pool = datasets._odb_full_page_pool(languages=ODB_EN_LANGUAGES)
    sample = pool[: declared["declared_n"]]
    assert declared["pool"] == odb_composition(pool)
    assert declared["sample"] == odb_composition(
        sample, [p["page_info"]["image_path"] for p in sample])
    # Cada `image_id` declarado existe, esta en la anotacion y es del idioma pedido.
    ids = declared["sample"]["image_ids"]
    assert len(ids) == declared["declared_n"] == ODB_EN_SAMPLE_N
    assert len(set(ids)) == len(ids)
    assert all(_odb_language(page_of(image_id)) == "english" for image_id in ids)
    # Misma revision pinnada que el resto del dataset (versionada, no un tag movil).
    assert declared["provenance"] == "medido"
    assert load_manifest()["revision"] == OMNIDOCBENCH_REVISION
    # Las referencias externas se declaran como `referencia`, nunca como medidas.
    refs = load_manifest()["external_references"]
    assert {"parsebench", "fr-bench-pdf2md"} <= set(refs)
    assert "referencia" in refs["comment"]


def test_muestra_no_china_es_reproducible_offline(tmp_path, monkeypatch):
    """Sin red y con el cache vacio cae a la fixture versionada, y la declara."""
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    monkeypatch.setenv("HF_DATASETS_OFFLINE", "1")
    monkeypatch.setattr(datasets, "DATA_CACHE", tmp_path)
    datasets._set_provenance(datasets.PROVENANCE_DATASET, None)
    samples = datasets.load_dataset("omnidocbench_full_page_en", limit=10)
    assert len(samples) >= 2, len(samples)              # la fixture tiene 2 `english`
    fixture = {str(p["page_info"]["image_path"]): p for p in
               datasets._load_omnidocbench_pages(tmp_path)}
    assert all(_odb_language(fixture[s.image_id]) == "english" for s in samples)
    assert datasets.fixture_provenance()["source"] == datasets.PROVENANCE_FIXTURE
