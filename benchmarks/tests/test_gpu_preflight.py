"""Preflight compartido: `--device gpu` sin EP acelerador aborta de entrada.

Medido 2026-11-14: un `.pyd` recompilado sin `--features cuda` produjo una run GPU
con las `pyocrust*` en `skipped` (cero filas `cuda`) después de horas de banco. El
guard vive en `run_backends` —el sitio por el que pasan los 9 bancos sueltos
(`features/<f>/bank.py --device gpu`), que **no** pasan por `campana_gpu.py`— y se
dispara antes de crear el directorio de resultados o construir ningún motor.
"""

from __future__ import annotations

import pytest

import common.runner as runner


def test_gpu_sin_ep_acelerador_aborta_con_el_comando_de_rebuild(monkeypatch):
    monkeypatch.setattr(runner, "available_providers", lambda: [])
    with pytest.raises(SystemExit) as exc:
        runner.require_accelerator("gpu")
    msg = str(exc.value)
    assert "available_providers()=[]" in msg
    assert "--features cuda" in msg and "maturin develop" in msg


def test_gpu_con_ep_acelerador_sigue(monkeypatch):
    monkeypatch.setattr(runner, "available_providers", lambda: ["cuda"])
    assert runner.require_accelerator("gpu") == ["cuda"]


def test_cpu_no_sondea_el_binario(monkeypatch):
    def boom():  # pragma: no cover - se llama sólo si el guard toca el binario
        raise AssertionError("--device cpu no debe sondear los EPs")

    monkeypatch.setattr(runner, "available_providers", boom)
    assert runner.require_accelerator("cpu") == []


def test_run_backends_es_el_sitio_compartido(monkeypatch, tmp_path):
    """Los 9 bancos heredan el preflight sin tocar su `bank.py`."""
    monkeypatch.setattr(runner, "available_providers", lambda: [])
    out = tmp_path / "results" / "feature"
    with pytest.raises(SystemExit):
        runner.run_backends([], ["pyocrust"], "local", out, "2026-11-14_00-00-00", device="gpu")
    assert not out.exists()  # aborta antes de publicar la run