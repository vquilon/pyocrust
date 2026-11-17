"""API de alto nivel de documentos PDF (DESIGN.md §13, tarjeta t_a7f78bfa).

Todo offline: usa el fixture versionado ``tests/data/mixed_text_and_scan.pdf``
(una página con text-layer real y una sin él). No descarga ni modelos ni nada.

La librería nativa PDFium se resuelve desde ``PYOCRUST_PDFIUM_LIB``; el
``conftest``/fixture la publica desde el wheel de ``pypdfium2_raw`` del entorno
(el mismo binario que usa el propio repo para leer PDFs), o el test se salta.
"""

from __future__ import annotations

import os
import struct
from pathlib import Path

import pytest

import pyocrust

FIXTURE = Path(__file__).parent / "data" / "mixed_text_and_scan.pdf"


def _find_pdfium() -> str | None:
    """Ruta al ``pdfium.dll`` del entorno, o ``None`` si no está."""
    from_env = os.environ.get("PYOCRUST_PDFIUM_LIB")
    if from_env:
        return from_env
    try:
        import pypdfium2_raw
    except ImportError:
        return None
    candidate = Path(pypdfium2_raw.__file__).parent / "pdfium.dll"
    return str(candidate) if candidate.is_file() else None


@pytest.fixture(autouse=True)
def pdfium_library(monkeypatch):
    """Publica la librería PDFium para toda la suite de documentos."""
    library = _find_pdfium()
    if library is None:
        pytest.skip("pdfium.dll no disponible (instala pypdfium2 o define PYOCRUST_PDFIUM_LIB)")
    monkeypatch.setenv("PYOCRUST_PDFIUM_LIB", library)


def _png_size(data: bytes) -> tuple[int, int]:
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "no es un PNG"
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def test_mixed_pdf_returns_text_page_and_flags_the_scanned_one():
    """El criterio de aceptación: una página con texto y otra marcada needs_ocr."""
    pages = pyocrust.parse_document(FIXTURE)

    assert [page.index for page in pages] == [1, 2]

    text_page, scan_page = pages
    assert text_page.has_text_layer is True
    assert text_page.needs_ocr is False
    assert scan_page.has_text_layer is False
    assert scan_page.needs_ocr is True
    assert scan_page.text_regions == []

    assert text_page.text_regions, "la página con text-layer debe traer regiones"
    assert any("fixture sintetico de pyocrust" in region.text for region in text_page.text_regions)
    assert all(region.confidence == 1.0 for region in text_page.text_regions)


def test_document_entry_runs_ocr_only_for_the_scanned_page():
    """Offline acceptance: text layer is exact; the scan enters the OCR path."""
    result = pyocrust.recognize_document(FIXTURE, pages=None, dpi=200, device="cpu")
    assert [page.index for page in result.pages] == [1, 2]
    text_page, scan_page = result.pages
    assert text_page.source == "text_layer"
    assert text_page.output.text == (
        "Este PDF es un fixture sintetico de pyocrust:\n"
        "la pagina 1 lleva una capa de texto real,\n"
        "de sobra para superar text_min_chars."
    )
    assert scan_page.source == "ocr"
    assert isinstance(scan_page.output, pyocrust.OcrResult)


def test_boxes_are_aabb_in_points_with_the_y_axis_flipped():
    """Marco único: origen arriba-izquierda, `y` hacia abajo, dentro de la página."""
    text_page = pyocrust.parse_document(FIXTURE, pages=[1])[0]
    width_pt, height_pt = 612.0, 792.0

    for region in text_page.text_regions:
        box = region.box
        assert 0.0 <= box.x1 < box.x2 <= width_pt
        assert 0.0 <= box.y1 < box.y2 <= height_pt
    # El texto del fixture va arriba de la página (Td 720 desde abajo): con el
    # eje volteado debe caer en la mitad superior.
    assert all(region.box.y1 < height_pt / 2 for region in text_page.text_regions)


def test_metadata_size_uses_dpi_and_regions_do_not():
    """`dpi` sólo mueve width_px/height_px; las cajas no cambian."""
    at_200 = pyocrust.parse_document(FIXTURE, pages=[1])[0]
    at_100 = pyocrust.parse_document(FIXTURE, pages=[1], dpi=100)[0]

    assert (at_200.width_px, at_200.height_px) == (1700, 2200)  # 612·200/72, 792·200/72
    assert (at_100.width_px, at_100.height_px) == (850, 1100)
    assert [(r.box.x1, r.box.y1) for r in at_200.text_regions] == [
        (r.box.x1, r.box.y1) for r in at_100.text_regions
    ]


def test_text_min_chars_can_force_a_page_with_text_into_ocr():
    """Un umbral absurdo convierte la página de texto en `needs_ocr`."""
    forced = pyocrust.parse_document(FIXTURE, pages=[1], text_min_chars=100_000)[0]
    assert forced.has_text_layer is False
    assert forced.needs_ocr is True
    assert forced.text_regions == []


def test_render_page_returns_a_png_of_the_dpi_size():
    png = pyocrust.render_page(FIXTURE, index=2, dpi=200)
    assert isinstance(png, bytes)
    assert _png_size(png) == (1700, 2200)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"pages": [0]},
        {"pages": [3]},
        {"pages": [1, 1]},
        {"pages": ["1"]},
        {"dpi": 0},
        {"text_min_chars": 0},
    ],
)
def test_invalid_input_raises_value_error_before_opening(kwargs):
    with pytest.raises(pyocrust.PyOcrValueError):
        pyocrust.parse_document(FIXTURE, **kwargs)


@pytest.mark.parametrize("index,dpi", [(0, 200), (3, 200), (1, 0)])
def test_render_page_rejects_bad_index_or_dpi(index, dpi):
    with pytest.raises(pyocrust.PyOcrValueError):
        pyocrust.render_page(FIXTURE, index=index, dpi=dpi)


def test_missing_file_is_an_error_not_an_empty_list():
    with pytest.raises(pyocrust.PyOcrValueError, match="no such file"):
        pyocrust.parse_document(FIXTURE.with_name("does_not_exist.pdf"))


def test_document_api_is_exported():
    assert {"PageInfo", "parse_document", "render_page"} <= set(pyocrust.__all__)
