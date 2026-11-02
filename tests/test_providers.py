"""Selección de `device` y EP efectivo (`DESIGN.md` §3.1.4, ADR-010).

Contrato:
* ``available_providers()`` es la fuente honesta de EPs aceleradores que
  registran de verdad en este host (``[]`` si ninguno), nunca el inventario
  físico de ``detect_hardware()``;
* ``VeloceOCR``/``TaskPredictor`` aceptan ``device`` (default ``"cpu"``) y
  exponen ``provider_effective`` = EP que corrió;
* pedir un EP que no registra (p. ej. ``cuda``) falla con ``PyOcrValueError``;
  **nunca** se devuelve una fila GPU que en realidad es CPU.

Ejecución: `python -m pytest tests/test_providers.py -q`
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pyocrust import (
    PyOcrRuntimeError,
    PyOcrValueError,
    TaskPredictor,
    VeloceOCR,
    available_providers,
)

IMAGEN = Path(__file__).parent / "data" / "sample_text.png"


def test_available_providers_is_a_list_of_names_without_cpu():
    providers = available_providers()
    assert isinstance(providers, list)
    assert all(isinstance(name, str) and name for name in providers)
    assert len(providers) == len(set(providers)), "sin duplicados"
    assert "cpu" not in providers, "cpu nunca es un EP acelerador"
    assert all(name in {"cuda", "directml", "coreml", "openvino", "tensorrt", "webgpu"} for name in providers)


def test_cpu_device_reports_cpu_and_runs(modelos_tiny):
    ocr = VeloceOCR("pp_ocrv6", custom_path=str(modelos_tiny), device="cpu")
    assert ocr.provider_effective == "cpu"

    resultado = ocr.recognize(str(IMAGEN))
    assert len(resultado.regions) >= 1


def test_auto_reports_a_real_provider_or_cpu(modelos_tiny):
    ocr = VeloceOCR("pp_ocrv6", custom_path=str(modelos_tiny), device="auto")
    assert ocr.provider_effective == "cpu" or ocr.provider_effective in available_providers()


def test_explicit_accelerator_is_honest(modelos_tiny):
    for device in available_providers():
        ocr = VeloceOCR("pp_ocrv6", custom_path=str(modelos_tiny), device=device)
        assert ocr.provider_effective == device


def test_cuda_that_does_not_register_never_labels_gpu(modelos_tiny):
    if "cuda" in available_providers():
        pytest.skip("CUDA sí registra en este host; nada que demostrar")
    with pytest.raises(PyOcrValueError):
        VeloceOCR("pp_ocrv6", custom_path=str(modelos_tiny), device="cuda")


def test_unknown_device_is_rejected(modelos_tiny):
    with pytest.raises(PyOcrValueError):
        VeloceOCR("pp_ocrv6", custom_path=str(modelos_tiny), device="tpu")


def test_task_predictor_exposes_provider_effective():
    try:
        predictor = TaskPredictor("document_orientation", device="cpu")
    except PyOcrRuntimeError as exc:  # artefactos ausentes en la caché del host
        pytest.skip(f"artefacto de document_orientation ausente: {exc}")
    assert predictor.provider_effective == "cpu"
    assert predictor.predict(str(IMAGEN))["orientations"]
