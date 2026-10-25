"""Niveles de resolución de rutas de modelos (`DESIGN.md` §3.2 y §7.1).

Orden estricto que debe cumplir `src/storage/config.rs`:

1. parámetro explícito `custom_path`
2. `OAR_HOME`
3. `OCR_MODELS_CACHE_DIR`
4. `~/.oar`

La resolución es pura: devuelve rutas absolutas normalizadas, no exige que el
directorio exista y no abre ninguna conexión de red.

Ejecución: `python -m pytest tests/test_config.py -q`
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from pyocrust import (
    PyOcrError,
    PyOcrRuntimeError,
    PyOcrValueError,
    VeloceOCR,
    resolve_models_dir,
)

VARIABLES_DE_ENTORNO = ("OAR_HOME", "OCR_MODELS_CACHE_DIR")


@pytest.fixture(autouse=True)
def entorno_aislado(monkeypatch):
    """Cada test parte sin `OAR_HOME` ni `OCR_MODELS_CACHE_DIR` del host."""
    for variable in VARIABLES_DE_ENTORNO:
        monkeypatch.delenv(variable, raising=False)


def test_nivel_1_custom_path_gana_a_las_variables_de_entorno(tmp_path, monkeypatch):
    monkeypatch.setenv("OAR_HOME", str(tmp_path / "oar_home"))
    monkeypatch.setenv("OCR_MODELS_CACHE_DIR", str(tmp_path / "cache_compartida"))
    propio = tmp_path / "modelos_propios"

    assert Path(resolve_models_dir(str(propio))) == propio


def test_nivel_2_oar_home_gana_a_ocr_models_cache_dir(tmp_path, monkeypatch):
    oar_home = tmp_path / "oar_home"
    monkeypatch.setenv("OAR_HOME", str(oar_home))
    monkeypatch.setenv("OCR_MODELS_CACHE_DIR", str(tmp_path / "cache_compartida"))

    assert Path(resolve_models_dir()) == oar_home


def test_nivel_2_ocr_models_cache_dir_se_usa_si_no_hay_oar_home(tmp_path, monkeypatch):
    cache = tmp_path / "cache_compartida"
    monkeypatch.setenv("OCR_MODELS_CACHE_DIR", str(cache))

    assert Path(resolve_models_dir()) == cache


def test_nivel_3_cae_en_el_directorio_oar_del_home(tmp_path, monkeypatch):
    monkeypatch.setenv("USERPROFILE", str(tmp_path))

    resuelto = Path(resolve_models_dir())

    assert resuelto == tmp_path / ".oar"
    assert resuelto.is_absolute()


def test_nivel_3_ignora_las_variables_vacias(tmp_path, monkeypatch):
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("OAR_HOME", "")
    monkeypatch.setenv("OCR_MODELS_CACHE_DIR", "")

    assert Path(resolve_models_dir()) == tmp_path / ".oar"


def test_una_ruta_relativa_se_resuelve_contra_el_directorio_de_trabajo(monkeypatch):
    resuelto = Path(resolve_models_dir("relativo/sub/dir"))

    assert resuelto.is_absolute()
    assert resuelto == Path.cwd() / "relativo" / "sub" / "dir"


def test_la_tilde_se_expande_al_home_del_usuario(tmp_path, monkeypatch):
    monkeypatch.setenv("USERPROFILE", str(tmp_path))

    assert Path(resolve_models_dir("~/mis_modelos")) == tmp_path / "mis_modelos"
    assert Path(resolve_models_dir("~")) == tmp_path


def test_una_ruta_inexistente_se_normaliza_sin_fallar(tmp_path):
    inexistente = tmp_path / "no" / "existe" / "foo" / ".." / "bar"

    resuelto = Path(resolve_models_dir(str(inexistente)))

    assert resuelto.is_absolute()
    assert resuelto == tmp_path / "no" / "existe" / "bar"


def test_veloceocr_usa_el_nivel_1_y_falla_con_error_tipado_si_no_hay_modelos(tmp_path):
    """El nivel 1 llega hasta el motor: sin artefactos, error tipado, no pánico.

    `custom_path` apunta a un directorio que no es la caché de `oar-ocr`, así que
    la autodescarga no puede intervenir y el fallo es determinista.
    """
    with pytest.raises(PyOcrRuntimeError) as fallo:
        VeloceOCR("pp_ocrv6", custom_path=str(tmp_path))

    assert "pp-ocrv6_tiny_det.onnx" in str(fallo.value)


def test_un_preset_desconocido_se_rechaza_como_value_error():
    with pytest.raises(PyOcrValueError) as fallo:
        VeloceOCR("preset_que_no_existe")

    assert "unknown preset" in str(fallo.value)


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Fallo de código: `src/core/error.rs` crea PyOcrValueError/PyOcrRuntimeError con una "
        "sola base (`create_exception!(..., PyValueError)`), así que no heredan de PyOcrError "
        "pese a que el comentario del propio fichero y los stubs "
        "(`pyocrust/__init__.pyi`: `class PyOcrValueError(ValueError, PyOcrError)`) lo declaran. "
        "`except pyocrust.PyOcrError` no captura ningún error del crate."
    ),
)
def test_las_excepciones_del_crate_heredan_de_pyocrerror(tmp_path):
    assert issubclass(PyOcrValueError, PyOcrError)
    assert issubclass(PyOcrRuntimeError, PyOcrError)

    with pytest.raises(PyOcrError):
        VeloceOCR("pp_ocrv6", custom_path=str(tmp_path))


def test_la_resolucion_no_depende_del_estado_de_disco(tmp_path, monkeypatch):
    """`resolve_models_dir` no crea ni exige directorios (§7.1: sin I/O ni red)."""
    fantasma = tmp_path / "todavia_no_existe"

    assert Path(resolve_models_dir(str(fantasma))) == fantasma
    assert not fantasma.exists()
    assert os.environ.get("OAR_HOME") is None
