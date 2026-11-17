"""Fixture de **esquematicos**: versionada, offline y con fallo claro si falta.

Verifica el criterio de la tarjeta `[ref] Fixture offline de esquematicos`:
`benchmarks/fixtures/schematics_mini/` trae N<=10 paginas de esquematico (PNG
renderizado) con su texto visible esperado, **versionadas** (no ignoradas por
git), consumibles **sin red** por el harness, y `load_schematics` **falla claro**
si la fixture falta en un checkout limpio.

No descarga nada: `load_schematics` lee solo la fixture commiteada.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import common.datasets as datasets
from test_fixture_fallback import _gitignored

BENCHMARKS = Path(__file__).resolve().parents[1]
FIXTURE = BENCHMARKS / "fixtures" / "schematics_mini"
MAX_PAGES = 10


def _manifest() -> dict:
    return json.loads((FIXTURE / "manifest.json").read_text(encoding="utf-8"))


def test_fixture_existe_pesa_menos_de_20mb_y_no_esta_ignorada():
    assert FIXTURE.is_dir(), "falta la fixture de esquematicos"
    assert (FIXTURE / "manifest.json").is_file()
    total = sum(f.stat().st_size for f in FIXTURE.rglob("*") if f.is_file())
    assert total < 20 * 1024 * 1024, f"la fixture pesa {total / 1e6:.2f} MB (>=20 MB)"
    # Commiteada: `.gitignore` NO debe ignorarla (a diferencia de data_cache/).
    assert not _gitignored("fixtures/schematics_mini"), "la fixture esta ignorada por .gitignore"


def test_manifiesto_tiene_n_paginas_con_imagen_y_texto_esperado():
    pages = _manifest()["pages"]
    assert 1 <= len(pages) <= MAX_PAGES, f"{len(pages)} paginas (criterio: N<=10)"
    for page in pages:
        assert page["id"] and page["image"], page
        assert page["text"].strip(), f"{page['id']}: sin texto esperado"
        assert (FIXTURE / "images" / page["image"]).is_file(), f"falta la imagen {page['image']}"


def test_las_imagenes_cuadran_con_el_sha256_del_manifiesto():
    """Versionado verificable: los bytes de cada PNG son los que declara el manifiesto."""
    for page in _manifest()["pages"]:
        data = (FIXTURE / "images" / page["image"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == page["sha256"], page["id"]


def test_la_fixture_carga_sin_red_y_declara_su_origen(monkeypatch):
    for var in ("HF_HUB_OFFLINE", "HF_DATASETS_OFFLINE", "TRANSFORMERS_OFFLINE"):
        monkeypatch.setenv(var, "1")
    samples = datasets.load_dataset("schematics", limit=MAX_PAGES)
    assert len(samples) == len(_manifest()["pages"]), "N<=10 paginas"
    assert all(s.gt_text.strip() and s.image.width > 0 for s in samples)
    assert datasets.fixture_provenance()["source"] == datasets.PROVENANCE_FIXTURE


def test_load_schematics_falla_claro_si_falta_la_fixture(monkeypatch, tmp_path):
    """Checkout limpio sin la fixture: error **accionable**, no 0 muestras."""
    monkeypatch.setattr(datasets, "SCHEMATICS_FIXTURE", tmp_path / "schematics_mini")
    with pytest.raises(datasets.DatasetUnavailable) as exc:
        datasets.load_schematics(limit=MAX_PAGES)
    message = str(exc.value)
    assert "schematics_mini" in message and "build_schematics_fixture.py" in message, message


def test_el_harness_produce_filas_ok_sobre_la_fixture():
    """El pipeline del harness cierra sobre las muestras (backend de identidad)."""
    from common import OcrOutput, run_benchmark

    samples = datasets.load_schematics(limit=4)

    def identity(image, sample=samples[0]):
        return OcrOutput(text=sample.gt_text, extra={"kind": "test"})

    rows, meta = run_benchmark(samples, "pyocrust", "schematics", warmup=0,
                               backend_factory=lambda: identity)
    ok = [row for row in rows if row["status"] == "ok"]
    assert len(ok) >= 2, f"{len(ok)} filas ok (meta={meta.get('status')})"


def test_extractor_saca_solo_el_texto_visible():
    """El extractor es la fuente del GT: referencia/valor/texto/etiqueta visible.

    Quedan fuera el `hide`, las propiedades de libreria (plantilla) y el marcado
    de KiCad (`~{...}`/`{slash}` se convierten al texto renderizado).
    """
    import build_schematics_fixture as build

    got = build.extract_visible_text(
        '(kicad_sch (title_block (title "T"))'
        ' (lib_symbols (symbol "R" (property "Reference" "R" (at 0 0 0))))'
        ' (symbol (lib_id "Device:R") (at 1 1 0)'
        '  (property "Reference" "R1" (at 1 0 0) (effects (font (size 1.27 1.27))))'
        '  (property "Value" "10k" (at 1 2 0) (effects (font (size 1.27 1.27))))'
        '  (property "Footprint" "" (at 0 0 0) (effects (hide yes))))'
        ' (text "~{EN} Vcc{slash}2" (at 2 2 0) (effects (font (size 1.27 1.27)))))')
    assert {"R1", "10k", "EN Vcc/2", "T"} <= set(got), got
    assert "Footprint" not in got and "R" not in got, got   # oculto y plantilla
