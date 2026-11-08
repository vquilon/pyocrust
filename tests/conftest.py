"""Utilidades compartidas de la suite de integración de pyocrust (tarjeta `V1`).

Aquí viven las dos piezas que necesitan más de un fichero de test:

* un generador de PNG sintético con la sola stdlib (`zlib` + `struct`), para que
  el troceado se pueda ejercitar con las dimensiones exactas que pida cada caso
  sin depender de Pillow ni de ficheros binarios;
* la localización de los modelos reales de PP-OCRv6 Tiny en disco, para que los
  escenarios `recognize` end-to-end corran de verdad cuando el host los tiene y
  se marquen `skip` (con motivo) cuando no.

Ejecución: `python -m pytest tests/ -q`
"""

from __future__ import annotations

import os
import shutil
import struct
import zlib
from pathlib import Path

import pytest

# --------------------------------------------------------------------------
# PNG sintético sin dependencias externas
# --------------------------------------------------------------------------


def _chunk(tag: bytes, data: bytes) -> bytes:
    """Un chunk PNG: longitud, tipo, datos y CRC-32."""
    return (
        struct.pack(">I", len(data))
        + tag
        + data
        + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


def png_bytes(width: int, height: int, gray: int = 255) -> bytes:
    """PNG RGB de un solo tono, determinista y con las dimensiones pedidas.

    El troceado solo depende de la geometría de la imagen, así que el contenido
    es irrelevante; un tono plano mantiene el PNG pequeño y la generación
    instantánea.
    """
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    filas = (b"\x00" + bytes([gray]) * (width * 3)) * height
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(filas, 6))
        + _chunk(b"IEND", b"")
    )


@pytest.fixture
def png_factory():
    """Fábrica de PNG sintéticos: `png_factory(ancho, alto) -> bytes`."""
    return png_bytes


# --------------------------------------------------------------------------
# Modelos reales de PP-OCRv6 Tiny (los 3 artefactos del preset)
# --------------------------------------------------------------------------

# Nombres del registro de `oar-ocr` 0.10.1 (`src/core/types.rs::OcrSize`).
PP_OCRV6_TINY = (
    "pp-ocrv6_tiny_det.onnx",
    "pp-ocrv6_tiny_rec.onnx",
    "ppocrv6_tiny_dict.txt",
)

# Los 11 artefactos de PP-StructureV3 (`src/core/types.rs::ModelPaths::new`).
PP_STRUCTUREV3 = (
    "pp-ocrv6_tiny_det.onnx",
    "pp-ocrv6_tiny_rec.onnx",
    "ppocrv6_tiny_dict.txt",
    "pp-doclayoutv3.onnx",
    "pp-lcnet_x1_0_table_cls.onnx",
    "slanext_wired.onnx",
    "slanet_plus.onnx",
    "rt-detr-l_wired_table_cell_det.onnx",
    "table_structure_dict_ch.txt",
    "pp-formulanet-s.onnx",
    "pp-formulanet-tokenizer.json",
)


def directorios_candidatos() -> list[Path]:
    """Dónde busca pyocrust los modelos: `$OAR_HOME` y, si no, `~/.oar`."""
    candidatos = [os.environ.get("OAR_HOME"), str(Path.home() / ".oar")]
    return [Path(c) for c in candidatos if c]


@pytest.fixture(autouse=True)
def entorno_de_modelos_aislado(monkeypatch):
    """Ningún test filtra `OAR_HOME`/`OCR_MODELS_CACHE_DIR` al siguiente.

    `resolve_models_dir` reexporta el directorio resuelto como `OAR_HOME` —lo lee
    `oar-ocr-core` para decidir su caché de auto-descarga—, así que un
    `custom_path` temporal (o un `OAR_HOME` de prueba) deja el entorno del
    proceso sucio y contamina a los módulos que se ejecutan después:
    `test_tasks.py` deriva su `models_dir` de `os.environ["OAR_HOME"]` y
    terminaba viendo solo los modelos de un `tmp_path`. `monkeypatch` restaura
    el valor original al terminar cada test.
    """
    for variable in ("OAR_HOME", "OCR_MODELS_CACHE_DIR"):
        monkeypatch.delenv(variable, raising=False)


def _motivo_faltantes(nombres: tuple[str, ...]) -> str:
    buscados = " o ".join(str(d) for d in directorios_candidatos())
    return (
        f"modelos en disco ausentes ({', '.join(nombres)}); "
        f"se buscaron en {buscados}. Ejecuta el reconocimiento una vez con "
        f"`VeloceOCR('pp_ocrv6')` para que oar-ocr los descargue, o define OAR_HOME."
    )


@pytest.fixture
def fuente_modelos() -> Path:
    """Directorio del host que contiene los 3 artefactos de PP-OCRv6 Tiny."""
    for directorio in directorios_candidatos():
        if all((directorio / nombre).is_file() for nombre in PP_OCRV6_TINY):
            return directorio
    pytest.skip(_motivo_faltantes(PP_OCRV6_TINY))


@pytest.fixture
def modelos_tiny(tmp_path: Path, fuente_modelos: Path) -> Path:
    """Copia local de los 3 artefactos, para no tocar la caché del host."""
    destino = tmp_path / "modelos"
    destino.mkdir()
    for nombre in PP_OCRV6_TINY:
        shutil.copy2(fuente_modelos / nombre, destino / nombre)
    return destino


@pytest.fixture
def modelos_structure(tmp_path: Path, fuente_modelos: Path) -> Path:
    """Copia local de los 11 artefactos de PP-StructureV3.
    
    Incluye los modelos de reconocimiento de fórmulas.
    """
    destino = tmp_path / "modelos"
    destino.mkdir()
    for nombre in PP_STRUCTUREV3:
        shutil.copy2(fuente_modelos / nombre, destino / nombre)
    return destino
