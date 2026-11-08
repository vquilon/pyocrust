"""Gestión de modelos: registro único, auto-descarga paralela y caché verificada (`S2.0`).

Los tres escenarios que exige la tarjeta se ejecutan de verdad:

* **caché fría con red** — un `OAR_HOME` temporal vacío descarga los 3 artefactos
  de `pp_ocrv6` (~6,5 MB) en paralelo y `VeloceOCR("pp_ocrv6")` funciona;
* **arranque en caliente con `PYOCRUST_OFFLINE=1`** — funciona **sin red**;
* **tamaño corrupto** — un artefacto truncado se vuelve a descargar.

Además: `pyocrust.models_status()` lista el directorio resuelto y los artefactos
de cada preset, y el modo offline con la caché vacía da un error tipado que indica
lista de artefactos y el comando exacto que los trae.

Los tests de descarga necesitan ModelScope alcanzable; si no lo está, se marcan
`skip` con el motivo en vez de dar un falso verde.

Ejecución: `python -m pytest tests/test_models.py -q`
"""

from __future__ import annotations

import shutil
import urllib.request
from pathlib import Path

import pytest

import pyocrust
from pyocrust import OcrResult, PyOcrRuntimeError, VeloceOCR

from conftest import PP_OCRV6_TINY, fuente_modelos

IMAGEN = Path(__file__).parent / "data" / "sample_text.png"

# El artefacto más pequeño del preset: sondea la red sin descargar 6,5 MB.
URL_SONDA = (
    "https://www.modelscope.cn/api/v1/models/greatv/oar-ocr/repo"
    "?Revision=master&FilePath=ppocrv6_tiny_dict.txt"
)

# Tamaños reales del registro de `oar-ocr` 0.10.1 (`src/storage/registry.rs`).
TAMANOS_TINY = {
    "pp-ocrv6_tiny_det.onnx": 1_780_590,
    "pp-ocrv6_tiny_rec.onnx": 4_462_639,
    "ppocrv6_tiny_dict.txt": 27_156,
}

PRESETS_ESPERADOS = ("pp_ocrv6_tiny", "pp_ocrv6_small", "pp_ocrv6_medium", "pp_structurev3")


@pytest.fixture(autouse=True)
def entorno_aislado(monkeypatch):
    """Sin `OAR_HOME`/`OCR_MODELS_CACHE_DIR`/`PYOCRUST_OFFLINE`: cada escenario fija el suyo."""
    for variable in ("OAR_HOME", "OCR_MODELS_CACHE_DIR", "PYOCRUST_OFFLINE"):
        monkeypatch.delenv(variable, raising=False)


def _modelscope_alcanzable() -> None:
    """Sondea ModelScope; si no responde, los tests de descarga se marcan `skip`."""
    peticion = urllib.request.Request(URL_SONDA, headers={"Range": "bytes=0-0"})
    try:
        with urllib.request.urlopen(peticion, timeout=20):
            return
    except Exception as error:  # pragma: no cover - depende de la red del host
        pytest.skip(
            f"ModelScope no alcanzable ({error}); no se puede probar la descarga real"
        )


# ---------------------------------------------------------------------------
# 1. Caché fría con red: descarga en paralelo y pipeline que funciona
# ---------------------------------------------------------------------------


def test_cache_fria_descarga_en_paralelo_y_el_preset_funciona(tmp_path, monkeypatch):
    """`OAR_HOME` vacío → los 3 artefactos (~6,5 MB) llegan y el preset funciona."""
    _modelscope_alcanzable()
    cache = tmp_path / "oar_home"
    monkeypatch.setenv("OAR_HOME", str(cache))
    monkeypatch.delenv("PYOCRUST_OFFLINE", raising=False)

    ocr = VeloceOCR("pp_ocrv6")

    assert Path(ocr.models_dir) == cache, "la descarga debe caer en el directorio resuelto"
    for nombre, tamano in TAMANOS_TINY.items():
        fichero = cache / nombre
        assert fichero.is_file(), f"{nombre} no se descargó"
        assert fichero.stat().st_size == tamano, f"{nombre} tiene un tamaño inesperado"
        # El sidecar permite el arranque en caliente sin re-hashear.
        sidecar = cache / f".{nombre}.sha256"
        assert sidecar.is_file(), f"{nombre} no dejó su sidecar .sha256"

    # El pipeline construido desde los artefactos recién descargados reconoce de verdad.
    assert IMAGEN.is_file(), "falta el fixture de imagen de tests/data/"
    resultado = ocr.recognize(str(IMAGEN))
    assert isinstance(resultado, OcrResult)
    assert resultado.text.strip(), "el modelo descargado no reconoce el texto del fixture"


# ---------------------------------------------------------------------------
# 2. Arranque en caliente con `PYOCRUST_OFFLINE=1`: sin red
# ---------------------------------------------------------------------------


def test_arranque_en_caliente_offline_funciona_sin_red(fuente_modelos, tmp_path, monkeypatch):
    """Caché poblada + `PYOCRUST_OFFLINE=1`: funciona sin tocar la red."""
    cache = tmp_path / "oar_home"
    cache.mkdir()
    for nombre in PP_OCRV6_TINY:
        shutil.copy2(fuente_modelos / nombre, cache / nombre)

    monkeypatch.setenv("OAR_HOME", str(cache))
    monkeypatch.setenv("PYOCRUST_OFFLINE", "1")
    # Proxy apagado: si algo intentara la red, fallaría.
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:9")
    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:9")

    ocr = VeloceOCR("pp_ocrv6")

    assert Path(ocr.models_dir) == cache
    for nombre in PP_OCRV6_TINY:
        assert (cache / nombre).stat().st_size == TAMANOS_TINY[nombre]

    assert isinstance(ocr.recognize(str(IMAGEN)), OcrResult)


def test_offline_con_cache_vacia_da_error_tipado_sin_red(tmp_path, monkeypatch):
    """`PYOCRUST_OFFLINE=1` y falta todo: error con la lista y el comando, sin red."""
    cache = tmp_path / "oar_home"
    monkeypatch.setenv("OAR_HOME", str(cache))
    monkeypatch.setenv("PYOCRUST_OFFLINE", "1")
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:9")

    with pytest.raises(PyOcrRuntimeError) as excinfo:
        VeloceOCR("pp_ocrv6")

    mensaje = str(excinfo.value)
    assert "PYOCRUST_OFFLINE" in mensaje, "el error debe nombrar el modo offline"
    for nombre in PP_OCRV6_TINY:
        assert nombre in mensaje, f"el error no lista {nombre}"
    assert "VeloceOCR" in mensaje, "el error debe indicar el comando que los trae"
    # No se descargó nada: el directorio sigue vacío (o no llegó a crearse).
    assert not cache.exists() or not any(cache.iterdir()), "offline tocó el disco"


# ---------------------------------------------------------------------------
# 3. Tamaño corrupto: se vuelve a descargar
# ---------------------------------------------------------------------------


def test_un_artefacto_con_tamano_incorrecto_se_redescarga(fuente_modelos, tmp_path, monkeypatch):
    """Un fichero truncado se detecta por tamaño y se vuelve a descargar."""
    _modelscope_alcanzable()
    cache = tmp_path / "oar_home"
    cache.mkdir()
    for nombre in PP_OCRV6_TINY:
        shutil.copy2(fuente_modelos / nombre, cache / nombre)
    # Corromper el detector: mismo nombre, 1 byte.
    (cache / "pp-ocrv6_tiny_det.onnx").write_bytes(b"x")
    monkeypatch.setenv("OAR_HOME", str(cache))
    monkeypatch.delenv("PYOCRUST_OFFLINE", raising=False)

    ocr = VeloceOCR("pp_ocrv6")

    # El detector corrupto se reemplazó por el artefacto real y verificado.
    assert (cache / "pp-ocrv6_tiny_det.onnx").stat().st_size == TAMANOS_TINY["pp-ocrv6_tiny_det.onnx"]
    assert isinstance(ocr.recognize(str(IMAGEN)), OcrResult)


# ---------------------------------------------------------------------------
# 4. Introspección: `models_status()`
# ---------------------------------------------------------------------------


def test_models_status_lista_el_directorio_y_los_artefactos_de_cada_preset(
    fuente_modelos, tmp_path, monkeypatch
):
    """`models_status()` devuelve el directorio resuelto y los artefactos por preset."""
    cache = tmp_path / "oar_home"
    cache.mkdir()
    for nombre in PP_OCRV6_TINY:
        shutil.copy2(fuente_modelos / nombre, cache / nombre)
    monkeypatch.setenv("OAR_HOME", str(cache))
    monkeypatch.delenv("PYOCRUST_OFFLINE", raising=False)

    estado = pyocrust.models_status()

    assert estado["models_dir"] == str(cache)
    assert estado["offline"] is False

    presets = estado["presets"]
    for nombre in PRESETS_ESPERADOS:
        assert nombre in presets, f"falta el preset {nombre}"
        artefactos = presets[nombre]
        assert isinstance(artefactos, list) and artefactos, f"{nombre} no lista artefactos"
        for artefacto in artefactos:
            assert {"name", "present", "size", "required"} <= set(artefacto)

    tiny = presets["pp_ocrv6_tiny"]
    assert [a["name"] for a in tiny] == list(PP_OCRV6_TINY)
    assert all(a["present"] for a in tiny)
    assert all(a["size"] == TAMANOS_TINY[a["name"]] for a in tiny)
    assert all(a["required"] for a in tiny)

    # `pp_structurev3` comparte los 3 de Tiny y añade 8: faltan.
    assert not all(a["present"] for a in presets["pp_structurev3"])

    # `indra` está en el registro pero aún no lo exige ningún preset (`S2.2`).
    indra = estado["indra"]
    assert isinstance(indra, list) and indra
    assert all(a["required"] is False for a in indra)


def test_models_status_refleja_el_modo_offline(tmp_path, monkeypatch):
    """`offline` es `True` sólo cuando `PYOCRUST_OFFLINE` lo pide."""
    monkeypatch.setenv("OAR_HOME", str(tmp_path / "vacia"))
    monkeypatch.setenv("PYOCRUST_OFFLINE", "1")
    assert pyocrust.models_status()["offline"] is True

    monkeypatch.setenv("PYOCRUST_OFFLINE", "0")
    assert pyocrust.models_status()["offline"] is False


# ---------------------------------------------------------------------------
# 5. Integridad ModelScope: tamaño correcto + contenido alterado → ausente
# ---------------------------------------------------------------------------


def test_models_status_rechaza_un_artefacto_modelscope_alterado_a_tamano_correcto(
    tmp_path, monkeypatch
):
    """Un ModelScope con el tamaño correcto pero contenido distinto no está presente.

    Escribe los 3 artefactos de Tiny rellenando con bytes nulos hasta su tamaño
    real (sin red): el tamaño cuadra, el SHA-256 no. Los 3 deben reportarse
    `present=False` en `models_status()`.
    """
    cache = tmp_path / "oar_home"
    cache.mkdir()
    for nombre, tamano in TAMANOS_TINY.items():
        (cache / nombre).write_bytes(b"\x5a" * tamano)
    monkeypatch.setenv("OAR_HOME", str(cache))
    monkeypatch.delenv("PYOCRUST_OFFLINE", raising=False)

    tiny = pyocrust.models_status()["presets"]["pp_ocrv6_tiny"]

    for artefacto in tiny:
        assert artefacto["size"] == TAMANOS_TINY[artefacto["name"]], "el tamaño cuadra"
        assert artefacto["present"] is False, (
            f"{artefacto['name']}: tamaño correcto no sustituye la validación SHA-256"
        )

