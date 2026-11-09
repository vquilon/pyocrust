"""Contrato del adaptador `pp_structurev3_api`: corre en SUBPROCESO con timeout.

`pp_structurev3_api` (PaddleOCR PP-StructureV3) **segfaultaba (exit 139) o colgaba**
en proceso sobre páginas reales y **abortaba el banco `full_page`** (hallazgo
t_53080e14, seguimiento t_4298724b). Se envolvió en un subproceso con timeout
(patrón de `docling`/`unimernet`): un segfault o un cuelgue mata solo al hijo y la
fila sale `error`/`skipped` con motivo — nunca se lleva por delante el banco.

Estos tests fijan ESE contrato con hijos triviales (sin cargar paddle ni inferir):
son la verificación barata del cambio, no un banco.
"""

from __future__ import annotations

import subprocess
import sys

import pytest
from PIL import Image

import common.runner as runner

BACKEND = "pp_structurev3_api"


def _factory_with_child(monkeypatch, child_src: str):
    """Factoría real con el script del hijo sustituido por uno trivial (sin paddle)."""
    monkeypatch.setattr(runner, "_PP_STRUCTUREV3_RUNNER", child_src)
    return runner.PROVIDERS[BACKEND](device="cpu")


def test_script_del_hijo_compila():
    compile(runner._PP_STRUCTUREV3_RUNNER, "<pp_structurev3_runner>", "exec")


def test_usa_subproceso_con_timeout_y_el_interprete_del_banco(monkeypatch):
    """Deadline explícito (no cuelgue infinito) y `sys.executable` (el venv del banco)."""
    calls = {}

    def fake_run(cmd, **kw):
        calls["cmd"], calls["kw"] = cmd, kw
        return subprocess.CompletedProcess(cmd, 0, stdout="# ok", stderr="")

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    out = runner.PROVIDERS[BACKEND](device="cpu")(Image.new("RGB", (4, 4)))

    assert out.text == "# ok"
    assert calls["kw"]["timeout"] == 900
    assert calls["cmd"][:3] == [sys.executable, "-c", runner._PP_STRUCTUREV3_RUNNER]


def test_hijo_que_imprime_devuelve_el_markdown(monkeypatch):
    run = _factory_with_child(monkeypatch, "import sys; sys.stdout.write('# hola')")
    assert run(Image.new("RGB", (4, 4))).text == "# hola"


def test_segfault_del_hijo_es_error_con_motivo(monkeypatch):
    """exit 139 del hijo -> `RuntimeError` con el exit en el motivo.

    El runner captura ese error como fila `error` de ESA imagen y sigue; el banco
    no se aborta (que era el defecto medido en proceso).
    """
    run = _factory_with_child(monkeypatch, "raise SystemExit(139)")
    with pytest.raises(RuntimeError, match="exit 139"):
        run(Image.new("RGB", (4, 4)))


def test_emits_y_provider_del_adaptador():
    run = runner.PROVIDERS[BACKEND](device="cpu")
    assert run.provider_effective == "cpu"
    assert run.emits == frozenset({"tables"})
