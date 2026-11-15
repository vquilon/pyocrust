"""Un motor GPU-only (VLM documental) puede faltar en CPU sin romper la validez.

Simetrico a la regla CPU-only: los VLM documentales de `full_page` no tienen pata
CPU en este banco (`GPU_ONLY_BACKENDS`), asi que su ausencia en la run CPU no es un
desemparejamiento y no debe marcar la feature para REHACER.
"""
from __future__ import annotations

from common.runner import GPU_ONLY_BACKENDS
from validez_medicion import faltan_sobran


def test_motor_gpu_only() -> None:
    assert {"paddleocr_vl", "lightonocr", "glm_ocr"} <= GPU_ONLY_BACKENDS


def test_gpu_only_no_cuenta_como_sobrante() -> None:
    cpu = {"pyocrust_structure", "pyocrust_indra", "docling", "pp_structurev3_api"}
    gpu = {*cpu, "lightonocr", "glm_ocr", "paddleocr_vl"}  # VLM: solo GPU
    assert faltan_sobran(cpu, gpu) == ([], [])


def test_cpu_only_no_cuenta_como_faltante() -> None:
    # tesseract no expone GPU: su ausencia en la run GPU no es desemparejamiento.
    assert faltan_sobran({"pyocrust", "tesseract"}, {"pyocrust"}) == ([], [])


def test_motor_normal_que_falta_en_gpu_si_se_marca() -> None:
    assert faltan_sobran({"pyocrust", "rapidocr"}, {"pyocrust"}) == (["rapidocr"], [])


def test_motor_normal_que_sobra_en_gpu_se_marca() -> None:
    assert faltan_sobran({"pyocrust"}, {"pyocrust", "easyocr"}) == ([], ["easyocr"])
