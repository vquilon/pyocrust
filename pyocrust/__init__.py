"""pyocrust — wrapper nativo unificado de OCR y análisis de estructura documental.

La implementación vive en Rust (crate ``pyocrust_core``, backend ``oar-ocr``)
y se expone a Python mediante el módulo nativo ``pyocrust._pyocrust_core``,
construido con Maturin. Este paquete es solo la fachada pública de alto nivel.

Fases del proyecto (ver ``PLANNING.md``): ``VeloceOCR`` devuelve ``OcrResult``
en los presets de texto (``pp_ocrv6*``) y ``StructureResult`` —con
``to_markdown()``, tablas HTML y fórmulas LaTeX— en ``pp_structurev3``
(ADR-003).
"""

from __future__ import annotations

from typing import Final

try:
    from pyocrust._pyocrust_core import (
        BoundingBox,
        LayoutRegion,
        OcrResult,
        PyOcrError,
        PyOcrRuntimeError,
        PyOcrValueError,
        StructureResult,
        TaskPredictor,
        TextRegion,
        VeloceOCR,
        native_version as _native_version,
        resolve_models_dir,
        models_status,
    )
except ImportError as exc:  # pragma: no cover - solo si el binario no está construido
    raise ImportError(
        "El módulo nativo 'pyocrust._pyocrust_core' no está construido. "
        "Ejecuta 'maturin develop' en la raíz del proyecto antes de importar pyocrust."
    ) from exc

__version__: Final[str] = _native_version()

from pyocrust._pyocrust_core import model_catalog, pipeline_profiles
from pyocrust.gpu import enable_cuda
from pyocrust.hardware import GpuInfo, HardwareProfile, detect_hardware
from pyocrust.resolver import TaskSpec, PipelineChoice, resolve_pipeline
from pyocrust._pyocrust_core import available_providers

__all__: Final[list[str]] = [
    "__version__",
    "BoundingBox",
    "LayoutRegion",
    "OcrResult",
    "PyOcrError",
    "PyOcrRuntimeError",
    "PyOcrValueError",
    "StructureResult",
    "TaskPredictor",
    "TextRegion",
    "VeloceOCR",
    "resolve_models_dir",
    "models_status",
    "model_catalog",
    "pipeline_profiles",
    "available_providers",
    "enable_cuda",
    "GpuInfo",
    "HardwareProfile",
    "detect_hardware",
    "TaskSpec",
    "PipelineChoice",
    "resolve_pipeline",
]
