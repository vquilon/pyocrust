"""Contrato de los adaptadores VLM documentales SOTA (`full_page`).

`lightonocr`, `glm_ocr` y `paddleocr_vl` corren por la ruta **`transformers`** en
el venv aislado de docling, por **subproceso con timeout**, un modelo a la vez.
Emiten SOLO Markdown -> sus columnas de estructura salen `N/A` (nunca `0.0`), y la
fila GPU solo se etiqueta `cuda` si ese venv ve la GPU. Estos tests fijan el
contrato sin cargar ningún modelo: la caché HF, la sonda y el subproceso son
dobles.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from PIL import Image

import common.runner as runner

VLM_BACKENDS = ("lightonocr", "glm_ocr", "paddleocr_vl", "lightonocr3_08b", "lightonocr3_4b")


def test_registro_completo_y_canales_de_estructura_vacios():
    for backend in VLM_BACKENDS:
        assert backend in runner.PROVIDERS, backend
        assert runner.TASK_TYPES[backend] == runner.FEATURE_TYPES[backend] == "full_page", backend
        model_name, variant = runner.MODEL_NAMES[backend]
        assert model_name and variant, backend
        assert backend in runner.LICENSES, backend
        # Solo-Markdown: 0 canales -> las columnas de estructura salen N/A, no 0.0.
        assert runner.STRUCTURE_CHANNELS[backend] == frozenset(), backend
        assert runner.emitted_channels(backend) == frozenset(), backend
        assert {"layout_map", "table_teds", "latex_sim", "read_order_tau"} <= \
            runner.not_evaluable_metrics(backend), backend
        assert backend in runner.GPU_CAPABLE_BACKENDS, backend
        assert runner.device_outcome(backend, "gpu") == (None, None), backend


def test_licencias_verificadas_en_la_ficha():
    assert runner.LICENSES["lightonocr"] == "Apache-2.0"
    assert runner.LICENSES["glm_ocr"] == "MIT"
    assert runner.LICENSES["paddleocr_vl"] == "Apache-2.0"


def test_missing_weights_is_skipped_with_download_command(monkeypatch):
    monkeypatch.setattr(runner, "_hf_repo_cached", lambda *a, **kw: False)
    for backend in VLM_BACKENDS:
        with pytest.raises(runner.ProviderUnavailable) as exc:
            runner.PROVIDERS[backend](device="cpu")
        assert "snapshot_download" in str(exc.value), backend


def test_gpu_without_cuda_runtime_is_skipped(monkeypatch):
    monkeypatch.setattr(runner, "_hf_repo_cached", lambda *a, **kw: True)
    monkeypatch.setattr(runner, "_runtime_sees_cuda", lambda *a, **kw: False)
    monkeypatch.setattr(runner, "DOCLING_VENV_PYTHON", Path(__file__))  # "existe"
    for backend in VLM_BACKENDS:
        with pytest.raises(runner.ProviderUnavailable):
            runner.PROVIDERS[backend](device="gpu")


def test_cpu_declara_cpu_y_pasa_device_y_prompt_al_hijo(monkeypatch):
    """En CPU no se sondea la GPU y el device viaja como último argv del hijo."""
    monkeypatch.setattr(runner, "_hf_repo_cached", lambda *a, **kw: True)
    monkeypatch.setattr(runner, "DOCLING_VENV_PYTHON", Path(__file__))

    def boom(*a, **kw):  # pragma: no cover - no debe llamarse en CPU
        raise AssertionError("no se sondea CUDA con device=cpu")

    monkeypatch.setattr(runner, "_runtime_sees_cuda", boom)
    calls = {}

    def fake_run(cmd, **kw):
        calls["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, stdout="# ok", stderr="")

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    for backend in VLM_BACKENDS:
        run = runner.PROVIDERS[backend](device="cpu")
        assert run.provider_effective == "cpu", backend
        assert run.emits == frozenset(), backend
        assert run(Image.new("RGB", (4, 4))).text == "# ok", backend
        assert calls["cmd"][-1] == "cpu", backend
        assert calls["cmd"][-4] == (runner.HF_VLM_MODELS[backend][1] or ""), backend
