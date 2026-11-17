"""Kwargs de detección de `VeloceOCR`: validación tipada y cableado al detector.

Contrato (bloque `RDET`): los siete `text_det_*` son opcionales; sin ellos el
detector se comporta como hoy (960/Max/4000 + umbrales 0.2/0.45/1.4/3000), y
cualquier valor fuera de rango da `PyOcrValueError` en el constructor — nunca
un default mudo.

Ejecución: `python -m pytest tests/test_text_det_options.py -q`
"""

from __future__ import annotations

import pytest

from pyocrust import PyOcrValueError, PyOcrRuntimeError, VeloceOCR

# (kwargs inválidos, fragmento esperado del mensaje)
CASOS_INVALIDOS = [
    ({"text_det_limit_type": "bogus"}, "text_det_limit_type"),
    ({"text_det_limit_type": "MAX"}, "text_det_limit_type"),
    ({"text_det_thresh": 1.5}, "text_det_thresh"),
    ({"text_det_thresh": -0.01}, "text_det_thresh"),
    ({"text_det_box_thresh": 2.0}, "text_det_box_thresh"),
    ({"text_det_unclip_ratio": -1.0}, "text_det_unclip_ratio"),
    ({"text_det_max_candidates": 0}, "text_det_max_candidates"),
    ({"text_det_limit_side_len": 0}, "text_det_limit_side_len"),
    ({"text_det_limit_side_len": -5}, "text_det_limit_side_len"),
    ({"text_det_max_side_len": 0}, "text_det_max_side_len"),
]


@pytest.mark.parametrize(("kwargs", "aguja"), CASOS_INVALIDOS)
def test_valor_invalido_es_value_error(tmp_path, monkeypatch, kwargs, aguja):
    """Un valor inválido es `PyOcrValueError`, no un fallback silencioso.

    `PYOCRUST_OFFLINE` + `tmp_path` vacío garantizan que, si la validación no
    saltara, el error sería `PyOcrRuntimeError` por el preflight: el tipo de
    excepción distingue "validó mal" de "validó y siguió".
    """
    monkeypatch.setenv("PYOCRUST_OFFLINE", "1")

    with pytest.raises(PyOcrValueError) as fallo:
        VeloceOCR("pp_ocrv6", custom_path=str(tmp_path), **kwargs)

    assert aguja in str(fallo.value)
    assert not isinstance(fallo.value, PyOcrRuntimeError)


def test_kwargs_validos_se_cablean_al_pipeline(modelos_tiny):
    """Los siete kwargs válidos construyen el detector real sin error."""
    ocr = VeloceOCR(
        "pp_ocrv6",
        custom_path=str(modelos_tiny),
        device="cpu",
        text_det_limit_type="min",
        text_det_limit_side_len=64,
        text_det_max_side_len=7000,
        text_det_thresh=0.2,
        text_det_box_thresh=0.45,
        text_det_unclip_ratio=1.4,
        text_det_max_candidates=3000,
    )

    assert ocr.provider_effective == "cpu"
