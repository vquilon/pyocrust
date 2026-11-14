"""Puerta GPU de los adaptadores de pipeline documental (`full_page`).

`docling` y `pp_structurev3_api` corren en CPU y en GPU, pero su fila GPU solo se
etiqueta `cuda` si el RUNTIME ve la GPU de verdad: el adaptador sondea su runtime
(torch con CUDA en el venv aislado de docling / el paddle del intérprete del banco
compilado con CUDA) **antes** de construir el motor. Sin esa sonda saldría una fila
CPU disfrazada de CUDA, que es justo lo que el banco prohíbe.

Estos tests fijan ese contrato sin cargar los motores: la sonda y el subproceso se
sustituyen por dobles, así que no importan torch/paddle ni infieren nada.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from PIL import Image

import common.runner as runner

# `cuda` para torch (venv de docling) y `gpu` para paddle (eje del pipeline API).
DEVICE_ARG = {"docling": "cuda", "pp_structurev3_api": "gpu"}


def _factory(monkeypatch, backend: str, device: str, sees_cuda: bool):
    """Factoría real con la sonda de CUDA y el venv de docling doblados."""
    monkeypatch.setattr(runner, "_runtime_sees_cuda", lambda *a, **kw: sees_cuda)
    if backend == "docling":  # el venv existe en este repo, pero el test no depende de él
        monkeypatch.setattr(runner, "DOCLING_VENV_PYTHON", Path(__file__))
    return runner.PROVIDERS[backend](device=device)


def test_ambos_pipelines_estan_declarados_gpu_capables():
    assert {"docling", "pp_structurev3_api"} <= runner.GPU_CAPABLE_BACKENDS
    assert runner.device_outcome("docling", "gpu") == (None, None)
    assert runner.device_outcome("pp_structurev3_api", "gpu") == (None, None)
    # La lista no se ensancha sola: un adaptador CPU-only sigue dando motivo de skip.
    assert runner.device_outcome("unstructured", "gpu")[0] == "n/a"


@pytest.mark.parametrize("backend", sorted(DEVICE_ARG))
def test_gpu_sin_runtime_cuda_es_skipped_con_motivo(monkeypatch, backend):
    """Runtime sin CUDA + `device=gpu` -> `ProviderUnavailable`, nunca `ok` con cuda."""
    with pytest.raises(runner.ProviderUnavailable):
        _factory(monkeypatch, backend, "gpu", sees_cuda=False)


@pytest.mark.parametrize("backend", sorted(DEVICE_ARG))
def test_cpu_no_sondea_la_gpu(monkeypatch, backend):
    """En CPU no se gasta sonda y la fila declara `cpu` (no `n/a`)."""

    def boom(*a, **kw):  # pragma: no cover - no debe llamarse
        raise AssertionError("no se sondea CUDA con device=cpu")

    monkeypatch.setattr(runner, "_runtime_sees_cuda", boom)
    if backend == "docling":
        monkeypatch.setattr(runner, "DOCLING_VENV_PYTHON", Path(__file__))
    assert runner.PROVIDERS[backend](device="cpu").provider_effective == "cpu"


@pytest.mark.parametrize("backend", sorted(DEVICE_ARG))
def test_gpu_pasa_el_device_al_hijo(monkeypatch, backend):
    """Con CUDA disponible el hijo recibe el device en su eje (`cuda`/`gpu`)."""
    calls = {}

    def fake_run(cmd, **kw):
        calls["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, stdout="# ok", stderr="")

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    run = _factory(monkeypatch, backend, "gpu", sees_cuda=True)

    assert run.provider_effective == "cuda"
    assert run(Image.new("RGB", (4, 4))).text == "# ok"
    assert calls["cmd"][-1] == DEVICE_ARG[backend]
