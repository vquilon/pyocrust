"""Fetch reproducible: revision fijada + checksum verificado + fallo claro sin red.

Criterios de la tarjeta `[bench][datasets] Fetch reproducible`:

* la revision HF esta fijada y consta en el provenance;
* el manifiesto de checksums se verifica al cargar (fallo claro si no cuadra);
* sin red y sin cache, `prepare_datasets` falla con UN error accionable.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import common.datasets as datasets

BENCHMARKS = Path(__file__).resolve().parents[1]


def test_revision_fijada_y_en_el_manifiesto():
    manifest = datasets.load_manifest()
    assert manifest["revision"] == datasets.OMNIDOCBENCH_REVISION
    # La revision fija un sha de 40 hex (commit HF), no un tag movil.
    assert len(datasets.OMNIDOCBENCH_REVISION) == 40
    assert datasets.OMNIDOCBENCH_REVISION == manifest["revision"]


def test_manifiesto_versionado_y_no_ignorado_por_git():
    assert datasets.DATASETS_MANIFEST.is_file()
    # Debe estar FUERA de data_cache/ (gitignored) para viajar con el repo.
    assert "data_cache" not in datasets.DATASETS_MANIFEST.parts
    assert datasets.load_manifest()["files"]["OmniDocBench.json"]["sha256"]


def test_verify_file_acepta_el_hash_correcto_y_rechaza_el_errado(tmp_path):
    import hashlib

    f = tmp_path / "x.bin"
    f.write_bytes(b"contenido determinista")
    good = hashlib.sha256(f.read_bytes()).hexdigest()
    assert datasets.verify_file(f, good) == good
    with pytest.raises(datasets.DatasetUnavailable):
        datasets.verify_file(f, "0" * 64)


def test_prepare_sin_red_y_sin_cache_falla_claro(tmp_path, monkeypatch):
    """Sin red ni cache: UN `DatasetOffline` accionable, no N skips."""
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    monkeypatch.setenv("HF_DATASETS_OFFLINE", "1")
    monkeypatch.setattr(datasets, "DATA_CACHE", tmp_path)
    with pytest.raises(datasets.DatasetOffline) as exc:
        datasets.prepare_datasets(cache_dir=tmp_path)
    msg = str(exc.value)
    # El mensaje dice COMO poblarlo (criterio: instruccion, no un skip silencioso).
    assert "--fetch" in msg
    assert "fixture" in msg


def test_provenance_del_dataset_real_lleva_la_revision():
    datasets._set_provenance(datasets.PROVENANCE_DATASET,
                             datasets._omnidocbench_source_detail(),
                             revision=datasets.OMNIDOCBENCH_REVISION)
    prov = datasets.fixture_provenance()
    assert prov["revision"] == datasets.OMNIDOCBENCH_REVISION
    assert datasets.OMNIDOCBENCH_REVISION in prov["detail"]
