"""pyocrust — wrapper nativo unificado de OCR y análisis de estructura documental.

La implementación vive en Rust (crate ``pyocrust_core``, backend ``oar-ocr``)
y se expone a Python mediante el módulo nativo ``pyocrust._pyocrust_core``,
construido con Maturin. Este paquete es solo la fachada pública de alto nivel.

Fases del proyecto (ver ``PLANNING.md``): la fachada definitiva con
``VeloceOCR``, ``OcrResult`` y ``StructureResult`` llega con las tarjetas
``I2`` (core), ``I3`` (storage) e ``I4`` (engines).
"""

from __future__ import annotations

from typing import Final

try:
    from pyocrust._pyocrust_core import native_version as _native_version
except ImportError as exc:  # pragma: no cover - solo si el binario no está construido
    raise ImportError(
        "El módulo nativo 'pyocrust._pyocrust_core' no está construido. "
        "Ejecuta 'maturin develop' en la raíz del proyecto antes de importar pyocrust."
    ) from exc

__version__: Final[str] = _native_version()

__all__: Final[list[str]] = ["__version__"]
