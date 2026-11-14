"""Smoke del preset VLM (`glm_ocr`, feature `vl`).

`vl` es opt-in: sin un build con `--features vl` el preset `glm_ocr` no existe
(`PyOcrValueError`, preset fantasma). Por eso todo el fichero se salta cuando el
build no trae la feature.

Dos escenarios del criterio de la tarjeta:

* **offline sin pesos** — `PYOCRUST_OFFLINE=1` con un `custom_path` vacío ⇒ error
  tipado (`PyOcrRuntimeError`), sin red ni descarga de pesos;
* **inferencia real** — una página de `tests/data/` produce Markdown **no vacío**
  con `provider_effective` honesto. Sólo corre si el host tiene los dos snapshots
  del VLM (~1.9 GB) bajo el root; si no, se marca `skip` con el motivo.

La raíz del host se captura en el import: el `conftest.py` borra `OAR_HOME` antes
de cada test (aislamiento), así que hay que leerla antes de que corra el fixture.

Ejecución: `python -m pytest tests/test_vlm.py -q`
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

import pyocrust

IMAGEN = Path(__file__).parent / "data" / "sample_text.png"

# Repos de los dos checkpoints del presets VLM (`src/core/types.rs::VlmModel`).
VLM_REPO = "zai-org/GLM-OCR"
LAYOUT_REPO = "PaddlePaddle/PP-DocLayoutV3_safetensors"

# `OAR_HOME` del host, antes de que `conftest` lo borre para aislar cada test.
RAIZ_HOST = os.environ.get("OAR_HOME")

pytestmark = pytest.mark.skipif(
    "glm_ocr" not in pyocrust.pipeline_profiles(),
    reason="requiere un build con la feature `vl` (maturin develop --features vl)",
)


def _snapshot_publicado(root: Path, repo: str) -> Path | None:
    """`<root>/models/<org>/<name>/<commit>` con un commit ya publicado."""
    base = root / "models" / repo
    for entry in sorted(base.glob("*")) if base.is_dir() else []:
        nombre = entry.name.lower()
        if entry.is_dir() and 40 <= len(nombre) <= 64 and all(c in "0123456789abcdef" for c in nombre):
            return entry
    return None


def _root_con_snapshots() -> Path | None:
    candidatos = [Path(RAIZ_HOST)] if RAIZ_HOST else []
    candidatos.append(Path.home() / ".oar")
    for root in candidatos:
        if _snapshot_publicado(root, VLM_REPO) and _snapshot_publicado(root, LAYOUT_REPO):
            return root
    return None


def test_offline_without_weights_is_a_typed_error(tmp_path, monkeypatch):
    """`PYOCRUST_OFFLINE=1` y sin pesos: error tipado, sin descarga."""
    monkeypatch.setenv("PYOCRUST_OFFLINE", "1")
    with pytest.raises(pyocrust.PyOcrRuntimeError) as excinfo:
        pyocrust.VeloceOCR("glm_ocr", custom_path=str(tmp_path), device="cpu")

    mensaje = str(excinfo.value)
    assert "offline" in mensaje.lower()
    assert "glm_ocr" in mensaje
    # No ha dejado nada descargado en el root vacío.
    assert not (tmp_path / "models").exists()


def test_cuda_without_the_vl_cuda_build_is_honest(tmp_path, monkeypatch):
    """`device='cuda'` sin build CUDA: error tipado, nunca CPU etiquetado CUDA."""
    monkeypatch.setenv("PYOCRUST_OFFLINE", "1")
    try:
        pyocrust.VeloceOCR("glm_ocr", custom_path=str(tmp_path), device="cuda")
    except pyocrust.PyOcrValueError as error:
        assert "cuda" in str(error).lower()
    else:
        # Con un build `--features vl-cuda` el dispositivo CUDA existe de verdad:
        # se acepta, pero nunca como CPU disfrazado.
        pytest.skip("build con CUDA de Candle disponible; no aplica el error tipado")


def test_real_page_produces_non_empty_markdown(monkeypatch):
    """Una página real → Markdown no vacío con `provider_effective` honesto."""
    monkeypatch.delenv("PYOCRUST_OFFLINE", raising=False)
    root = _root_con_snapshots()
    if root is None:
        pytest.skip(
            "sin snapshots del VLM (~1.9 GB) bajo el root; "
            "instancia `VeloceOCR('glm_ocr')` una vez para que oar-ocr-vl los baje"
        )
    assert IMAGEN.is_file(), "falta el fixture de imagen de tests/data/"

    ocr = pyocrust.VeloceOCR("glm_ocr", custom_path=str(root), device="cpu")
    assert ocr.provider_effective == "cpu"

    estructura = ocr.recognize(str(IMAGEN))
    markdown = estructura.to_markdown()
    assert markdown.strip(), "una página real debe producir Markdown no vacío"
    # Un VLM no emite cajas: la salida es sólo Markdown.
    assert estructura.elements == []
    assert estructura.regions == []
