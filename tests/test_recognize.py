"""`recognize` end-to-end (`DESIGN.md` §3.1 y §3.2).

Escenarios que cubre `DESIGN.md`:

* **carga directa** — `VeloceOCR(preset, custom_path=...)` (nivel 1);
* **variable de entorno** — `OAR_HOME` (nivel 2);
* **caché por defecto** — `~/.oar` (nivel 3).

Los tres construyen el pipeline de PP-OCRv6 Tiny y reconocen una imagen real de
texto. Necesitan los 3 artefactos del preset en disco: si el host no los tiene,
los tests se marcan `skip` con el motivo (la suite no descarga nada por su
cuenta).

El escenario de PP-StructureV3 (ADR-003: `StructureResult` con `to_markdown()`)
se ejecuta cuando el host tiene sus 9 artefactos y se marca `skip` con el motivo
cuando no. El detalle de tablas HTML y LaTeX dentro del Markdown lo cubre el
test unitario de `src/engines/oar_structure.rs`, que no descarga modelos.

Ejecución: `python -m pytest tests/test_recognize.py -q`
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from pyocrust import (
    OcrResult,
    PyOcrRuntimeError,
    PyOcrValueError,
    StructureResult,
    VeloceOCR,
)

from conftest import (
    PP_OCRV6_TINY,
    PP_STRUCTUREV3,
    directorios_candidatos,
    fuente_modelos,
)

IMAGEN = Path(__file__).parent / "data" / "sample_text.png"

# Las dos líneas del fixture, reconocidas por PP-OCRv6 Tiny con confianza > 0.97.
LINEAS_ESPERADAS = ("Hola mundo 12345", "Factura 2026-10-25")


@pytest.fixture(autouse=True)
def entorno_aislado(monkeypatch):
    """Sin `OAR_HOME`/`OCR_MODELS_CACHE_DIR`: cada escenario fija el suyo."""
    for variable in ("OAR_HOME", "OCR_MODELS_CACHE_DIR"):
        monkeypatch.delenv(variable, raising=False)


def _afirmar_reconocimiento(ocr: VeloceOCR) -> None:
    """Contrato de salida de `recognize`: texto, confianza y cajas válidas."""
    assert IMAGEN.is_file(), "falta el fixture de imagen de tests/data/"

    resultado = ocr.recognize(str(IMAGEN))

    # Un preset de texto devuelve `OcrResult`, nunca `StructureResult`.
    assert isinstance(resultado, OcrResult)
    assert len(resultado.regions) >= len(LINEAS_ESPERADAS)
    for linea in LINEAS_ESPERADAS:
        assert linea in resultado.text
    assert 0.0 < resultado.confidence <= 1.0
    for region in resultado.regions:
        assert region.text
        assert 0.0 < region.confidence <= 1.0
        assert region.box.width > 0
        assert region.box.height > 0


def test_reconocer_con_carga_directa(modelos_tiny):
    """Escenario 1: el nivel 1 (custom_path) es el que se usa."""
    ocr = VeloceOCR("pp_ocrv6", custom_path=str(modelos_tiny))

    assert Path(ocr.models_dir) == modelos_tiny
    _afirmar_reconocimiento(ocr)


def test_reconocer_con_variable_de_entorno(modelos_tiny, monkeypatch):
    """Escenario 2: sin `custom_path`, `OAR_HOME` resuelve el directorio."""
    monkeypatch.setenv("OAR_HOME", str(modelos_tiny))

    ocr = VeloceOCR("pp_ocrv6")

    assert Path(ocr.models_dir) == modelos_tiny
    _afirmar_reconocimiento(ocr)


def test_reconocer_con_la_cache_por_defecto(tmp_path, monkeypatch, fuente_modelos):
    """Escenario 3: sin `custom_path` ni entorno, la caché es `<home>/.oar`."""
    cache = tmp_path / ".oar"
    cache.mkdir()
    for nombre in PP_OCRV6_TINY:
        shutil.copy2(fuente_modelos / nombre, cache / nombre)
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))

    ocr = VeloceOCR("pp_ocrv6")

    assert Path(ocr.models_dir) == cache
    _afirmar_reconocimiento(ocr)


def test_recognize_acepta_ruta_bytes_y_pathlike(modelos_tiny):
    ocr = VeloceOCR("pp_ocrv6", custom_path=str(modelos_tiny))
    datos = IMAGEN.read_bytes()

    desde_ruta = ocr.recognize(str(IMAGEN))
    desde_bytes = ocr.recognize(datos)
    desde_pathlike = ocr.recognize(IMAGEN)

    assert desde_ruta.text.count("\n") >= 1
    assert desde_bytes.text == desde_ruta.text
    assert desde_pathlike.text == desde_ruta.text


def test_recognize_rechaza_una_ruta_que_no_existe(modelos_tiny, tmp_path):
    ocr = VeloceOCR("pp_ocrv6", custom_path=str(modelos_tiny))

    with pytest.raises(PyOcrRuntimeError):
        ocr.recognize(str(tmp_path / "no_existe.png"))


def test_recognize_rechaza_bytes_que_no_son_una_imagen(modelos_tiny):
    ocr = VeloceOCR("pp_ocrv6", custom_path=str(modelos_tiny))

    with pytest.raises(PyOcrRuntimeError):
        ocr.recognize(b"esto no es una imagen")


def test_recognize_rechaza_un_tipo_no_soportado(modelos_tiny):
    ocr = VeloceOCR("pp_ocrv6", custom_path=str(modelos_tiny))

    with pytest.raises(PyOcrValueError):
        ocr.recognize(12345)


def test_llamar_dos_veces_no_recarga_el_pipeline(modelos_tiny):
    """El modelo queda residente tras el constructor (ADR-002)."""
    ocr = VeloceOCR("pp_ocrv6", custom_path=str(modelos_tiny))

    primero = ocr.recognize(str(IMAGEN))
    segundo = ocr.recognize(str(IMAGEN))

    assert primero.text == segundo.text


def _directorio_structurev3() -> Path:
    """Directorio con los 9 artefactos de PP-StructureV3, o `skip` con el motivo."""
    for directorio in directorios_candidatos():
        if all((directorio / nombre).is_file() for nombre in PP_STRUCTUREV3):
            return directorio

    faltan = [
        nombre
        for nombre in PP_STRUCTUREV3
        if not any((directorio / nombre).is_file() for directorio in directorios_candidatos())
    ]
    pytest.skip(
        f"faltan {len(faltan)} de {len(PP_STRUCTUREV3)} artefactos de PP-StructureV3 "
        f"(~600 MB, p. ej. pp-doclayoutv3 y slanext_wired): {faltan}"
    )


def test_pp_structurev3_devuelve_structure_result_con_markdown():
    """ADR-003: la estructura no se aplana; `to_markdown()` cruza a Python.

    Es la condición `S1.2` del sign-off: con el preset `pp_structurev3` la salida
    es `StructureResult` (Markdown + elementos de layout), no un `OcrResult`
    plano. El LaTeX de una fórmula y el HTML de una tabla dentro de ese Markdown
    los cubre el test unitario de `src/engines/oar_structure.rs`, porque el
    fixture de imagen de esta suite no contiene ni tablas ni fórmulas.
    """
    ocr = VeloceOCR("pp_structurev3", custom_path=str(_directorio_structurev3()))

    resultado = ocr.recognize(str(IMAGEN))

    assert isinstance(resultado, StructureResult)
    assert not isinstance(resultado, OcrResult)

    markdown = resultado.to_markdown()
    assert isinstance(markdown, str)
    assert markdown.strip(), "el Markdown del documento no puede venir vacío"
    assert LINEAS_ESPERADAS[0] in markdown

    assert resultado.elements, "debe exponer los elementos de layout detectados"
    for elemento in resultado.elements:
        assert elemento.kind, "cada elemento lleva su etiqueta de layout"
        assert 0.0 <= elemento.confidence <= 1.0
        assert elemento.box.width >= 0 and elemento.box.height >= 0

    # Segunda llamada: el pipeline sigue residente y devuelve el mismo tipo.
    assert isinstance(ocr.recognize(IMAGEN), StructureResult)
